"""2D finishing at 1080x1920: upscale+sharpen, bloom, heat-haze, grade, transitions, hook text, HUDs, tracked labels,
animated word-highlight subtitles, fade to black.
usage: composite.py --test 10,100      (JPEGs to volcano/previews/comp/)
       composite.py --encode           (volcano/out/video_noaudio.mp4)"""
import sys, os, json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/home/user/Nikola123232/"; V = ROOT + "volcano/"
W, H = 1080, 1920; NF = 1800
SCENES = [("v12", 1, 150), ("v3", 151, 420), ("v4", 421, 750), ("v5", 751, 1110), ("v6", 1111, 1470), ("v7", 1471, 1680), ("v8", 1681, 1800)]
CUTS = (151, 421, 546, 751, 809, 951, 1111, 1471, 1681)          # 6-frame dissolves
ANTON = ROOT + "assets/fonts/Anton-Regular.ttf"; MONT = ROOT + "assets/fonts/Montserrat-Var.ttf"
YEL = (255, 214, 0); ORG = (255, 128, 20); RED = (255, 64, 40); WHITE = (255, 255, 255); CYN = (90, 200, 255); GRN = (70, 235, 130)
_fonts = {}
def font(path, size, var=None):
    k = (path, size, var)
    if k not in _fonts:
        f = ImageFont.truetype(path, size)
        if var: f.set_variation_by_name(var)
        _fonts[k] = f
    return _fonts[k]
def c01(x): return max(0.0, min(1.0, x))
def ease(x): x = c01(x); return x * x * (3 - 2 * x)
def back(x, s=1.9): x = c01(x) - 1; return x * x * ((s + 1) * x + s) + 1
def scene_of(f):
    for n, a, b in SCENES:
        if a <= f <= b: return n, a, b
    return SCENES[-1]

words = json.load(open(V + "audio/vo/words.json"))["words"]
def chunks(ws, maxw=3, maxc=19):
    res, cur = [], []
    for w in ws:
        if cur and (len(cur) >= maxw or sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > maxc or w["line"] != cur[-1]["line"]):
            res.append(cur); cur = []
        cur.append(w)
        if re.search(r"[,.?!]$", w["w"]): res.append(cur); cur = []
    if cur: res.append(cur)
    out = []
    for i, c in enumerate(res):
        e = c[-1]["e"] + 0.2
        if i + 1 < len(res): e = min(e, res[i + 1][0]["s"])
        out.append((c[0]["s"], e, c))
    return out
CHUNKS = chunks(words)
KEYWORDS = {"volcano", "dead", "lava", "heat", "gases", "gas", "burns", "temperatures", "thousand", "degrees", "celsius", "radiant", "toxic", "oxygen-poor",
            "consciousness", "catastrophic", "denser", "viscous", "kill", "airways", "sink", "crater", "dangerous", "threat", "water"}

def lj(p):
    try: return {int(k): v for k, v in json.load(open(V + p)).items()}
    except Exception: return {}
ANCH = {}
for n in ("v4", "v5", "v7"): ANCH.update(lj(f"renders/anchors_{n}.json"))
INFO = {}
for n in ("v3", "v6"):
    d = lj(f"renders/anchors_{n}.json")
    for k, v in d.items():
        if isinstance(v, dict) and "dist" in v: INFO[k] = v

# tracked labels: (anchor, text, f_in, f_out, colour, side, dy)
LABELS = [
    ("epi", "EPIDERMIS", 556, 745, CYN, 1, 0), ("der", "DERMIS", 566, 745, ORG, 1, 0), ("fat", "HYPODERMIS (FAT)", 576, 745, YEL, 1, 0),
    ("hair", "HAIR FOLLICLE", 586, 700, WHITE, -1, -20), ("sweat", "SWEAT GLAND", 600, 690, WHITE, 1, 40),
    ("vessel", "BLOOD VESSELS", 610, 745, RED, -1, 20), ("nerve", "NERVE ENDINGS", 596, 670, YEL, 1, -40), ("blister", "BLISTER", 650, 720, ORG, -1, -50),
    ("mouth", "HOT GAS IN", 758, 808, ORG, 1, -60), ("lungs", "LUNGS", 986, 1062, RED, -1, 40), ("brain", "BRAIN: LOW OXYGEN", 1030, 1112, YEL, 1, -30),
    ("trachea", "WINDPIPE", 1002, 1050, WHITE, 1, -50),
]
TAGS = [  # (text, f_in, f_out, colour, y)
    ("EXTREME HEAT", 436, 540, RED, 380), ("1ST DEGREE: REDDENING", 600, 640, ORG, 330), ("2ND DEGREE: BLISTERS", 641, 692, ORG, 330), ("3RD DEGREE: DEEP TISSUE", 693, 748, RED, 330),
    ("DANGEROUS GASES", 774, 884, RED, 330), ("TOXIC GAS", 905, 952, GRN, 330), ("CONTACT", 1264, 1296, RED, 360), ("CATASTROPHIC BURNS", 1300, 1380, RED, 330),
    ("IT FLOATS ON TOP", 1392, 1470, ORG, 330), ("LAVA ≠ WATER", 1476, 1680, YEL, 280),
]

