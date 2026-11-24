"""Pillow scatter of the vertex cloud (front X-Z and side Y-Z) with a 0.5 m grid; optional joint markers json.
python3 scatter_view.py mesh.npz out.png [joints.json]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); co = d['co']
ppm = 110
def panel(a, b, xr, zr):
    W = int((xr[1]-xr[0])*ppm); Hh = int((zr[1]-zr[0])*ppm)
    im = Image.new('RGB', (W, Hh), 'white'); dr = ImageDraw.Draw(im)
    for g in np.arange(np.ceil(xr[0]*2)/2, xr[1], 0.5):
        x = (g-xr[0])*ppm; dr.line([(x,0),(x,Hh)], fill=(200,220,255) if g % 1 else (120,160,255))
    for g in np.arange(0, zr[1], 0.5):
        y = Hh-(g-zr[0])*ppm; dr.line([(0,y),(W,y)], fill=(200,220,255) if g % 1 else (120,160,255))
    px = ((co[:,a]-xr[0])*ppm).astype(int); py = (Hh-(co[:,2]-zr[0])*ppm).astype(int)
    arr = np.array(im)
    ok = (px>=0)&(px<W)&(py>=0)&(py<Hh)
    arr[py[ok], px[ok]] = (60,60,60)
    return Image.fromarray(arr), (lambda p: ((p[a]-xr[0])*ppm, Hh-(p[2]-zr[0])*ppm))
f, ff = panel(0, 2, (-4.2, 4.2), (0, 8.2))
s, sf = panel(1, 2, (-1.4, 1.6), (0, 8.2))
if len(sys.argv) > 3:
    J = json.load(open(sys.argv[3]))
    for im, fn in ((f, ff), (s, sf)):
        dr = ImageDraw.Draw(im)
        for b in J['bones']:
            h = fn(b['head']); t = fn(b['tail'])
            dr.line([h, t], fill=(230,30,30) if b['name'].endswith('_l') else (30,160,30) if b['name'].endswith('_r') else (30,30,230), width=4)
            dr.ellipse([h[0]-6,h[1]-6,h[0]+6,h[1]+6], outline=(0,0,0), width=2)
im = Image.new('RGB', (f.width+s.width+10, f.height), 'black'); im.paste(f,(0,0)); im.paste(s,(f.width+10,0))
im.thumbnail((1024,1024)); im.save(sys.argv[2])
