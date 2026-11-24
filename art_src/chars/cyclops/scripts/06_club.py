"""Step 6: clean the club prop.
Blender -b --factory-startup --python 06_club.py -- <raw prop_club.glb> <out dir art_src/props> <out glb game/assets/props/club.glb>
- long axis -> +Z, club head (thick end) up, origin on the grip (GRIP_FROM_BUTT metres up from the butt end), 5.5 m long
- decimate to <= 5000 triangles, texture 1024 PNG, one material club_mat (base colour only)
- saves <out dir>/club.blend + club_albedo.png and exports the GLB (+Y up: head along +Y in Godot)
"""
import bpy, sys, os, json, bmesh
import numpy as np
from mathutils import Matrix, Vector

src, outd, outglb = [os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:][:3]]
L = 5.5
GRIP_FROM_BUTT = 0.45
MAX_TRIS = 5000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
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
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
# principal axis
c0 = co.mean(0); u, s, vt = np.linalg.svd(co - c0, full_matrices=False); ax = vt[0]
t = (co - c0) @ ax
# thick end = larger radius in the last 15 % of each end
def end_radius(mask):
    p = co[mask] - c0; p = p - np.outer(p @ ax, ax); return np.linalg.norm(p, axis=1).max()
lo, hi = t.min(), t.max(); span = hi - lo
r_lo = end_radius(t < lo + 0.15 * span); r_hi = end_radius(t > hi - 0.15 * span)
if r_lo > r_hi:          # make +ax point from the handle (butt) to the head
    ax = -ax; t = -t; lo, hi = -hi, -lo
# radial centre of the handle near the butt
hm = (t > lo + 0.03 * span) & (t < lo + 0.12 * span)
hc = (co[hm] - np.outer(t[hm], ax)).mean(0)           # point on the axis through the handle centre (perp. part)
# rotation taking ax -> +Z
R = Vector(ax).rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
sc = L / span
grip = Vector(hc) + Vector(ax) * (lo + GRIP_FROM_BUTT / sc)
M = Matrix.Scale(sc, 4) @ R @ Matrix.Translation(-grip)
me.transform(M)
me.update()
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)

me.calc_loop_triangles(); tris0 = len(me.loop_triangles)
if tris0 > MAX_TRIS:
    m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = (MAX_TRIS * 0.97) / tris0
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier='dec')
me.calc_loop_triangles(); tris1 = len(me.loop_triangles)

img = None
for mt in me.materials:
    if mt and mt.use_nodes:
        for n in mt.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                for l in n.outputs['Color'].links:
                    if l.to_socket.name == 'Base Color':
                        img = n.image
if img is None:
    img = [i for i in bpy.data.images if i.size[0] > 0][0]
w0 = list(img.size)
img.scale(1024, 1024)
png = os.path.join(outd, 'club_albedo.png')
img.filepath_raw = png; img.file_format = 'PNG'; img.save()
img2 = bpy.data.images.load(png); img2.name = 'club_albedo'
mat = bpy.data.materials.new('club_mat'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img2
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0; bsdf.inputs['Roughness'].default_value = 0.85
me.materials.clear(); me.materials.append(mat)
for mt in list(bpy.data.materials):
    if mt != mat:
        bpy.data.materials.remove(mt)
for i in list(bpy.data.images):
    if i != img2:
        bpy.data.images.remove(i)
img2.filepath = '//club_albedo.png'
ob.name = 'club'; me.name = 'club_mesh'
info = {'tris_raw': tris0, 'tris': tris1, 'tex_raw': w0, 'scale': sc, 'r_handle_end': float(min(r_lo, r_hi) * sc),
        'r_head_end': float(max(r_lo, r_hi) * sc),
        'min': co.min(0).round(3).tolist(), 'max': co.max(0).round(3).tolist(), 'grip_from_butt': GRIP_FROM_BUTT}
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outd, 'club.blend'), relative_remap=True)
os.makedirs(os.path.dirname(outglb), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=outglb, export_format='GLB', export_yup=True, export_apply=True,
                          export_materials='EXPORT', export_image_format='AUTO')
print('###CLUB###' + json.dumps(info))
