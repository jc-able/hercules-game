"""Hydra walk keys from the NATURAL stance (walk_n video): the old side-plane IK leg walk (clips/walk/poses_walk/gen_walk.py,
unchanged leg maths -> same stride, footfalls and move_speed) + every other limb group from natural_pose.json with walking
life on top (heads bob a beat apart, look changes, centre head nods on the footfalls, jaw breathes, spine and tail sway).
usage: python3 gen_walk_n.py params.json outdir      (env AK_INFO_JSON = `ak info hydra.blend --json-out` file)
Writes outdir/k_fNN.json for the kept frames and outdir/keys.json (clip time, loop)."""
import json, math, sys, os
P = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
NAT = json.load(open(P.get('natural', os.path.join(HERE, '..', '..', '..', 'natural_pose.json'))))
R = {b['name']: b for b in json.load(open(os.environ['AK_INFO_JSON']))['bones']}
D = P.get('duty', 0.7); S = P.get('stride', 2.0); H = P.get('lift', 0.7)
n = P.get('nkeys', 52); period = P['period']; off = P.get('phase', 0.0)
legs = P['legs']

# ---------------- legs: identical maths to clips/walk/poses_walk/gen_walk.py ----------------
def yz(b, end): p = R[b][end]; return (p[1], p[2])
def ang(dy, dz): return math.degrees(math.atan2(dy, -dz))
def ik(hip, tgt, L1, L2, sign):
    dy, dz = tgt[0] - hip[0], tgt[1] - hip[1]; d = math.hypot(dy, dz); d = min(d, (L1 + L2) * 0.999)
    a = math.atan2(dz, dy); c = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d); c = max(-1, min(1, c))
    t = a + sign * math.acos(c); k = (hip[0] + L1 * math.cos(t), hip[1] + L1 * math.sin(t))
    return ang(k[0] - hip[0], k[1] - hip[1]), ang(tgt[0] - k[0], tgt[1] - k[1])
def side_sign(leg):
    h, k, a = yz(f'leg_{leg}_01', 'head'), yz(f'leg_{leg}_01', 'tail'), yz(f'leg_{leg}_02', 'tail')
    best = None
    for s in (1, -1):
        L1 = math.dist(h, k); L2 = math.dist(k, a)
        u, l = ik(h, a, L1, L2, s); e = abs(u - R[f'leg_{leg}_01']['rest_side_deg']) + abs(l - R[f'leg_{leg}_02']['rest_side_deg'])
        if best is None or e < best[0]: best = (e, s)
    return best[1]
SIGN = {l: side_sign(l) for l in ('fl', 'fr', 'bl', 'br')}
def smooth(x): return x * x * (3 - 2 * x)
def bump(p, c, w=0.13):
    u = (p - c) % 1.0; u = u if u < 0.5 else u - 1.0
    return math.exp(-(u / w) ** 2)
def swing_centre(leg): return (legs[leg] + (1 + D) / 2) % 1.0
def spine_pitch(p):
    """per-link chest pitch (deg, + = chest tip up): the chest dips onto each forefoot footfall and rises after it."""
    # dip-only (-spine_up..0): a raised chest would lift the shoulder roots out of the straight forelegs' reach
    return -P.get('spine_up', 0.0) * (0.5 + 0.5 * math.cos(4 * math.pi * (p - P.get('dip_p', 0.33))))
def spine_yaw(p): return P.get('spine_side', 0.5) * math.sin(2 * math.pi * p + P.get('spine_ph', 0.0))
def rolls(p):
    """Body roll (ry, front panel, + drops the character's LEFT side): the shoulders rise over the planted foreleg,
    the hips over the planted hind leg. Returns (hips ry, chest ry total)."""
    rh = P.get('roll_hind', 0.0) * (bump(p, swing_centre('bl')) - bump(p, swing_centre('br')))
    rf = P.get('roll_fore', 0.0) * (bump(p, swing_centre('fl')) - bump(p, swing_centre('fr')))
    return rh, rf
