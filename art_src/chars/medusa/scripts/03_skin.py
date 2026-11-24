"""03: robust skin weights in numpy (no bone heat).
 1 label every vertex with its nearest bone segment (region rules for hair / snakes / back hair),
 2 relabel islands of a label that are not connected to that label's main body (classic spike source),
 3 weights = inverse-distance^P over the label's allowed set (itself, parent, children, siblings),
 4 surface (graph) smoothing, limit 4 influences, normalise, write vertex groups.
 -> work/rig_medusa/03_skin.blend (+ labels.npy, a label-colour attribute for checks)"""
import bpy, os, json, numpy as np
S = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(S)
W = os.path.join(D, '..', '..', '..', 'work', 'rig_medusa')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, '02_bones.blend'))
arm = bpy.data.objects['medusa_rig']; ob = bpy.data.objects['medusa']; me = ob.data
spec = json.load(open(os.path.join(S, 'bones_spec.json')))
bones = [b for b in spec if b['deform']]
names = [b['name'] for b in bones]; idx = {n: i for i, n in enumerate(names)}
parent = {b['name']: b['parent'] for b in spec}
nb = len(bones)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
n = len(co)
ed = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
H = np.array([b['head'] for b in bones]); T = np.array([b['tail'] for b in bones])
# ---- distance to every segment
v = T - H; L2 = (v * v).sum(1)
rel = co[:, None, :] - H[None]
t = np.clip((rel * v[None]).sum(2) / L2[None], 0, 1)
closest = H[None] + t[..., None] * v[None]
dist = np.linalg.norm(co[:, None, :] - closest, axis=2)          # (n, nb)
# ---- region rules (cost multipliers / exclusions)
cost = dist.copy()
ishair = np.array([nm.startswith('hair_') for nm in names])
x, y, z = co[:, 0], co[:, 1], co[:, 2]
# snakes only above the shoulders and outside the face/hair core
no_snake = (z < 5.05) | ((np.abs(x) < 0.42) & (y < -0.3))
cost[np.ix_(no_snake, ishair)] = 1e9
# a snake bone only takes vertices on its own side
for i, nm in enumerate(names):
    if nm.startswith('hair_l'): cost[x < 0.05, i] = 1e9
    if nm.startswith('hair_r'): cost[x > -0.05, i] = 1e9
# back hair (behind the neck/shoulders, above 4.85) rides with the head / neck, never chest or arms
# back hair (behind the neck/shoulders, above 4.85) never rides with the arms/shoulders; it grades spine_03 -> neck -> head
backhair = (z > 4.85) & (y > -0.45) & (np.abs(x) < 0.7)
for nm in names:
    if nm.startswith(('shoulder', 'upper_arm', 'forearm', 'hand')):
        cost[backhair, idx[nm]] = 1e9
# shoulders (clavicles) never take the breast / sternum / hair locks
for nm in ('shoulder_l', 'shoulder_r'):
    cost[(np.abs(x) < 0.3) | (z > 5.25) | (y < -1.05), idx[nm]] = 1e9
# arms never take the hair locks that hang over the shoulders
for nm in names:
    if nm.startswith(('upper_arm', 'forearm', 'hand')):
        cost[z > 5.15, idx[nm]] = 1e9
# arms never take the torso/skirt core, the torso never takes the arms beyond the shoulder
armb = np.array([nm.startswith(('upper_arm', 'forearm', 'hand')) for nm in names])
cost[np.ix_(np.abs(x) < 0.5, armb)] = 1e9
# tail bones never take vertices above the hips; arm/head bones never take tail vertices
tailb = np.array([nm.startswith('tail_') for nm in names])
cost[np.ix_(z > 3.9, tailb)] = 1e9
# the chest / bust in front never rides with the neck or head; the head never goes below the neck except back hair
cost[(z < 5.22) & (y < -1.0), idx['neck']] = 1e9
cost[(z < 5.22) & (y < -1.0), idx['head']] = 1e9
cost[(z < 5.15) & ~backhair, idx['head']] = 1e9
# the neck only takes the neck itself, not the tops of the shoulders
cost[(np.abs(x) > 0.36) & (z < 5.35), idx['neck']] = 1e9
# snakes keep out of the hair mass behind/beside the head unless very close to their own segment
for i, nm in enumerate(names):
    if nm.startswith('hair_'):
        cost[(np.abs(x) < 0.55) & (dist[:, i] > 0.14), i] = 1e9
lab = np.argmin(cost, 1)
# ---- island cleanup: for each label keep the component that holds most of its vertices
adj_a = np.concatenate([ed[:, 0], ed[:, 1]]); adj_b = np.concatenate([ed[:, 1], ed[:, 0]])
order = np.argsort(adj_a); adj_a = adj_a[order]; adj_b = adj_b[order]
start = np.searchsorted(adj_a, np.arange(n + 1))
def comps(mask):
    comp = -np.ones(n, dtype=np.int64); c = 0
    for s in np.nonzero(mask)[0]:
        if comp[s] >= 0: continue
        stack = [s]; comp[s] = c
        while stack:
            u = stack.pop()
            for w in adj_b[start[u]:start[u + 1]]:
                if mask[w] and comp[w] < 0:
                    comp[w] = c; stack.append(w)
        c += 1
    return comp, c
