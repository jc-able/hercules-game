"""python3 contact.py <dir> <out.jpg> <pose1,pose2,...> [views=front,side] [max=1024]"""
import sys, os
from PIL import Image, ImageDraw
d, out, poses = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
views = (sys.argv[4] if len(sys.argv) > 4 else 'front,side').split(',')
mx = int(sys.argv[5]) if len(sys.argv) > 5 else 1024
rows = []
for p in poses:
    ims = [Image.open(os.path.join(d, f'{p}_{v}.png')).convert('RGB') for v in views if os.path.exists(os.path.join(d, f'{p}_{v}.png'))]
    W = sum(i.width for i in ims) + 3 * (len(ims) - 1); H = max(i.height for i in ims)
    r = Image.new('RGB', (W, H), (40, 40, 40)); x = 0
    for i in ims: r.paste(i, (x, 0)); x += i.width + 3
    ImageDraw.Draw(r).text((6, 4), p, fill=(0, 0, 0))
    rows.append(r)
W = max(r.width for r in rows); H = sum(r.height for r in rows) + 3 * (len(rows) - 1)
s = Image.new('RGB', (W, H), (40, 40, 40)); y = 0
for r in rows: s.paste(r, (0, y)); y += r.height + 3
s.thumbnail((mx, mx)); s.save(out, quality=88); print(out, s.size)
