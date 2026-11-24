"""animkit name + geometry helpers shared by the driver (python3) and the Blender backend. Pure stdlib.

- left/right partners: rig.json "pairs" first, then token matching (split on _ . : -, swap l/r, L/R, fl/fr, bl/br,
  Left/Right; CamelCase prefixes LeftArm/RightArm).
- chain classes: a chain's bend axes depend on which way its rest direction points (see chain_targets).
"""
import math
import re

_TOK = [('l', 'r'), ('L', 'R'), ('fl', 'fr'), ('bl', 'br'), ('FL', 'FR'), ('BL', 'BR'), ('Left', 'Right'),
        ('left', 'right'), ('LEFT', 'RIGHT')]
SWAP = {}
for _a, _b in _TOK:
    SWAP[_a] = _b
    SWAP[_b] = _a
LEFT_TOKENS = {a for a, _ in _TOK}
_SPLIT = re.compile(r'([_.:\-\s])')
_CAMEL = re.compile(r'^(Left|Right|left|right)(?=[A-Z0-9]|$)(.*)$')


def token_mirror(name):
    """-> (mirrored name, side 'l'|'r'|None) by tokens only"""
    parts = _SPLIT.split(name)
    out, side = [], None
    for p in parts:
        if p in SWAP:
            out.append(SWAP[p])
            side = side or ('l' if p in LEFT_TOKENS else 'r')
            continue
        m = _CAMEL.match(p)
        if m:
            out.append(SWAP[m.group(1)] + m.group(2))
            side = side or ('l' if m.group(1) in LEFT_TOKENS else 'r')
            continue
        out.append(p)
    return ''.join(out), side


def mirror_map(names, pairs=None):
    """names: all bone names of the rig (or None = unknown). -> (map name->partner (self for centre bones), unpaired)
    unpaired = names that look sided by their tokens but have no partner in the rig."""
    m = {}
    for pr in pairs or []:
        if isinstance(pr, (list, tuple)) and len(pr) == 2:
            m[pr[0]] = pr[1]
            m[pr[1]] = pr[0]
    unpaired = []
    known = set(names) if names is not None else None
    for n in (names or []):
        if n in m:
            continue
        t, side = token_mirror(n)
        if side is None:
            m[n] = n
        elif known is None or t in known:
            m[n] = t
        else:
            unpaired.append(n)
    return m, unpaired


def mirror_one(n, m, names=None):
    if n in m:
        return m[n]
    if names is not None:
        raise KeyError(f'bone {n!r} is not in the rig')
    return token_mirror(n)[0]


# ------------------------------------------------------------------ chain axes
def chain_class(d):
    """d: (x, y, z) rest direction of a chain in view axes -> 'vertical' | 'fore-aft' | 'lateral'"""
    ax = [abs(float(v)) for v in d]
    k = max(range(3), key=lambda i: ax[i])
    return ('lateral', 'fore-aft', 'vertical')[k]


def chain_targets(cls):
    """-> (bend_up target, bend_side target): positive bend moves the chain tip toward these view directions.
    vertical (spine, legs, hanging hair): bend_up = lean FORWARD (-Y), bend_side = toward the character's LEFT (+X)
    fore-aft (horse neck, tails):         bend_up = UP (+Z),            bend_side = toward the character's LEFT (+X)
    lateral  (wings, arms in T-pose):     bend_up = UP (+Z),            bend_side = sweep FORWARD (-Y)"""
    up = (0.0, -1.0, 0.0) if cls == 'vertical' else (0.0, 0.0, 1.0)
    side = (0.0, -1.0, 0.0) if cls == 'lateral' else (1.0, 0.0, 0.0)
    return up, side


def mirror_flips_bend_side(cls):
    """bend_side toward +X flips sign under a left/right mirror; the forward sweep of lateral chains does not"""
    return cls != 'lateral'


# ------------------------------------------------------------------ panel angles (aim form)
def panel_angles(d, min_len=0.25, nd=1):
    """3D direction (view axes) -> (front_deg, side_deg) as drawn in each panel: 0 = straight down, clockwise positive
    (90 = pointing screen-left, -90 = screen-right, 180 = up). None when the bone points (almost) into that panel."""
    x, y, z = (float(v) for v in d)
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    x, y, z = x / n, y / n, z / n
    f = math.degrees(math.atan2(-x, -z)) if math.hypot(x, z) > min_len else None
    s = math.degrees(math.atan2(y, -z)) if math.hypot(y, z) > min_len else None
    rd = (lambda v: v) if nd is None else (lambda v: round(v, nd))
    return (None if f is None else rd(f)), (None if s is None else rd(s))


def aim_direction(front, side, rest_dir):
    """drawn panel angles (deg, either may be None) -> unit 3D direction (tuple). rest_dir supplies the missing depth when
    only one panel angle is given. Raises ValueError when the two angles contradict each other (one says up, one down)."""
    rx, ry, rz = rest_dir
    if front is None and side is None:
        raise ValueError('aim needs "front" and/or "side"')
    if front is not None and side is not None:
        A, B = math.radians(front), math.radians(side)
        f = (-math.sin(A), 0.0, -math.cos(A))
        s = (0.0, math.sin(B), -math.cos(B))
        d = (-math.sin(A) * math.cos(B), math.cos(A) * math.sin(B), -math.cos(A) * math.cos(B))
        if math.sqrt(sum(v * v for v in d)) < 1e-4:          # horizontal in both views: combine the two hints
            d = (-math.sin(A), math.sin(B), -(math.cos(A) + math.cos(B)) / 2)
        df = sum(a * b for a, b in zip(d, f)); ds = sum(a * b for a, b in zip(d, s))
        if df + ds < 0:
            d = tuple(-v for v in d); df, ds = -df, -ds
        if abs(math.cos(A)) > 0.35 and abs(math.cos(B)) > 0.35 and math.cos(A) * math.cos(B) < 0:
            raise ValueError(f'front {front} and side {side} contradict: one view says the bone points up, the other down')
    elif front is not None:
        A = math.radians(front)
        b = max(-0.95, min(0.95, ry))
        k = math.sqrt(1 - b * b)
        d = (-math.sin(A) * k, b, -math.cos(A) * k)
    else:
        B = math.radians(side)
        b = max(-0.95, min(0.95, rx))
        k = math.sqrt(1 - b * b)
        d = (b, math.sin(B) * k, -math.cos(B) * k)
    n = math.sqrt(sum(v * v for v in d))
    return tuple(v / n for v in d)