def load_frame(f, zoom=1.0, shift=(0, 0)):
    n, a, b = scene_of(f)
    p = f"{V}renders/{n}/{f:04d}.png"
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        for d in range(1, 300):
            for q in (f - d, f + d):
                qq = f"{V}renders/{n}/{q:04d}.png"
                if a <= q <= b and os.path.exists(qq) and os.path.getsize(qq) > 0: p = qq; break
            else: continue
            break
        else: return Image.new("RGB", (W, H), (10, 8, 8))
    im = Image.open(p).convert("RGB")
    Z = zoom
    im = im.resize((int(W * Z), int(H * Z)), Image.LANCZOS)
    if Z > 1.0 or shift != (0, 0):
        x0 = int((im.width - W) / 2 + shift[0]); y0 = int((im.height - H) / 2 + shift[1])
        x0 = max(0, min(im.width - W, x0)); y0 = max(0, min(im.height - H, y0)); im = im.crop((x0, y0, x0 + W, y0 + H))
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))

_vig = None
def vig():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.38 * np.clip(d - 0.4, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)
    return _vig

def heat_weight(f):
    if f <= 420 or 421 <= f <= 545 or 1111 <= f <= 1470 or f >= 1681: return 1.0
    return 0.0

def fx(im, f):
    a = np.asarray(im).astype(np.float32) / 255.0
    hw = heat_weight(f)
    if hw > 0:     # subtle heat-haze: rows shift horizontally with travelling sine, stronger in the lower (lava) half
        y = np.arange(H); t = f / 30.0
        amp = (1.2 + 2.6 * (y / H) ** 1.5) * hw
        dx = (amp * np.sin(y * 0.047 + t * 8.0) + 0.5 * amp * np.sin(y * 0.113 - t * 11.0)).round().astype(np.int32)
        idx = np.clip(np.arange(W)[None, :] + dx[:, None], 0, W - 1)
        a = np.take_along_axis(a, idx[:, :, None].repeat(3, 2), axis=1)
    # bloom
    small = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)).astype(np.float32) / 255
    lum = small @ np.array([0.3, 0.59, 0.11], np.float32)
    br = small * np.clip((lum - 0.5) * 2.2, 0, 1)[..., None]
    bl = Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BICUBIC)
    a = 1 - (1 - a) * (1 - np.asarray(bl).astype(np.float32) / 255 * 0.65)
    # grade: contrast, warm highlights / cool shadows, saturation
    a = np.clip((a - 0.5) * 1.08 + 0.5, 0, 1)
    l = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
    a = np.clip(l + (a - l) * 1.12, 0, 1)
    a = a * np.array([1.03, 1.0, 0.95], np.float32) * vig()
    g = np.random.default_rng(f).standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return np.clip(a + g * 0.011, 0, 1)

def to_img(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def flash(f):
    v = 0.0
    v = max(v, 0.55 * c01(1 - abs(f - 61) / 3.0))                      # freeze flash
    v = max(v, 0.35 * c01(1 - abs(f - 74) / 3.0))                      # bass hit
    v = max(v, 0.55 * c01(1 - abs(f - 1263) / 4.0))                    # contact
    return v

def stroke_text(d, xy, txt, fnt, fill, stroke=7, anchor="mm", sfill=(0, 0, 0)):
    d.text(xy, txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)

def panel(d, box, fill=(8, 10, 18, 175), outline=None, r=18):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=3)

