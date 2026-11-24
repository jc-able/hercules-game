"""Step 3b (python3, numpy): targeted weight repairs on top of 03a (rig review round 1, 2026-11-22).

python3 03b_fix.py <stage1r.npz> <vcolr.npy> <labels.npy> <weights_raw.npz> <out_weights.npz>

1. Saddle / back: neck_01..03 + head weight on non-mane skin fades out from rest y -0.55 to 0 at y -0.30 (behind the
   wing roots); the removed weight goes to spine_01/02/03 by position along the spine. Spine weights are then smoothed
   among themselves only (the per-vertex spine total is kept).
2. Rear mane (blue, y > -1.00): neck_02/03/head fade to 0 between y -1.00 and -0.60 (given to neck_01); behind y -0.60
   a mane strand uses only neck_01 + spine_03, neck_01 share linear 0.83 at y -0.60 -> 0 at y -0.22 (strands
   lying on the withers root at the back of the crest). The rear mane never gets neck_02+ weight.
2b. Mane <-> wing-root contact (the generator fused them): blended 4 rings either side, 15 passes (saddle area kept out).
   A rip (01c_rip.py without --no-rip) opened see-through holes up to 0.19 m wide (back faces are culled), so it is
   not used: the build runs 01c_rip.py --no-rip (labels only).
3. Wing lobe (labels 1) is wing/feather only and the flank under it (labels 2) has no wing weight (03a enforces both);
   here both rules fade in behind the true root (lobe y -0.25 -> -0.06, flank y -0.20 -> -0.02) and the fused
   lobe/flank band (|x| 0.25..0.47, y -0.32..-0.06, z 1.5..1.95, +3 rings) is smoothed 20 passes, so the change from
   wing to body is spread over the band instead of tearing at it (a rip there opened 0.28 m holes).
4. Breastplate (gold albedo, y -1.2..-0.5, z 1.2..1.9) and the chest front (y < -0.70, |x| < 0.30, facing forward,
   z < 1.80): neck weight -> spine_03, except a 2-ring blend along the band's top edge (0.5, 0.25 of the old neck weight)
   and z 1.72..1.80 on the chest. Foreleg weight on the brisket front (|x| < 0.12, fading out by 0.22) fades to 0
   between z 1.38 and 1.46.
5. Brisket: leg_f*_02 (forearm) fades to 0 between z 1.14 and 1.22 (the elbow; removed -> leg_f*_01, or spine_03 on
   the midline); leg_f*_01 is 0 for |x| < 0.06 (full again at 0.14), removed -> spine_03. Chest re-smoothed (8 passes).
6. Wing-root ring (vertices carrying wing_*_01 and body weight, grown 10 rings, z > 1.35, no mane) smoothed 40 passes
   (Laplacian): the wide root needs a long blend so the armpit does not stretch > 2x.
Then: top 4 influences, drop < 0.01, normalise.
"""
import sys, json
import numpy as np

npz, vcp, labp, win, wout = sys.argv[1:6]
d = np.load(npz); co = d['co']; E = d['edges']; T = d['tri']
col = np.load(vcp); lab = np.load(labp)
wd = np.load(win); names = [str(n) for n in wd['names']]; idx = wd['idx']; w4 = wd['w']
nv = len(co); nb = len(names); B = {n: i for i, n in enumerate(names)}
W = np.zeros((nb, nv))
for s in range(idx.shape[1]):
    np.add.at(W, (idx[:, s], np.arange(nv)), w4[:, s])
W0 = W.copy()

