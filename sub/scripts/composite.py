"""Finishing at 1080x1920: upscale, grade, bloom, grain, labels (depth, cross-section, speed tags), clean subtitles, fade."""
import sys, os, json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/user/Nikola123232/sub/scripts")
from tl import *
ROOT = "/home/user/Nikola123232/"; V = ROOT + "sub/"
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


ANCH = lj("renders/xs_anchors.json")
def src(f): return V + f"renders/main/{f:04d}.png"
def load(f):
    p = src(f)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        for d in range(1, 60):
            for q in (f - d, f + d):
                if os.path.exists(src(q)) and os.path.getsize(src(q)) > 0: p = src(q); break
            else: continue
            break
        else: return Image.new("RGB", (W, H), (6, 10, 16))
    im = Image.open(p).convert("RGB")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.3, percent=45, threshold=2))
_vig = None
def vig():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.42 * np.clip(d - 0.35, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)
    return _vig
def bloom(a):
    small = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)).astype(np.float32) / 255
    lum = small @ np.array([0.3, 0.59, 0.11], np.float32); br = small * np.clip((lum - 0.55) * 2.5, 0, 1)[..., None]
    bl = Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)).resize((W, H), Image.BICUBIC)
    return 1 - (1 - a) * (1 - np.asarray(bl).astype(np.float32) / 255 * 0.45)
def grade(a, f):
    sc_ = scene_of(f)
    a = np.clip(a * 1.10, 0, 1) ** 0.93
    l = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
    a = np.clip(l + (a - l) * 0.92, 0, 1) * np.array([0.96, 1.0, 1.05], np.float32)
    a = np.clip((a - 0.5) * 1.07 + 0.5 + 0.008, 0, 1)
    if F_FREEZE <= f <= 249: a = np.clip(l * 0.25 + a * 0.75, 0, 1)                      # frozen moment: slightly cooler / flatter
    return a * vig()
def shake(a, f):
    if not (F_COLL <= f <= F_COLL + 5): return a
    k = math.exp(-(f - F_COLL) / 2.0); dx, dy = int(14 * k * math.sin(f * 2.7)), int(10 * k * math.cos(f * 3.9))
    return np.roll(np.roll(a, dx, axis=1), dy, axis=0)
def label(d, xy, txt, al, size=34, var="SemiBold", anchor="lm"):
    d.text((xy[0] + 2, xy[1] + 2), txt, font=font(size, var), fill=(0, 0, 0, int(150 * al / 255)), anchor=anchor)
    d.text(xy, txt, font=font(size, var), fill=(255, 255, 255, int(al)), anchor=anchor, stroke_width=2, stroke_fill=(0, 0, 0, int(120 * al / 255)))
def leader(d, p0, p1, col, al):
    d.line([p0, p1], fill=(*col, int(al * 0.85)), width=3); d.ellipse((p1[0] - 7, p1[1] - 7, p1[0] + 7, p1[1] + 7), outline=(*col, int(al)), width=3)

def compose(f):
    a = np.asarray(load(f)).astype(np.float32) / 255.0
    a = grade(a, f); a = bloom(a)
    if F_COLL <= f <= F_COLL + 2: a = np.clip(a * (1 + 0.22 * (1 - (f - F_COLL) / 3.0)), 0, 1)
    a = shake(a, f)
    g_ = np.random.default_rng(f).standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1); a = np.clip(a + g_ * 0.012, 0, 1)
    if f >= NF - 22: a = a * (1 - ease((f - (NF - 22)) / 22.0))
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    def tag(txt, f0, f1, y=143, sub=None):
        if f0 <= f <= f1:
            k = min(ease((f - f0) / 8.0), 1 - ease((f - f1 + 8) / 8.0)); al = int(235 * k)
            d.rectangle((70, y - 25, 76, y + 25), fill=(255, 255, 255, al)); label(d, (96, y), txt, al, 36)
            if sub: label(d, (96, y + 46), sub, int(al * 0.8), 26, "Medium")
    tag("DEPTH: ~3,800 M", 262, 432)
    tag("PRESSURE HULL  ·  CROSS-SECTION", 436, 624, sub="ILLUSTRATIVE  ·  NOT TO SCALE")
    tag("FULL SPEED", F_COLL - 6, F_REAL_END)
    if F_REPLAY[0] <= f <= F_REPLAY[1]:
        k = min(ease((f - F_REPLAY[0]) / 6.0), 1 - ease((f - F_REPLAY[1] + 8) / 8.0)); al = int(235 * k)
        d.rectangle((70, 118, 76, 168), fill=(120, 190, 255, al)); label(d, (96, 133), "SLOW MOTION  ·  10× SLOWER", al, 34); label(d, (96, 178), "ILLUSTRATIVE REPLAY", int(al * 0.85), 26, "Medium")
        bw = 10; d.rectangle((0, 0, W - 1, H - 1), outline=(110, 180, 255, int(150 * k)), width=bw)
    # cross-section callouts (anchored to projected 3D points)
    if 436 <= f <= 624:
        an = ANCH.get(f)
        k = min(ease((f - 452) / 12.0), 1 - ease((f - 616) / 8.0)); al = int(240 * k)
        if k > 0:
            d.rounded_rectangle((36, 286, 700, 486), radius=22, fill=(0, 8, 18, int(120 * k)))
            for yy, col, l1, l2 in ((330, (90, 160, 255), "EXTERNAL WATER PRESSURE", "≈ 380 atm  (at ~3,800 m)"), (440, (255, 140, 50), "INSIDE THE HULL", "≈ 1 atm")):
                d.polygon([(74, yy - 14), (118, yy), (74, yy + 14)], fill=(*col, al)); d.rectangle((52, yy - 5, 78, yy + 5), fill=(*col, al))
                label(d, (140, yy - 8), l1, al, 34); label(d, (140, yy + 34), l2, int(al * 0.9), 30, "Medium")
        k2 = ease((f - 560) / 14.0) * (1 - ease((f - 616) / 8.0))
        if k2 > 0: label(d, (W / 2, 560), "THE SHELL BUCKLES INWARD", int(240 * k2), 38, anchor="mm")
    # subtitles: phrase level, no bounce, 2 lines max, safe zone above the Shorts UI
    t = (f - 1) / 30.0
    for (s, e, txt) in CH:
        if s <= t < e:
            k = min(ease((t - s) / 0.12), 1 - ease((t - e + 0.12) / 0.12)); al = int(255 * k)
            fnt = font(56, "SemiBold"); tw_ = d.textlength(txt, font=fnt); lines = [txt]
            if tw_ > W - 150:
                ws_ = txt.split(); best = None
                for i in range(1, len(ws_)):
                    a_, b_ = " ".join(ws_[:i]), " ".join(ws_[i:]); sc2 = max(d.textlength(a_, font=fnt), d.textlength(b_, font=fnt))
                    if best is None or sc2 < best[0]: best = (sc2, [a_, b_])
                lines = best[1]
            y = 1470 - (len(lines) - 1) * 36
            for ln in lines:
                d.text((W / 2 + 2, y + 3), ln, font=fnt, fill=(0, 0, 0, int(120 * k)), anchor="mm")
                d.text((W / 2, y), ln, font=fnt, fill=(255, 255, 255, al), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, int(190 * k)))
                y += 72
            break
    if f >= NF - 22: ov.putalpha(ov.getchannel("A").point(lambda v: int(v * (1 - ease((f - (NF - 22)) / 14.0)))))
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
