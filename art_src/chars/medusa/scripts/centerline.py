"""Run from work/rig_medusa (reads mesh.npz from scripts/dump_mesh.py, writes centerline_raw.json + cl_pts.json)."""
import numpy as np, json
d = np.load('mesh.npz'); co = d['co']
pts = []
# upright section: z slices, |x|<0.75 (exclude arms/hands which are at |x|>0.8 below z 3.7)
up = []
for z in np.arange(0.9, 2.95, 0.1):
    m = (co[:,2] >= z) & (co[:,2] < z+0.1) & (np.abs(co[:,0]) < 0.75) & (co[:,1] < 0.5)
    c = co[m]
    yc = (c[:,1].min() + c[:,1].max()) / 2
    up.append([0.0, yc, z + 0.05])
# bend: sectors around pivot P=(y=0.1,z=1.0), angles from down-front
P = np.array([0.1, 1.0])
bend = []
sel = (co[:,1] < 0.6) & (co[:,2] < 1.2) & (np.abs(co[:,0]) < 0.5)
c = co[sel][:, 1:]
rel = c - P
ang = np.degrees(np.arctan2(rel[:,1], rel[:,0]))   # angle in (y,z) plane: 180 = -Y, -90 = down
for a0 in np.arange(-175, -95, 10):
    m = (ang >= a0) & (ang < a0 + 10)
    r = np.linalg.norm(rel[m], axis=1)
    rm = (r.min() + r.max()) / 2
    am = np.radians(a0 + 5)
    bend.append([0.0, P[0] + rm*np.cos(am), P[1] + rm*np.sin(am)])
hor = []
for y in np.arange(0.4, 8.45, 0.25):
    m = (co[:,1] >= y) & (co[:,1] < y + 0.25) & (co[:,2] < 1.2)
    c = co[m]
    hor.append([0.0, y + 0.125, (c[:,2].min() + c[:,2].max()) / 2])
print('up', np.round(up, 2).tolist()[:3], '...', np.round(up, 2).tolist()[-3:])
print('bend', np.round(bend, 2).tolist())
print('hor', np.round(hor, 2).tolist()[:4], np.round(hor,2).tolist()[-3:])
allp = [p + [[255,0,0]] for p in up] + [p + [[0,170,0]] for p in bend] + [p + [[0,0,255]] for p in hor]
json.dump(allp, open('cl_pts.json', 'w'))
json.dump({'up': up, 'bend': bend, 'hor': hor}, open('centerline_raw.json', 'w'))
