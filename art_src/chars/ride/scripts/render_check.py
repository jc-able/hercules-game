"""Check views of ride.blend (not the sheet): 6 tiles, flat textured Workbench, one JPEG.

  Blender -b --factory-startup --python render_check.py -- <ride.blend> <out.png> [tile_px] [--close]

Tiles: front, right side, left side, top, rear 3/4 from above, front-left 3/4 from below. --close frames the rider only.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
tile = int(argv[2]) if len(argv) > 2 and not argv[2].startswith('--') else 400
close = '--close' in argv
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render]
focus = [o for o in objs if o.name != 'pegasus'] if close else objs
pts = []
for o in focus:
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    M = np.array(ev.matrix_world); pts.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]); ev.to_mesh_clear()
pts = np.concatenate(pts)
c = Vector(((pts.min(0) + pts.max(0)) / 2).tolist())
rad = float(np.linalg.norm(pts - np.array(c), axis=1).max())
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_object_outline = True; sh.show_cavity = False
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (0.35, 0.72, 0.47); sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = tile
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = rad * 2.05; cd.clip_end = 1000
co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
views = [('front', (0, -1, 0)), ('right', (-1, 0, 0)), ('left', (1, 0, 0)), ('top', (0, 0.0001, 1)),
         ('rear34', (0.8, 1, 0.9)), ('frontleft_low', (1, -1, -0.35))]
tiles = []
for name, d in views:
    d = Vector(d).normalized()
    co.location = c + d * 50
    co.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    p = out + f'.{name}.png'
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(tile, tile, 4)[::-1])
    bpy.data.images.remove(im); os.remove(p)
rows = [np.concatenate(tiles[i:i + 3], axis=1) for i in (0, 3)]
sheet = np.concatenate(rows, axis=0)[::-1]
res = bpy.data.images.new('s', sheet.shape[1], sheet.shape[0]); res.pixels = sheet.ravel()
res.filepath_raw = out; res.file_format = 'PNG'; res.save()
print('###CHECK###', out)
