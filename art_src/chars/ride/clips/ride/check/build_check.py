"""Ride proof: animate a COPY of ride.blend (art_src/chars/ride/ride_check.blend) with the hercules `ride` action and a
simple per-key Pegasus wing/body pose, count rider-vs-wing intersections per key, save the copy for
render_split_sheet.py --frame N.

  Blender -b --factory-startup --python check/build_check.py -- <repo> <ride_check.blend> <check_keys.json> <out.json>

check_keys.json: {"frames": [{"frame": N, "u": wing phase 0 = top .. 1 = bottom, "dz": pegasus root bob in m}, ...]}
Wing orientation of wing_*_01 = the make_poses.py raise family between full_up (-75) / glide / full_down (+70)
(art_src/chars/ride/poses/pegasus_wing_extremes.json), raise from u, plus a fixed 10 deg forward sweep (check/wing_search.py);
legs/neck/tail stay at poses/pegasus_fly.json."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Euler, Quaternion
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
REPO, BLEND, KEYS, OUT = argv[0], argv[1], argv[2], argv[3]
sys.path.insert(0, os.path.join(REPO, 'tools/animkit'))
import ak_blender as AK  # noqa: E402
RIDE = os.path.join(REPO, 'art_src/chars/ride')
HB = os.path.join(REPO, 'art_src/chars/hercules/hercules.blend')
PB = os.path.join(REPO, 'art_src/chars/pegasus/pegasus.blend')
CLIP = os.path.join(RIDE, 'clips/ride')

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
harm, parm = bpy.data.objects['hercules_rig'], bpy.data.objects['pegasus_rig']
hrig = AK.Rig(harm, json.load(open(os.path.join(REPO, 'art_src/chars/hercules/rig.json'))), HB)
prig = AK.Rig(parm, json.load(open(os.path.join(REPO, 'art_src/chars/pegasus/rig.json'))), PB)

# --- hercules: the baked game action, exactly as the GLB export writes it
act = json.load(open(os.path.join(CLIP, 'action_ride.json')))
AK.write_action(hrig, act)

# --- pegasus: per-key pose
ck = json.load(open(KEYS))
fly = json.load(open(os.path.join(RIDE, 'poses/pegasus_fly.json')))
ext = json.load(open(os.path.join(RIDE, 'poses/pegasus_wing_extremes.json')))
u_mid = ck.get('u_mid', 0.73)
from mathutils import Matrix
def R3(ax, a):
    return Matrix.Rotation(math.radians(a), 3, ax)
G = R3('Z', 23.3) @ R3('Y', 62.3) @ R3('X', 74.5)          # glide wing_l_01 (make_poses.py)
S = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))
PITCH, YAW = ck.get('pitch', 0.0), ck.get('yaw', -10.0)     # chosen by check/wing_search.py: 0 rider hits at every key
def wing(side, u):
    """make_poses.py family: raise about the body axis (full up -75, glide 0, full down +70 with Rz(-20)),
    then the clearance offset: Rz(YAW) sweeps the left wing forward (YAW < 0), Rx(PITCH) lifts the trailing edge."""
    ra = -75.0 * (1 - u / u_mid) if u <= u_mid else 70.0 * (u - u_mid) / (1 - u_mid)
    zd = 0.0 if u <= u_mid else -20.0 * (u - u_mid) / (1 - u_mid)
    M = R3('X', PITCH) @ R3('Z', YAW + zd) @ R3('Y', ra) @ G
    if side == 'r':
        M = S @ M @ S
    e = M.to_euler('XYZ')
    return {'rx': round(math.degrees(e.x), 2), 'ry': round(math.degrees(e.y), 2), 'rz': round(math.degrees(e.z), 2)}
if parm.animation_data and parm.animation_data.action:
    parm.animation_data.action = None
for pb in parm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
z0 = parm.location.z
for k in ck['frames']:
    pose = json.loads(json.dumps(fly))
    for s in ('l', 'r'):
        pose['bones'][f'wing_{s}_01'] = wing(s, k['u'])
    k['wing_l_01'] = pose['bones']['wing_l_01']
    prig.apply(pose)
    for pb in parm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=k['frame'])
        pb.keyframe_insert('location', frame=k['frame'])
    parm.location.z = z0 + k['dz']
    parm.keyframe_insert('location', frame=k['frame'])

# --- per key: rider vs pegasus intersections (triangle overlaps) by region
def world_tris(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', tri)
    ev.to_mesh_clear()
    return w, tri.reshape(-1, 3)
sys.path.insert(0, os.path.join(RIDE, 'scripts'))
from peg_regions import pegasus_regions  # noqa: E402
pmesh = bpy.data.objects['pegasus']
preg, pdom = pegasus_regions(pmesh)
rider_objs = [bpy.data.objects[n] for n in ('hercules', 'prop_sword', 'prop_shield')]
hgn = {g.index: g.name for g in bpy.data.objects['hercules'].vertex_groups}
hdom = np.array([hgn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-'
                 for v in bpy.data.objects['hercules'].data.vertices], dtype=object)
res = []
for k in ck['frames']:
    sc.frame_set(k['frame'])
    bpy.context.view_layer.update()
    pw, pt = world_tris(pmesh)
    treg = preg[pt[:, 0]]
    row = {'frame': k['frame'], 'u': k['u'], 'dz': k['dz'], 'wing_l_01': k['wing_l_01']}
    hits = {}
    for o in rider_objs:
        w, t = world_tris(o)
        bo = BVHTree.FromPolygons([tuple(v) for v in w], [tuple(x) for x in t], all_triangles=True)
        for r in ('wing', 'skin', 'hair'):
            sel = np.nonzero(treg == r)[0]
            bp = BVHTree.FromPolygons([tuple(v) for v in pw], [tuple(x) for x in pt[sel]], all_triangles=True)
            pairs = bo.overlap(bp)
            if pairs:
                if o.name == 'hercules':
                    parts = {}
                    for a, _ in pairs:
                        b = hdom[t[a][0]]; parts[b] = parts.get(b, 0) + 1
                    hits[f'{o.name}-{r}'] = {'n': len(pairs), 'bones': dict(sorted(parts.items(), key=lambda x: -x[1])[:6])}
                else:
                    hits[f'{o.name}-{r}'] = {'n': len(pairs)}
    row['hits'] = hits
    # seat: hips joint above the saddle head (pegasus armature axes) and lowest seat skin vs the back
    hips = harm.matrix_world @ harm.pose.bones['hips'].head
    sad = parm.matrix_world @ parm.pose.bones['saddle'].head
    row['hips_minus_saddle'] = [round(x, 4) for x in (hips - sad)]
    res.append(row)
    print('KEY', json.dumps(row))
sc.frame_set(ck['frames'][0]['frame'])
bpy.ops.wm.save_as_mainfile(filepath=BLEND, relative_remap=True)
json.dump({'keys': res, 'u_mid': u_mid}, open(OUT, 'w'), indent=1)
print('###CHECK### ok', OUT)
