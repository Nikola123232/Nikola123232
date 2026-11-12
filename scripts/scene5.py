"""SCENE 5 (0:45-0:56, frames 1351-1680): exploded view of the safety systems assembling around the driver.
Order: survival cell -> crash structures (front/side/rear) -> 6-point harness -> HANS -> halo -> helmet -> rest of car."""
import sys, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from mathutils import Vector, Matrix, Euler
from f1.core import *
from f1 import car as C, anatomy as A, gear as G, studio as St, world as Wd

F0, F1 = 1351, 1680
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
sc.frame_start, sc.frame_end = F0, F1
floor, floor_m = St.build_studio(grid_color=(0.08, 0.25, 0.6))
St.studio_lights((2.0, 0, 0.5), key=420, rim=520)
light("rim_top", "AREA", (1.0, 1.5, 3.2), energy=500, size=3, color=(0.6, 0.8, 1.0), target=(2.0, 0, 0.4))
P = C.build_car(font=ROOT + "/assets/fonts/Anton-Regular.ttf")
D = A.build_driver(anatomy=False)
Gr = G.build_gear(D)
D["root"].parent = P["body"]
D["root"].location, D["root"].rotation_euler = A.BODY_IN_CAR
bpy.context.view_layer.update()
key_reveal(D["M"]["skin"], E0, 0.0)

# raw carbon survival cell
tub = P["tub"]
tub.data.materials.clear(); tcm = carbon_mat("tub_carbon", scale=55, rough=0.4); tub.data.materials.append(tcm)
_ck = [n for n in tcm.node_tree.nodes if n.type == 'TEX_CHECKER'][0]
_ck.inputs["Color1"].default_value = (0.035, 0.037, 0.042, 1); _ck.inputs["Color2"].default_value = (0.11, 0.115, 0.125, 1)
principled(tcm).inputs["Coat Roughness"].default_value = 0.22

