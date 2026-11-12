"""SCENE 4 (0:33-0:45, frames 991-1350): head and neck.
4A f991-1080 head close-up: helmet + skull translucent, brain shifts forward inside the skull, impact zones glow.
4B f1081-1190 neck: without a head restraint the head whips forward, cervical spine highlighted red; helmet turns solid.
4C f1191-1350 HANS device appears, tethers catch the helmet: much smaller motion, neck highlight green."""
import sys, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from mathutils import Vector, Matrix, Euler
from f1.core import *
from f1 import car as C, anatomy as A, gear as G, studio as St, world as Wd

F0, F1 = 991, 1350
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
sc.frame_start, sc.frame_end = F0, F1
floor, floor_m = St.build_studio()
St.studio_lights((1.9, 0, 0.7), key=200, rim=320)
P = C.build_car(font=None)
St.ghost_car(P, strength=0.3)
bpy.data.materials["ghost_car"].node_tree.nodes["Layer Weight"].inputs[0].default_value = 0.12
for o in list(bpy.data.objects):
    if o.name.startswith(("sidepod_R", "inlet_lip_-1", "mirror_-1", "mirror_glass_-1", "mirror_stalk_-1", "wheel_FR", "wheel_RR",
                          "airbox", "shark_fin", "tcam")):
        o.hide_render = True
D = A.build_driver(anatomy=True)
Gr = G.build_gear(D)
D["root"].location, D["root"].rotation_euler = A.BODY_IN_CAR
M = D["M"]
arm = D["arm"]
bpy.context.view_layer.update()
key_reveal(M["skin"], E0, 1.0)
key_reveal(M["skull"], E0, 1.0)
# helmet: x-ray early, turns solid on "specialized helmets" (f1146-1175)
for mn in ("helmet_paint", "visor", "helmet_pad", "helmet_carbon"):
    m = add_reveal(bpy.data.materials[mn], (0.3, 0.7, 1.0), 0.25, power=0.15)
    key_reveal(m, E0, 1.0); key_reveal(m, 1146, 1.0); key_reveal(m, 1176, 0.0)
hm = bpy.data.materials["helmet_paint"]; pbh = principled(hm)
pbh.inputs["Emission Color"].default_value = (0.3, 0.8, 1.0, 1)
for f, v in ((E0, 0), (1150, 0), (1166, 0.8), (1195, 0)):
    pbh.inputs["Emission Strength"].default_value = v; pbh.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# HANS + tethers appear at "head-and-neck restraints"
hans_objs = [o for o in bpy.data.objects if o.name.startswith(("hans", "tether", "clip"))]
for o in hans_objs:
    key_vis(o, E0, False); key_vis(o, 1196, True)
gh = St.glow_mat("glow_hans", (0.2, 1.0, 0.45), 4)
hg = bpy.data.objects.new("hans_glow", Gr["hans"].data.copy()); link(hg)
hg.data.materials.clear(); hg.data.materials.append(gh)
sol = hg.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = 1
A.parent_to_bone(hg, arm, "spine")
St.key_glow_windows(gh, [(1196, 1240)], E0, E1, 1.0)
key_vis(hg, E0, False); key_vis(hg, 1196, True)
# harness hidden (not the focus); seat kept
for o in bpy.data.objects:
    if o.name.startswith(("harness", "seat")):
        o.hide_render = True

# ---- motion: brain shift (4A), big flexion without HANS (4B), restrained flexion with HANS (4C)
organs = [o for k, o in D["organs"].items()]
pose = St.Pose(D, organs, D["brain"])
pose.add(1008, 60, torso=0.02, torso_pitch=3, neck=10, head=6, organ=0.008, brain=0.010)
pose.add(1098, 60, torso=0.04, torso_pitch=4, neck=26, head=8, organ=0.012, brain=0.008)
pose.add(1250, 60, torso=0.035, torso_pitch=5, neck=12, head=5, organ=0.010, brain=0.004)
pose.key(E0, E1)

