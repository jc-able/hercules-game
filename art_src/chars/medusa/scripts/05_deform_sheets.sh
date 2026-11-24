#!/bin/zsh
# 05: deform proof sheets from the final blend -> sheets/deform_<pose>.jpg
B=/Applications/Blender.app/Contents/MacOS/Blender
S=${0:A:h}; D=${S:h}; T=$D/../../../work/rig_medusa/sheets_tmp; mkdir -p $T $D/sheets
if (( $# )); then P=($@); else P=($S/poses/p*.json); fi   # optional: render only the given pose files
for p in $P; do
  n=${p:t:r}
  desc=$(python3 -c "import json,sys;print(json.load(open('$p'))['_desc'])")
  box=$(python3 -c "import json;print(json.load(open('$p')).get('_box','-6,6,-4.5,9,-0.3,7.5'))")
  cubox=$(python3 -c "import json;print(json.load(open('$p')).get('_cubox','-2.6,2.6,-2.8,1.2,2.2,7.0'))")
  $B -b --factory-startup $D/medusa.blend --python $S/render_views.py -- --out $T/$n --ppm 55 --pose $p --box=$box 2>&1 | grep -E "^Error|Traceback"
  $B -b --factory-startup $D/medusa.blend --python $S/render_views.py -- --out $T/cu_$n --ppm 120 --pose $p --box=$cubox 2>&1 | grep -E "^Error|Traceback"
  python3 $S/compose_sheet.py $T/$n $T/cu_$n "medusa deform test ${n#p?_} - $desc" $D/sheets/deform_${n#p?_}.jpg
done
