"""Step 3b: 02_bones.blend + weights.npz -> 03_skin.blend.
1. RIP the fused seams between two different necks (edges whose two faces carry different neck labels) so a neck that
   moves away from its neighbour does not drag a membrane of stretched faces with it;
2. vertex groups from weights.npz (a duplicated seam vertex takes the weights of a neighbour of its own side);
3. armature modifier.
  Blender -b --factory-startup --python 03b_skin.py [-- --norip]"""
import bpy, bmesh, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CH = os.path.dirname(HERE)
WIP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CH))), 'work', 'rig_hydra', 'wip')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RIP = '--norip' not in args
bpy.ops.wm.open_mainfile(filepath=os.path.join(WIP, '02_bones.blend'))
wz = np.load(os.path.join(WIP, 'weights.npz'))
idx, w, names, label, parts = wz['idx'], wz['w'], list(wz['bones']), wz['label'], list(wz['parts'])
is_neck = np.array([p.startswith('neck') for p in parts])
mesh = bpy.data.objects['hydra']; arm = bpy.data.objects['hydra_rig']; me = mesh.data
bm = bmesh.new(); bm.from_mesh(me)
orig = bm.verts.layers.int.new('orig')
for v in bm.verts: v[orig] = v.index
bm.faces.ensure_lookup_table()
flab = np.array([np.bincount([label[v.index] for v in f.verts]).argmax() for f in bm.faces])
for f in bm.faces: f.tag = False
# fix round 1: tiny face islands (<= 12 faces) of one neck inside another part would be ripped off as loose fragments;
# give them the label of the faces around them first
nisl = 0
for rnd in range(3):
    seen = np.zeros(len(bm.faces), bool); changed = 0
    for f0 in bm.faces:
        if seen[f0.index]: continue
        L = flab[f0.index]; comp = [f0]; seen[f0.index] = True; k = 0
        while k < len(comp):
            f = comp[k]; k += 1
            for e in f.edges:
                for g in e.link_faces:
                    if not seen[g.index] and flab[g.index] == L: seen[g.index] = True; comp.append(g)
        if len(comp) <= 12 and is_neck[L]:
            ids = set(f.index for f in comp)
            around = [flab[g.index] for f in comp for e in f.edges for g in e.link_faces if g.index not in ids]
            if around:
                nl = np.bincount(around).argmax()
                for f in comp: flab[f.index] = nl
                changed += 1
    nisl += changed
    if not changed: break
print('###ISLANDS### small neck face islands relabelled', nisl)
seam = []
if RIP:
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a, b = flab[e.link_faces[0].index], flab[e.link_faces[1].index]
            if a != b and is_neck[a] and is_neck[b]: seam.append(e)
    flab_layer = bm.faces.layers.int.new('flab')
    for f in bm.faces: f[flab_layer] = int(flab[f.index])
    bmesh.ops.split_edges(bm, edges=seam)
    bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    flab = np.array([f[flab_layer] for f in bm.faces])
bm.verts.index_update(); bm.verts.ensure_lookup_table()
nv = len(bm.verts)
vo = np.array([v[orig] for v in bm.verts])
vlab = label[vo].copy()
src = vo.copy()                       # which original vertex's weights each vertex takes
fixed = 0
for v in bm.verts:
    fl = set(int(flab[f.index]) for f in v.link_faces)
    if len(fl) == 1:
        L = fl.pop()
        if L != vlab[v.index] and is_neck[L] and is_neck[vlab[v.index]]:
            # take weights from the nearest neighbour that belongs to the side it now lives on
            cand = [e.other_vert(v) for e in v.link_edges]
            cand = [c for c in cand if label[c[orig]] == L]
            if cand:
                c = min(cand, key=lambda c: (c.co - v.co).length)
                src[v.index] = c[orig]; vlab[v.index] = L; fixed += 1
bm.to_mesh(me); bm.free()
mesh.vertex_groups.clear()
groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.data.bones if b.use_deform}
I = idx[src]; Wt = w[src]
for bi, name in enumerate(names):
    if name not in groups: continue
    rows, cols = np.where((I == bi) & (Wt > 0))
    g = groups[name]
    for r, val in zip(rows.tolist(), Wt[rows, cols].tolist()): g.add([r], val, 'REPLACE')
for m in list(mesh.modifiers): mesh.modifiers.remove(m)
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
mesh.parent = arm; mesh.matrix_parent_inverse.identity()
if 'orig' in me.attributes: me.attributes.remove(me.attributes['orig'])
if 'flab' in me.attributes: me.attributes.remove(me.attributes['flab'])
np.save(os.path.join(WIP, 'vlabel_after_rip.npy'), vlab)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP, '03_skin.blend'), relative_remap=True)
me.calc_loop_triangles()
print('###SKIN### seam edges ripped', len(seam), 'verts', nv, 'tris', len(me.loop_triangles), 'reassigned', fixed)
