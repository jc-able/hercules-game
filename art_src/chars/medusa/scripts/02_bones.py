"""02: build the armature from scripts/bones_spec.json (computed from the mesh by make_spec.py) -> work/rig_medusa/02_bones.blend"""
import bpy, os, json
S = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(S)
W = os.path.join(D, '..', '..', '..', 'work', 'rig_medusa')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, '01_clean.blend'))
spec = json.load(open(os.path.join(S, 'bones_spec.json')))
ad = bpy.data.armatures.new('medusa_rig'); ad.display_type = 'STICK'
arm = bpy.data.objects.new('medusa_rig', ad); bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for b in spec:
    eb = ad.edit_bones.new(b['name']); eb.head = b['head']; eb.tail = b['tail']; eb.roll = 0
    eb.use_deform = b['deform']
for b in spec:
    if b['parent']:
        eb = ad.edit_bones[b['name']]; eb.parent = ad.edit_bones[b['parent']]
        eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
ob = bpy.data.objects['medusa']
ob.parent = arm
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
print('###BONES', len(ad.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, '02_bones.blend'))
