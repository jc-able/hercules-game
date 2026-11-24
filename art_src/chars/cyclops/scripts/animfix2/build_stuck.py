"""stuck fix (finding 10): club, both club hands and both feet pinned to the stuck pose (k00_stuck), keys every 3 frames
(read-backs of the re-based loop); the knees, hips, spine, neck and head keep the effort (trunk scaled down only where the
left hand could not reach grip2 otherwise: spine_03 hunches forward instead of scaling the tug).  python3 build_stuck.py [--write]"""
import sys, json, os, numpy as np
from fx import *
S = CL + '/slam/'; P = S + 'poses_stuck/'
WRITE = '--write' in sys.argv
ACT = S + 'action_stuck.rest_v2.json'
FR = list(range(1, 36))
NAME = {9: 'k005_life', 18: 'k01_tug', 27: 'k015_life'}
nm = lambda f: NAME.get(f, f'kf{f:02d}')
r = resolve([{'id': 'f0', 'from_action': ACT, 't': 0.0}] + [{'id': f'f{f}', 'from_action': ACT, 't': f / 24} for f in FR], 'stuck_a')
S0 = r['f0']; p0 = {b: np.array(v) for b, v in S0['pos'].items()}
US = [0, 2, 4, 6, 8, 10, 12, 14, 16]  # extra forward hunch of spine_03 (deg) so the shoulders stay within reach of the pinned club
cand = {}
for f in FR:
    for u in US:
        A = dict(r[f'f{f}']['abs'])
        for b, k in (('spine_02', 0.6), ('spine_03', 0.6)):  # upper-trunk tug x0.6 (relative to the stuck pose), chain follows
            A = rot_chain(A, b, slerp(S0['abs'][b], A[b], k) @ A[b].T)
        A = rot_chain(A, 'spine_03', rot_xyz(u, 0, 0))
        for b in ('foot_l', 'toe_l', 'foot_r', 'toe_r', 'hand_u_r', 'hand_u_l'): A[b] = S0['abs'][b]
        cand[(f, u)] = (A, {'loc': r[f'f{f}']['pose']['root']['loc']})
r1 = resolve([{'id': f'{f}_{u}', 'pose': pose_dict(A, root)} for (f, u), (A, root) in cand.items()], 'stuck_b')
fin = {}
for f in FR:
    for u in US:
        A, root = cand[(f, u)]; pos = r1[f'{f}_{u}']['pos']
        ok = True
        for up, fo, ha in (('upper_arm_u_l', 'forearm_u_l', 'hand_u_l'), ('upper_arm_u_r', 'forearm_u_r', 'hand_u_r')):
            H, K, W_ = (np.array(pos[x]) for x in (up, fo, ha))
            reach = np.linalg.norm(K - H) + np.linalg.norm(W_ - K)
            if np.linalg.norm(p0[ha] - H) > reach - 0.02: ok = False
        if ok or u == US[-1]: break
    A = leg_ik(A, pos, 'l', p0['foot_l']); A = leg_ik(A, pos, 'r', p0['foot_r'])
    A = arm_ik(A, pos, 'upper_arm_u_r', 'forearm_u_r', 'hand_u_r', p0['hand_u_r'])
    A = arm_ik(A, pos, 'upper_arm_u_l', 'forearm_u_l', 'hand_u_l', p0['hand_u_l'])
    fin[f] = (u, pose_dict(A, root, note=f'animfix 2026-11-23 stuck frame {f}: read-back of the re-based loop (+ spine_03 hunch {u} deg), feet + both club hands pinned to k00_stuck by IK'))
r2 = resolve([{'id': str(f), 'pose': p} for f, (u, p) in fin.items()], 'stuck_c')
for f in fin:
    q = r2[str(f)]['pos']
    print(f, nm(f), 'hunch', fin[f][0], {b: round(float(np.linalg.norm(np.array(q[b]) - p0[b])), 3) for b in ('foot_l', 'foot_r', 'hand_u_r', 'hand_u_l', 'hips', 'head', 'forearm_u_r')})
if WRITE:
    for f, (u, p) in fin.items(): json.dump(p, open(P + nm(f) + '.json', 'w'), indent=1)
    K = json.load(open(S + 'keys_stuck.json'))
    K['keys'] = [K['keys'][0]] + [{'t': round(f / 24, 4), 'pose_file': 'poses_stuck/' + nm(f) + '.json'} for f in FR]
    K['note_animfix2'] = '2026-11-23 animfix (cyclops): keys every frame = read-backs of the re-based loop with the feet, both club hands and the club pinned to k00_stuck (leg + arm IK); the tug shows in the knees, hips, spine and head (spine_03 hunches 0-16 deg forward where the left hand could not reach grip2 otherwise). Times of the loop, length 1.5 unchanged. Backups *.rest_v2.json.'
    json.dump(K, open(S + 'keys_stuck.json', 'w'), indent=1)
    print('written')