def leg_pose(leg, p, bob=0.0):
    u = (p - legs[leg]) % 1.0
    lift = 0.0; s = 0.0
    if u < D: dy = -S / 2 + S * u / D; dz = 0.0
    else:
        s = (u - D) / (1 - D)
        e = P.get('front_ease', 0.0) if leg[0] == 'f' else P.get('hind_ease', 0.0)
        f = (1 - e) * smooth(s) + e * (1 - (1 - s) ** 2.5)
        lift = math.sin(math.pi * s); dy = S / 2 - S * f
        dz = H * lift * (P.get('front_lift_scale', 1.0) if leg[0] == 'f' else 1.0)
    if leg[0] == 'b': dy *= P.get('hind_scale', 1.0); dz *= P.get('hind_lift_scale', 1.0)
    else: dy *= P.get('front_scale', 1.0)
    h = yz(f'leg_{leg}_01', 'head'); k = yz(f'leg_{leg}_01', 'tail'); a = yz(f'leg_{leg}_02', 'tail')
    L1 = math.dist(h, k); L2 = math.dist(k, a)
    h = (h[0], h[1] - P.get('drop', 0.3) + bob)
    # the leg root rides the body roll: re-solve the leg from the rolled root so the planted foot stays on the floor
    rh, rf = rolls(p); th = math.radians(rf if leg[0] == 'f' else rh)
    h = (h[0], h[1] - R[f'leg_{leg}_01']['head'][0] * math.sin(th))
    if leg[0] == 'f':   # chest pitch (spine bend_up on spine_01..03) lifts/lowers the shoulder roots: solve from there
        lever = sum(R[f'leg_{leg}_01']['head'][1] - R[b]['head'][1] for b in ('spine_01', 'spine_02', 'spine_03'))
        h = (h[0], h[1] - math.radians(spine_pitch(p)) * lever)
    dy += P.get('hind_shift', 0.0) if leg[0] == 'b' else P.get('front_shift', 0.0)
    r3 = R[f'leg_{leg}_03']['rest_side_deg']; rf = R[f'foot_{leg}']['rest_side_deg']
    fl = P.get('flex3', 35) * lift; ft = P.get('flexf', 45) * lift
    L3 = R[f'leg_{leg}_03']['length_m']; Lf = R[f'foot_{leg}']['length_m']
    drop = lambda a3, af: L3 * math.cos(math.radians(a3)) + Lf * math.cos(math.radians(af))
    need = drop(r3 + fl, rf + ft) - drop(r3, rf)
    if lift > 0: dz = max(dz, need + 0.05 * lift)
    tgt = (a[0] + dy, a[1] + dz); phi = 0.0
    if 'swing_reach' in P and leg[0] == 'f' and lift > 0:
        tgt = (tgt[0] - P['swing_reach'] * math.sin(math.pi * min(1, s * 1.25)) ** 2, tgt[1])
    reach = (L1 + L2) * 0.995
    if math.dist(h, tgt) > reach:
        t3 = math.radians(r3 + fl); tf = math.radians(rf + ft)
        toe = (tgt[0] + L3 * math.sin(t3) + Lf * math.sin(tf), tgt[1] - L3 * math.cos(t3) - Lf * math.cos(tf))
        best = None
        for sgn in (1, -1):
            for st in range(1, 61):
                ph = math.radians(st) * sgn; c, sn = math.cos(ph), math.sin(ph)
                vy, vz = tgt[0] - toe[0], tgt[1] - toe[1]
                ny = toe[0] + vy * c - vz * sn; nz = toe[1] + vz * c + vy * sn
                if math.dist(h, (ny, nz)) <= reach:
                    if best is None or st < best[0]: best = (st, sgn, (ny, nz))
                    break
        if best: phi = best[0] * best[1]; tgt = best[2]
    up, lo = ik(h, tgt, L1, L2, SIGN[leg])
    fl += phi; ft += phi
    if leg[0] == 'f':   # chest yaw sway moves the shoulder roots sideways: tilt the foreleg so the foot stays put
        lever = sum(R[b]['head'][1] - R[f'leg_{leg}_01']['head'][1] for b in ('spine_01', 'spine_02', 'spine_03'))
        dx = math.radians(spine_yaw(p)) * lever          # + = root moved to the character's left (+X)
        tilt = math.degrees(math.atan2(dx, 4.3))         # + front angle points the bone toward -X (screen-left)
        out = {}
        for b, sd in ((f'leg_{leg}_01', up), (f'leg_{leg}_02', lo), (f'leg_{leg}_03', r3 + fl), (f'foot_{leg}', rf + ft)):
            out[b] = {'side': round(sd, 2)}
            if b != f'foot_{leg}' and R[b].get('rest_front_deg') is not None:
                out[b]['front'] = round(R[b]['rest_front_deg'] + tilt, 2)
        return out
    return {f'leg_{leg}_01': {'side': round(up, 2)}, f'leg_{leg}_02': {'side': round(lo, 2)},
            f'leg_{leg}_03': {'side': round(r3 + fl, 2)}, f'foot_{leg}': {'side': round(rf + ft, 2)}}

# ---------------- upper body: natural stance + walking life ----------------
NATCH = {c['name']: c for c in NAT['chain']}
NATCH['spine'] = {'name': 'spine', 'bend_side': [0.0] + list(NATCH.pop('spine_01')['bend_side'])}
LEN = {'neck_c': 7, 'tail': 8, 'spine': 4, **{f'neck_{i}': 5 for i in range(1, 9)}}
def add(base, extra, L):
    b = list(base or []) + [0.0] * L; b = b[:L]
    return [round(b[j] + (extra[j] if j < len(extra) else 0.0), 2) for j in range(L)]
