"""Step 1b (fix round 1): 01_clean.blend -> 01b_trim.blend. Deletes the headless REAR TUBE behind the centre neck.
The generated mesh has a 10th tube (no head) standing 2.2 m behind the centre neck (x within +-0.9, y -1.0..1.2,
z 7.5..13.7). Rigging it to neck_c made it swing out as a long stretched sheet whenever the centre neck bent forward
(review blocker). Seen from the front it is hidden behind the centre neck; from the side it was only a dark backdrop
behind heads 1-4, so it is removed and the opening at the neck bases is capped with a fan (one centre vertex).
Vertex list: rear_tube_verts.json (indices into 01_clean.blend; = the v1 rear-tube label of 03a, horn tips excluded).
  Blender -b --factory-startup --python 01b_trim.py"""
import bpy, bmesh, os, json, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); CH = os.path.dirname(HERE)
WIP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CH))), 'work', 'rig_hydra', 'wip')
bpy.ops.wm.open_mainfile(filepath=os.path.join(WIP, '01_clean.blend'))
o = bpy.data.objects['hydra']; me = o.data
J = json.load(open(os.path.join(HERE, 'rear_tube_verts.json')))
assert len(me.vertices) == 34994, len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
dead = [bm.verts[i] for i in J['verts']]
bmesh.ops.delete(bm, geom=dead, context='VERTS')
bnd = [e for e in bm.edges if e.is_boundary]
# boundary vertex -> one UV (from an existing loop) so the cap can reuse the neighbouring texture
vuv = {}
for e in bnd:
    for v in e.verts:
        if v not in vuv:
            vuv[v] = v.link_loops[0][uvl].uv.copy()
# directed boundary (reverse of the face that owns each boundary edge); decompose into closed cycles (the opening has
# two pinch vertices, so it is three simple loops); each cycle gets a fan around a new centre vertex
out = {}
for e in bnd:
    l = e.link_loops[0]; a, b = l.link_loop_next.vert, l.vert
    out.setdefault(a, []).append(b)
used = set(); cycles = []
for a0 in list(out):
    for b0 in list(out[a0]):
        if (a0, b0) in used: continue
        cyc = [a0]; a, b = a0, b0
        while True:
            used.add((a, b)); cyc.append(b)
            if b == a0: break
            nxt = [x for x in out[b] if (b, x) not in used]
            a, b = b, nxt[0]
        cycles.append(cyc[:-1])
centre = []; cap_faces = []
for cyc in cycles:
    m = sum((v.co for v in cyc), Vector()) / len(cyc)
    c = bm.verts.new(m); centre.append(c)
    for i in range(len(cyc)):
        cap_faces.append(bm.faces.new((cyc[i], cyc[(i + 1) % len(cyc)], c)))
bm.normal_update()
# UVs: boundary loops keep their vertex's UV; the centre takes the UV of the first ring vertex of its cycle
for f in cap_faces:
    f.smooth = True
    ring = [x for x in f.verts if x in vuv]
    for l in f.loops:
        l[uvl].uv = vuv[l.vert] if l.vert in vuv else vuv[ring[0]]
CAPCO = [[round(x, 5) for x in c.co] for c in centre]
print('###CYCLES###', [len(c) for c in cycles])
bm.to_mesh(me); bm.free()
me.calc_loop_triangles()
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
bm2 = bmesh.new(); bm2.from_mesh(me); nbound = sum(1 for e in bm2.edges if e.is_boundary); bm2.free()
json.dump({'cap_centres_co': CAPCO}, open(os.path.join(WIP, 'cap.json'), 'w'))      # positions (bmesh reorders vertices)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP, '01b_trim.blend'), relative_remap=True)
print('###TRIM###', json.dumps(dict(deleted=len(J['verts']), boundary_edges_capped=len(bnd), cap_faces=len(cap_faces),
      verts=len(me.vertices), tris=len(me.loop_triangles), boundary_left=nbound,
      min=co.min(0).round(3).tolist(), max=co.max(0).round(3).tolist())))
