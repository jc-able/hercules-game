# Ride animation (Hercules on Pegasus): ride animator, 2026-11-22

The owner was away, so this agent made every decision below and notes it here. Scratch is in `work/anim/ride_ride/`.
Nothing was written to hercules.blend, pegasus.blend or ride.blend.

## Deliverables
- `art_src/chars/ride/clips/ride/action_ride.json`: the hercules `ride` loop, baked with `tools/ak bake` on hercules.blend.
  It is 1.5 s long at 24 fps with 4 keys plus the loop seam and no events. Its keys are in `keys_ride.json` and its
  poses are in `poses_ride/k0_top|k1_down|k2_bottom|k3_up.json`, all written by `make_ride_keys.py`.
- `art_src/chars/ride/ride_game.json`: rider offset (saddle bone frame and Godot form), beat period, clip names, sync notes.
- The proof: `art_src/chars/ride/ride_check.blend` is a copy of ride.blend next to it, so the relative texture paths
  still work. `clips/ride/check/` holds build_check.py, wing_search.py, make_strip.py, check_keys.json,
  check_result.json, wing_search.json, iou.json and render_fNN.png. The strips are `clips/ride/strip_ride.jpg`
  (8 keys, video row on top, our renders below) and `strip_ride_close_a.jpg` / `_b.jpg` (rider close-ups).
- Rebuild, from the repo root:
  1. `python3 art_src/chars/ride/clips/ride/make_ride_keys.py`, then `tools/ak bake ... --clip ride --keys .../keys_ride.json --loop --fps 24 --out-action .../action_ride.json`.
  2. `cp art_src/chars/ride/ride.blend art_src/chars/ride/ride_check.blend`.
  3. Run `Blender -b --factory-startup --python clips/ride/check/build_check.py -- <repo> <abs ride_check.blend> <abs check_keys.json> <abs check_result.json>`.
  4. For each frame in check_keys.json, run `render_split_sheet.py -- --in <abs ride_check.blend> --out check/render_fNN.png --cam clips/ride/cam.json --reuse --frame N`.
  5. Run `python3 clips/ride/check/make_strip.py art_src/chars/ride/clips/ride work/anim/ride_ride/keyf`.

## Measurements from the video (ref.mp4, 24 fps; calib_iou front 0.947, side 0.942)
- **Beat period: 1.48 s.** This comes from the front-panel wing height on every frame. The 7 wing tops fit a line
  with a 1.485 s period and the 6 wing bottoms fit 1.471 s. The autocorrelation peaks at 35-36 frames, and at
  70-72 frames for the double beat. The first 3 s repeat exactly every 36 frames (1.500 s). The prompt asked for a beat
  "about once per second", but the video beats about every 1.5 s.
  `ak cycle` could not settle the period: from t0 1.0 it gave 2.79 s and from t0 3.0 it gave 1.375 s. The horse's
  silhouette dominates its IoU score, so it was not used.
- Clip window: video 1.875 to 3.375 s, which runs from one wing top to the next. Clip t=0 is the wing top.
- **The rider is rigid relative to Pegasus in the video.**
  - Front panel: the distance from his hair to the horse's head stays at 111.1 px, within ±0.6 px. That is ±6 mm at
    96.5 px/m. This holds across the whole beat, while the pair bobs 8 px (8.3 cm) together.
  - Side panel: while the near wing does not cover him (2.375 to 2.917 s), his head stays at x 632.0-632.3 and
    y 161-163.
  - So the video shows no torso rocking, head motion, arm swing or leg grip. "The rider's body follows the up-and-down
    motion" is just him being carried by the horse.
- Body bob, which belongs to the Pegasus fly clip, not the rider: 8.3 cm peak to peak. The body is lowest at the wing
  top and highest at the end of the downstroke (clip t 0.6-0.75).

## The clip (decision)
- Base pose: the seated pose from ride.json (`poses/hercules_ride.json`), unchanged at its core. Root is untouched,
  so the hips stay where ride.json seats them. The bake reports "floating" at 0.19 m. That is expected: he is
  seated, not standing.
- Added motion, kept at or near the video's ±6 mm tolerance so the clip is not a dead freeze (no root keys):
  - Spine 01/02/03 adds +1/+1.5/+1.5 deg of lean at the wing top (the horse is lowest and accelerating up, so the
    rider settles) and -1/-1.5/-1.5 deg at the wing bottom.
  - Neck moves ±1 deg and head ∓1 deg against it. Head stays absolute, so his gaze holds.
  - Sword arm: upper_arm_r side +1.5 / -1.5 and forearm_r side +3 / -3, a quarter beat late (inertia).
  - Legs grip on the downstroke by drawing the heels back along the barrel: shin and foot side +3 deg at t 0.375 and
    +1.5 at t 0.75. They never move inward, because the shins already touch the flanks. A first version moved them
    2 deg inward and raised the shin_l flank hits from 42 to 54; that version was replaced.
  - The shield arm is not keyed, so the hand stays on the mane and the shield stays where ride.json put it.
