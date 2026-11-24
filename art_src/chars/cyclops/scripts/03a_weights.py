"""Step 3a (plain python3 + numpy): robust skin weights without bone heat.
python3 03a_weights.py <mesh.npz> <joints.json> <out weights.npz>

1. cost(v, bone) = geodesic-ish distance: start from K * euclidean distance to the bone SEGMENT and relax along mesh
   edges (cost(v) = min(cost(v), cost(u) + |uv|)), so a bone only reaches a vertex cheaply through the surface.
   This keeps the lower arm off the upper arm (the path runs around the armpit) and legs off each other.
2. falloff: bones within BAND of the cheapest bone compete: w = (1 - (c - cmin)/BAND)^2.
3. side rules: _l bones get nothing at x < -0.05, _r bones nothing at x > 0.05 (smoothing handles the seam).
4. region fixes (beard follows the head, crotch/skirt blends hips + both thighs).
5. Laplacian smoothing rounds, keep 4 strongest, normalise.
"""
import sys, json, numpy as np

mesh, jfile, out = sys.argv[1:4]
d = np.load(mesh); co = d['co']; E = d['edges']
J = json.load(open(jfile))
bones = [b for b in J['bones'] if b['deform']]
names = [b['name'] for b in bones]
V, B = len(co), len(bones)
H = np.array([b['head'] for b in bones]); T = np.array([b['tail'] for b in bones])
K, BAND, SMOOTH_IT, SMOOTH_A = 3.0, 0.65, 12, 0.5
# bone radius (metres, from the slices): costs are measured in bone radii so the wide torso bones are not beaten by
# a thin limb bone whose head sits closer to the torso surface
RAD = {'hips': 1.0, 'spine_01': 1.0, 'spine_02': 1.0, 'spine_03': 1.15, 'neck': 0.7, 'head': 0.6,
       'shoulder_u': 0.42, 'upper_arm_u': 0.38, 'forearm_u': 0.32, 'hand_u': 0.35,
       'upper_arm_d': 0.33, 'forearm_d': 0.33, 'hand_d': 0.35,
       'thigh': 0.50, 'shin': 0.45, 'foot': 0.35, 'toe': 0.30}
rad = np.array([RAD[n[:-2] if n[-2:] in ('_l', '_r') else n] for n in names])


def seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


eu = np.stack([seg_dist(co, H[i], T[i]) for i in range(B)], axis=1)   # V x B
# walking along the surface costs the same for every bone (in limb radii), otherwise the wide torso bones would
# reach far down the legs/arms through the surface
el = (np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1) / 0.35)[:, None]
c = K * eu / rad[None, :]
for it in range(600):
    a = c[E[:, 0]] + el; b = c[E[:, 1]] + el
    n = c.copy()
    np.minimum.at(n, E[:, 1], a); np.minimum.at(n, E[:, 0], b)
    ch = np.abs(n - c).max()
    c = n
    if ch < 1e-6:
        break
print('relax iterations', it + 1)

# side rules
x = co[:, 0]
for i, nm in enumerate(names):
    if nm.endswith('_l'):
        c[x < -0.05, i] = 1e9
    elif nm.endswith('_r'):
        c[x > 0.05, i] = 1e9

cmin = c.min(1, keepdims=True)
w = np.clip(1 - (c - cmin) / BAND, 0, 1) ** 2

idx = {nm: i for i, nm in enumerate(names)}
z, y = co[:, 2], co[:, 1]

def smoothstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

# beard + face: front of the head region rides the head (nod without stretching the beard)
beard = (z > 6.35) & (np.abs(x) < 0.8) & (y < 0.05)
fb = smoothstep(6.35, 6.75, z) * beard
for nm in ('spine_03', 'neck', 'shoulder_u_l', 'shoulder_u_r'):
    w[:, idx[nm]] *= (1 - fb)
w[:, idx['head']] += fb * 1.0

