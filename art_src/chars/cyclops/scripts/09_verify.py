"""Step 9: re-import export/cyclops.glb and game/assets/props/club.glb in a clean scene and report.
Blender -b --factory-startup --python 09_verify.py -- <cyclops.glb> <club.glb>"""
import bpy, sys, json
import numpy as np
from mathutils import Euler
a, c = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a)
S = bpy.context.scene
arms = [o for o in S.objects if o.type == 'ARMATURE']; meshes = [o for o in S.objects if o.type == 'MESH']
me = meshes[0]; me.data.calc_loop_triangles()
mods = [m for m in me.modifiers if m.type == 'ARMATURE']
dg = bpy.context.evaluated_depsgraph_get()
def wco():
    e = me.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    x = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', x); e.to_mesh_clear()
    M = np.array(me.matrix_world); x = x.reshape(-1, 3); return x @ M[:3, :3].T + M[:3, 3]
r0 = wco()
ar = arms[0]; pb = ar.pose.bones['upper_arm_u_r']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler((0, 0, 1.2))
bpy.context.view_layer.update()
moved = int((np.linalg.norm(wco() - r0, axis=1) > 0.05).sum())
res = {'armatures': len(arms), 'bones': len(ar.data.bones), 'meshes': len(meshes), 'tris': len(me.data.loop_triangles),
       'vgroups': len(me.vertex_groups), 'armature_mods': len(mods), 'size': (r0.max(0) - r0.min(0)).round(3).tolist(),
       'min_z': round(float(r0[:, 2].min()), 4), 'verts_moved_by_upper_arm_u_r': moved,
       'images': [(i.name, list(i.size)) for i in bpy.data.images if i.size[0]]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=c)
cm = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]; cm.data.calc_loop_triangles()
x = np.array([cm.matrix_world @ v.co for v in cm.data.vertices])
res['club'] = {'tris': len(cm.data.loop_triangles), 'min': x.min(0).round(3).tolist(), 'max': x.max(0).round(3).tolist(),
               'images': [(i.name, list(i.size)) for i in bpy.data.images if i.size[0]]}
print('###VERIFY###' + json.dumps(res))
