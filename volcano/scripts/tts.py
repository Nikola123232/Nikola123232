"""Narration: Kokoro neural TTS, auto-fitted into each scene window. Writes audio/vo/narration.wav, words.json, subtitles.srt"""
import json, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
R = "/home/user/Nikola123232/"; O = R + "volcano/audio/vo/"
SR = 24000; VOICE = "am_michael"
LINES = [  # start, hard end (s), text
    (0.12, 2.0,  "What if you fell into a volcano?"),
    (2.10, 5.0,  "You might be dead before you even touch the lava."),
    (5.20, 14.0, "As you fall deeper into the crater, the intense heat and dangerous gases could become a serious threat."),
    (14.20, 25.0, "Exposed lava can reach temperatures above a thousand degrees Celsius. Its intense radiant heat can cause severe burns without direct contact."),
    (25.20, 37.0, "Breathing hot gases can injure your airways, while toxic gases or oxygen-poor air can make you lose consciousness."),
    (37.20, 49.0, "If you reached the lava, the contact would cause catastrophic burns. But you wouldn't simply sink into it like water."),
    (48.30, 54.7, "Lava is much denser and usually far more viscous than water, so falling into it is nothing like diving into a pool."),
    (55.00, 59.95, "And in some volcanic conditions, the heat or gases could kill you before you ever touched the lava."),
]
k = Kokoro(R + "assets/tts/kokoro-v1.0.onnx", R + "assets/tts/voices-v1.0.bin")
def trim(s, thr=0.01):
    i = np.where(np.abs(s) > thr)[0]; return s[max(0, i[0] - 240): i[-1] + 480]
def synth(text, speed):
    """Sentences -> clauses (split after commas); each clause synthesised and trimmed, joined with a short gap."""
    sents = re.split(r"(?<=[.?!])\s+", text); parts = []
    for s in sents:
        cl = re.split(r"(?<=,)\s+", s); aud = []; 
        for c in cl:
            a, _ = k.create(c, voice=VOICE, speed=speed, lang="en-us"); aud.append(trim(a))
        gap = np.zeros(int(0.20 * SR), np.float32); joined = aud[0]
        for a in aud[1:]: joined = np.concatenate([joined, gap, a])
        parts.append((s, joined))
    return parts
def total(parts): return sum(len(a) / SR + 0.15 for _, a in parts) - 0.15
N = int(SR * 60.5); out = np.zeros(N, np.float32); words = []
for li, (t0, tend, text) in enumerate(LINES):
    speed = 0.95
    while True:
        parts = synth(text, speed)
        if t0 + total(parts) <= tend - 0.05 or speed >= 1.45: break
        speed += 0.05
    t = t0
    for s, a in parts:
        i0 = int(t * SR); out[i0:i0 + len(a)] += a
        ws = s.split()
        ww = [max(2, len(re.sub(r"\W", "", w))) + (5 if w[-1] in ",.?!" else 0) for w in ws]
        lead, tail = 0.05, 0.1; span = len(a) / SR - lead - tail; acc = 0; S = sum(ww)
        for w, x in zip(ws, ww):
            a0 = t + lead + span * acc / S; acc += x; a1 = t + lead + span * acc / S
            words.append({"line": li, "w": w, "s": round(a0, 3), "e": round(a1, 3)})
        t += len(a) / SR + 0.15
    print(f"line {li}: speed {speed:.2f}  {t0:.2f} -> {t-0.15:.2f} (limit {tend})")
out = out / np.abs(out).max() * 0.89
sf.write(O + "narration.wav", out, SR)
json.dump({"words": words}, open(O + "words.json", "w"), indent=1)
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
with open(R + "volcano/audio/subtitles.srt", "w") as f:
    chunk = []; n = 1
    for w in words + [None]:
        if chunk and (w is None or len(chunk) >= 4 or w["line"] != chunk[-1]["line"] or chunk[-1]["w"][-1] in ",.?!"):
            f.write(f"{n}\n{ts(chunk[0]['s'])} --> {ts(chunk[-1]['e'] + 0.15)}\n{' '.join(c['w'] for c in chunk)}\n\n"); n += 1; chunk = []
        if w: chunk.append(w)
