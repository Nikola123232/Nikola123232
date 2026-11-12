"""SCENE 2 (0:08-0:18, frames 241-540): loss of control and impact.
2A f241-318 chase cam from behind: rear snaps, car slides with locked tyres, sparks + smoke.
2B f319-438 side view, time ramps to 0.15x: impact with TecPro barrier, wing + debris fly, barrier compresses.
2C f439-540 aftermath: dust settles, camera pushes in toward the cockpit (white flash to scene 3 in compositing)."""
import sys, math, json
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from mathutils import Vector, Euler
from f1.core import *
from f1 import world as Wd, story as S, crash as K

F0, F1 = 241, 540
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
W = Wd.build_world(detail=True)
P = W["P"]
Wd.animate_car(P, E0, E1)
K.animate_front_wing(P, E0, E1)
K.animate_broken_wheel(P, E0, E1, "FR")
K.animate_shards(P, E0, E1)
K.animate_sparks(E0, E1)
K.animate_barrier(W["blocks"], E0, E1)
K.build_skidmarks(E0, E1)
K.animate_driver_head(W["D"], E0, E1)

camA = Wd.shot_camera("cam2A", F0, 30)
camB = Wd.shot_camera("cam2B", 319, 26)
camC = Wd.shot_camera("cam2C", 439, 30)
BX = S.BARRIER_X
cam_pos = {}
st_end = S.car_state(S.real_time(F1))
for f in range(E0, E1 + 1):
    t = S.real_time(f)
    st = S.car_state(t)
    if f <= 320:
        u = ease_in_out((f - F0) / 78)
        # chase cam in world axes (car rotates in frame); slight lag & roll on the snap
        snap = smoothstep(S.T_SNAP, S.T_SNAP + 0.5, t)
        off = (-6.6 + 1.2 * u, 0.4 - 1.2 * snap, 1.55 - 0.3 * u)
        Wd.key_camera_follow(camA, f, st, off, (2.2, -0.5 * snap, 0.45), 30 + 4 * u, world_axes=True,
                             shake=0.02 + 0.03 * snap, roll=-6 * snap)
        if f <= 318: cam_pos[f] = camA
    if 317 <= f <= 440:
        u = ease_in_out((f - 319) / 119)
        imp = math.exp(-max(0, t - S.T_IMP_TARGET) * 6) if t > S.T_IMP_TARGET else 0
        cen = Vector((st["x"], st["y"], 0)) + Euler((0, 0, st["yaw"])).to_matrix() @ Vector((2.4, 0, 0.5))
        tgt = cen.lerp(Vector((BX - 0.5, -7.0, 0.5)), 0.25 + 0.5 * u)
        fixed = Vector((BX - 5.0 + 1.5 * u, -15.5 + 1.5 * u, 0.9 + 0.35 * u))
        follow = cen + Vector((1.5, -8.5, 0.5))
        loc = follow.lerp(fixed, smoothstep(319, 352, f))
        loc += Vector((noise.noise(Vector((f * 0.9, 0, 0))), 0, noise.noise(Vector((0, 0, f * 0.8))))) * 0.12 * imp
        key_cam(camB, f, loc, tgt, 22 + 8 * u)
        if 319 <= f <= 438: cam_pos[f] = camB
    if f >= 437:
        u = ease_in_out((f - 439) / 101)
        u2 = u ** 1.6
        stc = st_end
        R = Euler((0, 0, stc["yaw"])).to_matrix()
        base = Vector((stc["x"], stc["y"], 0))
        start = Vector((BX - 7.5, -15.0, 2.6))
        end = base + R @ Vector((3.35, -1.5, 1.45))
        loc = start.lerp(end, u2)
        tgt = (base + R @ Vector((2.4, 0, 0.45))).lerp(base + R @ Vector((1.95, 0, 0.8)), u)
        key_cam(camC, f, loc, tgt, 30 + 8 * u)
        if f >= 439: cam_pos[f] = camC
for f in range(E0, F0): cam_pos[f] = camA
for f in range(F1 + 1, E1 + 1): cam_pos[f] = camC
tg = empty("bb_target")
Wd.setup_render(sc, F0, F1, "s2", samples=10)
for f in range(E0, E1 + 1):
    sc.frame_set(f)
    tg.location = cam_pos[f].matrix_world.to_translation()
    tg.keyframe_insert("location", frame=f)
K.animate_puffs(E0, E1, tg)
sc.cycles.transparent_max_bounces = 64
# HUD data
hud = {}
for f in range(F0, F1 + 1):
    t = S.real_time(f)
    st = S.car_state(t)
    g = 0.0
    if S.T_SNAP - 0.2 < t < S.T_IMP_TARGET:
        g = 1.1 if t > S.T_SNAP else 3.1
    if S.T_IMP_TARGET <= t < S.T_IMP_TARGET + S.IMPACT_DUR:
        u = (t - S.T_IMP_TARGET) / S.IMPACT_DUR
        g = S.PEAK_G * math.sin(math.pi * u)
    hud[f] = {"t": t, "kmh": st["v"] * 3.6, "g": g, "rate": S.rate((f - 1) / 30)}
json.dump(hud, open(ROOT + "/renders/hud_s2.json", "w"))
Wd.run_render(sc, sys.argv)
