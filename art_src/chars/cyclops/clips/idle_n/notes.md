# cyclops / video "idle_n" (natural stance) — animator notes (2026-11-23)

- idle | video window t0 2.25 - t1 6.65 s (two video breaths, 2.2 s each), slowed to 6.0 s (x1.36: breath every 3.0 s) |
  13 keys = 12 distinct poses every 0.5 s (k00 = natural_pose.json verbatim at 0.0 and at the 6.0 s seam) |
  IoU front/side: k00 0.953/0.955 (vs 2.25 s), k02 0.920/0.875 (vs 3.0 s), k06 0.829/0.904 (vs 4.46 s),
  k09 0.849/0.921 (vs 5.54 s), mean 0.901 | length 6.0 s (was 3.333 s), loop, 24 fps | events: none (the old clip had none) |
  25 of 29 bones move >= 3 deg (was 9 of 29); still < 3 deg: root (non-deforming), foot_r 1.1 and toe_l/toe_r 0 (planted feet).
  Not matched: the video barely moves (see below), so the weight shift, head turns, arm sway and hand flexing are AUTHORED;
  the keys that carry them score lower than the stance (k06 front 0.83 = the 0.12 m pelvis sway the video does not show).

## What the video shows (measured on the masks every 0.125 s, 0-10 s)
- calib_iou 0.964/0.955 (good, no drift). `ak cycle` from 1.0 s: period 2.208 s (IoU 0.994).
- Breathing only: head top +-0.035 m (2 px) with peaks at ~0.9, 3.0, 5.1, 7.5, 9.6 s; club top +-2 px; lower-arm width +-1-2 px.
- NOT in the video although the prompt asks for it: weight shift (silhouette centre x constant within 0.005 m over 10 s),
  head turns, visible finger flexing, upper-left-arm sway. The stance itself matches the natural stance (IoU 0.953/0.955).

## How the clip is built (work/anim2/cyclops_idle_n/gen.py)
Every key = natural_pose.json (all 28 posed bones) + layered deltas whose periods divide the loop (6, 3, 2 s), all zero at t=0:
- breath (3.0 s, inhale peaks 0.75/3.75 s): spine_01/02/03 straighten 0.6/2.0/2.6 deg, neck +1.2, shoulders rise 3 deg
  (lagged 0.15-0.25 rad), club arm bobs 2 deg behind the breath.
- weight shift (6 s, peak 3.0 s): pelvis sways 0.12 m toward the right foot and settles 0.035 m, hips level by 6 deg, spine
  counter-tilts 2/6/3 deg; left knee softens (thigh_l rx -3 -> -19, shin_l 3 -> 12). Legs solved per key with `ak solve`
  (Newton on thigh rx/ry + shin rx): both ankles stay within 4.8 mm of the stance, ground 0-5 mm all clip.
- head: looks left (peak ~1.8 s, 10 deg yaw neck+head) then right (~4.8 s), small nod on a 3 s cycle with an offset, tilt with the shift.
- upper left arm: hanging, sways 4/7/9 deg down upper arm -> forearm -> hand with 0.6 rad lag per link, wrist twist 8 deg (2 s).
- lower arms: each its own phase (6 s sway, 3 s wrist flex 10-12 deg, 2 s twist 12 deg in opposite senses) = the finger
  flexing (the rig has no finger bones).
- club hand: grip twist 4 deg (2 s). The club stays on the shoulder (no club/head contact in the strip).

## Notes for the lead
- `ak bake` removes the stance's root.loc x 0.25 m (in-place rule: first-key horizontal offset is subtracted), so the baked
  clip stands 0.25 m to screen-left of the video and the STRIP front IoU reads 0.58-0.71 (side 0.86-0.96, mean 0.785).
  The key-pose IoUs above (ak pose, same poses, root kept) are the real match. Every clip that starts from natural_pose.json
  gets the same shift, so clips still chain; a clip that does NOT start at the stance's 0.25 m would jump 0.25 m.
- Length changed 3.333 -> 6.0 s (one weight shift + two breaths); no events depend on it.
- Not verified in a GLB: `tools/clip_motion.py` needs an export (lead merges/exports); work/anim2/cyclops_idle_n/motion.py
  computes the same measure from action_idle.json (25/29 moving).
