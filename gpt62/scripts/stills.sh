#!/bin/bash
# usage: stills.sh name cue:+offset ...   (renders half-res stills and a contact sheet)
name=$1; shift; files=()
for spec in "$@"; do
  c=${spec%%:*}; off=${spec#*:}
  fr=$(python3 -c "import json;t=json.load(open('src/timeline.json'));print(round(t['cues']['$c'][0]*30)+int('$off'))")
  out=/tmp/claude-0/stills/${name}_${c}_${off}.png
  npx remotion still src/index.ts Main $out --frame=$fr --scale=0.5 --log=error >/dev/null 2>&1 || echo "FAIL $spec"
  files+=($out)
done
python3 /tmp/claude-0/sheet.py /tmp/claude-0/stills/sheet_$name.png "${files[@]}"
