#!/bin/bash
cd /home/user/Nikola123232
for r in "$@"; do
  find sub/renders -name "*.png" -size 0 -delete
  echo "=== $r start $(date)" >> sub/renders/queue.log
  CYCLES_TIME_LIMIT=${TL:-3.5} SPP=${SPP:-20} nice -n 5 .venv/bin/python sub/scripts/scene.py -- --render $r > sub/renders/log.txt 2>&1
  echo "=== $r end $(date)" >> sub/renders/queue.log
done
echo "=== done $(date)" >> sub/renders/queue.log
