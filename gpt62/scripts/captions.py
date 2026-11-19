"""Chunk narration into caption phrases (single source for burned-in captions and the SRT)."""
import json, re
t = json.load(open("src/timeline.json")); caps = []
for L in t["lines"]:
    ws = L["words"]; cur = []
    def flush(end):
        if cur: caps.append(dict(s=cur[0]["s"]-0.05, e=end, text=" ".join(w["w"] for w in cur)))
    for i, w in enumerate(ws):
        cur.append(w); txt = " ".join(x["w"] for x in cur)
        nxt = ws[i+1] if i+1 < len(ws) else None
        punct = re.search(r"[,.:;?!]$", w["w"])
        if nxt is None or (punct and len(cur) >= 3) or len(txt) + len(nxt["w"]) > 50:
            if nxt is not None and len(ws) - i - 1 <= 1 and len(txt) + len(nxt["w"]) <= 58: continue  # avoid 1-word orphan
            flush(nxt["s"] - 0.02 if nxt else L["end"] + 0.25); cur = []
for a, b in zip(caps, caps[1:]): a["e"] = min(a["e"], b["s"] - 0.01)
json.dump(caps, open("src/captions.json", "w"), indent=0)
def ts(x):
    ms = int(round(x*1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
with open("out/GPT-6.2_Astra_vs_Sol.srt", "w") as f:
    for i, c in enumerate(caps, 1): f.write(f"{i}\n{ts(c['s'])} --> {ts(c['e'])}\n{c['text']}\n\n")
print(len(caps), "captions; longest:", max(len(c["text"]) for c in caps)); [print(c["text"]) for c in caps[:12]]
