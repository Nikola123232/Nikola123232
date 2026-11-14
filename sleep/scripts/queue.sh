#!/bin/bash
# usage: queue.sh "apt:1-190" "brain:191-200" ...   (resume-safe, skips existing PNGs)
cd /home/user/Nikola123232
for job in "$@"; do
  s=${job%%:*}; r=${job#*:}
  find sleep/renders -name "*.png" -size 0 -delete
  echo "=== $job start $(date)" >> sleep/renders/queue.log
  CYCLES_TIME_LIMIT=${TL:-6} SPP=${SPP:-24} nice -n 5 .venv/bin/python sleep/scripts/$s.py -- --render $r > sleep/renders/log_${s}.txt 2>&1
  echo "=== $job end $(date)" >> sleep/renders/queue.log
done
echo "=== done $(date)" >> sleep/renders/queue.log
