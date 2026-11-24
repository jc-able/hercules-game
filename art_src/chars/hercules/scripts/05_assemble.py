"""Step 5: work/hercules_03b_fix.blend + props -> hercules.blend + rig.json
Props are linked from art_src/props/<name>.blend (copied in), bone-parented: sword -> hand_r, shield -> forearm_l.
socket_offsets = prop / socket transform in the BONE's rest frame (Blender bone local: +Y along the bone, same frame
the glTF joint node has), loc in metres, rot_deg = XYZ euler degrees.
"""
import bpy, os, json, math
import numpy as np, sys
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skirt_drivers

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_03b_fix.blend'))
sc = bpy.context.scene
arm = bpy.data.objects['hercules_rig']; ob = bpy.data.objects['hercules']; me = ob.data
for an in ('cls', 'comp'):
    if an in me.attributes:
        me.attributes.remove(me.attributes[an])
co = np.array([v.co[:] for v in me.vertices])
gi = {g.name: g.index for g in ob.vertex_groups}
def gverts(name, thr=0.5):
    i = gi[name]
    return np.array([v.index for v in me.vertices for g in v.groups if g.group == i and g.weight > thr])
B = arm.data.bones

def look(z_axis_dir, y_axis_dir):
    """rotation matrix whose local +Z points along z_axis_dir and +Y as close as possible to y_axis_dir"""
    zz = Vector(z_axis_dir).normalized()
    yy = (Vector(y_axis_dir) - Vector(y_axis_dir).dot(zz) * zz).normalized()
    xx = yy.cross(zz)
    return Matrix((xx, yy, zz)).transposed().to_4x4()

placed = {}
# --- sword in the right hand: grip at the palm centre, blade forward (-Y) pitched SWORD_DOWN deg down and turned
#     SWORD_OUT deg out (to the character's right, -X), flat of the blade toward the front camera, so the sword reads
#     in BOTH panels of the split sheet (straight forward it showed only a sliver of the grip in the front view).
#     The same transform is written to socket_offsets, so game and sheet agree.
SWORD_DOWN, SWORD_OUT = 35.0, 25.0
hb = B['hand_r']; h0, h1 = Vector(hb.head_local), Vector(hb.tail_local); d = (h1 - h0).normalized()
hv = co[gverts('hand_r')]
proj = (hv - np.array(h0)) @ np.array(d); L = (h1 - h0).length
palm = hv[(proj > 0.2 * L) & (proj < 0.6 * L)].mean(0)
cd_, sd_ = math.cos(math.radians(SWORD_DOWN)), math.sin(math.radians(SWORD_DOWN))
blade = Vector((-cd_ * math.sin(math.radians(SWORD_OUT)), -cd_ * math.cos(math.radians(SWORD_OUT)), -sd_)).normalized()
edge = blade.cross(Vector((0, 1, 0))).normalized()          # edges perpendicular to the view axis -> flat faces front
if edge.z < 0:
    edge = -edge
Msword = Matrix.Translation(Vector(palm)) @ look(blade, edge)
placed['sword'] = ('hand_r', Msword)

# --- shield on the left forearm: back centre on the outer side of the forearm, face outward, top toward the elbow
fb = B['forearm_l']; f0, f1 = Vector(fb.head_local), Vector(fb.tail_local); fd = (f1 - f0).normalized()
mid = f0 + (f1 - f0) * 0.55
fv = co[gverts('forearm_l')]
fp = (fv - np.array(f0)) @ np.array(fd)
ring = fv[np.abs(fp - 0.55 * (f1 - f0).length) < 0.02]
axis_pt = Vector(ring.mean(0))
out = Vector((1, 0, 0)); out = (out - out.dot(fd) * fd).normalized()
radius = float(np.max((ring - np.array(axis_pt)) @ np.array(out)))
strap = axis_pt + out * (radius + 0.005)
# shield local -Y = face normal (outward); local +Z (top of the lion) = thumb side (forward at rest), perpendicular to
# the forearm: hoplite grip, so the emblem stands upright when the forearm lies across the chest with the thumb up
yl = -out
zt = Vector((0, -1, 0)); zt = (zt - zt.dot(fd) * fd); zt = (zt - zt.dot(yl) * yl).normalized()
xl = yl.cross(zt).normalized()
Mshield = Matrix.Translation(strap) @ Matrix((xl, yl, zt)).transposed().to_4x4()
placed['shield'] = ('forearm_l', Mshield)

for name, (bone, M) in placed.items():
    with bpy.data.libraries.load(os.path.join(REPO, 'art_src', 'props', f'{name}.blend'), link=False) as (src, dst):
        dst.objects = [f'prop_{name}']
    po = dst.objects[0]; sc.collection.objects.link(po)
    po.parent = arm; po.parent_type = 'BONE'; po.parent_bone = bone
    bpy.context.view_layer.update()
    po.matrix_world = M
    bpy.context.view_layer.update()

offsets = {}
def bone_off(bone, M):
    off = B[bone].matrix_local.inverted() @ M
    return {'loc': [round(v, 4) for v in off.to_translation()],
            'rot_deg': [round(math.degrees(v), 2) for v in off.to_euler('XYZ')]}
