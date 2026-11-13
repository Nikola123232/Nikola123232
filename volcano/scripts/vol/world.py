"""Volcano environment: crater walls, molten lava lake (crust plates + glowing cracks), lights, smoke, embers, debris."""
import sys, math, random
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise
from f1.core import *
from f1.core import _fcurves

R0 = 110.0        # lava lake radius (m)
RMAX = 520.0
H_RIM = 300.0


# ------------------------------------------------------------------ materials
def lava_mat(name="lava", drift_frames=(1, 1800), drift=(0.0, 0.0, 0.0), speed=0.5, strength=2.0, K=1.0):
    m = bpy.data.materials.new(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); p = nodes.new("ShaderNodeBsdfPrincipled")
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping"); mp.name = "LavaDrift"
    links.new(tc.outputs["Object"], mp.inputs[0])
    # animated slow flow
    mp.inputs["Location"].default_value = (0, 0, 0)
    mp.inputs["Location"].keyframe_insert("default_value", frame=drift_frames[0])
    dur = (drift_frames[1] - drift_frames[0]) / 30.0
    mp.inputs["Location"].default_value = (-speed * dur, 0.35 * speed * dur, 0)
    mp.inputs["Location"].keyframe_insert("default_value", frame=drift_frames[1])
    for fc in _fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'

    wn = nodes.new("ShaderNodeTexNoise"); wn.noise_dimensions = '3D'; wn.inputs["Scale"].default_value = 0.045 * K; wn.inputs["Detail"].default_value = 4
    links.new(mp.outputs[0], wn.inputs[0])
    wc = nodes.new("ShaderNodeVectorMath"); wc.operation = 'SUBTRACT'; wc.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(wn.outputs["Color"], wc.inputs[0])

    def vor(scale, rnd=1.0, warp=1.0):
        sc_ = nodes.new("ShaderNodeVectorMath"); sc_.operation = 'SCALE'; sc_.inputs["Scale"].default_value = warp / K
        links.new(wc.outputs[0], sc_.inputs[0])
        ad_ = nodes.new("ShaderNodeVectorMath"); ad_.operation = 'ADD'
        links.new(mp.outputs[0], ad_.inputs[0]); links.new(sc_.outputs[0], ad_.inputs[1])
        v = nodes.new("ShaderNodeTexVoronoi"); v.feature = 'DISTANCE_TO_EDGE'
        v.inputs["Scale"].default_value = scale * K; v.inputs["Randomness"].default_value = rnd
        links.new(ad_.outputs[0], v.inputs[0]); return v

    def noi(scale, detail=6, rough=0.55):
        n = nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale * K; n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough; links.new(mp.outputs[0], n.inputs[0]); return n

    def mth(op, a, b=None, c=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs[0]

    def crack(v, width, soft=1.0):  # 1 on the crack line, 0 inside plate (narrow, soft falloff)
        lin = mth('MAXIMUM', mth('SUBTRACT', 1.0, mth('DIVIDE', v.outputs["Distance"], width)), 0.0)
        return mth('POWER', lin, 1.6)
    v1, v2, v3 = vor(0.040, 1.0, 34.0), vor(0.20, 1.0, 7.0), vor(1.1, 1.0, 1.2)
    warp = noi(0.03, 5)
    c1 = crack(v1, 0.075); c2 = crack(v2, 0.09); c3 = crack(v3, 0.12)
    nz_mask = mth('GREATER_THAN', noi(0.05, 4).outputs["Fac"], 0.55)             # where cracks are active
    cracks = mth('MAXIMUM', mth('MAXIMUM', c1, mth('MULTIPLY', c2, 0.55)), mth('MULTIPLY', c3, 0.22))
    cracks = mth('MULTIPLY', cracks, mth('ADD', 0.12, mth('MULTIPLY', nz_mask, 0.88)))
    molten = mth('MULTIPLY', mth('GREATER_THAN', noi(0.016, 4).outputs["Fac"], 0.70), 0.8)   # open molten pools
    E = mth('MINIMUM', mth('MAXIMUM', cracks, molten), 1.0)
    grain = noi(1.6, 7, 0.6).outputs["Fac"]
    heat = mth('MULTIPLY', mth('ADD', E, mth('MULTIPLY', grain, 0.35)), 1.0)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30; ramp.color_ramp.elements[0].color = (0.8, 0.03, 0.0, 1)
    e = ramp.color_ramp.elements.new(0.70); e.color = (1.0, 0.28, 0.01, 1)
    ramp.color_ramp.elements[2].position = 1.0; ramp.color_ramp.elements[2].color = (1.0, 0.5, 0.08, 1)
    links.new(heat, ramp.inputs[0])
    links.new(ramp.outputs[0], p.inputs["Emission Color"])
    links.new(mth('MULTIPLY', mth('POWER', E, 1.5), strength), p.inputs["Emission Strength"])
    # crust colour + roughness
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.012, 0.010, 0.010, 1); cr.color_ramp.elements[1].color = (0.06, 0.05, 0.045, 1)
    links.new(grain, cr.inputs[0]); links.new(cr.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.55
    # relief: plates raised, cracks sunken + fine noise
    h = mth('ADD', mth('MULTIPLY', mth('MINIMUM', v1.outputs["Distance"], 0.12), 8.0), mth('MULTIPLY', grain, 0.5))
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.9; bump.inputs["Distance"].default_value = 0.6
    links.new(h, bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    links.new(p.outputs[0], out.inputs[0])
    return m


def rock_mat():
    m = mat("basalt", (0.03, 0.028, 0.028), rough=0.85)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    vo = nodes.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 0.11
    links.new(tc.outputs["Object"], vo.inputs[0])
    vo2 = nodes.new("ShaderNodeTexVoronoi"); vo2.feature = 'DISTANCE_TO_EDGE'; vo2.inputs["Scale"].default_value = 0.6
    links.new(tc.outputs["Object"], vo2.inputs[0])
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8
    links.new(tc.outputs["Object"], nz.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.012, 0.011, 0.011, 1); cr.color_ramp.elements[1].color = (0.075, 0.062, 0.055, 1)
    links.new(nz.outputs["Fac"], cr.inputs[0]); links.new(cr.outputs[0], p.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 1.2
    mixh = nodes.new("ShaderNodeMath"); mixh.operation = 'ADD'
    links.new(vo.outputs["Distance"], mixh.inputs[0]); links.new(nz.outputs["Fac"], mixh.inputs[1])
    links.new(mixh.outputs[0], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    # hot glow close to the lake, in cracks
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
    low = mth('SUBTRACT', 1.0, mth('MINIMUM', mth('DIVIDE', sep.outputs[2], 150.0), 1.0))
    low = mth('POWER', low, 2.4)
    crk = mth('MULTIPLY', mth('SUBTRACT', 1.0, mth('DIVIDE', vo2.outputs["Distance"], 0.06)), 0.5)
    crk = mth('MAXIMUM', crk, 0.0)
    glow = mth('MULTIPLY', low, mth('ADD', mth('MULTIPLY', crk, 0.35), mth('MULTIPLY', mth('MAXIMUM', mth('SUBTRACT', nz.outputs['Fac'], 0.50), 0.0), 2.4)))
    p.inputs["Emission Color"].default_value = (1.0, 0.22, 0.02, 1)
    links.new(mth('MULTIPLY', glow, 1.5), p.inputs["Emission Strength"])
    return m


def smoke_mat(name="smoke", color=(0.16, 0.14, 0.13), density=1.0):
    """Soft billboard-free volume-ish puff: view-facing falloff x noise x per-object opacity (object colour R)."""
    m = bpy.data.materials.new(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tc = nodes.new("ShaderNodeTexCoord"); oi = nodes.new("ShaderNodeObjectInfo")
    lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    inv = nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; links.new(lw.outputs["Facing"], inv.inputs[1])
    fq = nodes.new("ShaderNodeMath"); fq.operation = 'POWER'; fq.inputs[1].default_value = 2.5; links.new(inv.outputs[0], fq.inputs[0])
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], nz.inputs[0])
    a = nodes.new("ShaderNodeMath"); a.operation = 'MULTIPLY'; links.new(fq.outputs[0], a.inputs[0]); links.new(nz.outputs["Fac"], a.inputs[1])
    sc = nodes.new("ShaderNodeSeparateColor"); links.new(oi.outputs["Color"], sc.inputs[0])
    b = nodes.new("ShaderNodeMath"); b.operation = 'MULTIPLY'; links.new(a.outputs[0], b.inputs[0]); links.new(sc.outputs[0], b.inputs[1])
    c = nodes.new("ShaderNodeMath"); c.operation = 'MULTIPLY'; c.inputs[1].default_value = 2.4 * density; links.new(b.outputs[0], c.inputs[0])
    cl = nodes.new("ShaderNodeClamp"); links.new(c.outputs[0], cl.inputs[0])
    tr = nodes.new("ShaderNodeBsdfTransparent")
    df = nodes.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (*color, 1)
    em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.9, 0.22, 0.04, 1); em.inputs[1].default_value = 0.07
    ad = nodes.new("ShaderNodeAddShader"); links.new(df.outputs[0], ad.inputs[0]); links.new(em.outputs[0], ad.inputs[1])
    mx = nodes.new("ShaderNodeMixShader"); links.new(cl.outputs[0], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[1]); links.new(ad.outputs[0], mx.inputs[2])
    links.new(mx.outputs[0], out.inputs[0])
    return m


# ------------------------------------------------------------------ crater
def crater_height(r, ang):
    u = max(0.0, min(1.0, (r - R0) / (RMAX - R0)))
    h = H_RIM * (1 - (1 - u) ** 1.55)
    # strata terraces + rock noise (deterministic)
    x, y = r * math.cos(ang), r * math.sin(ang)
    big = noise.fractal(Vector((x * 0.006, y * 0.006, 1.3)), 0.6, 2.0, 5)
    fine = noise.fractal(Vector((x * 0.04, y * 0.04, 4.1)), 0.55, 2.0, 5)
    ridge = abs(noise.noise(Vector((math.cos(ang) * 3.2, math.sin(ang) * 3.2, r * 0.004)))) * 0.0
    terr = 6.0 * math.sin(h * 0.09 + big * 3.0) * min(1.0, u * 6)
    return h + u * (70 * big) + 9 * fine * min(1, u * 4 + 0.15) + terr + 0.0 * ridge


def build_crater(seg_r=170, seg_t=300):
    rm = rock_mat()
    bm = bmesh.new()
    rows = []
    for i in range(seg_r + 1):
        t = i / seg_r
        r = R0 - 6 + (RMAX - R0 + 6) * t ** 1.45
        row = []
        for j in range(seg_t):
            a = 2 * math.pi * j / seg_t
            h = crater_height(max(r, R0), a)
            if r < R0:
                h = -2 + (r - (R0 - 6)) / 6 * 2
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), h)))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for j in range(seg_t):
            k = (j + 1) % seg_t
            bm.faces.new((a[j], a[k], b[k], b[j]))
    # outer plateau + horizon ring
    outer = []
    for j in range(seg_t):
        a = 2 * math.pi * j / seg_t
        outer.append(bm.verts.new((4000 * math.cos(a), 4000 * math.sin(a), H_RIM + 60 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 0))))))
    for j in range(seg_t):
        k = (j + 1) % seg_t
        bm.faces.new((rows[-1][j], rows[-1][k], outer[k], outer[j]))
    for f in bm.faces:
        f.normal_flip() if f.normal.z < 0 else None
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    wall = obj_from_bm("crater_wall", bm, [rm], smooth=True)
    return wall


