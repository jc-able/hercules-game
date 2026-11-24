"""contact.py out.jpg cols maxw img1 img2 ... -> grid contact sheet with labels"""
import sys, os
from PIL import Image, ImageDraw
out, cols, maxw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); ims = sys.argv[4:]
tiles = [Image.open(p).convert('RGB') for p in ims]
w, h = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (w * cols, h * rows), 'white'); d = ImageDraw.Draw(S)
for i, (t, p) in enumerate(zip(tiles, ims)):
    x, y = (i % cols) * w, (i // cols) * h; S.paste(t, (x, y)); d.text((x + 8, y + 6), os.path.basename(p).rsplit('.', 1)[0], fill=(0, 0, 0))
S.thumbnail((maxw, maxw)); S.save(out, quality=88); print(out, S.size)
