# Final check 3: after "feedback 2" (2026-11-23, about 14:05-14:25; owner at the Mac, not asked)

Role: final check agent (wave `hercules-feedback-2`). Files I wrote: this note and
`docs/devlog/media_inbox/final_check3/` (7 sheets + captions.txt). Scratch, logs, movies, sheets and run scripts:
`work/final_check3/` (`headless_chain.sh`, `mov.sh`, `lane1-4.sh`, `run_cold.sh`, `perf_chain.sh`, `sheet.py`,
`spikes.py`, `logs/`, `mov/`, `perf/`, `sheets/`).

**Decision: no code edits.** Every run was clean and I found no small mechanical leftover worth touching (the unused
`_look_*` vars / `CAM_MOUSE_SENS` / `CAM_PAD_SPEED` in `pegasus_flight.gd` print no warning; left for a later tidy).
No GLB, manifest or import touched; no git. `builds/Hercules.app` and the owner's save folder untouched. Every rendering
run went through `tools/godot_bg/gdwin` with a throwaway HOME (cold runs on my own clone `work/final_check3/bin/G.app`
with a new bundle id each). Every process I started has ended.

## 1. Whole game, headless (`--harness --seed=11 --speed=3`, throwaway HOME)
| Run | Result | Fights (fight_start -> victory, game s) | Notes |
|---|---|---|---|
| `--start=title --bot=win --campaign --keys` | victory, exit 0 | cyclops 24.18 -> 59.35, medusa 95.98 -> 119.93, hydra 150.05 -> 248.13 | title -> home -> sea -> 3 islands -> ending (3.2 s) -> free-flight sea; 22 strikes, 0 hits taken, 3 glances, victories=3 |
| same with `--pad` | victory, exit 0 | cyclops 24.15 -> 58.56, medusa 95.16 -> 119.14, hydra 149.44 -> 246.06 | same flow; 22 strikes, 0 hits taken, 3 glances |
| `--start=cyclops/medusa/hydra --bot=win` | victory x3 | 37.61 / 26.22 / 99.09 | identical to the vfx/sword re-fixers' last runs |
| `--start=cyclops --bot=lose` | defeat, exit 1 | - | 4 hits, defeat 21.09, restart 25.77, fight_start again |
| `--start=medusa --bot=lose` | defeat | - | 4 hits, defeat 56.34, restart 61.01 |
| `--start=hydra --bot=lose` | defeat | - | 9 hits, defeat 27.86, restart 32.54 |
| `--start=title --probe=ui` | quit, exit 0 | - | focus = New_game |
| `--start=cyclops --probe=ui --pad` | quit, exit 0 | - | pause focus = Resume, closes (paused=false) |

