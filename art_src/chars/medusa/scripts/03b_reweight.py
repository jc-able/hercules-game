"""03b: rebuild the upper-body weights (neck / shoulders / head / snake roots) on top of 03_skin.
Review fixes (2026-11-22, rig_review_medusa findings 1-3 + clavicle midline):
 - stage A: harmonic (Laplace, uniform edge weights) blend of every bone between anchor sets (head core above the jaw line,
   front neck ring, upper chest, upper back, clavicle tops, arms, everything below z 4.5 kept from 03);
 - stage A2: the neck+head share is its own harmonic field: 0 on the shoulder tops (|x| > 0.38, z < 5.2 in front,
   z < 5.0 behind where the hair curtain lies on the shoulders), the chest and below z 4.95; 1 on the head core / neck ring;
 - clavicles / upper arms faded to 0 across the midline (soft);
 - stage B: each snake's hair_* weight ramps 0 -> 1 geodesically over mesh edges from 5 cm inside the hair mass to 20 cm
   along the snake (55 cm for the low hair_*_03 snakes, which root at shoulder level in the back-hair curtain);
   no hair weight below z 5.25 on vertices that carry shoulder / spine weight;
 - soft restricted smoothing ({spine_03, shoulder_x, upper_arm_x} on the shoulder band; {head, hair_x} at the roots),
   no hard region masks afterwards; limit 4, normalise.
Blender -b --factory-startup --python 03b_reweight.py   (-> work/rig_medusa/03b_skin.blend, weights_03b.npy)"""
import bpy, os, sys, numpy as np
S = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(S)
W_DIR = os.path.join(D, '..', '..', '..', 'work', 'rig_medusa')
sys.path.insert(0, S)
import weights_solve
bpy.ops.wm.open_mainfile(filepath=os.path.join(W_DIR, '03_skin.blend'))
arm = bpy.data.objects['medusa_rig']; ob = bpy.data.objects['medusa']; me = ob.data
names = [b.name for b in arm.data.bones]
I = {k: i for i, k in enumerate(names)}
n = len(me.vertices)
co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
E = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
gname = {g.index: g.name for g in ob.vertex_groups}
W0 = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        if g.weight > 0: W0[v.index, I[gname[g.group]]] = g.weight
W0 /= W0.sum(1, keepdims=True)
W, info = weights_solve.build(W0, co, E, names)
deform = [b.name for b in arm.data.bones if b.use_deform]
assert W[:, [I[k] for k in names if k not in deform]].max() == 0, 'weight on a non-deforming bone'
cnt = (W > 0).sum(1)
print('###WEIGHTS changed verts', int((np.abs(W - W0).max(1) > 1e-3).sum()), 'max_inf', int(cnt.max()), 'min_inf', int(cnt.min()),
      'sum err', float(np.abs(W.sum(1) - 1).max()))
np.save(os.path.join(W_DIR, 'weights_03b.npy'), W)
ob.vertex_groups.clear()
for nm in deform:
    g = ob.vertex_groups.new(name=nm)
    col = W[:, I[nm]]
    nz = np.nonzero(col)[0]
    # group vertices by identical weight to cut the number of add() calls
    vals = np.round(col[nz], 5)
    order = np.argsort(vals); nz = nz[order]; vals = vals[order]
    cuts = np.nonzero(np.diff(vals))[0] + 1
    for idxs, val in zip(np.split(nz, cuts), np.split(vals, cuts)):
        g.add(idxs.tolist(), float(val[0]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W_DIR, '03b_skin.blend'))
print('###SAVED 03b_skin.blend')
