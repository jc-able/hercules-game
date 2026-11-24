"""Cyclops fixer metrics on a GLB (numpy FK + skinning, from natural_review/cyclops/analyze_lib.py).
usage: python3 measure.py <glb> [section ...]   sections: slam pull death walk sweep stuck all"""
import sys, numpy as np
exec(open(__import__('os').path.expanduser('~/HerculesGame/work/animfix_cyclops2/glib.py')).read())
exec(open(__import__('os').path.expanduser('~/HerculesGame/work/natural_review/cyclops/tri.py')).read().split('for tag,gl in')[0].split("exec(open('analyze_lib.py').read())")[1])
FPS = 24
gl = G(sys.argv[1])
SEC = sys.argv[2:] or ['all']
BN = [n for n in gl.meshes if gl.meshes[n]['skinned']][0]
CN = [n for n in gl.meshes if not gl.meshes[n]['skinned']][0]
P0 = gl.meshes[BN]['P']; SOLE = np.where(P0[:, 1] < 0.25)[0]; SL = P0[SOLE, 0] > 0
ARMS = ['shoulder_u_l', 'upper_arm_u_l', 'forearm_u_l', 'shoulder_u_r', 'upper_arm_u_r', 'forearm_u_r', 'upper_arm_d_l', 'forearm_d_l', 'upper_arm_d_r', 'forearm_d_r']
_F = None


def W(clip, t): return gl.world(gl.local(clip, min(t, gl.length(clip))))
def jp(Gm, b): return Gm[gl.node(b)][:3, 3]
def frames(clip, t0=0, t1=None):
    L = gl.length(clip); t1 = L if t1 is None else min(t1, L)
    return [f / FPS for f in range(int(round(t0 * FPS)), int(round(t1 * FPS)) + 1)]


def club_head(Gm):
    V = gl.verts(Gm, CN); g = sock_world(gl, Gm, 'hand_ur')
    return V[np.argmax(np.linalg.norm(V - g, axis=1))], V[:, 1].min()


def club_speed(clip, t0, t1):
    prev = None; s = []
    for t in frames(clip, t0, t1):
        h, _ = club_head(W(clip, t))
        if prev is not None: s.append(round(float(np.linalg.norm(h - prev) * FPS), 1))
        prev = h
    return s


def angvel(clip, bones, t0, t1):
    ts = frames(clip, t0, t1); out = {}
    for b in bones:
        Q = [gl.local(clip, t)[gl.node(b)][1] for t in ts]
        out[b] = [round(qang(Q[k], Q[k + 1]) * FPS) for k in range(len(ts) - 1)]
    return ts, out


def worldvel(clip, bones, t0, t1):
    """world-orientation angular speed (deg/s) per frame"""
    ts = frames(clip, t0, t1); out = {}
    Gs = [W(clip, t) for t in ts]
    for b in bones:
        R = [Gm[gl.node(b)][:3, :3] / np.linalg.norm(Gm[gl.node(b)][:3, 0]) for Gm in Gs]
        out[b] = [round(np.degrees(np.arccos(np.clip((np.trace(R[k].T @ R[k + 1]) - 1) / 2, -1, 1))) * FPS) for k in range(len(ts) - 1)]
    return ts, out


def armdev(clip, t):
    T = gl.local(clip, t); return {b: round(qang(T[gl.node(b)][1], gl.rest[gl.node(b)][1]), 1) for b in ARMS}


def feet(clip, t0=0, t1=None, thr=0.03):
    ts = frames(clip, t0, t1)
    V = np.array([gl.verts(W(clip, t), BN, SOLE) for t in ts])
    res = []
    for side, msk in (('L', SL), ('R', ~SL)):
        Vs = V[:, msk]; contact = Vs[:, :, 1].min(1) < thr; k = 0; n = len(ts)
        while k < n:
            if contact[k]:
                s = k
                while k < n and contact[k]: k += 1
                mid = (s + k - 1) // 2; cv = np.where(Vs[mid, :, 1] < thr)[0]
                seg = Vs[s:k][:, cv]; c = seg[:, :, [0, 2]].mean(1); d = c - c[0]
                res.append((side, round(ts[s], 3), round(ts[k - 1], 3), 'path', round(float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum()), 3),
                            'x_range', round(float(np.ptp(c[:, 0])), 3), 'z_range', round(float(np.ptp(c[:, 1])), 3), 'net', np.round(d[-1], 3).tolist()))
            else: k += 1
    return res


def tri(clip, step=1, groups=(('d_r', 'trunk'), ('d_l', 'trunk'), ('d_r', 'legs'), ('d_l', 'legs'))):
    global _F
    if _F is None:
        bn, F, dom = tris(gl); _F = {g: gfaces(F, dom, g) for g in GRP}
    out = []
    for f in range(0, int(round(gl.length(clip) * FPS)) + 1, step):
        t = f / FPS; V = gl.verts(W(clip, t), BN)
        h = tuple(hits(V, _F[a], _F[b]) for a, b in groups)
        if any(h): out.append((round(t, 3), h))
    return out


def jdev(Ga, Gb):
    return max(float(np.linalg.norm(jp(Ga, gl.jn[k]) - jp(Gb, gl.jn[k]))) for k in range(len(gl.jn)))


