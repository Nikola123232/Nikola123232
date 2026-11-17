"""F1 2026 grid: youngest -> oldest. Rebuilds the user's reference layout (no US-flag background) from the portraits in the reference video.
usage: build.py --test t1,t2,...   (preview frames to age/frames)   |   build.py --encode (full video with the reference audio)"""
import sys, os, math, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/user/Nikola123232/age")
from inpaint import diffuse
HERE = "/home/user/Nikola123232/age/"; W, H = 1280, 720; FPS = 30
REF = [p for p in os.listdir("/root/.claude/uploads/164b86a1-ee5f-5ccd-bad4-ded5aa95eb0d/") if p.endswith(".mov")][0]
REF = "/root/.claude/uploads/164b86a1-ee5f-5ccd-bad4-ded5aa95eb0d/" + REF
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; FMB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def font(p, s): return ImageFont.truetype(p, s)
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# rank order: youngest (1) -> oldest (22).  (src pair index, side) = where the portrait sits in the reference video
ORDER = [
    ("Lindblad", (4, "L"), "RACING BULLS", "LIN", (2007, 8, 8)), ("Antonelli", (9, "R"), "MERCEDES", "ANT", (2006, 8, 25)),
    ("Bearman", (5, "R"), "HAAS", "BEA", (2005, 5, 8)), ("Câmara", (1, "R"), "HAAS", "CAM", (2005, 5, 5)),
    ("Bortoleto", (2, "R"), "AUDI", "BOR", (2004, 10, 14)), ("Hadjar", (7, "L"), "RED BULL RACING", "HAD", (2004, 9, 28)),
    ("Colapinto", (2, "L"), "ALPINE", "COL", (2003, 5, 27)), ("Lawson", (6, "R"), "RACING BULLS", "LAW", (2002, 2, 11)),
    ("Piastri", (7, "R"), "MCLAREN", "PIA", (2001, 4, 6)), ("Norris", (9, "L"), "MCLAREN", "NOR", (1999, 11, 13)),
    ("Stroll", (0, "L"), "ASTON MARTIN", "STR", (1998, 10, 29)), ("Russell", (10, "L"), "MERCEDES", "RUS", (1998, 2, 15)),
    ("Leclerc", (8, "R"), "FERRARI", "LEC", (1997, 10, 16)), ("Verstappen", (10, "R"), "RED BULL RACING", "VER", (1997, 9, 30)),
    ("Albon", (4, "R"), "WILLIAMS", "ALB", (1996, 3, 23)), ("Gasly", (5, "L"), "ALPINE", "GAS", (1996, 2, 7)),
    ("Sainz", (6, "L"), "WILLIAMS", "SAI", (1994, 9, 1)), ("Pérez", (1, "L"), "CADILLAC", "PER", (1990, 1, 26)),
    ("Bottas", (0, "R"), "CADILLAC", "BOT", (1989, 8, 28)), ("Hülkenberg", (3, "R"), "AUDI", "HUL", (1987, 8, 19)),
    ("Hamilton", (8, "L"), "FERRARI", "HAM", (1985, 1, 7)), ("Alonso", (3, "L"), "ASTON MARTIN", "ALO", (1981, 7, 29)),
]
RACE = (2026, 11, 21)
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
def age(b): return RACE[0] - b[0] - ((RACE[1], RACE[2]) < (b[1], b[2]))
# sanity: strictly youngest -> oldest
for i in range(21): assert ORDER[i][4] > ORDER[i + 1][4], (ORDER[i][0], ORDER[i + 1][0])
assert len(ORDER) == 22 and len({o[0] for o in ORDER}) == 22
def suffix(n): return "TH" if 10 <= n % 100 <= 20 else {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")

# ------------------------------------------------------------------ 1. clean source frames (remove flag, logo, numbers, tables)
RECTS = [(36, 40, 98, 92), (425, 358, 565, 448), (722, 358, 850, 448), (520, 60, 610, 168), (520, 522, 610, 690), (662, 60, 748, 168), (662, 522, 748, 690)]
def load_clean(k):
    cp = HERE + f"work/clean{k}.npy"
    if os.path.exists(cp): return np.load(cp)
    im = np.asarray(Image.open(HERE + f"work/pair{k}.png").convert("RGB")).astype(np.float32)
    rects = list(RECTS) + ([(214, 652, 312, 684)] if k == 10 else [])
    for (x0, y0, x1, y1) in rects:
        pad = 4; X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + (0 if x0 == 722 else pad)), min(H, y1 + pad)
        sub = im[Y0:Y1, X0:X1].copy(); m = np.zeros(sub.shape[:2], bool); m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
        im[Y0:Y1, X0:X1] = diffuse(sub, m, iters=350)
    for (x0, x1, y0, y1, sx0, sx1) in ((16, 36, 236, 445, 36, 44), (1242, 1264, 236, 452, 1232, 1242)):      # vertical team labels at the margins (flag-free fill)
        im[y0:y1, x0:x1] = im[y0:y1, sx0:sx1].mean(axis=1, keepdims=True)
    np.save(cp, im); return im

