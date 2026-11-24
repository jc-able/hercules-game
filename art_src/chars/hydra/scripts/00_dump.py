"""Dump raw GLB vertices/faces (Blender world coords, Z up) to npz for numpy analysis.
  Blender -b --factory-startup --python 00_dump.py -- <in.glb> <out.npz>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = o.data
M = np.array(o.matrix_world)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
co = co @ M[:3, :3].T + M[:3, 3]
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tri)
print('OBJ', o.name, 'matrix', M.round(4).tolist(), 'parent', o.parent)
print('polys', len(me.polygons), 'loops', len(me.loops))
np.savez(a[1], co=co, tri=tri.reshape(-1, 3))
