"""Step 3a (python3 + numpy): skin weights by PART LABEL + CHAIN PARAMETER, not by nearest bone.
  python3 03a_weights.py <clean.npz> <bones.json> <out_weights.npz>
1. every vertex gets one part (body, tail, 4 legs, 9 necks) = the part whose centre line is nearest, distance divided
   by that bone's typical radius (so a thin neck does not lose its skin to the fat chest);
   necks: nearest neck CENTRE LINE (base -> head tip), so touching necks never share skin;
2. islands of a label that are not connected to the label's main region are relabelled from their neighbours;
3. inside a part the weight comes from the arc parameter along the chain (joint blends of `f` bone lengths);
   the first bone blends into the parent bone (spine_03 / hips) below its head;
4. part-aware smoothing (edges between two different necks or two legs never carry weight), limit 4, normalise.
Fix round 1 (rig review): the rear centre tube is deleted from the mesh (01b_trim.py), so its height-riding code is
gone; the body 'ext' segment behind the hips is gone and the tail root is blended hips -> tail_01 -> tail_02 along the
tail axis (no horizontal split); body skin around the four leg sockets takes a share of leg_*_01 (wider hip/shoulder
blend); the chest in front of the centre neck takes a small neck_c_01 share and spine_03 reaches ~1 m up neck_c_01."""
import numpy as np, json, sys
d = np.load(sys.argv[1]); co, E, med, th = d['co'], d['E'], d['med'], d['th']
bones = json.load(open(sys.argv[2])); BI = {b['name']: i for i, b in enumerate(bones)}
H = {b['name']: np.array(b['head']) for b in bones}; T = {b['name']: np.array(b['tail']) for b in bones}
n = len(co); S = 16.25

parts = {}   # name: dict(chain=[bones], parent=bone|None, f=blend, ext=[(p0,p1,bone,t0,t1)])
parts['body'] = dict(chain=['hips', 'spine_01', 'spine_02', 'spine_03'], parent=None, f=0.5,
                     ext=[(T['spine_03'], np.array([0, -3.6, 4.6]), 'spine_03', 1, 1)])
parts['tail'] = dict(chain=[f'tail_{i:02d}' for i in range(1, 9)], parent='hips', f=0.5, ext=[])
for s in ('fr', 'fl', 'br', 'bl'):
    parts['leg_' + s] = dict(chain=[f'leg_{s}_01', f'leg_{s}_02', f'leg_{s}_03', f'foot_{s}'],
                             parent='spine_03' if s[0] == 'f' else 'hips', f=0.3, ext=[])
for k in '12345678':
    hd = f'head_{k}'; tip = T[hd] + (T[hd] - H[hd]) * 0.25
    parts['neck_' + k] = dict(chain=[f'neck_{k}_{i:02d}' for i in range(1, 5)] + [hd], parent='spine_03', f=0.5,
                              ext=[(T[hd], tip, hd, 1, 1)])
hc = 'head_c'; tipc = T[hc] + (T[hc] - H[hc]) * 0.15
parts['neck_c'] = dict(chain=[f'neck_c_{i:02d}' for i in range(1, 6)] + [hc], parent='spine_03', f=0.5, f0=0.9,
                       ext=[(T[hc], tipc, hc, 1, 1)])

# segments table
seg = []   # (part, p0, p1, bone0, t0, bone1, t1)
for pn, P in parts.items():
    for b in P['chain']: seg.append((pn, H[b], T[b], b, 0.0, b, 1.0, True))
    for e in P['ext']:
        if e[2] is None: seg.append((pn, e[0], e[1], e[3][0], e[3][1], e[4][0], e[4][1], False))
        else: seg.append((pn, e[0], e[1], e[2], e[3], e[2], e[4], False))
