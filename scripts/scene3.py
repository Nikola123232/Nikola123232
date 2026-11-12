"""SCENE 3 (0:18-0:33, frames 541-990): inside the body.
3A f541-620 ghost car, suited driver; harness glows ("seat belts restrain your body"), skin turns to x-ray.
3B f621-760 side view: speed lines stop -> deceleration pulse; DECELERATION / INERTIA / HARNESS arrows.
3C f761-990 close orbit: brain (concussion), cervical spine (neck injury), abdomen (internal trauma) glow."""
import sys, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from mathutils import Vector, Matrix, Euler
from f1.core import *
from f1 import car as C, anatomy as A, gear as G, studio as St, world as Wd

F0, F1 = 541, 990
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
sc.frame_start, sc.frame_end = F0, F1
floor, floor_m = St.build_studio()
St.studio_lights((2.0, 0, 0.5), key=260, rim=380)
P = C.build_car(font=None)
St.ghost_car(P, strength=0.35)
bpy.data.materials["ghost_car"].node_tree.nodes["Layer Weight"].inputs[0].default_value = 0.12
for o in list(bpy.data.objects):
    if o.name.startswith(("sidepod_R", "inlet_lip_-1", "mirror_-1", "mirror_glass_-1", "mirror_stalk_-1", "wheel_FR", "wheel_RR")):
        o.hide_render = True
D = A.build_driver(anatomy=True)
Gr = G.build_gear(D)
D["root"].location, D["root"].rotation_euler = A.BODY_IN_CAR
M = D["M"]
bpy.context.view_layer.update()

# ---- materials over time
key_reveal(M["skin"], E0, 0.0); key_reveal(M["skin"], 600, 0.0); key_reveal(M["skin"], 650, 1.0)
key_reveal(M["skull"], E0, 0.0); key_reveal(M["skull"], 628, 0.0); key_reveal(M["skull"], 660, 1.0)
hm = bpy.data.materials["harness"]
pb = principled(hm)
pb.inputs["Emission Color"].default_value = (1.0, 0.15, 0.05, 1)
for f, v in ((E0, 0), (552, 0), (566, 3.0), (600, 1.5), (630, 0.6), (700, 1.2), (720, 0.6), (E1, 0.6)):
    pb.inputs["Emission Strength"].default_value = v
    pb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# helmet/HANS hidden once we are inside the body
for o in bpy.data.objects:
    if o.name.startswith(("helmet", "hans", "tether", "clip")):
        key_vis(o, E0, True); key_vis(o, 620, True); key_vis(o, 621, False)

# ---- deceleration events
organs = [o for k, o in D["organs"].items()] + [bpy.data.objects[n] for n in bpy.data.objects.keys() if n.startswith("bronchus")]
pose = St.Pose(D, organs, D["brain"])
pose.add(690, 50, torso=0.045, torso_pitch=6, neck=16, head=10, organ=0.016, brain=0.007)
pose.add(800, 50, torso=0.04, torso_pitch=5, neck=14, head=9, organ=0.014, brain=0.007)
pose.add(905, 50, torso=0.04, torso_pitch=5, neck=14, head=9, organ=0.014, brain=0.006)
pose.key(E0, E1)
St.speed_lines(E0, E1, 688, n=70, area=(-4, 9, -3.5, 3.5), speed=0.9)
gm = floor_m.node_tree.nodes["GridMap"]
for f in range(E0, E1 + 1):
    v = 0.9 * (1 - smoothstep(686, 694, f))
    off = gm.inputs["Location"].default_value[0]
    gm.inputs["Location"].default_value[0] = off + v if f > E0 else 0.0
    gm.inputs["Location"].keyframe_insert("default_value", frame=f, index=0)

# ---- arrows (car frame)
BM = Matrix.LocRotScale(Vector(A.BODY_IN_CAR[0]), Euler(A.BODY_IN_CAR[1]).to_quaternion(), Vector((1, 1, 1)))
def bodyp(p):
    return BM @ Vector(p)
arrows = {}
def mk(name, origin, direction, length, color, windows, radius=0.016, strength=1.4):
    a = St.arrow(name, length, radius, color, strength)
    a.location = origin
    a.rotation_euler = Vector((1, 0, 0)).rotation_difference(Vector(direction).normalized()).to_euler()
    St.key_arrow(a, windows)
    arrows[name] = a
    return a
