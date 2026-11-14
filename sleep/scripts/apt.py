"""Apartment shots: hook (OTS, POV, eye push), 24h glass, 48h desk + microsleep, 72h hallway, 7-day orbit, ending."""
import sys, math, json, random, os
sys.path.insert(0, "/home/user/Nikola123232/sleep/scripts")
from sl.man import *
from sl.room import *
from sl import util as U
from sl.timeline import *
from f1.core import _fcurves

sc = reset_scene()
R = build_room(); L = build_room_lights()
H = build_man("man"); root = H["root"]; root.location = (SEAT.x, SEAT.y, SEAT.z)
DB = build_man("double", face_detail=False); droot = DB["root"]
HEAD_W = Vector((SEAT.x, SEAT.y, SEAT.z)) + HEAD_C
D = DESK

def interp(f, pts, ease_=True):
    if f <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts[:-1], pts[1:]):
        if a <= f <= b:
            t = (f - a) / max(1, b - a); t = t * t * (3 - 2 * t) if ease_ else t; return va + (vb - va) * t
    return pts[-1][1]
def noise1(f, sc_=1.0, seed=0): return noise.noise(Vector((f * sc_, seed * 7.3, 0.5)))

# ------------------------------------------------------------------ the glass (24 h scene) -- animation in world space
GL_START = Vector((D["x0"] + 0.06, 1.60, D["z"]))
F_TIP, F_LEAVE, F_HIT = 388, 400, 437
gl_m = bpy.data.materials.new("glass_mat"); gl_m.node_tree.nodes.clear(); _o = gl_m.node_tree.nodes.new("ShaderNodeOutputMaterial"); _p = gl_m.node_tree.nodes.new("ShaderNodeBsdfGlass"); _p.inputs["IOR"].default_value = 1.5; _p.inputs["Roughness"].default_value = 0.02; _p.inputs["Color"].default_value = (0.92, 0.97, 1.0, 1)
gl_m.node_tree.links.new(_p.outputs[0], _o.inputs[0])
wt_m = bpy.data.materials.new("water_mat"); wt_m.node_tree.nodes.clear(); _o = wt_m.node_tree.nodes.new("ShaderNodeOutputMaterial"); _p = wt_m.node_tree.nodes.new("ShaderNodeBsdfGlass"); _p.inputs["IOR"].default_value = 1.33; _p.inputs["Roughness"].default_value = 0.01; _p.inputs["Color"].default_value = (0.85, 0.95, 1.0, 1)
wt_m.node_tree.links.new(_p.outputs[0], _o.inputs[0])
bm = bmesh.new(); lathe_bm(bm, [(0.0, 0.0), (0.030, 0.0), (0.0305, 0.003), (0.0368, 0.110), (0.0356, 0.112), (0.0336, 0.014), (0.0, 0.014)], 40, 'Z'); tumbler = obj_from_bm("tumbler", bm, [gl_m], smooth=True)
bm = bmesh.new(); lathe_bm(bm, [(0.0, 0.0145), (0.0336, 0.0145), (0.0348, 0.072), (0.0, 0.072)], 40, 'Z'); water_v = obj_from_bm("tumbler_water", bm, [wt_m], smooth=True)
for o in (tumbler, water_v): o.visible_shadow = True
tumbler.rotation_mode = 'XYZ'; water_v.rotation_mode = 'XYZ'
rng = random.Random(4)
def glass_state(f):
    """position (of the base centre) and rotation_y of the tumbler in world space."""
    t = (f - F_TIP) / 30.0 * 0.34             # slow-motion factor 0.34
    edge = D["x0"]
    if f < F_TIP: return GL_START.copy(), 0.0, True
    # phase 1: slides outward and tilts over the edge
    ts = (F_LEAVE - F_TIP) / 30.0 * 0.34
    if f <= F_LEAVE:
        u = (f - F_TIP) / (F_LEAVE - F_TIP)
        x = GL_START.x - 0.012 - 0.065 * u * u; th = math.radians(8 + 78 * u ** 2.0)
        return Vector((x, GL_START.y, D["z"] + 0.006 * u)), th, True
    tf = (f - F_LEAVE) / 30.0 * 0.34
    x0 = GL_START.x - 0.012 - 0.065; th0 = math.radians(86); w = 5.5; vx = -0.35
    z = D["z"] + 0.006 - 0.5 * 9.81 * tf * tf
    x = x0 + vx * tf; th = th0 + w * tf
    floor = 0.045
    if z <= floor or f >= F_HIT: return Vector((x0 + vx * ((F_HIT - F_LEAVE) / 30.0 * 0.34), GL_START.y + 0.02, floor)), th, False
    return Vector((x, GL_START.y, z)), th, True
