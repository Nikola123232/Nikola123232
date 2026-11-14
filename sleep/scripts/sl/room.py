"""The apartment (late night, dark, practical lights): desk + laptop + lamp + glass, chair, clock, window with night city, hallway with a coat rack,
bookshelf, rug. Returns handles for animation (clock hands, lamp, glass, lights)."""
import sys, math, random
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy, bmesh
from mathutils import Vector, Euler, noise
from f1.core import *

RX, RY, RZ = 5.2, 4.0, 2.6                      # room: x back wall(0) -> window wall (RX); y right wall(0) -> hallway wall (RY)
DESK = dict(x0=2.50, x1=3.24, y0=1.25, y1=2.85, z=0.74)
SEAT = Vector((2.28, 2.05, 0.50))      # hip joint position of the seated man
HALL = dict(x0=3.9, x1=4.85, depth=2.6)         # hallway opening in wall y=RY


def paint_mat(name, col, rough=0.92, bump=0.0006):
    m = mat(name, col, rough=rough); nodes, links = m.node_tree.nodes, m.node_tree.links; p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord"); nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 120; nz.inputs["Detail"].default_value = 6; links.new(tc.outputs["Object"], nz.inputs[0])
    nz2 = nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 1.4; nz2.inputs["Detail"].default_value = 3; links.new(tc.outputs["Object"], nz2.inputs[0])
    mx = nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; links.new(nz2.outputs["Fac"], mx.inputs[0]); mx.inputs[6].default_value = (*col, 1); mx.inputs[7].default_value = (col[0] * 0.7, col[1] * 0.72, col[2] * 0.76, 1)
    links.new(mx.outputs[2], p.inputs["Base Color"])
    bp = nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = bump
    links.new(nz.outputs["Fac"], bp.inputs["Height"]); links.new(bp.outputs[0], p.inputs["Normal"])
    return m


def wood_mat(name, c1=(0.13, 0.075, 0.04), c2=(0.06, 0.032, 0.018), planks=False, scale=1.0):
    m = mat(name, c1, rough=0.45, coat=0.15); nodes, links = m.node_tree.nodes, m.node_tree.links; p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord"); mp = nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 28.0, 1.0); links.new(tc.outputs["Object"], mp.inputs[0])
    wv = nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.inputs["Scale"].default_value = 9 * scale; wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
    links.new(mp.outputs[0], wv.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c2, 1); cr.color_ramp.elements[1].color = (*c1, 1); links.new(wv.outputs["Fac"], cr.inputs[0])
    col = cr.outputs[0]
    if planks:
        br = nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.006; br.inputs["Brick Width"].default_value = 1.2; br.inputs["Row Height"].default_value = 0.18
        br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1); br.inputs["Mortar"].default_value = (0.2, 0.2, 0.2, 1)
        links.new(tc.outputs["Object"], br.inputs[0])
        mm = nodes.new("ShaderNodeMix"); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs[0].default_value = 1.0; links.new(cr.outputs[0], mm.inputs[6]); links.new(br.outputs["Color"], mm.inputs[7]); col = mm.outputs[2]
    links.new(col, p.inputs["Base Color"])
    bp = nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.0008; links.new(wv.outputs["Fac"], bp.inputs["Height"]); links.new(bp.outputs[0], p.inputs["Normal"])
    return m


def box_obj(name, c, size, m, parent=None, rot=None):
    bm = bmesh.new(); box_bm(bm, (0, 0, 0), size)
    o = obj_from_bm(name, bm, [m], smooth=False); o.location = c
    if rot: o.rotation_euler = rot
    if parent: o.parent = parent
    return o


