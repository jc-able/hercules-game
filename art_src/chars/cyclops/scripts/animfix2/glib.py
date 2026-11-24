"""Naturalness reviewer: numeric checks on the cyclops GLB (new vs backup). numpy FK + linear skinning, no Blender.
usage: python3 analyze.py  -> prints a report and writes analyze.json next to this file."""
import json, math, sys, pathlib, numpy as np, pygltflib
HERE = pathlib.Path(__file__).parent
R = pathlib.Path('~/HerculesGame').expanduser()
NEW = R / 'game/assets/characters/cyclops/cyclops.glb'
OLD = R / 'art_src/chars/cyclops/backup_20261123/cyclops.glb'
MAN = json.load(open(R / 'art_src/chars/cyclops/backup_20261123/cyclops_clips.json'))
CT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def q2m(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


class G:
    def __init__(s, path, skin_mesh=True):
        g = s.g = pygltflib.GLTF2().load(str(path)); s.blob = g.binary_blob()
        s.N = len(g.nodes); s.names = [n.name for n in g.nodes]
        s.parent = [-1] * s.N
        for i, n in enumerate(g.nodes):
            for c in n.children or []: s.parent[c] = i
        s.rest = [(np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float), np.array(n.scale or [1, 1, 1], float)) for n in g.nodes]
        sk = g.skins[0]; s.joints = sk.joints; s.jn = [s.names[j] for j in s.joints]
        s.ibm = s.acc(sk.inverseBindMatrices).reshape(-1, 4, 4).transpose(0, 2, 1)
        s.order = []; seen = set()
        def visit(i):
            if i in seen: return
            if s.parent[i] >= 0: visit(s.parent[i])
            seen.add(i); s.order.append(i)
        for i in range(s.N): visit(i)
        s.meshes = {}
        for i, n in enumerate(g.nodes):
            if n.mesh is None: continue
            P, Nn, J, W = [], [], [], []
            for p in g.meshes[n.mesh].primitives:
                P.append(s.acc(p.attributes.POSITION)); Nn.append(s.acc(p.attributes.NORMAL))
                if n.skin is not None:
                    J.append(s.acc(p.attributes.JOINTS_0).astype(int)); W.append(s.acc(p.attributes.WEIGHTS_0))
            s.meshes[s.names[i]] = dict(node=i, P=np.concatenate(P), N=np.concatenate(Nn), J=np.concatenate(J) if J else None,
                                        W=np.concatenate(W) if W else None, skinned=n.skin is not None)
        s.anims = {a.name: a for a in g.animations}
        s.cache = {}

    def acc(s, i):
        a = s.g.accessors[i]; bv = s.g.bufferViews[a.bufferView]; n = NC[a.type]
        off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        dt = np.dtype(CT[a.componentType]); stride = bv.byteStride or dt.itemsize * n
        if stride == dt.itemsize * n:
            arr = np.frombuffer(s.blob, dtype=dt, count=a.count * n, offset=off).reshape(a.count, n)
        else:
            arr = np.stack([np.frombuffer(s.blob, dtype=dt, count=n, offset=off + k * stride) for k in range(a.count)])
        arr = arr.astype(np.float64)
        if a.normalized and dt != np.float32: arr /= np.iinfo(dt).max
        return arr

    def length(s, clip):
        an = s.anims[clip]
        return max(s.acc(sm.input)[-1, 0] for sm in an.samplers)

    def local(s, clip, t):
        an = s.anims[clip]
        T = [list(x) for x in s.rest]
        for ch in an.channels:
            sm = an.samplers[ch.sampler]
            key = (clip, ch.sampler)
            if key not in s.cache: s.cache[key] = (s.acc(sm.input)[:, 0], s.acc(sm.output))
            ti, vo = s.cache[key]
            k = int(np.clip(np.searchsorted(ti, t - 1e-6), 0, len(ti) - 1))
            if k > 0 and ti[k] > t + 1e-6:
                a = (t - ti[k-1]) / (ti[k] - ti[k-1]); v0, v1 = vo[k-1], vo[k]
                if ch.target.path == 'rotation' and np.dot(v0, v1) < 0: v1 = -v1
                v = v0 * (1 - a) + v1 * a
            else:
                v = vo[k]
            idx = {'translation': 0, 'rotation': 1, 'scale': 2}[ch.target.path]
            if idx == 1: v = v / np.linalg.norm(v)
            T[ch.target.node][idx] = np.array(v)
        return T

    def world(s, T):
        Gm = [None] * s.N
        for i in s.order:
            t, r, sc = T[i]
            L = np.eye(4); L[:3, :3] = q2m(r) * sc[None, :]; L[:3, 3] = t
            Gm[i] = L if s.parent[i] < 0 else Gm[s.parent[i]] @ L
        return Gm

    def verts(s, Gm, name, sub=None, normals=False):
        m = s.meshes[name]; P = m['P'] if sub is None else m['P'][sub]
        Nn = m['N'] if sub is None else m['N'][sub]
        Ph = np.c_[P, np.ones(len(P))]
        if m['skinned']:
            J = m['J'] if sub is None else m['J'][sub]; W = m['W'] if sub is None else m['W'][sub]
            Mj = np.stack([Gm[j] @ s.ibm[k] for k, j in enumerate(s.joints)])
            M = np.einsum('nc,ncij->nij', W, Mj[J])
            V = np.einsum('nij,nj->ni', M, Ph)[:, :3]
            if normals:
                NN = np.einsum('nij,nj->ni', M[:, :3, :3], Nn); NN /= np.linalg.norm(NN, axis=1, keepdims=True) + 1e-9
                return V, NN
            return V
        M = Gm[m['node']]
        V = (M @ Ph.T).T[:, :3]
        if normals:
            NN = (M[:3, :3] @ Nn.T).T; NN /= np.linalg.norm(NN, axis=1, keepdims=True) + 1e-9
            return V, NN
        return V

    def node(s, n): return s.names.index(n)


def qang(a, b):
    d = abs(float(np.dot(a, b))); return math.degrees(2 * math.acos(min(1.0, d)))


def sock_world(gl, Gm, sname):
    so = MAN['socket_offsets'][sname]
    M = Gm[gl.node(so['bone'])]
    return (M @ np.r_[so['loc'], 1.0])[:3]


