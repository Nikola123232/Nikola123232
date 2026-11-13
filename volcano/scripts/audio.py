"""Volcano short: procedural sound design + original suspense score + mix with narration. Run with .ttsenv python.
Outputs volcano/audio/{sfx,music,mix}.wav (48 kHz stereo). Mix levels: music 0.16, sfx 0.45, VO 0.95 (VO ducks both)."""
import numpy as np, soundfile as sf
from scipy import signal
SR = 48000; DUR = 60.5; N = int(SR * DUR); t_all = np.arange(N) / SR
R = "/home/user/Nikola123232/volcano/"
rng = np.random.default_rng(11)
F = lambda fr: (fr - 1) / 30.0

def lp(x, fc, o=2): b, a = signal.butter(o, min(fc, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = signal.butter(o, [f1 / (SR / 2), min(f2, SR / 2 - 200) / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def noise(n): return rng.standard_normal(n)
def place(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[: N - i]
    l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
    buf[i:i + len(x), 0] += x * g * l; buf[i:i + len(x), 1] += x * g * r
def sweep_noise(dur, f0, f1, q=1.4, shape=None):
    n = int(dur * SR); x = noise(n); out = np.zeros(n); blk = 1024; zi = None
    for i in range(0, n, blk):
        u = i / n; fc = f0 * (f1 / f0) ** u; bw = fc / q
        b, a = signal.butter(2, [max(30, fc - bw / 2) / (SR / 2), min(SR / 2 - 200, fc + bw / 2) / (SR / 2)], 'band')
        if zi is None: zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi); out[i:i + blk] = y
    if shape is not None: out *= shape(np.linspace(0, 1, n))
    return out / (np.abs(out).max() + 1e-9)
def env(t, pts): return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])

sfx = np.zeros((N, 2))
# ---- bed: volcanic rumble (sub + low noise), always present and breathing
rum = lp(noise(N), 70, 3) * 1.0 + 0.8 * np.sin(2 * np.pi * 38 * t_all + 2 * np.sin(2 * np.pi * 0.13 * t_all)) + 0.5 * np.sin(2 * np.pi * 52.5 * t_all)
rum *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.21 * t_all + 1.0) ** 2
rum *= env(t_all, [(0, 1.0), (2.0, 0.7), (5, 0.5), (14, 0.6), (25, 0.45), (37, 0.8), (42, 1.0), (49, 0.5), (56, 0.8), (59, 1.0), (60.5, 0.0)])
sfx[:, 0] += rum * 0.34; sfx[:, 1] += np.roll(rum, 800) * 0.34
# ---- wind rush (fall): 0-2.1 and 5.2-14 fading, 56-60 pull-away
w = sweep_noise(2.2, 700, 2600, 0.9, lambda u: np.clip(u * 6, 0, 1) * (0.7 + 0.3 * u))
place(sfx, w, 0.0, 1.0)
wind = bp(noise(N), 300, 3000) * env(t_all, [(0, 0), (5.0, 0), (5.4, 0.9), (9, 0.7), (14, 0.2), (14.5, 0), (55.9, 0), (56.5, 0.5), (59.2, 1.0), (60.5, 0)])
sfx[:, 0] += wind * 0.20; sfx[:, 1] += np.roll(wind, 600) * 0.20
# ---- lava bubbling: random low pops + gloops (continuous, slower at 37-49 for the slow-motion)
def pop(t0, f0, g, dur=0.18, pan=0.0):
    n = int(dur * SR); x = np.arange(n) / SR
    s = np.sin(2 * np.pi * (f0 * x - 0.5 * (f0 * 0.8) * x * x / dur)) * np.exp(-x * 22)
    s += 0.35 * lp(noise(n), 400) * np.exp(-x * 30); place(sfx, s, t0, g, pan)
t = 0.5
while t < 59.5:
    slow = 37.0 < t < 49.0
    pop(t, rng.uniform(80, 220) * (0.6 if slow else 1.0), rng.uniform(0.05, 0.22), 0.28 if slow else 0.16, rng.uniform(-0.7, 0.7))
    t += rng.exponential(0.30 if not slow else 0.5)
# fire crackle texture (heat scene 14-25, and near lava)
for i in range(900):
    tc = rng.uniform(14.0, 25.0) if i < 520 else rng.uniform(37, 49)
    ln = int(rng.uniform(0.002, 0.01) * SR); c = hp(noise(ln), 2500) * np.exp(-np.linspace(0, 7, ln))
    place(sfx, c, tc, rng.uniform(0.03, 0.12), rng.uniform(-0.8, 0.8))
# ---- hook accents
n = int(2.5 * SR); x = np.arange(n) / SR
hit = np.sin(2 * np.pi * (60 * x - 14 * x * x)) * np.exp(-x * 2.2) + 0.5 * lp(noise(n), 300) * np.exp(-x * 3.5) + 0.35 * hp(noise(n), 3000) * np.exp(-x * 14)
place(sfx, np.tanh(hit * 1.6), 0.0, 0.9)                                   # 0:00 impact-style accent
place(sfx, sweep_noise(0.9, 4000, 200, 1.2, lambda u: np.sin(np.pi * u) ** 1.5), 1.55, 0.5)   # whoosh into the freeze
n = int(3.0 * SR); x = np.arange(n) / SR
bass = np.sin(2 * np.pi * (46 * x - 6 * x * x)) * np.exp(-x * 1.4) + 0.4 * lp(noise(n), 160) * np.exp(-x * 2.0)
place(sfx, np.tanh(bass * 1.7), 2.42, 1.0)                                 # "BEFORE YOU TOUCH IT?!" bass hit
# ---- cut whooshes and transition hits
for tt, g in ((2.0, 0.5), (5.0, 0.5), (14.0, 0.6), (18.17, 0.45), (25.0, 0.45), (26.9, 0.55), (31.67, 0.4), (37.0, 0.5), (49.0, 0.55), (56.0, 0.5)):
    place(sfx, sweep_noise(0.75, 500, 5000, 1.3, lambda u: np.sin(np.pi * u) ** 2), tt - 0.45, g, rng.uniform(-0.4, 0.4))
for tt in (14.0, 18.17, 26.9, 37.0):
    n = int(1.2 * SR); x = np.arange(n) / SR
    place(sfx, np.sin(2 * np.pi * 52 * x) * np.exp(-x * 4) + 0.3 * hp(noise(n), 2000) * np.exp(-x * 14), tt, 0.5)
# ---- falling debris ticks (scene 3)
for i in range(70):
    tc = rng.uniform(5.2, 14.0); ln = int(rng.uniform(0.01, 0.05) * SR)
    c = bp(noise(ln), 500, 4000) * np.exp(-np.linspace(0, 6, ln)); place(sfx, c / (np.abs(c).max() + 1e-9), tc, rng.uniform(0.04, 0.12), rng.uniform(-0.9, 0.9))
# ---- scene 4: radiant-heat shimmer + skin tones
place(sfx, sweep_noise(5.5, 1500, 7000, 3.0, lambda u: u ** 1.5), 19.0, 0.32)
for fr in (580, 625, 690):
    n = int(0.9 * SR); x = np.arange(n) / SR
    place(sfx, (np.sin(2 * np.pi * 1180 * x) + 0.5 * np.sin(2 * np.pi * 1770 * x)) * np.exp(-x * 5) * 0.4, F(fr), 0.18)
for fr in (720, 735):   # tissue sizzle
    place(sfx, hp(noise(int(1.5 * SR)), 3000) * np.exp(-np.linspace(0, 4, int(1.5 * SR))), F(fr), 0.2)
# ---- scene 5: breathing through the airway, heartbeat that falters, hiss of gas, tinnitus
def breath(t0, inhale=True, g=0.25):
    d = 1.5; x = sweep_noise(d, 500, 2200 if inhale else 1200, 0.8, lambda u: np.sin(np.pi * u) ** 1.2); place(sfx, x, t0, g)
for k, tb in enumerate((26.9, 28.6, 30.4, 32.2)): breath(tb, k % 2 == 0, 0.28)
def heart(t0, g=0.45):
    for off, gg in ((0, 1), (0.27, 0.7)):
        n = int(0.2 * SR); x = np.arange(n) / SR
        place(sfx, np.sin(2 * np.pi * 52 * x) * np.exp(-x * 20) + 0.3 * np.sin(2 * np.pi * 90 * x) * np.exp(-x * 28), t0 + off, g * gg)
tb = 25.2; bpm = 76
while tb < 36.9:
    heart(tb, 0.4 * (1 - 0.7 * max(0, (tb - 31) / 6))); tb += 60 / bpm * (1 + 0.5 * max(0, (tb - 31) / 6))
n = int(6 * SR); x = np.arange(n) / SR
place(sfx, np.sin(2 * np.pi * 4100 * x) * np.clip(x / 2, 0, 1) * np.exp(-np.clip(x - 3, 0, None) * 0.5), 31.0, 0.018)      # ringing in the ears
place(sfx, sweep_noise(4.0, 900, 300, 1.0, lambda u: np.sin(np.pi * u)), 26.9, 0.30)                                        # tunnel through the airway
# ---- scene 6: slow motion
place(sfx, sweep_noise(3.5, 3000, 120, 1.2, lambda u: np.sin(np.pi * u) ** 1.2), 38.0, 0.45)
n = int(5.0 * SR); x = np.arange(n) / SR
impact = np.sin(2 * np.pi * (48 * x - 5 * x * x)) * np.exp(-x * 1.1) + 0.7 * lp(noise(n), 220) * np.exp(-x * 2.2) + 0.25 * bp(noise(n), 600, 3000) * np.exp(-x * 5)
place(sfx, np.tanh(impact * 1.6), F(1262) - 0.03, 1.0)                                                                    # contact
for k in range(10):
    pop(F(1262) + 0.15 + k * rng.uniform(0.25, 0.5), rng.uniform(60, 120), rng.uniform(0.2, 0.4), 0.5, rng.uniform(-0.5, 0.5))
place(sfx, hp(noise(int(4 * SR)), 2500) * np.exp(-np.linspace(0, 3, int(4 * SR))), F(1262), 0.22)                          # sizzle
# ---- scene 7: water vs lava
def splash(t0, g=0.5):
    n = int(1.4 * SR); x = np.arange(n) / SR
    s = bp(noise(n), 800, 7000) * np.exp(-x * 6) + 0.5 * hp(noise(n), 4000) * np.exp(-x * 10)
    for k in range(14):
        tt = rng.uniform(0.05, 0.9); f0 = rng.uniform(500, 1800); m = int(0.08 * SR); xx = np.arange(m) / SR
        b = np.sin(2 * np.pi * (f0 + 3000 * xx) * xx) * np.exp(-xx * 50) * 0.35
        s[int(tt * SR):int(tt * SR) + m] += b[: max(0, n - int(tt * SR))][: m] if int(tt * SR) + m <= n else 0
    place(sfx, s, t0, g)
def gloop(t0, g=0.6):
    n = int(1.6 * SR); x = np.arange(n) / SR
    place(sfx, (np.sin(2 * np.pi * (140 * x - 70 * x * x)) * np.exp(-x * 3.2) + 0.4 * lp(noise(n), 260) * np.exp(-x * 5)) * g, t0, 1.0)
splash(F(1525), 0.5); gloop(F(1525) + 0.02, 0.9); splash(F(1606), 0.65); gloop(F(1606) + 0.02, 0.9)
place(sfx, sweep_noise(1.1, 300, 6000, 1.2, lambda u: np.sin(np.pi * u) ** 2), 49.0, 0.35)
# ---- finale: heavy hit as the camera lifts away, then silence for the fade-to-black
n = int(3.5 * SR); x = np.arange(n) / SR
fin = np.sin(2 * np.pi * (44 * x - 3 * x * x)) * np.exp(-x * 1.0) + 0.5 * lp(noise(n), 200) * np.exp(-x * 1.6) + 0.3 * hp(noise(n), 2500) * np.exp(-x * 7)
place(sfx, np.tanh(fin * 1.7), 58.55, 1.0)
sfx *= env(t_all, [(0, 1), (59.4, 1), (60.0, 0.0), (60.5, 0.0)])[:, None]

# ============================================================ MUSIC: A minor suspense, 78 bpm
mus = np.zeros((N, 2)); BPM = 78; beat = 60 / BPM
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (38, [50, 53, 57]), (40, [52, 56, 59])]      # Am F Dm E
seg = beat * 8; k = 0
while k * seg < DUR:
    t0 = k * seg; root, notes = prog[k % 4]; n = int(seg * SR); x = np.arange(n) / SR
    pad = np.zeros(n)
    for m in notes:
        for det in (-0.09, 0.09): pad += signal.sawtooth(2 * np.pi * midi(m) * (1 + det / 100) * x) * 0.22
    ev = np.minimum(x / 1.2, 1) * np.minimum((seg - x) / 1.0, 1)
    pad = lp(pad, 1000) * ev
    place(mus, pad * 0.45, t0, 1.0, -0.3); place(mus, np.roll(pad, 400) * 0.45, t0, 1.0, 0.3)
    place(mus, np.sin(2 * np.pi * midi(root - 12) * x) * ev * 0.55, t0, 1.0)
    for i in range(16):                          # pulsing low ostinato
        nb = int(beat / 2 * SR); xb = np.arange(nb) / SR
        b_ = lp(signal.sawtooth(2 * np.pi * midi(root - 12) * xb), 500) * np.exp(-xb * 6)
        place(mus, b_ * (0.35 if i % 4 else 0.5), t0 + i * beat / 2, 1.0)
    k += 1