def build_room():
    R = {}
    walls = paint_mat("wall", (0.105, 0.12, 0.135)); ceil = paint_mat("ceiling", (0.12, 0.125, 0.13)); trim = mat("trim", (0.16, 0.16, 0.165), rough=0.5)
    floor_m = wood_mat("floor", (0.17, 0.11, 0.07), (0.07, 0.04, 0.025), planks=True, scale=0.6)
    box_obj("floor", (RX / 2, RY / 2 + 1.3, -0.02), (RX + 0.2, RY + 2.8, 0.04), floor_m)
    box_obj("ceiling", (RX / 2, RY / 2, RZ + 0.02), (RX, RY, 0.04), ceil)
    box_obj("wall_back", (-0.02, RY / 2, RZ / 2), (0.04, RY, RZ), walls)
    box_obj("wall_right", (RX / 2, -0.02, RZ / 2), (RX, 0.04, RZ), walls)
    # window wall (x = RX) with an opening y 1.0-3.1, z 0.85-2.2
    wy0, wy1, wz0, wz1 = 1.0, 3.1, 0.85, 2.2
    box_obj("wall_win_l", (RX + 0.02, wy0 / 2, RZ / 2), (0.04, wy0, RZ), walls)
    box_obj("wall_win_r", (RX + 0.02, (wy1 + RY) / 2, RZ / 2), (0.04, RY - wy1, RZ), walls)
    box_obj("wall_win_b", (RX + 0.02, (wy0 + wy1) / 2, wz0 / 2), (0.04, wy1 - wy0, wz0), walls)
    box_obj("wall_win_t", (RX + 0.02, (wy0 + wy1) / 2, (wz1 + RZ) / 2), (0.04, wy1 - wy0, RZ - wz1), walls)
    # hallway wall (y = RY) with a door opening
    hx0, hx1 = HALL["x0"], HALL["x1"]; hz = 2.1
    box_obj("wall_hall_l", ((hx0) / 2, RY + 0.02, RZ / 2), (hx0, 0.04, RZ), walls)
    box_obj("wall_hall_r", ((hx1 + RX) / 2, RY + 0.02, RZ / 2), (RX - hx1, 0.04, RZ), walls)
    box_obj("wall_hall_t", ((hx0 + hx1) / 2, RY + 0.02, (hz + RZ) / 2), (hx1 - hx0, 0.04, RZ - hz), walls)
    for nm, c, sz in (("jamb_l", (hx0, RY, hz / 2), (0.05, 0.12, hz)), ("jamb_r", (hx1, RY, hz / 2), (0.05, 0.12, hz)), ("lintel", ((hx0 + hx1) / 2, RY, hz), (hx1 - hx0 + 0.1, 0.12, 0.05))):
        box_obj(nm, c, sz, trim)
    # hallway box
    d = HALL["depth"]
    box_obj("hall_floor", ((hx0 + hx1) / 2, RY + d / 2, -0.02), (hx1 - hx0 + 0.6, d, 0.04), floor_m)
    box_obj("hall_ceiling", ((hx0 + hx1) / 2, RY + d / 2, RZ + 0.02), (hx1 - hx0 + 0.6, d, 0.04), ceil)
    box_obj("hall_end", ((hx0 + hx1) / 2, RY + d + 0.02, RZ / 2), (hx1 - hx0 + 0.6, 0.04, RZ), walls)
    box_obj("hall_wall_l", (hx0 - 0.3, RY + d / 2, RZ / 2), (0.04, d, RZ), walls); box_obj("hall_wall_r", (hx1 + 0.3, RY + d / 2, RZ / 2), (0.04, d, RZ), walls)
    # baseboards
    box_obj("base_back", (0.03, RY / 2, 0.05), (0.03, RY, 0.1), trim); box_obj("base_right", (RX / 2, 0.03, 0.05), (RX, 0.03, 0.1), trim)
    # night view through the window: dark gradient + city light bokeh dots
    sky = bpy.data.materials.new("night_sky"); nodes, links = sky.node_tree.nodes, sky.node_tree.links; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); em = nodes.new("ShaderNodeEmission"); tc = nodes.new("ShaderNodeTexCoord"); sp = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sp.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.003, 0.005, 0.015, 1); cr.color_ramp.elements[1].color = (0.035, 0.055, 0.11, 1)
    rm = nodes.new("ShaderNodeMapRange"); rm.inputs[1].default_value = -1.5; rm.inputs[2].default_value = 1.5; links.new(sp.outputs[2], rm.inputs[0]); links.new(rm.outputs[0], cr.inputs[0])
    links.new(cr.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.0; links.new(em.outputs[0], out.inputs[0])
    bm = bmesh.new(); box_bm(bm, (0, 0, 0), (0.02, 14, 6)); R["sky"] = obj_from_bm("night_sky", bm, [sky], smooth=False); R["sky"].location = (RX + 14, 2.0, 1.5)
    rng = random.Random(3); lights_m = emit_mat("city", (1.0, 0.78, 0.45), 18.0); cold_m = emit_mat("city2", (0.6, 0.8, 1.0), 14.0)
    for i in range(110):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        o = obj_from_bm(f"city{i}", bm, [lights_m if rng.random() < 0.7 else cold_m], smooth=False); o.visible_shadow = False
        o.location = (RX + rng.uniform(10, 30), rng.uniform(-9, 14), rng.uniform(-2, 3.2)); s_ = rng.uniform(0.05, 0.16) * 2.0; o.scale = (s_, s_, s_)
    # window frame + curtains
    fr = mat("window_frame", (0.07, 0.07, 0.075), rough=0.4)
    box_obj("win_sill", (RX - 0.05, (wy0 + wy1) / 2, wz0), (0.18, wy1 - wy0 + 0.1, 0.04), trim)
    for nm, y in (("win_mullion", (wy0 + wy1) / 2),):
        box_obj(nm, (RX - 0.01, y, (wz0 + wz1) / 2), (0.04, 0.04, wz1 - wz0), fr)
    box_obj("win_mullion_h", (RX - 0.01, (wy0 + wy1) / 2, (wz0 + wz1) / 2 + 0.2), (0.04, wy1 - wy0, 0.04), fr)
    cur = mat("curtain", (0.05, 0.055, 0.07), rough=0.95, sheen=0.5)
    for nm, y in (("curtain_l", wy0 - 0.12), ("curtain_r", wy1 + 0.12)):
        bm = bmesh.new()
        for k in range(10):
            tube_bm(bm, [(0, 0.1 * k - 0.45 + 0.0, 0.0), (0, 0.1 * k - 0.45, 2.4)], 0.07, 8)
        o = obj_from_bm(nm, bm, [cur], smooth=True); o.location = (RX - 0.12, y + (0.0), 0.05)
    # ---- desk, chair, laptop, lamp, mug, glass
    dw = wood_mat("desk_wood", (0.20, 0.125, 0.07), (0.09, 0.05, 0.03))
    D = DESK
    top = box_obj("desk_top", ((D["x0"] + D["x1"]) / 2, (D["y0"] + D["y1"]) / 2, D["z"] - 0.02), (D["x1"] - D["x0"], D["y1"] - D["y0"], 0.04), dw)
    for sx in (D["x0"] + 0.04, D["x1"] - 0.04):
        for sy in (D["y0"] + 0.04, D["y1"] - 0.04):
            box_obj("desk_leg", (sx, sy, (D["z"] - 0.04) / 2), (0.05, 0.05, D["z"] - 0.04), dw)
    metal = mat("metal_dark", (0.03, 0.03, 0.035), metal=0.9, rough=0.35); fab = mat("chair_fabric", (0.025, 0.026, 0.03), rough=0.9, sheen=0.5)
    # office chair (seat, back, gas-lift, star base)
    seat = box_obj("chair_seat", (SEAT.x, SEAT.y, 0.375), (0.46, 0.46, 0.07), fab); box_obj("chair_back", (SEAT.x - 0.24, SEAT.y, 0.70), (0.07, 0.42, 0.55), fab)
    box_obj("chair_stem", (SEAT.x, SEAT.y, 0.20), (0.05, 0.05, 0.34), metal)
    for k in range(5):
        a = k * 2 * math.pi / 5
        bm = bmesh.new(); tube_bm(bm, [(0, 0, 0.05), (0.30 * math.cos(a), 0.30 * math.sin(a), 0.045)], [0.02, 0.015], 6); o = obj_from_bm(f"chair_leg{k}", bm, [metal], smooth=True); o.location = (SEAT.x, SEAT.y, 0.0)
        box_obj(f"chair_wheel{k}", (SEAT.x + 0.31 * math.cos(a), SEAT.y + 0.31 * math.sin(a), 0.03), (0.05, 0.05, 0.05), metal)
    for sy in (-1, 1): box_obj("chair_arm", (SEAT.x + 0.0, SEAT.y + sy * 0.26, 0.56), (0.32, 0.04, 0.03), metal)
    # laptop
    lm = mat("laptop_body", (0.09, 0.09, 0.1), metal=0.8, rough=0.35)
    box_obj("laptop_base", (D["x0"] + 0.30, 2.05, D["z"] + 0.008), (0.24, 0.34, 0.016), lm)
    scr_m = bpy.data.materials.new("screen"); nodes, links = scr_m.node_tree.nodes, scr_m.node_tree.links; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); em = nodes.new("ShaderNodeEmission"); tc = nodes.new("ShaderNodeTexCoord"); sp = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sp.inputs[0])
    wv = nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 70; wv.inputs["Distortion"].default_value = 3; links.new(tc.outputs["Object"], wv.inputs[0])
    mx = nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.2, 0.3, 0.5, 1); mx.inputs[7].default_value = (0.8, 0.9, 1.0, 1); links.new(wv.outputs["Fac"], mx.inputs[0])
    links.new(mx.outputs[2], em.inputs[0]); em.inputs[1].default_value = 0.9; links.new(em.outputs[0], out.inputs[0]); R["screen_m"] = scr_m; R["screen_em"] = em
    lid = box_obj("laptop_lid", (D["x0"] + 0.185, 2.05, D["z"] + 0.12), (0.012, 0.34, 0.22), lm, rot=(0, math.radians(-14), 0))
    box_obj("laptop_screen", (D["x0"] + 0.178, 2.05, D["z"] + 0.12), (0.002, 0.31, 0.19), scr_m, rot=(0, math.radians(-14), 0)).location.x += 0.0
    # desk lamp (warm), articulated
    box_obj("lamp_base", (D["x0"] + 0.18, 1.45, D["z"] + 0.01), (0.14, 0.14, 0.02), metal)
    bm = bmesh.new(); tube_bm(bm, [(0, 0, 0), (0.0, 0.03, 0.28), (0.07, 0.10, 0.45)], 0.008, 8); arm_o = obj_from_bm("lamp_arm", bm, [metal], smooth=True); arm_o.location = (D["x0"] + 0.18, 1.45, D["z"] + 0.02)
    lamp_head = ellipsoid("lamp_head", (D["x0"] + 0.25, 1.55, D["z"] + 0.47), (0.075, 0.05, 0.05), [metal], 24, 12, rot=Euler((0, math.radians(30), math.radians(40))).to_quaternion())
    bulb_m = emit_mat("bulb", (1.0, 0.65, 0.35), 40.0); R["bulb_m"] = bulb_m; R["bulb_em"] = [n for n in bulb_m.node_tree.nodes if n.type == 'EMISSION'][0]
    ellipsoid("lamp_bulb", (D["x0"] + 0.23, 1.53, D["z"] + 0.45), (0.025, 0.025, 0.025), [bulb_m], 14, 8)
    # mug, papers, phone
    mugm = mat("mug", (0.55, 0.52, 0.48), rough=0.4, coat=0.5); bm = bmesh.new(); lathe_bm(bm, [(0.0, 0.0), (0.038, 0.0), (0.04, 0.005), (0.04, 0.09), (0.036, 0.09), (0.036, 0.008), (0.0, 0.008)], 32, 'Z'); mug = obj_from_bm("mug", bm, [mugm], smooth=True); mug.location = (D["x0"] + 0.55, 2.62, D["z"])
    paper = mat("paper", (0.5, 0.5, 0.46), rough=0.9)
    for k in range(3): box_obj(f"paper{k}", (D["x0"] + 0.45 + 0.01 * k, 1.75 + 0.02 * k, D["z"] + 0.002 + 0.002 * k), (0.21, 0.297, 0.002), paper, rot=(0, 0, math.radians(8 * k - 6)))
    box_obj("phone", (D["x0"] + 0.55, 2.3, D["z"] + 0.004), (0.075, 0.15, 0.008), mat("phone", (0.02, 0.02, 0.025), metal=0.6, rough=0.2), rot=(0, 0, math.radians(30)))
    # keyboard-side hand rest etc. are the man's hands; no extra props
    # ---- glass of water (hero prop for the 24 h scene) -- built in glass.py
    # ---- wall clock on the back wall above the man's head
    cm = mat("clock_face", (0.82, 0.8, 0.74), rough=0.5); ring = mat("clock_ring", (0.02, 0.02, 0.022), metal=0.5, rough=0.3)
    cx, cy, cz = 0.04, SEAT.y, 1.95
    bm = bmesh.new(); lathe_bm(bm, [(0.0, 0.0), (0.175, 0.0), (0.175, 0.018)], 64, 'X'); face = obj_from_bm("clock_face", bm, [cm], smooth=True); face.location = (cx, cy, cz)
    bm = bmesh.new(); lathe_bm(bm, [(0.175, 0.0), (0.19, 0.0), (0.19, 0.026), (0.175, 0.026)], 64, 'X'); obj_from_bm("clock_ring", bm, [ring], smooth=True).location = (cx, cy, cz)
    tick = mat("tick", (0.02, 0.02, 0.02), rough=0.6)
    for k in range(12):
        a = k * math.pi / 6; box_obj(f"tick{k}", (cx + 0.02, cy + 0.15 * math.sin(a), cz + 0.15 * math.cos(a)), (0.004, 0.006 if k % 3 else 0.012, 0.03 if k % 3 == 0 else 0.018), tick, rot=(a, 0, 0))
    def hand(name, L, w, col, z):
        piv = empty(name + "_pivot", (cx + 0.03 + z, cy, cz), size=0.02)
        bm = bmesh.new(); box_bm(bm, (0, 0, L / 2 - 0.02), (0.004, w, L)); o = obj_from_bm(name, bm, [mat(name + "_m", col, rough=0.5)], smooth=False); o.parent = piv; return piv
    R["hour"] = hand("hour_hand", 0.095, 0.011, (0.02, 0.02, 0.02), 0.0); R["minute"] = hand("minute_hand", 0.14, 0.008, (0.02, 0.02, 0.02), 0.004); R["second"] = hand("second_hand", 0.15, 0.003, (0.55, 0.05, 0.04), 0.008)
    for k in ("hour", "minute", "second"): R[k].rotation_mode = 'XYZ'
    # ---- bookshelf + plant + rug (back-left corner, visible when the camera orbits)
    shelf = wood_mat("shelf", (0.14, 0.085, 0.05), (0.06, 0.035, 0.02))
    sx, sy0 = 0.18, 0.5
    for k in range(5): box_obj(f"shelf_board{k}", (sx, sy0 + 0.5, 0.05 + k * 0.42), (0.28, 1.0, 0.03), shelf)
    box_obj("shelf_side_a", (sx, sy0, 0.9), (0.28, 0.03, 1.8), shelf); box_obj("shelf_side_b", (sx, sy0 + 1.0, 0.9), (0.28, 0.03, 1.8), shelf)
    brng = random.Random(8)
    for k in range(4):
        y = sy0 + 0.05
        while y < sy0 + 0.95:
            w = brng.uniform(0.025, 0.05); h = brng.uniform(0.2, 0.34)
            col = brng.choice([(0.05, 0.07, 0.12), (0.12, 0.05, 0.04), (0.06, 0.1, 0.07), (0.15, 0.12, 0.06), (0.1, 0.1, 0.11)])
            box_obj(f"book{k}_{y:.2f}", (sx, y + w / 2, 0.065 + k * 0.42 + h / 2), (0.2, w, h), mat("bk", col, rough=0.7), rot=(0, 0, 0)); y += w + 0.004
    pot = mat("pot", (0.2, 0.17, 0.15), rough=0.6); leaf = mat("leaf", (0.03, 0.09, 0.04), rough=0.5, sheen=0.4)
    bm = bmesh.new(); lathe_bm(bm, [(0.0, 0.0), (0.12, 0.0), (0.15, 0.28), (0.0, 0.28)], 24, 'Z'); pt = obj_from_bm("pot", bm, [pot], smooth=True); pt.location = (0.45, 3.6, 0.0)
    for k in range(14):
        a = k * 2.4; bm = bmesh.new(); tube_bm(bm, [(0, 0, 0), (0.18 * math.cos(a), 0.18 * math.sin(a), 0.35), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.25)], [0.012, 0.03, 0.002], 6)
        obj_from_bm(f"leaf{k}", bm, [leaf], smooth=True).location = (0.45, 3.6, 0.28)
    rug = mat("rug", (0.07, 0.075, 0.09), rough=0.98, sheen=0.7); box_obj("rug", (3.0, 2.05, 0.005), (2.4, 1.9, 0.01), rug)
    # ---- hallway coat rack with coat and hat
    cr_x, cr_y = 4.5, RY + 1.2
    bm = bmesh.new(); tube_bm(bm, [(0, 0, 0), (0, 0, 1.75)], 0.018, 8); o = obj_from_bm("rack_pole", [] and None or bm, [metal], smooth=True); o.location = (cr_x, cr_y, 0.0)
    for k in range(4):
        a = k * math.pi / 2; bm = bmesh.new(); tube_bm(bm, [(0, 0, 1.65), (0.12 * math.cos(a), 0.12 * math.sin(a), 1.72)], 0.008, 6); obj_from_bm(f"rack_hook{k}", bm, [metal], smooth=True).location = (cr_x, cr_y, 0.0)
    coat = mat("coat", (0.035, 0.037, 0.045), rough=0.9, sheen=0.8)
    cb = ellipsoid("coat_body", (cr_x, cr_y - 0.02, 1.25), (0.20, 0.13, 0.50), [coat], 32, 20); sc_ = ellipsoid("coat_scarf", (cr_x, cr_y - 0.05, 1.68), (0.09, 0.11, 0.07), [coat], 20, 12)
    hat = ellipsoid("hat", (cr_x, cr_y, 1.84), (0.12, 0.12, 0.07), [mat("hat", (0.03, 0.03, 0.035), rough=0.9)], 24, 12); brim = ellipsoid("hat_brim", (cr_x, cr_y, 1.79), (0.19, 0.19, 0.012), [coat], 32, 6)
    R["coat"] = [cb, sc_, hat, brim]
    return R


