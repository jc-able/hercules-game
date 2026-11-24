"""medusa idle v2 (animfix2 2026-11-23): natural stance + layered motion, sampled into key pose files.
Based on work/anim2/medusa_idle_n/gen.py. Changes (review finding: one fast lurch, whole body snapping back in unison):
- the S-curve weight shift is smaller (lean_k) and eases out over 1.2 s instead of 0.75 s;
- the body groups follow each other: pelvis + upright tail lead, chest +0.1 s, shoulders +0.15, neck/head +0.2,
  arms +0.25..0.3, snakes +0.35 (plus a trailing term so they lag the head);
- a smaller counter-shift toward her LEFT over 4.2-6.0 s, so something beyond breathing is always under way.
Every delta is exactly 0 at t=0 and t=T (frame 0 = natural_pose.json, exact seam).
usage: python3 idle_gen.py idle_params.json -> art_src/chars/medusa/clips/idle_n/poses_idle/k##.json + keys_idle.json"""
import json, math, os, sys, copy
REPO = os.path.expanduser('~/HerculesGame')
CLIP = REPO + '/art_src/chars/medusa/clips/idle_n'
P = json.load(open(sys.argv[1]))
NAT = json.load(open(REPO + '/art_src/chars/medusa/natural_pose.json'))
T = P['T']; DT = P['dt']
OUT = CLIP + '/poses_idle'; os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi


def bump(t, a, b, c, d):
    """0 before a, eases to 1 at b, holds to c, eases to 0 at d"""
    if t <= a or t >= d: return 0.0
    if t < b: return (1 - math.cos(math.pi * (t - a) / (b - a))) / 2
    if t <= c: return 1.0
    return (1 + math.cos(math.pi * (t - c) / (d - c))) / 2


def wave(t, cyc, ph):
    """periodic over T, exactly 0 at t=0"""
    return math.sin(TAU * cyc * t / T + ph) - math.sin(ph)


def add(p, bone, **kw):
    b = p['bones'].setdefault(bone, {'space': 'local_delta'})
    for k, v in kw.items():
        b[k] = round(b.get(k, 0.0) + v, 3)


def LS(t, off):
    """weight-shift curve of a body group that follows the lead by `off` seconds: lean to her RIGHT (+1),
    then a smaller counter-shift to her LEFT (negative)"""
    return P['lean_k'] * (bump(t - off, *P['lean_win']) - P['counter'] * bump(t - off, *P['counter_win']))


