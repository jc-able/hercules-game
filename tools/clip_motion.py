#!/usr/bin/env python3
"""Per clip: which bones move and by how much (max angle from the clip's first key, degrees). Finds frozen limbs.
usage: python3 tools/clip_motion.py <char id> [...]   (reads game/assets/characters/<id>/<id>.glb)
       python3 tools/clip_motion.py --glb <file.glb>   (any exported GLB, e.g. a scratch export)
A bone counts as frozen when it turns less than 3 degrees over the whole clip. Writes work/clip_motion.json."""
import sys, json, math, struct, pathlib
import pygltflib, numpy as np
REPO = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPO / 'game' / 'assets' / 'characters'
def acc(g, blob, i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    arr = np.frombuffer(blob, dtype=np.float32, count=a.count * n, offset=off).reshape(a.count, n)
    return arr
out = {}
args = sys.argv[1:]
items = []
while args:
    a = args.pop(0)
    if a == '--glb':
        f = pathlib.Path(args.pop(0)); items.append((f.stem, f))
    else:
        items.append((a, ROOT / a / f'{a}.glb'))
for cid, path in items:
    g = pygltflib.GLTF2().load(str(path)); blob = g.binary_blob()
    names = [n.name for n in g.nodes]
    joints = set(g.skins[0].joints) if g.skins else set()
    res = {}
    for an in g.animations:
        rng = {}
        for ch in an.channels:
            if ch.target.path != 'rotation' or ch.target.node not in joints: continue
            q = acc(g, blob, an.samplers[ch.sampler].output).astype(np.float64)
            q /= np.linalg.norm(q, axis=1, keepdims=True)
            d = np.abs(q @ q[0]).clip(0, 1)
            rng[names[ch.target.node]] = float(np.degrees(2 * np.arccos(d)).max())
        for j in joints:
            rng.setdefault(names[j], 0.0)
        t = acc(g, blob, an.samplers[an.channels[0].sampler].input)
        res[an.name] = {'len': float(t[-1][0]), 'rng': rng}
    out[cid] = res
(REPO / 'work').mkdir(exist_ok=True)
json.dump(out, open(REPO / 'work' / 'clip_motion.json', 'w'))
for cid, res in out.items():
    print(f'=== {cid}: {len(res)} clips, {len(next(iter(res.values()))["rng"])} joints')
    for an, r in sorted(res.items()):
        rng = r['rng']; moving = [b for b, v in rng.items() if v >= 3.0]; still = sorted(b for b, v in rng.items() if v < 3.0)
        print(f"  {an:22s} {r['len']:5.2f}s moving {len(moving):2d}/{len(rng)}  frozen: {', '.join(still)}")
