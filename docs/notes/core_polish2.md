# Core polish 2 (2026-11-23, about 08:50-09:35; owner at the Mac, no questions asked: decisions marked **Decision**)

Role: core polish fixer. Brief: the lead's task text + `docs/briefs/anim_natural.md` (the owner: "make every movement
natural"). No clip content was edited (the clips are being redone today). Nothing reads a clip length, event time or
stride as a constant: lengths come from `CharacterVisual.clip_length()`, speeds from the manifest `move_speed`.
No git writes, no imports, `builds/` untouched. Scratch, probes and logs: `work/core_polish2/`.

## Files changed
| File | Change |
|---|---|
| `game/scripts/visual/pose_fade.gd` (new) | `SkeletonModifier3D` cross-fade: from the pose ON SCREEN to the new clip's live pose, sine ease, real seconds |
| `game/scripts/visual/character_visual.gd` | `play()`: frame-clock characters (hero, Pegasus) fade through PoseFade (first modifier on the skeleton); bosses (physics clock) unchanged. New `set_socket_aim(socket, dir, weight)` + `socket_aim_weight()` |
| `game/scripts/player/player.gd` | sword carry blend (`_carry`); `_anim_loco` passes the play speed into `play()` and picks GAIT / IDLE / SETTLE blends; roll recovery settles into idle instead of holding the roll's last frame; roll / hit blends from Tuning |
| `game/scripts/world/arena_base.gd` | victory: LABOR COMPLETE waits for the fall (`_boss_screen_top()` from `live_top_points()`), upper third, event `victory_card after=<s> boss_top=<frac>` |
| `game/scripts/data/tuning.gd` | `GAIT_BLEND 0.2`, `IDLE_BLEND 0.25`, `SETTLE_BLEND 0.3`, `ROLL_BLEND 0.1`, `HIT_BLEND 0.08`, `SWORD_CARRY_*`, `VICTORY_CARD_*` (boss dictionaries not touched) |

`hercules_clips.json` socket_offsets: **not changed** (**Decision**: the carry is a runtime aim on top of the manifest
offset, so the strike/block/ride grip stays exactly as the rig agents set it).

