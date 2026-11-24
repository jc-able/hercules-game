"""Ortho flat render of a blend (optionally posed) in fixed framing + bone positions for overlays.

Blender -b --factory-startup --python render_views.py -- --blend X.blend --out prefix [--views front,side,top]
        [--pose pose.json] [--ppm 300] [--bounds x0,y0,z0,x1,y1,z1] [--bg r,g,b] [--xray]
Writes <prefix>_<view>.png and <prefix>.json {view: {u0, v1, ppm, w, h, axes}, bones: {name: [head, tail]}}.
Views: front (cam -Y, u=x, v=z), side (cam -X, u=-y, v=z: faces screen-right), top (cam +Z, u=x, v=y),
back (cam +Y, u=-x, v=z).
pose.json: {bone: [rx, ry, rz]} degrees, XYZ euler in the bone's local (pose) space.
"""
import bpy, sys, json, math, argparse
import numpy as np
from mathutils import Vector, Euler

ap = argparse.ArgumentParser()
ap.add_argument('--blend', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--views', default='front,side'); ap.add_argument('--pose', default=None)
ap.add_argument('--ppm', type=float, default=300); ap.add_argument('--bounds', default='-1.3,-1.8,-0.05,1.3,1.5,3.1')
ap.add_argument('--bg', default='1,1,1'); ap.add_argument('--clipx', type=float, default=None); ap.add_argument('--vcol', action='store_true'); ap.add_argument('--rest', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=a.blend)
sc = bpy.context.scene
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm:
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    if a.pose:
        pose = json.load(open(a.pose))
        for bn, r in pose.items():
            if bn in arm.pose.bones:
                arm.pose.bones[bn].rotation_euler = [math.radians(v) for v in r]
    arm.data.pose_position = 'REST' if a.rest else 'POSE'
bpy.context.view_layer.update()
if a.clipx is not None:
    import bmesh
    for o in [o for o in sc.objects if o.type == 'MESH']:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < a.clipx], context='VERTS')
        bm.to_mesh(o.data); bm.free()

b = [float(v) for v in a.bounds.split(',')]
x0, y0, z0, x1, y1, z1 = b
bg = [float(v) for v in a.bg.split(',')]
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX' if a.vcol else 'TEXTURE'; sh.show_object_outline = False
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = bg; sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('vcam'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 1000
cam = bpy.data.objects.new('vcam', cd); sc.collection.objects.link(cam); sc.camera = cam
info = {}
D = 100.0
for v in a.views.split(','):
    if v == 'front':
        ur, vr = (x0, x1), (z0, z1); loc = lambda uc, vc: Vector((uc, y0 - D, vc)); d = Vector((0, 1, 0)); up = Vector((0, 0, 1))
    elif v == 'back':
        ur, vr = (-x1, -x0), (z0, z1); loc = lambda uc, vc: Vector((-uc, y1 + D, vc)); d = Vector((0, -1, 0)); up = Vector((0, 0, 1))
    elif v == 'side':
        ur, vr = (-y1, -y0), (z0, z1); loc = lambda uc, vc: Vector((x0 - D, -uc, vc)); d = Vector((1, 0, 0)); up = Vector((0, 0, 1))
    elif v in ('wingl', 'wingr'):
        sx = 1 if v == 'wingl' else -1
        d = Vector((-0.869 * sx, 0.495, 0)); R = Vector((0.495, 0.869 * sx, 0))
        us = [x0 * R.x + y0 * R.y, x1 * R.x + y0 * R.y, x0 * R.x + y1 * R.y, x1 * R.x + y1 * R.y]
        ur, vr = (min(us), max(us)), (z0, z1); up = Vector((0, 0, 1))
        loc = lambda uc, vc, R=R, d=d: R * uc + Vector((0, 0, vc)) - d * D
    elif v == 'top':
        ur, vr = (x0, x1), (y0, y1); loc = lambda uc, vc: Vector((uc, vc, z1 + D)); d = Vector((0, 0, -1)); up = Vector((0, 1, 0))
    W = int(round((ur[1] - ur[0]) * a.ppm)); H = int(round((vr[1] - vr[0]) * a.ppm))
    sc.render.resolution_x = W; sc.render.resolution_y = H
    cd.ortho_scale = max(W, H) / a.ppm
    cam.location = loc((ur[0] + ur[1]) / 2, (vr[0] + vr[1]) / 2)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y' if up.y == 0 else 'Y').to_euler()
    if v == 'top':
        # look down with +Y as screen up
        cam.rotation_euler = Euler((0, 0, 0))
    sc.render.filepath = f'{a.out}_{v}.png'
    bpy.ops.render.render(write_still=True)
    info[v] = {'u0': ur[0], 'v1': vr[1], 'ppm': a.ppm, 'w': W, 'h': H, 'R': list(R) if v.startswith('wing') else None}
if arm:
    M = arm.matrix_world
    info['bones'] = {pb.name: [list(M @ pb.head), list(M @ pb.tail)] for pb in arm.pose.bones}
json.dump(info, open(a.out + '.json', 'w'))
print('###VIEWS###', a.out)
