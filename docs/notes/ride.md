# Ride sheet (Hercules on Pegasus) - ride sheet agent, 2026-11-22

Owner away: every decision below was made by this agent and is noted.

## Outputs (`art_src/chars/ride/`)
- `ride.blend`: both characters appended from their own blends (read-only, untouched) at real scale: `hercules` +
  `hercules_rig` + `prop_sword` + `prop_shield`, `pegasus` + `pegasus_rig`. `hercules_rig` is parented to
  `pegasus_rig` bone `saddle` with the parent space moved to the bone HEAD, so its object transform IS the rider offset.
  Textures are re-pathed relative to ride.blend (`//../hercules/hercules_albedo.png`, `//../../props/*`,
  `//../pegasus/pegasus_albedo.png`); the sheet render shows them, so they resolve.
- `ride.json`: `rider_offset` (saddle bone frame, origin at the bone head: loc [0.0041, -0.8365, -0.1701],
  rot_deg [-90, 0, 0] Euler XYZ, plus quat and matrix), `rider_offset_armature_axes` (same transform in Pegasus
  armature axes: loc [0.0041, 0.1701, -0.8365], rot 0), `seat`, `hercules_pose`, `pegasus_pose` (both ak format), notes.
- `sheet_std.png` + `cam_std.json`: FRONT | SIDE sheet, 1280x720, bg 0.35,0.72,0.47, `--env 2.09,2.25,2.0,3.76`
  (151.8 px/m). Pegasus root at the world origin, so `ground_z` 0 is Pegasus's own ground (the pair floats above it).
- `poses/`: `hercules_ride_in.json` (input: aim form + `grip`), `hercules_ride.json` (resolved, pure ak),
  `pegasus_fly.json`, `pegasus_wing_extremes.json` (envelope only).
- `scripts/`: `make_poses.py` (Pegasus poses from the wing numbers in rig_pegasus.md), `build_ride.py` (builds the blend,
  seats him, measures interpenetration and the wing-beat envelope, writes ride.json), `sweep_shield_arm.py` (2-bone IK
  search for the shield arm), `peg_regions.py` (Pegasus skin / blue hair / wing classification), `render_check.py`.
- Rebuild: `python3 art_src/chars/ride/scripts/make_poses.py art_src/chars/ride/poses`, then
  `Blender -b --factory-startup --python art_src/chars/ride/scripts/build_ride.py -- <repo> art_src/chars/ride/seat.json`,
  then `tools/blender/render_split_sheet.py -- --in <abs>/ride.blend --out <abs>/sheet_std.png --cam <abs>/cam_std.json
  --bg 0.35,0.72,0.47 --env 2.09,2.25,2.0,3.76` (absolute paths). Each build is ~5 s; scratch in `work/ride/`.

## Seat
- Hercules HIPS joint 0.20 m behind and 0.247 m above the saddle bone head (Pegasus armature axes), no root pitch:
  hips at world (0, 0.30, 2.127), i.e. 0.68 m behind the wing roots. The height is solved (`"z": "auto"`): lowered until
  his crotch/buttock skin (skirt excluded) touches the back, measured as a height field (ray down onto Pegasus skin).
  Seat skin depth 0.0 cm.
- Game use: `BoneAttachment3D` on Pegasus `saddle` + `rider_offset` (bone frame; glTF keeps Blender joint frames, same
  assumption as hercules socket_offsets; NOT checked in Godot). Hercules plays `ride`; the offset stays valid for any
  Pegasus clip because the saddle bone rides spine_02.
- Why 0.20 m back (decision): further forward the inner secondaries of the spread wing (wing_*_feather_01, which hang beside
  the flank at rest) lie across his thighs (183-206 triangle hits at seat 0.12). At 0.20 + wing pitch 18 deg: 0 thigh hits.

