"""Final assembly: composite video -> loudness-normalised audio -> mux -> ffprobe validation."""
import subprocess, json, sys, os
ROOT = "/home/user/Nikola123232/"
OUT = ROOT + "out/final_f1_crash_short.mp4"

def run(cmd):
    print("+", " ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)

# 1) check all frames exist
missing = []
for name, a, b in [("s1", 1, 240), ("s2", 241, 540), ("s3", 541, 990), ("s4", 991, 1350), ("s5", 1351, 1680), ("s6", 1681, 1800)]:
    for f in range(a, b + 1):
        p = f"{ROOT}renders/{name}/{f:04d}.png"
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            missing.append(p)
if missing and "--allow-missing" not in sys.argv:
    sys.exit(f"{len(missing)} frames missing, e.g. {missing[:3]}")
# 2) composite video (no audio)
if "--skip-video" not in sys.argv:
    run(["python3", ROOT + "scripts/composite.py", "--encode"])
# 3) loudness normalise (EBU R128, -14 LUFS, -1.5 dBTP) and mux
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", ROOT + "audio/mix.wav",
     "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", ROOT + "audio/mix_norm.wav"])
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", ROOT + "out/video_noaudio.mp4", "-i", ROOT + "audio/mix_norm.wav",
     "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "60.0",
     "-movflags", "+faststart", OUT])
# 4) validate
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", OUT],
                               capture_output=True, text=True, check=True).stdout)
v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
a = [s for s in pr["streams"] if s["codec_type"] == "audio"][0]
info = {"file": OUT, "duration_s": float(pr["format"]["duration"]), "size_MB": round(int(pr["format"]["size"]) / 1e6, 2),
        "video": f'{v["codec_name"]} {v["width"]}x{v["height"]} {v["r_frame_rate"]} {v.get("pix_fmt")} frames={v.get("nb_frames")}',
        "audio": f'{a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]} ch'}
print(json.dumps(info, indent=1))
assert v["width"] == 1080 and v["height"] == 1920 and v["r_frame_rate"] == "30/1"
assert 59.0 <= info["duration_s"] <= 61.0
json.dump(info, open(ROOT + "out/ffprobe_validation.json", "w"), indent=1)
print("VALID")
