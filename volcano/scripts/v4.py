"""SCENE 4 (frames 421-750, 0:14-0:25): WHAT HAPPENS TO YOUR SKIN?
4A f421-545: extreme close-up of the character next to the glowing lake; radiant heat reddens the skin.
4B f546-750: 3D skin cross-section (epidermis / dermis / hypodermis) under radiant heat -> 1st, 2nd, 3rd degree burn depth."""
import sys, math, json, random
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
from vol import world as W, util as U

F0, F1 = 421, 750
FB = 546
sc = reset_scene()
E = W.build_environment((F0, FB)); E["glowL"].rotation_euler = (math.pi, 0, 0)
H = build_human(anatomy=False); root = H["root"]; set_reveal(H, None, 0.0)
rim = light("char_rim", 'AREA', (4, -4, 10), (0, 0, 0), energy=500, size=6, color=(0.7, 0.8, 1.0))
heat_l = light("heat_light", 'AREA', (0, 0, 0), (math.pi, 0, 0), energy=1500, size=9, color=(1.0, 0.38, 0.08))

# ------------------------------------------------------------------ 4A: character near the lava
ZC = 5.0
for f in range(F0 - 1, FB + 2):
    u = (f - F0) / 125.0
    pose(H, fall_spec(1.15 + 0.03 * u, 0.3, 0.8), f)
    root.location = (0, 0, ZC + 0.15 * math.sin(u * 2)); root.rotation_euler = (0.55, 0.85, 2.45 + 0.1 * u)
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    heat_l.location = (0, 0, ZC - 3.2); heat_l.keyframe_insert("location", frame=f)
    heat_l.data.energy = 350 + 1100 * smoothstep(F0, FB, f); heat_l.data.keyframe_insert("energy", frame=f)
fm = H["M"]["face"]; pf = principled(fm)
pf.inputs["Emission Color"].default_value = (1.0, 0.12, 0.02, 1)
for f, v in ((F0 - 1, 0.0), (440, 0.0), (545, 0.28)):
    pf.inputs["Emission Strength"].default_value = v; pf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
W.embers(F0 - 1, FB + 1, n=80, rmax=70, zmax=40, speed=(1.0, 3.0), size=0.05, time_scale=lambda f: (f - F0) / 30.0 * 0.25)
W.smoke_puffs(F0 - 1, FB + 1, n=12, rmin=30, rmax=120, zmin=3, zmax=40, size=(20, 40), opacity=(0.04, 0.09), rise=1.0, seed=31)

# ------------------------------------------------------------------ 4B: skin cross-section (far below the crater, own lighting)
SX, SZ = 0.0, -1000.0
def L(x, y, z): return Vector((SX + x, y, SZ + z))
def layer_mat(name, c0, c1, c2, rough=0.5, sss=0.0):
    m = mat(name, c0, rough=rough)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    k1 = nodes.new("ShaderNodeValue"); k1.name = "K1"; k2 = nodes.new("ShaderNodeValue"); k2.name = "K2"; h = nodes.new("ShaderNodeValue"); h.name = "HEAT"
    m1 = nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'; links.new(k1.outputs[0], m1.inputs[0]); m1.inputs[6].default_value = (*c0, 1); m1.inputs[7].default_value = (*c1, 1)
    m2 = nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'; links.new(k2.outputs[0], m2.inputs[0]); links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (*c2, 1)
    links.new(m2.outputs[2], p.inputs["Base Color"])
    p.inputs["Emission Color"].default_value = (1.0, 0.18, 0.03, 1)
    links.new(h.outputs[0], p.inputs["Emission Strength"])
    return m
def key_m(m, node, f, v):
    n = m.node_tree.nodes[node]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)

M_epi = layer_mat("epidermis", (0.78, 0.52, 0.40), (0.85, 0.22, 0.16), (0.09, 0.04, 0.03), 0.4)
M_der = layer_mat("dermis", (0.80, 0.36, 0.36), (0.88, 0.14, 0.12), (0.72, 0.62, 0.55), 0.5)
M_fat = layer_mat("hypodermis", (0.95, 0.78, 0.32), (0.95, 0.65, 0.25), (0.82, 0.75, 0.55), 0.35)
M_ves = layer_mat("vessel", (0.7, 0.04, 0.05), (0.9, 0.05, 0.05), (0.25, 0.12, 0.1), 0.3)
M_vein = layer_mat("vein", (0.12, 0.2, 0.62), (0.35, 0.1, 0.4), (0.18, 0.15, 0.2), 0.3)
M_hair = mat("hair_shaft", (0.06, 0.035, 0.02), rough=0.4)
M_gland = layer_mat("gland", (0.95, 0.88, 0.55), (0.95, 0.6, 0.35), (0.35, 0.3, 0.25), 0.35)
M_nerve = layer_mat("nerve", (1.0, 0.85, 0.2), (1.0, 0.7, 0.2), (0.3, 0.28, 0.2), 0.3)
M_blister = mat("blister", (0.95, 0.85, 0.7), rough=0.12, transmission=0.6, coat=1.0); principled(M_blister).inputs["Alpha"].default_value = 0.55
M_pore = mat("slab_dark", (0.02, 0.02, 0.025), rough=0.9)

