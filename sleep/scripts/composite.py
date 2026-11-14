"""Finishing at 1080x1920: upscale, light grade/bloom/grain, pupil-to-brain iris wipe, blinks/microsleep dip/glitch lapses, day labels, clean subtitles, fade.
usage: composite.py --test 20,100 | --encode [a b]  (encode frames a..b to sleep/out/video_noaudio.mp4)"""
import sys, os, json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/user/Nikola123232/sleep/scripts")
from sl.timeline import *
ROOT = "/home/user/Nikola123232/"; V = ROOT + "sleep/"
W, H = 1080, 1920
MONT = ROOT + "assets/fonts/Montserrat-Var.ttf"
_f = {}
def font(size, var="SemiBold"):
    k = (size, var)
    if k not in _f:
        f = ImageFont.truetype(MONT, size); f.set_variation_by_name(var); _f[k] = f
    return _f[k]
def c01(x): return max(0.0, min(1.0, x))
def ease(x): x = c01(x); return x * x * (3 - 2 * x)

words = json.load(open(V + "audio/vo/words.json"))["words"]
def chunks(ws, maxw=6, maxc=30):
    res, cur = [], []
    for w in ws:
        if cur and (len(cur) >= maxw or sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > maxc or w["line"] != cur[-1]["line"]): res.append(cur); cur = []
        cur.append(w)
        if re.search(r"[,.?!]$", w["w"]): res.append(cur); cur = []
    if cur: res.append(cur)
    out = []
    for i, c in enumerate(res):
        e = c[-1]["e"] + 0.22
        if i + 1 < len(res): e = min(e, res[i + 1][0]["s"] - 0.02)
        out.append((c[0]["s"] - 0.05, e, " ".join(w["w"] for w in c)))
    return out
CH = chunks(words)

def lj(p):
    try: return {int(k): v for k, v in json.load(open(V + p)).items()}
    except Exception: return {}
PUPIL = lj("renders/anchors_pupil.json")

def src(f):
    if in_apt(f): return V + f"renders/apt/{f:04d}.png"
    return V + f"renders/brain/{f:04d}.png"
def load(f, scale=1.0):
    p = src(f)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        for d in range(1, 120):
            for q in (f - d, f + d):
                pp = src(q)
                if in_apt(q) == in_apt(f) and os.path.exists(pp) and os.path.getsize(pp) > 0: p = pp; break
            else: continue
            break
        else: return Image.new("RGB", (W, H), (6, 8, 12))
    im = Image.open(p).convert("RGB")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))

_vig = None
def vig():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.40 * np.clip(d - 0.35, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)
    return _vig

def glitch_level(f):
    if f < 931 or f > 1186: return 0.0
    g = 0.0
    for fl in (985, 1060, 1118, 1160): g = max(g, math.exp(-((f - fl) / 4.0) ** 2))
    return g

def grade(a, f):
    cold = c01((f - 1) / 1340.0)
    if not in_apt(f):                                                       # brain shots are already bright: no shadow lift
        l = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
        a = np.clip(a * 0.92, 0, 1); a = np.clip((a - 0.5) * 1.08 + 0.5, 0, 1)
        return a * vig()
    a = np.clip(a * 1.12, 0, 1) ** (0.78 if 61 <= f <= 120 else 0.94)       # lift the dark apartment for phone screens (more in the POV shot)
    l = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
    a = np.clip(l + (a - l) * (1.0 - 0.18 * cold), 0, 1)                    # gradually desaturate
    tint = np.array([1.0 - 0.05 * cold, 1.0, 1.0 + 0.07 * cold], np.float32); a = a * tint
    a = np.clip((a - 0.5) * 1.06 + 0.5 + 0.012, 0, 1)
    return a * vig()

def bloom(a):
    small = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)).astype(np.float32) / 255
    lum = small @ np.array([0.3, 0.59, 0.11], np.float32); br = small * np.clip((lum - 0.62) * 2.5, 0, 1)[..., None]
    bl = Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BICUBIC)
    return 1 - (1 - a) * (1 - np.asarray(bl).astype(np.float32) / 255 * 0.5)

def rgb_split(a, px):
    if px <= 0: return a
    px = int(px); out = a.copy(); out[:, px:, 0] = a[:, :-px, 0]; out[:, :-px, 2] = a[:, px:, 2]; return out

def wavy(a, amp, f):
    if amp <= 0: return a
    y = np.arange(H); dx = (amp * np.sin(y * 0.02 + f * 0.35)).round().astype(np.int32)
    idx = np.clip(np.arange(W)[None, :] + dx[:, None], 0, W - 1); return np.take_along_axis(a, idx[:, :, None].repeat(3, 2), axis=1)

def blink_overlay(f, a):
    """POV shot: eyelids close and reopen around f=98 (top and bottom soft black bars)."""
    c = 0.0
    for fb in (99,):
        t = f - fb; 
        if -5 <= t <= 12: c = max(c, 1 - abs(t - 1.5) / 6.0 if t < 1.5 else 1 - (t - 1.5) / 10.5)
    c = c01(c)
    if c <= 0: return a
    yy = np.linspace(0, 1, H)[:, None]; m = np.clip((c * 0.62 - np.minimum(yy, 1 - yy)) / 0.12, 0, 1)
    return a * (1 - m[..., None])

