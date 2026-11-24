"""Search the left (shield) arm: hand on the mane, shield clear of pegasus and of Hercules himself.

  Blender -b --factory-startup --python sweep_shield_arm.py -- <repo> <ride.blend> <wrist x,y,z> <grip x,y,z> [out.json]

Opens the built ride.blend (pegasus posed, hercules seated: his armature axes = world axes when pegasus is level).
Two-bone IK from the posed shoulder to the wrist target (rest bone lengths), elbow swivel phi around the
shoulder-wrist axis (0 = elbow straight down, + = elbow out to his left/up), forearm twist tau (ak aim twist).
For every (phi, tau): shield triangle overlaps with pegasus (body, mane, wings) and with his own body (left arm
excluded). Prints the clear candidates (fewest overlaps), best first, with the ak aim entries for the three bones.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
REPO, BLEND = argv[0], argv[1]
WRIST = Vector([float(v) for v in argv[2].split(',')])
GRIP = Vector([float(v) for v in argv[3].split(',')])
OUT = argv[4] if len(argv) > 4 else None
sys.path.insert(0, os.path.join(REPO, 'tools/animkit'))
import ak_blender as AK  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=BLEND)
harm = bpy.data.objects['hercules_rig']; hmesh = bpy.data.objects['hercules']
pmesh = bpy.data.objects['pegasus']; shield = bpy.data.objects['prop_shield']
ride = json.load(open(os.path.join(os.path.dirname(BLEND), 'ride.json')))
HB = os.path.join(REPO, 'art_src/chars/hercules/hercules.blend')
hrj = json.load(open(os.path.join(REPO, 'art_src/chars/hercules/rig.json')))
rig = AK.Rig(harm, hrj, HB)
base = ride['hercules_pose']
Mw = harm.matrix_world.copy(); Mwi = Mw.inverted()


def tri_bvh(obj, keep=None):
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh()
    M = ev.matrix_world
    co = [M @ v.co for v in me.vertices]
    me.calc_loop_triangles()
    tris = [tuple(t.vertices) for t in me.loop_triangles if keep is None or keep[t.vertices[0]]]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(co, tris, all_triangles=True)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peg_regions import pegasus_regions  # noqa: E402
reg, _ = pegasus_regions(pmesh)
PB = {r: tri_bvh(pmesh, reg == r) for r in ('skin', 'hair', 'wing')}
gh = {g.index: g.name for g in hmesh.vertex_groups}
hd = [gh[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in hmesh.data.vertices]
self_keep = np.array([not (b.endswith('_l') and b.split('_')[0] in ('upper', 'forearm', 'hand', 'fingers', 'shoulder')) for b in hd])
HBVH = tri_bvh(hmesh, self_keep)
hand_idx = [i for i, b in enumerate(hd) if b in ('hand_l', 'fingers_l')]
sco = [v.co.copy() for v in shield.data.vertices]
shield.data.calc_loop_triangles()
stri = [tuple(t.vertices) for t in shield.data.loop_triangles]
smid = Vector(np.mean([tuple(v) for v in sco], axis=0))

# posed shoulder (world) with the base pose
rig.apply(base)
S = Mw @ harm.pose.bones['upper_arm_l'].head
L1 = (harm.data.bones['forearm_l'].head_local - harm.data.bones['upper_arm_l'].head_local).length
L2 = (harm.data.bones['hand_l'].head_local - harm.data.bones['forearm_l'].head_local).length
D = (WRIST - S).length
print('shoulder', [round(v, 3) for v in S], 'L1', round(L1, 3), 'L2', round(L2, 3), 'D', round(D, 3))
if D >= L1 + L2 - 1e-3:
    raise SystemExit(f'wrist target out of reach: D {D:.3f} >= {L1 + L2:.3f}')
u = (WRIST - S).normalized()
a = (L1 * L1 - L2 * L2 + D * D) / (2 * D); r = math.sqrt(max(0.0, L1 * L1 - a * a))
down = Vector((0, 0, -1)); e1 = (down - u * down.dot(u)).normalized()
e2 = u.cross(e1).normalized()
if e2.x < 0:
    e2 = -e2                                   # + phi swings the elbow out to his left (+X)


def to_dir_entry(v, twist=None):
    x, y, z = v.normalized()
    e = {'front': round(math.degrees(math.atan2(-x, -z)), 2), 'side': round(math.degrees(math.atan2(y, -z)), 2)}
    if twist is not None:
        e['twist'] = twist
    return e


res = []
PHI = [int(v) for v in os.environ.get("SWEEP_PHI", "-180,180,15").split(",")]
for phi in range(*PHI):
    E = S + u * a + (e1 * math.cos(math.radians(phi)) + e2 * math.sin(math.radians(phi))) * r
    ua, fa, ha = (E - S), (WRIST - E), (GRIP - WRIST)
    if min(abs(ua.normalized().z), abs(fa.normalized().z), abs(ha.normalized().z)) < 0.04:
        continue
    for tau in range(-180, 180, 15):
        pose = json.loads(json.dumps(base))
        pose['bones']['upper_arm_l'] = to_dir_entry(Mwi.to_3x3() @ ua)
        pose['bones']['forearm_l'] = to_dir_entry(Mwi.to_3x3() @ fa, tau)
        pose['bones']['hand_l'] = to_dir_entry(Mwi.to_3x3() @ ha)
        pose['bones'].pop('fingers_l', None)
        try:
            rig.apply(pose)
        except ValueError:
            continue
        M = shield.matrix_world
        sb = BVHTree.FromPolygons([M @ c for c in sco], stri, all_triangles=True)
        ov = {k: len(sb.overlap(b)) for k, b in PB.items()}
        ov['self'] = len(sb.overlap(HBVH))
        n = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
        c = M @ smid
        dg = bpy.context.evaluated_depsgraph_get(); ev = hmesh.evaluated_get(dg); me = ev.to_mesh()
        Mh = ev.matrix_world
        gap = min(PB['hair'].find_nearest(Mh @ me.vertices[i].co, 1.0)[3] or 1.0 for i in hand_idx)
        ev.to_mesh_clear()
        ov['hand_gap_cm'] = round(gap * 100, 1)
        # hair is soft (pressing into it is fine); a hand off the mane costs 1 per cm beyond 1.5 cm
        tot = ov['skin'] + ov['wing'] + ov['self'] + 0.02 * ov['hair'] + max(0.0, gap * 100 - 1.5)
        res.append({'phi': phi, 'tau': tau, 'overlaps': ov, 'total': tot, 'normal': [round(v, 2) for v in n],
                    'centre': [round(v, 3) for v in c], 'elbow': [round(v, 3) for v in E],
                    'bones': {k: pose['bones'][k] for k in ('upper_arm_l', 'forearm_l', 'hand_l')}})
res.sort(key=lambda d: (d['total'], -d['normal'][0]))
for d in res[:15]:
    print('###CAND###', json.dumps(d))
if OUT:
    json.dump(res, open(OUT, 'w'), indent=1)
