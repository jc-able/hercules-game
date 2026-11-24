# Feedback 2: FLIGHT fixer (flight control + camera, mount / dismount, creatures on the islands)

Owner items handled here: 3 (flight steering + "the panning around the horse while it's flying needs to be fixed"),
2 (getting on and off the horse, code side), 4 (NEW: the creatures on their islands, seen from the air).
Files changed: `game/scripts/world/pegasus_flight.gd`, `home_base.gd`, `island_proxy.gd`, `sea_world.gd`
(`ending.gd` untouched). Scratch, probes, logs and frames: `work/flight2/`.

## 1. Flight control and camera (pegasus_flight.gd)
DECISION (the owner will not answer): in flight the LEFT stick / WASD do everything (x = turn, y = climb/dive), the
right stick and the mouse do nothing; the camera is not orbitable at all (no small look offset either).
- `_unhandled_input` no longer reads the mouse; `_update_camera` no longer reads `Controls.get_look_stick()`.
- New camera: it sits behind Pegasus on a SMOOTHED heading (`CAM_YAW_RESPONSE` 3.5/s, lag capped at
  `CAM_YAW_LAG_MAX_DEG` 14 deg, so in a turn the banked horse shows a little from the side and never swings round)
  and looks along that heading `CAM_LOOK_DOWN_DEG` 11 deg down, plus 35 % of Pegasus's smoothed pitch; it drops
  behind in a climb / rises in a dive by 45 % of the pitch. Pegasus is therefore always centred left-right and in the
  lower-middle of the frame, also on the first frame of the take-off (the old aim point 120 m ahead along the pitched
  flight line put the pair on the bottom edge at take-off: owner recording 6:20, 4.5 s off-screen).
- `CAM_BANK` 0.3 -> 0.1 (horizon roll 11.4 deg -> 3.7 deg max). Pegasus itself still banks 38 deg into turns.
- The camera keeps `CAM_GROUND_CLEAR` 3 m above island ground (the volcano landing, recording 9:44).
- Harness `--world-cam-yaw=<deg>` side views still work (for the Pegasus-clips agent).
Measured (work/flight2/flight_steer_probe.gd on `--start=sea`, left 3 s, right 3 s, up 2 s, down 2 s, the right
stick actions pushed and swapped every 0.5 s the whole time; 1280x720; screen = pair centre / frame size):
| | before | after |
|---|---|---|
| pair on screen x | -0.95 .. 15.5 (off-screen) | 0.49 .. 0.51 |
| pair on screen y | 0.46 .. 56 (off-screen; start frame 0.97 = bottom edge) | 0.65 .. 0.67 (start 0.66) |
| horizon roll | 11.4 deg | <= 3.7 deg |
| camera heading vs Pegasus | orbit by the right stick | <= 14 deg lag, back to 0 within ~1 s |
Bot trip home -> sea -> Cyclops ring -> fight: lands as before (ring_enter 18.50, land 18.54, fight scene 19.62).

## 2. Mount and dismount (home_base.gd)
In his play the mount read as a snap (standing -> seated in 0.2 s) and the rider vanished behind the near wing.
Measured on today's code: the old in-out blend moved him from standing to seated in about 0.13 s of the 0.9 s hop
(the middle of `ease(u, -1.8)`), while the fly beat on the wing bones swept the near wing through him.
Now:
- `_mount_path()` (MOUNT_HOP 0.9 -> 1.05 s): step in toward the flank on the grass with a 0.12 m crouch (0-0.25),
  spring up fast to above the saddle while turning to Pegasus's facing (0.25-0.6; he rises BESIDE the flank, never
  through it), swing across and drop into the seat (0.45-0.9), settle 0.06 m (0.9-1). Event `mount_seated` t = 1.07.
- `_dismount_path()`: rise out of the seat above the back first (0-0.35), out and down beside the flank (0.2-0.85),
  land with a 0.1 m knee give (0.85-1). Same DISMOUNT_HOP (0.85 s), same events and end pose.