# crotch / skirt band: between z 2.45 and 3.05 near the middle, share hips + both thighs
cr = (np.abs(x) < 0.45) & (z > 2.3) & (z < 3.1)
fc = (1 - smoothstep(0.15, 0.45, np.abs(x))) * smoothstep(2.3, 2.6, z) * (1 - smoothstep(2.85, 3.1, z)) * cr
side_l = smoothstep(-0.3, 0.3, x)
wh = w.copy()
wh[:, :] *= (1 - fc)[:, None]
wh[:, idx['hips']] += fc * 0.5
wh[:, idx['thigh_l']] += fc * 0.5 * side_l
wh[:, idx['thigh_r']] += fc * 0.5 * (1 - side_l)
w = wh

w /= w.sum(1, keepdims=True)

# smoothing over the edge graph
deg = np.bincount(E[:, 0], minlength=V) + np.bincount(E[:, 1], minlength=V)
for _ in range(SMOOTH_IT):
    acc = np.zeros_like(w)
    np.add.at(acc, E[:, 0], w[E[:, 1]]); np.add.at(acc, E[:, 1], w[E[:, 0]])
    avg = acc / np.maximum(deg, 1)[:, None]
    w = (1 - SMOOTH_A) * w + SMOOTH_A * avg
    # keep side rules hard
    for i, nm in enumerate(names):
        if nm.endswith('_l'):
            w[x < -0.05, i] = 0
        elif nm.endswith('_r'):
            w[x > 0.05, i] = 0
    w /= w.sum(1, keepdims=True)

# 6. chain banding (review fix 11-22): the smoothing smeared the limb chains (forearm_u never above 0.41, thigh weight
#    on the heel). Inside each limb chain the chain's total weight S is kept, but it is re-split between the chain bones
#    by joint PLANES: plane normal = bisector of the two bone directions (or given), linear blend over +-hw metres.
#    w_i = prod_{k<i} s_k * (1 - s_i), s_k = clip(0.5 + d_k / (2 hw_k)), d_k = signed distance past joint k.
JJ = J['joints']
import os
HW = {'elbow_u': 0.25, 'wrist_u': 0.12, 'elbow_d': 0.35, 'wrist_d': 0.15, 'knee': 0.25, 'ankle': 0.15, 'ball': 0.10}
# blend centre shift along the plane normal (negative = towards the parent bone)
SH = {'elbow_u': -0.10, 'elbow_d': 0.0}   # elbow_u blend 1.87..2.37: forearm_u = 1 from |x| 2.37 to 2.90
HW.update(json.loads(os.environ.get('HW_JSON', '{}')))     # experiments only
SH.update(json.loads(os.environ.get('SH_JSON', '{}')))
def mir(p, k):
    return np.array([p[0] * k, p[1], p[2]], float)
def band_chain(chain, joints, hws, normals=None, shifts=None):
    ci = [idx[n] for n in chain]
    S = w[:, ci].sum(1)
    m = S > 0
    P = co[m]
    s_list = []
    for k, (jp, hw) in enumerate(zip(joints, hws)):
        a = H[ci[k + 1]] - H[ci[k]]; b = T[ci[k + 1]] - H[ci[k + 1]]
        n = (normals[k] if normals and normals[k] is not None else a / np.linalg.norm(a) + b / np.linalg.norm(b))
        n = np.asarray(n, float); n = n / np.linalg.norm(n)
        d = (P - jp) @ n - (shifts[k] if shifts else 0.0)
        s_list.append(np.clip(0.5 + d / (2 * hw), 0, 1))
    acc = np.ones(len(P))
    for i in range(len(chain)):
        si = s_list[i] if i < len(s_list) else np.zeros(len(P))
        w[m, ci[i]] = S[m] * acc * (1 - si)
        acc = acc * si
for s, k in (('l', 1), ('r', -1)):
    # upper arm pair: forearm_u = 1 between |x| 2.37 and 2.90 (elbow blend widened on the upper-arm side, wrist +-0.12)
    band_chain([f'upper_arm_u_{s}', f'forearm_u_{s}', f'hand_u_{s}'],
               [mir(JJ['elbow_u'], k), mir(JJ['wrist_u'], k)], [HW['elbow_u'], HW['wrist_u']],
               shifts=[SH['elbow_u'], 0.0])
    band_chain([f'upper_arm_d_{s}', f'forearm_d_{s}', f'hand_d_{s}'],
               [mir(JJ['elbow_d'], k), mir(JJ['wrist_d'], k)], [HW['elbow_d'], HW['wrist_d']],
               shifts=[SH['elbow_d'], 0.0])
    # leg: knee +-0.25 (thigh 0 below ~1.95), ankle +-0.15 on the shin/foot bisector, ball on a y plane (toe 1 for
    # y < -0.55, 0 for y > -0.35)
    band_chain([f'thigh_{s}', f'shin_{s}', f'foot_{s}', f'toe_{s}'],
               [mir(JJ['knee'], k), mir(JJ['ankle'], k), mir(JJ['ball'], k)], [HW['knee'], HW['ankle'], HW['ball']],
               normals=[None, None, (0, -1, 0)])