- Skirt bones are driven (ak sets them). They were never posed.

## Proof (ride_check.blend, 8 phases, same framing as the video sheet)
- Rider: the baked game action, written onto hercules_rig with `ak_blender.write_action`.
- Pegasus, per key:
  - Body: legs, neck and tail from `poses/pegasus_fly.json`.
  - Wings: wing_*_01 uses the make_poses.py raise family (full up -75, glide 0, full down +70 with Rz(-20)). The raise
    comes from the measured wing height u, with u 0.73 at horizontal.
  - Bob: the root moves dz from the measured horse-head height.
- **Wing clearance (finding for the Pegasus fly animator).** With the unswept extremes the wing's inner feathers pass
  through the rider:
  - On the downstroke and at glide they hit his thighs, shins and feet: 223-944 triangle pairs.
  - At the wing top they hit his skirt: 102-270 pairs.
  - `check/wing_search.py` searched 25 offsets (pitch 0-40 x yaw -20..20) per key. Sweeping the left wing 10 deg
    forward (world Rz(-10) after the raise, right wing mirrored) gives **0 hits** with his body, skirt, sword and
    shield at all 8 phases. Yaw -20 also clears everything. A 10 deg trailing-edge pitch alone fails at the
    downstroke (235-1760 hits).
  - The proof uses yaw -10 throughout. A fly clip made for riding (the anim_clips "pegasus:fly_ridden") should carry
    this sweep, or more.
- Remaining contact, all present in the base seated pose already (docs/notes/ride_check.md), and not made worse by the clip:
  - Inner thighs into the flank: 142-199 tri pairs per thigh.
  - Skirt into the back: about 340-410 pairs.
  - shin_l on the barrel: 0-42.
  - Shield rim in the mane hair: 274-296.
- Silhouette IoU against the aligned video frames (mean, min-max over the 8 keys):

  | Region | Mean | Min-max |
  |---|---|---|
  | Front panel | 0.55 | 0.31-0.66 |
  | Side panel | 0.76 | 0.66-0.94 |
  | Rider box, front | 0.78 | 0.73-0.85 |
  | Rider box, side | 0.84 | 0.70-0.95 |

  The low whole-panel front scores come from the wings. Seedance redrew larger wings that rise to a near-vertical V
  and droop fully down around the barrel at the bottom of the stroke. The rig's wing has a different shape and
  envelope. This is a Pegasus fly-clip matter, not the rider's.
- Looked at (strip_ride_close_a/b): he sits on the back in every frame and the wings stay outside him. In the side
  panel the near wing covers him during the upstroke, the same as in the video.
  - The video draws him slightly more upright, with the shield at his chest as in our base pose.
  - Our sword points straight back, while the video's points back and down.
  - Base-pose differences are left as they are, by the brief: the base is the ride.json seated pose.

## For the lead / game (world module)
- Godot: put a `BoneAttachment3D` on Pegasus `saddle`, with the hercules glb scene root as its child.
  - Transform: `Transform3D(Basis.IDENTITY, Vector3(0.0041, -0.8365, -0.1701))`. Godot bone rest = glTF joint frame =
    Blender bone frame, and the Y-up change cancels the -90 deg X rotation.
  - Not run in Godot. ride_game.json gives the alternative for the case where the Skeleton3D node is used.
- `pegasus_flight.gd` currently seats the rider by his hips (`IslandProxy.seat_rider`). That works too, but drives
  the rider every frame.
- Sync:
  - Speed: `rider speed_scale = 1.5 / pegasus_fly_beat_s`.
  - Phase: rider t=0 = wing top. Re-sync the rider position from the Pegasus AnimationPlayer every frame.
- The Pegasus fly clip is not animated yet. When it is, it should use the 1.48 s beat (or the length the game wants;
  the rider scales to it), the 8.3 cm bob with the body highest at the end of the downstroke, and the 10 deg forward
  wing sweep.
- Side effect: `tools/ak info` rewrote its default bones picture `art_src/chars/hercules/hercules_bones.jpg`
  (untracked, same rig).
- No Higgsfield credits used.
