"""Step 2a (python3 + numpy): solve joint positions from the cleaned mesh -> joints.json.
  python3 02a_joints.py <clean.npz> <joints.json>
Neck centre lines: hand-read control points (front-view medial plot, raw units) refined against the medial-point cloud
(medial point = midpoint of a vertex and the opposite wall along -normal), then mirrored so the rig is symmetric."""
import numpy as np, json, sys
S = 16.25
d = np.load(sys.argv[1]); co, med, th = d['co'], d['med'], d['th']
okm = (th > 0.15) & (th < 1.4)          # neck-sized walls
Q = med[okm]

def resample(P, n):
    P = np.asarray(P, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n); return np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1)

def smooth(P, it=3):
    P = P.copy()
    for _ in range(it): P[1:-1] = 0.25 * P[:-2] + 0.5 * P[1:-1] + 0.25 * P[2:]
    return P

def refine(ctrl_xz, yprior, r=0.28, ywin=0.7):
    P = []
    for x, z in ctrl_xz:
        x, z = x * S, z * S
        sel = (np.hypot(Q[:, 0] - x, Q[:, 2] - z) < r) & (np.abs(Q[:, 1] - yprior * S) < ywin)
        s = Q[sel]
        P.append([np.median(s[:, 0]), np.median(s[:, 1]), np.median(s[:, 2])] if len(s) > 8 else [x, yprior * S, z])
    P = np.array(P); P = smooth(P, 2); P[:, 1] = smooth(P[:, 1:2], 6)[:, 0]
    return P

# right-side necks (character right = -X), head junction first, base last (raw units, x,z) + y prior (raw)
necks_r = {
 1: ([(-.225,.515),(-.20,.505),(-.18,.49),(-.16,.47),(-.14,.452),(-.125,.435),(-.115,.42)], -0.085),
 2: ([(-.225,.615),(-.20,.605),(-.185,.59),(-.17,.57),(-.155,.545),(-.145,.52),(-.135,.49),(-.125,.46),(-.12,.43)], 0.0),
 3: ([(-.225,.705),(-.20,.695),(-.18,.68),(-.165,.66),(-.15,.635),(-.14,.61),(-.13,.58),(-.115,.55),(-.105,.52),(-.095,.49),(-.09,.46),(-.09,.43)], 0.015),
 4: ([(-.155,.785),(-.14,.765),(-.13,.74),(-.12,.71),(-.115,.68),(-.11,.65),(-.10,.62),(-.09,.59),(-.08,.56),(-.072,.53),(-.065,.50),(-.06,.47),(-.06,.43)], 0.025),
}
J = {}
lines = {}
for k, (ctrl, yp) in necks_r.items():
    P = refine(ctrl, yp)[::-1]                      # base -> head
    P[0, 2] = 0.42 * S                              # base on the shoulder top
    lines[k] = P
    lines[9 - k] = P * np.array([-1, 1, 1])         # mirror: 1<->8, 2<->7, 3<->6, 4<->5

def head_tail(junc, prev, look, R=0.10):
    """head bone tail = snout tip: the head-blob vertices furthest along the look direction (outward + forward)"""
    look = np.asarray(look, float); look /= np.linalg.norm(look)
    rel = co - junc; dist = np.linalg.norm(rel, axis=1)
    blob = co[(dist < R * S) & (rel @ look > 0)]
    proj = (blob - junc) @ look
    tip = blob[proj > np.percentile(proj, 99)].mean(0)
    return tip, blob.mean(0)

for k, P in lines.items():
    nb = 4
    pts = resample(P, nb + 1)
    for i in range(nb):
        J[f'neck_{k}_{i+1:02d}'] = [pts[i].tolist(), pts[i + 1].tolist()]
    tip, c = head_tail(pts[-1], pts[-2], [(-1 if k <= 4 else 1), -0.6, -0.15])
    J[f'head_{k}'] = [pts[-1].tolist(), tip.tolist()]

# centre neck (x = 0), raw (y, z): base -> head junction
cy = [(-.14,.42),(-.155,.47),(-.145,.53),(-.13,.59),(-.12,.65),(-.12,.71),(-.135,.76)]
Pc = np.array([[0, y * S, z * S] for y, z in cy])
pts = resample(smooth(Pc, 2), 6)
for i in range(5):
    J[f'neck_c_{i+1:02d}'] = [pts[i].tolist(), pts[i + 1].tolist()]
tip, c = head_tail(pts[-1], pts[-2], [0, -1, -0.3], R=0.19)
tip[0] = 0.0
J['head_c'] = [pts[-1].tolist(), tip.tolist()]
J['_neck_lines'] = {str(k): v.tolist() for k, v in lines.items()}
J['_neck_lines']['c'] = pts.tolist()
json.dump(J, open(sys.argv[2], 'w'), indent=1)
for k in sorted(J):
    if not k.startswith('_'): print(k, np.round(J[k], 2).tolist())
