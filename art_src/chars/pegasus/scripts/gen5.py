"""Pegasus fly v5 / glide v5 (feedback 2 Pegasus RE-FIXER, 2026-11-23). Successor of gen4.py (same folder).
Reads the v3 absolute pose files (fx_k*.json) of BOTH clips and writes poses_<clip>/f5_k*.json + keys_<clip>.v5.json.
What changed against v4 (reviewer findings, docs/notes/feedback2_pegasus.md "Re-fix"):
- hind legs stretched back in line with the chase camera (thigh 38, gaskin 96, cannon 90, hoof 102, side panel, body frame)
  instead of trailing down (14/68/46/74); forelegs tucked like a jumping horse (20/-88/62/88).
- fly upstroke FOLDED: the hand (wing_02, wing_03 + all feather groups) swept back 60 deg and down 15 deg about the
  wrist, peak at mid-upstroke, open again 2 frames before the top; the feather groups trail a further 20 deg.
- glide wing SHAPE taken from the flat, spread fly downstroke frame at the level point (not the v3 glide curtain);
  +10 deg elevation, 3 deg breath, 0.125 s right-wing lag kept; primaries roll +-3 deg alternately, tip flex 2 deg.
- stroke timing: downstroke 0.625 s (15 fr), upstroke 0.417 s (10 fr); each half is half sine-ease, half power curve
  so the wing arrives at the bottom with speed (no 0.26 s bottom dwell) and leaves it at once.
- neck stretched forward (absolute rx targets, same in fly and glide, half of the v3 life kept), head counter-turned
  so the muzzle is ~20 deg below level; constant 9 deg nose-down body pitch (root.rot) in BOTH clips (a constant: the
  fly<->glide crossfade still does not rock).
usage: python3 gen5.py fly|glide [--write]
"""
import json, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pk import *

REPO = os.path.expanduser('~/HerculesGame')
clip = sys.argv[1]
CL = f'{REPO}/art_src/chars/pegasus/clips'
D = f'{CL}/{clip}'


def load(c):
    k = json.load(open(f'{CL}/{c}/keys_{c}.v3.json'))
    return k, [json.load(open(f"{CL}/{c}/{x['pose_file']}")) for x in k['keys']]


keys, src = load(clip)
fkeys, fsrc = (keys, src) if clip == 'fly' else load('fly')
L = keys['length']; FL = fkeys['length']
N = len(src); FN = len(fsrc)
WING = {s: [f'wing_{s}_01', f'wing_{s}_02', f'wing_{s}_03', f'wing_{s}_feather_01', f'wing_{s}_feather_02',
            f'wing_{s}_feather_03'] for s in 'lr'}
HAND = lambda s: WING[s][1:]                       # rotated about the wrist (wing_02 head)
FEATH = lambda s: WING[s][3:]


def m2q(M):
    t = np.trace(M)
    if t > 0:
        S = math.sqrt(t + 1) * 2; return np.array([0.25 * S, (M[2,1]-M[1,2])/S, (M[0,2]-M[2,0])/S, (M[1,0]-M[0,1])/S])
    i = int(np.argmax([M[0,0], M[1,1], M[2,2]]))
    if i == 0:
        S = math.sqrt(1 + M[0,0] - M[1,1] - M[2,2]) * 2
        return np.array([(M[2,1]-M[1,2])/S, 0.25*S, (M[0,1]+M[1,0])/S, (M[0,2]+M[2,0])/S])
    if i == 1:
        S = math.sqrt(1 + M[1,1] - M[0,0] - M[2,2]) * 2
        return np.array([(M[0,2]-M[2,0])/S, (M[0,1]+M[1,0])/S, 0.25*S, (M[1,2]+M[2,1])/S])
    S = math.sqrt(1 + M[2,2] - M[0,0] - M[1,1]) * 2
    return np.array([(M[1,0]-M[0,1])/S, (M[0,2]+M[2,0])/S, (M[1,2]+M[2,1])/S, 0.25*S])