## 1. Sword from behind (final check item 2)
**Decision:** aim the blade, not a fixed extra rotation. In idle / run / strafe / walk_back / circling the hand_r socket
is turned about the grip so the blade points along `SWORD_CARRY_DIR` (-0.55, -0.45, -0.70) in hero space (low, out to
his right, back), with weight 0.85 (15 % of the clip's own wrist swing kept), rotated with the upper twist in the
circling run. It blends out in 0.08 s for strikes, block, roll, flinch, death (the strike's active window starts at
0.20 s, so the swing is the clip's own) and back in over 0.25 s. A fixed bone-frame rotation was rejected: the hand bone
points differently in every clip (and the clips change today), an aim direction does not care.
Measured (probe `work/core_polish2/tools/carry_probe.gd`, 1280x720, blade length on screen, base -> chosen A):
| Pose | before px | after px |
|---|---|---|
| idle (free cam) | 33-36 | 124 |
| run (free cam) | 69-107 | 107-119 |
| run toward the boss (lock cam) | 142-178 | 220-237 |
| circling run (lock cam) | 185-210 | 180-193 (blade now beside him, not over the shoulder toward the boss) |
| strafe_l / strafe_r | 131 | 208 |
| walk_back | 139 | 208 |
| block / attack_1 / attack_2 | unchanged (weight 0 there) | unchanged |
Strikes unchanged: 22 strikes per campaign (keys and pad), 3 / 7 glances, the same counts as the final check logs.
Variants B (down-back), C (up over the shoulder), D (out-down) are in `docs/devlog/media_inbox/core_polish2/sword_carry_variants.jpg`.

## 2. Victory card (final check item 11)
Card in the upper third (lighter dim, like DEFEATED). It fades in when the boss's highest live point is below 30 % of
the screen height, or when the top has stopped falling while already below 18 %, never before 0.6 s and at the latest at
0.8 x the death clip's length (capped 4 s). Then 2.8 s hold, then the sea. A first try with "stopped falling" alone
fired while the Cyclops kneels (card over his head at 1.35 s): the low gate fixed it.
| Boss | before | after (windowed, seed 11) | headless campaign |
|---|---|---|---|
| Cyclops | card at 0 s over the falling body | 2.95 s, top 0.32 (he lies on his back below the card) | 2.45 s |
| Medusa | 0 s | 1.30 s, top 0.30 | 0.80-0.90 s |
| Hydra | 0 s | 2.35 s, top 0.32 | 2.50 s |
Scene time after a victory grows from 4.0 s to card delay + 2.8 s (cyclops scene in the campaign 40.2 -> 42.4 s).
DEFEATED path untouched (cyclops --bot=lose: defeat, restart at 25.77 s, fight_start again 26.78 s).

## 3. Hero transitions
Probe `work/core_polish2/tools/trans_probe.gd` (test arena, locked on, real input actions; movie `--write-movie
--fixed-fps 30`): idle<->run, side-step, into/out of the circling run, run<->walk_back, three rolls, attack_1 ->
attack_2 -> idle, attack_1 -> idle, block in/out (standing and running), flinch (standing and running). Metric: the
largest bone turn between two rendered frames (deg/frame at 30 fps); after = one BoneAttachment3D per bone (final pose,
after the modifiers); before = skeleton poses (no modifier was active outside the circling run).

**Root causes found**
1. The AnimationPlayer's cross-fade runs on the scaled clock: `_anim_loco` played the clip at speed 1 and set 2.5x right
   after, so a 0.15 s blend into the side-step lasted 0.06 s = a one-frame snap.
2. A cross-fade started while another one was running cut the older clip's weight in one frame (roll -> side-step).
   `play_with_capture()` did not fade skeleton tracks in 4.7.2 (tested), hence the own skeleton fade.
3. The roll clip ended 0.12 s before the state did: the hero froze for 4 frames, then started the next clip.

| Change of clip | before (deg/frame, worst frame) | after |
|---|---|---|
| idle -> side-step | 156 (shield forearm, 1 frame) | 39 |
| side-step -> idle | 32 | 32 (spread) |
| side-step -> circling run | 59 | 50 |
| run -> walk_back | 166 (sword hand, 1 frame) | 51 |
| walk_back -> run | 78 | 52 |
| roll -> side-step | 155 | 39 |
| roll end | 4 frozen frames | 0-1 (settles into idle during the recovery) |
| run -> roll | 104 | 78 (the roll's own motion) |
| run -> flinch | 105 | 60 (the flinch's own head snap) |
| run -> block | 63 | 46 |
| block_end -> run | 55 | 19 |
| attack_1 -> attack_2 | 102-111 | 102-111 (inside the attack clips at 2.3x: clip content) |
| Frames > 60 deg/frame outside the attack and roll clips | 13 | 3 (the hit clip's own head snap) |
For reference the run's own legs turn 35-40 deg/frame at the circling speed.
Home island (`--probe-home`): idle -> free run -> idle, a turn, walking to Pegasus and mounting: worst 39 deg/frame,
no spike over 60. The mount rider is a second visual (home_base.gd); its 0.25 s ride fade is now real seconds.
Strips: `docs/devlog/media_inbox/core_polish2/transitions_before_after.jpg`.

**Left to the clip redo (not fixable by blends):** `idle` and `block_idle` barely move (median 0.1-0.2 deg/frame; 28-30
frozen frames holding the shield); `strafe_r` holds the shield forearm rolled 168 deg from idle and `walk_back` the sword
hand ~166 deg: the fades now spread it over 0.2 s, but the shield still visibly rolls on every side-step.

## 4. Regression (headless, --speed=3, all exit as expected, 0 SCRIPT ERROR / Parse Error in every log)
| Run | Result | Fight | strikes / glances / hits |
|---|---|---|---|
| cyclops win seed 11 / 4242 | victory / victory | 33.9 / 29.8 s | 8/0/0, 8/0/0 (blocks 8 / 6) |
| medusa win seed 11 / 4242 | victory / victory | 23.8 / 22.9 s | 6/0/0, 6 reflects each |
| hydra win seed 11 / 4242 | victory / victory | 97.0 / 97.0 s | 8/6/0, 8/5/0 |
| cyclops --bot=lose | defeat, restart, fight again | died 21.09 s | 4 hits |
| --campaign --keys | victory | cyclops 34.0 s | 22 strikes, 3 glances, 0 hits |
| --campaign --pad | victory | cyclops 34.0 s | 22 strikes, 7 glances, 0 hits |
| --probe=ui | quit (menu probe passed) | - | - |
Note: at 08:55 a cyclops run failed to load because `bosses/cyclops.gd` was mid-edit by its fixer (`_walking` not
declared); it compiled again for every run above.

## Requests
- home_base.gd owner (world): optional, at the mount the rider visual starts from its own idle; for a seamless hop it
  could start where the walking hero is. A `CharacterVisual.copy_pose_from()` is not written yet; ask core if wanted.
- Clip redo team: see "Left to the clip redo" above (idle, block_idle frozen; strafe_r forearm and walk_back hand roll).
- Lead: rebuild the app at the end (not done by me).

## Re-fix after the independent review (2026-11-23, about 09:15-09:45; core polish re-fixer)
Scratch: `work/core_refix/` (probe = the reviewer's `sword_probe.gd`, headless `--fixed-fps 30`, cyclops seed 11; logs
`logs/before.log` / `logs/after3.log`, table script `tools/an.py`; windowed movie `after.avi`, movie frame = [F] + 74).
All four findings were checked against the reviewer's log and re-measured before any change: all four were right.

| Finding | Change | Before -> after (deg per frame at 30 fps, worst frame of the change) |
|---|---|---|
| Sword carry blends out in 0.08 s | `Tuning.SWORD_CARRY_OUT_STRIKE` 0.16 (capped at 85 % of the strike's active_start read from the clip), `SWORD_CARRY_OUT` 0.25 for block, roll, flinch, death. `CharacterVisual.set_socket_aim`: a falling weight LATCHES the correction in the hand bone's frame, so the blade rides with the hand and unwinds evenly | shield raise 64 -> 42 (arm itself 36); flinch 49 -> 18; strike start see next row |
| (found while fixing) | Only the longer blend-out made the strike WORSE (run -> attack_1 131 deg/frame): the live re-aim's shortest arc flipped while the wind-up swung the blade past the carry direction. The latch fixed the flip; the rest was the 0.06 s (2-frame) cross-fade into attack_1. New `Tuning.ATTACK_BLEND` 0.1 for the first strike (attack_1 -> attack_2 keeps 0.06); it ends long before the active window | run -> attack_1 sword 112 / 72 / 63 -> 42 / 57 / 68 / 63; circling -> attack_1 105 / 57 / 54 -> 40 / 54 / 56 / 52. Arm bones peak 52 (the clip's own wind-up) |
| Body yaw spins 85 deg in 3 frames | `player.gd _turn_visual()`: the visual yaw accelerates (`VIS_TURN_ACCEL` 9000 deg/s2) and brakes onto the target; top speed `VIS_TURN_DEG` 900 in locomotion, `VIS_TURN_ATTACK_DEG` 600 into a strike and for `VIS_TURN_ATTACK_AFTER` 0.4 s after it. The upper twist now unwinds WITH the hips (follows -yaw x CIRCLE_TWIST while that is smaller) instead of dropping on its own | circling -> strike yaw -85 -80 -60 -40 -20 -2.5 0 (was -85 -55 -25 0), done in 0.17 s, before active_start; back into the circling run 0 -25 -45 -65 -82.5 -85 (was 0 -30 -60 -85); twist 16.7 -> 11 deg/frame. Circle reversal right -> left: 7 frames with ease in/out (was 6 at a constant 30). No oscillation (0 sign flips in the yaw steps) |
| Roll with the stick held: roll -> idle -> run | `_tick_roll`: at the roll's end the clip the held stick asks for (`_held_loco_clip()`: run / strafe / walk_back, the same choice as `_tick_free`) with GAIT_BLEND; idle + SETTLE_BLEND only with no input. `_set_state(&"idle")` keeps a locomotion clip that already plays (no restart) | roll -> run directly (F515), no idle in between; yaw step at the end 30 -> 7.5 |
| Boss bar stays under LABOR COMPLETE | `arena_base._on_boss_defeated`: `hud.set_boss_visible(false)` when the card fades in (the DEFEATED path's call) | headless medusa win: bar + reticle visible at victory, hidden at the card (t 27.32 s). Card timing unchanged: cyclops 2.50 s / top 0.34, medusa 0.90 / 0.30, hydra 2.50 / 0.32 |

**Decision:** the strike start stays above the reviewer's 60 deg/frame target by 8 deg in one frame (68, run -> attack_1).
The blade has to be fully back in the clip's grip by 85 % of active_start (the hit capsule follows the socket), so about
115 deg of carry correction must unwind in 4-5 frames while the clip's own wind-up turns the hand 25-52 deg per frame.
From the chase camera the blade is in front of his body there (strip `refix_transitions_after.jpg`, row 2).

**Note for whoever reads `_vis_yaw`:** the sword hit capsule follows the socket, so the visual yaw is NOT only the
picture during a strike: it now reaches 0 at about 0.17 s (before: 0.1 s), before active_start (0.18-0.20 s).

### Regression (headless, --speed=3; `work/core_refix/logs/r_*.log`; 0 SCRIPT ERROR / Parse Error in every log)
| Run | Result | strikes / glances / hits | reviewer's run (same code minus this re-fix) |
|---|---|---|---|
| cyclops win seed 11 / 777 | victory / victory (35.1 / 30.0 s) | 8/0/0, 8/0/0 | 8/0/0, 8/0/0 (33.9 / 29.9 s) |
| medusa win seed 11 / 777 | victory / victory (23.8 / 24.5 s) | 6/0/0, 6/0/0 | same |
| hydra win seed 11 / 777 | victory / victory (97.0 / 97.0 s) | 8/6/0, 8/7/0 | 8/6/0, 8/5/0 |
| cyclops --bot=lose | defeat 21.08 s, restart 25.76, fight again 26.77 (exit 1 = defeat, as before) | 4 hits | same |
| --campaign --keys / --pad | victory / victory | 22 str., 4 / 5 glances | 22 str., 3 / 5 (first fixer's pad run: 7) |
| --probe=ui | quit (passed) | - | - |
Glance counts move by 1-2 between runs of the same code (bot timing; the boss modules are being edited today).

### Devlog
`docs/devlog/media_inbox/core_polish2/refix_strike_before.jpg`, `refix_roll_before.jpg` (the reviewer's strips) and
`refix_transitions_after.jpg` (30 fps frames: circling strike, run strike, shield raise, roll into the run).

### Still not right (left as it is)
- Strike start: 68 deg/frame in one frame (above).
- The roll itself snaps the body to the roll line in one frame (`_start_roll` sets `_vis_yaw` directly; unchanged, the
  roll clip starts in a crouch so it reads as the dive).
- Clip content (idle / block_idle frozen, strafe_r forearm roll, walk_back hand roll) waits for today's clip redo.
