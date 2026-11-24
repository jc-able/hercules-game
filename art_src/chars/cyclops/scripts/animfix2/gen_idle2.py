#!/usr/bin/env python3
"""Author the cyclops idle (video idle_n) as layered motion on top of the natural stance.
Every key = natural_pose.json + per-group deltas (sines with periods 6/3/2 s that divide the loop).
Planted feet: per key a small Newton solve (via `ak solve`) of thigh rx/ry + shin rx so both ankles stay where the
natural stance puts them while the pelvis sways.
usage: python3 gen.py <out_dir_for_pose_files> [amp_scale]

clip fix 2 (2026-11-23, copy of work/anim2/cyclops_idle_n/gen.py): the idle read as a still picture from the chase camera
at the start of the fight (giant ~20-24 m away, ~5 cm per pixel): amplitudes raised per group (factors below), every term
still 0 at t=0 and t=6 (first = last pose = natural_pose.json, unchanged). Solve scratch moved to work/clipfix2_cyclops/solve.
usage: python3 gen_idle2.py art_src/chars/cyclops/clips/idle_n/poses_idle"""
import json, math, subprocess, sys, copy, pathlib
from concurrent.futures import ThreadPoolExecutor

REPO = pathlib.Path('~/HerculesGame').expanduser()
AK = str(REPO / 'tools/ak')
CH = str(REPO / 'art_src/chars/cyclops/cyclops.blend')
NAT = json.load(open(REPO / 'art_src/chars/cyclops/natural_pose.json'))
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCR = REPO / 'work/clipfix2_cyclops/solve'; SCR.mkdir(parents=True, exist_ok=True)
L = 6.0                     # loop length (s)
STEP = 0.5                  # key spacing (s)
Z0 = -0.0852                # root z the natural stance gets from ground=lowest
TAU = 2 * math.pi
import os
F = {k: float(os.environ.get('F_' + k, v)) for k, v in
     dict(BREATH=2.0, SHOULDER=3.5, CLUB=3.0, ARM_UL=2.0, ARM_D=2.0, SHIFT=1.4, HEAD=1.5).items()}

def s(per, t, ph=0.0):      # sine that is 0 at t=0 when ph=0
    return math.sin(TAU * t / per + ph) - math.sin(ph)

def deltas(t):
    """per-bone deltas (deg) and root shift at clip time t. All terms are 0 at t=0 and t=L."""
    b = math.sin(TAU * t / 3.0)                 # breath: + = inhale (peaks 0.75 s, 3.75 s)
    w = (1 - math.cos(TAU * t / 6.0)) / 2       # weight shift toward the right leg: 0 -> 1 (3 s) -> 0
    d = {}
    def add(bone, key, v):
        d.setdefault(bone, {}); d[bone][key] = d[bone].get(key, 0.0) + v
    # trunk: chest lifts and straightens on the inhale, pelvis levels as weight centres
    add('hips', 'ry', 6.0 * F['SHIFT'] * w)
    add('spine_01', 'ry', -2.0 * F['SHIFT'] * w); add('spine_01', 'rx', -0.6 * F['BREATH'] * b)
    add('spine_02', 'ry', -6.0 * F['SHIFT'] * w); add('spine_02', 'rx', -2.0 * F['BREATH'] * b)
    add('spine_03', 'ry', -3.0 * F['SHIFT'] * w); add('spine_03', 'rx', -2.6 * F['BREATH'] * b); add('spine_03', 'rz', 2.0 * F['HEAD'] * s(6, t, 0.6))
    # head: slow look left (1.5 s) then right (4.5 s), small nod against the breath, tilt with the shift
    add('neck', 'rz', 3.0 * F['HEAD'] * math.sin(TAU * t / 6.0)); add('neck', 'rx', 1.2 * F['BREATH'] * b)
    add('head', 'rz', 7.0 * F['HEAD'] * s(6, t, -0.35)); add('head', 'rx', 2.0 * F['HEAD'] * s(3, t, 1.2)); add('head', 'ry', -2.0 * F['SHIFT'] * w)
    # shoulders rise on the inhale (lateral bones: left front more negative = up, right more positive = up)
    add('shoulder_u_l', 'front', -3.0 * F['SHOULDER'] * s(3, t, -0.25))
    add('shoulder_u_r', 'front', 3.0 * F['SHOULDER'] * s(3, t, -0.15))
    # club arm: the club bobs a little behind the breath, the grip shifts
    add('upper_arm_u_r', 'side', 2.0 * F['CLUB'] * s(3, t, -0.6)); add('upper_arm_u_r', 'front', 1.5 * F['CLUB'] * s(6, t, 0.4))
    add('forearm_u_r', 'side', -2.0 * F['CLUB'] * s(3, t, -0.9))
    add('hand_u_r', 'twist', 4.0 * F['CLUB'] * s(2, t, 0.3))
    # upper left arm: hangs bent, sways with lag down the chain
    add('upper_arm_u_l', 'side', 4.0 * F['ARM_UL'] * s(6, t, -0.5)); add('upper_arm_u_l', 'front', -2.0 * F['ARM_UL'] * s(3, t, 0.2))
    add('forearm_u_l', 'side', 7.0 * F['ARM_UL'] * s(6, t, -1.1)); add('forearm_u_l', 'front', -2.5 * F['ARM_UL'] * s(3, t, -0.4))
    add('hand_u_l', 'side', 9.0 * F['ARM_UL'] * s(6, t, -1.7)); add('hand_u_l', 'twist', 8.0 * s(2, t, 0.9))
    # lower arms: loose in front of the hips, each its own phase; hands flex (no finger bones: wrist + twist)
    add('upper_arm_d_l', 'side', 3.5 * F['ARM_D'] * s(6, t, 0.8)); add('upper_arm_d_l', 'front', -2.0 * F['ARM_D'] * w)
    add('forearm_d_l', 'side', 6.0 * F['ARM_D'] * s(6, t, 0.2)); add('forearm_d_l', 'front', 2.0 * F['ARM_D'] * s(3, t, 1.5))
    add('hand_d_l', 'side', 12.0 * s(3, t, 0.0)); add('hand_d_l', 'twist', 12.0 * s(2, t, 0.0))
    add('upper_arm_d_r', 'side', 3.0 * F['ARM_D'] * s(6, t, 2.6)); add('upper_arm_d_r', 'front', 1.5 * F['ARM_D'] * w)
    add('forearm_d_r', 'side', 5.0 * F['ARM_D'] * s(6, t, 2.1)); add('forearm_d_r', 'front', -2.0 * F['ARM_D'] * s(3, t, 2.4))
    add('hand_d_r', 'side', 10.0 * s(3, t, 1.9)); add('hand_d_r', 'twist', -12.0 * s(2, t, 1.1))
    root_dx = -0.12 * F['SHIFT'] * w            # pelvis sways toward the right foot
    root_dz = -0.035 * F['SHIFT'] * w           # and settles a little as the knees soften
    return d, root_dx, root_dz

