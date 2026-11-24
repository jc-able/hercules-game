"""Pegasus fly v4 / glide v4 (feedback 2 pegasus fixer, 2026-11-23).
Reads the v3 absolute pose files (fx_k*.json) and writes f4_k*.json + keys_<clip>.v4.json:
- wings (whole chain incl. feathers, rigid): new elevation curve. fly: full eased stroke +50 top -> -30 bottom
  (v3: held ~0.3 s at +41, dropped in 4 frames, held 0.33 s at -62 = 'hanging like legs'); the wing SHAPE of each
  output frame is taken (slerp) from the v3 frame of the same stroke direction and elevation progress, then the chain
  is turned about the body's long axis to the target. glide: spread near level (+10 deg, slow 3 deg breath).
- legs: forelegs tucked (forearm forward, cannon folded back), hind legs trailing back, small paddle on the beat.
- tail: streams back (aim 120..90 deg in the side panel) with a lagged wave, instead of hanging.
- neck: stretched forward (+10/+8/+6 deg lean), head keeps its v3 angle.
- fly root bob x1.5 (peak 0.12 m at the end of the downstroke, same phase as v3).
usage: python3 gen4.py fly|glide [--write]
"""
import json, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pk import *

REPO = os.path.expanduser('~/HerculesGame')
clip = sys.argv[1]
D = f'{REPO}/art_src/chars/pegasus/clips/{clip}'
keys = json.load(open(f'{D}/keys_{clip}.v3.json'))
L = keys['length']
src = [json.load(open(f"{D}/{k['pose_file']}")) for k in keys['keys']]
ts = [k['t'] for k in keys['keys']]
N = len(src)
WING = {s: [f'wing_{s}_01', f'wing_{s}_02', f'wing_{s}_03', f'wing_{s}_feather_01', f'wing_{s}_feather_02',
            f'wing_{s}_feather_03'] for s in 'lr'}

def elev(p, s):
    h = np.array(B[f'wing_{s}_01']['head']); d = chain_tip(p, WING[s][:3]) - h
    return math.degrees(math.atan2(d[2], abs(d[0])))

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

def chain_at(fi, s):
    """wing chain matrices at fractional source frame fi (wraps)"""
    i0 = int(math.floor(fi)) % N; i1 = (i0 + 1) % N; u = fi - math.floor(fi)
    return {n: q2m(slerp(m2q(mat(src[i0]['bones'][n])), m2q(mat(src[i1]['bones'][n])), u)) for n in WING[s]}

def chain_elev(ms, s):
    p = np.array(B[f'wing_{s}_01']['head'], float)
    for n in WING[s][:3]: p = p + ms[n] @ rest_vec(n)
    d = p - np.array(B[f'wing_{s}_01']['head'])
    return math.degrees(math.atan2(d[2], abs(d[0])))

def ease(u): return (1 - math.cos(math.pi * max(0.0, min(1.0, u)))) / 2

# ---------------------------------------------------------------- wing targets
TOP, BOT = 50.0, -30.0
T_DOWN = 0.5833          # downstroke 0 .. 0.583 s (14 frames), upstroke (quicker, 11 frames) back to the top
def fly_target(t):
    t = t % L
    if t <= T_DOWN: return TOP - (TOP - BOT) * ease(t / T_DOWN), 'down', t / T_DOWN
    return BOT + (TOP - BOT) * ease((t - T_DOWN) / (L - T_DOWN)), 'up', (t - T_DOWN) / (L - T_DOWN)

# v3 source segments: down = frames 0..15 (top -> bottom), up = 15..25 (bottom -> top); progress by elevation
SEG = {'down': (0, 15), 'up': (15, 25)}
def src_frame(s, phase, prog):
    a, b = SEG[phase]
    e = [elev(src[i % N], s) for i in range(a, b + 1)]
    lo, hi = min(e), max(e)
    want = hi - prog * (hi - lo) if phase == 'down' else lo + prog * (hi - lo)
    # first crossing along the segment (monotone enough)
    for j in range(len(e) - 1):
        e0, e1 = e[j], e[j+1]
        if (min(e0, e1) - 1e-6) <= want <= (max(e0, e1) + 1e-6) and abs(e1 - e0) > 1e-6:
            return a + j + (want - e0) / (e1 - e0)
    return a if (phase == 'down') == (prog < 0.5) else b

