# Hydra polish 2 (2026-11-23, 09:00-09:45; owner at the Mac, decisions marked **Decision**)

Role: HYDRA polish fixer. Files changed: `game/scripts/bosses/hydra.gd`, `game/scripts/data/tuning.gd` (HYDRA dict only).
`hydra_arena.gd` untouched. No imports, no git. Scratch: `work/hydra_polish2/` (logs/, probes `jaw_probe.gd`,
`move_probe.gd`, `move.avi`, strips). Devlog: `docs/devlog/media_inbox/hydra_polish2/`.

## 1. Natural movement (owner's words today)
What the state machine did before:
- guard: `face_towards` at a flat 35 deg/s from the first frame (infinite acceleration) and stopping dead; the walk clip
  at a fixed x0.9 only above 6 deg of error, so every correction under 6 deg (and the last 2-6 deg of each turn) was a
  statue pivot with the idle clip.
- forced fire (hero outran the turn 4.5 s): the body pivoted up to 60 deg in 0.9 s (up to 67 deg/s) on the fire clip,
  legs not stepping.
- blends under 0.2 s: bite 0.12, stomp 0.15, enraged return sweep 0.10; guard idle 0.3 after a bite/stomp that ends
  mid-recovery (bite state ends at clip 2.44 of 3.5 s).
- No clip is held paused: head_down is a loop; stomp runs past its end by only 0.06 s (normal) / 0.07 s (enraged); the
  fire clip is re-timed, never stopped. Nothing to fix there.

Changes:
- `_guard_turn()`: the body turns only while the walk clip steps; the rate eases in and out (`turn_accel_deg` 90
  deg/s^2, v = min(cap, sqrt(2 a err)) so it decelerates onto the target). Measured: 0 -> 35 deg/s in 0.39 s.
- `_walk_rate()`: the walk clip rate follows the real turn rate every tick: with a manifest `move_speed` it is
  turn rate x forefoot radius / move_speed (exact, read through CharacterVisual); without it (today's manifest has
  none) x0.9 at 35 deg/s, proportional below, clamped 0.3-1.5. Measured 0.31 -> 0.54 -> 0.90 during the ramp.
- Idle comes back only when the error is < 2 deg AND the turn has stopped (< 4 deg/s).
- **Decision** (forced fire): from `guard_force_fire` (4.5 s) the beast steps round x1.6 faster (`guard_urgent_turn_mult`);
  the old aimed/pivoting fire is kept only as a fallback after `guard_force_fire_late` (2.0 s) more. The bot never
  triggers it (it stands at the snout).
- Blends: fire start 0.2 -> 0.3, stomp 0.15 -> 0.25, bite 0.12 -> 0.2, enraged return sweep 0.1 -> 0.2, guard idle
  0.3 -> 0.4. Event times are unchanged (a cross-fade does not shift clip time).
- Not changed: bite tracking still turns the body <= 10 deg in 0.28 s on the bite clip (too short to step).

