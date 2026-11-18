"""Split-screen short: facecam on top, gameplay below, big animated captions between. usage: make_short.py cfg.json"""
import sys, json, subprocess, math
import numpy as np
sys.path.insert(0, '/home/user/Nikola123232/age')
from inpaint import diffuse
sys.path.insert(0, '/home/user/Nikola123232/shorts/sr')
from srnet import SR
from PIL import Image, ImageDraw, ImageFont, ImageFilter
cfg = json.load(open(sys.argv[1])); SW, SH = cfg["src_w"], cfg["src_h"]; W, H = 1080, 1920; FPS = 30
MONT = "/home/user/Nikola123232/assets/fonts/Montserrat-Var.ttf"
_f = {}
def font(size, var="ExtraBold"):
    k = (size, var)
    if k not in _f:
        f = ImageFont.truetype(MONT, size)
        try: f.set_variation_by_name(var)
        except Exception: f.set_variation_by_name("Bold")
        _f[k] = f
    return _f[k]
def ease_back(t, s=1.5): t = max(0.0, min(1.0, t)); t -= 1; return 1 + (s + 1) * t ** 3 + s * t ** 2
def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
cam = cfg["cam"]; game = cfg["game"]; cw, chh = cam[2] - cam[0], cam[3] - cam[1]; gw, gh = game[2] - game[0], game[3] - game[1]
CAM_H = int(round(W * chh / cw)); GAME_H = int(round(W * gh / gw)); CAM_Y = cfg.get("cam_y", 130); CAP_Y = CAM_Y + CAM_H + 70; GAME_Y = CAP_Y + 85
dur = cfg["duration"]; caps = cfg["captions"]; START = cfg.get("start", 0.0)      # [[start, end, text, [highlight words]]]
def draw_caption(canvas, t):
    for (s, e, text, hl) in caps:
        if s <= t < e:
            a = ease_back((t - s) / 0.16); fade = min(1.0, (e - t) / 0.08, (t - s) / 0.06 + 0.2); fnt = font(64)
            words = text.split(); lines = [text]
            if fnt.getlength(text) > W - 110:
                best = None
                for i in range(1, len(words)):
                    l1, l2 = " ".join(words[:i]), " ".join(words[i:]); sc = max(fnt.getlength(l1), fnt.getlength(l2))
                    if best is None or sc < best[0]: best = (sc, [l1, l2])
                lines = best[1]
            lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); y = 38 if len(lines) == 1 else 12
            for ln in lines:
                x = (W - fnt.getlength(ln)) / 2
                for w_ in ln.split(" "):
                    col = (255, 214, 10, 255) if any(tok in w_.lower().strip(".,?!…'") for h in hl for tok in h.lower().split()) else (255, 255, 255, 255)
                    d.text((x + 3, y + 4), w_, font=fnt, fill=(0, 0, 0, 150)); d.text((x, y), w_, font=fnt, fill=col, stroke_width=6, stroke_fill=(0, 0, 0, 255))
                    x += fnt.getlength(w_ + " ")
                y += 80
            sc = 0.82 + 0.18 * a; lay = lay.resize((int(W * sc), int(260 * sc)), Image.LANCZOS)
            if fade < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * max(0, fade))))
            canvas.alpha_composite(lay, ((W - lay.size[0]) // 2, CAP_Y + 40 - lay.size[1] // 2 + 40)); return
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(START), "-i", cfg["src"], "-t", str(dur), "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", str(FPS), "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-ss", str(START), "-i", cfg["src"], "-map", "0:v:0", "-map", "1:a:0",
    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-t", f"{dur:.3f}", "-movflags", "+faststart", cfg["out"]], stdin=subprocess.PIPE)
SRM = SR() if cfg.get('sr', True) else None; prev_sr = None
n = 0
while True:
    raw = dec.stdout.read(SW * SH * 3)
    if len(raw) < SW * SH * 3: break
    arr = np.frombuffer(raw, np.uint8).reshape(SH, SW, 3)
    if cfg.get("inpaint"):
        arr = arr.copy()
        for (x0, y0, x1, y1) in cfg["inpaint"]:
            X0, Y0, X1, Y1 = max(0, x0 - 4), max(0, y0 - 4), min(SW, x1 + 4), min(SH, y1 + 4); sub = arr[Y0:Y1, X0:X1].astype(np.float32); m = np.zeros(sub.shape[:2], bool); m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
            arr[Y0:Y1, X0:X1] = np.clip(diffuse(sub, m, iters=60), 0, 255).astype(np.uint8)
    fr = Image.fromarray(arr); t = n / FPS
    # blurred, darkened background built from the gameplay
    g = fr.crop(tuple(game)); bgs = g.resize((90, 160), Image.BILINEAR) if False else g.resize((W // 8, H // 8), Image.BILINEAR)
    bg = bgs.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BICUBIC); bg = Image.eval(bg, lambda v: int(v * 0.35))
    canvas = bg.convert("RGBA")
    zoom = 1.0 + 0.03 * min(1.0, t / dur)                                                     # small, slow push-in on the gameplay
    gimg = g.resize((W, GAME_H), Image.LANCZOS)
    if zoom > 1.0:
        cw2, ch2 = int(W / zoom), int(GAME_H / zoom); gimg = gimg.crop(((W - cw2) // 2, (GAME_H - ch2) // 2, (W - cw2) // 2 + cw2, (GAME_H - ch2) // 2 + ch2)).resize((W, GAME_H), Image.LANCZOS)
    if SRM is not None:                                                                    # Real-ESRGAN (general x4v3) on the tiny facecam crop, light temporal smoothing against flicker
        y = SRM(np.asarray(fr.crop(tuple(cam)))).astype(np.float32)
        if prev_sr is not None: y = 0.8 * y + 0.2 * prev_sr
        prev_sr = y; cimg = Image.fromarray(np.clip(y, 0, 255).astype(np.uint8)).resize((W, CAM_H), Image.LANCZOS)
    else: cimg = fr.crop(tuple(cam)).resize((W, CAM_H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    sh = Image.new("RGBA", (W + 60, CAM_H + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((30, 40, W + 30, CAM_H + 40), 26, fill=(0, 0, 0, 120)); canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (-30, CAM_Y - 30))
    canvas.alpha_composite(rounded(cimg, 26), (0, CAM_Y))
    sh2 = Image.new("RGBA", (W + 60, GAME_H + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh2).rounded_rectangle((30, 40, W + 30, GAME_H + 40), 26, fill=(0, 0, 0, 120)); canvas.alpha_composite(sh2.filter(ImageFilter.GaussianBlur(14)), (-30, GAME_Y - 30))
    canvas.alpha_composite(rounded(gimg, 26), (0, GAME_Y))
    draw_caption(canvas, t + START)
    enc.stdin.write(np.asarray(canvas.convert("RGB")).tobytes()); n += 1
enc.stdin.close(); enc.wait(); print("frames", n, "->", cfg["out"])
