"""Narration (Kokoro, calm documentary pacing). Lines are placed sequentially; prints the resulting timeline for scene planning."""
import json, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
R = "/home/user/Nikola123232/"; O = R + "sleep/audio/"
SR = 24000; VOICE = "am_michael"; SPEED = 1.02
LINES = [
    ("hook",  1.9, "After days without sleep, your brain can start showing you things that aren't there."),
    ("hook2", None, "But that's not even the first thing that goes wrong."),
    ("h24",   None, "After 24 hours awake, your attention, judgment, and reaction time can become seriously impaired."),
    ("h48",   None, "By 48 hours, microsleeps can interrupt your awareness for a few seconds, sometimes without you realizing it."),
    ("h72",   None, "After several days, confusion, distorted perception, and even hallucinations can occur."),
    ("h7d",   None, "By day seven, severe cognitive impairment and dangerous lapses in awareness could make ordinary activities unsafe."),
    ("end",   None, "And the frightening part? You may not fully realize how impaired you've become."),
]
GAPS = {"hook2": 0.40, "h24": 0.60, "h48": 0.55, "h72": 0.55, "h7d": 0.55, "end": 0.80}
k = Kokoro(R + "assets/tts/kokoro-v1.0.onnx", R + "assets/tts/voices-v1.0.bin")
def trim(s, thr=0.008):
    i = np.where(np.abs(s) > thr)[0]; return s[max(0, i[0] - 200): i[-1] + 500]
def synth(text):
    parts = []
    for s in re.split(r"(?<=[.?!])\s+", text):
        cl = re.split(r"(?<=,)\s+", s); aud = []
        for c in cl:
            a, _ = k.create(c, voice=VOICE, speed=SPEED, lang="en-us"); aud.append(trim(a))
        gap = np.zeros(int(0.22 * SR), np.float32); j = aud[0]
        for a in aud[1:]: j = np.concatenate([j, gap, a])
        parts.append((s, j))
    return parts
N = int(SR * 50); out = np.zeros(N, np.float32); words = []; tl = {}
t = 0.0
for name, t0, text in LINES:
    t = t0 if t0 is not None else t + GAPS[name]
    start = t
    for s, a in synth(text):
        out[int(t * SR): int(t * SR) + len(a)] += a
        ws = s.split(); ww = [max(2, len(re.sub(r"\W", "", w))) + (5 if w[-1] in ",.?!" else 0) for w in ws]
        lead, tail = 0.05, 0.1; span = len(a) / SR - lead - tail; acc = 0; S = sum(ww)
        for w, x in zip(ws, ww):
            a0 = t + lead + span * acc / S; acc += x; a1 = t + lead + span * acc / S
            words.append({"line": name, "w": w, "s": round(a0, 3), "e": round(a1, 3)})
        t += len(a) / SR + 0.18
    t -= 0.18; tl[name] = (round(start, 2), round(t, 2))
    print(f"{name:6s} {start:6.2f} -> {t:6.2f}  ({t - start:.2f}s)")
out = out / np.abs(out).max() * 0.89
sf.write(O + "vo/narration.wav", out, SR)
json.dump({"words": words, "timeline": tl}, open(O + "vo/words.json", "w"), indent=1)
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
with open(O + "subtitles.srt", "w") as f:
    ch = []; n = 1
    for w in words + [None]:
        if ch and (w is None or len(ch) >= 5 or w["line"] != ch[-1]["line"] or ch[-1]["w"][-1] in ",.?!"):
            f.write(f"{n}\n{ts(ch[0]['s'])} --> {ts(ch[-1]['e'] + 0.2)}\n{' '.join(c['w'] for c in ch)}\n\n"); n += 1; ch = []
        if w: ch.append(w)
