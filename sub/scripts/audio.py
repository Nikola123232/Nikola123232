"""Procedural sound design + sparse music + mix for the submarine implosion short -> sub/audio/{sfx,music,mix}.wav  (48 kHz stereo)."""
import sys, json, numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, "/home/user/Nikola123232/sub/scripts")
from tl import *
SR = 48000; D = NF / FPS + 0.5; N = int(SR * D); rng = np.random.default_rng(11)
A = "/home/user/Nikola123232/sub/audio/"

def sos(kind, fc, order=4):
    return signal.butter(order, fc, btype=kind, fs=SR, output="sos")
def lp(x, fc, o=4): return signal.sosfilt(sos("low", fc, o), x)
def hp(x, fc, o=4): return signal.sosfilt(sos("high", fc, o), x)
def bp(x, lo, hi, o=3): return signal.sosfilt(sos("band", [lo, hi], o), x)
def noise(n): return rng.normal(0, 1, n).astype(np.float32)
def tarr(n): return np.arange(n) / SR
def env(n, a, d, shape=2.0):
    t = tarr(n); e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / max(d, 1e-4) * shape / 2); return e.astype(np.float32)
def put(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR); n = min(len(x), buf.shape[1] - i)
    if n <= 0 or i < 0: return
    buf[0, i:i + n] += x[:n] * g * (1 - max(0, pan)); buf[1, i:i + n] += x[:n] * g * (1 + min(0, pan))
def fm_creak(dur, f0, f1, depth=60, ring=0.6):
    n = int(SR * dur); t = tarr(n); f = np.linspace(f0, f1, n) + depth * np.sin(2 * np.pi * rng.uniform(9, 23) * t) * np.sin(np.pi * t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR; x = np.sin(ph) + 0.5 * np.sin(2.01 * ph + 0.7) + 0.25 * np.sign(np.sin(3.02 * ph))
    x = bp(x + 0.4 * noise(n), max(60, min(f0, f1) * 0.8), max(f0, f1) * 6) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    # a little body resonance
    return (x * ring).astype(np.float32)
def sub_thump(dur, f0, f1, decay):
    n = int(SR * dur); t = tarr(n); f = f1 + (f0 - f1) * np.exp(-t / 0.08); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / decay) * np.minimum(t / 0.004, 1)).astype(np.float32)

sfx = np.zeros((2, N), np.float32)
# ---------------------------------------------------------------- ambience: deep water, rising pressure hum
t = tarr(N)
amb = lp(noise(N), 160, 2) * 0.55 + lp(noise(N), 520, 2) * 0.05
amb *= (0.55 + 0.25 * np.sin(2 * np.pi * 0.07 * t + 1.0)).astype(np.float32)
hum = (np.sin(2 * np.pi * 46 * t) * 0.5 + np.sin(2 * np.pi * 61.5 * t + 1.3) * 0.35 + np.sin(2 * np.pi * 92.3 * t) * 0.1)
depth_g = np.interp(t, [0, 8, 14, 20, 22.4, 23.0, 26, 31, 37.5], [0.35, 0.45, 0.8, 1.0, 1.15, 0.0, 0.18, 0.1, 0.05]).astype(np.float32)
amb_g = np.interp(t, [0, 4.6, 4.9, 5.5, 8, 23.0, 23.02, 26, 37.5], [0.7, 0.7, 0.12, 0.6, 0.8, 0.8, 0.0, 0.25, 0.1]).astype(np.float32)   # drop-out at the freeze and after the implosion
sfx[0] += (amb * amb_g * 0.32 + hum * depth_g * 0.05).astype(np.float32); sfx[1] += (np.roll(amb, 900) * amb_g * 0.32 + hum * depth_g * 0.05).astype(np.float32)

# ---------------------------------------------------------------- scene 1: hull creaks and the buckle (0-8.3 s)
for t0, f0, f1, g, pan in [(0.05, 120, 190, 0.25, -0.2), (0.9, 150, 230, 0.35, 0.2), (1.7, 110, 260, 0.45, -0.1), (2.5, 180, 300, 0.55, 0.15), (3.3, 140, 340, 0.7, 0.0), (3.95, 220, 420, 0.8, 0.0)]:
    put(sfx, fm_creak(0.7, f0, f1, 70), t0, g * 0.55, pan)
