"""Step 2b: hydra.blend (clean mesh) + joints_necks.json -> hydra_bones.blend (mesh + armature, no skin yet).
Body/leg/tail joints were read from mesh slices (see notes in rig.json); necks/heads come from 02a_joints.py."""
import bpy, os, json, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); CH = os.path.dirname(HERE)
WIP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CH))), 'work', 'rig_hydra', 'wip')
# fix round 1: start from the trimmed mesh (rear tube removed, 01b_trim.py) when it exists
SRC = os.path.join(WIP, '01b_trim.blend')
bpy.ops.wm.open_mainfile(filepath=SRC if os.path.exists(SRC) else os.path.join(WIP, '01_clean.blend'))
J = json.load(open(os.path.join(HERE, 'joints_necks.json')))
B = {}   # name: (head, tail, parent, deform)
def add(n, h, t, p, d=True): B[n] = (list(h), list(t), p, d)
add('root', (0, 0, 0), (0, 2.0, 0), None, False)
add('hips', (0, 4.0, 4.8), (0, 2.6, 5.0), 'root')
add('spine_01', (0, 2.6, 5.0), (0, 1.0, 5.1), 'hips')
add('spine_02', (0, 1.0, 5.1), (0, -0.5, 5.25), 'spine_01')
add('spine_03', (0, -0.5, 5.25), (0, -1.9, 5.7), 'spine_02')
# tail centre line (y, z) measured from cross-section mid-heights
tail_yz = [(4.0, 4.8), (4.6, 4.42), (5.1, 4.24), (5.6, 3.86), (6.1, 3.49), (6.6, 3.16), (7.1, 2.94), (7.6, 2.74),
           (8.1, 2.6), (8.6, 2.5), (9.1, 2.42), (9.6, 2.36), (10.1, 2.31), (10.6, 2.27), (11.3, 2.24)]
P = np.array([[0, y, z] for y, z in tail_yz]); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
t = np.linspace(0, s[-1], 9); TP = np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1)
for i in range(8):
    add(f'tail_{i+1:02d}', TP[i], TP[i + 1], 'hips' if i == 0 else f'tail_{i:02d}')
# legs (right side = -X, mirrored to +X)
legs = {
 'fr': [(-1.85, -1.55, 4.7), (-1.98, -1.40, 2.6), (-1.98, -1.50, 1.0), (-1.98, -1.80, 0.38), (-2.0, -2.80, 0.15)],
 'br': [(-1.50, 3.20, 4.9), (-1.66, 3.05, 2.6), (-1.66, 3.60, 1.0), (-1.70, 3.35, 0.38), (-1.72, 2.20, 0.15)],
}
for side, pts in list(legs.items()):
    legs[side[0] + 'l'] = [(-x, y, z) for x, y, z in pts]
for side, pts in legs.items():
    par = 'spine_03' if side[0] == 'f' else 'hips'
    for i in range(3):
        add(f'leg_{side}_{i+1:02d}', pts[i], pts[i + 1], par if i == 0 else f'leg_{side}_{i:02d}')
    add(f'foot_{side}', pts[3], pts[4], f'leg_{side}_03')
# necks + heads
for k in ['1', '2', '3', '4', '5', '6', '7', '8']:
    for i in range(4):
        h, tl = J[f'neck_{k}_{i+1:02d}']
        add(f'neck_{k}_{i+1:02d}', h, tl, 'spine_03' if i == 0 else f'neck_{k}_{i:02d}')
    h, tl = J[f'head_{k}']; add(f'head_{k}', h, tl, f'neck_{k}_04')
for i in range(5):
    h, tl = J[f'neck_c_{i+1:02d}']; add(f'neck_c_{i+1:02d}', h, tl, 'spine_03' if i == 0 else f'neck_c_{i:02d}')
h, tl = J['head_c']; add('head_c', h, tl, 'neck_c_05')
JAW = json.load(open(os.path.join(HERE, 'jaw.json'))) if os.path.exists(os.path.join(HERE, 'jaw.json')) else None
if JAW: add('jaw_c', JAW['head'], JAW['tail'], 'head_c')
else:
    hh, ht = np.array(J['head_c'][0]), np.array(J['head_c'][1])
    add('jaw_c', hh + np.array([0, -0.3, -0.55]), ht + np.array([0, 0.2, -0.45]), 'head_c')

ad = bpy.data.armatures.new('hydra_rig'); arm = bpy.data.objects.new('hydra_rig', ad)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, (h, tl, p, d) in B.items():
    eb = ad.edit_bones.new(n); eb.head = Vector(h); eb.tail = Vector(tl); eb.use_deform = d; eb.roll = 0
for n, (h, tl, p, d) in B.items():
    if p:
        eb = ad.edit_bones[n]; eb.parent = ad.edit_bones[p]
        eb.use_connect = (Vector(ad.edit_bones[p].tail) - Vector(h)).length < 1e-4
bpy.ops.object.mode_set(mode='OBJECT')
ad.display_type = 'STICK'; arm.show_in_front = True
mesh = bpy.data.objects['hydra']
mesh.parent = arm
json.dump([{'name': n, 'head': list(map(float, h)), 'tail': list(map(float, tl)), 'parent': p, 'deform': d} for n, (h, tl, p, d) in B.items()],
          open(os.path.join(WIP, 'bones.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP, '02_bones.blend'), relative_remap=True)
print('###BONES###', len(B), 'deform', sum(1 for v in B.values() if v[3]))