def compose(f):
    # ---- source frame (with the pupil -> brain iris wipe at 184..194)
    if 184 <= f <= 194:
        eye = load(min(f, 190)); br = load(max(f, 191)); pa = PUPIL.get(190, {"px": 0.5, "py": 0.5, "pr": 0.1})
        t = ease((f - 184) / 10.0); r = (pa["pr"] * 0.9 + (1.45 - pa["pr"] * 0.9) * t ** 1.4) * H
        yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt((xx - pa["px"] * W) ** 2 + (yy - pa["py"] * H) ** 2)
        mask = np.clip((r - d) / 6.0, 0, 1)[..., None]
        a = (np.asarray(eye).astype(np.float32) * (1 - mask) + np.asarray(br).astype(np.float32) * mask) / 255.0
    else:
        a = np.asarray(load(f)).astype(np.float32) / 255.0
        # lapse: repeated (held) frame
        if 931 <= f <= 1186 and (f % 19 in (0, 1) or glitch_level(f) > 0.5): a = np.asarray(load(max(931, f - (f % 19 if f % 19 in (0, 1) else 2)))).astype(np.float32) / 255.0
    g = glitch_level(f); cold = c01((f - 931) / 255.0) if 931 <= f <= 1186 else 0.0
    a = grade(a, f); a = bloom(a) if in_apt(f) else a
    if 931 <= f <= 1186: a = wavy(a, 1.0 + 4.0 * g + 1.5 * cold, f); a = rgb_split(a, 1 + 6 * g + 2 * cold)
    a = blink_overlay(f, a)
    # microsleep: dip to black / eyes shut
    dip = 0.0
    if 636 <= f <= 652: dip = ease((f - 636) / 8.0) * (1 - ease((f - 646) / 6.0))
    if 931 <= f <= 1186: dip = max(dip, 0.85 * g)
    if dip > 0: a = a * (1 - dip)
    g_ = np.random.default_rng(f).standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1); a = np.clip(a + g_ * 0.010, 0, 1)
    if f >= 1296: a = a * (1 - ease((f - 1296) / 44.0))
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # day labels (small, top-left)
    for (txt, f0, f1) in (("24 HOURS", 291, 502), ("48 HOURS", 503, 732), ("72 HOURS", 733, 930), ("7 DAYS", 931, 1186)):
        if f0 <= f <= f1:
            k = min(ease((f - f0) / 10.0), 1 - ease((f - f1 + 8) / 8.0)); al = int(235 * k)
            d.rectangle((70, 118, 76, 168), fill=(255, 255, 255, al))
            d.text((96, 143), txt, font=font(36, "SemiBold"), fill=(255, 255, 255, al), anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0, int(140 * k)))
    # subtitles: phrase level, no bounce, 2 lines max, safe zone above the Shorts UI
    t = (f - 1) / 30.0
    for (s, e, txt) in CH:
        if s <= t < e:
            k = min(ease((t - s) / 0.12), 1 - ease((t - e + 0.12) / 0.12)); al = int(255 * k)
            fnt = font(56, "SemiBold"); tw = d.textlength(txt, font=fnt); lines = [txt]
            if tw > W - 150:
                ws_ = txt.split(); best = None
                for i in range(1, len(ws_)):
                    a_, b_ = " ".join(ws_[:i]), " ".join(ws_[i:]); sc_ = max(d.textlength(a_, font=fnt), d.textlength(b_, font=fnt))
                    if best is None or sc_ < best[0]: best = (sc_, [a_, b_])
                lines = best[1]
            y = 1470 - (len(lines) - 1) * 36
            for ln in lines:
                d.text((W / 2 + 2, y + 3), ln, font=fnt, fill=(0, 0, 0, int(120 * k)), anchor="mm")
                d.text((W / 2, y), ln, font=fnt, fill=(255, 255, 255, al), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, int(190 * k)))
                y += 72
            break
    if f >= 1296: ov.putalpha(ov.getchannel("A").point(lambda v: int(v * (1 - ease((f - 1296) / 30.0)))))
    im.alpha_composite(ov)
    return im.convert("RGB")

if __name__ == "__main__":
    if "--test" in sys.argv:
        os.makedirs(V + "previews/comp", exist_ok=True)
        for f in [int(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]: compose(f).save(f"{V}previews/comp/{f:04d}.jpg", quality=90)
        print("ok")
    elif "--encode" in sys.argv:
        i = sys.argv.index("--encode"); a0 = int(sys.argv[i + 1]) if len(sys.argv) > i + 2 else 1; a1 = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else NF
        out = V + ("out/video_noaudio.mp4" if (a0, a1) == (1, NF) else "out/segment.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(a0, a1 + 1):
            p.stdin.write(compose(f).tobytes())
            if f % 100 == 0: print("frame", f, flush=True)
        p.stdin.close(); p.wait(); print("wrote", out)
