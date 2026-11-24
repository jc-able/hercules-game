# Cyclops polish 2: natural movement, rim curb, stuck club (2026-11-23, 09:00-09:45)

Role: cyclops polish fixer. Owner's words today (docs/briefs/anim_natural.md): "Make every movement throughout the process
natural." Files changed: `game/scripts/bosses/cyclops.gd`, `game/scripts/world/cyclops_arena.gd`, the CYCLOPS dictionary
in `game/scripts/data/tuning.gd`. No imports, no git. Scratch, probes, logs, movies: `work/cyclops_polish2/`.
Devlog: `docs/devlog/media_inbox/cyclops_polish2/` (6 JPEGs + captions.txt).

## 1. Natural movement (the gait)
**Before:** in `approach` he halted and switched to `idle` whenever the hero was inside 6.5 m, then rotated at a constant
70/110 deg/s on the spot (a statue on a turntable); turns started and stopped dead; he walked straight at the hero
whatever way he faced (sideways/backwards if the hero was behind); attacks began with an instant `halt()` from 2.6 m/s
and 0.12-0.15 s blends; the hurt flinch blended in 0.08 s; the step thud ran on its own timer, not on the clip.

**Now (cyclops.gd `_turn_smooth`, `_update_gait`, `_walk_footfalls`):**
- He plays `walk` whenever the body turns faster than `step_on_turn_deg` 15 deg/s or moves faster than `step_on_speed`
  0.3 m/s (or is about to: intent counts, so there is no one-tick idle flicker); `idle` only after both have been calm for
  `step_calm` 0.25 s. Cross-fade `loco_blend` 0.3 s.
- Walk playback = ground speed / the clip's `move_speed` (CharacterVisual.move_speed). On the spot it is the turn rate /
  `turn_step_ref_deg` 60. Clamped 0.5-1.3x. **Decision:** the cyclops manifest has no `move_speed` yet, so
  `Tuning.CYCLOPS.walk_move_speed` 2.43 m/s is a FALLBACK (measured today with `work/cyclops_polish2/measure_walk.gd`:
  the stance ankle travels ~1.87 m in ~0.77 s of the 1.4167 s clip). The manifest value wins as soon as the anim team
  writes it. Walking at 2.6 m/s plays 1.07x; turning on the spot at 70 deg/s plays 1.17x.
- He walks along his own facing, speed x clamp((cos(angle) - 0.3) / 0.7): a hero behind him gets a turn on the spot or an
  arc, never a sideways slide. Speed eases (`walk_accel` 4, `walk_decel` 5 m/s^2).
- Turns ease in and out (`turn_accel_deg` 360 deg/s^2, rate = error x `turn_ease` 4 near the goal), also in the slam
  windup steering (accel x1.5 there). A sweep that starts mid-turn lets the turn run out over `TURN_SETTLE` 0.25 s, and the
  sweep cone/decal is aimed where the body ends up (+_yaw_vel x 0.125 s), so the decal still matches the club arc.
- Sweep start: the walk momentum dies out over 0.2 s instead of an instant halt. Blends: every attack `attack_blend`
  0.22 s (slam rebound keeps 0.3), idle 0.3 s, `hurt_blend` 0.2 (BossBase default 0.08).
- Footfalls (thud + small shake) fire when the walk clip passes its `step*` events (one event: it and +half the clip;
  none: 1/4 and 3/4). Clip lengths and event times are read from the manifest every time (the clips are being redone).

**Proof:** 30 fps movie `work/cyclops_polish2/gait_final.avi` (probe `gait_probe.gd`, --bot=idle, hero put 150 deg off
his facing after the first sweep): approach at 2.6 m/s walk 1.07x, eased stop into the sweep, then a 121 deg turn ON THE
SPOT stepping (walk 1.17x, 70 deg/s, eased start 0 -> 70 in 0.2 s) + 8 deg run-out as the next sweep starts. Strip:
`docs/devlog/media_inbox/cyclops_polish2/gait_turn_strip.jpg`.

