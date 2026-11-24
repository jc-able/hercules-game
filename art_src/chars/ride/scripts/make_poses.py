"""Write the ride pose inputs (ak pose format) from a few design numbers.  python3 make_poses.py <outdir>

pegasus_fly.json   : flying pose for the ride sheet (wings half raised + spread, legs tucked, neck forward, tail back)
pegasus_wings_*.json: the wing extremes of a full beat (used only to size the sheet envelope)
hercules_ride_in.json: rider pose; "grip" (not ak) = finger curl about the finger bone's own X, converted to an ak
                       local_delta entry by build_ride.py (the resolved, pure-ak pose goes to ride.json)

Wing angles come from docs/notes/rig_pegasus.md: glide G = Euler XYZ (74.5, 62.3, 23.3) at wing_l_01 (armature space,
pegasus armature = world, so this IS ak absolute rx/ry/rz); a raise is a further rotation about the body axis Y
(negative raises the left wing; the reviewer's full up = G then Y -75, full down = G then Y +70, Z -20).
Right wing = X-mirror (S R S, S = diag(-1, 1, 1)).
"""
import json, math, os, sys
import numpy as np

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)


def Rx(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def E(x, y, z):          # Blender Euler XYZ = ak rot_xyz: Rz @ Ry @ Rx
    return Rz(z) @ Ry(y) @ Rx(x)


def to_e(R):
    ry = math.degrees(math.asin(max(-1, min(1, -R[2, 0]))))
    rx = math.degrees(math.atan2(R[2, 1], R[2, 2]))
    rz = math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(E(rx, ry, rz), R, atol=1e-6)
    return {'rx': round(rx, 2), 'ry': round(ry, 2), 'rz': round(rz, 2)}


S = np.diag([-1.0, 1.0, 1.0])
G = E(74.5, 62.3, 23.3)


def wing_pair(R_l, extra=None):
    d = {'wing_l_01': to_e(R_l), 'wing_r_01': to_e(S @ R_l @ S)}
    for k, v in (extra or {}).items():
        d[k] = v
    return d


LD = lambda rx: {'rx': rx, 'space': 'local_delta'}

# ---- pegasus flight pose
RAISE = float(os.environ.get('RIDE_RAISE', -15.0))   # half raised: glide wing lifted about the body axis (full up = -75)
PITCH = float(os.environ.get('RIDE_PITCH', 18.0))    # trailing edge up about X (through the wing root): lifts the
                                                     # inner secondaries off the flank so the rider's thighs pass under them
wings = wing_pair(Rx(PITCH) @ Ry(RAISE) @ G)
# no feather fan: ak local_delta turns about WORLD axes, which is not a fan once the wing is raised
legs = {}
# fore legs folded tight (pegasus rig agent's fly_ridden), hind legs folded up under the belly (reviewer's R1 tuck, softened)
for s, a in (('fl', (-55, -30, 135, 30)), ('fr', (-50, -28, 128, 30)), ('bl', (-50, 90, -70, -20)), ('br', (-45, 85, -65, -20))):
    for bn, v in zip((f'leg_{s}_01', f'leg_{s}_02', f'leg_{s}_03', f'hoof_{s}'), a):
        legs[bn] = LD(v)
neck = {'neck_01': LD(24), 'neck_02': LD(12), 'neck_03': LD(6), 'head': LD(-14)}       # stretched forward (limits 25 / 15)
tail = {'tail_01': LD(35), 'tail_02': LD(12), 'tail_03': LD(10), 'tail_04': LD(6), 'tail_05': LD(5)}  # streaming back
peg = {'space': 'absolute', 'bones': {**wings, **legs, **neck, **tail},
       'notes': f'ride sheet flight pose: wings half raised (glide + {-RAISE:g} deg up about the body axis, trailing edge '
                f'pitched up {PITCH:g} deg) and spread, '
                'legs tucked, neck stretched forward, tail streaming back; body level (root untouched)'}
json.dump(peg, open(os.path.join(out, 'pegasus_fly.json'), 'w'), indent=1)

# ---- wing extremes (envelope only): only the wing bones change, the rest of pegasus_fly is kept
ext = {'glide': wing_pair(G), 'full_up': wing_pair(Ry(-75) @ G), 'full_down': wing_pair(Rz(-20) @ Ry(70) @ G),
       'builder_up': wing_pair(E(55.7, 10.5, 17.5)), 'builder_down': wing_pair(E(-147.1, 57.9, 150.9))}
json.dump(ext, open(os.path.join(out, 'pegasus_wing_extremes.json'), 'w'), indent=1)

# ---- hercules rider (absolute; limbs in aim form = bone direction as drawn in each panel, 0 = down, clockwise +)
HP = os.path.join(out, 'hercules_ride_in.json')     # hand-tuned after the first build: written only if missing
if not os.path.exists(HP):
    H = {'space': 'absolute',
         'bones': {
             'spine_01': {'rx': 6}, 'spine_02': {'rx': 12}, 'spine_03': {'rx': 16}, 'neck': {'rx': 4}, 'head': {'rx': -6},
             'thigh_l': {'front': -40, 'side': -55}, 'shin_l': {'front': -2, 'side': 18}, 'foot_l': {'front': -10, 'side': -55},
             'thigh_r': {'front': 40, 'side': -55}, 'shin_r': {'front': 2, 'side': 18}, 'foot_r': {'front': 10, 'side': -55},
             'upper_arm_l': {'front': -12, 'side': -45}, 'forearm_l': {'front': 10, 'side': -80}, 'hand_l': {'front': 10, 'side': -100},
             'upper_arm_r': {'front': 25, 'side': 25}, 'forearm_r': {'front': 35, 'side': 35}, 'hand_r': {'front': 35, 'side': 40}},
         'grip': {'fingers_l': 75, 'fingers_r': 75}}
    json.dump(H, open(HP, 'w'), indent=1)
print('wrote', out)
