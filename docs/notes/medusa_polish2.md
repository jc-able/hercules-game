# Medusa polish 2 (2026-11-23 morning, owner at the Mac; decisions marked **Decision**)

Files changed: `game/scripts/bosses/medusa.gd`, the `MEDUSA` dictionary in `game/scripts/data/tuning.gd`.
Not changed: `medusa_arena.gd`, `medusa.glb` (no texture edit was needed), anything else. No imports, no git.
Scratch: `work/medusa_polish2/` (probes, logs, movies `movie/before.mp4` + `movie/after1.mp4`, sheets).
Devlog JPEGs: `docs/devlog/media_inbox/medusa_polish2/` (+ captions.txt).

## 1. Natural movement (owner, today: "no static pose ... a little stiff")
What was wrong (movie `before.mp4`, 30 fps, seed 11): turning to face the hero played `idle`, so a 120 deg turn was the
idle pose rotating like a statue (1.4 s); the slither always played at 1.0 and the body jumped 0 <-> 3.2 m/s in one
frame; the gaze started with a dead stop; action blends were 0.10-0.15 s; the tail swipe was cut back to idle at clip
1.53 of 2.25 s.

What changed (medusa.gd):
- `_update_loco()` (after move_and_slide, every physics frame) measures what her body really did: ground speed and turn
  rate. Effective speed = max(ground speed, turn rate x `slither_turn_radius` 2.2 m). In stalk the slither plays whenever
  that is >= 0.45 m/s, at rate = effective speed / reference (manifest `move_speed` of `slither` when the new clips have
  one, else `slither_speed` 3.2), clamped to Tuning.ANIM_SPEED_MIN/MAX. Idle only after 0.25 s under 0.2 m/s.
  No clip length / stride is hard-coded.
- Stalk speed ramps (6 m/s^2) and brakes into the target (v = sqrt(2 a d)); the gaze brakes over ~0.35 s (`_coast`)
  instead of `halt()`.
- Blends: idle <-> slither 0.35 s (`loco_blend`), into gaze / tail_swipe / stun_start / rise 0.25 s (`action_blend`,
  was 0.10-0.15).
- Back to stalk after a one-shot that still has its recovery (tail swipe, gaze, rise): the clip plays out and hands over
  to idle/slither with the loco blend (or at once if she has to move).
- A hurt flinch over the slither is left alone (BossBase resumes the slither; the rate is re-applied next frame).

Measured (probe `work/medusa_polish2/anim_probe.gd`, movie strips at 30 fps):
| Moment | before | after |
|---|---|---|
| turn 120 deg in place (90 deg/s) | clip idle x1.0 | slither x1.04-1.08 (effective 3.3-3.46 m/s) |
| approach from 15 m | slither x1.0 at 3.2 m/s from frame 1, hard stop | x0.60 -> 0.99 (0.5 s) -> 1.00 -> 0.60, stops at 7.7 m, idle 0.25 s later |
| gaze start | dead stop, blend 0.12 | brake ~0.35 s, blend 0.25 |
| tail swipe end | cut to idle at clip 1.53/2.25 | recovery plays out, then slither/idle 0.35 |
Snap meter (`anim_snap.gd`, largest bone-head jump per 60 Hz frame in her own frame; old blends vs new): approach
0.331 -> 0.234 m, turn 0.328 -> 0.241 m, tail end 0.350 -> 0.254 m, gaze end 0.026 both. The largest jumps left are the
attacks themselves: the gaze fire lunge (hair_r_01 0.78 m at fire) and the flat tail sweep (tip 3.36 m/frame = 707 deg/s).
Not changed: during the gaze windup she still turns at 180 deg/s with the gaze clip on (it only happens with the hero
within 25 deg, so it is a small correction); the 3 m stun recoil slide is a knock-back on the stun_start clip.

