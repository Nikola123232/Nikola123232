import sys, math; sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
from f1 import anatomy as A, gear as G
sc = reset_scene()
render_settings(sc, (360, 640), samples=16, transparent_bounces=24)
world_color((0.01, 0.015, 0.03), 1.0)
light("key", 'AREA', (1.5, -1.5, 1.5), energy=150, size=1.5, target=(0, 0, 0.3))
light("rim", 'AREA', (-1.5, 1.0, 1.2), energy=120, size=1.5, color=(0.6, 0.8, 1), target=(0, 0, 0.3))
light("fill", 'AREA', (1.0, 1.5, 0.5), energy=40, size=2, target=(0, 0, 0.3))
D = A.build_driver()
Gr = G.build_gear(D)
cam = camera("cam", 50); sc.camera = cam
mode = sys.argv[sys.argv.index("--")+1:]
for k in mode:
    rv, view = k.split("_")
    A_ = D["M"]["skin"].node_tree.nodes["Reveal"].outputs[0]; A_.default_value = 1.0 if rv == "x" else 0.0
    for o in [Gr["helmet"]] + list(bpy.data.objects):
        pass
    showgear = rv != "x"
    for o in bpy.data.objects:
        if o.name.startswith(("helmet", "hans", "tether", "harness", "seat", "clip")):
            o.hide_render = not showgear
    if view == "side":
        cam.location = (0.25, -2.6, 0.3); tgt = (0.3, 0, 0.25); cam.data.lens = 40
    elif view == "q":
        cam.location = (1.7, -1.4, 0.75); tgt = (0.25, 0, 0.3); cam.data.lens = 40
    else:  # head close
        cam.location = (0.45, -0.55, 0.85); tgt = (0.0, 0, 0.62); cam.data.lens = 45
    cam.rotation_euler = look_at_rot(cam.location, tgt)
    sc.render.filepath = f"{ROOT}/previews/drv_{k}.png"
    bpy.ops.render.render(write_still=True)
