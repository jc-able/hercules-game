"""Writes the hercules `ride` loop keys: base = art_src/chars/ride/poses/hercules_ride.json (the seated pose of ride.json),
plus small per-beat offsets (legs grip = heels drawn back along the barrel, never inward:
the shins already touch the flanks). Clip t=0 = wings at the TOP of the stroke (Pegasus body lowest). Run from the repo root."""
import json, copy, os
C = 'art_src/chars/ride/clips/ride'
base = json.load(open('art_src/chars/ride/poses/hercules_ride.json'))
L = 1.5
# per key: (t, {bone: {key: delta}})   delta is ADDED to the base value (absolute / aim form keys)
D = [
 (0.0,   'k0_top',  {'spine_01': {'rx': 1.0}, 'spine_02': {'rx': 1.5}, 'spine_03': {'rx': 1.5}, 'neck': {'rx': 1.0}, 'head': {'rx': -1.0},
                     'upper_arm_r': {'side': 0.0}, 'forearm_r': {'side': 2.0}}),
 (0.375, 'k1_down', {'spine_01': {'rx': 0.5}, 'spine_02': {'rx': 0.5}, 'spine_03': {'rx': 0.5},
                     'shin_l': {'side': 3.0}, 'shin_r': {'side': 3.0}, 'foot_l': {'side': 3.0}, 'foot_r': {'side': 3.0},
                     'upper_arm_r': {'side': 1.5}, 'forearm_r': {'side': 3.0}}),
 (0.75,  'k2_bottom', {'spine_01': {'rx': -1.0}, 'spine_02': {'rx': -1.5}, 'spine_03': {'rx': -1.5}, 'neck': {'rx': -1.0}, 'head': {'rx': 1.0},
                     'shin_l': {'side': 1.5}, 'shin_r': {'side': 1.5}, 'foot_l': {'side': 1.5}, 'foot_r': {'side': 1.5},
                     'forearm_r': {'side': -2.0}}),
 (1.125, 'k3_up',   {'spine_01': {'rx': -0.5}, 'spine_02': {'rx': -0.5}, 'spine_03': {'rx': -0.5},
                     'upper_arm_r': {'side': -1.5}, 'forearm_r': {'side': -3.0}}),
]
keys = []
for t, name, deltas in D:
    p = copy.deepcopy(base)
    for bn, dd in deltas.items():
        for k, v in dd.items():
            p['bones'][bn][k] = round(p['bones'][bn][k] + v, 2)
    p['note'] = f'ride loop key {name} at clip t={t}s (beat {L}s; t=0 = wings at the top of the stroke): base seated pose + {deltas}'
    fn = f'{C}/poses_ride/{name}.json'
    json.dump(p, open(fn, 'w'), indent=1)
    keys.append({'t': t, 'pose_file': f'poses_ride/{name}.json'})
json.dump({'fps': 24, 'loop': True, 'length': L, 'events': {}, 'keys': keys,
           'note': 'hercules ride loop, one wing beat (video period measured 1.48 s; t=0 = wing top). See docs/notes/ride_anim.md'},
          open(f'{C}/keys_ride.json', 'w'), indent=1)
print('ok', [k['pose_file'] for k in keys])
