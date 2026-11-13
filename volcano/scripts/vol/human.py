"""Volcano short: the human character. Re-uses the anatomy builders (skeleton, organs, brain) from f1.anatomy but with
a proper articulated rig, a modelled head (face, ears, eyes, hair), a hi-vis volcanologist suit and a pose solver."""
import sys, math, random
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler, noise
from f1.core import *
from f1 import anatomy as A

# ------------------------------------------------------------------ articulated rig
_PAR = {"farm_L": "uparm_L", "farm_R": "uparm_R", "shin_L": "thigh_L", "shin_R": "thigh_R", "foot_L": "shin_L", "foot_R": "shin_R"}
BONES2 = [(n, h, t, _PAR.get(n, p)) for (n, h, t, p) in A.BONES]
A.BONES = BONES2           # build_armature / skin_weights read this module global
HEAD_C = A.HEAD_C


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def gauss(x, s):
    return math.exp(-(x / s) ** 2)


# ------------------------------------------------------------------ materials
def suit_mat():
    """Hi-vis orange coverall: reflective silver bands, dark gloves/boots; reveal (x-ray) node for the cutaway shots."""
    m = reveal_mat("suit", (0.8, 0.17, 0.01), rough=0.62, sheen=0.1, edge=(0.2, 0.6, 1.0), estr=0.45, base_alpha=0.0)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = [n for n in nodes if n.type == 'BSDF_PRINCIPLED'][0]
    at = nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = "restpos"
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(at.outputs["Color"], sep.inputs[0])
    X, Y, Z = sep.outputs

    def mth(op, a, b=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs[0]

    def rng(v, a, b):
        return mth('MULTIPLY', mth('GREATER_THAN', v, a), mth('LESS_THAN', v, b))
    ay = mth('ABSOLUTE', Y)
    arms = mth('MULTIPLY', mth('GREATER_THAN', ay, 0.155), mth('GREATER_THAN', Z, 0.12))
    legs = mth('MULTIPLY', mth('LESS_THAN', Z, 0.075), mth('GREATER_THAN', X, 0.10))
    band = mth('MAXIMUM',
               mth('MAXIMUM', mth('MULTIPLY', arms, rng(X, 0.115, 0.14)), mth('MULTIPLY', arms, rng(X, 0.265, 0.29))),
               mth('MAXIMUM', mth('MULTIPLY', legs, rng(X, 0.30, 0.325)), mth('MULTIPLY', legs, rng(X, 0.60, 0.625))))
    torso = mth('MULTIPLY', mth('LESS_THAN', ay, 0.19), mth('LESS_THAN', X, 0.2))
    band = mth('MAXIMUM', band, mth('MULTIPLY', torso, mth('MAXIMUM', rng(Z, 0.385, 0.405), rng(Z, 0.140, 0.158))))
    dark = mth('MAXIMUM', mth('MULTIPLY', arms, mth('GREATER_THAN', X, 0.315)), mth('MULTIPLY', legs, mth('GREATER_THAN', X, 0.765)))
    m1 = nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'
    links.new(band, m1.inputs[0]); m1.inputs[6].default_value = (0.8, 0.17, 0.01, 1); m1.inputs[7].default_value = (0.62, 0.64, 0.66, 1)
    m2 = nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'
    links.new(dark, m2.inputs[0]); links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (0.015, 0.015, 0.016, 1)
    links.new(m2.outputs[2], p.inputs["Base Color"])
    links.new(mth('MULTIPLY', band, 0.8), p.inputs["Metallic"])
    return m


def human_materials():
    M = A.materials()
    M["suit"] = suit_mat()
    M["face"] = reveal_mat("face_skin", (0.74, 0.50, 0.38), rough=0.48, sheen=0.3, edge=(0.95, 0.75, 0.65), estr=0.35, base_alpha=0.0)
    M["hair"] = reveal_mat("hair", (0.055, 0.032, 0.02), rough=0.5, sheen=0.5, edge=(0.4, 0.3, 0.2), estr=0.1, base_alpha=0.0)
    M["lips"] = reveal_mat("lips", (0.55, 0.22, 0.22), rough=0.35, edge=(1.0, 0.5, 0.5), estr=0.2, base_alpha=0.0)
    M["iris"] = mat("iris", (0.08, 0.05, 0.03), rough=0.15, coat=1.0)
    M["rev"] = [M["suit"], M["face"], M["hair"], M["lips"], M["skull"]]
    return M


def set_reveal(H, frame, value):
    for m in H["M"]["rev"]:
        if frame is None:
            m.node_tree.nodes["Reveal"].outputs[0].default_value = value
        else:
            key_reveal(m, frame, value)


# ------------------------------------------------------------------ head
def build_head(M, arm):
    c = HEAD_C
    R = (0.106, 0.086, 0.099)

    def face(p, d):
        x, y, z = p
        fx = max(0.0, d.x)
        # nose: bridge + tip
        x += fx * (0.030 * gauss(d.y, 0.11) * gauss(d.z + 0.30, 0.17)) + fx * 0.006 * gauss(d.y, 0.05) * gauss(d.z + 0.02, 0.12)
        # brow ridge, eye sockets, cheek bones
        x += fx * 0.007 * gauss(d.z - 0.16, 0.09) * (1 - gauss(d.y, 0.05))
        for s in (1, -1):
            x -= fx * 0.0085 * gauss(d.y - s * 0.40, 0.14) * gauss(d.z + 0.03, 0.12)
            x += fx * 0.004 * gauss(d.y - s * 0.55, 0.15) * gauss(d.z + 0.22, 0.15)
        # mouth groove + lips + chin
        x += fx * 0.0045 * gauss(d.z + 0.55, 0.07) * gauss(d.y, 0.32) - fx * 0.003 * gauss(d.z + 0.62, 0.03) * gauss(d.y, 0.25)
        x += fx * 0.011 * gauss(d.z + 0.92, 0.14) * gauss(d.y, 0.3)
        # jaw taper, flatter face, longer back of skull
        if d.z < -0.2:
            y *= 1 - 0.22 * min(1.0, (-d.z - 0.2) / 0.7)
        if d.x < -0.2:
            x *= 1.05
        x *= 1 - 0.07 * max(0, d.x) ** 2 * (1 if d.z > -0.5 else 0)
        return Vector((x, y, z))
    bm = bmesh.new()
    ellipsoid_bm(bm, (0, 0, 0), R, 64, 44, 0, face)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    head = obj_from_bm("head_skin", bm, [M["face"]]); head.location = c
    objs = [head]
    # hair: shell that merges into the head at the hairline
    def hair(p, d):
        h = sstep(0.05, 0.5, d.z + 0.45 * max(0, -d.x) + 0.1 * abs(d.y) - 0.1)
        q = face(p, d)
        n = noise.noise(Vector(d) * 16 + Vector((2, 4, 1)))
        return q * (0.985 + h * (0.075 + 0.012 * n)) + Vector((0, 0, 0.004 * h))
    bm = bmesh.new()
    ellipsoid_bm(bm, (0, 0, 0), R, 96, 56, 0, hair)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    objs.append(obj_from_bm("hair", bm, [M["hair"]], loc=(0, 0, 0)))
    objs[-1].location = c
    for s in (1, -1):
        objs.append(ellipsoid(f"ear_{s}", c + Vector((-0.004, s * 0.085, -0.008)), (0.017, 0.006, 0.027), [M["face"]], 16, 10,
                              rot=Euler((s * 0.25, 0, s * 0.15)).to_quaternion()))
        sk = ellipsoid(f"eye_{s}", c + Vector((0.082, s * 0.034, -0.002)), (0.0105, 0.0105, 0.0105), [M["eye"]], 20, 12)
        ir = ellipsoid(f"iris_{s}", c + Vector((0.0905, s * 0.034, -0.002)), (0.0042, 0.0062, 0.0062), [M["iris"]], 12, 8)
        objs += [sk, ir]
        objs.append(tube(f"brow_{s}", [c + Vector((0.083, s * 0.012, 0.027)), c + Vector((0.089, s * 0.035, 0.033)), c + Vector((0.084, s * 0.058, 0.025))],
                         [0.0035, 0.004, 0.0028], [M["hair"]], 6))
    objs.append(ellipsoid("lips", c + Vector((0.0915, 0, -0.058)), (0.0075, 0.022, 0.0055), [M["lips"]], 20, 10))
    for o in objs:
        A.parent_to_bone(o, arm, "head")
    return objs


# ------------------------------------------------------------------ body skin (suit) as metaballs, split rig
def skin_weights2(obj, arm, power=10.0):
    from f1.anatomy import _seg_dist
    bones = [(nm, Vector(h), Vector(t)) for nm, h, t, _ in BONES2]
    groups = {nm: obj.vertex_groups.new(name=nm) for nm, _, _ in bones}
    for v in obj.data.vertices:
        p = v.co; ds = []
        for nm, h, t in bones:
            d = _seg_dist(p, h, t)
            if nm.startswith(("uparm", "farm")) and abs(p.y) < 0.165 and p.z < 0.56:
                d += 0.25                      # torso vertices must not follow the arms
            if nm.startswith(("thigh", "shin", "foot")) and p.z > 0.12:
                d += 0.25
            ds.append((nm, d))
        ds.sort(key=lambda x: x[1]); cand = ds[:3]
        w = [1.0 / (d ** power + 1e-12) for _, d in cand]; S = sum(w)
        for (nm, _), ww in zip(cand, w):
            if ww / S > 0.01:
                groups[nm].add([v.index], ww / S, 'REPLACE')
    mod = obj.modifiers.new("arm", 'ARMATURE'); mod.object = arm; mod.use_vertex_groups = True


def build_skin2(M, arm):
    mb = bpy.data.metaballs.new("body_mb"); mb.resolution = 0.011; mb.render_resolution = 0.009; mb.threshold = 0.6
    mo = bpy.data.objects.new("body_mb", mb); link(mo)

    def ell(c, size, r=0.1, stiff=2.0):
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = c; e.radius = r * 1.65
        e.size_x, e.size_y, e.size_z = size; e.stiffness = stiff

    def cap(a, b, r, stiff=2.0):
        a, b = Vector(a), Vector(b)
        e = mb.elements.new(); e.type = 'CAPSULE'; e.co = (a + b) / 2; e.radius = r * 1.65
        e.size_x = (b - a).length / 2; e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized()); e.stiffness = stiff
    cap((-0.045, 0, 0.50), (-0.005, 0, 0.665), 0.07); ell((-0.045, 0, 0.545), (0.9, 2.3, 0.9), 0.075)
    ell((-0.005, 0, 0.405), (0.95, 1.45, 1.05), 0.135); ell((0.0, 0, 0.255), (0.95, 1.25, 1.0), 0.12); ell((-0.01, 0, 0.09), (1.0, 1.45, 0.85), 0.125)
    ell((-0.06, 0.06, 0.0), (1.0, 1.0, 0.8), 0.08); ell((-0.06, -0.06, 0.0), (1.0, 1.0, 0.8), 0.08)
    cap((-0.04, -0.17, 0.475), (-0.04, 0.17, 0.475), 0.06)
    for s in (1, -1):
        cap(A.SHOULDER[s], A.ELBOW[s], 0.047); cap(A.ELBOW[s], A.WRIST[s], 0.038)
        ell(A.WRIST[s] + Vector((0.035, 0, 0.0)), (1.25, 0.8, 1.0), 0.045)
        cap(A.HIP[s], A.HIP[s].lerp(A.KNEE[s], 0.55), 0.085); cap(A.HIP[s].lerp(A.KNEE[s], 0.5), A.KNEE[s], 0.065)
        cap(A.KNEE[s], A.ANKLE[s], 0.052); cap(A.ANKLE[s] + Vector((-0.03, 0, -0.01)), A.TOE[s], 0.045)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg)); bpy.data.objects.remove(mo)
    skin = bpy.data.objects.new("skin", me); link(skin)
    me.materials.append(M["suit"])
    for p in me.polygons:
        p.use_smooth = True
    sm = skin.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.iterations = 4
    apply_mods(skin)
    ca = skin.data.color_attributes.new("restpos", 'FLOAT_COLOR', 'POINT')
    for v in skin.data.vertices:
        ca.data[v.index].color = (v.co.x, v.co.y, v.co.z, 1.0)
    skin_weights2(skin, arm)
    return skin


