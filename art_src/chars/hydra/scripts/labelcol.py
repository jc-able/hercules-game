"""python3 labelcol.py <weights.npz> <out_vcol.npz> [label|bone:<name>|dom]  -> per-vertex colours for view.py --vcol"""
import numpy as np, sys, colorsys
w = np.load(sys.argv[1]); mode = sys.argv[3] if len(sys.argv) > 3 else 'label'
if mode == 'label':
    lab = w['label']; L = lab.max() + 1
    pal = np.array([colorsys.hsv_to_rgb((i * 0.382) % 1, 0.85, 0.95) for i in range(L)])
    rgb = pal[lab]
elif mode == 'dom':   # dominant bone, random colours
    b = w['idx'][:, 0]; rng = np.random.default_rng(3); pal = rng.random((b.max() + 1, 3)) * 0.8 + 0.2
    rgb = pal[b] * (0.5 + 0.5 * w['w'][:, :1])
else:
    names = list(w['bones']); bi = names.index(mode.split(':')[1])
    x = (w['w'] * (w['idx'] == bi)).sum(1)
    rgb = np.stack([x, 0.15 + 0 * x, 1 - x], 1)
np.savez(sys.argv[2], rgb=rgb.astype(np.float32))