NS = len(seg)
D = np.empty((n, NS)); U = np.empty((n, NS))
for j, (pn, p0, p1, b0, t0, b1, t1, real) in enumerate(seg):
    v = p1 - p0; L2 = v @ v
    u = ((co - p0) @ v) / L2
    U[:, j] = u
    uc = np.clip(u, 0, 1)
    D[:, j] = np.linalg.norm(co - (p0 + uc[:, None] * v), axis=1)
seg_part = np.array([s[0] for s in seg]); PN = list(parts); seg_pi = np.array([PN.index(p) for p in seg_part])
seg_bone = [s[3] for s in seg]
# radius per segment, 2 rounds
rad = np.ones(NS)
for it in range(3):
    j = np.argmin(D / rad, axis=1)
    for k in range(NS):
        m = j == k
        if m.sum() > 20: rad[k] = max(np.median(D[m, k]), 0.15)
    # extensions inherit the radius of their bone
    for k in range(NS):
        if not seg[k][7]:
            b = seg[k][3]; kk = [q for q in range(NS) if seg[q][7] and seg[q][3] == b]
            if kk: rad[k] = rad[kk[0]]
ND = D / rad
jbest = np.argmin(ND, axis=1)
label = seg_pi[jbest]
# the fat torso must not claim crest spikes / neck skin high above the shoulders
BODY = PN.index('body')
nonbody = np.where(seg_pi != BODY)[0]
hi = (label == BODY) & (co[:, 2] > 7.0)
alt = nonbody[np.argmin(ND[:, nonbody], axis=1)]
take = hi & (D[np.arange(n), alt] < 1.6)
jbest[take] = alt[take]; label = seg_pi[jbest]
print('body->neck reassigned (z>7)', int(take.sum()))
# neck vs neck: decide by the vertex's MEDIAL point (midpoint to the opposite wall = inside its own tube), so the far
# side of a thick neck is not handed to a thin neighbour whose centre line happens to be closer to the surface
NECKP = np.array([p.startswith('neck') for p in PN])
neck_seg = np.where(NECKP[seg_pi])[0]
DM = np.full((n, len(neck_seg)), np.inf)
for c_, j in enumerate(neck_seg):
    _, p0, p1 = seg[j][:3]; v = p1 - p0
    u = np.clip(((med - p0) @ v) / (v @ v), 0, 1)
    DM[:, c_] = np.linalg.norm(med - (p0 + u[:, None] * v), axis=1)
isneck = NECKP[label] & (th > 0) & (th < 2.0)
jm = neck_seg[np.argmin(DM, axis=1)]
ch = isneck & (seg_pi[jm] != label)
jbest[ch] = jm[ch]; label = seg_pi[jbest]
print('neck labels changed by medial test', int(ch.sum()))

# neighbours
nb = [[] for _ in range(n)]
for a, b in E: nb[a].append(b); nb[b].append(a)
def components(mask):
    lab = -np.ones(n, int); c = 0
    for s0 in np.where(mask)[0]:
        if lab[s0] >= 0: continue
        st = [s0]; lab[s0] = c
        while st:
            x = st.pop()
            for y in nb[x]:
                if mask[y] and lab[y] < 0: lab[y] = c; st.append(y)
        c += 1
    return lab, c
moved = 0
for rnd in range(6):
    bad = np.zeros(n, bool)
    for L in range(len(PN)):
        lab, c = components(label == L)
        if c > 1:
            cnt = np.bincount(lab[lab >= 0]); keep = np.argmax(cnt)
            bad |= (lab >= 0) & (lab != keep)
    if not bad.any(): break
    moved += bad.sum()
    for _ in range(50):
        todo = np.where(bad)[0]
        if len(todo) == 0: break
        newl = label.copy()
        for x in todo:
            nl = [label[y] for y in nb[x] if not bad[y]]
            if nl: newl[x] = np.bincount(nl).argmax(); bad[x] = False
        label = newl
print('labels:', {p: int((label == i).sum()) for i, p in enumerate(PN)}, 'island verts relabelled', int(moved))

