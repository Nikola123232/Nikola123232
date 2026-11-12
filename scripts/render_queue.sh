#!/bin/bash
# Renders scenes sequentially (resume-safe: existing frames are skipped).
cd /home/user/Nikola123232
while pgrep -f "scripts/scene1.py" >/dev/null && [ "$1" != "now" ]; do sleep 20; done
for s in "$@"; do
  [ "$s" = "now" ] && continue
  find renders -name "*.png" -size 0 -delete
  echo "=== $s $(date)" >> renders/queue.log
  nice -n 5 .venv/bin/python scripts/$s.py > renders/log_$s.txt 2>&1
done
echo "=== done $(date)" >> renders/queue.log
