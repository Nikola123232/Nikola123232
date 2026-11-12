"""Driver safety equipment in the body frame: helmet, HANS (head-and-neck support) + tethers, 6-point harness, seat."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler
from .core import *
from .anatomy import HEAD_C, parent_to_bone

HELMET_C = HEAD_C + Vector((0.0, 0.0, -0.002))


def helmet_mat():
    m = mat("helmet_paint", (0.9, 0.9, 0.92), rough=0.25, coat=1.0, coat_rough=0.02)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    def mth(op, a, b):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, float):
                n.inputs[i].default_value = v
            else:
                links.new(v, n.inputs[i])
        return n.outputs[0]
    X, Y, Z = sep.outputs
    ay = mth('ABSOLUTE', Y, 0.0)
    top = mth('MULTIPLY', mth('LESS_THAN', ay, 0.03), mth('GREATER_THAN', Z, 0.02))
    low = mth('LESS_THAN', mth('ADD', Z, mth('MULTIPLY', X, 0.35)), -0.035)
    m1 = nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'
    links.new(low, m1.inputs[0]); m1.inputs[6].default_value = (0.9, 0.9, 0.92, 1); m1.inputs[7].default_value = (0.012, 0.09, 0.22, 1)
    m2 = nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'
    links.new(top, m2.inputs[0]); links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (1.0, 0.28, 0.02, 1)
    links.new(m2.outputs[2], p.inputs["Base Color"])
    return m


def build_helmet(arm, name="helmet"):
    shell_m = helmet_mat()
    visor_m = mat("visor", (0.02, 0.02, 0.03), metal=0.9, rough=0.05, coat=1.0)
    pad_m = mat("helmet_pad", (0.02, 0.02, 0.02), rough=0.9)
    bm = bmesh.new()
    R = (0.152, 0.128, 0.148)
    seg, rings = 48, 32
    grid = ellipsoid_bm(bm, (0, 0, 0), R, seg, rings, 0)
    # remove bottom (neck opening), slanted: lower at the chin
    kill = []
    for v in bm.verts:
        d = Vector((v.co.x / R[0], v.co.y / R[1], v.co.z / R[2]))
        cut = -0.62 + 0.18 * max(0, -d.x)  # back of the helmet ends higher
        if d.z < cut - 0.1 * max(0, d.x):
            kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for f in bm.faces:
        c = f.calc_center_median()
        d = Vector((c.x / R[0], c.y / R[1], c.z / R[2]))
        if d.x > 0.5 and -0.22 < d.z < 0.24 and abs(d.y) < 0.78:
            f.material_index = 1
    obj = obj_from_bm(name, bm, [shell_m, visor_m, pad_m])
    sol = obj.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.012; sol.material_offset = 2; sol.material_offset_rim = 2
    add_subsurf(obj, 1)
    obj.location = HELMET_C
    # rear spoiler (gurney) + visor strip edge
    bm = bmesh.new()
    box_bm(bm, (-0.135, 0, 0.07), (0.035, 0.10, 0.006), Quaternion((0, 1, 0), math.radians(-30)))
    for s in (1, -1):
        box_bm(bm, (-0.135, s * 0.05, 0.06), (0.035, 0.005, 0.02), Quaternion((0, 1, 0), math.radians(-30)))
    sp = obj_from_bm(name + "_spoiler", bm, [mat("helmet_carbon", (0.02, 0.02, 0.025), rough=0.3, coat=1.0)], smooth=False)
    sp.location = HELMET_C
    parent_to_bone(obj, arm, "head")
    parent_to_bone(sp, arm, "head")
    return obj


def build_hans(arm):
    cm = carbon_mat("hans_carbon", tint=(0.02, 0.02, 0.025), scale=260)
    bm = bmesh.new()
    # back collar: curved plate behind the neck rising up toward the helmet
    nc = Vector((-0.045, 0.0, 0.0))
    rows = []
    for i in range(7):
        z = 0.485 + 0.12 * i / 6
        r = 0.082 - 0.006 * i / 6
        back = -0.012 * i / 6
        row = []
        for j in range(11):
            a = math.radians(140 + 80 * j / 10)
            row.append(Vector((nc.x + back + r * math.cos(a), r * math.sin(a) * (1.0 - 0.15 * i / 6), z)))
        rows.append(row)
    vt = [[bm.verts.new(p) for p in r] for r in rows]
    vb = [[bm.verts.new(p + (p - Vector((nc.x, 0, p.z))).normalized() * 0.012) for p in r] for r in rows]
    for i in range(len(rows) - 1):
        for j in range(len(rows[0]) - 1):
            bm.faces.new((vt[i][j], vt[i][j + 1], vt[i + 1][j + 1], vt[i + 1][j]))
            bm.faces.new((vb[i][j], vb[i + 1][j], vb[i + 1][j + 1], vb[i][j + 1]))
    for i in range(len(rows) - 1):
        for j in (0, len(rows[0]) - 1):
            bm.faces.new((vt[i][j], vt[i + 1][j], vb[i + 1][j], vb[i][j]))
    for j in range(len(rows[0]) - 1):
        for i in (0, len(rows) - 1):
            bm.faces.new((vt[i][j], vb[i][j], vb[i][j + 1], vt[i][j + 1]))
    # yoke arms over the trapezius and down the chest
    for s in (1, -1):
        pts = catmull([(-0.115, s * 0.04, 0.49), (-0.085, s * 0.085, 0.525), (-0.02, s * 0.105, 0.535),
                       (0.05, s * 0.10, 0.50), (0.095, s * 0.085, 0.44), (0.11, s * 0.075, 0.39)], 5)
        tube_bm(bm, pts, 0.03, 10, ry=0.008, matidx=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm("hans", bm, [cm])
    parent_to_bone(o, arm, "spine")
    # tether anchors: on the collar (spine) and on the helmet sides (head)
    tethers = []
    tmat = mat("tether", (0.85, 0.2, 0.05), rough=0.6)
    for s in (1, -1):
        a = Vector((-0.115, s * 0.06, 0.585))
        b = HELMET_C + Vector((-0.035, s * 0.125, -0.045))
        L = (b - a).length
        bm = bmesh.new()
        tube_bm(bm, [(0, 0, 0), (0, L, 0)], 0.009, 8, ry=0.0035, up=(0, 0, 1))
        rodo = obj_from_bm(f"tether_{s}", bm, [tmat])
        # orient rod's +Y to b-a
        q = Vector((0, 1, 0)).rotation_difference((b - a).normalized())
        rodo.matrix_world = Matrix.LocRotScale(a, q, Vector((1, 1, 1)))
        parent_to_bone(rodo, arm, "spine")
        rodo.matrix_basis = Matrix.LocRotScale(a, q, Vector((1, 1, 1)))
        tgt = empty(f"tether_tgt_{s}", b, size=0.01)
        parent_to_bone(tgt, arm, "head")
        tgt.location = b
        c = rodo.constraints.new('STRETCH_TO')
        c.target = tgt
        c.rest_length = L
        c.volume = 'NO_VOLUME'
        c.keep_axis = 'PLANE_Z'
        tethers.append(rodo)
        # anchor clips
        ellipsoid(f"clip_h{s}", (0, 0, 0), (0.014, 0.008, 0.014), [cm], 12, 6).location = b
        cl = bpy.data.objects[f"clip_h{s}"]; parent_to_bone(cl, arm, "head"); cl.location = b
    return o, tethers


def build_harness(arm):
    hm = mat("harness", (0.75, 0.04, 0.03), rough=0.75, sheen=0.4)
    metal = mat("buckle", (0.7, 0.7, 0.72), metal=1.0, rough=0.2)
    buckle_c = Vector((0.135, 0.0, 0.18))
    objs = []
    bm_s = bmesh.new()  # parts that follow the torso
    bm_l = bmesh.new()  # parts that stay with pelvis / seat
    for s in (1, -1):
        sh = catmull([(-0.30, s * 0.075, 0.46), (-0.14, s * 0.085, 0.52), (-0.05, s * 0.095, 0.555), (0.04, s * 0.09, 0.53),
                      (0.11, s * 0.08, 0.45), (0.135, s * 0.06, 0.33), (0.14, s * 0.03, 0.22)], 5)
        tube_bm(bm_s, sh, 0.024, 8, ry=0.004)
        lap = catmull([(-0.06, s * 0.20, -0.04), (0.02, s * 0.175, 0.07), (0.09, s * 0.12, 0.15), (0.13, s * 0.05, 0.18)], 5)
        tube_bm(bm_l, lap, 0.024, 8, ry=0.004)
        cr = catmull([(0.12, s * 0.03, -0.10), (0.135, s * 0.025, 0.02), (0.138, s * 0.012, 0.15)], 5)
        tube_bm(bm_l, cr, 0.02, 8, ry=0.004)
        # adjusters
        box_bm(bm_s, (0.125, s * 0.075, 0.40), (0.012, 0.05, 0.03), Quaternion((0, 1, 0), math.radians(-60)), 1)
    # central rotary buckle
    tube_bm(bm_l, [buckle_c + Vector((-0.004, 0, 0)), buckle_c + Vector((0.012, 0, 0))], 0.038, 24, matidx=1)
    tube_bm(bm_l, [buckle_c + Vector((0.012, 0, 0)), buckle_c + Vector((0.02, 0, 0))], 0.02, 16, matidx=1)
    for bm, bone, nm in ((bm_s, "spine", "harness_upper"), (bm_l, "root", "harness_lower")):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from_bm(nm, bm, [hm, metal])
        parent_to_bone(o, arm, bone)
        objs.append(o)
    return objs


def build_seat(arm, m=None):
    m = m or carbon_mat("seat_carbon", tint=(0.025, 0.025, 0.03))
    rings = []
    for i in range(10):
        z = -0.10 + 0.62 * i / 9
        r = 0.21 if z < 0.35 else 0.21 - 0.06 * (z - 0.35) / 0.27
        ring = []
        for j in range(15):
            a = math.radians(105 + 150 * j / 14)
            ring.append(Vector((-0.04 + r * 0.75 * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    bm = bmesh.new()
    vt = [[bm.verts.new(p) for p in r] for r in rings]
    for i in range(len(rings) - 1):
        for j in range(len(rings[0]) - 1):
            bm.faces.new((vt[i][j], vt[i][j + 1], vt[i + 1][j + 1], vt[i + 1][j]))
    o = obj_from_bm("seat", bm, [m])
    sol = o.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.015
    parent_to_bone(o, arm, "root")
    return o


def build_gear(D):
    arm = D["arm"]
    G = {}
    G["helmet"] = build_helmet(arm)
    G["hans"], G["tethers"] = build_hans(arm)
    G["harness"] = build_harness(arm)
    G["seat"] = build_seat(arm)
    return G
