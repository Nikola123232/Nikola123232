import sys, math; sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
sc = reset_scene(); render_settings(sc, (540, 960), samples=24, transparent_bounces=24)
world_color((0.03, 0.035, 0.05), 1.0)
light("key", 'AREA', (2.5, -2.5, 2.5), energy=400, size=2, color=(1, 0.8, 0.6), target=(0, 0, 0.3))
light("rim", 'AREA', (-2.5, 2.0, 2.0), energy=300, size=2, color=(0.6, 0.8, 1), target=(0, 0, 0.3))
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -1.2)); bpy.context.object.data.materials.append(mat("fl", (0.05, 0.05, 0.05), rough=0.8))
H = build_human(anatomy=True)
cam = camera("cam", 50); sc.camera = cam
mode = sys.argv[sys.argv.index("--")+1:]
def shot(nm, loc, tgt, lens):
    cam.location = loc; cam.rotation_euler = look_at_rot(loc, tgt); cam.data.lens = lens
    sc.render.filepath = f"{ROOT}/volcano/previews/h_{nm}.png"; bpy.ops.render.render(write_still=True)
for md in mode:
    if md == "stand":
        pose(H, stand_spec()); set_reveal(H, None, 0.0)
        H["root"].rotation_euler = (0, 0, 0)
        for o in H["anat"]: o.hide_render = True
        shot("stand_front", (3.6, -0.4, 0.15), (0, 0, 0.1), 60)
        shot("face", (0.7, -0.35, 0.82), (0.03, 0, 0.74), 70)
        shot("torso", (1.6, -1.2, 0.5), (0, 0, 0.3), 60)
    if md == "fall":
        pose(H, fall_spec(0.3)); H["root"].rotation_euler = (0.3, 0.5, 0.4)
        for o in H["anat"]: o.hide_render = True
        shot("fall", (2.6, -2.2, 0.8), (0, 0, 0.0), 55)
    if md == "xray":
        pose(H, stand_spec()); H["root"].rotation_euler = (0, 0, 0)
        for o in H["anat"]: o.hide_render = False
        for m in H["M"]["rev"]: m.node_tree.nodes["Reveal"].outputs[0].default_value = 1.0
        shot("xray", (3.6, -1.0, 0.25), (0, 0, 0.0), 60)
