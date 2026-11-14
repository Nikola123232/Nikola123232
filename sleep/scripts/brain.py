"""Brain shots: anatomically plausible brain (two hemispheres with sulci/gyri shading, cerebellum, brainstem), region activity (frontal, parietal, temporal,
occipital) and illustrative signal pulses along a visual -> parietal -> frontal -> motor route.
 191-290  match cut from the pupil: macro on the cortex, pull back to the whole brain
 291-380  24 h: reaction pathway - a fast reference pulse vs a delayed pulse (illustrative)
 691-732  48 h: alertness activity stutters for ~0.5 s (not 'switched off') and resumes
 881-930  72 h: occipital (visual) cortex shows spontaneous activity while the incoming visual signal is weak"""
import sys, math, json, random, os
sys.path.insert(0, "/home/user/Nikola123232/sleep/scripts"); sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy, bmesh
from mathutils import Vector, Euler, noise
from f1.core import *
from f1.core import _fcurves
from sl import util as U
from sl.timeline import *

sc = reset_scene()
world_color((0.004, 0.006, 0.012), 1.0)
CX = 0.0
RAD = (0.083, 0.040, 0.057); HY = 0.0385


def gauss(x, s): return math.exp(-(x / s) ** 2)


GROOVE = {}


def hemi_deform(side):
    store = GROOVE.setdefault(side, [])

    def f(p, d):
        x, y, z = p
        m = d.y * side
        if m < 0: y = side * (-0.0385 * (1 - (1 + m) ** 2.5))
        if d.x > 0: y *= 1 - 0.16 * d.x ** 2
        if d.x > 0.3 and d.z < -0.2: z *= 0.80
        if d.x < -0.4: z *= 1 - 0.14 * min(1.0, (-d.x - 0.4) / 0.6)
        if d.z < -0.05:
            lat = max(0.0, m)
            z -= 0.013 * gauss(d.x - 0.12, 0.45) * lat * (-d.z)
            y += side * 0.006 * gauss(d.x - 0.05, 0.4) * lat
        if m > 0.35:                      # lateral (Sylvian) fissure
            z += -0.0030 * gauss(d.z - (-0.14 + 0.35 * d.x), 0.10) * 1.0
            y -= side * 0.0030 * gauss(d.z - (-0.14 + 0.35 * d.x), 0.10)
        if d.z < -0.62: z *= 0.9
        v = Vector((x, y, z)); P = Vector((x, y + side * HY, z))
        w = Vector((noise.noise(P * 11), noise.noise(P * 11 + Vector((5, 3, 1))), noise.noise(P * 11 + Vector((9, 7, 2))))) * 1.3
        q = P * 24.0 + w
        fv = noise.noise(q) + 0.35 * noise.noise(q * 2.1 + Vector((3, 1, 7))) * 0.5 + 0.12 * noise.noise(q * 4.3 + Vector((8, 2, 4)))
        groove = math.exp(-(fv / 0.14) ** 2)
        disp = -0.0042 * groove + 0.0010 * noise.noise(q * 3.7)
        store.append(groove)
        return v + v.normalized() * disp if v.length > 1e-6 else v
    return f