# ---- glows: coup (front) / contrecoup (back) on the brain, neck stress
gc = St.glow_mat("glow_coup", (1.0, 0.12, 0.05), 6)
for nm, off, win in (("coup", (0.07, 0, 0.0), [(1016, 1062)]), ("contrecoup", (-0.072, 0, 0.012), [(1030, 1070)])):
    m_ = gc if nm == "coup" else St.glow_mat("glow_cc", (1.0, 0.25, 0.05), 6)
    o = ellipsoid("glow_" + nm, A.HEAD_C + Vector(off), (0.03, 0.05, 0.045), [m_], 24, 12)
    A.parent_to_bone(o, arm, "head")
    St.key_glow_windows(m_, win, E0, E1, 1.0)
sp = A.spine_points()
gn_red = St.glow_mat("glow_neck", (1.0, 0.12, 0.05), 5)
gn_grn = St.glow_mat("glow_neck_ok", (0.15, 1.0, 0.4), 4)
for m_, win in ((gn_red, [(1100, 1170)]), (gn_grn, [(1252, 1330)])):
    for bone, idx in (("neck1", range(17, 21)), ("neck2", range(20, 24))):
        o = tube(f"{m_.name}_{bone}", [sp[i][0] for i in idx], 0.027 if m_ is gn_red else 0.031, [m_], 16)
        A.parent_to_bone(o, arm, bone)
    St.key_glow_windows(m_, win, E0, E1, 1.0)

# ---- cameras
camA = Wd.shot_camera("cam4A", F0, 50)
camB = Wd.shot_camera("cam4B", 1081, 45)
camC = Wd.shot_camera("cam4C", 1191, 42)
for f in range(E0, 1083):
    u = ease_in_out((f - F0) / 90)
    key_cam(camA, f, Vector((1.93, -1.0 + 0.2 * u, 0.84)), Vector((1.89, 0, 0.78)), 50)
for f in range(1079, 1193):
    u = ease_in_out((f - 1081) / 110)
    key_cam(camB, f, Vector((2.0 - 0.03 * u, -1.25 + 0.1 * u, 0.74 + 0.04 * u)), Vector((1.95, 0, 0.66)), 40)
for f in range(1189, E1 + 1):
    u = ease_in_out((f - 1191) / 159)
    ang = math.radians(-95 - 60 * u)
    c = Vector((1.86, 0, 0.66))
    r = 1.15 - 0.1 * u
    key_cam(camC, f, c + Vector((r * math.cos(ang), r * math.sin(ang), 0.32 + 0.1 * u)), c + Vector((0.02, 0, 0.02)), 40)

render_settings(sc, (720, 1280), samples=10, motion_blur=False, transparent_bounces=20)
St.no_shadow_translucent()
for o in bpy.data.objects:
    if o.name.startswith("glow_") or o.name == "hans_glow":
        o.visible_shadow = False
sc.render.filepath = f"{ROOT}/renders/s4/####"
pts = {
    "brain": lambda f: bpy.data.objects["brain"].matrix_world.translation + Vector((0, 0, 0.03)),
    "coup": lambda f: bpy.data.objects["glow_coup"].matrix_world.translation,
    "contrecoup": lambda f: bpy.data.objects["glow_contrecoup"].matrix_world.translation,
    "skull": lambda f: bpy.data.objects["skull"].matrix_world.translation + Vector((0, 0, 0.07)),
    "neck": lambda f: arm.matrix_world @ arm.pose.bones["neck1"].tail,
    "helmet": lambda f: bpy.data.objects["helmet"].matrix_world.translation + Vector((0, 0, 0.12)),
    "hans": lambda f: bpy.data.objects["hans"].matrix_world @ Vector((-0.1, 0, 0.55)),
    "tether": lambda f: bpy.data.objects["tether_-1"].matrix_world.translation,
}
St.export_anchors(sc, Wd.active_camera, pts, F0, F1, ROOT + "/renders/anchors_s4.json")
Wd.run_render(sc, sys.argv)
