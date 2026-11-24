"""Step 3a (python3, numpy): geodesic skin weights.

For every deform bone: seed vertices = vertices whose nearest bone segment (euclidean) is this bone and that lie within
the bone's radius. Multi-source Dijkstra over the welded mesh edge graph gives the geodesic distance D[b, v]. A vertex
takes weight from every bone whose distance is within that bone's blend width of the nearest one
(w = (1 - (D_b - D_min) / blend_b)^2), then Laplacian smoothing, max 4 influences, normalised.
Geodesic (surface) distance keeps feathers, tail hair and legs from picking up weights from parts that are only close in
space (a hanging feather beside the flank, the tail beside a hock).

Hair (mane, tail: saturated blue in the albedo, from 01b_colors.py) is a separate region: edges between hair and
non-hair vertices cost an extra HAIR_PENALTY metres, mane vertices may only use neck/head/spine_03 and tail hair only
tail/hips bones; vertices out on the wings (|x| > WING_X, not hair) may only use wing bones.

python3 03a_weights.py <stage1.npz> <bones.json> <out_weights.npz> <vcol.npy> [overrides.json] [--labels=<labels.npy>]
--labels (from 01c_rip.py): 1 = wing-only vertex (the hanging feather lobe behind the true wing root), 2 = flank skin under
the wing (no wing bones). Labelled vertices keep their restriction through the contact smoothing.
"""
import sys, json, heapq
import numpy as np

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
FLAGS = {a.split('=')[0]: a.split('=', 1)[1] if '=' in a else True for a in sys.argv[1:] if a.startswith('--')}
npz, bj, out = ARGS[0:3]
d = np.load(npz); co = d['co']; E = d['edges']
bones = json.load(open(bj))
names = [n for n, b in bones.items() if b['deform']]
nv = len(co)

def cls(n):
    if n.startswith('spine') or n == 'hips': return 'body'
    if n.startswith('neck'): return 'neck'
    if n == 'head': return 'head'
    if n.startswith('tail'): return 'tail'
    if n.startswith('hoof'): return 'hoof'
    if n.startswith('leg') and n.endswith('_01'): return 'leg1'
    if n.startswith('leg'): return 'leg'
    if 'feather' in n: return 'feather'
    if n.startswith('wing'): return 'wing'
    return 'body'
RADIUS = {'body': 0.50, 'neck': 0.30, 'head': 0.40, 'tail': 0.14, 'hoof': 0.12, 'leg1': 0.18, 'leg': 0.13,
          'wing': 0.13, 'feather': 0.10}
BLEND = {'body': 0.30, 'neck': 0.18, 'head': 0.12, 'tail': 0.20, 'hoof': 0.06, 'leg1': 0.12, 'leg': 0.09,
         'wing': 0.22, 'feather': 0.30}
col = np.load(ARGS[3])
CONFLICT = 0.8; RINGS = 8; CONTACT_ITERS = 30
HAIR_PENALTY = 0.6; WING_X = 0.55
hair = (col[:, 0] < 0.4) & (col[:, 2] > col[:, 0] + 0.2) & (co[:, 2] > 0.4) & (co[:, 1] > -1.3)
mane = hair & (co[:, 1] < 0.5); tailhair = hair & (co[:, 1] >= 0.5)
wingreg = (~hair) & (np.abs(co[:, 0]) > WING_X) & (co[:, 2] > 0.9)
lab = np.load(FLAGS['--labels']) if '--labels' in FLAGS else np.zeros(nv, np.int8)
wingreg |= (lab == 1)
flank = lab == 2
print('hair', int(hair.sum()), 'mane', int(mane.sum()), 'tail', int(tailhair.sum()), 'wing region', int(wingreg.sum()))
if len(ARGS) > 4:
    ov = json.load(open(ARGS[4]))
    RADIUS.update(ov.get('radius', {})); BLEND.update(ov.get('blend', {}))

H = np.array([bones[n]['head'] for n in names]); T = np.array([bones[n]['tail'] for n in names])
# euclidean distance vertex -> bone segment
seg = T - H; L2 = (seg ** 2).sum(1)
dist = np.empty((len(names), nv))
for i in range(len(names)):
    t = np.clip(((co - H[i]) @ seg[i]) / L2[i], 0, 1)
    p = H[i] + t[:, None] * seg[i]
    dist[i] = np.linalg.norm(co - p, axis=1)
near = dist.argmin(0)

