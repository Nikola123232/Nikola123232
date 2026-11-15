"""Final assembly: composite -> loudness-normalised audio -> mux -> ffprobe + black/freeze checks."""
import subprocess, json, sys, os, re
sys.path.insert(0, "/home/user/Nikola123232/sub/scripts")
from tl import *
R = "/home/user/Nikola123232/sub/"; OUT = R + "out/submarine_implosion_short.mp4"
def run(cmd): print("+", " ".join(cmd[:5]), "...", flush=True); subprocess.run(cmd, check=True)
missing = [f for f in range(1, NF + 1) if not os.path.exists(R + f"renders/main/{f:04d}.png") or os.path.getsize(R + f"renders/main/{f:04d}.png") == 0]
print("source frames missing:", len(missing), missing[:5])
if missing and "--allow-missing" not in sys.argv: sys.exit("render incomplete")
if "--skip-video" not in sys.argv: run(["python3", R + "scripts/composite.py", "--encode"])
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", R + "audio/mix.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "48000", R + "audio/mix_norm.wav"])
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", R + "out/video_noaudio.mp4", "-i", R + "audio/mix_norm.wav", "-map", "0:v:0", "-map", "1:a:0",
     "-vf", "hqdn3d=1.0:1.0:4:4", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", "-t", f"{NF / 30.0:.3f}", "-movflags", "+faststart", OUT])
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", OUT], capture_output=True, text=True, check=True).stdout)
v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]; a = [s for s in pr["streams"] if s["codec_type"] == "audio"][0]
info = {"file": OUT, "duration_s": float(pr["format"]["duration"]), "size_MB": round(int(pr["format"]["size"]) / 1e6, 2),
        "video": f'{v["codec_name"]} ({v.get("profile")}) {v["width"]}x{v["height"]} {v["r_frame_rate"]} fps {v["pix_fmt"]}, decoded frames={v["nb_read_frames"]}', "audio": f'{a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]} ch'}
bl = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT, "-vf", "blackdetect=d=0.1:pix_th=0.06", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
info["black_segments"] = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bl)
ld = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT, "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
m = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld); info["integrated_LUFS"] = m[-1] if m else None
print(json.dumps(info, indent=1))
assert v["width"] == 1080 and v["height"] == 1920 and v["r_frame_rate"] == "30/1" and int(v["nb_read_frames"]) == NF and 35.0 <= info["duration_s"] <= 40.0
json.dump(info, open(R + "out/ffprobe_validation.json", "w"), indent=1); print("VALID")