def draw_hook(ov, f):
    """f1-60 title card (small), f73-150 BEFORE YOU TOUCH IT?!"""
    d = ImageDraw.Draw(ov)
    if 73 <= f <= 152:
        k = back((f - 73) / 7.0, 2.6); out = 1 - ease((f - 140) / 10.0)
        sc_ = 2.3 - 1.3 * c01((f - 73) / 6.0)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        sh = int(10 * max(0, 1 - (f - 73) / 14.0))
        ox = int(sh * math.sin(f * 7.1)); oy = int(sh * math.cos(f * 6.3))
        fnt = font(ANTON, int(150 * sc_ if f < 79 else 150))
        stroke_text(dl, (W / 2 + ox, 470 + oy), "BEFORE YOU", fnt, WHITE, 10)
        stroke_text(dl, (W / 2 + ox, 640 + oy), "TOUCH IT?!", font(ANTON, int(190 * (sc_ if f < 79 else 1.0))), (255, 90, 25), 12)
        a = int(255 * c01(k) * out)
        lay.putalpha(lay.getchannel("A").point(lambda v: v * a // 255)); ov.alpha_composite(lay)

def draw_hud(ov, f):
    d = ImageDraw.Draw(ov)
    def meter(title, val, unit, f_in, f_out, col):
        k = min(back((f - f_in) / 10.0), 1 - ease((f - f_out) / 10.0))
        if k <= 0: return
        x0 = 60 - 420 * (1 - c01(k))
        panel(d, (x0, 150, x0 + 400, 330))
        d.text((x0 + 26, 168), title, font=font(MONT, 28, "Bold"), fill=(185, 200, 220))
        d.text((x0 + 22, 205), f"{val:,.0f}", font=font(ANTON, 100), fill=WHITE)
        d.text((x0 + 22 + d.textlength(f"{val:,.0f}", font=font(ANTON, 100)) + 14, 262), unit, font=font(ANTON, 42), fill=col)
    if 151 <= f <= 420: meter("DISTANCE TO LAVA", INFO.get(f, {}).get("dist", 0), "m", 160, 410, ORG)
    if 1111 <= f <= 1262: meter("HEIGHT ABOVE LAVA", INFO.get(f, {}).get("dist", 0), "m", 1118, 1255, ORG)
    if 421 <= f <= 545:   # thermometer
        k = min(back((f - 428) / 12.0), 1 - ease((f - 538) / 8.0))
        if k > 0:
            temp = 1000 * ease((f - 430) / 90.0)
            x0 = W - 190 + 260 * (1 - c01(k)); y0, y1 = 520, 1180
            panel(d, (x0 - 40, y0 - 90, x0 + 130, y1 + 90))
            d.rounded_rectangle((x0 + 20, y0, x0 + 70, y1), radius=24, outline=(220, 230, 240), width=4, fill=(20, 24, 32))
            hh = max(14.0, (y1 - y0) * min(1.0, temp / 1000))
            d.rounded_rectangle((x0 + 28, y1 - hh, x0 + 62, y1 - 6), radius=16, fill=(255, 70 + int(110 * (1 - temp / 1000)), 20))
            d.ellipse((x0 + 5, y1 - 30, x0 + 85, y1 + 50), fill=(255, 60, 20), outline=(220, 230, 240), width=4)
            d.text((x0 + 45, y0 - 55), f"{temp:,.0f}°C" + ("+" if temp >= 990 else ""), font=font(ANTON, 36), fill=WHITE, anchor="mm")
    if 940 <= f <= 1112:  # oxygen level
        k = min(back((f - 942) / 12.0), 1 - ease((f - 1104) / 8.0))
        if k > 0:
            o2 = 1.0 - 0.78 * ease((f - 950) / 140.0)
            x0 = W - 190 + 260 * (1 - c01(k)); y0, y1 = 560, 1160
            panel(d, (x0 - 40, y0 - 100, x0 + 130, y1 + 70))
            d.text((x0 + 45, y0 - 62), "O₂", font=font(ANTON, 48), fill=(120, 190, 255), anchor="mm")
            d.rounded_rectangle((x0 + 20, y0, x0 + 70, y1), radius=10, outline=(220, 230, 240), width=4, fill=(20, 24, 32))
            hh = max(14.0, (y1 - y0 - 12) * o2)
            col = (60, 170, 255) if o2 > 0.6 else ((255, 200, 40) if o2 > 0.4 else (255, 70, 50))
            d.rounded_rectangle((x0 + 28, y1 - 6 - hh, x0 + 62, y1 - 6), radius=6, fill=col)
            d.text((x0 + 45, y1 + 35), "OXYGEN", font=font(MONT, 22, "Bold"), fill=(185, 200, 220), anchor="mm")

def draw_labels(ov, f):
    d = ImageDraw.Draw(ov)
    for (an, txt, fi, fo, col, side, dy) in LABELS:
        if not (fi <= f <= fo + 8): continue
        a = ANCH.get(f, {}).get(an)
        if not a or a[2] <= 0: continue
        px, py = a[0] * W, a[1] * H
        if not (-30 < px < W + 30 and -30 < py < H + 30): continue
        k = min(ease((f - fi) / 10.0), 1 - ease((f - fo) / 8.0))
        if k <= 0: continue
        fnt = font(MONT, 40, "ExtraBold"); tw = d.textlength(txt, font=fnt)
        lx = px + side * 170; ly = min(max(py + dy, 520), 1180)
        lx = max(40 + tw + 30, min(W - 40, lx)) if side < 0 else max(40, min(lx, W - 70 - tw))
        ex = lx
        mx, my = px + (ex - px) * k, py + (ly - py) * k
        d.line((px, py, mx, my), fill=col + (int(235 * k),), width=4)
        r = 10 * k; d.ellipse((px - r, py - r, px + r, py + r), fill=col + (int(255 * k),), outline=(0, 0, 0, int(200 * k)), width=2)
        if k > 0.6:
            n = max(1, int(len(txt) * c01((f - fi - 5) / 10.0))); sub = txt if f > fi + 15 else txt[:n]
            bx0 = ex if side > 0 else ex - tw - 30; al = int(255 * min(1, (k - 0.6) / 0.4))
            panel(d, (bx0, ly - 32, bx0 + tw + 30, ly + 32), fill=(6, 8, 16, int(190 * al / 255)), outline=col + (al,), r=12)
            d.text((bx0 + 15, ly), sub, font=fnt, fill=WHITE + (al,), anchor="lm")
    for (txt, fi, fo, col, y) in TAGS:
        if fi <= f <= fo + 8:
            k = min(back((f - fi) / 10.0), 1 - ease((f - fo) / 8.0))
            if k <= 0: continue
            size = int((84 if len(txt) < 16 else 66) * (0.75 + 0.25 * k)); fnt = font(ANTON, size)
            shown = txt.replace("\u2260", "=")                      # Anton has no "not equal" glyph: draw "=" and strike it through
            tw = d.textlength(shown, font=fnt)
            panel(d, (W / 2 - tw / 2 - 34, y - 62, W / 2 + tw / 2 + 34, y + 62), fill=col + (int(230 * c01(k)),), r=16)
            d.text((W / 2, y), shown, font=fnt, fill=(255, 255, 255, int(255 * c01(k))), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 150))
            if "\u2260" in txt:
                i0 = txt.index("\u2260"); x0 = W / 2 - tw / 2 + d.textlength(shown[:i0], font=fnt); wq = d.textlength("=", font=fnt)
                cx = x0 + wq / 2; a_ = int(255 * c01(k))
                d.line((cx - wq * 0.55, y + size * 0.55, cx + wq * 0.55, y - size * 0.55), fill=(0, 0, 0, a_), width=int(size * 0.20))
                d.line((cx - wq * 0.55, y + size * 0.55, cx + wq * 0.55, y - size * 0.55), fill=(230, 30, 30, a_), width=int(size * 0.11))
    # science comparison (scene 7): tank info cards + object labels
    if 1480 <= f <= 1680:
        k = ease((f - 1480) / 14.0)
        aw, al = ANCH.get(f, {}).get("water"), ANCH.get(f, {}).get("lava")
        for a, name, rows, col in ((aw, "WATER", ("DENSITY ≈ 1,000 kg/m³", "VISCOSITY ≈ 0.001 Pa·s"), CYN), (al, "LAVA", ("DENSITY ≈ 2,600 kg/m³", "VISCOSITY ≈ 100–100,000+ Pa·s"), ORG)):
            if not a: continue
            x = min(W - 440, max(20, a[0] * W + 30)); y = a[1] * H
            if k <= 0: continue
            panel(d, (x, y - 70, x + 420, y + 78), fill=(6, 8, 16, int(200 * k)), outline=col + (int(255 * k),), r=14)
            d.text((x + 18, y - 40), name, font=font(ANTON, 40), fill=col + (int(255 * k),), anchor="lm")
            d.text((x + 18, y + 4), rows[0], font=font(MONT, 22, "Bold"), fill=WHITE + (int(255 * k),), anchor="lm")
            d.text((x + 18, y + 40), rows[1], font=font(MONT, 22, "Bold"), fill=WHITE + (int(255 * k),), anchor="lm")
        if 1500 <= f <= 1590 or 1596 <= f <= 1680:
            steel = f >= 1596
            for key, txt in ((("steel_w" if steel else "ball_w"), "STEEL 7,800 kg/m³" if steel else "BODY ≈ 985 kg/m³"), (("steel_l" if steel else "ball_l"), "STEEL 7,800 kg/m³" if steel else "BODY ≈ 985 kg/m³")):
                a = ANCH.get(f, {}).get(key)
                if a and a[2] > 0:
                    px, py = a[0] * W, a[1] * H; fnt = font(MONT, 26, "ExtraBold"); tw = d.textlength(txt, font=fnt)
                    d.line((px, py, px - 90, py - 36), fill=WHITE + (200,), width=3)
                    panel(d, (px - 90 - tw - 24, py - 60, px - 90, py - 12), fill=(6, 8, 16, 200), outline=YEL + (255,), r=8)
                    d.text((px - 90 - tw - 12, py - 36), txt, font=fnt, fill=WHITE, anchor="lm")

def draw_subs(ov, f):
    t = (f - 1) / 30.0; cur = None
    for (s, e, c) in CHUNKS:
        if s - 0.05 <= t < e: cur = (s, e, c); break
    if not cur: return
    s, e, c = cur; d = ImageDraw.Draw(ov)
    k = back((t - s + 0.05) / 0.16, 2.2); size = int(82 * (0.82 + 0.18 * k)); fnt = font(MONT, size, "Black")
    toks = [w["w"].upper() for w in c]; sp = d.textlength(" ", font=fnt); ws_ = [d.textlength(x, font=fnt) for x in toks]
    lines = [list(range(len(toks)))]
    if sum(ws_) + sp * (len(toks) - 1) > W - 110:
        cut = (len(toks) + 1) // 2; lines = [list(range(cut)), list(range(cut, len(toks)))]
    y = 1300 - (len(lines) - 1) * 48
    for ln in lines:
        lw = sum(ws_[i] for i in ln) + sp * (len(ln) - 1); x = W / 2 - lw / 2
        for i in ln:
            w = c[i]; nxt = c[i + 1]["s"] if i + 1 < len(c) else e
            active = w["s"] - 0.04 <= t < nxt
            key = re.sub(r"[^\w-]", "", w["w"].lower()) in KEYWORDS
            col = YEL if active else (ORG if key else WHITE)
            if active: d.rounded_rectangle((x - 10, y - size * 0.62, x + ws_[i] + 10, y + size * 0.62), radius=12, fill=(0, 0, 0, 125))
            d.text((x, y), toks[i], font=fnt, fill=col, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0))
            x += ws_[i] + sp
        y += size * 1.16