RED, YEL, BLU = (1.0, 0.05, 0.03), (1.0, 0.55, 0.0), (0.05, 0.35, 1.0)
mk("decel", Vector((3.15, 0, 1.28)), (-1, 0, 0), 1.1, RED, [(684, 990)], 0.028, 1.8)
mk("inertia_brain", bodyp((0.13, 0, 0.80)), (1, 0, 0), 0.26, YEL, [(640, 990)])
mk("inertia_chest", bodyp((0.18, 0, 0.42)), (1, 0, 0), 0.28, YEL, [(672, 990)])
mk("inertia_abd", bodyp((0.17, 0, 0.20)), (1, 0, 0), 0.26, YEL, [(676, 990)])
for s in (1, -1):
    mk(f"harness_sh{s}", bodyp((0.22, s * 0.09, 0.50)), (-1, 0, -0.25), 0.18, BLU, [(598, 990)], 0.013)
    mk(f"harness_hip{s}", bodyp((0.26, s * 0.14, 0.12)), (-1, 0, 0.1), 0.18, BLU, [(604, 990)], 0.013)

# ---- injury glows
sp = A.spine_points()
glow_brain = St.glow_mat("glow_brain", (1.0, 0.1, 0.06), 5)
gb = ellipsoid("glow_brain_shell", A.HEAD_C + Vector((-0.008, 0, 0.012)), (0.088, 0.071, 0.068), [glow_brain], 32, 16)
A.parent_to_bone(gb, D["arm"], "head")
glow_neck = St.glow_mat("glow_neck", (1.0, 0.15, 0.05), 5)
for bone, idx in (("neck1", range(17, 21)), ("neck2", range(20, 24))):
    pts = [sp[i][0] for i in idx]
    o = tube(f"glow_neck_{bone}", pts, 0.026, [glow_neck], 16)
    A.parent_to_bone(o, D["arm"], bone)
glow_abd = St.glow_mat("glow_abd", (1.0, 0.2, 0.05), 4)
ga = ellipsoid("glow_abd_shell", (0.035, 0.0, 0.22), (0.1, 0.13, 0.12), [glow_abd], 32, 16)
A.parent_to_bone(ga, D["arm"], "spine")
St.key_glow_windows(glow_brain, [(806, 870)], E0, E1, 1.0)
St.key_glow_windows(glow_neck, [(836, 885)], E0, E1, 1.0)
St.key_glow_windows(glow_abd, [(874, 990)], E0, E1, 0.9)

# ---- cameras
camA = Wd.shot_camera("cam3A", F0, 35)
camB = Wd.shot_camera("cam3B", 621, 40)
camC = Wd.shot_camera("cam3C", 761, 40)
c0 = Vector((2.05, 0, 0.5))
for f in range(E0, 623):
    u = ease_in_out((f - F0) / 80)
    ang = math.radians(-35 - 30 * u)
    r = 3.3 - 0.6 * u
    loc = c0 + Vector((r * math.cos(ang), r * math.sin(ang), 1.25 - 0.3 * u))
    key_cam(camA, f, loc, c0 + Vector((0, 0, 0.1 - 0.05 * u)), 32 + 4 * u)
for f in range(619, 763):
    u = ease_in_out((f - 621) / 140)
    loc = Vector((2.25 - 0.15 * u, -2.75 + 0.35 * u, 0.75 + 0.05 * u))
    key_cam(camB, f, loc, Vector((2.15, 0, 0.62)), 34)
path = [(759, (3.0, -1.6, 1.05), (1.93, 0, 0.73), 38), (850, (2.75, -1.3, 0.9), (1.92, 0, 0.66), 40),
        (900, (2.8, -1.5, 0.8), (1.98, 0, 0.55), 38), (992, (3.2, -2.0, 0.8), (2.05, 0, 0.45), 36)]
for f in range(759, E1 + 1):
    for (fa, la, ta, lea), (fb, lb, tb, leb) in zip(path[:-1], path[1:]):
        if fa <= f <= fb:
            u = ease_in_out((f - fa) / (fb - fa))
            key_cam(camC, f, Vector(la).lerp(Vector(lb), u), Vector(ta).lerp(Vector(tb), u), lea + (leb - lea) * u)
            break

# ---- render setup + anchors for 2D callouts
render_settings(sc, (720, 1280), samples=10, motion_blur=False, transparent_bounces=20)
St.no_shadow_translucent()
sc.render.filepath = f"{ROOT}/renders/s3/####"
pts = {
    "brain": lambda f: bpy.data.objects["brain"].matrix_world.translation + Vector((0, 0, 0.02)),
    "heart": lambda f: bpy.data.objects["heart"].matrix_world.translation,
    "lungs": lambda f: bpy.data.objects["lung_1"].matrix_world.translation,
    "abdomen": lambda f: bpy.data.objects["glow_abd_shell"].matrix_world.translation,
    "neck": lambda f: D["arm"].matrix_world @ D["arm"].pose.bones["neck1"].tail,
    "harness": lambda f: bodyp((0.13, -0.08, 0.40)),
    "decel": lambda f: Vector((2.6, 0, 1.36)),
    "inertia": lambda f: bodyp((0.25, 0, 0.30)),
}
St.export_anchors(sc, Wd.active_camera, pts, F0, F1, ROOT + "/renders/anchors_s3.json")
Wd.run_render(sc, sys.argv)
