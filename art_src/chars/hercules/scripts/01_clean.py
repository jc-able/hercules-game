"""Step 1: raw.glb -> hercules_01_clean.blend
Mesh baked to world space (scale 0.01 applied), Icosphere deleted, actions removed, fresh armature built from the
Meshy joint positions with convention names + a root bone, vertex groups renamed (headfront merged into head).
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'raw.glb')
OUT = os.path.join(HERE, 'work', 'hercules_01_clean.blend')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

RENAME = {
    'Hips': 'hips', 'Spine02': 'spine_01', 'Spine01': 'spine_02', 'Spine': 'spine_03', 'neck': 'neck', 'Head': 'head',
    'LeftShoulder': 'shoulder_l', 'LeftArm': 'upper_arm_l', 'LeftForeArm': 'forearm_l', 'LeftHand': 'hand_l',
    'RightShoulder': 'shoulder_r', 'RightArm': 'upper_arm_r', 'RightForeArm': 'forearm_r', 'RightHand': 'hand_r',
    'LeftUpLeg': 'thigh_l', 'LeftLeg': 'shin_l', 'LeftFoot': 'foot_l', 'LeftToeBase': 'toe_l',
    'RightUpLeg': 'thigh_r', 'RightLeg': 'shin_r', 'RightFoot': 'foot_r', 'RightToeBase': 'toe_r',
}
MERGE = {'headfront': 'Head', 'head_end': 'Head'}   # weighted helper bones folded into their parent

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH' and o.data.materials)

# --- does the bundled action pose differ from rest? (compare evaluated mesh posed vs rest)
dg = bpy.context.evaluated_depsgraph_get()
def eval_co():
    dg.update()
    ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)
posed = eval_co()
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
rest = eval_co()
print('###ACTION_VS_REST max vertex delta (mesh units):', float(np.abs(posed - rest).max()))

# --- joint positions in world space (rest)
Mw = arm.matrix_world.copy()
joints = {b.name: Mw @ b.head_local for b in arm.data.bones}
parents = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}

# --- mesh to world space, unparent
mw = mesh.matrix_world.copy()
mesh.parent = None
mesh.data.transform(mw)
mesh.matrix_world = Matrix.Identity(4)
for m in list(mesh.modifiers):
    mesh.modifiers.remove(m)

# --- merge helper groups, rename groups
vg = mesh.vertex_groups
for src, dst in MERGE.items():
    if src not in vg:
        continue
    gs, gd = vg[src], vg[dst]
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group == gs.index and g.weight > 0:
                w = g.weight
                cur = 0.0
                for g2 in v.groups:
                    if g2.group == gd.index:
                        cur = g2.weight
                gd.add([v.index], cur + w, 'REPLACE')
    vg.remove(gs)
for g in vg:
    if g.name in RENAME:
        g.name = RENAME[g.name]

# --- delete everything but the mesh
for o in list(sc.objects):
    if o != mesh:
        bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for a in list(bpy.data.armatures):
    bpy.data.armatures.remove(a)
for m in list(bpy.data.meshes):
    if m.users == 0:
        bpy.data.meshes.remove(m)
mesh.name = 'hercules'; mesh.data.name = 'hercules_mesh'

# --- mesh-derived end points
co = np.array([v.co[:] for v in mesh.data.vertices])
def group_verts(name):
    gi = vg[name].index
    ids = [v.index for v in mesh.data.vertices for g in v.groups if g.group == gi and g.weight > 0.5]
    return co[ids]
J = {RENAME.get(k, k): np.array(v[:]) for k, v in joints.items() if k in RENAME}
hand_tail = {}
for s in 'lr':
    d = J[f'hand_{s}'] - J[f'forearm_{s}']; d /= np.linalg.norm(d)
    hv = group_verts(f'hand_{s}')
    ext = ((hv - J[f'hand_{s}']) @ d).max()
    hand_tail[s] = J[f'hand_{s}'] + d * ext * 0.9
    tv = group_verts(f'toe_{s}')
    tip = tv[np.argmin(tv[:, 1])]
    J[f'toe_tip_{s}'] = np.array([J[f'toe_{s}'][0], tip[1], J[f'toe_{s}'][2]])
head_top = co[:, 2].max()

# --- build the armature
ad = bpy.data.armatures.new('hercules_rig')
ao = bpy.data.objects.new('hercules_rig', ad)
sc.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao
ao.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
CHILD = {'hips': 'spine_01', 'spine_01': 'spine_02', 'spine_02': 'spine_03', 'spine_03': 'neck', 'neck': 'head'}
for s in 'lr':
    CHILD.update({f'shoulder_{s}': f'upper_arm_{s}', f'upper_arm_{s}': f'forearm_{s}', f'forearm_{s}': f'hand_{s}',
                  f'thigh_{s}': f'shin_{s}', f'shin_{s}': f'foot_{s}', f'foot_{s}': f'toe_{s}'})
root = eb.new('root'); root.head = (0, 0, 0); root.tail = (0, 0.3, 0); root.use_deform = False
order = ['hips', 'spine_01', 'spine_02', 'spine_03', 'neck', 'head'] + \
        [f'{b}_{s}' for s in 'lr' for b in ('shoulder', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot', 'toe')]
inv = {v: k for k, v in RENAME.items()}
for n in order:
    b = eb.new(n)
    b.head = Vector(J[n])
    if n in CHILD:
        b.tail = Vector(J[CHILD[n]])
    elif n == 'head':
        b.tail = Vector((J['head'][0], J['head'][1], head_top - 0.01))
    elif n.startswith('hand_'):
        b.tail = Vector(hand_tail[n[-1]])
    elif n.startswith('toe_'):
        b.tail = Vector(J[f'toe_tip_{n[-1]}'])
    b.use_deform = True
for n in order:
    p = parents[inv[n]]
    eb[n].parent = eb[RENAME[p]] if p else eb['root']
    eb[n].use_connect = False
# simple consistent rolls: Z axis toward -Y (front) for vertical bones, toward +Z for horizontal-ish ones
for b in eb:
    b.align_roll(Vector((0, -1, 0)) if abs(b.vector.normalized().z) > 0.7 else Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')

mesh.parent = ao
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = ao

# --- material: Principled with base colour texture only, texture saved as PNG
tex_path = os.path.join(HERE, 'hercules_albedo.png')
img = next(i for i in bpy.data.images if i.size[0] > 0)
print('###IMAGE', img.name, img.size[:], img.file_format, 'alpha', img.alpha_mode)
img.filepath_raw = tex_path; img.file_format = 'PNG'; img.save()
img2 = bpy.data.images.load(tex_path); img2.name = 'hercules_albedo'
mat = bpy.data.materials.new('hercules_mat'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img2
nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.8
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for m in list(bpy.data.materials):
    if m.users == 0:
        bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i.users == 0:
        bpy.data.images.remove(i)

me = mesh.data; me.calc_loop_triangles()
print('###CLEAN', json.dumps({'tris': len(me.loop_triangles), 'verts': len(me.vertices),
      'bbmin': co.min(0).round(4).tolist(), 'bbmax': co.max(0).round(4).tolist(), 'bones': len(ad.bones),
      'groups': [g.name for g in mesh.vertex_groups]}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('###SAVED', OUT)