def build_lake(lava, radius=R0 + 8):
    bm = bmesh.new()
    seg = 128
    rings = [0.0, 0.2, 0.45, 0.7, 0.88, 1.0]
    vs = [[bm.verts.new((0, 0, 0))]]
    for r in rings[1:]:
        vs.append([bm.verts.new((radius * r * math.cos(2 * math.pi * j / seg), radius * r * math.sin(2 * math.pi * j / seg), 0)) for j in range(seg)])
    for j in range(seg):
        bm.faces.new((vs[0][0], vs[1][j], vs[1][(j + 1) % seg]))
    for a, b in zip(vs[1:-1], vs[2:]):
        for j in range(seg):
            k = (j + 1) % seg
            bm.faces.new((a[j], b[j], b[k], a[k]))
    for f in bm.faces:
        f.normal_flip() if f.normal.z < 0 else None
    return obj_from_bm("lava_lake", bm, [lava], smooth=True)


def build_environment(lava_frames=(1, 1800), sun=True, lava_light=True):
    sc = bpy.context.scene
    try:
        sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.3
    except Exception as e:
        print("view transform", e)
    world_color((0.018, 0.016, 0.017), 1.0)
    lava = lava_mat(drift_frames=lava_frames)
    wall = build_crater()
    lake = build_lake(lava)
    E = {"wall": wall, "lake": lake, "lava": lava}
    if sun:
        s = light("sky_sun", 'SUN', energy=0.9, angle=3, color=(0.75, 0.82, 1.0))
        s.rotation_euler = (math.radians(35), math.radians(10), math.radians(70))
    if lava_light:
        E["glowL"] = light("lava_glow", 'AREA', (0, 0, 6), (0, 0, 0), energy=260000, size=190, color=(1.0, 0.36, 0.07))
        E["glowL"].data.shape = 'DISK'
    return E


