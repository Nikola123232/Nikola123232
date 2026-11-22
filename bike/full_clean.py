"""Whole clip without the TikTok logo/@name (top-left early, bottom-right later) and without the TikTok end card. usage: full_clean.py [--test t1,t2]"""
import sys, glob, subprocess, numpy as np
from scipy.ndimage import binary_dilation
sys.path.insert(0, "/home/user/Nikola123232/age")
from inpaint import diffuse
from PIL import Image, ImageFilter
SRC = glob.glob("/root/.claude/uploads/164b86a1-ee5f-5ccd-bad4-ded5aa95eb0d/62cb5c6c*.mp4")[0]
OUT = "/home/user/Nikola123232/bike/biker_full.mp4"; END = 14.45; SW, SH = 576, 1024
BOXES = [(8, 468, 215, 560), (372, 700, 576, 800)]       # top-left logo + name, bottom-right logo + name
def logo_mask(sub):
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]; mn = sub.min(2); mx = sub.max(2)
    white = (mn > 215) & ((mx - mn) < 40)
    cyan = (r < 90) & (g > 170) & (b > 170); red = (r > 200) & (g < 100) & (b > 70)
    return white | cyan | red
def clean(a):
    out = a.copy()
    for (x0, y0, x1, y1) in BOXES:
        sub = a[y0:y1, x0:x1].astype(np.float32); m = logo_mask(sub)
        if m.sum() < 120: continue                                      # logo not in this box
        m = binary_dilation(m, iterations=3)
        out[y0:y1, x0:x1] = np.clip(diffuse(sub, m, iters=100), 0, 255).astype(np.uint8)
    return out
def frames(ss, t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(t), "-i", SRC, "-vf", "scale=576:1024,fps=25", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8); n = len(a) // (SW * SH * 3); return a[:n * SW * SH * 3].reshape(n, SH, SW, 3)
if "--test" in sys.argv:
    ts = [float(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]; ims = []
    for t in ts:
        f = frames(t, 0.04)[0]; ims.append(np.concatenate([f[380:640, 0:300], clean(f)[380:640, 0:300]], 1))
    Image.fromarray(np.concatenate(ims, 0)).save("/home/user/Nikola123232/bike/qa/full_test.png"); sys.exit()
enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "25", "-i", "-", "-ss", "0", "-t", str(END), "-i", SRC, "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(END), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
n = 0
for f in frames(0, END):
    im = Image.fromarray(clean(f)).resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2)); enc.stdin.write(im.tobytes()); n += 1
enc.stdin.close(); enc.wait(); print("wrote", OUT, n, "frames")
