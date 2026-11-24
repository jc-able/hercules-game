"""vertex penetration: verts of a neck/head group inside a 0.35 m core of another neck's segment (numpy skinning).
python3 pen3.py <glb> [prev.glb]"""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.expanduser('~/HerculesGame/work/natural_review/hydra'))
from glbfk import GLB
def load(path):
    G = GLB(path); g = G.g; blob = G.blob; sk = g.skins[0]; J = sk.joints
    def raw(i, dt, n):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=off).reshape(a.count, n)
    p = g.meshes[0].primitives[0]
    pos = raw(p.attributes.POSITION, np.float32, 3).astype(float)
    jo = raw(p.attributes.JOINTS_0, np.uint8, 4)
    we = raw(p.attributes.WEIGHTS_0, np.float32, 4) if g.accessors[p.attributes.WEIGHTS_0].componentType == 5126 else raw(p.attributes.WEIGHTS_0, np.uint8, 4) / 255.
    ibm = raw(sk.inverseBindMatrices, np.float32, 16).reshape(-1, 4, 4).transpose(0, 2, 1)
    jn = [G.names[j] for j in J]
    top = jo[np.arange(len(jo)), we.argmax(1)]
    return G, pos, jo, we, ibm, jn, top
def test(M, clip, t, ga, axis):
    G, pos, jo, we, ibm, jn, top = M
    W = G.pose(clip, t); Mx = np.array([W[n] @ ibm[k] for k, n in enumerate(jn)])
    V = np.c_[pos, np.ones(len(pos))]; out = np.zeros((len(pos), 3))
    for c in range(4):
        out += we[:, c:c + 1] * np.einsum('nij,nj->ni', Mx[jo[:, c]], V)[:, :3]
    sel = np.isin(top, [k for k, n in enumerate(jn) if n.startswith(ga)])
    va = out[sel]; a = W[axis[0]][:3, 3]; c = W[axis[1]][:3, 3]; d = c - a; L = np.linalg.norm(d); u = d / L
    s = np.clip((va - a) @ u, 0, L); r = np.linalg.norm(va - (a + np.outer(s, u)), axis=1)
    return int((r < 0.35).sum()), int(len(va))
cases = [('stomp', t, g, ('neck_c_04', 'neck_c_05')) for t in (0.6, 1.0, 1.4, 1.8, 2.2) for g in ('neck_5_04', 'head_5')] + \
        [('stomp', t, g, ('neck_6_04', 'head_6')) for t in (0.8, 1.0, 1.2, 1.4, 1.6) for g in ('neck_5_04', 'head_5')] + \
        [('stomp_r', t, g, ('neck_6_04', 'head_6')) for t in (1.0, 1.2, 1.4) for g in ('neck_5_04', 'head_5')] + \
        [('fire_sweep_l', t, g, ('neck_6_04', 'head_6')) for t in (1.6, 1.8, 2.0, 2.2) for g in ('head_8', 'neck_8_04')] + \
        [('fire_sweep_return_l', t, g, ('neck_6_04', 'head_6')) for t in (1.4, 1.6, 1.8, 2.0) for g in ('head_8', 'neck_8_04')] + \
        [('idle', t, 'neck_5_04', ('neck_c_04', 'neck_c_05')) for t in (0.0, 3.0)]
Ms = [load(p) for p in sys.argv[1:]]
for clip, t, ga, ax in cases:
    row = []
    for M in Ms:
        n, tot = test(M, clip, t, ga, ax); row.append('%d/%d' % (n, tot))
    print('%-20s t=%.1f %-10s in core of %s->%s: %s' % (clip, t, ga, ax[0], ax[1], '  vs  '.join(row)))
