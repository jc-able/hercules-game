"""python3 overlay.py <render.jpg> [out.jpg] [filter_substring] : draw the bones dumped by view.py over the render."""
import json, sys, numpy as np, colorsys
from PIL import Image, ImageDraw
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else src.replace('.jpg', '_b.jpg')
flt = sys.argv[3] if len(sys.argv) > 3 else ''
meta = json.load(open(src + '.json')); im = Image.open(src).convert('RGB'); dr = ImageDraw.Draw(im)
T = meta['tile']; span = meta['span']
names = sorted(meta.get('bones', {}))
for vi, v in enumerate(meta['views']):
    loc, r, u = map(np.array, (v['loc'], v['right'], v['up']))
    def P(p):
        q = np.array(p) - loc
        return (vi * T + T / 2 + q @ r / span * T, T / 2 - q @ u / span * T)
    for i, n in enumerate(names):
        if flt and flt not in n: continue
        h, t, par = meta['bones'][n]
        c = tuple(int(255 * x) for x in colorsys.hsv_to_rgb((i * 0.137) % 1, 1, 0.85))
        a, b = P(h), P(t)
        dr.line([a, b], fill=(0, 0, 0), width=4); dr.line([a, b], fill=c, width=2)
        dr.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], fill=(255, 255, 255), outline=(0, 0, 0))
im.save(out, quality=90); print(out)
