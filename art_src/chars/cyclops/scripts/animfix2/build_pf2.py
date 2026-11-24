"""pull_free clip fix 2 (2026-11-23, clip fixer): (a) time-warp of the heave so the club head never exceeds VCAP m/s,
(b) both feet planted by leg IK (right foot: one real step instead of a 1.25 m glide; left foot: its existing step kept,
the plants pinned). Poses come from the animfix2 bake (action_pull_free.rest_v3.json = the action merged before this fix),
so the club path, the hands' stagger and the body coordination are those of animfix2, only re-timed.
First key = poses_stuck/k00_stuck.json, last key = poses_pull_free/k08_natural.json (exact chain seams).
python3 build_pf2.py [--write]   (then: tools/ak bake ... --clip pull_free --keys keys_pull_free.json --out-action action_pull_free.json)"""
import sys, json, os, math, numpy as np
import fx
fx.HERE = os.path.expanduser('~/HerculesGame/work/clipfix2_cyclops')   # scratch for the headless resolve jobs (needs rb_resolve.py)
from fx import *
S = CL + '/slam/'; P = S + 'poses_pull_free/'
ACT = S + 'action_pull_free.rest_v3.json'
WRITE = '--write' in sys.argv
L, FPS = 1.5, 24
N = int(L * FPS)            # 36 -> frames 0..36
OFF = np.array([0.0844, -0.875, 5.0616])   # club head in the hand_u_r rest frame (calibrated on the GLB, spread 0.4 mm)
TA = float(os.environ.get('TA', 0.20))                  # warp window [TA, L]: before TA (strain, club still in the crack) timing is untouched
VCAP = float(os.environ.get('VCAP', 26.0))   # aim (fine sampled); measured at 24 fps it reads lower
RMAX = float(os.environ.get('RMAX', 2.0))                 # a slow passage is sped up at most this much (body moves there even if the club does not)


def head(res):
    return np.array(res['pos']['hand_u_r']) + res['abs']['hand_u_r'] @ OFF


# 1. club head speed of the source on a fine grid
FF = 96
ss = np.arange(0, int(L * FF) + 1) / FF
rs = resolve([{'id': f'{s:.5f}', 'from_action': ACT, 't': float(s)} for s in ss], 'pf2_fine')
H = np.array([head(rs[f'{s:.5f}']) for s in ss])
v = np.r_[np.linalg.norm(np.diff(H, axis=0), axis=1) * FF, 0.0]           # speed on [s_i, s_i+1)
print('source club head peak %.1f m/s at %.3f s' % (v.max(), ss[v.argmax()]))


