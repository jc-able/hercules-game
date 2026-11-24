"""Skirt bone drivers for hercules (pure math; runs inside Blender, needs only mathutils).

The skirt cloth has its own bones (skirt_f, skirt_b, skirt_l, skirt_r; children of hips, belt -> hem). They are not
keyed by hand: every pose sets them from the thighs. Angles are measured in the hips frame (so they work while the
whole body rolls or leans):

  pitch(thigh)  = forward swing of the thigh in the hips' sagittal plane, degrees, relative to rest (forward > 0)
  abd(thigh)    = sideways swing away from the body centre, degrees, relative to rest (outward > 0)

  m = (pitch_l + pitch_r) / 2   (MEAN of the thighs: in a wide stagger the centre panels hang straight)
  skirt_f  pitch = softcap(K * m, CAP)  forward, K_IN * m backward;  at least K * min(pitch_l, pitch_r) when BOTH
           thighs are forward beyond SEAT (sitting / riding: the panel must clear both thighs), eased in by smoothstep
  skirt_b  pitch = softcap(K * m, CAP)  backward, K_IN * m forward;  at most K * max(pitch_l, pitch_r) when BOTH
           thighs are back
  skirt_l  abd   = K * spread(abd_l)                (K_IN when negative; spread() halves... see SPREAD_KNEE)
  skirt_r  abd   = K * spread(abd_r)
  softcap(v, C) = C * tanh(v / C);  spread(a) = a up to SPREAD_KNEE deg, then SPREAD_SLOPE per degree beyond
  (review fix 2026-11-22: the old max()/min() pitch and the full abduction split the hem at the centre front and
  showed a dark crotch V in idle, run, strafe and block_idle)
  skirt_l / skirt_r also pitch = K_SIDE * pitch of their own thigh when it is forward, K_SIDE_BACK when it is back
  (the side panels lie over the thighs: thigh centre at about 75 deg from the front around the hip axis)
  every result clamped to +-MAX_DEG; the skirt bone turns about its own head (hip centre at belt height).

Use:  posed = skirt_matrices(rest, posed)   with rest/posed = {bone: 4x4 armature-space matrix} (Blender
bone.matrix_local / pose_bone.matrix, animkit Rig.rest / Rig.solve()). Returns {skirt bone: posed 4x4}.
"""
import math
from mathutils import Matrix, Vector

K = 0.85
K_IN = 0.15
K_SIDE = 0.5         # side panel pitch when its thigh swings forward (it lies over the thigh)
K_SIDE_BACK = 0.35   # ... and when it swings back (less shear against the front panel)
MAX_DEG = 95.0
CAP = 24.0           # soft cap (deg) of the centre panels' pitch from the thigh mean
SEAT = (30.0, 60.0)  # both thighs forward beyond SEAT[0] deg: the front panel starts to clear them (full at SEAT[1])
SPREAD_KNEE = 20.0   # thigh abduction (deg) up to which the side panels follow fully
SPREAD_SLOPE = 0.65  # ... and how much of each degree beyond it (lower lets wide-stance thighs through the side panels)
SKIRT_BONES = ('skirt_f', 'skirt_b', 'skirt_l', 'skirt_r')
SPEC = {'K': K, 'K_IN': K_IN, 'K_SIDE': K_SIDE, 'K_SIDE_BACK': K_SIDE_BACK, 'MAX_DEG': MAX_DEG, 'CAP': CAP,
        'SPREAD_KNEE': SPREAD_KNEE, 'SPREAD_SLOPE': SPREAD_SLOPE,
        'SEAT': SEAT, 'skirt_f': 'm = mean(pitch_l, pitch_r); pitch = CAP*tanh(K*m/CAP) if m > 0 else K_IN*m; >= K*lo*smoothstep(SEAT) with lo = min(pitch_l, pitch_r) > 0',
        'skirt_b': 'pitch = CAP*tanh(K*m/CAP) if m < 0 else K_IN*m; <= K*hi*smoothstep(SEAT) with hi = max(pitch_l, pitch_r) < 0',
        'skirt_l': 'abd = K * spread(abd(thigh_l)), K_IN if < 0; pitch = K_SIDE * pitch(thigh_l) forward, K_SIDE_BACK backward',
        'skirt_r': 'abd = K * spread(abd(thigh_r)), K_IN if < 0; pitch = K_SIDE * pitch(thigh_r) forward, K_SIDE_BACK backward',
        'frame': 'angles in the hips frame relative to rest; forward pitch = rotation about -X (Blender, char faces -Y); '
                 'outward abd = tail moves away from x=0; each skirt bone rotates about its own head'}


