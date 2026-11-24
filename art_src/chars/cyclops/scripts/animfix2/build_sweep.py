"""sweep fixes: (finding 7) lower left arm abducted out of the hips/skirt; (finding 8) the return to the stance starts at
k8c_unwind (2.125) and the root pivot of 2.0-2.25 no longer zig-zags (k8d carries root rot 42 instead of 0, same world pose).
Strike (<= 1.5 s) untouched except the lower left arm.  python3 build_sweep.py [--write]"""
import sys, json, os, numpy as np
from fx import *
D = CL + '/sweep/'
WRITE = '--write' in sys.argv
K = json.load(open(D + 'keys_sweep.rest_v2.json'))
SRC = {k['t']: k['pose_file'] for k in K['keys']}
src = lambda pf: D + pf.replace('.json', '.rest_v2.json')
r = resolve([{'id': str(t), 'pose_file': src(pf)} for t, pf in SRC.items() if t < 2.5], 'sweep_a')
W = {t: r[str(t)]['abs'] for t in SRC if t < 2.5}
NAT = W[0.0]
ABD = {0.375: 20, 0.625: 14, 0.875: 18, 1.8125: 22, 1.875: 30, 2.0: 20, 2.0833: 12}
RET = {2.125: 0.22, 2.25: 0.5, 2.375: 0.85}
ROT = {2.0833: 42.0}
mod = {}
for t, deg in ABD.items():
    A = dict(W[t]); S3 = A['spine_03']
    Rout = S3 @ rot_xyz(0, -deg, 0) @ S3.T
    A = rot_chain(A, 'upper_arm_d_l', Rout)
    if t >= 1.8:  # the rebase's trailing lower-left hand: take back half of it
        A['hand_d_l'] = slerp(A['hand_d_l'], Rout @ W[t]['forearm_d_l'] @ np.linalg.inv(W[t]['forearm_d_l']) @ A['hand_d_l'], 0.0)
    mod[t] = A
for t, u in RET.items():
    LEG = ('hips', 'thigh_l', 'shin_l', 'foot_l', 'toe_l', 'thigh_r', 'shin_r', 'foot_r', 'toe_r')
    Wa = dict(W[t]); S3 = Wa['spine_03']; da = {2.125: 9, 2.25: 4}.get(t, 0)
    Wa = rot_chain(Wa, 'upper_arm_d_l', S3 @ rot_xyz(0, -da, 0) @ S3.T)
    mod[t] = {b: (W[t][b] if b in LEG else slerp(Wa[b], NAT[b], u)) for b in W[t]}
for t in ROT: mod.setdefault(t, dict(W[t]))
for t, rz in ROT.items():  # k8d: the read-back had the hips/legs at yaw 0 between 60 (k8b) and 30 (k8c): turn the lower body to the root yaw
    for b in ('hips', 'thigh_l', 'shin_l', 'foot_l', 'toe_l', 'thigh_r', 'shin_r', 'foot_r', 'toe_r'):
        mod[t][b] = rot_xyz(0, 0, rz) @ mod[t][b]
    for b in mod[t]:
        if b not in ('hips', 'thigh_l', 'shin_l', 'foot_l', 'toe_l', 'thigh_r', 'shin_r', 'foot_r', 'toe_r'):
            mod[t][b] = slerp(mod[t][b], NAT[b], 0.12)
fin = {}
for t, A in mod.items():
    orig = json.load(open(src(SRC[t])))
    root = dict(orig['root'])
    rz = ROT.get(t, root.get('rot', [0, 0, 0])[2] * (1 - RET.get(t, 0.0)))
    root['rot'] = [0, 0, round(rz, 3)]
    R0 = rot_xyz(0, 0, rz).T
    p = pose_dict({b: R0 @ m for b, m in A.items()}, root, note=f'animfix 2026-11-23 sweep t={t}: ' + (
        f'lower left arm abducted {ABD[t]} deg (out of the skirt)' if t in ABD else f'{int(RET[t]*100)}% toward the natural stance (return starts at 2.125)' if t in RET else 'same world pose, root rot 42 (no root zig-zag 60-0-30)'))
    if 'view_offset' in orig: p['view_offset'] = orig['view_offset']
    fin[t] = p
chk = resolve([{'id': str(t), 'pose': p} for t, p in fin.items()], 'sweep_c')
for t in sorted(fin):
    q, o = chk[str(t)]['pos'], r[str(t)]['pos']
    dev = {b: round(float(np.linalg.norm(np.array(q[b]) - np.array(o[b]))), 3) for b in ('hips', 'hand_u_r', 'hand_d_l', 'head', 'foot_l')}
    print(t, dev)
if WRITE:
    for t, p in fin.items():
        pf = SRC[t]
        json.dump(p, open(D + pf, 'w'), indent=1)
    K2 = json.load(open(D + 'keys_sweep.json'))
    K2['note_animfix2'] = '2026-11-23 animfix (cyclops): upper_arm_d_l abducted 10-14 deg (spine_03 frame) at k1_lift, k2_cock, k3_behind_neck, k7c, k8, k8b (lower left hand out of the hips/skirt); k8c_unwind 22%, k9_recover 50%, k9b_settle 85% toward natural (the return starts at 2.125); k8d root rot 0 -> 42 with the same world pose (root no longer zig-zags 60-0-30-0). Strike, impact 1.31, length 2.5 unchanged. Backups *.rest_v2.json.'
    json.dump(K2, open(D + 'keys_sweep.json', 'w'), indent=1)
    print('written')