# ------------------------------------------------------------------ keyed helpers
def _constant_all(o, paths=("location",)):
    ad = o.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            if fc.data_path in paths:
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT'


def smoke_puffs(f0, f1, n=40, rmin=30, rmax=170, zmin=4, zmax=140, size=(25, 60), opacity=(0.05, 0.18), rise=2.5,
                seed=3, keepout=None, color=(0.17, 0.15, 0.14)):
    rng = random.Random(seed)
    m = smoke_mat(color=color)
    dur = (f1 - f0) / 30.0
    objs = []
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
        o = obj_from_bm(f"puff{i}", bm, [m], smooth=True)
        r = rng.uniform(rmin, rmax); a = rng.uniform(0, 2 * math.pi); z = rng.uniform(zmin, zmax)
        p0 = Vector((r * math.cos(a), r * math.sin(a), z))
        if keepout and (p0 - Vector(keepout[0])).length < keepout[1]:
            p0 += (p0 - Vector(keepout[0])).normalized() * keepout[1]
        s = rng.uniform(*size)
        o.scale = (s, s, s * rng.uniform(0.5, 0.9)); o.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 6))
        op = rng.uniform(*opacity); o.color = (op, op, op, 1)
        o.visible_shadow = False
        o.location = p0; o.keyframe_insert("location", frame=f0)
        o.location = p0 + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 1.0)) * rise * dur * rng.uniform(0.5, 1.2)
        o.keyframe_insert("location", frame=f1)
        objs.append(o)
    for o in objs:
        for fc in _fcurves(o.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = 'LINEAR'
    return objs


def embers(f0, f1, n=120, rmax=95, zmax=60, seed=5, speed=(2.0, 7.0), size=0.22, time_scale=lambda f: (f - 1) / 30.0, center=(0, 0), step=1):
    rng = random.Random(seed)
    em = emit_mat("ember", (1.0, 0.45, 0.06), 40.0)
    objs = []
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size * rng.uniform(0.5, 1.4))
        o = obj_from_bm(f"ember{i}", bm, [em], smooth=False)
        o.visible_shadow = False
        r = rmax * math.sqrt(rng.random()); a = rng.uniform(0, 6.28)
        x0, y0 = center[0] + r * math.cos(a), center[1] + r * math.sin(a)
        z0 = rng.uniform(0, zmax); v = rng.uniform(*speed); ph = rng.uniform(0, 6.28); sw = rng.uniform(0.5, 3.0)
        for f in range(f0, f1 + 1, step):
            t = time_scale(f)
            z = (z0 + v * t) % zmax
            o.location = (x0 + sw * math.sin(t * 0.8 + ph), y0 + sw * math.cos(t * 0.6 + ph), z)
            o.keyframe_insert("location", frame=f)
        _constant_all(o)
        objs.append(o)
    return objs


