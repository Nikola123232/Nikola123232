import sys, os, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *
V = ROOT + "/sleep"
def shot_camera(name, f_start, lens=35):
    sc = bpy.context.scene; cam = camera(name, lens, clip_end=200)
    mk = sc.timeline_markers.new(name, frame=f_start); mk.camera = cam
    if sc.camera is None: sc.camera = cam
    return cam
def active_camera(f):
    sc = bpy.context.scene; best = None
    for m in sc.timeline_markers:
        if m.camera and m.frame <= f and (best is None or m.frame > best.frame): best = m
    return best.camera if best else sc.camera
def dof(cam, obj=None, dist=None, fstop=2.8):
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    if obj is not None: cam.data.dof.focus_object = obj
    if dist is not None: cam.data.dof.focus_distance = dist
def setup(sc, outdir, samples=16, bounces=8, res=(720, 1280), motion_blur=False):
    render_settings(sc, res, samples=samples, motion_blur=motion_blur, shutter=0.4, transparent_bounces=8, max_bounces=bounces)
    sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
    except Exception as e: print("vt", e)
    sc.render.filepath = f"{V}/renders/{outdir}/####"
def parse_frames(arg):
    out = []
    for part in arg.split(","):
        if "-" in part: a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out
def run_render(sc, argv, frames_all, outdir):
    """--frames a-b,c : preview at PCT %; --render [a-b,...] : full quality, skips existing; --save : write .blend"""
    if "--save" in argv:
        os.makedirs(f"{V}/blend", exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=f"{V}/blend/{outdir}.blend", compress=True); print("SAVED", outdir); return
    if "--frames" in argv:
        fl = parse_frames(argv[argv.index("--frames") + 1]); sc.render.resolution_percentage = int(os.environ.get("PCT", 50))
        base = f"{V}/previews/{outdir}/####"; os.makedirs(os.path.dirname(base), exist_ok=True)
        for f in fl:
            sc.frame_set(f); sc.render.filepath = base.replace("####", f"{f:04d}"); bpy.ops.render.render(write_still=True)
        return
    fl = parse_frames(argv[argv.index("--render") + 1]) if ("--render" in argv and len(argv) > argv.index("--render") + 1) else frames_all
    os.makedirs(f"{V}/renders/{outdir}", exist_ok=True)
    for f in fl:
        p = f"{V}/renders/{outdir}/{f:04d}.png"
        if os.path.exists(p) and os.path.getsize(p) > 0: continue
        sc.frame_set(f); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
