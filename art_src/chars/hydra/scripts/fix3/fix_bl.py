"""Hydra animation fixer 3 (2026-11-23): re-base v2 with per-frame foot IK, new turn-in-place walks, breathing idle.

Run headless:  Blender -b --factory-startup --python fix_bl.py -- <out_dir> <clip> [<clip> ...]
Writes <out_dir>/keys_<clip>.json (one inline absolute pose per frame) and prints ###FX### {report}.

Clips:
  bite* fire_sweep* head_down head_up hurt* stomp* death*  re-base of the ORIGINAL (.rest_v1) action, as
        work/rebase/hydra/rebase_bl.py did, plus:
        - legs: never blended between the natural stance and the rest-keyed legs any more. Every frame the legs are
          q_natural * q_original (the keyed crouch on top of the stance) and then re-solved with foot IK so each planted
          foot stays on its natural-stance floor point; a foot that the original LIFTS (the stomp) follows the original's
          lift path, shifted so it lands where it lifted.  (death*: IK fades out with the old 0.35 s leg window)
        - stomp: neck_5 bends away from the centre neck; staggered rear-up of the side heads; smooth whip/rebound
        - fire_sweep_l / fire_sweep_return_l: neck_8 ducks under neck_6 while neck_6 leans over it
        - hurt: the passive heads' staggered original snap is low-passed (3-4 frame ease) and the flinch eases in
        - head_down: every life layer is zero at t=0 (= the shared chin rest); flank pant on spine_02/03 with the jaw
          kept exact (neck_c_01 counter-rotation)
  idle         base = clips/idle_n/base/action_idle_base.json + two breaths per 6 s (spine pitch, shoulders rise),
               root bob on the exhale, hip sway with the chest drift; legs re-solved per frame (feet planted).
  walk_turn_l / walk_turn_r   base = clips/walk_n/action_walk.json (upper body, lift timing); legs re-solved per frame
               so every planted foot moves along its circle about the turn pivot (body origin) at Omega = move_speed /
               r_forefoot rad per clip second (the body turns left = CCW seen from above for _l).
Never saves the blend (opened read-only in place through animkit's make_rig)."""
import bpy, sys, os, json, math, importlib.util
import numpy as np
from mathutils import Matrix, Vector, Quaternion

REPO = os.path.expanduser('~/HerculesGame')
CH = REPO + '/art_src/chars/hydra'
spec = importlib.util.spec_from_file_location('akb', REPO + '/tools/animkit/ak_blender.py')
akb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(akb)

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
CLIPS = argv[1:]
os.makedirs(OUT, exist_ok=True)
PARAMS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_params.json')))

TAU = 2 * math.pi
WIN = 0.3

