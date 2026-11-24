"""Per key of the ride proof: find a Pegasus wing_*_01 orientation that follows the video's beat (raise from the wing
height u) and keeps the wings out of the rider. Candidate = Rx(pitch) @ Rz(yaw) @ Ry(raise) @ G  (make_poses.py family:
G = glide, full up = raise -75, full down = raise +70 with Rz(-20)). Pitch lifts the trailing edge, yaw < 0 sweeps the
left wing forward (checked below by the hit counts). Writes the chosen wing per key into <check_keys.json> (in place).

  Blender -b --factory-startup --python check/wing_search.py -- <repo> <ride_check.blend> <check_keys.json> <out.json>"""
import bpy, sys, os, json, math, time
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
REPO, BLEND, KEYS, OUT = argv[0], argv[1], argv[2], argv[3]
sys.path.insert(0, os.path.join(REPO, 'tools/animkit'))
import ak_blender as AK  # noqa: E402
RIDE = os.path.join(REPO, 'art_src/chars/ride')
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
harm, parm = bpy.data.objects['hercules_rig'], bpy.data.objects['pegasus_rig']
hrig = AK.Rig(harm, json.load(open(os.path.join(REPO, 'art_src/chars/hercules/rig.json'))),
              os.path.join(REPO, 'art_src/chars/hercules/hercules.blend'))
prig = AK.Rig(parm, json.load(open(os.path.join(REPO, 'art_src/chars/pegasus/rig.json'))),
              os.path.join(REPO, 'art_src/chars/pegasus/pegasus.blend'))
AK.write_action(hrig, json.load(open(os.path.join(RIDE, 'clips/ride/action_ride.json'))))
if parm.animation_data:
    parm.animation_data_clear()
fly = json.load(open(os.path.join(RIDE, 'poses/pegasus_fly.json')))
ck = json.load(open(KEYS)); u_mid = ck.get('u_mid', 0.73)

def R3(ax, a):
    return Matrix.Rotation(math.radians(a), 3, ax)
G = (R3('Z', 23.3) @ R3('Y', 62.3) @ R3('X', 74.5))
S = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))
def euler(M):
    e = M.to_euler('XYZ'); return {'rx': round(math.degrees(e.x), 2), 'ry': round(math.degrees(e.y), 2), 'rz': round(math.degrees(e.z), 2)}
def wing_l(raise_, pitch, yaw):
    return R3('X', pitch) @ R3('Z', yaw) @ R3('Y', raise_) @ G
def raise_of(u):
    return -75.0 * (1 - u / u_mid) if u <= u_mid else 70.0 * (u - u_mid) / (1 - u_mid)
def zdown(u):   # full_down carries Rz(-20): blend it in over the down half
    return 0.0 if u <= u_mid else -20.0 * (u - u_mid) / (1 - u_mid)

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
pmesh = bpy.data.objects['pegasus']; hmesh = bpy.data.objects['hercules']
preg, pdom = pegasus_regions(pmesh)
hgn = {g.index: g.name for g in hmesh.vertex_groups}
hdom = np.array([hgn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in hmesh.data.vertices], dtype=object)

def rider_bvhs():
    out = {}
    w, t = world_tris(hmesh)
    tb = hdom[t[:, 0]].astype(str)
    sk = np.char.startswith(tb, 'skirt')
    out['body'] = BVHTree.FromPolygons([tuple(v) for v in w], [tuple(x) for x in t[~sk]], all_triangles=True)
    out['skirt'] = BVHTree.FromPolygons([tuple(v) for v in w], [tuple(x) for x in t[sk]], all_triangles=True)
    for n in ('prop_sword', 'prop_shield'):
        w2, t2 = world_tris(bpy.data.objects[n])
        out[n] = BVHTree.FromPolygons([tuple(v) for v in w2], [tuple(x) for x in t2], all_triangles=True)
    return out, (w, t)

def wing_hits(rb, ht):
    pw, pt = world_tris(pmesh)
    sel = preg[pt[:, 0]] == 'wing'
    bp = BVHTree.FromPolygons([tuple(v) for v in pw], [tuple(x) for x in pt[sel]], all_triangles=True)
    res = {k: len(b.overlap(bp)) for k, b in rb.items()}
    parts = {}
    for a, _ in rb['body'].overlap(bp):
        pass
    return res

t0 = time.time()
PITCH = [0, 10, 20, 30, 40]
YAW = [0, -10, -20, 10, 20]
report = []
for k in ck['frames']:
    sc.frame_set(k['frame']); bpy.context.view_layer.update()
    rb, ht = rider_bvhs()
    ra, zd = raise_of(k['u']), zdown(k['u'])
    cands = []
    for p in PITCH:
        for y in YAW:
            Wl = wing_l(ra, p, y + zd)
            pose = json.loads(json.dumps(fly))
            pose['bones']['wing_l_01'] = euler(Wl); pose['bones']['wing_r_01'] = euler(S @ Wl @ S)
            prig.apply(pose)
            h = wing_hits(rb, ht)
            hard = h['body'] + h['prop_sword'] + h['prop_shield']
            cands.append({'pitch': p, 'yaw': y, 'hits': h, 'hard': hard, 'cost': hard * 1000 + h['skirt'] + abs(p) * 2 + abs(y) * 3})
            print('CAND', k['frame'], p, y, h, flush=True)
    best = min(cands, key=lambda c: c['cost'])
    Wl = wing_l(ra, best['pitch'], best['yaw'] + zd)
    k['raise'] = round(ra, 2); k['pitch'] = best['pitch']; k['yaw'] = best['yaw'] + round(zd, 2)
    k['wing_l_01'] = euler(Wl); k['wing_r_01'] = euler(S @ Wl @ S)
    base = next(c for c in cands if c['pitch'] == 0 and c['yaw'] == 0)
    report.append({'frame': k['frame'], 'u': k['u'], 'raise': ra, 'best': best, 'unpitched': base})
    print('BEST', k['frame'], json.dumps(best), round(time.time() - t0, 1), flush=True)
json.dump(ck, open(KEYS, 'w'), indent=1)
json.dump(report, open(OUT, 'w'), indent=1)
print('###SEARCH### ok', round(time.time() - t0, 1))
