#!/bin/zsh
# Step 6: deform proof sheets (front | side, ortho flat) of every test pose in poses.json -> sheets/deform_<pose>.jpg
cd "${0:A:h}/.."
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python scripts/render_pose.py -- \
  --blend hercules.blend --poses scripts/poses.json --out work/deform --px 800 | grep -E "###POSE|Error"
python3 - <<'PY'
import json, os
from PIL import Image, ImageDraw
st = json.load(open('work/deform/stretch.json'))
for n, s in st.items():
    if n == 'rest':
        continue
    im = Image.open(f'work/deform/{n}.png').convert('RGB')
    d = ImageDraw.Draw(im)
    d.text((12, 10), f'hercules  pose: {n}   front | side (faces right)   max edge stretch x{s["max_stretch"]:.1f}', fill=(0, 0, 0))
    im.save(f'sheets/deform_{n}.jpg', quality=90)
    print('sheets/deform_%s.jpg' % n, im.size)
PY