# ------------------------------------------------------------------ 2. own background (no flag): dark navy panel with soft diagonal sheen, dark red bands
def make_bg():
    bg = np.zeros((H, W, 3), np.float32); bg[:] = (11, 13, 22)
    y = np.arange(H)[:, None]; top = np.clip(1 - y / 20.0, 0, 1); bot = np.clip((y - 700) / 20.0, 0, 1)
    band = np.maximum(top, bot)[..., None] * np.array([48, 12, 20], np.float32)
    bg = bg + band
    pan = np.zeros((H, W), bool); pan[20:700, 15:1265] = True
    bg[pan] = (24, 26, 39)
    yy, xx = np.mgrid[0:H, 0:W]; d = (xx - 0.55 * yy) % 340
    sheen = np.where(d < 70, 3.0, 0.0)[..., None]; bg[pan] += sheen[pan]
    return bg
BG = make_bg()

def slot_image(k, side, dst):
    """Return a (H,W,3) float layer + (H,W) alpha holding the portrait from src pair k/side placed into the dst slot ('L' or 'R')."""
    src = load_clean(k); SL = {"L": (16, 616), "R": (660, 1264)}; sx0, sx1 = SL[side]; dx0, dx1 = SL[dst]
    layer = np.zeros((H, W, 3), np.float32); alpha = np.zeros((H, W), np.float32)
    shift = 0 if side == dst else (756 if dst == "R" else -756)
    xs0, xs1 = max(sx0, dx0 - shift), min(sx1, dx1 - shift)
    layer[20:700, xs0 + shift:xs1 + shift] = src[20:700, xs0:xs1]; alpha[20:700, xs0 + shift:xs1 + shift] = 1
    # background filler where the shifted content does not reach the slot: use this panel's own edge colour per row
    if shift:
        edge = src[20:700, sx0 + 6:sx0 + 40].mean(axis=1)                       # (680,3) clean background colour per row
        gap = np.ones((H, W), bool); gap[:, :dx0] = False; gap[:, dx1:] = False; gap &= (alpha < 0.5); gap[:20] = False; gap[700:] = False
        for y in range(20, 700): layer[y][gap[y]] = edge[y - 20]
        alpha[gap] = 1
        # feather the seam
        for xseam in ((dx0 - shift + sx0 - 0, ) if False else ()): pass
        cols = np.where(alpha[400] > 0.5)[0]
        seam = (xs0 + shift) if dst == "R" else (xs1 + shift)
        for i in range(36):
            x = seam + (i if dst == "R" else -i - 1)
            if dx0 <= x < dx1:
                t = i / 36.0; row = layer[20:700, x]; mixc = edge * (1 - t) + src[20:700, min(max(x - shift, sx0), sx1 - 1)] * t if dst == "R" else edge * (1 - t) + src[20:700, min(max(x - shift, sx0), sx1 - 1)] * t
                layer[20:700, x] = mixc
    return layer, alpha

