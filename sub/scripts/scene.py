"""Deep-sea submersible implosion short: model, underwater environment, cross-section and per-frame animation (all procedural)."""
import sys, os, math, json, random
sys.path.insert(0, "/home/user/Nikola123232/scripts"); sys.path.insert(0, "/home/user/Nikola123232/sub/scripts")
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
from f1.core import *
import util as U
from tl import *

random.seed(7); rng = np.random.default_rng(7)
sc = reset_scene()
SUBDIR = "/home/user/Nikola123232/sub"

# =============================================================================== helpers
def S(a, b, x): return np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
def nodes_of(m): m.use_nodes = True; return m.node_tree.nodes, m.node_tree.links
def N(nodes, t, **kw):
    n = nodes.new(t)
    for k, v in kw.items(): setattr(n, k, v)
    return n
def mathn(nodes, links, op, a, b=None, clamp=False):
    n = nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if hasattr(v, "node") or hasattr(v, "links"): links.new(v, n.inputs[i])
        else: n.inputs[i].default_value = v
    return n.outputs[0]
def get_arr(me):
    a = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", a); return a.reshape(-1, 3)
def set_arr(me, a): me.vertices.foreach_set("co", np.ascontiguousarray(a, np.float32).ravel()); me.update()
def add_rest_attr(me, arr):
    ca = me.color_attributes.new("rest", 'FLOAT_COLOR', 'POINT')
    rgba = np.ones((len(arr), 4), np.float32); rgba[:, :3] = arr
    ca.data.foreach_set("color", rgba.ravel())

