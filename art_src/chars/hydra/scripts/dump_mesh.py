"""Dump the hydra mesh (from hydra.blend) to npz: co, tri, vertex normals, medial points + local thickness.
  Blender -b --factory-startup --python dump_mesh.py -- <blend> <out.npz>"""
import bpy, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['hydra']; me = o.data
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3)
vn = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
bvh = BVHTree.FromPolygons([Vector(v) for v in co], tri.tolist(), all_triangles=True)
med = co.copy(); th = np.full(len(co), -1.0)
for i in range(len(co)):
    v = co[i]; n = vn[i]
    hit, nor, idx, dist = bvh.ray_cast(Vector(v - n * 1e-3), Vector(-n), 20.0)
    if hit is not None: th[i] = dist; med[i] = (np.array(hit) + v) / 2
E = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [0, 2]]]), 1), axis=0)
np.savez(a[1], co=co, tri=tri, vn=vn, med=med, th=th, E=E)
print('###DUMP###', len(co), len(tri), (th > 0).mean())