## 2. Tail reaction (open item 1) — **Decision: `tail_radius` 9.0 -> 8.0, nothing else**
Probe `work/medusa_polish2/tail_probe2.gd` (from fixer 3's probe): forced swipe, hero placed at a random angle (seeded)
and distance from her body centre, 50 trials per cell (half enraged); "roll" = locked on, hold back, ONE roll at the
reaction time then keep backing off; "run" = lock off, run straight out. Hits / 50:

| react | mode | hug 2.4-4.0 m | 4 m | 5 m | 6 m | 7 m |
|---|---|---|---|---|---|---|
| ring 9.0 (before) 0.35 | roll | 3 | - | 0 | 0 | 0 |
| 0.5 | roll | 13 | - | 0 | 0 | - |
| 0.7 | roll | **28 (56 %)** | - | 0 | 0 | - |
| 0.9 | roll | 41 | - | 0 | 0 | 0 |
| 0.5 / 0.7 | run | 0 / 0 | - | 0 / 0 | - | - |
| **ring 8.0 (after)** 0.7 | roll | **1 (2 %)** | **0** | 0* | 0* | 0* |
| 0.9 | roll | 12 (24 %) | 0 | 0* | 0* | 0* |
\* a smaller hit radius cannot add a hit (same timing, same hero path), so the 0-hit cells at 9.0 stay 0; 0.35 / 0.5 s can only improve.
All hugging hits at 9.0 started 2.4-3.6 m from her centre; the 0.7 s miss at 8.0 is one case at 2.4-2.6 m.

Why the ring and not the fill time: a hugging hero needs (radius + 0.19 - start) m in (coil - reaction); one roll is
4.8 m and backing off locked is 2.4 m/s, so 1 m less radius saves ~0.4 s, the same as a 2.2 s fill but without slowing
the fight. The rule stays "roll out of the ring before it fills"; the ring decal, the hit and the green sweep crescent
all use `tail_radius`, so what you see is still what hits. The trigger (6.0 m for 1.5 s) and the fill (1.8 s) are unchanged.

**For the lead's README / SPEC §10.1 (Medusa tail_swipe row)**: "Ring = hit radius **8.0 m** from her body centre (was
9.0), fills in 1.8 s ... One roll 0.7 s after the ring appears clears it from 4 m and beyond every time (0/50) and from
beside her body 49/50; unlocked running out always works (0/50 at 0.7 s)."

