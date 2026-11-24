# Hero integrator 2 (2026-11-23, about 10:40-11:20; owner at the Mac, not asked: decisions marked **Decision**)

Role: HERO integrator after the natural-animation pass (new hercules idle 6.0 s, run 0.6667 s / move_speed 4.59, every
one-shot re-based on the natural stance; animfix_hercules re-fix). No GLB or manifest edit (none was needed: no hero
event time or move_speed is wrong). No import, no git writes, builds/ untouched. Every rendering run went through
`tools/godot_bg/gdwin`. Scratch, probes, logs, movies, strips: `work/integrate2_hero/`.

## Files changed
| File | Change |
|---|---|
| `game/scripts/bosses/boss_base.gd` | new `strike_point(from: Vector3) -> Vector3` (default `global_position`): the point a locked-on hero faces. Hydra already overrides it (jaw lying within 4 m) |
| `game/scripts/player/player.gd` | `_face_lock` aims at `lock_target.strike_point(global_position)`; a jump of more than `LOCK_FACE_SNAP_DEG` in one frame (jaw goes down beside him, a new lock) turns at `LOCK_FACE_JUMP_DEG` instead of snapping the body. `_tick_attack`: attack_1's recovery eased (below) |
| `game/scripts/data/tuning.gd` (hero part only) | `LOCK_FACE_SNAP_DEG 12`, `LOCK_FACE_JUMP_DEG 540`, `ATTACK_RECOVER_SPEED 1.3` |

## attack_1 recovery (the one real pop found)
attack_1 is 1.25 s and plays in 0.55 s (x2.27). Its new recovery (0.917-1.25 clip s: sword back to the stance, a step
back) then took 0.147 s: the sword arm dropped in 3 frames (53 / 58 / 43 deg per frame at 30 fps) and stopped dead in
the idle (0.6). **Decision:** past the chain point with no chain buffered, the rest of attack_1 plays at 1.3x and
finishes under `_hold_until` after control returns at 0.55 s (exactly as block_end does; any move or action cuts it with
SETTLE_BLEND). Gameplay timing is unchanged (state, active window, chain window, control all as before).
Measured (same probe, same frames): recovery 44 / 23 / 8 / 10 / 24 / 32 / 34 / 33 / 29 / 23 / 14 / 0 deg/frame over
0.37 s (was 53 / 58 / 43 / 0.6 over 0.1 s). Strip: `docs/devlog/media_inbox/integrate2_hero/attack_recovery_ba.jpg`.

## How it was looked at
`work/integrate2_hero/tools/trans_probe.gd` (core_polish2's transition probe, extended: 3 s idle, 1.5 s run, 2.5 s
circling, then petrify and death), cyclops arena with the boss stopped, 1280x720, `--write-movie --fixed-fps 30`
(`movie/trans.avi` before the recovery fix, `trans2.avi` after); home island idle + free run (`--probe-home`,
`movie/home.avi`). Per-frame largest bone turn (BoneAttachment3D per bone = final pose after fade / twist / aim):
`python3 tools/trans_an.py logs/trans2.log 45`. Strips (`tools/strip.py`): `strips/s1_idle_run.jpg` (idle, run,
circling), `s2_moves.jpg` (strafe, walk_back, three rolls), `s3_actions.jpg` (attacks, block, hit, petrify, death),
`home_idle.jpg`.

| State / change | Result (deg/frame at 30 fps, worst frame) | Look |
|---|---|---|
| idle (6.0 s) | median 0.5, never a frozen run of frames | relaxed, sword low right, head turns; first thing on the home island: fine |
| run (free x1.31, locked x1.0 = 4.6 / 4.59) | median 19.8, p95 36.5 | arms pump, feet under the hips, playback = ground speed / move_speed (no skating; GLB re-measure 4.71 = 2.6 % off, < 1 cm per frame) |
| circling run + twist | twist 46.8 deg as before | back to the camera, shield as a disc on his left, blade out right: the twist reads on the new run |
| idle -> run / run -> idle | 26 / 28 | eased (GAIT 0.2 / IDLE 0.25) |
| idle -> strafe -> circling | 37 / 38 | |
| run -> walk_back / back -> run | 52 / 48 (sword hand, carry + clip) | spread over 4 frames, no pop |
| rolls (back, side, from run) | clip content 60-74 (head, arms: the body rolls) | roll -> held gait / idle: 38 then settles, no freeze |
| attack_1 -> attack_2 | 102-113 inside the clips at x2.27 (the swing itself) | blade crosses the target: strikes register (below) |
| attack_2 -> idle | 35, 28, 0 | |
| block start / idle / end | 34 / 1 / 35 (see clip_problems: block_end) | shield up in front, then back to the side |
| hit, hit while running | 36 (head, the flinch) | |
| petrify | 0 for 1.5 s (a statue, as meant), then idle resumes | |
| death | 35 at the start, falls, props drop | |

## Sword and shield from behind
- The sword carry aim (core_polish2) acts only on `hand_r`; `forearm_l` has no aim: nothing is doubled. One sword,
  one shield in every frame looked at.
- Sword: idle, run, circling: low and out to his right, clearly readable. Strikes and block: the clip's own grip
  (carry weight 0 there).
- Shield: run and circling show it as a disc on his left. Idle (natural stance, forearm v2 twist -62 deg): it hangs at
  his side and from straight behind reads as a vertical plank (edge-on, rim visible). **Decision:** left as it is. It
  reads as a shield held at rest, and turning it ~35-45 deg face-back (a runtime socket turn) puts the rear rim into the
  hip/skirt per animfix_hercules' mesh check; a disc from behind needs the arm further out = clip work (lead's call).

## Regression (headless, --speed=3; `work/integrate2_hero/logs/r_*.log`)
0 SCRIPT ERROR / Parse Error in every run of the hero code. Runs marked * started after the attack_1 recovery change
(the others carry only the strike_point change; the recovery change touches no game timing).
| Run | Result | strikes / glances / player hits |
|---|---|---|
| cyclops win seed 11 / 777 | victory / victory (boss down 37.6 / 32.4 s) | 8/0/0 (8 blocks), 8/0/0 (6 blocks) |
| medusa win seed 11 / 777 | victory / victory (26.2 / 26.9 s) | 6/0/0, 6/0/0 (3 reflects each) |
| hydra win seed 11 | first try: did not load: `hydra.gd:459` called `_is_walk_clip()` / `_start_turn_walk()` while the hydra integrator was mid-edit (not hero code); re-run * victory 99.3 s | 8/5/0 |
| hydra win seed 777 | victory 99.4 s | 8/5/0 (as before: 8/5-7/0) |
| cyclops --bot=lose | died 21.09 s, fight again 26.78 s (exit 1 = defeat, as before) | 4 hits |
| --campaign --pad / --keys * | victory / victory (hydra down 245.8 s) | 22 / 5 / 0, 22 / 4 / 0 |
| --probe=ui | quit (passed) | - |
The Hydra strikes did not change with `strike_point` (8/5/0 both seeds): the bot already stands at the jaw.

## Left for others
- block_end (clip): see the final answer's clip_problems (the arm ends at full speed, 35 / 29 deg per frame, then stops).
- Idle shield edge-on from behind: lead's look call (above).
- walk_back plays at 2.0x (2.4 / 1.2 m/s): a 0.25 s stride cycle, quick but not sliding (unchanged from before).
