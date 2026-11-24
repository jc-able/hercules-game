# Feedback 2: the sword hold ("he has his hands like backwards") - sword fixer, 2026-11-23

Scratch: `work/sword/` (probes `hand_probe.gd` = hand close-ups of every clip front/side/back + chase view, `--carry`
applies the game's carry; `ride_probe.gd` = rider on Pegasus fly/glide from the side, behind, 3/4; `sword_probe.gd` +
`an.py` = the core_refix transition probe; `grip_calc.py` = socket offset from a grip axis; logs in `work/sword/logs/`).
Devlog: `docs/devlog/media_inbox/feedback2_sword/sword_grip_before_after.jpg` (+ captions.txt).

## The real cause (measured, not guessed)
- The clips pose the sword hand with the KNUCKLES FORWARD and the thumb toward the body (idle: hand bone X = out,
  Z = forward; thumb at hand-frame -X found from the skinned mesh, palm/curled fingers at -Z; marker render
  `work/sword/markers.jpg`).
- The old socket ran the grip along the fingers: blade in the hand frame (0.26, 0.72, 0.64), i.e. out through the
  knuckles / finger tips, never through the fist.
- The run-time carry (core_polish2, `SWORD_CARRY_DIR` (-0.55, -0.45, -0.70)) then turned the SWORD inside the hand
  ~100 deg so the blade pointed back and out: blade on the little-finger side of an open-looking hand = the owner's
  "backwards". On the horse (no carry) the ride clip left the blade pointing straight back (0.13, 0.08, -0.99), into
  the flank / across the thigh.
- The sword model itself is fine (blade +Y, flat normal X, grip y -0.03..0.12, guard 0.12-0.14).

## The fix
1. `hercules_clips.json` `socket_offsets.hand_r` = the grip THROUGH the closed fist along the knuckle line, blade out
   of the thumb side: hand-frame blade (-0.95, 0.30, 0) (diagonal across the palm), flat normal = palm normal, fist
   centre (-0.045, 0.105, -0.035) -> loc (-0.0021, 0.0914, -0.035), rot_deg (-17.53, -90, 0) (offset_space blender;
   `work/sword/grip_calc.py -0.95 0.3 0 -0.045 0.105 -0.035`). **Keep on manifest rebuilds.**
2. New manifest block `grip_fix` {socket hand_r, bone hand_r, forearm forearm_r, authored_offset = the OLD hand_r
   offset (loc -0.0086 0.1173 0.0093, rot -1.33 -50.27 -108.11), forearm_share 0.45, swing_max_deg 40,
   clip_dirs {ride: (-0.40, -0.30, 0.87)}}. **Keep on manifest rebuilds.**
3. New `game/scripts/visual/grip_fix.gd` (SkeletonModifier3D, last modifier): every frame it turns the HAND round the
   grip: a forearm twist shared 45 % forearm / 55 % hand, then a wrist bend up to 40 deg, so the blade points
   - in strikes, block, roll, hit, death: exactly where the clip was keyed with the old socket (target = hand pose x
     authored_offset blade; residual 0 deg in every pose of attack_1/2, block, roll, hit, death) -> the swing and the
     hit capsule (`SwordHitbox.follow`, real blade) are the clip's own; only the grip point moves a few cm;
   - in the carry (idle, run, strafe, walk_back, circling run): along `Tuning.SWORD_CARRY_DIR`, weighted as before;
   - on Pegasus (ride clip, no player): along clip_dirs.ride: forward and down beside the leg, outside the flank.
   The twist is unwrapped against the last frame and rate-limited (720 deg/s, max 230 deg) so it never flips.
4. `CharacterVisual`: `attach_prop()` makes the GripFix when the manifest has `grip_fix` for that socket (the player,
   the home rider and the flight rider all get it with no change in their files); `set_socket_aim(hand_r, ...)` feeds
   the GripFix (carry dir + weight) instead of turning the sword in the hand; `set_upper_twist()` keeps the GripFix last.
   `socket_aim_weight(hand_r)` now returns 0 (only probes read it).
5. `Tuning.SWORD_CARRY_DIR` (-0.55, -0.45, -0.70) -> (-0.36, -0.55, 0.75): forward, ~34 deg below horizontal, ~25 deg out.

## Numbers
- Idle blade (hero space): (-0.60, -0.57, -0.56) back/out -> (-0.38, -0.59, 0.72) forward-down. Run (-0.33, -0.55,
  0.77) and swings with the arm (15 % of the clip's own swing kept, as before). Ride (0.13, 0.08, -0.99) straight back
  -> (-0.40, -0.30, 0.87) (residual 4-10 deg).
- walk_back: the clip's arm is raised forward; the carry reaches its target within 21-31 deg (blade forward across
  the body, through a closed fist). Not a hit clip.
