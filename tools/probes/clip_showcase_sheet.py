#!/usr/bin/env python3
"""Contact sheet of a clip_showcase.gd run: one row per clip (name, length, moving joints), N poses across.
usage: clip_showcase_sheet.py <showcase dir> <out.jpg> [title] [--cell 200] [--motion work/clip_motion.json]"""
import sys, json, pathlib
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:] if not a.startswith('--')]
d = pathlib.Path(args[0]); out = args[1]; title = args[2] if len(args) > 2 else d.name
cell = 200
motion = None
for i, a in enumerate(sys.argv):
    if a == '--cell':
        cell = int(sys.argv[i + 1])
    if a == '--motion':
        motion = json.load(open(sys.argv[i + 1]))
info = json.load(open(d / 'showcase.json'))
n = info['n']
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 15)
    big = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22)
except Exception:
    font = big = ImageFont.load_default()
ch = int(cell * 9 / 16)
label_w = 190
W = label_w + n * cell
H = 40 + len(info['clips']) * (ch + 4)
sheet = Image.new('RGB', (W, H), (18, 18, 20))
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), title, fill=(255, 220, 120), font=big)
mrow = (motion or {}).get(info['id'], {})
for r, c in enumerate(info['clips']):
    y = 40 + r * (ch + 4)
    dr.text((8, y + 6), c['name'], fill=(255, 255, 255), font=font)
    dr.text((8, y + 26), f"{c['length']:.2f} s{' loop' if c['loop'] else ''}", fill=(170, 170, 170), font=font)
    key = next((k for k in mrow if k.lower().endswith(c['name'].lower())), None)
    if key:
        rng = mrow[key]['rng']
        mv = sum(1 for v in rng.values() if v >= 3.0)
        col = (120, 220, 120) if mv >= 0.7 * len(rng) else (255, 190, 90) if mv >= 0.4 * len(rng) else (255, 110, 110)
        dr.text((8, y + 46), f"{mv}/{len(rng)} joints move", fill=col, font=font)
    for i in range(n):
        p = d / f"{c['name']}__{i:02d}.png"
        if p.exists():
            im = Image.open(p).convert('RGB').resize((cell, ch), Image.LANCZOS)
            sheet.paste(im, (label_w + i * cell, y))
sheet.save(out, quality=88)
print(out, sheet.size)
