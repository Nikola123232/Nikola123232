"""Biker edit: remove TikTok marks, hook caption, the fall, then a zoomed slow-motion replay with 'What happened?'."""
import sys, subprocess, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/user/Nikola123232/age"); sys.path.insert(0, "/home/user/Nikola123232/shorts/sr")
from inpaint import diffuse
from srnet import SR
SRC = glob.glob("/root/.claude/uploads/164b86a1-ee5f-5ccd-bad4-ded5aa95eb0d/62cb5c6c*.mp4")[0]
OUT = "/home/user/Nikola123232/bike/biker_short.mp4"; TMP = "/tmp/claude-0/-home-user-Nikola123232/164b86a1-ee5f-5ccd-bad4-ded5aa95eb0d/scratchpad/bike/"
import os; os.makedirs(TMP, exist_ok=True)
W, H, SW, SH, FPS = 1080, 1920, 576, 1024, 30
T0, T1 = 5.2, 10.6                  # normal-speed part (source seconds)
R0, R1, SLOW = 8.7, 10.5, 0.4       # replay window and speed
CROP = (165, 300, 435, 780)         # 270x480 region around the crossing (x0,y0,x1,y1)
MONT = "/home/user/Nikola123232/assets/fonts/Montserrat-Var.ttf"
def font(s):
    f = ImageFont.truetype(MONT, s); f.set_variation_by_name("ExtraBold"); return f
def ease_back(t, s=1.6): t = max(0.0, min(1.0, t)); t -= 1; return 1 + (s + 1) * t ** 3 + s * t ** 2
def clean(arr):                     # remove the TikTok logo + @name (bottom-right): inpaint only the logo's own bright/colored pixels
    from scipy.ndimage import binary_dilation
    x0, y0, x1, y1 = 380, 708, 574, 792; pad = 6
    X0, Y0, X1, Y1 = x0 - pad, y0 - pad, min(SW, x1 + pad), min(SH, y1 + pad); sub = arr[Y0:Y1, X0:X1].astype(np.float32)
    lum = sub @ np.array([0.3, 0.59, 0.11], np.float32); mx = sub.max(2) - sub.min(2)
    m = (lum > 105) | ((mx > 70) & (lum > 60))
    box = np.zeros(m.shape, bool); box[pad:pad + (y1 - y0), pad:pad + (x1 - x0)] = True; m &= box
    m = binary_dilation(m, iterations=3) & box
    if not m.any(): return arr
    out = arr.copy(); out[Y0:Y1, X0:X1] = np.clip(diffuse(sub, m, iters=120), 0, 255).astype(np.uint8); return out
def read_frames(ss, t, vf, w, h, rate=FPS):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(t), "-i", SRC, "-vf", vf, "-r", str(rate), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8); n = len(a) // (w * h * 3); return a[:n * w * h * 3].reshape(n, h, w, 3)
def caption(im, lines, t, y, size=84, tag=None):
    a = ease_back(t / 0.18); lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = font(size); yy = 40
    for ln in lines:
        d.text(((W - f.getlength(ln)) / 2 + 3, yy + 5), ln, font=f, fill=(0, 0, 0, 150)); d.text(((W - f.getlength(ln)) / 2, yy), ln, font=f, fill=(255, 255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 255)); yy += int(size * 1.15)
    sc = 0.8 + 0.2 * a; lay = lay.resize((int(W * sc), int(300 * sc)), Image.LANCZOS); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * min(1, t / 0.08 + 0.2))))
    im.alpha_composite(lay, ((W - lay.size[0]) // 2, y - lay.size[1] // 2)); return im
# ---------------------------------------------------------------- part 1 (normal speed)
f1 = read_frames(T0, T1 - T0, "fps=30", SW, SH); n1 = len(f1)
# ---------------------------------------------------------------- part 2 (zoomed slow-motion replay): clean -> crop -> motion-interpolated slow-mo -> x4 super-resolution
src2 = read_frames(R0, R1 - R0, "fps=25", SW, SH, rate=25)
cx0, cy0, cx1, cy1 = CROP; cw, chh = cx1 - cx0, cy1 - cy0
enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{chh}", "-r", "25", "-i", "-", "-c:v", "libx264", "-crf", "8", "-pix_fmt", "yuv420p", TMP + "crop.mp4"], stdin=subprocess.PIPE)
for fr in src2: enc.stdin.write(clean(fr)[cy0:cy1, cx0:cx1].tobytes())
enc.stdin.close(); enc.wait()
p = subprocess.run(["ffmpeg", "-v", "error", "-i", TMP + "crop.mp4", "-vf", f"setpts={1 / SLOW}*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
a = np.frombuffer(p.stdout, np.uint8); n2 = len(a) // (cw * chh * 3); f2 = a[:n2 * cw * chh * 3].reshape(n2, chh, cw, 3)
print("part1", n1, "part2", n2, flush=True)
# ---------------------------------------------------------------- audio: normal part + slowed replay part
afil = f"[0:a]atrim={T0}:{T1},asetpts=PTS-STARTPTS[a1];[0:a]atrim={R0}:{R1},asetpts=PTS-STARTPTS,atempo=0.5,atempo=0.8,lowpass=f=5000[a2];[a1][a2]concat=n=2:v=0:a=1,afade=t=out:st={(n1 + n2) / FPS - 0.4:.2f}:d=0.4,loudnorm=I=-14:TP=-1.5:LRA=11[o]"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-filter_complex", afil, "-map", "[o]", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", TMP + "audio.m4a"], check=True)
# ---------------------------------------------------------------- compose
enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", TMP + "audio.m4a", "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
sr = SR(); FALL_START = 8.8 - T0          # caption "Look what this biker does..." until the fall begins
for i in range(n1):
    t = i / FPS; im = Image.fromarray(clean(f1[i])).resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2)).convert("RGBA")
    if t < FALL_START: im = caption(im, ["Look what this", "biker does..."], t, 360)
    enc.stdin.write(np.asarray(im.convert("RGB")).tobytes())
for j in range(n2):
    y = sr(f2[j]); im = Image.fromarray(y).resize((W, H), Image.LANCZOS).convert("RGBA") if y.shape[:2] != (H, W) else Image.fromarray(y).convert("RGBA")
    t = j / FPS
    if j < 4: im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.55 * (1 - j / 4)).convert("RGBA")      # quick flash into the replay
    im = caption(im, ["What happened?"], t, 330)
    d = ImageDraw.Draw(im); f = font(30); d.text((70, 150), "SLOW MOTION", font=f, fill=(255, 255, 255, 235), stroke_width=3, stroke_fill=(0, 0, 0, 220))
    enc.stdin.write(np.asarray(im.convert("RGB")).tobytes())
enc.stdin.close(); enc.wait(); print("wrote", OUT, n1 + n2, "frames")
