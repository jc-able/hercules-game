"""fix3 checks on a hydra GLB vs the previous one (FK on the GLB, glTF coords: +Y up, faces +Z).
python3 verify.py <new.glb> <new_clips.json> <prev.glb> [sections]   sections: feet turn trans necks seams idle stomp hurt hd contract"""
import sys, json, numpy as np
sys.path.insert(0, __import__('os').path.expanduser('~/HerculesGame/work/natural_review/hydra'))
from glbfk import GLB
N = GLB(sys.argv[1]); man = json.load(open(sys.argv[2])); O = GLB(sys.argv[3])
SEC = sys.argv[4].split(',') if len(sys.argv) > 4 else ['feet', 'turn', 'trans', 'seams', 'idle', 'stomp', 'hurt', 'hd', 'contract', 'necks']
FPS = 30
FEET = ['foot_fl', 'foot_fr', 'foot_bl', 'foot_br']


def P(G, clip, b, ts):
    return np.array([G.pose(clip, t)[b][:3, 3] for t in ts])


def ts_of(G, clip, step=1 / FPS):
    return np.arange(0, G.length(clip) + 1e-6, step)


def feet(G, clip):
    ts = ts_of(G, clip); res = []
    poses = [G.pose(clip, t) for t in ts]
    for f in FEET:
        p = np.array([W[f][:3, 3] for W in poses]); y = p[:, 1]
        low = y < 0.42
        st = np.linalg.norm(np.diff(p[:, [0, 2]], axis=0), axis=1)
        both = low[1:] & low[:-1]
        k = int(np.argmax(np.where(both, st, 0)))
        res.append('%s %.3fm(max %.2fm/s @%.2fs)' % (f[-2:], st[both].sum(), st[k] * FPS, ts[k]))
    return ', '.join(res)


if 'feet' in SEC:
    print('== planted-foot slide (foot joint below 0.42 m): PREV -> NEW')
    for c in N.anims:
        if c.startswith('walk') or c.startswith('death'):
            continue
        print(' %-20s PREV %s\n %-20s NEW  %s' % (c, feet(O, c) if c in O.anims else '-', '', feet(N, c)))

if 'turn' in SEC:
    print('\n== turning in place at the game rate (hydra.gd: rate = w * r / move_speed, r = 2.99 m): world slide in stance')
    r = 2.99
    for clip in ['walk_turn_l', 'walk_turn_r', 'walk']:
        ms = man['clips'][clip]['move_speed']
        L = N.length(clip)
        for wdeg in [35.0, 12.0]:
            w = np.radians(wdeg); rate = w * r / ms
            for sgn in ([1] if clip == 'walk_turn_l' else [-1] if clip == 'walk_turn_r' else [1, -1]):
                ts = np.arange(0, L / rate, 1 / FPS)
                out = []
                poses = [N.pose(clip, (t * rate) % L) for t in ts]
                for f in FEET:
                    pc = np.array([W[f][:3, 3] for W in poses])
                    th = sgn * w * ts; c, s = np.cos(th), np.sin(th)
                    pw = np.stack([c * pc[:, 0] + s * pc[:, 2], pc[:, 1], -s * pc[:, 0] + c * pc[:, 2]], 1)
                    low = pc[:, 1] < 0.42
                    st = np.linalg.norm(np.diff(pw[:, [0, 2]], axis=0), axis=1); both = low[1:] & low[:-1]
                    out.append('%s %.3f m/s' % (f[-2:], st[both].mean() * FPS if both.any() else 0))
                print('  %-12s %4.0f deg/s %s rate %.2f: mean stance slide %s' % (clip, wdeg, 'left ' if sgn > 0 else 'right', rate, '; '.join(out)))

if 'trans' in SEC:
    print('\n== walk/turn <-> idle: mean distance of the 4 foot joints from idle t=0, per clip time')
    I0 = N.pose('idle', 0)
    for clip in ['walk', 'walk_turn_l', 'walk_turn_r']:
        ts = ts_of(N, clip, 1 / 12)
        d = []
        for t in ts:
            W = N.pose(clip, t)
            d.append(np.mean([np.linalg.norm(W[f][:3, 3] - I0[f][:3, 3]) for f in FEET]))
        d = np.array(d); k = int(d.argmin())
        print('  %-12s mean %.2f, min %.2f m @%.2fs, max %.2f; %s' % (clip, d.mean(), d.min(), ts[k], d.max(), ' '.join('%.2f' % v for v in d)))
        if clip in man['clips'] and 'stop_window' in man['clips'][clip]:
            a, b = man['clips'][clip]['stop_window']; st = man['clips'][clip]['start_time']
            sel = (ts >= a) & (ts <= b)
            print('      stop window %.2f-%.2f s: offset %.2f-%.2f m; start_time %.3f s: %.2f m' % (a, b, d[sel].min(), d[sel].max(), st,
                  np.mean([np.linalg.norm(N.pose(clip, st)[f][:3, 3] - I0[f][:3, 3]) for f in FEET])))

