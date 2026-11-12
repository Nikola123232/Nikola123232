"""Crash effects driven by the shared physical timeline (real time). All deterministic (seeded)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, Quaternion
from .core import *
from . import story as S, car as C
from .world import car_matrix

G = Vector((0, 0, -9.81))
T_I = S.T_IMP_TARGET


def car_M(t):
    return car_matrix(S.car_state(t))


# ------------------------------------------------------------------ ballistic integrator with ground bounce
def ballistic(p0, v0, w0, t0, times, ground=0.02, rest=0.3, fric=0.55, dt=1 / 1000):
    """Returns {t: (pos, euler)} for requested times (sorted), integrating from t0."""
    out = {}
    p = Vector(p0); v = Vector(v0); w = Vector(w0); rot = Vector((0, 0, 0)); t = t0
    for tq in sorted(times):
        if tq <= t0:
            out[tq] = (Vector(p0), Vector((0, 0, 0)))
            continue
        while t < tq - 1e-12:
            h = min(dt, tq - t)
            v += G * h
            p += v * h
            rot += w * h
            if p.z < ground:
                p.z = ground
                if v.z < 0:
                    v.z = -v.z * rest
                    v.x *= fric; v.y *= fric; w *= fric
                    if abs(v.z) < 0.4:
                        v.z = 0
                        v.x *= 0.9; v.y *= 0.9; w *= 0.8
                # sliding friction
                v.x *= (1 - 2.5 * h); v.y *= (1 - 2.5 * h); w *= (1 - 3 * h)
            t += h
        out[tq] = (p.copy(), rot.copy())
    return out


def frames_times(f0, f1):
    return {f: S.real_time(f) for f in range(f0, f1 + 1)}


# ------------------------------------------------------------------ detaching front wing
def animate_front_wing(P, f0, f1):
    body = P["body"]
    fw = P["front_wing"]
    piv_local = Vector((4.78, 0, 0.17))
    piv = empty("fw_pivot", piv_local, parent=body)
    fw.parent = piv
    fw.location = -piv_local
    FT = frames_times(f0, f1)
    Mi = car_M(T_I) @ Matrix.Translation(piv_local)
    p0 = Mi.to_translation()
    q0 = Mi.to_quaternion()
    v0 = Vector((3.0, -7.5, 5.5))
    w0 = Vector((4.0, 9.0, -6.0))
    traj = ballistic(p0, v0, w0, T_I, [t for t in FT.values() if t > T_I], ground=0.12, rest=0.35)
    for f, t in FT.items():
        if t <= T_I:
            piv.location = piv_local; piv.rotation_euler = (0, 0, 0)
        else:
            p, r = traj[t]
            q = Euler(r).to_quaternion() @ q0
            Mw = Matrix.LocRotScale(p, q, Vector((1, 1, 1)))
            Ml = car_M(t).inverted() @ Mw
            piv.location = Ml.to_translation()
            piv.rotation_euler = Ml.to_euler()
        piv.keyframe_insert("location", frame=f)
        piv.keyframe_insert("rotation_euler", frame=f)
    fix_euler_continuity(piv)
    return piv


def animate_broken_wheel(P, f0, f1, key="FR"):
    hub, spin = P["wheels"][key]
    rest = Vector(hub.location)
    for f, t in frames_times(f0, f1).items():
        u = smoothstep(T_I + 0.015, T_I + 0.09, t)
        hub.location = rest + Vector((-0.42, 0.10, 0.06)) * u
        e = hub.rotation_euler.copy()
        hub.rotation_euler = (math.radians(-24) * u, math.radians(10) * u, e.z + math.radians(-35) * u)
        hub.keyframe_insert("location", frame=f)
        hub.keyframe_insert("rotation_euler", frame=f)


# ------------------------------------------------------------------ carbon shards
def shard_mesh(M, rng, name):
    bm = bmesh.new()
    n = rng.choice((3, 4, 5))
    r = rng.uniform(0.03, 0.12)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        rr = r * rng.uniform(0.5, 1.3)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    top = [bm.verts.new((x, y, 0.003)) for x, y in pts]
    bot = [bm.verts.new((x, y, -0.003)) for x, y in pts]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[i], top[j], bot[j], bot[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mats = [M["carbon"], M["livery"], M["accent"], M["carbon"]]
    return obj_from_bm(name, bm, [rng.choice(mats)], smooth=False)


def animate_shards(P, f0, f1, n=48, seed=5):
    rng = random.Random(seed)
    M = P["M"]
    FT = frames_times(f0, f1)
    contact_local = [Vector((4.7, -0.1, 0.25)), Vector((4.2, -0.9, 0.3)), Vector((3.7, -0.9, 0.4)), Vector((4.5, 0.4, 0.2))]
    objs = []
    for i in range(n):
        o = shard_mesh(M, rng, f"shard{i}")
        ts = T_I + rng.uniform(0.0, 0.09)
        c = car_M(ts) @ rng.choice(contact_local)
        c += Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rng.uniform(0, 0.2)))
        sp = rng.uniform(3, 15)
        d = Vector((rng.uniform(-1.0, 0.2), rng.uniform(-1, 1), rng.uniform(0.2, 1.1))).normalized()
        v0 = d * sp
        w0 = Vector((rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(-20, 20)))
        traj = ballistic(c, v0, w0, ts, [t for t in FT.values() if t > ts], ground=0.01, rest=0.25)
        for f, t in FT.items():
            if t <= ts:
                o.location = (0, 0, -50); o.scale = (0.001, 0.001, 0.001); o.rotation_euler = (0, 0, 0)
            else:
                p, r = traj[t]
                o.location = p; o.rotation_euler = r; o.scale = (1, 1, 1)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)
            o.keyframe_insert("scale", frame=f)
        set_constant_scale(o)
        objs.append(o)
    return objs


def set_constant_scale(o):
    ad = o.animation_data
    if ad and ad.action:
        from .core import _fcurves
        for fc in _fcurves(ad.action):
            if fc.data_path == "scale":
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT'


# ------------------------------------------------------------------ sparks
def spark_events(seed=9):
    """List of (spawn_t, life, p0, v0)."""
    rng = random.Random(seed)
    ev = []
    t = S.T_SNAP + 0.25
    while t < T_I:
        st = S.car_state(t)
        Mc = car_matrix(st)
        vcar = Vector((math.cos(0) * st["v"], 0, 0))
        for k in range(2):
            pl = Vector((rng.uniform(0.6, 2.4), rng.uniform(-0.25, 0.25), 0.03))
            p0 = Mc @ pl
            v = Vector((st["v"] * rng.uniform(0.15, 0.45), rng.uniform(-4, 4), rng.uniform(0.3, 2.5)))
            ev.append((t, rng.uniform(0.08, 0.2), p0, v))
        t += 1 / 70
    for i in range(70):
        ts = T_I + rng.uniform(0, 0.08)
        Mc = car_M(ts)
        p0 = Mc @ Vector((rng.uniform(3.6, 4.8), rng.uniform(-0.9, 0.2), rng.uniform(0.05, 0.35)))
        d = Vector((rng.uniform(-1, 0.3), rng.uniform(-1, 1), rng.uniform(0.0, 1.0))).normalized()
        ev.append((ts, rng.uniform(0.25, 0.6), p0, d * rng.uniform(5, 18)))
    return ev


def animate_sparks(f0, f1, pool=150):
    em = emit_mat("spark", (1.0, 0.55, 0.12), 60.0)
    ev = sorted(spark_events(), key=lambda e: e[0])
    FT = frames_times(f0, f1)
    # assign events to pool slots greedily
    slots = [[] for _ in range(pool)]
    free_at = [-1.0] * pool
    for e in ev:
        for i in range(pool):
            if free_at[i] < e[0] - 0.02:
                slots[i].append(e); free_at[i] = e[0] + e[1]
                break
    objs = []
    for i in range(pool):
        if not slots[i]:
            continue
        bm = bmesh.new()
        tube_bm(bm, [(-0.5, 0, 0), (0.5, 0, 0)], 0.5, 5)
        o = obj_from_bm(f"spark{i}", bm, [em], smooth=True)
        for f, t in FT.items():
            alive = None
            for e in slots[i]:
                if e[0] <= t <= e[0] + e[1]:
                    alive = e; break
            if alive is None:
                o.location = (0, 0, -50); o.scale = (0.0001, 0.0001, 0.0001)
            else:
                ts, life, p0, v0 = alive
                dt = t - ts
                p = p0 + v0 * dt + 0.5 * G * dt * dt
                v = v0 + G * dt
                o.location = p
                o.rotation_euler = Vector((1, 0, 0)).rotation_difference(v.normalized()).to_euler()
                L = 0.03 + 0.012 * v.length * (0.3 if S.rate((f - 1) / 30) < 0.5 else 1.0)
                fade = 1 - dt / life
                o.scale = (L, 0.006 * fade + 0.002, 0.006 * fade + 0.002)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)
            o.keyframe_insert("scale", frame=f)
        objs.append(o)
    return objs


# ------------------------------------------------------------------ smoke / dust billboards
def smoke_mat(name, color, density=0.5):
    m = bpy.data.materials.new(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tc = nodes.new("ShaderNodeTexCoord")
    oi = nodes.new("ShaderNodeObjectInfo")
    lw = nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    inv = nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    links.new(lw.outputs["Facing"], inv.inputs[1])
    fsq = nodes.new("ShaderNodeMath"); fsq.operation = 'POWER'; fsq.inputs[1].default_value = 2.5
    links.new(inv.outputs[0], fsq.inputs[0])
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], nz.inputs[0])
    w = nodes.new("ShaderNodeMath"); w.operation = 'MULTIPLY'
    links.new(fsq.outputs[0], w.inputs[0]); links.new(nz.outputs[0], w.inputs[1])
    fade = nodes.new("ShaderNodeSeparateColor")
    links.new(oi.outputs["Color"], fade.inputs[0])
    w2 = nodes.new("ShaderNodeMath"); w2.operation = 'MULTIPLY'
    links.new(w.outputs[0], w2.inputs[0]); links.new(fade.outputs[0], w2.inputs[1])  # R channel of object colour = opacity
    w3 = nodes.new("ShaderNodeMath"); w3.operation = 'MULTIPLY'; w3.inputs[1].default_value = density * 2.2
    links.new(w2.outputs[0], w3.inputs[0])
    cl = nodes.new("ShaderNodeClamp"); links.new(w3.outputs[0], cl.inputs[0])
    tr = nodes.new("ShaderNodeBsdfTransparent")
    df = nodes.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (*color, 1)
    tl = nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs[0].default_value = (*color, 1)
    ad0 = nodes.new("ShaderNodeMixShader"); ad0.inputs[0].default_value = 0.35
    links.new(df.outputs[0], ad0.inputs[1]); links.new(tl.outputs[0], ad0.inputs[2])
    em = nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*color, 1); em.inputs[1].default_value = 0.6
    ad = nodes.new("ShaderNodeAddShader"); links.new(ad0.outputs[0], ad.inputs[0]); links.new(em.outputs[0], ad.inputs[1])
    mx = nodes.new("ShaderNodeMixShader")
    links.new(cl.outputs[0], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[1]); links.new(ad.outputs[0], mx.inputs[2])
    links.new(mx.outputs[0], out.inputs[0])
    return m


def billboard_target(f0, f1, cam_for_frame):
    tg = empty("bb_target", size=0.1)
    for f in range(f0, f1 + 1):
        tg.location = cam_for_frame(f).matrix_world.to_translation() if False else cam_for_frame(f).location
        tg.keyframe_insert("location", frame=f)
    return tg


def make_puff(name, m, target=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    o = obj_from_bm(name, bm, [m], smooth=True)
    return o


def puff_events(seed=13):
    rng = random.Random(seed)
    ev = []
    # lock-up / sliding tyre smoke from the four contact patches
    t = S.T_SNAP - 0.05
    wheels = [(C.WHEELBASE, C.FRONT_Y), (C.WHEELBASE, -C.FRONT_Y), (0.0, C.REAR_Y), (0.0, -C.REAR_Y)]
    while t < T_I + 0.05:
        Mc = car_M(t)
        st = S.car_state(t)
        for (wx, wy) in wheels:
            if rng.random() < 0.75:
                p = Mc @ Vector((wx, wy, 0.25))
                v = Vector((st["v"] * 0.10, rng.uniform(-1, 1), rng.uniform(0.3, 0.8)))
                ev.append(dict(t=t, life=rng.uniform(1.0, 1.5), p=p, v=v, s0=0.5, s1=rng.uniform(2.2, 3.2), a=0.32, kind="smoke"))
        t += 0.11
    # impact dust: rubber/carbon dust + TecPro debris cloud
    for i in range(16):
        ts = T_I + rng.uniform(0.0, 0.25)
        Mc = car_M(ts)
        p = Mc @ Vector((rng.uniform(3.0, 4.9), rng.uniform(-1.2, 0.8), rng.uniform(0.2, 0.9)))
        v = Vector((rng.uniform(-3, 0.5), rng.uniform(-3.5, 3.5), rng.uniform(0.3, 2.5)))
        ev.append(dict(t=ts, life=rng.uniform(2.5, 4.0), p=p, v=v, s0=0.8, s1=rng.uniform(2.5, 4.0), a=0.22, kind="dust"))
    return ev


def animate_puffs(f0, f1, target):
    sm = smoke_mat("tyre_smoke", (0.85, 0.85, 0.86), 0.35)
    dm = smoke_mat("impact_dust", (0.78, 0.74, 0.68), 0.28)
    FT = frames_times(f0, f1)
    objs = []
    for i, e in enumerate(puff_events()):
        o = make_puff(f"puff{i}", sm if e["kind"] == "smoke" else dm, target)
        o.rotation_mode = 'XYZ'
        for f, t in FT.items():
            dt = t - e["t"]
            if dt < 0 or dt > e["life"]:
                o.location = (0, 0, -60); o.scale = (0.001,) * 3; o.color = (0, 0, 0, 1)
            else:
                u = dt / e["life"]
                drag = (1 - math.exp(-dt * 2.0)) / 2.0
                o.location = e["p"] + e["v"] * drag + Vector((0.6, 0.2, 0.25)) * dt
                s = e["s0"] + (e["s1"] - e["s0"]) * (1 - (1 - u) ** 2)
                o.scale = (s, s, s)
                op = e["a"] * min(1, dt / 0.08) * (1 - u) ** 1.5
                o.color = (op, op, op, 1)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("scale", frame=f)
            o.keyframe_insert("color", frame=f)
        objs.append(o)
    return objs


# ------------------------------------------------------------------ TecPro barrier response
def animate_barrier(blocks, f0, f1, seed=21):
    rng = random.Random(seed)
    BX = S.BARRIER_X
    wall = BX + 4.0
    # sample points on the car outline (car-local, x, y)
    outline = [(4.72, 0.0), (4.6, -0.12), (4.6, 0.12), (4.2, -0.2), (4.2, 0.2)]
    for x in [3.9, 3.6, 3.3]:
        outline += [(x, -0.98), (x, 0.98)]
    for x in [2.6, 2.0, 1.4, 0.8, 0.3, -0.2, -0.6]:
        outline += [(x, -0.9 if x > 0.6 else -0.98)]
    FT = frames_times(f0, f1)
    blocks_by_row = {0: [], 1: [], 2: []}
    for b in blocks:
        blocks_by_row[b["row"]].append(b)
    jitter = {b.name: (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 1)) for b in blocks}
    for f, t in FT.items():
        Mc = car_M(t)
        pts = [Mc @ Vector((x, y, 0.4)) for (x, y) in outline]
        front_after = {}
        for row in (0, 1, 2):
            for b in blocks_by_row[row]:
                c = Vector(b["rest"])
                y0, y1 = c.y - 0.74, c.y + 0.74
                rest_front = c.x - 0.29
                push_front = rest_front
                for p in pts:
                    if y0 - 0.15 < p.y < y1 + 0.15:
                        push_front = max(push_front, p.x)
                # pushed by blocks in the previous row overlapping in y
                for (pb_y0, pb_y1, back) in front_after.get(row - 1, []):
                    if pb_y1 > y0 and pb_y0 < y1:
                        push_front = max(push_front, back)
                dx = push_front - rest_front
                thick = 0.58 * (1 - min(0.5, dx * 0.35))
                back = push_front + thick
                limit = wall - 0.2 - (2 - row) * 0.25
                if back > limit:
                    thick = max(0.2, thick - (back - limit))
                    back = push_front + thick
                front_after.setdefault(row, []).append((y0, y1, back))
                jx, jy, jz = jitter[b.name]
                k = min(1.0, dx / 0.8)
                b.location = (push_front + thick / 2, c.y + jy * 0.25 * k, 0.5 + jz * 0.12 * k)
                b.scale = (thick / 0.58, 1 + 0.12 * k, 1 - 0.05 * k)
                b.rotation_euler = (jx * 0.12 * k, jy * 0.08 * k, jx * 0.25 * k)
                b.keyframe_insert("location", frame=f)
                b.keyframe_insert("scale", frame=f)
                b.keyframe_insert("rotation_euler", frame=f)


# ------------------------------------------------------------------ skid marks (progressive reveal)
def build_skidmarks(f0, f1):
    m = bpy.data.materials.new("skid")
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    uv = nodes.new("ShaderNodeUVMap")
    sep = nodes.new("ShaderNodeSeparateXYZ"); links.new(uv.outputs[0], sep.inputs[0])
    val = nodes.new("ShaderNodeValue"); val.name = "Now"
    lt = nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'
    links.new(sep.outputs[0], lt.inputs[0]); links.new(val.outputs[0], lt.inputs[1])
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4
    tc = nodes.new("ShaderNodeTexCoord"); links.new(tc.outputs["Object"], nz.inputs[0])
    edge = nodes.new("ShaderNodeMath"); edge.operation = 'PINGPONG'; edge.inputs[1].default_value = 0.5
    links.new(sep.outputs[1], edge.inputs[0])
    edge2 = nodes.new("ShaderNodeMapRange"); edge2.inputs[1].default_value = 0.0; edge2.inputs[2].default_value = 0.25
    links.new(edge.outputs[0], edge2.inputs[0])
    a1 = nodes.new("ShaderNodeMath"); a1.operation = 'MULTIPLY'; links.new(lt.outputs[0], a1.inputs[0]); links.new(nz.outputs[0], a1.inputs[1])
    a2 = nodes.new("ShaderNodeMath"); a2.operation = 'MULTIPLY'; links.new(a1.outputs[0], a2.inputs[0]); links.new(edge2.outputs[0], a2.inputs[1])
    a3 = nodes.new("ShaderNodeMath"); a3.operation = 'MULTIPLY'; a3.inputs[1].default_value = 1.4
    links.new(a2.outputs[0], a3.inputs[0])
    cl = nodes.new("ShaderNodeClamp"); links.new(a3.outputs[0], cl.inputs[0])
    tr = nodes.new("ShaderNodeBsdfTransparent")
    bs = nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Base Color"].default_value = (0.006, 0.006, 0.006, 1); bs.inputs["Roughness"].default_value = 0.6
    mx = nodes.new("ShaderNodeMixShader")
    links.new(cl.outputs[0], mx.inputs[0]); links.new(tr.outputs[0], mx.inputs[1]); links.new(bs.outputs[0], mx.inputs[2])
    links.new(mx.outputs[0], out.inputs[0])
    wheels = [(C.WHEELBASE, C.FRONT_Y, 0.3), (C.WHEELBASE, -C.FRONT_Y, 0.3), (0.0, C.REAR_Y, 0.4), (0.0, -C.REAR_Y, 0.4)]
    for k, (wx, wy, wd) in enumerate(wheels):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new()
        rows = []
        t = S.T_SNAP - 0.1
        while t < T_I + 0.12:
            Mc = car_M(t)
            p = Mc @ Vector((wx, wy, 0))
            a = Mc @ Vector((wx, wy - wd / 2, 0)); b = Mc @ Vector((wx, wy + wd / 2, 0))
            rows.append((bm.verts.new((a.x, a.y, 0.006)), bm.verts.new((b.x, b.y, 0.006)), t))
            t += 0.01
        for r0, r1 in zip(rows[:-1], rows[1:]):
            f = bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
            for loop, uvv in zip(f.loops, ((r0[2], 0), (r0[2], 1), (r1[2], 1), (r1[2], 0))):
                loop[uvl].uv = uvv
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj_from_bm(f"skid{k}", bm, [m], smooth=False)
    for f, t in frames_times(f0, f1).items():
        val.outputs[0].default_value = t - 0.02
        val.outputs[0].keyframe_insert("default_value", frame=f)
    return m


def animate_driver_head(D, f0, f1, amp=math.radians(26)):
    """Head/neck flexion at the impact (restrained by HANS: modest amplitude)."""
    arm = D["arm"]
    for f, t in frames_times(f0, f1).items():
        dt = t - T_I
        a = 0.0
        if dt > 0:
            a = amp * math.sin(min(math.pi, dt / 0.16 * math.pi)) * math.exp(-max(0, dt - 0.16) * 3)
            if dt > 0.16:
                a = -amp * 0.25 * math.sin((dt - 0.16) / 0.25 * math.pi) * math.exp(-(dt - 0.16) * 4)
        for bn, k in (("neck1", 0.35), ("neck2", 0.35), ("head", 0.3)):
            from .anatomy import pose_pitch
            pose_pitch(arm, bn, a * k, f)
        from .anatomy import pose_offset
        pose_offset(arm, "spine", (0.03 * (a / amp if amp else 0), 0, 0), f)