for f in range(0, 1342):
    pos, th, alive = glass_state(f)
    broke = f >= F_HIT
    for o in (tumbler, water_v):
        o.location = pos; o.rotation_euler = (0, th, 0.0); key_vis(o, f, not broke)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
fall_pos = glass_state(F_HIT - 1)[0]
# shards + droplets after the impact
shard_m = gl_m
def ballistic(p0, v0, w0, t0f, f, ground=0.004, rest=0.25, slow=0.34):
    t = max(0.0, (f - t0f) / 30.0 * slow); p = p0 + v0 * t + Vector((0, 0, -0.5 * 9.81 * t * t)); rot = w0 * t
    if p.z < ground:
        tb = (v0.z + math.sqrt(max(0, v0.z ** 2 + 2 * 9.81 * (p0.z - ground)))) / 9.81        # first ground time
        tt = t - tb
        if tt > 0:
            vz = rest * (-v0.z + 9.81 * tb)
            zz = vz * tt - 0.5 * 9.81 * tt * tt
            p = Vector((p0.x + v0.x * (tb + tt * 0.35 * 0.5), p0.y + v0.y * (tb + tt * 0.35 * 0.5), ground + max(0.0, zz)))
        else: p.z = ground
    return p, rot
for i in range(46):
    bm = bmesh.new(); n = rng.choice((3, 4)); r = rng.uniform(0.006, 0.022); pts = [(r * rng.uniform(0.5, 1.2) * math.cos(2 * math.pi * k / n), r * rng.uniform(0.5, 1.2) * math.sin(2 * math.pi * k / n)) for k in range(n)]
    top = [bm.verts.new((x, y, 0.0008)) for x, y in pts]; bot = [bm.verts.new((x, y, -0.0008)) for x, y in pts]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for k in range(n): bm.faces.new((top[k], top[(k + 1) % n], bot[(k + 1) % n], bot[k]))
    o = obj_from_bm(f"shard{i}", bm, [shard_m], smooth=False)
    v0 = Vector((rng.uniform(-0.6, 0.5), rng.uniform(-0.7, 0.7), rng.uniform(0.15, 0.9))); w0 = Vector((rng.uniform(-14, 14), rng.uniform(-14, 14), rng.uniform(-10, 10)))
    for f in range(0, 1342):
        if f < F_HIT: o.location = (0, 0, -9); o.scale = (1e-4,) * 3
        else:
            p_, r_ = ballistic(fall_pos + Vector((rng.uniform(-0.01, 0.01), 0, 0.0)), v0, w0, F_HIT, f); o.location = p_; o.rotation_euler = (r_.x, r_.y, r_.z); o.scale = (1, 1, 1)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
    rng.seed(i * 13 + 5)
drop_m = wt_m
for i in range(34):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = obj_from_bm(f"drop{i}", bm, [drop_m], smooth=True); o.visible_shadow = False
    v0 = Vector((rng.uniform(-0.5, 0.45), rng.uniform(-0.6, 0.6), rng.uniform(0.1, 0.8))); sz = rng.uniform(0.003, 0.008)
    for f in range(0, 1342):
        # droplets leave the glass as it tilts (from F_LEAVE) and again at the impact
        t0 = F_LEAVE if i < 14 else F_HIT; p0 = glass_state(t0)[0] + Vector((0, 0, 0.06))
        if f < t0: o.location = (0, 0, -9); o.scale = (1e-4,) * 3
        else:
            p_, r_ = ballistic(p0, v0 * (0.6 if i < 14 else 1.0), Vector((0, 0, 0)), t0, f, ground=0.004, rest=0.05); o.location = p_; o.scale = (sz, sz, sz * (0.6 if p_.z <= 0.0045 else 1.0))
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=1.0, segments=48); puddle = obj_from_bm("puddle", bm, [wt_m], smooth=True); puddle.visible_shadow = False
for f in range(0, 1342):
    g = max(0.0, (f - F_HIT - 2) / 70.0); r_ = 0.20 * (1 - math.exp(-g * 2.2)) if f >= F_HIT else 1e-4
    puddle.location = (fall_pos.x + 0.04, fall_pos.y, 0.0015); puddle.scale = (r_ + 1e-4, r_ * 0.8 + 1e-4, 1); puddle.keyframe_insert("location", frame=f); puddle.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ the man: behaviour per frame