# per side neck: (bob amp deg/link, bob phase, side amp, side phase, head nod amp, head yaw amp, yaw phase)
# phases spread round the circle so no two neighbours move together; amplitudes differ.
NECKS = P['necks']
def footfall_nod(p):
    """0..1 pulse a little after each forefoot touch-down (the centre head nods on the footfalls)."""
    v = 0.0
    for leg in ('fl', 'fr'):
        u = (p - legs[leg] - P.get('nod_lag', 0.04)) % 1.0
        v += math.exp(-((u if u < 0.5 else u - 1.0) / 0.09) ** 2)
    return v
def pose(p):
    w = 2 * math.pi * p
    bones = {}
    bob = P.get('bob', 0.05) * math.cos(4 * math.pi * p + P.get('bob_ph', 0.0))
    for leg in legs: bones.update(leg_pose(leg, p, bob))
    chains = []
    # side necks
    for nm, q in NECKS.items():
        nc = NATCH[nm]; L = 5
        bu = [q['bob'] * math.sin(2 * w + q['ph'] - P.get('neck_lag', 0.55) * j) for j in range(4)]
        bs = [q['side'] * math.sin(w + q['sph'] - 0.45 * j) for j in range(4)]
        # head counters the neck bob a beat later (keeps the look steady-ish but alive), slow look turn once per cycle
        hx = q['nod'] * math.sin(2 * w + q['ph'] - 4 * P.get('neck_lag', 0.55) - 0.9)
        hz = q['yaw'] * math.sin(w + q['yph'])
        chains.append({'name': nm, 'bend_up': add(nc.get('bend_up'), bu, 4), 'bend_side': add(nc.get('bend_side'), bs, 4),
                       'rx': add(nc.get('rx'), [0, 0, 0, 0, hx], L), 'rz': add(nc.get('rz'), [0, 0, 0, 0, hz], L)})
    # centre neck: high, looks ahead, small bob, nod on each forefoot footfall, jaw breathes once per cycle
    nc = NATCH['neck_c']; c = P['centre']
    bu = [c['bob'] * math.sin(2 * w + c['ph'] - 0.5 * j) for j in range(5)]
    bs = [c['side'] * math.sin(w + c['sph'] - 0.4 * j) for j in range(5)]
    nod = c['nod'] * (footfall_nod(p) - 0.5)
    hx = nod; hz = c['yaw'] * math.sin(w + c['yph'])
    jaw = c['jaw'] * (0.5 - 0.5 * math.cos(w + c['jph']))
    chains.append({'name': 'neck_c', 'bend_up': add(nc.get('bend_up'), bu, 5), 'bend_side': add(nc.get('bend_side'), bs, 5),
                   'rx': add(nc.get('rx'), [0, 0, 0, 0, 0, hx, jaw], 7), 'rz': add(nc.get('rz'), [0, 0, 0, 0, 0, hz, 0], 7)})
    # spine: lateral sway once per cycle + a little up-down flex twice (breathing-with-steps); hips index 0 stays
    sp = P.get('spine_side', 0.8); su = P.get('spine_up', 0.4)
    rh, rf = rolls(p)
    chains.append({'name': 'spine', 'bend_side': add(NATCH['spine']['bend_side'], [0.0] + [spine_yaw(p)] * 3, 4),
                   'bend_up': [0.0] + [round(spine_pitch(p), 2)] * 3,
                   'ry': [round(rh, 2)] + [round((rf - rh) / 3, 2)] * 3})
    # tail: side swing once per cycle (travelling wave), small lift twice per cycle
    nt = NATCH['tail']; ts = P.get('tail_side', 4.0)
    chains.append({'name': 'tail',
                   'bend_side': add(nt.get('bend_side'), [ts * (0.6 + 0.08 * j) * math.sin(w + P.get('tail_ph', 0) - 0.45 * j) for j in range(8)], 8),
                   'bend_up': add(nt.get('bend_up'), [P.get('tail_up', 1.0) * math.sin(2 * w - 0.5 * j) for j in range(8)], 8)})
    d = {'space': 'absolute', 'root': {'ground': 'lowest'}, 'bones': bones, 'chain': chains}
    if 'view_offset' in P: d['view_offset'] = P['view_offset']
    return d

keep = P.get('keep_frames')
keys = []
for i in range(n):
    if keep is not None and i not in keep: continue
    p = (i / n + off) % 1.0
    fn = f'k_f{i:02d}.json'; json.dump(pose(p), open(os.path.join(out, fn), 'w'), indent=1)
    keys.append({'t': round(i * period / n, 4), 'pose_file': fn})
json.dump({'fps': 24, 'loop': True, 'length': period, 'events': {}, 'keys': keys}, open(os.path.join(out, 'keys.json'), 'w'), indent=1)
print('signs', SIGN, 'keys', len(keys))
