# Cyclops integration 2: today's natural clips in the fight (cyclops integrator, 2026-11-23 ~10:30-11:10)

The owner was at the Mac: every render went through `tools/godot_bg/gdwin` (off-screen, no focus, silent), with HOME =
`work/integrate2_cyclops/home`. No import, no git, builds/ not touched. Scratch, logs, movies, sheets: `work/integrate2_cyclops/`.

## Files changed
- `game/assets/characters/cyclops/cyclops_clips.json`: walk `events` `{"step": 0.4}` -> `{"step_r": 0.4167, "step_l": 1.125}`
  plus an `events_note` (the only data edit allowed: event times of my own character). Backup: `work/integrate2_cyclops/cyclops_clips.before.json`.
- Mirrored in `art_src/chars/cyclops/clips/walk_n/keys_walk.json` (`events`, `note_integrate2`) and in
  `art_src/chars/cyclops/clips/walk_n/action_walk.json` (`events`, `spec.events`, `note_integrate2`: merge reads this file).
  Backups next to the manifest backup.
- `game/scripts/bosses/cyclops.gd`: new `cam_fit_points()` (see 3). No Tuning change, no arena change.

## 1. The fight in motion with the new clips
Movies (30 fps, chase camera, gdwin): `movie/fight_win11.avi` (bot win, seed 11, before my changes), `movie/gait.avi`
(`work/cyclops_polish2/refix/gait_probe2.gd`: hero put 150 deg behind him -> turn on the spot), `movie/fight_4242_after.avi`
(bot win seed 4242 with `--after-victory=3`: death, LABOR COMPLETE). Sheets in `sheets/` (A idle+approach, B sweep, C/F slam,
D stuck+pull_free, E turn, G death, H slam after, I pull_free at 15 fps). Image reads: 11.

| Thing | Measured | Verdict |
|---|---|---|
| Idle at the start (0-2.4 s) | idle 6.0 s loop, club on the shoulder | reads as a standing giant; from the start camera he is ~24 m away |
| Walk playback | ground 2.6 / manifest move_speed 2.54 = **1.02x** (log rate 1.02) | feet planted; human probe [SLIDE] **16-18 of 1149-1151** moving walk ticks > 30 % off (1.4-1.6 %), mean error 0.02 |
| Turn on the spot | 70 deg/s -> walk **0.58x** (turn_step_ref 120) | he steps while turning (legs lift in sheet E), no turntable |
| Footfalls | GLB lowest foot vertex reaches the floor: right **0.4167 s** (frame 10), left **1.125 s** (frame 27); old beats were 0.40 and 0.40 + 0.708 = 1.108 | now one event per foot at the contact (17 ms later than before for both feet; the old 0.17 s error was the OLD walk) |
| idle <-> walk | idle f0 vs walk f0: max joint 0.447 m, mean 0.151 m (walk f0 is the closest walk frame to the stance: every other frame 0.5-1.77 m) | the walk always starts at frame 0 (play restarts it), so the 0.3 s loco_blend is the best case; kept |
| Sweep | impact 1.31 at 2.18x (0.6 s windup), ends on idle f0 | no pop; the club arc and the cone decal agree; ends back on the shoulder |
| Slam | impact 1.5; `slam_aim` err **0.00 m**; `slam_land` err **0.04-0.14 m** (seeds 11/4242/7); stuck pose report: crack local (0.18, 5.99) vs LAND_LOCAL (0.17, 5.93) | the club still lands on the circle; LAND_LOCAL kept |
| Stuck / weak point | forearm `wp_y` 2.18 m, `in_reach=true` in every stuck window | reachable |
| Pull_free | clip 1.5 s played in 0.8 s (1.875x) | readable heave; the over-swing is fast (clip problem below) |
| Death | backward fall (head z -4.7 m, spine_03 z -3.0 m at 4.0 s; DEATH_BODY (0, 0, -3.2) still right), club let go at once, dropped 8.3-8.5 m from the camera | as before |

Decision (not changed): an attack that starts mid-stride cross-fades from the walk phase it is in (0.22 s, the body's
momentum dies over 0.2 s); waiting for a "feet together" phase would delay every attack up to 0.35 s and change the warning
rhythm. The 1-2 tick walk blip when `approach` gives way to an attack at once (sweep -> approach -> sweep in 0.04 s) carries
~13 % walk weight for 2 ticks = ~6 cm: invisible, left as is.

