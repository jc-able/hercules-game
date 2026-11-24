"""Step 9: numeric rig tests on hercules.blend (no renders). Prints ###TESTS {json}.
 - mirror: turn a left bone and its right twin by the mirrored rotation (X axis rotations mirror to themselves), mirror
   the right result to the left and compare the moved vertices with their left partners (p95 / max, metres).
 - stretch: edge stretch (>2.5x on edges > 2 cm) for single-joint tests the review used (neck/head/shoulder/spine_03).
Rotations are about WORLD axes through the bone head (same convention as render_pose.py); skirt drivers applied.
"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Matrix, Vector, kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skirt_drivers
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'hercules.blend'))
arm = bpy.data.objects['hercules_rig']; ob = bpy.data.objects['hercules']; me = ob.data
arm.data.pose_position = 'POSE'
nv = len(me.vertices)
rest = np.empty(nv * 3); me.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
rl = np.linalg.norm(rest[ed[:, 0]] - rest[ed[:, 1]], axis=1) + 1e-9
dg = bpy.context.evaluated_depsgraph_get()


def pose(spec):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for bone, ax, deg in spec:
        pb = arm.pose.bones[bone]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, ax.upper()) @ Matrix.Translation(-h) @ pb.matrix
        bpy.context.view_layer.update()
    skirt_drivers.apply_to_pose(arm)
    e = ob.evaluated_get(dg); m = e.to_mesh()
    c = np.empty(nv * 3); m.vertices.foreach_get('co', c); e.to_mesh_clear()
    return c.reshape(-1, 3)


# mirror partners: left vertex -> nearest mirrored right vertex
R = np.where(rest[:, 0] < -0.01)[0]
kd = kdtree.KDTree(len(R))
for k, i in enumerate(R):
    kd.insert(Vector((-rest[i, 0], rest[i, 1], rest[i, 2])), k)
kd.balance()
L = np.where(rest[:, 0] > 0.01)[0]
part = np.full(nv, -1); pd = np.full(nv, np.inf)
for i in L:
    _, k, d = kd.find(Vector(rest[i])); part[i] = R[k]; pd[i] = d
res = {'mirror_partner_dist_p50': round(float(np.median(pd[L])), 4)}


def mirror_test(bl, br, ax, deg):
    pl = pose([(bl, ax, deg)]); pr = pose([(br, ax, deg if ax == 'x' else -deg)])
    moved = np.linalg.norm(pl - rest, axis=1) > 0.005
    m = moved & (rest[:, 0] > 0.01) & (pd < 0.01)
    q = pr[part[m]].copy(); q[:, 0] *= -1
    d = np.linalg.norm(pl[m] - q, axis=1)
    return {'n': int(m.sum()), 'p95_m': round(float(np.quantile(d, 0.95)), 4), 'max_m': round(float(d.max()), 4)}


for b in ('foot', 'toe', 'shin', 'thigh', 'forearm', 'hand'):
    res[f'mirror_{b}_x30'] = mirror_test(f'{b}_l', f'{b}_r', 'x', 30)
res['mirror_foot_x-30'] = mirror_test('foot_l', 'foot_r', 'x', -30)


def stretch(name, spec, region=None):
    c = pose(spec)
    r = np.linalg.norm(c[ed[:, 0]] - c[ed[:, 1]], axis=1) / rl
    bad = (r > 2.5) & (rl > 0.02 / 2.5 * 0 + 0.0) & (np.linalg.norm(c[ed[:, 0]] - c[ed[:, 1]], axis=1) > 0.02)
    out = {'max': round(float(r.max()), 2), 'n_bad': int(bad.sum())}
    if region is not None:
        mid = (rest[ed[:, 0]] + rest[ed[:, 1]]) / 2
        m = region(mid)
        out.update({'region_max': round(float(r[m].max()), 2), 'region_n_bad': int((bad & m).sum())})
    res['stretch_' + name] = out


neck = lambda p: (p[:, 2] > 1.50) & (p[:, 2] < 1.75)
for s in (60, -60):
    stretch(f'shoulder_r_x{s}', [('shoulder_r', 'x', s)], neck)
    stretch(f'shoulder_l_x{s}', [('shoulder_l', 'x', s)], neck)
stretch('head_z45', [('head', 'z', 45)], neck)
stretch('head_x45', [('head', 'x', 45)], neck)
stretch('neck_z45', [('neck', 'z', 45)], neck)
stretch('neck_x45', [('neck', 'x', 45)], neck)
stretch('spine_03_x45', [('spine_03', 'x', 45)], lambda p: (p[:, 2] > 1.25) & (p[:, 2] < 1.65))
armpit = lambda p: (np.abs(np.abs(p[:, 0]) - 0.207) < 0.05) & (np.abs(p[:, 2] - 1.355) < 0.06)
stretch('arms_overhead', [('upper_arm_l', 'y', -150), ('upper_arm_r', 'y', 150)], armpit)
skirt = lambda p: (p[:, 2] > 0.6) & (p[:, 2] < 1.12) & (np.abs(p[:, 0]) < 0.32)
stretch('run_thigh_l-70_shin90', [('thigh_l', 'x', -70), ('shin_l', 'x', 90)], skirt)
stretch('ride_straddle', [('thigh_l', 'y', -35), ('thigh_l', 'x', -85), ('thigh_r', 'y', 35), ('thigh_r', 'x', -85)], skirt)
stretch('lunge', [('thigh_l', 'x', -80), ('shin_l', 'x', 80), ('thigh_r', 'x', 45), ('shin_r', 'x', 25)], skirt)
print('###TESTS', json.dumps(res))