# weights inside the part
NB = len(bones); W = np.zeros((n, NB))
def chain_w(P, b, t, out, scale=1.0):
    ch = P['chain']; ci = ch.index(b); f = P['f']
    if t > 1: t = 1.0
    if ci > 0 and t < 0: t = 0.0
    if t < f and (ci > 0 or P['parent']):
        prev = ch[ci - 1] if ci > 0 else P['parent']
        f0 = P.get('f0', f) if ci == 0 else f                            # first bone may reach further into its parent
        x = np.clip((t + f0) / (f0 + f), 0, 1); x = x * x * (3 - 2 * x)  # 0 at t=-f0 .. 1 at t=+f
        out[BI[b]] += x * scale; out[BI[prev]] += (1 - x) * scale
    elif t > 1 - f and ci < len(ch) - 1:
        nxt = ch[ci + 1]
        x = np.clip((t - (1 - f)) / (2 * f), 0, 1); x = x * x * (3 - 2 * x)
        out[BI[b]] += (1 - x) * scale; out[BI[nxt]] += x * scale
    else:
        out[BI[b]] += scale
rear_flag = np.zeros(n, bool)      # kept for the npz layout; the rear tube no longer exists in the mesh
for i in range(n):
    pn = PN[label[i]]; P = parts[pn]
    js = np.where(seg_pi == label[i])[0]
    j = js[np.argmin(ND[i, js])]
    _, p0, p1, b0, t0, b1, t1, real = seg[j]
    u = U[i, j]
    if real:
        chain_w(P, b0, u, W[i])
    else:
        uc = float(np.clip(u, 0, 1))
        if b0 == b1: W[i, BI[b0]] += 1
        else: W[i, BI[b0]] += 1 - uc; W[i, BI[b1]] += uc
# tail root: body + tail skin behind the hips gets its weights from the position ALONG the tail axis (hips -> tail_01 ->
# tail_02 ...), not from the part label, so the upper and lower halves of the tail root move together
TAIL = PN.index('tail'); PT = parts['tail']
tl_seg = [(H[b], T[b], b) for b in PT['chain'][:4]]
cand = np.where(np.isin(label, [BODY, TAIL]) & (co[:, 1] > 3.3))[0]
ntr = 0
for i in cand:
    best = None
    for k, (p0, p1, b) in enumerate(tl_seg):
        v = p1 - p0; u = float((co[i] - p0) @ v / (v @ v))
        uc = min(max(u, 0.0 if k else -10.0), 1.0)
        dd = np.linalg.norm(co[i] - (p0 + uc * v))
        if best is None or dd < best[0]: best = (dd, b, u)
    _, b, u = best
    if b == 'tail_04' and u > 0.5: continue          # far enough down the tail: keep the normal tail weights
    if label[i] == BODY and u < -0.9: continue        # well in front of the hips joint: plain body
    W[i] = 0; chain_w(PT, b, u, W[i]); label[i] = TAIL; ntr += 1
print('tail-root verts re-weighted along the tail axis', ntr)
# back of the centre-neck base (the side that faced the deleted rear tube, 1-2 m behind the neck axis): weight it by
# height spine_03 -> neck_c_01 -> neck_c_02 over BB_Z0..BB_Z1, so a forward bend stretches this outer side gradually
# instead of in one row of faces next to neck_4/neck_5
BB_Y, BB_Z0, BB_Z1 = -1.7, 6.6, 9.8
NC = PN.index('neck_c'); bb = np.where((label == NC) & (co[:, 1] > BB_Y) & (co[:, 2] < BB_Z1))[0]
for i in bb:
    t = (co[i, 2] - BB_Z0) / (BB_Z1 - BB_Z0) * 2.0 - 0.5          # -0.5 .. 1.5 over the band (neck_c_01 t-space)
    W[i] = 0; chain_w(parts['neck_c'], 'neck_c_01', min(t, 1.0), W[i]) if t <= 1.0 else chain_w(parts['neck_c'], 'neck_c_02', t - 1.0, W[i])
