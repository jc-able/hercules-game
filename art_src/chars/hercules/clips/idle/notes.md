# hercules / idle video: animator notes (2026-11-22)

| clip | video window | keys | IoU per key (front/side, mean) | length | events | loop |
|---|---|---|---|---|---|---|
| idle | 3.75-7.92 s (one `ak cycle` period, 4.167 s), retimed to 3.5 s | 4 | FIX 2026-11-22: k0 0.853/0.719 (0.786), k2 0.847/0.730 (0.789), k1 0.854/0.732 (0.793), k3 0.849/0.720 (0.785); strip mean 0.788 (was 0.787) | 3.5 s @24 fps | none | yes |

Keys (clip time): k0 0.0 s exhale (video 3.75) · k2 0.875 s mid-inhale + chest sways to his left (video 4.75) ·
k1 1.75 s full inhale (video 5.63) · k3 2.625 s mid-exhale + chest sways to his right (video 6.75). The loop seam copies k0.
Strip: every sampled frame scores 0.82-0.83 front / 0.74-0.75 side. No pops, nothing passes through the body, both feet
stay planted (ground check: left 0.000 m, right 0.001 m on every key).

## What the video shows
- 0-2 s: he steps out of the sheet A-pose into a wide, low ready stance. From 2.5 s to the end he holds that stance.
  Left foot forward, right foot back (seen in the side panel: the near leg, his right, is the back leg), knees bent, sword
  low in the right hand pointing forward-down, shield on the left forearm in front of his left side.
- The motion after 2.5 s is tiny: measured on the masks, the head top moves 1-2 px (about 1 cm) and the body centre
  moves less than 1 px over the 4.17 s breathing cycle (`ak cycle`: 4.167 s, IoU 0.978; 1.83 s is an equally good candidate
  because the frames barely change).

## Decisions (owner away)
- Window: one full cycle from the exhale low point (3.75 s). Retimed to 3.5 s so it sits inside the 2-4 s idle range.
- Legs are identical in all four keys, so the feet cannot slide; breathing lives in the upper body (spine_01/spine_02 lift,
  neck/head compensation, shoulders shrug 2 deg, arms open 1-3 deg). The left/right chest sway (spine_01 ry +-1 deg, head
  counter-turn) is AUTHORED, not traced: the prompt asks for a small weight shift and the video shows almost none, and a
  pure two-key breath looked mechanical.
- Back foot: foot_r rx 6.5 (heel lifted a few mm) so both feet touch the floor; without it the right foot floated 2.4 cm.
- Framing: the video character sits off the sheet framing (front x -0.07 m, side +0.27 m, scale 1.01); this is in
  `view_offset`/`view_scale` only, never in root.loc. Side-panel calibration IoU was 0.70 (front 0.96): Seedance redrew the
  side view slightly in frame 0, so the side offset was fitted per pose instead.

## What does not match and why
- Side panel tops out at ~0.75: the video's torso is deeper front-to-back than the model's and its near (right) shoulder
  sits further back. Twisting the chest 20 deg toward his right raised side IoU to 0.77 but dropped front to 0.79 and looked
  wrong from the front, so I left the chest square.
- Sword: in the video the blade faces the camera in the front view and points ~55 deg forward-down in the side view; those
  two views don't agree in 3D. Ours points forward-down (reads as a ready guard). A -60 deg forearm twist scored higher
  in the front view (0.845) but aimed the blade between his legs, so I didn't use it.
- The skirt front flap looks a little ragged in the side view with the forward thigh raised 56 deg (driven skirt bones,
  not keyable).

Files: `keys_idle.json`, `poses_idle/k0-k3.json`, `action_idle.json`, `strip_idle.jpg`; scratch + `strip_idle.mp4` in
`work/anim/hercules_idle/`.

## Fix pass 2026-11-22 (animation fixer, after review; owner away, decisions noted)
Changed `poses_idle/k0-k3.json`, re-baked `action_idle.json`, re-made `strip_idle.jpg` (looked at it: upright, no pops,
nothing through the body, feet planted). Old poses kept in `work/anim/hercules_idle_fix/poses_orig/`; generator
`work/anim/hercules_idle_fix/tools/gen.py` (args used: `v1 0 -8 -10 1.5 1.5`).
- **Torso lean.** spine_01 rx base -7 -> **0** (exhale k0 0, k2/k3 -1.125, k1 -2.25). Head tip vs hips (ak solve, +Y = back):
  k0 -0.6 cm (slightly in front), k2 +0.7, k3 +1.2, k1 +2.1 cm, was +5.8 cm at k0. view_offset re-fitted only
  ([-0.07, 0.28, -0.02/-0.01]); legs untouched; ground left 0.000 / right 0.0007 on every key.
  Cost: side IoU 0.744-0.748 -> 0.719-0.732 (drop 0.015-0.028, more than the ~0.01 the review allowed). Accepted because the
  head now sits over the pelvis and the stance reads combat-ready. Measured why: the video's whole upper body (belt included)
  sits ~8-10 cm further back over the feet than ours, so the old back-lean filled that area. That is pelvis placement between
  the feet (a leg re-pose), not spine lean; not done here (review said legs stay; feet would need re-planting).
- **Sword hand.** forearm_r side -32..-35 -> **-8..-12.5** (front 20 on all keys); hand_r local_delta rx **-10** so the blade
  keeps forward-down: measured blade angle in the side panel (grey-pixel PCA, `tools/blade.py`): video 28-29 deg below
  horizontal at 3.75 s and 5.625 s, ours ~31 deg (was ~10 deg). Hand now at the side of the hip; the video's hilt is still
  a little further back and its blade shorter (Seedance redraw), so our tip still ends just past the front knee.
  Front IoU rose 0.825 -> 0.853.
- **Bigger breathing (optional item, taken).** Breath deltas x1.5: spine_01 2.25 deg, spine_02/neck/head x1.5, shoulders
  +-3 deg, left arm opening x1.5, right arm side delta x1.5; authored chest sway spine_01 ry +-1.5 (head counter-turn
  +-1.2). Legs identical in all keys. Still subtle on purpose (the video moves ~1 cm).
- **Skirt (rigger item, not keyable).** Not changed: needs a clamp on the skirt_f / skirt_b drive from thigh rx (~25-30 deg)
  and hem weights near thigh_l in `art_src/chars/hercules/scripts/skirt_drivers.py` / the blend. Request filed in
  `docs/notes/anim_hercules_idle_fix.md`. After the rig fix the idle only needs `ak merge` (no key changes).
