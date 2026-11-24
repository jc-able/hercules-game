"""Step 3b (review fixes, 2026-11-22): work/hercules_03_skin.blend -> work/hercules_03b_fix.blend

 A. Feet: both ankles moved to (+-0.205, 0.070, 0.140) (centre of the ankle slice in the mesh), both ball joints to
    (+-0.237, -0.085, 0.045). Then the right foot / toe / lower-shin weights are mirrored onto the left (nearest
    neighbour within 1 cm, inverse-distance blend of 4 neighbours otherwise, bone names swapped) so both feet pivot alike.
 B. Skirt bones: skirt_f / skirt_b / skirt_l / skirt_r (deform, parent hips, from the belt z 1.12 to the hem z 0.70).
    Red cloth below the belt is re-weighted by geodesic distance from the belt: hips at the belt, blending to the skirt
    bones by the hem (angular partition cos^2 between the two nearest skirt bones). The mesh glues the skirt to each thigh
    along a ring under the hem: cloth within RING_R (geodesic) of that ring blends to the weights of the skin it joins. Thigh / shin weight is stripped from cloth and belt above BELT_STRIP_Z.
    The skirt bones are DRIVEN from the thighs (see skirt_drivers.py, rig.json "drivers").
 C. Skin under the skirt: opposite-leg weight removed (moved to the own thigh + hips) except on a +-SEAM_X strip at
    the centre line, where the crotch is weighted 50/50 to the two thighs with little hips; then smoothed.
 D. Neck: right back-of-neck weights mirrored from the left; neck >= 0.5 at the neck base; shoulder weight only below
    z 1.58 (ramped).
 E. Armpits: extra smoothing of upper_arm / shoulder / spine_02 weights within 4 cm geodesic of the armpit seam.
 F. spine_03 gets up to SP3_FRAC of the upper-chest spine_02 weight (z 1.40-1.55, |x| < 0.18), smoothed.
 G. near-coincident vertex pairs (edge < 4 mm) share weights.
 H. fingers_l / fingers_r curl bones (knuckles -> tips), weighted with a ramp across the knuckles.
 Then max 4 influences, normalised.
"""
import bpy, os, json, sys, heapq, math
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = dict(BELT_Z=1.12, HEM_Z=0.70, SKIRT_TOP=1.10, BELT_STRIP_Z=1.0, SKIRT_L=0.34, SKIRT_D0=0.02, RING_R=0.05, RING_MAX=0.0, UNGLUE=1,
         SEAM_X=0.012, SEAM_RAMP=0.03, CROTCH_HIPS=0.10, SMOOTH_SKIRT=6, SMOOTH_SKIN=6,
         SP3_FRAC=0.45, ARMPIT_R=0.04, ARMPIT_IT=10, NECK_MIN=0.5, SHOULDER_TOP=1.58, MICRO_E=0.004,
         KNUCKLE0=0.45, KNUCKLE1=0.62, T_MODE='z', T_Z0=1.10, T_Z1=0.66,
         UNLIP=0, LIP_NZ=-0.5, LIP_Z=0.82)
_extra = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if _extra and _extra[0] != "null":
    P.update(json.loads(_extra[0]))

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_03_skin.blend'))
ob = bpy.data.objects['hercules']; me = ob.data; nv = len(me.vertices)
arm = bpy.data.objects['hercules_rig']

