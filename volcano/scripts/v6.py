"""SCENE 6 (frames 1111-1470, 0:37-0:49): WHAT IF YOU TOUCH THE LAVA?  Extreme slow motion, non-graphic: the body becomes a simplified
anatomical silhouette, lands on the crust, the thick lava dents and ripples slowly - the body stays on top, it does not sink like in water."""
import sys, math, json, random
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
import numpy as np
from vol.human import *
from vol import world as W, util as U
from f1.core import _fcurves

F0, F1 = 1111, 1470
E0, E1 = F0 - 2, F1 + 2
FC = 1262                       # contact frame
sc = reset_scene()
E = W.build_environment((F0, F1)); E["glowL"].rotation_euler = (math.pi, 0, 0)
H = build_human(anatomy=True); root = H["root"]; arm = H["arm"]; M = H["M"]
under = light("char_glow", 'AREA', (0, 0, 20), (math.pi, 0, 0), energy=1200, size=10, color=(1.0, 0.42, 0.1))
rim = light("char_rim", 'AREA', (4, -4, 30), (0, 0, 0), energy=600, size=8, color=(0.7, 0.8, 1.0))

# ---- body: suit -> x-ray silhouette with orange rim
for f, v in ((E0, 0.0), (1135, 0.0), (1200, 1.0), (E1, 1.0)):
    set_reveal(H, f, v)
for m in M["rev"]:
    em = [n for n in m.node_tree.nodes if n.type == 'EMISSION']
    for e in em:
        for f, c, st in ((E0, (0.2, 0.6, 1.0), 0.45), (1150, (0.2, 0.6, 1.0), 0.45), (1215, (1.0, 0.42, 0.08), 1.6), (1380, (1.0, 0.35, 0.05), 1.5), (E1, (0.9, 0.12, 0.02), 1.0)):
            e.inputs[0].default_value = (*c, 1); e.inputs[0].keyframe_insert("default_value", frame=f)
            e.inputs[1].default_value = st; e.inputs[1].keyframe_insert("default_value", frame=f)
for o in H["anat"]:
    key_vis(o, E0, False); key_vis(o, 1150, True)
for o in H["anat"] + [H["skin"]] + H["head"]:
    o.visible_shadow = False

# ---- motion
Z0 = 35.0
def zc(f):
    if f <= FC:
        u = max(0.0, (f - F0) / (FC - F0)); return 0.12 + (Z0 - 0.12) * (1 - u ** 1.7)
    dt = f - FC
    return 0.12 - 0.16 * (1 - math.exp(-dt / 40.0)) + 0.07 * math.exp(-dt / 7.0) * math.sin(dt * 0.55)
def blend(s1, s2, w):
    I = Quaternion()
    return {b: s1.get(b, I).slerp(s2.get(b, I), w) for b in set(s1) | set(s2)}
info = {}
for f in range(E0, E1 + 2):
    t = (f - F0) / 30.0; w = smoothstep(FC - 10, FC + 40, f)
    z = zc(f)
    land = smoothstep(FC - 25, FC + 5, f)
    rot = (0.12 * math.sin(t * 0.8) * (1 - land), 1.30 + (1.5708 - 1.30) * land, 0.5 + 0.15 * t * (1 - land) + 0.12 * land)
    root.location = (0.25 * math.sin(t * 0.6) * (1 - land), 0.2 * math.cos(t * 0.5) * (1 - land), z + 0.0)
    root.rotation_euler = rot
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    pose(H, blend(fall_spec(t * 0.35 + 2.0, 0.6, 0.7), stand_spec(), w), f)
    under.location = (0, 0, max(z, 0) + 6); under.keyframe_insert("location", frame=f)
    rim.location = (4, -4, z + 18); rim.keyframe_insert("location", frame=f)
    info[f] = {"z": z, "dist": max(0.0, z - 0.1)}
fix_euler_continuity(root)
json.dump(info, open(U.V + "/renders/anchors_v6.json", "w"))

# ---- the thick lava surface: slow, heavy ripples and a dent under the body
K_W, K_V = 1.5, 1.1
def lava_h(f, x, y):
    t = (f - FC) / 30.0
    r = np.hypot(x, y)
    win = np.clip((19.0 - r) / 5.0, 0, 1)
    if t < 0:
        return np.zeros_like(r) + 0.0 * win
    front = K_V * t * 3.0
    wave = 0.14 * np.exp(-t * 0.45) * np.sin(K_W * (r - 3.2 * t)) * np.exp(-r / 8.0) * (r < front + 0.5)
    dent = -0.22 * np.exp(-(r / (1.2 + 0.25 * t)) ** 2) * (1 - np.exp(-t * 1.6)) - 0.05 * t * np.exp(-(r / 1.5) ** 2) * (t < 6)
    ring = 0.10 * np.exp(-((r - (1.6 + 0.5 * t)) / 0.7) ** 2) * np.exp(-t * 0.35)
    return (wave + dent + ring) * win
