"""SCENE 7 (frames 1471-1680, 0:49-0:56): THE SURPRISING SCIENCE - water vs lava in two glass tanks.
Human-density sphere (985 kg/m3): plunges into water, rides high on lava.  Steel sphere: sinks fast in water, slowly in lava (viscosity)."""
import sys, math, json, random
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
import numpy as np
from vol.human import *
from vol import world as W, util as U
from f1 import studio as St
from f1.core import _fcurves

F0, F1 = 1471, 1680
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
floor, floor_m = St.build_studio(grid_color=(0.08, 0.2, 0.45))
St.studio_lights((0, 0, 1.4), key=330, rim=380)
light("warm", 'AREA', (0.0, -2.0, 0.55), energy=140, size=2.0, color=(1.0, 0.45, 0.12), target=(0, 0, 0.6))

TW = 1.2                                  # tank footprint (m)
ZB_L, ZB_W = 0.0, 1.26                    # tank bottoms (lava tank low, water tank on a shelf above)
FILL = 0.85
ZS_L, ZS_W = ZB_L + FILL, ZB_W + FILL      # surface heights
r_ball = 0.15

# shelf + frames
steel_frame = mat("frame", (0.05, 0.055, 0.065), metal=0.8, rough=0.35)
bm = bmesh.new(); box_bm(bm, (0, 0, 1.18), (TW + 0.16, TW + 0.16, 0.06))
shelf = obj_from_bm("shelf", bm, [steel_frame], smooth=False)
for zb in (ZB_L, ZB_W):
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            box_bm(bm, (sx * TW / 2, sy * TW / 2, zb + 0.55), (0.04, 0.04, 1.1))
    for z in (zb, zb + 1.1):
        for sx in (-1, 1): box_bm(bm, (sx * TW / 2, 0, z), (0.04, TW, 0.04))
        for sy in (-1, 1): box_bm(bm, (0, sy * TW / 2, z), (TW, 0.04, 0.04))
    obj_from_bm("frame", bm, [steel_frame], smooth=False)
# glass panes (thin, nearly clear)
glass = bpy.data.materials.new("glass"); nodes, links = glass.node_tree.nodes, glass.node_tree.links; nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial"); lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.3
tr = nodes.new("ShaderNodeBsdfTransparent"); gl = nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05; gl.inputs["Color"].default_value = (0.7, 0.85, 1, 1)
mx = nodes.new("ShaderNodeMixShader"); links.new(lw.outputs["Facing"], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[2]); links.new(gl.outputs[0], mx.inputs[1])
sh = nodes.new("ShaderNodeMath"); sh.operation = 'MULTIPLY'; sh.inputs[1].default_value = 0.35; links.new(lw.outputs["Fresnel"], sh.inputs[0]); links.new(sh.outputs[0], mx.inputs[0])
links.new(mx.outputs[0], out.inputs[0])
# water volume (clear blue, fresnel + tint) and molten lava volume (translucent glowing)
water = bpy.data.materials.new("water"); nodes, links = water.node_tree.nodes, water.node_tree.links; nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial"); lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.4
tr = nodes.new("ShaderNodeBsdfTransparent"); em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.1, 0.45, 0.9, 1); em.inputs[1].default_value = 0.8
mx = nodes.new("ShaderNodeMixShader"); mf = nodes.new("ShaderNodeMath"); mf.operation = 'MULTIPLY_ADD'; mf.inputs[1].default_value = 0.55; mf.inputs[2].default_value = 0.14
links.new(lw.outputs["Fresnel"], mf.inputs[0]); links.new(mf.outputs[0], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[1]); links.new(em.outputs[0], mx.inputs[2]); links.new(mx.outputs[0], out.inputs[0])
lava_tank = W.lava_mat("lava_tank", (E0, E1), speed=0.02, strength=2.0, K=34.0)
lava_vol = bpy.data.materials.new("lava_volume"); nodes, links = lava_vol.node_tree.nodes, lava_vol.node_tree.links; nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial"); tr = nodes.new("ShaderNodeBsdfTransparent")
em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, 0.25, 0.03, 1); em.inputs[1].default_value = 0.55
mx = nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.6; links.new(tr.outputs[0], mx.inputs[1]); links.new(em.outputs[0], mx.inputs[2]); links.new(mx.outputs[0], out.inputs[0])
bm = bmesh.new(); box_bm(bm, (0, 0, ZB_W + FILL / 2 - 0.01), (TW - 0.02, TW - 0.02, FILL - 0.02))
wv = obj_from_bm("water_volume", bm, [water], smooth=False); wv.visible_shadow = False
bm = bmesh.new(); box_bm(bm, (0, 0, ZB_L + FILL / 2 - 0.01), (TW - 0.02, TW - 0.02, FILL - 0.02))
lv = obj_from_bm("lava_volume", bm, [lava_vol], smooth=False); lv.visible_shadow = False

