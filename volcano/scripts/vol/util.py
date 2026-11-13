import sys, os, math
sys.path.insert(0, "/home/user/Nikola123232/scripts")
import bpy
from f1.core import *

V = ROOT + "/volcano"

def shot_camera(name, f_start, lens=35):
    sc = bpy.context.scene
    cam = camera(name, lens, clip_end=6000)
    mk = sc.timeline_markers.new(name, frame=f_start); mk.camera = cam
    if sc.camera is None: sc.camera = cam
    return cam

def active_camera(f):
    sc = bpy.context.scene; best = None
    for m in sc.timeline_markers:
        if m.camera and m.frame <= f and (best is None or m.frame > best.frame): best = m
    return best.camera if best else sc.camera

def dof(cam, focus_obj=None, dist=None, fstop=2.8):
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    if focus_obj is not None: cam.data.dof.focus_object = focus_obj
    if dist is not None: cam.data.dof.focus_distance = dist

def setup(sc, f0, f1, outdir, samples=12, motion_blur=False, bounces=16, res=(720, 1280)):
    render_settings(sc, res, samples=samples, motion_blur=motion_blur, shutter=0.5, transparent_bounces=bounces)
    try:
        sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = float(os.environ.get('EXPO', -0.3))
    except Exception as e:
        print('vt', e)
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = f"{V}/renders/{outdir}/####"

def run_render(sc, argv):
    if "--save" in argv:               # write the Blender project (no render)
        name = os.path.basename(os.path.dirname(sc.render.filepath))
        os.makedirs(f"{V}/blend", exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=f"{V}/blend/{name}.blend", compress=True)
        print("SAVED", name); return
    pct = int(os.environ.get("PCT", 50))
    if "--frames" in argv or "--preview" in argv:
        fl = ([int(x) for x in argv[argv.index("--frames") + 1].split(",")] if "--frames" in argv
              else list(range(sc.frame_start, sc.frame_end + 1, int(argv[argv.index("--preview") + 1]))))
        sc.render.resolution_percentage = pct
        base = sc.render.filepath.replace("/renders/", "/previews/"); os.makedirs(os.path.dirname(base), exist_ok=True)
        for f in fl:
            sc.frame_set(f); sc.render.filepath = base.replace("####", f"{f:04d}")
            bpy.ops.render.render(write_still=True)
        return
    sc.render.use_overwrite = False; sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)

def key_linear(o):
    ad = o.animation_data
    if ad and ad.action:
        from f1.core import _fcurves
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
