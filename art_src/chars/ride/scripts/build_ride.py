"""Build art_src/chars/ride/ride.blend: Hercules (mesh + armature + sword + shield) seated on Pegasus's 'saddle' bone.

  Blender -b --factory-startup --python build_ride.py -- <repo> <seat.json> [--no-save]

seat.json: {"hercules_pose": "poses/hercules_ride_in.json", "pegasus_pose": "poses/pegasus_fly.json",
            "seat": {"y": <m, + = back>, "z": <m> | "auto", "pitch": <deg, + = lean forward>, "auto_depth": 0.015}}
  seat y/z = where the Hercules HIPS joint goes, relative to the saddle bone head, in Pegasus armature axes.
  "z": "auto" lowers him until his seat (crotch/buttocks skin) sinks auto_depth metres into the back.

Both characters are appended from their own blends (read-only, never modified) at real scale. Poses are applied with
animkit's own pose solver (tools/animkit/ak_blender.Rig, so the JSON is exactly ak format) while each armature is still
at the origin; Hercules's skirt bones are set by rig.json "driven" (skirt_drivers.skirt_matrices) inside Rig.solve.
Then hercules_rig is parented to pegasus_rig bone 'saddle' with the parent space moved to the bone HEAD, so the
object transform of hercules_rig IS the rider offset in the saddle bone frame.
Writes ride.blend, ride.json (rider offset + both poses), work/ride/metrics.json (interpenetration + envelope).
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
REPO = os.path.abspath(argv[0])
SEAT = json.load(open(argv[1]))
SAVE = '--no-save' not in argv
RIDE = os.path.join(REPO, 'art_src/chars/ride')
HB = os.path.join(REPO, 'art_src/chars/hercules/hercules.blend')
PB = os.path.join(REPO, 'art_src/chars/pegasus/pegasus.blend')
sys.path.insert(0, os.path.join(REPO, 'tools/animkit'))
import ak_blender as AK  # noqa: E402

rel = lambda p: p if os.path.isabs(p) else os.path.join(RIDE, p)
HPOSE_IN = json.load(open(rel(SEAT['hercules_pose'])))
PPOSE = json.load(open(rel(SEAT['pegasus_pose'])))
seat = SEAT['seat']

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def append(path, names):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        missing = [n for n in names if n not in src.objects]
        if missing:
            raise RuntimeError(f'{path}: no objects {missing}')
        dst.objects = list(names)
    objs = {}
    for o in dst.objects:
        scene.collection.objects.link(o)
        objs[o.name] = o
    # images: resolve relative to the SOURCE blend, keep absolute for now (re-pathed relative to ride.blend at save)
    return objs


img_src = {}
before = set(bpy.data.images)
H = append(HB, ['hercules', 'hercules_rig', 'prop_sword', 'prop_shield'])
for im in set(bpy.data.images) - before:
    img_src[im.name] = HB
before = set(bpy.data.images)
P = append(PB, ['pegasus', 'pegasus_rig'])
for im in set(bpy.data.images) - before:
    img_src[im.name] = PB
img_abs = {}
for im in bpy.data.images:
    fp = im.filepath
    if fp.startswith('//'):
        p = os.path.normpath(os.path.join(os.path.dirname(img_src.get(im.name, HB)), fp[2:]))
    else:
        p = os.path.normpath(bpy.path.abspath(fp))
    if not os.path.exists(p):
        raise RuntimeError(f'image {im.name}: {fp} -> {p} not found')
    img_abs[im.name] = p
    im.filepath = p
harm, parm = H['hercules_rig'], P['pegasus_rig']
hmesh, pmesh = H['hercules'], P['pegasus']
for a in (harm, parm):
    assert a.matrix_world == Matrix.Identity(4), a.name
    AK.clear_anim(a)
    a.data.pose_position = 'POSE'
bpy.context.view_layer.update()

hrj = json.load(open(os.path.join(os.path.dirname(HB), 'rig.json')))
prj = json.load(open(os.path.join(os.path.dirname(PB), 'rig.json')))
hrig = AK.Rig(harm, hrj, HB)            # loads the skirt driver from rig.json "driven"
prig = AK.Rig(parm, prj, PB)
assert hrig.driven, 'hercules skirt driver not loaded'


# ---------------------------------------------------------------- poses (ak format)
def resolve_dirs(pose_in):
    """"dir": [x, y, z] (bone direction in the character's view axes, faces -Y) -> ak aim front/side.
    front = atan2(-x, -z), side = atan2(y, -z) (docs/ANIM_PIPELINE.md aim form; for an up-pointing bone both panel
    angles pass 90 and ak's aim_direction flips the result back up); "twist" is kept. |z| must not be ~0."""
    pose = json.loads(json.dumps(pose_in))
    for bn, v in (pose.get('bones') or {}).items():
        if 'dir' in v:
            x, y, z = v.pop('dir')
            if abs(z) < 0.03 * math.sqrt(x * x + y * y + z * z):
                raise ValueError(f'{bn}: dir is horizontal (|z| ~ 0): front/side aim is degenerate, tilt it a little')
            v['front'] = round(math.degrees(math.atan2(-x, -z)), 2)
            v['side'] = round(math.degrees(math.atan2(y, -z)), 2)
    return pose


def resolve_grip(rig, pose_in):
    """'grip': {finger_bone: deg} = curl about the bone's own X (+X closes the hand, docs/notes/rig_hercules.md).
    ak has no own-axis key, so convert it to the equivalent local_delta rx/ry/rz (view axes) for THIS pose."""
    pose = json.loads(json.dumps(pose_in))
    grip = pose.pop('grip', None) or {}
    if grip:
        Pm = rig.solve(pose)
        for bn, deg in grip.items():
            p = rig.parent[bn]
            follow3 = (Pm[p] @ (rig.rest[p].inverted() @ rig.rest[bn])).to_3x3().normalized()
            Rd = follow3 @ Matrix.Rotation(math.radians(deg), 3, 'X') @ follow3.transposed()
            e = (rig.Ra @ Rd @ rig.RaT).to_euler('XYZ')   # rot_xyz = Rz @ Ry @ Rx = Blender Euler XYZ
            pose['bones'][bn] = {'rx': round(math.degrees(e.x), 2), 'ry': round(math.degrees(e.y), 2),
                                 'rz': round(math.degrees(e.z), 2), 'space': 'local_delta'}
    return pose


HPOSE = resolve_grip(hrig, resolve_dirs(HPOSE_IN))
hrig.apply(HPOSE)
prig.apply(PPOSE)
# skirt check: the driven bones must follow the thighs (Rig.solve calls skirt_matrices)
sys.path.insert(0, os.path.join(REPO, 'art_src/chars/hercules/scripts'))
import skirt_drivers  # noqa: E402
rest = {b.name: b.matrix_local.copy() for b in harm.data.bones}
posed = {pb.name: pb.matrix.copy() for pb in harm.pose.bones}
sk = skirt_drivers.skirt_angles(rest, posed)
want = skirt_drivers.skirt_matrices(rest, posed)
skirt_err = max(max(abs(a - b) for ra, rb in zip(want[n], posed[n]) for a, b in zip(ra, rb)) for n in want)
skirt_info = {k: [round(x, 1) for x in v[1:]] for k, v in sk.items() if k.startswith('skirt')}
skirt_info['thighs_pitch_abd'] = {s: [round(x, 1) for x in v] for s, v in sk['_thighs'].items()}

# ---------------------------------------------------------------- seat: parent to the saddle bone head
sb = parm.data.bones['saddle']
spb = parm.pose.bones['saddle']
harm.parent = parm
harm.parent_type = 'BONE'
harm.parent_bone = 'saddle'
harm.matrix_parent_inverse = Matrix.Translation((0, -sb.length, 0))   # parent space = saddle HEAD frame
harm.rotation_mode = 'XYZ'
bpy.context.view_layer.update()
S_world = parm.matrix_world @ spb.matrix                  # posed saddle head frame (world)
S_rest_rot = sb.matrix_local.to_3x3()                     # saddle bone axes in pegasus armature space (rest)
hips_rest = harm.data.bones['hips'].head_local.copy()     # hips joint in hercules armature space (rest)
hips_posed = harm.pose.bones['hips'].head.copy()          # == rest unless root.loc is used


def rider_matrix(y, z, pitch):
    """armature-axes offset A (saddle head origin, pegasus armature axes) -> world matrix of hercules_rig"""
    R = Matrix.Rotation(math.radians(-pitch), 4, 'X')      # + pitch = lean forward (char faces -Y): about -X
    # hips joint goes to (0, y, z) in the saddle head frame (armature axes); pitch turns him about the hips joint
    A = Matrix.Translation((0, y, z)) @ R @ Matrix.Translation(-hips_posed)
    return S_world @ S_rest_rot.inverted().to_4x4() @ A, A


def eval_world(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', tri)
    ev.to_mesh_clear()
    return w, tri.reshape(-1, 3)


def dominant(obj):
    gn = {g.index: g.name for g in obj.vertex_groups}
    d = []
    for v in obj.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        d.append(gn[best.group] if best else '-')
    return np.array(d, dtype=object)


hdom = dominant(hmesh)
pdom = dominant(pmesh)
hrest = np.array([v.co for v in hmesh.data.vertices])


def hreg(b):
    for k in ('thigh', 'shin', 'foot', 'toe', 'skirt', 'hand', 'fingers', 'forearm', 'upper_arm'):
        if b.startswith(k):
            return k + ('_' + b[-1] if b[-2:] in ('_l', '_r') else '')
    return b


pw, ptri = eval_world(pmesh)
sys.path.insert(0, os.path.join(RIDE, 'scripts'))
from peg_regions import pegasus_regions  # noqa: E402
_r, _ = pegasus_regions(pmesh)            # skin | hair (blue mane/tail texels, soft) | wing (wing bones)
preg_v = np.where(_r == 'wing', np.where(np.char.startswith(pdom.astype(str), 'wing_l'), 'wing_l', 'wing_r'), _r)
REGS = ('skin', 'hair', 'wing_l', 'wing_r')
# a triangle's region = its first vertex's region
ptri_reg = preg_v[ptri[:, 0]]
bvh_p = {r: BVHTree.FromPolygons([tuple(v) for v in pw], [tuple(t) for t in ptri[ptri_reg == r]], all_triangles=True)
         for r in REGS}
# seat skin: crotch / buttocks (rest z 0.86-1.06 inside the hips width), skirt cloth excluded
seat_sel = ((hrest[:, 2] > 0.86) & (hrest[:, 2] < 1.06) & (np.abs(hrest[:, 0]) < 0.13)
            & ~np.char.startswith(hdom.astype(str), 'skirt'))

# evaluate hercules once at the origin-equivalent seat (z = 0 offset) and translate in numpy for the auto seat
harm.matrix_world = rider_matrix(seat['y'], 0.0, seat.get('pitch', 0.0))[0]
bpy.context.view_layer.update()
hw0, _ = eval_world(hmesh)
up = np.array(S_world.to_3x3() @ S_rest_rot.inverted() @ Vector((0, 0, 1)))


def seat_depth(wco, sel):
    """seat skin vs the bare back as a height field: a ray straight down from 2.3 m onto pegasus skin faces.
    > 0 = the vertex is below the back surface (sunk in). The back behind the wing roots is a clean single surface."""
    d = np.full(len(wco), -1.0)
    dn = Vector((0, 0, -1))
    for i in np.where(sel)[0]:
        x, y, z = wco[i]
        hit = bvh_p['skin'].ray_cast(Vector((x, y, 2.3)), dn, 1.5)
        if hit[0] is not None:
            d[i] = hit[0].z - z
    return d


if seat['z'] == 'auto':
    target = float(seat.get('auto_depth', 0.015))
    lo, hi = -0.4, 0.6                            # z of the hips joint above the saddle head
    for _ in range(22):
        mid = (lo + hi) / 2
        dmax = seat_depth(hw0 + up * mid, seat_sel).max()
        if dmax > target:
            lo = mid
        else:
            hi = mid
    seat_z = round(hi, 4)
else:
    seat_z = float(seat['z'])
Wh, A = rider_matrix(seat['y'], seat_z, seat.get('pitch', 0.0))
harm.matrix_world = Wh
bpy.context.view_layer.update()
offset_bone = harm.matrix_basis.copy()          # = rider offset in the saddle bone frame (parent space = bone head)
chk = parm.matrix_world @ spb.matrix @ offset_bone
assert max(abs(a - b) for ra, rb in zip(chk, harm.matrix_world) for a, b in zip(ra, rb)) < 1e-5

# ---------------------------------------------------------------- interpenetration metrics
hw, htri = eval_world(hmesh)
hreg_v = np.array([hreg(b) for b in hdom])
metrics = {'seat_z': seat_z, 'skirt_driver_max_err': round(float(skirt_err), 6), 'skirt': skirt_info}
hbvh = BVHTree.FromPolygons([tuple(v) for v in hw], [tuple(t) for t in htri], all_triangles=True)
ov = {}
for r in REGS:
    pairs = hbvh.overlap(bvh_p[r])
    by = {}
    for ih, _ in pairs:
        k = hreg_v[htri[ih][0]]
        by[k] = by.get(k, 0) + 1
    ov[r] = dict(sorted(by.items(), key=lambda x: -x[1]))
    if pairs:                                    # where (pegasus side): centroid bbox of the touched pegasus triangles
        cc = np.array([pw[ptri[ptri_reg == r][ip]].mean(0) for _, ip in pairs])
        ov[r]['_where_min'] = [round(float(v), 2) for v in cc.min(0)]; ov[r]['_where_max'] = [round(float(v), 2) for v in cc.max(0)]
        if r.startswith('wing'):                 # same triangles at REST (feather or flank band?) + dominant bones
            pr = np.array([v.co for v in pmesh.data.vertices])
            vi = np.unique(np.concatenate([ptri[ptri_reg == r][ip] for _, ip in pairs]))
            ov[r]['_rest_min'] = [round(float(v), 2) for v in pr[vi].min(0)]; ov[r]['_rest_max'] = [round(float(v), 2) for v in pr[vi].max(0)]
            u, c = np.unique(pdom[vi].astype(str), return_counts=True)
            ov[r]['_bones'] = dict(zip(u.tolist(), c.tolist()))
for pn in ('prop_sword', 'prop_shield'):
    w, t = eval_world(H[pn])
    b = BVHTree.FromPolygons([tuple(v) for v in w], [tuple(x) for x in t], all_triangles=True)
    for r in REGS:
        n = len(b.overlap(bvh_p[r]))
        if n:
            ov[r][pn] = n
metrics['tri_overlaps'] = ov
# left hand on the mane: closest distance from the hand/finger skin to the blue mane hair (negative = inside it)
_hs = np.where(np.isin(hreg_v, ['hand_l', 'fingers_l']))[0]
_dm = min(bvh_p['hair'].find_nearest(Vector(hw[i]), 1.0)[3] or 9.0 for i in _hs)
metrics['hand_l_to_mane_cm'] = round(float(_dm) * 100, 1)
metrics['hand_l_in_mane_tris'] = sum(v for k, v in ov['hair'].items() if k in ('hand_l', 'fingers_l'))


def prop_axes(o, axis):
    co = np.array([v.co for v in o.data.vertices])
    M = o.matrix_world
    k = {'Z': 2, '-Y': 1}[axis]
    if axis == 'Z':
        tip = M @ Vector(co[co[:, 2].argmax()])
        return {'grip': [round(v, 3) for v in M.translation], 'tip': [round(v, 3) for v in tip]}
    n = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
    c = M @ Vector(co.mean(0))
    return {'centre': [round(v, 3) for v in c], 'face_normal': [round(v, 3) for v in n]}


metrics['props'] = {'sword': prop_axes(H['prop_sword'], 'Z'), 'shield': prop_axes(H['prop_shield'], '-Y')}
metrics['joints'] = {n: [round(v, 3) for v in harm.matrix_world @ harm.pose.bones[n].head]
                     for n in ('hips', 'thigh_l', 'shin_l', 'foot_l', 'thigh_r', 'shin_r', 'foot_r', 'upper_arm_l', 'forearm_l',
                               'hand_l', 'upper_arm_r', 'forearm_r', 'hand_r', 'head')}


def side_depth(wco, sel):
    """legs vs the flanks: a ray from 1.5 m out on the vertex's own side straight in (x) onto pegasus skin faces.
    > 0 = the vertex is inside the flank surface (thigh/shin sunk into the horse). Combined with seat_depth (min of the
    two) so inner thighs hovering above the rounded back near the spine do not count."""
    d = np.full(len(wco), -1.0)
    for i in np.where(sel)[0]:
        x, y, z = wco[i]
        sg = 1.0 if x >= 0 else -1.0
        hit = bvh_p['skin'].ray_cast(Vector((1.5 * sg, y, z)), Vector((-sg, 0, 0)), 1.5)
        if hit[0] is not None:
            d[i] = sg * (hit[0].x - x)
    return d


leg_sel = np.array([r.split('_')[0] in ('thigh', 'shin', 'foot', 'toe') for r in hreg_v])
sd = np.minimum(side_depth(hw, leg_sel), seat_depth(hw, leg_sel))   # inside = below the back AND inside the flank
metrics['legs_into_flank'] = {}
for hr in sorted(set(hreg_v[leg_sel])):
    m_ = (hreg_v == hr)
    dd = sd[m_]
    metrics['legs_into_flank'][hr] = {'n_verts': int(m_.sum()), 'n_gt_1cm': int((dd > 0.01).sum()), 'n_gt_3cm': int((dd > 0.03).sum()),
                                      'n_gt_5cm': int((dd > 0.05).sum()), 'max_cm': round(float(dd.max()) * 100, 1)}
    deep = m_ & (sd > 0.03)
    if deep.any():   # where on HIS body (rest coords) and where in the world
        metrics['legs_into_flank'][hr]['gt3_rest_bbox'] = [[round(float(v), 2) for v in hrest[deep].min(0)], [round(float(v), 2) for v in hrest[deep].max(0)]]
        metrics['legs_into_flank'][hr]['gt3_world_bbox'] = [[round(float(v), 2) for v in hw[deep].min(0)], [round(float(v), 2) for v in hw[deep].max(0)]]
# seat skin depth (should be ~auto_depth)
metrics['seat_skin_max_depth_cm'] = round(float(seat_depth(hw, seat_sel).max()) * 100, 2)


# ---------------------------------------------------------------- envelope of a full wing beat (pair bbox per wing pose)
def scene_bbox():
    mn = np.full(3, 1e9); mx = np.full(3, -1e9)
    for o in (hmesh, pmesh, H['prop_sword'], H['prop_shield']):
        w, _ = eval_world(o)
        mn = np.minimum(mn, w.min(0)); mx = np.maximum(mx, w.max(0))
    return mn, mx


env = {}
mn, mx = scene_bbox()
env['ride_pose'] = {'min': [round(v, 3) for v in mn], 'max': [round(v, 3) for v in mx]}
ext = json.load(open(os.path.join(RIDE, 'poses/pegasus_wing_extremes.json')))
for name, wings in ext.items():
    p2 = json.loads(json.dumps(PPOSE)); p2['bones'].update(wings)
    prig.apply(p2)
    a, b = scene_bbox()
    env[name] = {'min': [round(v, 3) for v in a], 'max': [round(v, 3) for v in b]}
prig.apply(PPOSE)
bpy.context.view_layer.update()
allmn = np.min([v['min'] for v in env.values()], axis=0); allmx = np.max([v['max'] for v in env.values()], axis=0)
env['union'] = {'min': [round(v, 3) for v in allmn], 'max': [round(v, 3) for v in allmx]}
metrics['envelope'] = env

# ---------------------------------------------------------------- outputs
q = offset_bone.to_quaternion()
e_bone = offset_bone.to_euler('XYZ')
e_arm = A.to_euler('XYZ')
ride = {
    'rider_offset': {
        'loc': [round(v, 4) for v in offset_bone.to_translation()],
        'rot_deg': [round(math.degrees(v), 3) for v in e_bone],
        'frame': "pegasus 'saddle' bone frame with the origin at the bone HEAD (Blender bone axes: +Y along the bone = "
                 "world up at rest; glTF/Godot keep this joint frame). Euler XYZ degrees. Transform of the hercules ROOT "
                 "(armature origin = between his feet): rider_world = saddle_bone_global @ T(loc) @ R(rot).",
        'quat_wxyz': [round(v, 6) for v in q],
        'matrix': [[round(v, 6) for v in row] for row in offset_bone],
    },
    'rider_offset_armature_axes': {
        'loc': [round(v, 4) for v in A.to_translation()], 'rot_deg': [round(math.degrees(v), 3) for v in e_arm],
        'frame': 'same transform, origin at the saddle bone head but in PEGASUS ARMATURE axes (Z up, faces -Y), '
                 'like pegasus rig.json socket_offsets. With pegasus at rest the rider root sits at saddle_head + loc.',
    },
    'seat': {'hips_joint_rel_saddle_head_armature_axes': [0.0, seat['y'], seat_z], 'pitch_deg': seat.get('pitch', 0.0),
             'seat_skin_depth_cm': metrics['seat_skin_max_depth_cm']},
    'hercules_pose': HPOSE,
    'pegasus_pose': PPOSE,
    'notes': None,   # filled below
}
ride['notes'] = [
    'Poses are ak (animkit) format: apply with tools/ak on each character\'s own blend (absolute view axes, each armature '
    'at the origin). hercules_pose is applied in HIS armature frame; the rider offset then carries the whole body onto the '
    'saddle, so his view axes follow pegasus\'s back (both face -Y when pegasus is level).',
    'Hercules skirt bones are driven (rig.json "driven", skirt_drivers.skirt_matrices): never key them; ak and the GLB '
    'export set them from the thighs.',
    'fingers_l / fingers_r: curl of %s deg about the finger bone\'s own X (grip), stored as the equivalent ak local_delta '
    'for THIS hand pose; if the hand pose changes, re-derive it (build_ride.py resolve_grip).' % HPOSE_IN.get('grip'),
    'The pegasus pose is the first frame of the ride video only (wings half raised); the game uses pegasus fly/glide clips '
    'and the hercules ride clip; rider_offset stays valid as long as the saddle bone is used (it rides spine_02).',
    'Rebuild: python3 art_src/chars/ride/scripts/make_poses.py art_src/chars/ride/poses; Blender -b --factory-startup '
    '--python art_src/chars/ride/scripts/build_ride.py -- <repo> art_src/chars/ride/seat.json',
]
metrics['rider_offset'] = ride['rider_offset']
os.makedirs(os.path.join(REPO, 'work/ride'), exist_ok=True)
json.dump(metrics, open(os.path.join(REPO, 'work/ride/metrics.json'), 'w'), indent=1)

if SAVE:
    out = os.path.join(RIDE, 'ride.blend')
    for o in scene.objects:
        o.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False, compress=True)
    for im in bpy.data.images:                      # relative to ride.blend (works wherever the repo lives)
        im.filepath = '//' + os.path.relpath(img_abs[im.name], RIDE)
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False, compress=True)
    b1 = out + '1'
    if os.path.exists(b1):
        os.remove(b1)
    json.dump(ride, open(os.path.join(RIDE, 'ride.json'), 'w'), indent=1)
    json.dump(HPOSE, open(os.path.join(RIDE, 'poses/hercules_ride.json'), 'w'), indent=1)   # resolved, pure ak format
print('###RIDE### ' + json.dumps({k: metrics[k] for k in ('seat_z', 'seat_skin_max_depth_cm', 'skirt_driver_max_err', 'legs_into_flank', 'tri_overlaps', 'hand_l_to_mane_cm', 'hand_l_in_mane_tris', 'props', 'joints')}))
print('###ENV### ' + json.dumps(env['union']))
