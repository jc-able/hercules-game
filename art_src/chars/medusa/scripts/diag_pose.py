"""print vertices in a rest box that moved less than X under a pose, with their weights
Blender -b <blend> --python diag_pose.py -- pose.json xmin,xmax,ymin,ymax,zmin,zmax maxmove"""
import bpy, sys, os, json, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posing import apply_pose
arm = bpy.data.objects['medusa_rig']; ob = bpy.data.objects['medusa']
n = len(ob.data.vertices)
rest = np.empty(n * 3); ob.data.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
apply_pose(arm, json.load(open(a[0]))); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
pos = np.empty(n * 3); me.vertices.foreach_get('co', pos); pos = pos.reshape(-1, 3)
b = [float(v) for v in a[1].split(',')]
m = (rest[:,0]>b[0])&(rest[:,0]<b[1])&(rest[:,1]>b[2])&(rest[:,1]<b[3])&(rest[:,2]>b[4])&(rest[:,2]<b[5])
mv = np.linalg.norm(pos - rest, axis=1)
sel = np.nonzero(m & (mv < float(a[2])))[0]
print('###', m.sum(), 'in box,', len(sel), 'moved <', a[2])
gn = {g.index: g.name for g in ob.vertex_groups}
for i in sel[:: max(1, len(sel)//25)]:
    ws = sorted([(gn[g.group], round(g.weight, 2)) for g in ob.data.vertices[i].groups], key=lambda t: -t[1])
    print('###', i, np.round(rest[i], 2), 'moved', round(mv[i], 2), ws)
