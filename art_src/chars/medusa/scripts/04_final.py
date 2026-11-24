"""04: final medusa.blend (one mesh + one armature, clean material, transforms applied), rig.json, export/medusa.glb
Blender -b --factory-startup --python 04_final.py"""
import bpy, os, json, numpy as np
from mathutils import Vector, Matrix
S = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(S)
W = os.path.join(D, '..', '..', '..', 'work', 'rig_medusa')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, '03b_skin.blend'))   # 03 + 03b_reweight (review fixes)
sc = bpy.context.scene
arm = bpy.data.objects['medusa_rig']; ob = bpy.data.objects['medusa']; me = ob.data
for o in list(sc.objects):
    if o not in (arm, ob): bpy.data.objects.remove(o)
# debug colour attributes out
for a in list(me.color_attributes): me.color_attributes.remove(a)
# material: reload the albedo from the PNG next to the blend (no packed copy)
png = os.path.join(D, 'medusa_albedo.png')
img = bpy.data.images.load(png, check_existing=False); img.name = 'medusa_albedo_png'
mat = bpy.data.materials['medusa_mat']
tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
old = tex.image; tex.image = img
if old: bpy.data.images.remove(old)
img.name = 'medusa_albedo'
assert len(me.materials) == 1 and me.materials[0] == mat
# transforms
for o in (arm, ob):
    assert o.location.length < 1e-6 and Vector(o.rotation_euler).length < 1e-6 and (o.scale - Vector((1, 1, 1))).length < 1e-6, o.name
ob.matrix_parent_inverse = Matrix.Identity(4)
# weights audit
n = len(me.vertices); gn = {g.index: g.name for g in ob.vertex_groups}
deform = {b.name for b in arm.data.bones if b.use_deform}
cnt = np.zeros(n, int); tot = np.zeros(n)
for v in me.vertices:
    gs = [g for g in v.groups if g.weight > 0]
    cnt[v.index] = len(gs); tot[v.index] = sum(g.weight for g in gs)
    assert all(gn[g.group] in deform for g in gs)
print('###WEIGHTS unweighted', int((cnt == 0).sum()), 'max_inf', int(cnt.max()), 'sum range', float(tot.min()), float(tot.max()))
assert (cnt > 0).all() and cnt.max() <= 4 and abs(tot - 1).max() < 1e-3
co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
me.calc_loop_triangles(); tris = len(me.loop_triangles)
size = co.max(0) - co.min(0)
print('###MESH tris', tris, 'verts', n, 'size', np.round(size, 3).tolist(), 'min', np.round(co.min(0), 3).tolist())
# armature display
arm.data.display_type = 'STICK'; arm.show_in_front = True
for o in (arm, ob): o.select_set(False)
bpy.context.view_layer.objects.active = arm
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'medusa.blend'), relative_remap=True)
print('###IMG', img.filepath, 'packed', bool(img.packed_file))
# ---- rig.json
bones = []
for b in arm.data.bones:
    bones.append({'name': b.name, 'parent': b.parent.name if b.parent else None,
                  'head': [round(v, 4) for v in b.head_local], 'tail': [round(v, 4) for v in b.tail_local], 'deform': b.use_deform})
def bone_local(bname, world_pt):
    M = arm.data.bones[bname].matrix_local
    return [round(v, 4) for v in (M.inverted() @ Vector(world_pt))]
