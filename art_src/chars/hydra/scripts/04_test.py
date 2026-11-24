"""Step 4: deform tests. For each pose in poses.json: edge-stretch stats + FRONT|SIDE flat render.
  Blender -b --factory-startup --python 04_test.py -- <skin.blend> <outdir> [pose,pose...]"""
import bpy, sys, os, json, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]; os.makedirs(out, exist_ok=True)
only = a[2].split(',') if len(a) > 2 and a[2] != 'all' else None
exec(open(os.path.join(HERE, 'posing.py')).read())
poses = json.load(open(os.path.join(HERE, 'poses.json')))
sc = bpy.context.scene; mesh = bpy.data.objects['hydra']; arm = bpy.data.objects['hydra_rig']
me0 = mesh.data
E = np.empty(len(me0.edges) * 2, dtype=np.int64); me0.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
co0 = np.empty(len(me0.vertices) * 3); me0.vertices.foreach_get('co', co0); co0 = co0.reshape(-1, 3)
L0 = np.linalg.norm(co0[E[:, 0]] - co0[E[:, 1]], axis=1)
sh = sc.display.shading; sc.render.engine = 'BLENDER_WORKBENCH'
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False; sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (1, 1, 1); sc.world = w; sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.1; cd.clip_end = 500
BOX = dict(cx=0.0, cy=3.0, cz=8.0, span=22.0)    # fixed framing for every pose
HEAT = len(a) > 4 and a[4] == 'heat'
if len(a) > 3: BOX = dict(zip(('cx', 'cy', 'cz', 'span'), map(float, a[3].split(','))))
T = 640; sc.render.resolution_x = T; sc.render.resolution_y = T; cd.ortho_scale = BOX['span']
from mathutils import Vector
stats = {}
for pname, pose in poses.items():
    if only and pname not in only: continue
    apply_pose(arm, pose)
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); ev.to_mesh_clear()
    L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1); r = L / np.maximum(L0, 1e-6)
    worst = np.argsort(-(L - L0))[:5]
    med = np.median(L0); grow = (L - L0) / med
    stats[pname] = dict(n_grow3=int((grow > 3).sum()), n_grow6=int((grow > 6).sum()), max_grow=float(grow.max()), max_stretch=float(r.max()), n_gt2=int((r > 2).sum()), n_gt3=int((r > 3).sum()), min_ratio=float(r.min()),
                        worst=[[round(float(r[i]), 2)] + [round(float(v), 2) for v in co0[E[i, 0]]] for i in worst])
    np.save(os.path.join(out, f'stretch_{pname}.npy'), r)
    heat = np.zeros(len(co0)); np.maximum.at(heat, E[:, 0], grow); np.maximum.at(heat, E[:, 1], grow)
    hx = np.clip(heat / 2.0, 0, 1)
    rgba = np.stack([0.85 * hx + 0.15, 0.8 * (1 - hx) + 0.1, 0.25 * (1 - hx) + 0.1, np.ones_like(hx)], 1).astype(np.float32)
    if 'heat' in me0.color_attributes: me0.color_attributes.remove(me0.color_attributes['heat'])
    at = me0.color_attributes.new('heat', 'FLOAT_COLOR', 'POINT'); at.data.foreach_set('color', rgba.ravel())
    me0.color_attributes.active_color = at
    tiles = []
    views = (('front', (0, -1, 0), 'TEXTURE'), ('side', (-1, 0, 0), 'TEXTURE'))
    if HEAT: views = views + (('heat_f', (0, -1, 0), 'VERTEX'), ('heat_s', (-1, 0, 0), 'VERTEX'))
    for vn, d, ct in views:
        sh.color_type = ct
        d = Vector(d); c = Vector((BOX['cx'], BOX['cy'], BOX['cz']))
        cam.location = c + d * 100; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(out, f'_{pname}_{vn}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(T, T, 4)); bpy.data.images.remove(im); os.remove(p)
    sheet = np.concatenate(tiles, 1); sheet[:, T - 1:T + 1, :3] = 0.3
    res = bpy.data.images.new('s', len(tiles) * T, T); res.pixels = sheet.ravel()
    res.filepath_raw = os.path.join(out, f'deform_{pname}.png'); res.file_format = 'PNG'; res.save(); bpy.data.images.remove(res)
    print('###POSE###', pname, json.dumps(stats[pname]))
json.dump(stats, open(os.path.join(out, 'stretch_stats.json'), 'w'), indent=1)
