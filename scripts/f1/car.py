"""Procedural modern open-wheel F1 car (2022+ ground-effect era proportions, original livery).
Car-local frame: +X forward, +Z up, rear axle at x=0, front axle x=3.6, ground z=0.
Every body part has its origin at the car origin so object coords == car-local coords (livery shader)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler
from .core import *

WHEELBASE = 3.6
R_WHEEL = 0.36
FRONT_Y = 0.80
REAR_Y = 0.78

PAL = dict(
    base=(0.012, 0.09, 0.22),      # deep metallic racing blue
    accent=(1.0, 0.28, 0.02),      # fluoro orange
    dark=(0.01, 0.01, 0.012),
)


def materials():
    M = {}
    M["livery"] = livery_mat("livery", PAL["base"], PAL["accent"], PAL["dark"])
    M["carbon"] = carbon_mat("carbon")
    M["carbon_ghost"] = carbon_mat("carbon_s5", tint=(0.02, 0.02, 0.024), scale=140)
    M["black"] = mat("satin_black", (0.008, 0.008, 0.009), rough=0.45)
    M["inlet"] = mat("inlet", (0.0, 0.0, 0.0), rough=0.9)
    M["rubber"] = mat("tyre_rubber", (0.022, 0.022, 0.024), rough=0.62, spec=0.35)
    M["band"] = mat("tyre_band", (1.0, 0.75, 0.02), rough=0.5)
    M["white"] = mat("white_print", (0.85, 0.85, 0.85), rough=0.5)
    M["rim"] = mat("rim", (0.03, 0.03, 0.035), metal=0.9, rough=0.25)
    M["cover"] = mat("wheel_cover", (0.012, 0.014, 0.02), metal=0.4, rough=0.3, coat=1.0)
    M["metal"] = mat("titanium", (0.55, 0.55, 0.58), metal=1.0, rough=0.25)
    M["halo"] = mat("halo_paint", (0.01, 0.01, 0.012), metal=0.3, rough=0.25, coat=1.0)
    M["accent"] = mat("accent", PAL["accent"], rough=0.3, coat=1.0)
    M["mirror"] = mat("mirror_glass", (0.9, 0.9, 0.9), metal=1.0, rough=0.02)
    M["disc"] = mat("brake_disc", (0.08, 0.07, 0.07), rough=0.6)
    M["pad"] = mat("cockpit_pad", (0.02, 0.02, 0.025), rough=0.8)
    M["light"] = emit_mat("rain_light", (1.0, 0.05, 0.02), 25)
    return M


# ------------------------------------------------------------------ body sections
TUB = [  # x, half-width, z_bottom, z_top
    (4.72, 0.045, 0.165, 0.235),
    (4.58, 0.085, 0.160, 0.285),
    (4.32, 0.125, 0.165, 0.355),
    (4.00, 0.160, 0.175, 0.430),
    (3.60, 0.195, 0.180, 0.500),
    (3.20, 0.235, 0.160, 0.565),
    (2.80, 0.285, 0.115, 0.615),
    (2.40, 0.330, 0.070, 0.650),
    (2.00, 0.370, 0.055, 0.670),
    (1.70, 0.395, 0.055, 0.690),
    (1.40, 0.395, 0.060, 0.670),
    (1.00, 0.335, 0.070, 0.610),
    (0.60, 0.255, 0.085, 0.545),
    (0.20, 0.180, 0.105, 0.460),
    (-0.20, 0.120, 0.140, 0.400),
    (-0.52, 0.070, 0.180, 0.340),
]

AIRBOX = [
    (1.86, 0.120, 0.600, 0.690),
    (1.76, 0.150, 0.580, 0.960),
    (1.58, 0.165, 0.560, 0.995),
    (1.30, 0.155, 0.540, 0.940),
    (0.90, 0.125, 0.500, 0.820),
    (0.45, 0.090, 0.450, 0.670),
    (0.00, 0.060, 0.400, 0.540),
    (-0.30, 0.045, 0.370, 0.470),
]

SIDEPOD = [  # x, center y, half-width, zb, zt
    (2.30, 0.50, 0.170, 0.250, 0.500),
    (2.24, 0.52, 0.205, 0.215, 0.540),
    (2.05, 0.55, 0.225, 0.180, 0.555),
    (1.70, 0.555, 0.225, 0.160, 0.545),
    (1.25, 0.50, 0.200, 0.140, 0.480),
    (0.85, 0.42, 0.160, 0.130, 0.400),
    (0.45, 0.32, 0.105, 0.120, 0.320),
    (0.12, 0.25, 0.055, 0.120, 0.250),
]


def _rings_tub(secs, n=40, steps=3):
    rings = []
    for (x, hw, zb, zt) in interp_sections(secs, steps):
        rings.append(superellipse_ring(x, 0.0, hw, zb, zt, n, p_top=2.4, p_bot=6.0))
    return rings


def build_body(M, parent):
    # --- monocoque / nose / engine bay, one lofted shell
    tub = loft("tub", _rings_tub(TUB), [M["livery"]], parent=parent)
    add_subsurf(tub, 1)
    apply_mods(tub)
    # cockpit opening: rounded cutter, interior walls receive the pad material
    cut_rings = []
    for x in [2.66, 2.62, 2.5, 2.2, 1.9, 1.76, 1.72]:
        hw = 0.235 if 1.76 < x < 2.62 else 0.20
        cut_rings.append(superellipse_ring(x, 0, hw, 0.28, 1.2, 24, 4, 4))
    cutter = loft("cockpit_cutter", cut_rings, [M["pad"]])
    boolean(tub, cutter)
    bpy.data.objects.remove(cutter)

    # --- airbox / engine cover (separate shell that merges visually with the tub)
    air = loft("airbox", _rings_tub(AIRBOX, 32, 3), [M["livery"]], parent=parent)
    add_subsurf(air, 1)
    # air intake (dark) above the head
    bm = bmesh.new()
    ring = superellipse_ring(1.765, 0, 0.115, 0.83, 0.955, 24, 3.5, 3.5)
    ring2 = superellipse_ring(1.70, 0, 0.09, 0.85, 0.94, 24, 3.5, 3.5)
    vs1 = [bm.verts.new(p) for p in ring]; vs2 = [bm.verts.new(p) for p in ring2]
    for i in range(24):
        j = (i + 1) % 24
        bm.faces.new((vs1[i], vs1[j], vs2[j], vs2[i]))
    bm.faces.new(list(reversed(vs2)))
    obj_from_bm("airbox_intake", bm, [M["inlet"]], parent=parent)
    # roll-hoop camera pod + shark fin
    bm = bmesh.new()
    fin = [(1.30, 0.94), (1.25, 1.02), (0.90, 1.00), (0.10, 0.62), (0.0, 0.54), (0.6, 0.70)]
    verts_l = [bm.verts.new((x, -0.006, z)) for x, z in fin]
    verts_r = [bm.verts.new((x, 0.006, z)) for x, z in fin]
    bm.faces.new(verts_l); bm.faces.new(list(reversed(verts_r)))
    for i in range(len(fin)):
        j = (i + 1) % len(fin)
        bm.faces.new((verts_l[i], verts_l[j], verts_r[j], verts_r[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj_from_bm("shark_fin", bm, [M["livery"]], smooth=False, parent=parent)
    tcam = ellipsoid("tcam", (1.62, 0, 1.015), (0.06, 0.02, 0.018), [M["black"]], 16, 8, parent=parent)

    # --- sidepods (mirrored), dark front inlet
    for side in (1, -1):
        rings = []
        for (x, cy, hw, zb, zt) in interp_sections(SIDEPOD, 3):
            rings.append(superellipse_ring(x, side * cy, hw, zb, zt, 32, 2.8, 3.6))
        sp = loft(f"sidepod_{'L' if side > 0 else 'R'}", rings, [M["livery"], M["inlet"]],
                  cap_mat=(1, 0), parent=parent)
        add_subsurf(sp, 1)
        # inlet lip
        lip = tube(f"inlet_lip_{side}", superellipse_ring(2.305, side * 0.50, 0.17, 0.25, 0.50, 32, 2.8, 3.6) +
                   [superellipse_ring(2.305, side * 0.50, 0.17, 0.25, 0.50, 32, 2.8, 3.6)[0]],
                   0.008, [M["black"]], n=6, caps=False, parent=parent)
        # side impact spar fairing / mirror
        mx = 2.38
        my = side * 0.47
        rod(f"mirror_stalk_{side}", (mx - 0.02, side * 0.36, 0.60), (mx, my, 0.665), 0.008, [M["livery"]], parent=parent)
        mh = ellipsoid(f"mirror_{side}", (mx, my, 0.67), (0.045, 0.075, 0.03), [M["livery"]], 20, 10, parent=parent)
        gl = ellipsoid(f"mirror_glass_{side}", (mx - 0.045, my, 0.67), (0.004, 0.065, 0.022), [M["mirror"]], 16, 8, parent=parent)
    return tub


def build_floor(M, parent):
    # floor plan outline (one side), mirrored
    plan = [(3.15, 0.20), (2.95, 0.42), (2.60, 0.80), (2.20, 0.86), (1.00, 0.86), (0.55, 0.80),
            (0.30, 0.56), (-0.10, 0.52), (-0.45, 0.50)]
    outline = [Vector((x, y, 0)) for x, y in plan] + [Vector((x, -y, 0)) for x, y in reversed(plan)]
    bm = bmesh.new()
    top = [bm.verts.new((p.x, p.y, 0.058)) for p in outline]
    bot = [bm.verts.new((p.x, p.y, 0.035)) for p in outline]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fl = obj_from_bm("floor", bm, [M["carbon"]], smooth=False, parent=parent)
    # floor edge fences / curled edge wing
    for s in (1, -1):
        pts = [(2.5, s * 0.84, 0.06), (1.8, s * 0.86, 0.075), (1.0, s * 0.86, 0.075), (0.6, s * 0.80, 0.07)]
        tube(f"floor_edge_{s}", catmull(pts, 5), 0.012, [M["carbon"]], n=6, ry=0.025, up=(0, 0, 1), parent=parent)
        # underfloor fences visible at the front
        for k, dy in enumerate([0.30, 0.40, 0.50]):
            bm = bmesh.new()
            q = [(3.0 - k * 0.05, s * dy, 0.04), (2.4, s * (dy + 0.1), 0.04), (2.4, s * (dy + 0.1), 0.14), (3.0 - k * 0.05, s * dy, 0.09)]
            bm.faces.new([bm.verts.new(v) for v in q])
            obj_from_bm(f"fence_{s}_{k}", bm, [M["carbon"]], smooth=False, parent=parent)
    # diffuser with strakes
    bm = bmesh.new()
    d = [(0.35, -0.48, 0.05), (0.35, 0.48, 0.05), (-0.55, 0.50, 0.30), (-0.55, -0.50, 0.30)]
    bm.faces.new([bm.verts.new(v) for v in d])
    obj_from_bm("diffuser", bm, [M["carbon"]], smooth=False, parent=parent)
    for y in (-0.48, -0.25, 0.0, 0.25, 0.48):
        bm = bmesh.new()
        st = [(0.35, y, 0.05), (-0.55, y, 0.30), (-0.55, y, 0.12), (0.2, y, 0.035)]
        bm.faces.new([bm.verts.new(v) for v in st])
        obj_from_bm(f"strake_{y}", bm, [M["carbon"]], smooth=False, parent=parent)
    # rear rain light
    ellipsoid("rain_light", (-0.53, 0, 0.30), (0.012, 0.035, 0.012), [M["light"]], 12, 6, parent=parent)
    return fl


def build_front_wing(M, parent, name="front_wing"):
    root = empty(name, (0, 0, 0), parent=parent)
    ys = [i / 28 * 1.94 - 0.97 for i in range(29)]
    elems = [  # chord, LE x, z base, z tip rise, aoa base, aoa tip
        (0.25, 4.98, 0.080, 0.015, 3, 6),
        (0.16, 4.80, 0.118, 0.060, 12, 20),
        (0.12, 4.68, 0.150, 0.105, 22, 30),
        (0.10, 4.60, 0.180, 0.150, 32, 40),
    ]
    for k, (c, lx, zb, rise, a0, a1) in enumerate(elems):
        def zf(y, zb=zb, rise=rise):
            t = min(1, abs(y) / 0.97)
            return zb + rise * t ** 1.6
        def lxf(y, lx=lx, k=k):
            t = abs(y) / 0.97
            return lx - 0.05 * t * k - 0.04 * t * t
        wing(f"{name}_el{k}", ys, lambda y, c=c: c * (1 - 0.15 * abs(y)), lxf, zf,
             lambda y, a0=a0, a1=a1: a0 + (a1 - a0) * abs(y) / 0.97,
             [M["livery"] if k < 3 else M["accent"]], t=0.09, camber=0.07, parent=root)
    for s in (1, -1):  # endplates
        bm = bmesh.new()
        prof = [(5.00, 0.05), (4.98, 0.24), (4.80, 0.33), (4.45, 0.34), (4.40, 0.10), (4.55, 0.05)]
        l = [bm.verts.new((x, s * 0.975, z)) for x, z in prof]
        r = [bm.verts.new((x, s * 0.990, z)) for x, z in prof]
        bm.faces.new(l); bm.faces.new(list(reversed(r)))
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((l[i], l[j], r[j], r[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj_from_bm(f"{name}_ep{s}", bm, [M["carbon"]], smooth=False, parent=root)
    return root


def build_rear_wing(M, parent):
    root = empty("rear_wing", parent=parent)
    ys = [i / 16 * 0.96 - 0.48 for i in range(17)]
    wing("rw_main", ys, lambda y: 0.30, lambda y: -0.48 + 0.03 * (y / 0.48) ** 2,
         lambda y: 0.82 + 0.04 * (abs(y) / 0.48) ** 3, lambda y: 8, [M["livery"]], t=0.11, camber=0.08, parent=root)
    wing("rw_flap", ys, lambda y: 0.20, lambda y: -0.73 + 0.02 * (y / 0.48) ** 2,
         lambda y: 0.905 + 0.04 * (abs(y) / 0.48) ** 3, lambda y: 32, [M["accent"]], t=0.10, camber=0.06, parent=root)
    wing("beam_wing", [i / 10 * 0.9 - 0.45 for i in range(11)], lambda y: 0.16, lambda y: -0.36,
         lambda y: 0.42, lambda y: 10, [M["carbon"]], t=0.12, camber=0.05, parent=root)
    for s in (1, -1):
        bm = bmesh.new()
        prof = [(-0.42, 0.40), (-0.45, 0.80), (-0.52, 0.95), (-0.75, 1.02), (-0.95, 0.98), (-0.98, 0.70), (-0.70, 0.36)]
        l = [bm.verts.new((x, s * 0.485, z)) for x, z in prof]
        r = [bm.verts.new((x, s * 0.500, z)) for x, z in prof]
        bm.faces.new(l); bm.faces.new(list(reversed(r)))
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((l[i], l[j], r[j], r[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj_from_bm(f"rw_ep{s}", bm, [M["livery"]], smooth=False, parent=root)
    # swan-neck pillar
    bm = bmesh.new()
    prof = [(-0.30, 0.38), (-0.48, 0.80), (-0.58, 0.79), (-0.50, 0.34)]
    l = [bm.verts.new((x, -0.012, z)) for x, z in prof]; r = [bm.verts.new((x, 0.012, z)) for x, z in prof]
    bm.faces.new(l); bm.faces.new(list(reversed(r)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((l[i], l[j], r[j], r[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj_from_bm("rw_pillar", bm, [M["carbon"]], smooth=False, parent=root)
    return root


def build_wheel(M, name, width, parent, loc):
    """Returns (hub_empty, spinning_object). Spin axis = local Y."""
    hub = empty(name, loc, parent=parent)
    bm = bmesh.new()
    hw = width / 2
    R = R_WHEEL
    rr = 0.235  # 18-inch rim edge
    # tyre profile (r, axial), open, from inner bead over tread to outer bead
    prof = [(rr, -hw * 0.82), (rr + 0.03, -hw * 0.98), (R - 0.04, -hw), (R - 0.012, -hw * 0.96),
            (R, -hw * 0.82), (R, hw * 0.82), (R - 0.012, hw * 0.96), (R - 0.04, hw), (rr + 0.03, hw * 0.98), (rr, hw * 0.82)]
    lathe_bm(bm, prof, 72, 'Y', 0)
    # coloured compound band on both sidewalls
    for s in (1, -1):
        band = [(R - 0.07, s * hw * 1.001), (R - 0.055, s * hw * 1.001)]
        lathe_bm(bm, band, 72, 'Y', 1)
        # sidewall lettering blocks (make rotation readable)
        for k in range(8):
            a = 2 * math.pi * k / 8
            for j in range(3):
                aa = a + j * 0.05
                r0 = R - 0.105
                c = Vector((r0 * math.cos(aa), s * hw * 1.002, r0 * math.sin(aa)))
                q = Quaternion((0, 1, 0), -aa)
                box_bm(bm, c, (0.012, 0.002, 0.03), q, 2)
    # rim
    rim_prof = [(rr, hw * 0.8), (rr - 0.01, hw * 0.85), (rr - 0.02, hw * 0.6), (rr - 0.02, -hw * 0.7), (rr, -hw * 0.82)]
    lathe_bm(bm, rim_prof, 48, 'Y', 3)
    # outer wheel cover (slightly concave) + centre nut
    for s in (1, -1):
        cov = [(rr - 0.015, s * hw * 0.78), (0.15, s * hw * 0.70), (0.06, s * hw * 0.66), (0.0, s * hw * 0.66)]
        lathe_bm(bm, cov, 48, 'Y', 4)
        # cover graphics: 5 radial accent stripes
        for k in range(5):
            a = 2 * math.pi * k / 5
            c = Vector((0.13 * math.cos(a), s * hw * 0.695, 0.13 * math.sin(a)))
            box_bm(bm, c, (0.15, 0.003, 0.02), Quaternion((0, 1, 0), -a), 5)
        nut = [(0.035, s * hw * 0.66), (0.035, s * hw * 0.75), (0.0, s * hw * 0.75)]
        lathe_bm(bm, nut, 16, 'Y', 3)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    spin = obj_from_bm(name + "_spin", bm, [M["rubber"], M["band"], M["white"], M["rim"], M["cover"], M["accent"]], parent=hub)
    # brake duct drum (non-spinning) on inner side
    inner = -1 if loc[1] > 0 else 1
    bm = bmesh.new()
    drum = [(0.0, inner * hw * 0.5), (0.20, inner * hw * 0.5), (0.20, inner * (hw + 0.06)), (0.0, inner * (hw + 0.06))]
    lathe_bm(bm, drum, 32, 'Y', 0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj_from_bm(name + "_duct", bm, [M["carbon"]], parent=hub)
    return hub, spin


def build_suspension(M, parent):
    parts = []
    def arm(a, b, r=0.014):
        parts.append(rod("susp", a, b, r, [M["carbon"]], n=8, ry=r * 0.4, up=(0, 0, 1), parent=parent))
    for s in (1, -1):
        # front
        up = (WHEELBASE, s * 0.66, 0.50); lo = (WHEELBASE, s * 0.68, 0.22)
        arm((3.95, s * 0.16, 0.48), up); arm((3.30, s * 0.20, 0.47), up)
        arm((3.95, s * 0.14, 0.22), lo); arm((3.25, s * 0.20, 0.20), lo)
        arm((3.55, s * 0.68, 0.24), (3.35, s * 0.18, 0.50), 0.011)      # pull/push rod
        arm((WHEELBASE - 0.1, s * 0.66, 0.30), (3.75, s * 0.15, 0.30), 0.010)  # track rod
        # rear
        up = (0.0, s * 0.62, 0.48); lo = (0.0, s * 0.64, 0.20)
        arm((0.35, s * 0.18, 0.40), up); arm((-0.25, s * 0.12, 0.40), up)
        arm((0.40, s * 0.20, 0.16), lo); arm((-0.25, s * 0.13, 0.17), lo)
        arm((0.02, s * 0.62, 0.45), (0.25, s * 0.17, 0.20), 0.011)
    return parts


def build_halo(M, parent):
    ring = catmull([(1.70, -0.285, 0.70), (1.76, -0.285, 0.86), (1.98, -0.28, 0.915), (2.28, -0.22, 0.925),
                    (2.44, -0.10, 0.92), (2.48, 0.0, 0.915), (2.44, 0.10, 0.92), (2.28, 0.22, 0.925),
                    (1.98, 0.28, 0.915), (1.76, 0.285, 0.86), (1.70, 0.285, 0.70)], 6)
    h1 = tube("halo_ring", ring, 0.024, [M["halo"]], n=14, ry=0.020, parent=parent)
    pil = catmull([(2.66, 0, 0.60), (2.60, 0, 0.75), (2.50, 0, 0.88), (2.47, 0, 0.915)], 5)
    h2 = tube("halo_pillar", pil, [0.03, 0.028, 0.024, 0.022, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
              [M["halo"]], n=12, ry=0.016, parent=parent)
    return [h1, h2]


def build_cockpit_detail(M, parent):
    # padded rim around the opening + steering wheel
    rim = catmull([(1.74, -0.21, 0.67), (1.95, -0.245, 0.668), (2.3, -0.245, 0.652), (2.58, -0.20, 0.625),
                   (2.63, 0.0, 0.62), (2.58, 0.20, 0.625), (2.3, 0.245, 0.652), (1.95, 0.245, 0.668), (1.74, 0.21, 0.67)], 5)
    tube("cockpit_rim", rim, 0.022, [M["pad"]], n=10, parent=parent)
    bm = bmesh.new()
    # steering wheel: grips + centre box
    c = Vector((2.42, 0, 0.56))
    q = Quaternion((0, 1, 0), math.radians(-25))
    box_bm(bm, c, (0.02, 0.20, 0.10), q, 0)
    for s in (1, -1):
        tube_bm(bm, [c + q @ Vector((0, s * 0.10, -0.06)), c + q @ Vector((0, s * 0.14, -0.02)),
                     c + q @ Vector((0, s * 0.14, 0.04)), c + q @ Vector((0, s * 0.11, 0.07))], 0.016, 8, matidx=0)
    box_bm(bm, c + q @ Vector((-0.012, 0, 0.01)), (0.004, 0.08, 0.04), q, 1)
    obj_from_bm("steering_wheel", bm, [M["black"], M["light"]], parent=parent)


def build_number(M, parent, font):
    t = text_obj("nose_number", "07", 0.19, font, 0.002, mats=[M["white"]], parent=parent)
    t.location = (3.95, 0, 0.452)
    t.rotation_euler = (0, math.radians(-11), math.radians(-90))
    for s in (1, -1):
        t2 = text_obj(f"side_number{s}", "07", 0.16, font, 0.002, mats=[M["white"]], parent=parent)
        t2.location = (1.30, s * 0.162, 0.80)
        t2.rotation_euler = (math.radians(90), math.radians(4) * s, math.radians(0 if s < 0 else 180))
    return t


def build_car(name="car", font=None, with_driver_helmet=True):
    """Returns dict of important objects. Root empty is 'root'."""
    M = materials()
    root = empty(name, (0, 0, 0), size=0.5)
    parts = {"root": root, "M": M}
    body = empty(name + "_body", parent=root)
    parts["body"] = body
    parts["tub"] = build_body(M, body)
    build_floor(M, body)
    parts["front_wing"] = build_front_wing(M, body)
    parts["rear_wing"] = build_rear_wing(M, body)
    build_suspension(M, body)
    parts["halo"] = build_halo(M, body)
    build_cockpit_detail(M, body)
    if font:
        build_number(M, body, font)
    wheels = {}
    for key, x, y, w in [("FL", WHEELBASE, FRONT_Y, 0.305), ("FR", WHEELBASE, -FRONT_Y, 0.305),
                         ("RL", 0.0, REAR_Y, 0.405), ("RR", 0.0, -REAR_Y, 0.405)]:
        wheels[key] = build_wheel(M, "wheel_" + key, w, body, (x, y, R_WHEEL))
    parts["wheels"] = wheels
    return parts


def spin_wheels(parts, frame, distance):
    """Key wheel rotation for travelled distance (m)."""
    ang = distance / R_WHEEL
    for key, (hub, spin) in parts["wheels"].items():
        spin.rotation_euler = (0, ang, 0)
        spin.keyframe_insert("rotation_euler", frame=frame)
