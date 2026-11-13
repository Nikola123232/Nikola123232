"""SCENES 1-2 (frames 1-150, 0:00-0:05): THE HOOK.
S1 f1-60  : character already falling toward the lava lake, high-angle tracking shot, fast push-in, motion blur.
S2 f61-150: macro of glowing lava, then the character frozen just above the surface; dramatic orbit."""
import sys, math, json
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
from vol import world as W, util as U

F0, F1 = 1, 150
sc = reset_scene()
E = W.build_environment((F0, F1))
E["glowL"].rotation_euler = (math.pi, 0, 0)
H = build_human(anatomy=False)
H["skin"].visible_shadow = True
root = H["root"]
set_reveal(H, None, 0.0)
under = light("char_glow", 'AREA', (0, 0, 180), (math.pi, 0, 0), energy=9000, size=14, color=(1.0, 0.42, 0.1))
under2 = light("char_rim", 'AREA', (0, 0, 200), (0, 0, 0), energy=700, size=10, color=(0.7, 0.8, 1.0))

Z0, VF = 192.0, 46.0
def char_z(f): return Z0 - VF * (f - 1) / 30.0
ZS2 = 6.2
info = {}
for f in range(F0 - 1, F1 + 2):
    t = (f - 1) / 30.0
    if f <= 60:
        z = char_z(f); pos = Vector((0.5 * math.sin(t * 1.3), 0.4 * math.cos(t * 1.1), z))
        rot = (0.35 * math.sin(t * 2.1), 1.25 + 0.35 * math.sin(t * 1.7 + 1), 0.9 + 1.5 * t + 0.4 * math.sin(t * 2.6))
        pose(H, fall_spec(t * 1.0, 0.3, 1.0), f)
    else:
        u = (f - 61) / 89.0
        pos = Vector((0, 0, ZS2 + 0.25 * math.sin(u * 2.0)))
        rot = (0.55, 0.85 + 0.03 * u, 2.45 + 0.10 * u)          # frozen in a dramatic, slightly twisting pose
        pose(H, fall_spec(1.15 + 0.02 * u, 0.3, 1.0), f)
    root.location = pos; root.rotation_euler = rot
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    under.location = pos + Vector((0, 0, -9 if f <= 60 else -4)); under.keyframe_insert("location", frame=f)
    under.data.energy = 6000 if f <= 60 else 220; under.data.keyframe_insert("energy", frame=f)
    under2.location = pos + Vector((3, -3, 14)); under2.keyframe_insert("location", frame=f)
    info[f] = {"z": pos.z}
fix_euler_continuity(root)
json.dump(info, open(U.V + "/renders/anchors_v12.json", "w"))

# ---- environment dressing
W.rock_chunks(F0 - 1, 61, n=46, center=lambda f: (0, 0, char_z(min(f, 60))), spread=(20, 20, 40), vfall=5.0, size=(0.2, 0.9))
W.embers(F0 - 1, F1 + 1, n=110, rmax=100, zmax=230, speed=(3, 9), size=0.30,
         time_scale=lambda f: (f - 1) / 30.0 if f <= 60 else 2.0 + (f - 61) / 30.0 * 0.12)
W.smoke_puffs(F0 - 1, F1 + 1, n=34, rmin=62, rmax=210, zmin=12, zmax=200, size=(35, 80), opacity=(0.04, 0.12), rise=2.0, seed=4)
W.smoke_puffs(F0 - 1, F1 + 1, n=14, rmin=15, rmax=90, zmin=3, zmax=14, size=(18, 35), opacity=(0.05, 0.10), rise=1.0, seed=11, keepout=((0, 0, 5), 20))

# ---- cameras
cam1 = U.shot_camera("cam1", 1, 22); cam2 = U.shot_camera("cam2", 61, 30)
for f in range(F0 - 1, 62):
    ff = max(f, 1); t = (ff - 1) / 30.0; u = ease_in_out((ff - 1) / 60.0)
    pc = Vector((0.5 * math.sin(t * 1.3), 0.4 * math.cos(t * 1.1), info[ff]["z"]))
    h = 3.9 + (2.6 - 3.9) * u
    ang = math.radians(-60 + 55 * u)
    loc = pc + Vector((2.6 * math.cos(ang) * (1 - 0.4 * u), 2.6 * math.sin(ang) * (1 - 0.4 * u), h))
    key_cam(cam1, f, loc, pc + Vector((0, 0, -0.9)), 30 + 8 * u, roll=-5 + 8 * u)
cen = Vector((0, 0, ZS2))
mac_tgt = Vector((-3.5, -3.0, 0.15))
Wm = 0
U.dof(cam2, None, fstop=2.2)
for f in range(60, F1 + 2):
    u = max(0.0, (f - 61) / 89.0); e = ease_in_out(u)
    a = math.radians(-125 + 175 * e); r = 7.0 - 2.6 * ease_in_out(u)
    z = 1.35 + 4.6 * ease_in_out(min(1.0, max(0.0, (u - 0.05) / 0.9)))
    loc = cen + Vector((r * math.cos(a), r * math.sin(a), 0)); loc.z = z
    w = ease_in_out(min(1.0, max(0.0, (u - 0.10) / 0.45)))
    tgt = mac_tgt.lerp(cen + Vector((0, 0, -0.1)), w)
    key_cam(cam2, f, loc, tgt, 30 + 18 * e)
    cam2.data.dof.focus_distance = (loc - tgt).length
    cam2.data.dof.aperture_fstop = 9.0 - 6.8 * ease_in_out(min(1.0, max(0.0, (u - 0.1) / 0.5)))
    cam2.data.dof.keyframe_insert("aperture_fstop", frame=f)
    cam2.data.dof.keyframe_insert("focus_distance", frame=f)
U.setup(sc, F0, F1, "v12", samples=12, motion_blur=True, bounces=20)
for f in range(F0, F1 + 1):
    sc.render.motion_blur_shutter = 0.6 if f <= 60 else 0.10
    sc.render.keyframe_insert("motion_blur_shutter", frame=f)
U.run_render(sc, sys.argv)
