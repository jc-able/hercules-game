"""Step 5: final blend + rig.json + GLB export + re-import check.

Blender -b --factory-startup --python 05_final.py -- <skinned.blend> <chardir>
"""
import bpy, sys, os, json
import numpy as np

SRC, CH = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['pegasus_rig']; ob = bpy.data.objects['pegasus']
for o in list(sc.objects):
    if o not in (arm, ob): bpy.data.objects.remove(o)
for ca in list(ob.data.color_attributes): ob.data.color_attributes.remove(ca)   # no vertex-colour tint in engines
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
arm.data.pose_position = 'POSE'
for o in (arm, ob):
    assert tuple(o.location) == (0, 0, 0) and tuple(o.rotation_euler) == (0, 0, 0) and tuple(o.scale) == (1, 1, 1), o.name
# purge leftovers
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.worlds, bpy.data.armatures):
    for d in list(blk):
        if d.users == 0: blk.remove(d)

# skin checks
me = ob.data
nv = len(me.vertices)
ng = np.array([len([g for g in v.groups if g.weight > 0]) for v in me.vertices])
ws = np.array([sum(g.weight for g in v.groups) for v in me.vertices])
me.calc_loop_triangles()
img = bpy.data.images['pegasus_albedo']
check = {'verts': nv, 'tris': len(me.loop_triangles), 'unweighted': int((ng == 0).sum()), 'max_influences': int(ng.max()),
         'weight_sum_min': round(float(ws.min()), 4), 'weight_sum_max': round(float(ws.max()), 4),
         'bones': len(arm.data.bones), 'deform_bones': sum(b.use_deform for b in arm.data.bones),
         'texture': list(img.size), 'materials': [m.name for m in me.materials]}
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
check['size'] = [round(float(v), 3) for v in co.max(0) - co.min(0)]
check['min'] = [round(float(v), 3) for v in co.min(0)]
print('###CHECK###' + json.dumps(check))

blend = os.path.join(CH, 'pegasus.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
img.filepath = '//pegasus_albedo.png'
bpy.ops.wm.save_as_mainfile(filepath=blend, relative_remap=True)

# rig.json
def chain(*n): return list(n)
bones = []
for b in arm.data.bones:
    bones.append({'name': b.name, 'parent': b.parent.name if b.parent else None,
                  'head': [round(v, 4) for v in b.head_local], 'tail': [round(v, 4) for v in b.tail_local],
                  'deform': b.use_deform})
rig = {
    'id': 'pegasus', 'height': round(float(co[:, 2].max()), 3), 'withers': 1.9,
    'size_xyz': check['size'],
    'bones': bones,
    'chains': {
        'spine': chain('hips', 'spine_01', 'spine_02', 'spine_03'),
        'neck': chain('neck_01', 'neck_02', 'neck_03', 'head'),
        'tail': chain('tail_01', 'tail_02', 'tail_03', 'tail_04', 'tail_05'),
        **{f'leg_{k}': chain(f'leg_{k}_01', f'leg_{k}_02', f'leg_{k}_03', f'hoof_{k}') for k in ('fl', 'fr', 'bl', 'br')},
        'wing_l': chain('wing_l_01', 'wing_l_02', 'wing_l_03'),
        'wing_r': chain('wing_r_01', 'wing_r_02', 'wing_r_03'),
        'wing_l_feathers': chain('wing_l_feather_01', 'wing_l_feather_02', 'wing_l_feather_03'),
        'wing_r_feathers': chain('wing_r_feather_01', 'wing_r_feather_02', 'wing_r_feather_03'),
    },
    'sockets': {'saddle': 'saddle', 'head': 'head'},
    'socket_offsets': {'saddle': {'loc': [0.0, 0.0, 0.0], 'rot_deg': [0.0, 0.0, 0.0]},
                       'head': {'loc': [0.0, -0.22, -0.17], 'rot_deg': [0.0, 0.0, 0.0]}},
    'pairs': [[f'leg_fl_0{i}', f'leg_fr_0{i}'] for i in (1, 2, 3)] + [['hoof_fl', 'hoof_fr']] +
             [[f'leg_bl_0{i}', f'leg_br_0{i}'] for i in (1, 2, 3)] + [['hoof_bl', 'hoof_br']] +
             [[f'wing_l_0{i}', f'wing_r_0{i}'] for i in (1, 2, 3)] +
             [[f'wing_l_feather_0{i}', f'wing_r_feather_0{i}'] for i in (1, 2, 3)],
    'notes': ('Blender Z up, faces -Y, left = +X, metres; all bone rolls 0. root and saddle do not deform. '
              'saddle head sits on the back surface (z 1.88) behind the withers, between the wing roots: the rider hips go '
              'there. socket_offsets loc are armature-space metres relative to the bone head (head offset = middle of the '
              'skull). Legs: leg_*_01 = shoulder point->elbow (front) / hip->stifle (hind), _02 forearm / gaskin, '
              '_03 cannon, hoof_* fetlock->ground. Wings rest raised and folded back; the arm (wing_*_01) points up from a '
              'broad root on the shoulder, so a flap is mostly a rotation about armature X+Y at wing_*_01 (see '
              'docs/notes/rig_pegasus.md for tested glide/down/up angles). feather_01 = secondaries (child of wing_02), '
              'feather_02 = lower primaries (child of wing_02), feather_03 = mid primaries (child of wing_03); keep '
              'relative fan/curl rotations within ~20 deg: neighbouring feathers are fused in the mesh. '
              'Mane rides neck_01..03/head; the rear mane behind rest y -0.6 (lying on the withers) rides neck_01 + spine_03 only, '
              'and the back behind the wing roots (y > -0.30, where the rider sits) has no neck weight, so neck moves do not '
              'move the saddle area. The fused mane/wing-root and wing-lobe/flank contacts are blended, not ripped (a rip '
              'opens see-through holes); the hanging feather lobe rides the wing. Breastplate rides spine_03. Tail hair rides tail_01..05/hips (5 bones). '
              'Keep neck_01/neck_02 within ~25/15 deg and tail lift within ~60 deg for clean skin.'),
}
json.dump(rig, open(os.path.join(CH, 'rig.json'), 'w'), indent=1)

# GLB export (+Y up), mesh + skeleton, no animation
os.makedirs(os.path.join(CH, 'export'), exist_ok=True)
glb = os.path.join(CH, 'export', 'pegasus.glb')
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_yup=True,
                          export_animations=False, export_skins=True, export_apply=False)
print('###GLB###', glb, os.path.getsize(glb))

# re-import in an empty scene
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
ars = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
skinned = [o for o in ms if any(m.type == 'ARMATURE' for m in o.modifiers)]
re = {'meshes': len(ms), 'armatures': len(ars), 'bones': [len(a.data.bones) for a in ars], 'skinned_meshes': len(skinned),
      'vgroups': [len(o.vertex_groups) for o in ms], 'tris': sum(len(o.data.polygons) for o in ms),
      'images': [(i.name, i.size[0]) for i in bpy.data.images], 'colour_attrs': [len(o.data.color_attributes) for o in ms]}
print('###REIMPORT###' + json.dumps(re))
