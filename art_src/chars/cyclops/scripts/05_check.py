"""Step 5: numeric skin checks on a skinned blend.
Blender -b --factory-startup <skinned.blend> --python 05_check.py -- <poses.json>
 - weights: unweighted verts, max influences, sum != 1
 - root move: translate root 10 m, every vertex must follow exactly
 - limb follow: rotate each limb root 90 deg; vertices of the limb tip region must all move with it
 - stretch: per pose, edge length ratio posed/rest (max, count > 1.8x, count < 0.4x)
"""
import bpy, sys, json
import numpy as np
from mathutils import Matrix, Euler, Vector

poses = json.load(open(sys.argv[sys.argv.index('--') + 1]))
scene = bpy.context.scene
ao = next(o for o in scene.objects if o.type == 'ARMATURE')
ob = next(o for o in scene.objects if o.type == 'MESH' and o.parent == ao)
arm = ao.data
me = ob.data
V = len(me.vertices)
gi = {g.index: g.name for g in ob.vertex_groups}
deform = {b.name for b in arm.bones if b.use_deform}
cnt = np.zeros(V, int); tot = np.zeros(V)
for v in me.vertices:
    for g in v.groups:
        if gi[g.group] in deform and g.weight > 0:
            cnt[v.index] += 1; tot[v.index] += g.weight
res = {'verts': V, 'unweighted': int((cnt == 0).sum()), 'max_influences': int(cnt.max()),
       'sum_off': int((np.abs(tot - 1) > 1e-3).sum())}
ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
rest = np.empty(V * 3); me.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
rl = np.linalg.norm(rest[ed[:, 0]] - rest[ed[:, 1]], axis=1)

def order(bones):
    out = []
    def rec(b):
        out.append(b)
        for c in b.children:
            rec(c)
    for b in bones:
        if b.parent is None:
            rec(b)
    return out
ORDER = order(arm.bones)

def apply_pose(spec, trans=None):
    for pb in ao.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    posed = {}
    for b in ORDER:
        pb = ao.pose.bones[b.name]
        M = posed[b.parent.name] @ b.parent.matrix_local.inverted() @ b.matrix_local if b.parent else b.matrix_local.copy()
        if b.name in spec:
            r = Euler([np.radians(a) for a in spec[b.name]], 'XYZ').to_matrix().to_4x4()
            h = M.to_translation()
            M = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ M
        if trans and b.name in trans:
            M = Matrix.Translation(Vector(trans[b.name])) @ M
        posed[b.name] = M
        pb.matrix = M
        bpy.context.view_layer.update()

def posed_co():
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg); m = e.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); e.to_mesh_clear()
    return c.reshape(-1, 3)

apply_pose({}, {'root': (10, 0, 0)})
d = posed_co() - rest
res['root_move_err_max'] = float(np.abs(d - np.array([10, 0, 0])).max())

# limb follow: (bone to rotate, rotation, region of verts that must move > 0.5 m)
x, y, z = rest[:, 0], rest[:, 1], rest[:, 2]
tests = {
 'upper_arm_u_l': ([0, 90, 0], (x > 2.6) & (z > 5.9)), 'upper_arm_u_r': ([0, -90, 0], (x < -2.6) & (z > 5.9)),
 'upper_arm_d_l': ([90, 0, 0], (x > 2.2) & (z < 4.6) & (z > 3.0)), 'upper_arm_d_r': ([90, 0, 0], (x < -2.2) & (z < 4.6) & (z > 3.0)),
 'thigh_l': ([-90, 0, 0], (x > 0.3) & (z < 1.0)), 'thigh_r': ([-90, 0, 0], (x < -0.3) & (z < 1.0)),
 'neck': ([60, 0, 0], (z > 7.4)),
}
follow = {}
for bn, (rot, region) in tests.items():
    apply_pose({bn: rot})
    mv = np.linalg.norm(posed_co() - rest, axis=1)
    follow[bn] = {'region': int(region.sum()), 'left_behind': int((mv[region] < 0.5).sum())}
    # also: how many verts OUTSIDE the limb moved (e.g. lower arm dragged by the upper arm)
    if bn.startswith('upper_arm_u'):
        lower = ((x > 2.3) if bn.endswith('_l') else (x < -2.3)) & (z < 4.6) & (z > 3.0)
        follow[bn]['lower_arm_dragged'] = int((mv[lower] > 0.05).sum())
    if bn.startswith('upper_arm_d'):
        upper = ((x > 2.3) if bn.endswith('_l') else (x < -2.3)) & (z > 5.9)
        follow[bn]['upper_arm_dragged'] = int((mv[upper] > 0.05).sum())
res['follow'] = follow

st = {}
for name, spec in poses.items():
    apply_pose(spec)
    p = posed_co()
    pl = np.linalg.norm(p[ed[:, 0]] - p[ed[:, 1]], axis=1)
    r = pl / np.maximum(rl, 1e-6)
    ab = pl - rl                      # absolute stretch in metres (ratio alone over-flags tiny crease edges)
    worst = np.argsort(-ab)[:3]
    st[name] = {'max': round(float(r.max()), 2), 'n>1.8': int((r > 1.8).sum()), 'n<0.4': int((r < 0.4).sum()),
                'abs_max_m': round(float(ab.max()), 3), 'n_abs>0.1m': int((ab > 0.1).sum()),
                'worst_at': [rest[ed[i, 0]].round(2).tolist() for i in worst],
                'worst_posed': [p[ed[i, 0]].round(2).tolist() for i in worst]}
res['stretch'] = st
print('###CHECK###' + json.dumps(res))
