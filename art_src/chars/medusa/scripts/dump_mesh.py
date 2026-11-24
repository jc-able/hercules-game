"""dump verts/tris of the mesh in a blend to npz: Blender -b <blend> --python dump_mesh.py -- out.npz"""
import bpy, sys, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = ob.data; me.calc_loop_triangles()
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
tr = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tr)
np.savez(out, co=co.reshape(-1, 3), tris=tr.reshape(-1, 3))
