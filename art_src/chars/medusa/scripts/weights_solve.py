"""Upper-body weight rebuild for medusa (numpy only).
Stage A: harmonic (Laplace) weights over the neck / shoulder / back-hair / head region between anchor sets.
Stage B: snake hair ramps 0 -> 1 geodesically along each snake, taken out of the head weight only.
Then soft masks (no hard cuts), restricted smoothing, limit 4, normalise.
Usage as a module: build(W0, rest, E, names) -> W (n, nb) in bone_names order."""
import numpy as np

def S(t, a, b):
    u = np.clip((t - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)

class Graph:
    def __init__(self, rest, E, wpow=0.0):
        self.n = len(rest); self.E = E
        L = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
        self.len = L
        self.w = np.maximum(L, 0.01) ** wpow     # 0 = uniform: even weight steps per edge, whatever its length
        a = np.concatenate([E[:, 0], E[:, 1]]); b = np.concatenate([E[:, 1], E[:, 0]]); ww = np.concatenate([self.w, self.w])
        ll = np.concatenate([L, L])
        o = np.argsort(a, kind='stable'); self.a, self.b, self.ww, self.ll = a[o], b[o], ww[o], ll[o]
        self.start = np.searchsorted(self.a, np.arange(self.n + 1))
        self.deg = np.bincount(self.a, weights=self.ww, minlength=self.n)
        self.cnt = np.bincount(self.a, minlength=self.n).astype(float)

    def nbr_sum(self, X, weighted=True):
        """sum_j w_ij X_j for every i (X: (n,) or (n,k))"""
        if X.ndim == 1:
            return np.bincount(self.a, weights=(self.ww if weighted else 1) * X[self.b], minlength=self.n)
        out = np.empty_like(X)
        for k in range(X.shape[1]):
            out[:, k] = np.bincount(self.a, weights=(self.ww if weighted else 1) * X[self.b, k], minlength=self.n)
        return out

    def harmonic(self, X0, free, iters=600, tol=1e-7):
        """Solve L X = 0 on free vertices with X fixed elsewhere (CG, all columns at once). X0: (n,k)."""
        X = X0.copy()
        fi = free.astype(float)[:, None]
        def A(P):          # (D - Wadj) restricted to free rows/cols; P is zero outside free
            return (self.deg[:, None] * P - self.nbr_sum(P)) * fi
        Xb = X * (1 - fi)
        b = self.nbr_sum(Xb) * fi              # rhs = W_fb X_b
        Xf = X * fi
        r = b - A(Xf); p = r.copy(); rs = (r * r).sum(0)
        rs0 = rs.copy() + 1e-30
        for it in range(iters):
            Ap = A(p)
            alpha = rs / np.maximum((p * Ap).sum(0), 1e-30)
            Xf += alpha * p; r -= alpha * Ap
            rn = (r * r).sum(0)
            if (rn / rs0).max() < tol: break
            p = r + (rn / np.maximum(rs, 1e-30)) * p; rs = rn
        return Xb + Xf, it

    def smooth(self, X, mask, cols, passes, lam=0.5):
        """Laplacian smoothing of columns `cols` on vertices `mask`, keeping each vertex's total of those columns."""
        X = X.copy()
        sub = X[:, cols]
        tot = sub.sum(1, keepdims=True)
        for _ in range(passes):
            avg = self.nbr_sum(sub) / np.maximum(self.deg, 1e-9)[:, None]
            # neighbours' share pattern, rescaled to this vertex's total of the group
            at = avg.sum(1, keepdims=True)
            share = np.where(at > 1e-9, avg / np.maximum(at, 1e-9), sub / np.maximum(tot, 1e-9))
            new = (1 - lam) * sub + lam * share * tot
            sub = np.where(mask[:, None], new, sub)
        X[:, cols] = sub
        return X

    def geodesic(self, seeds_d, allowed, iters=400):
        """Bellman-Ford style geodesic distance over edges from seed distances (inf elsewhere), only through `allowed`."""
        d = seeds_d.copy()
        for _ in range(iters):
            cand = d[self.b] + self.ll
            cand[~allowed[self.a]] = np.inf
            m = np.full(self.n, np.inf); np.minimum.at(m, self.a, cand)
            nd = np.minimum(d, m)
            if np.array_equal(nd, d): break
            d = nd
        return d


def limit4(W, floor=0.02):
    W = np.where(W < floor, 0.0, W)
    o = np.argsort(-W, 1)
    np.put_along_axis(W, o[:, 4:], 0.0, 1)
    s = W.sum(1, keepdims=True)
    return W / np.maximum(s, 1e-12)


def build(W0, rest, E, names, verbose=True, P=None):
    P = dict(G0=0.05, G1=0.20, G1_low=0.55, hair_top=5.95, zj_rise=0.45, smooth_band=8, smooth_hair=6, wpow=0.0, zb_y=-0.35, zb_z=5.00) | (P or {})
    I = {k: i for i, k in enumerate(names)}
    n, nb = W0.shape
    G = Graph(rest, E, P['wpow'])
    x, y, z = rest.T; ax = np.abs(x)
    hair = [I[k] for k in names if k.startswith('hair_')]
    low = [I['hair_l_03'], I['hair_r_03']]
    armL = [I[k] for k in ('upper_arm_l', 'forearm_l', 'hand_l')]; armR = [I[k] for k in ('upper_arm_r', 'forearm_r', 'hand_r')]
    arm_sum = W0[:, armL + armR].sum(1)
    dom = W0.argmax(1)
    snake = np.isin(dom, hair)
    skin = np.isin(dom, [I[k] for k in ('spine_02', 'spine_03', 'shoulder_l', 'shoulder_r', 'upper_arm_l', 'upper_arm_r')])

    # ---- snake geodesics: ring = snake vertices touching non-snake vertices
    ring = np.zeros(n, bool)
    e0, e1 = E[:, 0], E[:, 1]
    cross = snake[e0] != snake[e1]
    ring[e0[cross & snake[e0]]] = True; ring[e1[cross & snake[e1]]] = True
    seeds = np.where(ring, 0.0, np.inf)
    g_in = G.geodesic(seeds, snake)                        # distance along the snake from its root ring (over mesh edges)
    near = (z > 5.0) & (ax > 0.25)
    g_out = G.geodesic(seeds, ~snake & near, iters=60)      # distance into the hair mass from the ring
    lab = np.where(snake, dom, -1)                          # root zone in the hair mass takes the label of the nearest snake
    for _ in range(60):
        cand_lab = lab[G.b]; ok = (cand_lab >= 0) & (lab[G.a] < 0) & (~snake[G.a]) & near[G.a] & (g_out[G.a] <= P['G0'])
        if not ok.any(): break
        lab_new = lab.copy(); lab_new[G.a[ok]] = cand_lab[ok]; lab = lab_new
    sg = np.where(snake, g_in, -g_out)                      # signed: + along the snake, - into the hair mass
    h = np.zeros(n)
    for b in hair:
        sel = lab == b
        g1 = P['G1_low'] if b in low else P['G1']
        h[sel] = S(sg[sel], -P['G0'], g1)
    h[~np.isfinite(h)] = 0.0

    def onehot(b):
        r = np.zeros(nb); r[I[b]] = 1.0; return r
    # ---- stage A: harmonic weights for every bone between anchor sets (snakes free = they inherit their root)
    fixed = np.zeros(n, bool); X = np.zeros((n, nb)); cnt = {}
    def fix(name, mask, row=None):
        nonlocal fixed
        m = mask & ~fixed
        X[m] = W0[m] if row is None else row
        fixed |= m; cnt[name] = int(m.sum())
    fix('torso_low', z <= 4.50)
    fix('arms', (ax >= 0.84) & (arm_sum >= 0.6) & ~snake)
    zj = 5.48 + P['zj_rise'] * S(y, -1.0, -0.5)                  # jaw line: chin 5.48 at the front, rising toward the back of the skull
    head_core = ~snake & (lab < 0) & (((z > zj) & (y < -0.30) & (ax < 0.62)) | (z > P['hair_top']))
    fix('head', head_core, onehot('head'))
    neck_ring = (z > 5.25) & (z < 5.31) & (y < -0.78) & (ax < 0.22)
    fix('neck', neck_ring, onehot('neck'))
    fix('chest', (z > 4.93) & (z < 5.06) & (y < -1.0) & (ax < 0.30), onehot('spine_03'))
    fix('upper_back', (z > 4.62) & (z < 4.80) & (y > -0.62) & (ax < 0.45), onehot('spine_03'))
    for s, sg_ in (('l', 1), ('r', -1)):
        fix('clav_' + s, (sg_ * x > 0.50) & (sg_ * x < 0.66) & (z > 5.05) & (z < 5.32) & (y < -0.42) & (y > -0.98) & skin,
            onehot('shoulder_' + s))
    free = ~fixed
    X[free] = 0.0
    WA, it = G.harmonic(X, free)
    WA = np.clip(WA, 0, None); WA /= WA.sum(1, keepdims=True)
    # clavicles / upper arms stay on their own side (soft)
    WA[:, I['shoulder_l']] *= S(x, 0.0, 0.12); WA[:, I['shoulder_r']] *= S(-x, 0.0, 0.12)
    WA[:, I['upper_arm_l']] *= S(x, 0.15, 0.3); WA[:, I['upper_arm_r']] *= S(-x, 0.15, 0.3)
    WA /= WA.sum(1, keepdims=True)

    # ---- stage A2: the neck+head share phi as its own harmonic field: 0 on the shoulder tops (|x| > 0.38, z < 5.2),
    # the chest, the upper back and everything below z 4.95; 1 on the head core and the neck ring
    nh = [I['neck'], I['head']]
    zero = (~snake & (z < 4.95)) | (skin & (ax > 0.38) & (z < np.where(y < P['zb_y'], 5.20, P['zb_z']))) | ((ax >= 0.84) & (arm_sum >= 0.6))
    zero |= (z > 4.93) & (z < 5.06) & (y < -1.0) & (ax < 0.30)
    one = head_core | neck_ring
    zero &= ~one
    fixed2 = zero | one
    ph0 = np.where(one, 1.0, 0.0)[:, None]
    phi, it2 = G.harmonic(ph0, ~fixed2)
    phi = np.clip(phi[:, 0], 0, 1)
    nh_now = WA[:, nh].sum(1); rest_now = 1 - nh_now
    ratio = np.where(nh_now[:, None] > 1e-6, WA[:, nh] / np.maximum(nh_now, 1e-9)[:, None], np.array([[0.5, 0.5]]))
    W = WA.copy()
    others = np.ones(nb, bool); others[nh] = False
    W[:, others] *= np.where(rest_now > 1e-6, (1 - phi) / np.maximum(rest_now, 1e-9), 0.0)[:, None]
    # vertices that had no non-neck/head weight but must give some: spine_03
    gap = (rest_now <= 1e-6) & (phi < 1)
    W[gap, I['spine_03']] += 1 - phi[gap]
    W[:, nh] = ratio * phi[:, None]
    W /= W.sum(1, keepdims=True)
    if verbose: print('###ANCHORS', cnt, 'free', int(free.sum()), 'CG', it, it2)

    # ---- stage B: hair ramps 0 -> 1 along each snake (geodesic), full snake beyond the ramp
    for b in hair:
        sel = np.nonzero(lab == b)[0]
        hb = h[sel][:, None]
        W[sel] *= (1 - hb)
        W[sel, b] += hb[:, 0]
    # lowest snakes: no hair weight below z 5.25 on vertices that carry shoulder / spine weight (soft)
    ss = W[:, [I['spine_03'], I['spine_02'], I['shoulder_l'], I['shoulder_r']]].sum(1)
    for b in low:
        cut = (1 - S(z, 5.20, 5.30)) * S(ss, 0.0, 0.05) * (~snake)
        moved = W[:, b] * cut
        W[:, b] -= moved; W[:, I['head']] += moved

    # ---- restricted smoothing (soft, keeps each vertex's total of the smoothed group)
    band = (ax > 0.28) & (ax < 0.85) & (z > 4.55) & (z < 5.35) & ~snake
    for s in ('l', 'r'):
        cols = [I['spine_03'], I['shoulder_' + s], I['upper_arm_' + s]]
        W = G.smooth(W, band & ((x > 0) if s == 'l' else (x < 0)), cols, P['smooth_band'])
    for b in hair:
        sel = (lab == b) & (np.abs(sg) < 0.45)
        W = G.smooth(W, sel, [I['head'], b], P['smooth_hair'])
    W = limit4(W)
    return W, dict(WA=WA, phi=phi, h=h, lab=lab, sg=sg, snake=snake, fixed=fixed)
