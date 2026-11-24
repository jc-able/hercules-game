"""Step 1: raw.glb -> hydra.blend (clean mesh, real size, one material, 2048 texture).
Decision: shoulder (withers at the neck base, top of the torso without dorsal plates) measured at raw z = 0.40
-> scale 6.5 / 0.40 = 16.25.  Faces -Y already (head toward -Y, tail toward +Y)."""
import bpy, os, numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); CH = os.path.dirname(HERE)
SHOULDER_RAW, SHOULDER_M = 0.40, 6.5
S = SHOULDER_M / SHOULDER_RAW
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(CH, 'raw.glb'))
objs = list(bpy.context.scene.objects)
mesh = [o for o in objs if o.type == 'MESH'][0]
for o in objs:
    if o is not mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
mesh.name = 'hydra'; mesh.data.name = 'hydra_mesh'
# bake world matrix into the data
me = mesh.data
me.transform(mesh.matrix_world); mesh.matrix_world = Matrix.Identity(4)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
mn, mx = co.min(0), co.max(0)
off = np.array([-(mn[0] + mx[0]) / 2, 0.0, -mn[2]])
co = (co + off) * S
me.vertices.foreach_set('co', co.ravel()); me.update()
# weld UV-seam duplicates (UVs live on loops, so they survive)
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
before = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5 * S)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
# texture -> 2048 png
img = None
for m in me.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: img = n.image
img.scale(2048, 2048)
png = os.path.join(CH, 'hydra_albedo.png')
img.filepath_raw = png; img.file_format = 'PNG'; img.save()
old = img
img = bpy.data.images.load(png); img.name = 'hydra_albedo'
bpy.data.images.remove(old)
# one clean material
mat = bpy.data.materials.new('hydra_mat'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0; bsdf.inputs['Roughness'].default_value = 0.8
me.materials.clear(); me.materials.append(mat)
for m in list(bpy.data.materials):
    if m != mat: bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i != img: bpy.data.images.remove(i)
me.calc_loop_triangles()
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
print('###CLEAN###', dict(verts_before=before, verts=len(me.vertices), tris=len(me.loop_triangles),
      min=co.min(0).round(3).tolist(), max=co.max(0).round(3).tolist(), scale=S, offset_raw=off.round(4).tolist()))
WIP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CH))), 'work', 'rig_hydra', 'wip'); os.makedirs(WIP, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP, '01_clean.blend'), relative_remap=True)
print('###IMG###', img.filepath, img.packed_file)