def box(name, x0, x1, y0, y1, z0, z1, m):
    bm = bmesh.new(); box_bm(bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0))
    o = obj_from_bm(name, bm, [m], smooth=False); o.location = L(0, 0, 0); return o
XW, YF, YB = 1.6, -0.8, 0.25
epi = box("epidermis", -XW, XW, YF, YB, -0.13, 0.0, M_epi)
der = box("dermis", -XW, XW, YF, YB, -1.25, -0.13, M_der)
fat = box("hypodermis", -XW, XW, YF, YB, -2.35, -1.25, M_fat)
# papillary ridge on the epidermis/dermis boundary is suggested by a wavy strip
rid = tube("ridge", [L(x, YF - 0.002, -0.13 + 0.035 * math.sin(x * 9)) for x in [(-XW + i * 3.2 / 60) for i in range(61)]], 0.012, [M_epi], 6)
def tubev(name, ctrl, radii, m, n=10, steps=5):
    pts = catmull(ctrl, steps); N = len(pts)
    rr = [radii[min(len(radii) - 1, int(i / (N - 1) * (len(radii) - 1)))] if len(radii) == 1 else
          radii[int(i / (N - 1) * (len(radii) - 1))] * (1 - (i / (N - 1) * (len(radii) - 1)) % 1) + radii[min(len(radii) - 1, int(i / (N - 1) * (len(radii) - 1)) + 1)] * ((i / (N - 1) * (len(radii) - 1)) % 1) for i in range(N)]
    return tube(name, pts, rr, [m], n)
# hair follicle + shaft
HX = -0.35
fol = tubev("follicle", [L(HX, YF + 0.02, -0.95), L(HX + 0.02, YF, -0.6), L(HX, YF, -0.2), L(HX, YF, 0.0)], [0.07, 0.06, 0.05, 0.04], M_gland, 14)
bulb = ellipsoid("bulb", L(HX, YF + 0.02, -0.98), (0.11, 0.09, 0.12), [M_gland], 18, 10)
shaft = tubev("hair", [L(HX, YF, -0.9), L(HX, YF, -0.2), L(HX + 0.01, YF, 0.2), L(HX + 0.08, YF, 0.65)], [0.02, 0.025, 0.022, 0.012], M_hair, 8)
seb = ellipsoid("sebaceous", L(HX + 0.22, YF + 0.01, -0.45), (0.1, 0.05, 0.14), [M_gland], 16, 10)
seb2 = ellipsoid("sebaceous2", L(HX - 0.20, YF + 0.01, -0.5), (0.09, 0.05, 0.12), [M_gland], 16, 10)
# sweat gland: coil + duct
SXg = 0.6
coil = [L(SXg + 0.12 * math.cos(a), YF + 0.01, -1.05 + 0.34 * (a / (14 * math.pi)) + 0.12 * math.sin(a)) for a in [i * 0.35 for i in range(0, 41)]]
gl = tube("sweat_coil", coil, 0.028, [M_gland], 8)
duct = tube("sweat_duct", catmull([L(SXg, YF + 0.01, -0.75), L(SXg + 0.06, YF, -0.5), L(SXg - 0.05, YF, -0.28), L(SXg + 0.03, YF, -0.1), L(SXg, YF, 0.0)], 5), 0.022, [M_gland], 8)
# blood vessels: artery, vein, ascending capillary loops
art = tube("artery", [L(-XW + i * 3.2 / 40, YF, -1.2 + 0.03 * math.sin(i * 0.7)) for i in range(41)], 0.075, [M_ves], 12)
vein = tube("vein", [L(-XW + i * 3.2 / 40, YF, -1.4 + 0.035 * math.sin(i * 0.5 + 1)) for i in range(41)], 0.09, [M_vein], 12)
caps = []
for k, x in enumerate((-1.2, -0.75, -0.05, 0.3, 0.95, 1.3)):
    caps.append(tube(f"cap{k}", catmull([L(x, YF, -1.2), L(x + 0.04, YF, -0.9), L(x + 0.02, YF, -0.45), L(x + 0.08, YF, -0.2), L(x + 0.14, YF, -0.18), L(x + 0.16, YF, -0.4), L(x + 0.11, YF, -0.9), L(x + 0.12, YF, -1.38)], 4), 0.025, [M_ves], 8))
