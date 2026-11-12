"""Dark 'x-ray studio' used by scenes 3-5: grid floor, speed lines, ghost car, force arrows, rig pulse helpers."""
import bpy, bmesh, math, random, json
from mathutils import Vector, Matrix, Euler, Quaternion
from .core import *
from . import car as C, anatomy as A, gear as G

CYAN = (0.25, 0.7, 1.0)


def build_studio(grid_color=(0.1, 0.35, 0.8)):
    world_color((0.006, 0.01, 0.022), 1.0)
    # floor: dark glossy with emissive grid (mapping offset animatable via node 'GridMap')
    m = mat("studio_floor", (0.01, 0.012, 0.02), rough=0.45, spec=0.5)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping"); mp.name = "GridMap"
    links.new(tc.outputs["Object"], mp.inputs[0])
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(mp.outputs[0], sep.inputs[0])
    def line(axis_out, period=0.5, w=0.006):
        pp = nodes.new("ShaderNodeMath"); pp.operation = 'PINGPONG'; pp.inputs[1].default_value = period / 2
        links.new(axis_out, pp.inputs[0])
        lt = nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = w
        links.new(pp.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    mx = nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
    links.new(line(sep.outputs[0]), mx.inputs[0]); links.new(line(sep.outputs[1]), mx.inputs[1])
    # fade grid with distance from origin
    ln = nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; links.new(tc.outputs["Object"], ln.inputs[0])
    fd = nodes.new("ShaderNodeMapRange"); fd.inputs[1].default_value = 3.0; fd.inputs[2].default_value = 12.0
    fd.inputs[3].default_value = 1.0; fd.inputs[4].default_value = 0.0
    links.new(ln.outputs["Value"], fd.inputs[0])
    mm = nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
    links.new(mx.outputs[0], mm.inputs[0]); links.new(fd.outputs[0], mm.inputs[1])
    ms = nodes.new("ShaderNodeMath"); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = 1.2
    links.new(mm.outputs[0], ms.inputs[0])
    links.new(ms.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Emission Color"].default_value = (*grid_color, 1)
    bpy.ops.mesh.primitive_plane_add(size=40)
    fl = bpy.context.object; fl.name = "studio_floor"
    fl.data.materials.append(m)
    # back glow cyclorama (gives silhouette separation)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=30, segments=32, ring_count=16)
    dome = bpy.context.object; dome.name = "dome"
    dm = bpy.data.materials.new("dome")
    nodes, links = dm.node_tree.nodes, dm.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); em = nodes.new("ShaderNodeEmission")
    tc = nodes.new("ShaderNodeTexCoord"); sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    gr = nodes.new("ShaderNodeMapRange"); gr.inputs[1].default_value = -2; gr.inputs[2].default_value = 18
    links.new(sep.outputs[2], gr.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.02, 0.05, 0.12, 1); cr.color_ramp.elements[1].color = (0.002, 0.003, 0.008, 1)
    links.new(gr.outputs[0], cr.inputs[0]); links.new(cr.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.0
    links.new(em.outputs[0], out.inputs[0])
    dome.data.materials.append(dm)
    return fl, m


def studio_lights(center=(2.0, 0, 0.5), key=300, rim=400):
    c = Vector(center)
    light("key", 'AREA', c + Vector((2.5, -3.0, 2.5)), energy=key, size=3, color=(1, 0.97, 0.92), target=c)
    light("rim", 'AREA', c + Vector((-3.0, 2.5, 2.0)), energy=rim, size=3, color=(0.45, 0.7, 1.0), target=c)
    light("fill", 'AREA', c + Vector((1.0, 3.5, 1.0)), energy=key * 0.3, size=4, color=(0.7, 0.8, 1.0), target=c)
    light("top", 'AREA', c + Vector((0, 0, 4.0)), energy=key * 0.5, size=4, target=c)


def ghost_car(P, edge=CYAN, strength=1.3, keep=None):
    gm = xray_mat("ghost_car", edge, strength, base_alpha=0.0, power=0.25)
    for o in bpy.data.objects:
        if o.type in ('MESH', 'FONT') and _is_child_of(o, P["root"]):
            if o.type == 'FONT':
                o.hide_render = True
                continue
            if keep and any(o.name.startswith(k) for k in keep):
                continue
            o.data.materials.clear()
            o.data.materials.append(gm)
            for p_ in o.data.polygons:
                p_.material_index = 0
    return gm


def _is_child_of(o, root):
    p = o.parent
    while p:
        if p == root:
            return True
        p = p.parent
    return False


def arrow(name, length=0.4, radius=0.018, color=(1, 0.15, 0.1), strength=6.0):
    """Arrow pointing +X from origin."""
    bm = bmesh.new()
    hl = min(0.12, length * 0.35)
    tube_bm(bm, [(0, 0, 0), (length - hl, 0, 0)], radius, 12)
    tube_bm(bm, [(length - hl, 0, 0), (length - hl + 0.001, 0, 0), (length, 0, 0)], [radius * 2.6, radius * 2.6, 0.0005], 16)
    m = emit_mat(name + "_m", color, strength)
    return obj_from_bm(name, bm, [m])


def key_arrow(a, frames_vis, base_scale=1.0, pulse=True):
    """frames_vis: list of (f_in, f_out). Pops in/out with ease; gentle length pulse."""
    sc = bpy.context.scene
    for f in range(sc.frame_start - 2, sc.frame_end + 3):
        s = 0.0
        for (fi, fo) in frames_vis:
            if fi <= f <= fo + 8:
                s = max(s, ease_out_back((f - fi) / 9) if f < fi + 9 else 1.0)
                if f > fo:
                    s = min(s, 1 - (f - fo) / 8)
        s = max(0.0, s)
        pl = 1 + (0.12 * math.sin(f * 0.35) if pulse else 0)
        a.scale = (base_scale * s * pl + 1e-4, base_scale * s + 1e-4, base_scale * s + 1e-4)
        a.keyframe_insert("scale", frame=f)


def speed_lines(f0, f1, stop_frame, n=60, area=(-6, 8, -3.5, 3.5), speed=1.2, seed=3):
    """Streaks on the floor moving -X, decelerating to a stop (and fading) at stop_frame."""
    rng = random.Random(seed)
    m = emit_mat("speedline", (0.4, 0.75, 1.0), 4.0)
    objs = []
    x0, x1, y0, y1 = area
    span = x1 - x0
    for i in range(n):
        L = rng.uniform(0.6, 2.2)
        bm = bmesh.new()
        tube_bm(bm, [(0, 0, 0), (L, 0, 0)], 0.006, 4)
        o = obj_from_bm(f"sl{i}", bm, [m])
        y = rng.uniform(y0, y1); z = rng.uniform(0.005, 0.02)
        ph = rng.uniform(0, span)
        pos = ph
        for f in range(f0, f1 + 1):
            v = speed * (1 - smoothstep(stop_frame - 2, stop_frame + 6, f))
            pos = (pos - v) % span if f > f0 else pos
            vis = 1 - smoothstep(stop_frame, stop_frame + 10, f)
            o.location = (x0 + pos, y, z)
            o.scale = (1 + 2.5 * v, vis + 1e-4, vis + 1e-4)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("scale", frame=f)
        set_linear_loc_wrap(o)
        objs.append(o)
    return objs


def set_linear_loc_wrap(o):
    from .core import _fcurves
    for fc in _fcurves(o.animation_data.action):
        if fc.data_path == "location":
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'


def decel_pulse(u):
    """Normalised deceleration response 0..1..~0 for u in [0, ~1.6] (fast rise, damped return)."""
    if u <= 0:
        return 0.0
    if u < 0.35:
        return math.sin(u / 0.35 * math.pi / 2)
    w = u - 0.35
    return math.exp(-w * 3.0) * math.cos(w * 5.0)


def rig_event(D, f_start, dur, torso=0.045, torso_pitch=6, neck=12, head=8, organ=0.014, brain=0.006,
              organ_objs=(), brain_objs=(), rest=None, accumulate=None):
    """Return per-frame dict of pose values for a deceleration event (used by keyframing loop)."""
    pass


class Pose:
    """Accumulates rig/organ offsets from several events, then keys everything per frame."""
    def __init__(self, D, organs, brain_objs):
        self.D = D
        self.organs = organs
        self.brain = brain_objs
        self.rest = {o.name: Vector(o.location) for o in list(organs) + list(brain_objs)}
        self.events = []

    def add(self, f_start, dur, torso=0.04, torso_pitch=5, neck=14, head=10, organ=0.014, brain=0.006):
        self.events.append((f_start, dur, torso, torso_pitch, neck, head, organ, brain))

    def values(self, f):
        v = dict(torso=0, tp=0, neck=0, head=0, organ=0, brain=0)
        for (fs, dur, to, tp, ne, he, org, br) in self.events:
            u = (f - fs) / dur
            a = decel_pulse(u)
            a_lag = decel_pulse(u - 0.10)
            a_lag2 = decel_pulse(u - 0.16)
            v["torso"] += to * a; v["tp"] += tp * a
            v["neck"] += ne * a_lag; v["head"] += he * a_lag
            v["organ"] += org * a_lag2; v["brain"] += br * a_lag2
        return v

    def key(self, f0, f1):
        arm = self.D["arm"]
        for f in range(f0, f1 + 1):
            v = self.values(f)
            A.pose_offset(arm, "spine", (v["torso"], 0, 0), f)
            pb = arm.pose.bones["spine"]
            A.pose_pitch(arm, "spine", math.radians(v["tp"]), f)
            A.pose_pitch(arm, "neck1", math.radians(v["neck"] * 0.5), f)
            A.pose_pitch(arm, "neck2", math.radians(v["neck"] * 0.5), f)
            A.pose_pitch(arm, "head", math.radians(v["head"]), f)
            for o in self.organs:
                o.location = self.rest[o.name] + Vector((v["organ"], 0, -0.3 * v["organ"]))
                o.keyframe_insert("location", frame=f)
            for o in self.brain:
                o.location = self.rest[o.name] + Vector((v["brain"], 0, 0))
                o.keyframe_insert("location", frame=f)


def glow_shell(name, obj_or_bm_fn, color, parent_arm=None, bone=None):
    pass


def glow_mat(name, color, strength=4.0):
    """Fresnel glow, mostly transparent; animate node 'Glow' (value) 0..1."""
    m = bpy.data.materials.new(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.3
    inv = nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    links.new(lw.outputs["Facing"], inv.inputs[1])
    val = nodes.new("ShaderNodeValue"); val.name = "Glow"; val.outputs[0].default_value = 0.0
    mul = nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    links.new(inv.outputs[0], mul.inputs[0]); links.new(val.outputs[0], mul.inputs[1])
    mul2 = nodes.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = 0.85
    links.new(mul.outputs[0], mul2.inputs[0])
    em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*color, 1); em.inputs[1].default_value = strength
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mx = nodes.new("ShaderNodeMixShader")
    links.new(mul2.outputs[0], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[1]); links.new(em.outputs[0], mx.inputs[2])
    links.new(mx.outputs[0], out.inputs[0])
    return m


def key_glow(m, f, value):
    v = m.node_tree.nodes["Glow"].outputs[0]
    v.default_value = value
    v.keyframe_insert("default_value", frame=f)


def key_glow_windows(m, windows, f0, f1, peak=1.0):
    """windows: list of (f_in, f_out) -> smooth in/out with throb."""
    for f in range(f0, f1 + 1):
        g = 0.0
        for (a, b) in windows:
            g = max(g, smoothstep(a, a + 8, f) * (1 - smoothstep(b, b + 10, f)))
        g *= peak * (0.8 + 0.2 * math.sin(f * 0.5))
        key_glow(m, f, g)


def no_shadow_translucent():
    """Translucent/emissive helpers should not cast shadows (huge speed-up with transparent shadows)."""
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        names = {m.name for m in o.data.materials if m}
        if names & {"ghost_car", "driver_skin", "glow_brain", "glow_neck", "glow_abd", "glow_hans", "ghost_helmet"} or \
                any(n.startswith(("speedline", "arrow", "decel", "inertia", "harness_")) and n.endswith("_m") for n in names):
            o.visible_shadow = False


def export_anchors(sc, cam_for_frame, points, f0, f1, path):
    """points: dict name -> callable(f) returning world Vector. Saves normalised screen coords per frame."""
    data = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        cam = cam_for_frame(f)
        row = {}
        for k, fn in points.items():
            x, y, d = project(sc, cam, fn(f))
            row[k] = [round(x, 4), round(y, 4), round(d, 3)]
        data[f] = row
    json.dump(data, open(path, "w"))


def world_of(obj, local=(0, 0, 0)):
    return lambda f: obj.matrix_world @ Vector(local)
