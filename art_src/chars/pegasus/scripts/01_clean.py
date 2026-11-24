"""Step 1: import raw.glb, weld UV-seam duplicates, scale to withers 1.9 m, ground at Z=0, centre X, faces -Y,
2048 px albedo PNG, one material pegasus_mat. Saves work blend `stage1.blend` + npz dump.

Blender -b --factory-startup --python scripts/01_clean.py -- <chardir> <workdir>
"""
import bpy, bmesh, sys, os, json
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
CH, WK = argv[0], argv[1]
WITHERS = 1.9

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(CH, 'raw.glb'))
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o)
ob = [o for o in sc.objects if o.type == 'MESH'][0]
ob.name = 'pegasus'; ob.data.name = 'pegasus_mesh'
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

me = ob.data
# weld seam duplicates (UVs live on loops, so they survive)
bm = bmesh.new(); bm.from_mesh(me)
nv0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
nv1 = len(bm.verts)
bm.to_mesh(me); bm.free()

co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
# withers: top of the central strip just behind the mane (measured raw bin y in [-0.02, 0.02])
strip = (np.abs(co[:, 0]) < 0.03) & (co[:, 1] > -0.02) & (co[:, 1] < 0.02)
wz = co[strip, 2].max() - co[:, 2].min()
s = WITHERS / wz
cx = (co[:, 0].min() + co[:, 0].max()) / 2
co[:, 0] -= cx
co[:, 2] -= co[:, 2].min()
co *= s
me.vertices.foreach_set('co', co.ravel())
me.update()

# texture -> 2048 PNG next to the blend
img = None
for n in ob.material_slots[0].material.node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image:
        img = n.image
img.scale(2048, 2048)
png = os.path.join(CH, 'pegasus_albedo.png')
img.filepath_raw = png; img.file_format = 'PNG'; img.save()
img2 = bpy.data.images.load(png); img2.name = 'pegasus_albedo'

mat = bpy.data.materials.new('pegasus_mat'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img2; tex.location = (-400, 200)
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.7
me.materials.clear(); me.materials.append(mat)
for m in list(bpy.data.materials):
    if m != mat: bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i != img2: bpy.data.images.remove(i)
bpy.ops.object.shade_smooth() if False else None

me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tri)
edges = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', edges)
np.savez(os.path.join(WK, 'stage1.npz'), co=co, tri=tri.reshape(-1, 3), edges=edges.reshape(-1, 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WK, 'stage1.blend'))
info = {'verts_before': nv0, 'verts_after': nv1, 'tris': len(tri) // 3, 'scale': s, 'withers_raw': wz,
        'size': (co.max(0) - co.min(0)).tolist(), 'min': co.min(0).tolist(), 'max': co.max(0).tolist()}
print('###INFO###' + json.dumps(info))
