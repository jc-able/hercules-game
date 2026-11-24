"""Step 3: apply the numpy weights (03a_weights.py) as vertex groups.
Blender -b --factory-startup <work>/02_bones.blend --python 03_skin.py -- <weights.npz> <out.blend>
"""
import bpy, sys
import numpy as np
wf, out = sys.argv[sys.argv.index('--') + 1:][:2]
d = np.load(wf); W = d['w']; names = [str(n) for n in d['names']]
ob = bpy.data.objects['cyclops']
ob.vertex_groups.clear()
assert len(ob.data.vertices) == W.shape[0], (len(ob.data.vertices), W.shape)
for j, nm in enumerate(names):
    vg = ob.vertex_groups.new(name=nm)
    col = W[:, j]
    nz = np.nonzero(col > 0)[0]
    # group by identical weight is overkill; add one by one (20k verts x <=4)
    for i in nz:
        vg.add([int(i)], float(col[i]), 'REPLACE')
print('###SKIN###', len(names), int((W > 0).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
