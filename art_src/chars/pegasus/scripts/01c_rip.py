"""Step 1c (rig fix round 1): label the generator's fused contacts (and optionally rip them).

USED WITH --no-rip: the rips were tested and opened see-through holes (mane seam up to 0.19 m, lobe seam up to
0.28 m in flap poses; Godot culls back faces), so the build only writes the labels and the weights blend the contacts
(03b_fix.py). The rip code is kept for reference.

The generated mesh fused (a) the rear mane strands to the wing roots and (b) the wing's lower inner edge (the hanging
feather lobe) to the flank. Weights blended across those contacts stretched badly (rig review, 2026-11-22). Here the
contact edges are split (bmesh split_edges), so the geodesic weights of 03a can no longer cross them. Both seams are
covered: the mane overhangs the wing root, and the feather lobe hangs outside the flank.

Wing-lobe vs flank classification (|x| 0.28..0.72, y > -0.30, z 1.30..2.05): cast a ray from the vertex towards the
body midline. Flank skin starts inside the body and exits at the far side (past the midline). Feather-lobe skin either
starts outside (the inner wing face looks at the flank across a gap) or exits the wing before the midline. Outside that box
the old dominant bone (wing_* or not) decides. Mane = saturated blue albedo (01b_colors.py).

Blender -b --factory-startup --python 01c_rip.py -- <workdir> <old_weights.npz> --no-rip [--no-wing-flank]
  reads  <workdir>/stage2.blend, vcol.npy
  writes <workdir>/stage2r.blend, stage1r.npz (co, tri, edges, orig), vcolr.npy, labels.npy
         labels: 0 = free, 1 = wing-only (feather lobe behind the true root), 2 = flank (no wing bones)
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_a = sys.argv[sys.argv.index('--') + 1:]
WK, OLDW = _a[:2]
NO_WING_FLANK = '--no-wing-flank' in _a
NO_RIP = '--no-rip' in _a          # labels only, no split (see the round-1 notes: the rips open see-through holes)
bpy.ops.wm.open_mainfile(filepath=os.path.join(WK, 'stage2.blend'))
ob = bpy.data.objects['pegasus']; me = ob.data
nv = len(me.vertices)
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
vn = np.empty(nv * 3); me.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
col = np.load(os.path.join(WK, 'vcol.npy'))
ow = np.load(OLDW); onames = [str(n) for n in ow['names']]
odom = np.array([onames[i] for i in ow['idx'][:, 0]])
hair = (col[:, 0] < 0.4) & (col[:, 2] > col[:, 0] + 0.2) & (co[:, 2] > 0.4) & (co[:, 1] > -1.3)
mane = hair & (co[:, 1] < 0.5)
wingdom = np.array([n.startswith('wing') for n in odom])

bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
ax = np.abs(co[:, 0])
box = (ax > 0.28) & (ax < 0.72) & (co[:, 1] > -0.30) & (co[:, 1] < 0.45) & (co[:, 2] > 1.30) & (co[:, 2] < 2.05) & ~hair
wing = wingdom.copy()
nin = nout = 0
for v in np.where(box)[0]:
    d = Vector((-np.sign(co[v, 0]), 0, 0))
    o = Vector(co[v]) + d * 0.002
    hit, n, fi, dist = bvh.ray_cast(o, d, 2.0)
    if hit is None:
        wing[v] = True; continue          # nothing towards the midline: cannot be body skin
    if n.dot(d) > 0:                      # exiting: started inside a volume; body skin exits past the midline
        wing[v] = hit.x * np.sign(co[v, 0]) > -0.05; nin += 1
    else:                                 # entering another surface: started outside -> lobe face looking at the flank
        wing[v] = True; nout += 1
# majority filter (2 passes) inside the box to remove speckles
E = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
nbr_i = np.concatenate([E[:, 0], E[:, 1]]); nbr_j = np.concatenate([E[:, 1], E[:, 0]])
deg = np.bincount(nbr_i, minlength=nv)
for _ in range(2):
    s = np.bincount(nbr_i, weights=wing[nbr_j].astype(float), minlength=nv) / np.maximum(deg, 1)
    wing = np.where(box, s > 0.5, wing)
# the flank never reaches past x 0.40 under the wing (0.45 at the hips, measured): anything further out in the box is
# wing even where the ray says 'body' (the lobe and body share one volume in the fused band y -0.28..-0.15)
xlim = np.where(co[:, 1] < 0.2, 0.40, 0.45)
wing = np.where(box & (ax >= xlim), True, wing)
print('box verts', int(box.sum()), 'wing in box', int((wing & box).sum()), 'rays inside', nin, 'outside', nout)

cls = np.where(mane, 0, np.where(wing, 1, 2))     # 0 mane, 1 wing, 2 body
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
orig = bm.verts.layers.int.new('orig')
for v in bm.verts: v[orig] = v.index
def fcls(f):
    c = np.bincount([cls[v.index] for v in f.verts], minlength=3)
    if c[0] > 0: return 0                 # any mane vertex: mane face, so the seam runs fully outside the hair
    return int(np.argmax(c))
fc = {f.index: fcls(f) for f in bm.faces}
rip = []; kinds = {'mane_wing': 0, 'wing_flank': 0}
for e in bm.edges:
    if len(e.link_faces) != 2: continue
    a, b = fc[e.link_faces[0].index], fc[e.link_faces[1].index]
    if a == b: continue
    m = (np.array(e.verts[0].co) + np.array(e.verts[1].co)) / 2
    pair = {a, b}
    if pair == {0, 1} and m[1] > -0.6:
        rip.append(e); kinds['mane_wing'] += 1
    elif not NO_WING_FLANK and pair == {1, 2} and m[1] > -0.28 and m[2] < 2.0 and abs(m[0]) > 0.25 and abs(m[0]) < 0.75:
        rip.append(e); kinds['wing_flank'] += 1
print('rip edges', kinds)
ripco = np.array([[(np.array(e.verts[0].co) + np.array(e.verts[1].co)) / 2] for e in rip]).reshape(-1, 3)
np.save(os.path.join(WK, 'rip_edges_mid.npy'), ripco)
if NO_RIP:
    rip = []
bmesh.ops.split_edges(bm, edges=rip)
bm.verts.index_update()
o = np.array([v[orig] for v in bm.verts])
bm.to_mesh(me); bm.free()
me.update()
n2 = len(me.vertices)
co2 = np.empty(n2 * 3); me.vertices.foreach_get('co', co2); co2 = co2.reshape(-1, 3)
E2 = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', E2); E2 = E2.reshape(-1, 2)
me.calc_loop_triangles()
T2 = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', T2); T2 = T2.reshape(-1, 3)
assert (o[:nv] == np.arange(nv)).all(), 'original vertex order changed'
# per-vertex class after the split: majority class of the faces around each vertex
vf = np.zeros((n2, 3))
for t in T2:
    c = np.bincount(cls[o[t]], minlength=3)
    vf[t] += c
vcls = vf.argmax(1)
lab = np.zeros(n2, np.int8)
box2 = box[o]
lab[(vcls == 1) & box2 & (co2[:, 1] > -0.25)] = 1
lab[(vcls == 2) & box2 & (co2[:, 1] > -0.20)] = 2
# connected components (islands) before/after
def ncomp(n, E):
    p = np.arange(n)
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for a, b in E.tolist():
        ra, rb = f(a), f(b)
        if ra != rb: p[ra] = rb
    r = np.array([f(i) for i in range(n)])
    return np.unique(r, return_counts=True)[1]
c1 = ncomp(nv, E); c2 = ncomp(n2, E2)
print('islands before', len(c1), sorted(c1)[:8], 'after', len(c2), sorted(c2)[:8])
np.savez(os.path.join(WK, 'stage1r.npz'), co=co2, tri=T2, edges=E2, orig=o)
np.save(os.path.join(WK, 'vcolr.npy'), col[o])
np.save(os.path.join(WK, 'labels.npy'), lab)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WK, 'stage2r.blend'))
print('###RIP###', json.dumps({'verts_before': nv, 'verts_after': n2, 'rip': kinds, 'wing_only': int((lab == 1).sum()),
                               'flank': int((lab == 2).sum()), 'islands_after': len(c2)}))
