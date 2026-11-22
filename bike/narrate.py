import numpy as np, soundfile as sf, subprocess, sys
from kokoro_onnx import Kokoro
R = "/home/user/Nikola123232/"
k = Kokoro(R + "assets/tts/kokoro-v1.0.onnx", R + "assets/tts/voices-v1.0.bin")
a, sr = k.create("See what happened to this cyclist after he tried to run the red light.", voice="am_adam", speed=1.0, lang="en-us")
i = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, i[0] - 100): i[-1] + 1200]
sf.write(R + "bike/narration.wav", a, sr); print("dur", len(a) / sr)
