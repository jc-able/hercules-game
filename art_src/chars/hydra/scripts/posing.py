# exec'd by view.py / test scripts. pose dict: {bone: [rx, ry, rz] degrees about ARMATURE-space axes (rest frame)}
# optional "_loc": {bone: [x,y,z] metres in armature space}
import math
from mathutils import Euler, Matrix, Vector
def apply_pose(arm, pose):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    for name, r in pose.items():
        if name.startswith('_'): continue
        pb = arm.pose.bones.get(name)
        if pb is None: print('POSE: no bone', name); continue
        M3 = pb.bone.matrix_local.to_3x3()
        Ra = Euler([math.radians(v) for v in r], 'XYZ').to_matrix()
        pb.rotation_quaternion = (M3.inverted() @ Ra @ M3).to_quaternion()
    for name, l in pose.get('_loc', {}).items():
        pb = arm.pose.bones[name]; M3 = pb.bone.matrix_local.to_3x3()
        pb.location = M3.inverted() @ Vector(l)
    import bpy; bpy.context.view_layer.update()
