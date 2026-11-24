"""01: import raw.glb, scale to 6.5 m upright, centre X, ground Z=0, apply transforms, 2048 PNG albedo, one material.
Blender -b --factory-startup --python 01_clean.py
"""
import bpy, os, numpy as np
from mathutils import Vector
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = 6.5
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(D, 'raw.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o)
assert len(meshes) == 1
ob = meshes[0]
ob.name = 'medusa'; ob.data.name = 'medusa_mesh'
ob.parent = None
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
mn, mx = co.min(0), co.max(0)
s = H / (mx[2] - mn[2])
co = (co - np.array([(mn[0] + mx[0]) / 2, 0, mn[2]])) * s
ob.data.vertices.foreach_set('co', co.ravel()); ob.data.update()
import bmesh
bm = bmesh.new(); bm.from_mesh(ob.data)
nv0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bm.to_mesh(ob.data); bm.free(); ob.data.update()
print('###WELD', nv0, '->', len(ob.data.vertices))
co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
print('###SCALE', s, 'size', co.max(0) - co.min(0), 'min', co.min(0), 'max', co.max(0))
# texture
img = None
for m in ob.data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            img = n.image
img.scale(2048, 2048)
p = os.path.join(D, 'medusa_albedo.png')
img.filepath_raw = p; img.file_format = 'PNG'; img.save()
img.name = 'medusa_albedo'
img.filepath = '//medusa_albedo.png'
mat = bpy.data.materials.new('medusa_mat'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.8
ob.data.materials.clear(); ob.data.materials.append(mat)
for m in list(bpy.data.materials):
    if m != mat: bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i != img: bpy.data.images.remove(i)
ob.data.calc_loop_triangles()
print('###TRIS', len(ob.data.loop_triangles), 'verts', len(ob.data.vertices), 'uv', [u.name for u in ob.data.uv_layers])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, '..', '..', '..', 'work', 'rig_medusa', '01_clean.blend'))
