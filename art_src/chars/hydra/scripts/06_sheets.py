"""python3 06_sheets.py <tests_dir> <sheets_dir>: deform_<pose>.png (front|side|heat) -> sheets/deform_<pose>.jpg with a caption."""
import sys, os, glob, json
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
st = json.load(open(os.path.join(src, 'stretch_stats.json')))
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
except Exception: font = ImageFont.load_default()
for f in sorted(glob.glob(os.path.join(src, 'deform_*.png'))):
    name = os.path.basename(f)[7:-4]
    im = Image.open(f).convert('RGB'); T = im.size[1]
    im = im.crop((0, 0, 2 * T, T))                      # front | side (textured)
    out = Image.new('RGB', (im.size[0], T + 40), 'white'); out.paste(im, (0, 40))
    d = ImageDraw.Draw(out); s = st.get(name, {})
    d.text((10, 8), f'hydra deform test: {name}   front | side   edges stretched > 3x median edge: {s.get("n_grow3", "?")}', fill=(0, 0, 0), font=font)
    out.save(os.path.join(dst, f'deform_{name}.jpg'), quality=88)
    print(name)
