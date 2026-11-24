"""Step 5: 03_skin.blend -> art_src/chars/hydra/hydra.blend (+ rig.json, export/hydra.glb) and checks.
  Blender -b --factory-startup --python 05_finalize.py"""
import bpy, os, json, math, numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); CH = os.path.dirname(HERE)
WIP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CH))), 'work', 'rig_hydra', 'wip')
bpy.ops.wm.open_mainfile(filepath=os.path.join(WIP, '03_skin.blend'))
mesh = bpy.data.objects['hydra']; arm = bpy.data.objects['hydra_rig']
for o in list(bpy.data.objects):
    if o not in (mesh, arm): bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
    for d in list(coll): coll.remove(d)
me = mesh.data
for ca in list(me.color_attributes): me.color_attributes.remove(ca)
assert mesh.matrix_world == Matrix.Identity(4) and arm.matrix_world == Matrix.Identity(4)
assert mesh.location.length == 0 and arm.location.length == 0
arm.data.pose_position = 'POSE'
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
# --- weight checks
nv = len(me.vertices); maxinf = 0; bad_sum = 0; empty = 0
for v in me.vertices:
    gs = [g for g in v.groups if g.weight > 0]
    maxinf = max(maxinf, len(gs)); s = sum(g.weight for g in gs)
    if not gs: empty += 1
    elif abs(s - 1) > 1e-3: bad_sum += 1
me.calc_loop_triangles()
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
img = bpy.data.images['hydra_albedo']
# --- save the blend next to the texture
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CH, 'hydra.blend'), relative_remap=True)
img_path = bpy.data.images['hydra_albedo'].filepath
# --- rig.json
B = arm.data.bones
def r3(v): return [round(float(x), 4) for x in v]
bones = [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'head': r3(b.head_local), 'tail': r3(b.tail_local),
          'deform': b.use_deform} for b in B]
def chain(prefix, names): return [n for n in names if n in B]
chains = {'spine': ['hips', 'spine_01', 'spine_02', 'spine_03'], 'tail': [f'tail_{i:02d}' for i in range(1, 9)]}
for s in ('fl', 'fr', 'bl', 'br'): chains['leg_' + s] = [f'leg_{s}_01', f'leg_{s}_02', f'leg_{s}_03', f'foot_{s}']
chains['neck_c'] = [f'neck_c_{i:02d}' for i in range(1, 6)] + ['head_c', 'jaw_c']
for k in range(1, 9): chains[f'neck_{k}'] = [f'neck_{k}_{i:02d}' for i in range(1, 5)] + [f'head_{k}']
def local_offset(bone, world_pt):
    M = B[bone].matrix_local
    return r3(M.inverted() @ Vector(world_pt))
def lerp(a, b, t): return Vector(a).lerp(Vector(b), t)
sockets = {'head_c': 'head_c', 'jaw_c': 'jaw_c', 'foot_fl': 'foot_fl', 'foot_fr': 'foot_fr'}
for k in range(1, 9): sockets[f'head_{k}'] = f'head_{k}'
offs = {}; world = {}
# jaw weak point = soft underside of the lower jaw: lowest skin under the middle of the jaw bone
jm = lerp(B['jaw_c'].head_local, B['jaw_c'].tail_local, 0.45)
under = co[(np.abs(co[:, 0]) < 0.35) & (np.abs(co[:, 1] - jm.y) < 0.35)]
under = under[(under[:, 2] < jm.z) & (under[:, 2] > jm.z - 1.0)]
jw = Vector((0.0, jm.y, float(under[:, 2].min()) if len(under) else jm.z - 0.3))
world['jaw_c'] = jw
for s, b in sockets.items():
    if s == 'jaw_c': continue
    if s.startswith('foot'):
        p = lerp(B[b].head_local, B[b].tail_local, 0.35); p.z = 0.0          # ground contact under the foot
    else:
        p = lerp(B[b].head_local, B[b].tail_local, 0.45)                    # centre of the skull
    world[s] = p
for s, b in sockets.items():
    offs[s] = {'loc': local_offset(b, world[s]), 'rot_deg': [0, 0, 0]}
def to_godot(v): return r3((v.x, v.z, -v.y))
# bow head_down recipe (from poses.json) + measured jaw socket height in that pose
BOW = json.load(open(os.path.join(HERE, 'poses.json')))['head_down_bow']
exec(open(os.path.join(HERE, 'posing.py')).read())
apply_pose(arm, BOW)
BOW_JAW_Z = round(float((arm.pose.bones['jaw_c'].matrix @ Vector(offs['jaw_c']['loc'])).z), 3)
apply_pose(arm, {})
print('###BOW### jaw socket z', BOW_JAW_Z)
pairs = []
for s in ('f', 'b'):
    for i in range(1, 4): pairs.append([f'leg_{s}l_{i:02d}', f'leg_{s}r_{i:02d}'])
    pairs.append([f'foot_{s}l', f'foot_{s}r'])
for a_, b_ in ((5, 4), (6, 3), (7, 2), (8, 1)):     # character-left neck first
    for i in range(1, 5): pairs.append([f'neck_{a_}_{i:02d}', f'neck_{b_}_{i:02d}'])
    pairs.append([f'head_{a_}', f'head_{b_}'])