def build(t, legs):
    p = copy.deepcopy(NAT); p.pop('_note', None)
    d, dx, dz = deltas(t)
    for bone, kv in d.items():
        e = p['bones'].setdefault(bone, {})
        for k, v in kv.items():
            e[k] = round(e.get(k, 0.0) + v, 3)
    for (bone, key), v in legs.items():
        p['bones'].setdefault(bone, {})[key] = round(v, 4)
    p['root'] = {'loc': [round(0.25 + dx, 4), 0, round(Z0 + dz, 4)]}
    return p

def solve(p, tag):
    f = SCR / f'{tag}.json'; f.write_text(json.dumps(p))
    r = subprocess.run([AK, 'solve', CH, '--pose', str(f)], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('###AK###')][-1]
    j = json.loads(line[9:]); return j

def ankles(j):
    return [j['bones']['foot_l']['head'], j['bones']['foot_r']['head']]

PARAMS = [('thigh_l', 'rx'), ('thigh_l', 'ry'), ('shin_l', 'rx'), ('thigh_r', 'rx'), ('thigh_r', 'ry'), ('shin_r', 'rx')]
NATP = {k: NAT['bones'][k[0]].get(k[1], 0.0) for k in PARAMS}

def lin3(A, b):
    import numpy as np
    return list(np.linalg.lstsq(np.array(A), np.array(b), rcond=None)[0])

def solve_key(t):
    tag = f't{t:05.2f}'
    import os
    if os.environ.get('REUSE_LEGS'):   # legs depend only on root + hips: reuse the solved angles
        f = OUT / f'k{int(round(t / STEP)):02d}.json'; pb = json.load(open(f))['bones']
        legs = {k: pb[k[0]][k[1]] for k in PARAMS}
        j0 = solve(build(t, legs), tag + '_reuse'); a0 = ankles(j0)
        err = max(abs(TARGET[i][c] - a0[i][c]) for i in range(2) for c in range(3))
        return t, legs, err, j0['ground']
    target = TARGET
    legs = dict(NATP)
    for it in range(4):
        j0 = solve(build(t, legs), tag + f'_i{it}')
        a0 = ankles(j0)
        res = [[target[i][c] - a0[i][c] for c in range(3)] for i in range(2)]
        err = max(abs(x) for r in res for x in r)
        if err < 0.008: break
        J = [[None] * 3 for _ in range(2)]
        h = 2.0
        for pi in range(3):   # perturb the same parameter on both legs at once (independent legs)
            lp = dict(legs); lp[PARAMS[pi]] += h; lp[PARAMS[pi + 3]] += h
            a1 = ankles(solve(build(t, lp), tag + f'_i{it}_p{pi}'))
            for leg in range(2):
                J[leg][pi] = [(a1[leg][c] - a0[leg][c]) / h for c in range(3)]
        for leg in range(2):
            A = [[J[leg][pi][c] for pi in range(3)] for c in range(3)]
            dlt = lin3(A, res[leg])
            for pi in range(3):
                legs[PARAMS[pi + 3 * leg]] += max(-8, min(8, dlt[pi]))
    return t, legs, err, j0['ground']

TARGET = ankles(solve(build(0.0, NATP), 'nat'))
if __name__ == '__main__':
    times = [round(i * STEP, 3) for i in range(int(L / STEP))]
    with ThreadPoolExecutor(5) as ex:
        results = list(ex.map(solve_key, times[1:]))
    results.insert(0, (0.0, dict(NATP), 0.0, None))
    keys = []
    for i, (t, legs, err, gr) in enumerate(results):
        p = NAT if t == 0 else build(t, legs)
        p = copy.deepcopy(p)
        p['_note'] = ('natural stance (loop seam)' if t == 0 else
                      f'idle t={t}: natural stance + authored breath/weight-shift/head/arm deltas (clip fix 2 amplitudes {F}); legs solved to plant feet (ankle err {err*1000:.1f} mm)')
        name = f'k{i:02d}.json'
        (OUT / name).write_text(json.dumps(p, indent=1))
        keys.append({'t': t, 'pose_file': name})
        print(f'{name} t={t:4.2f} ankle_err={err*1000:5.1f} mm ground={gr} legs=' + ', '.join(f'{a}.{b}={v:.1f}' for (a, b), v in legs.items()))
    json.dump(keys, open(OUT / '_keys.json', 'w'))
