"""Render the FRONT | SIDE split-screen sheet of a 3D asset (the owner's animation-reference method).

  Blender -b --factory-startup --python tools/blender/render_split_sheet.py -- \
      --in <model.glb|.blend> --out <sheet.png> [--cam <cam.json>] [--size 1280x720] [--bg 1,1,1]
      [--mw 1.6] [--mh 1.25] [--ground 0.08] [--rest] [--frame N] [--extra <prop.glb> ...]

Both panels are orthographic at the SAME scale (pixels per metre). Left = front view (camera in front of the
character, looking at its face). Right = side view from the character's right side, so it faces screen-right
(same as the owner's character sheets). `--mw` / `--mh` leave room around the rest pose for the motion.
Writes <cam.json> with everything needed to render later poses with identical framing.
With `--cam` pointing at an existing file the framing is READ from it instead (so every later render matches).
"""
import bpy, sys, json, os, argparse
import numpy as np
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('--in', dest='src', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--cam', default=None)
ap.add_argument('--size', default='1280x720')
ap.add_argument('--bg', default='1,1,1')
ap.add_argument('--mw', type=float, default=1.6)
ap.add_argument('--mh', type=float, default=1.25)
ap.add_argument('--ground', type=float, default=0.08, help='ground line height as a fraction of the frame height')
ap.add_argument('--rest', action='store_true')
ap.add_argument('--frame', type=int, default=None)
ap.add_argument('--reuse', action='store_true', help='read framing from --cam instead of computing it')
ap.add_argument('--env', default=None, help='motion envelope in metres around the root (feet centre): half_width,back,front,top '
                                            '- front panel shows x in [-half_width, +half_width]; side panel shows from `front` m '
                                            'in front of the character to `back` m behind it; `top` = highest point reached')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
W, H = [int(v) for v in a.size.split('x')]
bg = [float(v) for v in a.bg.split(',')]

if a.src.lower().endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=a.src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.src)
scene = bpy.context.scene
for arm in [o for o in scene.objects if o.type == 'ARMATURE']:
    if a.rest:
        arm.data.pose_position = 'REST'
if a.frame is not None:
    scene.frame_set(a.frame)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

# skip helper meshes (bone custom shapes such as Meshy's 'Icosphere': no material) and keep them out of the render
shapes = {pb.custom_shape for arm in scene.objects if arm.type == 'ARMATURE' for pb in arm.pose.bones if pb.custom_shape}
for o in scene.objects:
    if o.type == 'MESH' and (o in shapes or not [m for m in o.data.materials if m]):
        o.hide_render = True
meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render]
mn = np.array([1e9] * 3); mx = np.array([-1e9] * 3)
for o in meshes:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world)
    wco = co @ M[:3, :3].T + M[:3, 3]
    mn = np.minimum(mn, wco.min(axis=0)); mx = np.maximum(mx, wco.max(axis=0))
    ev.to_mesh_clear()
size = mx - mn

if a.reuse and a.cam and os.path.exists(a.cam):
    cam = json.load(open(a.cam))
    ppm = cam['ppm']; fw = cam['front_w']; sw = cam['side_w']; cx = cam['centre_x']; cy = cam['centre_y']; z0 = cam['ground_z']
    bg = cam.get('bg', bg); W = cam['width']; H = cam['height']
else:
    # each panel is at least 0.9 x the height wide, so limbs and steps have room in the narrow view too
    need_front = max(size[0] * a.mw, size[2] * 0.9)
    need_side = max(size[1] * a.mw, size[2] * 0.9)
    need_h = size[2] * a.mh / (1.0 - a.ground - 0.04)
    ppm = min(W / (need_front + need_side), H / need_h)
    fw = int(round(W * need_front / (need_front + need_side) / 2) * 2)
    sw = W - fw
    cx = float((mn[0] + mx[0]) / 2); cy = float((mn[1] + mx[1]) / 2); z0 = float(mn[2])
    if a.env:
        hw, back, front, top = [float(v) for v in a.env.split(',')]
        ppm = min(W / (2 * hw + back + front), H * (1.0 - a.ground - 0.02) / top)
        fw = int(round(W * 2 * hw / (2 * hw + back + front) / 2) * 2)
        sw = W - fw
        cx = 0.0                      # front panel centred on the root
        cy = (back - front) / 2.0     # character faces -Y: more room in front puts it left of the side panel centre
        z0 = 0.0
    cam = {'width': W, 'height': H, 'ppm': ppm, 'front_w': fw, 'side_w': sw, 'centre_x': cx, 'centre_y': cy,
           'ground_z': z0, 'ground_frac': a.ground, 'bg': bg, 'rest_size': [float(v) for v in size],
           'note': 'left panel = front view (camera at -Y looking +Y), right panel = side view (camera at -X looking +X, character faces screen-right)'}
    if a.cam:
        json.dump(cam, open(a.cam, 'w'), indent=1)
ground_frac = cam.get('ground_frac', a.ground)

scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
scene.display.render_aa = '8'
world = bpy.data.worlds.new('w'); world.color = bg; scene.world = world
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('akcam'); cd.type = 'ORTHO'
co = bpy.data.objects.new('akcam', cd); scene.collection.objects.link(co); scene.camera = co
cd.clip_start = 0.01; cd.clip_end = 1000

zc = z0 + (0.5 - ground_frac) * H / ppm      # camera centre height so that the ground sits at ground_frac from the bottom
dist = 200.0
tiles = []
for name, pw, loc, rot_dir, centre in (
        ('front', fw, Vector((cx, cy - dist, zc)), Vector((0, 1, 0)), None),
        ('side', sw, Vector((cx - dist, cy, zc)), Vector((1, 0, 0)), None)):
    scene.render.resolution_x = pw; scene.render.resolution_y = H
    cd.ortho_scale = max(pw, H) / ppm
    co.location = loc
    co.rotation_euler = rot_dir.to_track_quat('-Z', 'Y').to_euler()
    p = a.out + f'.{name}.png'
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(H, pw, 4))
    bpy.data.images.remove(im); os.remove(p)

sheet = np.concatenate(tiles, axis=1)
sheet[:, fw - 2:fw + 2, :3] = 0.25      # divider
res = bpy.data.images.new('sheet', W, H)
res.pixels = sheet.ravel()
res.filepath_raw = a.out
res.file_format = 'PNG'
res.save()
print('###SHEET###' + json.dumps({'out': a.out, 'ppm': ppm, 'front_w': fw, 'side_w': sw, 'size': [float(v) for v in size]}))