Proof: `work/hydra_polish2/move.avi` (gdwin, 30 fps), strip `hydra_natural_move_strip.jpg`: approach, a stepping turn
(the probe starts it 120 deg off; the fire starts once inside 50 deg: ~70 deg turned in 2.33 s), inhale + fire start,
fire end -> head_down, head_down -> head_up -> stomp.
Clip-side (not mine): the hydra idle is a statue and the attack clips freeze the 8 idle heads (lead's table). The code
now plays them without freezes or snaps; their own life must come from the redone clips.

## 2. Jaw reach (open item 3)
Probe `work/hydra_polish2/jaw_probe.gd` (headless, `--sword-debug`): head forced down, hero unlocked facing the snout at
angle A round the lying jaw (0 = in front, 90 = beside the head, 180 = behind it) and start distance D from the jaw centre,
one attack press (the swing lunges 0.65 m). "tip" = closest approach of the VISIBLE blade tip (tip without
SWORD_TIP_EXTRA) to the jaw centre before the hit; the snout surface is ~0.6 m from the jaw centre.

| A (deg) | r 1.3: hits from D | r 1.3: no hit from | r 1.0: hits from D | r 1.0: no hit from | behind rule |
|---|---|---|---|---|---|
| 0 | 1.2-3.0 | 3.4 | 1.2-2.6 | 3.0 | - |
| +-30 | 1.2-3.0 (+30: 3.4) | 3.4 / 3.8 | 1.2-2.6 | 3.0 | - |
| +-60 | 1.2-3.0 (+60: 3.4) | 3.4 / 3.8 | 1.2-2.6 | 3.0 | - |
| +-90 | 1.2-3.0 (90: 3.4) | 3.4 / 3.8 | 1.2-2.6 | 3.0 | - |
| 120 | 1.2 only | 2.0+ glance | 1.2 only | 2.0+ glance | jaw_glance (_jaw_side_ok) |
| 150, 180 | never | glance / miss | never | glance / miss | jaw_glance |

At r 1.3 strikes from 3.0-3.4 m still counted while the visible tip stayed 1.35-1.7 m from the jaw centre (0.8-1.1 m
short of the snout): the hit volume was far bigger than what the eye sees. The over-reach comes mostly from core's
SWORD_TIP_EXTRA 0.7 + SWORD_HIT_RADIUS 0.45; only jaw_radius is mine.
**Decision:** `jaw_radius` 1.3 -> 1.0 (Tuning.HYDRA and EXTRA). Now every front-arc strike from <= 2.6 m (all strikes
whose blade visibly reaches the snout) hits, 3.0 m no longer does; behind the head still glances. The bot strikes from
<= 1.15 m, unaffected (8/8 below). The final-check "whiff at 1.3 m" did not reproduce: from 1.2 m every front strike hits.

## 3. Inhale warning (open item 6)
`INHALE_SHADER` rewritten: Voronoi cracks (2 scales, fwidth anti-aliased) glowing orange -> hot yellow toward the
head, heat rising through the inhale (`progress`), heat fronts running along the cracks in toward the head (moving
front), flickering embers, a bright steady edge (sides + rim), a faint fill near the head only. Telegraph fill alpha
`COL_FIRE_WARN` 0.38 -> 0.10. Before/after: `hydra_inhale_before_after.jpg` (chase camera, hero inside the cone).

## 4. Regression (headless, --speed=3)
| Run | Before (r 1.3, old code, final_check) | After |
|---|---|---|
| win seed 11 / 4242 / 7 | 99.0-99.57 s | 99.42 / 99.48 / 99.44 s, 8 openings 8 strikes, 0 hits taken, 0 glances |
| lose seed 11 | died 27.85 s, defeat | died 27.87 s, fight_start again 33.56 s, result=defeat |
No SCRIPT ERROR / Parse Error in any log (bot, probes, movie).

## Requests
- Clip team: keep `head_down` a loop (the state holds it 2.5 s); if it becomes a one-shot, the lying head freezes. Add
  `move_speed` to the hydra `walk` manifest row so the turn-in-place rate is exact (code reads it already).
- Core: SWORD_TIP_EXTRA 0.7 lets strikes count ~1 m before the visible blade arrives (all bosses); a smaller extra
  would let the jaw radius be honest.

---
# Polish 2 RE-FIX (2026-11-23, after the independent review; owner at the Mac, decisions marked **Decision**)
Role: HYDRA polish re-fixer. Files: `game/scripts/bosses/hydra.gd`, Tuning.HYDRA (3 keys). `hydra_arena.gd` untouched.
No imports, no git. Scratch `work/hydra_polish2b/` (logs/, `move_probe.gd` + `movie/move.avi`, `orbit_probe.gd`,
`orbit_bite.gd`, strips). Reviewer probes re-run from `work/polish2_review/hydra/`.

## Findings, verified, and what changed
| # | Finding | Verified? | Change | Measured after |
|---|---|---|---|---|
| 1 major | attack starts while the body turns: rate -> 0 in one tick | yes (old circle log: t=14.23 26.6 -> 0 at fire_sweep entry) | guard: the chosen attack waits in `_pending_attack` while `_guard_turn(..., brake=true)` slows the body at turn_accel_deg; it starts below `attack_brake_deg` 5 deg/s (fire kept if the hero is still inside arc/2 - 10 deg, else re-chosen). The < 5 deg/s left brakes out under the fire inhale and the stomp. Forced fire carries its rate into its own stepping turn (#6) | reviewer's circle probe: no one-tick change > 12 deg/s (was 2 snaps); the movie run: largest one-tick change of the turn rate 1.5 deg/s over 16 s (35 -> 0.5 deg/s in 0.4 s, ~9 deg, then the inhale) |
| 2 major | locked strikes face the body root, so side strikes at r 1.0 missed | yes: `player.gd _face_lock` aims at `lock_target.global_position` | **Decision:** `jaw_radius` back to 1.3 (Tuning.HYDRA + EXTRA). The real fix is core's (request below) | locked probe (reviewer's `jaw_locked.gd`, speed 3), hits per start distance: 0 deg: 1.2-3.0 m; +30: to 2.6 (3.0 misses); -30: to 3.0; +-60: to 2.0 (2.6 misses); +-90: 1.2 only; 120: never (1 glance). Front arc +-60 all hits to 2.0 m. Bot unchanged (strikes from <= 1.15 m) |
| 3 minor | the guard turn still stopped dead on the target, and reversed with a jolt | yes (code: `step = err; _yaw_vel = 0`) | `_ease_turn`: a critically damped spring on the yaw error (`turn_spring_k` 6 /s^2), acceleration limited to turn_accel_deg 90, rate to turn_deg (urgent x1.6; leaving the urgent rate slows at the accel limit, no clamp snap). No dead stop, no overshoot on a still target (sim: 120 deg -> 0 overshoot; 10 deg corrections peak 9 deg/s) | circle probe: guard/walk max 29 deg/s, no jolt; reversal is smooth (accel <= 90 deg/s^2) |
| 4 minor | bite tracking a flat 35 deg/s spin on still legs | yes | eased shift: v toward sqrt(2 a err), a = 2 x turn_accel_deg, cap min(`bite_turn_cap_deg` 15, a x time to the lock), so it is ~0 at the lock; _yaw_vel = 0 at the lock | orbit probe (12 deg/s at 6.6 m): bite/bite 3.0 deg turned, max 15 deg/s, no snap. **Decision:** the bite now tracks ~3 deg instead of ~10 deg; the circle still follows that (fairer to a person, the bot rolls anyway) |
| 5 minor | inhale cracks read as a glowing tiled grid | partly (still unmistakable as danger; reviewer agrees) | INHALE_SHADER: fine cracks 0.5 -> 0.25, glow = cracks x heat x (0.25 + 1.4 band), fronts u*2.4 -> u*1.6 (2-3 pulses), cracks fade out from 62 % to 90 % of the reach (side edges + rim stay), fronts burn whiter than the arena's orange veins, embers brighten as a front passes | `hydra_refix_inhale_strip.jpg` (0.1 s apart, inside the cone): a white-hot band moves toward the head; `hydra_refix_inhale_before_after.jpg` |
| 6 minor | forced fire pivots up to 60 deg on the fire clip's legs | yes (code) | real model: the forced fire keeps the walk clip and steps round (eased spring, urgent rate) to the aimed arc; the inhale is lengthened by the simulated turn time + 0.45 s (`_turn_time_est`, so the cone warning lasts the whole turn); the fire clip blends in (0.35) once it faces the arc, seeked so `fire_start` still lands at the end of the inhale. Stand-in keeps the old pivot | orbit probe (hero forced round at 70 deg/s): fire_sweep/walk 49.8 deg stepped, then `fire_step_done err=-1.5 yaw_vel=-2.9`, fire clip max 2.9 deg/s; inhale 2.48 s instead of 1.5 |

Reviewer's alternative for #6 ("aim the cone without turning") was not used: on the real model the flame angle follows
the mouth relative to `_fire_dir` (`_flame_actual`), so an aimed cone without a turn would burn the wrong arc.

## Regression (headless, --speed=3)
| Run | Polish 2 | Re-fix |
|---|---|---|
| win seed 11 / 4242 / 7 | 99.42 / 99.48 / 99.44 s | victory at 99.44 / 99.45 / 99.47 s; 8 strikes, 0 hits taken, 0 glances each |
| lose seed 11 | died 27.87 s, defeat | died 27.85 s, fight_start again 33.55 s, result=defeat |
No SCRIPT ERROR / Parse Error in any log (bots, probes, movie).

Proof (task 1): `work/hydra_polish2b/movie/move.avi` (gdwin, 30 fps) and `hydra_refix_move_strip.jpg`: approach, a
120 deg stepping turn (2.57 s to the inhale, 77 deg turned, fire at 43 deg off), the brake, the inhale, fire start
and end, the head landing, head_down -> head_up -> stomp.

## Requests (other modules)
- **Core (player.gd + boss_base.gd), finding 2 (hydra.gd already has `strike_point(from)` ready):** in `Player._face_lock` aim at `lock_target.strike_point(global_position)`
  instead of `lock_target.global_position`; `BossBase.strike_point(from: Vector3) -> Vector3` returns `global_position`
  by default. Hydra will override it: during head_down with the hero within ~4 m of `weak_points[&"jaw"]`, return the
  jaw position. Then locked side strikes at 60-90 deg / 2.0 m hit, and `jaw_radius` can drop back toward 1.0 (re-run
  `work/polish2_review/hydra/jaw_locked.gd`; lower it only if the front arc stays all hits to 2.0 m).
- Clip team: unchanged from above (head_down a loop; `move_speed` on the hydra walk row).
