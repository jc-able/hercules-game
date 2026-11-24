"""Step 2: build the armature from ../joints.json and parent the mesh to it (no weights yet).
Blender -b --factory-startup <work>/01_clean.blend --python 02_bones.py -- <chars/cyclops dir> <work dir>
"""
import bpy, sys, os, json
from mathutils import Vector

D, W = sys.argv[sys.argv.index('--') + 1:][:2]
J = json.load(open(os.path.join(D, 'joints.json')))
ob = bpy.data.objects['cyclops']
for o in list(bpy.context.scene.objects):
    if o.type == 'ARMATURE':
        bpy.data.objects.remove(o, do_unlink=True)
arm = bpy.data.armatures.new('cyclops_rig')
ao = bpy.data.objects.new('cyclops_rig', arm)
bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for b in J['bones']:
    e = arm.edit_bones.new(b['name'])
    e.head = Vector(b['head']); e.tail = Vector(b['tail'])
    e.use_deform = b['deform']
    eb[b['name']] = e
for b in J['bones']:
    if b['parent']:
        e = eb[b['name']]; p = eb[b['parent']]
        e.parent = p
        e.use_connect = (p.tail - e.head).length < 1e-4
# rolls: point each bone's local Z towards world -Y (the character's front) where possible, +Z for horizontal/foot bones
for e in arm.edit_bones:
    d = (e.tail - e.head).normalized()
    if abs(d.y) > 0.7:          # foot / toe / root-like bones along Y
        e.align_roll(Vector((0, 0, 1)))
    else:
        e.align_roll(Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
ob.parent = ao
ob.matrix_parent_inverse.identity()
for m in list(ob.modifiers):
    ob.modifiers.remove(m)
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = ao
print('###BONES###', len(arm.bones), sum(b.use_deform for b in arm.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, '02_bones.blend'))