- Transition probe (cyclops seed 11, 30 fps, worst sword turn per frame in the 9 frames after a clip change,
  before -> after): idle->run 21 -> 6, run->idle 50 -> 13, run->attack_1 68 -> 59, attack_1->attack_2 111 -> 104
  (the clip's own), attack->idle 67 -> 36, block_end 53 -> 23, idle after block 38 -> 4; WORSE: idle->walk_back
  32 -> 53, walk_back->idle 25 -> 45, idle->strafe 17 -> 39, run->roll 56 -> 63 (the hand turns ~150 deg between
  those clips' hand poses over the 0.2 s gait blend; rate-limited, no flips). Logs `work/sword/logs/probe2_an.txt`.
- Bots (headless, --speed=3, seed 11, final code): cyclops / medusa / hydra victory at 37.58 / 26.21 / 99.35 s
  (this morning's core_refix runs: 37.54 / 26.20 / 99.37 s, so the hits are unchanged), 0 SCRIPT ERROR; campaign
  (title -> ending -> sea) victory, 0 SCRIPT ERROR.

## Looked at
- Close-ups every clip front/side/back before/after: `work/sword/before*/`, `work/sword/after3/`, sheet
  `work/sword/ba_check.jpg`: closed fist, pommel below the little finger, blade out of the thumb side.
- Game camera (gdwin 1280x720, cyclops --bot=win, home -> flight): `work/sword/crops1.jpg`: from behind the blade
  hangs forward-down beside the right leg, visible. Rider on Pegasus: `work/sword/ride_after.jpg`: blade forward-down
  at the hip, outside the flank and the thigh.

## Left / for others
- The shield and the other clips are unchanged. The mount/dismount and flight agents own the rider's placement;
  the rider's sword direction comes from `grip_fix.clip_dirs.ride` in the manifest (hero space) if they need to change it.
- If a clip is re-keyed with the hand already in a proper grip, set its blade via authored_offset (or drop grip_fix).

## Re-fix after the review (sword re-fixer, 2026-11-23) — scratch `work/sword2/`
All three findings checked first and reproduced (edge_probe on the current tree: f13 lead 0.44, EW 0.48; mount_probe:
28.5 / 20.9 deg; run spread ~4 deg). Fixed:
1. **Edge leads the reach strike.** New optional manifest keys in `grip_fix`: `clip_roll_deg {attack_1: 25}` and
   `clip_roll_from {attack_1: 0.4}` (clip s, just before active_start 0.458). `grip_fix.gd` rolls the hand about the
   blade's OWN LINE THROUGH THE GRIP (`grip_local` = socket origin in the hand frame) after the twist, eased at
   400 deg/s, so the blade line and the hit capsule are unchanged (tip speeds identical frame for frame). The first try
   (roll about the hand origin, from the clip start) made the wind-up worse (f5 0.55 -> 0.86): replaced.
   edge_probe (cyclops seed 11, 30 fps), attack_1 lead f9/f10/f11/f12/f13: 0.98/0.86/0.32/0.26/0.44 -> 0.92/0.56/0.11/0.64/0.02;
   weighted EW for the 2-hit combo 0.48 -> 0.44 (wind-up and attack_2 unchanged). **The review's acceptance "f11-f13 all
   < 0.2" cannot be met by any constant roll:** the signed flat angles at f11/f12/f13 are -18.5/+15.1/-26.1 deg (the
   flat wobbles across the motion frame to frame, `work/sword2/logs/edge_s0.log`), a 41 deg spread, so the best
   constant roll leaves >= 20.6 deg (0.35) on one frame. 25 deg puts the fastest frame (43 m/s) edge-on and f12 (25 m/s,
   after active_end) at 0.64. A per-frame keyed roll would be a clip re-key (not done: small details only).
2. **No sword pop at the mount.** `CharacterVisual._make_grip_fix` seeds a new hero visual's GripFix from the
   "player" group's visual (`copy_grip_state` -> `GripFix.copy_state`: carry dir/weight, and the twist if it then
   plays the same clip), so the home mount rider starts with the walking hero's sword; `clip_dirs` (the rider's `ride`)
   now eases in/out over `grip_fix.clip_dir_blend` 0.4 s (smoothstep), settled at once if the visual starts in that
   clip (flight rider, arrival rider). No change in home_base.gd. mount_probe: rider first frames 28.5 / 20.9 ->
   2.7 / 0.7 deg, max 2.9 deg per frame through the mount (`work/sword2/logs/mount.log`).
3. **The run swings the blade.** `Tuning.SWORD_CARRY_WEIGHT_RUN` 0.6; player.gd blends the carry weight 0.85 ->
   0.6 by ground speed / RUN_SPEED. Run cycle (home bot, every frame): blade spread 4 -> 15.7 deg, y -0.59..-0.35,
   z >= 0.76 (always forward of the hip). Game camera (`work/sword2/four.jpg`): forward-down by the right leg, visible.
Looked at: attack_1 hand close-ups front/side/back with and without the roll (`work/sword2/hp_sheet.jpg`, hp0/ vs hp/):
closed fist, blade out of the thumb side, no visible wrist break. Devlog: `docs/devlog/media_inbox/feedback2_sword2/`.
- Bots after the re-fix (headless --speed=3 seed 11, final code, full tree): cyclops 37.62 s, medusa 26.22 s, hydra 99.10 s, all victory, 0 SCRIPT ERROR; quit-after 2 clean; home --bot=win (mount -> flight) 0 SCRIPT ERROR.