def wing_pose(t, s, lag=0.0, amp=1.0):
    if clip == 'fly':
        tgt, phase, prog = fly_target(t - lag)
        mean = (TOP + BOT) / 2; tgt = mean + (tgt - mean) * amp
        fi = src_frame(s, phase, prog)
    else:
        tgt = 10.0 + 3.0 * math.sin(2 * math.pi * 2 * (t - lag) / L)     # 2 slow breaths per 3 s loop
        fi = (t / L) * N
    ms = chain_at(fi, s)
    d = tgt - chain_elev(ms, s)
    # left wing (+X): +Ry lowers it; right wing (-X): +Ry raises it
    Q = Ry(-d if s == 'l' else d)
    return {n: dec(Q @ ms[n]) for n in WING[s]}, tgt

# ---------------------------------------------------------------- legs / tail / neck
def legs(t):
    ph = 2 * math.pi * t / L
    pad = 1.0 if clip == 'fly' else 0.7
    cyc = 1 if clip == 'fly' else 2                    # glide: 2 slow paddles per 3 s loop
    ph = ph * cyc
    out = {}
    for side, lagf in (('l', 0.0), ('r', 0.0625)):
        p = ph - 2 * math.pi * cyc * lagf / L
        out[f'leg_f{side}_01'] = {'side': 8 + 6 * pad * math.sin(p)}
        out[f'leg_f{side}_02'] = {'side': -72 + 12 * pad * math.sin(p + 0.6)}
        out[f'leg_f{side}_03'] = {'side': 42 + 12 * pad * math.sin(p + 1.0)}
        out[f'hoof_f{side}'] = {'side': 88 + 10 * pad * math.sin(p + 1.3)}
    for side, lagf in (('l', 0.042), ('r', 0.1)):
        p = ph + math.pi - 2 * math.pi * cyc * lagf / L
        out[f'leg_b{side}_01'] = {'side': 14 + 6 * pad * math.sin(p)}
        out[f'leg_b{side}_02'] = {'side': 68 + 8 * pad * math.sin(p + 0.5)}
        out[f'leg_b{side}_03'] = {'side': 46 + 8 * pad * math.sin(p + 0.9)}
        out[f'hoof_b{side}'] = {'side': 74 + 8 * pad * math.sin(p + 1.2)}
    return out

def tail(t):
    cyc = 1 if clip == 'fly' else 2
    ph = 2 * math.pi * cyc * t / L
    base = [122, 110, 100, 94, 91]; amp = [2, 4, 6, 8, 10] if clip == 'fly' else [3, 4.5, 6, 7.5, 9]
    return {f'tail_0{i+1}': {'side': base[i] + amp[i] * math.sin(ph - 0.7 * i - 0.8)} for i in range(5)}

NECK = {'neck_01': 10.0, 'neck_02': 8.0, 'neck_03': 6.0}

# ---------------------------------------------------------------- build
outkeys = []; rep = []
for i, k in enumerate(keys['keys']):
    t = k['t']; p = json.loads(json.dumps(src[i]))
    for s, lag, amp in (('l', 0.0, 1.0), ('r', 1.0 / 24 if clip == 'fly' else 0.125, 0.97 if clip == 'fly' else 1.0)):
        wb, tgt = wing_pose(t, s, lag, amp)
        p['bones'].update(wb)
        rep.append((round(t, 3), s, round(tgt, 1)))
    for n, v in legs(t).items(): p['bones'][n] = {k2: round(v2, 3) for k2, v2 in v.items()}
    for n, v in tail(t).items(): p['bones'][n] = {k2: round(v2, 3) for k2, v2 in v.items()}
    for n, d in NECK.items(): p['bones'][n]['rx'] = round(p['bones'][n]['rx'] + d, 3)
    if clip == 'fly': p['root']['loc'][2] = round(p['root']['loc'][2] * 1.5, 5)
    p['fix4'] = 'v4 (feedback2 pegasus fixer 2026-11-23): wing stroke curve, tucked legs, streaming tail, neck stretch' + (', bob x1.5' if clip == 'fly' else '')
    fn = f'poses_{clip}/f4_k{i:02d}.json'
    if '--write' in sys.argv: json.dump(p, open(f'{D}/{fn}', 'w'), indent=1)
    outkeys.append({'t': t, 'pose_file': fn})
nk = {x: keys[x] for x in keys if x != 'keys'}
nk['fix4'] = {'by': 'feedback2 pegasus fixer 2026-11-23', 'base_keys': f'keys_{clip}.v3.json (fx_k*.json)',
              'tool': 'work/feedback2_pegasus/gen4.py', 'wing_target': 'fly: +50 top -> -30 bottom eased, down 0.583 s / up 0.458 s; glide +10 +-3' }
nk['keys'] = outkeys
if '--write' in sys.argv: json.dump(nk, open(f'{D}/keys_{clip}.v4.json', 'w'), indent=1)
for r in rep[::2]: print(r)
