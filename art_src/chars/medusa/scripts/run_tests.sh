#!/bin/zsh
# render every pose in scripts/poses on a blend: run_tests.sh <blend> <outdir> [ppm]
B=/Applications/Blender.app/Contents/MacOS/Blender
S=${0:A:h}; BL=$1; OUT=$2; PPM=${3:-45}
mkdir -p $OUT
for p in $S/poses/*.json; do
  n=${p:t:r}
  $B -b --factory-startup $BL --python $S/render_views.py -- --out $OUT/$n --ppm $PPM --pose $p --box=-6,6,-4,9,-0.5,7.5 2>&1 | grep -E "^Error|Traceback|Exception"
  python3 $S/overlay.py $OUT/$n $OUT/$n.jpg --grid 1.0 --maxw 1100 >/dev/null
done
