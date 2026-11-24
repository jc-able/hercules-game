"""death fixes: (finding 3) asymmetric arm flail in g0375..g112 (+ k2_kneel arms eased), root/hips/legs/fall untouched;
(finding 9) shoulder slump held constant in the spine_03 frame from k3b_hold (2.6 s) to the end.  python3 build_death.py [--write]"""
import sys, json, os, numpy as np
from fx import *
D = CL + '/death/'; P = D + 'poses_death/'
WRITE = '--write' in sys.argv
K = json.load(open(D + 'keys_death.rest_v2.json'))
SRC = {k['t']: k['pose_file'] for k in K['keys']}
src = lambda pf: D + pf.replace('.json', '.rest_v2.json') if os.path.exists(D + pf.replace('.json', '.rest_v2.json')) else D + pf
r = resolve([{'id': str(t), 'pose_file': src(pf)} for t, pf in SRC.items()], 'death_a')
nat = r['0.0']; NA = nat['abs']; NP = {b: np.array(v) for b, v in nat['pos'].items()}
CH = {'shoulder_u_l': 'upper_arm_u_l', 'upper_arm_u_l': 'forearm_u_l', 'forearm_u_l': 'hand_u_l',
      'upper_arm_d_l': 'forearm_d_l', 'forearm_d_l': 'hand_d_l', 'upper_arm_d_r': 'forearm_d_r', 'forearm_d_r': 'hand_d_r'}
ndir = {b: (NP[c] - NP[b]) / np.linalg.norm(NP[c] - NP[b]) for b, c in CH.items()}
un = lambda v: np.asarray(v, float) / np.linalg.norm(v)


def aimed(spec):
    """spec: {bone: direction}; hands follow their forearm. returns {bone: abs}"""
    out = {}
    for b, d in spec.items():
        out[b] = rotmin(ndir[b], un(d)) @ NA[b]
    for fa, h in (('forearm_u_l', 'hand_u_l'), ('forearm_d_l', 'hand_d_l'), ('forearm_d_r', 'hand_d_r')):
        if fa in spec:
            out[h] = rotmin(ndir[fa], un(spec[fa])) @ NA[h]
    return out


def bend(u, f): return round(float(np.degrees(np.arccos(np.clip(np.dot(un(u), un(f)), -1, 1)))), 1)


# left upper arm: thrown up and back, elbow bent 40-60, then falls limp toward the knees
LU = {0.375: ((0.62, 0.30, 0.72), (0.08, -0.05, 1.0), -14),
      0.625: ((0.72, 0.42, 0.55), (0.25, -0.05, 0.97), -12),
      0.75: ((0.86, 0.32, 0.20), (0.55, -0.30, 0.78), -7),
      0.875: ((0.80, 0.05, -0.45), (0.62, -0.45, -0.10), -3),
      1.0: ((0.55, -0.12, -0.80), (0.38, -0.50, -0.70), 0),
      1.083: ((0.48, -0.08, -0.86), (0.30, -0.36, -0.86), 0),
      1.25: ((0.42, -0.06, -0.90), (0.28, -0.28, -0.90), 0)}
for t, (u, f, s) in LU.items(): print('left elbow bend', t, bend(u, f))
LUA = {0.0: {b: NA[b] for b in ('shoulder_u_l', 'upper_arm_u_l', 'forearm_u_l', 'hand_u_l')}}
for t, (u, f, s) in LU.items():
    A = aimed({'upper_arm_u_l': u, 'forearm_u_l': f}); A['shoulder_u_l'] = rot_xyz(0, s, 0) @ NA['shoulder_u_l']; LUA[t] = A
# lower arms reach toward the knees; right one higher (~15 deg) and 2 frames later
LO = {'reach_l': {'upper_arm_d_l': (0.30, -0.55, -0.78), 'forearm_d_l': (0.15, -0.75, -0.64)},
      'brace_l': {'upper_arm_d_l': (0.32, -0.42, -0.85), 'forearm_d_l': (0.14, -0.52, -0.84)},
      'reach_r': {'upper_arm_d_r': (-0.32, -0.70, -0.64), 'forearm_d_r': (-0.18, -0.90, -0.40)},
      'brace_r': {'upper_arm_d_r': (-0.34, -0.60, -0.72), 'forearm_d_r': (-0.16, -0.72, -0.67)}}
LOA = {k: aimed(v) for k, v in LO.items()}
natL = {b: NA[b] for b in ('upper_arm_d_l', 'forearm_d_l', 'hand_d_l')}; natR = {b: NA[b] for b in ('upper_arm_d_r', 'forearm_d_r', 'hand_d_r')}
TRL = [(0.0, natL, natL, 0), (0.75, natL, LOA['reach_l'], 1), (0.875, LOA['reach_l'], LOA['reach_l'], 0), (1.0, LOA['reach_l'], LOA['brace_l'], 1), (1.25, LOA['brace_l'], LOA['brace_l'], 0)]
TRR = [(0.0, natR, natR, 0), (0.75, natR, LOA['reach_r'], 1), (0.875, LOA['reach_r'], LOA['reach_r'], 0), (1.0, LOA['reach_r'], LOA['brace_r'], 1), (1.25, LOA['brace_r'], LOA['brace_r'], 0)]


