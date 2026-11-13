#!/bin/bash
# sequential, resume-safe final render:  queue.sh v12 v3 v4 ...
cd /home/user/Nikola123232
for s in "$@"; do
  find volcano/renders -name "*.png" -size 0 -delete
  echo "=== $s start $(date)" >> volcano/renders/queue.log
  CYCLES_TIME_LIMIT=${TL:-5} nice -n 5 .venv/bin/python volcano/scripts/$s.py > volcano/renders/log_$s.txt 2>&1
  echo "=== $s end $(date)" >> volcano/renders/queue.log
done
echo "=== done $(date)" >> volcano/renders/queue.log