def brain_material():
    m = bpy.data.materials.new("cortex"); nodes, links = m.node_tree.nodes, m.node_tree.links; p = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord")
    wn = nodes.new("ShaderNodeTexNoise"); wn.noise_dimensions = '3D'; wn.inputs["Scale"].default_value = 70; wn.inputs["Detail"].default_value = 3; links.new(tc.outputs["Object"], wn.inputs[0])
    wc = nodes.new("ShaderNodeVectorMath"); wc.operation = 'SUBTRACT'; wc.inputs[1].default_value = (0.5, 0.5, 0.5); links.new(wn.outputs["Color"], wc.inputs[0])
    ws = nodes.new("ShaderNodeVectorMath"); ws.operation = 'SCALE'; ws.inputs["Scale"].default_value = 0.012; links.new(wc.outputs[0], ws.inputs[0])
    ad = nodes.new("ShaderNodeVectorMath"); ad.operation = 'ADD'; links.new(tc.outputs["Object"], ad.inputs[0]); links.new(ws.outputs[0], ad.inputs[1])
    at = nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = "sulc"
    sp_ = nodes.new("ShaderNodeSeparateColor"); links.new(at.outputs["Color"], sp_.inputs[0])

    def mth(op, a, b=None, c=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = float(v)
            else: links.new(v, n.inputs[i])
        return n.outputs[0]
    gyr = mth('SUBTRACT', 1.0, mth('MINIMUM', mth('MULTIPLY', sp_.outputs[0], 1.15), 1.0))
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.20, 0.055, 0.055, 1); cr.color_ramp.elements[1].color = (0.66, 0.34, 0.30, 1); links.new(gyr, cr.inputs[0])
    # veins on the surface (thin dark red lines)
    vn = nodes.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 38; vn.inputs["Detail"].default_value = 5; links.new(tc.outputs["Object"], vn.inputs[0])
    vl = mth('GREATER_THAN', mth('SUBTRACT', 1.0, mth('MULTIPLY', mth('ABSOLUTE', mth('SUBTRACT', vn.outputs["Fac"], 0.5)), 12.0)), 0.55)
    mv = nodes.new("ShaderNodeMix"); mv.data_type = 'RGBA'; links.new(mth('MULTIPLY', vl, 0.18), mv.inputs[0]); links.new(cr.outputs[0], mv.inputs[6]); mv.inputs[7].default_value = (0.45, 0.04, 0.05, 1)
    links.new(mv.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.34; p.inputs["Coat Weight"].default_value = 0.35; p.inputs["Coat Roughness"].default_value = 0.18
    p.inputs["Subsurface Weight"].default_value = 0.25; p.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2); p.inputs["Subsurface Scale"].default_value = 0.004
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.0008; links.new(gyr, bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    # ---- activity glow by region (object coordinates mirrored in y)
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    cb = nodes.new("ShaderNodeCombineXYZ"); links.new(sep.outputs[0], cb.inputs[0]); links.new(mth('ABSOLUTE', sep.outputs[1]), cb.inputs[1]); links.new(sep.outputs[2], cb.inputs[2])
    regions = {"F": ((0.062, 0.024, 0.018), 0.030), "P": ((-0.018, 0.030, 0.046), 0.030), "O": ((-0.070, 0.022, 0.002), 0.026), "T": ((0.006, 0.052, -0.030), 0.028), "M": ((0.020, 0.028, 0.050), 0.016)}
    total = None
    for k, (c, r) in regions.items():
        v = nodes.new("ShaderNodeValue"); v.name = "ACT_" + k; v.outputs[0].default_value = 0.0
        dist = nodes.new("ShaderNodeVectorMath"); dist.operation = 'DISTANCE'; dist.inputs[1].default_value = c; links.new(cb.outputs[0], dist.inputs[0])
        g = mth('POWER', 2.71828, mth('MULTIPLY', mth('MULTIPLY', mth('DIVIDE', dist.outputs["Value"], r), mth('DIVIDE', dist.outputs["Value"], r)), -1.0))
        t = mth('MULTIPLY', g, v.outputs[0]); total = t if total is None else mth('ADD', total, t)
    hue = nodes.new("ShaderNodeValue"); hue.name = "HUE"; hue.outputs[0].default_value = 0.0
    hm = nodes.new("ShaderNodeMix"); hm.data_type = 'RGBA'; links.new(hue.outputs[0], hm.inputs[0]); hm.inputs[6].default_value = (0.35, 0.70, 1.0, 1); hm.inputs[7].default_value = (1.0, 0.50, 0.12, 1)
    links.new(hm.outputs[2], p.inputs["Emission Color"]); links.new(mth("MULTIPLY", total, 1.3), p.inputs["Emission Strength"])
    return m


def build_brain():
    mt = brain_material(); objs = []
    for side, nm in ((1, "hemi_L"), (-1, "hemi_R")):
        bm = bmesh.new(); ellipsoid_bm(bm, (0, 0, 0), RAD, 220, 150, 0, hemi_deform(side))
        for v in bm.verts: v.co.y += side * HY
        lay = bm.verts.layers.float_color.new("sulc")
        for i_, v in enumerate(bm.verts): v[lay] = (GROOVE[side][i_], 0.0, 0.0, 1.0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); o = obj_from_bm(nm, bm, [mt], smooth=True); objs.append(o)
    # cerebellum (fine folia) + brainstem
    cbm = bpy.data.materials.new("cerebellum"); nodes, links = cbm.node_tree.nodes, cbm.node_tree.links; p = nodes.get("Principled BSDF"); tc = nodes.new("ShaderNodeTexCoord")
    wv = nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 520; wv.inputs["Distortion"].default_value = 1.5; links.new(tc.outputs["Object"], wv.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.36, 0.14, 0.12, 1); cr.color_ramp.elements[1].color = (0.70, 0.40, 0.34, 1); links.new(wv.outputs["Fac"], cr.inputs[0]); links.new(cr.outputs[0], p.inputs["Base Color"])
    bp = nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.0007; links.new(wv.outputs["Fac"], bp.inputs["Height"]); links.new(bp.outputs[0], p.inputs["Normal"])
    p.inputs["Roughness"].default_value = 0.4; p.inputs["Coat Weight"].default_value = 0.4
    cb = ellipsoid("cerebellum", (-0.054, 0, -0.038), (0.030, 0.046, 0.020), [cbm], 80, 48); objs.append(cb)
    stem_m = mat("brainstem", (0.50, 0.28, 0.24), rough=0.45, coat=0.3)
    st = tube("brainstem", catmull([(-0.012, 0, -0.022), (-0.020, 0, -0.045), (-0.028, 0, -0.068)], 6), 0.0090, [stem_m], 16); objs.append(st)
    return objs, mt


def snap(pt, off=0.003):
    c = Vector((0, HY, 0)); v = Vector(pt) - c
    k = math.sqrt((v.x / RAD[0]) ** 2 + (v.y / RAD[1]) ** 2 + (v.z / RAD[2]) ** 2); v = v / k
    n = Vector((v.x / RAD[0] ** 2, v.y / RAD[1] ** 2, v.z / RAD[2] ** 2)).normalized()
    return c + v + n * off


objs, MT = build_brain()
root = empty("brain_root", size=0.05)
for o in objs: o.parent = root
node = lambda name: MT.node_tree.nodes[name].outputs[0]

# ---- the route (left hemisphere): visual cortex -> parietal -> frontal -> motor
ROUTE = [snap(p_) for p_ in ((-0.080, 0.040, 0.002), (-0.062, 0.058, 0.026), (-0.030, 0.068, 0.046), (0.000, 0.066, 0.052), (0.030, 0.060, 0.048), (0.056, 0.052, 0.036))]
RP = catmull(ROUTE, 10)
Lr = [0.0]
for a, b in zip(RP[:-1], RP[1:]): Lr.append(Lr[-1] + (b - a).length)


def route_pos(u):
    t = u * Lr[-1]; i = 0
    while i < len(Lr) - 2 and Lr[i + 1] < t: i += 1
    k = (t - Lr[i]) / max(1e-9, Lr[i + 1] - Lr[i]); return RP[i].lerp(RP[i + 1], k)


bm = bmesh.new(); tube_bm(bm, RP, 0.00035, 6)
tract = obj_from_bm("route_line", bm, [emit_mat("route", (0.45, 0.65, 1.0), 1.0)], smooth=True); tract.parent = root; tract.visible_shadow = False
BEAD_C = emit_mat("bead_cool", (0.45, 0.8, 1.0), 80.0); BEAD_A = emit_mat("bead_amber", (1.0, 0.5, 0.1), 80.0)


def bead_set(name, m_, n_tail=6):
    objs_ = []
    for k in range(n_tail):
        bmx = bmesh.new(); bmesh.ops.create_icosphere(bmx, subdivisions=2, radius=1.0); o = obj_from_bm(f"{name}{k}", bmx, [m_], smooth=True); o.parent = root; o.visible_shadow = False; objs_.append(o)
    return objs_


fastb = bead_set("fast", BEAD_C); slowb = bead_set("slow", BEAD_A)


def key_bead(objs_, frame, u, on, size=0.0075):
    for k, o in enumerate(objs_):
        uu = max(0.0, u - 0.022 * k); sc_ = size * (1.0 - 0.14 * k) * on * (1 if u > 0 else 0)
        o.location = route_pos(min(1.0, uu)); o.scale = (sc_ + 1e-6,) * 3
        o.keyframe_insert("location", frame=frame); o.keyframe_insert("scale", frame=frame)


def sm(a, b, x): return ease_in_out(max(0.0, min(1.0, (x - a) / (b - a))))


def trial_fast(f, f0, dur=15): return (f - f0) / dur
def trial_slow(f, f0, dur_s): return (f - f0) / dur_s


FPS_ALL = [f for a, b in BRAIN_RANGES for f in range(a, b + 1)]
# activity / hue / pulses / camera per frame
cam = U.shot_camera("brain_cam", 191, 50)
spont_rng = random.Random(9)
spark_events = sorted([spont_rng.uniform(881, 930) for _ in range(26)])
for f in range(185, 936):
    if not any(a - 2 <= f <= b + 2 for a, b in BRAIN_RANGES): continue
    F_, P_, O_, T_, M_ = 0.0, 0.0, 0.0, 0.0, 0.0; hue = 0.0
    fast_u = slow_u = -1.0; fast_on = slow_on = 0.0
    if 191 <= f <= 290:                                  # reveal: calm baseline glow, slowly brightens frontal cortex
        F_ = 0.25 + 0.35 * sm(230, 288, f); P_ = 0.15; O_ = 0.12 * (1 + math.sin(f * 0.3)); T_ = 0.10
    elif 291 <= f <= 380:                                # 24 h: two reaction trials, the second one slower
        t1 = 296; t2 = 340
        fu1 = (f - t1) / 14.0; su1 = (f - t1) / 30.0; fu2 = (f - t2) / 14.0; su2 = (f - t2) / 40.0
        for fu, su in ((fu1, su1), (fu2, su2)):
            if 0 <= fu <= 1.15: fast_u, fast_on = min(1.0, fu), 1.0
            if 0 <= su <= 1.15: slow_u, slow_on = min(1.0, su), 1.0
        O_ = 0.9 * (math.exp(-((f - t1) / 5.0) ** 2) + math.exp(-((f - t2) / 5.0) ** 2))
        M_ = 1.6 * (math.exp(-((f - (t1 + 14)) / 4.0) ** 2) + math.exp(-((f - (t2 + 14)) / 4.0) ** 2))
        hue_m = 1.6 * (math.exp(-((f - (t1 + 30)) / 4.0) ** 2) + math.exp(-((f - (t2 + 40)) / 4.0) ** 2))
        F_ = 0.30 + 0.20 * math.sin(f * 0.15); P_ = 0.25 + 0.15 * math.sin(f * 0.11 + 1)
        hue = 1.0 if hue_m > M_ else 0.0
        M_ = max(M_, hue_m)
    elif 691 <= f <= 732:                                # 48 h: alertness network stutters for ~0.5 s and resumes
        gap = 1.0 if 706 <= f <= 722 else 0.0
        flick = 0.5 + 0.5 * math.sin(f * 0.9) if 702 <= f < 706 or 722 < f <= 726 else 1.0
        base = (1 - gap) * flick
        F_ = 0.7 * base; P_ = 0.6 * base; O_ = 0.4 * base * (0.5 + 0.5 * math.sin(f * 0.5)); T_ = 0.6 * base; hue = 0.35 + 0.4 * gap
        u = ((f - 691) / 24.0) % 1.0 if not gap else (706 - 691) / 24.0
        slow_u, slow_on = u, 1.0 - gap * 0.0
    elif 881 <= f <= 930:                                # 72 h: spontaneous occipital activity, weak incoming signal
        O_ = 0.08
        for ev in spark_events: O_ += 0.5 * math.exp(-((f - ev) / 1.8) ** 2)
        P_ = 0.15 + 0.1 * math.sin(f * 0.2); F_ = 0.2; hue = 0.55 + 0.25 * math.sin(f * 0.3)
        slow_u = ((f - 881) / 70.0); slow_on = 0.35 * (0.5 + 0.5 * math.sin(f * 0.4)) if slow_u < 1 else 0.0
    for k, v in (("F", F_), ("P", P_), ("O", O_), ("T", T_), ("M", M_)):
        node("ACT_" + k).default_value = v; node("ACT_" + k).keyframe_insert("default_value", frame=f)
    node("HUE").default_value = hue; node("HUE").keyframe_insert("default_value", frame=f)
    key_bead(fastb, f, max(0.0, fast_u), fast_on if fast_u >= 0 else 0.0); key_bead(slowb, f, max(0.0, slow_u), slow_on if slow_u >= 0 else 0.0)
    # turntable rotation + camera
    if f <= 290:
        root.rotation_euler = (0, 0, math.radians(-18 + 40 * (f - 191) / 100.0))
    elif f <= 380: root.rotation_euler = (0, 0, math.radians(6 + 12 * (f - 291) / 90.0))
    elif f <= 732: root.rotation_euler = (0, 0, math.radians(25 + 30 * (f - 691) / 42.0))
    else: root.rotation_euler = (0, 0, math.radians(-30 + 25 * (f - 881) / 50.0))
    root.keyframe_insert("rotation_euler", frame=f)
    if f <= 290:
        u = sm(191, 290, f); dist = 0.17 + 0.27 * u ** 0.8
        loc = Vector((0.0, dist, 0.03 + 0.05 * u))
        tgt = Vector((-0.02 + 0.02 * u, 0.04 + 0.0 * u, 0.012 * (1 - u))); lens = 60
    elif f <= 380:
        u = (f - 291) / 89.0; loc = Vector((0.04 - 0.05 * u, 0.40 - 0.05 * u, 0.06)); tgt = Vector((0.0, 0.03, 0.0)); lens = 52
    elif f <= 732:
        u = (f - 691) / 41.0; loc = Vector((-0.34 + 0.05 * u, 0.30, 0.15)); tgt = Vector((0.0, 0.03, 0.01)); lens = 55
    else:
        u = (f - 881) / 49.0; loc = Vector((-0.36 + 0.08 * u, 0.28, 0.10)); tgt = Vector((-0.02, 0.03, 0.0)); lens = 55
    key_cam(cam, f, loc, tgt, lens)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8 if f > 300 else 6.0; cam.data.dof.focus_distance = max(0.03, (loc - tgt).length - 0.04) if f <= 290 else (loc - tgt).length * 0.97
    cam.data.dof.keyframe_insert("focus_distance", frame=f); cam.data.dof.keyframe_insert("aperture_fstop", frame=f)

# lights (studio, dark): warm key, cool rim
light("key", 'AREA', (0.30, 0.35, 0.28), energy=2.6, size=0.30, color=(1.0, 0.86, 0.72), target=(0, 0.02, 0.0))
light("rim", 'AREA', (-0.30, -0.25, 0.22), energy=4.5, size=0.30, color=(0.45, 0.65, 1.0), target=(0, 0.02, 0.0))
light("fill", 'AREA', (0.0, 0.30, -0.15), energy=0.9, size=0.40, color=(0.6, 0.7, 1.0), target=(0, 0.02, 0.0))
light("top", 'AREA', (0.0, 0.0, 0.40), energy=1.0, size=0.40, color=(0.8, 0.85, 1.0), target=(0, 0.02, 0.0))
U.setup(sc, "brain", samples=int(os.environ.get("SPP", 24)), bounces=6)
cam.data.clip_start = 0.004
U.run_render(sc, sys.argv, FPS_ALL, "brain")