tails = [f'tail_{i:02d}' for i in range(1, 15)]
eye_z = 5.82; face_y = float(co[(np.abs(co[:, 0]) < 0.15) & (np.abs(co[:, 2] - eye_z) < 0.05), 1].min())
sockets = {'head': 'head', 'neck': 'neck', 'tail_tip': 'tail_14', 'eyes': 'head'}
offs = {
    'head': {'loc': bone_local('head', (0, -0.84, 5.85)), 'rot_deg': [0, 0, 0]},
    'neck': {'loc': bone_local('neck', (0, -0.86, 5.33)), 'rot_deg': [0, 0, 0]},
    'tail_tip': {'loc': bone_local('tail_14', arm.data.bones['tail_14'].tail_local), 'rot_deg': [0, 0, 0]},
    'eyes': {'loc': bone_local('head', (0, face_y + 0.05, eye_z)), 'rot_deg': [0, 0, 0]},
}
rig = {
    'id': 'medusa', 'height': round(float(size[2]), 3),
    'size_m': {'x': round(float(size[0]), 3), 'y': round(float(size[1]), 3), 'z': round(float(size[2]), 3)},
    'tris': tris, 'bones': bones,
    'chains': {'spine': ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck', 'head'], 'tail': tails,
               'arm_l': ['shoulder_l', 'upper_arm_l', 'forearm_l', 'hand_l'], 'arm_r': ['shoulder_r', 'upper_arm_r', 'forearm_r', 'hand_r'],
               'hair_l': ['hair_l_01', 'hair_l_02', 'hair_l_03'], 'hair_r': ['hair_r_01', 'hair_r_02', 'hair_r_03']},
    'sockets': sockets, 'socket_offsets': offs,
    'framing': {'default': {'sheet': 'split_sheet.png', 'cam': 'cam.json',
                            'clips': ['idle', 'slither', 'gaze', 'stun_start', 'stunned', 'rise', 'hurt', 'death']},
                'tail_swipe': {'sheet': 'split_sheet_tail_swipe.png', 'cam': 'cam_tail_swipe.json', 'clips': ['tail_swipe']}},
    'lean_recipe': {'pivot_bone': 'tail_03', 'pivot': [0.0, -0.9145, 1.622],
                    'steps': ['move pelvis on the arc about the pivot by the lean angle', 'rotate pelvis by the lean angle',
                              'rotate tail_03 by minus the lean angle']},
    'pairs': [[f'{p}_l', f'{p}_r'] for p in ('shoulder', 'upper_arm', 'forearm', 'hand')] + [[f'hair_l_{k:02d}', f'hair_r_{k:02d}'] for k in (1, 2, 3)],
    'notes': ('Blender Z up, faces -Y, character left = +X, metres; GLB export +Y up. Bone rolls 0. socket_offsets.loc are in the '
              'bone\'s local rest frame (metres from the bone head, Y along the bone; for the vertical head/neck bones local Z = '
              'world -Y = forward). Sockets head/neck/tail_tip are the SPEC 8 logical names; eyes is an extra (gaze beam origin, '
              'on the face between the eyes). Hierarchy: root -> pelvis; pelvis is the centre of gravity and parents BOTH '
              'spine_01 (up) and tail_01 (down the upright tail, round the bend at tail_03/04, then flat along +Y to the tip at '
              'tail_14). Rotating or moving pelvis moves the whole body incl. the grounded tail: LEAN RECIPE (bow, '
              'lean back, head to the floor): move the pelvis on an arc about the tail_03 head (0, -0.9145, 1.622), rotate the '
              'pelvis by the lean angle about the same axis, and counter-rotate tail_03 by minus that angle, so tail_03..14 stay '
              'on the ground (e.g. stunned = ~80 deg forward lean about X; see _lean in work/rig_review_medusa/stress.py). Decision '
              '(owner away): no re-parenting of the tail; animkit can wrap this as a helper. Tail is 14 even segments of 0.84 m (11.8 m '
              'from the pelvis to the tip; the tail lies 9.9 m along the ground behind the body, tip 9.3 m from the pelvis axis; SPEC 3.2/8 '
              'says ~14 m: kept the owner-sheet proportions, the lead should change SPEC to ~10 m; tail_swipe r 7 m is covered). Snake hair is fused into one mesh with the head (no separable snake islands), so there are 6 '
              'hair_* bones, one per visible snake (01 top, 03 bottom), each from inside the hair mass to the snake head. Weights '
              '(03b): neck+head and the shoulders are harmonic blends, so the back-hair curtain (fused to the upper back) grades '
              'spine_03 -> head from z 4.95 to ~5.95 and the shoulder tops carry no neck/head weight; the face above the jaw line is '
              'head 1.0; each snake ramps from head to its hair bone over the first 20 cm (55 cm for the low hair_*_03 snakes). '
              'Max edge stretch: head turn 45 / nod 40 ~5 cm, neck turn 35 ~4 cm, clavicle up 30 ~3 cm. '
              'FRAMING: split_sheet.png + cam.json (1920x1080) for idle, slither, gaze, stun_start, stunned, rise, hurt, death; '
              'split_sheet_tail_swipe.png + cam_tail_swipe.json (1920x1080, front +-10 m, side y -10.5..+10) for tail_swipe only.')
}
json.dump(rig, open(os.path.join(D, 'rig.json'), 'w'), indent=1)
print('###RIG bones', len(bones), 'deform', sum(b['deform'] for b in bones))
# ---- GLB test export (mesh + skeleton, no animation)
os.makedirs(os.path.join(D, 'export'), exist_ok=True)
glb = os.path.join(D, 'export', 'medusa.glb')
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); ob.select_set(True)
kw = dict(filepath=glb, export_format='GLB', use_selection=True, export_yup=True, export_skins=True,
          export_animations=False, export_apply=False, export_materials='EXPORT', export_image_format='AUTO')
try:
    bpy.ops.export_scene.gltf(**kw, export_def_bones=False)
except TypeError:
    bpy.ops.export_scene.gltf(**kw)
print('###GLB', glb, os.path.getsize(glb))
