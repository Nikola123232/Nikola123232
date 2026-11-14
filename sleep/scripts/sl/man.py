"""The man: articulated character with casual clothes, detailed head (skin shader with eye-bags / pallor / stubble, eyes with iris+cornea,
upper/lower eyelids, lashes, brows, hair), blink / gaze / droop control, seated pose, two-bone arm IK, breathing."""
import sys, math, random
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts"); sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler, noise
from vol.human import *          # core helpers, A (anatomy module with BONES2 patch), pose/aim/eul, gauss, sstep, skin_weights2
from f1 import anatomy as A

HEAD_C = A.HEAD_C
EYE_C = {s: Vector((0.077, s * 0.034, -0.002)) for s in (1, -1)}       # head-local eye centres
RE = 0.0120                                                              # eyeball radius


# ------------------------------------------------------------------ materials
def val_node(nodes, name, v=0.0):
    n = nodes.new("ShaderNodeValue"); n.name = name; n.label = name; n.outputs[0].default_value = v; return n


def skin_material(name="skin", lid=False):
    m = bpy.data.materials.new(name); nodes, links = m.node_tree.nodes, m.node_tree.links
    p = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    X, Y, Z = sep.outputs
    pale = val_node(nodes, "PALE", 0.0); bags = val_node(nodes, "BAGS", 0.0); stub = val_node(nodes, "STUB", 0.35); red = val_node(nodes, "FLUSH", 0.0)

    def mth(op, a, b=None, c=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = float(v)
            else: links.new(v, n.inputs[i])
        return n.outputs[0]
    base = nodes.new("ShaderNodeMix"); base.data_type = 'RGBA'
    links.new(pale.outputs[0], base.inputs[0]); base.inputs[6].default_value = (0.52, 0.34, 0.26, 1); base.inputs[7].default_value = (0.60, 0.47, 0.42, 1)
    # freckle / blotch variation
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 55; nz.inputs["Detail"].default_value = 6; links.new(tc.outputs["Object"], nz.inputs[0])
    var = nodes.new("ShaderNodeMix"); var.data_type = 'RGBA'; var.inputs[0].default_value = 0.10
    links.new(base.outputs[2], var.inputs[6]); links.new(nz.outputs["Color"], var.inputs[7])
    col = var.outputs[2]
    # flush (redness) + eye bags: ring below / around the eyes (head-local coordinates), skipped on lids (they use BAGS directly)
    if not lid:
        d = [mth('SUBTRACT', mth('ABSOLUTE', Y), 0.034), mth('ADD', Z, 0.020)]
        r = mth('SQRT', mth('ADD', mth('MULTIPLY', d[0], d[0]), mth('MULTIPLY', d[1], d[1])))
        ring = mth('MULTIPLY', mth('MAXIMUM', mth('SUBTRACT', 1.0, mth('DIVIDE', r, 0.026)), 0.0), mth('GREATER_THAN', X, 0.03))
        bagf = mth('MULTIPLY', mth('MULTIPLY', ring, bags.outputs[0]), 0.9)
    else:
        bagf = mth('MULTIPLY', bags.outputs[0], 0.6)
    mb = nodes.new("ShaderNodeMix"); mb.data_type = 'RGBA'; links.new(bagf, mb.inputs[0]); links.new(col, mb.inputs[6]); mb.inputs[7].default_value = (0.30, 0.20, 0.27, 1)
    # stubble on lower face / upper lip (head local)
    if not lid:
        vo = nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 900; vo.feature = 'F1'; links.new(tc.outputs["Object"], vo.inputs[0])
        pts = mth('LESS_THAN', vo.outputs["Distance"], 0.32)
        region = mth('MULTIPLY', mth('LESS_THAN', Z, -0.030), mth('GREATER_THAN', X, -0.01))
        sf = mth('MULTIPLY', mth('MULTIPLY', pts, region), stub.outputs[0])
        ms = nodes.new("ShaderNodeMix"); ms.data_type = 'RGBA'; links.new(sf, ms.inputs[0]); links.new(mb.outputs[2], ms.inputs[6]); ms.inputs[7].default_value = (0.05, 0.035, 0.03, 1)
        col = ms.outputs[2]
    else:
        col = mb.outputs[2]
    fl = nodes.new("ShaderNodeMix"); fl.data_type = 'RGBA'; links.new(red.outputs[0], fl.inputs[0]); links.new(col, fl.inputs[6]); fl.inputs[7].default_value = (0.72, 0.32, 0.27, 1)
    links.new(fl.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.48; p.inputs["Specular IOR Level"].default_value = 0.45
    p.inputs["Subsurface Weight"].default_value = 0.10; p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.22); p.inputs["Subsurface Scale"].default_value = 0.004
    p.inputs["Sheen Weight"].default_value = 0.15
    pores = nodes.new("ShaderNodeTexNoise"); pores.inputs["Scale"].default_value = 700; pores.inputs["Detail"].default_value = 3; links.new(tc.outputs["Object"], pores.inputs[0])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.0004
    links.new(pores.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    return m


def hair_material():
    m = mat("hair", (0.035, 0.024, 0.018), rough=0.42, sheen=0.4, spec=0.6)
    return m


def eye_materials():
    # sclera with veins (RED value)
    sc = bpy.data.materials.new("sclera"); nodes, links = sc.node_tree.nodes, sc.node_tree.links; p = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord"); red = val_node(nodes, "RED", 0.15)
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 140; nz.inputs["Detail"].default_value = 7; nz.inputs["Roughness"].default_value = 0.7; links.new(tc.outputs["Object"], nz.inputs[0])
    vm = nodes.new("ShaderNodeMath"); vm.operation = 'GREATER_THAN'; vm.inputs[1].default_value = 0.55; links.new(nz.outputs["Fac"], vm.inputs[0])
    vm2 = nodes.new("ShaderNodeMath"); vm2.operation = 'MULTIPLY'; links.new(vm.outputs[0], vm2.inputs[0]); links.new(red.outputs[0], vm2.inputs[1])
    gl = nodes.new("ShaderNodeMath"); gl.operation = 'MULTIPLY'; gl.inputs[1].default_value = 0.35; links.new(red.outputs[0], gl.inputs[0])
    tot = nodes.new("ShaderNodeMath"); tot.operation = 'ADD'; links.new(vm2.outputs[0], tot.inputs[0]); links.new(gl.outputs[0], tot.inputs[1])
    mx = nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; links.new(tot.outputs[0], mx.inputs[0]); mx.inputs[6].default_value = (0.93, 0.91, 0.88, 1); mx.inputs[7].default_value = (0.85, 0.22, 0.2, 1)
    links.new(mx.outputs[2], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.25
    # iris: radial fibres, limbal ring, pupil (PUPIL radius value)
    ir = bpy.data.materials.new("iris"); nodes, links = ir.node_tree.nodes, ir.node_tree.links; p = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord"); sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(tc.outputs["Object"], sep.inputs[0])
    pup = val_node(nodes, "PUPIL", 0.0034)

    def mth(op, a, b=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = float(v)
            else: links.new(v, n.inputs[i])
        return n.outputs[0]
    r = mth('SQRT', mth('ADD', mth('MULTIPLY', sep.outputs[1], sep.outputs[1]), mth('MULTIPLY', sep.outputs[2], sep.outputs[2])))
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 4; nz.noise_dimensions = '3D'
    sc_ = nodes.new("ShaderNodeVectorMath"); sc_.operation = 'MULTIPLY'; sc_.inputs[1].default_value = (0.2, 3.0, 3.0); links.new(tc.outputs["Object"], sc_.inputs[0]); links.new(sc_.outputs[0], nz.inputs[0])
    cr = nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.10, 0.05, 0.025, 1); cr.color_ramp.elements[1].color = (0.42, 0.26, 0.10, 1); links.new(nz.outputs["Fac"], cr.inputs[0])
    limb = mth('MAXIMUM', mth('SUBTRACT', mth('DIVIDE', r, 0.0062), 0.55), 0.0)
    dark = nodes.new("ShaderNodeMix"); dark.data_type = 'RGBA'; links.new(mth('MINIMUM', mth('MULTIPLY', limb, 1.6), 1.0), dark.inputs[0]); links.new(cr.outputs[0], dark.inputs[6]); dark.inputs[7].default_value = (0.02, 0.012, 0.008, 1)
    pm = nodes.new("ShaderNodeMix"); pm.data_type = 'RGBA'; links.new(mth('LESS_THAN', r, pup.outputs[0]), pm.inputs[0]); links.new(dark.outputs[2], pm.inputs[6]); pm.inputs[7].default_value = (0.0, 0.0, 0.0, 1)
    links.new(pm.outputs[2], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.2
    co = bpy.data.materials.new("cornea"); nodes, links = co.node_tree.nodes, co.node_tree.links; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); tr = nodes.new("ShaderNodeBsdfTransparent"); gl = nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.02
    lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.1; mx = nodes.new("ShaderNodeMixShader")
    fm = nodes.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; fm.inputs[1].default_value = 0.9; links.new(lw.outputs["Fresnel"], fm.inputs[0]); links.new(fm.outputs[0], mx.inputs[0])
    links.new(tr.outputs[0], mx.inputs[1]); links.new(gl.outputs[0], mx.inputs[2]); links.new(mx.outputs[0], out.inputs[0])
    return sc, ir, co


def cloth_material():
    m = bpy.data.materials.new("clothes"); nodes, links = m.node_tree.nodes, m.node_tree.links; p = nodes.get("Principled BSDF")
    at = nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = "restpos"
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(at.outputs["Color"], sep.inputs[0]); X, Y, Z = sep.outputs

    def mth(op, a, b=None):
        n = nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = float(v)
            else: links.new(v, n.inputs[i])
        return n.outputs[0]
    ay = mth('ABSOLUTE', Y)
    arms = mth('MULTIPLY', mth('GREATER_THAN', ay, 0.155), mth('GREATER_THAN', Z, 0.12))
    legs = mth('MULTIPLY', mth('LESS_THAN', Z, 0.10), mth('GREATER_THAN', X, 0.10))
    hand = mth('MULTIPLY', arms, mth('GREATER_THAN', X, 0.325))
    shoe = mth('MULTIPLY', legs, mth('GREATER_THAN', X, 0.77))
    cuff = mth('MULTIPLY', arms, mth('MULTIPLY', mth('GREATER_THAN', X, 0.29), mth('LESS_THAN', X, 0.325)))
    m1 = nodes.new("ShaderNodeMix"); m1.data_type = 'RGBA'; links.new(legs, m1.inputs[0]); m1.inputs[6].default_value = (0.085, 0.095, 0.115, 1); m1.inputs[7].default_value = (0.035, 0.05, 0.095, 1)   # hoodie / jeans
    m2 = nodes.new("ShaderNodeMix"); m2.data_type = 'RGBA'; links.new(cuff, m2.inputs[0]); links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (0.06, 0.065, 0.08, 1)
    m3 = nodes.new("ShaderNodeMix"); m3.data_type = 'RGBA'; links.new(hand, m3.inputs[0]); links.new(m2.outputs[2], m3.inputs[6]); m3.inputs[7].default_value = (0.58, 0.39, 0.30, 1)
    m4 = nodes.new("ShaderNodeMix"); m4.data_type = 'RGBA'; links.new(shoe, m4.inputs[0]); links.new(m3.outputs[2], m4.inputs[6]); m4.inputs[7].default_value = (0.05, 0.05, 0.055, 1)
    links.new(m4.outputs[2], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.85; p.inputs["Sheen Weight"].default_value = 0.18; p.inputs["Sheen Roughness"].default_value = 0.5
    tc = nodes.new("ShaderNodeTexCoord"); wv = nodes.new("ShaderNodeTexNoise"); wv.inputs["Scale"].default_value = 260; wv.inputs["Detail"].default_value = 2; links.new(tc.outputs["Object"], wv.inputs[0])
    wv2 = nodes.new("ShaderNodeTexNoise"); wv2.inputs["Scale"].default_value = 9; wv2.inputs["Detail"].default_value = 5; links.new(tc.outputs["Object"], wv2.inputs[0])
    ad = nodes.new("ShaderNodeMath"); ad.operation = 'ADD'; links.new(wv.outputs["Fac"], ad.inputs[0]); links.new(wv2.outputs["Fac"], ad.inputs[1])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.004
    links.new(ad.outputs[0], bump.inputs["Height"]); links.new(bump.outputs[0], p.inputs["Normal"])
    return m


# ------------------------------------------------------------------ body
def build_body_skin(M, arm, inflate=1.0):
    mb = bpy.data.metaballs.new("body_mb"); mb.resolution = 0.010; mb.render_resolution = 0.008; mb.threshold = 0.6
    mo = bpy.data.objects.new("body_mb", mb); link(mo)

    def ell(c, size, r=0.1, stiff=2.0):
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = c; e.radius = r * 1.65 * inflate; e.size_x, e.size_y, e.size_z = size; e.stiffness = stiff

    def cap(a, b, r, stiff=2.0):
        a, b = Vector(a), Vector(b); e = mb.elements.new(); e.type = 'CAPSULE'; e.co = (a + b) / 2; e.radius = r * 1.65 * inflate
        e.size_x = (b - a).length / 2; e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized()); e.stiffness = stiff
    cap((-0.045, 0, 0.50), (-0.005, 0, 0.665), 0.064 / inflate * 1.0); ell((-0.045, 0, 0.545), (0.9, 2.3, 0.9), 0.075)
    ell((-0.07, 0, 0.52), (0.8, 1.7, 0.7), 0.075)                                               # hood bunched at the collar
    ell((-0.005, 0, 0.405), (0.95, 1.45, 1.05), 0.135); ell((0.0, 0, 0.255), (0.95, 1.30, 1.0), 0.125); ell((-0.01, 0, 0.09), (1.0, 1.45, 0.85), 0.125)
    ell((-0.06, 0.06, 0.0), (1.0, 1.0, 0.8), 0.08); ell((-0.06, -0.06, 0.0), (1.0, 1.0, 0.8), 0.08)
    cap((-0.04, -0.17, 0.475), (-0.04, 0.17, 0.475), 0.06)
    for s in (1, -1):
        cap(A.SHOULDER[s], A.ELBOW[s], 0.048); cap(A.ELBOW[s], A.WRIST[s], 0.040)
        ell(A.WRIST[s] + Vector((0.04, 0, 0.0)), (1.35, 0.75, 0.9), 0.040)
        cap(A.HIP[s], A.HIP[s].lerp(A.KNEE[s], 0.55), 0.086); cap(A.HIP[s].lerp(A.KNEE[s], 0.5), A.KNEE[s], 0.066)
        cap(A.KNEE[s], A.ANKLE[s], 0.054); cap(A.ANKLE[s] + Vector((-0.03, 0, -0.01)), A.TOE[s], 0.050)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg)); bpy.data.objects.remove(mo)
    skin = bpy.data.objects.new("body", me); link(skin); me.materials.append(M["cloth"])
    for pp in me.polygons: pp.use_smooth = True
    sm = skin.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.iterations = 5; apply_mods(skin)
    ca = skin.data.color_attributes.new("restpos", 'FLOAT_COLOR', 'POINT')
    for v in skin.data.vertices: ca.data[v.index].color = (v.co.x, v.co.y, v.co.z, 1.0)
    skin_weights2(skin, arm)
    return skin


# ------------------------------------------------------------------ head
def _face(p, d):
    x, y, z = p; fx = max(0.0, d.x)
    x += fx * (0.030 * gauss(d.y, 0.11) * gauss(d.z + 0.30, 0.17)) + fx * 0.006 * gauss(d.y, 0.05) * gauss(d.z + 0.02, 0.12)
    x += fx * 0.007 * gauss(d.z - 0.16, 0.09) * (1 - gauss(d.y, 0.05))
    for s in (1, -1):
        x -= fx * 0.021 * gauss(d.y - s * 0.40, 0.135) * gauss(d.z + 0.02, 0.115)
        x += fx * 0.004 * gauss(d.y - s * 0.55, 0.15) * gauss(d.z + 0.22, 0.15)
        x += fx * 0.0012 * gauss(d.y - s * 0.12, 0.05) * gauss(d.z + 0.33, 0.05)            # nostrils
    x += fx * 0.0045 * gauss(d.z + 0.55, 0.07) * gauss(d.y, 0.32) - fx * 0.003 * gauss(d.z + 0.62, 0.03) * gauss(d.y, 0.25)
    x += fx * 0.011 * gauss(d.z + 0.92, 0.14) * gauss(d.y, 0.3)
    if d.z < -0.2: y *= 1 - 0.22 * min(1.0, (-d.z - 0.2) / 0.7)
    if d.x < -0.2: x *= 1.05
    x *= 1 - 0.07 * max(0, d.x) ** 2 * (1 if d.z > -0.5 else 0)
    return Vector((x, y, z))


def build_head2(M, arm, detail=True):
    c = HEAD_C; R = (0.106, 0.086, 0.099)
    bm = bmesh.new(); ellipsoid_bm(bm, (0, 0, 0), R, 160, 100, 0, _face); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    head = obj_from_bm("head_skin", bm, [M["skin"]]); head.location = c; objs = [head]

    def hair(p, d):
        h = sstep(0.0, 0.42, d.z + 1.25 * max(0, -d.x) + 0.1 * abs(d.y) - 0.52); q = _face(p, d)
        n = noise.noise(Vector(d) * 18 + Vector((2, 4, 1)))
        return q * (0.985 + h * 0.060 + 0.014 * n * h * h * h) + Vector((0, 0, 0.004 * h))
    bm = bmesh.new(); ellipsoid_bm(bm, (0, 0, 0), R, 110, 64, 0, hair); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ho = obj_from_bm("hair", bm, [M["hair"]], loc=(0, 0, 0)); ho.location = c; objs.append(ho)
    for s in (1, -1):
        objs.append(ellipsoid(f"ear_{s}", c + Vector((-0.004, s * 0.085, -0.008)), (0.017, 0.006, 0.027), [M["skin"]], 20, 12, rot=Euler((s * 0.25, 0, s * 0.15)).to_quaternion()))
        bmb = bmesh.new(); rngb = random.Random(5 + s)
        for k in range(70):
            u = rngb.random(); arcp = [c + Vector((0.083, s * 0.011, 0.027)), c + Vector((0.088, s * 0.036, 0.033)), c + Vector((0.083, s * 0.060, 0.026))]
            pt = (arcp[0] * (1 - u) ** 2 + arcp[1] * 2 * u * (1 - u) + arcp[2] * u * u) - c
            pt += Vector((0, 0, rngb.uniform(-0.0035, 0.0035))) + Vector((rngb.uniform(-0.0008, 0.0008), 0, 0))
            dv = Vector((0.0, s * 1.0, 0.25 * (1 - u) + 0.0)).normalized() + Vector((0.25, 0, 0.1))
            tube_bm(bmb, [pt, pt + dv.normalized() * 0.0035, pt + dv.normalized() * 0.0068 + Vector((0, 0, -0.0006 * u))], [0.00032, 0.00026, 0.00012], 4)
        bo = obj_from_bm(f"brow_{s}", bmb, [M["hair"]], smooth=True); bo.location = c; objs.append(bo)
    objs.append(ellipsoid("lips", c + Vector((0.0895, 0, -0.058)), (0.0030, 0.016, 0.0044), [M["lips"]], 24, 12))
    for o in objs: A.parent_to_bone(o, arm, "head")
    face = {"head": head, "objs": objs}
    if detail:
        scl, iris_m, cor_m = M["eye_mats"]
        face["pivot"], face["lid_u"], face["lid_l"], face["lash"], face["brow"] = {}, {}, {}, {}, {}
        for s in (1, -1):
            ce = c + EYE_C[s]
            piv = empty(f"eye_pivot_{s}", ce, size=0.005); A.parent_to_bone(piv, arm, "head")
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=56, v_segments=34, radius=RE); eb = obj_from_bm(f"eyeball_{s}", bm, [scl], smooth=True)
            # iris + pupil disc: cap of the sphere in front (+X)
            bm = bmesh.new(); rr = RE * 1.002; N = 36
            rings = []
            for i in range(0, 9):
                th = math.radians(34 * i / 8); row = [bm.verts.new((rr * math.cos(th), rr * math.sin(th) * math.cos(2 * math.pi * j / N), rr * math.sin(th) * math.sin(2 * math.pi * j / N))) for j in range(N)]
                rings.append(row)
            for a_, b_ in zip(rings[:-1], rings[1:]):
                for j in range(N): bm.faces.new((a_[j], a_[(j + 1) % N], b_[(j + 1) % N], b_[j]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            ir = obj_from_bm(f"iris_{s}", bm, [iris_m], smooth=True)
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=28, radius=RE * 1.025); co = obj_from_bm(f"cornea_{s}", bm, [cor_m], smooth=True)
            for o in (eb, ir, co): o.parent = piv; o.location = (0, 0, 0)
            piv.rotation_mode = 'XYZ'
            face["pivot"][s] = piv
            # eyelids: spherical caps rotating about the eye centre (Y axis)
            def lid(name, up, th0, th1):
                bm = bmesh.new(); rl = RE * 1.16; Nu, Nv = 40, 14; grid = []
                for i in range(Nv + 1):
                    th = th0 + (th1 - th0) * i / Nv
                    grid.append([bm.verts.new((rl * math.sin(th) * math.cos(2 * math.pi * j / Nu * 0.72 - 0.72 * math.pi + 0.0) , rl * math.sin(th) * math.sin(2 * math.pi * j / Nu * 0.72 - 0.72 * math.pi), rl * math.cos(th))) for j in range(Nu)])
                return bm, grid
            # build both caps as a sphere sector in front of the eye (azimuth +-70 deg) to avoid covering the back
            def cap_mesh(th0, th1, name):
                bm = bmesh.new(); rl = RE * 1.17; Nu, Nv = 36, 12; grid = []
                for i in range(Nv + 1):
                    th = th0 + (th1 - th0) * i / Nv
                    row = []
                    for j in range(Nu + 1):
                        az = math.radians(-80 + 160 * j / Nu)
                        row.append(bm.verts.new((rl * math.sin(th) * math.cos(az), rl * math.sin(th) * math.sin(az), rl * math.cos(th))))
                    grid.append(row)
                for a_, b_ in zip(grid[:-1], grid[1:]):
                    for j in range(Nu): bm.faces.new((a_[j], a_[j + 1], b_[j + 1], b_[j]))
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                return obj_from_bm(name, bm, [M["skin_lid"]], smooth=True)
            lu = cap_mesh(math.radians(8), math.radians(62), f"lid_up_{s}"); ll = cap_mesh(math.radians(106), math.radians(150), f"lid_low_{s}")
            for o in (lu, ll):
                o.location = ce; A.parent_to_bone(o, arm, "head"); o.location = ce; o.rotation_mode = 'XYZ'
            face["lid_u"][s], face["lid_l"][s] = lu, ll
            # lashes along the upper lid edge (child of the upper lid so they blink with it)
            bm = bmesh.new(); rl = RE * 1.17; th = math.radians(62)
            for k in range(22):
                az = math.radians(-62 + 124 * k / 21); rad = Vector((math.sin(th) * math.cos(az), math.sin(th) * math.sin(az), math.cos(th)))
                base = rad * rl; tan_down = Vector((math.cos(th) * math.cos(az), math.cos(th) * math.sin(az), -math.sin(th)))
                dv = (rad * 0.8 + tan_down * 0.35 + Vector((0, 0, 0.12)) + Vector((0, math.sin(az) * 0.25, 0))).normalized()
                L = 0.0075 * (0.6 + 0.4 * math.cos(az * 0.9))
                tube_bm(bm, [base, base + dv * L * 0.5 + Vector((0, 0, 0.0004)), base + dv * L + Vector((0, 0, 0.0016))], [0.00026, 0.00019, 0.00008], 4)
            lash = obj_from_bm(f"lashes_{s}", bm, [M["hair"]], smooth=True); lash.parent = lu; lash.location = (0, 0, 0)
            face["lash"][s] = lash
            face["brow"][s] = objs[[o.name for o in objs].index(f"brow_{s}")]
        face["scl"], face["iris"] = scl, iris_m
    return face


def build_man(name="man", face_detail=True, inflate=1.06):
    M = A.materials()                              # bone / organ materials not used here but keep the dictionary shape
    M["skin"] = skin_material("skin"); M["skin_lid"] = skin_material("skin_lid", lid=True)
    M["hair"] = hair_material(); M["lips"] = mat("lips", (0.33, 0.19, 0.17), rough=0.45)
    M["eye_mats"] = eye_materials(); M["cloth"] = cloth_material()
    root = empty(name, size=0.2); arm = A.build_armature(name + "_rig")
    H = {"root": root, "arm": arm, "M": M}
    H["body"] = build_body_skin(M, arm, inflate); H["body"].parent = arm
    H["face"] = build_head2(M, arm, face_detail)
    arm.parent = root
    return H


# ------------------------------------------------------------------ face control
def set_face(H, gaze=(0.0, 0.0), openness=1.0, droop=0.0, pupil=0.0034, brow=0.0, side_gaze=None):
    """gaze: (yaw rad, pitch rad); openness 1 open .. 0 closed; droop 0..1 (tired lids); brow: vertical offset (m)."""
    F = H["face"]
    for s in (1, -1):
        g = side_gaze[s] if side_gaze else gaze
        F["pivot"][s].rotation_euler = (0.0, g[1], g[0])
        cl = 1.0 - openness                                  # closure 0..1
        a_u = math.radians(-2 + 14 * droop + (32 - 14 * droop) * cl) + 0.35 * g[1]
        a_l = -math.radians(2 + 9 * cl + 3 * droop)
        F["lid_u"][s].rotation_euler = (0.0, a_u, 0.0); F["lid_l"][s].rotation_euler = (0.0, a_l, 0.0)
        F["brow"][s].location = (0, 0, brow)
    F["iris"].node_tree.nodes["PUPIL"].outputs[0].default_value = pupil


def key_face(H, frame):
    F = H["face"]
    for s in (1, -1):
        for o in (F["pivot"][s], F["lid_u"][s], F["lid_l"][s]): o.keyframe_insert("rotation_euler", frame=frame)
        F["brow"][s].keyframe_insert("location", frame=frame)
    F["iris"].node_tree.nodes["PUPIL"].outputs[0].keyframe_insert("default_value", frame=frame)


def blink_curve(f, events, dur_close=3.0, hold=1.0, dur_open=5.0):
    """events: list of (frame, slow_factor). Returns openness 0..1 at frame f."""
    o = 1.0
    for (fe, k) in events:
        t = f - fe
        c, h, op = dur_close * k, hold * k, dur_open * k
        if t < 0 or t > c + h + op: continue
        o = min(o, 1 - (t / c) if t < c else (0.0 if t < c + h else (t - c - h) / op))
    return max(0.0, min(1.0, o))


def set_skin_state(H, pale=0.0, bags=0.0, flush=0.0, stub=0.35, red=0.15, frame=None):
    M = H["M"]
    for m in (M["skin"], M["skin_lid"]):
        for nm, v in (("PALE", pale), ("BAGS", bags), ("FLUSH", flush), ("STUB", stub)):
            n = m.node_tree.nodes.get(nm)
            if n:
                n.outputs[0].default_value = v
                if frame is not None: n.outputs[0].keyframe_insert("default_value", frame=frame)
    n = H["face"]["scl"].node_tree.nodes["RED"]; n.outputs[0].default_value = red
    if frame is not None: n.outputs[0].keyframe_insert("default_value", frame=frame)


# ------------------------------------------------------------------ pose helpers
def arm_ik(side, target_body, pole=(0.0, 0.0, -1.0)):
    S = A.SHOULDER[side]; L1 = (A.ELBOW[side] - S).length; L2 = (A.WRIST[side] - A.ELBOW[side]).length
    T = Vector(target_body); d = (T - S).length; d = max(0.12, min(L1 + L2 - 1e-3, d)); u = (T - S).normalized()
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0.0, L1 * L1 - a * a))
    pv = Vector(pole); pp = (pv - u * pv.dot(u)).normalized()
    E = S + u * a + pp * h
    return (E - S).normalized(), (S + u * d - E).normalized()