No `SCRIPT ERROR`, `Parse Error`, `ERROR` or `WARNING` line in any of these 10 logs, the 8 movie runs (except the steer
probe's own `quit()` leak line at exit, a probe artefact) or the 6 perf runs.

## 2. The owner's six points: game camera now beside his recording
Movies: gdwin 1280x720 window (frames come out 1600x900), 30 fps, `--seed=11`: cyclops / hydra `--bot=win` 22 s, home
mount (`--start=home --bot=win`), dismount (`--home-from=sea`), sea trips to the Cyclops, Medusa (`--defeated=cyclops`)
and Hydra (`--defeated=cyclops,medusa`), and the flight2 steer probe (left 3 s, right 3 s, climb 2 s, dive 2 s with the
right-stick actions swapped every 0.5 s the whole time). Sheets in `work/final_check3/sheets/`, 7 of them in the devlog inbox.

| # | Point | Verdict | What I saw (and what is still off) |
|---|---|---|---|
| 1 | Sword hold ("hands backwards") | **Fixed** (one minor left) | Owner: open hand, grip on the finger tips, blade out of the little-finger side flaring out/back. Now (cyclops 3.6 / 8.0 / 10.4, dismount 3.0-3.3, `s1b_hand.jpg`): a closed fist, pommel above the little finger toward the camera, guard at the bottom of the fist, blade down beside the right leg. The fixer's front/side close-ups (`work/sword/ba_check.jpg`) agree: blade forward-down out of the thumb side. Still off (minor): from the chase camera (behind) the blade reads "down and a little OUT" more than "forward", because the carry direction points ~25 deg outward and the forward part is foreshortened. No sword stuck out sideways after the mount (mount 1.9-2.5). On Pegasus from behind the blade is mostly hidden by the wing; where seen (sea 11.0 / 12.0) it is outside the flank, not in it. |
| 2 | Mount / dismount | **Mostly fixed** | Owner: standing -> seated in 0.2 s, rider gone 0.4-0.6 s on the dismount. Now, mount every 0.1 s (`s2b`): step in 1.1-1.4, spring up beside the flank 1.5-1.6, over the back 1.7-1.8, seated 1.9 (ground -> seat ~0.3-0.4 s), wings folded then spread level; rider visible in every frame up to the lift. Dismount (`s3`): visible in every frame, rises out of the seat 2.5, beside the flank 2.65, on the grass 2.8. Still off (minor): at the first wing beat of the take-off the near wing hides most of the rider for about 0.15-0.2 s (2.65-2.8; head top / legs only). The fixers measured 0.15 s; I see up to 0.2 s. The hero still has no mount clip (idle -> ride blend). |
| 3 | Flight: left stick only, camera, Pegasus animation | **Fixed** | Owner: Pegasus thrown round the frame / off-screen 4.5 s, horizon 10-15 deg, upright horse with a hanging tail. Steer probe, 59 samples: pair centre x 0.49-0.51, y 0.65-0.67, camera lag <= 14.0 deg, roll <= 3.7 deg, first frame of take-off already centred (0.50, 0.66). The right-stick actions changed nothing; the mouse handler is now empty (`_unhandled_input` = pass, read in code; not driven by a probe). Approach to the ring: camera stays behind (sea 13.5-15.0). Take-off side view (mount 2.6-3.15): body nose-down, forelegs tucked, hind legs trailing, tail streaming back, full wing strokes; from behind (sea 5.0-6.4 every 0.2 s) the wings go from a high V to below level each beat. Still off (cosmetic): from behind the two blue hind hooves show under the rump. Not flown by a person yet. |
| 4 | NEW creatures on the islands | **Fixed for the Cyclops, partly for Medusa / Hydra** | Owner: no creature on any island. Cyclops (`s5b`): walks its loop on the grass to the right of the pair, club in hand, position changes every 0.5 s, readable 9.0-12.5 s of the trip (~5 s), hidden behind the stone blocks from 13.0 until landing. Medusa (`s5c`): a small green figure right of the colonnade at 15.5-17.5 (about 35-40 px tall at 1280x720), gone behind the near wing / colonnade by 19.0. Hydra: a small magenta figure on the volcano shelf at 24-27 s and at the ring (~45 px). Both are recognisable but small; legs cycling could not be judged at that size. `--defeated=cyclops` showed Medusa and the Hydra, not the Cyclops. Landing and the fight start are unchanged (ring_enter 14.99, land 15.02, fight 18.53). |
| 5 | NEW strike effects + damage | **Mostly fixed** | Owner: whole-body white flash, a few dots, nothing stays. Now (`s6`): cyclops hit 2 (11.19) shows a gold star burst + ring + sparks at the forearm at 11.23 / 11.30; at 11.60 two glowing gold cut marks sit on the forearm and stay (19.30 after 4 hits). Hydra (8.42, 20.16): a cyan burst + cyan droplets at the jaw (8.53, 8.65). Still off (minor): (a) the whole boss still turns near-white for 2 frames (cyclops 10.90, hydra 8.47 and 20.20) and on the FIRST cyclops hit no star was visible in any 30 fps frame (10.90 flash, 10.94 / 10.98 only small gold dots); the owner's acceptance says the flash must not hide the new effects; (b) on the Hydra the burst sits beside the hero at the lowered jaw and is drawn at 0.6x (hero between camera and cut), so it reads small; (c) the sword trail is faint (a thin pale arc at 11.23), hit-stop and shake could not be judged from stills (code: 0.06 s, 0.35, unchanged from before). Hydra wound marks not checked in frames. |
| 6 | Clipping | **Mostly fixed** | Owner: head inside the Cyclops leg, standing inside the club, inside the lowered Hydra head. Now (`s7`): in both stuck phases (9.6-10.6, 17.6-19.6) the hero stands in front of the shin and beside the club shaft, not in them; at the lowered Hydra head (8.0-8.3, 19.8-20.5) he stands in front of the head. Probes (vfx re-fixer): legs <= 0.05 m inside, club <= 0.02 m, snout -0.01 m. Still off (minor, by design): his sword arm enters the Hydra's head on every jaw strike (the jaw weak point sits inside the mesh; 8.6). Unconfirmed / not recorded: the home urns (they have collision: `EnvKit.prop` collide=true, so the 1:35 overlap was probably camera parallax) and the flight camera at the volcano landing (`CAM_GROUND_CLEAR` 3 m added; my Hydra trip stopped at the ring, not inside the landing). |

## 3. Frame times
**Fully cold fights** (new HOME + new Metal bundle id, `freeze_probe.gd`, 1920x1080, `--bot=win`, speed 1, load 2-4):
- Cyclops to victory (37.47): **0 frames over 50 ms after fight start**; the largest listed frame 25.8 ms (first slam,
  t 9.19). Hit frames 4.2 / 5.5 / 2.9 / 3.3 ms. Hits 10.83 / 11.17 / 18.73 / 19.08 (same fight as before).
- Hydra to t 25: **1 frame over 50 ms**: 60.5 ms at t 2.41, the first frame after fight_start, with 0 pipeline compiles
  (a load frame: HUD bar + music start; freeze_fix measured 36-52 ms there). Hit frames 3.8 / 4.9 ms. No shader freeze.

**Sea flight with the creatures** (perf_probe, `--start=sea --bot=win` 14 s, 1920x1080, 120 Hz vsync, two A/B pairs,
one run at a time, load average 4.6 with the owner working):
| Run | avg ms | p99 | >16.7 ms | worst |
|---|---|---|---|---|
| creatures on #1 / #2 | 8.41 / 8.39 (119 fps) | 14.08 / 12.68 | 9 / 7 | 19.8 / 21.7 |
| `--no-island-creatures` #1 / #2 | 8.39 / 8.41 (119 fps) | 12.34 / 14.17 | 5 / 7 | 19.3 / 21.5 |
The creatures cost nothing measurable (same averages, spike counts overlap). Neither variant meets "99 % under 11.1 ms"
on this loaded machine; the 17-22 ms frames come about once a second in both variants (not caused by this wave).

## 4. Still open (severity)
1. **Minor** - take-off: the near wing hides most of the rider for ~0.15-0.2 s at the first wing beat after the mount.
2. **Minor** - strike flash: the 0.08 s whole-body white flash whitens the boss for 2 frames; on the first Cyclops hit the
   new star burst was not visible in any frame (shorten/weaken the flash or start the star a frame later than the flash).
3. **Minor** - Hydra hit effect reads small (0.6x at the hero's side at the lowered jaw); the sword trail is faint.
4. **Minor** - Medusa and the Hydra are small from the air (~35-45 px at 1280x720); Medusa goes behind the near wing /
   colonnade within ~110 m; the Cyclops hides behind the stone blocks for the last ~2 s.
5. **Minor** - sword carry from the chase camera reads "down and a little out" (carry 25 deg outward); the reach strike's
   flat leads on f12 (0.64, after the hit window) - accepted by the sword re-fixer (needs a clip re-key).
6. **Minor (by design)** - the sword arm enters the Hydra's head on jaw strikes.
7. **Cosmetic** - from behind, Pegasus's hind hooves show under the rump in flight.
8. **Not verified** - the mouse in flight (code only), the volcano landing camera, the home urns, the Hydra's wound
   marks, hit-stop/shake in motion, legs cycling on Medusa/Hydra at island size. No person has played this wave.
9. **Info** - the first frame of a cold Hydra fight is 60.5 ms (no compile; was 36-52 ms); the sea p99 is 12-14 ms on a
   loaded machine with or without the creatures.

## 5. README.md lines for the lead
Controls table, row "Camera": `| Camera | Mouse | Right stick |` ->
`| Camera (on foot) | Mouse | Right stick |`

Controls, the "In flight" line (line 70) -> "In flight: the left stick / WASD steer (left/right turns, up climbs, down
dives); the camera follows behind Pegasus by itself (the right stick and the mouse do nothing). Menus: A or Enter
accepts, B or Esc goes back, and the D-pad, left stick or arrow keys move the selection."

How a playthrough goes, item 2, replace "The wings open as you press it, and the hop takes about a second." with
"The hop takes about a second: Hercules steps in, springs up beside the flank and swings over the back, and Pegasus
spreads its wings as he sits."

Item 3, add after the first sentence: "Each island whose boss you have not beaten shows that creature walking about on
it (drawn larger so it reads from the air)."

Known limits, replace the first bullet with: "The owner played the version before these fixes (Nov 23, 1 PM). The
fixes since (sword grip, mount and dismount, flight camera and Pegasus's flight clips, creatures on the islands, strike
effects and wounds, clipping) were checked by bots, probes and recorded frames only. Feel, difficulty, mouse camera
and sound are yours to judge."

Known limits, replace "During the mount and the dismount the near wing covers the rider for about 0.2 to 0.35 s." with
"During the mount and the dismount Pegasus spreads its wings level and the rider stays in view; at the first wing beat
of the take-off the near wing hides most of the rider for about 0.15 to 0.2 s. Hercules has no mount clip: he blends
from standing into the riding pose while he climbs."

Known limits, add under Animations:
- "Hercules carries the sword in a closed fist, blade forward and down beside his right leg. From the camera behind
  him it reads as pointing down and a little outward. In the reaching strike the flat of the blade, not the edge,
  leads for a moment just after the hit."
- "In flight, seen from behind, Pegasus's hind hooves show under its rump."

Known limits, add:
- "A weak-point hit shows a short sword trail, a star burst, ichor in a colour per boss (Cyclops gold, Medusa lime,
  Hydra cyan) and a glowing cut mark that stays until the fight ends (up to 12). The whole boss still flashes white for
  0.08 s; on some hits that flash covers the first frames of the burst. On the Hydra the burst sits beside Hercules at
  the lowered jaw and is drawn smaller."