## 3. Snake-hair patches (open item 8) — fixed in her material, no texture change
Texture: one 2048x2048 PNG atlas (`medusa_albedo`), islands scattered. Of the 8,776 vertices skinned > 50 % to the six
`hair_*` bones, 19 % sample warm texels (hue 12-67 deg, sat 0.68-0.99) bled in from skin and gold-armour islands (59 % are
green, hue 86-133). A UV-region fix is impossible (skin and gold are everywhere in the atlas).
Fix (`_hair_recolour()`, hydra.gd's pattern): her own copy of core's toon shader gets a `vertex()` that sums
BONE_WEIGHTS of the skin binds named `hair*` (bind indices read from the Skin at load: 6, passed as two ivec4 uniforms)
and, in the fragment, repaints warm texels (brown / orange / yellow, green 0.3-1.2x red) snake green where that weight
is > 0.35-0.6. Pure reds (the forked tongues) are kept. Gold armour, skin and face are untouched (not hair-skinned).
Close-ups before/after: `medusa_polish2_hair.jpg`. Side effect: the small yellow snake eyes turn light green too.
The shader skips itself with a warning if core's toon shader ever gets its own `vertex()` or loses the tint line.

## 4. One place for numbers (open item 9)
`Tuning.MEDUSA` now holds the as-built values and medusa.gd reads only it (`T = Tuning.MEDUSA.duplicate(true)`):
DEFAULTS, AS_BUILT, TAIL_HIT_R and TAIL_COIL are gone. Changed keys: keep_min 9 -> 7, keep_max 14 -> 10, gaze_max_dist
10 -> 9, stalk_area 17 -> 12, tail_trigger_dist 5.5 -> 6.0, tail_coil 0.7 -> 1.8, tail_radius 7.0 -> 9.0 (then 8.0, task 2),
tail_sweep_radius removed (unused). New keys for the locomotion pass: slither_accel, slither_turn_radius,
slither_start_speed, slither_stop_speed, slither_stop_hold, loco_blend, action_blend. The constants left in medusa.gd
are model measurements (scale S, bone chains, clip spans, offsets) and visuals.
Proof (refactor alone, before the animation change): bot win seeds 11 / 4242 / 7 = 26.17 / 25.30 / 27.27 s before,
26.21 / 25.30 / 27.25 after; lose died 55.73 -> 55.72; --pad 26.21 -> 26.23 (headless run-to-run noise is ~0.04 s).

## 5. Regression (headless, --speed=3, all changes)
| run | before | after |
|---|---|---|
| win seed 11 | victory 26.17 s, 3 gazes, 0 hits | victory 26.19 s, 3 gazes, 0 hits |
| win seed 4242 | 25.30 | 25.29 |
| win seed 7 | 27.27 | 27.28 |
| lose seed 11 | defeat, died 55.73 (4 gaze hits) | defeat, died 55.74 (4 gaze hits) |
| win --pad seed 11 | 26.21 | 26.22 |
No SCRIPT ERROR / Parse Error in any log; windowed gdwin runs (movie, hair shots) print no shader errors.
None of the bot fights triggers a tail swipe (the bot keeps 7.5 m), so task 2 is proven by the probe only.

## Requests for the lead
- README + SPEC §10.1 Medusa tail row: hit radius 9.0 -> 8.0 and the new probe numbers (text above).
- When the new slither clip lands, give it a `move_speed` in medusa_clips.json (planted-foot = tail-wave ground speed);
  medusa.gd then uses it instead of slither_speed 3.2 automatically.
- final_check §4 items 1, 8 and 9 can be closed.

# Polish 3: re-fix after the independent review (2026-11-23, about 09:20-10:10)
Files: `game/scripts/bosses/medusa.gd`, the `MEDUSA` dictionary in `tuning.gd`. Not changed: medusa_arena.gd, medusa.glb
(no image edit, no import). Scratch: `work/medusa_polish3/` (regress.sh, probes copied from the reviewer, logs, movie
`movie/person.avi`, strip `strip_after.jpg`, hair shots `hair2/`). Devlog: `medusa_polish3_moves.jpg`, `medusa_polish3_hair.jpg`.

## Findings, each checked first
1. **Backwards glide (major): confirmed and fixed.** Reviewer's person probe (`person_probe.gd`, real input) before:
   she slid back at 3.2 m/s with the forward slither at x1.0. My first try (the arc target turned around the HERO) made it
   worse: she circled him tangentially at 3.2 m/s (trace `logs/person_trace.log`: d stayed 4.6 m while she covered 3 m).
   **Decision**: the arc turns HER path: she backs off 55 deg (`retreat_arc_deg`) to the side with more room (kept for
   the whole retreat), always at `slither_back_speed` 1.4 m/s. `_update_loco` keeps a smoothed signed speed along her
   facing (`_loco_fwd`); below `slither_back_play` -0.3 m/s the slither loop plays backwards (`_slither_rate()` < 0).
   After (`logs/movie_person2.log`, segment E): v 1.40, clip slither -0.60, d 4.6 -> 5.5 m in 1.1 s, then the tail ring.
2. **Gaze end snap (major): confirmed and fixed.** She leaves the gaze only when the neck window is shut AND the lean
   weight < 0.1 (safety: 3 s), the gaze clip holds its last frame meanwhile (seek clamped to the clip length), the lean
   eases out over `lean_out_time` 0.9 s (gaze / stalk; rise, recoil, stun keep rise_time 1.2), the hand-over blend is
   `gaze_exit_blend` 0.5 s, and for `post_gaze_turn_time` 0.4 s she turns at most `post_gaze_turn_deg` 45 deg/s. The lean
   goal no longer counts "gaze and fired" after the beam (only the neck window). Movie f523 -> f547: she rises over
   ~0.8 s on the held gaze pose (was ~0.2 s), yaw unchanged (-118) until the stalk. Cost: the miss case of a gaze lasts
   ~1.0 s longer, a gaze HIT ~0.2 s longer (lose bot dies 0.6 s later, below).
   Not measured: the reviewer's 0.25 m/frame bone-jump target with `anim_snap.gd` (no time left); the strip is the proof.
3. **Hair patches (major): confirmed, partly fixed.** Stats of the hair-skinned vertices (weight > 0.6, 8,579): 30 % sample
   red to orange-red texels (hue 340-15 deg), median g/r 0.15-0.29, not only tongues. **Decision** (the reviewer's
   cheaper middle step, without the sat < 0.9 guard because the orange-red patch texels have sat 0.92): deep in the hair
   (hair_w > 0.6) the red cut drops from g/r 0.26-0.36 to 0.17-0.24 (deep-red tongues kept); bright yellow (value > 0.62-0.72,
   g/r > 0.75-0.85) is kept for the eyes; the replacement green is the texture's own snake green (median 0.05, 0.33, 0.07),
   value 0.18-0.42 (was up to 0.5: read as pale). Result (`hair_zoom.jpg`): the orange-red patch on the back snake head is
   gone, the orange mouth rim mostly gone. **Still wrong**: pale mint blobs where the yellow patches / snake eyes were (the
   eye-keep rule does not catch them; they are lighter, less saturated texels that get only a partial mix). The real fix
   is the reviewer's UV mask (rasterise hair triangles to a 512 R8 mask, exclude tongue and eye islands, ship it as her
   own texture under the import lock). Not done: it needs an import and more than the time left.
