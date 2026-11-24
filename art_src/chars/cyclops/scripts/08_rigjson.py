"""Step 8 (python3): verify export/cyclops.glb and write rig.json (+ socket offsets in the glTF joint frame).
python3 08_rigjson.py <chars/cyclops dir>

Socket offsets are given in the frame of the glTF joint node (= Godot Skeleton3D bone global rest, Y up, metres):
  loc: offset of the attachment origin in the joint frame; rot_deg: Euler degrees in Godot's default YXZ order
  (assign to Node3D.rotation_degrees under a BoneAttachment3D); quat_xyzw: the same rotation as a quaternion.
"""
import sys, os, json, math
import numpy as np
import pygltflib

D = sys.argv[1]
J = json.load(open(os.path.join(D, 'joints.json')))
g = pygltflib.GLTF2().load(os.path.join(D, 'export', 'cyclops.glb'))

def local(n):
    if n.matrix and n.matrix != [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]:
        return np.array(n.matrix, float).reshape(4, 4).T
    T = np.eye(4); T[:3, 3] = n.translation or [0, 0, 0]
    x, y, z, w = n.rotation or [0, 0, 0, 1]
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    S = np.diag(list(n.scale or [1, 1, 1]) + [1])
    M = np.eye(4); M[:3, :3] = R
    return T @ M @ S

parent = {}
for i, n in enumerate(g.nodes):
    for c in n.children or []:
        parent[c] = i
def glob(i):
    M = local(g.nodes[i])
    while i in parent:
        i = parent[i]; M = local(g.nodes[i]) @ M
    return M

assert len(g.skins) == 1, len(g.skins)
sk = g.skins[0]
jn = {g.nodes[j].name: j for j in sk.joints}
mesh_tris = 0
for m in g.meshes:
    for p in m.primitives:
        acc = g.accessors[p.indices]; mesh_tris += acc.count // 3
C = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)   # Blender Z-up -> glTF Y-up
Ci = np.linalg.inv(C)

# check joint heads against the Blender rest (converted)
errs = []
for b in J['bones']:
    G = glob(jn[b['name']])
    h = C[:3, :3] @ np.array(b['head'])
    errs.append(float(np.linalg.norm(G[:3, 3] - h)))

def rot_to_yxz_deg(R):
    # R = Ry(a) Rx(b) Rz(c)  (Godot EULER_ORDER_YXZ)
    b = math.asin(max(-1, min(1, -R[1, 2])))
    if abs(math.cos(b)) > 1e-6:
        a = math.atan2(R[0, 2], R[2, 2]); c = math.atan2(R[1, 0], R[1, 1])
    else:
        a = math.atan2(-R[2, 0], R[0, 0]); c = 0.0
    return [math.degrees(b), math.degrees(a), math.degrees(c)]   # (x, y, z) components for rotation_degrees

def quat(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1) * 2; w = s / 4; x = (R[2, 1] - R[1, 2]) / s; y = (R[0, 2] - R[2, 0]) / s; z = (R[1, 0] - R[0, 1]) / s
    else:
        i = int(np.argmax(np.diag(R)))
        if i == 0:
            s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; w = (R[2, 1] - R[1, 2]) / s; x = s / 4; y = (R[0, 1] + R[1, 0]) / s; z = (R[0, 2] + R[2, 0]) / s
        elif i == 1:
            s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; w = (R[0, 2] - R[2, 0]) / s; x = (R[0, 1] + R[1, 0]) / s; y = s / 4; z = (R[1, 2] + R[2, 1]) / s
        else:
            s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; w = (R[1, 0] - R[0, 1]) / s; x = (R[0, 2] + R[2, 0]) / s; y = (R[1, 2] + R[2, 1]) / s; z = s / 4
    return [x, y, z, w]

def offset(bone, W_blender):
    Wg = C @ W_blender @ Ci
    O = np.linalg.inv(glob(jn[bone])) @ Wg
    R = O[:3, :3]
    return {'bone': bone, 'loc': [round(float(v), 4) for v in O[:3, 3]],
            'rot_deg': [round(v, 3) for v in rot_to_yxz_deg(R)], 'quat_xyzw': [round(v, 5) for v in quat(R)]}

cw = json.load(open(os.path.join(D, 'export', 'club_world.json')))
Wclub = np.array(cw['club_world'], float)
def tr(p):
    M = np.eye(4); M[:3, 3] = p; return M
