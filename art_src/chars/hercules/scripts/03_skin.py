"""Step 3: repair the Meshy auto-weights. Loads work/hercules_02_cls.blend, saves work/hercules_03_skin.blend.

Repairs (numbers in PARAMS):
 A. tunic armholes: cloth vertices above the belt lose their upper-arm weight (it went into the shoulder above the
    armpit, into spine_02 below it) -> no more tunic "wings" when the arms rise / swing forward.
 B. skirt: cloth below the belt keeps at most LEG_TOP..LEG_HEM of thigh weight (belt -> hem), rest goes to hips,
    so a lifted leg does not tear the skirt open between the thighs.
 C. Laplacian smoothing of the weights in the repaired regions (+ the hidden inner thigh skin under the skirt),
    then max 4 influences, normalised.
"""
import bpy, os, json, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = dict(BELT_Z=1.05, HEM_Z=0.67, ARMPIT_Z=1.40, LEG_TOP=1.0, LEG_HEM=1.0, CROTCH_X=0.07, CROTCH_HIPS=0.6, SMOOTH_IT=8, SMOOTH_A=0.5, ARM_D=0.07, ARM_KEEP=0.8)
_extra = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if _extra:
    P.update(json.loads(_extra[0]))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_02_cls.blend'))
ob = bpy.data.objects['hercules']; me = ob.data; nv = len(me.vertices)
names = [g.name for g in ob.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
W0 = W.copy()
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
cls = np.zeros(nv, np.int32); me.attributes['cls'].data.foreach_get('value', cls)
ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
z = co[:, 2]; cloth = cls == 1

# --- A. tunic armholes: keep a little upper-arm weight on cloth right at the armhole edge (geodesic falloff
#     over ARM_D metres from the arm skin) so the armpit stretch is spread over many triangles, zero beyond.
import heapq
nbw = [[] for _ in range(nv)]
for a_, b_ in ed:
    d_ = float(np.linalg.norm(co[a_] - co[b_])); nbw[a_].append((b_, d_)); nbw[b_].append((a_, d_))
def geodesic(seeds, limit):
    dist = np.full(nv, np.inf); h = []
    for s_ in seeds:
        dist[s_] = 0.0; h.append((0.0, int(s_)))
    heapq.heapify(h)
    while h:
        d_, u = heapq.heappop(h)
        if d_ > dist[u] or d_ > limit:
            continue
        for v_, w_ in nbw[u]:
            nd = d_ + w_
            if nd < dist[v_]:
                dist[v_] = nd; heapq.heappush(h, (nd, v_))
    return dist
for s in 'lr':
    ua = gi[f'upper_arm_{s}']
    m = cloth & (z > P['BELT_Z'])
    seeds = np.where((cls == 0) & (W[:, ua] > 0.3))[0]
    dist = geodesic(seeds, P['ARM_D'])
    keepf = np.clip(1 - dist / P['ARM_D'], 0, 1) ** 2 * P['ARM_KEEP']
    take = W[m, ua] * (1 - keepf[m])
    hi = z[m] > P['ARMPIT_Z']
    tgt = np.where(hi, gi[f'shoulder_{s}'], gi['spine_02'])
    W[m, ua] -= take
    np.add.at(W, (np.where(m)[0], tgt), take)
    for b in ('forearm', 'hand'):
        W[m, gi[f'{b}_{s}']] = 0
regionA = cloth & (z > P['BELT_Z'] - 0.02) & (np.abs(co[:, 0]) > 0.08) & (z > 1.15)

# --- B. skirt
legs = [gi[n] for n in names if n.startswith(('thigh_', 'shin_', 'foot_', 'toe_'))]
beltm = np.zeros(nv, bool)   # belt left as Meshy weighted it (smoothing it pulled thigh weight up into the belt)
m = (cloth & (z < P['BELT_Z'])) | beltm
t = np.clip((P['BELT_Z'] - z[m]) / (P['BELT_Z'] - P['HEM_Z']), 0, 1)
t = t * t * (3 - 2 * t)
cap = P['LEG_TOP'] + (P['LEG_HEM'] - P['LEG_TOP']) * t
Lsum = W[m][:, legs].sum(1)
f = np.where(Lsum > cap, cap / np.maximum(Lsum, 1e-9), 1.0)
idx = np.where(m)[0]
moved = Lsum * (1 - f)
for j in legs:
    W[idx, j] *= f
W[idx, gi['hips']] += moved
# crotch seam: where the two thighs meet under the skirt, hand part of the leg weight to the hips
crotch = (cls == 0) & (z > 0.76) & (z < 1.0) & (np.abs(co[:, 0]) < P['CROTCH_X'])
fc = 1 - P['CROTCH_HIPS'] * (1 - np.abs(co[crotch, 0]) / P['CROTCH_X'])
ci = np.where(crotch)[0]
Lc = W[ci][:, legs].sum(1)
for j in legs:
    W[ci, j] *= fc
W[ci, gi['hips']] += Lc * (1 - fc)
# hidden skin under the skirt (inner thighs / crotch) joins the skirt smoothing
inner = (cls == 0) & (z > P['HEM_Z'] - 0.03) & (z < 1.0) & (np.abs(co[:, 0]) < 0.30)
regionB = (cloth & (z < P['BELT_Z'] + 0.03)) | inner | beltm

# --- C. smoothing (Jacobi, only on the region; others act as fixed boundary)
region = regionA | regionB
nb = [[] for _ in range(nv)]
for a_, b_ in ed:
    nb[a_].append(b_); nb[b_].append(a_)
ridx = np.where(region)[0]
deg = np.array([len(nb[i]) for i in ridx])
rows = np.repeat(np.arange(len(ridx)), deg); cols = np.concatenate([nb[i] for i in ridx])
for it in range(P['SMOOTH_IT']):
    acc = np.zeros((len(ridx), W.shape[1]))
    np.add.at(acc, rows, W[cols])
    W[ridx] = (1 - P['SMOOTH_A']) * W[ridx] + P['SMOOTH_A'] * acc / deg[:, None]

# --- limit 4, normalise
order = np.argsort(-W, axis=1)
keep = np.zeros_like(W, bool)
np.put_along_axis(keep, order[:, :4], True, axis=1)
W[~keep] = 0
W[W < 0.005] = 0
W /= W.sum(1, keepdims=True)
assert np.all(W.sum(1) > 0.999)

for g in ob.vertex_groups:
    g.remove(list(range(nv)))
for j, g in enumerate(ob.vertex_groups):
    nz = np.where(W[:, j] > 0)[0]
    for i in nz:
        g.add([int(i)], float(W[i, j]), 'REPLACE')
print('###SKIN', json.dumps({'changed_verts': int((np.abs(W - W0).max(1) > 0.01).sum()), 'regionA': int(regionA.sum()),
      'regionB': int(regionB.sum()), 'max_infl': int((W > 0).sum(1).max()), 'params': P}))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_03_skin.blend'))
