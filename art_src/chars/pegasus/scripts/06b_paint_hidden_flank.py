"""Step 6b (python3, Pillow): repaint the hidden-flank texels found by 06a_hidden_flank_uv.py.

python3 06b_paint_hidden_flank.py <hidden_uv.npz> <albedo_in.png> <albedo_out.png>
Inside the UV triangles of the flank skin hidden under the wing lobe (no dilation: neighbouring UV islands are
untouched), a texel is junk when it is bluer than the cream skin (b - r > -0.05), dark (luma < 0.62) or saturated.
Junk texels get the mean of the clean flank texels within 8 px (normalised box blur), else the flank median.
The original albedo is kept as <albedo_in>.pre_flank_paint.png once.
"""
import sys, os, shutil, json
import numpy as np
from PIL import Image, ImageDraw

HUV, SRC, OUT = sys.argv[1:4]
d = np.load(HUV); uv = d['uv']
im = Image.open(SRC).convert('RGB'); W, H = im.size
mask = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(mask)
for t in uv:
    dr.polygon([(u * W, (1 - v) * H) for u, v in t], fill=255)
m = np.array(mask) > 0
a = np.array(im).astype(np.float32) / 255
r, g, b = a[..., 0], a[..., 1], a[..., 2]
luma = 0.299 * r + 0.587 * g + 0.114 * b
sat = a.max(-1) - a.min(-1)
junk = m & ((b - r > -0.05) | (luma < 0.62) | (sat > 0.25))
clean = m & ~junk
med = np.median(a[clean], 0) if clean.any() else np.array([0.886, 0.839, 0.788])
def box(x, k):
    c = np.cumsum(np.cumsum(np.pad(x, ((k + 1, k), (k + 1, k))), 0), 1)
    return c[2 * k + 1:, 2 * k + 1:] - c[:-2 * k - 1, 2 * k + 1:] - c[2 * k + 1:, :-2 * k - 1] + c[:-2 * k - 1, :-2 * k - 1]
wsum = box(clean.astype(np.float32), 8)
out = a.copy()
for ch in range(3):
    s = box(a[..., ch] * clean, 8)
    fill = np.where(wsum > 0.5, s / np.maximum(wsum, 1e-6), med[ch])
    out[..., ch] = np.where(junk, fill, a[..., ch])
bak = SRC.replace('.png', '.pre_flank_paint.png')
if os.path.abspath(SRC) == os.path.abspath(OUT) and not os.path.exists(bak):
    shutil.copy2(SRC, bak)
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
print('###PAINT###', json.dumps({'mask_px': int(m.sum()), 'junk_px': int(junk.sum()), 'median': [round(float(v), 3) for v in med]}))