grip_l = np.array(cw['grip']) * np.array([-1, 1, 1])
sock_off = {
    'hand_ur': offset('hand_u_r', Wclub),
    'hand_ul': offset('hand_u_l', tr(grip_l)),
    'forearm_ur': offset('forearm_u_r', tr([-2.62, 0.39, 6.37])),
    'head': offset('head', tr([0.0, -0.15, 7.68])),
    # review fix 11-22: a real second grip ON the club (0.7 m above the main grip along the club axis), carried by
    # hand_u_r like the club itself, for two-hand IK of the left upper hand
    'club_grip2': offset('hand_u_r', Wclub @ tr([0.0, 0.0, 0.7])),
}
sock_off['hand_ur']['note'] = 'club.glb origin (grip) and orientation: club head along +Y when the socket has no rotation'
sock_off['hand_ul']['note'] = ('left upper hand: palm centre (mirror of the right grip) in the hand_u_l frame, world-up '
                               'orientation. NOT on the club: for the left hand on the club (two-hand slam) use club_grip2 '
                               'as the IK target')
sock_off['club_grip2']['note'] = ('second grip on the club handle, 0.7 m above the main grip along the club axis, in the '
                                  'hand_u_r frame (moves with the club); same orientation as the club (+Y = club axis)')
sock_off['forearm_ur']['note'] = 'weak point `forearm`: middle of the right upper forearm, radius ~0.33 m'
sock_off['head']['note'] = 'the eye (front of the head), for look-at / targeting'

names = [b['name'] for b in J['bones']]
pairs = sorted({tuple(sorted((n, n[:-2] + '_r'))) for n in names if n.endswith('_l')})
pairs = [[a if a.endswith('_l') else b, b if b.endswith('_r') else a] for a, b in pairs]
chains = {'spine': ['hips', 'spine_01', 'spine_02', 'spine_03', 'neck', 'head']}
for s in ('l', 'r'):
    chains[f'arm_u_{s}'] = [f'shoulder_u_{s}', f'upper_arm_u_{s}', f'forearm_u_{s}', f'hand_u_{s}']
    chains[f'arm_d_{s}'] = [f'upper_arm_d_{s}', f'forearm_d_{s}', f'hand_d_{s}']
    chains[f'leg_{s}'] = [f'thigh_{s}', f'shin_{s}', f'foot_{s}', f'toe_{s}']
rig = {
    'id': 'cyclops', 'height': 8.0,
    'bones': [{'name': b['name'], 'parent': b['parent'], 'head': [round(v, 4) for v in b['head']],
               'tail': [round(v, 4) for v in b['tail']], 'deform': b['deform']} for b in J['bones']],
    'chains': chains,
    'sockets': {'hand_ur': 'hand_u_r', 'hand_ul': 'hand_u_l', 'forearm_ur': 'forearm_u_r', 'head': 'head',
                'club_grip2': 'hand_u_r'},
    'socket_offsets': sock_off,
    'pairs': pairs,
    'props': {'club': {'glb': 'game/assets/props/club.glb', 'socket': 'hand_ur', 'length_m': 5.5,
                       'origin': 'grip, 0.45 m above the butt end', 'axis': 'club head along +Y (Godot) / +Z (Blender)',
                       'blender_world_rest': [[round(v, 5) for v in r] for r in Wclub.tolist()]}},
    'notes': ('Blender space: Z up, faces -Y, metres; bone head/tail in armature space = world (transforms applied). '
              'Left = character left = +X. socket_offsets are in the glTF joint frame (= Godot bone global rest frame, '
              'Y up): loc metres, rot_deg = Godot rotation_degrees (YXZ order), quat_xyzw the same rotation. '
              'Upper arm pair = *_u_*, lower arm pair = *_d_* (parented to spine_03, no clavicle). root is non-deforming. '
              'Skin: own distance/geodesic weights (03a_weights.py), max 4 influences, normalised; beard rides the head; '
              'crotch shares hips + both thighs. Rest pose = generated pose (T upper arms, lower arms ~40 deg down). '
              'Rev 2 (11-22, after review): legs re-measured from slices - knee at the back hollow z 2.22, ankle at the '
              'narrowing z 0.95 (the first rig had them one segment low); limb chains re-split by joint planes '
              '(forearm_u = 1 for |x| 2.37-2.90, thigh 0 below z ~1.97, shin 0 below ~0.75, heel = foot, toe only in '
              'front of the ball y < -0.35); posterior armpit blend widened (upper_arm_d fades out on the back above z 5.5).'),
}
json.dump(rig, open(os.path.join(D, 'rig.json'), 'w'), indent=1)
print('###RIG###' + json.dumps({'skins': len(g.skins), 'joints': len(sk.joints), 'meshes': len(g.meshes),
                                'tris': mesh_tris, 'images': len(g.images), 'materials': [m.name for m in g.materials],
                                'joint_head_err_max': round(max(errs), 6), 'animations': len(g.animations or []),
                                'socket_offsets': sock_off}))
