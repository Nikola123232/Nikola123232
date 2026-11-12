import sys, math; sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
from f1 import car as C, track as T, story as S
sc = reset_scene()
render_settings(sc, (360, 640), samples=12)
world_sky(20, 200)
sun = light("sun", 'SUN', energy=3.2, angle=1.0)
sun.rotation_euler = look_at_rot((math.cos(math.radians(-60))*10, math.sin(math.radians(-60))*10, 10*math.tan(math.radians(20))), (0,0,0))
T.build_track()
P = C.build_car(font=ROOT + "/assets/fonts/Anton-Regular.ttf")
cam = camera("cam", 24); sc.camera = cam
shots = {"low": (0, S.LANE_Y, 0, (7, -5.2, 0.3), (2.0, -3.0, 0.45), 22),
         "crash": (S.BARRIER_X - 10, -6, 0.5, (S.BARRIER_X - 9, -22, 1.4), (S.BARRIER_X - 2, -6, 0.6), 30),
         "chase": (150, -4.5, 0.4, (140, -4.5, 2.0), (152, -4.8, 0.6), 30)}
for k in sys.argv[sys.argv.index("--")+1:]:
    x, y, yaw, cl, tg, lens = shots[k]
    P["root"].location = (x, y, 0); P["root"].rotation_euler = (0, 0, yaw)
    cam.location = (x + cl[0] if k=="low" else cl[0], y + cl[1] + 3 if k=="low" else cl[1], cl[2])
    tgt = (x + tg[0], tg[1], tg[2]) if k=="low" else tg
    cam.rotation_euler = look_at_rot(cam.location, tgt); cam.data.lens = lens
    sc.render.filepath = f"{ROOT}/previews/track_{k}.png"
    bpy.ops.render.render(write_still=True)