# ---------------------------------------------------------------- bones (edit mode)
ANKLE = {'l': (0.205, 0.070, 0.140), 'r': (-0.205, 0.070, 0.140)}
BALL = {'l': (0.237, -0.085, 0.045), 'r': (-0.237, -0.085, 0.045)}
SKIRT = {  # head, tail
    'skirt_f': ((0.0, 0.03, P['BELT_Z']), (0.0, -0.17, P['HEM_Z'])),
    'skirt_b': ((0.0, 0.03, P['BELT_Z']), (0.0, 0.20, P['HEM_Z'])),
    'skirt_l': ((0.0, 0.03, P['BELT_Z']), (0.26, 0.03, P['HEM_Z'])),
    'skirt_r': ((0.0, 0.03, P['BELT_Z']), (-0.26, 0.03, P['HEM_Z'])),
}
bpy.context.view_layer.objects.active = arm
for o in bpy.context.scene.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for s in 'lr':
    rolls = {n: eb[n].roll for n in (f'shin_{s}', f'foot_{s}', f'toe_{s}')}
    eb[f'shin_{s}'].tail = Vector(ANKLE[s])
    eb[f'foot_{s}'].head = Vector(ANKLE[s]); eb[f'foot_{s}'].tail = Vector(BALL[s])
    t = eb[f'toe_{s}'].tail.copy()
    eb[f'toe_{s}'].head = Vector(BALL[s]); eb[f'toe_{s}'].tail = Vector((BALL[s][0], t.y, BALL[s][2]))
    for n, r in rolls.items():
        eb[n].roll = r