_last = {}
def compose(f):
    zoom, shift = 1.0, (0, 0)
    if 73 <= f <= 90:
        zoom = 1.04; amp = 14 * max(0, 1 - (f - 73) / 17.0); shift = (amp * math.sin(f * 5.3), amp * math.cos(f * 4.1))
    if 1263 <= f <= 1275:
        zoom = 1.04; amp = 10 * (1 - (f - 1263) / 12.0); shift = (amp * math.sin(f * 6.1), amp * math.cos(f * 5.0))
    base = load_frame(f, zoom, shift)
    for cb in CUTS:
        if cb <= f < cb + 6 and cb != 151 or (cb == 151 and 151 <= f < 157):
            prev = load_frame(cb - 1)
            base = Image.blend(prev, base, ease((f - cb + 1) / 7.0)); break
    a = fx(base, f)
    fl = flash(f)
    if fl > 0: a = a * (1 - fl) + np.array([1.0, 0.85, 0.65], np.float32) * fl
    if f >= 1776: a = a * (1 - ease((f - 1776) / 22.0))          # clean fade to black
    im = to_img(a).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hook(ov, f); draw_hud(ov, f); draw_labels(ov, f); draw_subs(ov, f)
    if f >= 1776:
        al = 1 - ease((f - 1776) / 22.0); ov.putalpha(ov.getchannel("A").point(lambda v: int(v * al)))
    im.alpha_composite(ov)
    return im.convert("RGB")

if __name__ == "__main__":
    if "--test" in sys.argv:
        os.makedirs(V + "previews/comp", exist_ok=True)
        for f in [int(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]:
            compose(f).save(f"{V}previews/comp/{f:04d}.jpg", quality=88)
        print("ok")
    elif "--encode" in sys.argv:
        out = V + "out/video_noaudio.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                              "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(1, NF + 1):
            p.stdin.write(compose(f).tobytes())
            if f % 100 == 0: print("frame", f, flush=True)
        p.stdin.close(); p.wait(); print("wrote", out)
