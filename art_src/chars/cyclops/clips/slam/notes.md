# cyclops / slam video: notes (animator, 2026-11-22)

Video ok: calib_iou front 0.923 / side 0.950, views in sync, static camera. Clips chain: slam ends on and stuck/pull_free
start from the SAME file `poses_stuck/k00_stuck.json`; slam starts and pull_free ends on `poses_slam/k00_ready.json`
(= the rest pose, club held up). IoU per key = (front, side) against the aligned frame at the key's video time.

- slam | window 1.0-2.75 s | 9 keys | ready 0.91/0.92, lift 0.77/0.73, raise 0.65/0.80, overhead 0.80/0.66, windup 0.81/0.70,
  chop 0.66/0.48, swing 0.75/0.56, impact 0.76/0.68, stuck 0.73/0.72 (mean 0.73) | 1.75 s, no loop | impact 1.5 |
  The smash is 3 video frames (2.375-2.5) with motion smear: chop/swing keys score low because the video frames are blurred;
  the club arcs over the head and lands at 1.5. Keys 1.333-1.5 are linear for speed.
- stuck | window 3.0-6.0 s | 2 keys (stuck, tug) | 0.73/0.72, 0.74/0.70 (mean 0.72) | 1.5 s loop | no events |
  The video is almost static here (club near end moves < 0.2 m in 3 s); the loop is an authored tug: trunk leans back 3 deg,
  the handle lifts 0.18 m about the club tip resting on the ground. Slow it down in game if 1.5 s reads too busy.
- pull_free | window 6.0-7.75 s | 9 keys | stuck 0.72/0.64, strain 0.74/0.68, heave 0.75/0.67, lift 0.75/0.60, across 0.68/0.65,
  swing_up 0.64/0.66, over 0.74/0.76, shoulder 0.74/0.71, ready 0.69/0.82 (mean 0.70) | 1.75 s (ready reached at 1.5, held) |
  no events | SPEC wants 0.8 s: play at ~2.2x. No visible roar in the video (the head stays level), none authored.

## What does not match and why
- The rig's upper arms are short (upper arm + forearm 1.6 m on an 8 m body, plus a 1.1 m shoulder bone) while Seedance
  draws longer arms. The left upper hand cannot reach the club handle in the stuck/impact poses: it sits ~0.6-0.9 m above
  the handle (right hand grips it). At 7.0 s the hands hold the club lower/closer than the video. Fixing that needs either
  a deeper bend than the video shows or longer arm bones (rig request, see docs/notes/anim_cyclops_slam.md).
- `ak fit` liked S-shaped spine twists (spine_02 ry +20, spine_03 ry -30) on the stuck pose; kept because it matches the
  hunched silhouette in both views, but it is a fit artefact more than anatomy.
- The club in the video is redrawn ~25% longer than the prop (4.7 m visible thick part vs 3.7 m), so the club tip never
  overlays exactly; the club was aimed by its measured direction (brown-pixel line fit in both panels).

## How the poses were made
Hands are placed by a small IK on top of `ak` poses: club direction + grip point measured from the video (largest brown
component, PCA line, both panels -> 3D), right hand oriented so the club (rest axis +Z of hand_u_r) lies on that line,
two-bone IK for upper arm/forearm with the shoulder bone partly following, feet planted by leg IK. Then `ak fit` on
trunk/legs/view_offset and the arms re-solved. Scripts (scratch, not in git): work/anim/cyclops_slam/{kin,build,aim2eul,
club,refit}.py, specs in work/anim/cyclops_slam/s/.

## Fix pass (anim fixer, 2026-11-22; owner away, decisions noted)
- stuck | re-keyed for the game, not the video | 2 keys (k00_stuck, k01_tug) | strip IoU 0.53/0.49 (was 0.73/0.72: the video draws the club to his LEFT, the game needs it on the centre line) | 1.5 s loop | no events | deeper crouch (hips 2.79 -> 2.34 m), club yawed to the centre line and pitched 18 deg down: club-head centre (0.20, -5.32, 0.19), lowest vertex -0.66 m (half the head in the earth), forearm_u_r mid 2.15-2.24 m, left upper hand ON club_grip2 (0.00 m, was 0.70 m), tug moves the club head < 0.01 m.
- slam | 10 keys (+k065_fall, a re-grounded read-back at 1.458: feet were 0.10 m under the floor) | strip IoU 0.72/0.66 | 1.75 s | impact 1.5 | k07_impact re-solved: same buried club point as stuck, trunk 3 deg deeper; ends exactly on k00_stuck.
- pull_free | 9 keys | strip IoU 0.65/0.60 | 1.5 s (held tail dropped; game stretch x1.875) | no events | k01-k03 re-solved from the new stuck pose (club head stays in the crack at strain, clears the floor from 0.375 s); k05 left arm = read-back at 1.1875 so the left hand lets go over 1.0-1.25 instead of in one frame; head/neck thrown back 18/6 deg at 1.25-1.375 (roar). Known: one frame (0.875) the handle crosses the left forearm near the grip.
