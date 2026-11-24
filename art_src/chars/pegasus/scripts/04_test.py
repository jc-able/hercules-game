"""Step 4: deform tests. Poses are armature-space Euler XYZ degrees applied in each bone's rest frame.

Blender -b --factory-startup --python 04_test.py -- <blend> <poses.json> <outdir> [ppm] [--vcol]
For every pose: <outdir>/<pose>_front.png, <pose>_side.png (+ _top.png if the pose lists "_views") and edge-stretch
stats (edges longer than 2x rest = tears/spikes) printed as ###STRETCH### json lines.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, pj, outd = argv[:3]
ppm = float(argv[3]) if len(argv) > 3 and not argv[3].startswith('--') else 110
only = [a.split('=')[1].split(',') for a in argv if a.startswith('--only=')]
norender = '--norender' in argv
vcol = '--vcol' in argv
os.makedirs(outd, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
ob = next(o for o in sc.objects if o.type == 'MESH' and o.parent == arm)
arm.data.pose_position = 'POSE'
poses = json.load(open(pj))

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX' if vcol else 'TEXTURE'; sh.show_object_outline = False
sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); w.color = (0.35, 0.72, 0.47); sc.world = w
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('tcam'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 1000
cam = bpy.data.objects.new('tcam', cd); sc.collection.objects.link(cam); sc.camera = cam

me0 = ob.data
E = np.empty(len(me0.edges) * 2, dtype=np.int64); me0.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
co0 = np.empty(len(me0.vertices) * 3); me0.vertices.foreach_get('co', co0); co0 = co0.reshape(-1, 3)
L0 = np.linalg.norm(co0[E[:, 0]] - co0[E[:, 1]], axis=1)
# dominant group per vertex, to name the worst spots
gnames = {g.index: g.name for g in ob.vertex_groups}
dom = []
for v in me0.vertices:
    g = max(v.groups, key=lambda g: g.weight) if len(v.groups) else None
    dom.append(gnames[g.group] if g else '-')

B = (-2.2, -2.2, -0.3, 2.2, 2.0, 3.6)   # framing (x0, y0, z0, x1, y1, z1)
for a_ in argv:
    if a_.startswith('--box='): B = tuple(float(v) for v in a_[6:].split(','))
tag = ''.join(a_[6:] for a_ in argv if a_.startswith('--tag='))
for pname, pose in poses.items():
    if only and pname not in only[0]: continue
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    for bn, r in pose.items():
        if bn.startswith('_'): continue
        M = arm.data.bones[bn].matrix_local.to_3x3()
        R = Euler([math.radians(v) for v in r[:3]], 'XYZ').to_matrix()
        pb = arm.pose.bones[bn]
        pb.rotation_quaternion = (M.inverted() @ R @ M).to_quaternion()
        if len(r) > 3: pb.location = Vector(r[3:6])
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ev.to_mesh_clear()
    L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
    ratio = L / np.maximum(L0, 1e-6)
    bad = np.where((ratio > 2.0) & (L > 0.03))[0]
    spots = {}
    for e in bad:
        k = dom[E[e, 0]] + '/' + dom[E[e, 1]]
        spots[k] = spots.get(k, 0) + 1
    print('###STRETCH###', json.dumps({'pose': pname, 'max_ratio': round(float(ratio.max()), 2),
          'bad_edges': int(len(bad)), 'spots': dict(sorted(spots.items(), key=lambda x: -x[1])[:8]),
          'min_z': round(float(co[:, 2].min()), 3),
          'worst': [[round(float(ratio[e]), 1)] + [round(float(x), 2) for x in (co0[E[e, 0]] + co0[E[e, 1]]) / 2] + [dom[E[e, 0]], dom[E[e, 1]]]
                    for e in np.argsort(-ratio)[:6]]}))
    if '--stretchviz' in argv:
        vr_ = np.ones(len(co0))
        np.maximum.at(vr_, E[:, 0], ratio); np.maximum.at(vr_, E[:, 1], ratio)
        np.maximum.at(vr_, E[:, 0], 1 / np.maximum(ratio, 1e-3)); np.maximum.at(vr_, E[:, 1], 1 / np.maximum(ratio, 1e-3))
        t = np.clip((vr_ - 1.3) / 1.7, 0, 1)
        c = np.stack([np.ones_like(t) * 0.92, 0.92 * (1 - t), 0.92 * (1 - t), np.ones_like(t)], 1)
        if 'stretchviz' in me0.color_attributes: me0.color_attributes.remove(me0.color_attributes['stretchviz'])
        ca = me0.color_attributes.new('stretchviz', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', c.ravel())
        me0.color_attributes.active_color = ca
        sh.color_type = 'VERTEX'; sh.light = 'STUDIO'
    views = [] if norender else pose.get('_views', ['front', 'side'])
    for v in views:
        if v == 'front':
            ur, vr = (B[0], B[3]), (B[2], B[5]); loc = lambda uc, vc: Vector((uc, B[1] - 100, vc)); d = Vector((0, 1, 0))
        elif v == 'side':
            ur, vr = (-B[4], -B[1]), (B[2], B[5]); loc = lambda uc, vc: Vector((B[0] - 100, -uc, vc)); d = Vector((1, 0, 0))
        elif v == 'top':
            ur, vr = (B[0], B[3]), (B[1], B[4]); loc = lambda uc, vc: Vector((uc, vc, B[5] + 100)); d = None
        elif v == 'q34':
            ur, vr = (-2.6, 2.6), (B[2], B[5]); d = Vector((1, 1, -0.5)).normalized()
            loc = lambda uc, vc, d=d: Vector((0, 0, 1.4)) + Vector((0.7071, -0.7071, 0)) * uc - d * 100 + Vector((0, 0, vc - (B[2] + B[5]) / 2))
        W = int((ur[1] - ur[0]) * ppm); H = int((vr[1] - vr[0]) * ppm)
        sc.render.resolution_x = W; sc.render.resolution_y = H
        cd.ortho_scale = max(W, H) / ppm
        cam.location = loc((ur[0] + ur[1]) / 2, (vr[0] + vr[1]) / 2)
        cam.rotation_euler = Euler((0, 0, 0)) if d is None else d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(outd, f'{pname}{tag}_{v}.png')
        bpy.ops.render.render(write_still=True)
print('###DONE###')
