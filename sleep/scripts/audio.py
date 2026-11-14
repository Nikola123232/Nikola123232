"""Sound design + restrained score for the 44.6 s film, mixed with the narration. Run with .ttsenv python (numpy/scipy/soundfile).
Outputs sleep/audio/{sfx,music,mix}.wav (48 kHz stereo)."""
import numpy as np, soundfile as sf
from scipy import signal
R = "/home/user/Nikola123232/sleep/"; SR = 48000; NFR = 1340; DUR = (NFR) / 30.0 + 0.3; N = int(SR * DUR); t_all = np.arange(N) / SR
rng = np.random.default_rng(21)
F = lambda fr: (fr - 1) / 30.0

def lp(x, fc, o=2): b, a = signal.butter(o, min(fc, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = signal.butter(o, [f1 / (SR / 2), min(f2, SR / 2 - 200) / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def noise(n): return rng.standard_normal(n)
def place(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[: N - i]; l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
    buf[i:i + len(x), 0] += x * g * l; buf[i:i + len(x), 1] += x * g * r
def env(t, pts): return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
def sweep(dur, f0, f1, q=1.4, shape=None):
    n = int(dur * SR); x = noise(n); out = np.zeros(n); blk = 1024; zi = None
    for i in range(0, n, blk):
        u = i / n; fc = f0 * (f1 / f0) ** u; bw = fc / q
        b, a = signal.butter(2, [max(30, fc - bw / 2) / (SR / 2), min(SR / 2 - 200, fc + bw / 2) / (SR / 2)], 'band')
        if zi is None: zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi); out[i:i + blk] = y
    if shape is not None: out *= shape(np.linspace(0, 1, n))
    return out / (np.abs(out).max() + 1e-9)

# ------------------------------------------------------------------ room tone (no music in the first 0.5 s, only room + clock)
room = lp(noise(N), 140, 3) * 0.5 + bp(noise(N), 200, 1800) * 0.06 + 0.25 * np.sin(2 * np.pi * 50 * t_all) + 0.12 * np.sin(2 * np.pi * 100.2 * t_all)
room *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t_all)
silence_win = env(t_all, [(0, 1), (F(843), 1), (F(851), 0.0), (F(880), 0.0), (F(884), 1), (F(1186), 1), (F(1190), 0.05), (DUR, 0.05)])
sfx = np.zeros((N, 2)); sfx[:, 0] += room * 0.30 * silence_win; sfx[:, 1] += np.roll(room, 700) * 0.30 * silence_win

# ------------------------------------------------------------------ clock ticks (1 Hz tick-tock; muffled in the microsleep, irregular in the 7th day, silent in the ending)
def tick(t0, kind, g=1.0, bright=1.0, pitch=1.0):
    n = int(0.09 * SR); x = np.arange(n) / SR
    f0 = (3400 if kind == 0 else 2700) * pitch
    s = (np.sin(2 * np.pi * f0 * x) * np.exp(-x * 90) + 0.6 * bp(noise(n), 1500, 6500) * np.exp(-x * 110) + 0.5 * np.sin(2 * np.pi * 410 * pitch * x) * np.exp(-x * 60))
    s = lp(s, 900 + 8000 * bright)
    place(sfx, s, t0, 0.22 * g, -0.35)
    # small room reverb tail
    place(sfx, lp(s, 2500) * 0.25, t0 + 0.028, 0.22 * g, -0.1); place(sfx, lp(s, 1800) * 0.12, t0 + 0.065, 0.22 * g, -0.5)
k = 0; tt = 0.15
while tt < F(1186) + 0.1:
    if tt >= F(851) - 0.2 and tt <= F(884): tt += 1.0; k += 1; continue
    if tt > F(931):
        jitter = rng.uniform(-0.18, 0.22) * min(1, (tt - F(931)) / 3); tick(tt + jitter, k % 2, 0.9, 0.7, 1.0 + rng.uniform(-0.12, 0.05) * min(1, (tt - F(931)) / 6))
        if rng.random() < 0.22: tick(tt + jitter + rng.uniform(0.12, 0.3), (k + 1) % 2, 0.5, 0.6, 0.85)           # double / stutter ticks
    else:
        near = 1.0 if tt < 7.0 else 0.8
        tick(tt, k % 2, near, 1.0)
    tt += 1.0; k += 1
# ------------------------------------------------------------------ breathing (very quiet), only in the apartment
def breath(t0, g=1.0):
    d = 1.7; place(sfx, sweep(d * 0.9, 700, 2600, 0.8, lambda u: np.sin(np.pi * u) ** 1.4) * 0.5, t0, 0.18 * g, 0.2)
    place(sfx, sweep(d, 1800, 500, 0.8, lambda u: np.sin(np.pi * u) ** 1.2) * 0.5, t0 + d * 0.95, 0.15 * g, 0.2)
for fr_a, fr_b, gg in ((1, 190, 1.0), (381, 732, 0.9), (733, 880, 0.9), (931, 1186, 1.2)):
    tb = F(fr_a) + 0.4
    while tb < F(fr_b) - 2.2:
        breath(tb, gg * rng.uniform(0.8, 1.1)); tb += rng.uniform(3.6, 4.6)
# ------------------------------------------------------------------ the hook: restrained accent at the cut to POV, match-cut swell into the brain
n = int(1.6 * SR); x = np.arange(n) / SR
acc = np.sin(2 * np.pi * (48 * x - 3 * x * x)) * (np.clip(x / 0.25, 0, 1) * np.exp(-np.clip(x - 0.25, 0, None) * 2.2)) + 0.25 * lp(noise(n), 300) * np.exp(-x * 3.0)
place(sfx, acc, F(61) - 0.10, 0.50)
place(sfx, sweep(0.45, 400, 4500, 1.2, lambda u: u ** 2 * (1 - u * 0.0)), F(61) - 0.5, 0.20)             # air drawn in just before the cut
n = int(2.2 * SR); x = np.arange(n) / SR
place(sfx, np.sin(2 * np.pi * (36 + 20 * x / 2.2) * x) * np.clip(x / 1.6, 0, 1) * np.exp(-np.clip(x - 1.6, 0, None) * 4) * 0.5, F(121) + 0.1, 0.55)  # push-in swell
place(sfx, sweep(0.9, 6000, 200, 1.2, lambda u: np.sin(np.pi * u) ** 1.5), F(186) - 0.2, 0.30)                                                   # pupil -> brain
n = int(1.5 * SR); x = np.arange(n) / SR; place(sfx, np.sin(2 * np.pi * 46 * x) * np.exp(-x * 3.0) * 0.8, F(190), 0.40)
# ------------------------------------------------------------------ brain: soft electrical shimmer + pulse blips
for (a_, b_) in ((191, 380), (691, 732), (881, 930)):
    n = int((F(b_) - F(a_)) * SR); sh = bp(noise(n), 2500, 9000) * 0.012 * np.sin(np.linspace(0, np.pi, n)); place(sfx, sh, F(a_), 1.0)
def blip(t0, f0, g=0.5):
    m = int(0.25 * SR); x = np.arange(m) / SR; place(sfx, (np.sin(2 * np.pi * f0 * x) + 0.4 * np.sin(2 * np.pi * f0 * 2.01 * x)) * np.exp(-x * 14), t0, 0.07 * g, 0.4)
for fr, f0 in ((310, 1400), (355, 1200), (340, 880), (394, 740)): blip(F(fr), f0)
# 48 h brain: network stutters then resumes
n = int(0.6 * SR); x = np.arange(n) / SR
place(sfx, lp(noise(n), 400) * np.exp(-x * 5) * 0.5, F(706), 0.3); place(sfx, np.sin(2 * np.pi * 70 * x) * np.exp(-x * 4) * 0.5, F(722), 0.35)
# ------------------------------------------------------------------ glass (slow motion)
n = int(0.5 * SR); x = np.arange(n) / SR; place(sfx, bp(noise(n), 600, 3000) * np.exp(-x * 6) * 0.3, F(388), 0.28, -0.2)     # slides on the desk
place(sfx, sweep(1.9, 900, 160, 1.0, lambda u: np.sin(np.pi * u) ** 1.2) * 0.8, F(398), 0.30, 0.0)                              # slow fall
n = int(5.0 * SR); x = np.arange(n) / SR
crash = bp(noise(n), 500, 9000) * np.exp(-x * 3.0) + 0.5 * np.sum([np.sin(2 * np.pi * rng.uniform(700, 4200) * x) * np.exp(-x * rng.uniform(3, 9)) for _ in range(22)], axis=0) / 4
crash = lp(crash, 5200) * np.clip(x / 0.01, 0, 1)
place(sfx, crash, F(437), 0.55, -0.1)                                                                                           # slowed shatter
n = int(1.8 * SR); x = np.arange(n) / SR; place(sfx, np.sin(2 * np.pi * 55 * x) * np.exp(-x * 4) * 0.9 + lp(noise(n), 300) * np.exp(-x * 6) * 0.4, F(437), 0.45)
for k_ in range(26):
    tb = F(441) + rng.uniform(0.0, 2.8) ** 1.2; m = int(rng.uniform(0.03, 0.14) * SR)
    place(sfx, bp(noise(m), 1000, 8000) * np.exp(-np.linspace(0, 6, m)), tb, rng.uniform(0.03, 0.12), rng.uniform(-0.8, 0.8))
place(sfx, hp(noise(int(1.4 * SR)), 3000) * np.exp(-np.linspace(0, 5, int(1.4 * SR))) * 0.5, F(440), 0.07)                      # water
# ------------------------------------------------------------------ 48 h: muffled room (everything except the narration is low-passed) + ring; jolt back
mix_gate = np.zeros(N)
mix_gate += env(t_all, [(0, 0), (F(548), 0), (F(562), 1), (F(646), 1), (F(649), 0), (DUR, 0)])
n = int(3.0 * SR); x = np.arange(n) / SR; place(sfx, np.sin(2 * np.pi * 3100 * x) * np.clip(x / 1.0, 0, 1) * np.exp(-np.clip(x - 1.0, 0, None) * 1.2) * 0.012, F(610), 1.0)
n = int(0.5 * SR); place(sfx, sweep(0.5, 1200, 3500, 1.0, lambda u: np.sin(np.pi * u)) * 0.6, F(646), 0.35)                    # sharp inhale on the jolt
place(sfx, np.sin(2 * np.pi * 60 * np.arange(int(0.8 * SR)) / SR) * np.exp(-np.arange(int(0.8 * SR)) / SR * 5) * 0.7, F(649), 0.30)
# ------------------------------------------------------------------ 72 h: low tone building, then the silence
place(sfx, sweep(3.8, 180, 120, 2.0, lambda u: np.sin(np.pi * u * 0.5) ** 2) * 0.7, F(762), 0.18)
n = int(0.7 * SR); x = np.arange(n) / SR; place(sfx, sweep(0.6, 2500, 200, 1.0, lambda u: np.sin(np.pi * u)) * 0.5, F(843), 0.30)    # air drawn out before the silence
place(sfx, np.sin(2 * np.pi * 52 * x) * np.exp(-x * 5) * 0.6, F(884), 0.25)
# ------------------------------------------------------------------ 7 days: pitch-wobbling drone, dropouts at the lapses
dr = (np.sin(2 * np.pi * 55 * t_all * (1 + 0.004 * np.sin(2 * np.pi * 0.31 * t_all))) + 0.5 * np.sin(2 * np.pi * 82.5 * t_all) + 0.3 * lp(noise(N), 160))
dr *= env(t_all, [(0, 0), (F(925), 0), (F(960), 0.7), (F(1186), 1.0), (F(1200), 0.2), (DUR, 0.0)])
sfx[:, 0] += dr * 0.16; sfx[:, 1] += np.roll(dr, 900) * 0.16
for fl in (985, 1060, 1118, 1160):
    g_ = env(t_all, [(0, 1), (F(fl) - 0.06, 1), (F(fl) - 0.04, 0.1), (F(fl) + 0.10, 0.1), (F(fl) + 0.13, 1), (DUR, 1)]); sfx *= g_[:, None]
    n = int(0.9 * SR); x = np.arange(n) / SR; place(sfx, np.sin(2 * np.pi * 2900 * x) * np.exp(-x * 5) * 0.015, F(fl) + 0.1, 1.0)
# ------------------------------------------------------------------ ending: the room is silent, one slow breath out as his eyes close
place(sfx, sweep(2.0, 1500, 350, 0.8, lambda u: np.sin(np.pi * u) ** 1.3) * 0.5, F(1252), 0.18, 0.2)
n = int(3.5 * SR); x = np.arange(n) / SR; place(sfx, np.sin(2 * np.pi * 40 * x) * np.exp(-x * 1.0) * 0.8, F(1296), 0.35)
# muffling: gate crossfades dry/low-passed copy of the room sound
sfx_m = np.stack([lp(sfx[:, 0], 520, 3), lp(sfx[:, 1], 520, 3)], 1); sfx = sfx * (1 - mix_gate[:, None]) + sfx_m * mix_gate[:, None] * 1.3

# ------------------------------------------------------------------ music: sparse, cold, restrained (starts at 0.5 s; dissolves into silence in the ending)
mus = np.zeros((N, 2)); midi = lambda m: 440 * 2 ** ((m - 69) / 12)
roots = [(33, [45, 52, 57]), (29, [41, 48, 53]), (31, [43, 50, 55]), (28, [40, 47, 52])]
seg = 5.6; k = 0
while k * seg < DUR:
    t0 = k * seg; root, nts = roots[k % 4]; n = int((seg + 1.0) * SR); x = np.arange(n) / SR
    pad = np.zeros(n)
    for m in nts:
        for dt in (-0.1, 0.1): pad += signal.sawtooth(2 * np.pi * midi(m) * (1 + dt / 100) * x) * 0.16
    ev = np.clip(x / 1.8, 0, 1) * np.clip((seg + 1.0 - x) / 1.6, 0, 1)
    place(mus, lp(pad, 650) * ev * 0.6, t0, 1.0, -0.3); place(mus, np.roll(lp(pad, 650), 500) * ev * 0.6, t0, 1.0, 0.3)
    place(mus, np.sin(2 * np.pi * midi(root) * x) * ev * 0.55, t0, 1.0)
    k += 1
for tn, m in ((1.5, 81), (4.1, 76), (10.8, 79), (17.2, 76), (23.0, 74), (29.0, 79), (33.5, 72), (37.0, 70), (41.0, 69)):      # sparse glass-like notes
    n = int(3.0 * SR); x = np.arange(n) / SR; place(mus, (np.sin(2 * np.pi * midi(m) * x) + 0.25 * np.sin(2 * np.pi * midi(m) * 2.76 * x)) * np.exp(-x * 1.6) * 0.18, tn, 1.0, rng.uniform(-0.5, 0.5))
mus *= env(t_all, [(0, 0), (0.5, 0), (2.5, 0.8), (F(851), 0.8), (F(851) + 0.1, 0.0), (F(884), 0.0), (F(888), 0.8), (F(1186), 1.0), (F(1215), 0.0), (DUR, 0.0)])[:, None]
mus /= np.abs(mus).max() + 1e-9

# ------------------------------------------------------------------ mix
vo, vsr = sf.read(R + "audio/vo/narration.wav"); vo = signal.resample_poly(vo, SR, vsr); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
e = np.convolve(np.abs(vo), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same'); duck = 1 - 0.5 * np.clip(e / (e.max() * 0.25), 0, 1); duck = np.convolve(duck, np.ones(int(0.2 * SR)) / int(0.2 * SR), 'same')
sfx_n = sfx / (np.abs(sfx).max() + 1e-9)
mix = mus * 0.12 * duck[:, None] + sfx_n * 0.62 * (0.7 + 0.3 * duck)[:, None]
mix[:, 0] += vo * 0.95; mix[:, 1] += vo * 0.95
mix *= env(t_all, [(0, 1), (NFR / 30.0 - 1.4, 1), (NFR / 30.0, 0), (DUR, 0)])[:, None]
mix /= np.abs(mix).max() / 0.95
sf.write(R + "audio/sfx.wav", sfx_n.astype(np.float32), SR); sf.write(R + "audio/music.wav", mus.astype(np.float32), SR); sf.write(R + "audio/mix.wav", mix.astype(np.float32), SR)
print("audio written", mix.shape)