# 2. warp s(t) (source time of new time t): before TA identity; from TA the club head follows a target speed
#    K * env(t) (env eases in over 0.08 s from rate 1 and eases out to 0.1 over the last DOUT s), i.e. ds/dt = K env / v(s),
#    clamped to [0.25, RMAX] (a passage where the club is slow but the body moves is sped up at most RMAX x).
#    K is found by bisection so that s(L) = L (length unchanged).
DOUT = float(os.environ.get('DOUT', 0.30))
sg = 0.015 * FF; gk = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); gk /= gk.sum()
vs = np.convolve(np.pad(v, len(gk) // 2, mode='edge'), gk, mode='valid')[:len(ss)]
DT = 1 / 960.0
tt = np.arange(0, L + DT / 2, DT)


def integrate(K):
    s = 0.0; out = np.empty_like(tt)
    for i, t in enumerate(tt):
        out[i] = s
        if t < TA: rate = 1.0
        else:
            ein = min(1.0, (t - TA) / 0.08); ein = ein * ein * (3 - 2 * ein)
            u = min(1.0, max(0.0, (t - (L - DOUT)) / DOUT)); env = 1.0 - 0.9 * (u * u * (3 - 2 * u))
            rr = min(RMAX, max(0.25, K * env / max(float(np.interp(s, ss, vs)), 1e-3)))
            rate = 1.0 + (rr - 1.0) * ein
        s = min(L, s + rate * DT)
    return out


lo, hi = 1.0, 80.0
for _ in range(40):
    KW = (lo + hi) / 2; so = integrate(KW)
    if so[-1] < L - 1e-4: lo = KW
    else: hi = KW
so = integrate(hi); KW = hi
so = so * (L / so[-1])
s_of_t = lambda t: float(np.interp(t, tt, so))
pts = np.array([np.interp(x, ss, H[:, 0]) for x in so]), np.array([np.interp(x, ss, H[:, 1]) for x in so]), np.array([np.interp(x, ss, H[:, 2]) for x in so])
Hn = np.stack(pts, 1)[::10]; vn = np.linalg.norm(np.diff(Hn, axis=0), axis=1) * 96
print('warp K %.2f; predicted new club peak %.1f m/s (96 Hz), last 0.1 s max %.1f, window %.2f-%.2f s' % (KW, vn.max(), vn[-10:].max(), TA, L))

# 3. per-frame read-backs of the source at the warped times
fr = list(range(N + 1)); sf = [s_of_t(f / FPS) for f in fr]
r = resolve([{'id': str(f), 'from_action': ACT, 't': sf[f]} for f in fr]
            + [{'id': 'k00', 'pose_file': CL + '/slam/poses_stuck/k00_stuck.json'}, {'id': 'k08', 'pose_file': P + 'k08_natural.json'}], 'pf2_frames')
AB = [r[str(f)]['abs'] for f in fr]; POS = [r[str(f)]['pos'] for f in fr]
ROOT = [r[str(f)]['pose']['root'] for f in fr]
for f in fr[1:N]:
    assert ROOT[f].get('rot', [0, 0, 0]) == [0, 0, 0]

# 4. feet. contact frames of the source read-back: ankle within 4 cm of its lowest height
plan = {}
for s in 'lr':
    z = np.array([POS[f]['foot_' + s][2] for f in fr]); z0 = min(z[0], z[-1])
    contact = z < z0 + 0.04
    P0 = np.array(POS[0]['foot_' + s]); P1 = np.array(POS[N]['foot_' + s])
    tgt = {}; fabs = {}
    if contact.all():
        # one planted run in the source (the glide): one real step at the frames where the source ankle moves most
        xy = np.array([POS[f]['foot_' + s][:2] for f in fr]); sp = np.r_[0, np.linalg.norm(np.diff(xy, axis=0), axis=1)]
        cum = np.cumsum(sp); half = cum[-1] / 2; mid = int(np.searchsorted(cum, half))
        a, b = max(1, mid - 3), min(N - 1, mid + 4)        # 7-frame step (0.29 s clip, 0.16 s in game)
        runs = [(0, a), (b, N)]
    else:
        runs = []; f = 0
        while f <= N:
            if contact[f]:
                g = f
                while g + 1 <= N and contact[g + 1]: g += 1
                runs.append((f, g)); f = g + 1
            else: f += 1
        assert runs[0][0] == 0 and runs[-1][1] == N, (s, runs)
    if s == 'r' and len(runs) == 2 and len(plan['l'][0]) == 2:
        # never both feet in the air: the right step starts 1 frame after the left foot lands, same swing length (>= 6)
        la = plan['l'][0][1][0]; sw = max(6, runs[1][0] - runs[0][1] - 1)
        if runs[0][1] + 1 <= la:
            runs = [(0, la), (la + sw + 1, N)]
    # plant position of each run: start run = frame 0, end run = frame N, others = their middle frame
    anchor = []
    for i, (a, b) in enumerate(runs):
        k = 0 if i == 0 else (N if i == len(runs) - 1 else (a + b) // 2)
        anchor.append((np.array(POS[k]['foot_' + s]), AB[k]['foot_' + s], AB[k]['toe_' + s]))
    for i, (a, b) in enumerate(runs):
        for f in range(a, b + 1):
            p = anchor[i][0].copy(); tgt[f] = p; fabs[f] = (anchor[i][1], anchor[i][2])
        if i + 1 < len(runs):   # swing to the next run: smoothstep in plan, lift
            a2 = runs[i + 1][0]
            for f in range(b + 1, a2):
                u = (f - b) / (a2 - b); e = u * u * (3 - 2 * u)
                p = anchor[i][0] * (1 - e) + anchor[i + 1][0] * e
                src_lift = POS[f]['foot_' + s][2] - (anchor[i][0][2] * (1 - u) + anchor[i + 1][0][2] * u)
                p[2] += max(src_lift, 0.16 * math.sin(math.pi * u))
                tgt[f] = p; fabs[f] = (slerp(anchor[i][1], anchor[i + 1][1], e), slerp(anchor[i][2], anchor[i + 1][2], e))
    plan[s] = (runs, tgt, fabs)
    print(s, 'runs', runs)

fin = {}
for f in fr[1:N]:
    A = dict(AB[f])
    for s in 'lr':
        A['foot_' + s], A['toe_' + s] = plan[s][2][f]
    fin[f] = A
# hips/thigh heads do not depend on the legs: IK on the read-back positions
for f in fin:
    A = fin[f]
    for s in 'lr':
        A = leg_ik(A, POS[f], s, plan[s][1][f])
    fin[f] = pose_dict(A, {'loc': ROOT[f]['loc']}, note=f'clipfix2 2026-11-23 pull_free frame {f}: animfix2 bake read at {sf[f]:.4f} s (heave time-warp, club head <= {VCAP:.0f} m/s) + feet planted by leg IK')
chk = resolve([{'id': str(f), 'pose': p} for f, p in fin.items()], 'pf2_chk')
err = max(np.linalg.norm(np.array(chk[str(f)]['pos']['foot_' + s]) - plan[s][1][f]) for f in fin for s in 'lr')
up = max(np.linalg.norm(np.array(chk[str(f)]['pos'][b]) - np.array(POS[f][b])) for f in fin for b in ('hips', 'head', 'hand_u_r', 'hand_u_l'))
print('IK foot error max %.4f m; upper body moved by IK max %.4f m' % (err, up))
for s in 'lr':
    pth = sum(np.linalg.norm(np.array(chk[str(f + 1)]['pos']['foot_' + s][:2]) - np.array(chk[str(f)]['pos']['foot_' + s][:2])) for f in range(1, N - 1))
    print(s, 'ankle plan path (frames 1..35) %.3f m' % pth)
if WRITE:
    # ak bake removes the straight-line root drift between the first and last key (k00_stuck loc x 0 -> k08_natural loc x
    # 0.25) from EVERY key; the read-backs already have it removed, so it is added back here (else the feet slide 0.25 m)
    l0 = json.load(open(CL + '/slam/poses_stuck/k00_stuck.json'))['root']['loc']; l1 = json.load(open(P + 'k08_natural.json'))['root']['loc']
    for f, p in fin.items():
        u = f / N; loc = list(p['root']['loc'])
        loc[0] += l0[0] + u * (l1[0] - l0[0]); loc[1] += l0[1] + u * (l1[1] - l0[1])
        p['root']['loc'] = [round(x, 5) for x in loc]
        json.dump(p, open(P + f'pf2_f{f:02d}.json', 'w'), indent=1)
    K = json.load(open(S + 'keys_pull_free.rest_v3.json'))
    K['keys'] = ([{'t': 0.0, 'pose_file': 'poses_stuck/k00_stuck.json'}]
                 + [{'t': round(f / FPS, 4), 'pose_file': f'poses_pull_free/pf2_f{f:02d}.json'} for f in fin]
                 + [{'t': L, 'pose_file': 'poses_pull_free/k08_natural.json'}])
    K['length'] = L; K['events'] = {}
    K['note_clipfix2'] = (f'2026-11-23 clip fix 2 (cyclops): keys = 35 per-frame read-backs of the animfix2 bake (keys_pull_free.rest_v3.json and '
                          f'its poses stay as the source) at time-warped clip times: from {TA} s the heave is re-timed so the club head moves at '
                          f'<= {VCAP:.0f} m/s (warp K {KW:.2f}, at most {RMAX}x faster where the club is slow); both feet planted by leg IK '
                          '(right foot: one step instead of the 1.25 m glide; left: its own step kept, plants pinned). First key k00_stuck, '
                          'last key k08_natural (seams exact). Length 1.5, no events. Generator: art_src/chars/cyclops/scripts/animfix2/build_pf2.py.')
    json.dump(K, open(S + 'keys_pull_free.json', 'w'), indent=1)
    print('written')
