"""Step 6a (rig fix round 1): find the flank skin that the hanging wing lobe hides in the rest pose and export its UV
triangles. The generator painted junk there (pale-blue feather-shadow shards it could not see); once the lobe rides the
wing, an upstroke reveals it. 06b_paint_hidden_flank.py repaints those texels.

Blender -b --factory-startup --python 06a_hidden_flank_uv.py -- <stage2r.blend> <labels.npy> <out.npz>
Hidden flank face: no lobe (label 1) vertex (the mane never reaches below z 1.85 here), centroid |x| 0.20..0.50, y -0.30..0.80, z 1.20..1.85, and a ray
from the centroid going outwards (+-X) hits the mesh within 0.60 m (the wing in front of it).
"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SRC, LABP, OUT = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=SRC)
ob = bpy.data.objects['pegasus']; me = ob.data
lab = np.load(LABP)
nv = len(me.vertices)
assert nv == len(lab), (nv, len(lab))
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
me.calc_loop_triangles()
nt = len(me.loop_triangles)
TV = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', TV); TV = TV.reshape(-1, 3)
TL = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('loops', TL); TL = TL.reshape(-1, 3)
uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
c = co[TV].mean(1); ax = np.abs(c[:, 0])
cand = (ax > 0.20) & (ax < 0.50) & (c[:, 1] > -0.30) & (c[:, 1] < 0.80) & (c[:, 2] > 1.20) & (c[:, 2] < 1.85) & \
       np.all(lab[TV] != 1, axis=1)
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
hidden = np.zeros(nt, bool)
for t in np.where(cand)[0]:
    d = Vector((np.sign(c[t, 0]), 0, 0))
    hit = bvh.ray_cast(Vector(c[t]) + d * 0.004, d, 0.60)
    hidden[t] = hit[0] is not None
print('###HIDDEN###', int(cand.sum()), int(hidden.sum()))
np.savez(OUT, uv=uv[TL[hidden]], cen=c[hidden])
