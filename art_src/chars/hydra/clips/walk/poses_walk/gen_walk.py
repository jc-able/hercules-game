"""Procedural quadruped walk keys for the hydra (side-plane 2-bone IK, aim form).
usage: gen.py params.json outdir   -> outdir/k00.json.. + outdir/keys.json"""
import json, math, sys, os
P = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
_info = os.environ.get('AK_INFO_JSON') or next((f for f in (os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'info.json'),
         os.path.expanduser('~/HerculesGame/work/anim/hydra_walk/info.json')) if os.path.exists(f)), None)
R = {b['name']: b for b in json.load(open(_info))['bones']}   # `ak info hydra.blend --json-out info.json`
D = P.get('duty', 0.7); S = P.get('stride', 2.0); H = P.get('lift', 0.7)
n = P.get('nkeys', 8); period = P['period']; off = P.get('phase', 0.0)
# lateral-sequence walk: LH, LF, RH, RF
legs = P.get('legs', {'bl': 0.0, 'fl': 0.25, 'br': 0.5, 'fr': 0.75})
if P.get('swap'): legs = {k[0] + ('r' if k[1] == 'l' else 'l'): v for k, v in legs.items()}
def yz(b, end): p = R[b][end]; return (p[1], p[2])
def ang(dy, dz): return math.degrees(math.atan2(dy, -dz))   # side-panel aim angle (0 down, + = toward +Y/back)
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
STATS = {}
def smooth(x): return x * x * (3 - 2 * x)
def leg_pose(leg, p, bob=0.0):
    u = (p - legs[leg]) % 1.0
    lift = 0.0
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
    dy += P.get('hind_shift', 0.0) if leg[0] == 'b' else P.get('front_shift', 0.0)
    r3 = R[f'leg_{leg}_03']['rest_side_deg']; rf = R[f'foot_{leg}']['rest_side_deg']
    fl = P.get('flex3', 35) * lift; ft = P.get('flexf', 45) * lift
    # keep the toe tip above its rest height (no toe through the floor at lift-off / touch-down)
    L3 = R[f'leg_{leg}_03']['length_m']; Lf = R[f'foot_{leg}']['length_m']
    drop = lambda a3, af: L3 * math.cos(math.radians(a3)) + Lf * math.cos(math.radians(af))
    need = drop(r3 + fl, rf + ft) - drop(r3, rf)
    if lift > 0: dz = max(dz, need + 0.05 * lift)
    tgt = (a[0] + dy, a[1] + dz); phi = 0.0
    if 'swing_reach' in P and leg[0] == 'f' and lift > 0:
        tgt = (tgt[0] - P['swing_reach'] * math.sin(math.pi * min(1, s * 1.25)) ** 2, tgt[1])
    reach = (L1 + L2) * 0.995
    if math.dist(h, tgt) > reach:
        # heel lift: turn the leg_03+foot unit about the toe until the ankle is reachable
        t3 = math.radians(r3 + fl); tf = math.radians(rf + ft)
        toe = (tgt[0] + L3 * math.sin(t3) + Lf * math.sin(tf), tgt[1] - L3 * math.cos(t3) - Lf * math.cos(tf))
        best = None
        for sgn in (1, -1):
            for st in range(1, 61):
                ph = math.radians(st) * sgn; c, sn = math.cos(ph), math.sin(ph)
                vy, vz = tgt[0] - toe[0], tgt[1] - toe[1]
                # side-panel clockwise (+ angle toward +Y when pointing down) = rotation in (y,z) by -ph about x? use aim convention
                ny = toe[0] + vy * c - vz * sn; nz = toe[1] + vz * c + vy * sn
                if math.dist(h, (ny, nz)) <= reach:
                    if best is None or st < best[0]: best = (st, sgn, (ny, nz))
                    break
        if best:
            phi = best[0] * best[1]; tgt = best[2]
        STATS['clamped'] = max(STATS.get('clamped', 0), math.dist(h, (a[0] + dy, a[1] + dz)) / (L1 + L2))
    STATS['phi_max_' + leg] = max(STATS.get('phi_max_' + leg, 0), abs(phi))
    up, lo = ik(h, tgt, L1, L2, SIGN[leg])
    fl += phi; ft += phi
    return {f'leg_{leg}_01': {'side': round(up, 2)}, f'leg_{leg}_02': {'side': round(lo, 2)},
            f'leg_{leg}_03': {'side': round(r3 + fl, 2)}, f'foot_{leg}': {'side': round(rf + ft, 2)}}
def pose(p):
    w = 2 * math.pi * p
    bones = {}
    bob = P.get('bob', 0.05) * math.cos(4 * math.pi * p + P.get('bob_ph', 0.0))
    for leg in legs: bones.update(leg_pose(leg, p, bob))
    sway = P.get('sway', 0.0); yaw = P.get('yaw', 0.0)
    root = {'ground': 'lowest', 'rot': [round(P.get('pitch', 0.0) * math.sin(2 * w + P.get('pitch_ph', 0)), 2),
                                        round(sway * math.sin(w + P.get('sway_ph', 0)), 2),
                                        round(yaw * math.sin(w + P.get('yaw_ph', 1.57)), 2)]}
    chains = []
    nb = P.get('neck_bob', 2.0)
    for i, nm in enumerate(['neck_c', 'neck_1', 'neck_2', 'neck_3', 'neck_4', 'neck_5', 'neck_6', 'neck_7', 'neck_8']):
        ph = P.get('neck_ph', 0.0) + 0.35 * i * (1 if i % 2 else -1) + (0 if nm == 'neck_c' else 0.6)
        L = 6 if nm == 'neck_c' else 5
        amp = nb * (0.7 if nm == 'neck_c' else 1.0)
        lean = P.get('neck_c_lean', 0.0) if nm == 'neck_c' else P.get('necks_lean', 0.0)
        bu = [round(lean + amp * math.sin(2 * w + ph - 0.5 * j), 2) for j in range(L)]
        bs = [round(P.get('neck_side', 1.5) * math.sin(w + ph + P.get('neck_side_ph', 0.0) - 0.4 * j), 2) for j in range(L)]
        chains.append({'name': nm, 'bend_up': bu, 'bend_side': bs})
    sp = P.get('spine_side', 0.5)
    chains.append({'name': 'spine', 'bend_side': [0.0] + [round(sp * math.sin(w + P.get('spine_ph', 0.0)), 2)] * 3})
    ts = P.get('tail_side', 4.0)
    chains.append({'name': 'tail', 'bend_side': [round(ts * math.sin(w + P.get('tail_ph', 0) - 0.45 * j), 2) for j in range(8)],
                   'bend_up': [round(P.get('tail_up', 1.0) * math.sin(2 * w - 0.5 * j), 2) for j in range(8)]})
    d = {'space': 'absolute', 'root': root, 'bones': bones, 'chain': chains}
    if 'view_offset' in P: d['view_offset'] = P['view_offset']
    return d
keys = []
for i in range(n):
    p = (i / n + off) % 1.0
    fn = f'k{i:02d}.json'; json.dump(pose(p), open(os.path.join(out, fn), 'w'), indent=1)
    keys.append({'t': round(i * period / n, 4), 'pose_file': os.path.abspath(os.path.join(out, fn))})
json.dump({'fps': 24, 'loop': True, 'length': period, 'events': {}, 'keys': keys}, open(os.path.join(out, 'keys.json'), 'w'), indent=1)
print('signs', SIGN, 'keys', n, 'stats', {k: round(v, 3) for k, v in STATS.items()})