def build_limbs2(M, arm):
    """Skeleton of the limbs, split per bone so the articulated rig can move them."""
    V = Vector
    for s, tag in ((1, "L"), (-1, "R")):
        def mk(name, bone, fn):
            bm = bmesh.new(); fn(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            o = obj_from_bm(name, bm, [M["bone"]]); A.parent_to_bone(o, arm, bone)
        mk(f"humerus_{tag}", f"uparm_{tag}", lambda bm: A.long_bone_bm(bm, A.SHOULDER[s] + V((0, 0, 0.005)), A.ELBOW[s], 0.010, 0.024, 0.018))

        def fore(bm):
            side = (A.WRIST[s] - A.ELBOW[s]).cross(V((0, 0, 1))).normalized() * 0.012
            A.long_bone_bm(bm, A.ELBOW[s] + side, A.WRIST[s] + side, 0.006, 0.012, 0.010)
            A.long_bone_bm(bm, A.ELBOW[s] - side, A.WRIST[s] - side, 0.006, 0.010, 0.012)
            for f in range(4):
                off = V((0, 0, -0.018 + f * 0.012)); base = A.WRIST[s] + off + V((0.012, 0, 0)); k = base + V((0.05, 0, 0))
                tube_bm(bm, catmull([base, k, k + V((0.025, -s * 0.012, 0)), k + V((0.03, -s * 0.035, 0)), k + V((0.01, -s * 0.045, 0))], 3), 0.0045, 6)
            tube_bm(bm, catmull([A.WRIST[s] + V((0.01, -s * 0.01, 0.02)), A.WRIST[s] + V((0.04, -s * 0.03, 0.035)), A.WRIST[s] + V((0.065, -s * 0.035, 0.03))], 3), 0.005, 6)
        mk(f"forearm_{tag}", f"farm_{tag}", fore)

        def thigh(bm):
            A.long_bone_bm(bm, A.HIP[s] + V((0.01, s * 0.01, 0)), A.KNEE[s], 0.013, 0.024, 0.026)
            ellipsoid_bm(bm, A.HIP[s], (0.022, 0.022, 0.022), 12, 8); ellipsoid_bm(bm, A.HIP[s] + V((-0.01, s * 0.035, 0)), (0.018, 0.016, 0.022), 10, 6)
            ellipsoid_bm(bm, A.KNEE[s] + V((0.03, 0, 0.03)), (0.012, 0.02, 0.02), 10, 6)
        mk(f"femur_{tag}", f"thigh_{tag}", thigh)

        def shin(bm):
            A.long_bone_bm(bm, A.KNEE[s] + V((0, 0, -0.01)), A.ANKLE[s], 0.011, 0.025, 0.017)
            A.long_bone_bm(bm, A.KNEE[s] + V((-0.02, s * 0.02, -0.02)), A.ANKLE[s] + V((-0.015, s * 0.02, 0)), 0.005, 0.009, 0.010)
        mk(f"tibia_{tag}", f"shin_{tag}", shin)

        def foot(bm):
            ellipsoid_bm(bm, A.ANKLE[s] + V((-0.02, 0, -0.03)), (0.03, 0.018, 0.02), 10, 6)
            for m_ in range(5):
                o_ = V((0, s * (-0.025 + m_ * 0.012), 0))
                A.long_bone_bm(bm, A.ANKLE[s] + o_ * 0.5 + V((0.01, 0, 0)), A.TOE[s] + o_, 0.004, 0.007, 0.006, n=6)
        mk(f"foot_{tag}", f"foot_{tag}", foot)


def build_human(anatomy=True, name="human"):
    M = human_materials()
    root = empty(name, size=0.2)
    arm = A.build_armature(name + "_rig")
    H = {"root": root, "arm": arm, "M": M}
    H["skin"] = build_skin2(M, arm); H["skin"].parent = arm
    H["head"] = build_head(M, arm)
    H["anat"] = []
    if anatomy:
        sp = A.spine_points()
        before = set(bpy.data.objects.keys())
        A.build_spine(M, arm, sp); A.build_ribcage(M, arm, sp); A.build_pelvis(M, arm); build_limbs2(M, arm)
        A.build_skull(M, arm); H["brain"] = A.build_brain(M, arm); H["organs"] = A.build_organs(M, arm)
        H["anat"] = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before and bpy.data.objects[n].type == 'MESH']
        # the jaw/eye parts of the skull builder; the head mesh already has eyes, remove duplicate eyes from skull builder
        for o in list(H["anat"]):
            if o.name.startswith("eye_"):          # duplicate eyeballs from the skull builder; the head mesh has its own
                H["anat"].remove(o); bpy.data.objects.remove(o)
    arm.parent = root
    return H


