#!/bin/bash
# Two-pass loudnorm (-14 LUFS, -1 dBTP) and mux with the rendered picture.
set -e
cd "$(dirname "$0")/.."
J=$(ffmpeg -hide_banner -i public/mix.wav -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -y -hide_banner -loglevel error -i out/video_noaudio.mp4 -i public/mix.wav \
  -af "loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest out/GPT-6.2_Astra_vs_Sol.mp4
echo done