def ease(x): return x * x * (3 - 2 * x)


def at(anchors, t):
    """anchors: {time: {bone: abs}} -> slerp between neighbours (smoothstep)"""
    ts = sorted(anchors)
    if t <= ts[0]: return anchors[ts[0]]
    if t >= ts[-1]: return anchors[ts[-1]]
    for a, b in zip(ts, ts[1:]):
        if a <= t <= b:
            u = ease((t - a) / (b - a)); return {k: slerp(anchors[a][k], anchors[b][k], u) for k in anchors[a]}


def lower(t, side):
    pts = {0.0: natL if side == 'l' else natR, 0.75: LOA['reach_' + side], 0.875: LOA['reach_' + side], 1.0: LOA['brace_' + side], 1.25: {b: rot_xyz(7 if side == 'l' else 4, 0, 0) @ m for b, m in LOA['brace_' + side].items()}}
    return at(pts, t)


CLUBB = ('shoulder_u_r', 'upper_arm_u_r', 'forearm_u_r', 'hand_u_r')
g104 = r['1.042']['abs']
CU = {0.375: 0.3, 0.625: 0.6, 0.75: 0.75, 0.875: 0.88, 1.0: 0.96}
WIN = [0.375, 0.625, 0.75, 0.875, 1.0, 1.042, 1.083, 1.125, 1.25]
fin = {}
for t in WIN:
    A = dict(r[str(t)]['abs'])
    A.update(at(LUA, t))
    A.update(lower(t, 'l')); A.update(lower(max(0.0, t - 0.0833), 'r'))
    if t in CU:
        for b in CLUBB: A[b] = slerp(NA[b], g104[b], CU[t])
    pf = SRC[t]; orig = json.load(open(src(pf)))
    p = pose_dict(A, orig['root'], note=f'animfix 2026-11-23 death t={t}: arms re-posed as an asymmetric flail (left upper arm thrown up/back, club arm drops and drags the club, lower arms reach toward the knees, right 2 frames later and higher); root/hips/legs/spine = previous key')
    if 'view_offset' in orig: p['view_offset'] = orig['view_offset']
    fin[t] = (pf, p)
# finding 9: constant shoulder slump (relative to spine_03) from k3b_hold on
ref = r['2.6']['abs']; rel = {s: ref['spine_03'].T @ ref[s] for s in ('shoulder_u_l', 'shoulder_u_r')}
for t, pf in SRC.items():
    if t < 2.6 or t in fin: continue
    orig = json.load(open(src(pf)))
    A = r[str(t)]['abs']
    R0 = rot_xyz(*orig['root'].get('rot', [0, 0, 0])).T  # entries are measured before root.rot
    for s in ('shoulder_u_l', 'shoulder_u_r'):
        orig['bones'][s] = dict(zip(('rx', 'ry', 'rz'), euler_xyz(R0 @ A['spine_03'] @ rel[s])))
    orig['_animfix'] = 'animfix 2026-11-23: shoulder_u_l/r absolute = constant slump relative to spine_03 (value of k3b_hold 2.6 s)'
    fin[t] = (pf, orig)
chk = resolve([{'id': str(t), 'pose': p} for t, (pf, p) in fin.items() if t < 2.6], 'death_c')
for t in WIN:
    q = chk[str(t)]['pos']; o = r[str(t)]['pos']
    print(t, 'hips moved', round(float(np.linalg.norm(np.array(q['hips']) - np.array(o['hips']))), 4), 'hand_u_l', np.round(q['hand_u_l'], 2), 'hand_d_l', np.round(q['hand_d_l'], 2), 'hand_d_r', np.round(q['hand_d_r'], 2), 'knees', np.round(q['shin_l'], 2), np.round(q['shin_r'], 2), 'hand_u_r', np.round(q['hand_u_r'], 2))
if WRITE:
    for t, (pf, p) in fin.items(): json.dump(p, open(D + pf, 'w'), indent=1)
    K2 = json.load(open(D + 'keys_death.json'))
    K2['note_animfix2'] = '2026-11-23 animfix (cyclops): arms of g0375..g112 and k2_kneel re-posed (asymmetric flail, no rest T pose); shoulder slump constant in the spine_03 frame from 2.6 s (no stop-and-go at 3.25-3.42). Root, hips, legs, fall path, times unchanged. Backups *.rest_v2.json.'
    json.dump(K2, open(D + 'keys_death.json', 'w'), indent=1)
    print('written')
