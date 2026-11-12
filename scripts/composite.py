"""2D compositing at full 1080x1920: upscale + grade, transitions, hook title, HUD, 3D-tracked callouts,
animated word-highlighted subtitles, end title. Streams frames into FFmpeg (or writes test PNGs).
usage: composite.py --test 10,350,700     (PNG previews to previews/comp/)
       composite.py --encode               (writes out/video_noaudio.mp4)"""
import sys, os, json, math, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = "/home/user/Nikola123232/"
W, H = 1080, 1920
NF = 1800
SCENES = [("s1", 1, 240), ("s2", 241, 540), ("s3", 541, 990), ("s4", 991, 1350), ("s5", 1351, 1680), ("s6", 1681, 1800)]
ANTON = ROOT + "assets/fonts/Anton-Regular.ttf"
MONT = ROOT + "assets/fonts/Montserrat-Var.ttf"
YEL = (255, 212, 0)
RED = (255, 60, 40)
GRN = (60, 235, 120)
CYN = (90, 200, 255)
WHITE = (255, 255, 255)

_fonts = {}
def font(path, size, var=None):
    k = (path, size, var)
    if k not in _fonts:
        f = ImageFont.truetype(path, size)
        if var:
            f.set_variation_by_name(var)
        _fonts[k] = f
    return _fonts[k]


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_back(x, s=1.7):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def scene_of(f):
    for name, a, b in SCENES:
        if a <= f <= b:
            return name, a, b
    return SCENES[-1]


# ------------------------------------------------------------------ data
words = json.load(open(ROOT + "audio/vo/words.json"))["words"]

def merge_tokens(ws):
    out = []
    i = 0
    while i < len(ws):
        w = ws[i]
        seq = [x["w"].lower().strip(",.?!") for x in ws[i:i + 5]]
        if seq[:5] == ["three", "hundred", "kilometers", "per", "hour"]:
            punct = re.sub(r"[\w' -]", "", ws[i + 4]["w"])
            out.append({"w": "300 KM/H" + punct, "s": w["s"], "e": ws[i + 4]["e"], "line": w["line"]}); i += 5; continue
        if seq[:2] == ["formula", "one"]:
            out.append({"w": "FORMULA 1", "s": w["s"], "e": ws[i + 1]["e"], "line": w["line"]}); i += 2; continue
        out.append(dict(w)); i += 1
    return out
words = merge_tokens(words)


def chunks(ws, maxw=3, maxc=17):
    res, cur = [], []
    for w in ws:
        if cur and (len(cur) >= maxw or sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > maxc or w["line"] != cur[-1]["line"]):
            res.append(cur); cur = []
        cur.append(w)
        if re.search(r"[,.?!]$", w["w"]):
            res.append(cur); cur = []
    if cur:
        res.append(cur)
    out = []
    for i, c in enumerate(res):
        s = c[0]["s"]
        e = c[-1]["e"] + 0.25
        if i + 1 < len(res):
            e = min(e, res[i + 1][0]["s"])
        out.append((s, e, c))
    return out
CHUNKS = chunks(words)

def load_json(p):
    try:
        return {int(k): v for k, v in json.load(open(ROOT + p)).items()}
    except Exception:
        return {}
ANCH = {}
for s in ("s3", "s4", "s5"):
    ANCH.update(load_json(f"renders/anchors_{s}.json"))
HUD1 = load_json("renders/anchors_s1.json")
HUD2 = load_json("renders/hud_s2.json")

