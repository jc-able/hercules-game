# Hydra integrator 2 (2026-11-23, 10:59-11:45; owner at the Mac, decisions marked **Decision**)

Files changed: `game/scripts/bosses/hydra.gd`, `game/scripts/data/tuning.gd` (HYDRA `jaw_radius` only), `docs/SPEC.md` §8
(the hydra clip list). `hydra_arena.gd` untouched. No GLB / manifest edits, no imports, no git. Godot rendered only through
`tools/godot_bg/gdwin` (960x540, `--fixed-fps 30`); everything else headless. Scratch: `work/integrate2_hydra/`
(probes `look_probe.gd` / `look_probe2.gd`, logs/, movie/ with `bot_before.avi` = bot-win fight before my changes,
`turn_after.avi` = 4 forced 70-130 deg turns, strips `s1_fire.jpg`, `s2_stomp_bite.jpg`, `t1_turn.jpg`).

## How I looked
- `look_probe2.gd --mode=teleport` (headless and rendered): the hero (hp huge) is put 120 / -90 / 70 / -130 deg off the
  snout at 13 m each time the beast returns to guard; per physics frame it measures the four foot BONES (planted = bone
  y < 0.47 m, natural 0.39) world slide per clip, head-socket acceleration at every clip change vs steady, the fire
  (flame angle vs the centre mouth's angle, mouth height, emitter on), the jaw in head_down. `--mode=bot`/`circle` too.
- Strips read: fire chain (inhale, sweep from the mouth, head lands, head_up, stomp), stomp + bite + idle, the 120 deg
  turn walk into the inhale. Heads move independently in idle and walk; no pops seen.

## Measured
| thing | before (clips of today, code of 10:54) | after |
|---|---|---|
| turn walk blend-in (idle -> walk_turn, 0.35 s, body turn ramping at the same time) | planted feet 1.0-1.9 m/s for ~0.4 s | body turn cap ramps in over the 0.5 s blend (k^2): 0.4-1.1 m/s; what remains is the blend itself moving the feet 0.45 m (clip, see below) |
| turn walk steady (35 deg/s, x1.52) | median 0.07-0.09 m/s; spikes only at toe-off / touch-down (bl, fl ~1.5 m/s, 1-3 frames) | same (clip) |
| attack started mid-turn-walk (walk_turn -> fire_sweep, 0.3 s blend) | started at any phase (clip 0.93-1.61 s): feet 4.4-5.5 m/s peaks | **wind-down**: a pending attack lets the walk step on at a matched 16 deg/s until the `stop_window` (max 1.2 s), then brakes; 3 of 4 turns start the attack at clip 1.54 s (in the window), 1 timed out at 1.28 s; attack blend out of a walk 0.5 s: peaks 2.2-3.3 m/s |
| head pops at clip changes | max head-socket accel at changes 9-750 m/s^2 vs steady p99 1053-1104 (the strikes) | unchanged: no change is above the clips' own motion |
| fire from the mouth | flame angle = 1.65 x mouth angle: mouth +-41..45 deg -> flame +-70..76.5 deg; mouth 2.4-4.0 m high while the stream emits (emitter on 496 of 508 fire frames; off only while the head is still diving, by design) | unchanged (correct) |
| head_down jaw | jaw weak point 0.48-0.74 m high once landed, 6.93-7.64 m ahead (landing phase starts at 3.8 m) | unchanged |
| idle / stomp / head_up planted feet | median 0.003-0.017, p90 0.06-0.13 m/s | unchanged; the stomp foot's touch-down frame reads 7.8 m/s (the hoof arriving, below 0.47 m) |

## Changes (hydra.gd)
- `_guard_turn`: (1) **wind-down**: with an attack pending during a turn walk that is not in its `stop_window`, the body
  keeps turning at `attack_wind_deg` 16 deg/s (the clip rate follows the turn, so the feet stay planted) for at most
  `attack_wind_max` 1.2 s, then brakes as before. **Decision:** up to ~19 deg of extra turn before an attack is fine
  (fire keeps its 60 deg check; bites/stomp are chosen again). (2) the turn cap ramps in (k^2) over `turn_walk_blend`
  0.5 s after a turn walk starts, so the body does not swing on a half-weighted clip.
- `_start_turn_walk`: the turn clips blend in over `turn_walk_blend` 0.5 s (was 0.35).
- `_attack_blend(base)`: fire_sweep / stomp / bite blend in over `attack_walk_blend` 0.5 s when they start out of a
  walk clip; out of the idle unchanged (0.3 / 0.25 / 0.2). Event times are unaffected (cross-fades do not shift clip time).
- New EXTRA keys: `turn_walk_blend`, `attack_wind_deg`, `attack_wind_max`, `attack_walk_blend`.

## Jaw radius (open request)
Re-ran `work/polish2_review/hydra/jaw_locked.gd` (locked, speed 3) with core's strike_point hook in:
- r 1.3: every case 0 / +-30 / +-60 / +-90 deg hits at 1.2, 2.0, 2.6 AND 3.0 m (3.0 m hits while the visible tip stays
  1.3-1.7 m from the jaw: over-reach); 120 deg: 1.2 m only.
- r 1.0: every case 0..+-90 deg hits at 1.2, 2.0 and 2.6 m; 3.0 m misses everywhere; 120 deg 1.2 m only.
**Decision:** `jaw_radius` 1.3 -> **1.0** (Tuning.HYDRA and EXTRA): the condition (within 60 deg all hit to 2.0 m) holds
with margin (to 2.6 m, and to 90 deg).

## Regression (headless, --speed=3)
| run | before my changes | after (jaw 1.0, all changes) |
|---|---|---|
| win seed 11 / 4242 / 7 | victory 99.34 / 99.34 / 99.36 s, 8 strikes, 0 hits taken | victory 99.33 / 99.37 / 99.35 s, 8 strikes, 0 hits taken, no jaw_fallback |
| lose seed 11 | died 27.86 s, restart 33.55 s, result=defeat | died 27.85 s, restart 33.54 s, result=defeat |
No SCRIPT ERROR / Parse Error in any log (bots, probes, movies).
The bot's 5 `glance` events per win are its follow-up swing hitting the closed jaw right after the killing strike
(correct clang); they were there before my changes too.

## For the animation fixer (clip problems)
1. walk_turn_l / walk_turn_r: the turn walk starts at `start_time` 1.5833 with the feet 0.45 m off the stance, so the
   idle -> walk blend slides all four planted feet (0.4-1.1 m/s for 0.5 s). Fix: a short step-in (2-3 feet lift one
   after another from the stance into the walk phase), e.g. `walk_turn_start_l/_r`, or a start phase whose feet sit on
   the stance. Same for the stop: a settle step (`walk_turn_stop_*`) from the stop window to the stance.
2. walk_turn_l/_r steady: toe-off / touch-down frames of foot_bl and foot_fl slide ~1.5 m/s for 1-3 frames at 35 deg/s
   (IK reach, the fixer's known 7 cm miss).
3. fire_sweep / fire_sweep_l / stomp / bite start from the stance: out of a walk (even in the stop window) the blend moves
   the feet 0.45 m (peaks 2.2-3.3 m/s with the 0.5 s blend). A settle clip (2) would remove it.
