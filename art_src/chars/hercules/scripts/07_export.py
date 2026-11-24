"""Step 7: hercules.blend -> export/hercules.glb (mesh + skeleton, no props, no animation, +Y up), then re-import
it in a clean scene and check: one armature, one skinned mesh, bone names, vertex count, weights, height."""
import bpy, os, json
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'export', 'hercules.glb')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'hercules.blend'))
arm = bpy.data.objects['hercules_rig']; ob = bpy.data.objects['hercules']
arm.data.pose_position = 'REST'
for o in bpy.context.scene.objects:
    o.select_set(o in (arm, ob))
bone_names = sorted(b.name for b in arm.data.bones)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True,
                          export_animations=False, export_skins=True, export_def_bones=False,
                          export_apply=False, export_materials='EXPORT')
size = os.path.getsize(OUT)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT)
arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
skinned = [m for m in meshes if any(md.type == 'ARMATURE' for md in m.modifiers)]
m = skinned[0]; me = m.data; me.calc_loop_triangles()
co = np.array([m.matrix_world @ v.co for v in me.vertices])
ninf = [len([g for g in v.groups if g.weight > 1e-4]) for v in me.vertices]
sums = [sum(g.weight for g in v.groups) for v in me.vertices]
rb = sorted(b.name for b in arms[0].data.bones)
res = {'glb_bytes': size, 'armatures': len(arms), 'meshes': len(meshes), 'skinned_meshes': len(skinned),
       'bones': len(rb), 'bone_names_match': rb == bone_names, 'verts': len(me.vertices), 'tris': len(me.loop_triangles),
       'unweighted_verts': int(sum(1 for n in ninf if n == 0)), 'max_influences': max(ninf),
       'weight_sum_min': round(min(sums), 4), 'weight_sum_max': round(max(sums), 4),
       'height': round(float(co[:, 2].max() - co[:, 2].min()), 4), 'min_z': round(float(co[:, 2].min()), 4),
       'x_centre': round(float((co[:, 0].max() + co[:, 0].min()) / 2), 4),
       'images': [(i.name, i.size[0], i.size[1]) for i in bpy.data.images if i.size[0]],
       'materials': [x.name for x in bpy.data.materials]}
print('###EXPORT', json.dumps(res))
