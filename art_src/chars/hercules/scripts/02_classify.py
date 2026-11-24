"""Step 2: tag every vertex with a material class from the albedo texture (stored as int attribute 'cls'):
0 skin, 1 cloth (red tunic), 2 leather (belt / sandal straps), 3 hair/beard (dark).
Also prints connected-component stats. Loads work/hercules_01_clean.blend, saves work/hercules_02_cls.blend.
"""
import bpy, os, json
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_01_clean.blend'))
mesh = bpy.data.objects['hercules']; me = mesh.data
# glTF splits vertices along UV seams: weld co-located vertices (UVs live on loops, so they survive)
import bmesh
from mathutils import kdtree
_nv = len(me.vertices); _ng = len(mesh.vertex_groups)
_W = np.zeros((_nv, _ng))
for v in me.vertices:
    for g in v.groups:
        _W[v.index, g.group] = g.weight
_kd = kdtree.KDTree(_nv)
for v in me.vertices:
    _kd.insert(v.co, v.index)
_kd.balance()
_diff = 0.0; _pairs = 0
for v in me.vertices:
    for (_c, j, d) in _kd.find_range(v.co, 1e-5):
        if j > v.index:
            _pairs += 1; _diff = max(_diff, np.abs(_W[v.index] - _W[j]).max())
print('###SEAM pairs', _pairs, 'max weight diff across seam duplicates', round(_diff, 4))
bm = bmesh.new(); bm.from_mesh(me)
nv0 = len(bm.verts); nf0 = len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
print('###WELD verts', nv0, '->', len(bm.verts), 'faces', nf0, '->', len(bm.faces))
bm.to_mesh(me); bm.free(); me.update()
img = bpy.data.images['hercules_albedo']
W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[:, :, :3]
nl = len(me.loops); nv = len(me.vertices)
uv = np.empty(nl * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
lv = np.empty(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
xi = np.clip((uv[:, 0] % 1.0) * W, 0, W - 1).astype(int); yi = np.clip((uv[:, 1] % 1.0) * H, 0, H - 1).astype(int)
lc = px[yi, xi]
col = np.zeros((nv, 3)); cnt = np.zeros(nv)
np.add.at(col, lv, lc); np.add.at(cnt, lv, 1)
col /= np.maximum(cnt, 1)[:, None]
r, g, b = col.T
lum = 0.3 * r + 0.59 * g + 0.11 * b
cls = np.zeros(nv, np.int32)
red = (r > 0.25) & (g < r * 0.45) & (b < r * 0.45)
dark = lum < 0.22
cls[red] = 1
cls[dark & ~red] = 3
co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
# leather: dark/brown verts at belt height or near the feet
cls[((cls == 3) | ((r < 0.55) & (lum < 0.35))) & (co[:, 2] < 0.25)] = 2
belt = (co[:, 2] > 1.02) & (co[:, 2] < 1.16) & (cls != 0) & ~((cls == 1) & (lum > 0.25))
cls[belt & (lum < 0.3)] = 2
# dark verts below the beard are shaded tunic folds
cls[(cls == 3) & (co[:, 2] < 1.52)] = 1
# a vertex is cloth if most of its neighbours are cloth (cleans speckle)
a = me.attributes.get('cls') or me.attributes.new('cls', 'INT', 'POINT')
a.data.foreach_set('value', cls)
print('###CLS counts', np.bincount(cls, minlength=4).tolist())
for c in range(4):
    m = cls == c
    if m.any():
        print('###CLS', c, 'z range', co[m, 2].min().round(3), co[m, 2].max().round(3), 'mean col', col[m].mean(0).round(2))

# connected components
ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
parent = np.arange(nv)
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for u, v in ed:
    ru, rv = find(u), find(v)
    if ru != rv:
        parent[ru] = rv
roots = np.array([find(i) for i in range(nv)])
uniq, inv, counts = np.unique(roots, return_inverse=True, return_counts=True)
order = np.argsort(-counts)
print('###COMPONENTS', len(uniq), 'sizes', counts[order][:15].tolist())
for k in order[:12]:
    m = inv == k
    print('###COMP size', counts[k], 'bbmin', co[m].min(0).round(3).tolist(), 'bbmax', co[m].max(0).round(3).tolist(),
          'cls', np.bincount(cls[m], minlength=4).tolist())
comp = me.attributes.get('comp') or me.attributes.new('comp', 'INT', 'POINT')
rank = np.empty_like(order); rank[order] = np.arange(len(order))
comp.data.foreach_set('value', rank[inv].astype(np.int32))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hercules_02_cls.blend'))
