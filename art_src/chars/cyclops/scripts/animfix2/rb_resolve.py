"""Headless Blender helper for the cyclops re-base (read-only use of the blend; never saves).
Blender -b --factory-startup --python rb_resolve.py -- job.json out.json
job: {"blend": path, "items": [{"id": s, "pose_file": p} | {"id": s, "from_action": a, "t": t}]}
out: {id: {"pose": resolved pose dict (from_action only), "local": {bone: 3x3 view-axes Rw for local_delta},
           "abs": {bone: 3x3 view-axes Rw absolute}}}"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../../tools/animkit')))
import ak_blender as AK

argv = sys.argv[sys.argv.index('--') + 1:]
job = json.load(open(argv[0]))
arm = AK.open_blend(job['blend'])
rig = AK.Rig(arm, AK.rig_json_for(job['blend']), job['blend'])
AK.clear_anim(arm)
res = {}
def m2l(M):
    return [[round(M[i][j], 7) for j in range(3)] for i in range(3)]
for it in job['items']:
    pose_out = None
    if 'from_action' in it:
        pose = AK.read_pose_from(rig, it['from_action'], float(it['t']))
        pose_out = pose
    else:
        pose = AK.load_pose(it['pose_file'])
    P = rig.solve(pose)
    loc, ab = {}, {}
    for n in rig.names:
        if n in rig.driven_all:
            continue
        p = rig.parent[n]
        follow = rig.rest[n] if p is None else P[p] @ (rig.rest[p].inverted() @ rig.rest[n])
        R = P[n].to_3x3().normalized()
        loc[n] = m2l(rig.Ra @ (R @ follow.to_3x3().normalized().inverted()) @ rig.RaT)
        ab[n] = m2l(rig.Ra @ (R @ rig.rest[n].to_3x3().normalized().inverted()) @ rig.RaT)
    AK.apply_grounded(rig, pose); G = True
    pos = {pb.name: [round(v, 4) for v in (arm.matrix_world @ pb.head)] for pb in arm.pose.bones} if G is not None else None
    res[it['id']] = {'pose': pose_out, 'local': loc, 'abs': ab, 'parent': rig.parent, 'pos': pos}
json.dump(res, open(argv[1], 'w'))
print('###RB### ok', len(res))
