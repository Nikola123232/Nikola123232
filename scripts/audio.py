"""Procedural sound design + music for the 60 s short (all synthesised, original).
Outputs audio/sfx.wav, audio/music.wav, audio/mix.wav (48 kHz stereo, VO ducking applied)."""
import json, math, numpy as np, soundfile as sf
from scipy import signal

SR = 48000
DUR = 60.5
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR
ROOT = "/home/user/Nikola123232/"


def F(frame):  # video frame -> seconds
    return (frame - 1) / 30.0


def env_adsr(n, a, d, s, r, sl=0.6):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    s = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, sl, max(d, 1)), np.full(s, sl), np.linspace(sl, 0, max(r, 1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)


def place(buf, x, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    x = x[: N - i] if i >= 0 else x[-i:]
    i = max(i, 0)
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.414
    buf[i:i + len(x), 1] += x * gain * r * 1.414


def noise(n):
    return rng.standard_normal(n)


def sweep_filter_noise(dur, f_start, f_end, q=1.5, shape=None):
    """Band-pass noise with a sweeping centre frequency (processed in short blocks)."""
    n = int(dur * SR)
    x = noise(n)
    out = np.zeros(n)
    blk = 1024
    zi = None
    for i in range(0, n, blk):
        u = i / n
        fc = f_start * (f_end / f_start) ** u
        bw = fc / q
        lo, hi = max(30, fc - bw / 2), min(SR / 2 - 200, fc + bw / 2)
        b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band')
        if zi is None or len(zi) != max(len(a), len(b)) - 1:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi)
        out[i:i + blk] = y
    if shape is not None:
        out *= shape(np.linspace(0, 1, n))
    return out / (np.abs(out).max() + 1e-9)


# ============================================================ SFX
sfx = np.zeros((N, 2))

# ---- engine: V6 turbo-hybrid. rpm curve over video time (scene 1 + scene 2 until impact)
T_IMP_VID = F(357)
def rpm_at(tt):
    if tt < 3.3:
        return 11300 + 400 * tt / 3.3
    if tt < 3.42:
        return 11700 - 1300 * (tt - 3.3) / 0.12        # upshift
    if tt < 8.35:
        return 10400 + 1500 * min(1, (tt - 3.42) / 4.0)
    if tt < 8.55:  # braking downshift blips
        return 11900 - 2500 * (tt - 8.35) / 0.2 + 1500 * (math.sin((tt - 8.35) * 60) > 0.6)
    if tt < 10.6:  # rear snaps: wheelspin flare, then lift
        return 12200 - 2200 * min(1, (tt - 8.6) / 1.6) + 400 * math.sin(tt * 23)
    return 9000
eng_n = int(T_IMP_VID * SR) + int(0.3 * SR)
tt = np.arange(eng_n) / SR
rpm = np.array([rpm_at(x) for x in tt[::48]])
rpm = np.interp(tt, tt[::48], rpm)
# slow-motion: pitch dives as time slows (10.6 -> 11.0) to a deep rumble
slow = np.clip((tt - 10.6) / 0.4, 0, 1)
rate = 1 - 0.85 * (slow * slow * (3 - 2 * slow))
f0 = rpm / 60 * 3 * rate          # firing frequency (3 per rev on a V6)
ph = 2 * np.pi * np.cumsum(f0) / SR
eng = np.zeros(eng_n)
for k, a in [(0.5, 0.35), (1, 1.0), (1.5, 0.25), (2, 0.55), (3, 0.35), (4, 0.22), (5, 0.12), (6, 0.08), (8, 0.05)]:
    eng += a * np.sin(k * ph + rng.uniform(0, 6))
eng += 0.5 * lp(noise(eng_n), 3000) * (0.6 + 0.4 * np.sin(ph))     # combustion grit
eng += 0.15 * hp(noise(eng_n), 6000) * (np.sin(ph * 0.5) > 0.3)       # turbo/mechanical hiss
eng = np.tanh(eng * 0.9)
eng = lp(eng, 7000)
eng_env = np.ones(eng_n)
eng_env *= np.clip(tt / 0.15, 0, 1)
eng_env *= np.where(tt > T_IMP_VID, np.exp(-(tt - T_IMP_VID) * 30), 1)
eng_env *= np.where((tt > 3.5) & (tt < 8.0), 0.8, 1.0)              # side tracking shot slightly further
eng_env *= np.where(tt > 10.6, 0.7, 1.0)
eng *= eng_env
eng /= np.abs(eng).max()
place(sfx, eng, 0.0, 0.42)
# pass-by whoosh at the overtake in 1A (~3.4 s)
place(sfx, sweep_filter_noise(1.2, 400, 2500, 1.2, lambda u: np.sin(np.pi * u) ** 2), 2.8, 0.25, -0.4)

# ---- tyre screech + lock-up
scr = sweep_filter_noise(2.05, 1400, 900, 3.0, lambda u: np.clip(u * 8, 0, 1) * (1 - u) ** 0.3)
scr += 0.6 * sweep_filter_noise(2.05, 2600, 2000, 4.0, lambda u: np.clip(u * 8, 0, 1))
scr *= 1 + 0.3 * np.sin(np.arange(len(scr)) / SR * 2 * np.pi * 13)
place(sfx, scr / np.abs(scr).max(), 8.55, 0.24, 0.1)
# spark crackle
for i in range(240):
    tc = rng.uniform(8.8, 10.6)
    c = hp(noise(int(0.004 * SR)), 4000) * np.exp(-np.linspace(0, 8, int(0.004 * SR)))
    place(sfx, c, tc, rng.uniform(0.02, 0.06), rng.uniform(-0.5, 0.5))

# ---- slow-motion whoosh (time drop) and impact
place(sfx, sweep_filter_noise(1.6, 3000, 150, 1.5, lambda u: np.sin(np.pi * u) ** 1.5), 10.3, 0.45)
n = int(4.0 * SR); x = np.arange(n) / SR
boom = np.sin(2 * np.pi * (55 * x - 12 * x * x)) * np.exp(-x * 1.4)          # sub drop
boom += 0.6 * lp(noise(n), 180) * np.exp(-x * 2.5)
crack = hp(noise(n), 1500) * np.exp(-x * 9) * 1.2                              # carbon crack
crack += 0.6 * bp(noise(n), 500, 2500) * np.exp(-x * 4)
imp = boom * 0.9 + crack * 0.7
imp = np.tanh(imp * 1.5)
place(sfx, imp / np.abs(imp).max(), T_IMP_VID - 0.02, 0.95)
for i in range(70):   # slowed debris rattles
    tc = T_IMP_VID + rng.uniform(0.05, 3.2)
    ln = int(rng.uniform(0.02, 0.09) * SR)
    c = bp(noise(ln), rng.uniform(300, 900), rng.uniform(1500, 4000)) * np.exp(-np.linspace(0, 6, ln))
    place(sfx, c / (np.abs(c).max() + 1e-9), tc, rng.uniform(0.04, 0.14), rng.uniform(-0.8, 0.8))
n = int(3.5 * SR); x = np.arange(n) / SR
ring = np.sin(2 * np.pi * 3800 * x) * np.exp(-x * 1.0) * np.clip(x / 0.3, 0, 1)
place(sfx, ring, T_IMP_VID + 0.1, 0.035)
for i in range(25):  # settling debris at real speed
    tc = rng.uniform(15.3, 17.5); ln = int(0.03 * SR)
    c = bp(noise(ln), 800, 5000) * np.exp(-np.linspace(0, 6, ln))
    place(sfx, c / np.abs(c).max(), tc, rng.uniform(0.03, 0.08), rng.uniform(-0.8, 0.8))

# ---- ambience: outdoor wind + distant crowd (0-18 s, 56-60 s)
amb = lp(noise(N), 500) * 0.5 + bp(noise(N), 300, 2000) * 0.25 * (1 + 0.3 * np.sin(t_all * 0.7))
amb_env = np.where(t_all < 18, 1.0, 0) * np.clip((18 - t_all) / 0.4, 0, 1) + np.where(t_all > 56, np.clip((t_all - 56) / 0.5, 0, 1), 0)
amb = amb / np.abs(amb).max() * amb_env
sfx[:, 0] += amb * 0.06; sfx[:, 1] += np.roll(amb, 1200) * 0.06

# ---- transition whooshes + flash hit
for fr in (106, 319, 439, 621, 761, 1081, 1191, 1351, 1681):
    place(sfx, sweep_filter_noise(0.7, 600, 4000, 1.3, lambda u: np.sin(np.pi * u) ** 2), F(fr) - 0.4, 0.16, rng.uniform(-0.4, 0.4))
place(sfx, sweep_filter_noise(1.5, 200, 6000, 1.0, lambda u: u ** 2), F(541) - 1.5, 0.3)  # riser into the flash
n = int(1.5 * SR); x = np.arange(n) / SR
hit = np.sin(2 * np.pi * 45 * x) * np.exp(-x * 3) + 0.4 * hp(noise(n), 2000) * np.exp(-x * 12)
place(sfx, hit, F(541), 0.5)

# ---- anatomy: heartbeat 18-45 s, deceleration thuds
def heartbeat(t0, t1, bpm=72, gain=0.35):
    tb = t0
    while tb < t1:
        for off, g in ((0, 1.0), (0.28, 0.7)):
            n = int(0.18 * SR); x = np.arange(n) / SR
            b = np.sin(2 * np.pi * 50 * x) * np.exp(-x * 22) + 0.3 * np.sin(2 * np.pi * 90 * x) * np.exp(-x * 30)
            place(sfx, b, tb + off, gain * g)
        tb += 60 / bpm
heartbeat(18.2, 45.0)
for fr, g in ((690, 0.7), (800, 0.6), (905, 0.6), (1008, 0.55), (1098, 0.9), (1250, 0.5)):
    n = int(1.2 * SR); x = np.arange(n) / SR
    th = np.sin(2 * np.pi * (70 * x - 15 * x * x)) * np.exp(-x * 5) + 0.3 * lp(noise(n), 400) * np.exp(-x * 6)
    place(sfx, th, F(fr), g)
    place(sfx, sweep_filter_noise(0.8, 2500, 300, 1.2, lambda u: np.sin(np.pi * u)), F(fr) - 0.25, 0.18 * g)

# ---- UI blips for callouts (times written by composite.py label schedule)
try:
    labels = json.load(open(ROOT + "renders/label_times.json"))
except Exception:
    labels = []
for (fr, pan) in labels:
    n = int(0.12 * SR); x = np.arange(n) / SR
    b = (np.sin(2 * np.pi * 1760 * x) + 0.5 * np.sin(2 * np.pi * 2640 * x)) * np.exp(-x * 40)
    place(sfx, b, F(fr), 0.07, pan)

# ---- scene 5 assembly clunks + scene 4 chimes
for fr in (1392, 1466, 1470, 1474, 1526, 1556, 1584, 1610, 1645, 1650):
    n = int(0.5 * SR); x = np.arange(n) / SR
    c = np.sin(2 * np.pi * 110 * x) * np.exp(-x * 14) + 0.5 * bp(noise(n), 1500, 5000) * np.exp(-x * 30)
    place(sfx, c, F(fr) - 0.02, 0.4, rng.uniform(-0.3, 0.3))
    place(sfx, sweep_filter_noise(0.5, 500, 3000, 1.5, lambda u: u ** 2), F(fr) - 0.5, 0.1)
for fr in (1166, 1210):
    n = int(1.5 * SR); x = np.arange(n) / SR
    ch = sum(np.sin(2 * np.pi * f * x) * a for f, a in ((880, 1), (1320, 0.6), (1760, 0.3))) * np.exp(-x * 3)
    place(sfx, ch, F(fr), 0.12)

# ---- final title hit
n = int(3.0 * SR); x = np.arange(n) / SR
fin = np.sin(2 * np.pi * 41 * x) * np.exp(-x * 1.2) + 0.5 * lp(noise(n), 250) * np.exp(-x * 2) + 0.25 * hp(noise(n), 3000) * np.exp(-x * 8)
place(sfx, fin, 57.4, 0.7)

# ============================================================ MUSIC (D minor, 100 bpm)
mus = np.zeros((N, 2))
BPM = 100; beat = 60 / BPM
def midi(m):
    return 440 * 2 ** ((m - 69) / 12)
prog = [(50, [62, 65, 69]), (46, [62, 65, 70]), (53, [60, 65, 69]), (48, [60, 64, 67])]  # Dm Bb F C
def chord_at(tm):
    bar = int(tm / (beat * 4))
    return prog[(bar // 2) % 4]

def intensity(tm):
    """Arrangement curve: 0 = silent, 1 = full."""
    pts = [(0, 0.85), (8.3, 0.9), (10.4, 1.0), (10.8, 0.15), (15.0, 0.2), (17.6, 0.5), (18.0, 0.0), (18.4, 0.45),
           (33.0, 0.55), (45.0, 0.6), (45.4, 0.9), (55.5, 1.0), (57.3, 0.6), (60.5, 0.3)]
    xs, ys = zip(*pts)
    return float(np.interp(tm, xs, ys))
inten = np.array([intensity(x) for x in t_all[::480]]); inten = np.interp(t_all, t_all[::480], inten)

def drums_on(tm):
    return (tm < 10.6) or (45.3 < tm < 57.3)

# pads (detuned saws, lowpassed) per 2-bar chord
seg = beat * 8
k = 0
while k * seg < DUR:
    t0 = k * seg
    root, notes = chord_at(t0 + 0.01)
    n = int(seg * SR); x = np.arange(n) / SR
    pad = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.08):
            pad += signal.sawtooth(2 * np.pi * midi(m) * (1 + det / 100) * x) * 0.25
    pad = lp(pad, 1400) * env_adsr(n, 0.6, 0.5, 0, 0.8, 0.8)
    sub = np.sin(2 * np.pi * midi(root - 12) * x) * env_adsr(n, 0.3, 0.3, 0, 0.6, 0.9)
    place(mus, pad * 0.35, t0, 1.0, -0.3)
    place(mus, np.roll(pad, 300) * 0.35, t0, 1.0, 0.3)
    place(mus, sub * 0.4, t0, 1.0)
    # 8th-note pulse bass + arpeggio
    for i in range(16):
        tb = t0 + i * beat / 2
        nb = int(beat / 2 * SR); xb = np.arange(nb) / SR
        bass = signal.sawtooth(2 * np.pi * midi(root - 12) * xb) * np.exp(-xb * 7)
        place(mus, lp(bass, 700) * 0.28, tb, 1.0)
        arp_note = notes[i % 3] + 12 * ((i // 3) % 2)
        pl = np.sin(2 * np.pi * midi(arp_note) * xb) * np.exp(-xb * 9) + 0.3 * np.sin(4 * np.pi * midi(arp_note) * xb) * np.exp(-xb * 14)
        place(mus, pl * 0.12, tb, 1.0, 0.5 if i % 2 else -0.5)
    k += 1
# drums
tb = 0.0
step = 0
while tb < DUR:
    if drums_on(tb):
        nb = int(0.4 * SR); xb = np.arange(nb) / SR
        if step % 4 == 0:
            kick = np.sin(2 * np.pi * (52 * xb + 90 * (1 - np.exp(-xb * 30)) / 30)) * np.exp(-xb * 9)
            place(mus, kick * 0.55, tb, 1.0)
        if step % 8 == 4:
            sn = bp(noise(nb), 800, 6000) * np.exp(-xb * 18) + np.sin(2 * np.pi * 190 * xb) * np.exp(-xb * 25) * 0.5
            place(mus, sn * 0.3, tb, 1.0)
        hh = hp(noise(int(0.05 * SR)), 7000) * np.exp(-np.linspace(0, 10, int(0.05 * SR)))
        place(mus, hh * (0.10 if step % 2 else 0.06), tb, 1.0, 0.3)
    tb += beat / 4; step += 1
mus[:, 0] *= inten; mus[:, 1] *= inten
# tension drone for slow-mo / anatomy
x = t_all
drone = (np.sin(2 * np.pi * 36.7 * x) + 0.5 * np.sin(2 * np.pi * 73.4 * x * 1.002) + 0.2 * lp(noise(N), 200))
dr_env = np.interp(x, [0, 10.6, 11.2, 17.8, 18.2, 44.5, 45.3, 60.5], [0, 0, 1, 1, 0.5, 0.5, 0, 0])
mus[:, 0] += drone * dr_env * 0.18; mus[:, 1] += drone * dr_env * 0.18
mus /= np.abs(mus).max()

# ============================================================ MIX with VO ducking
vo, vsr = sf.read(ROOT + "audio/vo/narration.wav")
vo = signal.resample_poly(vo, SR, vsr)
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo_env = np.abs(signal.hilbert(lp(vo, 50, 1))) if False else np.convolve(np.abs(vo), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
duck = 1 - 0.55 * np.clip(vo_env / (vo_env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(int(0.2 * SR)) / int(0.2 * SR), 'same')
sfx_n = sfx / np.abs(sfx).max()
mix = np.zeros((N, 2))
mix += mus * 0.30 * duck[:, None]
mix += sfx_n * 0.75 * (0.6 + 0.4 * duck)[:, None]
mix[:, 0] += vo * 0.95; mix[:, 1] += vo * 0.95
fade = np.clip((DUR - t_all) / 0.6, 0, 1)
mix *= fade[:, None]
mix /= np.abs(mix).max() / 0.95
sf.write(ROOT + "audio/sfx/sfx.wav", sfx_n.astype(np.float32), SR)
sf.write(ROOT + "audio/music/music.wav", mus.astype(np.float32), SR)
sf.write(ROOT + "audio/mix.wav", mix.astype(np.float32), SR)
print("audio written", mix.shape, "impact at", T_IMP_VID)