def pose_at(t):
    p = copy.deepcopy(NAT)
    p.pop('_note', None)
    ch = p['chain']
    for k in ('rx', 'ry', 'rz'):
        ch[k] = (ch.get(k) or []) + [0.0] * (14 - len(ch.get(k) or []))
    O = P['offsets']
    L0 = LS(t, O['pelvis']); Lc = LS(t, O['chest']); Lsh = LS(t, O['shoulders']); Lh = LS(t, O['head'])
    Lar = LS(t, O['arm_r']); Lar2 = LS(t, O['arm_r'] + 0.05); Lal = LS(t, O['arm_l']); Lsn = LS(t, O['snakes'])
    B = (1 - math.cos(TAU * t / P['breath'])) / 2       # breath: 0 = exhaled, 1 = full (peaks at 1.5, 4.5)
    H = bump(t, *P['look_win'])                        # head look to her left
    F1 = bump(t, *P['flick1']); F2 = bump(t, *P['flick2'])
    F = P['flick1_amp'] * F1 + F2
    Fl = P['flick1_amp'] * bump(t - 0.12, *P['flick1']) + bump(t - 0.12, *P['flick2'])   # lagging whip
    C = bump(t, *P['curl1']) + 0.7 * bump(t, *P['curl2'])                                 # right hand curl
    Pm = bump(t, *P['palm'])                                                             # left palm turn
    # trunk: S-curve lean (pelvis pivot: hips go left, chest/head right) + breath; each group on its own delay
    p['bones']['pelvis']['ry'] = round(p['bones']['pelvis']['ry'] + P['pelvis_ry'] * L0, 3)
    for b, v in zip(['spine_01', 'spine_02', 'spine_03'], P['spine_ry']):
        add(p, b, ry=v * Lc)
    add(p, 'spine_02', rx=-P['breath_spine'] * B)
    add(p, 'spine_03', rx=-P['breath_spine'] * B, rz=P['spine_twist'] * Lc)
    add(p, 'neck', ry=P['neck_ry'] * Lh, rz=P['look_neck'] * H + P['lean_turn'] * Lh * 0.4)
    add(p, 'head', ry=P['head_ry'] * Lh, rz=P['look_head'] * H + P['lean_turn'] * Lh * 0.6,
        rx=P['breath_head'] * B + P['look_nod'] * H)
    # shoulders: lift with breath, the lean side drops
    add(p, 'shoulder_l', ry=-P['breath_sh'] * B - P['lean_sh'] * Lsh)
    add(p, 'shoulder_r', ry=P['breath_sh'] * 0.8 * B - P['lean_sh'] * Lsh)
    # right arm hangs loose: lags the lean, elbow breathes, wrist curls
    ua = p['bones']['upper_arm_r']; fa = p['bones']['forearm_r']; ha = p['bones']['hand_r']
    # pendulum lag: while the shoulders travel, the hanging hand trails them (absolute aim tilts against the travel)
    drag = Lsh - LS(t, O['shoulders'] + P['drag_lag'])
    ua['front'] = round(ua['front'] + P['arm_r_lean'] * Lar + 1.5 * wave(t, 1, 0.8) - P['drag'] * drag, 3)
    ua['side'] = round(ua['side'] + 2.0 * wave(t, 1, 2.0), 3)
    fa['side'] = round(fa['side'] - P['elbow_r'] * B + P['arm_r_lean'] * 0.5 * Lar2, 3)
    fa['front'] = round(fa['front'] + P['arm_r_lean'] * Lar2 - P['drag'] * 1.3 * (LS(t, O['arm_r']) - LS(t, O['arm_r'] + P['drag_lag'])), 3)
    ha['side'] = round(ha['side'] - P['curl'] * C, 3)
    ha['twist'] = round(ha['twist'] - 8 * C, 3)
    # left raised forearm: palm turns, forearm floats with the breath
    ul = p['bones']['upper_arm_l']; fl = p['bones']['forearm_l']; hl = p['bones']['hand_l']
    ul['side'] = round(ul['side'] - 3 * B + 2 * wave(t, 1, 1.2), 3)
    ul['front'] = round(ul['front'] - P['arm_l_lean'] * Lal - 0.5 * P['drag'] * drag, 3)
    fl['side'] = round(fl['side'] - 4 * B + 3 * wave(t, 1, 2.6), 3)
    fl['front'] = round(fl['front'] - P['arm_l_lean'] * 0.6 * Lal, 3)
    hl['twist'] = round(hl['twist'] + P['palm_twist'] * Pm, 3)
    hl['side'] = round(hl['side'] + 8 * Pm - 4 * B, 3)
    # hair snakes: separate phases, rates and amplitudes + trail behind the head's lean (follow-through)
    lag = P['snake_trail'] * (Lh - Lsn)
    for n, (amp, cyc, ph) in P['hair'].items():
        add(p, n, rx=amp * wave(t, cyc, ph), rz=0.8 * amp * wave(t, cyc, ph + 1.3),
            ry=0.5 * amp * wave(t, 1, ph * 1.7) + lag)
    # tail: S-curve support (net turn 0 below tail_04), floor tail stays put, tip flicks (leads with the pelvis)
    for i, v in enumerate(P['tail_lean_ry']): ch['ry'][i] += v * L0
    for i, v in enumerate(P['tail_lean_rx']): ch['rx'][i] += v * L0
    ch['rz'][4] += P['tail05_rz'] * L0; ch['rz'][6] -= P['tail05_rz'] * L0
    for k in range(5, 11):
        ch['rz'][k] += P['tail_wave'] * wave(t, 1, -0.7 * (k - 5))
    for i, v in zip([10, 11, 12], P['flick_rx']): ch['rx'][i] += v * F
    for i, v in zip([11, 12, 13], P['flick_rz']): ch['rz'][i] += v * Fl
    for k in ('rx', 'ry', 'rz'): ch[k] = [round(x, 3) for x in ch[k]]
    p['root']['loc'] = [round(P['root_shift'][0] * L0, 4), round(P['root_shift'][1] * L0, 4), 0]
    p['view_offset'] = P['view_offset']
    return p


n = int(round(T / DT))
keys = []
for i in range(n):
    t = round(i * DT, 4)
    fn = os.path.join(OUT, 'k%02d.json' % i)
    json.dump(pose_at(t), open(fn, 'w'), indent=1)
    keys.append({'t': t, 'pose_file': fn})
json.dump({'fps': 24, 'loop': True, 'length': T, 'events': {}, 'keys': keys,
           'note': 'idle from video idle_n, window 3.75-9.75 s (clip t = video t - 3.75). Frame 0 = natural_pose.json exactly. '
                   'v2 (animfix2 2026-11-23): smaller, staggered weight shift with a 1.2 s ease-out and a counter-shift; '
                   'built by work/animfix2_medusa/idle_gen.py + idle_params.json (v1: work/anim2/medusa_idle_n/gen.py)'},
          open(CLIP + '/keys_idle.json', 'w'), indent=1)
print('ok', n, 'keys')
