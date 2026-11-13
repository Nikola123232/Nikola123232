"""SCENE 3 (frames 151-420, 0:05-0:14): THE FALL. Side tracking shot, then the camera rises and rotates to reveal the lava lake below."""
import sys, math, json
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
from vol import world as W, util as U

F0, F1 = 151, 420
sc = reset_scene()
E = W.build_environment((F0, F1)); E["glowL"].rotation_euler = (math.pi, 0, 0)
H = build_human(anatomy=False); root = H["root"]; set_reveal(H, None, 0.0)
under = light("char_glow", 'AREA', (0, 0, 100), (math.pi, 0, 0), energy=5000, size=14, color=(1.0, 0.42, 0.1))
rim = light("char_rim", 'AREA', (0, 0, 120), (0, 0, 0), energy=700, size=10, color=(0.7, 0.8, 1.0))
ZA, ZB = 150.0, 34.0
def cz(f):
    u = (f - F0) / (F1 - F0); return ZA + (ZB - ZA) * (u + 0.06 * math.sin(u * math.pi * 2) / (2 * math.pi) * 0.0)
info = {}
def cpos(f):
    t = (f - F0) / 30.0
    return Vector((1.2 * math.sin(t * 0.7), 0.8 * math.cos(t * 0.5), cz(f)))
for f in range(F0 - 2, F1 + 3):
    t = (f - F0) / 30.0; pc = cpos(f)
    rot = (0.25 * math.sin(t * 0.9), 1.30 + 0.25 * math.sin(t * 0.6 + 1), 0.4 + 0.35 * t + 0.25 * math.sin(t * 1.3))
    pose(H, fall_spec(t * 0.55 + 2.0, 0.6, 0.85), f)       # slower, heavier flailing in the slow-motion fall
    root.location = pc; root.rotation_euler = rot
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    under.location = pc + Vector((0, 0, -10)); under.keyframe_insert("location", frame=f)
    rim.location = pc + Vector((4, -4, 16)); rim.keyframe_insert("location", frame=f)
    info[f] = {"z": pc.z, "dist": max(0.0, pc.z)}
fix_euler_continuity(root)
json.dump(info, open(U.V + "/renders/anchors_v3.json", "w"))
W.rock_chunks(F0 - 2, F1 + 2, n=50, center=lambda f: tuple(cpos(f)), spread=(6.0, 6.0, 36), vfall=3.0, size=(0.15, 0.55), seed=21)
W.embers(F0 - 2, F1 + 2, n=130, rmax=105, zmax=190, speed=(3, 9), size=0.32, time_scale=lambda f: (f - F0) / 30.0 * 0.5)
W.smoke_puffs(F0 - 2, F1 + 2, n=40, rmin=45, rmax=230, zmin=8, zmax=170, size=(35, 85), opacity=(0.05, 0.14), rise=2.0, seed=8)
W.smoke_puffs(F0 - 2, F1 + 2, n=14, rmin=20, rmax=95, zmin=3, zmax=16, size=(18, 36), opacity=(0.06, 0.12), rise=1.0, seed=17)
cam = U.shot_camera("cam3", F0, 40)
for f in range(F0 - 2, F1 + 3):
    u = (f - F0) / (F1 - F0); pc = cpos(f)
    s = ease_in_out(min(1.0, max(0.0, (u - 0.35) / 0.65)))           # 0 = side tracking, 1 = high over the lake
    R = 9.0 - 2.5 * s; a = math.radians(-70 + 25 * min(1, u / 0.35) + 95 * s)
    H_ = 4.5 + 6.5 * s
    loc = pc + Vector((R * math.cos(a), R * math.sin(a), H_))
    key_cam(cam, f, loc, pc + Vector((0, 0, -0.8 - 3.5 * s)), 38 - 6 * s, roll=3 * math.sin(u * 5) * (1 - s))
U.setup(sc, F0, F1, "v3", samples=12, motion_blur=True, bounces=18)
sc.render.motion_blur_shutter = 0.35
U.run_render(sc, sys.argv)