BLINKS = [(6, 1.8), (146, 1.5), (440, 1.4), (468, 1.0), (500, 1.6), (516, 1.6), (534, 2.0), (700, 1.6), (742, 1.8), (790, 1.5), (960, 3.2), (1010, 2.8), (1066, 3.0), (1128, 3.4), (1250, 3.0)]
SKIN = [(1, dict(pale=0.30, bags=0.80, red=0.50)), (200, dict(pale=0.10, bags=0.25, red=0.18)), (500, dict(pale=0.20, bags=0.45, red=0.30)),
        (730, dict(pale=0.30, bags=0.65, red=0.42)), (930, dict(pale=0.42, bags=0.9, red=0.60)), (1340, dict(pale=0.45, bags=1.0, red=0.66))]
def skin_state(f):
    for (a, A_), (b, B_) in zip(SKIN[:-1], SKIN[1:]):
        if a <= f <= b:
            t = (f - a) / (b - a); return {k: A_[k] + (B_[k] - A_[k]) * t for k in A_}
    return SKIN[-1][1]
KB = Vector((D["x0"] + 0.14, 0, D["z"] + 0.03)) - Vector((SEAT.x, SEAT.y, SEAT.z))
def man_frame(f):
    d = dict(lean=0.05, lean_side=0.0, head=(0.0, 0.0, 0.0), gaze=(0.0, 0.0), droop=0.6, pupil=0.0034, brow=-0.002, handR=None, handL=None, openness=None)
    breath = 0.011 * math.sin(f / 30.0 * 2 * math.pi * 0.23)
    d["breath"] = breath
    sw = 0.012 * noise1(f, 0.012, 1)
    if f <= 120:                                           # hook: looks down at the laptop, slowly raises his eyes
        d["head"] = (interp(f, [(1, 0.40), (12, 0.40), (52, 0.03), (120, 0.03)]), interp(f, [(1, 0.0), (52, 0.04), (90, -0.04), (120, 0.0)]), 0.015)
        d["gaze"] = (interp(f, [(1, 0.0), (45, 0.02), (80, 0.14), (120, 0.0)]), interp(f, [(1, 0.28), (30, 0.20), (52, -0.05), (120, -0.02)])); d["droop"] = 0.62
    elif f <= 190:
        d["head"] = (0.03, 0.0, 0.0); d["gaze"] = (0.012 * math.sin(f * 0.2), -0.03 + 0.01 * math.sin(f * 0.13)); d["droop"] = interp(f, [(121, 0.6), (190, 0.7)])
        d["pupil"] = interp(f, [(121, 0.0032), (160, 0.0030), (190, 0.0046)])
    elif f <= 380:                                         # (brain shots; man not rendered) keep neutral
        d["head"] = (0.1, 0.0, 0.0)
    elif f <= 502:                                         # 24 h: the glass slips, he reacts too late
        react = F_TIP + 22
        a = interp(f, [(react, 0.0), (react + 16, 0.6), (react + 40, 1.0), (react + 70, 1.0), (502, 0.85)])
        d["head"] = (0.10 + 0.20 * a, -0.25 * a, 0.0); d["gaze"] = (-0.30 * interp(f, [(F_TIP + 4, 0.0), (F_TIP + 14, 1.0)]), 0.35 * interp(f, [(F_TIP + 4, 0.0), (F_TIP + 30, 1.0)]))
        d["lean"] = 0.05 + 0.40 * a; d["lean_side"] = 0.32 * a; d["droop"] = 0.55 - 0.3 * interp(f, [(F_TIP + 6, 0.0), (F_TIP + 20, 1.0)])
        tgt_w = Vector((GL_START.x - 0.07, GL_START.y, 0.12)); tgt_b = tgt_w - Vector((SEAT.x, SEAT.y, SEAT.z))
        kbR = Vector((KB.x, -0.085, KB.z)); kbR2 = Vector((KB.x + 0.02, -0.12, KB.z))
        reach = interp(f, [(react + 6, 0.0), (react + 50, 1.0), (react + 80, 1.0), (502, 0.8)])
        d["handR"] = kbR2.lerp(tgt_b, reach); d["handL"] = Vector((KB.x, 0.085, KB.z)).lerp(Vector((KB.x - 0.05, 0.2, KB.z - 0.12)), reach)
    elif f <= 620:                                         # 48 h: typing, then an unresponsive stare
        stare = interp(f, [(535, 0.0), (552, 1.0), (606, 1.0), (620, 1.0)])
        d["head"] = (0.12 + 0.06 * stare + 0.02 * math.sin(f * 0.05) * (1 - stare), 0.0, 0.0); d["gaze"] = ((0.02 * math.sin(f * 0.31)) * (1 - stare), 0.20 - 0.03 * stare)
        d["droop"] = 0.62 + 0.10 * stare; d["pupil"] = 0.0033
        type_amp = 0.006 * (1 - stare)
        d["handR"] = Vector((KB.x + 0.01, -0.085, KB.z + type_amp * math.sin(f * 1.9))); d["handL"] = Vector((KB.x + 0.01, 0.085, KB.z + type_amp * math.sin(f * 2.3 + 1)))
        d["openness"] = None if stare < 0.5 else 1.0
    elif f <= 690:                                         # microsleep: lids sink, head drops, then a jolt back
        c1 = interp(f, [(621, 0.0), (640, 1.0), (646, 1.0)]); jolt = interp(f, [(647, 0.0), (652, 1.0), (680, 0.7)])
        d["head"] = (0.18 + 0.30 * c1 * (1 if f < 647 else 0.0) - 0.12 * (jolt if f >= 647 else 0.0), 0.0, 0.0); d["droop"] = 0.72 + 0.28 * c1 * (1 if f < 647 else 0.0)
        d["openness"] = 1.0 - 0.9 * c1 if f < 647 else (1.0 if f < 662 else None)
        d["pupil"] = 0.0030 if f < 647 else 0.0040; d["gaze"] = (0.0, 0.18 if f < 647 else 0.0)
        d["handR"] = Vector((KB.x, -0.085, KB.z)); d["handL"] = Vector((KB.x, 0.085, KB.z))
    elif f <= 732: d["head"] = (0.1, 0.0, 0.0)
    elif f <= 880:                                         # 72 h: he turns toward the hallway
        turn = interp(f, [(766, 0.0), (800, 1.0), (850, 1.0)])
        d["head"] = (0.06, 0.95 * turn, 0.05 * turn); d["gaze"] = (0.22 * turn, 0.02); d["lean"] = 0.05 - 0.02 * turn; d["droop"] = 0.66 - 0.28 * turn; d["pupil"] = 0.0033 + 0.0012 * turn
        d["handR"] = Vector((KB.x, -0.085, KB.z)); d["handL"] = Vector((KB.x, 0.085, KB.z))
        if f > 850: d["head"] = (0.06, 0.95 - 0.5 * interp(f, [(851, 0.0), (880, 1.0)]), 0.0)
    elif f <= 930: d["head"] = (0.1, 0.0, 0.0)
    elif f <= 1186:                                        # 7 days: motionless, lapses
        lapse = 0.0
        for fl in (985, 1060, 1118, 1160): lapse = max(lapse, math.exp(-((f - fl) / 5.0) ** 2))
        d["head"] = (0.12 + 0.22 * lapse + 0.02 * noise1(f, 0.02, 3), 0.03 * noise1(f, 0.015, 4), 0.04 * noise1(f, 0.01, 5)); d["lean"] = 0.10; d["droop"] = 0.88 + 0.12 * lapse
        d["pupil"] = 0.0040; d["gaze"] = (0.01 * noise1(f, 0.02, 6), -0.04); d["openness"] = 1.0 - 0.85 * lapse if lapse > 0.05 else None
        d["handR"] = Vector((KB.x - 0.04, -0.12, KB.z - 0.02)); d["handL"] = Vector((KB.x - 0.04, 0.12, KB.z - 0.02))
    else:                                                  # ending: he looks across the room, then closes his eyes
        d["head"] = (0.04, 0.0, 0.0); d["gaze"] = (0.01 * noise1(f, 0.03, 7), -0.02); d["droop"] = interp(f, [(1187, 0.85), (1260, 0.95)]); d["pupil"] = 0.0042
        cl = interp(f, [(1252, 0.0), (1292, 1.0)]); d["openness"] = 1.0 - cl if f >= 1252 else None
        d["head"] = (0.04 + 0.10 * cl, 0.0, 0.0); d["lean"] = 0.10
        d["handR"] = Vector((KB.x - 0.04, -0.12, KB.z - 0.02)); d["handL"] = Vector((KB.x - 0.04, 0.12, KB.z - 0.02))
    return d

