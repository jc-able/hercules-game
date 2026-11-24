"""Ortho flat renders (front from -Y, side from -X) of a region, plus posed bone positions as JSON.
Blender -b --factory-startup <blend> --python render_views.py -- --out <prefix> [--box xmin,xmax,ymin,ymax,zmin,zmax]
  [--ppm 60] [--pose <pose.json>] [--views front,side] [--xray]
pose.json: {bone: [rx,ry,rz] degrees (armature-space-ish: applied as pose-bone euler XYZ local)}  (optional)
Writes <prefix>.<view>.png and <prefix>.json (mapping + bones)."""
import bpy, sys, json, argparse, math, os
from mathutils import Vector, Euler
ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--box', default='-2.2,2.2,-1.8,8.8,-0.2,6.8')
ap.add_argument('--ppm', type=float, default=60)
ap.add_argument('--pose', default=None)
ap.add_argument('--views', default='front,side')
ap.add_argument('--alpha', type=float, default=1.0)
ap.add_argument('--vcol', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
x0, x1, y0, y1, z0, z1 = [float(v) for v in a.box.split(',')]
sc = bpy.context.scene
img_abs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'medusa_albedo.png')
for im in bpy.data.images:
    if im.name.startswith('medusa_albedo'):
        im.filepath = img_abs; im.reload()
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm and a.pose:
    pose = json.load(open(a.pose))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from posing import apply_pose
    apply_pose(arm, pose)
bpy.context.view_layer.update()
for o in sc.objects:
    if o.type == 'MESH' and not o.data.materials:
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX' if a.vcol else 'TEXTURE'; sh.show_object_outline = False
if a.alpha < 1:
    sh.show_xray = True; sh.xray_alpha = a.alpha
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (1, 1, 1); sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 1000
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
info = {'box': [x0, x1, y0, y1, z0, z1], 'ppm': a.ppm, 'views': {}}
for v in a.views.split(','):
    if v == 'front':   # camera at -Y looking +Y; screen right = +X
        wd, ht = x1 - x0, z1 - z0
        cam.location = ((x0 + x1) / 2, y0 - 100, (z0 + z1) / 2); d = Vector((0, 1, 0))
    elif v == 'back':  # camera at +Y looking -Y; screen right = -X
        wd, ht = x1 - x0, z1 - z0
        cam.location = ((x0 + x1) / 2, y1 + 100, (z0 + z1) / 2); d = Vector((0, -1, 0))
    elif v == 'top':   # camera above looking down; screen right = -Y, screen up = +X
        wd, ht = y1 - y0, x1 - x0
        cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, z1 + 100); d = None
    else:              # camera at -X looking +X; screen right = -Y
        wd, ht = y1 - y0, z1 - z0
        cam.location = (x0 - 100, (y0 + y1) / 2, (z0 + z1) / 2); d = Vector((1, 0, 0))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler() if d is not None else (0, 0, -math.pi / 2)
    W, H = int(round(wd * a.ppm)), int(round(ht * a.ppm))
    sc.render.resolution_x, sc.render.resolution_y = W, H
    cd.ortho_scale = max(wd, ht)
    sc.render.filepath = f'{a.out}.{v}.png'
    bpy.ops.render.render(write_still=True)
    info['views'][v] = {'w': W, 'h': H}
if arm:
    M = arm.matrix_world
    info['bones'] = {pb.name: {'head': list(M @ pb.head), 'tail': list(M @ pb.tail), 'parent': pb.parent.name if pb.parent else None}
                     for pb in arm.pose.bones}
json.dump(info, open(a.out + '.json', 'w'))