x, y, z = co[:, 0], co[:, 1], co[:, 2]
ax = np.abs(x)
hair = (col[:, 0] < 0.4) & (col[:, 2] > col[:, 0] + 0.2) & (z > 0.4) & (y > -1.3)
mane = hair & (y < 0.5)
gold = (col[:, 0] > 0.55) & (col[:, 1] > 0.3) & (col[:, 2] < 0.3)
band = gold & (y > -1.2) & (y < -0.5) & (z > 1.2) & (z < 1.9)
# vertex normals (area weighted) to find the forward-facing chest
fn = np.cross(co[T[:, 1]] - co[T[:, 0]], co[T[:, 2]] - co[T[:, 0]])
vn = np.zeros_like(co)
for k in range(3): np.add.at(vn, T[:, k], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
nbr_i = np.concatenate([E[:, 0], E[:, 1]]); nbr_j = np.concatenate([E[:, 1], E[:, 0]])
deg = np.bincount(nbr_i, minlength=nv).astype(float)

NECK = [B[n] for n in ('neck_01', 'neck_02', 'neck_03', 'head')]
NECK2 = [B[n] for n in ('neck_02', 'neck_03', 'head')]
SP = [B['spine_01'], B['spine_02'], B['spine_03']]
SPINE = [B['hips']] + SP
WING = [i for i, n in enumerate(names) if n.startswith('wing')]
s3 = B['spine_03']; n1 = B['neck_01']
RING_GROW, RING_ITERS = 10, 40
CONTACT_RINGS, CONTACT_ITERS = 4, 15
def smoothstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def spine_share(yy):
    """weights of spine_01/02/03 by rest y (bone mid points y 0.125, -0.225, -0.55)"""
    c = np.array([0.125, -0.225, -0.55])
    yy = np.clip(yy, c[2], c[0])
    out = np.zeros((3, len(yy)))
    a = yy >= c[1]; t = (yy[a] - c[1]) / (c[0] - c[1]); out[0, a] = t; out[1, a] = 1 - t
    b = ~a; t = (yy[b] - c[2]) / (c[1] - c[2]); out[1, b] = t; out[2, b] = 1 - t
    return out
def smooth(Wm, sel, iters, rows=None):
    """Laplacian smoothing of the selected vertices (neighbours outside the selection act as fixed boundary values)."""
    rows = list(range(nb)) if rows is None else rows
    for _ in range(iters):
        S = np.zeros((len(rows), nv))
        for k, r in enumerate(rows):
            S[k] = np.bincount(nbr_i, weights=Wm[r, nbr_j], minlength=nv)
        avg = S / np.maximum(deg, 1)
        for k, r in enumerate(rows):
            Wm[r, sel] = 0.5 * Wm[r, sel] + 0.5 * avg[k, sel]
    return Wm
def norm(Wm):
    Wm /= np.maximum(Wm.sum(0, keepdims=True), 1e-12); return Wm
stats = {}

# ---- 5. brisket / forearm
for side in ('fl', 'fr'):
    l2, l1 = B[f'leg_{side}_02'], B[f'leg_{side}_01']
    f = 1 - smoothstep(1.14, 1.22, z)
    rem = W[l2] * (1 - f); W[l2] *= f
    mid = ax < 0.06
    W[l1] += np.where(mid, 0, rem); W[s3] += np.where(mid, rem, 0)
    g = np.where(y < -0.4, smoothstep(0.06, 0.14, ax), 1.0)
    rem = W[l1] * (1 - g); W[l1] *= g; W[s3] += rem
# ---- 4. breastplate band + chest front
chest_front = (~mane) & (y < -0.70) & (ax < 0.30) & (z < 1.80) & (z > 1.0) & (vn[:, 1] < -0.3)
inband = np.zeros(nv, bool); inband[band] = True
# rings from the band's top edge: band verts with a non-band neighbour above them
up = (~inband[nbr_j]) & inband[nbr_i] & (z[nbr_j] > z[nbr_i])
ring1 = np.zeros(nv, bool); ring1[nbr_i[up]] = True
ring2 = np.zeros(nv, bool); ring2[nbr_j[ring1[nbr_i] & inband[nbr_j]]] = True; ring2 &= ~ring1
keep = np.where(ring1, 0.5, np.where(ring2, 0.25, 0.0))
chest_keep = smoothstep(1.72, 1.80, z)
neck_keep = np.ones(nv)
neck_keep = np.where(chest_front, np.minimum(neck_keep, chest_keep), neck_keep)
neck_keep = np.where(inband, keep, neck_keep)
for r in NECK:
    rem = W[r] * (1 - neck_keep); W[r] -= rem; W[s3] += rem
legf = [i for i, n in enumerate(names) if n.startswith('leg_f') or n in ('hoof_fl', 'hoof_fr')]
# only the brisket between the shoulder points (|x| < 0.12, fading out by 0.22): the shoulder point itself is leg
lk = np.where(chest_front | inband, 1 - smoothstep(1.38, 1.46, z) * (1 - smoothstep(0.12, 0.22, ax)), 1.0)
for r in legf:
    rem = W[r] * (1 - lk); W[r] -= rem; W[s3] += rem
stats['band_verts'] = int(inband.sum()); stats['chest_front_verts'] = int(chest_front.sum())
# ---- 1. back behind the wing roots: no neck weight on non-mane skin
nk = np.where(~mane, 1 - smoothstep(-0.55, -0.30, y), 1.0)
rem = np.zeros(nv)
for r in NECK:
    rem += W[r] * (1 - nk); W[r] *= nk
sh = spine_share(y)
for k, r in enumerate(SP): W[r] += rem * sh[k]
back = (~mane) & (y > -0.65) & (y < 0.6) & (z > 1.2)
tot = W[SP].sum(0)
P = W[SP] / np.maximum(tot, 1e-12)
Pm = np.zeros((nb, nv)); Pm[SP] = P
Pm = smooth(Pm, back & (tot > 1e-6), 6, rows=SP)
for k, r in enumerate(SP): W[r] = np.where(back, Pm[r] / np.maximum(Pm[SP].sum(0), 1e-12) * tot, W[r])
# ---- 2. rear mane
low = np.ones(nv)   # tried a z fade (keep strands above z 2.05 on neck_02/03): they hang into the low mane and tore, N12 withers 330 -> 1115
rm = mane & (y > -1.00)
g = np.where(rm, 1 - smoothstep(-1.00, -0.60, y) * low, 1.0)    # 0.4 m fade: a 0.2 m fade tore the high mane in N1
for r in NECK2:
    rem = W[r] * (1 - g); W[r] -= rem; W[n1] += rem
behind = mane & (y > -0.60) & (low > 0.999)
blend = mane & (y > -0.60) & (low <= 0.999)
a = np.clip((-0.22 - y) / 0.46, 0, 1)          # linear: 1 at y -0.68 .. 0 at y -0.22 (longest even blend)
Wt = np.zeros((nb, nv)); Wt[n1] = a; Wt[s3] = 1 - a
for r in range(nb):
    if r not in (n1, s3): W[r, behind] = 0
W[n1, behind] = a[behind]; W[s3, behind] = 1 - a[behind]
W[:, blend] = low[blend] * Wt[:, blend] + (1 - low[blend]) * W[:, blend]
W = smooth(W, mane & (y > -1.10) & (y < -0.20), 6, rows=[n1, s3] + NECK2)
# ---- 2b. mane <-> wing-root contact: the generator fused them; a rip opens see-through holes (culled back faces),
# so blend instead: 4 rings either side of the contact, 15 passes, all bones (the saddle area stays out)
wingw = W[WING].sum(0)
ce = (mane[nbr_i] & ~mane[nbr_j] & (wingw[nbr_j] > 0.2)) & (y[nbr_i] > -0.75)
contact = np.zeros(nv, bool); contact[nbr_i[ce]] = True; contact[nbr_j[ce]] = True
for _ in range(CONTACT_RINGS):
    c2 = contact.copy(); c2[nbr_i[contact[nbr_j]]] = True; contact = c2
contact &= np.linalg.norm(co - np.array([0, 0.10, 1.88]), axis=1) > 0.22
W = smooth(W, contact, CONTACT_ITERS)
stats['mane_wing_contact_verts'] = int(contact.sum())
# ---- 6. wing-root ring + chest smoothing
wr = (W[[B['wing_l_01'], B['wing_r_01']]].max(0) > 0.05) & (W[SPINE].sum(0) > 0.05)
ring = wr.copy()
for _ in range(RING_GROW):
    r2 = ring.copy(); r2[nbr_i[ring[nbr_j]]] = True; ring = r2
ring &= ~mane & (z > 1.35)
W = smooth(W, ring, RING_ITERS)
# fused lobe/flank band (no rip): spread the lobe -> flank change over the band
band2 = (ax > 0.25) & (ax < 0.47) & (y > -0.32) & (y < -0.06) & (z > 1.5) & (z < 1.95) & ~mane
for _ in range(3):
    b2 = band2.copy(); b2[nbr_i[band2[nbr_j]]] = True; band2 = b2
band2 &= ~mane
W = smooth(W, band2, 20)
stats['lobe_flank_band_verts'] = int(band2.sum())
chest = (~mane) & (y < -0.55) & (z > 1.0) & (z < 1.85) & (ax < 0.36)
W = smooth(W, chest, 8)
stats['wing_root_ring_verts'] = int(ring.sum()); stats['chest_smooth_verts'] = int(chest.sum())

# ---- hard constraints again after smoothing
def constrain(W):
    nk = np.where(~mane, 1 - smoothstep(-0.55, -0.30, y), 1.0)
    rem = np.zeros(nv)
    for r in NECK: rem += W[r] * (1 - nk); W[r] *= nk
    sh = spine_share(y)
    for k, r in enumerate(SP): W[r] += rem * sh[k]
    for r in NECK2: W[r, behind] = 0     # rear mane: no neck_02+ (wing weight from the contact blend may stay)
    for side in ('fl', 'fr'):
        l2 = B[f'leg_{side}_02']; f = 1 - smoothstep(1.14, 1.22, z)
        rem = W[l2] * (1 - f); W[l2] *= f; W[B[f'leg_{side}_01']] += np.where(ax < 0.06, 0, rem); W[s3] += np.where(ax < 0.06, rem, 0)
        l1 = B[f'leg_{side}_01']; g = np.where(y < -0.4, smoothstep(0.06, 0.14, ax), 1.0)
        rem = W[l1] * (1 - g); W[l1] *= g; W[s3] += rem
    # wing lobe: wing-only from y -0.12 back, fading in from the true root at y -0.25 (a hard switch at the root made
    # the armpit stretch); flank under it: no wing weight from y -0.08 back, fading in from -0.20
    nonw = [i for i in range(nb) if i not in WING]
    f1 = np.where(lab == 1, 1 - smoothstep(-0.25, -0.06, y), 1.0)
    f2 = np.where(lab == 2, 1 - smoothstep(-0.20, -0.02, y), 1.0)
    W[nonw] *= f1[None, :]; W[WING] *= f2[None, :]
    for r in legf:
        rem = W[r] * (1 - lk); W[r] -= rem; W[s3] += rem
    return norm(W)
W = constrain(norm(W))
# top 4, drop tiny, normalise, then constrain once more (cannot add influences) and normalise
order = np.argsort(-W, axis=0)[:4]
w4n = np.take_along_axis(W, order, 0)
w4n[w4n < 0.01] = 0
w4n /= np.maximum(w4n.sum(0, keepdims=True), 1e-12)
empty = w4n.sum(0) < 0.5
assert not empty.any(), int(empty.sum())

# report
def st(Wm, sel, rows): return round(float(Wm[rows][:, sel].sum(0).mean()), 3) if sel.any() else None
Wn = np.zeros((nb, nv)); np.add.at(Wn, (order, np.broadcast_to(np.arange(nv), order.shape)), w4n)
saddle = (np.linalg.norm(co - np.array([0, 0.10, 1.88]), axis=1) < 0.2) & ~mane & (z > 1.8)
stats.update({
    'saddle_area_verts': int(saddle.sum()),
    'saddle_neck_before': st(W0, saddle, NECK), 'saddle_neck_after': st(Wn, saddle, NECK),
    'back_nonmane_y>-0.3_neck_max_after': round(float(Wn[NECK][:, (~mane) & (y > -0.3)].sum(0).max()), 4),
    'rear_mane_neck02+_max_after': round(float(Wn[NECK2][:, mane & (y > -0.6)].sum(0).max()), 4),
    'chest_band_neck_mean_before': st(W0, inband, NECK), 'chest_band_neck_mean_after': st(Wn, inband, NECK),
    'chest_front_foreleg_z>1.45_max_after': round(float(Wn[legf][:, (chest_front | inband) & (z > 1.46)].sum(0).max()), 4) if ((chest_front | inband) & (z > 1.46)).any() else 0,
    'both_forelegs_w>0.05_before': int(((W0[[i for i in legf if names[i].endswith('fl') or '_fl_' in names[i]]].sum(0) > 0.05) & (W0[[i for i in legf if names[i].endswith('fr') or '_fr_' in names[i]]].sum(0) > 0.05)).sum()),
    'both_forelegs_w>0.05_after': int(((Wn[[i for i in legf if names[i].endswith('fl') or '_fl_' in names[i]]].sum(0) > 0.05) & (Wn[[i for i in legf if names[i].endswith('fr') or '_fr_' in names[i]]].sum(0) > 0.05)).sum()),
    'forearm_z>1.22_max_after': round(float(Wn[[B['leg_fl_02'], B['leg_fr_02']]][:, z > 1.22].max()), 4),
    'wing_only_nonwing_max': round(float(Wn[[i for i in range(nb) if i not in WING]][:, (lab == 1) & (y > -0.06)].sum(0).max()), 4),
    'flank_wing_max': round(float(Wn[WING][:, (lab == 2) & (y > -0.02)].sum(0).max()), 4),
})
np.savez(wout, names=np.array(names), idx=order.T, w=w4n.T)
print('###FIX###', json.dumps(stats))
