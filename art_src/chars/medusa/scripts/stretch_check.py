"""edge stretch audit: for every pose in poses/ (+ a 60-degree twist of every single deform bone) report edges whose
length changes by more than x2.5 / under x0.3 -> spikes, torn islands, collapsed areas.
Blender -b <blend> --python stretch_check.py [-- --single]"""
import bpy, sys, os, json, glob, numpy as np
S = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, S)
from posing import apply_pose
single = '--single' in sys.argv
arm = bpy.data.objects['medusa_rig']; ob = bpy.data.objects['medusa']; me = ob.data
n = len(me.vertices)
rest = np.empty(n * 3); me.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
ed = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
L0 = np.linalg.norm(rest[ed[:, 0]] - rest[ed[:, 1]], axis=1)
def posed():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); m = ev.to_mesh()
    p = np.empty(n * 3); m.vertices.foreach_get('co', p); ev.to_mesh_clear(); return p.reshape(-1, 3)
def audit(tag, pose):
    apply_pose(arm, pose); p = posed()
    L = np.linalg.norm(p[ed[:, 0]] - p[ed[:, 1]], axis=1)
    r = L / np.maximum(L0, 1e-6)
    long = (r > 2.5) & (L - L0 > 0.06); short = (r < 0.3) & (L0 > 0.03)
    worst = np.argmax(np.where(L - L0 > 0.06, r, 0))
    loc = np.round(rest[ed[worst, 0]], 2).tolist()
    print(f'###{tag:28s} max x{r.max():5.2f} at {loc}  >2.5x: {int(long.sum()):4d}  <0.3x: {int(short.sum()):4d}')
    return r
for f in sorted(glob.glob(os.path.join(S, 'poses', '*.json'))):
    audit(os.path.basename(f)[:-5], json.load(open(f)))
if single:
    for pb in arm.pose.bones:
        if not pb.bone.use_deform: continue
        for ax in range(3):
            r = [0, 0, 0]; r[ax] = 60
            audit(f'{pb.name} {"XYZ"[ax]}60', {pb.name: r})