surf = W.Surface("lava_patch", 40.0, 150, E["lava"], z=0.02, fn=lava_h)

# ---- impact splash (viscous, small, slow), embers, smoke, debris
rng = random.Random(13)
em = emit_mat("lava_drop", (1.0, 0.22, 0.03), 3.5)
for i in range(34):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    o = obj_from_bm(f"drop{i}", bm, [em], smooth=True); o.visible_shadow = False
    s = rng.uniform(0.025, 0.06); ang = rng.uniform(0, 6.28); sp = rng.uniform(0.6, 2.2); vz = rng.uniform(1.0, 3.6)
    for f in range(E0, E1 + 1):
        t = (f - FC - 3) / 30.0
        if t < 0 or t > 9:
            o.location = (0, 0, -30); o.scale = (1e-4,) * 3
        else:
            g = 0.55
            z = 0.2 + vz * t - 0.5 * g * t * t
            if z < 0.02: o.location = (0, 0, -30); o.scale = (1e-4,) * 3
            else:
                o.location = (sp * t * math.cos(ang) * 1.1, sp * t * math.sin(ang) * 1.1, z); o.scale = (s * (1 - 0.05 * t),) * 3
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    for fc in _fcurves(o.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
W.embers(E0, E1, n=140, rmax=60, zmax=40, speed=(0.8, 3.0), size=0.07, time_scale=lambda f: (f - F0) / 30.0 * 0.22)
smk = W.smoke_mat("lava_steam", (0.22, 0.18, 0.16))
for i in range(16):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    o = obj_from_bm(f"steam{i}", bm, [smk], smooth=True); o.visible_shadow = False
    a = rng.uniform(0, 6.28); r = rng.uniform(0.0, 3.0); sz = rng.uniform(3.5, 7.0); op = rng.uniform(0.10, 0.20); o.color = (op, op, op, 1)
    for f in range(E0, E1 + 1):
        t = max(0.0, (f - FC - 4 - 2 * i % 7) / 30.0)
        g = smoothstep(0, 2.5, t)
        o.location = (r * math.cos(a) + 0.6 * t, r * math.sin(a), 0.3 + 1.4 * t); s_ = max(1e-3, sz * g * (0.4 + 0.25 * t))
        o.scale = (s_, s_, s_ * 0.8)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
W.smoke_puffs(E0, E1, n=26, rmin=45, rmax=220, zmin=10, zmax=170, size=(35, 80), opacity=(0.04, 0.11), rise=1.5, seed=19)
W.smoke_puffs(E0, E1, n=10, rmin=14, rmax=70, zmin=2, zmax=10, size=(14, 28), opacity=(0.05, 0.1), rise=0.8, seed=23)
W.rock_chunks(E0, FC, n=26, center=lambda f: (0, 0, zc(f)), spread=(5.5, 5.5, 22), vfall=2.0, size=(0.1, 0.4), seed=29)

# ---- camera: follow the fall, drop low, then orbit the floating silhouette
camA = U.shot_camera("cam6A", F0, 40); camB = U.shot_camera("cam6B", FC - 40, 32)
for f in range(E0, FC - 38):
    u = (f - F0) / 110.0; z = zc(f)
    loc = Vector((4.6 - 1.0 * u, -3.0, z + 1.8 - 0.6 * u)); loc.z = max(loc.z, 1.2)
    key_cam(camA, f, loc, Vector((0, 0, z - 0.3)), 34)
U.dof(camA, root, fstop=2.8)
for f in range(FC - 42, E1 + 1):
    u = min(1.0, (f - (FC - 40)) / (F1 - (FC - 40)))
    e = ease_in_out(u)
    z = zc(f)
    a = math.radians(-58 + 128 * e); r = 4.6 - 1.7 * e
    h = 0.8 + 0.7 * math.sin(u * math.pi) + 0.15 * u
    tgt = Vector((0, 0, max(z, 0.0) + 0.15 + 0.35 * (1 - ease_in_out(min(1.0, u * 2.0)))))
    loc = Vector((r * math.cos(a), r * math.sin(a), h))
    key_cam(camB, f, loc, tgt, 34 + 6 * e)
U.dof(camB, root, fstop=2.6)
U.setup(sc, F0, F1, "v6", samples=12, motion_blur=False, bounces=24)
from f1 import studio as St
pts = {"contact": lambda f: Vector((0, 0, 0.1)), "body": lambda f: root.location.copy()}
St.export_anchors(sc, U.active_camera, pts, F0, F1, U.V + "/renders/anchors_v6.json2")
U.run_render(sc, sys.argv)
