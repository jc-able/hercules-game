"""Dump vertex coords, triangle indices and edges of the single mesh in a blend to an npz (for numpy analysis).
Blender -b --factory-startup <blend> --python dump_mesh.py -- <out.npz>"""
import bpy, sys
import numpy as np
out = sys.argv[sys.argv.index('--') + 1]
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = ob.data
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tri)
ed = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', ed)
np.savez(out, co=co.reshape(-1, 3), tri=tri.reshape(-1, 3), edges=ed.reshape(-1, 2))
print('###DUMP###', out, len(me.vertices))
