import sys, math; sys.path.insert(0, "/home/user/Nikola123232/sleep/scripts")
from sl.man import *
ROOT_ = "/home/user/Nikola123232/"
sc = reset_scene(); render_settings(sc, (540, 960), samples=40)
try:
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
world_color((0.01, 0.012, 0.018), 1.0)
light("key", 'AREA', (1.3, -0.9, 1.2), energy=14, size=0.6, color=(1.0, 0.75, 0.5), target=(0.05, 0, 0.75))
light("fill", 'AREA', (1.0, 1.2, 0.9), energy=6, size=1.0, color=(0.55, 0.7, 1.0), target=(0.05, 0, 0.7))
light("rim", 'AREA', (-1.2, 0.8, 1.3), energy=9, size=0.6, color=(0.6, 0.75, 1.0), target=(0.0, 0, 0.7))
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.5)); bpy.context.object.data.materials.append(mat("fl", (0.04, 0.04, 0.045), rough=0.8))
H = build_man()
set_skin_state(H, 0.3, 0.7, 0.0, 0.5, 0.45)
pose(H, seated_spec(0.05, (0.12, 0.0, 0.03)))
cam = camera("cam", 85); sc.camera = cam
def shot(nm, loc, tgt, lens):
    cam.location = loc; cam.rotation_euler = look_at_rot(loc, tgt); cam.data.lens = lens
    sc.render.filepath = f"{ROOT_}sleep/previews/m_{nm}.png"; bpy.ops.render.render(write_still=True)
set_face(H, (0.0, 0.0), 1.0, 0.45, 0.0034, -0.002)
shot("face", (1.0, -0.35, 0.80), (0.03, 0.0, 0.735), 85)
set_face(H, (0.25, 0.08), 0.35, 0.6, 0.0042, -0.003)
shot("face2", (0.40, -0.05, 0.745), (0.077, 0.034, 0.733), 135)
set_face(H, (0.0, 0.0), 1.0, 0.3)
shot("body", (3.2, -2.0, 0.9), (0.2, 0, 0.35), 50)
