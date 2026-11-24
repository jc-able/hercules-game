"""autocrop.py out.jpg height img... : crop each panel (front|side halves) to content, scale to height, tile."""
import sys, numpy as np
from PIL import Image
out, H = sys.argv[1], int(sys.argv[2]); tiles = []
for p in sys.argv[3:]:
    im = Image.open(p).convert('RGB'); w, h = im.size
    for half in (im.crop((0, 0, w // 2, h)), im.crop((w // 2, 0, w, h))):
        a = np.asarray(half); m = (a < 240).any(2); m[:, :3] = False; m[:, -3:] = False
        ys, xs = np.where(m)
        c = half.crop((max(0, xs.min() - 6), max(0, ys.min() - 6), xs.max() + 6, ys.max() + 6))
        c = c.resize((int(c.width * H / c.height), H)); tiles.append(c)
W = sum(t.width for t in tiles) + 4 * len(tiles)
S = Image.new('RGB', (W, H), 'white'); x = 0
for t in tiles:
    S.paste(t, (x, 0)); x += t.width + 4
S.thumbnail((1600, 1600)); S.save(out, quality=88); print(out, S.size)
