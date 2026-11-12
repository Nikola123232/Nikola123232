"""Core helpers: scene setup, materials, procedural mesh builders (lofts, tubes, airfoils, lathes)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, Quaternion, noise

ROOT = "/home/user/Nikola123232"


# ----------------------------------------------------------------------------- scene
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    return sc


def render_settings(sc, res=(720, 1280), samples=12, motion_blur=False, shutter=0.5,
                    transparent_bounces=8, max_bounces=4, pct=100):
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    try:
        sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        sc.cycles.denoising_prefilter = 'ACCURATE'
    except Exception:
        pass
    sc.cycles.max_bounces = max_bounces
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = transparent_bounces
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.cycles.sample_clamp_indirect = 6.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = shutter
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.compression = 15
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.render.threads_mode = 'AUTO'


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


_active_coll = [None]


def set_coll(c):
    _active_coll[0] = c


def link(obj):
    c = _active_coll[0] or bpy.context.scene.collection
    c.objects.link(obj)
    return obj


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = rot
    link(e)
    if parent:
        e.parent = parent
    return e


def obj_from_bm(name, bm, mats=(), smooth=True, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    link(o)
    if parent:
        o.parent = parent
    return o


def add_subsurf(o, levels=2, render=None):
    m = o.modifiers.new("sub", 'SUBSURF')
    m.levels = levels
    m.render_levels = render if render is not None else levels
    return m


def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(oe)
    o.modifiers.clear()
    old = o.data
    o.data = me
    bpy.data.meshes.remove(old)
    return o


def boolean(o, cutter, op='DIFFERENCE', apply=True):
    m = o.modifiers.new("bool", 'BOOLEAN')
    m.operation = op
    m.object = cutter
    m.solver = 'EXACT'
    try:
        m.material_mode = 'TRANSFER'
    except Exception:
        pass
    if apply:
        apply_mods(o)
    return o


def join(objs, name=None):
    """Join meshes into the first object (keeps materials)."""
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world if o.parent is None else o.matrix_world)
        base = len(mats)
        for m in o.data.materials:
            mats.append(m)
        for p in me.polygons:
            p.material_index += base
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in objs:
        bpy.data.objects.remove(o)
    return bm, mats


def hide(o, hidden=True):
    o.hide_render = hidden
    o.hide_viewport = hidden


def key_vis(o, frame, visible):
    o.hide_render = not visible
    o.hide_viewport = not visible
    o.keyframe_insert("hide_render", frame=frame)
    o.keyframe_insert("hide_viewport", frame=frame)


# ----------------------------------------------------------------------------- materials
def _nodes(m):
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m.node_tree.nodes, m.node_tree.links


def mat(name, color=(0.8, 0.8, 0.8), metal=0.0, rough=0.5, coat=0.0, coat_rough=0.03,
        emission=None, estr=0.0, alpha=1.0, transmission=0.0, spec=0.5, aniso=0.0,
        sss=0.0, sss_radius=(0.5, 0.2, 0.1), sheen=0.0):
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    p = nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = coat_rough
    p.inputs["Specular IOR Level"].default_value = spec
    p.inputs["Anisotropic"].default_value = aniso
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["Sheen Weight"].default_value = sheen
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = sss_radius
        p.inputs["Subsurface Scale"].default_value = 0.01
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, 1)
    return m


def emit_mat(name, color, strength=3.0):
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    em.inputs[1].default_value = strength
    links.new(em.outputs[0], out.inputs[0])
    return m


def principled(m):
    return m.node_tree.nodes.get("Principled BSDF")


def carbon_mat(name="carbon", tint=(0.012, 0.012, 0.014), scale=180.0, coat=1.0, rough=0.32):
    """Twill-weave carbon fibre: two crossed wave bands -> anisotropic-looking tone + bump."""
    m = mat(name, tint, metal=0.0, rough=rough, coat=coat, coat_rough=0.04, spec=0.6)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    links.new(tc.outputs["Object"], mp.inputs[0])
    chk = nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 1.0
    chk.inputs["Color1"].default_value = (0.004, 0.004, 0.005, 1)
    chk.inputs["Color2"].default_value = (0.035, 0.036, 0.04, 1)
    links.new(mp.outputs[0], chk.inputs[0])
    links.new(chk.outputs["Color"], p.inputs["Base Color"])
    rr = nodes.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = rough + 0.12
    rr.inputs[4].default_value = rough - 0.12
    links.new(chk.outputs["Fac"], rr.inputs[0])
    links.new(rr.outputs[0], p.inputs["Roughness"])
    return m


def livery_mat(name, base, accent, dark, accent2=None):
    """Car livery using object-space (car-local) coordinates:
    carbon-black lower body, metallic base, fluoro accent stripes."""
    m = mat(name, base, metal=0.55, rough=0.28, coat=1.0, coat_rough=0.02, spec=0.6)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])

    def node_math(op, a, b=None, val=None):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        if isinstance(a, float):
            n.inputs[0].default_value = a
        else:
            links.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, float):
                n.inputs[1].default_value = b
            else:
                links.new(b, n.inputs[1])
        return n.outputs[0]
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    # lower carbon region: z < 0.17 + 0.04*x-ish
    zl = node_math('SUBTRACT', Z, node_math('MULTIPLY_ADD', X, 0.0))
    lower = node_math('LESS_THAN', Z, 0.165)
    # diagonal accent stripe along sidepods/engine cover: band of (z - 0.09*x)
    d = node_math('SUBTRACT', Z, node_math('MULTIPLY', X, 0.07))
    s1 = node_math('MULTIPLY', node_math('GREATER_THAN', d, 0.265), node_math('LESS_THAN', d, 0.305))
    # nose spine stripe
    ay = node_math('ABSOLUTE', Y)
    s2 = node_math('MULTIPLY', node_math('LESS_THAN', ay, 0.035), node_math('GREATER_THAN', X, 2.75))
    stripe = node_math('MAXIMUM', s1, s2)
    mix1 = nodes.new("ShaderNodeMix"); mix1.data_type = 'RGBA'
    links.new(stripe, mix1.inputs[0])
    mix1.inputs[6].default_value = (*base, 1)
    mix1.inputs[7].default_value = (*accent, 1)
    mix2 = nodes.new("ShaderNodeMix"); mix2.data_type = 'RGBA'
    links.new(lower, mix2.inputs[0])
    links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = (*dark, 1)
    links.new(mix2.outputs[2], p.inputs["Base Color"])
    # metallic lower for carbon, accent non-metal
    met = node_math('MULTIPLY', node_math('SUBTRACT', 1.0, node_math('MAXIMUM', lower, stripe)), 0.6)
    links.new(met, p.inputs["Metallic"])
    return m


def xray_mat(name, edge=(0.25, 0.7, 1.0), strength=2.5, base_alpha=0.04, power=0.35):
    """Fresnel-edge glowing translucent shell."""
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = power
    tr = nodes.new("ShaderNodeBsdfTransparent")
    em = nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*edge, 1)
    em.inputs[1].default_value = strength
    gl = nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.15
    gl.inputs["Color"].default_value = (0.08, 0.1, 0.12, 1)
    add = nodes.new("ShaderNodeAddShader")
    links.new(em.outputs[0], add.inputs[0])
    links.new(gl.outputs[0], add.inputs[1])
    rmp = nodes.new("ShaderNodeMapRange")
    rmp.inputs[3].default_value = base_alpha
    rmp.inputs[4].default_value = 1.0
    links.new(lw.outputs["Facing"], rmp.inputs[0])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(rmp.outputs[0], mix.inputs[0])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(add.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    return m


def reveal_mat(name, solid_mat_color, rough=0.6, edge=(0.3, 0.75, 1.0), estr=2.0, base_alpha=0.03,
               sheen=0.0, metal=0.0, coat=0.0):
    """Material that blends from opaque (reveal=0) to x-ray (reveal=1).
    Animate via node 'Reveal' (Value) output default_value."""
    m = bpy.data.materials.new(name)
    nodes, links = _nodes(m)
    p = nodes.get("Principled BSDF")
    out = nodes.get("Material Output")
    p.inputs["Base Color"].default_value = (*solid_mat_color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Sheen Weight"].default_value = sheen
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.35
    tr = nodes.new("ShaderNodeBsdfTransparent")
    em = nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*edge, 1)
    em.inputs[1].default_value = estr
    rmp = nodes.new("ShaderNodeMapRange")
    rmp.inputs[3].default_value = base_alpha
    rmp.inputs[4].default_value = 1.0
    links.new(lw.outputs["Facing"], rmp.inputs[0])
    xm = nodes.new("ShaderNodeMixShader")
    links.new(rmp.outputs[0], xm.inputs[0])
    links.new(tr.outputs[0], xm.inputs[1])
    links.new(em.outputs[0], xm.inputs[2])
    val = nodes.new("ShaderNodeValue")
    val.name = "Reveal"
    val.label = "Reveal"
    val.outputs[0].default_value = 0.0
    fm = nodes.new("ShaderNodeMixShader")
    links.new(val.outputs[0], fm.inputs[0])
    links.new(p.outputs[0], fm.inputs[1])
    links.new(xm.outputs[0], fm.inputs[2])
    links.new(fm.outputs[0], out.inputs[0])
    return m


def key_reveal(m, frame, value):
    v = m.node_tree.nodes["Reveal"]
    v.outputs[0].default_value = value
    v.outputs[0].keyframe_insert("default_value", frame=frame)


def key_input(m, node_name, inp, frame, value):
    n = m.node_tree.nodes[node_name]
    n.inputs[inp].default_value = value
    n.inputs[inp].keyframe_insert("default_value", frame=frame)


# ----------------------------------------------------------------------------- geometry
def superellipse_ring(x, cy, hw, zb, zt, n=32, p_top=2.6, p_bot=5.0, axis='X'):
    """Ring of points in a plane perpendicular to X. Top/bottom have independent squareness."""
    zc = (zb + zt) / 2
    hh = (zt - zb) / 2
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        p = p_top if s >= 0 else p_bot
        y = cy + hw * math.copysign(abs(c) ** (2 / p), c)
        z = zc + hh * math.copysign(abs(s) ** (2 / p), s)
        pts.append(Vector((x, y, z)))
    return pts


def loft(name, rings, mats=(), cap_start=True, cap_end=True, cap_mat=(0, 0), closed=True,
         smooth=True, parent=None):
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    for a, b in zip(vr[:-1], vr[1:]):
        rng = n if closed else n - 1
        for i in range(rng):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_start and closed:
        f = bm.faces.new(list(reversed(vr[0])))
        f.material_index = cap_mat[0]
    if cap_end and closed:
        f = bm.faces.new(vr[-1])
        f.material_index = cap_mat[1]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, mats, smooth, parent)


def interp_sections(secs, steps=3):
    """Catmull-Rom interpolate a list of numeric tuples (section params)."""
    out = []
    n = len(secs)
    for i in range(n - 1):
        p0 = secs[max(i - 1, 0)]; p1 = secs[i]; p2 = secs[i + 1]; p3 = secs[min(i + 2, n - 1)]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(secs[-1])
    return out


def catmull(points, steps=6):
    pts = [Vector(p) for p in points]
    res = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, n - 1)]
        for s in range(steps):
            t = s / steps
            res.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    res.append(pts[-1])
    return res


def tube_bm(bm, points, radius, n=10, up=None, ry=None, matidx=0, caps=True):
    """Add a tube along points into bm. radius: float or list. ry: second radius (elliptic)."""
    pts = [Vector(p) for p in points]
    m = len(pts)
    rad = radius if isinstance(radius, (list, tuple)) else [radius] * m
    rady = ry if isinstance(ry, (list, tuple)) else ([ry] * m if ry else rad)
    # tangents
    tans = []
    for i in range(m):
        t = (pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)])
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    # initial normal
    if up is not None:
        upv = Vector(up)
    else:
        upv = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (upv - tans[0] * upv.dot(tans[0])).normalized()
    rings = []
    for i in range(m):
        if i > 0:
            # parallel transport, or re-project the provided up vector
            if up is not None:
                nn = (upv - tans[i] * upv.dot(tans[i]))
                if nn.length > 1e-6:
                    nrm = nn.normalized()
            else:
                rot = tans[i - 1].rotation_difference(tans[i])
                nrm = (rot @ nrm).normalized()
        bi = tans[i].cross(nrm).normalized()
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            ring.append(bm.verts.new(pts[i] + bi * math.cos(a) * rad[i] + nrm * math.sin(a) * rady[i]))
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            f = bm.faces.new((a[k], a[j], b[j], b[k]))
            f.material_index = matidx
    if caps:
        f = bm.faces.new(list(reversed(rings[0]))); f.material_index = matidx
        f = bm.faces.new(rings[-1]); f.material_index = matidx
    return rings


def tube(name, points, radius, mats=(), n=10, up=None, ry=None, parent=None, smooth=True, caps=True):
    bm = bmesh.new()
    tube_bm(bm, points, radius, n, up, ry, 0, caps)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, mats, smooth, parent)


def rod(name, p1, p2, r, mats=(), n=8, ry=None, up=None, parent=None):
    return tube(name, [p1, p2], r, mats, n, up, ry, parent)


def naca(t=0.12, m=0.06, p=0.4, n=24):
    """NACA 4-digit airfoil, returns closed list of (x,z) chord-normalised, from TE over top to LE to bottom."""
    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    upper, lower = [], []
    for x in xs:
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        if x < p:
            yc = m / p ** 2 * (2 * p * x - x * x); dy = 2 * m / p ** 2 * (p - x)
        else:
            yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x); dy = 2 * m / (1 - p) ** 2 * (p - x)
        th = math.atan(dy)
        upper.append((x - yt * math.sin(th), yc + yt * math.cos(th)))
        lower.append((x + yt * math.sin(th), yc - yt * math.cos(th)))
    pts = list(reversed(upper)) + lower[1:-1]
    return pts


def wing(name, span_pts, chord_f, le_x_f, z_f, aoa_f, mats=(), t=0.12, camber=0.07, n=20,
         flip=True, parent=None):
    """Extrude an inverted (downforce) airfoil along Y. span_pts: list of y values.
    chord_f/le_x_f/z_f/aoa_f: functions of y. Airfoil chord runs from LE (front, +X) to TE (-X)."""
    prof = naca(t, camber, 0.4, n)
    rings = []
    for y in span_pts:
        c = chord_f(y); lx = le_x_f(y); z0 = z_f(y); a = math.radians(aoa_f(y))
        ring = []
        for (u, v) in prof:
            v = -v if flip else v  # inverted wing
            # chord along -X from LE; rotate by aoa (TE up for downforce)
            px = -u * c; pz = v * c
            rx = px * math.cos(a) - pz * math.sin(-a)
            rz = px * math.sin(-a) + pz * math.cos(a)
            ring.append(Vector((lx + rx, y, z0 + rz)))
        rings.append(ring)
    return loft(name, rings, mats, parent=parent)


def lathe_bm(bm, profile, segments=48, axis='Y', matidx=0, center=(0, 0, 0)):
    """Revolve list of (r, a) around axis (a = axial coord). Profile is open polyline."""
    cx, cy, cz = center
    rings = []
    for s in range(segments):
        ang = 2 * math.pi * s / segments
        c, sn = math.cos(ang), math.sin(ang)
        ring = []
        for (r, a) in profile:
            if axis == 'Y':
                ring.append(bm.verts.new((cx + r * c, cy + a, cz + r * sn)))
            elif axis == 'Z':
                ring.append(bm.verts.new((cx + r * c, cy + r * sn, cz + a)))
            else:
                ring.append(bm.verts.new((cx + a, cy + r * c, cz + r * sn)))
        rings.append(ring)
    for s in range(segments):
        a, b = rings[s], rings[(s + 1) % segments]
        for i in range(len(profile) - 1):
            f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
            f.material_index = matidx
    return rings


def ellipsoid_bm(bm, center, radii, seg=32, rings=16, matidx=0, deform=None, rot=None):
    c = Vector(center)
    R = rot.to_matrix() if rot is not None else Matrix.Identity(3)
    verts = []
    top = None
    grid = []
    for i in range(1, rings):
        th = math.pi * i / rings
        row = []
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            p = Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
            if deform:
                p = deform(p, d)
            row.append(bm.verts.new(c + R @ p))
        grid.append(row)
    def pole(z):
        d = Vector((0, 0, z)); p = Vector((0, 0, z * radii[2]))
        if deform:
            p = deform(p, d)
        return bm.verts.new(c + R @ p)
    vt = pole(1); vb = pole(-1)
    for j in range(seg):
        k = (j + 1) % seg
        f = bm.faces.new((vt, grid[0][j], grid[0][k])); f.material_index = matidx
        f = bm.faces.new((vb, grid[-1][k], grid[-1][j])); f.material_index = matidx
    for i in range(len(grid) - 1):
        for j in range(seg):
            k = (j + 1) % seg
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][k], grid[i][k])); f.material_index = matidx
    return grid


def ellipsoid(name, center, radii, mats=(), seg=32, rings=16, deform=None, rot=None, parent=None, smooth=True):
    bm = bmesh.new()
    ellipsoid_bm(bm, (0, 0, 0), radii, seg, rings, 0, deform, rot)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, mats, smooth, parent)
    o.location = center
    return o


def box_bm(bm, center, size, rot=None, matidx=0):
    r = bmesh.ops.create_cube(bm, size=1.0)
    M = Matrix.LocRotScale(Vector(center), rot if rot else Quaternion(), Vector(size))
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = matidx
    return r["verts"]


def text_obj(name, body, size=0.1, font=None, extrude=0.0, align='CENTER', mats=(), parent=None):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = 'CENTER'
    if font:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    o = bpy.data.objects.new(name, cu)
    for m in mats:
        cu.materials.append(m)
    link(o)
    if parent:
        o.parent = parent
    return o


# ----------------------------------------------------------------------------- animation utils
def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.4):
    t = min(1, max(0, t)) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out(t):
    t = min(1, max(0, t))
    return t * t * (3 - 2 * t)


def ease_out_cubic(t):
    t = min(1, max(0, t))
    return 1 - (1 - t) ** 3


def key_loc_rot(o, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=frame)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert("scale", frame=frame)


def linear_fcurves(o):
    ad = o.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points:
                k.interpolation = 'LINEAR'


def _fcurves(action):
    """Blender 5 layered actions: gather fcurves from all channelbags."""
    try:
        return list(action.fcurves)
    except Exception:
        pass
    res = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                res.extend(cb.fcurves)
    return res


def camera(name, lens=35, loc=(0, 0, 0), sensor=36, clip_end=3000, parent=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = 'VERTICAL'
    cd.sensor_height = sensor
    cd.clip_start = 0.02
    cd.clip_end = clip_end
    o = bpy.data.objects.new(name, cd)
    o.location = loc
    link(o)
    if parent:
        o.parent = parent
    return o


def look_at_rot(cam_loc, target, roll=0.0):
    d = Vector(target) - Vector(cam_loc)
    q = d.to_track_quat('-Z', 'Y')
    e = q.to_euler()
    if roll:
        e = (q @ Quaternion((0, 0, 1), math.radians(roll))).to_euler()
    return e


def key_cam(cam, frame, loc, target, lens=None, roll=0.0):
    cam.location = loc
    cam.rotation_euler = look_at_rot(loc, target, roll)
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    if lens is not None:
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=frame)


def fix_euler_continuity(o):
    """Make rotation_euler keyframes continuous (avoid 360 flips)."""
    ad = o.animation_data
    if not (ad and ad.action):
        return
    for fc in _fcurves(ad.action):
        if fc.data_path != "rotation_euler":
            continue
        prev = None
        for k in fc.keyframe_points:
            if prev is not None:
                while k.co[1] - prev > math.pi:
                    k.co[1] -= 2 * math.pi
                while k.co[1] - prev < -math.pi:
                    k.co[1] += 2 * math.pi
            prev = k.co[1]
        fc.update()


def world_sky(sun_elev=22, sun_rot=200, strength=0.18, air=1.0, dust=1.5, disc=False):
    w = bpy.data.worlds.new("sky")
    bpy.context.scene.world = w
    nodes, links = _nodes(w)
    bg = nodes.get("Background")
    sky = nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = 'MULTIPLE_SCATTERING'
    except Exception:
        sky.sky_type = 'SINGLE_SCATTERING'
    sky.sun_elevation = math.radians(sun_elev)
    sky.sun_rotation = math.radians(sun_rot)
    sky.air_density = air
    sky.aerosol_density = dust
    sky.sun_disc = disc
    links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    return w


def world_color(color=(0.01, 0.012, 0.02), strength=1.0):
    w = bpy.data.worlds.new("studio")
    bpy.context.scene.world = w
    nodes, links = _nodes(w)
    bg = nodes.get("Background")
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def light(name, kind='AREA', loc=(0, 0, 5), rot=(0, 0, 0), energy=500, size=2, color=(1, 1, 1),
          angle=None, parent=None, target=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA':
        ld.size = size
    if kind == 'SUN' and angle is not None:
        ld.angle = math.radians(angle)
    if kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = rot
    link(o)
    if target is not None:
        o.rotation_euler = look_at_rot(loc, target)
    if parent:
        o.parent = parent
    return o


def project(sc, cam, p):
    """World point -> normalised (x,y) image coords (0..1, y down) and depth."""
    from bpy_extras.object_utils import world_to_camera_view
    co = world_to_camera_view(sc, cam, Vector(p))
    return co.x, 1 - co.y, co.z


def add_reveal(m, edge=(0.3, 0.75, 1.0), estr=0.6, power=0.3):
    """Insert an x-ray branch into an existing material; 'Reveal' value node: 0 = solid, 1 = x-ray."""
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = [n for n in nodes if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs[0].links[0].from_socket
    lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = power
    tr = nodes.new("ShaderNodeBsdfTransparent")
    em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*edge, 1); em.inputs[1].default_value = estr
    xm = nodes.new("ShaderNodeMixShader")
    links.new(lw.outputs["Facing"], xm.inputs[0]); links.new(tr.outputs[0], xm.inputs[1]); links.new(em.outputs[0], xm.inputs[2])
    val = nodes.new("ShaderNodeValue"); val.name = "Reveal"; val.outputs[0].default_value = 0.0
    fm = nodes.new("ShaderNodeMixShader")
    links.new(val.outputs[0], fm.inputs[0]); links.new(src, fm.inputs[1]); links.new(xm.outputs[0], fm.inputs[2])
    links.new(fm.outputs[0], out.inputs[0])
    return m
