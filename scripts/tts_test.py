import sys, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("assets/tts/kokoro-v1.0.onnx", "assets/tts/voices-v1.0.bin")
print([v for v in k.get_voices() if v.startswith(("am_","bm_"))])
t="What would actually happen to your body if you crashed a Formula 1 car at 300 kilometers per hour?"
for v in ["am_michael","bm_george","am_fenrir","bm_lewis"]:
    s,sr=k.create(t,voice=v,speed=1.0,lang="en-us" if v.startswith("a") else "en-gb")
    sf.write(f"audio/vo/test_{v}.wav",s,sr); print(v,len(s)/sr)
