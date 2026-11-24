#!/usr/bin/env python3
"""Split a character sheet (title + FRONT / SIDE / BACK figures + labels) into one image per view.

Image-to-3D models reconstruct everything in the frame as ONE object, so each view must be its own file.
Finds the three largest connected blobs of non-white pixels (the figures), ignores the title and the
labels, and writes each figure centred on a white square canvas.

usage: crop_views.py <sheet.png> <out_dir> <name> [--canvas 1536] [--order front,side,back]
writes <name>_front.png, <name>_side.png (character's RIGHT side, facing screen-right),
       <name>_back.png, <name>_side_mirror.png (mirrored = LEFT side view) + <name>_views.json
"""
import sys, json, argparse
from collections import deque
import numpy as np
from PIL import Image, ImageOps


def components(mask):
    """4-connected components of a small boolean mask -> (list of (area, x0, y0, x1, y1, label), label image)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    labels = np.zeros(mask.shape, dtype=np.int32)
    out = []
    for y in range(h):
        row = np.nonzero(mask[y] & ~seen[y])[0]
        for x in row:
            if seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            lab = len(out) + 1
            area = 0
            x0 = x1 = x
            y0 = y1 = y
            while q:
                cy, cx = q.popleft()
                labels[cy, cx] = lab
                area += 1
                x0 = min(x0, cx); x1 = max(x1, cx); y0 = min(y0, cy); y1 = max(y1, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append((area, x0, y0, x1, y1, lab))
    return out, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet'); ap.add_argument('out_dir'); ap.add_argument('name')
    ap.add_argument('--canvas', type=int, default=1536)
    ap.add_argument('--ds', type=int, default=3, help='downscale factor for blob finding')
    ap.add_argument('--order', default='front,side,back')
    a = ap.parse_args()

    im = Image.open(a.sheet).convert('RGB')
    W, H = im.size
    arr = np.asarray(im)
    nonwhite = (arr.min(axis=2) < 232)
    ds = a.ds
    hh, ww = H // ds, W // ds
    small = nonwhite[:hh * ds, :ww * ds].reshape(hh, ds, ww, ds).any(axis=(1, 3))
    allc, labels = components(small)
    comps = sorted(allc, reverse=True)[:3]
    labels_up = np.kron(labels, np.ones((ds, ds), dtype=np.int32))  # back to full resolution
    work = arr[:hh * ds, :ww * ds].copy()
    comps = sorted(comps, key=lambda c: c[1])  # left to right
    names = a.order.split(',')
    info = {'sheet': a.sheet, 'size': [W, H], 'views': {}}
    for (area, x0, y0, x1, y1, lab), view in zip(comps, names):
        pad = 6
        box = tuple(int(v) for v in (max(0, x0 * ds - pad), max(0, y0 * ds - pad),
                                     min(W, (x1 + 1) * ds + pad), min(H, (y1 + 1) * ds + pad)))
        # blank everything that belongs to another blob (bounding boxes of neighbours can overlap)
        mine = work.copy()
        other = (labels_up != lab) & (labels_up != 0)
        mine[other] = 255
        crop = Image.fromarray(mine).crop(box)
        cw, ch = crop.size
        C = a.canvas
        margin = int(C * 0.06)
        scale = min((C - 2 * margin) / cw, (C - 2 * margin) / ch)
        nw, nh = max(1, round(cw * scale)), max(1, round(ch * scale))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new('RGB', (C, C), (255, 255, 255))
        canvas.paste(crop, ((C - nw) // 2, (C - nh) // 2))
        p = f'{a.out_dir}/{a.name}_{view}.png'
        canvas.save(p)
        info['views'][view] = {'box': box, 'file': p, 'px': [cw, ch]}
        if view == 'side':
            ImageOps.mirror(canvas).save(f'{a.out_dir}/{a.name}_side_mirror.png')
    json.dump(info, open(f'{a.out_dir}/{a.name}_views.json', 'w'), indent=1)
    print(a.name, {k: v['box'] for k, v in info['views'].items()})


if __name__ == '__main__':
    main()