print('back-of-neck-base verts re-weighted', len(bb))
# jaw: lower part of head_c below the hinge -> chin line
jh, jt = H['jaw_c'], T['jaw_c']
v = jt - jh; nrm = np.array([0, -v[2], v[1]]); nrm /= np.linalg.norm(nrm)      # normal in YZ plane
if nrm[2] > 0: nrm = -nrm                                                       # pointing down
below = (co - jh) @ nrm
along = ((co - jh) @ v) / (v @ v)
hcw = W[:, BI['head_c']]
xj = np.clip((below + 0.02) / 0.2, 0, 1) * np.clip((along + 0.05) / 0.25, 0, 1) * (np.abs(co[:, 0]) < 1.0)
xj = xj * xj * (3 - 2 * xj) * (label == PN.index('neck_c'))
mv = hcw * xj; W[:, BI['head_c']] -= mv; W[:, BI['jaw_c']] += mv
print('jaw verts >0.5:', int((W[:, BI['jaw_c']] > 0.5).sum()))

# soften body <-> leg sockets: body skin near the top of a leg (thigh front / belly, shoulder / chest) takes a share of
# that leg vertex's weights (up to LEG_A at the seam, fading to 0 at LEG_R metres)
LEG_R, LEG_A, LEG_DZ = 1.3, 0.5, 2.4
for s_ in ('fl', 'fr', 'bl', 'br'):
    L = PN.index('leg_' + s_)
    legv = np.where((label == L) & (co[:, 2] > H[f'leg_{s_}_01'][2] - LEG_DZ))[0]
    bv = np.where((label == BODY) & (np.linalg.norm(co - H[f'leg_{s_}_01'], axis=1) < 3.2))[0]
    for i in bv:
        dd = np.linalg.norm(co[legv] - co[i], axis=1); k = np.argmin(dd)
        if dd[k] < LEG_R:
            x = 1 - dd[k] / LEG_R; a_ = LEG_A * x * x * (3 - 2 * x)
            W[i] = (1 - a_) * W[i] + a_ * W[legv[k]]
# chest in front of / under the centre neck base: a small neck_c_01 share (max NC_A at the neck, gone at NC_R metres)
NC_R, NC_A = 1.4, 0.3
ncv = np.where((label == PN.index('neck_c')) & (co[:, 2] < H['neck_c_01'][2] + 1.0))[0]
bv = np.where((label == BODY) & (co[:, 2] > 5.0) & (co[:, 1] < 0.0))[0]
for i in bv:
    dd = np.linalg.norm(co[ncv] - co[i], axis=1); k = np.argmin(dd)
    if dd[k] < NC_R:
        x = 1 - dd[k] / NC_R; a_ = NC_A * x * x * (3 - 2 * x)
        W[i] = (1 - a_) * W[i] + a_ * W[ncv[k]]
# soften body <-> neck junctions: body vertices near a neck take part of that neck vertex's weights
NECKS = [PN.index(p) for p in PN if p.startswith('neck')]
neckv = np.where(np.isin(label, NECKS))[0]
bodyv = np.where((label == BODY) & (co[:, 2] > 5.0))[0]
R = 1.0
for i in bodyv:
    dd = np.linalg.norm(co[neckv] - co[i], axis=1); k = np.argmin(dd)
    if dd[k] < R:
        a_ = 0.5 * (1 - dd[k] / R) ** 2
        W[i] = (1 - a_) * W[i] + a_ * W[neckv[k]]
# part-aware smoothing
par_of = {pn: P['parent'] for pn, P in parts.items()}
def ok_edge(la, lb):
    if la == lb: return True
    a, b = PN[la], PN[lb]
    return (a == 'body' and par_of[b] in parts['body']['chain']) or (b == 'body' and par_of[a] in parts['body']['chain'])
