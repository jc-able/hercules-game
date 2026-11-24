#!/bin/zsh
# top views of chosen poses: run_top.sh <blend> <outdir> pose...
B=/Applications/Blender.app/Contents/MacOS/Blender
S=${0:A:h}; BL=$1; OUT=$2; shift 2
mkdir -p $OUT
for n in $@; do
  $B -b --factory-startup $BL --python $S/render_views.py -- --out $OUT/top_$n --ppm 45 --views top --pose $S/poses/$n.json --box=-6,6,-4,9,-0.5,7.5 2>&1 | grep -E "^Error|Traceback|Exception"
  python3 $S/overlay.py $OUT/top_$n $OUT/top_$n.jpg --views top --grid 1.0 --maxw 1024 >/dev/null
done