def seated_spec(lean=0.0, head=(0.0, 0.0, 0.0), neck_share=0.5, sway=0.0, hands=None, breath=0.0, lean_side=0.0):
    """Seated on a chair. lean: torso pitch forward (rad); head: (pitch, yaw, roll) relative to torso (+pitch = looking down)."""
    s = {}
    for sd, tag in ((1, "L"), (-1, "R")):
        s[f"thigh_{tag}"] = aim(f"thigh_{tag}", (0.995, sd * 0.05, -0.02))
        s[f"shin_{tag}"] = aim(f"shin_{tag}", (0.10, sd * 0.03, -0.995))
        s[f"foot_{tag}"] = aim(f"foot_{tag}", (0.96, sd * 0.02, -0.12))
        if hands and tag in hands:
            du, df = arm_ik(sd, hands[tag], pole=(-0.1, sd * 0.6, -0.8))
        else:
            du, df = aim(f"uparm_{tag}", (0.10, sd * 0.22, -0.97)), aim(f"farm_{tag}", (0.92, sd * 0.12, -0.38))
            du = Vector((0.10, sd * 0.22, -0.97)).normalized(); df = Vector((0.92, sd * 0.12, -0.38)).normalized()
        s[f"uparm_{tag}"] = aim(f"uparm_{tag}", du); s[f"farm_{tag}"] = aim(f"farm_{tag}", df)
    sp = eul(lean_side, lean + breath, sway)
    s["spine"] = sp
    pitch, yaw, roll = head
    s["neck1"] = sp @ eul(roll * neck_share * 0.5, pitch * neck_share * 0.5, yaw * neck_share * 0.5)
    s["neck2"] = s["neck1"] @ eul(roll * neck_share * 0.5, pitch * neck_share * 0.5, yaw * neck_share * 0.5)
    s["head"] = s["neck2"] @ eul(roll * (1 - neck_share), pitch * (1 - neck_share), yaw * (1 - neck_share))
    return s


def standing_spec(head=(0.0, 0.0, 0.0), lean=0.0):
    s = stand_spec()
    s["spine"] = eul(0, lean, 0)
    s["neck1"] = s["spine"] @ eul(head[2] * 0.3, head[0] * 0.3, head[1] * 0.3); s["neck2"] = s["neck1"] @ eul(head[2] * 0.3, head[0] * 0.3, head[1] * 0.3)
    s["head"] = s["neck2"] @ eul(head[2] * 0.4, head[0] * 0.4, head[1] * 0.4)
    return s