- "Hercules is kept out of the Cyclops's legs and stuck club and the Hydra's lowered head (probes: at most 0.05 m
  inside). His sword arm still goes into the Hydra's head when he strikes its jaw."
- "From the air Medusa and the Hydra are small (about 40 px tall at 1280x720) and pass behind the near wing or the
  island's columns when you come close; the Cyclops walks beside your approach for about 5 s."

Known limits, "Not recorded in motion by anyone" bullet -> "Not recorded in motion by anyone: the new flight camera and
the mouse in flight (only the left stick / WASD steer now), the Hydra's side bites and Medusa's tail swipe (the bots
never trigger them). They were checked by probes and logs only."

Known limits, "First-use freezes" bullet -> "First-use freezes: every effect is drawn once while the island title card
is up. In fully cold test runs on Nov 23 (2 PM) the Cyclops fight had no frame over 50 ms (largest 26 ms) and the Hydra
fight one 60 ms frame at the moment the fight starts (no shader compile); the wait under the black fade before an
island is about 1.4 s longer the very first time."

Known limits, after the 120 fps bullet add: "Flying over the sea with the creatures on the islands: 119 fps average
(8.4 ms), the same with them switched off; on a busy machine 99 % of frames were under 12-14 ms."

## Finishing pass (strike burst + README, 2026-11-23 afternoon; owner at the Mac, not asked)
Scratch: `work/finish/` (`mov.sh` = gdwin 1280x720 movie at `--fixed-fps 60`, `hl.sh` = headless bots, `sheet.py`,
`mov/`, `logs/`, `frames/`). Every rendering run through `tools/godot_bg/gdwin` with a throwaway HOME; app and save
folder untouched; no git except `git diff`. All processes ended.

