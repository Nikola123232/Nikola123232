"""SCENE 1 (0:00-0:08, frames 1-240): flat out at 300 km/h.
1A f1-105  : low tracking camera skimming the asphalt, front 3/4, the car slowly overtakes the camera.
1B f106-240: long-lens side tracking shot orbiting to rear 3/4."""
import sys, math, json
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
from f1 import world as Wd, story as S

F0, F1 = 1, 240
sc = reset_scene()
W = Wd.build_world(detail=True)
P = W["P"]
Wd.animate_car(P, F0 - 2, F1 + 2)
camA = Wd.shot_camera("cam1A", F0, 20)
camB = Wd.shot_camera("cam1B", 106, 45)
anchors = {}
for f in range(F0 - 2, F1 + 3):
    st = S.car_state(S.real_time(f))
    if f <= 107:
        u = ease_in_out((f - 1) / 104)
        off = (6.2 + (1.0 - 6.2) * u, -2.3 + 0.2 * u, 0.20 + 0.12 * u)
        look = (2.4 + (1.2 - 2.4) * u, 0.0, 0.40 + 0.08 * u)
        lens = 19 + 5 * u
        Wd.key_camera_follow(camA, f, st, off, look, lens, shake=0.006, roll=-4 + 6 * u)
    if f >= 104:
        u = ease_in_out((f - 106) / 134)
        ang = math.radians(-92 + (-38 + 92) * u)   # orbit from side to rear 3/4 (around car centre)
        r = 9.0 - 2.5 * u
        cx = 2.0 - 0.5 * u
        off = (cx + r * math.cos(ang + math.pi), r * math.sin(ang), 0.75 + 0.55 * u)
        look = (1.9, 0.0, 0.5)
        Wd.key_camera_follow(camB, f, st, off, look, 48 - 14 * u, shake=0.01)
    anchors[f] = {}
# HUD anchors (screen positions of the car centre) for the compositor
Wd.setup_render(sc, F0, F1, "s1", samples=12)
for f in range(F0, F1 + 1, 1):
    sc.frame_set(f)
    st = S.car_state(S.real_time(f))
    x, y, d = project(sc, Wd.active_camera(f), (st["x"] + 2.0, st["y"], 0.6))
    anchors[f] = {"car": [x, y, d], "kmh": st["v"] * 3.6}
json.dump(anchors, open(ROOT + "/renders/anchors_s1.json", "w"))
Wd.run_render(sc, sys.argv)
