"""SCENE 5 (frames 751-1110, 0:25-0:37): WHAT HAPPENS INSIDE YOUR BODY? Flight through the mouth and airways to the alveoli.
5A f751-808  x-ray head, hot gas streams toward the mouth
5B f809-1000 camera flies through mouth -> pharynx -> trachea -> carina -> bronchial tree -> alveoli (hot gas, toxic gas, falling O2)
5C f1001-1110 pull-out to the whole chest: inflamed lungs, brain losing oxygen"""
import sys, math, json, random
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
from vol import util as U, airway as AW
from f1 import studio as St
from f1.core import _fcurves

F0, F1 = 751, 1110
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
world_color((0.006, 0.008, 0.016), 1.0)
H = build_human(anatomy=True); arm = H["arm"]
pose(H, stand_spec())
set_reveal(H, None, 1.0)
M = H["M"]
for o in bpy.data.objects:
    if o.name == "lips":
        o.hide_render = True
for o in H["head"] + [H["skin"]] + [bpy.data.objects[n] for n in bpy.data.objects.keys() if n.startswith("lung")]:
    o.visible_shadow = False
# lungs -> translucent, glow turns red with inflammation
lx = xray_mat("lung_x", (1.0, 0.55, 0.6), 1.3, base_alpha=0.0, power=0.5)
em_lung = [n for n in lx.node_tree.nodes if n.type == 'EMISSION'][0]
for f, c in ((E0, (1.0, 0.55, 0.6)), (870, (1.0, 0.55, 0.6)), (960, (1.0, 0.12, 0.05)), (E1, (1.0, 0.1, 0.04))):
    em_lung.inputs[0].default_value = (*c, 1); em_lung.inputs[0].keyframe_insert("default_value", frame=f)
for k, o in H["organs"].items():
    if k.startswith("lung"):
        o.data.materials.clear(); o.data.materials.append(lx)
# brain loses oxygen
pb = principled(M["brain"])
for f, c in ((E0, (0.85, 0.48, 0.48)), (940, (0.85, 0.48, 0.48)), (1070, (0.30, 0.26, 0.34))):
    pb.inputs["Base Color"].default_value = (*c, 1); pb.inputs["Base Color"].keyframe_insert("default_value", frame=f)

skull_o = bpy.data.objects["skull"]
key_vis(skull_o, E0, True); key_vis(skull_o, 808, True); key_vis(skull_o, 809, False); key_vis(skull_o, 1004, False); key_vis(skull_o, 1005, True)
rib = bpy.data.objects["ribcage"]
key_vis(rib, E0, True); key_vis(rib, 958, True); key_vis(rib, 959, False); key_vis(rib, 1062, False); key_vis(rib, 1063, True)
# ------------------------------------------------------------------ airway
muc = AW.mucosa_mat()
A_ = AW.build_airway(muc)
for f, a, b in ((E0, 0, 0), (840, 0, 0), (900, 0.7, 0), (960, 1.0, 0), (1040, 1.0, 0.45), (E1, 1.0, 0.6)):
    AW.key_m(muc, "K1", f, a); AW.key_m(muc, "K2", f, b)
for o in (A_["main"], A_["tree"]):
    o.visible_shadow = True
# the translucent skin/skull would hide the tunnel from inside only if camera were outside; fine.

# ------------------------------------------------------------------ flow particles
rng = random.Random(7)
paths = A_["paths"]
mainp = A_["main_pts"]; mainr = A_["main_r"]
def pr(p, r):  # full path with a radius per point; prepend outside approach swirl radius
    return p, r
def local_r(r_list, idx):
    return r_list[min(idx, len(r_list) - 1)]
