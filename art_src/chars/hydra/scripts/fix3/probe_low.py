"""Where is the lowest vertex?  Blender -b --factory-startup --python probe_low.py -- keys.json t1 t2 ...
Prints per time: lowest z, its xyz, the vertex group with the largest weight, and the 3 lowest bones' groups."""
import bpy, os, sys, json, importlib.util, numpy as np
REPO = os.path.expanduser('~/HerculesGame')
spec = importlib.util.spec_from_file_location('akb', REPO + '/tools/animkit/ak_blender.py')
akb = importlib.util.module_from_spec(spec); spec.loader.exec_module(akb)
argv = sys.argv[sys.argv.index('--') + 1:]
keys = json.load(open(argv[0]))
arm, rig = akb.make_rig({'blend': REPO + '/art_src/chars/hydra/hydra.blend'})
for ts in argv[1:]:
    t = float(ts)
    k = min(keys['keys'], key=lambda k: abs(k['t'] - t))
    rig.apply(k['pose'])
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    best = []
    for o in akb.body_meshes(arm):
        e = o.evaluated_get(dg); me = e.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3); me.vertices.foreach_get('co', co)
        M = np.array(e.matrix_world); w = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        idx = np.argsort(w[:, 2])[:400]
        groups = {}
        for i in idx:
            v = o.data.vertices[i]
            if v.groups:
                g = max(v.groups, key=lambda g: g.weight)
                nm = o.vertex_groups[g.group].name
                if nm not in groups:
                    groups[nm] = (round(float(w[i, 2]), 3), [round(float(x), 2) for x in w[i]])
        best.append(groups)
        e.to_mesh_clear()
    for g in best:
        print('t=%.3f' % k['t'], ' | '.join('%s %s' % (nm, v) for nm, v in list(g.items())[:5]))
