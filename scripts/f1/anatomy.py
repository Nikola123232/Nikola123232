"""Seated driver: rigged skin shell + skeleton + brain + internal organs.

Body frame: origin at the hip-joint centre, +X forward (face direction), +Z up along the torso, +Y = driver's left.
The whole body is posed for an F1 cockpit: thighs forward, shins slightly down, hands at the steering wheel.
Placement in the car: body_root at (2.18, 0, 0.13) rotated -25 deg about Y (reclined)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler, noise
from .core import *

BODY_IN_CAR = ((2.18, 0.0, 0.13), (0.0, math.radians(-25.0), 0.0))

# --------------------------------------------------------------------------- key points (body frame)
SPINE_CTRL = [(-0.070, 0.070), (-0.045, 0.170), (-0.060, 0.250), (-0.095, 0.380), (-0.080, 0.480),
              (-0.065, 0.520), (-0.035, 0.585), (-0.020, 0.625)]
HEAD_C = Vector((0.025, 0.0, 0.735))
SHOULDER = {s: Vector((-0.04, s * 0.19, 0.47)) for s in (1, -1)}
ELBOW = {s: Vector((0.17, s * 0.245, 0.32)) for s in (1, -1)}
WRIST = {s: Vector((0.36, s * 0.155, 0.27)) for s in (1, -1)}
HIP = {s: Vector((0.0, s * 0.09, 0.0)) for s in (1, -1)}
KNEE = {s: Vector((0.438, s * 0.11, -0.038)) for s in (1, -1)}
ANKLE = {s: Vector((0.805, s * 0.10, -0.242)) for s in (1, -1)}
TOE = {s: Vector((0.97, s * 0.095, -0.127)) for s in (1, -1)}


def spine_points():
    """24 vertebra centres from L5 (index 0) to C1 (index 23) + tangents."""
    pts = catmull([Vector((x, 0, z)) for x, z in SPINE_CTRL], 30)
    # cumulative length
    L = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        L.append(L[-1] + (b - a).length)
    total = L[-1]
    # vertebra spacing: lumbar larger, cervical smaller (weights)
    wts = [1.35] * 5 + [1.0] * 12 + [0.78] * 7
    S = sum(wts)
    targets = []
    acc = 0.06 * total
    span = total * 0.94
    for w in wts:
        targets.append(acc + span * (w / 2) / S)
        acc += span * w / S
    res = []
    j = 0
    for tl in targets:
        while j < len(L) - 2 and L[j + 1] < tl:
            j += 1
        u = (tl - L[j]) / max(1e-9, L[j + 1] - L[j])
        p = pts[j].lerp(pts[j + 1], u)
        t = (pts[j + 1] - pts[j]).normalized()
        res.append((p, t))
    return res  # 0..4 L5..L1, 5..16 T12..T1, 17..23 C7..C1


# --------------------------------------------------------------------------- materials
def materials():
    M = {}
    M["bone"] = mat("bone", (0.62, 0.56, 0.44), rough=0.42, spec=0.5, sheen=0.2)
    M["skull"] = reveal_mat("skull_bone", (0.62, 0.56, 0.44), rough=0.42, sheen=0.2, edge=(0.95, 0.9, 0.8), estr=1.2, base_alpha=0.05)
    M["cart"] = mat("cartilage", (0.62, 0.78, 0.86), rough=0.3)
    M["disc"] = mat("disc", (0.35, 0.55, 0.85), rough=0.35)
    M["brain"] = mat("brain", (0.85, 0.48, 0.48), rough=0.45, sheen=0.4, coat=0.3)
    M["cereb"] = mat("cerebellum", (0.78, 0.40, 0.42), rough=0.45, coat=0.3)
    M["heart"] = mat("heart", (0.55, 0.04, 0.05), rough=0.35, coat=0.5)
    M["lung"] = mat("lung", (0.85, 0.42, 0.45), rough=0.5, sheen=0.5)
    M["liver"] = mat("liver", (0.35, 0.07, 0.05), rough=0.3, coat=0.6)
    M["stomach"] = mat("stomach", (0.85, 0.55, 0.45), rough=0.4, coat=0.4)
    M["intestine"] = mat("intestine", (0.88, 0.58, 0.52), rough=0.4, coat=0.4)
    M["colon"] = mat("colon", (0.72, 0.42, 0.38), rough=0.45, coat=0.3)
    M["kidney"] = mat("kidney", (0.45, 0.10, 0.08), rough=0.35, coat=0.5)
    M["vessel_r"] = mat("artery", (0.65, 0.03, 0.04), rough=0.35, coat=0.5)
    M["vessel_b"] = mat("vein", (0.1, 0.2, 0.6), rough=0.35, coat=0.5)
    M["trachea"] = mat("trachea", (0.8, 0.75, 0.7), rough=0.4)
    M["eye"] = mat("eye", (0.9, 0.9, 0.88), rough=0.1, coat=1.0)
    M["teeth"] = mat("teeth", (0.92, 0.9, 0.82), rough=0.2)
    # skin shell: race-suit when opaque, x-ray when revealed
    M["skin"] = reveal_mat("driver_skin", (0.03, 0.06, 0.16), rough=0.7, sheen=0.6,
                           edge=(0.2, 0.6, 1.0), estr=0.45, base_alpha=0.0)
    return M


# --------------------------------------------------------------------------- armature
BONES = [  # name, head, tail, parent
    ("root", (0, 0, -0.05), (0, 0, 0.06), None),
    ("spine", (-0.045, 0, 0.17), (-0.075, 0, 0.50), "root"),
    ("neck1", (-0.065, 0, 0.52), (-0.045, 0, 0.575), "spine"),
    ("neck2", (-0.045, 0, 0.575), (-0.02, 0, 0.625), "neck1"),
    ("head", (-0.02, 0, 0.625), (0.03, 0, 0.82), "neck2"),
]
for s, tag in ((1, "L"), (-1, "R")):
    BONES += [(f"uparm_{tag}", tuple(SHOULDER[s]), tuple(ELBOW[s]), "spine"),
              (f"farm_{tag}", tuple(ELBOW[s]), tuple(WRIST[s]), "root"),
              (f"thigh_{tag}", tuple(HIP[s]), tuple(KNEE[s]), "root"),
              (f"shin_{tag}", tuple(KNEE[s]), tuple(ANKLE[s]), "root"),
              (f"foot_{tag}", tuple(ANKLE[s]), tuple(TOE[s]), "root")]


def build_armature(name="rig"):
    ad = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, ad)
    link(arm)
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = ad.edit_bones
    for nm, h, t, par in BONES:
        b = eb.new(nm)
        b.head = h; b.tail = t
        b.roll = 0.0
        if par:
            b.parent = eb[par]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    arm.hide_render = True
    return arm


def parent_to_bone(obj, arm, bone):
    b = arm.data.bones[bone]
    obj.parent = arm
    obj.parent_type = 'BONE'
    obj.parent_bone = bone
    M = b.matrix_local @ Matrix.Translation((0, b.length, 0))
    obj.matrix_parent_inverse = M.inverted()


def pose_pitch(arm, bone, angle, frame=None):
    """Rotate pose bone about the body-frame Y axis (positive = forward flexion)."""
    pb = arm.pose.bones[bone]
    b = arm.data.bones[bone]
    ax = b.matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))
    pb.rotation_quaternion = Quaternion(ax.normalized(), angle)
    if frame is not None:
        pb.keyframe_insert("rotation_quaternion", frame=frame)


def pose_offset(arm, bone, offset, frame=None):
    """Translate pose bone by a body-frame vector."""
    pb = arm.pose.bones[bone]
    b = arm.data.bones[bone]
    pb.location = b.matrix_local.to_3x3().inverted() @ Vector(offset)
    if frame is not None:
        pb.keyframe_insert("location", frame=frame)


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def skin_weights(obj, arm, power=8.0):
    bones = [(nm, Vector(h), Vector(t)) for nm, h, t, _ in BONES]
    groups = {nm: obj.vertex_groups.new(name=nm) for nm, _, _ in bones}
    for v in obj.data.vertices:
        p = v.co
        ds = [(nm, _seg_dist(p, h, t)) for nm, h, t in bones]
        ds.sort(key=lambda x: x[1])
        cand = ds[:3]
        w = [1.0 / (d ** power + 1e-12) for _, d in cand]
        S = sum(w)
        for (nm, _), ww in zip(cand, w):
            if ww / S > 0.01:
                groups[nm].add([v.index], ww / S, 'REPLACE')
    mod = obj.modifiers.new("arm", 'ARMATURE')
    mod.object = arm
    mod.use_vertex_groups = True


# --------------------------------------------------------------------------- skin shell (metaballs)
def build_skin(M, arm):
    mb = bpy.data.metaballs.new("body_mb")
    mb.resolution = 0.012
    mb.render_resolution = 0.010
    mb.threshold = 0.6
    mo = bpy.data.objects.new("body_mb", mb)
    link(mo)

    def ell(c, size, r=0.1, rot=None, stiff=2.0):
        e = mb.elements.new()
        e.type = 'ELLIPSOID'
        e.co = c
        e.radius = r * 1.65
        e.size_x, e.size_y, e.size_z = size
        e.stiffness = stiff
        if rot is not None:
            e.rotation = rot
        return e

    def cap(a, b, r, stiff=2.0):
        a, b = Vector(a), Vector(b)
        e = mb.elements.new()
        e.type = 'CAPSULE'
        e.co = (a + b) / 2
        e.radius = r * 1.65
        e.size_x = (b - a).length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
        e.stiffness = stiff
        return e
    # head & neck
    ell(HEAD_C + Vector((0.0, 0, 0.005)), (0.95, 0.78, 1.0), 0.12)
    ell(HEAD_C + Vector((0.05, 0, -0.065)), (0.8, 0.8, 0.7), 0.065)
    cap((-0.045, 0, 0.50), (-0.005, 0, 0.66), 0.058)
    # torso
    ell((-0.005, 0, 0.405), (0.95, 1.45, 1.05), 0.135)
    ell((0.0, 0, 0.255), (0.95, 1.25, 1.0), 0.12)
    ell((-0.01, 0, 0.09), (1.0, 1.45, 0.85), 0.125)
    ell((-0.06, 0.06, 0.0), (1.0, 1.0, 0.8), 0.08)
    ell((-0.06, -0.06, 0.0), (1.0, 1.0, 0.8), 0.08)
    cap((-0.04, -0.17, 0.475), (-0.04, 0.17, 0.475), 0.06)
    for s in (1, -1):
        cap(SHOULDER[s], ELBOW[s], 0.047)
        cap(ELBOW[s], WRIST[s], 0.038)
        ell(WRIST[s] + Vector((0.035, 0, 0.0)), (1.2, 0.7, 1.0), 0.045)
        cap(HIP[s] + Vector((0.0, 0, 0)), HIP[s].lerp(KNEE[s], 0.55), 0.085)
        cap(HIP[s].lerp(KNEE[s], 0.5), KNEE[s], 0.065)
        cap(KNEE[s], ANKLE[s], 0.052)
        cap(ANKLE[s] + Vector((-0.03, 0, -0.01)), TOE[s], 0.042)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
    bpy.data.objects.remove(mo)
    skin = bpy.data.objects.new("skin", me)
    link(skin)
    me.materials.append(M["skin"])
    for p in me.polygons:
        p.use_smooth = True
    sm = skin.modifiers.new("smooth", 'CORRECTIVE_SMOOTH')
    sm.iterations = 4
    apply_mods(skin)
    skin_weights(skin, arm)
    return skin


# --------------------------------------------------------------------------- skeleton
def long_bone_bm(bm, a, b, r_shaft, r_a, r_b, matidx=0, n=12):
    a, b = Vector(a), Vector(b)
    pts, rad = [], []
    K = 14
    for i in range(K + 1):
        u = i / K
        pts.append(a.lerp(b, u))
        ea = math.exp(-((u) / 0.09) ** 2)
        eb = math.exp(-((1 - u) / 0.09) ** 2)
        rad.append(r_shaft + (r_a - r_shaft) * ea + (r_b - r_shaft) * eb)
    tube_bm(bm, pts, rad, n, matidx=matidx)


def vertebra_bm(bm, c, t, r, h, kind, matidx_bone=0, matidx_disc=1):
    t = t.normalized()
    fwd = Vector((1, 0, 0))
    fwd = (fwd - t * fwd.dot(t)).normalized()
    side = t.cross(fwd).normalized()
    # body (short cylinder, slightly waisted)
    tube_bm(bm, [c - t * h * 0.5, c - t * h * 0.25, c + t * h * 0.25, c + t * h * 0.5], [r, r * 0.92, r * 0.92, r], 14, matidx=matidx_bone)
    # intervertebral disc above
    tube_bm(bm, [c + t * h * 0.5, c + t * h * 0.8], [r * 0.95, r * 0.95], 14, matidx=matidx_disc)
    # pedicles + arch + spinous process (points back and down) + transverse processes
    back = -fwd
    arch_c = c + back * r * 1.5
    for s in (1, -1):
        tube_bm(bm, [c + back * r * 0.8 + side * s * r * 0.55, arch_c + side * s * r * 0.55], r * 0.22, 6, matidx=matidx_bone)
    sp_len = {"C": 1.0, "T": 1.4, "L": 1.3}[kind]
    tip = arch_c + back * r * sp_len - t * r * (0.9 if kind == "T" else 0.3)
    tube_bm(bm, [arch_c, arch_c.lerp(tip, 0.5), tip], [r * 0.32, r * 0.25, r * 0.18], 6, matidx=matidx_bone)
    tl = {"C": 0.9, "T": 1.1, "L": 1.2}[kind]
    for s in (1, -1):
        tube_bm(bm, [arch_c, arch_c + side * s * r * tl + back * r * 0.2], [r * 0.25, r * 0.17], 6, matidx=matidx_bone)


def build_spine(M, arm, sp):
    groups = {"root": range(0, 5), "spine": range(5, 18), "neck1": range(18, 21), "neck2": range(21, 24)}
    objs = {}
    for bone, idx in groups.items():
        bm = bmesh.new()
        for i in idx:
            c, t = sp[i]
            if i < 5:
                kind, r, h = "L", 0.021, 0.026
            elif i < 17:
                kind, r = "T", 0.0145 + 0.005 * (16 - i) / 11
                h = 0.016
            else:
                kind, r, h = "C", 0.0115, 0.011
            vertebra_bm(bm, c, t, r, h, kind)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from_bm(f"spine_{bone}", bm, [M["bone"], M["disc"]])
        parent_to_bone(o, arm, bone)
        objs[bone] = o
    return objs


def build_ribcage(M, arm, sp):
    bm = bmesh.new()
    widths = [0.065, 0.092, 0.112, 0.126, 0.136, 0.142, 0.144, 0.142, 0.137, 0.130, 0.115, 0.098]
    for k in range(12):
        vi = 16 - k  # T1 = index 16 ... T12 = index 5
        c, t = sp[vi]
        b = widths[k]
        a = 0.085 + 0.012 * min(k, 6) / 6
        xc = c.x + a * 0.95
        drop = 0.055 + 0.02 * k / 11
        true_rib = k < 7
        floating = k >= 10
        end_phi = 0.93 * math.pi if true_rib else (0.80 * math.pi if not floating else 0.55 * math.pi)
        for s in (1, -1):
            pts = []
            N = 26
            for i in range(N + 1):
                ph = 0.12 + (end_phi - 0.12) * i / N
                x = xc - a * math.cos(ph)
                y = s * (0.02 + b * math.sin(ph) * (1.0 if ph < math.pi / 2 else (0.88 + 0.12 * math.sin(ph))))
                z = c.z + 0.012 - drop * (ph / math.pi) ** 1.4 + 0.012 * math.sin(ph * 1.2)
                pts.append((x, y, z))
            # bony part / costal cartilage split
            split = int(N * (0.72 if true_rib else 0.85)) if not floating else N
            r = 0.0062 if k > 0 else 0.0075
            tube_bm(bm, pts[:split + 1], r, 8, ry=r * 0.55, up=(0, 0, 1), matidx=0)
            if split < N:
                # cartilage curves toward the sternum
                end = Vector(pts[-1])
                if true_rib:
                    st_z = 0.48 - 0.15 * k / 6
                    target = Vector((0.085 + 0.02 * k / 6, s * 0.018, st_z))
                else:
                    target = Vector((0.07 + 0.02 * (k - 7), s * (0.075 + 0.02 * (k - 7)), 0.30 - 0.02 * (k - 7)))
                cp = catmull([pts[split], end.lerp(target, 0.3) + Vector((0.01, 0, 0.0)), target], 4)
                tube_bm(bm, cp, r * 0.9, 8, ry=r * 0.6, up=(0, 0, 1), matidx=1)
    # sternum: manubrium + body + xiphoid
    st = [Vector((0.075, 0, 0.495)), Vector((0.085, 0, 0.44)), Vector((0.095, 0, 0.37)), Vector((0.098, 0, 0.33)), Vector((0.10, 0, 0.30))]
    tube_bm(bm, st, [0.024, 0.017, 0.016, 0.012, 0.006], 10, ry=[0.006, 0.006, 0.006, 0.005, 0.003], up=(1, 0, 0), matidx=0)
    # clavicles (S-shaped) and scapulae
    for s in (1, -1):
        cl = catmull([(0.075, s * 0.02, 0.50), (0.06, s * 0.08, 0.505), (0.01, s * 0.14, 0.50), (-0.035, s * 0.175, 0.495)], 5)
        tube_bm(bm, cl, [0.008] * len(cl), 8, matidx=0)
        # scapula: triangular curved plate on the back
        tri = [Vector((-0.12, s * 0.06, 0.47)), Vector((-0.10, s * 0.165, 0.475)), Vector((-0.125, s * 0.085, 0.33))]
        vs = []
        for p in tri:
            vs.append(bm.verts.new(p))
        vs2 = [bm.verts.new(p + Vector((0.008, 0, 0))) for p in tri]
        bm.faces.new(vs); bm.faces.new(list(reversed(vs2)))
        for i in range(3):
            j = (i + 1) % 3
            bm.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
        tube_bm(bm, [(-0.125, s * 0.08, 0.455), (-0.09, s * 0.16, 0.48), (-0.05, s * 0.18, 0.49)], 0.006, 6, matidx=0)  # spine of scapula/acromion
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm("ribcage", bm, [M["bone"], M["cart"]])
    parent_to_bone(o, arm, "spine")
    return o


def build_pelvis(M, arm):
    bm = bmesh.new()
    # iliac wings: patches of an ellipsoid surface, thickened
    for s in (1, -1):
        c = Vector((-0.025, s * 0.065, 0.075))
        rad = Vector((0.065, 0.07, 0.075))
        rows = []
        for i in range(9):
            th = math.radians(20 + 75 * i / 8)       # from top toward the side
            row = []
            for j in range(11):
                ph = math.radians(-60 + 150 * j / 10)  # from back to front
                d = Vector((math.sin(th) * math.cos(ph) * 0.0 + math.cos(ph) * math.sin(th), s * math.sin(th) * abs(math.sin(ph + 1.57)) , math.cos(th)))
                d = Vector((math.sin(th) * math.sin(ph), s * math.sin(th) * math.cos(ph) * 0.9 + s * 0.15, math.cos(th)))
                p = c + Vector((d.x * rad.x, d.y * rad.y, d.z * rad.z))
                row.append(p)
            rows.append(row)
        for th_off in (0.0, 0.007):
            pass
        top = [[bm.verts.new(p) for p in r] for r in rows]
        bot = [[bm.verts.new(p - Vector((0, s * 0.007, 0))) for p in r] for r in rows]
        for i in range(len(rows) - 1):
            for j in range(len(rows[0]) - 1):
                bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]))
                bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]))
        for i in range(len(rows) - 1):
            for j in (0, len(rows[0]) - 1):
                bm.faces.new((top[i][j], top[i + 1][j], bot[i + 1][j], bot[i][j]))
        for j in range(len(rows[0]) - 1):
            for i in (0, len(rows) - 1):
                bm.faces.new((top[i][j], bot[i][j], bot[i][j + 1], top[i][j + 1]))
        # acetabulum rim + ischium + pubic ramus
        tube_bm(bm, [(0.0, s * 0.075, 0.02), (0.005, s * 0.09, -0.005)], 0.022, 10, matidx=0)
        tube_bm(bm, catmull([(-0.03, s * 0.07, 0.0), (-0.035, s * 0.06, -0.05), (0.01, s * 0.045, -0.06), (0.05, s * 0.02, -0.04), (0.055, s * 0.008, -0.02)], 4), 0.011, 8, matidx=0)
        tube_bm(bm, catmull([(0.02, s * 0.075, 0.015), (0.05, s * 0.04, 0.0), (0.058, s * 0.008, -0.015)], 4), 0.009, 8, matidx=0)
    # sacrum + coccyx (wedge following the spine base)
    tube_bm(bm, catmull([(-0.065, 0, 0.085), (-0.08, 0, 0.04), (-0.08, 0, 0.0), (-0.065, 0, -0.035)], 4),
            [0.040, 0.038, 0.034, 0.028, 0.022, 0.017, 0.012, 0.010, 0.008, 0.006, 0.005, 0.004, 0.004], 10, ry=[0.016] * 13, up=(1, 0, 0), matidx=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm("pelvis", bm, [M["bone"]])
    parent_to_bone(o, arm, "root")
    return o


def build_limbs(M, arm):
    objs = []
    for s, tag in ((1, "L"), (-1, "R")):
        bm = bmesh.new()  # humerus (follows the torso)
        long_bone_bm(bm, SHOULDER[s] + Vector((0, 0, 0.005)), ELBOW[s], 0.010, 0.024, 0.018)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from_bm(f"humerus_{tag}", bm, [M["bone"]]); parent_to_bone(o, arm, "spine"); objs.append(o)
        bm = bmesh.new()  # forearm + hand + leg bones (static w.r.t. pelvis/seat)
        side = (WRIST[s] - ELBOW[s]).cross(Vector((0, 0, 1))).normalized() * 0.012
        long_bone_bm(bm, ELBOW[s] + side, WRIST[s] + side, 0.006, 0.012, 0.010)
        long_bone_bm(bm, ELBOW[s] - side, WRIST[s] - side, 0.006, 0.010, 0.012)
        # hand: metacarpals + curled fingers around the grip
        for f in range(4):
            off = Vector((0, 0, -0.018 + f * 0.012))
            base = WRIST[s] + off + Vector((0.012, 0, 0))
            k = base + Vector((0.05, 0, 0.0))
            tube_bm(bm, catmull([base, k, k + Vector((0.025, -s * 0.012, 0.0)), k + Vector((0.03, -s * 0.035, 0.0)), k + Vector((0.01, -s * 0.045, 0.0))], 3),
                    0.0045, 6)
        tube_bm(bm, catmull([WRIST[s] + Vector((0.01, -s * 0.01, 0.02)), WRIST[s] + Vector((0.04, -s * 0.03, 0.035)), WRIST[s] + Vector((0.065, -s * 0.035, 0.03))], 3), 0.005, 6)
        long_bone_bm(bm, HIP[s] + Vector((0.01, s * 0.01, 0)), KNEE[s], 0.013, 0.024, 0.026)   # femur
        bm_head = HIP[s]
        ellipsoid_bm(bm, bm_head, (0.022, 0.022, 0.022), 12, 8)                                   # femoral head
        ellipsoid_bm(bm, HIP[s] + Vector((-0.01, s * 0.035, 0.0)), (0.018, 0.016, 0.022), 10, 6)  # greater trochanter
        ellipsoid_bm(bm, KNEE[s] + Vector((0.03, 0, 0.03)), (0.012, 0.02, 0.02), 10, 6)           # patella
        long_bone_bm(bm, KNEE[s] + Vector((0, 0, -0.01)), ANKLE[s], 0.011, 0.025, 0.017)           # tibia
        long_bone_bm(bm, KNEE[s] + Vector((-0.02, s * 0.02, -0.02)), ANKLE[s] + Vector((-0.015, s * 0.02, 0)), 0.005, 0.009, 0.010)  # fibula
        # foot: calcaneus + metatarsals
        ellipsoid_bm(bm, ANKLE[s] + Vector((-0.02, 0, -0.03)), (0.03, 0.018, 0.02), 10, 6)
        for m_ in range(5):
            o_ = Vector((0, s * (-0.025 + m_ * 0.012), 0))
            long_bone_bm(bm, ANKLE[s] + o_ * 0.5 + Vector((0.01, 0, 0)), TOE[s] + o_, 0.004, 0.007, 0.006, n=6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from_bm(f"limbs_{tag}", bm, [M["bone"]]); parent_to_bone(o, arm, "root"); objs.append(o)
    return objs


def build_skull(M, arm):
    c = HEAD_C
    def cranium(p, d):
        # flatten temporal sides, longer front-back, bulge back of head, flatter base
        x, y, z = p
        if d.z < -0.2:
            z *= 0.8
        if d.x < -0.3:
            x *= 1.04
        y *= 1.0 - 0.06 * max(0, -d.z)
        # face: push lower front downward to form the maxilla & cheekbones
        if d.x > 0.35 and d.z < 0.15:
            k = min(1, (d.x - 0.35) / 0.4) * min(1, (0.15 - d.z) / 0.5)
            z -= 0.045 * k
            x += 0.006 * k
            y *= 1 - 0.18 * k
        return Vector((x, y, z))
    bm = bmesh.new()
    ellipsoid_bm(bm, (0, 0, 0), (0.093, 0.072, 0.082), 48, 32, 0, cranium)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sk = obj_from_bm("skull", bm, [M["skull"]])
    sk.location = c
    # eye sockets & nasal aperture
    cutters = []
    for s in (1, -1):
        cutters.append(ellipsoid("cut_orb", c + Vector((0.088, s * 0.033, -0.012)), (0.03, 0.021, 0.019), [M["bone"]], 16, 10))
    cutters.append(ellipsoid("cut_nose", c + Vector((0.098, 0, -0.048)), (0.025, 0.011, 0.017), [M["bone"]], 12, 8))
    bpy.context.view_layer.update()
    for ct in cutters:
        boolean(sk, ct)
        bpy.data.objects.remove(ct)
    # mandible (U shape) + teeth + zygomatic arches
    bm = bmesh.new()
    jaw = []
    for i in range(21):
        a = math.radians(-100 + 200 * i / 20)
        jaw.append(c + Vector((0.035 + 0.052 * math.cos(a), 0.046 * math.sin(a), -0.074 - 0.008 * math.cos(a))))
    tube_bm(bm, jaw, 0.0065, 8, ry=0.011, up=(0, 0, 1))
    for s in (1, -1):
        tube_bm(bm, [c + Vector((-0.02, s * 0.047, -0.08)), c + Vector((-0.03, s * 0.052, -0.04)), c + Vector((-0.025, s * 0.055, -0.025))], 0.008, 8, ry=0.012)
        tube_bm(bm, [c + Vector((0.07, s * 0.055, -0.035)), c + Vector((0.03, s * 0.068, -0.03)), c + Vector((-0.01, s * 0.066, -0.028))], 0.005, 6)
    for i in range(14):
        a = math.radians(-70 + 140 * i / 13)
        for row, zz in ((0, -0.062), (1, -0.07)):
            box_bm(bm, c + Vector((0.042 + 0.045 * math.cos(a), 0.036 * math.sin(a), zz)), (0.006, 0.007, 0.009),
                   Quaternion((0, 0, 1), a), matidx=1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    jo = obj_from_bm("jaw", bm, [M["skull"], M["teeth"]])
    eyes = []
    for s in (1, -1):
        eyes.append(ellipsoid(f"eye_{s}", c + Vector((0.071, s * 0.033, -0.012)), (0.0115, 0.0115, 0.0115), [M["eye"]], 16, 10))
    for o in [sk, jo] + eyes:
        parent_to_bone(o, arm, "head") if o.parent is None else None
    # parent_to_bone uses matrix_parent_inverse from rest: objects placed at world coords already
    return sk


def build_brain(M, arm):
    c = HEAD_C + Vector((-0.008, 0, 0.012))
    def brain_def(p, d):
        x, y, z = p
        # flatten bottom, frontal lobe narrower, longitudinal fissure
        if d.z < 0:
            z *= 0.75
        y *= 1 - 0.12 * max(0, d.x)
        fis = math.exp(-(d.y / 0.06) ** 2) * max(0, d.z)
        r = Vector((x, y, z))
        n = noise.noise(Vector(d) * 9.0)
        n2 = noise.noise(Vector(d) * 19.0 + Vector((3, 1, 2)))
        gyri = 0.0035 * (1 - abs(n)) + 0.0018 * (1 - abs(n2))
        # temporal lobe bulge
        if d.z < -0.1 and abs(d.y) > 0.5:
            r *= 1.03
        k = 1.0 + gyri / max(0.04, r.length) - 0.05 * fis
        return r * k
    bm = bmesh.new()
    ellipsoid_bm(bm, (0, 0, 0), (0.080, 0.064, 0.060), 96, 64, 0, brain_def)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    br = obj_from_bm("brain", bm, [M["brain"]])
    br.location = c
    # cerebellum + brainstem
    def cb(p, d):
        return p * (1 + 0.04 * math.sin(d.z * 40) * 0.5)
    cbl = ellipsoid("cerebellum", c + Vector((-0.042, 0, -0.05)), (0.032, 0.05, 0.022), [M["cereb"]], 32, 18, cb)
    stem = tube("brainstem", [c + Vector((-0.005, 0, -0.03)), c + Vector((-0.015, 0, -0.07)), c + Vector((-0.03, 0, -0.1))], [0.014, 0.012, 0.010], [M["cereb"]], 10)
    # spinal cord down the neck (follows the head bone; short)
    grp = []
    for o in (br, cbl, stem):
        parent_to_bone(o, arm, "head")
        grp.append(o)
    return grp


def build_organs(M, arm):
    """Thoracic + abdominal organs. Returns dict of objects (all parented to the 'spine' bone so they move with the torso)."""
    O = {}
    def lung_def(s):
        def f(p, d):
            x, y, z = p
            w = 1.0 + 0.35 * max(0, -d.z)        # wider base
            if d.z > 0:
                w *= 1 - 0.25 * d.z               # pointed apex
            y *= w; x *= w * 0.95
            # medial concavity for the heart
            if d.y * s < -0.3:
                y *= 0.75
            return Vector((x, y, z))
        return f
    for s in (1, -1):
        O[f"lung{s}"] = ellipsoid(f"lung_{s}", (0.005, s * 0.07, 0.405), (0.055, 0.052, 0.088), [M["lung"]], 32, 20, lung_def(s))
    def heart_def(p, d):
        x, y, z = p
        if d.z < 0:  # apex
            k = 1 - 0.35 * (-d.z)
            x *= k; y *= k
        return Vector((x, y, z))
    O["heart"] = ellipsoid("heart", (0.045, 0.018, 0.375), (0.042, 0.038, 0.055), [M["heart"]], 32, 18, heart_def,
                           rot=Euler((math.radians(25), math.radians(-30), 0)).to_quaternion())
    O["aorta"] = tube("aorta", catmull([(0.05, 0.005, 0.40), (0.045, 0.0, 0.445), (0.0, 0.01, 0.46), (-0.045, 0.015, 0.43), (-0.05, 0.012, 0.30), (-0.04, 0.008, 0.15)], 5),
                      0.011, [M["vessel_r"]], 10)
    O["vena"] = tube("vena_cava", catmull([(0.03, -0.025, 0.46), (0.035, -0.03, 0.40), (0.0, -0.03, 0.30), (-0.03, -0.025, 0.15)], 5), 0.009, [M["vessel_b"]], 10)
    O["trachea"] = tube("trachea", catmull([(0.0, 0, 0.60), (0.01, 0, 0.53), (0.01, 0, 0.47), (0.005, 0.03, 0.43)], 4), 0.009, [M["trachea"]], 10)
    tube("bronchus_r", [(0.01, 0, 0.47), (0.005, -0.03, 0.43)], 0.007, [M["trachea"]], 8).parent = None
    def liver_def(p, d):
        x, y, z = p
        # wedge: thick on the right (-y), thin on the left
        k = 1.0 + 0.35 * (-d.y)
        z *= k
        if d.z > 0:
            z *= 0.8  # dome under the diaphragm
        return Vector((x, y, z))
    O["liver"] = ellipsoid("liver", (0.03, -0.035, 0.285), (0.065, 0.095, 0.042), [M["liver"]], 32, 18, liver_def)
    O["stomach"] = tube("stomach", catmull([(0.02, 0.025, 0.33), (0.03, 0.065, 0.31), (0.045, 0.075, 0.27), (0.06, 0.04, 0.24), (0.06, 0.0, 0.245), (0.05, -0.03, 0.26)], 5),
                        [0.02, 0.03, 0.036, 0.036, 0.034, 0.03, 0.026, 0.022, 0.02, 0.018, 0.016, 0.015, 0.014, 0.013, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012],
                        [M["stomach"]], 14)
    for s in (1, -1):
        O[f"kidney{s}"] = ellipsoid(f"kidney_{s}", (-0.045, s * 0.06, 0.235), (0.022, 0.03, 0.05), [M["kidney"]], 20, 12,
                                    rot=Euler((0, 0, s * 0.3)).to_quaternion())
    # large intestine frame + small intestine coils
    O["colon"] = tube("colon", catmull([(0.03, -0.085, 0.07), (0.04, -0.09, 0.15), (0.05, -0.08, 0.21), (0.06, 0.0, 0.215), (0.05, 0.08, 0.21),
                                        (0.04, 0.09, 0.14), (0.035, 0.08, 0.07), (0.04, 0.03, 0.05)], 6), 0.02, [M["colon"]], 12)
    random.seed(11)
    pts = []
    for i in range(140):
        u = i / 140
        a = u * math.pi * 2 * 6.5
        r = 0.05 * (0.4 + 0.6 * abs(math.sin(u * math.pi * 3)))
        pts.append((0.07 + 0.012 * math.sin(a * 0.5), r * math.cos(a), 0.135 + 0.06 * math.sin(u * math.pi * 5) * 0.7 + r * math.sin(a) * 0.55))
    O["intestine"] = tube("small_intestine", pts, 0.0105, [M["intestine"]], 8)
    for k, o in list(O.items()):
        parent_to_bone(o, arm, "spine")
    for o in bpy.data.objects:
        if o.name.startswith("bronchus"):
            parent_to_bone(o, arm, "spine")
    return O


def build_driver(name="driver", anatomy=True, skin=True):
    """Returns dict with root empty, armature, skin, groups. Built in body frame at origin, then root can be placed."""
    M = materials()
    root = empty(name, size=0.2)
    arm = build_armature(name + "_rig")
    D = {"root": root, "arm": arm, "M": M}
    if skin:
        D["skin"] = build_skin(M, arm)
        D["skin"].parent = arm
    if anatomy:
        sp = spine_points()
        D["spine"] = build_spine(M, arm, sp)
        D["ribs"] = build_ribcage(M, arm, sp)
        D["pelvis"] = build_pelvis(M, arm)
        D["limbs"] = build_limbs(M, arm)
        D["skull"] = build_skull(M, arm)
        D["brain"] = build_brain(M, arm)
        D["organs"] = build_organs(M, arm)
    arm.parent = root
    return D


def anatomy_objects(D):
    """All internal (non-skin) objects."""
    res = []
    arm = D["arm"]
    for o in bpy.data.objects:
        if o.parent == arm and o is not D.get("skin") and o.type == 'MESH':
            res.append(o)
    return res
