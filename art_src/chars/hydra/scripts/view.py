"""Generic check render: flat textured ortho views of a .glb or .blend.
  Blender -b --factory-startup --python view.py -- --in X --out Y.png [--views front,side,back,top,q34,q34b]
     [--box xmin,xmax,ymin,ymax,zmin,zmax] [--tile 512] [--pose pose.json] [--xray] [--bones] [--weights bone_or_group]
pose.json: {"bone": [rx,ry,rz] degrees (armature-space-ish: applied as pose-bone local euler XYZ)}
"""
import bpy, sys, json, math, os, argparse
import numpy as np
from mathutils import Vector, Euler
ap = argparse.ArgumentParser()
ap.add_argument('--in', dest='src'); ap.add_argument('--out')
ap.add_argument('--views', default='front,side'); ap.add_argument('--box', default=None)
ap.add_argument('--tile', type=int, default=512); ap.add_argument('--pose', default=None)
ap.add_argument('--vcol', default=None, help='npz with per-vertex rgb to show instead of texture')
ap.add_argument('--bones', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
if a.src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=a.src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a.src)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH']
arms = [o for o in sc.objects if o.type == 'ARMATURE']
if a.pose and arms:
    exec(open(os.path.join(os.path.dirname(__file__), 'posing.py')).read())
    apply_pose(arms[0], json.load(open(a.pose)))
sh = sc.display.shading
sc.render.engine = 'BLENDER_WORKBENCH'
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
if a.vcol:
    vc = np.load(a.vcol)['rgb']
    me = meshes[0].data
    attr = me.color_attributes.new('chk', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([vc, np.ones((len(vc), 1))], 1).astype(np.float32)
    attr.data.foreach_set('color', rgba.ravel())
    me.color_attributes.active_color = attr
    sh.color_type = 'VERTEX'
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (1, 1, 1); sc.world = w
sc.view_settings.view_transform = 'Standard'
dg = bpy.context.evaluated_depsgraph_get()
if a.box: b = [float(v) for v in a.box.split(',')]; mn = Vector((b[0], b[2], b[4])); mx = Vector((b[1], b[3], b[5]))
else:
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(ev.matrix_world); pts.append(co @ M[:3, :3].T + M[:3, 3]); ev.to_mesh_clear()
    pts = np.concatenate(pts); mn = Vector(pts.min(0)); mx = Vector(pts.max(0))
c = (mn + mx) / 2; size = mx - mn
span = max(size) * 1.06
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = span; cd.clip_start = 0.01; cd.clip_end = span * 30
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
if a.bones and arms:
    arm = arms[0]; arm.show_in_front = True; arm.data.display_type = 'STICK'
V = {'front': (0, -1, 0), 'side': (-1, 0, 0), 'back': (0, 1, 0), 'top': (0, 0, 1), 'right': (1, 0, 0),
     'q34': (-0.7, -0.7, 0.35), 'q34b': (0.6, 0.7, 0.5), 'q34f': (0.7, -0.7, 0.35)}
T = a.tile; sc.render.resolution_x = T; sc.render.resolution_y = T
tiles = []; meta = {'tile': T, 'span': span, 'views': []}
for name in a.views.split(','):
    d = Vector(V[name]).normalized()
    cam.location = c + d * span * 8
    up = 'Y' if name != 'top' else 'Y'
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    R = cam.matrix_world.to_3x3()
    meta['views'].append({'name': name, 'loc': list(cam.location), 'right': list(R.col[0]), 'up': list(R.col[1])})
    p = a.out + f'.{name}.png'; sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(T, T, 4))
    bpy.data.images.remove(im); os.remove(p)
sheet = np.concatenate(tiles, axis=1)
res = bpy.data.images.new('s', sheet.shape[1], T); res.pixels = sheet.ravel()
res.filepath_raw = a.out; res.file_format = 'JPEG' if a.out.endswith('.jpg') else 'PNG'; res.save()
if arms:
    arm = arms[0]; Mw = arm.matrix_world
    meta['bones'] = {pb.name: [list(Mw @ pb.head), list(Mw @ pb.tail), pb.parent.name if pb.parent else None] for pb in arm.pose.bones}
json.dump(meta, open(a.out + '.json', 'w'))
print('###OUT###', a.out)
