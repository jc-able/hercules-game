"""Step 2: build the armature. Joint positions measured from the stage-1 mesh (edge-plane sections, see
work/rig_pegasus/*.py): leg columns + narrowings (fetlock/knee/hock), tail and neck sections, wing points picked in a
view perpendicular to the wing plane (normal ~ (0.87,-0.49,0)) and mapped back to 3D from a dense surface sample.
Left = +X (the horse faces -Y). Right side = mirror.

Blender -b --factory-startup --python 02_bones.py -- <workdir>   (reads stage1.blend, writes stage2.blend + bones.json)
"""
import bpy, sys, os, json
from mathutils import Vector

WK = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=os.path.join(WK, 'stage1.blend'))

# name: (head, tail, parent, deform)   -- left-side limbs only, mirrored below
B = {
    'root':    ((0, 0, 0), (0, -0.4, 0), None, False),
    'hips':    ((0, 0.30, 1.58), (0, 0.72, 1.62), 'root', True),
    'spine_01': ((0, 0.30, 1.58), (0, -0.05, 1.60), 'hips', True),
    'spine_02': ((0, -0.05, 1.60), (0, -0.40, 1.62), 'spine_01', True),
    'spine_03': ((0, -0.40, 1.62), (0, -0.70, 1.72), 'spine_02', True),
    'neck_01': ((0, -0.70, 1.72), (0, -0.86, 2.05), 'spine_03', True),
    'neck_02': ((0, -0.86, 2.05), (0, -0.95, 2.33), 'neck_01', True),
    'neck_03': ((0, -0.95, 2.33), (0, -1.03, 2.62), 'neck_02', True),
    'head':    ((0, -1.03, 2.62), (0, -1.50, 2.22), 'neck_03', True),
    # tail: 5 bones at even arc length (~0.25 m) on the tail-hair centre line (slice centroids of the blue tail hair,
    # work/rig_pegasus/fix/tailline.py); rig review: 3 bones stretched the hair base and looked stiff
    'tail_01': ((0, 0.85, 1.72), (0.01, 1.00, 1.52), 'hips', True),
    'tail_02': ((0.01, 1.00, 1.52), (0.015, 1.09, 1.28), 'tail_01', True),
    'tail_03': ((0.015, 1.09, 1.28), (0.025, 1.10, 1.03), 'tail_02', True),
    'tail_04': ((0.025, 1.10, 1.03), (0.04, 1.20, 0.80), 'tail_03', True),
    'tail_05': ((0.04, 1.20, 0.80), (0.07, 1.17, 0.55), 'tail_04', True),
    'saddle':  ((0, 0.10, 1.88), (0, 0.10, 2.13), 'spine_02', False),
    # front leg: shoulder point -> elbow -> knee -> fetlock -> hoof
    'leg_fl_01': ((0.160, -0.90, 1.47), (0.175, -0.75, 1.17), 'spine_03', True),
    'leg_fl_02': ((0.175, -0.75, 1.17), (0.148, -0.775, 0.70), 'leg_fl_01', True),
    'leg_fl_03': ((0.148, -0.775, 0.70), (0.147, -0.785, 0.26), 'leg_fl_02', True),
    'hoof_fl':   ((0.147, -0.785, 0.26), (0.156, -0.93, 0.02), 'leg_fl_03', True),
    # hind leg: hip -> stifle -> hock -> fetlock -> hoof
    'leg_bl_01': ((0.220, 0.68, 1.50), (0.255, 0.45, 1.15), 'hips', True),
    'leg_bl_02': ((0.255, 0.45, 1.15), (0.265, 0.72, 0.70), 'leg_bl_01', True),
    'leg_bl_03': ((0.265, 0.72, 0.70), (0.290, 0.757, 0.29), 'leg_bl_02', True),
    'hoof_bl':   ((0.290, 0.757, 0.29), (0.325, 0.665, 0.02), 'leg_bl_03', True),
    # wing: root -> elbow -> wrist -> primary tip, + 3 feather fans
    'wing_l_01': ((0.24, -0.38, 1.92), (0.53, 0.04, 2.62), 'spine_02', True),
    'wing_l_02': ((0.53, 0.04, 2.62), (0.66, 0.43, 2.85), 'wing_l_01', True),
    'wing_l_03': ((0.66, 0.43, 2.85), (0.97, 1.06, 2.61), 'wing_l_02', True),
    'wing_l_feather_01': ((0.58, 0.13, 2.45), (0.83, 0.39, 1.05), 'wing_l_02', True),
    'wing_l_feather_02': ((0.76, 0.43, 2.60), (1.11, 0.69, 1.60), 'wing_l_02', True),  # lower primaries hang from the wrist: child of the forearm so a hand curl moves only the upper primaries
    'wing_l_feather_03': ((0.74, 0.56, 2.75), (1.08, 0.93, 2.27), 'wing_l_03', True),
}

def mirror_name(n):
    if n is None: return None
    for a, b in (('_fl', '_fr'), ('_bl', '_br'), ('wing_l', 'wing_r')):
        if a in n: return n.replace(a, b)
    return n

full = {}
for n, (h, t, p, d) in B.items():
    full[n] = (h, t, p, d)
    m = mirror_name(n)
    if m != n:
        full[m] = ((-h[0], h[1], h[2]), (-t[0], t[1], t[2]), mirror_name(p), d)

ad = bpy.data.armatures.new('pegasus_rig')
arm = bpy.data.objects.new('pegasus_rig', ad)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for n, (h, t, p, d) in full.items():
    b = ad.edit_bones.new(n); b.head = Vector(h); b.tail = Vector(t); b.roll = 0.0; b.use_deform = d
    eb[n] = b
for n, (h, t, p, d) in full.items():
    if p:
        eb[n].parent = eb[p]
        eb[n].use_connect = (Vector(eb[p].tail) - Vector(h)).length < 1e-6
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WK, 'stage2.blend'))
json.dump({n: {'head': list(h), 'tail': list(t), 'parent': p, 'deform': d} for n, (h, t, p, d) in full.items()},
          open(os.path.join(WK, 'bones.json'), 'w'), indent=1)
print('###BONES###', len(full))