**Still not natural (not mine to fix):** the walk clip itself keeps the four arms in the T pose with the club straight up
(anim team's job today). During the slam windup he still turns (<= 120 deg/s, now eased) and lunges (<= 3.2 m/s) while the
slam clip plays, so the club lands on the circle; the feet do not step then. A layered lower-body step would need an
AnimationTree in CharacterVisual (core).

## 2. Curb at the rim (final check open item 4)
Probe `work/cyclops_polish2/rim_probe.gd`: boss stopped at the centre, hero put on the rim at 8 angles (45 deg apart) and
holding `move_back` 1.2 s into the boundary; camera ends outside the ring (r 31.7-32.5 m, 1.2-1.3 m high, 2.5-3.1 m from
the hero). Each frame is rendered twice, with and without the arena's dressing bodies; the difference is the cover.

| | bottom quarter covered by dressing (mean / worst of 8) | angle 0 |
|---|---|---|
| before | 0.547 / 0.670 | 0.670 |
| near fade 1.8-3.6 m | 0.502 / 0.664 | 0.664 (the faded curb showed its dark ink shell + shadow) |
| + no curb shadow, fade 2.4-4.0 | 0.294 / 0.493 | 0.386 |
| **final: + no ink shell on the curb, fade 2.6-4.6 m** | **0.109 / 0.389** | **0.067** |

The 0.389 (west, 270 deg) is the ground shadow of the west colonnade, not geometry. Hero box covered after: 0.005-0.236
(shadows again; 0.005-0.15 at 6 of 8 angles). **Decision:** near fade on every arena StaticBody3D except the floor
(`_near_fade_dressing`, RIM_NEAR_HIDE 2.6 / RIM_NEAR_FULL 4.6), curb blocks without shadow and without the ink outline (a
0.45 m curb did not need either). Inside the ring the camera never comes within 4.6 m of any of it. The windowed lose run
(`--bot=lose`, death 21.09 s) shows the DEFEATED view with no curb band (`defeated_view_after.jpg`).

## 3. Stuck club (open item 5)
Probe `work/cyclops_polish2/club_probe.gd` (--bot=win, seed 11, the 4 forearm hits): club pixels in the strike frame.

| | lower-right quarter | whole frame | weak point on screen |
|---|---|---|---|
| before (club fade 1.8-4.6 m) | 0.527 (0.493-0.559) | 0.160-0.207 | 4/4 |
| stuck fade 3.2-6.0 m | 0.488 | 0.142-0.183 | 4/4 |
| **final: stuck fade 4.2-6.8 m** | **0.279 (0.256-0.291)** | **0.118-0.130** | **4/4** |

What remains in the lower right is mostly the club's ground shadow (the fade keeps shadows, which is what still says
"the club is in the ground"). The club's near point is 3.2-3.6 m from the camera; the weak point 4.6-5.1 m. The body (and
forearm) keep their own fade (0.9-2.6 m). The club fade eases to CLUB_STUCK_* over 0.3 s when stuck starts and back during
the first 0.4 s of pull_free; death keeps its own drop fade.

## 4. Regression (headless, --speed=3, after all changes; logs work/cyclops_polish2/logs/v3_*)
| Run | Result | Fight (fight_start 2.4 s -> end) | Notes |
|---|---|---|---|
| bot win seed 11 | victory | 36.35 s game (33.9 s fight) | 8 hits, slam_aim err 0.00-0.01 m, slam_land err 0.01-0.14 m |
| bot win seed 4242 | victory | 32.19 s (29.8 s) | same |
| bot win seed 7 | victory | 33.61 s (31.2 s) | same |
| bot lose seed 11 | defeat | player_died 21.09 s | restarts |
No SCRIPT ERROR / Parse Error / ERROR / WARNING lines. Every stuck window: `in_reach=true`, forearm weak point at
2.23-2.24 m (sword reaches 2.9 m). Same numbers as before the gait (v1 run): 36.36 / 32.21 / 33.59 s.

## Requests
- **Anim team (cyclops clips):** write `move_speed` for `walk` in cyclops_clips.json (planted-foot speed at 1.0x; today's
  clip measures ~2.43 m/s). A `step` event per foot (`step_l`, `step_r`) would put each thud exactly on its foot; today
  `step` 0.4 s is used with +half the clip, while the ankles touch down at ~0.57 s (right) and ~1.28 s (left).
- **Core (optional):** a lower-body step layer (AnimationTree blend) would let him step during the slam windup turn/lunge.

## Re-fix after the independent review (2026-11-23, ~09:25-10:10, cyclops polish re-fixer)
Scratch: `work/cyclops_polish2/refix/` (regress.sh, club_probe2.gd, gait_probe2.gd, logs/, movie/). Probe for the person-style
play: the reviewer's `work/polish2_review/cyclops/human_probe.gd` (headless, seed 11 and 7: identical numbers).