## Poses
- Pegasus: glide wing (74.5, 62.3, 23.3) raised 15 deg about the body axis and pitched trailing-edge-up 18 deg (Rx), right
  wing = X-mirror; fore legs folded (rig agent's fly_ridden), hind legs folded under the belly (reviewer's R1, softened);
  neck_01/02/03 24/12/6 deg forward (limits 25/15), head -14; tail 35/12/10/6/5 back. Legs/neck/tail are
  `local_delta` rx (identical to the rig agent's 04_test semantics because they are pure X turns).
  Decision: "half raised" = mid-beat, only 15 deg up. At 22-38 deg the near wing covers his whole torso in the side panel;
  at 15 deg his head, torso, right arm and sword read above the wing and his legs below it.
- Hercules (absolute, aim form): spine 14/25/32 deg forward, neck 14, head -8 (looks ahead); thighs 58 deg out, 25 deg
  forward; shins 35 deg back (knees bent), feet down-forward; right arm low and back, sword trailing back and slightly up
  over the croup (grip (-0.47, 0.61, 2.10) -> tip (-0.59, 1.37, 2.19)); fingers curled 75 deg about their own X (grip),
  stored as the equivalent ak local_delta for this hand pose (re-derive if the hands change: build_ride.resolve_grip).
- Skirt: driven by skirt_drivers.skirt_matrices inside ak's Rig.solve (checked against a direct call: max matrix error
  1e-6). Thigh pitch/abduction 19/48 deg -> skirt_f 16.5, skirt_b 2.9, skirt_l/r 41 out + 9.7 pitch.
- Shield arm (decision): the brief allows "hand on the mane / shield tucked along his side". With a 0.9 m shield on the
  forearm, every arm that puts the hand on the withers mane pushes the shield into the horse: a 2-bone IK sweep
  (phi = elbow swivel, tau = forearm twist, up to 576 arms per wrist target, about 20 targets) found no arm that has both the
  hand on the mane and zero shield contact (zero-contact arms exist only with the hand 12-18 cm above the mane).
  Chosen: hand at the mane (nearest hand skin 4 cm from the hair surface with the fingers curled), elbow out, shield vertical along his left
  side facing out (normal 0.93, -0.37, 0.03); its lower front edge presses into the blue mane HAIR (279 triangle hits,
  hair only), 0 hits with Pegasus skin, wings or his own body. In the front panel the shield is a narrow upright ellipse at
  his left shoulder, in the side panel it shows behind his back.

## Interpenetration (build_ride.py metrics, final)
- Triangle overlaps: legs vs wings 0; sword 0 everywhere; shield vs skin/wings/self 0 (hair 279, see above);
  skirt side panels brush the inner secondaries (24 / 42 hits: cloth on feathers); the skirt hangs into the back (338
  hits, hidden, known rig limit: skirt_b barely moves when both thighs go forward).
- Legs into the flanks (vertex inside both the back height field and the side surface): shins <= 0.1 cm (they grip the
  barrel), feet and toes clear, inner thighs up to 8.3 / 9.2 cm (17 / 27 vertices > 5 cm): the medial thigh skin pressed
  against the upper flank. Wider thighs (65 deg) only took this to 8.2 / 9.2 cm and lifted the shins 8 cm off the flank.

## Envelope (wing beat)
Pair bounding box over the ride pose, glide, the reviewer's full up / full down and the builder's up / down strokes:
x +-1.99 (glide span), y -1.79 (muzzle) .. +2.10 (tail), z up to 3.64 (full up). Sheet env adds 0.10-0.15 m on each side
(0.21 m in front for the neck bob). Pegasus is huge next to Hercules (withers 1.9 m, both real scale), so the rider is ~1/5 of
the panel height.

## For the lead
- `tools/hf/gen_anim_refs.py ride` can use `art_src/chars/ride/sheet_std.png` now. The anim_clips "ride" prompt says
  "one hand holding the mane": the hand is at the mane but half hidden behind the shield in the front panel.
- The Godot check of `rider_offset` on the saddle BoneAttachment3D is still open (no Godot run here).
- No Higgsfield credits used.
