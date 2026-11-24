"""Step 4: clean the generated weapon props -> art_src/props/<name>.blend + game/assets/props/<name>.glb
  sword : 0.85 m long, origin at the grip centre, blade along +Z (Blender) = +Y (Godot), edges along +-Y (Blender)
  shield: 0.90 m across, origin at the centre of the back (arm strap), face toward -Y (Blender) = +Z (Godot)
  <= 4000 triangles, texture 1024 px, one Principled material (base colour only).
  Blender -b --factory-startup --python 04_props.py -- sword|shield
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix

name = sys.argv[sys.argv.index('--') + 1]
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'art_src', 'props', 'raw', f'prop_{name}.glb')
OUT_BLEND = os.path.join(REPO, 'art_src', 'props', f'{name}.blend')
OUT_TEX = os.path.join(REPO, 'art_src', 'props', f'{name}_albedo.png')
OUT_GLB = os.path.join(REPO, 'game', 'assets', 'props', f'{name}.glb')
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
MAX_TRIS = 4000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
for o in list(bpy.context.scene.objects):
    if o != ob:
        bpy.data.objects.remove(o, do_unlink=True)
ob.parent = None
ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(me); bm.free()

co = np.array([v.co[:] for v in me.vertices])
mn, mx = co.min(0), co.max(0)
if name == 'sword':
    L = mx[2] - mn[2]; s = 0.85 / L
    zs = np.linspace(mn[2], mx[2], 121)
    width = []
    for a, b in zip(zs[:-1], zs[1:]):
        m = (co[:, 2] >= a) & (co[:, 2] < b)
        width.append(np.ptp(co[m, 1]) if m.sum() > 2 else 0)
    width = np.array(width); zc = (zs[:-1] + zs[1:]) / 2
    g = int(np.argmax(width[:60]))                      # crossguard: widest slice in the lower half
    below = np.arange(g)
    wmin = width[below][width[below] > 0].min()
    grip = below[(width[below] < wmin * 1.35) & (width[below] > 0)]
    grip_z = float((zc[grip].min() + zc[grip].max()) / 2)
    m = np.abs(co[:, 2] - grip_z) < 0.02
    origin = Vector((float(co[m, 0].mean()), float(co[m, 1].mean()), grip_z))
    info = {'guard_z_raw': float(zc[g]), 'grip_z_raw': grip_z, 'grip_len_raw': float(zc[grip].max() - zc[grip].min())}
else:
    D = max(mx[0] - mn[0], mx[2] - mn[2]); s = 0.90 / D
    cx, cz = (mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2
    m = (np.abs(co[:, 0] - cx) < 0.05) & (np.abs(co[:, 2] - cz) < 0.05)
    origin = Vector((cx, float(co[m, 1].max()), cz))  # back surface at the centre
    info = {'back_y_raw': float(co[m, 1].max()), 'front_y_raw': float(co[:, 1].min())}
me.transform(Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-origin))

# decimate
me.calc_loop_triangles(); t0 = len(me.loop_triangles)
mod = ob.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
mod.ratio = (MAX_TRIS * 0.97) / t0; mod.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_apply(modifier='dec')
me.calc_loop_triangles(); t1 = len(me.loop_triangles)

# texture + material
img = next(i for i in bpy.data.images if i.size[0] > 0)
img.scale(1024, 1024)
img.filepath_raw = OUT_TEX; img.file_format = 'PNG'; img.save()
img2 = bpy.data.images.load(OUT_TEX); img2.name = f'{name}_albedo'
mat = bpy.data.materials.new(f'{name}_mat'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img2
nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0; bsdf.inputs['Roughness'].default_value = 0.6
me.materials.clear(); me.materials.append(mat)
for x in list(bpy.data.materials):
    if x.users == 0: bpy.data.materials.remove(x)
for x in list(bpy.data.images):
    if x.users == 0: bpy.data.images.remove(x)
ob.name = f'prop_{name}'; me.name = f'prop_{name}_mesh'
co = np.array([v.co[:] for v in me.vertices])
info.update({'tris_raw': t0, 'tris': t1, 'scale': s, 'bbmin': co.min(0).round(4).tolist(), 'bbmax': co.max(0).round(4).tolist()})
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', export_yup=True, use_selection=False, export_animations=False)
info['glb_bytes'] = os.path.getsize(OUT_GLB)
print('###PROP', name, json.dumps(info))
