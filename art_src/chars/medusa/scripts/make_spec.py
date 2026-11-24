"""Run from work/rig_medusa after centerline.py; copy bones_spec.json into scripts/. Compute bone head/tail positions from the mesh (centerline, snake clusters) + measured joints -> bones_spec.json"""
import numpy as np, json
d = np.load('mesh.npz'); co = d['co']
cl = json.load(open('centerline_raw.json'))
PELVIS = np.array([0.0, -0.86, 3.30])
up = [p for p in cl['up'] if p[2] < 3.25][::-1]           # top -> down
poly = [PELVIS.tolist()] + up + cl['bend'] + cl['hor']
poly = np.array(poly, float)
tipy = co[:,1].max()
poly = poly[poly[:,1] < tipy - 0.05]
poly = np.vstack([poly, [0.0, tipy - 0.04, 0.32]])
# light smoothing (keep ends)
for _ in range(3):
    s = poly.copy(); s[1:-1] = 0.25*poly[:-2] + 0.5*poly[1:-1] + 0.25*poly[2:]; poly = s
seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); L = np.concatenate([[0], np.cumsum(seg)])
t = np.linspace(0, L[-1], 15)
tail = np.stack([np.interp(t, L, poly[:,k]) for k in range(3)], 1); tail[:,0] = 0
print('tail length', L[-1], 'seg', L[-1]/14)
bones = []
def B(name, parent, head, tail_, deform=True):
    bones.append({'name': name, 'parent': parent, 'head': [round(float(v), 4) for v in head], 'tail': [round(float(v), 4) for v in tail_], 'deform': deform})
B('root', None, [0, 0, 0], [0, -0.8, 0], False)   # along -Y (forward) on the ground
B('pelvis', 'root', PELVIS, [0, -0.90, 3.85])
B('spine_01', 'pelvis', [0, -0.90, 3.85], [0, -0.93, 4.35])
B('spine_02', 'spine_01', [0, -0.93, 4.35], [0, -0.90, 4.80])
B('spine_03', 'spine_02', [0, -0.90, 4.80], [0, -0.82, 5.20])
B('neck', 'spine_03', [0, -0.82, 5.20], [0, -0.84, 5.45])
B('head', 'neck', [0, -0.84, 5.45], [0, -0.84, 6.35])
for side, s in (('l', 1), ('r', -1)):
    B(f'shoulder_{side}', 'spine_03', [s*0.12, -0.72, 4.90], [s*0.66, -0.62, 4.80])
    B(f'upper_arm_{side}', f'shoulder_{side}', [s*0.66, -0.62, 4.80], [s*1.05, -0.59, 4.22])
    B(f'forearm_{side}', f'upper_arm_{side}', [s*1.05, -0.59, 4.22], [s*1.37, -0.57, 3.82])
    B(f'hand_{side}', f'forearm_{side}', [s*1.37, -0.57, 3.82], [s*1.74, -0.58, 3.36])
prev = 'pelvis'
for i in range(14):
    n = f'tail_{i+1:02d}'
    B(n, prev, tail[i], tail[i+1]); prev = n
# snakes: 3 per side, clusters by z
for side, sgn in (('l', 1), ('r', -1)):
    m = (co[:,0]*sgn > 0.7) & (co[:,2] > 5.1)
    c = co[m]
    cz = np.array([6.25, 5.85, 5.5])
    for _ in range(30):
        lab = np.argmin(np.abs(c[:,2][:,None] - cz[None]), 1)
        cz = np.array([c[lab==k,2].mean() for k in range(3)])
    for k in range(3):
        q = c[lab == k]
        ax = np.abs(q[:,0])
        tipp = q[ax > np.quantile(ax, 0.85)].mean(0)
        basep = q[ax < np.quantile(ax, 0.15)].mean(0)
        base = basep + (basep - tipp) / np.linalg.norm(basep - tipp) * 0.25   # reach into the hair mass
        B(f'hair_{side}_{k+1:02d}', 'head', base, tipp)
json.dump(bones, open('bones_spec.json', 'w'), indent=1)
for b in bones: print(b['name'], b['parent'], b['head'], b['tail'])