P_HOT = emit_mat("hot_gas", (1.0, 0.16, 0.015), 2.6)
P_TOX = emit_mat("toxic_gas", (0.25, 0.9, 0.08), 1.8)
P_O2 = emit_mat("oxygen", (0.15, 0.4, 1.0), 2.4)
def particles(name, mat_, n, window, speed, seed, size_k=1.0, only_main=False, fade=(10, 10)):
    rr = random.Random(seed); objs = []
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        o = obj_from_bm(f"{name}{i}", bm, [mat_], smooth=True); o.visible_shadow = False
        pts, rl = (mainp, mainr) if only_main else paths[rr.randrange(len(paths))]
        off = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1)))
        s0 = rr.random(); v = speed * rr.uniform(0.7, 1.3)
        for f in range(E0, E1 + 1):
            on = smoothstep(window[0], window[0] + fade[0], f) * (1 - smoothstep(window[1] - fade[1], window[1], f))
            t = (f - F0) / 30.0
            u = (s0 + v * t) % 1.0
            p, idx, Ltot = AW.sample_path(pts, u)
            r_ = rl[min(idx, len(rl) - 1)]
            rad = 0.045 if idx < 6 else r_
            offs = off.normalized() * rad * (0.8 if idx < 6 else 0.55) * rr.random() ** 0.5
            size = max(0.00018, min(0.0030, 0.00032 * (rad / 0.0098) ** 0.8)) * size_k
            o.location = p + offs; o.scale = (size * on + 1e-6,) * 3
            o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
        for fc in _fcurves(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
        objs.append(o)
    return objs
particles("hot", P_HOT, 130, (F0, 1000), 0.20, 1)
particles("tox", P_TOX, 100, (905, 1100), 0.22, 2, 1.0)
particles("o2", P_O2, 40, (940, 1090), 0.20, 3, 1.1, fade=(10, 14))

# ------------------------------------------------------------------ lights
light("key", 'AREA', (1.4, -1.5, 1.5), energy=160, size=1.6, color=(1, 0.85, 0.7), target=(0, 0, 0.5))
light("rim", 'AREA', (-1.5, 1.3, 1.3), energy=140, size=1.6, color=(0.5, 0.75, 1.0), target=(0, 0, 0.5))
light("fill", 'AREA', (1.0, 1.5, 0.4), energy=45, size=2, target=(0, 0, 0.5))

# ------------------------------------------------------------------ cameras
camA = U.shot_camera("cam5A", F0, 40); camB = U.shot_camera("cam5B", 809, 24); camC = U.shot_camera("cam5C", 951, 30)
full_path = max(paths, key=lambda pp: len(pp[0]))[0]
Ltot = sum((b - a).length for a, b in zip(full_path[:-1], full_path[1:]))
# arc-length of the lips along the path
acc = 0.0; u_lips = 0.0
for a, b in zip(full_path[:-1], full_path[1:]):
    acc += (b - a).length
    if (b - Vector((0.095, 0, 0.693))).length < 0.006:
        u_lips = acc / Ltot; break
u_lips = max(u_lips, 0.18)
def cam_on_path(u, ahead=0.012):
    p, i, _ = AW.sample_path(full_path, min(1.0, u)); q, _, _ = AW.sample_path(full_path, min(1.0, u + ahead / Ltot))
    return p, q
head_c = HEAD_C
for f in range(E0, 810):
    u = ease_in_out(min(1.0, max(0.0, (f - F0) / 57.0)))
    a = math.radians(-50 + 38 * u)
    loc = head_c + Vector((0.55 * math.cos(a) - 0.18 * u, 0.55 * math.sin(a), 0.02 - 0.05 * u))
    key_cam(camA, f, loc, head_c + Vector((0.02, 0, -0.045 * u)), 42 - 12 * u)
# inside
t0f, t1f = 809, 950
for f in range(808, 954):
    u = ease_in_out(min(1.0, max(0.0, (f - t0f) / (t1f - t0f))))
    uu = (u_lips - 0.05) + (0.74 - (u_lips - 0.05)) * u
    p, q = cam_on_path(uu, 0.012 if uu < 0.45 else 0.006)
    sway = Vector((math.sin(f * 0.11), math.cos(f * 0.09), 0)) * 0.0004
    key_cam(camB, f, p + sway, q, 26, roll=6 * math.sin(f * 0.04))
lamp = light("headlamp", 'POINT', (0, 0, 0), energy=0.0012, size=0.002, color=(1.0, 0.93, 0.85)); lamp.parent = camB
camB.data.clip_start = 0.0008
lamp.data.energy = 0.0012
for f in range(E0, E1 + 1):
    lamp.data.energy = 0.0012 if f < 954 else 0.0
    lamp.data.keyframe_insert("energy", frame=f)
    camB.data.keyframe_insert("clip_start", frame=f)
# pull-out: through the lung wall, close on the bronchial tree, then the whole chest
pend, qend = cam_on_path(0.74)
LC = Vector((0.0, 0.0, 0.42))
for f in range(949, E1 + 1):
    if f < 1000:
        u = ease_in_out((f - 950) / 50.0)
        loc = pend.lerp(Vector((0.36, -0.03, 0.44)), u); tgt = qend.lerp(LC, u); lens = 26 + 12 * u
    elif f < 1050:
        u = ease_in_out((f - 1000) / 50.0); a_ = math.radians(-4 - 50 * u)
        loc = LC + Vector((0.36 * math.cos(a_), 0.36 * math.sin(a_), 0.03 + 0.05 * u)); tgt = LC; lens = 38
    else:
        u = ease_in_out(min(1.0, (f - 1050) / 62.0)); a_ = math.radians(-54 - 6 * u)
        loc = (LC + Vector((0.36 * math.cos(a_), 0.36 * math.sin(a_), 0.08))).lerp(Vector((1.1 * math.cos(a_), 1.1 * math.sin(a_), 0.66)), u)
        tgt = LC.lerp(Vector((0.02, 0, 0.60)), u); lens = 38 - 4 * u
    key_cam(camC, f, loc, tgt, lens)

U.setup(sc, F0, F1, "v5", samples=12, motion_blur=False, bounces=24)
sc.cycles.volume_bounces = 0
# anchors for labels (outside views)
pts = {"mouth": lambda f: Vector((0.092, 0, 0.693)), "lungs": lambda f: Vector((0.0, -0.085, 0.43)), "brain": lambda f: head_c + Vector((0, 0, 0.02)),
       "trachea": lambda f: Vector((0.0, 0.012, 0.54)), "heart": lambda f: Vector((0.045, 0.018, 0.375))}
St.export_anchors(sc, U.active_camera, pts, F0, F1, U.V + "/renders/anchors_v5.json")
U.run_render(sc, sys.argv)
