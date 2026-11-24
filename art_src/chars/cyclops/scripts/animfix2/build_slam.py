"""slam fix (findings 1 + 6): new k01_lift in-between; feet planted with leg IK (root, hips, spine, arms, club kept);
left weight-shift step 0.25-0.75; right step 1.125-1.333 onto the impact spot.  python3 build_slam.py [--write]"""
import sys, json, os, copy, numpy as np
from fx import *
S = CL + '/slam/'; P = S + 'poses_slam/'
ACT = S + 'action_slam.rest_v2.json' if os.path.exists(S + 'action_slam.rest_v2.json') else S + 'action_slam.json'
WRITE = '--write' in sys.argv
FR = [0, 6, 12, 18, 24, 27, 29, 32, 33, 34, 35, 36]
T = [f / 24 for f in FR]
KT = {0: 0.0, 6: 0.25, 12: 0.5, 18: 0.75, 24: 1.0, 27: 1.125, 29: 1.2083, 32: 1.333, 33: 1.375, 34: 1.417, 35: 1.458, 36: 1.5}
items = [{'id': f'rb{t}', 'from_action': ACT, 't': t} for t in T]
items += [{'id': 'nat', 'pose_file': P + 'k00_ready.json'}, {'id': 'k02', 'pose_file': P + 'k02_raise.json'}]
r = resolve(items, 'slam_a')
rb = {KT[f]: r[f'rb{f/24}'] for f in FR}
nat, k02 = r['nat'], r['k02']
Lnat = np.array(rb[0.0]['pos']['foot_l']); Rnat = np.array(rb[0.0]['pos']['foot_r'])
Limp = np.array(rb[1.5]['pos']['foot_l']); Rimp = np.array(rb[1.5]['pos']['foot_r'])
print('feet nat L', Lnat, 'R', Rnat, ' imp L', Limp, 'R', Rimp)
FLAT = Lnat[2]  # ankle height of a flat planted foot


def tgt(p, z=None, lift=0.0):
    p = np.array(p, float).copy(); p[2] = (FLAT if z is None else z) + lift; return p


Lmid = (Lnat + Limp) / 2; Rmid = (Rnat + Rimp) / 2
plan = {  # t: (left target, right target, left foot abs source, right foot abs source)
    0.25: (tgt(Lnat), tgt(Rnat), ('nat', 0), ('nat', 0)),
    0.5: (tgt(Lmid, lift=0.16), tgt(Rnat), ('mix', 0.5), ('nat', 0)),
    0.75: (tgt(Limp), tgt(Rnat), ('imp', 0), ('nat', 0)),
    1.0: (tgt(Limp), tgt(Rnat), ('imp', 0), ('nat', 0)),
    1.125: (tgt(Limp), tgt(Rnat), ('imp', 0), ('nat', 0)),
    1.2083: (tgt(Limp), tgt(Rmid, lift=0.30), ('imp', 0), ('mix', 0.5)),
    1.333: (tgt(Limp), tgt(Rimp), ('imp', 0), ('imp', 0)),
    1.375: (tgt(Limp), tgt(Rimp), ('imp', 0), ('imp', 0)),
    1.417: (tgt(Limp), tgt(Rimp), ('imp', 0), ('imp', 0)),
    1.458: (tgt(Limp), tgt(Rimp), ('imp', 0), ('imp', 0)),
}
names = {0.25: 'k01_lift', 0.5: 'k02_raise', 0.75: 'k025_step', 1.0: 'k03_overhead', 1.125: 'k035_plant', 1.2083: 'k037_step',
         1.333: 'k04_windup', 1.375: 'k05_chop', 1.417: 'k06_swing', 1.458: 'k065_fall'}


def new_k01():
    """club lifts off the shoulder: right arm toward k02, forearm stays bent; left upper hand reaches up; lower arms brace forward-down"""
    A = dict(rb[0.25]['abs'])
    for b, u in (('shoulder_u_r', 0.4), ('upper_arm_u_r', 0.4), ('forearm_u_r', 0.35), ('hand_u_r', 0.35),
                 ('shoulder_u_l', 0.45)):
        A[b] = slerp(nat['abs'][b], k02['abs'][b], u)
    # left upper arm: elbow out to the side and forward, hand rising in front of the chest/face (not behind the neck)
    NP = {b: np.array(v) for b, v in rb[0.0]['pos'].items()}; NA = rb[0.0]['abs']
    nd = lambda b, c: (NP[c] - NP[b]) / np.linalg.norm(NP[c] - NP[b])
    du = np.array([0.35, -0.75, 0.10]); df = np.array([-0.45, -0.35, 0.82])
    Ru = rotmin(nd('upper_arm_u_l', 'forearm_u_l'), du); Rf = rotmin(nd('forearm_u_l', 'hand_u_l'), df)
    A['upper_arm_u_l'] = Ru @ NA['upper_arm_u_l']; A['forearm_u_l'] = Rf @ NA['forearm_u_l']; A['hand_u_l'] = Rf @ NA['hand_u_l']
    for b in ('upper_arm_d_l', 'forearm_d_l', 'hand_d_l', 'upper_arm_d_r', 'forearm_d_r', 'hand_d_r'):
        A[b] = nat['abs'][b]
    A = rot_chain(A, 'upper_arm_d_l', rot_xyz(-22, 4, 0)); A = rot_chain(A, 'forearm_d_l', rot_xyz(-18, 0, 0))
    A = rot_chain(A, 'upper_arm_d_r', rot_xyz(-16, -3, 0)); A = rot_chain(A, 'forearm_d_r', rot_xyz(-24, 0, 0))
    return A