def apply_man(f):
    st = man_frame(f); sk = skin_state(f)
    hands = {}
    if st["handR"] is not None: hands["R"] = st["handR"]
    if st["handL"] is not None: hands["L"] = st["handL"]
    h_ = st["head"]
    pose(H, seated_spec(st["lean"], h_, hands=hands or None, breath=st["breath"], lean_side=st["lean_side"]), f)
    op = st["openness"] if st["openness"] is not None else blink_curve(f, BLINKS)
    set_face(H, st["gaze"], op, st["droop"], st["pupil"], st["brow"]); key_face(H, f)
    set_skin_state(H, sk["pale"], sk["bags"], 0.0, 0.4, sk["red"], f)
for f in range(0, 1342): apply_man(max(1, min(f, 1340)))

# double: window position in the hook, hallway during the 72 h scene
for f in range(0, 1342):
    pose(DB, standing_spec((0.10, 0.0, 0.05), 0.0), f)
    vis = (1 <= f <= 60) or (733 <= f <= 850)
    for o in [DB["body"]] + DB["face"]["objs"]: key_vis(o, f, vis)
    if f < 700: droot.location = (4.15, 2.25, 0.945); droot.rotation_euler = (0, 0, math.pi + 0.06)
    else: droot.location = (4.45, RY + 0.50, 0.945); droot.rotation_euler = (0, 0, -math.pi / 2)
    droot.keyframe_insert("location", frame=f); droot.keyframe_insert("rotation_euler", frame=f)