size = (co.max(0) - co.min(0))
rig = {
 'id': 'hydra', 'height': round(float(co[:, 2].max()), 3), 'shoulder_height': 6.5,
 'size_xyz_m': r3(size), 'bounds_min': r3(co.min(0)), 'bounds_max': r3(co.max(0)),
 'bones': bones, 'chains': chains, 'sockets': sockets, 'socket_offsets': offs,
 'socket_rest_world_blender': {k: r3(v) for k, v in world.items()},
 'socket_rest_world_godot': {k: to_godot(v) for k, v in world.items()},
 'weak_points': {'jaw': 'jaw_c'},
 'pairs': pairs,
 'notes': ('Blender: Z up, faces -Y, metres; GLB export +Y up (faces +Z in Godot). socket_offsets.loc are in the bone\'s own rest frame '
           '(Y = along the bone head->tail, Blender/Godot convention); socket_rest_world_* give the same points in model space. '
           'Necks are numbered left to right in the front view: 1-4 on the character\'s right (-X), 5-8 on its left (+X); '
           'on each side the outermost/lowest head is 1 (right) / 8 (left) and the inner top heads are 4 and 5, so mirror pairs are '
           '1-8, 2-7, 3-6, 4-5. Leg bones: leg_<fl|fr|bl|br>_01 = shoulder/hip -> elbow/knee, _02 -> wrist/hock, _03 -> ankle, foot_* -> toe tip. '
           'Rest pose = the generated neutral pose. Bone rolls are 0: animate in armature-space angles. '
           'The jaw is fused in the mesh (no mouth interior): jaw_c opens the lower face by stretching, keep it within ~20 deg. '
           'The touching necks were ripped apart along their fused seams (vertices duplicated, no faces added), so a neck that leaves its neighbour '
           'shows a narrow open seam instead of a membrane: keep hydra_mat double-sided (glTF doubleSided = true -> Godot cull_mode disabled). '
           'Fix round 1: the headless 10th tube that stood behind the centre neck was deleted from the mesh (1,775 verts) and its opening capped; '
           'neck_c can now bend forward freely (each joint up to ~25 deg). The outer (back) side of the thick centre-neck base still stretches '
           'smoothly in a deep bow (no tear). '
           'head_down (jaw weak point, SPEC 3.3): neck bends alone cannot bring the head down (neck base 6.8 m, chain 5.6 m). Use the BOW in '
           'clip_recipes.head_down_bow: spine_01 +10, spine_02 +12, spine_03 +25, neck_c 25/25/20/15/10, head_c -30, front legs folded by IK so the '
           'front feet stay planted (leg_f*_01 -28, _02 -94, _03 +75; elbows stay behind), hind legs untouched. Result: jaw_c socket at z ~1.2 m, '
           'snout ~0.2 m above the ground, shoulders down ~1.45 m. Optionally let neck_4_01/neck_5_01 follow +10..15 deg. Target for the clip: jaw_c socket z <= 1.5 m. '
           'Scale (fix round 1, lead to confirm): kept at the brief\'s 6.5 m shoulder, so heads reach 12.2-13.5 m (centre horns 14.4 m) and '
           'nose-to-tail is 16.0 m, not SPEC 3.3\'s ~11 m heads / ~18 m; a x0.80 scale would give 11 m heads but a 5.2 m shoulder.'),
 'clip_recipes': {'head_down_bow': dict(pose=BOW, target='jaw_c socket z <= 1.5 m', measured_jaw_socket_z=BOW_JAW_Z,
                  convention='armature-space XYZ degrees applied in the bone rest frame (posing.py); compounds down the chain')},
}
json.dump(rig, open(os.path.join(CH, 'rig.json'), 'w'), indent=1)
# --- glb export (mesh + skeleton, no animation)
os.makedirs(os.path.join(CH, 'export'), exist_ok=True)
glb = os.path.join(CH, 'export', 'hydra.glb')
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_yup=True, export_skins=True,
                          export_animations=False, export_apply=False, export_materials='EXPORT', export_image_format='AUTO')
print('###FINAL###', json.dumps(dict(verts=nv, tris=len(me.loop_triangles), bones=len(B), deform=sum(b.use_deform for b in B),
      max_influences=maxinf, verts_bad_sum=bad_sum, verts_unweighted=empty, size=r3(size), img=img_path,
      glb_bytes=os.path.getsize(glb))))
# --- re-import check
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']; ars = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
skinned = [o.name for o in ms if any(m.type == 'ARMATURE' for m in o.modifiers)]
co2 = []
for o in ms:
    M = np.array(o.matrix_world); c = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', c)
    co2.append(c.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
co2 = np.concatenate(co2)
print('###REIMPORT###', json.dumps(dict(meshes=len(ms), armatures=len(ars), bones=[len(a.data.bones) for a in ars], skinned=skinned,
      groups=[len(o.vertex_groups) for o in ms], min=r3(co2.min(0)), max=r3(co2.max(0)),
      images=[(i.name, i.size[0], i.size[1]) for i in bpy.data.images])))
