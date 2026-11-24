"""fly v2 (animation fixer, 2026-11-22, after docs/notes/anim_review_pegasus.md findings 2-3).

  python3 art_src/chars/pegasus/clips/fly/make_fly_v2.py        (from the repo root)

Reads the matched pose files poses_fly/k*.json (the animator's video match, unchanged) and writes
poses_fly/v2_*.json + keys_fly.json:
- legs + neck/head: graded in-betweens between the tucked pose (k0) and the extended pose (k3) instead of holds
  (fraction LEG_F per key time), so nothing steps between held poses.
- root: no `ground` (a flying horse has no floor) and no pitch (root.rot 0, same as glide, so a rider glued by
  position does not rock 8 deg in the fly<->glide crossfade). root.loc z keyed by hand: 0 at the wing top (lowest),
  highest at the end of the downstroke (ride video: 8.3 cm peak to peak, lowest at the wing top).
- wings: the matched wing poses; mid_down moved 0.333 -> 0.292 (spreads the downstroke), a settle at 0.458
  (wing_*_01 ry 5 deg further down, wing_*_02 5 deg more curl), down_end moved 0.708 -> 0.750 and lowered (the video
  holds the wings fully down until 1.750 s and snaps up from there) instead of the old k4 that already lifted.
- tail: the animator's authored wave, re-timed with its keys."""
import json, os, copy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'poses_fly')
ld = lambda n: json.load(open(os.path.join(P, n)))
k0, k1, k2, k2b, k3, k4, k5 = (ld(n) for n in ('k0_up.json', 'k1_up_spread.json', 'k2_mid_down.json',
                                             'k2b_mid_down_late.json', 'k3_down.json', 'k4_down_end.json',
                                             'k5_mid_up.json'))
LEGS = []
for s in ('fl', 'fr', 'bl', 'br'):
    LEGS += [f'leg_{s}_01', f'leg_{s}_02', f'leg_{s}_03', f'hoof_{s}']
HEAD = ['neck_01', 'neck_02', 'head']
WINGS = ['wing_l_01', 'wing_r_01', 'wing_l_02', 'wing_r_02']

# root.loc z (m): 0 at the wing top, +0.04 at 0.33, +0.08 at the end of the downstroke, +0.03 at 0.9
BOB_T, BOB_Z = [0.0, 0.33, 0.625, 0.9, 1.0417], [0.0, 0.04, 0.08, 0.03, 0.0]


def lerp_bone(a, b, f):
    out = {}
    for ax in set(a) | set(b):
        if ax == 'space':
            out[ax] = a.get(ax, b.get(ax))
            continue
        out[ax] = round(a.get(ax, 0.0) + f * (b.get(ax, 0.0) - a.get(ax, 0.0)), 2)
    return out


def wing_mod(src, ry_l=None, w2rz_l=None):
    w = {b: copy.deepcopy(src['bones'][b]) for b in WINGS}
    if ry_l is not None:
        w['wing_l_01']['ry'] = ry_l
        w['wing_r_01']['ry'] = -ry_l
    if w2rz_l is not None:
        w['wing_l_02']['rz'] = w2rz_l
        w['wing_r_02']['rz'] = -w2rz_l
    return w


def mix_chain(a, b, f):
    ca, cb = a['chain'], b['chain']
    return {'name': ca['name'], 'bend_up': [round(x + f * (y - x), 2) for x, y in zip(ca['bend_up'], cb['bend_up'])],
            'bend_side': [round(x + f * (y - x), 2) for x, y in zip(ca['bend_side'], cb['bend_side'])]}


# the matched poses were pitched 8 deg nose-up with root.rot; v2 keeps the body level (like glide) and gives the
# legs, neck and head that 8 deg instead (absolute rx, -8 = forward/nose-up), so they hang as they did in the world.
PITCH_COMP = -8.0
FRONT_CAP = 0.75        # forelegs only go 75% of the way to k3 (the video keeps them half tucked in the downstroke)
ry3 = k3['bones']['wing_l_01']['ry']           # 61.9 (smaller ry = wing hangs lower, closer to the body)
rz3 = k3['bones']['wing_l_02']['rz']           # -10
# name, t, leg fraction (0 tucked k0 -> 1 extended k3), wings, tail
KEYS = [
    ('v2_k0_top', 0.0, 0.00, wing_mod(k0), k0['chain']),
    ('v2_k1_up_spread', 0.25, 0.30, wing_mod(k1), k1['chain']),
    ('v2_k2_mid_down', 0.292, 0.40, wing_mod(k2), k2['chain']),
    ('v2_k2b_mid_down_late', 0.375, 0.65, wing_mod(k2b), k2b['chain']),
    ('v2_k3_down', 0.417, 0.85, wing_mod(k3), k3['chain']),
    ('v2_k3s_settle', 0.458, 0.92, wing_mod(k3, ry3 - 5.0, rz3 - 5.0), k3['chain']),
    ('v2_k3h_hang', 0.625, 1.00, wing_mod(k3, ry3 - 2.0, rz3 - 3.0), mix_chain(k3, k4, 0.5)),
    ('v2_k4_down_end', 0.75, 0.68, wing_mod(k3, ry3 + 2.0, rz3), k4['chain']),
    ('v2_k5_mid_up', 0.875, 0.40, wing_mod(k5), k5['chain']),
]

keys = []
for name, t, f, wings, chain in KEYS:
    bones = {}
    for b in LEGS + HEAD:
        fb = f * FRONT_CAP if b[-2:] in ('fl', 'fr') or b[-5:-3] in ('fl', 'fr') else f
        bones[b] = lerp_bone(k0['bones'][b], k3['bones'][b], fb)
        bones[b]['rx'] = round(bones[b].get('rx', 0.0) + PITCH_COMP, 2)
    bones['hips'] = {'rx': 0.0}
    bones.update(wings)
    z = round(float(np.interp(t, BOB_T, BOB_Z)), 4)
    pose = {'space': 'absolute', 'root': {'loc': [0.0, 0.0, z], 'rot': [0.0, 0.0, 0.0]}, 'bones': bones,
            'view_offset': [0, 0.02, 0], 'chain': chain, 'leg_fraction': f}
    fn = os.path.join(P, name + '.json')
    json.dump(pose, open(fn, 'w'), indent=1)
    keys.append({'t': t, 'pose_file': 'poses_fly/' + name + '.json'})

kj = {'fps': 24, 'loop': True, 'length': 1.0417,
      'video_window': '1.000-2.042 s (one wing beat, ak cycle period 1.0417 s, IoU 0.986)',
      'version': 'v2 (fixer 2026-11-22): graded legs, hand-keyed bob, no ground, no body pitch (legs/neck carry it), settle + later down_end; '
                 'generated by make_fly_v2.py from the matched k*.json',
      'events': {}, 'keys': keys}
json.dump(kj, open(os.path.join(HERE, 'keys_fly.json'), 'w'), indent=1)
print(json.dumps({'keys': [(k['t'], k['pose_file']) for k in keys]}))