# callouts: (anchor, text, f_in, f_out, colour, dx, dy)
LABELS = [
    ("harness", "6-POINT HARNESS", 560, 760, RED, 1, 170),
    ("brain", "BRAIN", 636, 760, YEL, -1, -30),
    ("heart", "HEART & LUNGS", 671, 760, YEL, -1, 40),
    ("decel", "DECELERATION", 690, 760, RED, -1, -70),
    ("inertia", "INERTIA", 700, 760, YEL, 1, -60),
    ("brain", "CONCUSSION RISK", 808, 875, RED, -1, -80),
    ("neck", "NECK INJURY", 838, 893, RED, -1, 30),
    ("abdomen", "INTERNAL TRAUMA", 878, 985, RED, -1, 60),
    ("skull", "SKULL", 998, 1080, WHITE, -1, -90),
    ("brain", "BRAIN", 1004, 1080, YEL, 1, -60),
    ("coup", "IMPACT ZONE", 1018, 1080, RED, 1, 60),
    ("neck", "CERVICAL SPINE", 1096, 1188, RED, -1, 30),
    ("helmet", "HELMET", 1166, 1190, CYN, 1, -60),
    ("hans", "HANS DEVICE", 1198, 1345, GRN, 1, -40),
    ("tether", "TETHERS", 1216, 1345, GRN, -1, 60),
    ("cell", "CARBON SURVIVAL CELL", 1388, 1452, CYN, 1, -100),
    ("front", "CRASH STRUCTURES", 1460, 1525, (255, 150, 30), -1, -80),
    ("side", "ENERGY ABSORBING", 1472, 1525, (255, 150, 30), 1, 80),
    ("harness", "6-POINT HARNESS", 1522, 1585, RED, 1, 60),
    ("hans", "HANS", 1552, 1612, GRN, -1, -40),
    ("halo", "HALO", 1580, 1645, CYN, 1, -90),
    ("helmet", "HELMET", 1606, 1668, WHITE, -1, -70),
]
TAGS = [  # big status tags (text, f_in, f_out, colour)
    ("WITHOUT HEAD RESTRAINT", 1098, 1186, RED),
    ("WITH HANS", 1246, 1345, GRN),
]
json.dump([(l[2], -0.3 if l[5] < 0 else 0.3) for l in LABELS] + [(t[1], 0) for t in TAGS], open(ROOT + "renders/label_times.json", "w"))


# ------------------------------------------------------------------ helpers
def load_frame(f):
    name, a, b = scene_of(f)
    p = f"{ROOT}renders/{name}/{f:04d}.png"
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        # fall back to nearest rendered frame (allows test runs mid-render)
        for d in range(1, 400):
            for q in (f - d, f + d):
                qq = f"{ROOT}renders/{name}/{q:04d}.png"
                if a <= q <= b and os.path.exists(qq) and os.path.getsize(qq) > 0:
                    p = qq; break
            else:
                continue
            break
        else:
            return Image.new("RGB", (W, H), (10, 12, 20))
    im = Image.open(p).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    return im


_vig = None
def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.32 * np.clip(d - 0.45, 0, 1) ** 1.6, 0, 1)[..., None].astype(np.float32)
    return _vig