NAMES = [n for n in N.names if n not in ('hydra', 'hydra_rig', 'root')]
if 'seams' in SEC:
    print('\n== chain joins (largest joint gap, metres): PREV -> NEW')
    for c1, c2 in [('fire_sweep', 'head_down'), ('fire_sweep_l', 'head_down'), ('fire_sweep_return', 'head_down'), ('fire_sweep_return_l', 'head_down'),
                   ('head_down', 'head_up'), ('hurt', 'head_down'), ('head_down', 'death'), ('head_up', 'idle'), ('bite', 'idle'),
                   ('stomp', 'idle'), ('stomp_r', 'idle'), ('idle', 'bite'), ('idle', 'stomp'), ('idle', 'fire_sweep')]:
        out = []
        for G in (O, N):
            A = G.pose(c1, G.length(c1)); B = G.pose(c2, 0)
            d = sorted(((np.linalg.norm(A[b][:3, 3] - B[b][:3, 3]), b) for b in NAMES), reverse=True)[:2]
            out.append(', '.join('%s %.3f' % (b, v) for v, b in d))
        print('  %-20s -> %-10s PREV %s | NEW %s' % (c1, c2, out[0], out[1]))
    print('  loop seams (velocity jump at the seam vs the bone p95 of frame-to-frame velocity change, NEW):')
    for c in ['idle', 'head_down', 'walk_turn_l', 'walk_turn_r']:
        L = N.length(c); ts = np.arange(0, L + 1e-6, 1 / FPS)
        worst = (0, '')
        for b in NAMES:
            p = P(N, c, b, ts); v = np.diff(p, axis=0) * FPS
            seam = np.linalg.norm(v[0] - v[-1]); inner = np.linalg.norm(np.diff(v, axis=0), axis=1)
            p95 = np.percentile(inner, 95)
            if seam - p95 > worst[0]:
                worst = (seam - p95, '%s seam %.2f m/s vs p95 %.2f, pos gap %.3f m' % (b, seam, p95, np.linalg.norm(p[0] - p[-1])))
        print('    %-12s worst excess %.2f: %s' % (c, worst[0], worst[1]))

if 'idle' in SEC:
    print('\n== idle: vertical range (m) of body bones over 6 s, PREV -> NEW; feet horizontal range')
    ts = np.arange(0, 6.0001, 1 / 15)
    for b in ['hips', 'spine_01', 'spine_02', 'spine_03', 'neck_c_01', 'neck_4_01', 'neck_5_01', 'leg_fl_02', 'leg_bl_02', 'foot_fl', 'foot_br']:
        o = P(O, 'idle', b, ts); n = P(N, 'idle', b, ts)
        print('  %-10s y range %.3f -> %.3f ; x range %.3f -> %.3f' % (b, np.ptp(o[:, 1]), np.ptp(n[:, 1]), np.ptp(o[:, 0]), np.ptp(n[:, 0])))
    n = P(N, 'idle', 'spine_03', ts)
    print('  spine_03 y every 0.5 s: ' + ' '.join('%+.3f' % v for v in (n[::7, 1] - n[0, 1])))
    for b in FEET:
        n = P(N, 'idle', b, ts)
        print('  %s horizontal range %.4f m, height %.3f-%.3f' % (b, np.max(np.linalg.norm(n[:, [0, 2]] - n[0, [0, 2]], axis=1)), n[:, 1].min(), n[:, 1].max()))

if 'stomp' in SEC:
    print('\n== stomp: head heights and speeds')
    for c in ['stomp', 'stomp_r']:
        ts = ts_of(N, c)
        for G, nm in [(O, 'PREV'), (N, 'NEW')]:
            rows = []
            for h in ['head_c'] + ['head_%d' % k for k in range(1, 9)]:
                p = P(G, c, h, ts)
                y0 = p[0, 1]; sel = (ts >= 0.4) & (ts <= 1.75)
                rows.append('%s +%.2f' % (h[5:], p[sel, 1].max() - y0))
            print('  %-8s %-4s rear-up (max head rise 0.4-1.75 s): %s' % (c, nm, ' '.join(rows)))
        for G, nm in [(O, 'PREV'), (N, 'NEW')]:
            for b in ['head_c', 'jaw_c', 'tail_08']:
                sel = np.arange(1.5, 2.05, 1 / FPS); p = P(G, c, b, sel)
                v = np.linalg.norm(np.diff(p, axis=0), axis=1) * FPS
                print('  %-8s %-4s %-7s speed 1.5-2.05 s: %s' % (c, nm, b, ' '.join('%.1f' % x for x in v)))
        fo = O.pose(c, 1.75)['foot_fl' if c == 'stomp' else 'foot_fr'][:3, 3]; fn = N.pose(c, 1.75)['foot_fl' if c == 'stomp' else 'foot_fr'][:3, 3]
        f0 = N.pose(c, 0.0)['foot_fl' if c == 'stomp' else 'foot_fr'][:3, 3]
        print('  %s impact foot @1.75: PREV %s NEW %s (moved %.3f m); NEW start foot %s -> ring centre offset %.3f m' % (
            c, np.round(fo, 2), np.round(fn, 2), np.linalg.norm(fo - fn), np.round(f0, 2), np.linalg.norm((fn - f0)[[0, 2]])))

