# Medusa module notes (boss module builder 2026-11-22; review fixes the same day; REAL-MODEL INTEGRATION by the
# medusa integrator 2026-11-22 evening, owner away: decisions marked **Decision**)

Files: `game/scripts/bosses/medusa.gd` (extends BossBase, no class_name), `game/scripts/world/medusa_arena.gd`
(extends ArenaBase, loads the boss by path; unchanged in the integration pass). Model: `game/assets/characters/medusa/
medusa.glb` + `medusa_clips.json` (9 clips). Scratch: `work/medusa_int/` (clip probes `probe/sample.gd`, `probe/swipe.gd`
with logs; contact-sheet tools `tools/sheet.py`, `tools/multi.py`; logs `logs/`, final pass `logs/final/`; shots `shots/`).
Older scratch: `work/medusa/`.

## QA FIXER 3 (2026-11-23, owner away; scratch `work/medusa_fix3/`) — wins over every older row
File changed: `game/scripts/bosses/medusa.gd` only (medusa_arena.gd unchanged). Also SPEC §10.1 row "Medusa tail_swipe".
Requests: `docs/notes/qa_requests.md` "From the medusa fixer 3".
| Finding | Change | Status |
|---|---|---|
| major: tail ring 13.95 m, trigger at ~6 m: a 4.8 m roll or 0.7 s run cannot leave it, only a roll timed through the hit | **Decision: one rule, "roll OUT of the ring before it fills".** `TAIL_HIT_R` 9.0 m from her body centre = hit radius = ring decal = green sweep crescent (the 14 m visual tail still sweeps; its outer part passes over the hero harmlessly). `TAIL_COIL` 1.5 s ring fill (was 0.7 / 0.595), NOT shortened when enraged (the time to get out never changes; enraged only the sweep is faster, clip x1.18 instead of x1.0). The clip's wind-up (0-0.625) is stretched over the fill, then the flat sweep plays at its own speed (`_sweep_speed`, `visual.set_speed`). Hit as before: when the measured tip reaches the hero's angle, never before the ring is full. On-screen hint on the first two swipes of a fight: "Tail sweep: {roll} roll out of the ring" (device-aware). Bot: rolls out 0.35 s after the ring lights up, again while inside, backs away between | fixed, proven (below) |
| minor: hero in the beam at ~7 m: her head/eyes cut at the top during the gaze | (a) `get_lock_point()` during the gaze = her root (flat) at the usual lock height: the camera measured the cut_inside fade from the lock point, and her snapping/lunging head came within 4.8 m of the hero, so the arm could not grow at all. (b) new hook `cam_fit_points()` (eyes + measured post-snap eye spot `SNAP_EYES_LOCAL` (0, 8.9, 4.2) during the windup). **Core must read (b)**: no must-fit hook existed, request 1 | (a) live: after-beam eyes now 11 % inside the frame (was 3 % above it), beam cut shortened. Fully fixed only with request 1: proven with the exact patch swapped in at runtime: eyes >= 10 % inside the frame through windup, beam, lunge |
**Tail probe** (`work/medusa_fix3/tail_probe.gd`, log `logs/tail_probe.log`): forced swipes with the hero standing at every
trigger distance (2.38 m = touching her body capsule, 3, 4, 5 m and the trigger edge = root distance 5.98 m, i.e. 5.2-6.7 m
from her body centre) x 10 angles (0, +-45, +-90, 125, +-150, -135, 180), normal and enraged; he reacts 0.35 s after the
ring lights up: stick away from her + roll, roll again as soon as the roll ends while inside.
| Mode | Out of the ring at the hit | Already out when the ring is full |
|---|---|---|
| roll (the rule), normal | 50/50, worst margin +0.88 m | 50/50, worst +0.28 m (hugging her, 2 rolls) |
| roll, enraged | 50/50, worst +0.53 m | 50/50, worst +0.28 m |
| run out unlocked (6 m/s), normal | 50/50, worst +0.47 m | 49/50 (worst -0.06 m, hugging, 180 deg) |
| back off locked (2.4 m/s), normal | 6/50 | 4/50 -> the hint says "roll out", not "back off" |
One roll is enough from 5 m and from the trigger edge; from beside her body it takes two (0.35 + 0.82 + 0.25 s = 1.42 s < 1.5 s).
**Camera probe** (`work/medusa_fix3/cam_probe.gd`, hero held 7 m in front in the beam, eyes' screen y: 0 = top edge):
before -0.010 windup / -0.055 beam / -0.030 after; with (a) -0.009 / -0.050 / +0.108; with (a)+(b) and the core patch
+0.104 / +0.115 / +0.115 (arm 4.63 m during the windup instead of 3.4).
**Runs** (headless `--speed=3`, logs `work/medusa_fix3/logs/`): win seeds 11 / 4242 / 777 victory 26.22 / 25.28 / 26.90 s,
6 strikes, 0 hits; `--pad` 26.87 s; lose 4 gaze hits, DEFEATED 56.2 s, restart, `fight_start` again, `result=defeat`;
linger (hugs her at 2.3 m) 34.11 s, 2 tail swipes, both `miss` with the hero 11.6-12.0 m out; flank 41.23 s, 0 hits; no
SCRIPT ERROR. Windowed shots: `work/medusa_fix3/sheet_fix3.jpg` (6: approach ~1.6x the hero, windup at 7.6 m with eyes in
frame, reflect with the neck mark beside the neck, stunned, two tail rings with the hint). Devlog
`docs/devlog/media_inbox/medusa_fix3/`.
Decisions: hit 9.0 m (task range 9-10; 9.5 would leave a hugging hero 0.1 s of margin at 1.5 s); coil 1.5 s for both
phases instead of x0.85 enraged (otherwise 1.28 s, a hugging hero cannot get out); the hint shows twice per fight only.

## QA FIXER pass after the play-test (2026-11-22 night, owner away; scratch `work/medusa_fix2/`) — wins over older rows
Files: `game/scripts/bosses/medusa.gd`, `game/scripts/world/medusa_arena.gd`. Requests to others: `docs/notes/qa_requests.md`.
| Finding | Change | Status |
|---|---|---|
| major: she does not tower (x2 findings) | **Decision:** whole boss scaled uniformly x1.5 (`S`): `visual.scale`, body capsule r 1.95 / h 9.0, tail capsules, torso capsule, weak point r 1.2, tail sweep ring 2.1-13.95 m, stunned neck spot (0, 1.43, 6.83), gaze origin, body centre. She gazes from ~7.2-7.7 m (stalk band 7-10 m, gaze range 9 m, close-in to ~7.5 m), `stalk_area` 17 -> 12 m (the 14.9 m tail stays inside the 28 m courtyard), tail trigger 5.5 -> 6.0 m, `cam_max_extra()` 2.0 m (camera hook already read by PlayerCamera). **Reflect recoil:** stunned, she slides back 3.0 m in 0.9 s (ease-out) so her 7 m collapse lays the head ~3 m in front of the hero | fixed. Windowed (`--cam-debug`): at the fire she is ~1.8-2.0x the hero's screen height (silhouette; ~1.65x to the head top), was ~1.1x; head + eyes in frame in the windup (arm 3.4-3.9 m, lo <= hi). A per-boss base arm would add more (qa_requests 1, optional) |
| major: tail swipe hit before the ring filled | ring fills when the flat sweep BEGINS (`_swipe_speed = SWEEP_SPAN.x / coil`); hit resolved when the MEASURED tip (unwrapped angle swept since the sweep began) reaches the hero's angle, plus `state_time >= coil` safety and a fallback at the sweep end | fixed: probe (8 angles x normal/enraged, hero 6.5 m out) hits 0.03-0.45 s AFTER the ring is full, never before; tip 13-35 deg past the hero at the hit (one-frame pose lag: slightly late, never early). The measured sweep starts at ~+125 deg (not -166 as the old constant said) and slows from ~950 to ~600 deg/s |
| major: perma-shield trivialises her | **Decision:** timed raise. Module tracks when `Player.state` turns `block`; a gaze reflects only if the shield went up <= 0.6 s before the fire (or during the beam). A shield held longer just BLOCKS: 0 damage, the normal block shove once, no stun, no lunge; lowering it mid-beam lets the beam through | fixed: `qa_human.gd --perma-shield` (react 0.35) now 22 hits taken, 0 reflects, 5 defeats in 150 s (was a 27 s no-damage win); the normal reaction probe still reflects (raised 0.15-0.32 s before the fire) and wins 26.9 s |
| minor: overexposed sanctuary, white-ghost petrify | arena: marble albedo (0.81, 0.78, 0.73), step 0.76, inlays a touch darker, toon `shade_dark/shade_mid` 0.34/0.66 on floor/step/tier. Petrify: the additive 2.2 m burst is gone (grey chips + dust at his feet), the core ray and light sheet stop 1.4 m short of a petrified hero, no lunge onto him | fixed (windowed shot: opaque grey statue). Stone colour itself is core's (toon.gdshader, no emission added) |
| minor: legs through the snake hair when stunned; muddy snake blotches | new `Hair` capsule (r 0.83, across her right axis, 0.45 m ahead of the head socket) while the head is down; bot strike spot neck + 2.35 m, swing from <= 3.3 m (blade 2.5 + radius 1.2) | hair fixed (shot: hero stands in front of the snakes). **Blotches = texture (art track), not fixed** -> qa_requests 3 |
| core fixer request (qa_requests): neck mark covered her face | while the neck is high (> 3 m) the mark sits 0.68 m to the hero's side and 0.23 m lower | done (not re-shot) |
| player_fix request 1 | `visual.seek()` / `visual.clip_position()` instead of `visual._anim` | done |
Proof (headless `--speed=3`, logs `work/medusa_fix2/logs/f_*.log`): win seeds 11 / 4242 / 777 victory 26.18 / 25.30 / 26.91 s (6 neck hits, 0 player hits); `--pad` 26.83 s; flank (dodge + side cut of the lunging neck, SPEC answer a) 41.23 s, 6 misses, 0 hits; linger 32.35 s, 2 tail swipes dodged (hit 0.26-0.28 s after the ring); lose 4 gaze hits, DEFEATED at 56.2 s, restart, `fight_start` again, `result=defeat`; `--quit-after 2` clean; no SCRIPT ERROR. Probes: `work/medusa_fix2/tail_probe.gd` (tail angles + held vs timed shield). Windowed sheets: `work/medusa_fix2/sheet_fix2.jpg`, `sheet_fix2b.jpg`, `sheet_fix2c.jpg` (hits frames show the white hurt flash, not a bug). Devlog `docs/devlog/media_inbox/medusa_fix2/`.
Harness: `--medusa-trace` now also prints `trace_stun` (hero / weak point in her frame) while stunned.

## FIXER pass after the integration check (2026-11-22 late, owner away; scratch `work/medusa_fix/`)
Findings: (major) she did not tower at the stalk/gaze range (0.95x the hero's screen height vs ~1.4x in key_medusa.png);
(minor) the beam's light sheet passed over the camera (pale wedge) and washed out the petrified hero.
| Change (medusa.gd unless noted) | Why |
|---|---|
| **Decision:** `AS_BUILT` keep_min 6.0, keep_max 9.0, gaze_max_dist 8.0 (SPEC 9-14 / 10). Tail trigger 5.5 m kept | closer = taller on screen with the 3.7 m lock arm |
| Close-in hysteresis `_closing_in`: out of the band, or a gaze due beyond 8 m, she slithers in to ~6.5 m (`GAZE_APPROACH` 1.7) and gazes from there (gate 6.7 m), not at the 8 m line; if the 17 m stalk area holds her back she gazes from where she is | otherwise she stopped at the band edge (9 m) / gazed the moment she crossed 8 m |
| Default win bot holds `BOT_KEEP` 6.4 m (was 9.8) | inside the new band |
| medusa_arena.gd `player_spawn()` radius-7 (21 m from the centre, was 24 m) | a hero at 24 m was out of her reach (stalk area 17 m): gazed from 7.6 m |
| Beam light sheet ends on the floor `SHEET_STOP` 0.6 m short of the hero (lit floor fan still shows the 26 m reach); beam material distance fade 1-3 m; petrify burst 3.2 -> 2.2 m, alpha 0.8 -> 0.6 | the sheet to the far edge rose over the chase camera; now it lies beyond the hero, who occludes it |
| `lock_arm_extra()` (new, unused until core reads it) | camera hint, see request 6 |
Why not closer than ~6 m: the stunned clip lays her head 4.55-4.99 m ahead of her origin; at a 6 m gaze it lands ~1 m in
front of the hero (good); at 5 m it would land on him. **So the module alone reaches ~1.1x (head top) / ~1.2x (raised arms
in the windup), not 1.3x.** Geometry check (camera 3.69 m behind at 1.3 m, axis +7.9 deg from `--cam-debug`, top 6.2 m): her
head top predicted at y 176 px, shot shows ~200 px of 720. The verifier's 3.42*arm/(arm+d) is a small-angle estimate that
over-reads at short range (it says 1.3x at 6 m; the projection gives 1.06-1.15x). 1.33x at 6 m needs a 5.0 m arm (hero 30 %
of the frame) -> request 6.
Proof (logs `work/medusa_fix/logs/`): win seeds 11 / 4242 victory 26.16 / 25.26 s (6 strikes, 0 hits, gazes from 6.7 / 6.0 / 6.0 m);
lose: 4 gaze hits from 6.7 m, DEFEATED, `restart`, `fight_start` again, `result=defeat`; pad 26.83 s; flank 41.49 s (6 strikes,
0 hits); linger 36.08 s (3 tail swipes dodged); `--quit-after 2` clean. Windowed look `work/medusa_fix/sheet_look.jpg` (6
shots: approach, windup, enraged windup, stun close-up, fire, petrified hero). Devlog `docs/devlog/media_inbox/medusa_fix/`.

## Status (integration pass, real GLB from game/assets, headless `--speed=3`, logs `work/medusa_int/logs/final/`)
| Run | Result |
|---|---|
| `--start=medusa --harness --bot=win --quit-after=240`, seeds 11 / 4242 / 777 | victory 26.31 / 25.50 / 27.06 s; 3 reflects, 6 neck hits (all with the head on the floor, neck 0.95 m), 0 player hits |
| `--bot=lose` | 4 gazes hit (30 dmg + petrify each), DEFEATED, `restart`, `fight_start` again, `result=defeat` |
| `--bot=win --pad` | victory 26.97 s |
| `--bot=win --medusa-bot=flank` (dodge path: roll out of the locked fan, cut the lunging neck) | victory 44.36 s, 6 neck hits at neck_y 2.13-2.17 m, 0 player hits, 7 beams missed |
| `--bot=win --medusa-bot=linger` (provokes the tail) | victory 32.33 s, 2 tail swipes dodged (hit test when the tip crosses the hero: tip_deg -16 / -37 vs hero 0) |
| `--bot=idle --medusa-probe=tailturn` | turn into the hero refused, she goes the long way (147 deg), hero not shoved (4.67 m before and after) |
| `Godot --headless --path game --quit-after 2` | no SCRIPT ERROR / Parse Error |
| windowed `--shots` 1280x720 (win, lose, flank, linger; 8 images looked at) | see "Look" below; devlog `docs/devlog/media_inbox/medusa_int/` |

## Measured on the real model (Godot frame, boss at origin facing +Z; probe `work/medusa_int/probe/sample.log`)
| Clip | Fact |
|---|---|
| idle / slither | neck socket 5.33 m; tail bone heads on the floor (y 0.3-0.4), rest tip 8.9 m behind the body centre; slither sways the mid tail +-1.5 m |
| gaze (4.25 s, fire_start 2.0, fire_end 3.25) | stands tall the whole clip: neck 5.33 m, eyes 5.8-5.9 m in the windup; at fire_start the head snaps 1.5 m forward, neck 5.05 m, eyes 5.4 m, head pitched 17 deg down. **Out of sword reach (2.9 m) the whole clip** |
| stun_start (1.625 s) | recoil upright to 1.25 s (neck 4.96 m), collapse 1.25-1.625 s (neck 2.44 m at 1.5 s, 0.95 m at 1.625 s) |
| stunned (3.0 s loop) | **neck socket 0.95-0.99 m high, 4.55 m in front; head socket 0.61-0.72 m, 4.92-4.99 m in front** (head really on the floor); pelvis (0, 1.38, 2.58); the tail tip curls to x -4.8 m, z -5.7 m |
| rise (2.5 s) | starts from the stunned pose (neck 0.95 m), upright by 2.0 s |
| tail_swipe (2.25 s, impact 0.833) | wind-up 0-0.6 s (tip up to 2 m high), then a FLAT 360 deg sweep: the tip circles 383 deg in 0.54 clip-s (0.625 -> 1.167 s, ~707 deg/s), low (0.69 m), crossing her front at ~0.85 s; tip radius 9.25-9.4 m from the body centre at the front (bone heads 8.5 m). At the impact event the tip is at -19 deg |
| death (3.5 s) | falls onto her side (pelvis ends at (-2.28, 0.61, 2.25)) |

## States as built (numbers: Tuning.MEDUSA, then module AS_BUILT / constants)
| State | Clip | What happens |
|---|---|---|
| stalk | idle / slither | 6-9 m band since the fixer pass (was 9-14), close-in to ~6.5 m, gaze due after 2.2-3.6 s, gaze only within 8 m (6.7 m while closing in) and 25 deg, chase limit 8 s, tail timer 5.5 m / 1.5 s |
| gaze | `gaze`, three speeds | **clip 0 -> fire_start fills the windup** (1.2 s, x0.85 enraged): she stands tall, eyes glow (spheres + halo on the real `eyes` socket = head + manifest offset), fan decal + edge lines, lock at 0.5 s. **Beam exactly from clip fire_start to fire_end**: at the fire the clip is re-timed so 2.0 -> 3.25 takes the SPEC 1.0 s (x1.25), then 3.25 -> 4.25 takes `gaze_recover` 0.6 s. The beam (light sheet + a bright camera-facing core ray) leaves the real eyes socket along the LOCKED direction. Harness: `gaze_fire clip_t=1.97-2.02 fire_start=2.00`, `gaze_beam_end clip_t=3.25-3.28 fire_end=3.25` in every run (windowed included). Neck exposed for 1 hit from the fire to 0.8 s after the beam (as before). **After the fire she lunges down the beam** (LeanMod, 0.35 s, neck bone to 2.1 m, 83.8 deg), neck + head bend back 80 % of the lean so the face stays on the hero; held while the window is open, eases out over rise_time |
| stunned | `stun_start` x1.3 (1.25 s) -> `stunned` loop 3.0 s | neck exposed for 2 hits for the whole state; no procedural lean (the clips lay the head on the floor); the weak point rides the real neck, so it is reachable once the head lands (`stun_down` event, cuts land 0.25 s later at neck_y 0.95 m) |
| rise | `rise` stretched to 1.2 s | -> stalk |
| recoil | `hurt` (1.625 s, BossBase plays it) | after a cut during a gaze; waits the clip length |
| tail_swipe | `tail_swipe` x(impact / coil) = 1.19 (1.40 enraged) | 0.7 s coil, **ring decal r 1.4-9.3 m = the real tail's sweep**; the hero is struck when the tip passes HIS angle (clip time = impact + (hero_deg + 19) / 707); a green crescent rides the real tail tip over the sweep; 20 dmg, knockback 5, not blockable; tail capsules off during the swipe |
| dead | `death` | killed with the head on the floor (stunned / rise): the death clip is joined at 2.25 s (already lying) with a 1.0 s blend, so she slumps onto her side instead of getting up first (pelvis 1.02 -> 0.61 m, head 0.62-0.65 m). Lean eases out (runs in `_process`, not `_tick_state`) |

Clip timing guard: `_sync_clip` seeks a timed clip (gaze, stun_start, rise, tail_swipe) back onto the game clock when it
drifts > 0.04 s. Found in windowed `--shots` runs: screenshot hitches left the gaze clip at 1.25 / 1.57 instead of 2.0 at
the fire (and the stun loop popped in before the collapse). Headless never drifted.

## Weak point and reach
- Real model: weak point `neck` (radius 0.9) rides module socket `neck_wp`, copied from the REAL `neck` socket every
  physics and process frame (no height clamp, no sideways offset any more). It is reachable only when the neck is low:
  stunned 0.95 m (head on the floor, 4.55 m ahead), gaze lunge 2.13-2.17 m. During the recoil part of stun_start and the
  first 0.35 s of the beam the mark is up at ~5 m (visible, unreachable): honest, and the HUD arrow shows where it is.
- **Decision (gaze reach):** the gaze clip keeps the neck at 5.05 m, which a 1.9 m hero cannot reach (sword box top 2.9 m).
  SPEC answer (a) "cut the exposed side of her neck" therefore keeps the procedural lunge, but only AFTER the fire: the
  windup plays the real clip upright (the key_medusa.png pose), then she drives her head down the beam. A hero beside the
  lunging neck stands outside the fan (the bot stands 1.7 m to the side, 1 m past the neck: 17-20 deg off the fan axis).
- Stand-in (no skeleton): old placement (side of the neck during a gaze, 3 m ahead at 1.3 m when stunned).

## Tail and body collision (real model)
- Four capsules follow the tail bones every physics frame: tail_05-08-11-14-tip, radii 0.55 / 0.45 / 0.35 / 0.25 m, kept
  above the floor (never pushes her body up). Off while the tail swipes (the ring hit is the damage), after death, and
  for any part above 1.6 m. A capsule only switches on where it does not start inside the hero (no shoves).
- Torso capsule (r 0.55) pelvis -> head socket, only while the upper body lies on the floor (stunned): the hero cannot
  walk through her lying body or head. Body capsule as before (r 1.3, 0.5 m forward).
- The tail-aware turn (`face_towards` override) now tests the live capsules.

## Bot strategy (`bot_advice`)
Default (reflect): hold 9.8 m; raise the shield 0.45 s before the fire; when stunned, go to the floor neck (her frame
(0, 0.95, 4.55)) + 1.8 m along her forward and swing only when the mark is within 2.6 m, in front, and < 2.7 m above the
feet; two cuts, back off. `--medusa-bot=flank`: after the lock, step sideways and ROLL when the fire is < 0.5 s away (a
locked side-step runs 1.8 m/s for 0.3 s and cannot clear the 1.8 m half-fan at 9.2 m before an enraged fire), then stand
beside the lunging neck and cut; a window left open by the previous gaze is used only before the next lock.
`--medusa-bot=linger`, `--medusa-keep`, `--medusa-trace`, `--medusa-probe=tailturn`, `--medusa-glb/--medusa-manifest` as before.

## Look (windowed shots, compared with art_src/reference_video/key_medusa.png)
- Camera right behind the hero, hero large in the lower centre: yes. Upright gaze windup with arms raised, green eye halo,
  green fan with dark edge lines: yes. Lunge with the core ray along the fan: reads. Head on the floor with the snakes
  spread in front of the hero, orange mark on the neck: yes. Petrified hero: grey stone statue in the beam: yes.
- **Framing gap (for the lead / core camera):** at the SPEC stalk range (gaze from 9.2-10 m) Medusa stands about as tall on
  screen as the hero (0.95x; measured hero 36 % of the frame height, Medusa 31 %). key_medusa.png has her at ~1.4x the hero
  (74 % vs 54 %), i.e. shot with the hero ~4 m from her; our linger frames (hero 2-5 m from her) match the keyframe. The
  camera already tilts as far up as the "feet above the boss bar" rule allows, so the module cannot fix this alone: it needs
  either a closer stalk band (SPEC 9-14 m) or a lock-camera change. Not changed here (SPEC numbers kept).
- Arena unchanged (pale veined marble, inlaid rings, statues on pedestals in the colonnade, tall wall behind her).

## Decisions taken with the owner away (integration pass)
1. Gaze reach: upright windup, lunge after the fire (above).
2. Stun: stun_start at x1.3 so the head lands 1.25 s after the reflect, then the SPEC 3.0 s with the head on the floor
   (SPEC: "lowers her head to the floor 3.0 s"); state 4.25 s in all. Neck exposed for the whole state (2 hits).
3. `rise_time` 0.8 -> 1.2 s (animfix_medusa: the 2.5 s clip at 3.1x was a 0.16 s pop). Module override `AS_BUILT`.
4. Tail swipe radius 7 -> 9.3 m on the real model (ring and hit), the real sweep of the 9.9 m tail (SPEC §10 sizes win);
   per-angle hit timing from the measured sweep. Stand-in keeps 7 m.
5. Hurt clip: plays on cuts outside the stun (recoil after a gaze cut; a cut in stalk flinches); suppressed while stunned
   (a standing flinch would lift the head off the floor: flash + sound only).
6. Reflect: a white-gold burst + sparks at the centre of the hero's real shield prop (`reflect_flash shield_y=1.32`), then
   the glare line from the shield to her eyes and a burst at her eyes (as before).

Earlier decisions still valid: gaze range 10 m, chase limit 8 s, enraged follow-up timing, fan direction = toward the
hero until the lock, tail swipe only while stalking, arena dressing outside the lane, no OmniLight3D.

## Requests for others (not my files)
1. **core `Tuning.MEDUSA`:** `"rise_time": 1.2` (was 0.8) and a real-model sweep key, e.g. `"tail_sweep_radius": 9.3`
   (the module overrides both today: `AS_BUILT` and `T["tail_radius"] = TAIL_SWEEP_R` when the GLB is loaded). Optional:
   `"stun_start_speed": 1.3`, `"lean_in_time": 0.35` if core wants every number in Tuning.
2. **core `CharacterVisual`:** a public `seek(t)` / `clip_position()` and `play(clip, blend, speed, from_time)`. The module
   reaches into `visual._anim` for the clip-clock sync, the harness clip times and the death join (marked in the code).
3. **core (all bosses):** AnimationPlayer runs on the frame clock, game logic on the physics clock; during frame hitches
   (windowed `--shots`: one screenshot every 0.1-0.2 s) clips drift 0.3-0.75 s. Medusa re-syncs itself; cyclops/hydra
   timed clips (slam, fire_sweep) drift the same way. Option: `_anim.callback_mode_process = PHYSICS` for bosses or a sync
   helper in CharacterVisual.
4. **lead / core camera:** the framing gap above (SPEC stalk 9-14 m vs key_medusa.png).
6. **core camera (fixer pass, for the Medusa framing major):** read an optional boss hint in `PlayerCamera._lock_distance`:
   `if boss.has_method("lock_arm_extra"): d = max(d, Tuning.CAM_LOCK_DISTANCE + boss.lock_arm_extra())` (smoothed by the
   existing lerp). medusa.gd already returns clamp(1.3 + 0.15 * (d - 6), 0, 1.8) m (0 while stunned): at 6 m that is a 5.0 m
   arm, boss/hero ~1.33x. Also `Tuning.MEDUSA` keep_min 6.0 / keep_max 9.0 / gaze_max_dist 8.0 (module overrides via AS_BUILT).
5. **animation track (optional):** if `gaze` lowered the head itself after fire_start (neck <= ~2.2 m by +0.35 s), the
   procedural lunge would add nothing (LeanMod only tops up). The stunned chain needs nothing.

## Known gaps
- The lunge is deep (83.8 deg, torso nearly horizontal at the hero's head height); it reads as a strike in the shots, but
  the neck/head counter-bend (2 x 33 deg) was not inspected close up for skin stretching.
- (fixed in the fixer pass) the beam's light sheet no longer passes over the camera.
- Framing: ~1.1-1.2x the hero at the gaze until core reads `lock_arm_extra()` (request 6).
- The default win bot only uses the reflect path; the dodge path is proven by `--medusa-bot=flank`.
- Death after a kill inside the gaze window: the death clip starts upright while the lunge eases out over 1.2 s.
- Tail capsules follow bones but are simple capsules (the tapered tail between bone heads is approximated).
