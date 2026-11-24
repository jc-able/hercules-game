# pegasus / glide (animator, 2026-11-22; owner away, decisions noted here)

| clip | window (video s) | keys | IoU per key (front/side) | length | loop | events |
|---|---|---|---|---|---|---|
| glide | 1.500-4.500 | 4 (+ loop seam) | k0 0.78/0.80, k1 0.75/0.80, k2 0.78/0.79, k3 0.76/0.80 (mean 0.78) | 3.000 s (72 frames @ 24) | yes | none |

Files: `keys_glide.json`, `poses_glide/k0..k3.json`, `action_glide.json`, `strip_glide.jpg` (scratch strip mp4:
`work/anim/pegasus_glide/strip_glide.mp4`). Strip in-between IoU 0.75-0.81 on every frame, no pops, seam exact.

- **Tool problem (IoU was meaningless until worked around).** `akimg.silhouette` counts colourful pixels (chroma > 0.10)
  as character, so on Pegasus' green `--bg` sheet the whole background is "character" (93% of the frame): plain `tools/ak`
  reports IoU ~0.93 for ANY pose, calibration is garbage and `fit` climbs nothing. All numbers above come from
  `python3 work/anim/pegasus_glide/akg.py <ak args>`, a wrapper that swaps in a green-key silhouette (bg = green-dominant
  pixels) and then runs the normal ak main; the tool files are untouched. The fly and idle animators need the same.
- **Calibration.** Seedance did not start from the sheet: frame 0 is already the glide pose, the divider moved to the
  centre and the horse hovers. Bounds calibration against the rest sheet failed (IoU 0.46). I calibrated against a render
  of my first glide pose instead (`--sheet work/anim/pegasus_glide/k1_render.png`, calib `work/anim/pegasus_glide/kf1/calib.json`,
  scale 1.437 / 1.431); `view_offset` [0.02, 0, -0.30] + `view_scale` 1.02 are the same in all keys (no camera drift measured).
- **What the video shows vs the prompt.** The prompt asked for flat, still, fully outstretched wings and side-to-side
  tilting. Seedance drew wings raised in a wide V that slowly "breathe": the front-view span pulses between ~318 and
  ~387 sheet px (sweep back = narrow front, wider side) with a ~1.4-1.6 s period, legs tucked, hooves dangling a bit
  lower when the wings are wide. Measured centre x is constant: no visible roll. I matched the V + breathing (narrow keys
  k0/k2 at 1.5/3.125 s, wide keys k1/k3 at 2.25/3.875 s; 1.5 and 4.5 s have identical silhouettes, so the loop is clean).
- **Authored, not traced:** a +-1.5 deg body roll on the wide keys (the prompt's tilt, too small to fight the video),
  a small tail sway (chain bend_side +-4 deg, bend_up -3) and a 3-deg head nod for secondary motion.
- **Does not match:** side view - the video's wings sweep a little further back and the forelegs fold tighter than ours
  (front cannons); front view - our tucked legs read ~10 px longer. Fit could not raise these without breaking the front.
- Root height: root.loc stays 0; the body hovers with the lowest hoof 0.13-0.14 m above the floor (bake "floating" notes
  are expected for a flying clip). The game places Pegasus in the air.
- Wing limits from docs/notes/rig_pegasus.md respected: wing_*_03 within ~25 deg of rest, no feather-group rotations,
  neck_01 6 deg.

- Fix (animation fixer, 2026-11-22): leg_fl_02 / leg_fr_02 rx -10 on all four keys (tighter foreleg fold, shorter tucked legs in the front panel). wing_r_03 ry 32 -> 28 on k1/k3 (the primary-tip spike in the chase view). Strip mean 0.781 (0.75-0.80 front, 0.79-0.80 side), seam exact. Rider pair check: 0 hits on 36 frames.

## Re-base (natural pass, 2026-11-23, re-base animator)
glide rebase | base = action_glide.rest_v1.json (the matched clip above) | 24 keys every 3 frames (incl. the 4 matched key times, values unchanged) | 3.000 s, loop, no events | tool `work/rebase/pegasus/rebase_bl.py`, layers in `work/rebase/pegasus/life.json` | moving joints 13 -> 38 of 41 | head/neck look + nod with lag, tucked legs paddling, tail streaming, wing_03 + feathers trailing the breath | rider pair check 0 hits / 72 frames. Old files: keys_glide.rest_v1.json, action_glide.rest_v1.json, strip_glide.rest_v1.jpg; new poses poses_glide/rb_k*.json. Details: docs/notes/rebase_pegasus.md.

## glide v3 (animation fixer, 2026-11-23)
glide v3 | base = keys_glide.rebase.json (rb_k*.json) | 24 keys fx_k*.json | 3.000 s, loop, no events | tool `work/anim2/pegasus_fix/fly/glide2_bl.py` (args 1 1.5)
- Right wing chain (wing_r_01/02/03 + feathers) one key = 0.125 s late (wraps): wing_01 L/R corr 1.000 -> 0.846.
- spine_03 and everything on it (neck, head, forelegs) bank 1.5 deg * sin(2 pi t / 3 s) about the spine_03 head. Saddle,
  wing roots, hips and spine_01/02 unchanged (probe: saddle socket identical).
- Rider pair check at 0.4x: 0 hits / 72 samples. Strip (akg): 0.595 (re-base 0.595).
- Re-base version kept: keys_glide.rebase.json, action_glide.rebase.json, strip_glide.rebase.* (never merge them).