if 'hurt' in SEC:
    print('\n== hurt 0-0.4 s: per-frame speed of side heads (PREV -> NEW peak)')
    ts = np.arange(0, 0.45, 1 / FPS)
    for h in ['head_%d' % k for k in range(1, 9)] + ['head_c']:
        out = []
        for G in (O, N):
            p = P(G, 'hurt', h, ts); v = np.linalg.norm(np.diff(p, axis=0), axis=1) * FPS
            out.append('peak %.1f @%.2f' % (v.max(), ts[int(v.argmax())]))
        p = P(N, 'hurt', h, ts); v = np.linalg.norm(np.diff(p, axis=0), axis=1) * FPS
        print('  %-7s PREV %s | NEW %s | NEW %s' % (h, out[0], out[1], ' '.join('%.0f' % x for x in v[:10])))

if 'hd' in SEC:
    print('\n== head_down: body motion (PREV -> NEW) and the jaw weak point')
    ts = np.arange(0, 1.5001, 1 / FPS)
    for b in ['spine_02', 'spine_03', 'neck_c_01', 'neck_4_01', 'neck_c_03', 'head_c', 'jaw_c', 'tail_08', 'head_5']:
        o = P(O, 'head_down', b, ts); n = P(N, 'head_down', b, ts)
        print('  %-10s range %.3f -> %.3f m' % (b, np.max(np.linalg.norm(o - o[0], axis=1)), np.max(np.linalg.norm(n - n[0], axis=1))))
    for G, nm in [(O, 'PREV'), (N, 'NEW')]:
        j = P(G, 'head_down', 'jaw_c', ts)
        print('  %s jaw_c height %.3f-%.3f, ahead %.3f-%.3f, x %.3f-%.3f' % (nm, j[:, 1].min(), j[:, 1].max(), j[:, 2].min(), j[:, 2].max(), j[:, 0].min(), j[:, 0].max()))

if 'contract' in SEC:
    print('\n== contracts')
    for G, nm in [(O, 'PREV'), (N, 'NEW')]:
        W = G.pose('bite', 1.5); h = W['head_c'][:3, 3]
        print('  %s bite head_c @1.5: %s ; bite_l head_6 %s ; bite_r head_3 %s' % (nm, np.round(h, 3), np.round(G.pose('bite_l', 1.5)['head_6'][:3, 3], 3), np.round(G.pose('bite_r', 1.5)['head_3'][:3, 3], 3)))
        W = G.pose('fire_sweep', 2.8)
        print('  %s fire_sweep head_c/jaw_c @2.8: %s %s' % (nm, np.round(W['head_c'][:3, 3], 3), np.round(W['jaw_c'][:3, 3], 3)))
    for c in man['clips']:
        print('  %-20s len %.4f GLB %.4f loop %s events %s %s' % (c, man['clips'][c]['length'], N.length(c), man['clips'][c]['loop'], man['clips'][c]['events'],
                                                         ('move_speed %s' % man['clips'][c].get('move_speed')) if 'move_speed' in man['clips'][c] else ''))

if 'necks' in SEC:
    def chain(h):
        return (['neck_c_%02d' % k for k in range(1, 6)] + ['head_c']) if h == 'c' else (['neck_%s_%02d' % (h, k) for k in range(1, 5)] + ['head_' + h])
    HS = ['c'] + [str(i) for i in range(1, 9)]

    def segd(a1, a2, b1, b2):
        s = np.linspace(0, 1, 10); A = a1 + (a2 - a1) * s[:, None]; B = b1 + (b2 - b1) * s[:, None]
        return np.min(np.linalg.norm(A[:, None] - B[None], axis=2))

    def scan(G, clip, thr=0.8):
        L = G.length(clip); hits = {}
        for t in np.arange(0, L + 1e-6, 1 / 15):
            W = G.pose(clip, t)
            for i in range(9):
                for j in range(i + 1, 9):
                    A = chain(HS[i]); B = chain(HS[j])
                    for a in range(2, len(A) - 1):
                        for b in range(2, len(B) - 1):
                            d = segd(W[A[a]][:3, 3], W[A[a + 1]][:3, 3], W[B[b]][:3, 3], W[B[b + 1]][:3, 3])
                            if d < thr:
                                k = (HS[i], HS[j]); h = hits.setdefault(k, [9, 0, 1e9, -1, ''])
                                if d < h[0]: h[0] = d; h[4] = '%s/%s' % (A[a], B[b])
                                h[2] = min(h[2], t); h[3] = max(h[3], t)
        return hits
    print('\n== upper neck links closer than 0.8 m (PREV -> NEW)')
    for c in N.anims:
        if c.startswith('death'):
            continue
        fmt = lambda H: '; '.join('%s-%s %.2fm %s %.2f-%.2fs' % (k[0], k[1], v[0], v[4], v[2], v[3]) for k, v in sorted(H.items(), key=lambda x: x[1][0])) or 'none'
        o = scan(O, c) if c in O.anims else {}
        n = scan(N, c)
        print('%-20s PREV: %s\n%-20s NEW:  %s' % (c, fmt(o), '', fmt(n)), flush=True)
