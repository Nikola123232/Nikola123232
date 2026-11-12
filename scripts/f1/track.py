"""Procedural race circuit: long straight into a left-hand corner with asphalt run-off and a TecPro barrier."""
import bpy, bmesh, math, random
from mathutils import Vector, Quaternion, Matrix
from .core import *
from . import story

TEX = ROOT + "/assets/textures/"
ROAD_HW = 7.0


def img_mat(name, path, rough=0.5, emission=0.0, repeat=True, spec=0.5):
    m = mat(name, (1, 1, 1), rough=rough, spec=spec)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    t = nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    t.extension = 'REPEAT' if repeat else 'EXTEND'
    links.new(t.outputs[0], p.inputs["Base Color"])
    if emission:
        links.new(t.outputs[0], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emission
    return m


def asphalt_mat(name="asphalt", tone=0.05, rubber=True):
    m = mat(name, (tone, tone, tone * 1.05), rough=0.78, spec=0.45)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    # fine aggregate
    vor = nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 140
    links.new(tc.outputs["Object"], vor.inputs[0])
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], nz.inputs[0])
    nz2 = nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 25; nz2.inputs["Detail"].default_value = 4
    links.new(tc.outputs["Object"], nz2.inputs[0])
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.inputs[3].default_value = tone * 0.6; ramp.inputs[4].default_value = tone * 1.7
    mixv = nodes.new("ShaderNodeMath"); mixv.operation = 'MULTIPLY_ADD'
    links.new(nz.outputs[0], mixv.inputs[0]); mixv.inputs[1].default_value = 0.6
    links.new(nz2.outputs[0], mixv.inputs[2])
    m2 = nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 0.62
    links.new(mixv.outputs[0], m2.inputs[0])
    links.new(m2.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if rubber:
        # darker rubbered-in racing line around y = LANE_Y
        sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
        d = nodes.new("ShaderNodeMath"); d.operation = 'SUBTRACT'; links.new(sep.outputs[1], d.inputs[0]); d.inputs[1].default_value = story.LANE_Y
        a = nodes.new("ShaderNodeMath"); a.operation = 'ABSOLUTE'; links.new(d.outputs[0], a.inputs[0])
        band = nodes.new("ShaderNodeMapRange"); band.inputs[1].default_value = 0.6; band.inputs[2].default_value = 2.2
        band.inputs[3].default_value = 0.55; band.inputs[4].default_value = 1.0
        links.new(a.outputs[0], band.inputs[0])
        mm = nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
        links.new(col, mm.inputs[0]); links.new(band.outputs[0], mm.inputs[1])
        col = mm.outputs[0]
    links.new(col, p.inputs["Base Color"])
    rr = nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.62; rr.inputs[4].default_value = 0.9
    links.new(vor.outputs["Distance"], rr.inputs[0]); links.new(rr.outputs[0], p.inputs["Roughness"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.004
    links.new(vor.outputs["Distance"], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    return m


def grass_mat():
    m = mat("grass", (0.05, 0.12, 0.025), rough=0.85, spec=0.3, sheen=0.4)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 8
    links.new(tc.outputs["Object"], nz.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.03, 0.075, 0.015, 1); cr.color_ramp.elements[1].color = (0.09, 0.17, 0.04, 1)
    links.new(nz.outputs[0], cr.inputs[0]); links.new(cr.outputs[0], p.inputs["Base Color"])
    # mowing stripes
    wv = nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 0.035
    links.new(tc.outputs["Object"], wv.inputs[0])
    nz2 = nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 60
    links.new(tc.outputs["Object"], nz2.inputs[0])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5
    links.new(nz2.outputs[0], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    return m


def stripe_mat(name, c1, c2, period=1.0, rough=0.45):
    """Stripes along UV u (metres)."""
    m = mat(name, c1, rough=rough, coat=0.3)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    uv = nodes.new("ShaderNodeUVMap")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(uv.outputs[0], sep.inputs[0])
    md = nodes.new("ShaderNodeMath"); md.operation = 'PINGPONG'; md.inputs[1].default_value = period
    links.new(sep.outputs[0], md.inputs[0])
    gt = nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = period / 2
    links.new(md.outputs[0], gt.inputs[0])
    mx = nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    links.new(gt.outputs[0], mx.inputs[0]); mx.inputs[6].default_value = (*c1, 1); mx.inputs[7].default_value = (*c2, 1)
    links.new(mx.outputs[2], p.inputs["Base Color"])
    return m


# ------------------------------------------------------------------------------------------------
def centerline():
    """Road centreline points (x, y, heading)."""
    pts = []
    cx = story.CORNER_X
    R = 60.0
    x = -1250.0
    while x < cx:
        pts.append((x, 0.0, 0.0)); x += 8.0
    for i in range(0, 41):
        th = -math.pi / 2 + (math.pi / 2) * i / 40
        pts.append((cx + R * math.cos(th), R + R * math.sin(th), th + math.pi / 2))
    y = R + 8
    while y < R + 400:
        pts.append((cx + R, y, math.pi / 2)); y += 8
    return pts


def strip_mesh(name, pts, off0, off1, z, mats, uv_scale=1.0, ridges=0.0):
    """Ribbon offset from the centreline between lateral offsets off0..off1 (left positive)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    rows = []
    s = 0.0
    prev = None
    for (x, y, h) in pts:
        if prev:
            s += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
        nx, ny = -math.sin(h), math.cos(h)
        n = 4 if ridges else 1
        row = []
        for k in range(n + 1):
            o = off0 + (off1 - off0) * k / n
            zz = z + (ridges * math.sin(math.pi * k / n) if ridges else 0)
            row.append((bm.verts.new((x + nx * o, y + ny * o, zz)), s, k / n))
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        for k in range(len(a) - 1):
            f = bm.faces.new((a[k][0], a[k + 1][0], b[k + 1][0], b[k][0]))
            for loop, (vv, uu, ww) in zip(f.loops, (a[k], a[k + 1], b[k + 1], b[k])):
                loop[uvl].uv = (uu * uv_scale, ww)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return obj_from_bm(name, bm, mats, smooth=True)


def subsection(pts, x0=None, x1=None, th0=None, th1=None):
    res = []
    for p in pts:
        x, y, h = p
        if x0 is not None and not (x0 <= x <= x1 and abs(h) < 1e-6):
            continue
        if th0 is not None and not (th0 <= h <= th1 and h > 1e-6):
            continue
        res.append(p)
    return res


def build_track(detail=True):
    root = empty("track")
    cl = centerline()
    asph = asphalt_mat()
    road = strip_mesh("road", cl, -ROAD_HW, ROAD_HW, 0.0, [asph])
    white = mat("line_white", (0.8, 0.8, 0.78), rough=0.6)
    for side in (1, -1):
        o0 = side * (ROAD_HW - 0.35); o1 = side * (ROAD_HW - 0.2)
        strip_mesh(f"edge_line{side}", cl, min(o0, o1), max(o0, o1), 0.004, [white])
    kerb = stripe_mat("kerb", (0.75, 0.02, 0.02), (0.85, 0.85, 0.85), 2.0)
    kerb_ranges = [(-720, -560), (-420, -300), (-160, -40), (40, story.CORNER_X)]
    for (a, b) in kerb_ranges:
        sub = subsection(cl, a, b)
        for side in (1, -1):
            o0, o1 = (ROAD_HW, ROAD_HW + 1.3) if side > 0 else (-ROAD_HW - 1.3, -ROAD_HW)
            strip_mesh(f"kerb_{a}_{side}", sub, o0, o1, 0.0, [kerb], ridges=0.035)
    sub = subsection(cl, th0=0.01, th1=math.pi / 2 - 0.01)
    strip_mesh("kerb_apex", sub[5:35], ROAD_HW, ROAD_HW + 1.3, 0.0, [kerb], ridges=0.035)
    strip_mesh("kerb_exit", sub[20:], -ROAD_HW - 1.6, -ROAD_HW, 0.0, [kerb], ridges=0.035)

    # ground + run-off
    bpy.ops.mesh.primitive_plane_add(size=1); g = bpy.context.object
    g.name = "grass"; g.scale = (3000, 2000, 1); g.location = (0, 0, -0.03)
    g.data.materials.append(grass_mat())
    bm = bmesh.new()
    BX = story.BARRIER_X
    q = [(story.CORNER_X - 40, -24, -0.01), (BX + 4, -40, -0.01), (BX + 4, 60, -0.01), (story.CORNER_X + 40, 60, -0.01)]
    bm.faces.new([bm.verts.new(v) for v in q])
    runoff = obj_from_bm("runoff", bm, [asphalt_mat("runoff_asph", 0.07, rubber=False)], smooth=False)
    # blue/white painted run-off strip next to the track
    rs = stripe_mat("runoff_paint", (0.05, 0.2, 0.6), (0.8, 0.8, 0.8), 3.0, 0.6)
    bm = bmesh.new()
    q = [(story.CORNER_X - 40, -8.5, -0.005), (story.CORNER_X + 18, -8.5, -0.005), (story.CORNER_X + 18, -11.5, -0.005), (story.CORNER_X - 40, -11.5, -0.005)]
    bm.faces.new([bm.verts.new(v) for v in q])
    obj_from_bm("runoff_paint", bm, [mat("blue_paint", (0.04, 0.16, 0.5), rough=0.6)], smooth=False)

    build_walls()
    if detail:
        build_grandstands()
        build_trees()
        build_marker_boards()
    barrier = build_barrier()
    return root, barrier


def wall_segment(name, p0, p1, height=1.0, boards=True, fence=True, board_mat=None, face=1):
    """Concrete wall with ad boards & catch fence from p0 to p1 (2D)."""
    p0 = Vector((p0[0], p0[1], 0)); p1 = Vector((p1[0], p1[1], 0))
    d = (p1 - p0); L = d.length; d.normalize()
    ang = math.atan2(d.y, d.x)
    concrete = bpy.data.materials.get("concrete") or mat("concrete", (0.42, 0.42, 0.4), rough=0.8)
    bpy.ops.mesh.primitive_cube_add(size=1)
    w = bpy.context.object; w.name = name
    w.scale = (L, 0.35, height); w.location = (p0 + p1) / 2 + Vector((0, 0, height / 2)); w.rotation_euler = (0, 0, ang)
    w.data.materials.append(concrete)
    objs = [w]
    if boards and board_mat:
        bpy.ops.mesh.primitive_plane_add(size=1)
        b = bpy.context.object; b.name = name + "_boards"
        b.scale = (L, 0.8, 1); b.rotation_euler = (math.radians(90), 0, ang)
        b.location = (p0 + p1) / 2 + Vector((0, 0, height * 0.55)) + Vector((-d.y, d.x, 0)) * (-0.18 * face)
        # repeat the board strip every 4 boards (UV x scale)
        uv = b.data.uv_layers[0].data
        for l in uv:
            l.uv.x *= (L / 16.0) * (-1 if face < 0 else 1)
        b.data.materials.append(board_mat)
        objs.append(b)
    if fence:
        post_mat = bpy.data.materials.get("post") or mat("post", (0.35, 0.36, 0.38), metal=0.8, rough=0.4)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=3.5)
        po = bpy.context.object; po.name = name + "_posts"
        po.location = p0 + Vector((0, 0, height + 1.75)); po.data.materials.append(post_mat)
        ar = po.modifiers.new("arr", 'ARRAY'); ar.count = max(1, int(L / 5)); ar.use_relative_offset = False
        ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0, 0)
        po.rotation_euler = (0, 0, ang)
        ar.constant_offset_displace = (5.0, 0, 0)
        # cables
        for zc in (1.6, 2.6, 3.6):
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.012, depth=L)
            c = bpy.context.object; c.name = name + "_cable"
            c.rotation_euler = (0, math.radians(90), ang); c.location = (p0 + p1) / 2 + Vector((0, 0, height + zc - 1.0))
            c.data.materials.append(post_mat)
        # mesh fence plane (procedural wire grid, alpha)
        fm = bpy.data.materials.get("fence") or fence_mat()
        bpy.ops.mesh.primitive_plane_add(size=1)
        f = bpy.context.object; f.name = name + "_fence"
        f.scale = (L, 3.2, 1); f.rotation_euler = (math.radians(90), 0, ang)
        f.location = (p0 + p1) / 2 + Vector((0, 0, height + 1.6))
        f.data.materials.append(fm)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return objs


def fence_mat():
    """Chain-link look: two perpendicular thin wave bands -> wire mask; everything else transparent."""
    m = bpy.data.materials.new("fence")
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    def band(a, b, period=0.06):
        ad = nodes.new("ShaderNodeMath"); ad.operation = 'ADD'
        links.new(a, ad.inputs[0]); links.new(b, ad.inputs[1])
        pp = nodes.new("ShaderNodeMath"); pp.operation = 'PINGPONG'; pp.inputs[1].default_value = period / 2
        links.new(ad.outputs[0], pp.inputs[0])
        lt = nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = period * 0.06
        links.new(pp.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    neg = nodes.new("ShaderNodeMath"); neg.operation = 'MULTIPLY'; neg.inputs[1].default_value = -1
    links.new(sep.outputs[2], neg.inputs[0])
    horiz = nodes.new("ShaderNodeMath"); horiz.operation = 'ADD'
    links.new(sep.outputs[0], horiz.inputs[0]); links.new(sep.outputs[1], horiz.inputs[1])
    w1 = band(horiz.outputs[0], sep.outputs[2]); w2 = band(horiz.outputs[0], neg.outputs[0])
    mx_ = nodes.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'
    links.new(w1, mx_.inputs[0]); links.new(w2, mx_.inputs[1])
    sc_ = nodes.new("ShaderNodeMath"); sc_.operation = 'MULTIPLY_ADD'
    links.new(mx_.outputs[0], sc_.inputs[0]); sc_.inputs[1].default_value = 0.75; sc_.inputs[2].default_value = 0.08
    tr = nodes.new("ShaderNodeBsdfTransparent")
    met = nodes.new("ShaderNodeBsdfPrincipled"); met.inputs["Base Color"].default_value = (0.45, 0.45, 0.47, 1)
    met.inputs["Metallic"].default_value = 0.9; met.inputs["Roughness"].default_value = 0.4
    mix = nodes.new("ShaderNodeMixShader")
    links.new(sc_.outputs[0], mix.inputs[0])
    links.new(tr.outputs[0], mix.inputs[1]); links.new(met.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])
    return m


def build_walls():
    bm_ = img_mat("boards", TEX + "boards.png", rough=0.4, emission=0.15)
    wall_segment("wall_L", (-1250, 13.5), (story.CORNER_X - 12, 13.5), board_mat=bm_, face=1)
    wall_segment("wall_R", (-1250, -14.5), (story.CORNER_X - 45, -14.5), board_mat=bm_, face=-1)
    wall_segment("wall_R2", (story.CORNER_X - 45, -14.5), (story.CORNER_X - 5, -36), board_mat=bm_, face=-1, fence=False)
    # wall on the outside of the corner exit (left side of run-off)
    wall_segment("wall_exit", (story.CORNER_X + 75, 70), (story.CORNER_X + 75, 400), board_mat=bm_, face=1)


def build_grandstands():
    crowd = img_mat("crowd", TEX + "crowd.png", rough=0.9)
    roofm = mat("roof", (0.85, 0.86, 0.88), metal=0.3, rough=0.4)
    steel = mat("steel", (0.3, 0.3, 0.33), metal=0.8, rough=0.5)
    def stand(x0, x1, y0, facing_y=-1, rows=12, depth=14, h=10, ang=0.0, origin=None):
        root = empty("stand")
        L = x1 - x0
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new()
        # stepped terraces as one sloped textured surface (crowd texture) + roof
        p = [(0, 0, 1.5), (L, 0, 1.5), (L, depth, h), (0, depth, h)]
        f = bm.faces.new([bm.verts.new(v) for v in p])
        for loop, uvv in zip(f.loops, [(0, 0), (L / 40, 0), (L / 40, 1), (0, 1)]):
            loop[uvl].uv = uvv
        o = obj_from_bm("stand_seats", bm, [crowd], smooth=False, parent=root)
        bm = bmesh.new()
        box_bm(bm, (L / 2, depth + 0.5, h / 2), (L, 1.0, h + 2))
        box_bm(bm, (L / 2, depth * 0.45, h + 4.5), (L + 2, depth * 1.3, 0.4), matidx=1)
        for k in range(int(L / 12) + 1):
            box_bm(bm, (k * 12, depth * 0.95, (h + 4.5) / 2), (0.4, 0.4, h + 4.5))
        obj_from_bm("stand_struct", bm, [steel, roofm], smooth=False, parent=root)
        root.location = (x0, y0, 0) if origin is None else origin
        root.rotation_euler = (0, 0, ang)
        if facing_y > 0:
            root.scale.y = -1
        return root
    stand(-560, -90, 22)
    stand(-60, 60, 22)
    # behind the crash barrier, facing the run-off
    bx = story.BARRIER_X
    stand(0, 70, 0, origin=(bx + 30, -30, 0), ang=math.radians(90))


def build_trees():
    random.seed(7)
    trunk = mat("trunk", (0.08, 0.05, 0.03), rough=0.9)
    leaf_cols = [(0.03, 0.08, 0.02), (0.05, 0.1, 0.03), (0.04, 0.07, 0.025)]
    protos = []
    for k in range(3):
        bm = bmesh.new()
        tube_bm(bm, [(0, 0, 0), (0, 0, 4.5)], [0.25, 0.15], 6)
        def dfm(p, d, k=k):
            n = noise.noise(Vector(d) * 2.3 + Vector((k * 3, 0, 0)))
            return p * (1 + 0.35 * n)
        ellipsoid_bm(bm, (0, 0, 7 + k), (3.2 + k * 0.4, 3.2 + k * 0.4, 4.5), 14, 9, 1, dfm)
        lm = mat(f"leaf{k}", leaf_cols[k], rough=0.85, sheen=0.5)
        o = obj_from_bm(f"tree_proto{k}", bm, [trunk, lm], smooth=True)
        o.location = (0, 0, -100)
        protos.append(o)
    BX = story.BARRIER_X
    for i in range(420):
        side = random.choice((1, -1))
        x = random.uniform(-1250, 500)
        y = side * random.uniform(48, 160)
        if story.CORNER_X - 50 < x < BX + 40 and -60 < y < 120:
            continue
        p = random.choice(protos)
        o = bpy.data.objects.new("tree", p.data); link(o)
        o.location = (x, y, 0); s = random.uniform(0.8, 1.5); o.scale = (s, s, s * random.uniform(0.9, 1.3))
        o.rotation_euler = (0, 0, random.uniform(0, 6.28))
    for i in range(90):  # dense backdrop behind barrier
        x = BX + random.uniform(45, 140); y = random.uniform(-120, 160)
        p = random.choice(protos)
        o = bpy.data.objects.new("tree", p.data); link(o)
        o.location = (x, y, 0); s = random.uniform(0.9, 1.6); o.scale = (s, s, s)


def build_marker_boards():
    font = ROOT + "/assets/fonts/Anton-Regular.ttf"
    white = mat("board_white", (0.9, 0.9, 0.9), rough=0.5)
    blk = mat("board_black", (0.02, 0.02, 0.02), rough=0.5)
    for i, dist in enumerate((300, 200, 100)):
        x = story.CORNER_X - dist + 40
        bpy.ops.mesh.primitive_cube_add(size=1); b = bpy.context.object
        b.scale = (0.08, 1.2, 1.0); b.location = (x, -11.0, 1.2); b.data.materials.append(white)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=0.7); p = bpy.context.object
        p.location = (x, -11.0, 0.35); p.data.materials.append(blk)
        t = text_obj(f"mk{dist}", str(dist), 0.7, font, 0.01, mats=[blk])
        t.location = (x - 0.05, -11.0, 1.2); t.rotation_euler = (math.radians(90), 0, math.radians(-90))


def build_barrier():
    """TecPro barrier: 3 rows of interlocking blocks in front of a concrete wall. Returns list of impact-zone blocks."""
    BX = story.BARRIER_X
    blue = img_mat("tecpro_b", TEX + "tecpro_blue.png", rough=0.55)
    red = img_mat("tecpro_r", TEX + "tecpro_red.png", rough=0.55)
    wall_segment("barrier_wall", (BX + 4.2, -45), (BX + 4.2, 70), height=1.2, board_mat=bpy.data.materials["boards"], face=-1)
    blocks = []
    static_bm = bmesh.new()
    k = 0
    for row in range(3):
        y = -45.0 + (0.75 if row % 2 else 0)
        while y < 70:
            c = (BX + 0.29 + row * 0.6, y + 0.75, 0.5)
            mi = (k + row) % 2
            if -16 < y < 2:
                bm = bmesh.new()
                box_bm(bm, (0, 0, 0), (0.58, 1.48, 1.0), matidx=0)
                bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.04, segments=2)
                o = obj_from_bm(f"tecpro_{row}_{k}", bm, [blue if mi else red], smooth=False)
                o.location = c
                o["rest"] = c
                o["row"] = row
                blocks.append(o)
            else:
                vs = box_bm(static_bm, c, (0.58, 1.48, 1.0), matidx=mi)
            y += 1.5; k += 1
    obj_from_bm("tecpro_static", static_bm, [red, blue], smooth=False)
    return blocks
