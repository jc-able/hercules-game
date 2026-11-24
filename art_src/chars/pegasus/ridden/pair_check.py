"""Pair check (assembler): Pegasus clip actions + the seated Hercules `ride` action in a COPY of ride.blend
(art_src/chars/ride/, so the relative textures resolve). Counts rider-vs-WING triangle overlaps on every sampled frame.

  Blender -b --factory-startup --python pair_check.py -- <repo> <ride copy.blend> <out.json> <clip>=<action.json>[@<rider_speed>] ...

rider_speed: 'beat' (rider 1.5 s loop scaled to one Pegasus clip length = one wing beat, phase 0 = wing top, as in
ride_game.json) or a number (rider playback speed, e.g. 0.4 for glide)."""
import bpy, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
REPO, BLEND, OUT = argv[0], argv[1], argv[2]
specs = argv[3:]
sys.path.insert(0, os.path.join(REPO, 'tools/animkit'))
import ak_blender as AK  # noqa: E402
RIDE = os.path.join(REPO, 'art_src/chars/ride')
sys.path.insert(0, os.path.join(RIDE, 'scripts'))
from peg_regions import pegasus_regions  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
harm, parm = bpy.data.objects['hercules_rig'], bpy.data.objects['pegasus_rig']
hrig = AK.Rig(harm, json.load(open(os.path.join(REPO, 'art_src/chars/hercules/rig.json'))),
              os.path.join(REPO, 'art_src/chars/hercules/hercules.blend'))
prig = AK.Rig(parm, json.load(open(os.path.join(REPO, 'art_src/chars/pegasus/rig.json'))),
              os.path.join(REPO, 'art_src/chars/pegasus/pegasus.blend'))
ride = json.load(open(os.path.join(RIDE, 'clips/ride/action_ride.json')))
RIDE_LEN = float(ride['length'])

pmesh = bpy.data.objects['pegasus']
preg, _ = pegasus_regions(pmesh)
rider_objs = [bpy.data.objects[n] for n in ('hercules', 'prop_sword', 'prop_shield')]
hgn = {g.index: g.name for g in bpy.data.objects['hercules'].vertex_groups}
hdom = np.array([hgn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-'
                 for v in bpy.data.objects['hercules'].data.vertices], dtype=object)


def world_tris(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', tri)
    ev.to_mesh_clear()
    return w, tri.reshape(-1, 3)


def scale_action_time(arm, k):
    for fc in AK.action_fcurves(arm.animation_data.action):
        for kp in fc.keyframe_points:
            kp.co.x *= k; kp.handle_left.x *= k; kp.handle_right.x *= k
        fc.update()


report = {}
for spec in specs:
    name, rest = spec.split('=', 1)
    path, _, rs = rest.partition('@')
    data = json.load(open(path))
    fps, L = float(data['fps']), float(data['length'])
    AK.write_action(prig, data)
    AK.write_action(hrig, ride)
    if rs in ('', 'beat'):
        k = L / RIDE_LEN                       # one rider loop per Pegasus loop, both start at the wing top
    else:
        k = 1.0 / float(rs)
    scale_action_time(harm, k)
    sc.render.fps = int(round(fps))
    nF = int(round(L * fps))
    step = 1 if nF <= 30 else (2 if nF <= 80 else 4)
    sub = int(os.environ.get('PAIR_SUB', '1'))
    rows, worst = [], 0
    for fi in range(0, nF * sub, step):
        f = fi / sub
        sc.frame_set(int(f), subframe=f - int(f))
        bpy.context.view_layer.update()
        pw, pt = world_tris(pmesh)
        sel = np.nonzero(preg[pt[:, 0]] == 'wing')[0]
        bp = BVHTree.FromPolygons(pw.tolist(), pt[sel].tolist(), all_triangles=True)
        hits, parts = {}, {}
        for o in rider_objs:
            w, t = world_tris(o)
            bo = BVHTree.FromPolygons(w.tolist(), t.tolist(), all_triangles=True)
            pairs = bo.overlap(bp)
            hits[o.name] = len(pairs)
            if o.name == 'hercules':
                for a, _ in pairs:
                    b = hdom[t[a][0]]; parts[b] = parts.get(b, 0) + 1
        tot = sum(hits.values())
        worst = max(worst, tot)
        rows.append({'frame': f, 't': round(f / fps, 4), 'hits': hits, 'bones': parts})
        print('ROW', name, json.dumps(rows[-1]), flush=True)
    report[name] = {'action': path, 'length': L, 'fps': fps, 'rider_time_scale': k, 'frames_checked': len(rows),
                    'frames_with_hits': sum(1 for r in rows if sum(r['hits'].values())), 'max_pairs': worst,
                    'rows': rows}
    json.dump(report, open(OUT, 'w'), indent=1)
print('###PAIR### ok', json.dumps({n: {'frames_with_hits': v['frames_with_hits'], 'max_pairs': v['max_pairs'],
                                     'frames_checked': v['frames_checked']} for n, v in report.items()}))