def seams():
    i0 = W('idle', 0); s0 = W('stuck', 0); L = gl.length
    print('seams (max joint dev m): slam0-idle0 %.3f slamEnd-stuck0 %.3f pf0-stuck0 %.3f pfEnd-idle0 %.3f sweep0 %.3f sweepEnd %.3f hurt0-stuck %.3f hurtEnd-stuck %.3f death0-idle %.3f idle loop %.3f walk loop %.3f stuck loop %.3f' % (
        jdev(W('slam', 0), i0), jdev(W('slam', L('slam')), s0), jdev(W('pull_free', 0), s0), jdev(W('pull_free', L('pull_free')), i0),
        jdev(W('sweep', 0), i0), jdev(W('sweep', L('sweep')), i0), jdev(W('hurt', 0), s0), jdev(W('hurt', L('hurt')), s0), jdev(W('death', 0), i0),
        jdev(W('idle', 0), W('idle', L('idle'))), jdev(W('walk', 0), W('walk', L('walk'))), jdev(W('stuck', 0), W('stuck', L('stuck')))))
    print('lengths', {c: round(L(c), 4) for c in sorted(gl.anims)})


def lowest(clip):
    lo = [gl.verts(W(clip, t), BN)[:, 1].min() for t in frames(clip)]
    return round(min(lo), 3), round(max(lo), 3)


def sect(n): return 'all' in SEC or n in SEC


if sect('seams'): seams()
if sect('slam'):
    print('== slam club head m/s 0..0.6', club_speed('slam', 0, 0.6))
    for t in (0.125, 0.25, 0.375):
        d = armdev('slam', t); print(f'   slam t={t} arm dev from rest mean {np.mean(list(d.values())):.1f}', d)
    print('   slam feet', feet('slam'))
    G15 = W('slam', 1.5); h, lo = club_head(G15)
    print('   slam impact club head', np.round(h, 3), 'lowest club', round(lo, 3), 'hand_ur', np.round(sock_world(gl, G15, 'hand_ur'), 3), 'grip2', np.round(sock_world(gl, G15, 'club_grip2'), 3))
    for t in (1.333, 1.375, 1.417, 1.458, 1.5, 1.75):
        Gm = W('slam', t); print(f'   slam {t} hand_ur', np.round(sock_world(gl, Gm, 'hand_ur'), 3), 'grip2', np.round(sock_world(gl, Gm, 'club_grip2'), 3), 'foot_r', np.round(jp(Gm, 'foot_r'), 3), 'foot_l', np.round(jp(Gm, 'foot_l'), 3))
    print('   slam lowest', lowest('slam'))
if sect('pull'):
    ts, o = worldvel('pull_free', ['hand_u_l', 'hand_u_r', 'upper_arm_u_l', 'hand_d_l', 'hand_d_r', 'forearm_u_r'], 1.0, 1.5)
    print('== pull_free world ang vel 1.0..1.5'); [print('   ', b, v) for b, v in o.items()]
    print('   club head m/s 1.0..1.5', club_speed('pull_free', 1.0, 1.5))
    for t in (1.25, 1.333, 1.375):
        d = armdev('pull_free', t); print(f'   pf t={t} arm dev mean {np.mean(list(d.values())):.1f}', d)
    print('   pf feet', feet('pull_free')); print('   pf lowest', lowest('pull_free'))
if sect('death'):
    for t in (0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.125):
        d = armdev('death', t); print(f'== death t={t} arm dev mean {np.mean(list(d.values())):.1f}', d)
    ts, o = angvel('death', ['shoulder_u_l', 'shoulder_u_r'], 3.0, 3.6); print('   death shoulder local vel 3.0..3.6', o)
    print('   death club lowest', round(min(club_head(W('death', t))[1] for t in frames('death')), 3))
if sect('walk'):
    print('== walk feet', feet('walk'))
    print('   walk tri (d_r>trunk, d_l>trunk, d_r>legs, d_l>legs)', tri('walk', 1))
    ts = frames('walk'); T = [gl.local('walk', t) for t in ts]
    for b in ('hand_u_r', 'forearm_u_r', 'upper_arm_u_r', 'shoulder_u_r', 'upper_arm_d_l', 'upper_arm_d_r', 'forearm_d_l', 'forearm_d_r', 'upper_arm_u_l'):
        q = [x[gl.node(b)][1] for x in T]; m = max(qang(a, c) for a in q for c in q)
        print(f'   walk {b} range {m:.1f}')
    hx = [jp(W('walk', t), 'hips')[0] for t in ts]; print('   walk hips x sway', round(float(np.ptp(hx)), 3))
if sect('sweep'):
    print('== sweep tri', tri('sweep', 1, (('d_l', 'trunk'), ('d_l', 'legs'), ('d_r', 'trunk'))))
    d = armdev('sweep', 2.31); print('   sweep 2.31 arm dev', d)
    G = W('sweep', 2.3125); I = W('idle', 0); print('   sweep 2.3125 vs idle0 jdev', round(jdev(G, I), 3))
    ts, o = worldvel('sweep', ['root', 'hips', 'forearm_u_r', 'hand_u_r'], 1.9, 2.5); print('   sweep vel', o)
    print('   sweep feet', feet('sweep'))
if sect('stuck'):
    los = []; hs = []
    for t in frames('stuck'):
        Gm = W('stuck', t); los.append(round(float(club_head(Gm)[1]), 3)); hs.append(sock_world(gl, Gm, 'hand_ur'))
    hs = np.array(hs); print('== stuck club lowest per frame', los); print('   hand_ur max dev from f0', round(float(np.linalg.norm(hs - hs[0], axis=1).max()), 3))
    print('   stuck feet', feet('stuck'))