EE = np.array([(a, b) for a, b in E if ok_edge(label[a], label[b])])
print('edges kept for smoothing', len(EE), 'of', len(E))
for it in range(6):
    acc = np.zeros_like(W); cnt = np.zeros(n)
    np.add.at(acc, EE[:, 0], W[EE[:, 1]]); np.add.at(acc, EE[:, 1], W[EE[:, 0]])
    np.add.at(cnt, EE[:, 0], 1); np.add.at(cnt, EE[:, 1], 1)
    m = cnt > 0
    W[m] = 0.5 * W[m] + 0.5 * acc[m] / cnt[m, None]
# extra smoothing rounds limited to the leg sockets and the tail root (all body/leg/tail edges)
reg = np.zeros(n, bool)
for s_ in ('fl', 'fr', 'bl', 'br'): reg |= np.linalg.norm(co - H[f'leg_{s_}_01'], axis=1) < 1.6
reg |= (co[:, 1] > 3.3) & (co[:, 1] < 6.2) & np.isin(label, [BODY, TAIL])
EEr = EE[reg[EE[:, 0]] & reg[EE[:, 1]]]
for it in range(4):
    acc = np.zeros_like(W); cnt = np.zeros(n)
    np.add.at(acc, EEr[:, 0], W[EEr[:, 1]]); np.add.at(acc, EEr[:, 1], W[EEr[:, 0]])
    np.add.at(cnt, EEr[:, 0], 1); np.add.at(cnt, EEr[:, 1], 1)
    m = cnt > 0
    W[m] = 0.5 * W[m] + 0.5 * acc[m] / cnt[m, None]
# the hind thighs are massive (thigh front 1.4 m ahead of the hip joint): many more rounds there, so the hips/spine ->
# leg_b*_01 gradient spreads over ~1 m (a steep gradient is what stretched the thigh front in a walk back-swing)
HIND_R, HIND_IT = 1.8, 40
reg = np.zeros(n, bool)
for s_ in ('bl', 'br'): reg |= np.linalg.norm(co - H[f'leg_{s_}_01'], axis=1) < HIND_R
reg &= ~np.isin(label, NECKS)
EEh = EE[reg[EE[:, 0]] & reg[EE[:, 1]]]
for it in range(HIND_IT):
    acc = np.zeros_like(W); cnt = np.zeros(n)
    np.add.at(acc, EEh[:, 0], W[EEh[:, 1]]); np.add.at(acc, EEh[:, 1], W[EEh[:, 0]])
    np.add.at(cnt, EEh[:, 0], 1); np.add.at(cnt, EEh[:, 1], 1)
    m = cnt > 0
    W[m] = 0.5 * W[m] + 0.5 * acc[m] / cnt[m, None]
# cap over the deleted rear tube (01b_trim.py): each fan centre takes the mean of its ring (neck_c + neck_4 + neck_5
# boundary), so a bending centre neck pulls the cap into a low slope instead of a tall cone on one neighbour's weights
import os
capf = os.path.join(os.path.dirname(os.path.abspath(sys.argv[3])), 'cap.json')
if os.path.exists(capf):
    for c in json.load(open(capf))['cap_centres_co']:
        ci = int(np.argmin(np.linalg.norm(co - np.array(c), axis=1)))
        ring = nb[ci]
        if len(ring) >= 8: W[ci] = W[ring].mean(0)
        label[ci] = BODY
# limit 4, normalise
idx = np.argsort(-W, axis=1)[:, :4]
w4 = np.take_along_axis(W, idx, 1); w4[w4 < 0.01] = 0
w4 /= w4.sum(1, keepdims=True)
print('max infl used', int((w4 > 0).sum(1).max()), 'verts with 0 weight', int((w4.sum(1) == 0).sum()))
np.savez(sys.argv[3], idx=idx, w=w4, label=label, rear=rear_flag, parts=np.array(PN), bones=np.array([b['name'] for b in bones]))