# crash structures (honeycomb amber)
def honey_mat(name):
    m = mat(name, (0.25, 0.12, 0.02), rough=0.35, coat=0.6)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    vo = nodes.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 45
    links.new(tc.outputs["Object"], vo.inputs[0])
    lt = nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.07
    links.new(vo.outputs["Distance"], lt.inputs[0])
    mm = nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = 3.0; mm.inputs[2].default_value = 0.4
    links.new(lt.outputs[0], mm.inputs[0])
    links.new(mm.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Emission Color"].default_value = (1.0, 0.45, 0.05, 1)
    return m
hm = honey_mat("honeycomb")
from f1.car import TUB, _rings_tub
front_secs = [(x, hw * 1.03, zb - 0.005, zt + 0.006) for (x, hw, zb, zt) in TUB if x >= 3.15]
rear_secs = [(x, hw * 1.04, zb - 0.006, zt + 0.006) for (x, hw, zb, zt) in TUB if x <= 0.25]
fis = loft("front_impact_structure", _rings_tub(front_secs, 32, 3), [hm], parent=P["body"])
ris = loft("rear_impact_structure", _rings_tub(rear_secs, 32, 3), [hm], parent=P["body"])
sis = []
for s in (1, -1):
    sis.append(tube(f"side_impact_{s}", [(2.25, s * 0.40, 0.36), (1.35, s * 0.42, 0.36)], 0.06, [hm], 16, parent=P["body"]))
    sis.append(tube(f"side_impact_lo{s}", [(2.25, s * 0.38, 0.20), (1.6, s * 0.40, 0.20)], 0.045, [hm], 16, parent=P["body"]))

# ---- grouping of parts and their exploded offsets / landing frames
def objs(prefixes):
    return [o for o in bpy.data.objects if o.name.startswith(prefixes) and o.type in ('MESH', 'FONT', 'EMPTY')]
groups = [
    ("cell", [tub, bpy.data.objects["cockpit_rim"], bpy.data.objects["steering_wheel"]], Vector((0, 0, -2.2)), 1360, 1392),
    ("crash", [fis], Vector((2.5, 0, 0.3)), 1436, 1466),
    ("crash", [ris], Vector((-2.3, 0, 0.3)), 1440, 1470),
    ("crash", sis, Vector((0, 0, 0)), 1444, 1474),
    ("harness", objs(("harness",)), Vector((0, 0, 0.9)), 1498, 1526),
    ("hans", objs(("hans", "tether", "clip")), Vector((-0.9, 0, 0.5)), 1528, 1556),
    ("halo", P["halo"], Vector((0, 0, 1.6)), 1556, 1584),
    ("helmet", objs(("helmet",)), Vector((0, 0, 1.0)), 1584, 1610),
]
rest_parts = objs(("airbox", "shark_fin", "tcam", "sidepod", "inlet_lip", "mirror", "floor", "fence", "diffuser", "strake",
                   "rain_light", "susp", "nose_number", "side_number"))
for side in (1, -1):
    pass
groups.append(("car", rest_parts, Vector((0, 0, 0)), 1612, 1645))
wing_groups = [("car", [P["front_wing"]], Vector((2.0, 0, 0)), 1612, 1640), ("car", [P["rear_wing"]], Vector((-1.8, 0, 0.6)), 1616, 1644)]
for key, (hub, spin) in P["wheels"].items():
    off = Vector((0.6 if key[0] == "F" else -0.6, (1.6 if hub.location.y > 0 else -1.6), 0))
    wing_groups.append(("car", [hub], off, 1618, 1650))
groups += wing_groups

side_offsets = {}
for o in sis:
    side_offsets[o.name] = Vector((0, 1.6 if "_1" in o.name or "lo1" in o.name else -1.6, 0))
for o in rest_parts:
    if o.name.startswith(("sidepod_L", "inlet_lip_1", "mirror_1", "mirror_glass_1", "mirror_stalk_1")):
        side_offsets[o.name] = Vector((0, 1.4, 0.2))
    elif o.name.startswith(("sidepod_R", "inlet_lip_-1", "mirror_-1", "mirror_glass_-1", "mirror_stalk_-1")):
        side_offsets[o.name] = Vector((0, -1.4, 0.2))
    elif o.name.startswith(("airbox", "shark_fin", "tcam")):
        side_offsets[o.name] = Vector((-0.6, 0, 1.2))
    else:
        side_offsets[o.name] = Vector((0, 0, -1.0))

glows = {}
gcol = {"cell": (0.2, 0.7, 1.0), "crash": (1.0, 0.5, 0.05), "harness": (1.0, 0.2, 0.1), "hans": (0.2, 1.0, 0.45),
        "halo": (0.2, 0.75, 1.0), "helmet": (0.9, 0.9, 1.0), "car": (0.2, 0.6, 1.0)}
for name, col in gcol.items():
    glows[name] = St.glow_mat("glow5_" + name, col, 2.0)
for gname, olist, off, fa, fb in groups:
    for o in olist:
        rest = Vector(o.location)
        oo = side_offsets.get(o.name, off)
        for f in range(E0, E1 + 1):
            u = (f - fa) / (fb - fa)
            k = 1 - ease_out_back(u, 1.2) if u > 0 else 1.0
            o.location = rest + oo * k
            o.keyframe_insert("location", frame=f)
        # visibility: appear when the move starts
        key_vis(o, E0, False); key_vis(o, fa, True)
        for ch in o.children_recursive:
            if ch.type in ('MESH', 'FONT'):
                key_vis(ch, E0, False); key_vis(ch, fa, True)
        # glow shell on landing (meshes only, not for the many small car parts)
        if gname != "car" and o.type == 'MESH':
            g = bpy.data.objects.new(o.name + "_glow", o.data); link(g)
            g.parent = o.parent; g.parent_type = o.parent_type; g.parent_bone = o.parent_bone
            g.matrix_parent_inverse = o.matrix_parent_inverse.copy()
            g.location = o.location
            for fc_f in range(E0, E1 + 1):
                pass
            g.data = o.data.copy(); g.data.materials.clear(); g.data.materials.append(glows[gname])
            dsp = g.modifiers.new("d", 'DISPLACE'); dsp.strength = 0.01
            sol = g.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1
            g.visible_shadow = False
            c = g.constraints.new('COPY_LOCATION'); c.target = o; c.use_offset = False
            c.target_space = 'LOCAL'; c.owner_space = 'LOCAL'
            key_vis(g, E0, False); key_vis(g, fb - 8, True); key_vis(g, fb + 30, False)
    St.key_glow_windows(glows[gname], [(fb - 6, fb + 24)], E0, E1, 1.0)
# driver body slowly fades from x-ray (start) to suit as the cell arrives
key_reveal(D["M"]["skin"], E0, 0.6); key_reveal(D["M"]["skin"], 1380, 0.6); key_reveal(D["M"]["skin"], 1420, 0.0)

# ---- camera: continuous orbit
cam = Wd.shot_camera("cam5", F0, 30)
c0 = Vector((2.0, 0, 0.45))
for f in range(E0, E1 + 1):
    u = ease_in_out((f - F0) / (F1 - F0))
    ang = math.radians(32 - 100 * u)
    r = 3.9 - 0.9 * u
    loc = c0 + Vector((r * math.cos(ang), r * math.sin(ang), 2.0 - 0.95 * u))
    key_cam(cam, f, loc, c0 + Vector((0.15 - 0.1 * u, 0, 0.12)), 26 + 4 * u)

render_settings(sc, (720, 1280), samples=10, motion_blur=False, transparent_bounces=16)
sc.render.filepath = f"{ROOT}/renders/s5/####"
BM = Matrix.LocRotScale(Vector(A.BODY_IN_CAR[0]), Euler(A.BODY_IN_CAR[1]).to_quaternion(), Vector((1, 1, 1)))
pts = {
    "cell": lambda f: tub.matrix_world @ Vector((2.7, 0.3, 0.55)),
    "front": lambda f: fis.matrix_world @ Vector((4.2, 0, 0.36)),
    "rear": lambda f: ris.matrix_world @ Vector((-0.3, 0, 0.4)),
    "side": lambda f: sis[0].matrix_world @ Vector((1.8, 0.42, 0.36)),
    "harness": lambda f: BM @ Vector((0.13, 0.0, 0.33)),
    "hans": lambda f: BM @ Vector((-0.09, 0.0, 0.56)),
    "halo": lambda f: P["halo"][0].matrix_world @ Vector((2.3, 0, 0.93)),
    "helmet": lambda f: BM @ (A.HEAD_C + Vector((0, 0, 0.15))),
}
St.export_anchors(sc, Wd.active_camera, pts, F0, F1, ROOT + "/renders/anchors_s5.json")
Wd.run_render(sc, sys.argv)
