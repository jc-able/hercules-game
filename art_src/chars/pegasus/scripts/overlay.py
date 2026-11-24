"""Compose render_views output into one sheet with grid (+ bones). python3 overlay.py <prefix> <out.png> [--grid 0.1] [--bones] [--labels] [--title T]"""
import json, sys, argparse
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('prefix'); ap.add_argument('out'); ap.add_argument('--grid', type=float, default=0)
ap.add_argument('--bones', action='store_true'); ap.add_argument('--labels', action='store_true')
ap.add_argument('--title', default=''); ap.add_argument('--views', default=None); ap.add_argument('--max', type=int, default=0)
a = ap.parse_args()
info = json.load(open(a.prefix + '.json'))
views = a.views.split(',') if a.views else [k for k in ('front', 'side', 'back', 'top') if k in info]
ims = []
for v in views:
    m = info[v]; im = Image.open(f'{a.prefix}_{v}.png').convert('RGB'); dr = ImageDraw.Draw(im)
    def P(p):
        if v == 'front': uu, vv = p[0], p[2]
        elif v == 'back': uu, vv = -p[0], p[2]
        elif v == 'side': uu, vv = -p[1], p[2]
        elif v.startswith('wing'): uu, vv = p[0] * m['R'][0] + p[1] * m['R'][1], p[2]
        else: uu, vv = p[0], p[1]
        return ((uu - m['u0']) * m['ppm'], (m['v1'] - vv) * m['ppm'])
    if a.grid:
        import math
        g = a.grid
        u = math.ceil(m['u0'] / g) * g
        while (u - m['u0']) * m['ppm'] < m['w']:
            x = (u - m['u0']) * m['ppm']; major = abs(round(u / (g * 5)) * g * 5 - u) < 1e-6
            dr.line([(x, 0), (x, m['h'])], fill=(255, 120, 120) if major else (200, 200, 255), width=1)
            if major: dr.text((x + 2, 2), '%.1f' % u, fill=(200, 0, 0))
            u += g
        vb = m['v1'] - m['h'] / m['ppm']; vv = math.ceil(vb / g) * g
        while vv < m['v1']:
            y = (m['v1'] - vv) * m['ppm']; major = abs(round(vv / (g * 5)) * g * 5 - vv) < 1e-6
            dr.line([(0, y), (m['w'], y)], fill=(255, 120, 120) if major else (200, 200, 255), width=1)
            if major: dr.text((2, y + 2), '%.1f' % vv, fill=(200, 0, 0))
            vv += g
    if a.bones and 'bones' in info:
        for n, (h, t) in info['bones'].items():
            col = (230, 30, 30) if any(k in n for k in ('_l_', '_fl', '_bl')) else (30, 90, 230) if any(k in n for k in ('_r_', '_fr', '_br')) else (20, 160, 20)
            if n in ('root', 'saddle'): col = (160, 0, 160)
            ph, pt = P(h), P(t)
            dr.line([ph, pt], fill=col, width=3)
            dr.ellipse([ph[0] - 4, ph[1] - 4, ph[0] + 4, ph[1] + 4], fill=(0, 0, 0))
            if a.labels:
                dr.text(((ph[0] + pt[0]) / 2 + 3, (ph[1] + pt[1]) / 2), n, fill=(0, 0, 0))
    dr.text((6, m['h'] - 16), v, fill=(0, 0, 0))
    ims.append(im)
W = sum(i.width for i in ims) + 4 * (len(ims) - 1); H = max(i.height for i in ims) + (24 if a.title else 0)
sheet = Image.new('RGB', (W, H), (60, 60, 60)); x = 0
dr = ImageDraw.Draw(sheet)
for i in ims:
    sheet.paste(i, (x, H - i.height)); x += i.width + 4
if a.title: dr.text((8, 5), a.title, fill=(255, 255, 255))
if a.max and max(sheet.size) > a.max:
    sheet.thumbnail((a.max, a.max))
sheet.save(a.out, quality=88)
print('sheet', a.out, sheet.size)