# ------------------------------------------------------------------ pose solver
_rest = {n: (Vector(t) - Vector(h)).normalized() for (n, h, t, p) in BONES2}
_par = {n: p for (n, h, t, p) in BONES2}


def aim(bone, direction):
    return _rest[bone].rotation_difference(Vector(direction).normalized())


def eul(x=0.0, y=0.0, z=0.0):
    return Euler((x, y, z), 'XYZ').to_quaternion()


def pose(H, spec, frame=None):
    """spec: bone -> absolute body-frame delta rotation (quaternion). Unspecified bones inherit the parent's delta."""
    arm = H["arm"]
    D = {}
    for (n, h, t, p) in BONES2:
        D[n] = spec.get(n, D.get(p, Quaternion()) if p else Quaternion())
        Dp = D[p] if p else Quaternion()
        Rr = arm.data.bones[n].matrix_local.to_3x3()
        q = (Rr.inverted() @ Dp.to_matrix().inverted() @ D[n].to_matrix() @ Rr).to_quaternion()
        pb = arm.pose.bones[n]
        pb.rotation_quaternion = q
        if frame is not None:
            pb.keyframe_insert("rotation_quaternion", frame=frame)


def fall_spec(t, ph=0.0, panic=1.0, arch=0.0):
    """Flailing free-fall pose (t in seconds)."""
    s = {}
    w = 5.2
    for sd, tag in ((1, "L"), (-1, "R")):
        a = math.sin(w * t + ph + (0 if sd > 0 else 1.7))
        b = math.cos(w * 0.8 * t + ph + (0.5 if sd > 0 else 2.4))
        s[f"uparm_{tag}"] = aim(f"uparm_{tag}", (0.10 + 0.25 * b * panic, sd * 0.85, 0.50 + 0.45 * a * panic))
        s[f"farm_{tag}"] = aim(f"farm_{tag}", (0.25 + 0.2 * a, sd * (0.55 + 0.25 * b), 0.85 + 0.15 * b * panic))
        s[f"thigh_{tag}"] = aim(f"thigh_{tag}", (0.30 + 0.15 * a * panic, sd * (0.28 + 0.1 * b), -0.90))
        s[f"shin_{tag}"] = aim(f"shin_{tag}", (-0.40 - 0.2 * b * panic, sd * 0.2, -0.85))
        s[f"foot_{tag}"] = aim(f"foot_{tag}", (0.45, sd * 0.1, -0.85))
    s["spine"] = eul(0, -0.15 - arch + 0.05 * math.sin(w * t * 0.5 + ph), 0.05 * math.sin(w * 0.7 * t))
    s["neck1"] = s["spine"] @ eul(0, 0.10 + 0.05 * math.sin(w * t + ph), 0)
    s["neck2"] = s["neck1"] @ eul(0, 0.12, 0)
    s["head"] = s["neck2"] @ eul(0, 0.12 + 0.08 * math.sin(w * 1.3 * t), 0.15 * math.sin(w * 0.6 * t))
    return s


def stand_spec(sway=0.0):
    s = {}
    for sd, tag in ((1, "L"), (-1, "R")):
        s[f"uparm_{tag}"] = aim(f"uparm_{tag}", (0.05, sd * 0.30, -1.0))
        s[f"farm_{tag}"] = aim(f"farm_{tag}", (0.30, sd * 0.15, -0.90))
        s[f"thigh_{tag}"] = aim(f"thigh_{tag}", (0.02, sd * 0.06, -1.0))
        s[f"shin_{tag}"] = aim(f"shin_{tag}", (0.0, sd * 0.05, -1.0))
        s[f"foot_{tag}"] = aim(f"foot_{tag}", (0.9, sd * 0.05, -0.30))
    return s