nerves = []
for k, x in enumerate((-0.95, 0.05, 1.1)):
    nerves.append(tube(f"nerve{k}", catmull([L(x, YF, -1.3), L(x + 0.05, YF, -0.8), L(x - 0.03, YF, -0.4), L(x + 0.02, YF, -0.17)], 5), 0.012, [M_nerve], 6))
    nerves.append(ellipsoid(f"nerve_end{k}", L(x + 0.02, YF, -0.17), (0.03, 0.02, 0.045), [M_nerve], 12, 8))
rng = random.Random(4)
fats = []
for i in range(9):
    for j, zc in enumerate((-1.62, -1.95)):
        x = -1.4 + i * 0.35 + (0.17 if j else 0); r = rng.uniform(0.15, 0.2)
        fats.append(ellipsoid(f"fat{i}_{j}", L(x, YF + 0.02, zc), (r, 0.09, r * 0.9), [M_fat], 18, 10))
# blisters between epidermis and dermis (grow during 2nd degree)
blis = [ellipsoid(f"blister{k}", L(bx, YF + 0.01, -0.12), (0.001, 0.001, 0.001), [M_blister], 20, 12) for k, bx in enumerate((-1.1, 0.15, 1.0))]
bsz = [(0.34, 0.07, 0.16), (0.46, 0.07, 0.21), (0.3, 0.07, 0.14)]
# ---- animation of the burn: K1 (redness/inflammation) f580-640, K2 (charring/coagulation) f690-745, blisters f625-690
for m_ in (M_epi, M_der, M_fat, M_ves, M_vein, M_gland, M_nerve):
    for f, k1, k2, hh in ((F0 - 1, 0, 0, 0), (572, 0, 0, 0), (600, 0.35, 0, 0.0), (640, 1.0, 0, 0.0), (690, 1.0, 0.1, 0.0), (745, 1.0, 1.0, 0.0), (752, 1.0, 1.0, 0.0)):
        key_m(m_, "K1", f, k1); key_m(m_, "K2", f, k2); key_m(m_, "HEAT", f, hh)
# epidermis and dermis react first, deeper layers later
for f, v in ((F0 - 1, 0), (572, 0), (600, 0.6), (640, 1.5), (690, 2.5), (745, 3.0)):
    key_m(M_epi, "HEAT", f, v * 0.5); key_m(M_der, "HEAT", f, max(0, v - 1.2) * 0.6)
for m_ in (M_fat, M_ves, M_vein):    # keyed K1 only after 3rd degree reaches them
    for f, k1, k2 in ((F0 - 1, 0, 0), (690, 0, 0), (720, 0.6, 0.3), (748, 1.0, 1.0)):
        key_m(m_, "K1", f, k1); key_m(m_, "K2", f, k2)
for b, (sx, sy, sz) in zip(blis, bsz):
    for f in range(F0 - 1, F1 + 3):
        g = smoothstep(625, 668, f) * (1 + 0.05 * math.sin(f * 0.25) * smoothstep(668, 700, f))
        b.scale = (max(1e-3, sx * g), max(1e-3, sy * g), max(1e-3, sz * g)); b.keyframe_insert("scale", frame=f)
# dilating vessels (heat response) : scale tube thickness via object scale in y/z is not uniform -> slight pulse on whole network
for o in caps + [art]:
    for f in (F0 - 1, 600, 650, 700):
        o.scale = (1, 1, 1) if f < 600 else (1, 1.0, 1.0); o.keyframe_insert("scale", frame=f)
# radiant heat rays
ray_m = emit_mat("heat_ray", (1.0, 0.35, 0.05), 7.0)
rays = []
for i in range(70):
    bm = bmesh.new(); tube_bm(bm, [(0, 0, 0), (0, 0, 0.9)], 0.02, 5)
    o = obj_from_bm(f"ray{i}", bm, [ray_m]); o.visible_shadow = False
    x = rng.uniform(-1.5, 1.5); y = rng.uniform(-0.75, 0.2); z0 = rng.uniform(0, 5); v = rng.uniform(2.5, 4.5)
    for f in range(F0 - 1, F1 + 3):
        t = (f - 572) / 30.0
        on = smoothstep(572, 590, f) * (1 - smoothstep(742, 750, f))
        zz = (z0 - v * max(t, 0)) % 5.0
        o.location = L(x, y, zz + 0.05); o.scale = (1, 1, max(1e-4, on * (0.4 + 0.6 * math.sin(f * 0.3 + i))))
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    from f1.core import _fcurves
    for fc in _fcurves(o.animation_data.action):
        if fc.data_path == "location":
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    rays.append(o)
bm = bmesh.new(); box_bm(bm, (0, 0, 0), (14, 0.05, 9))
bd = obj_from_bm("backdrop", bm, [emit_mat("backdrop", (0.025, 0.04, 0.07), 0.6)], smooth=False); bd.location = L(0, 2.2, -1.0)
# slab lighting
light("slab_key", 'AREA', L(-2.5, -4.5, 1.2), energy=520, size=3, color=(1.0, 0.95, 0.88), target=L(0, YF, -1.0))
light("slab_rim", 'AREA', L(3.0, -1.0, 2.5), energy=300, size=3, color=(0.5, 0.7, 1.0), target=L(0, YF, -1.0))
hl2 = light("slab_heat", 'AREA', L(0, -1.5, 3.2), (math.radians(165), 0, 0), energy=0, size=3.4, color=(1.0, 0.35, 0.05))
for f, v in ((F0 - 1, 0), (572, 0), (610, 900), (700, 2600), (752, 3000)):
    hl2.data.energy = v; hl2.data.keyframe_insert("energy", frame=f)
