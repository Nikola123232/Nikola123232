"""Speech -> timed text with sherpa-onnx (Whisper small.en) + Silero VAD. usage: transcribe.py video out.json"""
import sys, json, subprocess, numpy as np, sherpa_onnx
M = "/tmp/asr/model/sherpa-onnx-whisper-small.en/"; src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.float32)
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "small.en-encoder.int8.onnx", decoder=M + "small.en-decoder.int8.onnx", tokens=M + "small.en-tokens.txt", language="en", task="transcribe", num_threads=4)
vc = sherpa_onnx.VadModelConfig(); vc.silero_vad.model = "/home/user/Nikola123232/shorts/asr/silero_vad.onnx"; vc.silero_vad.min_silence_duration = 0.35; vc.silero_vad.min_speech_duration = 0.15; vc.silero_vad.max_speech_duration = 8.0; vc.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(vc, buffer_size_in_seconds=60); res = []
def run(seg):
    s = rec.create_stream(); s.accept_waveform(16000, seg.samples); rec.decode_stream(s)
    res.append({"s": round(seg.start / 16000, 2), "e": round(seg.start / 16000 + len(seg.samples) / 16000, 2), "text": s.result.text.strip()})
W = 512
for i in range(0, len(a), W):
    vad.accept_waveform(a[i:i + W])
    while not vad.empty(): run(vad.front); vad.pop()
vad.flush()
while not vad.empty(): run(vad.front); vad.pop()
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
for r in res: print(r["s"], r["e"], r["text"])