def grade(im, f):
    a = np.asarray(im).astype(np.float32) / 255.0
    a = np.clip((a - 0.5) * 1.06 + 0.5, 0, 1)                   # gentle contrast
    a = a * vignette()
    rs = np.random.default_rng(f).standard_normal((H // 2, W // 2, 1)).astype(np.float32)
    rs = np.repeat(np.repeat(rs, 2, 0), 2, 1)
    a = np.clip(a + rs * 0.012, 0, 1)                             # fine film grain
    return a


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def flash_amount(f):
    """White flashes / dips for transitions & the impact."""
    v = 0.0
    v = max(v, ease((f - 526) / 14) * (1 - ease((f - 541) / 12)))   # s2 -> s3 white flash
    v = max(v, 0.55 * clamp01(1 - abs(f - 358) / 3))                # impact flash
    v = max(v, ease((f - 1676) / 5) * (1 - ease((f - 1681) / 8)))   # s5 -> s6
    return v


def text_stroke(d, xy, txt, fnt, fill, stroke=6, sfill=(0, 0, 0), anchor="mm"):
    d.text(xy, txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)


# ------------------------------------------------------------------ overlay layers
def draw_hook(ov, f):
    if f > 125:
        return
    d = ImageDraw.Draw(ov)
    t_in = ease_back((f - 4) / 12)
    out = 1 - ease((f - 108) / 14)
    a = int(255 * clamp01(t_in) * out)
    if a <= 0:
        return
    l1 = "WHAT HAPPENS TO YOUR BODY"
    l2 = "IF YOU CRASH AT"
    l3 = "300 KM/H?"
    y0 = 250 - 40 * (1 - t_in)
    s1 = font(ANTON, 72); s2 = font(ANTON, 64); s3 = font(ANTON, 150)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(layer)
    text_stroke(dl, (W / 2, y0), l1, s1, WHITE, 7)
    text_stroke(dl, (W / 2, y0 + 82), l2, s2, WHITE, 7)
    pulse = 1 + 0.03 * math.sin(f * 0.4)
    s3p = font(ANTON, int(150 * pulse))
    text_stroke(dl, (W / 2, y0 + 205), l3, s3p, YEL, 9)
    if a < 255:
        alpha = layer.getchannel("A").point(lambda v: v * a // 255)
        layer.putalpha(alpha)
    ov.alpha_composite(layer)


def panel(d, box, fill=(8, 12, 22, 170), outline=None, r=18):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=3)


def draw_hud(ov, f):
    d = ImageDraw.Draw(ov)
    if 108 <= f <= 240:
        k = ease_back((f - 108) / 10)
        kmh = HUD1.get(f, {}).get("kmh", 300)
        x0 = 60 - 400 * (1 - k)
        panel(d, (x0, 230, x0 + 330, 400))
        d.text((x0 + 26, 248), "SPEED", font=font(MONT, 30, "Bold"), fill=(170, 200, 230))
        d.text((x0 + 22, 280), f"{kmh:3.0f}", font=font(ANTON, 96), fill=WHITE)
        d.text((x0 + 210, 330), "KM/H", font=font(ANTON, 40), fill=YEL)
        # speed bar
        d.rounded_rectangle((x0 + 26, 386, x0 + 26 + 278 * min(1, kmh / 330), 392), radius=3, fill=YEL)
    if 241 <= f <= 470:
        h = HUD2.get(f, {})
        kmh = h.get("kmh", 0); g = h.get("g", 0); rate = h.get("rate", 1)
        out = 1 - ease((f - 452) / 16)
        x0 = 60 - 420 * (1 - out)
        panel(d, (x0, 230, x0 + 380, 480))
        d.text((x0 + 26, 248), "SPEED", font=font(MONT, 30, "Bold"), fill=(170, 200, 230))
        d.text((x0 + 22, 280), f"{kmh:3.0f}", font=font(ANTON, 96), fill=WHITE)
        d.text((x0 + 210, 330), "KM/H", font=font(ANTON, 40), fill=YEL)
        gtxt = "50+" if g >= 50 else f"{g:0.1f}"
        peak_seen = f >= 362
        col = RED if g > 5 or peak_seen else WHITE
        d.text((x0 + 26, 398), "G-FORCE", font=font(MONT, 30, "Bold"), fill=(170, 200, 230))
        d.text((x0 + 26, 432), (("PEAK 50+" if peak_seen and g < 5 else gtxt) + " g"), font=font(ANTON, 40), fill=col,
               anchor="la")
        if rate < 0.6:
            blink = (f // 8) % 2 == 0
            panel(d, (W - 380, 236, W - 60, 300), fill=(8, 12, 22, 170))
            if blink:
                d.ellipse((W - 360, 255, W - 334, 281), fill=RED)
            d.text((W - 320, 268), "SLOW MOTION", font=font(MONT, 34, "ExtraBold"), fill=WHITE, anchor="lm")


def draw_labels(ov, f):
    d = ImageDraw.Draw(ov)
    for (an, txt, fi, fo, col, side, dy) in LABELS:
        if not (fi <= f <= fo + 8):
            continue
        a = ANCH.get(f, {}).get(an)
        if not a or a[2] <= 0:
            continue
        px, py = a[0] * W, a[1] * H
        if not (-50 < px < W + 50 and -50 < py < H + 50):
            continue
        k_in = ease((f - fi) / 10)
        k_out = 1 - ease((f - fo) / 8)
        k = min(k_in, k_out)
        if k <= 0:
            continue
        fnt = font(MONT, 40, "ExtraBold")
        tw = d.textlength(txt, font=fnt)
        lx = px + side * 150
        ly = py + dy
        # keep label boxes on screen
        if side > 0:
            lx = min(lx, W - 50 - tw - 30)
            lx = max(lx, 40)
        else:
            lx = max(lx, 50 + tw + 30)
            lx = min(lx, W - 40)
        ly = min(max(ly, 520), 1180)
        ex = lx; ey = ly
        # leader line grows from the anchor
        mx = px + (ex - px) * k; my = py + (ey - py) * k
        d.line((px, py, mx, my), fill=col + (int(230 * k),), width=4)
        r = 9 * k
        d.ellipse((px - r, py - r, px + r, py + r), fill=col + (int(255 * k),), outline=(0, 0, 0, int(200 * k)), width=2)
        if k > 0.6:
            n = max(1, int(len(txt) * clamp01((f - fi - 5) / 10)))
            sub = txt[:n] if f < fo else txt
            bx0 = ex if side > 0 else ex - tw - 30
            bx1 = bx0 + tw + 30
            alpha = int(255 * min(1, (k - 0.6) / 0.4))
            panel(d, (bx0, ey - 32, bx1, ey + 32), fill=(6, 10, 20, int(185 * alpha / 255)), outline=col + (alpha,), r=12)
            d.text((bx0 + 15, ey), sub, font=fnt, fill=WHITE + (alpha,), anchor="lm")
    for (txt, fi, fo, col) in TAGS:
        if fi <= f <= fo + 8:
            k = min(ease_back((f - fi) / 10), 1 - ease((f - fo) / 8))
            if k <= 0:
                continue
            fnt = font(ANTON, int(78 * (0.8 + 0.2 * k)))
            tw = d.textlength(txt, font=fnt)
            y = 340
            panel(d, (W / 2 - tw / 2 - 30, y - 55, W / 2 + tw / 2 + 30, y + 55), fill=col + (int(220 * k),), r=14)
            d.text((W / 2, y), txt, font=fnt, fill=(255, 255, 255, int(255 * k)), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, int(160 * k)))


def draw_subs(ov, f):
    t = (f - 1) / 30.0
    cur = None
    for (s, e, c) in CHUNKS:
        if s - 0.05 <= t < e:
            cur = (s, e, c)
            break
    if not cur:
        return
    s, e, c = cur
    d = ImageDraw.Draw(ov)
    k = ease_back((t - s + 0.05) / 0.16, 2.2)
    size = int(84 * (0.82 + 0.18 * k))
    fnt = font(MONT, size, "Black")
    toks = [w["w"].upper() for w in c]
    sp = d.textlength(" ", font=fnt)
    widths = [d.textlength(x, font=fnt) for x in toks]
    total = sum(widths) + sp * (len(toks) - 1)
    lines = [list(range(len(toks)))]
    if total > W - 120:
        cut = len(toks) // 2 + len(toks) % 2
        lines = [list(range(cut)), list(range(cut, len(toks)))]
    y = 1330 - (len(lines) - 1) * 50
    for ln in lines:
        lw = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
        x = W / 2 - lw / 2
        for i in ln:
            w = c[i]
            active = w["s"] - 0.04 <= t < (c[i + 1]["s"] if i + 1 < len(c) else e)
            col = YEL if active else WHITE
            if active:
                d.rounded_rectangle((x - 10, y - size * 0.62, x + widths[i] + 10, y + size * 0.62), radius=12, fill=(0, 0, 0, 120))
            d.text((x, y), toks[i], font=fnt, fill=col, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0))
            x += widths[i] + sp
        y += size * 1.15


def draw_end_title(ov, f):
    if f < 1728:
        return
    d = ImageDraw.Draw(ov)
    k = ease_back((f - 1728) / 14)
    k2 = ease((f - 1745) / 12)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(layer)
    y = 470
    fnt = font(ANTON, int(132 * (0.7 + 0.3 * k)))
    text_stroke(dl, (W / 2, y), "SURVIVAL", fnt, WHITE, 8)
    text_stroke(dl, (W / 2, y + 140), "BY DESIGN", fnt, YEL, 8)
    if k2 > 0:
        w2 = int(560 * k2)
        dl.rectangle((W / 2 - w2 / 2, y + 232, W / 2 + w2 / 2, y + 238), fill=YEL)
        dl.text((W / 2, y + 285), "THE SCIENCE OF AN F1 CRASH", font=font(MONT, 40, "ExtraBold"), fill=(255, 255, 255, int(255 * k2)),
                anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(200 * k2)))
    a = clamp01((f - 1728) / 6)
    if a < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    ov.alpha_composite(layer)


