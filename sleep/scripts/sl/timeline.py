"""Global frame map (30 fps, 1-based). Narration lines: hook 1.90-6.32 s | hook2 6.72-9.03 | 24h 9.63-16.51 | 48h 17.06-24.06 | 72h 24.61-30.55 | 7d 31.10-39.06 | end 39.86-44.07"""
T = dict(hook_over=(1, 60), hook_pov=(61, 120), hook_eyes=(121, 190), brain0=(191, 290), brain24=(291, 380), glass=(381, 502),
         d48a=(503, 620), d48b=(621, 690), brain48=(691, 732), d72a=(733, 850), d72b=(851, 880), brain72=(881, 930), d7=(931, 1186), end=(1187, 1340))
NF = 1340
APT_RANGES = [T["hook_over"][0], T["hook_eyes"][1]], [T["glass"][0], T["d48b"][1]], [T["d72a"][0], T["d72b"][1]], [T["d7"][0], T["end"][1]]
BRAIN_RANGES = [(191, 380), (691, 732), (881, 930)]
def in_apt(f): return any(a <= f <= b for a, b in APT_RANGES)