# 7. posterior armpit (review fix 11-22): the strip between the lower-arm root and the upper shoulder stretched 2-8x
#    when the upper arms rise. (a) the lower-arm root rides its own bone: upper_arm_d chain >= 0.5..0.7 over its first
#    0.2 m along the bone, >= 0.7..1.0 from 0.2 to 0.45 m (inside r 0.5 m, only where it already owns >= 0.3);
#    (b) on the back above z 5.5 upper_arm_d fades out by z 5.9 and spine_03 takes it; (c) 14 local smoothing
#    rounds over the back strip spread the shoulder_u <-> upper_arm_d <-> spine_03 blend over ~0.4 m.
ARMPIT = os.environ.get('ARMPIT', '1') == '1'
ROOT_D = os.environ.get('ROOT_D', '0') == '1'   # (a) off: it moved the stretch to the torso side under the lower arm
if ARMPIT:
    for s, k in (('l', 1), ('r', -1)):
        cd = [idx[f'upper_arm_d_{s}'], idx[f'forearm_d_{s}'], idx[f'hand_d_{s}']]
        h0 = mir(JJ['shoulder_d'], k); a = mir(JJ['elbow_d'], k) - h0; a /= np.linalg.norm(a)
        t = (co - h0) @ a; r = np.linalg.norm((co - h0) - np.outer(t, a), axis=1)
        Sd = w[:, cd].sum(1)
        tmin = np.where(t < 0.2, 0.5 + 0.2 * smoothstep(0.0, 0.2, t), 0.7 + 0.3 * smoothstep(0.2, 0.45, t))
        m = (t > 0) & (t < 0.45) & (r < 0.5) & (Sd >= 0.3) & (Sd < tmin)
        if ROOT_D and m.any():
            gain = tmin[m] / Sd[m]
            others = [j for j in range(B) if j not in cd]
            rest = w[m][:, others].sum(1)
            w[np.ix_(m, cd)] *= gain[:, None]
            w[np.ix_(m, others)] *= ((1 - tmin[m]) / np.maximum(rest, 1e-9))[:, None]
        back = (k * x > 0.8) & (k * x < 1.9) & (y > 0.4)
        cap = 1 - smoothstep(5.5, 5.9, z)
        ud = idx[f'upper_arm_d_{s}']
        mb = back & (w[:, ud] > cap)
        ex = w[mb, ud] - cap[mb]
        w[mb, ud] -= ex; w[mb, idx['spine_03']] += ex
        reg = (k * x > 0.75) & (k * x < 1.95) & (y > 0.25) & (z > 5.45) & (z < 6.35)
        for _ in range(14):
            acc = np.zeros_like(w)
            np.add.at(acc, E[:, 0], w[E[:, 1]]); np.add.at(acc, E[:, 1], w[E[:, 0]])
            avg = acc / np.maximum(deg, 1)[:, None]
            w[reg] = 0.5 * w[reg] + 0.5 * avg[reg]
            w[reg] /= w[reg].sum(1, keepdims=True)

# limit 4 + prune tiny
order = np.argsort(-w, axis=1)
keep = np.zeros_like(w, bool)
np.put_along_axis(keep, order[:, :4], True, axis=1)
w = np.where(keep, w, 0); w[w < 0.01] = 0
w /= w.sum(1, keepdims=True)
nz = (w > 0).sum(1)
print('influences per vertex: max', nz.max(), 'mean', round(nz.mean(), 2), 'unweighted', int((w.sum(1) == 0).sum()))
dom = np.argmax(w, 1)
print('dominant counts', {names[i]: int((dom == i).sum()) for i in range(B)})
np.savez(out, w=w.astype(np.float32), names=np.array(names))
