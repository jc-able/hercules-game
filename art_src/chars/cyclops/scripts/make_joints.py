"""Write ../joints.json (bone list with head/tail/parent/deform) from joint positions measured on the mesh slices.
Left side (+X, the character's left) is given; the right side is mirrored (x -> -x)."""
import json, os
J = {  # measured with numpy slices of the 8 m mesh (see notes in rig.json)
 'pelvis': (0, 0.30, 2.95), 'spine1': (0, 0.27, 3.70), 'spine2': (0, 0.20, 4.45), 'spine3': (0, 0.26, 5.25),
 'neck': (0, 0.37, 6.30), 'head': (0, 0.36, 6.95), 'top': (0, 0.30, 8.0),
 'clav': (0.32, 0.40, 6.36), 'shoulder_u': (1.42, 0.45, 6.40), 'elbow_u': (2.22, 0.42, 6.36),
 'wrist_u': (3.02, 0.36, 6.38), 'hand_u_tip': (4.02, 0.42, 6.42),
 'shoulder_d': (1.15, 0.36, 5.35), 'elbow_d': (1.85, 0.36, 4.80), 'wrist_d': (2.48, 0.33, 4.22),
 'hand_d_tip': (3.22, 0.42, 3.42),
 'hip': (0.72, 0.30, 2.95),
 # legs re-measured 11-22 (review): knee = back hollow / width minimum z 2.2-2.3 (x centre 0.77-0.82, y centre ~0.3);
 # ankle = narrowing z 0.8-1.1 (width 0.6-0.7, y centre 0.57). The old knee (z 1.12) was really the ankle.
 'knee': (0.80, 0.33, 2.22), 'ankle': (0.97, 0.57, 0.95),
 'ball': (1.15, -0.45, 0.14), 'toe_tip': (1.20, -1.05, 0.12),
}
B = []
def add(name, parent, h, t, deform=True):
    B.append({'name': name, 'parent': parent, 'head': list(h), 'tail': list(t), 'deform': deform})
add('root', None, (0, 0, 0), (0, 0, 1.0), False)
add('hips', 'root', J['pelvis'], J['spine1'])
add('spine_01', 'hips', J['spine1'], J['spine2'])
add('spine_02', 'spine_01', J['spine2'], J['spine3'])
add('spine_03', 'spine_02', J['spine3'], J['neck'])
add('neck', 'spine_03', J['neck'], J['head'])
add('head', 'neck', J['head'], J['top'])
def side(s, k):
    m = lambda p: (p[0] * k, p[1], p[2])
    add(f'shoulder_u_{s}', 'spine_03', m(J['clav']), m(J['shoulder_u']))
    add(f'upper_arm_u_{s}', f'shoulder_u_{s}', m(J['shoulder_u']), m(J['elbow_u']))
    add(f'forearm_u_{s}', f'upper_arm_u_{s}', m(J['elbow_u']), m(J['wrist_u']))
    add(f'hand_u_{s}', f'forearm_u_{s}', m(J['wrist_u']), m(J['hand_u_tip']))
    add(f'upper_arm_d_{s}', 'spine_03', m(J['shoulder_d']), m(J['elbow_d']))
    add(f'forearm_d_{s}', f'upper_arm_d_{s}', m(J['elbow_d']), m(J['wrist_d']))
    add(f'hand_d_{s}', f'forearm_d_{s}', m(J['wrist_d']), m(J['hand_d_tip']))
    add(f'thigh_{s}', 'hips', m(J['hip']), m(J['knee']))
    add(f'shin_{s}', f'thigh_{s}', m(J['knee']), m(J['ankle']))
    add(f'foot_{s}', f'shin_{s}', m(J['ankle']), m(J['ball']))
    add(f'toe_{s}', f'foot_{s}', m(J['ball']), m(J['toe_tip']))
side('l', 1); side('r', -1)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'joints.json')
json.dump({'joints': J, 'bones': B}, open(out, 'w'), indent=1)
print(len(B), 'bones ->', os.path.normpath(out))