footabs = {'nat': {s: nat['abs']['foot_' + s] for s in 'lr'}, 'imp': {s: rb[1.5]['abs']['foot_' + s] for s in 'lr'}}
for s in 'lr':
    footabs.setdefault('toe', {})[s] = (nat['abs']['toe_' + s], rb[1.5]['abs']['toe_' + s])
out = {}
for t, (lt, rt, lf, rf) in plan.items():
    A = new_k01() if t == 0.25 else dict(rb[t]['abs'])
    for s, src in (('l', lf), ('r', rf)):
        if src[0] == 'mix':
            A['foot_' + s] = slerp(footabs['nat'][s], footabs['imp'][s], src[1]); A['toe_' + s] = slerp(*footabs['toe'][s], src[1])
        else:
            A['foot_' + s] = footabs[src[0]][s]; A['toe_' + s] = footabs['toe'][s][0 if src[0] == 'nat' else 1]
    root = {'loc': rb[t]['pose']['root']['loc'] if rb[t]['pose'].get('root') else [0, 0, 0]}
    out[t] = (A, root)
# pass 1: resolve with the new arms/feet to get hip positions, then IK (hips do not depend on the legs)
r1 = resolve([{'id': str(t), 'pose': pose_dict(A, root)} for t, (A, root) in out.items()], 'slam_b')
fin = {}
for t, (A, root) in out.items():
    pos = r1[str(t)]['pos']; lt, rt = plan[t][0], plan[t][1]
    A = leg_ik(A, pos, 'l', lt); A = leg_ik(A, pos, 'r', rt)
    fin[t] = pose_dict(A, root, note=f'animfix 2026-11-23 slam t={t}: legs IK (feet planted / stepping), root.loc explicit = old bake' + ('; NEW in-between arms' if t == 0.25 else '; arms/trunk/club = old bake'))
r2 = resolve([{'id': str(t), 'pose': p} for t, p in fin.items()] + [{'id': 'k07', 'pose_file': P + 'k07_impact.json'}], 'slam_c')
for t in plan:
    p = r2[str(t)]['pos']; q = rb[t]['pos']
    dh = max(np.linalg.norm(np.array(p[b]) - np.array(q[b])) for b in ('hand_u_r', 'head', 'spine_03', 'hips'))
    print(f't={t:6.4f} L {np.round(p["foot_l"],3)} (tgt {np.round(plan[t][0],3)})  R {np.round(p["foot_r"],3)} (tgt {np.round(plan[t][1],3)})  upper-body moved {dh:.4f} m  hand_u_r {np.round(p["hand_u_r"],3)}')
if WRITE:
    for t, p in fin.items():
        json.dump(p, open(P + names[t] + '.json', 'w'), indent=1)
    K = json.load(open(S + 'keys_slam.json'))
    keep = {k['t']: k for k in K['keys']}
    keys = []
    for t in [0.0] + list(plan) + [1.5, 1.75]:
        if t in keep: keys.append(keep[t])
        else: keys.append({'t': t, 'pose_file': 'poses_slam/' + names[t] + '.json'})
    K['keys'] = keys
    K['note_animfix2'] = '2026-11-23 animfix (cyclops): k01_lift rewritten as a real in-between (club lifts off the shoulder, left hand reaches up, lower arms brace); feet planted by leg IK at every key 0.25-1.458 with root.loc = the old bake (club path from 1.333 unchanged); left weight-shift step 0.25-0.75 onto the impact spot (new key k025_step), right step 1.125-1.333 lifting 0.30 m (new keys k035_plant, k037_step). Backups *.rest_v2.json.'
    json.dump(K, open(S + 'keys_slam.json', 'w'), indent=1)
    print('written')
