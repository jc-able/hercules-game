"""Dump raw mesh (Blender coords, transforms applied) to npz for numpy analysis.
Blender -b --factory-startup --python 00_dump.py -- <raw.glb> <out.npz>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
o = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
print('OBJ', o.name, tuple(o.location), tuple(o.rotation_euler), tuple(o.scale), o.parent)
me = o.data
M = np.array(o.matrix_world)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
co = co @ M[:3, :3].T + M[:3, 3]
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tri)
edges = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', edges)
np.savez(argv[1], co=co, tri=tri.reshape(-1, 3), edges=edges.reshape(-1, 2))
print('DUMPED', co.shape, len(tri) // 3)
