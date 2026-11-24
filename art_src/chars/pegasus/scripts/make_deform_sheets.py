"""python3 make_deform_sheets.py <render_dir> <stretch.txt> <out_dir> : sheets/deform_<pose>.jpg (front | side [| top]) + deform_overview.jpg"""
import sys, os, json
from PIL import Image, ImageDraw
rd, st, od = sys.argv[1:4]
poses = json.load(open(os.path.join(os.path.dirname(__file__), 'poses.json')))
stats = {l.split()[0]: l.strip() for l in open(st)}
os.makedirs(od, exist_ok=True)
thumbs = []
for p, spec in poses.items():
    if p == 'rest': continue
    ims = [Image.open(os.path.join(rd, f'{p}_{v}.png')).convert('RGB') for v in ('front', 'side', 'top') if os.path.exists(os.path.join(rd, f'{p}_{v}.png'))]
    W = sum(i.width for i in ims) + 4 * (len(ims) - 1); H = max(i.height for i in ims) + 44
    s = Image.new('RGB', (W, H), (30, 30, 30)); x = 0
    for i in ims: s.paste(i, (x, 44)); x += i.width + 4
    d = ImageDraw.Draw(s)
    d.text((8, 4), f'pegasus deform test: {p}   (views: front | side' + (' | top' if len(ims) > 2 else '') + ')', fill=(255, 255, 255))
    keys = ', '.join(f'{k} {v[:3]}' for k, v in spec.items() if not k.startswith('_'))
    d.text((8, 18), keys[:230], fill=(200, 200, 200))
    d.text((8, 30), 'edge stretch: ' + stats.get(p, ''), fill=(200, 200, 120))
    s.thumbnail((1600, 1600))
    s.save(os.path.join(od, f'deform_{p}.jpg'), quality=88)
    t = ims[1].copy(); t.thumbnail((400, 400)); f = ims[0].copy(); f.thumbnail((400, 400))
    thumbs.append((p, f, t))
# overview: 2 columns of (front, side) per pose
cw = max(f.width + t.width for _, f, t in thumbs) + 8; ch = max(max(f.height, t.height) for _, f, t in thumbs) + 16
cols = 2; rows = (len(thumbs) + 1) // 2
ov = Image.new('RGB', (cw * cols, ch * rows), (30, 30, 30)); d = ImageDraw.Draw(ov)
for k, (p, f, t) in enumerate(thumbs):
    x0 = (k % cols) * cw; y0 = (k // cols) * ch
    ov.paste(f, (x0, y0 + 14)); ov.paste(t, (x0 + f.width + 4, y0 + 14)); d.text((x0 + 4, y0 + 1), p, fill=(255, 255, 255))
ov.thumbnail((1600, 1600)); ov.save(os.path.join(od, 'deform_overview.jpg'), quality=88)
print('sheets', len(thumbs))
