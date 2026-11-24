"""python3 overlay.py <prefix> <out.jpg> [--grid 0.5] [--pts pts.json] [--nobones]
Composite front|side panels, draw a metre grid, bones (if in json) and extra points."""
import json, sys, argparse
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('prefix'); ap.add_argument('out')
ap.add_argument('--grid', type=float, default=0.5); ap.add_argument('--pts', default=None)
ap.add_argument('--nobones', action='store_true'); ap.add_argument('--views', default='front,side')
ap.add_argument('--maxw', type=int, default=1600)
a = ap.parse_args()
info = json.load(open(a.prefix + '.json'))
x0, x1, y0, y1, z0, z1 = info['box']; ppm = info['ppm']
pts = json.load(open(a.pts)) if a.pts else []
tiles = []
for v in a.views.split(','):
    im = Image.open(f'{a.prefix}.{v}.png').convert('RGB')
    W, H = im.size
    dr = ImageDraw.Draw(im)
    def P(p):
        if v == 'front': return ((p[0] - x0) * ppm, (z1 - p[2]) * ppm)
        if v == 'back': return ((x1 - p[0]) * ppm, (z1 - p[2]) * ppm)
        if v == 'top': return ((y1 - p[1]) * ppm, (x1 - p[0]) * ppm)
        return ((y1 - p[1]) * ppm, (z1 - p[2]) * ppm)
    lo, hi = (x0, x1) if v in ('front', 'back') else (y0, y1)
    if v == 'top':
        dr.text((10, 10), 'TOP (up=+X)', fill=(0, 0, 0))
    import math
    g = math.ceil(lo / a.grid) * a.grid
    while g <= hi:
        px = (g - x0) * ppm if v == 'front' else (x1 - g) * ppm if v == 'back' else (y1 - g) * ppm
        dr.line([(px, 0), (px, H)], fill=(200, 200, 255) if abs(g % 1) > 1e-6 else (120, 120, 255), width=1)
        dr.text((px + 2, 2), f'{g:.1f}', fill=(0, 0, 200))
        g += a.grid
    g = math.ceil(z0 / a.grid) * a.grid
    while g <= z1 and v != 'top':
        py = (z1 - g) * ppm
        dr.line([(0, py), (W, py)], fill=(200, 200, 255) if abs(g % 1) > 1e-6 else (120, 120, 255), width=1)
        dr.text((2, py + 2), f'{g:.1f}', fill=(0, 0, 200))
        g += a.grid
    if 'bones' in info and not a.nobones:
        for n, b in info['bones'].items():
            h, t = P(b['head']), P(b['tail'])
            col = (255, 0, 0) if n.endswith('_l') or '_l_' in n else (0, 160, 255) if n.endswith('_r') or '_r_' in n else (255, 0, 255) if n.startswith(('hair', 'snake')) else (0, 0, 0)
            dr.line([h, t], fill=col, width=3)
            dr.ellipse([h[0] - 4, h[1] - 4, h[0] + 4, h[1] + 4], outline=col, width=2)
    for p in pts:
        q = P(p[:3]); c = tuple(p[3]) if len(p) > 3 else (255, 0, 0)
        dr.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=c)
    dr.text((10, H - 20), v.upper(), fill=(0, 0, 0))
    tiles.append(im)
W = sum(t.size[0] for t in tiles) + 6 * (len(tiles) - 1); H = max(t.size[1] for t in tiles)
out = Image.new('RGB', (W, H), (60, 60, 60)); x = 0
for t in tiles: out.paste(t, (x, 0)); x += t.size[0] + 6
if out.size[0] > a.maxw:
    s = a.maxw / out.size[0]; out = out.resize((a.maxw, int(H * s)), Image.LANCZOS)
out.save(a.out, quality=88)
print(out.size)
