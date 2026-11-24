"""Heat-map renders of vertex-group weights (front, side, back) — one row per group.
  Blender -b --factory-startup --python viz_weights.py -- --blend X.blend --groups a,b,c --out sheet.png [--px 360]
  --groups may contain 'CLASS' to show the colour classes stored in the 'cls' attribute if present.
"""
import bpy, sys, os, argparse
import numpy as np
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('--blend', required=True); ap.add_argument('--groups', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--px', type=int, default=360)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=a.blend)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.data.pose_position = 'REST'
mesh = next(o for o in sc.objects if o.type == 'MESH' and len(o.data.vertices) > 5000)
for o in sc.objects:
    if o.type == 'MESH' and o != mesh:
        o.hide_render = True
me = mesh.data; nv = len(me.vertices)
attr = me.color_attributes.new('wviz', 'FLOAT_COLOR', 'POINT')
me.color_attributes.active_color = attr
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'VERTEX'
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (1, 1, 1); sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = a.px; sc.render.resolution_y = a.px
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.0; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam

def heat(x):
    x = np.clip(x, 0, 1)
    r = np.clip(2 * x - 1, 0, 1); g = 1 - np.abs(2 * x - 1); b = np.clip(1 - 2 * x, 0, 1)
    c = np.stack([r, g, b, np.ones_like(x)], 1)
    c[x < 1e-3] = (0.75, 0.75, 0.75, 1)
    return c

rows = []
for gname in a.groups.split(','):
    if gname == 'CLASS':
        cls = np.zeros(nv, np.int32); me.attributes['cls'].data.foreach_get('value', cls)
        pal = np.array([[0.9, 0.7, 0.55, 1], [0.8, 0.1, 0.1, 1], [0.35, 0.2, 0.05, 1], [0.1, 0.1, 0.1, 1], [0.2, 0.5, 1, 1]])
        col = pal[np.clip(cls, 0, 4)]
    else:
        gi = mesh.vertex_groups[gname].index
        wt = np.zeros(nv)
        for v in me.vertices:
            for g in v.groups:
                if g.group == gi:
                    wt[v.index] = g.weight
        col = heat(wt)
    attr.data.foreach_set('color', col.astype(np.float32).ravel())
    me.update()
    tiles = []
    for view, d in (('front', Vector((0, 1, 0))), ('side', Vector((1, 0, 0))), ('back', Vector((0, -1, 0))), ('side2', Vector((-1, 0, 0)))):
        cam.location = Vector((0, 0, 1.0)) - d * 20
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        p = a.out + f'._{view}.png'; sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p)
        tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(a.px, a.px, 4))
        bpy.data.images.remove(im); os.remove(p)
    rows.append(np.concatenate(tiles, 1))
sheet = np.concatenate(rows[::-1], 0)
H, W = sheet.shape[:2]
res = bpy.data.images.new('s', W, H); res.pixels = sheet.ravel(); res.filepath_raw = a.out; res.file_format = 'PNG'; res.save()
print('###VIZ', a.out, a.groups)
