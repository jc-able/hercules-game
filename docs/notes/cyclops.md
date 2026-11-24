# Cyclops module notes (boss builder 2026-11-22; real-model integration pass the same night)

Files: `game/scripts/bosses/cyclops.gd` (extends BossBase) and `game/scripts/world/cyclops_arena.gd` (extends ArenaBase;
unchanged in the integration pass). No class_name; the arena preloads the boss script by path.
Integration scratch: `work/cyclops_int/` (probes, logs, shots, sheets). Previous versions: `work/cyclops_int/*_before.gd`.

## Fixer pass after the play-test (2026-11-22, owner away; scratch + logs + shots `work/cyclops_fix4/`)
Both module files changed. Decisions marked **Decision**.
| Finding | Fix | Proof |
|---|---|---|
| major: the 5.5 m club passes through the camera (stuck, pull_free, death) | (1) **Near fade** (module-side, core's toon has none): `_install_near_fade()` swaps every toon/outline material of the boss and its club to a runtime copy of core's shader with `near_fade_hide/full` uniforms and a 4x4 Bayer `discard` on the view distance. Body dithers out 2.6 -> 0.9 m, club 4.6 -> 1.8 m (**Decision**: 2.6 m on the club still left its near end over the lower right of the strike frames). Same material objects, parameters copied: flash/tint/petrify unchanged; shadows unaffected. (2) **Death**: `_release_club()` lets go of the club at once (reparented to the arena, world transform kept); after 0.2 s it topples in 0.7 s (eased in) to lie on the floor, grip end to his right-back (or left-back if that is farther from the camera), sliding so the head ends >= 7.5 m from the camera and inside the ring; dust + thud + shake on landing (`event=cyclops_club_dropped`). The old club puff at 1.4 s is gone. **Decision**: did not move the stuck impact point off the camera axis (the alternative in the finding): the slam clip's two upper hands grip the club, so yawing it about one grip would pull it out of the other hand; the fade covers it | windowed seed 11 (`shots2/`, `sheet2.jpg`): strike frame shows the stuck club see-through (dither) instead of a solid third of the screen; death frames: club falls dithered, then out of view; `club_dropped ... cam_dist=7.51` in all three win runs (was 3.4 m when it pivoted in place) |
| major: skin washed out to near-white lavender | `SKIN_FACTOR` (0.76, 0.70, 0.76) on the body's albedo factor (not the club), and the arena's sky ambient 0.34 -> 0.26. Enrage tint softened to (1.0, 0.80, 0.74) since the base is darker now (with the old tint the enraged giant went maroon (118, 71, 77)) | rendered skin (windowed, fight start) median #C2A8BC / lit band (90th pct) #DDC0CD -> first factor 0.80/0.74: #B48DA5 / #C29AB1 -> final: median #AD869E, lit #BC93AB (texture median #BF92A2, sheet ~#BC9099, finding's target ~#A88DA8). Devlog `media_inbox/cyclops/qa_fix_before_after.jpg` |
| minor: quarry arena bare | Framing colonnades moved in to r 33.5-34 m (just outside the curb, ~20-25 m from the lock camera across the ring) at 1.4x (8.4 m columns, lintels and debris scaled), the NW/NE pair framing the sea at 180 deg, plus a broken lintel span leaning from the last column to the ground; two smaller colonnades at 38 m fill the gaps. Rim ruins / lone columns moved off the colonnade spans. Floor: stronger noise ramp, 18 patches (dark, dusty, reddish), 16 branching dark cracks (one flat mesh). Stepped three-tier quarry wall (288-326 deg, r 39.5-44.7) joining the south quarry face. **Decision**: not at 18-24 m from the centre as written: that is inside the 30 m fighting ring (boss and hero walk there); 18-24 m from the CAMERA is what the outside-the-curb position gives | windowed strike frame: big colonnades left and right of the giant, sea between |
| minor: enraged sweep windup 0.48 s | `ENRAGED_SWEEP_MIN` 0.55: the enraged sweep never drops under 0.55 s (slam keeps x0.8) | headless: enraged sweep windup 21.41 -> 21.95 s (0.54-0.55 at the speed-3 tick), was 0.48 |
Proof (headless `--speed=3`, logs `work/cyclops_fix4/logs/*_b.log`): bot win seed 11 victory at 36.00 s, seed 4242 victory at 32.00 s, 8 strikes, 0 hits taken each; bot lose: 4 hits, death at 20.04 s, arena rebuilt, `fight_start` again, `result=defeat`. Windowed seed 11 speed 1: victory, no SCRIPT ERROR / shader error. 0 SCRIPT ERROR / ERROR / WARNING in every log.
Requests: docs/notes/qa_requests.md "From the cyclops fixer" (core may adopt the near-fade uniforms in toon/outline; optional detach_prop helper).

## Fixer pass after integration check 2 (2026-11-22, owner away; scratch + logs `work/cyclops_fix3/`, final = `final/`)
Only `cyclops.gd` changed (`cyclops_arena.gd` untouched).
| Finding | Fix | Proof |
|---|---|---|
| minor: crack 0.42-0.45 m short of the club tip (crack z 5.63, tip z 6.08) and the club reads as lying on the ground | crack, chunks and inner dust now at the club tip (`club.global_transform * (0, 5.05, 0)`) projected to y = 0 (`_entry_point()`); `LAND_LOCAL` = that point (0.17, 0, 5.93), so the giant steers the tip onto the slam circle's centre. While stuck the GLB club node (no animation track) pivots about the grip so the tip sinks `CLUB_SINK` 0.32 m (in 0.12 s, back out over 0.2 s at pull_free, in step with the clip lifting it). The crack gets a raised earth lip (flattened torus, ~0.17 m) + 6 clods, seeded from its own RNG (Game.rng / attack pattern unchanged). The "club at rest" test is now a speed (< 1.5 m/s of game time) instead of < 0.1 m per frame, which in `--speed=0.3` windowed runs accepted the head while still settling (crack 0.2 m off) | `cyclops_stuck_pose tip_local=(0.19,-0.38,5.96) crack_local=(0.18-0.19,0,5.94-5.96)` in every stuck window (was crack 5.63 vs tip 6.08); `slam_land err` 0.02-0.03 m (rebound puffs 0.14, no crack); windowed `shot_0038/0068`: the club end disappears into the lip with the crack around it (devlog `media_inbox/cyclops/club_stuck_before_after.jpg`) |
| minor: club top cut in approach and the slam windup | `frame_top_points()` override adds the club tip and head top during the slam windup only (state slam, before impact), so the lock camera grows its arm within `CAM_LOCK_MAX_EXTRA` when needed. No `cam_max_extra()` hook exists in core yet; approach not changed (integrate_player: props stay out of the top) | windowed `--cam-debug`: windup frames lo 6.6-7.6 <= hi 7.9-8.6 (fits at arm 3.70-3.86); shots 30-32 show the whole raised club. Still cut: the first ~0.2 s of the windup (club in the rest pose at his side, shot 29) and approach (11.45 m club top) |
Proof runs (headless, `--speed=3`): bot win seed 11 victory, fight 2.40 -> 35.43 s; seed 4242 victory 2.41 -> 31.58 s; 8 strikes in 4 stuck windows, 0 hits taken each; bot lose dies at 20.05 s, arena rebuilt, `fight_start` 24.23, `result=defeat`. 0 SCRIPT ERROR / ERROR / WARNING. Windowed: `--bot=win --seed=11 --speed=0.3 --shots --cam-debug` (120 frames, sheets `sheet_a/b/e.jpg`, crops `crop_c/d/g.jpg`) and `--bot=lose` (stuck behind the hero: not useful as a look shot).
**Request for core (camera)**: a per-boss `cam_max_extra()` hook (BossBase default `Tuning.CAM_LOCK_MAX_EXTRA`), the cyclops would return ~1.5 m and could then add its club to the top in approach too, so key_cyclops.png's whole raised club is in frame at the engage distance.

## Status (integration pass, real GLB game/assets/characters/cyclops)
| Run (headless unless noted) | Result |
|---|---|
| `--start=cyclops --harness --bot=win --speed=3` seeds 11 / 4242 / 999 | victory, fight 2.4 -> 35.5 / 31.6 / 32.5 s, 8 forearm hits in 4 stuck windows, 0 damage taken |
| same with `--pad` (seed 5) | victory 31.4 s, 2 hits in every window |
| same with `--cyclops-strafe` (seed 3: the bot circles while the shadow tracks) | victory 35.5 s, club still lands 0.11-0.14 m from the circle centre |
| `--bot=lose --speed=3` | sweep 25, sweep 25, slam 45, sweep 25 -> dead at 20 s, arena rebuilt, `fight_start` again, `result=defeat` |
| windowed `--shots` (1280x720, `--speed=0.3` so frames line up with events) | real Cyclops with club, cone on the club's path, trail, circle, club in a crack, forearm strike (sheets `work/cyclops_int/sheetD/E/F.jpg`) |
0 SCRIPT ERROR / ERROR / WARNING in every headless log (`work/cyclops_int/final/`). Windowed runs that quit mid-fight
sometimes print Godot's exit line `ERROR: 1 resources still in use at exit` (not seen headless or when quitting later).

## What the real model does now (numbers measured on the GLB, `work/cyclops_int/probe_clips.gd`, boss-local +Z forward, -X = his right)
| State | Clip, playback | Timing / effect |
|---|---|---|
| approach | walk at speed 1 (1.4167 s cycle authored for 2.6 m/s, thud every 0.708 s from the `step` event 0.40); idle while turning in place | walks 2.6 m/s, turns 70 deg/s (110 inside 5 m); attacks <= 7.0 m and within 30 deg, or after 5 s if < 7.0 m and in front, or the 2 s stall break if the hero is inside the sweep arc |
| sweep | sweep x(1.31 / 0.6) = x2.18 (x2.73 enraged): the `impact` event lands on the 0.6 s / 0.48 s windup | cone decal + hit cone = the club's visible low arc: centre -37.5 deg (his right), 155 deg wide, 7.6 m (club lowest vertex < 1.9 m from -115 to +40 deg, head 6.6-7.2 m out, head radius 0.7). 25 dmg, blockable, knockback 3.5. Trail ribbon follows the real club tip (tip to 3 m down the shaft) from clip 1.06 to 1.44 s; dust wherever the tip skims below 1.3 m. Recover = rest of the clip (0.55 s) |
| slam | slam x(1.5 / 1.4) = x1.07 (x1.34 enraged) | circle r 3.4 follows the hero until 0.35 s before impact; during the whole windup he turns (<= 120 deg/s) and steps (<= 3.2 m/s, forward or back) so that his club landing point LAND_LOCAL (0.18, 0, 5.75) = club head centre at the impact frame sits on the circle centre. `slam_aim err` (predicted) 0.00-0.01 m; `slam_land err` (real club head seen in the earth vs circle centre) 0.09-0.14 m in every run. 45 dmg, guard_break. Dust ring + shockwave on the circle at impact; inner dust, earth chunks and the crack where the real club tip enters the earth (GLB node `club`, tip 5.05 m up the club, sunk 0.32 m while stuck; read once the head is at rest in the earth, <= 0.3 s). Since fixer pass 3 LAND_LOCAL = the sunk tip's floor point (0.17, 0, 5.93) |
| stuck | stuck loop at speed 1 (2 loops in 3.0 s) | club stays in the earth (tip (0.19, -0.06, 6.08)); weak point `forearm` (2 hits) sits directly on socket `forearm_ur`: (-0.47, 2.15-2.24, 1.64), inside the sword's reach (blade up to 2.9 m) -> **the stand-in clamp is dropped for the real model** (kept for the stand-in only). Radius 0.7 (glow 0.49 m on the ~0.33 m forearm). `cyclops_stuck_pose ... wp_y=2.23 in_reach=true clamped=false` |
| hurt | hurt (0.667 s, club stays in the ground) by BossBase on each forearm hit; stuck resumes after 0.6 s | |
| pull_free | pull_free x(1.5 / 0.8) = x1.875 | roar, dust at the real club head, crack fades |
| dead | death at speed 1 (falls backward, root motion: the body node does not move) | dust at the knees 1.0 s, club thud at his right (-5.9, 0, -1.3) 1.4 s, back hits the ground (0, 0, -3.2) 3.35 s with a 0.8 shake |
Pattern [sweep, sweep, slam], one sweep dropped with 25 %. Enraged: windups x0.8, 40 % of slams are double (the first
rebounds out of the earth with a 0.3 s blend, no crack, small puff, high bellow; the second re-tracks and sticks).

Lock point: on his vertical axis at upper-chest height (head socket height blended 40 % toward 0.6 x height). Before it
followed the head socket, which dips 2.5 m forward in the slam/stuck crouch, i.e. almost over the hero standing at the
forearm: the chase camera's yaw would swing. With the core lock camera (3.7 m arm, chest height) the stuck/strike
frames match key_cyclops.png: the crouched giant fills the frame right in front of the hero, hero in the lower centre.

## Two strikes in the 3.0 s window
The bot now waits REACT_DELAY 0.25 s after the club lands (a human's reaction) before running in. Measured in all six
proof runs: first hit 1.67-1.72 s, second 2.01-2.06 s after `weak_open`, about 0.95 s to spare. Earlier "one hit per
window" (assembler's run, fight 62 s) came from the old stuck clip: forearm at 2.50-2.61 m, clamped and moved onto the
club line away from where the bot aimed; the re-keyed clip (forearm 2.15-2.24 m) plus the weak point on the real socket
fixed it. A hero who rolls sideways out of the circle ends ~6 m from the forearm: roll 0.82 s + ~1.0 s run + 0.2 s
to the first active frame.

## Decisions taken with the owner away
- **Sweep shape follows the clip, not the SPEC numbers**: the task asked the arc to match the visible club path. SPEC
  150 deg x 10 m centred ahead would hit where no club passes (his left front, 7.6-10 m). Kept 25 dmg, blockable. The
  stand-in still uses Tuning (150 deg, 10 m, centred). ATTACK_ANYWAY_DIST 9.5 -> 7.0 to stay inside the 7.6 m reach.
- **No safe zone under the swing**: the shaft passes ~3 m above a hero who hugs the giant (club touches 1.9 m only from
  ~4.8 m out), but the cone still starts at his body. An inner gap would make hugging him a free answer to 2 of 3
  attacks and the telegraph cone shader has no inner radius (core). Visible mismatch only very close to him.
- Slam steering instead of "lunge when > 5.5 m": he steps back as well as forward, so the club also lands on a hero who
  stands right under him. The feet slide during these steps (the slam clip is planted); usually < 1.3 m.
- Crack position read from the real club after the impact frame (the skeleton pose lags the physics tick by a frame,
  more at --speed=3): wait until the club head is in the earth and at rest, fallback after 0.3 s to the predicted point.
- Earlier decisions still hold: double slam = rebound then a second tracked slam; red slam circle (not a dark shadow);
  boss bar name "Brontes the Quarry Giant"; stuck window stays 3.0 s after both hits; arena layout as below.
- Harness-only flag `--cyclops-strafe` (read by bot_advice): the bot circles while the slam shadow tracks, to prove the
  club steering against a moving hero.

## Bot strategy (bot_advice)
approach: hold 6 m in front of him. sweep: shield up within 9.1 m until 0.25 s after impact. slam: stand still (or circle
with `--cyclops-strafe`) while the circle tracks, then step sideways and roll when 0.04-0.33 s remain. stuck: wait 0.25 s,
run to 1.1 m outside the weak point on the boss->forearm line and attack within SWORD_REACH + 0.6 x radius. pull_free /
weak point used up: back off to 9 m.

## Arena (cyclops_arena.gd, unchanged this pass)
30 m ring of packed earth (darkened `Color(0.58, 0.42, 0.29)`, noise mottling, patches), marble curb, pale terrace to 47 m,
cliffs to the sea at -12 m, four colonnades (two framing the giant at 35 m), broken columns and drums on the rim on the
north half, statues, boulders, amphorae, quarry face of cliff_rock + cut blocks south (behind the hero's start), olive
trees and cypresses, sea stacks. Checked in the windowed shots: decals readable on the earth, centre open.

## Requests for core
1. `Tuning.CYCLOPS` keys (cyclops.gd now reads them through `_k(key, CONSTANT)`, so Tuning wins once added):
   `engage_dist 6.5, engage_angle 30.0, approach_timeout 5.0, attack_anyway_dist 7.0, close_turn_dist 5.0,
   close_turn_deg 110.0, stall_time 2.0, lunge_speed 3.2, slam_rebound 0.35, step_interval 0.65, weak_radius 0.85,
   weak_line_y 1.9`. (`slam_reach` is gone: the landing point comes from the clip.) The club-path constants
   (LAND_LOCAL, SWEEP_CENTER_DEG/ARC/REACH, death times) describe the current clips and should stay next to them.
2. (optional) telegraph.gdshader: honour `inner` in cone mode too (annular sector), if a later pass wants the sweep's
   safe zone under the shaft.

## Requests for the art track
None required. If the sweep is re-keyed, re-run `work/cyclops_int/probe_clips.gd` (and the finer `probe_sweep.gd`) and
update SWEEP_* / LAND_LOCAL / DEATH_* in cyclops.gd.

## Known gaps
- The club (top 11.45 m at rest) is cut at the top of the lock frame in approach and the first ~0.2 s of the slam windup;
  the rest of the windup now fits (frame_top_points). Needs core's cam_max_extra() hook (request above).
- Hero ~35 % of the frame height at the usual 6-7 m engage distance (reference ~53 %, hero closer): core camera; the
  stuck/strike frames are the close ones.
- Feet slide while he steps to aim the slam; no footstep dust.
- Windowed runs on this machine reach ~4 fps while other agents render (shots1 lagged); use `--speed=0.3` for shots.

## Final-check fixer pass (2026-11-23, cyclops + hydra fixer; owner away, decisions marked **Decision**)
Scratch/logs: `work/cychyd_fix/` (logs/F_*.log = final runs, shots/cyc2, sheet_cyc.jpg).
| Finding | Fix | Proof |
|---|---|---|
| death: the released club still crossed the right third of the frame for ~0.6 s under LABOR COMPLETE | `_release_club()`: let go at death start (`CLUB_DROP_DELAY` 0.2 -> 0); the lying spot is pushed along the camera -> boss line until BOTH ends are >= 7.5 m (flat) from the camera (was: head only, along head - camera); **while it topples the club's near fade is 6.0 -> 8.5 m** (`CLUB_DROP_HIDE/FULL`, via `visual.set_near_fade(.., club)`), eased back to 1.8 / 4.6 m over 0.6 s after it lands | windowed seed 1234567 shots at death +0.2 / +0.45 / landing +0.3 s: no club in frame under the card; `cyclops_club_dropped cam_dist=7.49` in all win runs |
Still open (listed, not changed): in the strike frame the stuck club fills the lower-right quarter of the frame (near end only lightly dithered at ~4 m); it does not cover the hero. A stronger stuck-time club fade would make the club in the crack read as see-through (**Decision**: keep the earlier fixer's 1.8-4.6 m).
Runs (headless `--speed=3`): win seeds 11 / 4242 / 7 = victory 35.99 / 32.00 / 33.31 s, 8 strikes in 4 openings, 0 hits; lose seed 11 = 4 hits, died 20.04 s, fight_start again, `result=defeat`. No SCRIPT ERROR / Parse Error.