**Cause found.** The hit pause (`Game.hit_pause`, 0.06 s) sets `Engine.time_scale` to 5 %. Every tween slows with it,
so the whole-body flash stayed at 0.85 (white) and the star stayed at its 0.35x starting size for the whole pause
(about 4 frames at 60 fps). The star's centre was also inside the struck forearm (cut point 0.1 m toward the camera),
so the arm covered it. Before (60 fps, `mov/before_cyclops.avi`, hit at 10.85 = frame 651): frames 651-656 the Cyclops
is white, no star; the star shows only from frame 657.

**Changes (small, no contract, no timing changed: hit pause 0.06 s, shake, flash 0.08 s, tween lengths unchanged).**
- `game/scripts/visual/character_visual.gd`: `flash(color, seconds, strength := 0.85)` (new optional arg; other callers
  unchanged).
- `game/scripts/bosses/boss_base.gd`: weak-hit flash strength `WEAK_HIT_FLASH` 0.15 (was 0.85). 0.3 was tried first:
  Cyclops and Medusa kept their colour, the Hydra still went pale pink.
- `game/scripts/combat/fx.gd` `impact()`: the star starts at 1.15x and settles to 1.0x in 0.07 s (was 0.35x -> 1.0x);
  the ring starts at 0.55x (was 0.3x). The star/ring sits `IMPACT_FRONT` 0.45 x size toward the camera (out of the
  limb). Hero near the camera->cut line (Cyclops forearm, Hydra jaw, Medusa neck all hit this case): full size (was
  0.6x), pulled toward the camera only while it stays `IMPACT_HERO_GAP` 0.6 m behind the hero (Hydra beside him: 0),
  and its centre moved `IMPACT_NEAR_SHIFT` 0.25 x size away from him across the view (the cut stays inside the inner
  star). The hero is always drawn in front of it.
