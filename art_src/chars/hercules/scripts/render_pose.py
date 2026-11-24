"""Render FRONT | SIDE ortho flat sheets of the rig in test poses + measure edge stretch.

  Blender -b --factory-startup --python render_pose.py -- --blend X.blend --poses poses.json --out DIR [--bones] [--px 700]
           [--only name,name]

poses.json: {"pose_name": [["bone", "x|y|z", deg], ...], ...}  rotations about WORLD axes through the bone head,
applied in list order (put parents first); axis "lx"/"ly"/"lz" = the bone's own axis. "rest" = [].
Writes DIR/<pose>.png (front|side, side camera at -X so the character faces screen-right) and DIR/stretch.json.
"""
import bpy, sys, os, json, argparse, math
import numpy as np
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
ap.add_argument('--blend', required=True); ap.add_argument('--poses', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--bones', action='store_true'); ap.add_argument('--px', type=int, default=700)
ap.add_argument('--only', default=''); ap.add_argument('--span', type=float, default=2.7)
ap.add_argument('--zc', type=float, default=None); ap.add_argument('--cx', type=float, default=0.0); ap.add_argument('--cy', type=float, default=0.0); ap.add_argument('--views', default='front,side')
ap.add_argument('--no-drivers', action='store_true', help='do not drive the skirt bones from the thighs')
ap.add_argument('--horse', default='', help='blend whose meshes are shown in the --horse-poses poses (ride check)')
ap.add_argument('--horse-poses', default='ride'); ap.add_argument('--horse-offset', default='0,-0.07,-1.04')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
os.makedirs(a.out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a.blend)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH' and o.parent == arm and o.data.materials and o.data.materials[0] and 'mat' in o.data.materials[0].name and len(o.data.vertices) > 5000)
arm.data.pose_position = 'POSE'
poses = json.load(open(a.poses))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skirt_drivers
horse = []
if a.horse:
    with bpy.data.libraries.load(a.horse, link=False) as (src, dst):
        dst.objects = list(src.objects)
    off = Vector([float(v) for v in a.horse_offset.split(',')])
    for im in bpy.data.images:
        if im.filepath.startswith('//') and not os.path.exists(bpy.path.abspath(im.filepath)):
            cand = os.path.join(os.path.dirname(os.path.abspath(a.horse)), im.filepath[2:])
            if os.path.exists(cand):
                im.filepath = cand; im.reload()
    for o in dst.objects:
        if o is None:
            continue
        if o.type == 'MESH' and o.data.materials and len(o.data.vertices) > 1000:
            sc.collection.objects.link(o)
            for m in list(o.modifiers):
                o.modifiers.remove(m)
            o.parent = None
            o.matrix_world = Matrix.Translation(off) @ o.matrix_world
            # ride check only: cut the wings away (|x| > 0.40 m) and draw the horse flat grey so the rider reads
            import bmesh
            bmh = bmesh.new(); bmh.from_mesh(o.data)
            bmesh.ops.delete(bmh, geom=[v for v in bmh.verts if abs(v.co.x) > 0.40], context='VERTS')
            bmh.to_mesh(o.data); bmh.free()
            gm = bpy.data.materials.new('horse_grey'); gm.diffuse_color = (0.62, 0.66, 0.70, 1)
            o.data.materials.clear(); o.data.materials.append(gm)
            horse.append(o)
if a.only:
    poses = {k: v for k, v in poses.items() if k in a.only.split(',')}

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (1, 1, 1); sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = a.px; sc.render.resolution_y = a.px
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = a.span; cd.clip_start = 0.01; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
ZC = a.span / 2 - 0.25 if a.zc is None else a.zc

me0 = mesh.data
edges = np.empty(len(me0.edges) * 2, dtype=np.int64); me0.edges.foreach_get('vertices', edges); edges = edges.reshape(-1, 2)
rest_co = np.empty(len(me0.vertices) * 3); me0.vertices.foreach_get('co', rest_co); rest_co = rest_co.reshape(-1, 3)
rest_len = np.linalg.norm(rest_co[edges[:, 0]] - rest_co[edges[:, 1]], axis=1) + 1e-9
_vn = np.empty(len(me0.vertices) * 3); me0.vertices.foreach_get('normal', _vn); _vn = _vn.reshape(-1, 3)
# 'hidden' edges: facing down (skirt underside, soles) or between the legs under the skirt (|x| < 0.3, 0.6 < z < 1.0)
_mid = (rest_co[edges[:, 0]] + rest_co[edges[:, 1]]) / 2
under_e = ((_vn[edges[:, 0], 2] + _vn[edges[:, 1], 2]) / 2 < -0.4)

def set_pose(spec):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for bone, ax, deg in spec:
        pb = arm.pose.bones[bone]
        h = pb.head.copy()     # armature space == world (armature at identity)
        if ax.lower().startswith('l'):      # 'lx' / 'ly' / 'lz': about the bone's own (posed) axis
            v = pb.matrix.to_3x3().col['xyz'.index(ax[1].lower())].normalized()
            R = Matrix.Rotation(math.radians(deg), 4, v)
        else:
            R = Matrix.Rotation(math.radians(deg), 4, ax.upper())
        pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ pb.matrix
        bpy.context.view_layer.update()
    if not a.no_drivers:
        skirt_drivers.apply_to_pose(arm)

stats = {}
for name, spec in poses.items():
    for o in horse:
        o.hide_render = name not in a.horse_poses.split(',')
    set_pose(spec)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ev.to_mesh_clear()
    L = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
    r = L / rest_len
    bad = np.where((r > 2.5) & (L > 0.02))[0]
    worst = np.argsort(-r)[:5]
    vis = ~under_e
    badv = np.where((r > 2.5) & (L > 0.02) & vis)[0]
    stats[name] = {'max_stretch': float(r.max()), 'p999': float(np.quantile(r, 0.999)), 'n_bad_edges': int(len(bad)),
                   'max_stretch_up_facing': float(r[vis].max()), 'n_bad_up_facing': int(len(badv)),
                   'worst_up_facing_at': [[round(float(x_), 3) for x_ in rest_co[edges[i, 0]]] for i in np.where(vis)[0][np.argsort(-r[vis])[:4]]],
                   'worst_edges_at': [[round(float(x), 3) for x in rest_co[edges[i, 0]]] for i in worst],
                   'min_z': float(co[:, 2].min()), 'max_z': float(co[:, 2].max())}
    tiles = []
    VIEWS = {'front': (Vector((a.cx, -20, ZC)), Vector((0, 1, 0))), 'side': (Vector((-20, a.cy, ZC)), Vector((1, 0, 0))),
             'q34r': (Vector((-14.1, -14.1, ZC)), Vector((1, 1, 0)).normalized()),
             'q34l': (Vector((14.1, -14.1, ZC)), Vector((-1, 1, 0)).normalized()),
             'low': (Vector((0, -14.1, ZC - 14.1)), Vector((0, 1, 1)).normalized())}
    for view in a.views.split(','):
        loc, d = VIEWS[view]
        cam.location = loc; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(a.out, f'_{name}_{view}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p)
        px = np.array(im.pixels[:], dtype=np.float32).reshape(a.px, a.px, 4)[::-1]   # top row first
        bpy.data.images.remove(im); os.remove(p)
        if a.bones and view in ('front', 'side'):
            scale = a.px / a.span
            def proj(v):
                h = v.x if view == 'front' else -v.y
                return (int(a.px / 2 + h * scale), int(a.px / 2 - (v.z - ZC) * scale))
            for pb in arm.pose.bones:
                p0, p1 = proj(pb.head), proj(pb.tail)
                n = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), 1)
                col = (0.1, 0.3, 1.0) if pb.name.endswith('_l') else (0.0, 0.7, 0.2) if pb.name.endswith('_r') else (0.1, 0.1, 0.1)
                for t in np.linspace(0, 1, n * 2):
                    x = int(p0[0] + (p1[0] - p0[0]) * t); y = int(p0[1] + (p1[1] - p0[1]) * t)
                    px[max(0, y - 1):y + 2, max(0, x - 1):x + 2, :3] = col
                x, y = p0
                px[max(0, y - 3):y + 4, max(0, x - 3):x + 4, :3] = (1, 0.1, 0.1)
        tiles.append(px)
    sheet = np.concatenate(tiles, axis=1)
    for k in range(1, len(tiles)):
        sheet[:, k * a.px - 1:k * a.px + 1, :3] = 0.3
    out = bpy.data.images.new('s', a.px * len(tiles), a.px)
    out.pixels = sheet[::-1].ravel()
    out.filepath_raw = os.path.join(a.out, f'{name}.png'); out.file_format = 'PNG'; out.save()
    bpy.data.images.remove(out)
    print('###POSE', name, json.dumps(stats[name]))
json.dump(stats, open(os.path.join(a.out, 'stretch.json'), 'w'), indent=1)