def q2m(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


def slerp(q0, q1, u):
    d = float(np.dot(q0, q1))
    if d < 0: q1, d = -q1, -d
    if d > 0.9995: return (q0 + u * (q1 - q0)) / np.linalg.norm(q0 + u * (q1 - q0))
    th = math.acos(d); return (math.sin((1-u)*th)*q0 + math.sin(u*th)*q1) / math.sin(th)


def axis_rot(axis, deg):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a); th = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def chain_at(S, fi, s):
    n = len(S); i0 = int(math.floor(fi)) % n; i1 = (i0 + 1) % n; u = fi - math.floor(fi)
    return {b: q2m(slerp(m2q(mat(S[i0]['bones'][b])), m2q(mat(S[i1]['bones'][b])), u)) for b in WING[s]}


def joints(ms, s):
    """shoulder, wrist, hand tip (world, body frame) of a wing chain"""
    p0 = np.array(B[f'wing_{s}_01']['head'], float)
    p1 = p0 + ms[WING[s][0]] @ rest_vec(WING[s][0])
    p2 = p1 + ms[WING[s][1]] @ rest_vec(WING[s][1])
    p3 = p2 + ms[WING[s][2]] @ rest_vec(WING[s][2])
    return p0, p1, p2, p3


def chain_elev(ms, s):
    p0, _, _, p3 = joints(ms, s); d = p3 - p0
    return math.degrees(math.atan2(d[2], abs(d[0])))


def elev_pose(p, s):
    return chain_elev({b: mat(p['bones'][b]) for b in WING[s]}, s)


def ease(u): return (1 - math.cos(math.pi * max(0.0, min(1.0, u)))) / 2


# ---------------------------------------------------------------- stroke
TOP, BOT = 50.0, -30.0
T_DOWN = 0.625            # 15 frames down, 10 frames up (L = 1.0417)
def fly_target(t):
    t = t % FL
    if t <= T_DOWN:
        u = t / T_DOWN; f = 0.5 * ease(u) + 0.5 * u ** 1.4            # arrives at the bottom with speed
        return TOP - (TOP - BOT) * f, 'down', u
    u = (t - T_DOWN) / (FL - T_DOWN); f = 0.5 * ease(u) + 0.5 * (1 - (1 - u) ** 1.4)   # leaves the bottom at once
    return BOT + (TOP - BOT) * f, 'up', u


SEG = {'down': (0, 15), 'up': (15, 25)}   # v3 fly source: top -> bottom, bottom -> top
def src_frame(s, phase, prog):
    a, b = SEG[phase]
    e = [elev_pose(fsrc[i % FN], s) for i in range(a, b + 1)]
    lo, hi = min(e), max(e)
    want = hi - prog * (hi - lo) if phase == 'down' else lo + prog * (hi - lo)
    for j in range(len(e) - 1):
        e0, e1 = e[j], e[j+1]
        if (min(e0, e1) - 1e-6) <= want <= (max(e0, e1) + 1e-6) and abs(e1 - e0) > 1e-6:
            return a + j + (want - e0) / (e1 - e0)
    return a if (phase == 'down') == (prog < 0.5) else b


def fold_w(u):
    """upstroke fold weight: starts once the wrist is above the rider's thighs (u 0.25), full 0.5-0.7 (mid/late
    upstroke), open again by u 0.85 (the last 2 frames before the top). A fold that started at the bottom hit the
    seated rider's thighs/skirt on frames 17-19 (pair_check r2 #1)."""
    if u < FOLD_START: return 0.0
    if u < 0.4: return ease((u - FOLD_START) / (0.4 - FOLD_START))
    if u < 0.7: return 1.0
    return ease((0.85 - u) / 0.15) if u < 0.85 else 0.0


# how much of the hand's BACK sweep each feather group follows: the inner secondaries (feather_01, 02 on wing_02)
# already point back, a full back sweep would swing them INWARD into the rider; the primaries (feather_03) fold fully
FEATHER_FOLLOW = (0.45, 0.75, 1.0)
FOLD_START = float(os.environ.get('FOLD_START', '0.1'))


FOLD_BACK, FOLD_DOWN, FEATHER_TRAIL = 55.0, 15.0, 8.0
GLIDE_SHAPE_PROG = 0.6       # fly downstroke progress of the flat, spread, level-ish wing (reviewer: fly k07-k08)


