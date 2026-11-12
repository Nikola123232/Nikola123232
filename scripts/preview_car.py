import sys, math; sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
from f1 import car as C
sc = reset_scene()
render_settings(sc, (540, 960), samples=16)
world_sky(18, 210)
light("sun", 'SUN', energy=3.0, angle=1.5, rot=(math.radians(60), 0, math.radians(30)))
bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.object
g.data.materials.append(mat("ground", (0.08, 0.08, 0.085), rough=0.7))
P = C.build_car(font=ROOT + "/assets/fonts/Anton-Regular.ttf")
cam = camera("cam", 40)
sc.camera = cam
views = {"fq": ((7.5, -4.8, 1.6), (2.0, 0, 0.4), 40), "side": ((2.0, -9.0, 1.0), (2.0, 0, 0.45), 32),
         "rq": ((-4.0, 4.0, 2.2), (1.5, 0, 0.4), 40), "top": ((2.3, -3.0, 5.5), (2.0, 0, 0.4), 30),
         "low": ((5.2, -1.6, 0.25), (2.0, 0.0, 0.5), 22)}
which = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else list(views)
for k in which:
    loc, tgt, lens = views[k]
    cam.location = loc; cam.rotation_euler = look_at_rot(loc, tgt); cam.data.lens = lens
    sc.render.filepath = f"{ROOT}/previews/car_{k}.png"
    bpy.ops.render.render(write_still=True)