def build_room_lights():
    """Practical lighting. Returns dict of light objects (keyframed by the caller)."""
    L = {}
    world_color((0.003, 0.005, 0.010), 1.0)
    D = DESK
    L["lamp"] = light("lamp_spot", 'SPOT', (D["x0"] + 0.24, 1.54, D["z"] + 0.46), energy=75, size=0.04, color=(1.0, 0.62, 0.32), target=(D["x0"] + 0.35, 2.0, D["z"]))
    L["lamp"].data.spot_size = math.radians(95); L["lamp"].data.spot_blend = 0.8
    L["lamp_fill"] = light("lamp_fill", 'POINT', (D["x0"] + 0.24, 1.54, D["z"] + 0.46), energy=6, size=0.05, color=(1.0, 0.62, 0.32))
    L["screen"] = light("screen_glow", 'AREA', (D["x0"] + 0.15, 2.05, D["z"] + 0.14), (0, math.radians(90 + 14 + 180), 0), energy=1.6, size=0.3, color=(0.55, 0.7, 1.0))
    L["screen"].rotation_euler = look_at_rot(L["screen"].location, SEAT + Vector((0, 0, 0.75)))
    L["window"] = light("window_moon", 'AREA', (RX + 0.6, 2.05, 1.5), (0, math.radians(-90), 0), energy=110, size=2.0, color=(0.50, 0.65, 1.0))
    L["window"].rotation_euler = look_at_rot(L["window"].location, Vector((2.5, 2.05, 0.9)))
    L["window"].data.shape = 'RECTANGLE'; L["window"].data.size = 2.0; L["window"].data.size_y = 1.3
    L["street"] = light("street_warm", 'AREA', (RX + 0.8, 2.6, 1.0), energy=50, size=1.0, color=(1.0, 0.7, 0.4)); L["street"].rotation_euler = look_at_rot(L["street"].location, Vector((3.0, 2.0, 0.8)))
    L["hall"] = light("hall_cold", 'AREA', (4.37, RY + HALL["depth"] - 0.2, 2.2), energy=35, size=0.4, color=(0.6, 0.75, 1.0)); L["hall"].rotation_euler = look_at_rot(L["hall"].location, Vector((4.37, RY - 0.2, 1.0)))
    L["ambient"] = light("ambient_fill", 'AREA', (2.5, 2.0, RZ - 0.1), (math.pi, 0, 0), energy=22, size=3.2, color=(0.55, 0.65, 0.9))
    L["ceiling"] = light("ceiling_cold", 'AREA', (2.6, 2.05, RZ - 0.05), (0, 0, 0), energy=0, size=1.2, color=(0.65, 0.8, 1.0)); L["ceiling"].rotation_euler = (math.pi, 0, 0)
    return L