moved = 0
for it in range(4):
    changed = 0
    for b in range(nb):
        m = lab == b
        if not m.any(): continue
        comp, c = comps(m)
        if c <= 1: continue
        sizes = np.bincount(comp[m], minlength=c)
        keep = np.argmax(sizes)
        bad = np.nonzero(m & (comp != keep))[0]
        # relabel each stray vertex to the most common neighbour label (iterate until stable)
        lab[bad] = -1
        changed += len(bad)
    for _ in range(200):
        un = np.nonzero(lab < 0)[0]
        if len(un) == 0: break
        for u in un:
            nl = lab[adj_b[start[u]:start[u + 1]]]; nl = nl[nl >= 0]
            if len(nl):
                vals = np.bincount(nl, minlength=nb)
                # prefer the cheapest allowed among neighbour labels
                cand = np.nonzero(vals)[0]
                cand = cand[cost[u, cand] < 1e8]
                if len(cand):
                    lab[u] = cand[np.argmin(cost[u, cand])]
    un = lab < 0
    lab[un] = np.argmin(cost[un], 1)
    moved += changed
    if changed == 0: break
print('###ISLANDS relabelled', moved)
# ---- allowed sets
nbr = {nm: {nm} for nm in names}
for nm in names:
    p = parent[nm]
    if p in idx:
        nbr[nm].add(p); nbr[p].add(nm)
for nm in names:   # siblings (children of the same parent), e.g. tail_01 / spine_01, shoulders / neck
    p = parent[nm]
    for o in names:
        if parent[o] == p and p in idx: nbr[nm].add(o)
for nm in names:
    if nm.startswith('hair_'): nbr[nm] = {nm, 'head'}
nbr['head'] = {'head', 'neck'} | {o for o in names if o.startswith('hair_')}
allowed = np.zeros((nb, nb), bool)
for nm in names:
    for o in nbr[nm]: allowed[idx[nm], idx[o]] = True
P = 4.0
mask = allowed[lab]                                   # (n, nb)
mask &= cost < 1e8
bad = ~mask.any(1)
print('###EMPTY-MASK vertices', int(bad.sum()), 'labels', sorted({names[l] for l in lab[bad]}))
mask[bad, np.argmin(cost[bad], 1)] = True
dd = np.maximum(dist, 0.02)
w = np.where(mask, dd ** -P, 0.0)
w /= w.sum(1, keepdims=True)
# ---- tail: hat-function weights along the chain (linear blend between neighbouring segment midpoints) for wide, even
# blends; the top half of tail_01 keeps the inverse-distance blend into pelvis / spine
tidx = [idx[f'tail_{i+1:02d}'] for i in range(14)]
pos_in_chain = {b: k for k, b in enumerate(tidx)}
istail = np.isin(lab, tidx)
for u in np.nonzero(istail)[0]:
    k = pos_in_chain[lab[u]]
    sp = k + t[u, lab[u]]
    if sp < 0.5:
        continue
    row = np.zeros(nb)
    if sp >= 13.5:
        row[tidx[13]] = 1.0
    else:
        c = np.floor(sp - 0.5); f = sp - 0.5 - c; c = int(c)
        row[tidx[c]] = 1 - f; row[tidx[c + 1]] = f
    w[u] = row
# ---- back hair: grade from chest/neck (bottom, z 4.95) to head (z 5.65) so a head turn spreads the stretch over
# the whole hanging mass instead of tearing one band under the snakes
bh = backhair & ~np.isin(lab, np.nonzero(ishair)[0])
wh = np.clip((z[bh] - 4.95) / 0.70, 0, 1); wh = wh * wh * (3 - 2 * wh)
w[bh] = 0.0
w[bh, idx['head']] = wh; w[bh, idx['neck']] = (1 - wh) * 0.5; w[bh, idx['spine_03']] = (1 - wh) * 0.5
# ---- graph smoothing (keeps blends on the surface, never through the air between parts)
deg = np.bincount(ed.ravel(), minlength=n).astype(float)
for _ in range(int(os.environ.get('SMOOTH', 10))):
    acc = np.zeros_like(w)
    np.add.at(acc, ed[:, 0], w[ed[:, 1]]); np.add.at(acc, ed[:, 1], w[ed[:, 0]])
    w = 0.5 * w + 0.5 * acc / np.maximum(deg, 1)[:, None]
# ---- re-apply the region rules as hard limits after smoothing
forbid = cost >= 1e8
forbid[backhair, idx['neck']] = False; forbid[backhair, idx['head']] = False
w[forbid] = 0.0
empty = w.sum(1) <= 0
w[empty, np.argmin(cost[empty], 1)] = 1.0
w /= w.sum(1, keepdims=True)
# ---- limit 4, prune tiny, normalise
w[w < 0.01] = 0
o = np.argsort(-w, 1)
cut = o[:, 4:]
np.put_along_axis(w, cut, 0.0, 1)
w /= w.sum(1, keepdims=True)
np.save(os.path.join(W, 'labels.npy'), lab); np.save(os.path.join(W, 'weights.npy'), w)
assert np.isfinite(w).all(), 'NaN weights'
print('###MAXINF', int((w > 0).sum(1).max()), 'zero', int((w.sum(1) == 0).sum()))
ob.vertex_groups.clear()
for b in range(nb):
    g = ob.vertex_groups.new(name=names[b])
    nz = np.nonzero(w[:, b])[0]
    for val in np.unique(np.round(w[nz, b], 4)):
        pass
    for i in nz:
        g.add([int(i)], float(w[i, b]), 'REPLACE')
# label colours for checks
base = np.array([[1,.2,.2],[.2,.8,.2],[.2,.4,1],[1,.85,.1],[.9,.3,.9],[.1,.85,.85],[1,.55,.1],[.55,.3,.1]])
pal = np.array([base[i % len(base)] for i in range(nb)])
attr = me.color_attributes.new('label', 'FLOAT_COLOR', 'POINT')
cols = np.ones((n, 4)); cols[:, :3] = pal[lab]
attr.data.foreach_set('color', cols.ravel())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, '03_skin.blend'))