# ---- animated surfaces
EV_A, EV_B = 1525, 1606           # contact frames: sphere A (human density), sphere B (steel)
def waves(f, x, y, ev_list, k, w, amp, decay, speed, aoff):
    r_tot = np.zeros_like(x)
    for (fc, bx, by) in ev_list:
        t = (f - fc) / 30.0
        if t < 0: continue
        r = np.hypot(x - bx, y - by); front = speed * t + 0.05
        r_tot += amp * np.exp(-t * decay) * np.sin(k * (r - speed * t)) * np.exp(-r / aoff) * (r < front)
    win = np.clip((TW / 2 - 0.04 - np.maximum(np.abs(x), np.abs(y))) / 0.12, 0, 1)
    return r_tot * win
wsurf = W.Surface("water_surface", TW - 0.04, 110, water, z=ZS_W, fn=lambda f, x, y: waves(f, x, y, [(EV_A, 0, 0), (EV_B, 0, 0)], 26.0, 0, 0.022, 1.4, 0.9, 0.7))
lsurf = W.Surface("lava_surface", TW - 0.04, 110, lava_tank, z=ZS_L, fn=lambda f, x, y: waves(f, x, y, [(EV_A, 0, 0), (EV_B, 0, 0)], 9.0, 0, 0.02, 0.55, 0.22, 0.9)
                  - 0.07 * np.exp(-(np.hypot(x, y) / 0.2) ** 2) * (smoothstep(EV_A, EV_A + 30, f) * (1 - smoothstep(EV_B - 6, EV_B + 20, f)) + 0.6 * smoothstep(EV_B, EV_B + 60, f)))
wsurf.obj.visible_shadow = False

# ---- spheres
human_m = mat("body_density", (0.9, 0.3, 0.05), rough=0.4, coat=0.5, emission=(1.0, 0.25, 0.03), estr=0.25)
steel_m = mat("steel_ball", (0.6, 0.62, 0.66), metal=1.0, rough=0.18)
def sphere(name, m_):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=r_ball)
    return obj_from_bm(name, bm, [m_], smooth=True)
balls = {k: sphere(k, m_) for k, m_ in (("hw", human_m), ("hl", human_m), ("sw", steel_m), ("sl", steel_m))}
G = 4.0
def drop_z(zs, fc, f, h0=0.55):
    t = (f - fc) / 30.0
    return zs + r_ball * 0.0 + h0 - 0.5 * G * (t + math.sqrt(2 * h0 / G)) ** 2 if False else None