- `fx.gd` `slash()`: cut streak `SLASH_WIDTH` 0.34 m (was 0.22), edge alpha 0.8 (was 0.55), hold 0.16 s (was 0.1),
  fade 0.2 s (was 0.18). Glance streak keeps its 0.45 strength (still faint, as intended).
- No new material kind (star, ring and streak are still the "ribbon" material; ichor/sparks the "dot"), so the warm-up
  set (`warm_fx.tscn`, docs/notes/freeze_fix.md) was not rebuilt.

**Proof (60 fps, 12 frames after each first hit, looked at).**
- Cyclops (hit 10.85, frames 651-661): the boss stays purple (slightly lighter), a full-size gold star in front of the
  forearm from frame 651, the ring growing round it to 661; hero in front of it in every frame.
- Medusa (8.43, frames 506-516): she stays green; a large lime star behind the hero from 506, ring to 516; a lime-white
  streak beside the shield from 511.
- Hydra (8.43, frames 506-515): a full-size cyan star + ring at the jaw on his shield side from 506, not over his body;
  the Hydra still turns pale pink for frames 506-511 (the volcano's glow amplifies even the 0.15 flash). Still open.
- Sword trail: wider, but on the Cyclops's first hit (early in the swing) it is still short and hard to see in stills.
- Headless `--bot=win --speed=3 --seed=11` after the last change: cyclops victory 36.78, medusa 26.21, hydra 99.12
  (identical hit times to before: cyclops 10.85 / 11.19 / 18.77 / 19.11); 0 SCRIPT ERROR / Parse Error / ERROR /
  WARNING lines in these 3 logs and the 3 final movie logs.
- Devlog: `docs/devlog/media_inbox/feedback2_finish/strike_burst_first_hit_before_after.jpg` (+ captions.txt).

**README.md**: section 5 lines applied (camera row, in-flight line, playthrough items 2 and 3, Known limits: owner
played the earlier version, mount/dismount wing, sword carry, hind hooves, strike effects with this pass's result,
clipping, creatures from the air, not-recorded list, first-use freezes, sea-flight fps). No still-true limit removed.

**Not done / open:** the Hydra's pale-pink 0.1 s flash in the volcano (a per-boss lower strength, e.g. 0.06 via an
overridable var, would fix it; not tried for time); no cold-cache freeze run (no new material, same code paths);
the Medusa/Hydra later hits and wound marks were not re-recorded.