for n, (h, t) in SKIRT.items():
    b = eb.get(n) or eb.new(n)
    b.head = Vector(h); b.tail = Vector(t); b.parent = eb['hips']; b.use_connect = False; b.use_deform = True
    b.align_roll(Vector((0, 0, 1)) if n in ('skirt_l', 'skirt_r') else Vector((1, 0, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
for n in SKIRT:
    if n not in ob.vertex_groups:
        ob.vertex_groups.new(name=n)

# ---------------------------------------------------------------- A0. unglue the skirt from the thighs
# The generated mesh joins the hem underside to each thigh by a band of faces (496 faces with both red-cloth and skin
# vertices, ring at z 0.70-0.79 outside, up to 0.91 at the crotch). Any motion of a leg relative to the skirt
# stretches that band into a membrane (the old tears). Deleting those faces frees the skirt (it keeps its underside
# as an inner lip) and leaves the thigh tops open inside the skirt; the material is double-sided, so a glimpse into
# the opening shows skin colour, not a hole. 19 vertices used only by the glue faces go with them.
import bmesh
_cls = np.zeros(nv, np.int32); me.attributes['cls'].data.foreach_get('value', _cls)
_co = np.empty(nv * 3); me.vertices.foreach_get('co', _co); _co = _co.reshape(-1, 3)
_skirt = (_cls == 1) & (_co[:, 2] < P['SKIRT_TOP'])
bm = bmesh.new(); bm.from_mesh(me)
glue = [f for f in bm.faces if any(_skirt[v.index] for v in f.verts) and any(_cls[v.index] == 0 for v in f.verts)]
n_glue = len(glue); n_loose = 0; n_lip = 0
if P['UNGLUE'] and glue:
    bmesh.ops.delete(bm, geom=glue, context='FACES')     # faces + their now-unused edges (the old glue edges)
    if P['UNLIP']:
        # the hem underside band (faces looking down, below LIP_Z) would hang free as a ragged inner lip: drop it too,
        # leaving a clean single-layer hem (double-sided material shows the inside of the skirt in red)
        lip = [f for f in bm.faces if f.normal.z < P['LIP_NZ'] and f.calc_center_median().z < P['LIP_Z']
               and all(_skirt[v.index] for v in f.verts)]
        bmesh.ops.delete(bm, geom=lip, context='FACES')
        n_lip = len(lip)
    n_loose = nv - len(bm.verts)
    bm.to_mesh(me); me.update()
    nv = len(me.vertices)
bm.free()

# ---------------------------------------------------------------- data
names = [g.name for g in ob.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
W0 = W.copy()
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
x, y, z = co.T
cls = np.zeros(nv, np.int32); me.attributes['cls'].data.foreach_get('value', cls)
ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
elen = np.linalg.norm(co[ed[:, 0]] - co[ed[:, 1]], axis=1)
nbw = [[] for _ in range(nv)]
for (a_, b_), d_ in zip(ed, elen):
    nbw[a_].append((int(b_), float(d_))); nbw[b_].append((int(a_), float(d_)))
skin, cloth, leather = cls == 0, cls == 1, cls == 2
LEG = ('thigh', 'shin', 'foot', 'toe')
side = np.where(x >= 0, 'l', 'r')
info = {'lip_faces_deleted': n_lip, 'glue_faces_deleted': n_glue if P['UNGLUE'] else 0, 'glue_only_verts_removed': n_loose if P['UNGLUE'] else 0}


def geodesic(seeds, limit, allowed=None, src_out=None):
    dist = np.full(nv, np.inf); h = []
    src = np.full(nv, -1, np.int64)
    for s_ in seeds:
        dist[s_] = 0.0; h.append((0.0, int(s_))); src[s_] = s_
    heapq.heapify(h)
    while h:
        d_, u = heapq.heappop(h)
        if d_ > dist[u] or d_ > limit:
            continue
        for v_, w_ in nbw[u]:
            if allowed is not None and not allowed[v_]:
                continue
            nd = d_ + w_
            if nd < dist[v_]:
                dist[v_] = nd; src[v_] = src[u]; heapq.heappush(h, (nd, v_))
    if src_out is not None:
        src_out.append(src)
    return dist


def smooth(mask, cols, iters, alpha=0.5, graph_mask=None):
    """Jacobi smoothing of the given weight columns on mask vertices; neighbours outside graph_mask are ignored,
    neighbours outside mask (but inside graph_mask) act as a fixed boundary. Column sum per vertex is preserved."""
    idx = np.where(mask)[0]
    if not len(idx):
        return
    gm = np.ones(nv, bool) if graph_mask is None else graph_mask
    rows, colsn = [], []
    for k, i in enumerate(idx):
        for j, _ in nbw[i]:
            if gm[j]:
                rows.append(k); colsn.append(j)
    rows = np.array(rows, np.int64); colsn = np.array(colsn, np.int64)
    deg = np.bincount(rows, minlength=len(idx)).astype(float)
    ok = deg > 0
    cols = list(cols)
    tot = W[idx][:, cols].sum(1)
    for _ in range(iters):
        acc = np.zeros((len(idx), len(cols)))
        np.add.at(acc, rows, W[colsn][:, cols])
        sub = W[np.ix_(idx, cols)]
        new = np.where(ok[:, None], (1 - alpha) * sub + alpha * acc / np.maximum(deg, 1)[:, None], sub)
        s_ = new.sum(1)
        new *= np.where(s_ > 1e-9, tot / np.maximum(s_, 1e-9), 0)[:, None]
        W[np.ix_(idx, cols)] = new


def mirror_weights(dst_mask, src_mask, bone_filter=None, blend=None):
    """copy weights from the mirror image (-x) of each dst vertex, found among src vertices; names _l <-> _r"""
    src = np.where(src_mask)[0]
    kd = kdtree.KDTree(len(src))
    for k, i in enumerate(src):
        kd.insert(Vector((-co[i, 0], co[i, 1], co[i, 2])), k)
    kd.balance()
    perm = np.arange(len(names))
    for n, j in gi.items():
        m = n[:-2] + ('_r' if n.endswith('_l') else '_l') if n.endswith(('_l', '_r')) else n
        perm[j] = gi.get(m, j)
    cols = [gi[n] for n in names if bone_filter is None or bone_filter(n)]
    dst = np.where(dst_mask)[0]; exact = 0
    for k, i in enumerate(dst):
        found = kd.find_n(Vector(co[i]), 4)
        if found[0][2] < 0.01:
            wv = W[src[found[0][1]]][perm]; exact += 1
        else:
            ws = np.array([1 / max(f[2], 1e-4) for f in found]); ws /= ws.sum()
            wv = sum(wk * W[src[f[1]]][perm] for wk, f in zip(ws, found))
        b = 1.0 if blend is None else blend[k]
        new = W[i].copy()
        new[cols] = (1 - b) * W[i, cols] + b * wv[cols]
        W[i] = new
    return len(dst), exact


# ---------------------------------------------------------------- A. feet mirror (right -> left)
FOOTZ0, FOOTZ1 = 0.30, 0.36
lf = (x > 0.04) & (z < FOOTZ1)
rf = (x < -0.04) & (z < FOOTZ1 + 0.05)
bl = np.clip((FOOTZ1 - z[lf]) / (FOOTZ1 - FOOTZ0), 0, 1)
n_, ex_ = mirror_weights(lf, rf, bone_filter=lambda n: n.startswith(('shin_', 'foot_', 'toe_', 'thigh_')), blend=bl)
info['feet_mirror'] = {'verts': n_, 'exact_within_1cm': ex_}

# ---------------------------------------------------------------- B. skirt
legcols = [gi[f'{b}_{s}'] for b in LEG for s in 'lr']
skirt_cols = [gi[n] for n in SKIRT]
hips = gi['hips']
# B0. no leg weight on cloth / belt above BELT_STRIP_Z (it reached z 1.28)
up = (z > P['BELT_STRIP_Z']) & (np.abs(x) < 0.32) & ((cls != 0) | (z > 1.03))   # belt, buckle, tunic (not crotch skin)
moved = W[up][:, legcols].sum(1)
W[np.ix_(np.where(up)[0], legcols)] = 0
tgt = np.where(z[up] > 1.21, gi['spine_01'], hips)
np.add.at(W, (np.where(up)[0], tgt), moved)
info['leg_weight_stripped_above_belt'] = int((moved > 0.01).sum())
# ---------------------------------------------------------------- C. skin under the skirt
under = (skin | (cls == 3)) & (z < 1.02) & (z > 0.55) & (np.abs(x) < 0.30)
ui = np.where(under)[0]
ax = np.abs(x[ui])
own_w = np.clip((ax - P['SEAM_X']) / P['SEAM_RAMP'], 0, 1)        # 0 at the seam, 1 beyond SEAM_X + SEAM_RAMP
for k, i in enumerate(ui):
    s = side[i]; o = 'r' if s == 'l' else 'l'
    opp = [gi[f'{b}_{o}'] for b in LEG]
    take = W[i, opp] * own_w[k]
    W[i, opp] -= take
    W[i, gi[f'thigh_{s}']] += take.sum() * 0.5
    W[i, hips] += take.sum() * 0.5
# crotch seam: 50/50 thighs, little hips
seam = under & (np.abs(x) < P['SEAM_X'] + P['SEAM_RAMP']) & (z < 0.95)
si = np.where(seam)[0]
f = 1 - np.clip((np.abs(x[si]) - P['SEAM_X']) / P['SEAM_RAMP'], 0, 1)
tot_leg_hips = W[si, hips] + W[si][:, legcols].sum(1)
target_th = tot_leg_hips * (1 - P['CROTCH_HIPS']) / 2
for s in 'lr':
    W[si, gi[f'thigh_{s}']] = (1 - f) * W[si, gi[f'thigh_{s}']] + f * target_th
W[si, hips] = (1 - f) * W[si, hips] + f * tot_leg_hips * P['CROTCH_HIPS']
smooth(under & (z < 0.98), [hips] + legcols, P['SMOOTH_SKIN'], graph_mask=~(cloth & (z < P['SKIRT_TOP'])))
# re-zero opposite leg beyond the seam strip after smoothing
for k, i in enumerate(ui):
    s = side[i]; o = 'r' if s == 'l' else 'l'
    opp = [gi[f'{b}_{o}'] for b in LEG]
    take = W[i, opp] * own_w[k]
    W[i, opp] -= take
    W[i, gi[f'thigh_{s}']] += take.sum()
info['skin_under'] = {'verts': int(under.sum()), 'seam': int(seam.sum())}

# B1. skirt region and geodesic distance from the belt
skirt = cloth & (z < P['SKIRT_TOP'])
seeds = np.where((leather & (z > 0.98) & (z < 1.18)) | (cloth & (z >= P['SKIRT_TOP']) & (z < 1.18)))[0]
dist = geodesic(seeds, 1.0, allowed=(cloth | leather))
dz = np.where(np.isfinite(dist), dist, np.clip(P['BELT_Z'] - z, 0, None))
t = np.clip((dz - P['SKIRT_D0']) / P['SKIRT_L'], 0, 1)
if P['T_MODE'] == 'z':          # height below the belt: same value across a pleat's inner and outer crease
    t = np.clip((P['T_Z0'] - z) / (P['T_Z0'] - P['T_Z1']), 0, 1)
elif P['T_MODE'] == 'mix':
    t = 0.5 * t + 0.5 * np.clip((P['T_Z0'] - z) / (P['T_Z0'] - P['T_Z1']), 0, 1)
t = t * t * (3 - 2 * t)
# angular partition: front (-Y), left (+X), back (+Y), right (-X) around the hip centre
phi = np.arctan2(x, -(y - 0.03))
dirs = {'skirt_f': 0.0, 'skirt_l': math.pi / 2, 'skirt_b': math.pi, 'skirt_r': -math.pi / 2}
ang = {n: np.clip(np.cos(phi - a_), 0, None) ** 2 for n, a_ in dirs.items()}
# B2. the generated mesh glues the skirt to each thigh along a ring (hem underside -> thigh skin, z 0.70-0.79 outside,
#     up to 0.91 at the crotch). Cloth near that ring must follow the leg it is glued to, or it tears: blend to the
#     weights of the skin it joins over RING_R (geodesic, along the cloth).
is_skin_nb = np.zeros(nv, bool)
ring_w = {}
for i in np.where(skirt)[0]:
    sk_nb = [j for j, _ in nbw[i] if cls[j] == 0]
    if sk_nb:
        is_skin_nb[i] = True
        ring_w[i] = W[sk_nb].mean(0)
srcl = []
dring = geodesic(np.where(is_skin_nb)[0], P['RING_R'] * 1.5, allowed=skirt, src_out=srcl)
src = srcl[0]
a_ring = np.clip(1 - dring / P['RING_R'], 0, 1)
a_ring = a_ring * a_ring * (3 - 2 * a_ring) * P['RING_MAX']
idx = np.where(skirt)[0]
base = np.zeros((len(idx), W.shape[1]))
base[:, hips] = 1 - t[idx]
for n in SKIRT:
    base[:, gi[n]] = t[idx] * ang[n][idx]
ringv = np.zeros_like(base)
for k, i in enumerate(idx):
    if src[i] >= 0:
        ringv[k] = ring_w[int(src[i])]
ar = a_ring[idx][:, None]
W[idx] = (1 - ar) * base + ar * ringv
smooth(skirt & ~is_skin_nb, [hips] + skirt_cols + legcols, P['SMOOTH_SKIRT'], graph_mask=skirt)
info['skirt'] = {'verts': int(skirt.sum()), 'ring_verts': int(is_skin_nb.sum()), 'with_ring_weight>0.05': int((a_ring[idx] > 0.05).sum()),
                 'unreached_geodesic': int((~np.isfinite(dist[idx])).sum())}

# ---------------------------------------------------------------- D. neck (right back mirrored from the left)
neckr = (x < -0.02) & (z > 1.52) & (z < 1.72) & (np.abs(x) < 0.16) & (y > -0.02)
necks = (x > 0.0) & (z > 1.50) & (z < 1.74)
bl = np.clip((-x[neckr] - 0.02) / 0.03, 0, 1)
n_, ex_ = mirror_weights(neckr, necks, blend=bl)
info['neck_mirror'] = {'verts': n_, 'exact_within_1cm': ex_}
sh_cols = [gi['shoulder_l'], gi['shoulder_r']]
band = (z > 1.55) & (z < 1.70) & (np.abs(x) < 0.13)
bi = np.where(band)[0]
ramp = np.clip((z[bi] - (P['SHOULDER_TOP'] - 0.03)) / 0.04, 0, 1)   # 0 below 1.55, 1 above 1.59
for c in sh_cols:
    take = W[bi, c] * ramp
    W[bi, c] -= take
    W[bi, gi['neck']] += take
base = band & (z > 1.58) & (z < 1.64)
bi2 = np.where(base)[0]
need = np.clip(P['NECK_MIN'] - W[bi2, gi['neck']], 0, None)
others = [gi['head'], gi['spine_03'], gi['spine_02']] + sh_cols
osum = W[bi2][:, others].sum(1)
for c in others:
    W[bi2, c] -= np.where(osum > 1e-9, need * W[bi2, c] / np.maximum(osum, 1e-9), 0)
W[bi2, gi['neck']] += np.minimum(need, osum)
neck_cols = [gi['neck'], gi['head'], gi['spine_03'], gi['spine_02']] + sh_cols
smooth((z > 1.50) & (z < 1.72) & (np.abs(x) < 0.16), neck_cols, 20)

# ---------------------------------------------------------------- E. armpits
for s, sg in (('l', 1), ('r', -1)):
    c0 = np.array([0.207 * sg, 0.07, 1.355])
    seedm = np.linalg.norm(co - c0, axis=1) < 0.015
    if not seedm.any():
        seedm[np.argmin(np.linalg.norm(co - c0, axis=1))] = True
    dd = geodesic(np.where(seedm)[0], P['ARMPIT_R'])
    m = dd < P['ARMPIT_R']
    smooth(m, [gi[f'upper_arm_{s}'], gi[f'shoulder_{s}'], gi['spine_02'], gi['spine_01'], gi['spine_03']], P['ARMPIT_IT'])
    info[f'armpit_{s}'] = int(m.sum())

# ---------------------------------------------------------------- F. spine_03
chest = (z > 1.38) & (z < 1.57) & (np.abs(x) < 0.20)
ci = np.where(chest)[0]
fz = np.clip((z[ci] - 1.40) / 0.08, 0, 1) * np.clip((1.57 - z[ci]) / 0.03, 0, 1)
fx = np.clip((0.18 - np.abs(x[ci])) / 0.06, 0, 1)
take = W[ci, gi['spine_02']] * P['SP3_FRAC'] * fz * fx
W[ci, gi['spine_02']] -= take
W[ci, gi['spine_03']] += take
smooth(chest, [gi['spine_02'], gi['spine_03'], gi['spine_01']], 6)
info['spine_03_verts'] = int((W[:, gi['spine_03']] > 0.05).sum())

# ---------------------------------------------------------------- G. near-coincident vertices share weights
# (edges < MICRO_E long with different weights become spikes: 1.5 mm pairs at the neck stretched 16x)
short = ed[elen < P['MICRO_E']]
for _ in range(3):
    avg = (W[short[:, 0]] + W[short[:, 1]]) / 2
    W[short[:, 0]] = avg; W[short[:, 1]] = avg
info['micro_edges_averaged'] = int(len(short))

# ---------------------------------------------------------------- H. finger curl bones (one per hand)
# fingers_l / fingers_r: child of the hand, head on the knuckle line, tail at the finger tips, local X = knuckle line,
# so a rotation about the bone's own X curls all four fingers (and the thumb tip a little) toward the palm.
fing = {}
for s in 'lr':
    hb = arm.data.bones[f'hand_{s}']
    h0 = np.array(hb.head_local); ax = np.array(hb.tail_local) - h0; ax /= np.linalg.norm(ax)
    hv = np.where(W[:, gi[f'hand_{s}']] > 0.5)[0]
    pr = (co[hv] - h0) @ ax
    Lh = float(np.quantile(pr, 0.995))
    c = co[hv] - co[hv].mean(0)
    _, _, Vt = np.linalg.svd(c, full_matrices=False)
    palm_n = Vt[2]                                   # flattest direction of the hand = palm normal
    palm_n -= (palm_n @ ax) * ax; palm_n /= np.linalg.norm(palm_n)
    if palm_n[0] * (1 if s == 'r' else -1) < 0:      # point it to the palm side (toward the body)
        palm_n = -palm_n
    k0, k1 = P['KNUCKLE0'] * Lh, P['KNUCKLE1'] * Lh
    head = h0 + ax * (k0 + k1) / 2
    tail = h0 + ax * Lh
    wf = np.clip((pr - k0) / (k1 - k0), 0, 1); wf = wf * wf * (3 - 2 * wf)
    fing[s] = dict(head=head, tail=tail, palm_n=palm_n, hv=hv, wf=wf)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for s, f in fing.items():
    b = eb.get(f'fingers_{s}') or eb.new(f'fingers_{s}')
    b.head = Vector(f['head']); b.tail = Vector(f['tail']); b.parent = eb[f'hand_{s}']; b.use_connect = False
    b.use_deform = True
    b.align_roll(Vector(f['palm_n']))               # bone Z -> palm side, so +X rotation curls toward the palm
bpy.ops.object.mode_set(mode='OBJECT')
for s, f in fing.items():
    n = f'fingers_{s}'
    if n not in ob.vertex_groups:
        ob.vertex_groups.new(name=n)
    names.append(n); gi[n] = len(names) - 1
    W = np.concatenate([W, np.zeros((nv, 1))], axis=1)
for s, f in fing.items():
    hv, wf = f['hv'], f['wf']
    # take the share from every weight of those vertices (hand-dominant verts), so the fingers ride fully at the tips
    take = W[hv] * wf[:, None]
    W[hv] -= take
    W[hv, gi[f'fingers_{s}']] += take.sum(1)
    hand_zone = np.zeros(nv, bool); hand_zone[hv] = True
    smooth(hand_zone, [gi[f'hand_{s}'], gi[f'fingers_{s}']], 4)
    info[f'fingers_{s}'] = {'verts': int((W[:, gi[f'fingers_{s}']] > 0.05).sum()), 'hand_len': round(float(np.linalg.norm(f['tail'] - arm.data.bones[f'hand_{s}'].head_local)), 3)}

# ---------------------------------------------------------------- limit 4, normalise, write
W[W < 0] = 0
order = np.argsort(-W, axis=1)
keep = np.zeros_like(W, bool)
np.put_along_axis(keep, order[:, :4], True, axis=1)
W[~keep] = 0
W[W < 0.005] = 0
W /= W.sum(1, keepdims=True)
assert np.all(np.isfinite(W)) and np.all(W.sum(1) > 0.999)
for g in ob.vertex_groups:
    g.remove(list(range(nv)))
for j, g in enumerate(ob.vertex_groups):
    nz = np.where(W[:, j] > 0)[0]
    for i in nz:
        g.add([int(i)], float(W[i, j]), 'REPLACE')
# opposite-thigh check on skin
chk = {}
for s, o, sg in (('l', 'r', 1), ('r', 'l', -1)):
    m = skin & (x * sg > P['SEAM_X'] + P['SEAM_RAMP']) & (z < 1.0)
    chk[f'skin_{s}_with_thigh_{o}>0.01'] = int((W[m, gi[f'thigh_{o}']] > 0.01).sum())
    m2 = cloth & (x * sg > 0.02) & (z < 1.10)
    chk[f'cloth_{s}_with_thigh_{o}>0.1'] = int((W[m2, gi[f'thigh_{o}']] > 0.1).sum())
chk['cloth_thigh_max_z'] = float(z[cloth & (W[:, [gi['thigh_l'], gi['thigh_r']]].sum(1) > 0.01)].max()) if (cloth & (W[:, [gi['thigh_l'], gi['thigh_r']]].sum(1) > 0.01)).any() else None
info['checks'] = chk
info['changed_verts'] = int((np.abs(W - np.pad(W0, ((0, 0), (0, W.shape[1] - W0.shape[1])))).max(1) > 0.01).sum())
info['max_infl'] = int((W > 0).sum(1).max())
print('###FIX', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_03b_fix.blend'))