TEAM_LABEL = {"MCLAREN": "MCLAREN"}
def make_card(pair_i):
    """pair_i 0..10 -> (base RGB array, overlay RGBA PIL image). rank numbers 2*pair_i+1 (left) and 2*pair_i+2 (right)."""
    base = BG.copy(); L = ORDER[2 * pair_i]; R = ORDER[2 * pair_i + 1]
    for (drv, dst) in ((L, "L"), (R, "R")):
        layer, al = slot_image(drv[1][0], drv[1][1], dst); a = al[..., None]; base = base * (1 - a) + layer * a
    g = 1 - 0.55 * np.clip((np.arange(H) - 644) / 40.0, 0, 1)[:, None, None]; g[:, :] = g; sl = np.zeros((H, W, 1), np.float32); sl[:, 16:616] = 1; sl[:, 660:1264] = 1
    base = base * (1 - sl + sl * g)                                                         # soft shade under the age line so it stays readable
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    # centre strip: red bars with diagonal cuts + vertical caption
    d.rectangle((613, 20, 660, 700), fill=(14, 16, 26, 255))
    red = (255, 44, 56, 255)
    d.polygon([(618, 0), (634, 0), (634, 244), (618, 226)], fill=red); d.polygon([(636, 0), (652, 0), (652, 246), (636, 232)], fill=red)
    d.polygon([(618, 486), (634, 502), (634, 720), (618, 720)], fill=red); d.polygon([(636, 498), (652, 512), (652, 720), (636, 720)], fill=(200, 30, 44, 255))
    cap = Image.new("RGBA", (200, 18), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); txt = "BY AGE"; x = 0
    for ch in txt: cd.text((x, 2), ch, font=font(FMB, 11), fill=(214, 186, 110, 255)); x += 12
    cap = cap.crop((0, 0, x, 18)).rotate(-90, expand=True); im.alpha_composite(cap, (624, 368 - cap.size[1] // 2 + 6))
    # team labels on the outer margins
    for (drv, dst) in ((L, "L"), (R, "R")):
        lab = drv[2]; t = Image.new("RGBA", (260, 16), (0, 0, 0, 0)); td = ImageDraw.Draw(t); x = 0
        for ch in lab: td.text((x, 1), ch, font=font(FB, 11), fill=(240, 240, 248, 235)); x += td.textlength(ch, font=font(FB, 11)) + 3.2
        t = t.crop((0, 0, int(x), 16)); t = t.rotate(90 if dst == "L" else -90, expand=True)
        im.alpha_composite(t, (4 if dst == "L" else 1260, 340 - t.size[1] // 2))
    base_img = im.convert("RGB")
    # overlay: rank numbers, ages, revealed-so-far tables
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    for (drv, dst, rank) in ((L, "L", 2 * pair_i + 1), (R, "R", 2 * pair_i + 2)):
        xe = 555 if dst == "L" else 848; sf = suffix(rank); fs = font(FB, 26); fn = font(FB, 84); sw = o.textlength(sf, font=fs)
        o.text((xe - sw - 3, 437), str(rank), font=fn, fill=(246, 246, 255, 255), anchor="rs"); o.text((xe - sw, 384), sf, font=fs, fill=(246, 246, 255, 255), anchor="ls")
        cx = 262 if dst == "L" else 1018; b = drv[4]; a_ = age(b)
        s1 = f"AGE {a_}"; s2 = f"   ·   {b[2]:02d} {MONTHS[b[1] - 1]} {b[0]}"; f1 = font(FMB, 15); f2 = font(FM, 14); w1, w2 = o.textlength(s1, font=f1), o.textlength(s2, font=f2)
        x0 = cx - (w1 + w2) / 2; o.text((x0, 676), s1, font=f1, fill=(250, 250, 255, 255), anchor="ls"); o.text((x0 + w1, 676), s2, font=f2, fill=(176, 182, 204, 255), anchor="ls")
        # revealed so far (lower ranks), odd on the left, even on the right, filling the last slots
        rev = [r for r in range(1, rank) if (r % 2 == 1) == (dst == "L")]
        slots = [71, 96, 121, 146, 537, 562, 587, 612, 637, 662]; n = len(rev); bx = 524 if dst == "L" else 660
        for j, r in enumerate(rev):
            y = slots[10 - n + j]
            o.rectangle((bx, y - 10, bx + 82, y + 10), fill=(12, 14, 24, 215), outline=(52, 56, 74, 255))
            o.text((bx + 8, y + 5), f"{r}", font=font(FM, 12), fill=(150, 156, 180, 255), anchor="ls"); o.text((bx + 42, y + 5), ORDER[r - 1][3], font=font(FMB, 12), fill=(232, 234, 246, 255), anchor="ls")
    return np.asarray(base_img).astype(np.float32), ov

def make_title():
    im = Image.fromarray(np.clip(BG, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im); cx = W // 2
    def ctext(y, s, f, fill, sp=0.0):
        w = sum(d.textlength(ch, font=f) + sp for ch in s) - sp; x = cx - w / 2
        for ch in s: d.text((x, y), ch, font=f, fill=fill, anchor="ls"); x += d.textlength(ch, font=f) + sp
    ctext(188, "FORMULA 1  /  2026 GRID", font(FMB, 24), (176, 184, 208, 255), 1.5)
    f = 84
    while d.textlength("YOUNGEST TO OLDEST", font=font(FB, f)) > 960: f -= 2
    ctext(312, "YOUNGEST TO OLDEST", font(FB, f), (244, 245, 252, 255))
    d.rectangle((527, 355, 753, 360), fill=(255, 50, 62, 255))
    ctext(424, "ALL 22 DRIVERS BY AGE", font(FB, 36), (236, 238, 248, 255))
    ctext(496, "1ST = YOUNGEST   →   22ND = OLDEST", font(FMB, 19), (182, 190, 212, 255), 0.5)
    ctext(532, "AGES ON 21 NOVEMBER 2026  ·  LAS VEGAS GP WEEKEND", font(FM, 17), (160, 168, 192, 255), 0.5)
    return np.asarray(im.convert("RGB")).astype(np.float32)

TITLE = make_title(); CARDS = [make_card(k) for k in range(11)]
def card_full(k, alpha=1.0):
    base, ov = CARDS[k]; im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    if alpha > 0:
        o = ov.copy()
        if alpha < 1: o.putalpha(o.getchannel("A").point(lambda v: int(v * alpha)))
        im.alpha_composite(o)
    return np.asarray(im.convert("RGB")).astype(np.float32)
FULL = [card_full(k) for k in range(11)]
YY, XX = np.mgrid[0:H, 0:W]
def frame(t):
    if t < 6.0: seg, lt, prev, cur = 0, t, TITLE, TITLE
    else:
        k = min(10, int((t - 6) // 6)); lt = (t - 6) - 6 * k; prev = TITLE if k == 0 else FULL[k - 1]
        a = ease((lt - 0.45) / 0.45); cur = card_full(k, a) if a < 1 else FULL[k]
    out = cur
    if t >= 6.0 and lt < 0.5:
        p = ease(lt / 0.5); xb = -260 + (W + 520) * p; edge = XX - 0.32 * (YY - H / 2)
        m = (edge < xb)[..., None]; out = np.where(m, cur, prev)
        dist = np.abs(edge - xb); glow = np.clip(1 - dist / 9.0, 0, 1)[..., None] * np.array([255, 50, 60], np.float32); out = np.maximum(out, glow * (1 - abs(p - 0.5) * 0.2))
    if t > 72.9 - 0.45: out = out * max(0.0, (72.9 - t) / 0.45)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

if __name__ == "__main__":
    if "--test" in sys.argv:
        os.makedirs(HERE + "frames", exist_ok=True)
        for t in [float(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]: frame(t).save(HERE + f"frames/t{t:05.1f}.png")
        print("ok")
    elif "--encode" in sys.argv:
        out = HERE + "F1_2026_youngest_to_oldest.mp4"; dur = 72.9
        p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-i", REF,
                              "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                              "-t", f"{dur:.3f}", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(int(round(dur * FPS))):
            p.stdin.write(frame(i / FPS).tobytes())
            if i % 300 == 0: print("frame", i, flush=True)
        p.stdin.close(); p.wait(); print("wrote", out)