sb = F_BUCKLE0 / 30.0
put(sfx, (bp(noise(int(0.25 * SR)), 400, 5000) * env(int(0.25 * SR), 0.001, 0.05)), sb, 0.9)                       # metallic crack
put(sfx, fm_creak(0.5, 380, 90, 120, 1.0), sb, 0.7)
put(sfx, sub_thump(1.8, 70, 34, 0.55), F_FREEZE / 30.0 + 0.02, 1.0)                                                # restrained bass hit on the freeze
put(sfx, lp(noise(int(1.2 * SR)), 900) * env(int(1.2 * SR), 0.5, 0.5) * 0.5, 6.0, 0.5)                              # slow water rush of the pull-back
# ---------------------------------------------------------------- scene 2: descent (8.3-14.5)
for k, t0 in enumerate((9.4, 11.6, 13.5)): put(sfx, fm_creak(0.9, 90 + 20 * k, 160 + 40 * k, 40), t0, 0.3, (-1) ** k * 0.3)
ping = (np.sin(2 * np.pi * 1180 * tarr(int(1.6 * SR))) * env(int(1.6 * SR), 0.004, 0.45)).astype(np.float32)
put(sfx, ping, 8.45, 0.045, 0.2); put(sfx, ping, 8.45 + 0.19, 0.02, -0.3)
put(sfx, lp(noise(int(4.0 * SR)), 300) * env(int(4.0 * SR), 2.0, 2.0) * 0.4, 9.5, 0.6)
# ---------------------------------------------------------------- scene 3: cross-section, escalating strain (14.5-20.8)
for k, (t0, f0, f1) in enumerate([(14.7, 70, 120), (15.9, 80, 150), (17.0, 90, 200), (18.0, 110, 260), (18.8, 130, 330), (19.5, 160, 420), (20.0, 200, 520), (20.4, 260, 700)]):
    put(sfx, fm_creak(0.55 + 0.1 * (k < 4), f0, f1, 50 + 6 * k), t0, 0.28 + 0.07 * k, (-1) ** k * 0.25)
swell = (np.sin(2 * np.pi * 38 * tarr(int(6.5 * SR))) * np.sin(np.pi * np.linspace(0, 1, int(6.5 * SR))) ** 2).astype(np.float32)
put(sfx, swell, 14.5, 0.55)
for t0 in (19.3, 19.9, 20.3, 20.55, 20.7): put(sfx, (hp(noise(int(0.05 * SR)), 2500) * env(int(0.05 * SR), 0.0005, 0.012)), t0, 0.3)   # strain ticks
# ---------------------------------------------------------------- scene 4: tension, then the implosion (20.8-26)
tc_ = F_COLL / 30.0
for k, t0 in enumerate(np.linspace(21.2, 22.9, 9)): put(sfx, fm_creak(0.35, 300 + 60 * k, 620 + 80 * k, 70, 1.0), float(t0), 0.45 + 0.04 * k, (-1) ** k * 0.3)
for t0 in (22.05, 22.22, 22.31, 22.55, 22.62, 22.78, 22.86, 22.93): put(sfx, (bp(noise(int(0.03 * SR)), 1500, 9000) * env(int(0.03 * SR), 0.0005, 0.008)), t0, 0.55)   # lights stutter / structure ticks
put(sfx, lp(noise(int(1.8 * SR)), 400) * np.linspace(0, 1, int(1.8 * SR)) ** 3 * 0.7, tc_ - 1.8, 0.5)                    # pressure builds
# the implosion itself: short, dense, no fireball
n = int(SR * 0.6)
imp = sub_thump(0.9, 90, 28, 0.22) * 1.3 + bp(noise(n), 60, 1800, 2)[:int(0.9 * SR) if n >= int(0.9 * SR) else n].mean() * 0
put(sfx, sub_thump(0.9, 95, 26, 0.24), tc_ - 0.01, 1.35)
put(sfx, (lp(noise(int(0.5 * SR)), 2600) * env(int(0.5 * SR), 0.0008, 0.07)), tc_, 1.1)
put(sfx, (bp(noise(int(0.35 * SR)), 800, 9000) * env(int(0.35 * SR), 0.0005, 0.03)), tc_, 0.8)                       # shell crack
put(sfx, fm_creak(0.35, 900, 120, 200, 1.0), tc_ + 0.005, 0.8)
put(sfx, lp(noise(int(2.5 * SR)), 260) * env(int(2.5 * SR), 0.02, 0.8) * 0.9, tc_ + 0.02, 0.6)                          # water rushing in
# slow-motion replay: pitch-dropped, long
t_r = F_REPLAY[0] / 30.0; nr = int(SR * 2.6); tr = tarr(nr)
rep = (np.sin(2 * np.pi * np.cumsum(22 + 40 * np.exp(-tr / 0.7)) / SR) * np.exp(-tr / 0.9) * 0.9 + lp(noise(nr), 140) * np.exp(-tr / 0.8) * 0.8).astype(np.float32)
put(sfx, rep, t_r, 0.8)
put(sfx, (bp(noise(int(1.2 * SR)), 120, 900, 2) * env(int(1.2 * SR), 0.05, 0.4) * 0.4), t_r + 0.1, 0.5)
# ---------------------------------------------------------------- scene 5: aftermath (26-37)
tk = np.sort(rng.uniform(26.4, 35.5, 26))
for i, t0 in enumerate(tk):
    f0 = rng.uniform(380, 1500) * (1 - 0.4 * (t0 - 26.4) / 9); dur = rng.uniform(0.12, 0.35); nn = int(dur * SR); tt_ = tarr(nn)
    x = (np.sin(2 * np.pi * f0 * tt_) + 0.4 * np.sin(2 * np.pi * f0 * 2.76 * tt_)) * np.exp(-tt_ / (dur / 4))                      # tiny metal tinks
    put(sfx, x.astype(np.float32), float(t0), 0.05 * (1 - 0.8 * (t0 - 26.4) / 9.5), rng.uniform(-0.7, 0.7))