| Finding | Verdict | What changed | Result |
|---|---|---|---|
| 1 major: slam windup slides/turns like a statue (2.96-3.20 m, 3.2 m/s, snap from 2.6 to 0 to 3.2 m/s) | confirmed (reproduced 2.96/3.20 m) | `_enter_state(slam)`: no `halt()`; `_steer_club_to` eases velocity (`_ease_velocity`, `lunge_accel` 6 m/s^2) and caps it by `lunge_speed` 1.2 (was 3.2) and by the stopping distance sqrt(2 a err); windup turn cap `slam_turn_deg` 40 (was 120); the tracked circle is clamped (`_slam_reachable`) to `_slam_budget` = lunge x (windup - lunge/accel - 0.15 s) ~1.26 m around where the club lands at the slam start (+ the momentum's drift); a due slam waits for the hero within `slam_window` 1 m of LAND_LOCAL.z (the stepping walk closes a far gap; a hugging hero delays it at most `slam_close_wait` 1 s) and for the walk to brake to `slam_brake_speed` 0.6 m/s (he plants, then winds up); the rebound tick eases instead of `halt()` | [SLAM] move 1.02 / 0.79 m per windup (target <= 1.2), peak 1.20 m/s, turn <= 41 deg/s, 9-10 deg per windup; slam_land err 0.01-0.14 m on seeds 11/4242/7 |
| 2 major: stuck club vanishes, its shadow stays | confirmed | CLUB_STUCK 3.8 / 5.6 m (reviewer proposed 3.4 / 5.0: measured lower-right 0.375 > 0.3, so pushed out a little); club `cast_shadow` OFF while `_club_fade` > 0.5 (`_set_club_shadow`, restored when the club is dropped at death) | club_probe2 (third render with the fade off = the club's own silhouette): visible 0.71 / 0.44 / 0.68 / 0.43 of the silhouette (target >= 0.3), lower-right 0.333 / 0.204 / 0.334 / 0.171 (mean 0.260, target <= 0.3; two hits at 0.33), weak point on screen 4/4, no orphan shadow. At 3.4/5.0: visible 0.59-0.80, lower-right mean 0.375 |
| 3 minor: on-the-spot turn plays walk too fast (treadmill kick) | confirmed | `turn_step_ref_deg` 60 -> 120 | 70 deg/s turn on the spot plays walk at 0.58x (movie strip) |
| 4 minor: feet slide while speeding up / slowing | confirmed (148/1146 = 13 %) | `walk_rate_min` 0.5 -> 0.25, `walk_accel` 4 -> 6 m/s^2 | [SLIDE] 16 / 1149 moving walk ticks = 1.4 % (target < 5 %), mean error 0.02 |
| 5 minor: footfall thud ~0.17 s early | correct, no code change (as the reviewer says) | - | the anim team should write `step_l` / `step_r` at the real contacts (request above stands); lead checks when today's clips land |
| 6 minor: no before JPEG of the old gait | partly | my brief allows only `git diff` (no `git archive`/`git show`), so I could not render HEAD. The only pre-polish movie (work/audio/movie/cyclops.avi, far camera) does not show a turn on the spot clearly. Added `club_refix_before_after.jpg` (before/after the re-fix) and `gait_refix_strip.jpg` | **Lead:** cut a before strip of the idle-rotation from a HEAD export (reviewer's recipe) |

Proof movie: `work/cyclops_polish2/refix/movie/gait_refix.avi` (30 fps, gdwin, --bot=idle seed 11): approach (walk 1.07x), eased
stop into the sweep, hero put 150 deg behind -> 121 deg turn on the spot stepping (walk 0.58x at 70 deg/s), sweep, walk,
brake to 0.6 m/s, slam windup (shift 0.3 m, then standing), club lands, stuck, pull free, walk. Strip:
`docs/devlog/media_inbox/cyclops_polish2/gait_refix_strip.jpg`.

Regression (headless --speed=3, logs `work/cyclops_polish2/refix/logs/`): win seed 11 victory 37.56 s, 4242 33.02 s, 7 34.41 s
(was 36.35 / 32.19 / 33.61: the brake before each slam adds ~0.4 s); lose seed 11 player_died 21.06 s; slam_aim err 0.00,
slam_land err 0.01-0.14 m; every stuck window in_reach=true (weak point reachable). No SCRIPT ERROR / Parse Error.

Still not natural (not fixable in this module): during the slam windup the slam clip plays with no step while he shifts up
to ~1 m (<= 1.2 m/s) and turns <= 40 deg/s; the sweep start still lets 2.6 m/s of walk momentum die out over 0.2 s under the
sweep clip (~0.26 m). A lower-body step layer in CharacterVisual (core) or a slam clip with a planted step would fix both.
The walk clip's arms (T pose, club straight up) are the anim team's.
