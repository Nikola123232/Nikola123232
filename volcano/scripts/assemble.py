"""Final assembly: composite -> loudness-normalised audio -> mux -> ffprobe validation + black/duplicate-frame check."""
import subprocess, json, sys, os, re
R = "/home/user/Nikola123232/volcano/"; OUT = R + "out/what_if_you_fell_into_a_volcano.mp4"
def run(cmd): print("+", " ".join(cmd[:5]), "...", flush=True); subprocess.run(cmd, check=True)
missing = []
for n, a, b in [("v12", 1, 150), ("v3", 151, 420), ("v4", 421, 750), ("v5", 751, 1110), ("v6", 1111, 1470), ("v7", 1471, 1680), ("v8", 1681, 1800)]:
    for f in range(a, b + 1):
        p = f"{R}renders/{n}/{f:04d}.png"
        if not os.path.exists(p) or os.path.getsize(p) == 0: missing.append(p)
if missing and "--allow-missing" not in sys.argv: sys.exit(f"{len(missing)} frames missing, e.g. {missing[:3]}")
if "--skip-video" not in sys.argv: run(["python3", R + "scripts/composite.py", "--encode"])
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", R + "audio/mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", R + "audio/mix_norm.wav"])
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", R + "out/video_noaudio.mp4", "-i", R + "audio/mix_norm.wav", "-map", "0:v:0", "-map", "1:a:0",
     "-vf", "hqdn3d=1.2:1.2:5:5", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", "-t", "60.0", "-movflags", "+faststart", OUT])
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", OUT], capture_output=True, text=True, check=True).stdout)
v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]; a = [s for s in pr["streams"] if s["codec_type"] == "audio"][0]
info = {"file": OUT, "duration_s": float(pr["format"]["duration"]), "size_MB": round(int(pr["format"]["size"]) / 1e6, 2),
        "video": f'{v["codec_name"]} ({v.get("profile")}) {v["width"]}x{v["height"]} {v["r_frame_rate"]} fps {v["pix_fmt"]}, decoded frames={v["nb_read_frames"]}',
        "audio": f'{a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]} ch'}
bl = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT, "-vf", "blackdetect=d=0.2:pix_th=0.06", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
info["black_segments"] = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bl)
fr = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT, "-vf", "freezedetect=n=0.001:d=0.5", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
info["frozen_segments"] = re.findall(r"freeze_start: ([\d.]+)", fr)
print(json.dumps(info, indent=1))
assert v["width"] == 1080 and v["height"] == 1920 and v["r_frame_rate"] == "30/1" and int(v["nb_read_frames"]) == 1800 and 59.0 <= info["duration_s"] <= 61.0
json.dump(info, open(R + "out/ffprobe_validation.json", "w"), indent=1); print("VALID")