def compose(f):
    base = load_frame(f)
    # freeze-dissolves into scenes 4 and 5
    for boundary, dur in ((991, 9), (1351, 9)):
        if boundary <= f < boundary + dur:
            prev = load_frame(boundary - 1)
            al = ease((f - boundary + 1) / (dur + 1))
            base = Image.blend(prev, base, al)
    a = grade(base, f)
    fl = flash_amount(f)
    if fl > 0:
        a = a * (1 - fl) + fl
    # end: slight darkening behind the title
    if f >= 1725:
        a = a * (1 - 0.35 * ease((f - 1725) / 20))
    im = to_img(a).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hook(ov, f)
    draw_hud(ov, f)
    draw_labels(ov, f)
    draw_end_title(ov, f)
    draw_subs(ov, f)
    im.alpha_composite(ov)
    return im.convert("RGB")


if __name__ == "__main__":
    if "--test" in sys.argv:
        fl = [int(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]
        os.makedirs(ROOT + "previews/comp", exist_ok=True)
        for f in fl:
            compose(f).save(f"{ROOT}previews/comp/{f:04d}.jpg", quality=88)
        print("ok")
    elif "--encode" in sys.argv:
        out = ROOT + "out/video_noaudio.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(1, NF + 1):
            p.stdin.write(compose(f).tobytes())
            if f % 100 == 0:
                print("frame", f, flush=True)
        p.stdin.close(); p.wait()
        print("wrote", out)
