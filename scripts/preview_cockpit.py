import sys, math; sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
from f1 import car as C, anatomy as A, gear as G
sc = reset_scene()
render_settings(sc, (360, 640), samples=12)
world_sky(20, 200)
sun = light("sun", 'SUN', energy=3.2, angle=1.0); sun.rotation_euler = look_at_rot((5, -8, 5), (0,0,0))
bpy.ops.mesh.primitive_plane_add(size=60); bpy.context.object.data.materials.append(mat("g",(0.08,0.08,0.085),rough=0.7))
P = C.build_car(font=ROOT + "/assets/fonts/Anton-Regular.ttf")
D = A.build_driver(anatomy=False); Gr = G.build_gear(D)
D["root"].parent = P["body"]; D["root"].location, D["root"].rotation_euler = A.BODY_IN_CAR
cam = camera("cam", 40); sc.camera = cam
for k, (loc, tgt, lens) in {"cs": ((2.1, -3.2, 1.6), (2.1, 0, 0.55), 35), "ct": ((2.9, -0.9, 1.9), (2.0, 0, 0.6), 30),
                           "cx": ((1.9, -2.0, 0.55), (2.1, 0, 0.5), 30)}.items():
    cam.location = loc; cam.rotation_euler = look_at_rot(loc, tgt); cam.data.lens = lens
    sc.render.filepath = f"{ROOT}/previews/cock_{k}.png"; bpy.ops.render.render(write_still=True)
# x-section: hide tub to check body placement
for o in bpy.data.objects:
    if o.name.startswith(("tub","sidepod","airbox","mirror","inlet")): o.hide_render = True
cam.location = (2.1, -3.2, 0.6); cam.rotation_euler = look_at_rot(cam.location, (2.1, 0, 0.5))
sc.render.filepath = f"{ROOT}/previews/cock_cut.png"; bpy.ops.render.render(write_still=True)
