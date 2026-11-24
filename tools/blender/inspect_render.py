"""Import one GLB, print its stats as JSON, and render a 4-view contact sheet (front, side, back, three-quarter).

  Blender -b --factory-startup --python tools/blender/inspect_render.py -- <in.glb> <out.jpg> [tile_px]

Flat textured Workbench render on white, orthographic, auto-framed. Used to judge generated meshes.
"""
import bpy, sys, json, math, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
tile = int(argv[2]) if len(argv) > 2 else 512

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
arms = [o for o in scene.objects if o.type == 'ARMATURE']

dg = bpy.context.evaluated_depsgraph_get()
mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
tris = verts = 0
for o in meshes:
    me = o.data
    me.calc_loop_triangles()
    tris += len(me.loop_triangles); verts += len(me.vertices)
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
        mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
size = mx - mn
centre = (mx + mn) / 2
stats = {
    'file': os.path.basename(src), 'bytes': os.path.getsize(src),
    'meshes': len(meshes), 'verts': verts, 'tris': tris,
    'materials': sorted({m.name for o in meshes for m in o.data.materials if m}),
    'images': [(i.name, i.size[0], i.size[1]) for i in bpy.data.images if i.size[0] > 0],
    'armatures': [(a.name, len(a.data.bones)) for a in arms],
    'bones': [b.name for a in arms for b in a.data.bones][:80],
    'actions': [a.name for a in bpy.data.actions],
    'size_xyz': [round(v, 3) for v in size], 'min': [round(v, 3) for v in mn], 'max': [round(v, 3) for v in mx],
}
print('###STATS###' + json.dumps(stats))

scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
scene.display.render_aa = '8'
world = bpy.data.worlds.new('w'); world.color = (1, 1, 1); scene.world = world
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x = tile; scene.render.resolution_y = tile
scene.render.image_settings.file_format = 'PNG'

cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
span = max(size.x, size.y, size.z) * 1.08
cam_data.ortho_scale = span
cam_data.clip_start = 0.01; cam_data.clip_end = span * 20
views = {'front': (0, -1, 0), 'side': (-1, 0, 0), 'back': (0, 1, 0), 'q34': (-0.7, -0.7, 0.35)}
paths = []
for name, d in views.items():
    d = Vector(d).normalized()
    cam.location = centre + d * span * 5
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    p = out + f'.{name}.png'
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    paths.append(p)

# stitch with Blender's own image API (no Pillow inside Blender)
import numpy as np
W = tile * len(paths)
sheet = np.ones((tile, W, 4), dtype=np.float32)
for i, p in enumerate(paths):
    im = bpy.data.images.load(p)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(tile, tile, 4)
    sheet[:, i * tile:(i + 1) * tile, :] = px
    bpy.data.images.remove(im)
    os.remove(p)
res = bpy.data.images.new('sheet', W, tile)
res.pixels = sheet.ravel()
res.filepath_raw = out
res.file_format = 'JPEG' if out.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
scene.render.image_settings.quality = 88
res.save()
print('###SHEET###' + out)
