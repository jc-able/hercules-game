# cyclops / walk reference: animator notes (2026-11-22)

walk | video window 3.667-7.583 s (t0 3.667), loop, length 3.917 s (94 frames @ 24 fps), no events |
14 keys = 5 traced poses (k0, k0b, k1, k2, k3) + the passing re-ground k3b, each mirrored for the second step (m*),
k1/m1 held 0.21 s (the foot hangs at the top of the lift, then stomps down) |
key IoU front/side: k0 0.94/0.89, k0b 0.80/0.82, k1 0.85/0.72, k2 0.85/0.79, k3 0.93/0.84 (mean 0.88/0.81);
mirrored step, side only: m1 0.72, m2 0.79, m3 0.88 | strip mean IoU 0.82 (12 samples), lowest vertex -0.05..+0.08 m |
what does not match: see below.

## Reference problems (the video is only partly usable)
- calib_iou front 0.95, side 0.81 (ok).
- **The panels are out of sync.** The side panel steps steadily every ~1.96 s (alternating legs, `ak cycle` candidates
  2.04 / 3.96 / 5.875 s). The front panel lifts ONLY the character's right leg, once every ~2.93 s
  (0.83-1.67, 3.75-4.60, 6.70-7.60, 9.60-10.0 s); its left foot never leaves the floor (measured on the masks).
  The two agree only on the right-leg steps at 3.75-4.6 s and 9.6-10 s.
- Decision (owner away): trace the first step (3.667-5.625 s, both panels agree, right leg) and build the second step as
  the left/right mirror of it (`ak mirror`), timed from the side panel (step 1.958 s). Checked against the side panel only;
  the front panel at 6.7-7.6 s shows a right-leg lift that contradicts the side view and was ignored.
- Upper body: the prompt asked for torso sway, club swing and four moving arms; the video keeps the arms in the T pose and
  the club still. Matched the video: the arms stay at rest with an authored lower-arm swing (local_delta rx 2-10 deg,
  opposite to the legs) and a 1-3 deg trunk twist (spine_02 rz, neck counter-turns). A 2.5 deg side sway cost 0.10 front
  IoU against the video, so it was left out.
- The side panel's lifted-leg frames (k1, m1) stop at ~0.72: the video's skirt flaps forward over the raised thigh,
  the mesh skirt does not (cloth is skinned to hips/thighs).
- k2 (heel strike, 1.0 s): the right heel is 0.17-0.28 m above the floor at the key itself; it settles by k3 (1.583 s).
  A pose with both feet planted scored 0.81/0.72 against 0.85/0.79, so the better-matching pose was kept.

## Timing
Video timing kept: 1.96 s per step, 3.92 s per stride. That is slower than the prompt's "one step per second". At the
SPEC approach speed (2.6 m/s) the game should play the clip at about 1.5-2x (or `ak retime keys_walk.json --scale 0.5`)
so the feet do not slide; the stride length was not measured from the video (it walks on the spot).

## Files
keys_walk.json, poses_walk/*.json, action_walk.json, strip_walk.jpg (this folder);
scratch work/anim/cyclops_walk/ (strip_walk.mp4, fit logs, frame dumps, ana.py = per-frame foot lift / reach on the masks).

## Fix pass (anim fixer, 2026-11-22; owner away, decisions noted)
- walk | same poses, retimed x0.365 (ak retime) and the two k1/m1 holds dropped | 12 keys | 1.4167 s loop (24 fps) | events step 0.40 (right heel strike) | planted foot ~2.6 m/s at speed 1, footfalls every 0.71 s (= cyclops.gd _step_beat). The mirrored second step stays (the reference's front panel never lifts the left leg; side panel agrees with the alternation). Feet -0.02..+0.08 m.