## 2. Today's polish still holds with the new poses
- Stuck club framing (`work/cyclops_polish2/refix/club_probe2.gd`, seed 11, 4 forearm hits): club visible 0.605 / 0.487 / 0.630 /
  0.390 of its silhouette (target >= 0.3), lower-right quarter 0.294 / 0.246 / 0.304 / 0.202, **mean 0.261** (polish2: 0.260),
  club near point 3.41-3.67 m from the camera, weak point on screen 4/4, club shadow off while faded. Unchanged: the stuck clip
  keeps the club pinned to k00_stuck (club lowest -0.656 every frame).
- Curb near fade: arena code only, not touched by the clips; the lose run (DEFEATED view) is unchanged (player_died 21.07-21.09 s).
- Club on the shoulder vs near fade: the club keeps CLUB_NEAR 1.8-4.6 m; in the walk/approach frames the shoulder club never
  comes close to the chase camera (behind the hero, the giant >= 5 m away).
- Camera top points: the lock camera frames a real visual by its live BODY top points (props such as the club are left out),
  so the club on the shoulder does not change the framing.

## 3. Found: the raised slam club was never a camera point for the real model
`frame_top_points()` (club tip + head during the slam windup) is read by PlayerCamera only for a stand-in: for a real visual
`_boss_tops()` uses `CharacterVisual.live_top_points()`. Added `cam_fit_points()` (the hook Medusa uses) returning the same two
points during the windup. Measured effect: none at the usual slam distance (hero 5-7 m, `cut_inside` 6 m stops the arm, the
feet limit already holds the tilt: sheets F vs H identical); it only lets the arm grow when the hero is farther than ~6 m (as the
original comment intended). The raised club is cut by the top of the frame in the windup at the usual distance: a camera rule
(integrate_player: top cut inside ~6 m), not changed here.

## 4. Regression (headless, --speed=3; logs `work/integrate2_cyclops/logs/a` before, `logs/b` after)
| Run | before (a) | after (b) |
|---|---|---|
| win seed 11 | victory 37.62 s | victory 37.60 s |
| win seed 4242 | 33.05 s | 33.07 s |
| win seed 7 | 34.46 s | 34.49 s |
| lose seed 11 | player_died 21.07 s, defeat | 21.09 s, defeat |
| human probe 11 / 7 | [SLAM] 9.5 deg, 1.02 m; [SLIDE] 18/1151 | [SLAM] 8.7 deg, 0.79 m; [SLIDE] 16/1149 |
0 SCRIPT ERROR / Parse Error in every log. slam_aim err 0.00, slam_land err 0.04-0.14 m, every stuck window in_reach=true.
(The human probe takes camera-relative inputs, so the footfall shake timing moves its path a little: both runs stay in range.)
`Godot --headless --path game --quit-after 2`: no script errors.

## Requests
- **Anim team (cyclops):** `art_src/chars/cyclops/scripts/animfix2/build_walk.py` rebuilds `keys_walk.json` from
  `keys_walk.rest_v2.json`, which still has `{"step": 0.4}`: a re-run would put the single event back. Carry
  `{"step_r": 0.4167, "step_l": 1.125}` over (cyclops.gd also still works with a single `step`).
- **Anim team (cyclops), pull_free:** the club over-swing peaks 46-50 m/s at clip 1.04-1.13 s (animfix2 note); the game plays the
  clip at 1.875x (pull_free_time 0.8 s), i.e. ~90 m/s on screen: the club crosses the frame in 2 frames at 30 fps (sheet I,
  12.66-12.80). Spread the heave over 0.9-1.3 s of the clip. Kept pull_free_time 0.8 (SPEC timing of the back-off window).
- **Core / player camera (optional):** if the raised slam club should be seen at the usual slam distance, `cut_inside` for the
  cyclops would have to let the arm grow during the windup (or allow a little more tilt); today the club top is cut.

## Devlog
`docs/devlog/media_inbox/integrate2_cyclops/01_cyclops_natural_fight.jpg` (6 frames: idle, walk, sweep, turn step, slam landing,
death) + captions.txt.
