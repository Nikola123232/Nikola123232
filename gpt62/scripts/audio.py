"""Original music bed + SFX (numpy synthesis), ducked under VO -> public/mix.wav (48 kHz stereo)."""
import json, re, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
SR = 48000; rng = np.random.default_rng(7)
t = json.load(open("src/timeline.json")); T = t["total"]; N = int(T * SR)
vo, vsr = sf.read("public/vo.wav"); vo = resample_poly(vo, SR, vsr)[:N]; vo = np.pad(vo, (0, N - len(vo)))
f2s = lambda fr: fr / 30
s2f = lambda s: round(s * 30)
cue = lambda c: t["cues"][c][0]
def word(c, w, nth=0):
    L = next(l for l in t["lines"] if l["cue"] == c)
    hits = [x for x in L["words"] if re.sub(r"[^a-z0-9$.-]", "", x["w"].lower()).startswith(w)]
    return hits[nth]["s"]
lp = lambda x, fc, o=2: sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
hp = lambda x, fc, o=2: sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], "band", fs=SR, output="sos"), x)
env = lambda n, a, r: np.minimum(np.linspace(0, 1, n) * n / max(1, a), 1) * np.exp(-np.arange(n) / max(1, r))

# ---------------- music: warm pad + soft pulse, 96 bpm, i–VI–III–VII in A minor
bpm = 96; beat = 60 / bpm; bar = 4 * beat
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G (midi)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
music = np.zeros((N, 2))
tt = np.arange(N) / SR
pad = np.zeros(N)
for b in range(int(T / bar) + 1):
    a, e = int(b * bar * SR), min(N, int((b + 1) * bar * SR) + int(0.4 * SR))
    if a >= N: break
    seg = tt[a:e] - b * bar; ch = chords[b % 4]; s = np.zeros(e - a)
    for m in ch + [ch[0] - 12]:
        fr = mtof(m)
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * fr * (1 + det / 100) * seg) * 0.5 + 0.18 * np.sin(2 * np.pi * 2 * fr * seg)
    w = np.minimum(1, seg / 0.6) * np.minimum(1, (bar + 0.4 - seg) / 0.6)
    pad[a:e] += s * w * 0.05
pad = lp(pad, 1800)
# pulse: muted kick + shaker on offbeats
pulse = np.zeros(N)
for k in range(int(T / beat)):
    p = int(k * beat * SR); n = int(0.25 * SR)
    if p + n >= N: break
    ph = np.cumsum(2 * np.pi * (45 + 70 * np.exp(-np.arange(n) / (0.03 * SR))) / SR)
    pulse[p:p + n] += np.sin(ph) * np.exp(-np.arange(n) / (0.07 * SR)) * 0.32
    q = int((k + 0.5) * beat * SR); m = int(0.06 * SR)
    if q + m < N: pulse[q:q + m] += hp(rng.normal(0, 1, m), 6000) * np.exp(-np.arange(m) / (0.012 * SR)) * 0.05
# arrangement: intensity per section
inten = np.ones(N) * 0.8
def ramp(a, b, v0, v1):
    i, j = int(a * SR), int(b * SR); inten[i:j] = np.linspace(v0, v1, j - i)
secs = t["sections"]
inten[:] = 0.75
inten[: int(secs["launch"][0] * SR)] = 1.0          # cold open: full pulse
ramp(secs["verdict"][0] - 1, secs["verdict"][0] + 2, 0.75, 1.0)
inten[int(secs["verdict"][1] * SR):] = 1.0
mono = pad + pulse * inten
music[:, 0] = mono; music[:, 1] = np.roll(mono, int(0.012 * SR)) * 0.96 + pad * 0.04
# fade in/out
fade = np.minimum(1, tt / 0.8) * np.minimum(1, (T - tt) / 2.5).clip(0, 1)
music *= fade[:, None]
# sidechain duck from VO envelope
ve = np.abs(vo); win = int(0.05 * SR); ve = np.convolve(ve, np.ones(win) / win, "same")
duck = 1 - 0.72 * np.clip(ve / 0.04, 0, 1)
duck = np.convolve(duck, np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
music *= duck[:, None] * 0.55

# ---------------- SFX
sfx = np.zeros((N, 2))
def place(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < 0 or i >= N: return
    sfx[i:j, 0] += sig[: j - i] * gain * (1 - max(0, pan)); sfx[i:j, 1] += sig[: j - i] * gain * (1 + min(0, pan))
def whoosh(d=0.55):
    n = int(d * SR); x = rng.normal(0, 1, n); out = np.zeros(n); step = n // 24
    for k in range(24):
        a, b = k * step, (k + 1) * step if k < 23 else n
        fc = 300 + 5200 * np.sin(np.pi * k / 24) ** 2
        out[a:b] = bp(x[a:b + 2000][: b - a] if b - a > 0 else x[a:b], fc * 0.6, min(fc * 1.6, 20000))
    return out * np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.35
def tick(fr=1800):
    n = int(0.12 * SR); a = np.arange(n) / SR
    return (np.sin(2 * np.pi * fr * a) + 0.4 * np.sin(2 * np.pi * fr * 2.01 * a)) * np.exp(-a / 0.025) * 0.28
def reveal():
    n = int(0.6 * SR); a = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * a) * g for f, g in [(880, 0.5), (1320, 0.3), (1760, 0.2)])
    thump = np.sin(2 * np.pi * (60 + 80 * np.exp(-a / 0.02)) * a) * np.exp(-a / 0.08)
    return (s * np.exp(-a / 0.18) * 0.22 + thump * 0.5)
