# hercules / walk_back: animator notes (2026-11-22, owner away: decisions noted)

| clip | video window | keys | IoU per key (front/side) | length | loop | events |
|---|---|---|---|---|---|---|
| walk_back | 4.167-4.667 s (one cycle, `ak cycle` from t0 4.0: period 0.50 s, IoU 0.983) | 12 (one per frame at 24 fps, linear, + loop seam) | strip 9 frames: 0.83/0.72, 0.83/0.73, 0.81/0.73, 0.80/0.74, 0.80/0.73, 0.83/0.75, 0.82/0.75, 0.82/0.74, 0.83/0.72 (mean 0.776) | 0.5 s (12 frames at 24 fps) | yes | none (SPEC §8 lists none for locomotion) |

**Stride for lead/core: 0.60 m per 0.5 s cycle (two 0.30 m steps) = 1.2 m/s at playback speed 1.0.**

## Fix pass (2026-11-22, animation fixer) - review findings addressed
Owner-away decision: game need wins over tracing. The video marches in place (its back foot stays at the same pixel
for the whole cycle), so the clip no longer copies its feet; it is a real backpedal that keeps the video's guard
upper body, crouch, rhythm (0.5 s) and right-then-left order. The strip IoU dropped 0.794 -> 0.776 because of that.

- **Stride (major).** Contacts: t=0 the LEFT foot lands behind, t=0.25 the RIGHT foot lands behind. (The review wrote
  "t=0 right lands"; that would swap the step order, so I kept the video's right-then-left order: the right foot swings
  0-0.25 s, the left 0.25-0.5 s, passing at 0.125 / 0.375 as the review asked.) At each contact the foot middle (ankle..ball)
  is 0.15 m behind the hips for the landing foot and 0.15 m in front for the other. Contact thighs come out at rx about
  -10/-12 (rear) and -37/-42 (front): the 0.15 m target needed less than the review's -45 estimate.
- **Planted feet (minor).** Every frame is an IK key: the stance foot's ball moves forward relative to the hips at exactly
  0.05 m per frame, so in the world it stays put while the body travels back at 1.2 m/s. Checked with `ak solve` on all
  12 keys: stance ball x and world y are constant to 0.1 mm; the foot's lowest vertex stays at 0 (the ball bone rises 6 mm
  over the stance through skinning, the sole does not). Foot angles are k0's (absolute), so soles stay flat;
  thigh rx, thigh ry and shin rx are solved per frame (ry holds the foot's sideways position).
- **Even steps (minor).** Lowest-vertex lift: right 5.9 cm at 0.125 s, left 5.5 cm at 0.375 s (was 8.3 / 2.2). 5 deg toe-down at mid-swing.
- **Sword (minor).** Blade tilted 16 deg forward in the side panel (world-X turn of hand_r, re-expressed in the same euler
  branch: hand_r rx 22.9 -> ~7, NOT +20: hand_r ry is -187, which flips the sign of a plain rx change) and forearm_r rx -28
  (-31.4 -> -59.4) to bring the hand forward, off the face. Side diff now overlaps the video blade; front panel blade stays
  vertical, hand at screen left.
- **Secondary (minor).** spine_01 ry +-2 (spine_02/03 +-1) leaning away from the lifting leg, peaks at 0.125 / 0.375;
  hip bob 1.0 cm (high at passing); upper_arm_l rx +-2.5 trailing the bob by 1.5 frames. Seam exact (loop).
- Files: `keys_walk_back.json`, `poses_walk_back/k00..k11.json` (old k0..k3 backed up in
  `work/anim/hercules_walk_back_fix/orig/`), `action_walk_back.json`, `strip_walk_back.jpg`; strip mp4
  `work/anim/hercules_walk_back_fix/strip_walk_back.mp4`. Generator (params + IK, re-run to tweak):
  `python3 work/anim/hercules_walk_back_fix/gen.py "$(cat work/anim/hercules_walk_back_fix/params_final.json)" <clip>/poses_walk_back`.

## For lead/core (not my module)
- `player.gd` back-away uses locked-on 4.6 m/s; at 1.2 m/s per clip that is 3.8x playback and will look frantic.
  Either play walk_back at speed = velocity / 1.2 m/s (clamped ~0.6-2.0), or lower back-away speed to ~2.5 m/s
  (then ~2.1x), or both. Same request is in `docs/notes/anim_hercules_walk_back_fix.md`.
- Optional re-prompt (lead, credits): Seedance "each foot reaches 30 cm behind the body, the body travels on the spot".

## Original animator notes (first pass)
- Reference: usable. Calibration IoU front 0.935, side 0.966. Settles into the guard 0.5-1.5 s, then a very steady in-place
  backpedal from ~2.0 s to the end.
- Pose: deep crouch (root ~0.26 m lower than rest), knees out, lower spine leaning 40 deg forward, upper spine 20-24,
  head tilted back 12 to keep the eyes forward. Shield forearm across the chest at 45 deg (front 90 / side -90 aim,
  twist 40) so the shield face shows in BOTH panels.
- What does not match and why: side IoU stops at ~0.72-0.76 because Seedance draws the side view bigger and the shield as a
  near-full disc in both panels at once (a flat disc cannot face both cameras; 45 deg is the compromise). In the side view
  Seedance also shows an open right hand in front of the shield; ours holds the sword there. Now also: our feet stride,
  the video's do not (deliberate, see above).
- Tool note: `ak fit` refuses aim-form bones; aim poses were converted to rx/ry/rz by baking and reading back
  (`work/anim/hercules_walk_back/conv.sh`). A built-in `--to-euler` would save that step.
