"""walk fixes (findings 4, 5, 11) on per-frame read-backs of the walk_n bake (34 keys, loop 1.4167 s):
 - lower arms: abducted 14 deg out of the hips/skirt (spine_03 frame), 2 frames later than before (local to spine_03),
   right lower arm amplitude x0.82 of the left (no exact mirror)
 - club arm: roll (hand_u_r, +-5 deg) and a dip (forearm_u_r + hand, 4 deg) 2-3 frames after each footfall
 - stance foot: x pinned by leg IK to its contact x (counters the 0.13 m hip sway); fades out over 4 frames after lift-off
python3 build_walk.py [--write]"""
import sys, json, os, math, numpy as np
from fx import *
from rbcore import m2q, q2m
Dd = CL + '/walk_n/'
WRITE = '--write' in sys.argv
ACT = Dd + 'action_walk.rest_v2.json'
N = 34
r = resolve([{'id': str(f), 'from_action': ACT, 't': f / 24} for f in range(N)], 'walk_a')
AB = [r[str(f)]['abs'] for f in range(N)]
POS = [{b: np.array(v) for b, v in r[str(f)]['pos'].items()} for f in range(N)]
ROOT = [r[str(f)]['pose'].get('root', {'loc': [0, 0, 0]})['loc'] for f in range(N)]
print('root loc f0', ROOT[0], 'pose keys', list(r['0']['pose'].keys()))
LOW = {'l': ['upper_arm_d_l', 'forearm_d_l', 'hand_d_l'], 'r': ['upper_arm_d_r', 'forearm_d_r', 'hand_d_r']}
DELAY, AMP_R, ABD, ABD_R = 2, 0.82, 14.0, 19.0


def qmean(Ms):
    qs = [m2q(M) for M in Ms]; q0 = qs[0]
    acc = sum((q if np.dot(q, q0) >= 0 else -q) for q in qs); return q2m(acc / np.linalg.norm(acc))


rel = {b: [AB[f]['spine_03'].T @ AB[f][b] for f in range(N)] for s in LOW for b in LOW[s]}
mean = {b: qmean(rel[b]) for b in rel}
foot_l = [POS[f]['foot_l'] for f in range(N)]; foot_r = [POS[f]['foot_r'] for f in range(N)]
STANCE = {'r': list(range(9, 24)), 'l': list(range(26, 34)) + list(range(0, 7))}


def xcorr(side):
    """x correction per frame: stance -> contact x minus current x; 4 frames after lift-off fade out"""
    fp = foot_l if side == 'l' else foot_r; st = STANCE[side]; x0 = fp[st[0]][0]
    c = {f: x0 - fp[f][0] for f in st}
    last = c[st[-1]]
    for k in range(1, 5):
        c[(st[-1] + k) % N] = last * (1 - k / 5)
    return c


XC = {s: xcorr(s) for s in 'lr'}
FALLS = [10, 27]  # right heel 0.4167, left heel 1.125
# footfall events (integrate2_cyclops 2026-11-23, one per foot at the measured heel contacts = FALLS / 24); cyclops.gd thuds
# on every event whose name starts with "step". keys_walk.rest_v2.json still carries the old single {step: 0.4}: replaced here.
EVENTS = {'step_r': round(FALLS[0] / 24, 4), 'step_l': round(FALLS[1] / 24, 4)}
assert EVENTS == {'step_r': 0.4167, 'step_l': 1.125}


def pulse(f, lag=2.5, width=3.0):
    """0..1 bump peaking lag frames after each footfall (cyclic)"""
    v = 0.0; sgn = 0.0
    for i, ff in enumerate(FALLS):
        d = (f - ff - lag) % N
        if d > N / 2: d -= N
        b = math.exp(-(d / width) ** 2); v += b; sgn += b * (1 if i == 0 else -1)
    return v, sgn