DOWN_ACT = {'neck_c', 'spine', 'legs'}
CLIPS_CFG = {
    'bite':               dict(dir='bite', start='natural', end='natural', act={'neck_c', 'spine', 'legs'}),
    'bite_l':             dict(dir='bite', start='natural', end='natural', act={'n6', 'spine', 'legs'}),
    'bite_r':             dict(dir='bite', start='natural', end='natural', act={'n3', 'spine', 'legs'}),
    'fire_sweep':         dict(dir='fire_sweep', start='natural', end='down', act=DOWN_ACT),
    'fire_sweep_l':       dict(dir='fire_sweep', start='natural', end='down', act=DOWN_ACT),
    'fire_sweep_return':  dict(dir='fire_sweep', start='own', end='down', act=DOWN_ACT),
    'fire_sweep_return_l': dict(dir='fire_sweep', start='own', end='down', act=DOWN_ACT),
    'head_down':          dict(dir='fire_sweep', start='down', end='down', act=DOWN_ACT),
    'head_up':            dict(dir='fire_sweep', start='down', end='natural', act=DOWN_ACT),
    'hurt':               dict(dir='hurt', start='down', end='down', act=DOWN_ACT),
    'hurt_standing':      dict(dir='hurt', start='natural', end='natural', act=set()),
    'stomp':              dict(dir='stomp', start='natural', end='natural', act={'legs', 'spine'}),
    'stomp_r':            dict(dir='stomp', start='natural', end='natural', act={'legs', 'spine'}),
    'death':              dict(dir='death', start='down', end='own',
                               act={'neck_c', 'spine', 'legs', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8'}),
    'death_standing':     dict(dir='death', start='natural', end='own',
                               act={'neck_c', 'legs', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8'}),
}
SIDE = ['n%d' % k for k in range(1, 9)]
ALLG = ['spine', 'tail', 'neck_c', 'legs'] + SIDE
HX = {'n1': -2.94, 'n2': -2.09, 'n3': -4.87, 'n4': -3.09, 'n5': 2.20, 'n6': 3.70, 'n7': 4.96, 'n8': 3.14, 'neck_c': 0.36}
HEAD = {
    'n1': dict(a=1.9, fu=0.29, fs=0.21, ph=0.0, dl=0.10, st=0.08, sc=0.85),
    'n2': dict(a=1.4, fu=0.33, fs=0.26, ph=2.1, dl=0.04, st=0.03, sc=1.10),
    'n3': dict(a=2.2, fu=0.24, fs=0.31, ph=4.0, dl=0.13, st=0.11, sc=0.75),
    'n4': dict(a=1.2, fu=0.37, fs=0.23, ph=1.2, dl=0.06, st=0.05, sc=1.00),
    'n5': dict(a=1.5, fu=0.27, fs=0.35, ph=3.3, dl=0.05, st=0.02, sc=1.05),
    'n6': dict(a=1.8, fu=0.31, fs=0.19, ph=5.1, dl=0.09, st=0.07, sc=0.90),
    'n7': dict(a=2.1, fu=0.22, fs=0.28, ph=0.7, dl=0.14, st=0.12, sc=0.70),
    'n8': dict(a=1.6, fu=0.35, fs=0.24, ph=2.8, dl=0.08, st=0.06, sc=0.95),
    'neck_c': dict(a=0.9, fu=0.26, fs=0.20, ph=1.9, dl=0.0, st=0.0, sc=1.0),
}
DROOP = {'n1': -1.5, 'n2': -3.0, 'n3': -2.5, 'n4': -3.5, 'n5': -2.0, 'n6': -3.2, 'n7': -1.8, 'n8': -2.6}
# stomp rear-up stagger (s) per side head: never two together
REAR_ST = {'n1': 0.10, 'n2': 0.05, 'n3': 0.14, 'n4': 0.07, 'n5': 0.12, 'n6': 0.06, 'n7': 0.15, 'n8': 0.09, 'neck_c': 0.0}


def ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return ss((t - a) / (b - a)) if b > a else (1.0 if t >= a else 0.0)


def rec(t, t0, f=1.8, tau=0.35, ease=0.08):
    """damped settle, 0 before t0; eased in over `ease` s (no velocity kink at the onset)"""
    if t < t0:
        return 0.0
    d = t - t0
    return math.sin(TAU * f * d) * math.exp(-d / tau) * ss(d / ease if ease > 0 else 1.0)


def bump(t, a, b, c, d):
    return ramp(t, a, b) * (1 - ramp(t, c, d))


def gauss(t, c, w):
    return math.exp(-((t - c) / w) ** 2)


# ---------------------------------------------------------------- rig
arm, rig = akb.make_rig({'blend': CH + '/hydra.blend'})
names = rig.names
GROUP = {}
for n in names:
    if n.startswith('neck_c') or n in ('head_c', 'jaw_c'):
        GROUP[n] = 'neck_c'
    elif n.startswith('neck_') or n.startswith('head_'):
        GROUP[n] = 'n' + n.split('_')[1]
    elif n.startswith('tail'):
        GROUP[n] = 'tail'
    elif n.startswith('leg_') or n.startswith('foot_'):
        GROUP[n] = 'legs'
    elif n in ('hips', 'spine_01', 'spine_02', 'spine_03'):
        GROUP[n] = 'spine'
    else:
        GROUP[n] = 'root'
CHAIN_OF = {}
for cname in ['neck_c'] + ['neck_%d' % k for k in range(1, 9)] + ['tail', 'spine_01']:
    for i, bn in enumerate(rig.chains[cname]):
        CHAIN_OF[bn] = (cname, i)
REL = {n: (rig.rest[rig.parent[n]].inverted() @ rig.rest[n]) if rig.parent[n] else None for n in names}
LEGS = ['fl', 'fr', 'bl', 'br']
LB = {l: [f'leg_{l}_01', f'leg_{l}_02', f'leg_{l}_03', f'foot_{l}'] for l in LEGS}
LEGSET = {b for l in LEGS for b in LB[l]}
R0 = rig.roots[0]

natp, _ = akb.apply_grounded(rig, json.load(open(CH + '/natural_pose.json')))
PN = rig.solve(natp)
BN = rig.basis(PN)
QN = {n: BN[n].to_quaternion().normalized() for n in names}
NAT_ROOT_T = BN[R0].translation.copy()          # natural body drop (root bone basis translation)
SN = {l: PN[LB[l][3]].translation.copy() for l in LEGS}          # natural foot joint (armature space)
RN = {l: PN[LB[l][3]].to_3x3().normalized() for l in LEGS}       # natural foot orientation (flat)
SN3 = {l: PN[LB[l][2]].translation.copy() for l in LEGS}         # natural head of leg_03 (top of the hoof unit)
R3N = {l: PN[LB[l][2]].to_3x3().normalized() for l in LEGS}
D3 = {l: SN[l] - SN3[l] for l in LEGS}
ZARM = (rig.RaT @ Vector((0, 0, 1))).normalized()
# lift axis per neck bone: horizontal, across the bone's NATURAL-stance direction (fixed: never flips mid-clip);
# the centre neck points forward, so its lift is the plain world-X bend
LIFT_AX = {}
for _n in names:
    if _n.startswith('neck_') or _n.startswith('head_'):
        _d = PN[_n].to_3x3().col[1].normalized()
        _a = _d.cross(ZARM)
        if _n.startswith('neck_c') or _n == 'head_c' or _a.length < 0.2:
            _a = (rig.RaT @ Vector((-1, 0, 0)))      # = (-Y forward) x Z: + lifts a forward-pointing link
        LIFT_AX[_n] = _a.normalized()
SPL = {n: (rig.rest[c].translation - rig.rest[n].translation).length for n, c in (('spine_01', 'spine_02'), ('spine_02', 'spine_03'))}                           # hoof unit: _03 head -> foot joint


def to_arm(Rw):
    return rig.RaT @ Rw @ rig.Ra


def view_m(v):
    return rig.Ra @ v * rig.s


def life_matrix(bn, ang):
    up, side, rx, rz = ang
    c = CHAIN_OF.get(bn)
    R = akb.rot_xyz(rx, 0.0, rz)
    if c is not None:
        ax = rig.chain_axes[c[0]]
        R = R @ Matrix.Rotation(math.radians(side), 3, ax['side']) @ Matrix.Rotation(math.radians(up), 3, ax['up'])
    return R


def load_action(path):
    data = json.load(open(path))
    akb.clear_anim(arm)
    akb.write_action(rig, data)
    act = arm.animation_data.action
    fcs = {}
    for fc in akb.action_fcurves(act):
        fcs[(fc.data_path, fc.array_index)] = fc
    return data, fcs


def eval_o(fcs, fps, length, loop, t):
    if loop:
        t = t % length
    else:
        t = min(max(t, 0.0), length)
    f = t * fps
    Q, L = {}, {}
    for n in names:
        dp = f'pose.bones["{n}"].rotation_quaternion'
        q = Quaternion([fcs[(dp, i)].evaluate(f) for i in range(4)]).normalized() if (dp, 0) in fcs else Quaternion()
        Q[n] = q
        lp = f'pose.bones["{n}"].location'
        L[n] = Vector([fcs[(lp, i)].evaluate(f) for i in range(3)]) if (lp, 0) in fcs else Vector()
    return Q, L


def fk_all(Q, L, extra=None):
    """plain FK from local quats/locs (+ optional world-axis deltas {bone: Matrix3 in armature axes})"""
    P = {}
    for n in names:
        B4 = Matrix.Translation(L[n]) @ Q[n].to_matrix().to_4x4()
        p = rig.parent[n]
        M = (rig.rest[n] @ B4) if p is None else (P[p] @ REL[n] @ B4)
        if extra and n in extra:
            M = Matrix.Translation(M.translation) @ (extra[n] @ M.to_3x3()).to_4x4()
        P[n] = M
    return P


# ---------------------------------------------------------------- leg IK
REG = PARAMS.get('ik_reg', [0.0015, 0.004, 0.0015, 0.003])   # metres of foot error worth one degree of correction
REG4 = REG[:3] + [PARAMS.get('ik_reg_hoof', 0.02)]


def corr(rx, ry):
    return to_arm(akb.rot_xyz(rx, ry, 0.0))


def leg_fk(P, l, Qd, Ld, x, R3=None, Rfoot=None):
    """the leg's 4 bones; x = [rx at _01, ry at _01, rx at _02] (world view-axis deltas); R3/Rfoot = absolute world
    orientation of the lowest segment (_03) and the foot: the hoof unit is placed rigidly, so its skin never deforms"""
    out = {}
    prev = P[rig.parent[LB[l][0]]]
    a3 = x[3] if len(x) > 3 else 0.0
    cs = [(x[0], x[1]), (x[2], 0.0), None, None]
    for k, n in enumerate(LB[l]):
        M = prev @ REL[n] @ (Matrix.Translation(Ld[n]) @ Qd[n].to_matrix().to_4x4())
        if cs[k] is not None and (abs(cs[k][0]) > 1e-9 or abs(cs[k][1]) > 1e-9):
            M = Matrix.Translation(M.translation) @ (corr(*cs[k]) @ M.to_3x3()).to_4x4()
        if k == 2 and R3 is not None:
            M = Matrix.Translation(M.translation) @ R3.to_4x4()
        if k == 2 and abs(a3) > 1e-9:      # last resort: tilt the hoof unit's upper segment (heavily regularised)
            M = Matrix.Translation(M.translation) @ (corr(a3, 0.0) @ M.to_3x3()).to_4x4()
        if k == 3 and Rfoot is not None:
            M = Matrix.Translation(M.translation) @ Rfoot.to_4x4()
        out[n] = M
        prev = M
    return out


def solve_leg(P, l, Qd, Ld, tgt, x0, R3=None):
    """place the foot joint (head of foot_<l>) on tgt; the hoof unit keeps orientation R3 unless out of reach"""
    x = np.array((list(x0) + [0.0])[:4], float)
    jf = LB[l][3]
    W = np.diag(np.array(REG4) ** 2)
    for it in range(14):
        f0 = leg_fk(P, l, Qd, Ld, x, R3)[jf].translation
        r = np.array(f0 - tgt) * rig.s
        if float(np.linalg.norm(r)) < 2e-4 and it > 0:
            break
        J = np.zeros((3, 4))
        for j in range(4):
            xx = x.copy(); xx[j] += 0.05
            f1 = leg_fk(P, l, Qd, Ld, xx, R3)[jf].translation
            J[:, j] = np.array(f1 - f0) * rig.s / 0.05
        A = J.T @ J + W
        b = -(J.T @ r + W @ x)
        x = x + np.linalg.solve(A, b)
    f0 = leg_fk(P, l, Qd, Ld, x, R3)[jf].translation
    return x, float(np.linalg.norm(np.array(f0 - tgt) * rig.s))


def ik_legs(P, Qd, Ld, targets, r3s, rfeet, xprev, wk=None):
    """re-solve the four legs in P (in place). targets = per leg the wanted _03 head; r3s/rfeet = the hoof unit's
    world orientation. wk: per leg weight 0..1 (death collapse: fades back to the free original leg)"""
    xs, errs = {}, {}
    for l in LEGS:
        if targets.get(l) is None:
            continue
        w = 1.0 if wk is None else wk[l]
        R3, Rf = r3s[l], rfeet[l]
        if w < 1.0:
            Mf = leg_fk(P, l, Qd, Ld, [0, 0, 0, 0])
            R3 = Mf[LB[l][2]].to_3x3().normalized().to_quaternion().slerp(R3.to_quaternion(), w).to_matrix()
            Rf = Mf[LB[l][3]].to_3x3().normalized().to_quaternion().slerp(Rf.to_quaternion(), w).to_matrix()
        x, e = solve_leg(P, l, Qd, Ld, targets[l], xprev.get(l, [0, 0, 0, 0]), R3)
        if e > 0.02:          # warm start went astray: try from the un-corrected leg, keep the better
            x2, e2 = solve_leg(P, l, Qd, Ld, targets[l], [0, 0, 0, 0], R3)
            if e2 < e:
                x, e = x2, e2
        xs[l], errs[l] = x, e
        P.update(leg_fk(P, l, Qd, Ld, list(np.array(x) * w), R3, Rf))
    return xs, errs


# ---------------------------------------------------------------- output
def pose_of(P):
    pose = {'space': 'absolute', 'bones': {}}
    for n in names:
        if n in rig.driven_all:
            continue
        p = rig.parent[n]
        follow = rig.rest[n] if p is None else P[p] @ REL[n]
        R = P[n].to_3x3().normalized()
        if p is not None and R.to_quaternion().rotation_difference(follow.to_3x3().normalized().to_quaternion()).angle < math.radians(0.02):
            continue
        Rw = rig.Ra @ (R @ rig.rest[n].to_3x3().normalized().inverted()) @ rig.RaT
        e = Rw.to_euler('XYZ')
        pose['bones'][n] = {'rx': round(math.degrees(e.x), 4), 'ry': round(math.degrees(e.y), 4), 'rz': round(math.degrees(e.z), 4)}
    dt = rig.Ra @ (P[R0].translation - rig.rest[R0].translation) * rig.s
    pose['root'] = {'loc': [round(v, 5) for v in dt]}
    return pose


def foot_track(P_list):
    return {l: [view_m(P[LB[l][3]].translation) for P in P_list] for l in LEGS}


# ================================================================ re-base clips
LIFT = {}


def life_angles(clip, cfg, t, length, loop):
    L = {}
    LIFT.clear()

    def lift(bn, deg):
        LIFT[bn] = LIFT.get(bn, 0.0) + deg

    def add(bn, up=0.0, side=0.0, rx=0.0, rz=0.0):
        a = L.get(bn, [0.0, 0.0, 0.0, 0.0])
        L[bn] = [a[0] + up, a[1] + side, a[2] + rx, a[3] + rz]

    def fq(f):
        if not loop:
            return f
        return max(1, round(f * length)) / length

    tb = 1.5 if loop else 3.5
    breath = math.sin(TAU * t / tb)
    for i, bn in enumerate(rig.chains['spine_01']):
        add(bn, up=0.45 * breath, side=0.35 * math.sin(TAU * fq(0.19) * t + 1.0))
    add('tail_01', up=0.4 * breath)
    # head_down: the side heads hold the chin rest (the original loop's own side-head motion is left out, it carried
    # head_5's seam jump), so their weave and the tail stir are larger there
    lk = PARAMS.get('life_k', {}).get(clip, 1.0)
    for g in SIDE + ['neck_c']:
        h = HEAD[g]
        cn = 'neck_c' if g == 'neck_c' else 'neck_' + g[1:]
        nlinks = 5 if g == 'neck_c' else 4
        for i, bn in enumerate(rig.chains[cn]):
            if bn == 'jaw_c':
                continue
            k = (0.6 + 0.15 * i) * (lk if g != 'neck_c' else 1.0)
            up = h['a'] * k * math.sin(TAU * fq(h['fu']) * t + h['ph'] - 0.45 * i)
            side = 0.8 * h['a'] * k * math.sin(TAU * fq(h['fs']) * t + 1.7 * h['ph'] - 0.45 * i)
            if i == 0:
                up += 0.5 * breath
            rz = 0.0
            if i == nlinks:
                rz = 2.5 * h['a'] * math.sin(TAU * fq(h['fs'] * 0.7) * t + h['ph'] + 0.9)
            add(bn, up=up, side=side, rz=rz)
    for i, bn in enumerate(rig.chains['tail']):
        add(bn, side=1.1 * lk * (0.5 + 0.12 * i) * math.sin(TAU * fq(0.24) * t - 0.5 * i),
            up=0.4 * (0.5 + 0.1 * i) * math.sin(TAU * fq(0.17) * t - 0.4 * i + 2.0))

    def heads_react(fn):
        for g in SIDE + ['neck_c']:
            if g in cfg['act']:
                continue
            cn = 'neck_c' if g == 'neck_c' else 'neck_' + g[1:]
            for i, bn in enumerate(rig.chains[cn]):
                if bn == 'jaw_c':
                    continue
                r = fn(g, i)
                if r:
                    add(bn, *r)

    if clip in ('bite', 'bite_l', 'bite_r'):
        ti = 1.5
        s_act = {'bite': 0.0, 'bite_l': 1.0, 'bite_r': -1.0}[clip]

        def f(g, i):
            h = HEAD[g]; sg = 1.0 if HX[g] > 0 else -1.0
            ant = bump(t, 0.9, 1.30, 1.42, 1.62)
            r = rec(t, ti + h['dl'], f=1.6, tau=0.32)
            up = 2.0 * ant * (0.5 + 0.2 * i) + 2.4 * r * (1.0 - 0.1 * i)
            side = 2.6 * sg * r * (0.6 + 0.15 * i)
            rz = 0.0
            nl = 5 if g == 'neck_c' else 4
            if i == nl:
                rz = 14.0 * s_act * bump(t, 0.6, 1.2, 2.3, 3.0) - 6.0 * sg * r
            if g == 'neck_c' and clip != 'bite':
                up *= 0.6
            return (up, side, 0.0, rz)
        heads_react(f)
        for i, bn in enumerate(rig.chains['tail']):
            add(bn, side=-(s_act or 1.0) * 2.0 * (0.4 + 0.15 * i) * rec(t, ti + 0.05 * i, f=1.2, tau=0.5))

    if clip.startswith('fire_sweep'):
        if clip == 'fire_sweep':
            sw = (1.7, 3.95, -5.5, 5.5); fs, fe = 1.5, 4.05
        elif clip == 'fire_sweep_l':
            sw = (1.7, 3.95, 5.5, -5.5); fs, fe = 1.5, 4.05
        elif clip == 'fire_sweep_return':
            sw = (0.0, 2.2, 5.5, -5.5); fs, fe = 0.0, 2.2
        else:
            sw = (0.0, 2.2, -5.5, 5.5); fs, fe = 0.0, 2.2
        a, b, x0, x1 = sw
        s = x0 + (x1 - x0) * min(max((t - a) / (b - a), 0.0), 1.0)
        fire = bump(t, fs + 0.2, fs + 0.45, fe - 0.1, fe + 0.3)

        def f(g, i):
            h = HEAD[g]
            p = math.exp(-((HX[g] - s) / 2.6) ** 2) * fire
            away = 1.0 if HX[g] >= s else -1.0
            r = rec(t, fs + 0.35 + h['dl'], f=1.4, tau=0.4) if fs > 0.01 else 0.0
            up = 3.0 * p * (0.5 + 0.2 * i) + 2.0 * r
            side = 2.4 * away * p * (0.5 + 0.2 * i)
            nl = 4
            rz = (10.0 * away * p) if i == nl else 0.0
            return (up, side, 0.0, rz)
        heads_react(f)
        for i, bn in enumerate(rig.chains['tail']):
            add(bn, side=-(1.0 if x1 > x0 else -1.0) * 2.2 * (0.4 + 0.12 * i) * math.sin(math.pi * min(max((t - a) / (b - a), 0), 1) - 0.3 * i) * fire)
        # FIX 5: in the _l variants head 8 passes into neck 6 / head 6 while neck 6 leans over it: neck 8 ducks
        duck = PARAMS['duck_n8'].get(clip)
        if duck:
            wd = bump(t, *duck['win'])
            for i, bn in enumerate(rig.chains['neck_8']):
                add(bn, up=duck['up'] * wd * (0.7 + 0.15 * i), side=duck.get('side', 0.0) * wd)

    if clip in ('stomp', 'stomp_r'):
        sp = PARAMS['stomp']

        def f(g, i):
            h = HEAD[g]
            d = REAR_ST[g]
            # rear up (staggered, finished before the whip), then a smooth whip down peaking just before the impact,
            # a delayed, damped rebound and a small settle (no one-frame stop between whip and rebound)
            rear = bump(t, sp['rear_a'] + d, sp['rear_b'] + d, sp['rear_c'] + 0.3 * d, sp['rear_d'])
            amp = sp['rear_amp'] * sp['rear_k'].get(g, 1.0)
            wc = sp['whip_c'] + 0.25 * h['dl']
            whip = gauss(t, wc, sp['whip_w'])
            reb = gauss(t, wc + sp['reb_delay'], sp['reb_w'])
            settle = gauss(t, wc + sp['reb_delay'] * 2.1, sp['reb_w'] * 1.2)
            k = (0.6 + 0.12 * i)
            # rear and whip LIFT the neck toward +Z about its own horizontal cross axis (the side necks fan out
            # sideways, so a world-X bend_up would only twist them)
            nl = 5 if g == 'neck_c' else 4
            prof = sp['rear_prof'][i] if i < nl else sp['rear_head']
            cn = 'neck_c' if g == 'neck_c' else 'neck_' + g[1:]
            lift(rig.chains[cn][i], amp * rear * prof - sp['whip_amp'] * k * (whip - sp['reb_k'] * reb + 0.2 * sp['reb_k'] * settle))
            side = 0.8 * (1 if HX[g] > 0 else -1) * sp['reb_k'] * reb
            return (0.0, side, 0.0, 0.0)
        heads_react(f)
        # centre neck follow-through: it keeps travelling down for ~0.15 s while the keyed body bounces up off the
        # impact, then eases back (softens the body's one-frame V turn at the head)
        for i, bn in enumerate(rig.chains['neck_c'][:6]):
            lift(bn, -sp['follow_amp'] * (0.6 + 0.12 * i) * bump(t, sp['follow'][0], sp['follow'][1], sp['follow'][2], sp['follow'][3]))
        for i, bn in enumerate(rig.chains['tail']):
            wc = sp['whip_c'] + 0.04 * i
            add(bn, up=1.6 * (0.4 + 0.1 * i) * bump(t, 0.5, 1.4, 1.62, 2.1)
                - 1.2 * (gauss(t, wc + 0.03, 0.09) - 0.4 * gauss(t, wc + 0.30, 0.14)))
        # FIX 4: neck_5 bends away from the centre neck while the hip shift carries neck_c toward it
        if clip == 'stomp':
            nb = PARAMS['stomp_n5']
            wv = bump(t, *nb['win'])
            for i, bn in enumerate(rig.chains['neck_5']):
                add(bn, side=nb['side'] * wv, up=nb.get('up', 0.0) * wv)
        # outer necks lean outward while the fan rears up, so neighbours never meet (stomp_side: chain -> deg per link)
        for cn_, sd_ in PARAMS['stomp_side'].items():
            wv6 = bump(t, *PARAMS['stomp_side_win'])
            for i, bn in enumerate(rig.chains[cn_]):
                add(bn, side=sd_ * wv6)

    if clip == 'hurt':
        ti = 0.0667

        def f(g, i):
            h = HEAD[g]
            r = rec(t, ti + 0.06 + h['dl'], f=1.5, tau=0.25, ease=0.1)
            return (3.2 * r * (0.6 + 0.15 * i), 1.6 * (1 if HX[g] > 0 else -1) * r, 0.0, 0.0)
        heads_react(f)
        for i, bn in enumerate(rig.chains['tail']):
            add(bn, side=3.0 * (0.4 + 0.12 * i) * rec(t, ti + 0.05 + 0.03 * i, f=2.0, tau=0.3))

    if clip == 'hurt_standing':
        ti = 0.125
        fl = rec(t, ti, f=1.4, tau=0.3)
        for i, bn in enumerate(rig.chains['neck_c']):
            if bn == 'jaw_c':
                add(bn, rx=10.0 * bump(t, 0.08, 0.2, 0.5, 0.9))
            elif bn == 'head_c':
                add(bn, up=12.0 * fl, rz=-5.0 * fl)
            else:
                add(bn, up=3.0 * fl * (0.4 + 0.15 * i), side=-1.5 * fl)
        for i, bn in enumerate(rig.chains['spine_01']):
            add(bn, side=1.6 * rec(t, ti, f=3.5, tau=0.25), up=-1.0 * rec(t, ti, f=2.0, tau=0.3))
        for i, bn in enumerate(rig.chains['tail']):
            add(bn, side=3.0 * (0.4 + 0.12 * i) * rec(t, ti + 0.04 * i, f=1.8, tau=0.35))

    if clip in ('death', 'death_standing'):
        t0, t1 = (0.3, 2.3) if clip == 'death' else (0.7, 4.0)
        amp = ramp(t, t0, t0 + 0.4) * (1 - ramp(t, t1 - 0.6, t1 + 0.3))
        for i, bn in enumerate(rig.chains['tail']):
            add(bn, side=4.0 * (0.3 + 0.13 * i) * amp * math.sin(TAU * 1.1 * t - 0.6 * i))
        if clip == 'death_standing':
            for i, bn in enumerate(rig.chains['spine_01']):
                add(bn, side=1.5 * amp * math.sin(TAU * 0.9 * t - 0.3 * i))

    if loop:
        env = 1.0
    else:
        env = 1.0
        if cfg['start'] in ('natural', 'down'):
            env *= ramp(t, 0.0, 0.35)
        if cfg['end'] in ('natural', 'down'):
            env *= 1 - ramp(t, length - 0.35, length)
        env_d = (1 - ramp(t, 1.9, 2.5)) if clip == 'death' else ((1 - ramp(t, 3.4, 4.2)) if clip == 'death_standing' else None)
        if env_d is not None:
            for bn in list(L):
                if GROUP[bn] != 'tail':
                    L[bn] = [v * env_d for v in L[bn]]
    return L, env


def weights(clip, cfg, t, length, loop):
    W = {}
    for g in ALLG:
        mid = 0.0 if g in cfg['act'] else 1.0

        def bval(kind):
            if kind == 'natural':
                return 1.0
            if kind == 'down':
                return 0.0 if g in DOWN_ACT else 1.0
            return mid
        if loop:
            W[g] = mid
            continue
        s, e = bval(cfg['start']), bval(cfg['end'])
        win_s = 0.35 if clip.startswith('death') else WIN
        a = ramp(t, 0.0, win_s)
        b = ramp(t, length - WIN, length)
        w = s + (mid - s) * a
        w = w + (e - w) * b
        if clip == 'death' and g == 'tail':
            w *= 1 - ramp(t, 1.75, 2.05)
        if clip == 'death_standing' and g in ('tail', 'spine'):
            w *= 1 - ramp(t, 3.0, 3.45)
        W[g] = w
    if clip in ('head_down', 'hurt', 'death'):
        d = 1.0
    elif clip.startswith('fire_sweep'):
        d = ramp(t, length - 0.65, length)
    else:
        d = 0.0
    return W, d


def droop_of(clip, g, t, length, d):
    if clip == 'head_up':
        h = HEAD[g]
        return 1 - ramp(t, 0.1 + 2.0 * h['dl'], 0.9 + 2.5 * h['dl'])
    return d


def leg_weight(clip, t):
    """weight of the natural-stance legs + foot IK (1 everywhere except the death collapse)"""
    if clip.startswith('death'):
        return 1.0 - ramp(t, 0.0, 0.35)
    return 1.0


def smooth_q(fcs, fps, length, loop, t, taps):
    """weighted quaternion average of the original around t (low-pass for single-frame snaps)"""
    acc = {n: Vector((0, 0, 0, 0)) for n in names}
    ref = None
    tw = sum(w for _, w in taps)
    for dtk, w in taps:
        Q, _ = eval_o(fcs, fps, length, loop, t + dtk / fps)
        if ref is None:
            ref = Q
        for n in names:
            q = Q[n]
            if q.dot(ref[n]) < 0:
                q = -q
            acc[n] += Vector(q) * (w / tw)
    return {n: Quaternion(acc[n]).normalized() for n in names}


def compose(clip, cfg, fcs, data, t, life_shift=None, extra_world=None):
    """one frame -> (P without leg IK, desired leg locals, Wlegs) ; extra_world: {bone: (up, side, rx, rz)} added"""
    fps, length, loop = data['fps_src'], data['length'], data['loop']
    W, d = weights(clip, cfg, t, length, loop)
    QO, LO = eval_o(fcs, fps, length, loop, t)
    stag = {}
    Q0 = data['_q0']; QL = data['_qL']
    uref = ss(t / length)
    for g in SIDE + ['neck_c', 'tail']:
        if g not in cfg['act'] and g in HEAD and HEAD[g]['st'] > 0:
            if clip == 'head_down':
                stag[g] = Q0      # the original loop's side heads hold the chin rest (its head_5 seam jump stays out)
            else:
                # the stagger fades out over the last 0.5 s so the end pose is the original's end pose (clean joins)
                st_ = HEAD[g]['st'] * (1.0 if loop else 1.0 - ramp(t, length - 0.5, length))
                if clip == 'hurt':
                    stag[g] = smooth_q(fcs, fps, length, loop, t - st_, PARAMS['hurt_taps'])
                else:
                    stag[g] = eval_o(fcs, fps, length, loop, t - st_)[0]
    life, env = life_angles(clip, cfg, t, length, loop)
    LIFT_F = dict(LIFT)
    if life_shift:
        for bn, v in life_shift.items():
            a = life.get(bn, [0.0, 0.0, 0.0, 0.0])
            life[bn] = [a[k] - v[k] for k in range(4)]
    wl = leg_weight(clip, t)
    P = {}
    Qd, Ld = {}, {}
    for n in names:
        g = GROUP[n]
        qo = QO[n]
        Lo = LO[n]
        if g == 'root':
            q = qo
            # natural body drop with the old leg-group weight (natural boundaries; hurt_standing throughout)
            Lo = Lo + NAT_ROOT_T * max(W['legs'], PARAMS['root_drop_mid'].get(clip, 0.0))
        elif g == 'legs':
            qp = QN[n] @ qo
            q = qo.slerp(qp, wl) if wl < 1 - 1e-9 else qp
            Qd[n], Ld[n] = q, Lo
        else:
            w = W[g]
            if g in stag:
                # scale the original's motion relative to its first frame (the chin rest for down-start clips)
                # reference = the original's first pose blending to its last pose: both boundary poses stay exact
                # (chin rest / natural stance joins), only the motion in between is scaled
                q0 = Q0[n] if (loop or uref <= 0.0) else Q0[n].slerp(QL[n], uref)
                dq = q0.inverted() @ stag[g][n]
                ax_, an_ = dq.to_axis_angle()
                if an_ > math.pi:
                    an_ -= 2 * math.pi
                qs = q0 @ Quaternion(ax_, an_ * HEAD[g]['sc'])
            else:
                qs = qo
            qp = QN[n] @ qs
            q = qo.slerp(qp, w) if w < 1 - 1e-9 else qp
            if w <= 1e-9:
                q = qo
        B4 = Matrix.Translation(Lo) @ q.to_matrix().to_4x4()
        p = rig.parent[n]
        M = (rig.rest[n] @ B4) if p is None else (P[p] @ REL[n] @ B4)
        if g not in ('root', 'legs'):
            ang = None
            if n in life:
                k = W[g] * env
                if k > 1e-6:
                    ang = [v * k for v in life[n]]
            if g in DROOP:
                dd = droop_of(clip, g, t, length, d) * W[g]
                if dd > 1e-6:
                    ang = ang or [0.0, 0.0, 0.0, 0.0]
                    ang[0] += DROOP[g] * dd
            if extra_world and n in extra_world:
                ang = ang or [0.0, 0.0, 0.0, 0.0]
                ang = [ang[k] + extra_world[n][k] for k in range(4)]
            if ang is not None and any(abs(v) > 1e-5 for v in ang):
                R = to_arm(life_matrix(n, ang))
                M = Matrix.Translation(M.translation) @ (R @ M.to_3x3()).to_4x4()
            lv = LIFT_F.get(n, 0.0) * W[g] * env
            if abs(lv) > 1e-5 and n in LIFT_AX:
                M = Matrix.Translation(M.translation) @ (Matrix.Rotation(math.radians(lv), 3, LIFT_AX[n]) @ M.to_3x3()).to_4x4()
        P[n] = M
    return P, Qd, Ld, wl


def foot_targets_from_original(Fo, Ro, Ro3, nfr):
    """per leg: natural floor point while the original foot is planted; while the original LIFTS it, follow the
    original's lift path relative to its lift-off point, corrected linearly so it lands where it lifted."""
    T, RF, R3F, lifted = {}, {}, {}, {}
    for l in LEGS:
        z = np.array([f.z for f in Fo[l]])
        zmin = float(z.min())
        h = z - zmin
        up = h > PARAMS['lift_thr']
        # grow each lifted run by one frame each side so the path starts/ends on the floor
        segs = []
        i = 0
        while i < nfr:
            if up[i]:
                a = i
                while i < nfr and up[i]:
                    i += 1
                segs.append((max(a - 1, 0), min(i, nfr - 1)))
            else:
                i += 1
        lifted[l] = [(a, b, float(h[a:b + 1].max())) for a, b in segs]
        Tl = [SN[l].copy() for _ in range(nfr)]
        Rl = [RN[l].copy() for _ in range(nfr)]
        R3l = [R3N[l].copy() for _ in range(nfr)]
        for a, b in segs:
            if h[a:b + 1].max() < PARAMS['lift_min']:
                continue        # crouch noise, not a step: keep planted
            net = Fo[l][b] - Fo[l][a]
            za = Fo[l][a].z
            for k in range(a, b + 1):
                u = ss((k - a) / max(b - a, 1))
                dv = (Fo[l][k] - Fo[l][a]) - net * u
                hz = max(0.0, Fo[l][k].z - za - net.z * u)
                hk = ss(hz / PARAMS.get('travel_full_h', 0.3))      # sideways/forward travel only once the hoof is up
                Tl[k] = Vector((SN[l].x + hk * dv.x, SN[l].y + hk * dv.y, SN[l].z + hz))
                # the original's hoof tilt only while the foot is well up: flat again as it reaches the floor
                wt = ss((Fo[l][k].z - za) / PARAMS.get('tilt_full_h', 0.35))
                idq = Quaternion()
                Rl[k] = idq.slerp((Ro[l][k] @ Ro[l][a].inverted()).to_quaternion(), wt).to_matrix() @ RN[l]
                R3l[k] = idq.slerp((Ro3[l][k] @ Ro3[l][a].inverted()).to_quaternion(), wt).to_matrix() @ R3N[l]
        # wanted head of leg_03 = foot target minus the (rotated) hoof unit
        T[l], RF[l], R3F[l] = Tl, Rl, R3l
    return T, RF, R3F, lifted


def run_rebase(clip):
    cfg = CLIPS_CFG[clip]
    d = f'{CH}/clips/{cfg["dir"]}'
    src = f'{d}/action_{clip}.rest_v1.json'
    data, fcs = load_action(src)
    data['fps_src'] = data['fps']
    data['_q0'] = eval_o(fcs, data['fps'], data['length'], data['loop'], 0.0)[0]
    data['_qL'] = eval_o(fcs, data['fps'], data['length'], data['loop'], data['length'])[0]
    fps, length, loop = data['fps'], data['length'], data['loop']
    if not clip.startswith('death') and abs(round(length * 30) - length * 30) < 1e-3:
        fps = 30.0        # key every GLB frame: no in-between drift of the IK'd feet when the original snaps
        data = dict(data); data['fps'] = fps
    nfr = int(round(length * fps))
    frames = list(range(nfr)) if loop else list(range(nfr + 1))
    N = len(frames)
    # pass 1: the original's own feet (FK of the original action)
    Fo, Ro, Ro3 = {l: [] for l in LEGS}, {l: [] for l in LEGS}, {l: [] for l in LEGS}
    for fr in frames:
        QO, LO = eval_o(fcs, data['fps_src'], length, loop, fr / fps)
        PO = fk_all(QO, LO)
        for l in LEGS:
            Fo[l].append(PO[LB[l][3]].translation.copy())
            Ro[l].append(PO[LB[l][3]].to_3x3().normalized())
            Ro3[l].append(PO[LB[l][2]].to_3x3().normalized())
    T, RF, R3F, lifted = foot_targets_from_original(Fo, Ro, Ro3, N)
    # head_down: every life layer zero at t = 0 (the shared chin rest); flank pant with the jaw kept exact
    life0 = None
    if clip == 'head_down':
        life0, _ = life_angles(clip, cfg, 0.0, length, loop)
    keys, xprev, errs_max, P_list = [], {}, {l: 0.0 for l in LEGS}, []
    err_t = {}
    for fr in frames:
        t = fr / fps
        extra = None
        if clip == 'head_down':
            hp = PARAMS['head_down_pant']
            pant = math.sin(TAU * t / length)          # one pant per loop (1.5 s), zero at the seam
            # bulge: spine_01 +a, spine_02 -(1 + l1/l2) a, spine_03 +(l1/l2) a keeps spine_03's tip and direction
            # (so the centre neck and the jaw) in place while the mid back / flank heaves
            r12 = SPL['spine_01'] / SPL['spine_02']
            a_ = hp['amp'] * pant
            extra = {'spine_01': (a_, 0, 0, 0), 'spine_02': (-(1 + r12) * a_, 0, 0, 0), 'spine_03': (r12 * a_, 0, 0, 0)}
            for g in SIDE:      # neck bases ride the pant
                extra['neck_%s_01' % g[1:]] = (hp['neck'] * pant, 0, 0, 0)
        P, Qd, Ld, wl = compose(clip, cfg, fcs, data, t, life_shift=life0, extra_world=extra)
        if clip == 'head_down' and extra:
            Pref, _, _, _ = compose(clip, cfg, fcs, data, t, life_shift=life0, extra_world=None)
            # counter-rotate neck_c_01 so the jaw (weak point) stays exactly where the un-panted pose has it
            P0 = P
            comp = Matrix.Identity(3)
            for it in range(4):
                J = P['jaw_c'].translation; Jr = Pref['jaw_c'].translation
                H = P['neck_c_01'].translation
                e = Jr - J
                if e.length < 1e-7:
                    break
                v = J - H
                axis = v.cross(e)
                if axis.length < 1e-12:
                    break
                comp = Matrix.Rotation(e.length / v.length, 3, axis.normalized()) @ comp
                P = reapply_subtree(P0, 'neck_c_01', comp)
            if os.environ.get('FXDBG'):
                print('DBG t=%.3f jaw P0 %s Pref %s P %s' % (t, tuple(round(c, 3) for c in view_m(P0['jaw_c'].translation)), tuple(round(c, 3) for c in view_m(Pref['jaw_c'].translation)), tuple(round(c, 3) for c in view_m(P['jaw_c'].translation))))
        tg = {l: T[l][fr] for l in LEGS}
        rf = {l: RF[l][fr] for l in LEGS}
        r3 = {l: R3F[l][fr] for l in LEGS}
        wk = {l: wl for l in LEGS}
        xs, errs = ik_legs(P, Qd, Ld, tg, r3, rf, xprev, wk if wl < 1 - 1e-9 else None)
        xprev = xs
        if wl > 0.5:
            for l in LEGS:
                if errs[l] > errs_max[l]:
                    errs_max[l] = errs[l]; err_t[l] = round(t, 3)
        P_list.append(P)
        keys.append({'t': round(t, 5), 'pose': pose_of(P)})
    out = {'fps': fps, 'loop': loop, 'length': length, 'events': data['events'],
           'note': (f'fix3 2026-11-23 (work/animfix3_hydra/fix_bl.py): re-base v2 of {os.path.basename(src)}, one key per frame; '
                    f'acting groups {sorted(cfg["act"] - {"legs"})} exact in the middle; legs = natural stance x keyed motion, '
                    f'feet re-solved per frame with IK on the natural floor points (lifted feet follow the original lift path); '
                    f'start={cfg["start"]} end={cfg["end"]}; previous version in backup_20261123/fix3_pre/'),
           'keys': keys}
    json.dump(out, open(f'{OUT}/keys_{clip}.json', 'w'))
    ft = foot_track(P_list)
    slide = {}
    for l in LEGS:
        pts = ft[l]
        s = 0.0
        for a, b in zip(pts, pts[1:]):
            if a.z < 0.42 and b.z < 0.42:
                s += math.hypot(b.x - a.x, b.y - a.y)
        slide[l] = round(s, 3)
    return {'frames': N, 'fps': fps, 'length': length, 'loop': loop, 'ik_err_max_m': {l: round(v, 4) for l, v in errs_max.items()}, 'ik_err_t': err_t,
            'planted_slide_m': slide, 'lifted': {l: [(a / fps, b / fps, round(h, 2)) for a, b, h in lifted[l] if h >= PARAMS['lift_min']] for l in LEGS}}


def reapply_subtree(P, top, Rw_arm):
    """rotate bone `top` (and everything below it) by the armature-space rotation Rw_arm about top's head"""
    H = P[top].translation.copy()
    G = Matrix.Translation(H) @ Rw_arm.to_4x4() @ Matrix.Translation(-H)
    sub = set()
    for n in names:
        if n == top or rig.parent[n] in sub:
            sub.add(n)
    P2 = dict(P)
    for n in sub:
        P2[n] = G @ P[n]
    return P2


# ================================================================ idle
def run_idle():
    ip = PARAMS['idle']
    data, fcs = load_action(CH + '/clips/idle_n/base/action_idle_base.json')
    fps, length, loop = data['fps'], data['length'], data['loop']
    nfr = int(round(length * fps))
    frames = list(range(nfr))
    # the chest drift of the base clip (spine_03 head x, view metres) drives the hip sway
    cx = []
    for fr in frames:
        QO, LO = eval_o(fcs, fps, length, loop, fr / fps)
        PO = fk_all(QO, LO)
        cx.append(view_m(PO['neck_c_01'].translation).x)      # front of the chest
    cx = np.array(cx) - cx[0]
    cmax = float(np.abs(cx).max()) or 1.0
    keys, xprev, errs_max, P_list = [], {}, {l: 0.0 for l in LEGS}, []
    for fr in frames:
        t = fr / fps
        QO, LO = eval_o(fcs, fps, length, loop, t)
        b = math.sin(TAU * ip['breaths'] * t / length)           # 0 at the seam (= natural stance)
        extra = {'spine_02': to_arm(life_matrix('spine_02', (ip['pitch2'] * b, 0, 0, 0))),
                 'spine_03': to_arm(life_matrix('spine_03', (ip['pitch3'] * b, 0, 0, 0)))}
        # neck bases ride the chest (children of spine_03) and lift a touch more on the inhale
        for k in range(1, 9):
            extra['neck_%d_01' % k] = to_arm(life_matrix('neck_%d_01' % k, (ip['neck'] * b, 0, 0, 0)))
        Lr = dict(LO)
        sway = ip['sway_m'] * cx[fr] / cmax
        dz = ip['bob_m'] * b                                        # body rises on the inhale, sinks on the exhale
        Lr[R0] = LO[R0] + (rig.rest[R0].to_3x3().inverted() @ (rig.RaT @ Vector((sway, 0.0, dz)) / rig.s))
        P = fk_all(QO, Lr, extra)
        Qd = {n: QO[n] for n in LEGSET}; Ld = {n: LO[n] for n in LEGSET}
        xs, errs = ik_legs(P, Qd, Ld, {l: SN[l] for l in LEGS}, {l: R3N[l] for l in LEGS}, {l: RN[l] for l in LEGS}, xprev)
        xprev = xs
        for l in LEGS:
            errs_max[l] = max(errs_max[l], errs[l])
        P_list.append(P)
        keys.append({'t': round(t, 5), 'pose': pose_of(P)})
    out = {'fps': fps, 'loop': True, 'length': length, 'events': {},
           'note': ('fix3 2026-11-23 (work/animfix3_hydra/fix_bl.py idle): base = clips/idle_n/base/action_idle_base.json (the anim2 '
                    'traced+authored idle, its keys in base/keys_idle_base.json) + %d breaths per loop (spine_02 %.1f / spine_03 %.1f deg, '
                    'neck bases %.1f deg), root bob %.3f m, hip sway %.3f m with the chest drift; legs re-solved per frame (feet planted '
                    'on the natural floor points). First key = natural stance.' % (ip['breaths'], ip['pitch2'], ip['pitch3'], ip['neck'], ip['bob_m'], ip['sway_m'])),
           'keys': keys}
    json.dump(out, open(f'{OUT}/keys_idle.json', 'w'))
    ft = foot_track(P_list)
    return {'frames': len(frames), 'ik_err_max_m': {l: round(v, 4) for l, v in errs_max.items()},
            'foot_range_m': {l: round(max((a - ft[l][0]).length for a in ft[l]), 4) for l in LEGS}}


# ================================================================ turn in place
def run_turn(clip):
    tp = PARAMS['turn']
    dirn = 1.0 if clip.endswith('_l') else -1.0          # +1: body turns CCW seen from above (to its left)
    data, fcs = load_action(CH + '/clips/walk_n/action_walk.json')
    fps, length = data['fps'], data['length']
    nfr = int(round(length * fps))
    frames = list(range(nfr))
    gp = json.load(open(CH + '/clips/walk_n/poses_walk/gen_params_n.json'))
    D = gp.get('duty', 0.7)
    T_st = D * length
    # pass 1: the walk's own feet (lift height and timing)
    Fo = {l: [] for l in LEGS}
    Ro = {l: [] for l in LEGS}
    Ro3 = {l: [] for l in LEGS}
    for fr in frames:
        QO, LO = eval_o(fcs, fps, length, True, fr / fps)
        PO = fk_all(QO, LO)
        for l in LEGS:
            Fo[l].append(PO[LB[l][3]].translation.copy())
            Ro[l].append(PO[LB[l][3]].to_3x3().normalized())
            Ro3[l].append(PO[LB[l][2]].to_3x3().normalized())
    zpl = {l: min(f.z for f in Fo[l]) for l in LEGS}
    zroot_mean = sum(eval_o(fcs, fps, length, True, k / fps)[1][R0].z for k in range(nfr)) / nfr
    kpl = {l: min(range(nfr), key=lambda k: Fo[l][k].z) for l in LEGS}
    # turn pivot = the body origin (armature origin projected on the floor); radius of the natural forefeet
    def ang_r(v):
        w = view_m(v)
        return math.atan2(w.y, w.x), math.hypot(w.x, w.y)
    r_fore = tp['r_game']        # the radius hydra.gd _walk_rate() measures on the foot sockets in Godot
    Om = tp['move_speed'] / r_fore                       # rad per clip second, the same for every foot (rigid body)
    Dth = Om * T_st                                      # stance sweep (rad)
    phi = tp['match_phase']
    keys, xprev, errs_max, P_list = [], {}, {l: 0.0 for l in LEGS}, []
    th_nat = {l: ang_r(SN[l])[0] for l in LEGS}
    rad = {l: ang_r(SN[l])[1] for l in LEGS}

    def theta(l, p):
        u = (p - gp['legs'][l]) % 1.0
        e = gp.get('front_ease', 0.0) if l[0] == 'f' else gp.get('hind_ease', 0.0)
        if u < D:
            prog = u / D
            off = 0.5 - prog                             # +0.5 .. -0.5 over the stance
        else:
            s = (u - D) / (1 - D)
            f = (1 - e) * ss(s) + e * (1 - (1 - s) ** 2.5)
            off = -0.5 + f
        return off
    # arc centre per foot: the natural angle shifted (match x) so that at match_phase the feet sit on their natural spots
    centre = {l: th_nat[l] - tp['match'] * dirn * Dth * theta(l, phi) for l in LEGS}
    zw = {l: [Fo[l][k].z - zpl[l] for k in range(nfr)] for l in LEGS}
    err_rows = []
    warm = list(range(nfr))
    for fr in warm + frames:
        t = fr / fps
        p = t / length
        QO, LO = eval_o(fcs, fps, length, True, t)
        QO = dict(QO)
        QO['hips'] = QN['hips'].slerp(QO['hips'], tp.get('hip_roll_k', 1.0))   # the walk's hip roll, damped
        Lt = dict(LO)
        # body: the walk's bob scaled (tp bob_k), lowered by the crouch so the arcs stay inside the legs' reach
        lz = LO[R0].copy()
        lz.z = zroot_mean + tp.get('bob_k', 1.0) * (LO[R0].z - zroot_mean)
        Lt[R0] = lz + rig.rest[R0].to_3x3().inverted() @ (rig.RaT @ Vector((0, 0, -tp['crouch'])) / rig.s)
        P = fk_all(QO, Lt)
        tg, rf, r3 = {}, {}, {}
        for l in LEGS:
            u_ = (p - gp['legs'][l]) % 1.0
            th = centre[l] + dirn * Dth * theta(l, p)
            r = rad[l]
            wv = Vector((r * math.cos(th), r * math.sin(th), 0.0))
            a = (rig.RaT @ wv) / rig.s
            # lift only in the swing (the walk's planted feet wander 0-5 cm in height: keep stance feet on the floor)
            lift = (max(0.0, zw[l][fr] - tp['lift_dead']) * tp['lift_scale']) if u_ >= D else 0.0
            tf = Vector((a.x, a.y, SN[l].z)) + (rig.RaT @ Vector((0, 0, lift))) / rig.s
            # planted foot keeps its world yaw (turns with the arc in the clip frame); the walk's own foot pitch on top
            yaw = to_arm(akb.rot_xyz(0, 0, math.degrees(th - th_nat[l])))
            # the walk's foot pitch while lifted (relative to its planted orientation)
            # the walk's hoof pitch only while the foot is really in the air (its toe-pivot reach trick near touch-down
            # belongs to the straight walk's foot positions, not to these)
            sl = ss((zw[l][fr] - 0.10) / 0.40) if u_ >= D else 0.0
            ident = Quaternion()
            rel = ident.slerp((Ro[l][fr] @ Ro[l][kpl[l]].inverted()).to_quaternion(), sl).to_matrix()
            rel3 = ident.slerp((Ro3[l][fr] @ Ro3[l][kpl[l]].inverted()).to_quaternion(), sl).to_matrix()
            rf[l] = yaw @ rel @ RN[l]
            r3[l] = yaw @ rel3 @ R3N[l]
            tg[l] = tf
        Qd = {n: QO[n] for n in LEGSET}; Ld = {n: LO[n] for n in LEGSET}
        xs, errs = ik_legs(P, Qd, Ld, tg, r3, rf, xprev)
        xprev = xs
        if warm:
            warm.pop(0)
            continue
        for l in LEGS:
            errs_max[l] = max(errs_max[l], errs[l])
        err_rows.append([round(errs[l], 3) for l in LEGS])
        P_list.append(P)
        keys.append({'t': round(t, 5), 'pose': pose_of(P)})
    out = {'fps': fps, 'loop': True, 'length': length, 'events': {},
           'note': ('fix3 2026-11-23 (work/animfix3_hydra/fix_bl.py %s): upper body, root bob and foot lift timing = clips/walk_n/action_walk.json '
                    '(unchanged walk); legs re-solved per frame so each planted foot moves on its circle about the body origin at %.4f rad '
                    'per clip second (= move_speed %.2f / forefoot radius %.3f m), stance sweep %.1f deg, body turning %s; at clip time '
                    '%.4f s the feet are %d%% of the way onto their natural-stance spots (the stop/start phase for hydra.gd).'
                    % (clip, Om, tp['move_speed'], r_fore, math.degrees(Dth), 'left (CCW from above)' if dirn > 0 else 'right (CW)',
                       phi * length, round(tp['match'] * 100))),
           'keys': keys}
    json.dump(out, open(f'{OUT}/keys_{clip}.json', 'w'))
    # report: stance slide in WORLD for a body turning at Om (clip rate 1): should be ~0
    ft = foot_track(P_list)
    wsl = {}
    for l in LEGS:
        s, n_ = 0.0, 0
        for k in range(nfr):
            a_, b_ = ft[l][k], ft[l][(k + 1) % nfr]
            if a_.z < 0.42 and b_.z < 0.42:
                ta, tb = k / fps, (k + 1) / fps
                def wpos(v, tt):
                    c, s_ = math.cos(dirn * Om * tt), math.sin(dirn * Om * tt)
                    return Vector((c * v.x - s_ * v.y, s_ * v.x + c * v.y))
                s += (wpos(b_, tb) - wpos(a_, ta)).length
                n_ += 1
        wsl[l] = round(s / max(n_, 1) * fps, 3)
    off = []
    for k in range(nfr):
        off.append(round(sum((Vector((ft[l][k].x, ft[l][k].y)) - Vector((view_m(SN[l]).x, view_m(SN[l]).y))).length for l in LEGS) / 4, 3))
    kbest = int(np.argmin(off))
    return {'frames': nfr, 'omega': round(Om, 4), 'sweep_deg': round(math.degrees(Dth), 1), 'r_fore': round(r_fore, 3),
            'ik_err_max_m': {l: round(v, 4) for l, v in errs_max.items()}, 'world_stance_slide_mps': wsl,
            'mean_foot_offset_vs_stance_by_frame': off, 'err_rows': err_rows, 'best_frame': kbest, 'best_t': round(kbest / fps, 4), 'best_off': off[kbest]}


report = {}
for clip in CLIPS:
    if clip == 'idle':
        report[clip] = run_idle()
    elif clip.startswith('walk_turn'):
        report[clip] = run_turn(clip)
    else:
        report[clip] = run_rebase(clip)
    akb.clear_anim(arm)
    print('###CLIP### ' + clip + ' ' + json.dumps(report[clip]), flush=True)
print('###FX### ' + json.dumps(report))
