"""Ride proof strip: video frames (tools/ak frames, aligned to the sheet framing) on top, our ride_check.blend renders
below.  python3 check/make_strip.py <clip_dir> <keyframes_dir>
Writes strip_ride.jpg (8 keys, whole frame), strip_ride_close_a.jpg / _b.jpg (rider close-ups, 4 keys each),
check/iou.json (silhouette IoU per key: whole panel and rider box)."""
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageDraw
C, KF = sys.argv[1], sys.argv[2]
ck = json.load(open(os.path.join(C, 'check/check_keys.json')))
vids = sorted(glob.glob(os.path.join(KF, 'f0*_t*.png')))[:8]
rens = [os.path.join(C, f"check/render_f{k['frame']:02d}.png") for k in ck['frames']]
cam = json.load(open(os.path.join(C, 'cam.json'))); FW = cam['front_w']
FB = (215, 185, 445, 470); SB = (820, 185, 1090, 470)        # rider boxes (sheet px) front / side
def mask(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    return ~((a[..., 1] - np.maximum(a[..., 0], a[..., 2])) > 25)
def iou(a, b):
    u = (a | b).sum(); return round(float((a & b).sum() / u), 4) if u else None
ious = []
for k, v, r in zip(ck['frames'], vids, rens):
    mv, mr = mask(Image.open(v)), mask(Image.open(r))
    row = {'clip_t': round(k['frame'] / 24, 3), 'video': os.path.basename(v),
           'front': iou(mv[:, :FW], mr[:, :FW]), 'side': iou(mv[:, FW:], mr[:, FW:]),
           'rider_front': iou(mv[FB[1]:FB[3], FB[0]:FB[2]], mr[FB[1]:FB[3], FB[0]:FB[2]]),
           'rider_side': iou(mv[SB[1]:SB[3], SB[0]:SB[2]], mr[SB[1]:SB[3], SB[0]:SB[2]])}
    ious.append(row)
json.dump(ious, open(os.path.join(C, 'check/iou.json'), 'w'), indent=1)
lab = lambda im, s: (ImageDraw.Draw(im).rectangle((0, 0, 8 * len(s) + 8, 14), fill=(0, 0, 0)),
                     ImageDraw.Draw(im).text((4, 2), s, fill=(255, 255, 0)))
# 1) whole frames: 8 columns, video row over render row
tw, th = 480, 270
S = Image.new('RGB', (tw * 8, th * 2), (0, 0, 0))
for i, (k, v, r) in enumerate(zip(ck['frames'], vids, rens)):
    a = Image.open(v).convert('RGB').resize((tw, th)); b = Image.open(r).convert('RGB').resize((tw, th))
    lab(a, f"video t={k['video_t']:.3f}"); lab(b, f"ours clip t={k['frame'] / 24:.3f}")
    S.paste(a, (i * tw, 0)); S.paste(b, (i * tw, th))
S.save(os.path.join(C, 'strip_ride.jpg'), quality=88)
# small overview for reading: 2 rows of 4 keys, each key = video over ours
O = Image.new('RGB', (1024, 4 * 144), (0, 0, 0))
for i in range(8):
    a = S.crop((i * tw, 0, (i + 1) * tw, th)).resize((256, 144)); b = S.crop((i * tw, th, (i + 1) * tw, 2 * th)).resize((256, 144))
    O.paste(a, ((i % 4) * 256, (i // 4) * 288)); O.paste(b, ((i % 4) * 256, (i // 4) * 288 + 144))
O.save(os.path.join(C, 'check/strip_overview_small.jpg'), quality=88)
# 2) rider close-ups: tile = [video front | video side] over [ours front | ours side]
def tile(k, v, r):
    iv, ir = Image.open(v).convert('RGB'), Image.open(r).convert('RGB')
    w = (FB[2] - FB[0]) + (SB[2] - SB[0]) + 4; h = (FB[3] - FB[1])
    T = Image.new('RGB', (w, 2 * h + 4), (0, 0, 0))
    for row, im in enumerate((iv, ir)):
        T.paste(im.crop(FB), (0, row * (h + 4))); T.paste(im.crop(SB), (FB[2] - FB[0] + 4, row * (h + 4)))
    lab(T, f"t={k['frame'] / 24:.3f} video / ours")
    return T
for part, idx in (('a', range(0, 4)), ('b', range(4, 8))):
    ts = [tile(ck['frames'][i], vids[i], rens[i]) for i in idx]
    w, h = ts[0].size
    G = Image.new('RGB', (2 * w + 6, 2 * h + 6), (60, 60, 60))
    for j, t in enumerate(ts):
        G.paste(t, ((j % 2) * (w + 6), (j // 2) * (h + 6)))
    G.thumbnail((1024, 1024)); G.save(os.path.join(C, f'strip_ride_close_{part}.jpg'), quality=90)
print(json.dumps(ious))
