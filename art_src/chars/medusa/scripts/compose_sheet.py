"""python3 compose_sheet.py <full_prefix> <closeup_prefix|-> <title> <out.jpg>: full front|side row + optional close-up row"""
import sys, json
from PIL import Image, ImageDraw
full, cu, title, out = sys.argv[1:5]
def row(prefix):
    ims = [Image.open(f'{prefix}.{v}.png').convert('RGB') for v in ('front', 'side')]
    W = sum(i.size[0] for i in ims) + 6; H = max(i.size[1] for i in ims)
    r = Image.new('RGB', (W, H), (70, 70, 70)); x = 0
    for i in ims: r.paste(i, (x, 0)); x += i.size[0] + 6
    d = ImageDraw.Draw(r); d.text((8, H - 16), 'FRONT', fill=(0, 0, 0)); d.text((ims[0].size[0] + 14, H - 16), 'SIDE (her right)', fill=(0, 0, 0))
    return r
rows = [row(full)] + ([row(cu)] if cu != '-' else [])
Wm = max(r.size[0] for r in rows)
rows = [r.resize((Wm, int(r.size[1] * Wm / r.size[0])), Image.LANCZOS) for r in rows]
H = 30 + sum(r.size[1] for r in rows) + 6 * (len(rows) - 1)
s = Image.new('RGB', (Wm, H), (255, 255, 255)); d = ImageDraw.Draw(s)
d.text((10, 8), title, fill=(0, 0, 0)); y = 30
for r in rows: s.paste(r, (0, y)); y += r.size[1] + 6
if s.size[0] > 1600: s = s.resize((1600, int(s.size[1] * 1600 / s.size[0])), Image.LANCZOS)
s.save(out, quality=90); print(out, s.size)