- WingOverlay got `hold_top`: on the mount the wings rise to the TOP of the beat over 0.35 s and STAY there until he
  sits (then the beat starts from the top, in phase with the fly clip: no jump); on arrival home the beat runs on to
  the next top and holds there through the hop off, then folds as before.
- Mount camera: the push-up during the hop 0.4 -> 1.3 m (the hop is seen a little from above).
Seen in frames (work/flight2/mount_ba.jpg, mount_after2_zoom.jpg; devlog jpeg row 3-4): the step, the spring beside
the flank and the swing over are visible in every 0.067 s frame; no frame jumps.
STILL OPEN (for the PEGASUS-CLIPS agent / the sword agent, not code here):
- At the top of the beat the NEAR wing is raised up-and-forward; from the chase camera on the mount side it covers the
  seated rider's torso for the last ~0.15 s of the mount and the ~0.35 s settle before the lift (head and legs stay
  visible). REQUEST (pegasus clips): a short Pegasus clip or pose `wings_up` (wings raised and swept BACK, tips
  behind the saddle, leading edge behind the rider's shoulders) for the mount / dismount; when it exists, home_base
  can play it on the wing bones instead of holding `fly` at t = 0 (`_make_wing_overlay` takes any clip: change the
  `"fly"` lookup there).
- The seated rider's sword arm sticking out sideways right after the mount (owner 1:39.7) comes from the `ride`
  clip / sword socket aim (sword agent / pegasus clips), not from the mount path. The rider blends from his walking
  clip into `ride` over 0.6 s while he climbs.
- There are no mount / dismount clips for the hero (only `ride`): a `mount` clip (step, spring, right leg swings over
  the back) of ~1.0 s would make the climb itself read better; the path above is timed for it (u 0-0.25 step,
  0.25-0.6 spring, 0.45-0.9 leg over, 0.9-1 settle).

## 3. Creatures on their islands (island_proxy.gd, sea_world.gd)
DECISION: in the SEA scene only (`creature_enabled`, set by sea_world; the home island's distant scenery shows none),
an island whose boss is not beaten shows that boss: the real model through `CharacterVisual.create(id)`, no
collision, no AI, no shadows. It patrols an arc of its arena: walk (`walk` / Medusa `slither`, rate 0.8) along the
arc, stop and idle 2.6 s, turn round on the spot over 1.8 s (walk clip at half rate), walk back. The arc lies to the
SIDE of the line Pegasus arrives on (from the previous island), because flying in, Pegasus covers the middle and the
near side of the island in the frame. Beaten bosses are hidden; the creature is hidden and not processed beyond
1300 m from the camera. Locked islands: the creature walks inside the storm wall (the wall hides it, as asked).
- Sizes: drawn 2.2x (Cyclops, 17.6 m), 2.4x (Medusa, 15.6 m), 1.4x (Hydra, ~20 m) their fight size so they read from
  the flight height and from ~300 m out (at 1x the Cyclops was 29 px tall from 50 m: a dot from the air). The fight
  scenes are unchanged. Patrol radii 15 / 14 / 18 m inside arenas of 30 m (Hydra centred 14 m south of the shelf
  centre, clear of the volcano).
- Checks: `--defeated=cyclops` hides the Cyclops and shows Medusa + Hydra; `--defeated=all` routes to the ending as
  before. Views: docs/devlog/media_inbox/feedback2_flight/island_creatures.jpg.
- `--no-island-creatures` (harness) turns them off for A/B.
- Frame times on the sea, `--bot=win` 14 s at 1920x1080 (perf_probe, same machine, other agents running):
  without 8.38 ms avg, p99 11.96, 4 frames > 16.7 ms; with 8.39 ms avg, p99 12.63, 2 frames > 16.7 ms. Same.
  Scene switch home -> sea unchanged (mount_seated -> scene sea 1.46 s before, 1.47 s after). VRAM +83 MB.

## Contracts
No clip names, events, sockets or flags removed. New harness flag `--no-island-creatures`. New WingOverlay fields
`hold_top` / `_held` (home_base inner class). MOUNT_HOP 0.9 -> 1.05 s (mount_seated now at t 1.07).
Bots after the change: cyclops / medusa / hydra `--bot=win --speed=3` headless = victory, victory, victory, no SCRIPT
ERROR; home -> sea -> Cyclops trip lands and starts the fight.
README line for the lead (Controls table, "In flight"): "In flight: the left stick / WASD steer (left/right turns,
up climbs, down dives); the camera follows behind Pegasus by itself (the right stick and the mouse do nothing)."
Known-limits line: "During the mount the raised near wing hides the seated rider's body for about half a second
before the lift."

## Re-fix (FLIGHT RE-FIXER, 2026-11-23 ~14:05-14:50) — reviewer findings, each checked first
Scratch: `work/flight2r/` (rider_probe.gd = the reviewer's dismount probe extended to the mount rider; trip_monitor.gd =
the reviewer's monitor with a frame every 0.5 s of the whole trip; perf_ab3.sh; bots.sh; sheets). Files changed:
home_base.gd, island_proxy.gd (pegasus_flight.gd, sea_world.gd, ending.gd untouched in this round).

1. DISMOUNT (major) — CONFIRMED (the reviewer's crops: rider hidden behind the held-up near wing 1.99-2.54 s).
   Fix: the held top is gone. At 78 % of the landing the WingOverlay plays the GLIDE wing pose (wings spread level;
   pair_check glide 0/36 hits with the rider seated, so no clipping) instead of holding `fly` at its top; it starts to
   fold into the idle at hop u 0.12 (DISMOUNT_WINGS_AT 0.5 -> 0.12, CLOSE 0.55 -> 0.45), while he rises off the back,
   and is folded before he comes down beside the flank. I did not fold before the hop as the reviewer first proposed:
   the idle folds the wings where the seated rider's legs are (manifest idle_clearance: never idle with the rider
   seated), so that would put the wing through his legs for 0.5 s.
   Result (dz/, dis_sheet.jpg, rider-centred crops of the DismountCamera every ~0.067 s, 1.83-3.03 s): head and
   torso visible in all 21 frames; at 2.49-2.56 the folding wing passes in front of his legs, head + shoulders + shield
   stay in view. dismount 2.22 -> dismount_done 3.07 (same timing as before).
2. MOUNT (major) — CONFIRMED (float-up in ~0.17 s, the held-up near wing hid him during the settle).
   Fix: the wings stay FOLDED (idle) through the step and the spring (he is beside the flank, clear of them) and
   spread LEVEL (glide wing pose) from hop u 0.55 as he swings over the back (MOUNT_WINGS_AT); at mount_seated the body
   joins `fly` from t 0.3 (wings near level, going down: MOUNT_FLY_FROM) while the spread overlay eases out over 0.65 s
   (slower than the 0.4 s body crossfade, so the wings never dip toward folded). Rider: plays `idle` for the step and
   crouch (no walk stride), `ride` starts at the spring (u 0.3, blend 0.3 s: MOUNT_RIDE_AT / MOUNT_RIDE_BLEND 0.6 ->
   0.3). Path: crouch 0.12 -> 0.2 m, rise to the seat height spread over u 0.2-0.7 (was 0.25-0.6 ease-out), swing in
   over u 0.5-0.92. Take-off camera rises 2.2 m (was 1.0) so the lift beat is seen over the near wing. MOUNT_HOP 1.05 s
   unchanged; mount_seated still at t 1.06.
   Result (mz/, mnt_sheet.jpg): rider visible in every frame from the start of the hop to the lift; ground -> seat
   height over ~0.4 s (1.43 -> 1.83), no 0.1 s jump. During the first upstroke of the lift (2.69-2.83) the near wing
   covers part of him for ~0.15 s (normal fly beat, his head/legs stay visible).
   Not used: the new `wings_up` clip (pegasus agent). It raises the wings 15 deg MORE and sweeps them forward, which is
   exactly the pose that hid the rider from the mount-side camera; the level spread does not. It stays available.
3. CREATURES (minor) — CONFIRMED (in the bot's frames they sat behind the pair / among the stones / behind the
   colonnade). First try (a short arc across the far half of the court) still hid them behind the rider and the
   columns (trip frames t 4-14). Final: Cyclops and Medusa walk a 60 deg arc on the open grass OUTSIDE the columns
   (r 36 / 37; tops are r 46 / 40), centred 69 deg off the arrival line on the near half (`off` in CREATURES); Medusa
   3.0x (was 2.4), Cyclops 2.6x (was 2.2), Hydra 1.7x (was 1.4; its arc unchanged, the reviewer said it reads; not
   re-checked in frames). Measured on the bot trips (trip_cyc.log / trip_med.log, 1920x1080 coordinates, pair centre
   at x 960): Cyclops beside the pair at x 1091-1459 from 211 m to 71 m (t 8.5-13.5, ~5 s, 76-125 px tall), clearly
   readable in frames t 9.5-11.5 (cr_zoom.jpg); Medusa beside the colonnade x 1039-1184 from ~300 m to 131 m (t 12.5-
   17.5, ~5 s), readable at t 14.5-16.5; at ~110 m she goes behind the near wing.
4. FRAME TIME (minor) — NOT CONFIRMED as a real cost. Three A/B runs each (perf_probe, sea --bot=win 14 s,
   1920x1080, one run at a time, with the new code): off avg 8.41/8.45/8.42 ms, p99 13.88/15.07/13.61, >16.7 ms 3/5/2;
   on avg 8.42/8.42/8.44, p99 14.19/14.15/15.59, >16.7 ms 6/2/7. Averages identical, spike counts overlap. Still lowered
   CREATURE_RANGE 1300 -> 900 m (beyond that they are under ~8 px), which skips them for most of each trip.
5. SIZE AT LANDING (minor) — CONFIRMED by the numbers (2.2x Cyclops beside the pair at ~50 m, then the 1x boss).
   Fix: the creature eases from its far size to 1.2x between 170 m and 55 m flat distance from the camera
   (CREATURE_NEAR_*), its walking speed follows the drawn scale (no foot slide).

Checks after the re-fix: headless `--bot=win --speed=3 --seed=11` cyclops / medusa / hydra = victory x3, 0 SCRIPT
ERROR; home -> sea -> Cyclops trip: mount_seated 2.06 (t 1.06), scene sea 3.54, ring_enter 18.49, land 18.53, fight
19.61 (as before); `--start=home --home-from=sea`: dismount 2.22, dismount_done 3.07; no SCRIPT ERROR in any windowed run.
Devlog: docs/devlog/media_inbox/feedback2_flight/dismount_refix_before_after.jpg, mount_refix_sheet.jpg,
island_creatures_refix.jpg (captions.txt).
Contracts: no clip, event, socket or flag removed or renamed; MOUNT_HOP and event times unchanged. `mount_wings` is
now emitted at hop u 0.55 (when the wings open) instead of at the mount start. `_make_wing_overlay` takes an optional
clip name (falls back to `fly`). WingOverlay `hold_top` is kept but home_base no longer sets it.
README known-limits line for the lead (replaces the one above): "During the mount and the dismount Pegasus spreads
its wings level; for about 0.15 s of the first take-off beat the near wing passes in front of the rider."
Clip requests: none needed now. A hero `mount` clip (~1.05 s: step, crouch u 0-0.3, spring, right leg over the back
u 0.3-0.9, settle) would still read better than the idle -> ride blend; the path is timed for it.
