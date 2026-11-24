"""pose maths for the absolute view-axis pose files (R = Rz Ry Rx, world axes, degrees) - feedback2 pegasus"""
import json, math, os, numpy as np
REPO = os.path.expanduser('~/HerculesGame')
INFO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rig_info.json')))  # ak info of pegasus.blend
B = {b['name']: b for b in INFO['bones']}
def Rx(a): a=math.radians(a); c,s=math.cos(a),math.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a): a=math.radians(a); c,s=math.cos(a),math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a): a=math.radians(a); c,s=math.cos(a),math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def mat(e): return Rz(e.get('rz',0)) @ Ry(e.get('ry',0)) @ Rx(e.get('rx',0))
def dec(M):
    # M = Rz(c) Ry(b) Rx(a): M[2,0] = -sin b
    b = math.asin(max(-1, min(1, -M[2,0])))
    a = math.atan2(M[2,1], M[2,2]); c = math.atan2(M[1,0], M[0,0])
    return {'rx': round(math.degrees(a),4), 'ry': round(math.degrees(b),4), 'rz': round(math.degrees(c),4)}
def rest_vec(n): b=B[n]; return np.array(b['tail'])-np.array(b['head'])
def chain_tip(pose, names):
    p = np.array(B[names[0]]['head'], float)
    for n in names:
        e = pose['bones'].get(n, {}); p = p + mat(e) @ rest_vec(n)
    return p