offsets['hand_r'] = bone_off('hand_r', Msword)
offsets['forearm_l'] = bone_off('forearm_l', Mshield)
# head: centre of the head volume; chest: front surface of the chest at spine_02 height
hv = co[gverts('head')]
hc = Vector(((hv[:, 0].min() + hv[:, 0].max()) / 2, (hv[:, 1].min() + hv[:, 1].max()) / 2, (hv[:, 2].min() + hv[:, 2].max()) / 2))
offsets['head'] = bone_off('head', Matrix.Translation(hc))
cz = (B['spine_02'].head_local.z + B['spine_03'].head_local.z) / 2
m = (np.abs(co[:, 0]) < 0.03) & (np.abs(co[:, 2] - cz) < 0.02)
chest = Vector((0.0, float(co[m, 1].min()), cz))
offsets['chest'] = bone_off('spine_02', Matrix.Translation(chest))

def r(v): return [round(x, 4) for x in v]
bones = [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'head': r(b.head_local), 'tail': r(b.tail_local),
          'deform': b.use_deform} for b in B]
rig = {
    'id': 'hercules', 'height': round(float(co[:, 2].max() - co[:, 2].min()), 4),
    'bones': bones,
    'chains': {'spine': ['hips', 'spine_01', 'spine_02', 'spine_03', 'neck', 'head'],
               **{f'arm_{s}': [f'shoulder_{s}', f'upper_arm_{s}', f'forearm_{s}', f'hand_{s}'] for s in 'lr'},
               **{f'leg_{s}': [f'thigh_{s}', f'shin_{s}', f'foot_{s}', f'toe_{s}'] for s in 'lr'}},
    'sockets': {'hand_r': 'hand_r', 'forearm_l': 'forearm_l', 'head': 'head', 'chest': 'spine_02'},
    'socket_offsets': offsets,
    'socket_props': {'hand_r': 'res://assets/props/sword.glb', 'forearm_l': 'res://assets/props/shield.glb'},
    'socket_rest_world_blender': {k: r((B[rig_b].matrix_local @ Matrix.Translation(Vector(offsets[k]['loc']))).to_translation())
                                  for k, rig_b in (('hand_r', 'hand_r'), ('forearm_l', 'forearm_l'), ('head', 'head'), ('chest', 'spine_02'))},
    'pairs': [[f'{b}_l', f'{b}_r'] for b in ('shoulder', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot', 'toe', 'skirt', 'fingers')],
    'driven': {'bones': list(skirt_drivers.SKIRT_BONES), 'by': ['thigh_l', 'thigh_r'], 'spec': skirt_drivers.SPEC,
               'code': 'art_src/chars/hercules/scripts/skirt_drivers.py (skirt_matrices(rest, posed))',
               'note': 'Do not key the skirt bones by hand: set them from the thighs on every pose/frame before baking.'},
    'notes': ('Coordinates: Blender, Z up, metres, character faces -Y, its left = +X; armature and mesh at identity, so bone '
              'head/tail are world positions. glTF export (+Y up) keeps each joint in the Blender bone frame (+Y along the bone), '
              'so a Godot BoneAttachment3D on the socket bone + socket_offsets (loc, XYZ euler rot_deg, in that bone frame) '
              'reproduces the placement in hercules.blend. Skeleton = Higgsfield/Meshy auto-rig renamed (Hips->hips, '
              'Spine02->spine_01, Spine01->spine_02, Spine->spine_03, neck, Head->head, Left*/Right* -> *_l/*_r); Meshy helper '
              'bone headfront merged into head, head_end dropped, root added (non-deforming, at the origin). '
              'Review fixes 2026-11-22: (1) SKIRT: four deform bones skirt_f/b/l/r (children of hips, belt z 1.12 -> hem z 0.70) '
              'own the red cloth below the belt (hips at the belt blending to the skirt bones by the hem, by geodesic distance); '
              'no thigh weight on the skirt, tunic or belt. The generated mesh glued the hem underside to both thighs with 496 '
              'faces; they were deleted (19 verts) so the skirt hangs free; the thigh tops are open inside the skirt and the '
              'material is double-sided. The skirt bones are DRIVEN, never keyed: see "driven" and skirt_drivers.py. Without the '
              'driver the skirt stays rigid with the hips and the thighs pass through it. (2) Feet: both ankles at '
              '(+-0.205, 0.070, 0.140), ball joints at (+-0.237, -0.085, 0.045); left foot/toe/lower-shin weights mirrored from the '
              'right; mirror test foot 30 deg p95 7.5 mm. (3) Skin under the skirt: no opposite-leg weight beyond a 1.2 cm centre '
              'seam; crotch seam 45/45 thighs + 10% hips. (4) Neck: right back mirrored from the left, shoulder weight ramps out '
              'above z 1.55-1.59, near-coincident vertex pairs share weights. (5) spine_03 now carries up to 45% of the upper chest '
              '(z 1.40-1.55): keying it is safe. (6) Sword at rest pitched 35 deg down and 25 deg out, flat toward the front camera, '
              'so it reads in both sheet panels; socket_offsets.hand_r matches. (7) fingers_l / fingers_r: one curl bone per hand '
              '(knuckles -> tips; rotate about its own X, about 60-80 deg, to close the hand on the sword grip in clips). Props: sword.glb origin = grip centre, blade +Y (Godot); shield.glb origin = centre of the back, '
              'face +Z (Godot); on the left forearm the face points outward and the emblem top points to the thumb side.'),
}
json.dump(rig, open(os.path.join(HERE, 'rig.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'hercules.blend'))
print('###ASSEMBLE', json.dumps({'offsets': offsets, 'palm': r(palm), 'strap': r(strap), 'forearm_radius': round(radius, 4),
      'objects': [o.name for o in sc.objects]}))
