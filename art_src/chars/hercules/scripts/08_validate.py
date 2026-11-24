"""Step 8: validate hercules.blend: objects/transforms/material/texture, weights (limit, sums, stray vertices whose
weights disagree with all neighbours), and a per-bone move test (moving a bone moves every vertex it owns, and only
vertices connected to its region)."""
import bpy, os, json
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'hercules.blend'))
sc = bpy.context.scene
objs = {o.name: (o.type, [round(v, 5) for v in o.location], [round(v, 5) for v in o.rotation_euler], [round(v, 5) for v in o.scale],
                 o.parent.name if o.parent else None, o.parent_bone) for o in sc.objects}
ob = bpy.data.objects['hercules']; arm = bpy.data.objects['hercules_rig']; me = ob.data; nv = len(me.vertices)
names = [g.name for g in ob.vertex_groups]
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
acc = np.zeros_like(W); deg = np.zeros(nv)
np.add.at(acc, ed[:, 0], W[ed[:, 1]]); np.add.at(acc, ed[:, 1], W[ed[:, 0]]); np.add.at(deg, ed.ravel(), 1)
diff = np.abs(W - acc / np.maximum(deg, 1)[:, None]).max(1)
co = np.array([v.co[:] for v in me.vertices])
# bone move test: rotate each deform bone 90 deg about a perpendicular axis; vertices owned (w>0.5) must move,
# vertices that move > 2 cm must be weighted (>0) to that bone or its descendants
dg = bpy.context.evaluated_depsgraph_get()
def ev():
    bpy.context.view_layer.update(); e = ob.evaluated_get(dg); m = e.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); e.to_mesh_clear(); return c.reshape(-1, 3)
rest = ev(); bad = {}
for pb in arm.pose.bones:
    if not pb.bone.use_deform: continue
    pb.rotation_mode = 'XYZ'; pb.rotation_euler = (1.5708, 0, 0); moved = np.linalg.norm(ev() - rest, axis=1)
    pb.rotation_euler = (0, 0, 0)
    fam = [names.index(b.name) for b in [pb.bone] + list(pb.bone.children_recursive) if b.name in names]
    own = W[:, names.index(pb.name)] > 0.5 if pb.name in names else np.zeros(nv, bool)
    blen = pb.bone.length
    stuck = int((own & (moved < 1e-4)).sum())
    stray = int(((moved > 0.02) & (W[:, fam].sum(1) == 0)).sum())
    if stuck or stray: bad[pb.name] = {'stuck_owned': stuck, 'moved_unweighted': stray}
img = bpy.data.images.get('hercules_albedo')
res = {'objects': objs, 'materials': [m.name for m in me.materials], 'texture': [img.size[:], img.filepath] if img else None,
       'tris': sum(len(p.vertices) - 2 for p in me.polygons), 'verts': nv, 'max_infl': int((W > 0).sum(1).max()),
       'unweighted': int(((W > 0).sum(1) == 0).sum()), 'sum_min': round(float(W.sum(1).min()), 4), 'sum_max': round(float(W.sum(1).max()), 4),
       'stray_weight_verts(>0.5 off all neighbours)': int((diff > 0.5).sum()), 'diff_p999': round(float(np.quantile(diff, 0.999)), 3),
       'bone_move_test_failures': bad, 'height': round(float(co[:, 2].max() - co[:, 2].min()), 4),
       'z_min': round(float(co[:, 2].min()), 5), 'x_centre': round(float(co[:, 0].max() + co[:, 0].min()) / 2, 5)}
print('###VALIDATE', json.dumps(res))
