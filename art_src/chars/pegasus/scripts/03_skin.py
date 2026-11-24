"""Step 3: bind the mesh to the armature with the weights from 03a_weights.py.

Blender -b --factory-startup --python 03_skin.py -- <workdir> <weights.npz> <out.blend> [stage2.blend]
(stage2.blend defaults to <workdir>/stage2.blend; since the round-1 rig fix use stage2r.blend, the ripped mesh)
Also writes a 'weightviz' colour attribute (dominant bone colour, blended by weight) for check renders.
"""
import bpy, sys, os, colorsys
import numpy as np

_a = sys.argv[sys.argv.index('--') + 1:]
WK, WNPZ, OUT = _a[:3]
bpy.ops.wm.open_mainfile(filepath=_a[3] if len(_a) > 3 else os.path.join(WK, 'stage2.blend'))
ob = bpy.data.objects['pegasus']; arm = bpy.data.objects['pegasus_rig']
d = np.load(WNPZ)
names = [str(n) for n in d['names']]; idx = d['idx']; w = d['w']
for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
for b in arm.data.bones:
    if b.use_deform: ob.vertex_groups.new(name=b.name)
vgs = {g.name: g for g in ob.vertex_groups}
nv = len(ob.data.vertices)
assert nv == len(idx), (nv, len(idx))
for k, n in enumerate(names):
    g = vgs[n]
    for slot in range(idx.shape[1]):
        sel = np.where((idx[:, slot] == k) & (w[:, slot] > 0))[0]
        for v in sel.tolist():
            g.add([v], float(w[v, slot]), 'REPLACE')
for m in list(ob.modifiers): ob.modifiers.remove(m)
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
ob.parent = arm
ob.matrix_parent_inverse.identity()

# weight visualisation colours
rng = np.random.default_rng(3)
def gcol(n):
    if 'feather' in n: return (1.0, 0.55, 0.1)
    if n.startswith('wing'): return (0.9, 0.1, 0.1)
    if n.startswith('neck') or n == 'head': return (0.15, 0.3, 1.0)
    if n.startswith('tail'): return (0.9, 0.1, 0.9) if n[-1] in '135' else (0.5, 0.0, 0.6)
    if n.startswith('leg') or n.startswith('hoof'): return (1.0, 0.95, 0.1) if n.endswith('_01') or n.endswith('_03') else (0.1, 0.9, 0.9)
    return (0.1, 0.75, 0.15)
cols = np.array([gcol(n) for n in names])
vc = (cols[idx] * w[:, :, None]).sum(1)
if 'weightviz' in ob.data.color_attributes:
    ob.data.color_attributes.remove(ob.data.color_attributes['weightviz'])
ca = ob.data.color_attributes.new('weightviz', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', np.concatenate([vc, np.ones((nv, 1))], 1).ravel())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('###SKIN###', OUT, len(names))