def rock_chunks(f0, f1, n=60, center=lambda f: (0, 0, 0), spread=(14, 14, 40), vfall=6.0, seed=9, size=(0.15, 0.7)):
    """Volcanic debris hanging/falling slowly in WORLD space around a moving centre; the (fast) faller flies past it."""
    rng = random.Random(seed)
    rm = rock_mat()
    c0 = Vector(center(f0))
    objs = []
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        s = rng.uniform(*size)
        for v in bm.verts:
            v.co *= s * (0.7 + 0.6 * rng.random())
        o = obj_from_bm(f"rock{i}", bm, [rm], smooth=False)
        x0 = c0.x + rng.uniform(-1, 1) * spread[0]; y0 = c0.y + rng.uniform(-1, 1) * spread[1]; z0 = c0.z + rng.uniform(-1, 1) * spread[2]
        vr = vfall * rng.uniform(0.5, 1.4)
        rot = Vector((rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-4, 4)))
        for f in range(f0, f1 + 1):
            c = Vector(center(f)); t = (f - f0) / 30.0
            zz = c.z + ((z0 - vr * t - c.z + spread[2]) % (2 * spread[2])) - spread[2]
            o.location = (x0, y0, zz)
            o.rotation_euler = rot * t
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
        _constant_all(o, ("location",))
        objs.append(o)
    return objs


# ------------------------------------------------------------------ dynamic surface (ripples / dents) driven by a frame handler
class Surface:
    def __init__(self, name, size, n, mat, z=0.02, center=(0, 0), fn=None):
        self.n, self.size, self.center, self.fn, self.z = n, size, center, fn, z
        bm = bmesh.new()
        xs = np.linspace(-size / 2, size / 2, n)
        vs = [[bm.verts.new((center[0] + x, center[1] + y, z)) for y in xs] for x in xs]
        for i in range(n - 1):
            for j in range(n - 1):
                bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
        self.obj = obj_from_bm(name, bm, [mat], smooth=True)
        gx, gy = np.meshgrid(xs, xs, indexing='ij')
        self.gx, self.gy = gx.ravel() + center[0], gy.ravel() + center[1]
        bpy.app.handlers.frame_change_pre.append(self._h)

    def _h(self, scene, *a):
        f = scene.frame_current
        if self.fn is None:
            return
        h = self.fn(f, self.gx, self.gy)
        co = np.empty((self.n * self.n, 3), dtype=np.float32)
        co[:, 0] = self.gx; co[:, 1] = self.gy; co[:, 2] = self.z + h
        self.obj.data.vertices.foreach_set("co", co.ravel())
        self.obj.data.update()