# the coat rack is a visible 'real' object: it is hidden during the misperception (the shadow figure stands in front of it) -- nothing to do

# ------------------------------------------------------------------ clock + lights
t0_sec = 3 * 3600 + 11 * 60 + 12
def clock_time(f):
    tt = t0_sec + (f - 1) / 30.0
    if f >= 647: tt += 37.0                         # microsleep: time discontinuity
    return tt
for f in range(0, 1342):
    tt = clock_time(f); sec = math.floor(tt) % 60 + 0.0; mn = (tt / 60.0) % 60; hr = (tt / 3600.0) % 12
    if f > 930:        # distorted clock: erratic second hand, wobbling minute hand
        k = (f - 930) / 256.0; sec = sec + 25 * k * noise1(f, 0.35, 9) + (6 * math.sin(f * 0.8) if (f // 7) % 5 == 0 else 0); mn = mn + 4 * k * noise1(f, 0.1, 10)
    R["second"].rotation_euler = (-math.radians(6.0 * sec), 0, 0); R["minute"].rotation_euler = (-math.radians(6.0 * mn), 0, 0); R["hour"].rotation_euler = (-math.radians(30.0 * hr), 0, 0)
    for k_ in ("second", "minute", "hour"): R[k_].keyframe_insert("rotation_euler", frame=f)
    cold = interp(f, [(1, 0.0), (500, 0.15), (730, 0.35), (930, 0.7), (1340, 1.0)])
    warm = Vector((1.0, 0.62, 0.32)); coolc = Vector((0.55, 0.72, 1.0)); c = warm.lerp(coolc, cold)
    en = interp(f, [(1, 1.0), (930, 0.8), (1340, 0.55)]); fl = 1.0
    if f > 930: fl = 1.0 - 0.5 * (math.sin(f * 1.3) > 0.985)
    L["lamp"].data.color = tuple(c); L["lamp"].data.energy = 75 * en * fl; L["lamp_fill"].data.color = tuple(c); L["lamp_fill"].data.energy = 10 * en * fl
    L["ceiling"].data.energy = interp(f, [(1, 0), (930, 0), (1186, 140), (1340, 240)])
    L["screen"].data.energy = 1.6 * (0.25 if 118 <= f <= 192 else 1.0); L["ambient"].data.energy = 22 * (0.35 if 118 <= f <= 192 else (4.5 if 61 <= f <= 118 else 1.0))
    L["screen"].data.keyframe_insert("energy", frame=f); L["ambient"].data.keyframe_insert("energy", frame=f)
    for ld in (L["lamp"].data, L["lamp_fill"].data): ld.keyframe_insert("color", frame=f); ld.keyframe_insert("energy", frame=f)
    L["ceiling"].data.keyframe_insert("energy", frame=f)
    R["bulb_em"].inputs[0].default_value = (c.x, c.y * 0.9, c.z * 0.9, 1); R["bulb_em"].inputs[0].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ cameras
cams = {k: U.shot_camera(k, a, 35) for k, a in (("c_over", 1), ("c_pov", 61), ("c_eyes", 121), ("c_glass", 381), ("c_48a", 503), ("c_48b", 621), ("c_72a", 733), ("c_72pov", 851),
                                                ("c_7d", 931), ("c_end", 1187))}
OTS_LOC = lambda u: Vector((1.55 + 0.10 * u, 1.55, 1.20 + 0.01 * u)); OTS_TGT = Vector((4.2, 2.30, 1.02))
for f in range(0, 62): key_cam(cams["c_over"], f, OTS_LOC(max(0.0, f / 60.0)), OTS_TGT, 35)
U.dof(cams["c_over"], droot, fstop=2.0)
for f in range(60, 122):
    u = max(0.0, (f - 61) / 59.0); eye = HEAD_W + Vector((0.108, 0.0, 0.004))
    key_cam(cams["c_pov"], f, eye, Vector((4.15, 2.25 + 0.15 * (1 - 2 * u), 1.0 + 0.04 * u)), 26 + 2 * u)
U.dof(cams["c_pov"], None, dist=3.5, fstop=2.8)
EYE_FRONT_X = HEAD_W.x + EYE_C[-1].x + RE
U.dof(cams["c_eyes"], None, dist=1.0, fstop=14.0)
for f in range(120, 192):
    sc.frame_set(f)
    pw = H["face"]["pivot"][-1].matrix_world @ Vector((RE, 0, 0))
    u = ease_in_out(max(0.0, min(1.0, (f - 121) / 69.0))); dist = 0.30 + (0.108 - 0.30) * u ** 0.85
    loc = pw + Vector((dist, 0.05 * (1 - u), 0.012 * (1 - u)))
    key_cam(cams["c_eyes"], f, loc, pw, 100 + 55 * u)
    cams["c_eyes"].data.dof.focus_distance = max(0.05, dist); cams["c_eyes"].data.dof.keyframe_insert("focus_distance", frame=f)
# glass: camera low, front-right of the desk
U.dof(cams["c_glass"], None, dist=1.6, fstop=2.8)
for f in range(380, 504):
    u = ease_in_out(max(0.0, min(1.0, (f - 381) / 121.0)))
    loc = Vector((1.62 + 0.10 * u, 0.72 + 0.05 * u, 0.72 + 0.04 * u)); tgt = Vector((2.40, 1.72 + 0.05 * u, 0.58 - 0.02 * u))
    key_cam(cams["c_glass"], f, loc, tgt, 26)
    cams["c_glass"].data.dof.focus_distance = (loc - Vector((2.45, 1.70, 0.5))).length; cams["c_glass"].data.dof.keyframe_insert("focus_distance", frame=f)
# 48 h: front view with the clock above his head; slow push
U.dof(cams["c_48a"], None, dist=2.0, fstop=2.4)
for f in range(502, 622):
    u = (f - 503) / 117.0; loc = Vector((3.55 - 0.25 * u, 2.98 - 0.12 * u, 1.25)); tgt = Vector((2.1, 2.05, 1.42))
    key_cam(cams["c_48a"], f, loc, tgt, 36 + 3 * u); cams["c_48a"].data.dof.focus_distance = (loc - HEAD_W).length; cams["c_48a"].data.dof.keyframe_insert("focus_distance", frame=f)
U.dof(cams["c_48b"], None, dist=2.0, fstop=2.4)
for f in range(620, 692):
    u = (f - 621) / 69.0; loc = Vector((3.30 - 0.10 * u, 2.90, 1.26)); tgt = Vector((2.1, 2.05, 1.40))
    key_cam(cams["c_48b"], f, loc, tgt, 38); cams["c_48b"].data.dof.focus_distance = (loc - HEAD_W).length; cams["c_48b"].data.dof.keyframe_insert("focus_distance", frame=f)
# 72 h: over his left shoulder toward the hallway, then his point of view
U.dof(cams["c_72a"], None, dist=3.0, fstop=2.0)
for f in range(732, 852):
    u = (f - 733) / 117.0; loc = Vector((1.70 + 0.06 * u, 1.10, 1.22)); tgt = Vector((4.45, RY + 0.4, 1.05))
    key_cam(cams["c_72a"], f, loc, tgt, 35); cams["c_72a"].data.dof.focus_distance = (loc - Vector((4.45, RY + 0.5, 1.0))).length; cams["c_72a"].data.dof.keyframe_insert("focus_distance", frame=f)
for f in range(850, 882):
    u = (f - 851) / 29.0; eye = HEAD_W + Vector((0.09, 0.03, 0.004))
    key_cam(cams["c_72pov"], f, eye, Vector((4.45, RY + 0.4, 1.0)) + Vector((0, 0, 0.1 * u)), 26); cams["c_72pov"].data.dof.use_dof = True; cams["c_72pov"].data.dof.aperture_fstop = 2.8; cams["c_72pov"].data.dof.focus_distance = 3.0
# 7 days: slow orbit
U.dof(cams["c_7d"], None, dist=1.8, fstop=2.2)
for f in range(930, 1188):
    u = ease_in_out((f - 931) / 255.0); a = math.radians(30 + 235 * u); r = 1.40 - 0.12 * math.sin(u * math.pi)
    c0 = HEAD_W + Vector((0.0, 0.0, -0.02)); loc = Vector((c0.x + 0.55 + r * math.cos(a), c0.y + r * math.sin(a), 1.18 + 0.12 * math.sin(u * math.pi)))
    loc.x = min(max(loc.x, 0.35), 4.6); loc.y = min(max(loc.y, 0.4), 3.7)
    key_cam(cams["c_7d"], f, loc, c0 + Vector((0, 0, 0.05)), 40); cams["c_7d"].data.dof.focus_distance = (loc - c0).length; cams["c_7d"].data.dof.keyframe_insert("focus_distance", frame=f)
# ending: back to the opening camera angle
U.dof(cams["c_end"], droot, fstop=2.0)
for f in range(1186, 1342):
    u = (f - 1187) / 153.0; key_cam(cams["c_end"], f, OTS_LOC(1.0 + 0.5 * u), OTS_TGT, 35)

U.setup(sc, "apt", samples=int(os.environ.get("SPP", 24)))
# match-cut anchors: pupil of the right eye in screen space (normalised) and its radius
from bpy_extras.object_utils import world_to_camera_view
anch = {}
for f in range(121, 191):
    sc.frame_set(f); cam = U.active_camera(f)
    pw = HEAD_W + EYE_C[-1] + Vector((RE + 0.001, 0, 0)); st = man_frame(f); pw = Vector(H["face"]["pivot"][-1].matrix_world @ Vector((RE, 0, 0)))
    a = world_to_camera_view(sc, cam, pw); b = world_to_camera_view(sc, cam, pw + Vector((0, 0, st["pupil"])))
    anch[f] = {"px": a.x, "py": 1 - a.y, "pr": abs(b.y - a.y)}
json.dump(anch, open(U.V + "/renders/anchors_pupil.json", "w"))
frames_all = [f for a, b in APT_RANGES for f in range(a, b + 1)]
U.run_render(sc, sys.argv, frames_all, "apt")