# interior glow when the glow hits the surface
# ---- cameras
camA = U.shot_camera("cam4A", F0, 55); camB = U.shot_camera("cam4B", FB, 35)
pcm = Vector((0, 0, ZC))
for f in range(F0 - 1, FB + 2):
    u = (f - F0) / 125.0; e = ease_in_out(min(1.0, max(0.0, u)))
    Mr = Matrix.LocRotScale(Vector((0, 0, ZC + 0.15 * math.sin(u * 2))), Euler((0.55, 0.85, 2.45 + 0.1 * u)).to_quaternion(), Vector((1, 1, 1)))
    head_w = Mr @ HEAD_C
    face_d = (Mr.to_3x3() @ Vector((1, 0, 0))).normalized()          # direction the face looks
    side_d = (Mr.to_3x3() @ Vector((0, 1, 0))).normalized()
    up_d = (Mr.to_3x3() @ Vector((0, 0, 1))).normalized()
    ang = math.radians(-8 + 62 * e)
    dirv = (face_d * math.cos(ang) + side_d * math.sin(ang)).normalized()
    loc = head_w + dirv * (0.95 - 0.30 * e) + up_d * 0.10
    key_cam(camA, f, loc, head_w + side_d * 0.0 + up_d * 0.0, 62 + 14 * e)
    camA.data.dof.focus_distance = (loc - head_w).length; camA.data.dof.keyframe_insert("focus_distance", frame=f)
U.dof(camA, None, fstop=2.0)
kb = [(FB, (0.0, -7.0, -1.0), (0, YF, -1.0), 30), (600, (-0.1, -4.4, -0.9), (-0.1, YF, -0.9), 35), (660, (0.2, -2.8, -0.75), (0.1, YF, -0.75), 40),
      (720, (0.5, -2.9, -1.4), (0.5, YF, -1.4), 38), (752, (0.2, -4.6, -1.2), (0.1, YF, -1.2), 34)]
for f in range(FB - 1, F1 + 3):
    for (fa, la, ta, lea), (fb, lb, tb, leb) in zip(kb[:-1], kb[1:]):
        if fa <= max(f, FB) <= fb:
            u = ease_in_out((max(f, FB) - fa) / (fb - fa))
            key_cam(camB, f, L(*la).lerp(L(*lb), u), L(*ta).lerp(L(*tb), u), lea + (leb - lea) * u)
            break
U.setup(sc, F0, F1, "v4", samples=12, motion_blur=False, bounces=24)
bpy.context.scene.cycles.use_adaptive_sampling = True
for o in bpy.data.objects:
    if o.name.startswith(("ray", "blister")): o.visible_shadow = False
# anchors for 2D labels (screen positions)
from f1 import studio as St
sc.frame_start, sc.frame_end = F0, F1
pts = {"epi": lambda f: L(1.25, YF, -0.07), "der": lambda f: L(1.25, YF, -0.7), "fat": lambda f: L(1.25, YF, -1.8),
       "hair": lambda f: L(HX + 0.08, YF, 0.5), "sweat": lambda f: L(SXg, YF, -1.05), "vessel": lambda f: L(-1.2, YF, -1.2),
       "nerve": lambda f: L(1.1, YF, -0.5), "blister": lambda f: L(0.15, YF, -0.1), "face": lambda f: (Matrix.LocRotScale(Vector((0, 0, ZC)), Euler((0.55, 0.85, 2.45)).to_quaternion(), Vector((1, 1, 1))) @ HEAD_C)}
St.export_anchors(sc, U.active_camera, pts, F0, F1, U.V + "/renders/anchors_v4.json")
U.run_render(sc, sys.argv)
