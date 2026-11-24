"""pull_free end fix (finding 2): left upper arm + lower arms toward natural in k06/k07, return starts earlier, hands staggered.
keys: ... k05 1.125 | k06_over 1.2083 | k07_shoulder 1.2917 | k075_settle 1.375 (~60%) | k078_settle 1.4583 (~90%) | k08_natural 1.5"""
import sys, json, os, numpy as np
from fx import *
S = CL + '/slam/'; P = S + 'poses_pull_free/'
SRC = lambda n: P + n + ('.rest_v2.json' if os.path.exists(P + n + '.rest_v2.json') else '.json')
WRITE = '--write' in sys.argv
r = resolve([{'id': k, 'pose_file': SRC(k)} for k in ('k06_over', 'k07_shoulder', 'k08_natural')], 'pf_b')
k06, k07, nat = (r[k]['abs'] for k in ('k06_over', 'k07_shoulder', 'k08_natural'))
LEFT = ['shoulder_u_l', 'upper_arm_u_l', 'forearm_u_l', 'hand_u_l']
LOWER = ['upper_arm_d_l', 'forearm_d_l', 'hand_d_l', 'upper_arm_d_r', 'forearm_d_r', 'hand_d_r']


def mix(A, B, u, bones=None, per=None):
    out = dict(A)
    for b in (bones or list(A)):
        uu = (per or {}).get(b, u)
        out[b] = slerp(A[b], B[b], uu)
    return out


CLUB = ['shoulder_u_r', 'upper_arm_u_r', 'forearm_u_r', 'hand_u_r']
K6 = mix(k06, nat, 0.4, LEFT + LOWER)
K6 = mix(K6, nat, 0.15, CLUB)
K7 = mix(k07, nat, 0.75, LEFT + LOWER)
K7 = mix(K7, nat, 0.55, CLUB)
HANDS1 = {'hand_u_r': 0.72, 'hand_u_l': 0.6, 'hand_d_l': 0.5, 'hand_d_r': 0.42}
HANDS2 = {'hand_u_r': 1.0, 'hand_u_l': 0.95, 'hand_d_l': 0.88, 'hand_d_r': 0.8}
K75 = mix(K7, nat, 0.6, None, HANDS1)
K78 = mix(K7, nat, 0.92, None, HANDS2)
root = lambda f: {'loc': [round(0.25 * f, 4), 0, 0], 'ground': 'lowest'}
new = {'k06_over': (K6, root(0)), 'k07_shoulder': (K7, root(0)), 'k075_settle': (K75, root(0.6)), 'k078_settle': (K78, root(0.92))}
fin = {n: pose_dict(A, rt, note=f'animfix 2026-11-23 pull_free {n}: left upper arm + lower arms toward natural; return to natural from 1.29 s, hands staggered') for n, (A, rt) in new.items()}
chk = resolve([{'id': n, 'pose': p} for n, p in fin.items()], 'pf_c')
for n in fin: print(n, 'hand_u_r', np.round(chk[n]['pos']['hand_u_r'], 3), 'hand_u_l', np.round(chk[n]['pos']['hand_u_l'], 3))
if WRITE:
    for n, p in fin.items(): json.dump(p, open(P + n + '.json', 'w'), indent=1)
    K = json.load(open(S + 'keys_pull_free.json'))
    keys = [k for k in K['keys'] if k['t'] <= 0.75]
    keys += [{'t': 0.9583, 'pose_file': 'poses_pull_free/k04_across.json'}, {'t': 1.0833, 'pose_file': 'poses_pull_free/k05_swing_up.json'}]
    keys += [{'t': 1.1667, 'pose_file': 'poses_pull_free/k06_over.json'}, {'t': 1.2917, 'pose_file': 'poses_pull_free/k07_shoulder.json'},
             {'t': 1.375, 'pose_file': 'poses_pull_free/k075_settle.json'}, {'t': 1.4583, 'pose_file': 'poses_pull_free/k078_settle.json'},
             {'t': 1.5, 'pose_file': 'poses_pull_free/k08_natural.json'}]
    K['keys'] = keys
    K['note_animfix2'] = '2026-11-23 animfix (cyclops): end re-timed (k04 1.0->0.9583, k05 1.125->1.0833, k06 1.25->1.1667, k07 1.375->1.2917, new k075_settle 1.375 ~60% to natural, k078_settle 1.4583 ~90% with the four hands staggered, natural 1.5); left upper arm and lower arms move toward natural already in k06 (50%) and k07 (80%). Length 1.5 unchanged, no events. Backups *.rest_v2.json.'
    json.dump(K, open(S + 'keys_pull_free.json', 'w'), indent=1)
    print('written')
