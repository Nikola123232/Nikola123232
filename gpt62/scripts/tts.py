"""Kokoro TTS -> public/vo.wav + src/timeline.json (measured sentence timings, phoneme-weighted word timings)."""
import json, re, sys, numpy as np, soundfile as sf
sys.path.insert(0, "scripts"); from script_data import S, say
from kokoro_onnx import Kokoro
SR = 24000; VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"; SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9
k = Kokoro("../assets/tts/kokoro-v1.0.onnx", "../assets/tts/voices-v1.0.bin")
def trim(a, thr=0.008):
    i = np.where(np.abs(a) > thr)[0]; return a[max(0, i[0]-120): i[-1]+360]
def weight(w):
    ph = k.tokenizer.phonemize(say(re.sub(r"[^\w'$.,-]", "", w)).strip(" ,"), "en-us")
    return max(2, len(ph.replace(" ", "")))
GAP, SECGAP = 0.42, 1.30
chunks, t, lines, prev = [], 0.25, [], None
for i, ln in enumerate(S):
    if prev and prev != ln["section"]: t += SECGAP
    elif prev: t += GAP
    prev = ln["section"]; t += ln["pb"]
    subs = re.split(r"(?<=[.?!])\s+", ln["text"]); L = dict(ln, start=t, words=[])
    for j, sub in enumerate(subs):
        a, _ = k.create(say(sub), voice=VOICE, speed=SPEED, lang="en-us"); a = trim(a)
        if j: t += 0.22; chunks.append(np.zeros(int(0.22*SR), np.float32))
        d = len(a)/SR; ws = sub.split(); wt = np.array([weight(w) for w in ws], float)
        # leading/trailing tiny margins
        edges = t + 0.03 + np.concatenate([[0], np.cumsum(wt)])/wt.sum()*(d-0.12)
        L["words"] += [dict(w=w, s=round(edges[n],3), e=round(edges[n+1],3)) for n, w in enumerate(ws)]
        chunks.append(a.astype(np.float32)); t += d
    L["end"] = t; lines.append(L)
    t += ln["pa"]; chunks.append(np.zeros(int((ln["pa"] + (0 if i+1==len(S) else (SECGAP if S[i+1]["section"]!=ln["section"] else GAP) + S[i+1]["pb"]))*SR), np.float32))
# rebuild audio strictly from timeline to avoid drift
total = lines[-1]["end"] + 3.6
out = np.zeros(int(total*SR)+SR, np.float32)
for L in lines:
    pass
# simpler: re-synthesize placement by start times stored per sub; reconstruct from chunks sequentially
audio = np.concatenate([np.zeros(int((0.25+S[0]["pb"])*SR), np.float32)] + chunks)
out[:len(audio)] = audio[:len(out)]
out = out[:int(total*SR)]
sf.write("public/vo.wav", out, SR)
secs = {}
for L in lines:
    s = secs.setdefault(L["section"], [L["start"], L["end"]]); s[1] = L["end"]
json.dump(dict(fps=30, total=total, lines=lines, sections=secs, cues={L["cue"]: [round(L["start"],3), round(L["end"],3)] for L in lines if L["cue"]}), open("src/timeline.json","w"), indent=1)
print("voice", VOICE, "speed", SPEED, "total", round(total,2), {k_: [round(v[0],1), round(v[1],1)] for k_, v in secs.items()})
