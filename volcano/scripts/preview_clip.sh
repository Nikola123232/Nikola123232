#!/bin/bash
# usage: preview_clip.sh <script> <name> <f0> <f1> <step>   -> low-res clip volcano/previews/<name>.mp4
cd /home/user/Nikola123232
PCT=${PCT:-35} CYCLES_TIME_LIMIT=${TL:-1.5} .venv/bin/python volcano/scripts/$1.py -- --preview ${5:-1} > volcano/previews/log_$2.txt 2>&1
ffmpeg -y -hide_banner -loglevel error -framerate $((30/${5:-1})) -i volcano/previews/$3/%04d.png -c:v libx264 -pix_fmt yuv420p volcano/previews/$2.mp4 2>/dev/null
