import numpy as np, json, os, math, copy
REPO=os.path.expanduser('~/HerculesGame')
C=REPO+'/art_src/chars/cyclops/clips'
CLIPS={"slam":"slam/keys_slam.json","stuck":"slam/keys_stuck.json","pull_free":"slam/keys_pull_free.json",
       "sweep":"sweep/keys_sweep.json","hurt":"hurt/keys_hurt.json","death":"death/keys_death.json"}
BONES=["hips","spine_01","spine_02","spine_03","neck","head","thigh_l","shin_l","foot_l","toe_l","thigh_r","shin_r","foot_r","toe_r",
 "shoulder_u_l","upper_arm_u_l","forearm_u_l","hand_u_l","shoulder_u_r","upper_arm_u_r","forearm_u_r","hand_u_r",
 "upper_arm_d_l","forearm_d_l","hand_d_l","upper_arm_d_r","forearm_d_r","hand_d_r"]
def Rx(a):
    c,s=math.cos(a),math.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a):
    c,s=math.cos(a),math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a):
    c,s=math.cos(a),math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def rot_xyz(rx,ry,rz):
    r=math.radians; return Rz(r(rz))@Ry(r(ry))@Rx(r(rx))
def euler_xyz(R):
    ry=math.asin(max(-1,min(1,-R[2,0]))); rx=math.atan2(R[2,1],R[2,2]); rz=math.atan2(R[1,0],R[0,0])
    return [round(math.degrees(v),3) for v in (rx,ry,rz)]
def ang(A,B):
    return math.degrees(math.acos(max(-1,min(1,(np.trace(A.T@B)-1)/2))))
def m2q(M):
    t=np.trace(M)
    if t>0:
        s=math.sqrt(t+1)*2; w=0.25*s; x=(M[2,1]-M[1,2])/s; y=(M[0,2]-M[2,0])/s; z=(M[1,0]-M[0,1])/s
    elif M[0,0]>M[1,1] and M[0,0]>M[2,2]:
        s=math.sqrt(1+M[0,0]-M[1,1]-M[2,2])*2; w=(M[2,1]-M[1,2])/s; x=0.25*s; y=(M[0,1]+M[1,0])/s; z=(M[0,2]+M[2,0])/s
    elif M[1,1]>M[2,2]:
        s=math.sqrt(1+M[1,1]-M[0,0]-M[2,2])*2; w=(M[0,2]-M[2,0])/s; x=(M[0,1]+M[1,0])/s; y=0.25*s; z=(M[1,2]+M[2,1])/s
    else:
        s=math.sqrt(1+M[2,2]-M[0,0]-M[1,1])*2; w=(M[1,0]-M[0,1])/s; x=(M[0,2]+M[2,0])/s; y=(M[1,2]+M[2,1])/s; z=0.25*s
    return np.array([w,x,y,z])
def q2m(q):
    w,x,y,z=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def slerp(A,B,u):
    qa,qb=m2q(A),m2q(B)
    if np.dot(qa,qb)<0: qb=-qb
    d=float(np.clip(np.dot(qa,qb),-1,1))
    if d>0.9995: q=qa+(qb-qa)*u
    else:
        th=math.acos(d); q=(math.sin((1-u)*th)*qa+math.sin(u*th)*qb)/math.sin(th)
    return q2m(q)
def load_res(path):
    r=json.load(open(path))
    for k,v in r.items():
        v['local']={b:np.array(m) for b,m in v['local'].items()}
        v['abs']={b:np.array(m) for b,m in v['abs'].items()}
    return r
def keypath(clip,pf):
    return os.path.normpath(os.path.join(C,os.path.dirname(CLIPS[clip]),pf))