# =============================================================================== materials
def hull_material():
    m = bpy.data.materials.new("hull"); nd, lk = nodes_of(m); p = nd["Principled BSDF"]
    at = N(nd, "ShaderNodeAttribute", attribute_name="rest", attribute_type='GEOMETRY')
    sep = N(nd, "ShaderNodeSeparateXYZ"); lk.new(at.outputs["Color"], sep.inputs[0]) if False else lk.new(at.outputs["Color"], sep.inputs[0])
    X, Y, Z = sep.outputs
    # panel seam lines: axial every 0.74 m, circumferential every 45 degrees
    fr = mathn(nd, lk, 'FRACT', mathn(nd, lk, 'ADD', mathn(nd, lk, 'DIVIDE', X, 0.74), 0.5))
    bx = mathn(nd, lk, 'ABSOLUTE', mathn(nd, lk, 'SUBTRACT', fr, 0.5))
    ang = mathn(nd, lk, 'ARCTAN2', Z, Y)
    fr2 = mathn(nd, lk, 'FRACT', mathn(nd, lk, 'ADD', mathn(nd, lk, 'DIVIDE', ang, math.pi / 4), 0.5))
    by = mathn(nd, lk, 'ABSOLUTE', mathn(nd, lk, 'SUBTRACT', fr2, 0.5))
    g1 = mathn(nd, lk, 'SUBTRACT', 1.0, mathn(nd, lk, 'SMOOTH_STEP' if False else 'MULTIPLY', mathn(nd, lk, 'MINIMUM', bx, 0.02), 50.0))   # 1 on the seam, 0 away
    g2 = mathn(nd, lk, 'SUBTRACT', 1.0, mathn(nd, lk, 'MULTIPLY', mathn(nd, lk, 'MINIMUM', by, 0.012), 83.0))
    seam = mathn(nd, lk, 'MAXIMUM', mathn(nd, lk, 'POWER', g1, 6.0), mathn(nd, lk, 'POWER', g2, 6.0))
    nz = N(nd, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 9; nz.inputs["Roughness"].default_value = 0.62
    lk.new(at.outputs["Color"], nz.inputs["Vector"])
    nz2 = N(nd, "ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 700; nz2.inputs["Detail"].default_value = 3
    lk.new(at.outputs["Color"], nz2.inputs["Vector"])
    stre = N(nd, "ShaderNodeTexNoise"); stre.inputs["Scale"].default_value = 5.0; stre.inputs["Detail"].default_value = 6
    mp = N(nd, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 7.0, 7.0)         # long axial streaks
    lk.new(at.outputs["Color"], mp.inputs[0]); lk.new(mp.outputs[0], stre.inputs["Vector"])
    dirt = mathn(nd, lk, 'MAXIMUM', mathn(nd, lk, 'MULTIPLY', mathn(nd, lk, 'SUBTRACT', stre.outputs["Fac"], 0.5), 2.2, True), mathn(nd, lk, 'MULTIPLY', seam, 0.8))
    dirt = mathn(nd, lk, 'MAXIMUM', dirt, mathn(nd, lk, 'MULTIPLY', mathn(nd, lk, 'SUBTRACT', nz.outputs["Fac"], 0.55), 1.8, True))
    mix = N(nd, "ShaderNodeMix", data_type='RGBA'); mix.inputs[6].default_value = (0.5, 0.53, 0.55, 1); mix.inputs[7].default_value = (0.09, 0.08, 0.065, 1)
    lk.new(dirt, mix.inputs[0]); lk.new(mix.outputs[2], p.inputs["Base Color"])
    rr = mathn(nd, lk, 'ADD', 0.34, mathn(nd, lk, 'MULTIPLY', dirt, 0.4)); lk.new(rr, p.inputs["Roughness"])
    p.inputs["Metallic"].default_value = 0.35; p.inputs["Coat Weight"].default_value = 0.35; p.inputs["Coat Roughness"].default_value = 0.25
    h = mathn(nd, lk, 'ADD', mathn(nd, lk, 'MULTIPLY', seam, -1.0), mathn(nd, lk, 'MULTIPLY', nz2.outputs["Fac"], 0.025))
    bp = N(nd, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.01
    lk.new(h, bp.inputs["Height"]); lk.new(bp.outputs[0], p.inputs["Normal"])
    return m

def alu_material(name, col=(0.55, 0.58, 0.62), rough=0.38, metal=0.9):
    m = mat(name, col, metal=metal, rough=rough); nd, lk = nodes_of(m); p = nd["Principled BSDF"]
    tc_ = N(nd, "ShaderNodeTexCoord"); nz = N(nd, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 8
    lk.new(tc_.outputs["Object"], nz.inputs["Vector"])
    rr = mathn(nd, lk, 'ADD', rough * 0.7, mathn(nd, lk, 'MULTIPLY', nz.outputs["Fac"], 0.5)); lk.new(rr, p.inputs["Roughness"])
    bp = N(nd, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; lk.new(nz.outputs["Fac"], bp.inputs["Height"]); lk.new(bp.outputs[0], p.inputs["Normal"])
    return m

MAT = {}
def build_materials():
    MAT["hull"] = hull_material()
    MAT["bolt"] = mat("bolt", (0.16, 0.16, 0.17), metal=1.0, rough=0.35)
    MAT["frame"] = alu_material("frame", (0.5, 0.53, 0.58), 0.42)
    MAT["dark"] = mat("darkmetal", (0.06, 0.065, 0.07), metal=0.8, rough=0.5)
    MAT["foam"] = mat("foam", (0.9, 0.28, 0.04), rough=0.85, spec=0.2)
    MAT["rubber"] = mat("rubber", (0.02, 0.02, 0.022), rough=0.7)
    MAT["pod"] = mat("pod", (0.85, 0.62, 0.08), rough=0.5, coat=0.3)
    MAT["acrylic"] = mat("acrylic", (0.75, 0.9, 1.0), rough=0.0, transmission=1.0, spec=0.6)
    MAT["acrylic"].node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.49
    MAT["cabin"] = emit_mat("cabin", (1.0, 0.62, 0.3), 1.6)
    MAT["lens"] = emit_mat("lens", (0.85, 0.95, 1.0), 25.0)
    MAT["strobe"] = emit_mat("strobe", (1.0, 0.05, 0.03), 0.0)
    MAT["part"] = mat("particle", (0.7, 0.8, 0.9), rough=0.6, emission=(0.5, 0.65, 0.9), estr=0.25)
    MAT["shard"] = mat("shard", (0.7, 0.72, 0.75), metal=0.6, rough=0.4)
    MAT["arrow"] = emit_mat("arrow", (0.2, 0.55, 1.0), 6.0)
    MAT["shock"] = None
    # pressure-wave shell: faint blue rim only
    m = bpy.data.materials.new("shock"); nd, lk = nodes_of(m); nd.clear(); out = N(nd, "ShaderNodeOutputMaterial")
    lw = N(nd, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.2
    em = N(nd, "ShaderNodeEmission"); em.inputs[0].default_value = (0.45, 0.75, 1.0, 1); em.inputs[1].default_value = 0.0; em.name = "SHOCK_E"
    tr = N(nd, "ShaderNodeBsdfTransparent"); mx = N(nd, "ShaderNodeMixShader")
    pw = mathn(nd, lk, 'POWER', lw.outputs["Facing"], 3.0)
    lk.new(pw, mx.inputs[0]); lk.new(em.outputs[0], mx.inputs[2]); lk.new(tr.outputs[0], mx.inputs[1]); lk.new(mx.outputs[0], out.inputs[0])
    MAT["shock"] = m

# =============================================================================== the submersible
R, LC, CAP = 0.95, 2.2, 0.80
STRUCT = []                 # (object, rest array, kind)   -- deformed vertex-by-vertex by the collapse field
RIGID = []                  # (object, centre, spin axis, drift dir, w, speed)   -- parts that tumble
SUB = None

def hull_profile():
    prof = []
    ribs = [(-0.62, 0.03, 0.045), (0.0, 0.025, 0.04), (0.62, 0.03, 0.045), (-LC / 2, 0.055, 0.06), (LC / 2, 0.055, 0.06)]
    for i in range(0, 25):
        phi = (math.pi / 2) * i / 24; prof.append((R * math.sin(phi) + 0.0004, -LC / 2 - CAP * math.cos(phi)))
    for i in range(1, 130):
        a = -LC / 2 + LC * i / 130; r = R
        for (ac, h, w) in ribs: r += h * math.exp(-((a - ac) / w) ** 2)
        prof.append((r, a))
    for i in range(0, 25):
        phi = (math.pi / 2) * (24 - i) / 24; prof.append((R * math.sin(phi) + 0.0004, LC / 2 + CAP * math.cos(phi)))
    return prof

def add_part(name, bm, mats, smooth=True, kind="struct"):
    o = obj_from_bm(name, bm, mats, smooth=smooth, parent=SUB)
    arr = get_arr(o.data)
    if name == "hull": add_rest_attr(o.data, arr)
    STRUCT.append((o, arr.copy(), kind)); return o

def superellipse(a, b, p, n, x0):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n; c, s = math.cos(t), math.sin(t)
        pts.append((x0, a * np.sign(c) * abs(c) ** (2 / p), b * np.sign(s) * abs(s) ** (2 / p)))
    return pts

def build_sub():
    global SUB
    SUB = empty("SUB", size=0.5)
    # --- pressure hull (+ bolts in the same object)
    bm = bmesh.new(); lathe_bm(bm, hull_profile(), segments=144, axis='X', matidx=0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0006)
    for xf in (-LC / 2, LC / 2):
        for k in range(56):
            a = 2 * math.pi * (k + 0.5) / 56; rr = R + 0.052
            c = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.016, radius2=0.013, depth=0.022)
            q = Quaternion((0, 0, 1), 0)
            d = Vector((0, math.cos(a), math.sin(a)))
            M = Matrix.Translation(Vector((xf + (0.0), rr * d.y, rr * d.z))) @ d.to_track_quat('Z', 'X').to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=M, verts=c["verts"])
            for f in {f for v in c["verts"] for f in v.link_faces}: f.material_index = 1
    add_part("hull", bm, [MAT["hull"], MAT["bolt"]])
    # --- viewport (acrylic dome in a titanium ring), cabin glow behind it
    bm = bmesh.new(); ellipsoid_bm(bm, (1.64, 0, 0), (0.48, 0.44, 0.44), seg=40, rings=24); add_part("dome", bm, [MAT["acrylic"]], kind="dome")
    bm = bmesh.new(); ellipsoid_bm(bm, (1.62, 0, 0), (0.40, 0.37, 0.37), seg=24, rings=14); add_part("cabin", bm, [MAT["cabin"]], kind="dome")
    bm = bmesh.new(); tube_bm(bm, superellipse(0.45, 0.45, 2.0, 48, 1.70), 0.034, n=10, matidx=0); add_part("vp_ring", bm, [MAT["frame"]], kind="dome")
    # --- external cage: three hoops, longitudinal rails, skids, braces
    bm = bmesh.new()
    xs = (-1.45, -0.25, 0.95)
    for x0 in xs: tube_bm(bm, superellipse(1.12, 1.15, 3.2, 44, x0), 0.042, n=10)
    for sy in (-1, 1):
        for sz in (-1, 1):
            tube_bm(bm, [(-1.75, sy * 0.90, sz * 0.93), (-1.45, sy * 0.90, sz * 0.93), (0.95, sy * 0.90, sz * 0.93), (1.45, sy * 0.72, sz * 0.80), (1.8, sy * 0.48, sz * 0.60)], 0.036, n=10)
    for sy in (-1, 1):                                                                         # skid rails
        tube_bm(bm, [(-1.85, sy * 0.88, -1.17), (1.45, sy * 0.88, -1.17), (1.85, sy * 0.62, -1.02), (2.0, sy * 0.45, -0.85)], 0.05, n=10)
        for x0 in (-1.45, 0.95): tube_bm(bm, [(x0, sy * 0.88, -1.17), (x0, sy * 0.9, -0.95)], 0.045, n=8)
        if sy > 0:
            tube_bm(bm, [(-1.45, sy * 1.05, -0.6), (-0.25, sy * 1.12, 0.4)], 0.03, n=8)           # diagonal braces (starboard side only)
            tube_bm(bm, [(-0.25, sy * 1.12, -0.4), (0.95, sy * 1.05, 0.55)], 0.03, n=8)
    for x0 in xs:                                                                              # hull standoffs
        for ang in (0.5, 2.6, 3.7, 5.8):
            tube_bm(bm, [(x0, 0.95 * math.cos(ang), 0.95 * math.sin(ang)), (x0, 1.09 * math.cos(ang), 1.12 * math.sin(ang))], 0.026, n=6)
    add_part("cage", bm, [MAT["frame"]])
    # --- foam, battery pods
    bm = bmesh.new(); box_bm(bm, (-0.15, 0, 1.2), (2.9, 1.0, 0.2)); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=True)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.012, segments=2, affect='EDGES') if False else None
    add_part("foam", bm, [MAT["foam"]], smooth=False, kind="foam")
    bm = bmesh.new()
    for sy in (-1, 1):
        prof = [(0.0004, -1.0)] + [(0.17 * math.sin(math.pi / 2 * i / 8), -0.8 - 0.2 * math.cos(math.pi / 2 * i / 8)) for i in range(8)] + [(0.17, 0.8)] + [(0.17 * math.sin(math.pi / 2 * (8 - i) / 8), 0.8 + 0.2 * math.cos(math.pi / 2 * (8 - i) / 8)) for i in range(1, 9)]
        lathe_bm(bm, prof, segments=24, axis='X', center=(-0.1, sy * 0.52, -1.02))
    add_part("pods", bm, [MAT["pod"]])
    # --- rigid parts: thrusters, lamps, strobe antenna
    def rigid(o, centre, w, spd, ax=(0, 0, 1)):
        d = Vector(centre); d.normalize() if d.length > 1e-6 else None
        RIGID.append(dict(obj=o, c=Vector(centre), w=w, spd=spd, ax=Vector(ax).normalized(), d=Vector((d.x, d.y, d.z)), rot0=tuple(o.rotation_euler)))
    def thruster(name, loc, axis):
        bm = bmesh.new()
        prof = [(0.215, -0.13), (0.235, -0.115), (0.235, 0.115), (0.2, 0.13), (0.18, 0.115), (0.18, -0.1), (0.2, -0.13)]
        lathe_bm(bm, prof, segments=36, axis='X', matidx=0)
        lathe_bm(bm, [(0.0004, -0.12), (0.075, -0.1), (0.075, 0.2), (0.0004, 0.24)], segments=18, axis='X', matidx=1)
        for k in range(4):
            a = k * math.pi / 2; d = Vector((0, math.cos(a), math.sin(a)))
            tube_bm(bm, [(-0.06, 0.07 * d.y, 0.07 * d.z), (-0.06, 0.19 * d.y, 0.19 * d.z)], 0.012, n=6, matidx=1)
        o = obj_from_bm(name, bm, [MAT["dark"], MAT["frame"]], parent=SUB)
        o.location = loc
        if axis == 'Z': o.rotation_euler = (0, math.radians(-90), 0)
        # propeller
        bm = bmesh.new()
        for k in range(4):
            a = k * math.pi / 2 + 0.3
            ellipsoid_bm(bm, (0.04, 0.12 * math.cos(a), 0.12 * math.sin(a)), (0.012, 0.085, 0.032), seg=10, rings=6, rot=Euler((a, 0.35, 0)).to_quaternion())
        po = obj_from_bm(name + "_prop", bm, [MAT["rubber"]], parent=o); po.location = (0.0, 0, 0)
        return o, po
    PROPS = []
    for nm, loc, ax in (("th_rl", (-1.78, -0.95, 0.0), 'X'), ("th_rr", (-1.78, 0.95, 0.0), 'X'), ("th_vl", (-0.1, -1.2, 0.5), 'Z'), ("th_vr", (-0.1, 1.2, 0.5), 'Z')):
        o, po = thruster(nm, loc, ax); PROPS.append(po); rigid(o, loc, 1.6, 1.2, (0, 1, 0))
    LAMPS = []
    for k, (lx, ly, lz) in enumerate(((1.55, -0.78, 0.62), (1.55, 0.78, 0.62), (1.55, -0.78, -0.62), (1.55, 0.78, -0.62))):
        bm = bmesh.new(); lathe_bm(bm, [(0.0004, -0.07), (0.075, -0.06), (0.085, 0.06), (0.0004, 0.07)], segments=20, axis='X', matidx=0)
        lathe_bm(bm, [(0.0004, 0.075), (0.06, 0.072)], segments=20, axis='X', matidx=1)
        o = obj_from_bm(f"lamp{k}", bm, [MAT["dark"], MAT["lens"]], parent=SUB); o.location = (lx, ly, lz); o.rotation_euler = (0, 0, math.radians(8 * (1 if ly > 0 else -1)))
        L_ = light(f"lampL{k}", 'SPOT', (lx + 0.1, ly, lz), (0, 0, 0), energy=900, size=0.05, color=(0.82, 0.93, 1.0), parent=SUB, target=(lx + 6.0, ly * 1.5, lz * 1.1))
        L_.data.spot_size = math.radians(58); L_.data.spot_blend = 0.55; LAMPS.append(L_)
        rigid(o, (lx, ly, lz), 2.0, 1.6)
    bm = bmesh.new(); tube_bm(bm, [(0, 0, 0), (0, 0, 0.62)], 0.014, n=8, matidx=0); ellipsoid_bm(bm, (0, 0, 0.66), (0.04, 0.04, 0.04), seg=12, rings=8, matidx=1)
    ant = obj_from_bm("antenna", bm, [MAT["dark"], MAT["strobe"]], parent=SUB); ant.location = (-1.0, 0.0, 1.30); rigid(ant, (-1.0, 0, 1.3), 1.0, 0.8, (1, 0, 0))
    return PROPS, LAMPS, ant

# =============================================================================== deformation field
X0 = 0.35                      # origin of the buckle
PD = Vector((X0, -0.94 * 0.995, 0.14))
VC, TAU = 55.0, 0.035

def deform_points(P, dent_d, tcol):
    x, y, z = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    r = np.hypot(y, z)
    if dent_d > 1e-4:
        n0 = np.array([0.0, -0.99, 0.14]); n0 /= np.linalg.norm(n0)
        dx = (x - PD.x) / 0.42; dp = np.sqrt(((y - PD.y) ** 2 + (z - PD.z) ** 2)) / 0.30
        w = np.exp(-(dx ** 2 + dp ** 2)) * np.clip((1.12 - r) / 0.12, 0, 1)
        ripple = 1.0 + 0.18 * np.cos(11.0 * np.arctan2(z - PD.z, y - PD.y)) * np.exp(-dp ** 2 * 0.5)
        amt = dent_d * w * ripple
        y -= n0[1] * amt; z -= n0[2] * amt
    if tcol is not None:
        g = S(0, 1, (tcol - np.abs(x - X0) / VC) / TAU)
        fz = 0.92 - 0.38 * S(1.0, 1.25, r)
        z2 = z * (1 - fz * g)
        y2 = y * (1 + 0.14 * g)
        cx = X0 + (x - X0) * (1 - 0.15 * g)
        nzx = np.sin(9 * x + 2.1) * np.cos(11 * y + 1.3) + np.sin(13 * z + 0.7) * np.cos(7 * x)
        nzy = np.sin(8 * x + 0.3) * np.cos(12 * z + 2.2) + np.cos(10 * y + 0.9)
        nzz = np.cos(11 * x + 1.7) * np.sin(9 * y + 0.4) + np.sin(6 * z + 1.1)
        amp = 0.085 * g * (1 - 0.35 * g)
        x, y, z = cx + amp * 0.5 * nzx, y2 + amp * nzy, z2 + amp * nzz * 0.8
    return np.stack([x, y, z], 1)

def deform_one(p, dent_d, tcol): return deform_points(np.array([p], np.float32), dent_d, tcol)[0]

# =============================================================================== particles / debris (numpy-driven meshes)
class Swarm:
    def __init__(self, name, n, tmpl, mat_, parent=None):
        self.n = n; self.t = np.array(tmpl, np.float32); k = len(self.t)
        faces = []
        self.tf = None
        return_faces = []
        self.name = name; self.k = k
        me = bpy.data.meshes.new(name)
        self.fa = tmpl_faces(k)
        verts = np.zeros((n * k, 3), np.float32)
        faces = [tuple(int(i) + j * k for i in fc) for j in range(n) for fc in self.fa]
        me.from_pydata(verts.tolist(), [], faces); me.update()
        for p_ in me.polygons: p_.use_smooth = False
        me.materials.append(mat_)
        self.obj = bpy.data.objects.new(name, me); link(self.obj); self.me = me
    def set(self, c, s, Rm=None):
        t = self.t[None] * (s[:, None, :] if s.ndim == 2 else s[:, None, None])
        if Rm is not None: t = np.einsum("nij,nkj->nki", Rm, t)
        set_arr(self.me, (c[:, None, :] + t).reshape(-1, 3))
OCT = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
OCT_F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
BOXT = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
BOX_F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
def tmpl_faces(k): return OCT_F if k == 6 else BOX_F
def rot_mats(ax, ang):
    ax = ax / np.linalg.norm(ax, axis=1, keepdims=True); c, s = np.cos(ang), np.sin(ang); x, y, z = ax.T; C = 1 - c
    return np.stack([np.stack([c + x * x * C, x * y * C - z * s, x * z * C + y * s], 1),
                     np.stack([y * x * C + z * s, c + y * y * C, y * z * C - x * s], 1),
                     np.stack([z * x * C - y * s, z * y * C + x * s, c + z * z * C], 1)], 1)

# =============================================================================== cross-section model (separate location)
XS = None
def build_xs():
    global XS
    root = empty("XS", loc=XS_ORIGIN, size=0.5)
    NT, NR, NX = 192, 4, 2                  # around, radial layers (rho levels), ends
    rho = np.array([0.0, 0.33, 0.66, 1.0])  # wall thickness fractions: liner, composite, outer coat
    RI, RO = 0.84, 0.97; L = 0.55
    verts, faces, mats = [], [], []
    def vid(t, k, e): return ((e * NR + k) * NT + (t % NT))
    for e, xx in enumerate((-L / 2, L / 2)):
        for k in range(NR):
            for t in range(NT): verts.append((xx, 0, 0))
    for e in range(NX):
        for k in range(NR - 1):
            for t in range(NT): faces.append((vid(t, k, e), vid(t + 1, k, e), vid(t + 1, k + 1, e), vid(t, k + 1, e))); mats.append(k)       # cut faces, 3 bands
    for k, mi in ((0, 3), (NR - 1, 4)):                                                    # inner/outer surfaces
        for t in range(NT): faces.append((vid(t, k, 0), vid(t + 1, k, 0), vid(t + 1, k, 1), vid(t, k, 1))); mats.append(mi)
    me = bpy.data.meshes.new("xs"); me.from_pydata(verts, [], faces); me.update()
    cut = [mat("xs_liner", (0.85, 0.87, 0.9), rough=0.4, metal=0.0), mat("xs_comp", (0.045, 0.05, 0.06), rough=0.3, metal=0.0, spec=0.7), mat("xs_coat", (0.9, 0.9, 0.92), rough=0.45), mat("xs_in", (0.05, 0.045, 0.04), rough=0.6), mat("xs_out", (0.55, 0.57, 0.6), metal=0.7, rough=0.35)]
    # stress overlay: emission driven by a "stress" point attribute (red at the lobes)
    sa = me.color_attributes.new("stress", 'FLOAT_COLOR', 'POINT')
    for m_ in cut[0:5]:
        nd, lk = nodes_of(m_); p = nd["Principled BSDF"]; at = N(nd, "ShaderNodeAttribute", attribute_name="stress", attribute_type='GEOMETRY')
        lk.new(at.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Color"].default_value = (1, 0.1, 0.03, 1)
        sep = N(nd, "ShaderNodeSeparateColor"); lk.new(at.outputs["Color"], sep.inputs[0]); lk.new(mathn(nd, lk, 'MULTIPLY', sep.outputs[0], 2.5), p.inputs["Emission Strength"])
        em = N(nd, "ShaderNodeMix", data_type='RGBA'); em.inputs[7].default_value = (1.0, 0.16, 0.04, 1); em.inputs[6].default_value = (0, 0, 0, 1); lk.new(sep.outputs[0], em.inputs[0]); lk.new(em.outputs[2], p.inputs["Emission Color"])
    for m_ in cut: me.materials.append(m_)
    for i, pl in enumerate(me.polygons): pl.material_index = mats[i]; pl.use_smooth = (mats[i] >= 3)
    o = bpy.data.objects.new("xs_ring", me); link(o); o.parent = root
    # backdrop with a faint grid, floor glow
    bm = bmesh.new(); box_bm(bm, (3.5, 0, 0), (0.05, 14, 14)); bd = obj_from_bm("xs_back", bm, [], parent=root); bd.location = (0, 0, 0)
    bm_ = bpy.data.materials.new("xs_bg"); nd, lk = nodes_of(bm_); nd.clear(); out = N(nd, "ShaderNodeOutputMaterial"); em = N(nd, "ShaderNodeEmission")
    tcn = N(nd, "ShaderNodeTexCoord"); sepx = N(nd, "ShaderNodeSeparateXYZ"); lk.new(tcn.outputs["Object"], sepx.inputs[0])
    def gridline(v, step):
        fr = mathn(nd, lk, 'FRACT', mathn(nd, lk, 'ADD', mathn(nd, lk, 'DIVIDE', v, step), 0.5)); b = mathn(nd, lk, 'ABSOLUTE', mathn(nd, lk, 'SUBTRACT', fr, 0.5))
        return mathn(nd, lk, 'SUBTRACT', 1.0, mathn(nd, lk, 'MULTIPLY', mathn(nd, lk, 'MINIMUM', b, 0.012), 83.0))
    gl = mathn(nd, lk, 'MAXIMUM', mathn(nd, lk, 'POWER', gridline(sepx.outputs[1], 0.5), 8.0), mathn(nd, lk, 'POWER', gridline(sepx.outputs[2], 0.5), 8.0))
    rad = mathn(nd, lk, 'DIVIDE', mathn(nd, lk, 'ADD', mathn(nd, lk, 'MULTIPLY', sepx.outputs[1], sepx.outputs[1]), mathn(nd, lk, 'MULTIPLY', sepx.outputs[2], sepx.outputs[2])), 36.0)
    base = mathn(nd, lk, 'MULTIPLY', mathn(nd, lk, 'SUBTRACT', 1.0, mathn(nd, lk, 'MINIMUM', rad, 1.0)), 0.9)
    mx = N(nd, "ShaderNodeMix", data_type='RGBA'); mx.inputs[6].default_value = (0.002, 0.006, 0.014, 1); mx.inputs[7].default_value = (0.02, 0.06, 0.1, 1); lk.new(base, mx.inputs[0])
    gmix = N(nd, "ShaderNodeMix", data_type='RGBA'); lk.new(mx.outputs[2], gmix.inputs[6]); gmix.inputs[7].default_value = (0.05, 0.16, 0.26, 1); lk.new(mathn(nd, lk, 'MULTIPLY', gl, 0.22), gmix.inputs[0])
    lk.new(gmix.outputs[2], em.inputs[0]); em.inputs[1].default_value = 1.0; lk.new(em.outputs[0], out.inputs[0]); bd.data.materials.append(bm_)
    # arrows: external (blue, inward) / internal (orange, outward)
    arr_m = emit_mat("xs_arr_out", (0.12, 0.45, 1.0), 1.6); arr_i = emit_mat("xs_arr_in", (1.0, 0.45, 0.08), 1.8)
    def arrow_bm(bm, ln, rs, rc):
        c = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=rc, radius2=0.0, depth=ln * 0.35)
        bmesh.ops.translate(bm, vec=(0, 0, ln * 0.35 / 2 + ln * 0.65), verts=c["verts"])
        c2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=rs, radius2=rs, depth=ln * 0.65)
        bmesh.ops.translate(bm, vec=(0, 0, ln * 0.65 / 2), verts=c2["verts"])
    ext, inn = [], []
    for k in range(22):
        bm = bmesh.new(); arrow_bm(bm, 0.75, 0.03, 0.085); o_ = obj_from_bm(f"ax{k}", bm, [arr_m], parent=root); ext.append(o_)
    for k in range(10):
        bm = bmesh.new(); arrow_bm(bm, 0.30, 0.012, 0.035); o_ = obj_from_bm(f"ai{k}", bm, [arr_i], parent=root); inn.append(o_)
    XS = dict(root=root, me=me, NT=NT, NR=NR, NX=NX, rho=rho, RI=RI, RO=RO, L=L, ext=ext, inn=inn, ring=o)

def xs_state(f):
    """buckle amplitude of the cross-section (0..1) and pressure arrow phase."""
    u = (f - 436) / (624 - 436)
    a = 0.012 + 0.05 * sstep(0.0, 0.55, u) + 0.20 * sstep(0.55, 0.95, u) ** 1.6 + 0.25 * sstep(0.93, 1.0, u)
    return a

def xs_apply(f):
    X = XS; NT, NR, NX = X["NT"], X["NR"], X["NX"]; a = xs_state(f)
    th = np.linspace(0, 2 * np.pi, NT, endpoint=False)
    n = 3; phi = 0.4
    out = np.zeros((NX * NR * NT, 3), np.float32); st = np.zeros(out.shape[0], np.float32)
    for e, xx in enumerate((-X["L"] / 2, X["L"] / 2)):
        for k in range(NR):
            rr = X["RI"] + (X["RO"] - X["RI"]) * X["rho"][k]
            lobe = np.cos(n * th + phi)
            rd = rr * (1 - a * lobe * (0.9 + 0.1 * np.cos(2 * th))) - 0.0
            # axial wave on the far end: a slightly different amplitude -> shows depth
            rd = rd * (1 - 0.02 * a * (1 if e else -1))
            i0 = (e * NR + k) * NT
            out[i0:i0 + NT] = np.stack([np.full(NT, xx), rd * np.cos(th), rd * np.sin(th)], 1)
            st[i0:i0 + NT] = np.clip(a * 1.6 * np.maximum(0, -lobe) * 1.1 - 0.12, 0, 1) * (0.2 + 0.8 * (k / (NR - 1)))
    set_arr(X["me"], out)
    ca = X["me"].color_attributes["stress"]; rgba = np.zeros((len(st), 4), np.float32); rgba[:, 0] = st; rgba[:, 3] = 1; ca.data.foreach_set("color", rgba.ravel())
    # arrows
    t = f / 30.0; ph = (t * 0.9) % 1.0
    vis_ext = sstep(436, 452, f)
    for k, o in enumerate(X["ext"]):
        ang = 2 * math.pi * k / len(X["ext"]); sck = vis_ext * 0.9; rloc = (1.55 - 0.45 * ((ph + k * 0.37) % 1.0)) + 0.75 * sck
        th_k = ang; local_r = np.interp(ang, np.append(th, 2 * np.pi), np.append(1 - a * np.cos(n * th + phi), 1 - a * np.cos(n * 2 * np.pi + phi)))
        rr = max(rloc, local_r * X["RO"] + 0.14) if False else rloc
        d = Vector((0, math.cos(ang), math.sin(ang)))
        o.location = (0.0, rr * d.y, rr * d.z)
        o.rotation_euler = d.to_track_quat('-Z', 'X').to_euler() if False else (Vector((0, 0, 1)).rotation_difference(-d)).to_euler()
        o.scale = (max(1e-3, sck),) * 3
    vi = sstep(450, 466, f)
    for k, o in enumerate(X["inn"]):
        ang = 2 * math.pi * (k + 0.5) / len(X["inn"]); rr = 0.12 + 0.34 * ((ph + k * 0.21) % 1.0)
        d = Vector((0, math.cos(ang), math.sin(ang))); o.location = (0.0, rr * d.y, rr * d.z); o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler(); o.scale = (vi,) * 3

# =============================================================================== environment
def build_env():
    w = bpy.data.worlds.new("deep"); sc.world = w; nd, lk = nodes_of(w); bg = nd["Background"]; bg.inputs[0].default_value = (0.0015, 0.005, 0.011, 1); bg.inputs[1].default_value = 1.0
    # water volume (limited region so the cross-section stays clean)
    bm = bmesh.new(); box_bm(bm, (0, 0, 0), (140, 140, 140)); wv = obj_from_bm("water", bm, [], smooth=False)
    m = bpy.data.materials.new("water_vol"); nd, lk = nodes_of(m); nd.clear(); out = N(nd, "ShaderNodeOutputMaterial"); pv = N(nd, "ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.35, 0.6, 0.85, 1); pv.inputs["Density"].default_value = 0.03; pv.inputs["Anisotropy"].default_value = 0.55; pv.name = "WATER"
    lk.new(pv.outputs[0], out.inputs["Volume"]); wv.data.materials.append(m); wv.visible_shadow = False
    sc.cycles.volume_step_rate = 1.5; sc.cycles.volume_max_steps = 160; sc.cycles.volume_preview_step_rate = 1.0
    return wv

# =============================================================================== build everything
build_materials()
PROPS, LAMPS, ANT = build_sub()
WV = build_env()
build_xs()
# camera + rig light
CAM = U.shot_camera("cam", 1, lens=35); sc.camera = CAM
RIG = light("rig", 'SPOT', (0, 0, 0), (0, 0, 0), energy=300, size=0.08, color=(0.78, 0.9, 1.0)); RIG.data.spot_size = math.radians(75); RIG.data.spot_blend = 0.9
KEY_XS = light("xs_key", 'AREA', (1000 - 3.0, -2.5, 3.5), energy=240, size=3.0, color=(0.9, 0.95, 1.0), target=(1000, 0, 0))
RIM_XS = light("xs_rim", 'AREA', (1000 - 1.5, 3.0, -2.2), energy=120, size=2.5, color=(0.45, 0.7, 1.0), target=(1000, 0, 0))
FILL_XS = light("xs_fill", 'AREA', (1000 - 4.0, -0.5, -3.0), energy=45, size=3.0, color=(0.5, 0.65, 0.9), target=(1000, 0, 0))
RAKE = light("rake", 'SPOT', (-0.95, -1.40, 0.62), (0, 0, 0), energy=0, size=0.12, color=(0.75, 0.88, 1.0), target=(0.35, -0.95, 0.1)); RAKE.data.spot_size = math.radians(40); RAKE.data.spot_blend = 0.7
AMB = light("ambient", 'AREA', (0, -9, 6), energy=40, size=14, color=(0.35, 0.55, 1.0), target=(0, 0, 0))      # barely-there deep-blue fill

NEAR = Swarm("snow_near", 900, OCT, MAT["part"]); FAR = Swarm("snow_far", 1100, OCT, MAT["part"])
CLOUD = Swarm("cloud", 1600, OCT, MAT["part"]); SHARDS = Swarm("shards", 70, BOXT, MAT["shard"])
BASE_N = rng.uniform(-1, 1, (900, 3)).astype(np.float32); BASE_F = rng.uniform(-1, 1, (1100, 3)).astype(np.float32)
SZ_N = rng.uniform(0.004, 0.016, 900).astype(np.float32); SZ_F = rng.uniform(0.01, 0.035, 1100).astype(np.float32)
DRIFT_N = (rng.normal(0, 1, (900, 3)) * np.array([0.03, 0.03, 0.04])).astype(np.float32); DRIFT_F = (rng.normal(0, 1, (1100, 3)) * 0.02).astype(np.float32)
# collapse debris
CP = []
for i in range(1600):
    x = rng.uniform(-1.7, 1.7); a = rng.uniform(0, 2 * np.pi); r = 0.95 * np.sqrt(rng.uniform(0, 1))
    CP.append((x, r * np.cos(a), r * np.sin(a)))
CP = np.array(CP, np.float32); CV = rng.normal(0, 1, (1600, 3)).astype(np.float32); CV[:, 0] *= 0.7
CSZ = rng.uniform(0.006, 0.03, 1600).astype(np.float32); CT = rng.uniform(0.0, 0.07, 1600).astype(np.float32)
SP = []
for i in range(70):
    x = rng.uniform(-1.7, 1.7); a = rng.uniform(0, 2 * np.pi); SP.append((x, 1.0 * np.cos(a), 1.0 * np.sin(a)))
SP = np.array(SP, np.float32); SSZ = rng.uniform(0.04, 0.14, (70, 3)).astype(np.float32) * np.array([1.0, 1.0, 0.1], np.float32)
SAX = rng.normal(0, 1, (70, 3)).astype(np.float32); SW = rng.uniform(0.5, 3.0, 70).astype(np.float32); SV = rng.normal(0, 1, (70, 3)).astype(np.float32)
# pressure-wave shell
bm = bmesh.new(); ellipsoid_bm(bm, (0, 0, 0), (1, 1, 1), seg=48, rings=24); SHOCK = obj_from_bm("shock", bm, [MAT["shock"]], parent=None); SHOCK.visible_shadow = False
# pressure arrows around the hull (descent): one small object per arrow
ARR_N = 24; ARROWS = []; ARR_DIR = []
for k in range(ARR_N):
    xs_ = (-1.2, -0.45, 0.35, 1.05)[k % 4]; ang = 2 * math.pi * (k // 4) / 6 + (k % 4) * 0.5
    d = Vector((0, math.cos(ang), math.sin(ang))); ARR_DIR.append((xs_, d))
    bm = bmesh.new()
    c1 = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.06, radius2=0.0, depth=0.16); bmesh.ops.translate(bm, vec=(0, 0, -0.08), verts=c1["verts"])
    c2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.014, radius2=0.014, depth=0.30); bmesh.ops.translate(bm, vec=(0, 0, -0.31), verts=c2["verts"])
    o = obj_from_bm(f"parrow{k}", bm, [MAT["arrow"]], parent=SUB); o.rotation_euler = Vector((0, 0, 1)).rotation_difference(-d).to_euler(); ARROWS.append(o)
STRUCT_RESTS = [(o, a) for (o, a, k) in STRUCT]
for r_ in RIGID: pass
U.setup(sc, "main", samples=int(os.environ.get("SPP", 24)), bounces=6, res=(720, 1280), motion_blur=False)
sc.cycles.volume_bounces = 0

# =============================================================================== camera plans
def lerp(a, b, t): return a + (b - a) * t
def V3(*a): return Vector(a)
def cam_plan(f):
    """returns (loc, target, lens, fstop, focus) in WORLD space."""
    sub_loc, sub_rot = sub_pose(f)
    if f <= T["h1"][1]:
        u = (f - 1) / 131.0; e = u
        loc = V3(lerp(-0.08, 0.46, e), lerp(-1.62, -1.52, e), lerp(0.30, 0.26, e)); tg = V3(loc.x + lerp(0.20, 0.0, e), -0.93, lerp(0.14, 0.12, e))
        return loc, tg, 60, 3.2, (tg - loc).length
    if f <= T["h2"][1]:
        if f <= 150: loc = V3(0.42, -1.50, 0.26) + V3(0.0, -0.01, 0.0) * (f - 132); tg = V3(0.42, -0.93, 0.12); return loc, tg, 60, 3.2, (tg - loc).length
        u = sstep(150, 249, f)
        loc = V3(lerp(0.42, 0.5, u), lerp(-1.52, -8.0, u ** 0.8 if False else 1 - (1 - u) ** 2.2), lerp(0.26, 1.2, u)); tg = V3(lerp(0.42, 0.1, u), lerp(-0.93, 0, u), lerp(0.12, 0.0, u))
        lens = lerp(60, 35, u); return loc, tg, lens, lerp(3.2, 8.0, u), (tg - loc).length
    if f <= T["desc"][1]:
        u = (f - 250) / 185.0; c = sub_loc
        loc = c + V3(lerp(-0.6, 1.2, u), lerp(-7.6, -6.9, u), lerp(0.8, 0.2, u)); tg = c + V3(0.1, 0, lerp(0.0, -0.1, u))
        return loc, tg, 35, 8.0, (tg - loc).length
    if f <= T["xs"][1]:
        u = (f - 436) / 188.0; o = V3(*XS_ORIGIN)
        a = math.radians(lerp(38, 18, u)); d = lerp(4.6, 3.7, u)
        loc = o + V3(-d * math.cos(a) * 0.9, -d * math.sin(a) * 0.9 + lerp(-0.6, 0.2, u), 0.35); tg = o + V3(0, 0, 0.0)
        return loc, tg, 38, 8.0, (tg - loc).length
    if f <= F_REAL_END:
        u = (f - 625) / 75.0
        loc = V3(lerp(1.2, 0.9, u), lerp(-8.6, -7.8, u), lerp(0.9, 0.7, u)); tg = V3(0.1, 0, 0)
        return loc, tg, 35, 8.0, (tg - loc).length
    if f <= F_REPLAY[1]:
        u = (f - 701) / 80.0
        loc = V3(lerp(-2.9, -1.6, u), lerp(-4.7, -4.2, u), lerp(1.4, 0.6, u)); tg = V3(lerp(0.2, 0.35, u), 0, 0.0)
        return loc, tg, 35, 6.0, (tg - loc).length
    u = (f - 782) / 328.0
    c = sub_loc
    if u < 0.72:
        k = u / 0.72; loc = c + V3(lerp(1.3, -2.4, k), lerp(-3.2, -3.6, k), lerp(0.5, -0.4, k)); tg = c + V3(lerp(-0.6, 0.2, k), 0, lerp(-0.2, 0.0, k))
    else:
        k = sstep(0.72, 1.0, u); loc = c + V3(lerp(-2.4, 2.0, k), lerp(-3.6, -15.0, k), lerp(-0.4, 1.2, k)); tg = c + V3(lerp(0.2, 0.0, k), 0, lerp(0.0, -0.4, k))
    return loc, tg, 35, 6.0, (tg - loc).length

def sub_pose(f):
    """world position and euler of the submersible."""
    t = tc(f)
    if f < 250 or t is None and f < 625: return V3(0, 0, 0), (0, 0, 0)
    if f <= T["desc"][1]:
        u = (f - 250) / 185.0
        return V3(0, 0, -1.7 * (f - 250) / 30.0), (math.radians(4 * math.sin(u * 3.0)), math.radians(14 + 5 * u), 0)
    if f < 625: return V3(0, 0, 0), (0, 0, 0)
    if t is None: return V3(0, 0, 0), (0, 0, 0)
    # after the collapse the wreck sinks, tumbling slowly
    tt = max(0.0, t - 0.1)
    return V3(0.0, 0.0, -0.35 * tt), (math.radians(8 * tt), math.radians(6 * tt), math.radians(10 * tt))

# =============================================================================== per-frame apply
EVT = None
def apply(f):
    f = int(f); scn = scene_of(f); t = tw(f); tcol = tc(f); dd = dent(f)
    in_xs = scn == "xs"
    # ---- sub pose + structure
    sl, sr = sub_pose(f); SUB.location = sl; SUB.rotation_euler = sr
    SUB.hide_render = in_xs
    if not in_xs:
        for (o, rest, kind) in STRUCT: set_arr(o.data, deform_points(rest, dd, tcol))
    # rigid parts (thrusters, lamps, antenna) follow the field and tumble apart after the collapse
    for r_ in RIGID:
        c = deform_one(np.array(r_["c"], np.float32), dd, tcol); o = r_["obj"]; r0 = r_["rot0"]
        if tcol is None: o.location = Vector(c); o.rotation_euler = r0
        else:
            k = 1 - math.exp(-tcol * 2.2); o.location = Vector(c) + r_["d"] * r_["spd"] * 0.6 * k; w = r_["w"] * tcol * 1.4; ax = r_["ax"]
            o.rotation_euler = (r0[0] + w * ax.x + 0.3 * w, r0[1] + w * ax.y, r0[2] + w * ax.z)
    # propellers spin until the collapse
    for p_ in PROPS: p_.rotation_euler = (0.0 if tcol is not None else (f * 0.9) % 6.283, 0, 0)
    alive = 1.0
    if tcol is not None: alive = max(0.0, 1.0 - tcol * 18.0) if tcol < 0.12 else 0.0
    flick = 1.0
    if 662 <= f < 689: flick = 0.65 + 0.35 * (1 if (f * 7 % 5) > 1 else 0.2)
    for L_ in LAMPS: L_.data.energy = 900 * alive * flick * (1.0 if scn not in ("h1", "h2") else 0.3)
    MAT["lens"].node_tree.nodes["Emission"].inputs[1].default_value = 25.0 * alive * flick
    MAT["cabin"].node_tree.nodes["Emission"].inputs[1].default_value = 1.6 * (1.0 if tcol is None else max(0.0, 1 - tcol * 15))
    MAT["strobe"].node_tree.nodes["Emission"].inputs[1].default_value = (18.0 if (f % 30) < 6 and tcol is None else 0.0)
    # ---- arrows (descent)
    show = 250 <= f <= 435
    ph = (f / 30.0 * 0.8) % 1.0; fade = sstep(262, 282, f) * (1 - sstep(418, 435, f)) if show else 0.0
    for k, o in enumerate(ARROWS):
        xs_, d = ARR_DIR[k]; off = 0.1 + 0.5 * (1 - ((ph + k * 0.17) % 1.0)); o.location = Vector((xs_, 0, 0)) + d * (1.05 + off); o.scale = (max(1e-3, fade),) * 3; o.hide_render = not show
    MAT["arrow"].node_tree.nodes["Emission"].inputs[1].default_value = 1.2
    # ---- particles
    c_ = np.array(sl, np.float32)
    def wrap(base, size, drift, box):
        p = base * (box / 2) + drift * t; rel = p - c_; rel = (rel + box / 2) % box - box / 2; return c_ + rel
    NEAR.set(wrap(BASE_N, 0, DRIFT_N, 4.6), SZ_N); FAR.set(wrap(BASE_F, 0, DRIFT_F, 26.0), SZ_F)
    if tcol is None:
        CLOUD.set(np.zeros((1600, 3), np.float32) + 1e4, np.zeros(1600, np.float32)); SHARDS.set(np.zeros((70, 3), np.float32) + 1e4, np.ones((70, 3), np.float32) * 1e-4)
        SHOCK.scale = (1e-3,) * 3; SHOCK.hide_render = True
    else:
        tt = np.maximum(0.0, tcol - CT)
        tau = 0.45; disp = CV * (1.8 * tau * (1 - np.exp(-tt / tau)))[:, None] + CV * 0.12 * np.maximum(0, tcol - 0.3)  # fast burst that quickly slows (no fireball)
        pos = CP + disp
        shrink = (S(0, 0.04, tt) * (1.0 - 0.6 * S(1.0, 4.0, tcol))).astype(np.float32)
        CLOUD.set(np.array(sl, np.float32) + pos, CSZ * shrink)
        # shards: pulled inwards during the collapse, then drifting
        gs = S(0, 1, (tcol - np.abs(SP[:, 0] - X0) / VC) / TAU)
        inw = 1 - 0.8 * gs[:, None]; cs = SP * np.array([1.0, 1.0, 1.0]) * np.stack([np.ones_like(gs), inw[:, 0], inw[:, 0]], 1)
        outv = SV * np.float32(0.22 * (1 - math.exp(-max(0.0, tcol - 0.06) * 1.4)) + 0.03 * max(0.0, tcol - 1))
        Rm = rot_mats(SAX, SW * tcol * 1.3)
        SHARDS.set(np.array(sl, np.float32) + cs + outv, SSZ * np.float32(1.0), Rm)
        SHOCK.hide_render = False; SHOCK.location = sl + Vector((X0, 0, 0)); rad = 0.9 + 12.0 * min(tcol, 0.3) ** 0.8; SHOCK.scale = (rad,) * 3
        MAT["shock"].node_tree.nodes["SHOCK_E"].inputs[1].default_value = 0.35 * max(0.0, 1 - tcol / 0.22) * float(S(0, 0.01, tcol))
    # ---- cross section
    for o in [XS["ring"]] + XS["ext"] + XS["inn"]: o.hide_render = not in_xs
    if in_xs: xs_apply(f)
    # ---- camera + lights
    loc, tg, lens, fs, fd = cam_plan(f)
    CAM.location = loc; CAM.rotation_euler = look_at_rot(loc, tg); CAM.data.lens = lens
    CAM.data.dof.use_dof = scn in ("h1", "h2"); CAM.data.dof.aperture_fstop = fs; CAM.data.dof.focus_distance = max(0.05, fd * (0.97 if scn == "h1" else 1.0))
    RIG.location = loc + CAM.matrix_world.to_3x3() @ Vector((0.0, 0.0, 0.0)); RIG.rotation_euler = CAM.rotation_euler
    K = {"h1": 9.0, "h2": 9.0, "desc": 4.5, "xs": 0.0, "imp": 1.0, "aft": 6.0}[scn]
    RIG.data.energy = min(K * max(0.3, fd) ** 2, 220.0)
    if scn == "aft": RIG.data.energy *= (1 - 0.88 * sstep(0.74, 1.0, (f - 782) / 328.0))
    RAKE.data.energy = (38.0 if f <= 150 else 38.0 * (1 - sstep(150, 175, f))) if scn in ("h1", "h2") else 0.0
    AMB.data.energy = 0.0 if in_xs else {"h1": 22, "h2": 40, "desc": 60, "imp": 60, "aft": 18}[scn]
    dens = 0.03 if scn != "desc" else lerp(0.026, 0.05, (f - 250) / 185.0)
    WV.hide_render = in_xs
    for n_ in ("WATER",): [m for m in WV.data.materials][0].node_tree.nodes[n_].inputs["Density"].default_value = dens
    for L_ in (KEY_XS, RIM_XS, FILL_XS): L_.hide_render = not in_xs
    sc.camera = CAM
    # anchors for compositor labels (cross-section)
    if in_xs: ANCH[f] = dict(ext=[proj(Vector(XS_ORIGIN) + XS['ext'][k].location + Vector(-XS['ext'][k].location.normalized()) * 0.0 * 0 + XS['ext'][k].location.normalized() * 0.0) for k in (3, 16)], inn=proj(Vector(XS_ORIGIN) + XS['inn'][2].location), ring=proj(Vector(XS_ORIGIN) + Vector((0, -0.2, 0.96))))
ANCH = {}
def proj(p):
    loc = CAM.location; M = Euler(CAM.rotation_euler).to_matrix(); v = M.transposed() @ (Vector(p) - loc)
    k = CAM.data.lens / 18.0; ny = (v.y / -v.z) * k; nx = (v.x / -v.z) * k * (720 / 1280)
    return [round(0.5 + 0.5 * nx, 4), round(0.5 - 0.5 * ny, 4)]

def on_frame(scene, *a):
    apply(scene.frame_current)
bpy.app.handlers.frame_change_pre.append(on_frame)
sc.frame_start, sc.frame_end = 1, NF

if __name__ == "__main__" or True:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ALL = list(range(1, NF + 1))
    U.run_render(sc, argv, ALL, "main")
    if ANCH:
        pth = SUBDIR + "/renders/xs_anchors.json"; old = json.load(open(pth)) if os.path.exists(pth) else {}
        old.update({str(k): v for k, v in ANCH.items()}); json.dump(old, open(pth, "w"))
