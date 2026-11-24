"""Generate hydra idle key poses. usage: gen.py OUTDIR [json params]"""
import json, math, sys, os
P = dict(spine=[-0.3, -0.3, -0.4], neckc=[0.3, 0.3, 0.2, 0.2, 0.2], tail=[0.8]*8, tail0=[0,0,0,0,0,0,0,0],
         sway_side=0.7, sway_up=0.5, twist=3.0, headc_side=0.4, view=[0.02, 0.01, -0.07], vscale=1.0, n=6, sag=0.25, fwd=0.15, headc_rx=1.0)
if len(sys.argv) > 2: P.update(json.loads(sys.argv[2]))
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
# phase offsets per side neck (radians), and per-neck amplitude multipliers: no two necks move alike
PH = {'1': 0.0, '2': 2.1, '3': 4.0, '4': 1.2, '5': 3.3, '6': 5.2, '7': 0.6, '8': 2.7}
PH.update(P.get('ph_over', {}))
AM = {'1': 1.0, '2': 0.8, '3': 1.1, '4': 0.7, '5': 0.75, '6': 1.05, '7': 0.85, '8': 0.95}
AM.update(P.get('am_over', {}))
n = P['n']
for i in range(n):
    p = i / n
    b = (1 - math.cos(2 * math.pi * p)) / 2          # breath: 0 inhale (video 1.0 s), 1 exhale (video ~2.0 s)
    chains = []
    chains.append({"name": "spine", "bend_up": [0.0] + [v * b for v in P['spine']]})  # hips link untouched
    cs = P['headc_side'] * math.sin(2 * math.pi * p + 1.9)
    chains.append({"name": "neck_c", "bend_up": [v * b for v in P['neckc']], "bend_side": [cs, cs, cs, cs, cs]})
    chains.append({"name": "tail", "bend_up": [t0 + v * b for t0, v in zip(P['tail0'], P['tail'])],
                   "bend_side": [0.5 * math.sin(2 * math.pi * p - 0.8) * (k + 1) / 4 for k in range(8)]})
    bones = {}
    for k, ph in PH.items():
        a = AM[k]
        s = P['sway_side'] * a * math.sin(2 * math.pi * p + ph)
        u = P['sway_up'] * a * math.sin(2 * math.pi * p + ph + 1.4)
        # exhale: every head drops a little (video: all heads ~5 cm down, ~3 cm forward at ~2.0 s).
        # neck_1/8 are 'lateral' chains (bend_up = up); the others are 'vertical' (bend_up = forward,
        # bend_side + = toward the character's left), so they drop by leaning further OUT.
        if k in ('1', '8'):
            u -= P['sag'] * b
        else:
            u += P['fwd'] * b
            s += (-P['sag'] * b) if k in ('2', '3', '4') else (P['sag'] * b)
        chains.append({"name": f"neck_{k}", "bend_up": [u, u, u, u], "bend_side": [s, s, s, s]})
        bones[f"head_{k}"] = {"space": "local_delta", "rz": P['twist'] * a * math.sin(2 * math.pi * p + ph + 0.7),
                              "rx": -1.5 * a * math.sin(2 * math.pi * p + ph + 2.2)}
    for side in ("fr", "fl"):   # front legs keep their rest orientation so the feet stay planted when spine_03 breathes
        for seg in ("01", "02", "03"):
            bones[f"leg_{side}_{seg}"] = {"rx": 0.0, "ry": 0.0, "rz": 0.0}
        bones[f"foot_{side}"] = {"rx": 0.0, "ry": 0.0, "rz": 0.0}
    bones["head_c"] = {"space": "local_delta", "rx": P['headc_rx'] * b, "rz": 1.5 * math.sin(2 * math.pi * p + 1.0)}
    pose = {"space": "absolute", "root": {"loc": [0, 0, 0], "ground": "lowest"},
            "view_offset": P['view'], "view_scale": P['vscale'], "chain": chains, "bones": bones}
    json.dump(pose, open(f"{out}/k{i}.json", "w"), indent=1)
print("wrote", n, "poses to", out)
