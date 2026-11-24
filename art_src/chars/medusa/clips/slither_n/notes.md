# medusa / slither_n video: clip notes (animator, 2026-11-23; owner at the Mac, no questions, decisions written here)

Video: Seedance 2.5 from `sheet.png` (= sheet_nat_std, natural stance), calib IoU front 0.907 / side 0.905. `ak cycle` from 1.0 s:
1.75 s (IoU 0.981) and 3.5 s (0.982 = two cycles); the masks confirm ONE sway cycle = 1.75 s (hips at her right 2.15 s,
at her left 3.02 s, right again 3.90 s). Window used: 2.1667-3.9167 s (t0 = 2.1667 = video frame 52, hips at their extreme
toward her RIGHT). Scratch + measurement scripts: `work/anim2/medusa_slither_n/` (meas.py, score.sh, fit3/).

| clip | window | keys | IoU per key front/side (rest pose scores ~.59/.75) | length | events |
|---|---|---|---|---|---|
| slither | 2.1667-3.9167 s | 7 (every 0.25 s), loop | k0 .79/.87, k1 .74/.83, k2 .72/.81, k3 .72/.82, k4 .74/.85, k5 .81/.85, k6 .83/.89 (mean .766/.845; strip mp4 mean .779) | **1.75 s @ 24 fps (was 2.0 s)** | none (old clip had none) |

## Length change (contract note for the lead)
Old 2.0 s -> new 1.75 s: the video's measured cycle (the brief allows it when the motion needs it). The game plays slither at
`speed / reference` (manifest `move_speed`, else T.slither_speed = 3.2 m/s); nothing times on the clip length (loop, no events).
**Stride** (how far a planted point of the ground tail travels per cycle) = wavelength of the tail wave = 6.67 links x 0.84 m
= **5.60 m per 1.75 s cycle**; **planted speed at clip speed 1 = 3.20 m/s** = slither_speed, so the game's rate stays right
(old clip: 6.7 m / 2.0 s = 3.35 m/s). Suggest writing `"move_speed": 3.2` into the slither manifest entry at merge time.
Two "steps" per cycle = one sway to her right + one to her left.

## How the keys are built (reproducible: `poses_slither/gen_slither_n.py poses_slither/gen_params.json ../../natural_pose.json poses_slither 7`)
Every key = `natural_pose.json` (merged: all its bones, the tail chain curve, the S-curve pelvis tilt) + the slither motion
on top; bones the motion does not touch keep their stance angles. The motion was MEASURED on the video masks (every 1/12 s,
harmonic fit per body band, 1.75 s period) and keyed from those numbers:
- Sway runs DOWN the body as a travelling wave (phase of the +X max): head .38 (amp 0.117 m), chest .41 (0.117 m), hips .49
  (0.162 m), upright tail z 2 m .55-.61 (0.21 m), z 1.2 m .65 (0.27 m), then into the ground wave. Keyed with root x (pelvis)
  plus spine_01/02 and spine_03/neck tilts that put chest and head on their measured offsets, and tail_01..03 `ry` that put
  each upright-tail joint on its band; tail_04 cancels the roll so the ground tail stays flat.
- Side view: the upright body rocks about chest height (head forward at .50, lower tail forward at .93-.97, ~0.1 m each):
  pelvis `rx` 2.7 deg with tail_04 counter-pitch (the rig's lean recipe), +3 deg forward lean of spine_01 (prompt).
- Ground tail (tail_05..14): travelling heading wave, 50 deg, 6.67 links per wave, runs hips -> tip, on top of the stance curve
  (phase 0.3125 picked by a front/side IoU scan over 0/.25/.375/.5/.75).
- Arms (traced from the frames): alternate, the RIGHT arm fully forward at phase .37 (forearm level, palm forward, as in the
  video at 2.75-2.92 s), the LEFT at .87; the back arm hangs with a soft elbow. Upper arms swing 20 deg, forearms 37.5 deg,
  forearm lags .05, hand lags .10 (follow-through) and keeps the stance's wrist bend; hand twist +-10, shoulders shrug 3 and
  yaw 3 with their arm.
- Authored (not readable at 480p): chest yaw 7 deg against the arms (spine_01..03) with the pelvis 3 deg the other way,
  neck/head counter-yaw so she keeps looking ahead, head tilt 3 deg into the sway, a small nod at twice the cycle; the six
  hair snakes trail back 6 deg and sway 7-10 deg each with its own delay (0, .15, .31, .47, .62, .78 of the cycle).
- Framing: per-key `view_offset`/`view_scale` from `ak fit` (Seedance drifts ~0.1-0.16 m fore-aft at 2.7-3.2 s); render-only,
  pasted into the k*.json after generation from `work/anim2/medusa_slither_n/fit3/k*.json` (the generator alone writes 0).

Motion check on action_slither.json (max key-to-key turn, < 3 deg = frozen): 34 of 35 bones move (only the non-deforming
`root`); old clip 26 of 35. Arms 24-58 deg, shoulders 8, spine 4-5, neck 8.6, head 5.6, snakes 16-25, upright tail 4-12,
ground tail as before. Loop seam 0.15 deg; lowest vertex within +-2 mm of the floor in every strip frame.

## Does not match, and why
- Front panel, lower body: the stance's S-curve (pelvis tilted 6 deg, upright tail offset ~0.1-0.18 m to her left) is kept in
  every key; the video slowly re-centres it, so a constant red/blue band remains on the upright tail (front IoU ~.72 at k2/k3).
- Side panel tail: Seedance draws the ground tail longer/thicker, running out of the frame (same as the old video); our wave
  shortens it in side view. The top-down S-shape is not visible in either panel: wavelength chosen for planted speed 3.2 m/s
  and confirmed by the IoU scan (5.6 m scored as well as 6.4 m in front, better in side).
- The forward hand reaches ~0.1-0.2 m less far than the video's at phase .4 (the video's hand is redrawn larger).
- Snake hair, head tilt/yaw and chest yaw are authored, not traced.

- animfix2: stance floor-tail curl faded to 0 in slither (gen_params stance_tail_fade 1.0), wave 40 deg / 7.0 links / x1.03 per link; no-slip best speed 3.21 m/s, slip rms 1.21 m/s at 3.2; strip IoU .71/.82 (animfix2 2026-11-23; details in docs/notes/assemble2_medusa.md "Animation fix pass")
