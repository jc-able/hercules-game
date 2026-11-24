"""apply_pose(arm, pose): pose = {bone: [rx, ry, rz]} degrees, rotations about ARMATURE (world rest) axes at the bone head."""
import math
from mathutils import Euler, Matrix
def apply_pose(arm, pose):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for name, d in pose.get('_loc', {}).items():   # armature-space translation of a bone head (metres)
        pb = arm.pose.bones[name]
        from mathutils import Vector
        pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(d)
    for name, r in pose.items():
        if name.startswith('_'): continue
        pb = arm.pose.bones[name]
        Rw = Euler([math.radians(v) for v in r], 'XYZ').to_matrix()
        B = pb.bone.matrix_local.to_3x3()
        Rl = B.inverted() @ Rw @ B
        pb.rotation_quaternion = Rl.to_quaternion()
