"""Generate narration with Kokoro neural TTS and estimate per-word timings.
Output: audio/vo/narration.wav (full 60 s timeline) + audio/vo/words.json"""
import json, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SR = 24000
VOICE = "am_michael"
LINES = [  # (start_sec, window_end, text, speed)
    (0.30, 8.0,  "What would actually happen to your body, if you crashed a Formula One car at three hundred kilometers per hour?", 1.05),
    (8.40, 18.0, "At this speed, the danger isn't just the impact. It's how quickly your body is forced to stop.", 1.0),
    (18.30, 33.0, "Your seat belts restrain your body, but your brain and internal organs can still experience dangerous forces. Severe crashes can cause concussions, neck injuries, or internal trauma.", 1.04),
    (33.30, 45.0, "And your head and neck are especially vulnerable. That's why Formula One drivers wear specialized helmets, and head-and-neck restraints.", 1.0),
    (45.30, 56.0, "Modern Formula One cars are designed to absorb crash energy, while multiple safety systems work together to protect the driver.", 1.0),
    (54.95, 60.0, "At three hundred kilometers per hour, survival depends on how the crash happens.", 1.12),
]
# display text for subtitles (numerals read better on screen)
DISPLAY = {"Formula One": "Formula 1", "three hundred kilometers per hour": "300 km/h"}

k = Kokoro("assets/tts/kokoro-v1.0.onnx", "assets/tts/voices-v1.0.bin")

def trim(s, thr=0.01):
    idx = np.where(np.abs(s) > thr)[0]
    return s[max(0, idx[0]-240): idx[-1]+480]

def word_weights(words):
    w = []
    for wd in words:
        ph = k.tokenizer.phonemize(re.sub(r"[^\w' -]", "", wd), "en-us")
        w.append(max(2, len(ph.replace(" ", ""))))
    return w

total = np.zeros(int(SR*60.5), dtype=np.float32)
timeline = []
for li, (t0, tend, text, speed) in enumerate(LINES):
    # synthesize sentence by sentence (keeps natural prosody, gives exact sentence boundaries)
    sents = re.split(r"(?<=[.?!])\s+", text)
    t = t0
    for si, s in enumerate(sents):
        audio, sr = k.create(s, voice=VOICE, speed=speed, lang="en-us")
        audio = trim(audio)
        n = len(audio); dur = n/SR
        i0 = int(t*SR); total[i0:i0+n] += audio
        # per-word timing: proportional to phoneme count, commas add a pause weight
        words = s.split()
        ww = word_weights(words)
        ww = [x + (6 if words[i].endswith(",") else 0) for i, x in enumerate(ww)]
        lead, tail = 0.05, 0.12
        span = dur - lead - tail; acc = 0; S = sum(ww)
        for wd, x in zip(words, ww):
            ws = t + lead + span*acc/S; acc += x; we = t + lead + span*acc/S
            timeline.append({"line": li, "w": wd, "s": round(ws, 3), "e": round(we, 3)})
        t += dur + 0.18
    print(f"line {li}: ends {t:.2f}s (window {tend})", "OVER!" if t > tend else "")

peak = np.abs(total).max(); total = total/peak*0.89
sf.write("audio/vo/narration.wav", total, SR)
json.dump({"words": timeline, "display": DISPLAY}, open("audio/vo/words.json", "w"), indent=1)
