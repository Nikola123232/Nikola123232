"""Outdoor world shared by scenes 1, 2, 6: track + car + driver + lighting, plus per-frame car animation."""
import bpy, math, random
from mathutils import Vector, Matrix, Euler, Quaternion
from .core import *
from . import car as C, track as T, story as S, anatomy as A, gear as G

FONT = ROOT + "/assets/fonts/Anton-Regular.ttf"
SUN_AZ, SUN_EL = -60.0, 21.0


def build_world(detail=True, driver=True):
    sc = bpy.context.scene
    world_sky(SUN_EL, 200, strength=0.2)
    d = Vector((math.cos(math.radians(SUN_AZ)), math.sin(math.radians(SUN_AZ)), math.tan(math.radians(SUN_EL)))) * 50
    sun = light("sun", 'SUN', energy=3.4, angle=0.8, color=(1.0, 0.93, 0.82))
    sun.rotation_euler = look_at_rot(d, (0, 0, 0))
    trk, blocks = T.build_track(detail)
    P = C.build_car(font=FONT)
    W = {"sun": sun, "blocks": blocks, "P": P}
    if driver:
        D = A.build_driver(anatomy=False)
        Gr = G.build_gear(D)
        D["root"].parent = P["body"]
        D["root"].location, D["root"].rotation_euler = A.BODY_IN_CAR
        W["D"], W["G"] = D, Gr
    return W


def car_matrix(st):
    return Matrix.LocRotScale(Vector((st["x"], st["y"], st["z"])),
                              Euler((st["roll"], st["pitch"], st["yaw"]), 'XYZ').to_quaternion(), Vector((1, 1, 1)))


def animate_car(P, f0, f1, wheel_lock=True):
    """Per-frame keys for the car root, wheel spin and steering, for global frames f0..f1."""
    root = P["root"]
    dist_rear = 0.0
    dist_front = 0.0
    prev = None
    for f in range(f0, f1 + 1):
        t = S.real_time(f)
        st = S.car_state(t)
        root.location = (st["x"], st["y"], st["z"])
        root.rotation_euler = (st["roll"], st["pitch"], st["yaw"])
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        # wheel rolling distance (fronts lock under the slide, rears spin down)
        if prev is None:
            dist_rear = dist_front = S.V0 * t
        else:
            ds = math.hypot(st["x"] - prev["x"], st["y"] - prev["y"])
            front_k = 1.0 if (t < S.T_SNAP - 0.15 or not wheel_lock) else max(0.0, 1.0 - (t - S.T_SNAP + 0.15) * 6)
            rear_k = 1.0 if t < S.T_SNAP else 0.55
            if t > S.T_IMP_TARGET:
                front_k = 0.0; rear_k = 0.3 * math.exp(-(t - S.T_IMP_TARGET) * 3)
            dist_front += ds * front_k
            dist_rear += ds * rear_k
        prev = st
        for key, (hub, spin) in P["wheels"].items():
            d = dist_front if key[0] == "F" else dist_rear
            spin.rotation_euler = (0, d / C.R_WHEEL, 0)
            spin.keyframe_insert("rotation_euler", frame=f)
        # counter-steer after the snap
        steer = 0.0
        if t > S.T_SNAP:
            steer = -math.radians(18) * min(1.0, (t - S.T_SNAP) * 4) * (1 if t < S.T_IMP_TARGET else 0.6)
        for key in ("FL", "FR"):
            hub = P["wheels"][key][0]
            hub.rotation_euler = (0, 0, steer)
            hub.keyframe_insert("rotation_euler", frame=f)


def key_camera_follow(cam, f, car_st, offset, look, lens=None, world_axes=False, shake=0.0, roll=0.0):
    """offset/look are expressed in car-heading frame (unless world_axes)."""
    if world_axes:
        R = Matrix.Identity(3)
    else:
        R = Euler((0, 0, car_st["yaw"])).to_matrix()
    base = Vector((car_st["x"], car_st["y"], 0))
    loc = base + R @ Vector(offset)
    tgt = base + R @ Vector(look)
    if shake:
        loc += Vector((noise.noise(Vector((f * 0.37, 0.1, 0))), noise.noise(Vector((0, f * 0.41, 0.3))),
                       noise.noise(Vector((0.5, 0, f * 0.33))))) * shake
    key_cam(cam, f, loc, tgt, lens, roll)


def shot_camera(name, f_start, lens=35):
    """One camera per shot, bound to a timeline marker (prevents motion-blur smear across cuts)."""
    sc = bpy.context.scene
    cam = camera(name, lens)
    mk = sc.timeline_markers.new(name, frame=f_start)
    mk.camera = cam
    if sc.camera is None:
        sc.camera = cam
    return cam


def active_camera(f):
    sc = bpy.context.scene
    best = None
    for m in sc.timeline_markers:
        if m.camera and m.frame <= f and (best is None or m.frame > best.frame):
            best = m
    return best.camera if best else sc.camera


def setup_render(sc, f0, f1, outdir, samples=12, motion_blur=True, res=(720, 1280)):
    render_settings(sc, res, samples=samples, motion_blur=motion_blur, shutter=0.5)
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = f"{ROOT}/renders/{outdir}/####"


def run_render(sc, argv):
    """--preview STEP renders every STEP-th frame at 50% to previews/; --range a b limits frames."""
    import os
    if "--frames" in argv:
        fl = [int(x) for x in argv[argv.index("--frames") + 1].split(",")]
        sc.render.resolution_percentage = int(os.environ.get("PCT", 50))
        base = sc.render.filepath.replace("/renders/", "/previews/")
        os.makedirs(os.path.dirname(base), exist_ok=True)
        for f in fl:
            sc.frame_set(f)
            sc.render.filepath = base.replace("####", f"{f:04d}")
            bpy.ops.render.render(write_still=True)
        return
    if "--preview" in argv:
        step = int(argv[argv.index("--preview") + 1])
        sc.render.resolution_percentage = int(os.environ.get("PCT", 50))
        base = sc.render.filepath.replace("/renders/", "/previews/")
        os.makedirs(os.path.dirname(base), exist_ok=True)
        for f in range(sc.frame_start, sc.frame_end + 1, step):
            sc.frame_set(f)
            sc.render.filepath = base.replace("####", f"{f:04d}")
            bpy.ops.render.render(write_still=True)
        return
    if "--range" in argv:
        i = argv.index("--range")
        sc.frame_start, sc.frame_end = int(argv[i + 1]), int(argv[i + 2])
    if "--frames" in argv:  # explicit list for debugging
        pass
    sc.render.use_overwrite = False  # resume-safe
    sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)