def apply_hand(ms, s, back, down, feather_extra=0.0, feather_roll=None):
    p0, p1, _, _ = joints(ms, s)
    a = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.cross(a, [0, 1, 0]); n /= np.linalg.norm(n)              # +angle sweeps the hand BACK (+Y), both sides
    m = np.cross([0, 0, 1], a); m /= np.linalg.norm(m)              # +angle bends the hand DOWN, both sides
    Q = axis_rot(m, down) @ axis_rot(n, back)
    out = dict(ms)
    for b in HAND(s): out[b] = Q @ ms[b]
    if back:
        for i, b in enumerate(FEATH(s)):
            out[b] = axis_rot(m, down) @ axis_rot(n, back * FEATHER_FOLLOW[i]) @ ms[b]
    if feather_extra or feather_roll:
        for i, b in enumerate(FEATH(s)):
            R = axis_rot(Q @ n, feather_extra * FEATHER_FOLLOW[i])
            if feather_roll: R = axis_rot(Q @ a, feather_roll[i] * (1 if s == 'l' else -1)) @ R
            out[b] = R @ out[b]
    return out


def tip_flex(ms, s, deg):
    """bend wing_03 + feather_03 down about the wing_03 head"""
    _, p1, _, _ = joints(ms, s)
    p0 = np.array(B[f'wing_{s}_01']['head'], float); a = (p1 - p0) / np.linalg.norm(p1 - p0)
    m = np.cross([0, 0, 1], a); m /= np.linalg.norm(m)
    Q = axis_rot(m, deg); out = dict(ms)
    for b in (WING[s][2], WING[s][5]): out[b] = Q @ ms[b]
    return out


def wing_pose(t, s, lag=0.0, amp=1.0):
    if clip == 'fly':
        tgt, phase, prog = fly_target(t - lag)
        mean = (TOP + BOT) / 2; tgt = mean + (tgt - mean) * amp
        ms = chain_at(fsrc, src_frame(s, phase, prog), s)
        if phase == 'up':
            w = fold_w(prog)
            ms = apply_hand(ms, s, FOLD_BACK * w, FOLD_DOWN * w, FEATHER_TRAIL * w)
    else:
        tt = t - lag
        tgt = 10.0 + 3.0 * math.sin(2 * math.pi * 2 * tt / L)
        ms = chain_at(fsrc, src_frame(s, 'down', GLIDE_SHAPE_PROG), s)
        roll = [3.0 * math.sin(2 * math.pi * 3 * tt / L + i * math.pi) for i in range(3)]   # alternating corrections
        ms = apply_hand(ms, s, 0.0, 0.0, 0.0, roll)
        ms = tip_flex(ms, s, 2.0 * math.sin(2 * math.pi * 2 * tt / L + 1.1))
    d = tgt - chain_elev(ms, s)
    Q = Ry(-d if s == 'l' else d)            # left wing (+X): +Ry lowers it; right wing (-X): +Ry raises it
    return {b: Q @ ms[b] for b in WING[s]}, tgt


# ---------------------------------------------------------------- legs / tail / neck / body
def legs(t):
    pad = 1.0 if clip == 'fly' else 0.7
    cyc = 1 if clip == 'fly' else 2
    ph = 2 * math.pi * cyc * t / L
    out = {}
    for side, lagf in (('l', 0.0), ('r', 0.0625)):
        p = ph - 2 * math.pi * cyc * lagf / L
        out[f'leg_f{side}_01'] = {'side': 20 + 5 * pad * math.sin(p)}
        out[f'leg_f{side}_02'] = {'side': -88 + 8 * pad * math.sin(p + 0.6)}
        out[f'leg_f{side}_03'] = {'side': 62 + 8 * pad * math.sin(p + 1.0)}
        out[f'hoof_f{side}'] = {'side': 88 + 10 * pad * math.sin(p + 2.2)}   # lags the cannon: visible fetlock flex
    for side, lagf in (('l', 0.042), ('r', 0.1)):
        p = ph + math.pi - 2 * math.pi * cyc * lagf / L
        out[f'leg_b{side}_01'] = {'side': 38 + 4 * pad * math.sin(p)}
        out[f'leg_b{side}_02'] = {'side': 96 + 5 * pad * math.sin(p + 0.5)}
        out[f'leg_b{side}_03'] = {'side': 90 + 6 * pad * math.sin(p + 0.9)}
        out[f'hoof_b{side}'] = {'side': 102 + 6 * pad * math.sin(p + 1.2)}
    return out


