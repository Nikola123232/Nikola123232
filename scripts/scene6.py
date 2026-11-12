"""SCENE 6 (0:56-1:00, frames 1681-1800): back at the crash site. Driver safe inside the intact survival cell;
camera cranes up and away from the halo/helmet to a wide shot. Title is composited."""
import sys, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from mathutils import Vector, Euler
from f1.core import *
from f1 import world as Wd, story as S, crash as K, anatomy as A

F0, F1 = 1681, 1800
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
W = Wd.build_world(detail=True)
W["sun"].data.color = (1.0, 0.86, 0.68)   # same sun, slightly warmer grade for the ending
P = W["P"]
Wd.animate_car(P, E0, E1)
K.animate_front_wing(P, E0, E1)
K.animate_broken_wheel(P, E0, E1, "FR")
K.animate_shards(P, E0, E1)
K.animate_barrier(W["blocks"], E0, E1)
K.build_skidmarks(E0, E1)
arm = W["D"]["arm"]
for f in range(E0, E1 + 1):  # driver lifts head slightly
    u = smoothstep(F0 + 10, F0 + 50, f)
    A.pose_pitch(arm, "neck2", math.radians(-6 * u), f)
    A.pose_pitch(arm, "head", math.radians(-4 * u), f)
st = S.car_state(S.real_time(F0))
R = Euler((0, 0, st["yaw"])).to_matrix()
base = Vector((st["x"], st["y"], 0))
cam = Wd.shot_camera("cam6", F0, 34)
for f in range(E0, E1 + 1):
    u = ease_in_out((f - F0) / (F1 - F0))
    u2 = u ** 1.3
    a = base + R @ Vector((2.9, 1.45, 1.3))
    b = base + R @ Vector((-5.5, 8.5, 7.0))
    loc = a.lerp(b, u2)
    tgt = (base + R @ Vector((1.95, 0, 0.82))).lerp(base + R @ Vector((2.2, 0, 0.4)), u)
    key_cam(cam, f, loc, tgt, 34 - 6 * u)
Wd.setup_render(sc, F0, F1, "s6", samples=10, motion_blur=False)
sc.cycles.transparent_max_bounces = 16
Wd.run_render(sc, sys.argv)
