"""SCENE 8 (frames 1681-1800, 0:56-1:00): POWERFUL ENDING. The camera pulls rapidly away from the lava lake to a wide shot of the
glowing crater and its smoke. The compositor fades to black at the end."""
import sys, math, json
sys.path.insert(0, "/home/user/Nikola123232/volcano/scripts")
from vol.human import *
from vol import world as W, util as U

F0, F1 = 1681, 1800
E0, E1 = F0 - 2, F1 + 2
sc = reset_scene()
E = W.build_environment((F0, F1)); E["glowL"].rotation_euler = (math.pi, 0, 0)
H = build_human(anatomy=False); root = H["root"]
set_reveal(H, None, 1.0)
for m in H["M"]["rev"]:
    for e in [n for n in m.node_tree.nodes if n.type == 'EMISSION']:
        e.inputs[0].default_value = (0.9, 0.12, 0.02, 1); e.inputs[1].default_value = 1.0
pose(H, stand_spec()); root.location = (0, 0, -0.04); root.rotation_euler = (0, 1.5708, 0.6)
for o in H["head"] + [H["skin"]]: o.visible_shadow = False
light("body_glow", 'AREA', (0, 0, 5), (math.pi, 0, 0), energy=250, size=6, color=(1.0, 0.42, 0.1))
W.embers(E0, E1, n=170, rmax=105, zmax=150, speed=(2.0, 7.0), size=0.5, time_scale=lambda f: (f - F0) / 30.0 * 0.8)
W.smoke_puffs(E0, E1, n=60, rmin=30, rmax=260, zmin=15, zmax=260, size=(50, 130), opacity=(0.06, 0.16), rise=3.0, seed=41)
W.smoke_puffs(E0, E1, n=20, rmin=40, rmax=120, zmin=5, zmax=30, size=(25, 50), opacity=(0.06, 0.12), rise=1.5, seed=43)
cam = U.shot_camera("cam8", F0, 30)
for f in range(E0, E1 + 1):
    u = min(1.0, max(0.0, (f - F0) / (F1 - F0)))
    e = u ** 1.8 * (3 - 2 * u) * 0.0 + (u * u * (3 - 2 * u)) ** 1.35
    loc = Vector((0, -28, 4.5)).lerp(Vector((0, -230, 380)), e)
    tgt = Vector((0, 0, 14)).lerp(Vector((0, 0, 0)), e)
    key_cam(cam, f, loc, tgt, 28 - 4 * e)
U.setup(sc, F0, F1, "v8", samples=12, motion_blur=True, bounces=20)
sc.render.motion_blur_shutter = 0.4
U.run_render(sc, sys.argv)