def tail(t):
    cyc = 1 if clip == 'fly' else 2
    ph = 2 * math.pi * cyc * t / L
    base = [122, 110, 100, 94, 91]; amp = [2, 4, 6, 8, 10] if clip == 'fly' else [3, 4.5, 6, 7.5, 9]
    return {f'tail_0{i+1}': {'side': base[i] + amp[i] * math.sin(ph - 0.7 * i - 0.8)} for i in range(5)}


PITCH = 9.0                                   # constant nose-down body pitch (root.rot rx +), both clips
NECK_T = {'neck_01': 21.0, 'neck_02': 19.0, 'neck_03': 17.0, 'head': -28.0}   # absolute rx targets (body frame)
neck_mean = {b: sum(p['bones'][b]['rx'] for p in src) / N for b in NECK_T}

# ---------------------------------------------------------------- build
outkeys = []; rep = []
for i, k in enumerate(keys['keys']):
    t = k['t']; p = json.loads(json.dumps(src[i]))
    for s, lag, amp in (('l', 0.0, 1.0), ('r', 1.0 / 24 if clip == 'fly' else 0.125, 0.97 if clip == 'fly' else 1.0)):
        wb, tgt = wing_pose(t, s, lag, amp)
        p['bones'].update({b: dec(M) for b, M in wb.items()})
        p0, p1, p2, p3 = joints(wb, s)
        tips = [p3] + [joints(wb, s)[1] + wb[WING[s][1]] @ (np.array(B[b]['head']) - np.array(B[WING[s][1]]['head']))
                       + wb[b] @ rest_vec(b) for b in (WING[s][3], WING[s][4])]
        rep.append((i, round(t, 3), s, round(tgt, 1), 'span', round(max(abs(x[0]) for x in tips + [p2]), 3),
                    'tipz', round(min(x[2] for x in tips), 2), 'p3z', round(p3[2], 2), 'p3x', round(abs(p3[0]), 2)))
    for n, v in legs(t).items(): p['bones'][n] = {k2: round(v2, 3) for k2, v2 in v.items()}
    for n, v in tail(t).items(): p['bones'][n] = {k2: round(v2, 3) for k2, v2 in v.items()}
    for n, tv in NECK_T.items():
        life = 0.5 * (p['bones'][n]['rx'] - neck_mean[n])
        if clip == 'glide':   # glide v3 neck barely moves: a slow 2-per-loop reach, lagging down the neck (small corrections)
            life += {'neck_01': 2.0, 'neck_02': 3.0, 'neck_03': 3.5, 'head': -3.0}[n] * math.sin(2 * math.pi * 2 * t / L - 0.5 * list(NECK_T).index(n))
        p['bones'][n]['rx'] = round(tv + life, 3)
    if clip == 'fly': p['root']['loc'][2] = round(p['root']['loc'][2] * 1.5, 5)
    p['root']['rot'] = [PITCH, 0, 0]
    p['fix5'] = 'v5 (feedback2 pegasus re-fixer 2026-11-23): legs stretched/tucked, ' + \
        ('upstroke fold, timing 0.625/0.417' if clip == 'fly' else 'flat spread wing shape from fly') + \
        ', neck stretched, 9 deg nose-down'
    fn = f'poses_{clip}/f5_k{i:02d}.json'
    if '--write' in sys.argv: json.dump(p, open(f'{D}/{fn}', 'w'), indent=1)
    outkeys.append({'t': t, 'pose_file': fn})
nk = {x: keys[x] for x in keys if x not in ('keys', 'fix4')}
nk['fix5'] = {'by': 'feedback2 pegasus re-fixer 2026-11-23', 'base_keys': f'keys_{clip}.v3.json (fx_k*.json)',
              'tool': 'art_src/chars/pegasus/scripts/gen5.py', 'pitch_deg': PITCH,
              'wing': ('fly: +50 top -> -30 bottom, down 0.625 s / up 0.417 s, upstroke fold back %g down %g feathers %g'
                       % (FOLD_BACK, FOLD_DOWN, FEATHER_TRAIL)) if clip == 'fly' else
                      'glide: fly downstroke shape at progress %g, +10 +-3 deg, primaries roll +-3, tip flex 2' % GLIDE_SHAPE_PROG}
nk['keys'] = outkeys
if '--write' in sys.argv: json.dump(nk, open(f'{D}/keys_{clip}.v5.json', 'w'), indent=1)
for r in rep:
    if r[2] == 'l': print(r)
