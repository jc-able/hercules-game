"""Builds tools/animkit/doc/pose_axes.jpg (the sign picture of docs/ANIM_PIPELINE.md).
python3 tools/animkit/doc/make_axes_figure.py <char.blend> <cam.json>"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import akimg as I
from PIL import Image, ImageDraw

blend, cam = sys.argv[1], sys.argv[2]
AK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ak')
td = tempfile.mkdtemp()
cases = [('rest: every angle 0', {}),
         ('LeftArm ry -60: counter-clockwise in FRONT', {'LeftArm': {'ry': -60}}),
         ('RightArm rx -80: counter-clockwise in SIDE = forward', {'RightArm': {'rx': -80}}),
         ('LeftUpLeg rx +40: clockwise in SIDE = back', {'LeftUpLeg': {'rx': 40}}),
         ('Spine02 rx +25: lean forward (child bones follow)', {'Spine02': {'rx': 25}}),
         ('Head rz +40: turn to its own left (seen from above: CCW)', {'Head': {'rz': 40}})]
cells = []
for i, (title, bones) in enumerate(cases):
    pj = os.path.join(td, f'p{i}.json'); json.dump({'bones': bones}, open(pj, 'w'))
    rp = os.path.join(td, f'r{i}.png')
    subprocess.run([sys.executable, AK, 'pose', blend, '--cam', cam, '--pose', pj, '--out', os.path.join(td, 'x.jpg'),
                    '--render-out', rp], check=True, capture_output=True)
    im = Image.open(rp).convert('RGB')
    c = I.load_cam(cam)
    im = I.crop_panels(im, (int(c['height'] * 0.12), c['height'], (int(c['front_w'] * 0.15), int(c['front_w'] * 0.85)),
                            (c['front_w'] + int(c['side_w'] * 0.1), c['width'] - int(c['side_w'] * 0.1))))
    d = ImageDraw.Draw(im)
    I.text(d, (8, 6), title, 26)
    I.text(d, (8, im.size[1] - 34), 'FRONT (its left = screen right)', 20)
    I.text(d, (im.size[0] - 8, im.size[1] - 34), 'SIDE (faces right)', 20, anchor='ra')
    cells.append(im)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pose_axes.jpg')
I.save_jpg(I.grid(cells, 3, 520), out)
print(out)
