#!/bin/zsh
# close-up (upper body) renders of chosen poses: run_closeups.sh <blend> <outdir> pose...
B=/Applications/Blender.app/Contents/MacOS/Blender
S=${0:A:h}; BL=$1; OUT=$2; shift 2
mkdir -p $OUT
for n in $@; do
  $B -b --factory-startup $BL --python $S/render_views.py -- --out $OUT/cu_$n --ppm 110 --pose $S/poses/$n.json --box=-2.6,2.6,-2.6,1.0,2.4,7.0 2>&1 | grep -E "^Error|Traceback|Exception"
  python3 $S/overlay.py $OUT/cu_$n $OUT/cu_$n.jpg --grid 0.5 --maxw 1024 --nobones >/dev/null
done