# graph
el = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
el = el + HAIR_PENALTY * (hair[E[:, 0]] != hair[E[:, 1]])
adj = [[] for _ in range(nv)]
for (a, b), l in zip(E.tolist(), el.tolist()):
    adj[a].append((b, l)); adj[b].append((a, l))

CUT = 1.2
D = np.full((len(names), nv), np.inf)
A = np.ones((len(names), nv), bool)
for i, n in enumerate(names):
    r = RADIUS[cls(n)]
    allowed = np.ones(nv, bool)
    if not (cls(n) in ('neck', 'head') or n == 'spine_03'): allowed &= ~mane
    if n.startswith('leg_f') and n.endswith('_01'): allowed &= np.abs(co[:, 0]) > 0.09
    if n.startswith('leg_b') and n.endswith('_01'): allowed &= np.abs(co[:, 0]) > 0.14
    seedok = allowed.copy()
    if n.startswith('leg') and n.endswith('_02'): seedok &= co[:, 2] < bones[n]['head'][2] - 0.03
    if not (cls(n) == 'tail' or n == 'hips'): allowed &= ~tailhair
    if cls(n) not in ('wing', 'feather'): allowed &= ~wingreg
    else: allowed &= ~flank
    A[i] = allowed
    seeds = np.where((near == i) & (dist[i] < r) & seedok)[0]
    if len(seeds) < 5:
        seeds = np.argsort(np.where(allowed, dist[i], np.inf))[:20]
    di = D[i]
    di[seeds] = 0.0
    hq = [(0.0, int(s)) for s in seeds]
    heapq.heapify(hq)
    while hq:
        dv, v = heapq.heappop(hq)
        if dv > di[v] or dv > CUT: continue
        for w, l in adj[v]:
            nd = dv + l
            if nd < di[w] and allowed[w]:
                di[w] = nd; heapq.heappush(hq, (nd, w))
    di[~allowed] = np.inf
    print(f'{n:20s} seeds {len(seeds):5d} reached {np.isfinite(di).sum()}', flush=True)

dmin = D.min(0)
bl = np.array([BLEND[cls(n)] for n in names])[:, None]
W = np.clip(1 - (D - dmin) / bl, 0, 1) ** 2
W[~np.isfinite(W)] = 0
W /= W.sum(0, keepdims=True)

# Laplacian smoothing (uniform neighbours)
nbr_i = np.concatenate([E[:, 0], E[:, 1]]); nbr_j = np.concatenate([E[:, 1], E[:, 0]])
deg = np.bincount(nbr_i, minlength=nv).astype(float)
for it in range(6):
    S = np.zeros_like(W)
    for k in range(len(names)):
        S[k] = np.bincount(nbr_i, weights=W[k, nbr_j], minlength=nv)
    W = 0.5 * W + 0.5 * S / np.maximum(deg, 1)
    W *= A
    W /= np.maximum(W.sum(0, keepdims=True), 1e-12)

# contact zones: where neighbouring vertices disagree strongly (fused surfaces of parts that move apart: mane on the
# wing root, the wing's inner edge on the flank) spread the change over a few rings so it stretches instead of tearing
diff = np.abs(W[:, E[:, 0]] - W[:, E[:, 1]]).sum(0)
zone = np.zeros(nv, bool); zone[E[diff > CONFLICT].ravel()] = True
for r in range(RINGS):
    z2 = zone.copy(); z2[nbr_i[zone[nbr_j]]] = True; zone = z2
print('conflict edges', int((diff > CONFLICT).sum()), 'zone verts', int(zone.sum()))
for it in range(CONTACT_ITERS):
    S = np.zeros_like(W)
    for k in range(len(names)):
        S[k] = np.bincount(nbr_i, weights=W[k, nbr_j], minlength=nv)
    Wn = 0.5 * W + 0.5 * S / np.maximum(deg, 1)
    W[:, zone] = Wn[:, zone]
W *= A | zone[None, :] & ~tailhair[None, :] & (lab == 0)[None, :]
W /= np.maximum(W.sum(0, keepdims=True), 1e-12)

# top 4, normalise, drop tiny
idx = np.argsort(-W, axis=0)[:4]
w4 = np.take_along_axis(W, idx, 0)
w4[w4 < 0.01] = 0
w4 /= w4.sum(0, keepdims=True)
np.savez(out, names=np.array(names), idx=idx.T, w=w4.T, dmin=dmin, near=near)
unreached = int((~np.isfinite(dmin)).sum())
print('###WEIGHTS###', json.dumps({'bones': len(names), 'verts': nv, 'unreached': unreached,
      'max_influences': int((w4 > 0).sum(0).max())}))