def _angles(v, sg):
    pitch = math.degrees(math.atan2(-v.y, -v.z))
    abd = math.degrees(math.atan2(sg * v.x, math.hypot(v.y, v.z)))
    return pitch, abd


def thigh_angles(rest, posed):
    Hr = rest['hips'].to_3x3().normalized(); Hp = posed['hips'].to_3x3().normalized()
    toR = Hr @ Hp.inverted()
    out = {}
    for s, sg in (('l', 1), ('r', -1)):
        n = f'thigh_{s}'
        d0 = rest[n].to_3x3().col[1].normalized()
        d = (toR @ posed[n].to_3x3().col[1]).normalized()
        p0, a0 = _angles(d0, sg); p, a = _angles(d, sg)
        out[s] = (p - p0, a - a0)
    return out


def _k(v, outward_positive=True):
    k = K if (v > 0) == outward_positive else K_IN
    return max(-MAX_DEG, min(MAX_DEG, k * v))


def skirt_angles(rest, posed):
    ta = thigh_angles(rest, posed)
    (pl, al), (pr, ar) = ta['l'], ta['r']
    clamp = lambda v: max(-MAX_DEG, min(MAX_DEG, v))
    m = 0.5 * (pl + pr)
    soft = CAP * math.tanh(K * m / CAP)
    f = soft if m > 0 else K_IN * m
    lo, hi = min(pl, pr), max(pl, pr)
    sstep = lambda x: 0.0 if x <= 0 else (1.0 if x >= 1 else x * x * (3 - 2 * x))
    if lo > 0:                                   # seated / riding: clear both thighs
        f = max(f, K * lo * sstep((lo - SEAT[0]) / (SEAT[1] - SEAT[0])))
    b = soft if m < 0 else K_IN * m
    if hi < 0:
        b = min(b, K * hi * sstep((-hi - SEAT[0]) / (SEAT[1] - SEAT[0])))
    spread = lambda a: a if abs(a) <= SPREAD_KNEE else math.copysign(SPREAD_KNEE + SPREAD_SLOPE * (abs(a) - SPREAD_KNEE), a)
    sidep = lambda v: clamp((K_SIDE if v > 0 else K_SIDE_BACK) * v)
    return {'skirt_f': ('pitch', clamp(f)), 'skirt_b': ('pitch', clamp(b)),
            'skirt_l': ('abd', _k(spread(al), True), sidep(pl)), 'skirt_r': ('abd', _k(spread(ar), True), sidep(pr)),
            '_thighs': ta}


def skirt_matrices(rest, posed):
    if not all(n in rest for n in SKIRT_BONES):
        return {}
    ang = skirt_angles(rest, posed)
    Hr = rest['hips']; Hp = posed['hips']
    G = Hp @ Hr.inverted()
    out = {}
    for n in SKIRT_BONES:
        kind, a = ang[n][0], ang[n][1]
        if kind == 'pitch':
            R = Matrix.Rotation(math.radians(-a), 4, 'X')            # forward = about -X
        else:
            sg = 1 if n == 'skirt_l' else -1
            R = (Matrix.Rotation(math.radians(-ang[n][2]), 4, 'X') @
                 Matrix.Rotation(math.radians(-a * sg), 4, 'Y'))     # outward: left +X needs -Y rotation; then pitch
        h = rest[n].translation
        out[n] = G @ Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ rest[n]
    return out


def apply_to_pose(arm):
    """Blender helper: set the skirt pose bones of armature object `arm` from its current thigh pose."""
    import bpy
    rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    posed = {pb.name: pb.matrix.copy() for pb in arm.pose.bones}
    M = skirt_matrices(rest, posed)
    for n, m in M.items():
        arm.pose.bones[n].matrix = m
    bpy.context.view_layer.update()
    return M