# war drums on scene boundaries
for tt in (0.0, 5.0, 14.0, 37.0, 56.0):
    for j in range(4):
        n = int(0.45 * SR); x = np.arange(n) / SR
        place(mus, np.sin(2 * np.pi * (70 - 25 * x) * x) * np.exp(-x * 9) * 0.7, tt + j * beat * 0.5, 1.0)
# risers into scene changes
for tt, d in ((12.0, 2.0), (23.0, 2.0), (35.0, 2.0), (47.0, 2.0)):
    place(mus, sweep_noise(d, 300, 5000, 1.5, lambda u: u ** 2) * 0.5, tt, 1.0)
inten = env(t_all, [(0, 1.0), (1.8, 1.0), (2.2, 0.2), (5.0, 0.35), (5.3, 0.8), (14, 0.9), (25, 0.65), (37, 0.9), (43, 0.55), (49, 0.8), (55.5, 1.0), (58.5, 0.6), (60.5, 0.0)])
mus *= inten[:, None]
mus /= np.abs(mus).max() + 1e-9

# ============================================================ MIX
vo, vsr = sf.read(R + "audio/vo/narration.wav"); vo = signal.resample_poly(vo, SR, vsr); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
e = np.convolve(np.abs(vo), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
duck = 1 - 0.65 * np.clip(e / (e.max() * 0.25), 0, 1); duck = np.convolve(duck, np.ones(int(0.2 * SR)) / int(0.2 * SR), 'same')
sfx_n = sfx / np.abs(sfx).max()
mix = mus * 0.16 * duck[:, None] + sfx_n * 0.45 * (0.55 + 0.45 * duck)[:, None]
mix[:, 0] += vo * 0.95; mix[:, 1] += vo * 0.95
mix *= np.clip((DUR - 0.4 - t_all) / 0.5, 0, 1)[:, None]
mix /= np.abs(mix).max() / 0.95
sf.write(R + "audio/sfx.wav", sfx_n.astype(np.float32), SR); sf.write(R + "audio/music.wav", mus.astype(np.float32), SR); sf.write(R + "audio/mix.wav", mix.astype(np.float32), SR)
print("audio written", mix.shape)