def thock():
    n = int(0.5 * SR); a = np.arange(n) / SR
    body = np.sin(2 * np.pi * (90 + 120 * np.exp(-a / 0.015)) * a) * np.exp(-a / 0.09)
    click = hp(rng.normal(0, 1, n), 2500) * np.exp(-a / 0.004)
    shimmer = np.sin(2 * np.pi * 1320 * a) * np.exp(-a / 0.25) * 0.15
    return body * 0.6 + click * 0.15 + shimmer
def riser(d=1.2):
    n = int(d * SR); a = np.arange(n) / SR; x = rng.normal(0, 1, n)
    return hp(x, 1500) * (a / d) ** 2 * 0.18
def pop_():
    n = int(0.09 * SR); a = np.arange(n) / SR
    return np.sin(2 * np.pi * (500 + 900 * a / 0.09) * a) * np.exp(-a / 0.02) * 0.18

order = ["cold", "launch", "bench", "web", "bug", "slides", "verdict"]
for p, s in zip(order, order[1:]):
    b = (s2f(secs[p][1]) + s2f(secs[s][0])) / 2 / 30
    place(whoosh(), b - 0.32, 0.9)
# cold open
place(whoosh(0.7), 0.0, 0.7)
place(reveal(), word("gap", "half") - 0.2, 0.8, -0.3)
place(tick(2200), word("gap", "point"), 0.8)
place(reveal(), cue("cost") + 0.05, 0.8, 0.3)
place(tick(2200), word("cost", "fifth"), 0.8)
place(riser(1.0), cue("ask") - 0.9, 0.7); place(thock(), cue("ask"), 0.7)
# launch
for c in ["astra", "sol"]: place(whoosh(0.4), cue(c) - 0.25, 0.55)
place(tick(), word("price", "$8"), 0.6); place(tick(), word("price", "$40"), 0.6); place(tick(1500), word("pricesol", "$2"), 0.6)
place(thock(), word("quarter", "quarter"), 0.5)
# bench
place(thock(), word("merge", "merge") + 0.2, 0.55)
place(riser(0.8), word("astrascore", "44") - 0.8, 0.6)
place(reveal(), word("astrascore", "44"), 0.8, -0.2); place(reveal(), word("solscore", "43"), 0.8, 0.2)
place(whoosh(0.6), cue("gapnum") - 0.1, 0.6); place(tick(2400), cue("gapnum") + 0.6, 0.8)
place(reveal(), word("astracost", "$5"), 0.75, -0.2); place(reveal(), word("solcost", "$1"), 0.75, 0.2)
place(thock(), word("fifth", "fifth"), 0.6)
place(whoosh(0.5), cue("source") - 0.3, 0.5)
for c in ["cav1", "cav2"]: place(pop_(), cue(c), 1.0)
# scenarios
for w in ["hero", "menu", "opening", "contact"]: place(pop_(), word("webparts", w), 0.9)
place(thock(), cue("webpick"), 0.7); place(thock(), cue("bugpick"), 0.7); place(thock(), cue("slidepick"), 0.7)
for w in ["cart", "currency", "discount"]: place(tick(1300), word("chain", w), 0.6)
place(tick(900), word("coupon", "currency"), 0.8)
place(whoosh(0.3), cue("slidecomp") - 0.1, 0.6)
for w in ["fixed", "locked", "legal"]: place(pop_(), word("template", w), 0.9)
place(tick(700), cue("wrongnum") + 0.3, 0.7)
# verdict
for w in ["bakery", "internal", "routine"]: place(pop_(), word("vsol", w), 0.9)
for w in ["cross", "client"]: place(pop_(), word("vastra", w), 0.9)
for w in ["connected", "check", "mistake"]: place(tick(1600), word("r2", w), 0.6)
place(reveal(), cue("end"), 0.7, -0.2); place(reveal(), word("end", "astra"), 0.7, 0.2)

mix = music + sfx * 0.55
mix[:, 0] += vo; mix[:, 1] += vo
peak = np.abs(mix).max(); mix = mix / peak * 0.89 if peak > 0.89 else mix
sf.write("public/mix.wav", mix.astype(np.float32), SR)
print("mix", mix.shape[0] / SR, "s, peak", round(float(np.abs(mix).max()), 3))
