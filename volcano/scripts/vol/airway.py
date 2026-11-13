"""Respiratory tract at real scale inside the character: mouth -> pharynx -> larynx -> trachea (cartilage rings) -> carina ->
bronchial tree -> alveolar clusters. Returns geometry + flow paths for particles."""
import sys, math, random
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy, bmesh
from mathutils import Vector
from f1.core import *

# (x, y, z, lateral radius, vertical radius)
MAIN = [(0.26, 0, 0.693, 0.03, 0.02), (0.095, 0, 0.693, 0.024, 0.0085), (0.05, 0, 0.688, 0.026, 0.0125), (0.0, 0, 0.672, 0.022, 0.016),
        (-0.018, 0, 0.645, 0.017, 0.017), (-0.008, 0, 0.615, 0.0125, 0.0125), (0.0, 0, 0.60, 0.0098, 0.0098), (0.004, 0, 0.53, 0.0098, 0.0098),
        (0.010, 0, 0.465, 0.0098, 0.0098)]


def mucosa_mat(name="mucosa"):
    m = bpy.data.materials.new(name); nodes, links = m.node_tree.nodes, m.node_tree.links
    p = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord")
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 5; links.new(tc.outputs["Object"], nz.inputs[0])
    vo = nodes.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 260; links.new(tc.outputs["Object"], vo.inputs[0])
    k1 = nodes.new("ShaderNodeValue"); k1.name = "K1"; k2 = nodes.new("ShaderNodeValue"); k2.name = "K2"
    m1 = nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'; links.new(k1.outputs[0], m1.inputs[0])
    m1.inputs[6].default_value = (0.78, 0.30, 0.30, 1); m1.inputs[7].default_value = (0.62, 0.04, 0.03, 1)
    m2 = nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'; links.new(k2.outputs[0], m2.inputs[0]); links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (0.20, 0.02, 0.02, 1)
    links.new(m2.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.22; p.inputs["Coat Weight"].default_value = 0.8; p.inputs["Coat Roughness"].default_value = 0.1
    p.inputs["Emission Color"].default_value = (0.85, 0.12, 0.1, 1)
    em = nodes.new("ShaderNodeMath"); em.operation = 'MULTIPLY_ADD'; em.inputs[1].default_value = 0.35; em.inputs[2].default_value = 0.05
    links.new(k1.outputs[0], em.inputs[0]); links.new(em.outputs[0], p.inputs["Emission Strength"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.0004
    mx = nodes.new("ShaderNodeMath"); mx.operation = 'ADD'; links.new(nz.outputs["Fac"], mx.inputs[0]); links.new(vo.outputs["Distance"], mx.inputs[1])
    links.new(mx.outputs[0], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    return m


def key_m(m, node, f, v):
    n = m.node_tree.nodes[node]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)


def _interp(ctrl, steps=6):
    pts = catmull([c[:3] for c in ctrl], steps)
    n = len(pts); ctrl_n = len(ctrl)
    rl, rv = [], []
    for i in range(n):
        u = i / (n - 1) * (ctrl_n - 1); a = int(u); b = min(ctrl_n - 1, a + 1); t = u - a
        rl.append(ctrl[a][3] * (1 - t) + ctrl[b][3] * t); rv.append(ctrl[a][4] * (1 - t) + ctrl[b][4] * t)
    return pts, rl, rv


def build_airway(M_muc, seed=2):
    rng = random.Random(seed)
    pts, rl, rv = _interp(MAIN, 6)
    # start at the lips (drop the outside approach point from the mesh)
    skip = 6
    airway = tube("airway_main", pts[skip:], rl[skip:], [M_muc], 28, up=(0, 0, 1), ry=rv[skip:])
    cart = mat("cartilage", (0.86, 0.88, 0.9), rough=0.25, coat=0.6)
    bm = bmesh.new()
    zs = [0.595 - i * 0.0078 for i in range(16)]
    for z in zs:
        t = (0.60 - z) / 0.135; cx = 0.0 + 0.010 * t
        arc = [Vector((cx - 0.0098 * math.cos(a) * 1.02, 0.0098 * math.sin(a) * 1.02, z)) for a in [math.radians(-135 + 270 * i / 18) for i in range(19)]]
        arc = [Vector((cx + 0.0105 * math.cos(math.radians(a)), 0.0105 * math.sin(math.radians(a)), z)) for a in [30 + 300 * i / 22 for i in range(23)]]
        tube_bm(bm, arc, 0.0012, 6)
    rings = obj_from_bm("tracheal_rings", bm, [cart], smooth=True)
    # bronchial tree
    paths = []
    bmT = bmesh.new(); bmA = bmesh.new()
    lungc = {1: Vector((0.005, 0.07, 0.405)), -1: Vector((0.005, -0.07, 0.405))}
    main_path = [Vector(p) for p in pts]
    mr = rl[:]

    def grow(start, d, radius, length, depth, side, trail, rtrail):
        end = start + d.normalized() * length
        mid = (start + end) / 2 + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * length * 0.07
        cp = [start, mid, end]
        cat = catmull(cp, 3)
        rad = [radius * (1 - 0.18 * i / (len(cat) - 1)) for i in range(len(cat))]
        tube_bm(bmT, cat, rad, 10)
        trail2 = trail + cat[1:]; rtrail2 = rtrail + rad[1:]
        if depth >= 4:
            paths.append((trail2, rtrail2))
            for k in range(6):
                off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized() * 0.0025
                ellipsoid_bm(bmA, end + off + d.normalized() * 0.002, (0.0018, 0.0018, 0.0018), 10, 6)
            return
        for sgn in (1, -1):
            ax = d.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))).normalized()
            from mathutils import Quaternion
            nd = Quaternion(ax, math.radians(rng.uniform(25, 45)) * sgn) @ d.normalized()
            nd = (nd + (lungc[side] - end).normalized() * 0.45 + Vector((0, 0, -0.15))).normalized()
            grow(end, nd, radius * 0.74, length * 0.74, depth + 1, side, trail2, rtrail2)
    carina = Vector(MAIN[-1][:3])
    for side in (1, -1):
        d0 = Vector((0.15, side * 0.9, -0.42))
        grow(carina, d0, 0.0072, 0.055, 0, side, main_path, mr)
    bmesh.ops.recalc_face_normals(bmT, faces=bmT.faces); bmesh.ops.recalc_face_normals(bmA, faces=bmA.faces)
    tree = obj_from_bm("bronchial_tree", bmT, [M_muc], smooth=True)
    alv_m = mat("alveoli", (0.85, 0.45, 0.5), rough=0.3, coat=0.5)
    alv = obj_from_bm("alveoli", bmA, [alv_m], smooth=True)
    return {"main": airway, "rings": rings, "tree": tree, "alveoli": alv, "paths": paths, "main_pts": main_path, "main_r": mr}


def sample_path(pts, u):
    """u in 0..1 along arc-length."""
    L = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        L.append(L[-1] + (b - a).length)
    t = u * L[-1]
    i = 0
    while i < len(L) - 2 and L[i + 1] < t:
        i += 1
    k = (t - L[i]) / max(1e-9, L[i + 1] - L[i])
    return pts[i].lerp(pts[i + 1], k), i, L[-1]