put(sfx, (np.sin(2 * np.pi * 32 * tarr(int(9 * SR))) * np.sin(np.pi * np.linspace(0, 1, int(9 * SR))) ** 2 * 0.45).astype(np.float32), 26.5, 1.0)
# ---------------------------------------------------------------- music: sparse, cold, suspenseful
mus = np.zeros((2, N), np.float32)
def pad(freqs, t0, dur, g):
    n = int(dur * SR); tt_ = tarr(n); x = np.zeros(n, np.float32)
    for f in freqs: x += (np.sin(2 * np.pi * f * tt_) + 0.35 * np.sin(2 * np.pi * 2 * f * tt_ + 0.4) + 0.18 * np.sin(2 * np.pi * 3 * f * tt_)).astype(np.float32) * (1 + 0.003 * np.sin(2 * np.pi * 0.31 * tt_))
    x = lp(x, 900, 2) * (np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6); put(mus, x, t0, g)
pad([36.7, 55.0], 0.0, 9.0, 0.10); pad([36.7, 38.9, 55.0], 8.5, 10.0, 0.12); pad([32.7, 49.0, 51.9], 17.0, 6.2, 0.15); pad([32.7, 46.2], 22.2, 1.6, 0.16)
pad([27.5, 41.2, 43.7], 25.5, 12.5, 0.11)
for k, t0 in enumerate((2.0, 6.2, 10.0, 14.0, 18.2)):                                                              # sparse high shimmer notes (very quiet)
    f = (440, 415.3, 369.99, 349.2, 311.1)[k]; n = int(2.4 * SR); tt_ = tarr(n)
    put(mus, (np.sin(2 * np.pi * f * tt_) * np.exp(-tt_ / 0.8) * np.minimum(tt_ / 0.02, 1)).astype(np.float32), t0, 0.012, 0.4 * (-1) ** k)
mus[:, int((tc_ - 0.01) * SR):int((tc_ + 3.6) * SR)] *= 0.0                                                         # music drops out: silence around the implosion

# ---------------------------------------------------------------- mix with narration, ducking
vo, vsr = sf.read(A + "vo/narration.wav", dtype="float32")
assert vsr == 24000
vo = signal.resample_poly(vo, 2, 1).astype(np.float32); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo = lp(hp(vo, 70, 2), 11000, 2) * 0.95
envv = np.abs(vo); envv = lp(envv, 6, 2); envv = np.clip(envv / (envv.max() * 0.5 + 1e-9), 0, 1)
duck = 1 - 0.45 * envv
sfx_m = sfx * duck[None]; mus_m = mus * (1 - 0.6 * envv)[None]
mix = sfx_m * 0.9 + mus_m * 0.9 + np.stack([vo, vo]) * 1.0
# gentle underwater feel on the music/sfx is already in the filtering; fade out at the end
g = np.ones(N, np.float32); fo = int(2.5 * SR); g[int((NF / FPS) * SR) - fo:int((NF / FPS) * SR)] = np.linspace(1, 0, fo); g[int((NF / FPS) * SR):] = 0
mix *= g[None]; mix = np.tanh(mix * 0.9) / 0.9
mix = mix / np.abs(mix).max() * 0.92
sf.write(A + "sfx.wav", sfx.T, SR); sf.write(A + "music.wav", mus.T, SR); sf.write(A + "mix.wav", mix[:, :int(NF / FPS * SR)].T, SR)
print("audio done", mix.shape, "peak", float(np.abs(mix).max()))