fin = {}
for f in range(N):
    A = dict(AB[f]); S3 = A['spine_03']
    fd = (f - DELAY) % N
    for s in 'lr':
        for b in LOW[s]:
            R = rel[b][fd]
            if s == 'r': R = slerp(mean[b], R, AMP_R)
            A[b] = S3 @ R
        Rout = S3 @ rot_xyz(0, -ABD if s == 'l' else ABD_R, 0) @ S3.T
        A = rot_chain(A, LOW[s][0], Rout)
    # club arm: dip + roll after footfalls
    v, sg = pulse(f)
    fa = POS[f]['hand_u_r'] - POS[f]['forearm_u_r']; fa /= np.linalg.norm(fa)
    roll = sg * 5.0
    K = np.array([[0, -fa[2], fa[1]], [fa[2], 0, -fa[0]], [-fa[1], fa[0], 0]]); th = math.radians(roll)
    Rroll = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
    A['hand_u_r'] = Rroll @ A['hand_u_r']
    A = rot_chain(A, 'forearm_u_r', S3 @ rot_xyz(-4.0 * v, 0, 0) @ S3.T)
    # stance foot x pin
    for s in 'lr':
        if f in XC[s]:
            tgt = POS[f]['foot_' + s].copy(); tgt[0] += XC[s][f]
            A = leg_ik(A, POS[f], s, tgt)
    fin[f] = pose_dict(A, {'loc': ROOT[f]}, note=f'animfix 2026-11-23 walk frame {f}: read-back of walk_n (k* keys, *.rest_v2.json) + lower arms abducted 14/delayed 2 frames/right x0.82, club dip+roll after footfalls, stance-foot x pinned (IK)')
chk = resolve([{'id': str(f), 'pose': p} for f, p in fin.items()], 'walk_c')
for s in 'lr':
    xs = [chk[str(f)]['pos']['foot_' + s][0] for f in STANCE[s]]; xo = [POS[f]['foot_' + s][0] for f in STANCE[s]]
    print(s, 'stance foot x range new %.3f old %.3f' % (np.ptp(xs), np.ptp(xo)))
for f in (0, 10, 17, 27):
    q = chk[str(f)]['pos']; print(f, 'hand_d_l', np.round(q['hand_d_l'], 2), 'hand_d_r', np.round(q['hand_d_r'], 2), 'hips', np.round(q['hips'], 2))
if WRITE:
    os.makedirs(Dd + 'poses_walk', exist_ok=True)
    for f, p in fin.items(): json.dump(p, open(Dd + f'poses_walk/f{f:02d}.json', 'w'), indent=1)
    K = json.load(open(Dd + 'keys_walk.rest_v2.json'))
    K['events'] = dict(EVENTS)
    K['note_integrate2'] = ('integrate2_cyclops 2026-11-23: one footfall event per foot at the measured heel contacts of the natural walk '
                            '(GLB, lowest foot vertex reaches the floor: right 0.4167 s = frame 10, left 1.125 s = frame 27 at 24 fps); replaces '
                            'the single `step` 0.40 (+ half the clip). cyclops.gd thuds on every event named step*. (Carried into build_walk.py by clip fix 2.)')
    K['keys'] = [{'t': round(f / 24, 4), 'pose_file': f'poses_walk/f{f:02d}.json'} for f in range(N)]
    K['note_animfix2'] = ('2026-11-23 animfix (cyclops): keys = 34 per-frame read-backs of the walk_n bake (the authored k*.json keys and '
                          'keys_walk.rest_v2.json stay as the source) with: lower arms abducted 14 (left) / 19 (right) deg and delayed 2 frames (right amplitude x0.82), '
                          'club dip 4 deg + roll +-5 deg 2-3 frames after each footfall, stance-foot x pinned by leg IK (hip sway no longer drags the planted foot). '
                          'Generator: art_src/chars/cyclops/scripts/animfix2/build_walk.py. Length, loop, move_speed unchanged; events = EVENTS (step_r/step_l).')
    json.dump(K, open(Dd + 'keys_walk.json', 'w'), indent=1)
    print('written')
