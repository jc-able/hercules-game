"""Step 1: import raw.glb, clean, scale to 8.0 m, apply transforms, one material with a PNG albedo.
Blender -b --factory-startup --python 01_clean.py -- <chars/cyclops dir> <work dir>
Writes <work dir>/01_clean.blend.
"""
import bpy, sys, os, json, bmesh
import numpy as np
from mathutils import Vector

D, W = [os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:][:2]]
H = 8.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(D, 'raw.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

me = ob.data
n0 = len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me)
r = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
# drop loose verts/edges
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(me); bm.free()
n1 = len(me.vertices)

co = np.empty(n1 * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
mn, mx = co.min(0), co.max(0)
s = H / (mx[2] - mn[2])
# centre: X on bbox centre, Y on the feet centre (lowest 5% of height)
feet = co[co[:, 2] < mn[2] + 0.05 * (mx[2] - mn[2])]
cx = (mn[0] + mx[0]) / 2
cy = (feet[:, 1].min() + feet[:, 1].max()) / 2
co = (co - np.array([cx, cy, mn[2]])) * s
me.vertices.foreach_set('co', co.ravel())
me.update()

# connected components
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
seen = np.zeros(len(bm.verts), bool); comps = []
for v in bm.verts:
    if seen[v.index]:
        continue
    st = [v]; seen[v.index] = True; c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if not seen[y.index]:
                seen[y.index] = True; st.append(y)
    comps.append(c)
bm.free()
comps.sort(key=len, reverse=True)
comp_info = []
for c in comps[:12]:
    p = co[c]
    comp_info.append({'n': len(c), 'min': p.min(0).round(2).tolist(), 'max': p.max(0).round(2).tolist()})

# material: base colour texture only
img = None
for m in me.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                # the base colour one: linked to Base Color
                for l in n.outputs['Color'].links:
                    if l.to_socket.name == 'Base Color':
                        img = n.image
if img is None:
    img = [i for i in bpy.data.images if i.size[0] > 0][0]
w, h = img.size
if max(w, h) > 2048:
    img.scale(min(2048, w), min(2048, h))
png = os.path.join(D, 'cyclops_albedo.png')
img.filepath_raw = png; img.file_format = 'PNG'; img.save()
img2 = bpy.data.images.load(png); img2.name = 'cyclops_albedo'

mat = bpy.data.materials.new('cyclops_mat'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img2
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.8
me.materials.clear(); me.materials.append(mat)
ob.name = 'cyclops'; me.name = 'cyclops_mesh'
# remove unused data
for m in list(bpy.data.materials):
    if m != mat:
        bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i != img2:
        bpy.data.images.remove(i)
me.calc_loop_triangles()
info = {'verts_raw': n0, 'verts_merged': n1, 'tris': len(me.loop_triangles), 'scale': s,
        'size': (co.max(0) - co.min(0)).round(3).tolist(), 'min': co.min(0).round(3).tolist(),
        'max': co.max(0).round(3).tolist(), 'components': len(comps), 'top_components': comp_info,
        'albedo': [w, h]}
print('###INFO###' + json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, '01_clean.blend'))
