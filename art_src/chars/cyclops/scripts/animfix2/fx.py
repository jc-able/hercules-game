"""Cyclops fixer helpers: resolve poses in headless Blender (rb_resolve.py, read-only blend), edit them as view-axes
rotation matrices, write absolute rx/ry/rz pose files."""
import json, os, subprocess, math, copy, numpy as np, hashlib
from rbcore import Rx, Ry, Rz, rot_xyz, euler_xyz, ang, slerp, BONES
REPO = os.path.expanduser('~/HerculesGame')
HERE = REPO + '/work/animfix_cyclops2'
BLEND = REPO + '/art_src/chars/cyclops/cyclops.blend'
CL = REPO + '/art_src/chars/cyclops/clips'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
CHILD = {}


def resolve(items, tag='job'):
    """items: list of dicts {id, pose_file|pose|from_action+t}. returns {id: {abs, local, pos, pose, parent}} (numpy)"""
    its = []
    os.makedirs(HERE + '/tmp', exist_ok=True)
    for i, it in enumerate(items):
        it = dict(it)
        if 'pose' in it:
            p = HERE + f'/tmp/{tag}_{i}.json'; json.dump(it.pop('pose'), open(p, 'w')); it['pose_file'] = p
        its.append(it)
    job = HERE + f'/tmp/{tag}.json'; out = HERE + f'/tmp/{tag}_out.json'
    json.dump({'blend': BLEND, 'items': its}, open(job, 'w'))
    cmd = [BL, '-b', '--factory-startup', '--python', HERE + '/rb_resolve.py', '--', job, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if '###RB### ok' not in r.stdout:
        raise RuntimeError(r.stdout[-3000:] + r.stderr[-3000:])
    res = json.load(open(out))
    for k, v in res.items():
        v['abs'] = {b: np.array(m) for b, m in v['abs'].items()}
        v['local'] = {b: np.array(m) for b, m in v['local'].items()}
        if not CHILD:
            for b, p in v['parent'].items():
                CHILD.setdefault(p, []).append(b)
    return res


def desc(b):
    out = [b]
    for c in CHILD.get(b, []): out += desc(c)
    return out


def write_pose(path, absm, root=None, note=None, keep=None, extra=None):
    """absm: {bone: 3x3} -> absolute pose json (every bone listed)."""
    p = {'space': 'absolute'}
    if note: p['_note'] = note
    p['root'] = root or {'loc': [0, 0, 0], 'ground': 'lowest'}
    p['bones'] = {}
    for b in BONES:
        if b in absm:
            p['bones'][b] = dict(zip(('rx', 'ry', 'rz'), euler_xyz(absm[b])))
    if extra: p['bones'].update(extra)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(p, open(path, 'w'), indent=1)
    return p


def rot_chain(absm, bone, R, chain=True):
    """pre-multiply a world (view-axes) rotation on bone (and its descendants)."""
    out = dict(absm)
    for b in (desc(bone) if chain else [bone]):
        if b in out: out[b] = R @ out[b]
    return out


def rot_about_bone(absm, bone, axis_angle_deg, chain=True):
    return rot_chain(absm, bone, rot_xyz(*axis_angle_deg), chain)


def blend(A, B, u):
    """slerp every bone of two abs dicts"""
    return {b: slerp(A[b], B[b], u) for b in A if b in B}


def angs(absm, b, ref):
    return round(ang(absm[b], ref[b]), 1)


def bake(clip, keys, out_action, keep_root=False):
    cmd = [REPO + '/tools/ak', 'bake', BLEND, '--clip', clip, '--keys', keys, '--out-action', out_action]
    if keep_root: cmd.append('--keep-root-motion')
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    last = [l for l in r.stdout.splitlines() if l.startswith('###AK###')]
    js = json.loads(last[-1][9:]) if last else {'ok': False, 'error': r.stderr[-2000:]}
    if not js.get('ok'): raise RuntimeError(json.dumps(js)[:3000])
    return js


def rotmin(a, b):
    a = np.asarray(a, float) / np.linalg.norm(a); b = np.asarray(b, float) / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b)); s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)


def leg_ik(absm, pos, side, target, pole=None):
    """2-bone IK on thigh/shin (absolute space: the foot keeps its world orientation). pos: resolved bone heads."""
    H = np.array(pos['thigh_' + side]); K = np.array(pos['shin_' + side]); A = np.array(pos['foot_' + side]); T = np.array(target, float)
    l1 = np.linalg.norm(K - H); l2 = np.linalg.norm(A - K)
    d = T - H; D = np.linalg.norm(d); u = d / D
    D = min(max(D, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    pk = (K - H) if pole is None else np.asarray(pole, float)
    pk = pk - np.dot(pk, u) * u; pk /= np.linalg.norm(pk)
    a = (l1 * l1 - l2 * l2 + D * D) / (2 * D); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    K2 = H + a * u + h * pk; T2 = H + D * u
    out = dict(absm)
    R1 = rotmin(K - H, K2 - H); out['thigh_' + side] = R1 @ absm['thigh_' + side]
    R2 = rotmin(A - K, T2 - K2); out['shin_' + side] = R2 @ absm['shin_' + side]
    return out


def pose_dict(absm, root, extra_bones=None, note=None):
    p = {'space': 'absolute'}
    if note: p['_note'] = note
    p['root'] = root
    p['bones'] = {b: dict(zip(('rx', 'ry', 'rz'), euler_xyz(absm[b]))) for b in BONES if b in absm}
    if extra_bones: p['bones'].update(extra_bones)
    return p


SRC = json.load(open(REPO + '/art_src/chars/cyclops/clip_sources.json'))['clips']


def merge_export(glb=HERE + '/iter.glb', clips_json=HERE + '/iter_clips.json'):
    r = subprocess.run([REPO + '/tools/ak', 'merge', BLEND] + [REPO + '/' + SRC[c] for c in SRC], capture_output=True, text=True, cwd=REPO)
    m = json.loads([l for l in r.stdout.splitlines() if l.startswith('###AK###')][-1][9:])
    if not m.get('ok'): raise RuntimeError(str(m))
    r = subprocess.run([REPO + '/tools/ak', 'export', BLEND, '--out', glb, '--clips-json', clips_json], capture_output=True, text=True, cwd=REPO)
    e = json.loads([l for l in r.stdout.splitlines() if l.startswith('###AK###')][-1][9:])
    if not e.get('ok'): raise RuntimeError(str(e))
    return m, e


def arm_ik(absm, pos, upper, fore, hand, target, pole=None):
    """2-bone IK upper/fore so that the hand head lands on target (hand keeps its absolute orientation)."""
    H = np.array(pos[upper]); K = np.array(pos[fore]); A = np.array(pos[hand]); T = np.array(target, float)
    l1 = np.linalg.norm(K - H); l2 = np.linalg.norm(A - K)
    d = T - H; D = np.linalg.norm(d); u = d / D
    D = min(max(D, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    pk = (K - H) if pole is None else np.asarray(pole, float)
    pk = pk - np.dot(pk, u) * u; pk /= np.linalg.norm(pk)
    a = (l1 * l1 - l2 * l2 + D * D) / (2 * D); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    K2 = H + a * u + h * pk; T2 = H + D * u
    out = dict(absm)
    out[upper] = rotmin(K - H, K2 - H) @ absm[upper]
    out[fore] = rotmin(A - K, T2 - K2) @ absm[fore]
    return out