4. **Turn without angular acceleration (minor): confirmed and fixed.** `face_towards` keeps a signed `_yaw_rate` that
   moves toward min(cap, |angle left| x `turn_ease` 4.0) at `turn_accel_deg` 360 deg/s^2 (reset after a frame without a
   turn). The tail-gap refusal / long-way detour is kept and also guards a turn that is still unwinding the other way.
5. **Tail swipe dead stop (minor): confirmed and fixed.** tail_swipe keeps her speed and brakes with `_coast` over
   `tail_brake_time` 0.35 s; the ring decal follows her body centre while she brakes. With the 1.4 m/s back-off the drift
   is ~0.1 m (movie: v 1.40 -> 0 in ~0.2 s).
6. **Timeout gaze statue turn (minor): fixed.** The +2.5 s timeout gaze starts only within `gaze_timeout_angle` 60 deg;
   until then the slither keeps turning her.

## Tail reaction probe (task 2) after polish 3
`work/medusa_polish3/tail_probe3.gd` (= tail_probe2), ring 8.0 m, fill 1.8 s, trigger 6.0 m / 1.5 s, one roll:
| react | hug 2.4-4.0 m | 5 m and beyond |
|---|---|---|
| 0.35 | 0/50 | 0/50 |
| 0.7 | 1/50 (2 %, the one case at 2.4 m) | 0/50 |
| 0.9 | 12/50 (24 %) | 0/50 |
Same as polish 2: the probe forces the swipe with her standing, and the brake only acts when she moves. README numbers
for the lead stay as written above (ring 8.0 m). Gameplay note: a hero who chases her now closes in (she backs off at
1.4 m/s, not 3.2), so the 6 m / 1.5 s trigger is reached sooner when chasing: in the person probe the ring came 1.1 s
after he stopped at 4.6 m. That is the intended "do not hug her" rule.

## Regression (headless, --speed=3; pre = this morning's shipped polish 2, after = all of the above)
| run | pre | after |
|---|---|---|
| win 11 | victory 26.20 | 26.21 |
| win 4242 | 25.30 | 25.28 |
| win 7 | 27.26 | 27.27 |
| lose 11 | died 55.71 (4 gaze hits) | died 56.32 (4 gaze hits; each gaze hit holds ~0.2 s longer for the neck window) |
| win --pad 11 | 26.22 | 26.22 |
0 SCRIPT ERROR / Parse Error. Windowed runs: no shader errors. (One of my first movie runs died on a Parse Error in
player.gd while another agent was editing it; it was stopped and re-run.)