def traj(kind, f):
    zs = ZS_W if kind in ("hw", "sw") else ZS_L
    fc = EV_A if kind in ("hw", "hl") else EV_B
    t = (f - fc) / 30.0
    tf = math.sqrt(2 * 0.5 / G)                       # fall time from 0.5 m above the surface
    if t < -tf - 0.4:
        return zs + 0.5 + r_ball                       # waiting above
    if t < 0:
        s = max(0.0, t + tf)
        return zs + r_ball + 0.5 - 0.5 * G * s * s if t > -tf else zs + r_ball + 0.5
    if kind == "hw":
        rest = zs - 0.095
        return rest + (zs - rest) * math.exp(-3.0 * t) * 0 + 0.095 * math.exp(-3.0 * t) + 0.0 - 0.17 * math.exp(-1.5 * t) * math.sin(5.5 * t) + 0.015 * math.exp(-0.8 * t) * math.sin(11 * t)
    if kind == "hl":
        rest = zs + 0.02
        return rest + (r_ball - 0.02 + 0.0) * math.exp(-t / 0.6) - 0.05 * (1 - math.exp(-t / 0.22)) * math.exp(-t / 0.9)
    if kind == "sw":
        z = zs + r_ball - 1.3 * (t - 0.22 * (1 - math.exp(-t / 0.22)))
        zb = ZB_W + r_ball + 0.02
        if z < zb:
            tb = t - (0.3 + 0.55)       # approx impact time
            return zb + 0.04 * abs(math.sin(max(0, 6 * (t - 0.9)))) * math.exp(-3 * max(0, t - 0.9))
        return z
    if kind == "sl":
        return zs + r_ball - 0.10 * (t - 1.6 * (1 - math.exp(-t / 1.6)))
SX, SY = 0.0, 0.0
for k, o in balls.items():
    for f in range(E0, E1 + 1):
        o.location = (SX, SY, traj(k, f)); o.rotation_euler = (0, 0.0, 0.0)
        o.keyframe_insert("location", frame=f)
# water-entry splash
rng = random.Random(7)
spl = emit_mat("splash", (0.7, 0.9, 1.0), 2.0)
for i in range(46):
    ev = EV_A if i < 22 else EV_B; vz = rng.uniform(0.8, 2.0) * (1.0 if ev == EV_A else 1.5); sp = rng.uniform(0.15, 0.6); ang = rng.uniform(0, 6.28); sz = rng.uniform(0.008, 0.02)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); o = obj_from_bm(f"splash{i}", bm, [spl], smooth=True); o.visible_shadow = False
    for f in range(E0, E1 + 1):
        t = (f - ev) / 30.0
        z = ZS_W + vz * t - 0.5 * 4.5 * t * t
        if t < 0 or z < ZS_W: o.location = (0, 0, -9); o.scale = (1e-4,) * 3
        else: o.location = (sp * t * math.cos(ang), sp * t * math.sin(ang), z); o.scale = (sz,) * 3
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    for fc in _fcurves(o.animation_data.action):
        for kf in fc.keyframe_points: kf.interpolation = 'CONSTANT'
# tanks pop in
for o in [bpy.data.objects[n] for n in bpy.data.objects.keys() if n.startswith(("frame", "glass", "water_vol", "lava_vol", "shelf"))] + [wsurf.obj, lsurf.obj]:
    for f in (E0, F0 + 14):
        pass

# ---- camera
cam = U.shot_camera("cam7", F0, 38)
for f in range(E0, E1 + 1):
    u = (f - F0) / (F1 - F0); e = ease_in_out(min(1, max(0, u)))
    az = math.radians(-26 + 46 * e); d = 3.9 - 1.2 * ease_in_out(min(1.0, u * 1.2))
    zc = 1.25 + 0.12 * math.sin(u * math.pi * 1.2)
    # in the steel-ball phase look at both tanks a bit lower to follow the action
    loc = Vector((d * math.sin(az), -d * math.cos(az), zc + 0.35 - 0.1 * e))
    key_cam(cam, f, loc, Vector((0, 0, zc)), 38 - 4 * e)
U.setup(sc, F0, F1, "v7", samples=14, motion_blur=False, bounces=24)
pts = {"water": lambda f: Vector((TW / 2, -TW / 2, ZB_W + 0.75)), "lava": lambda f: Vector((TW / 2, -TW / 2, ZB_L + 0.75)),
       "ball_w": lambda f: balls["hw"].location.copy(), "ball_l": lambda f: balls["hl"].location.copy(),
       "steel_w": lambda f: balls["sw"].location.copy(), "steel_l": lambda f: balls["sl"].location.copy()}
St.export_anchors(sc, U.active_camera, pts, F0, F1, U.V + "/renders/anchors_v7.json")
U.run_render(sc, sys.argv)
