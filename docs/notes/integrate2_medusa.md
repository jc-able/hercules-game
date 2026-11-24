# Medusa integrator 2: the new natural clips in the fight (2026-11-23 ~10:40-11:15, owner at the Mac)

Owner at the Mac, no questions: every decision is mine and written down. Godot rendered only through
`tools/godot_bg/gdwin` (off-screen, throwaway HOME), everything else headless. `builds/Hercules.app`, the GLB, the
manifest and the clip keys were not touched (no event / move_speed correction was needed). No import, no git.
Files changed: `game/scripts/bosses/medusa.gd`, the `MEDUSA` dictionary in `game/scripts/data/tuning.gd`.
Scratch: `work/integrate2_medusa/` (probes, logs, `movie/after.avi` + `movie/final.avi`, `strips/`).

## Probes (all in work/integrate2_medusa/)
- `movie_probe.gd`: the whole fight from the chase camera (start idle, approach from 15 m, stop, 120 deg turn,
  back-off, gaze, gaze + neck cut (hurt/recoil), reflected gaze (stun_start / stunned / rise), forced tail swipe with
  rolls, killing blow while stunned) + a snap meter: largest bone-head jump per 60 Hz physics frame in her own frame,
  per phase (`[SNAP]`), every jump > 0.4 m printed (`[J]`). `--old-blends` = the old 0.35 s idle/slither fades.
- `clip_speed_probe.gd`: the clips' own largest bone jump per 1/60 s at 1x (game metres).
- `phase_probe.gd`: distance of every slither phase from the idle stance. `death_join_probe.gd`: stunned -> death join variants.
- `lean_probe.gd`: a gaze with the hero stepping out of the fan to 35 deg at 5 m: neck mark during the window.
- `tail_probe4.gd` (= polish 3's tail_probe3) and `regress.sh` (win 11/4242/7, lose 11, --pad 11, headless --speed=3).

## What changed and why (measured; snap = largest bone jump per 60 Hz frame, game metres)
| What | Before | After |
|---|---|---|
| idle <-> slither fade (owner: no pop). The new slither tail trails straight back, the idle tail curls round her: tail tip 4.3-5.6 m apart at every slither phase (`phase_probe`: best phase 0.958 s still 4.25 m, so no phase trick; slither starts at 0) | 0.35 on the clip clock (real 0.35 s to stop, 0.35-0.58 s to start) | **`loco_blend_start` 0.75 s / `loco_blend_stop` 0.8 s in REAL seconds** (medusa.gd multiplies by the clip rate, because the boss AnimationPlayer fades on the scaled clock). A one-shot that hands over to the slither also uses the start fade. Snap approach 0.223 -> **0.151**, stop 0.265 -> **0.136**, turn 0.296 -> **0.184**, back-off stop 0.310 -> **0.157**; tail tip 0.44 -> 0.27, 0.31 -> 0.17, 0.56 -> 0.33 m |
| hurt (neck cut out of the gaze lunge) | `hurt_blend` 0.08 (BossBase default): hand_r 0.88 m/frame | **Medusa `hurt_blend` 0.2**: 0.57 (hair_r_01; the clip's own hair whip is 0.32) |
| death while stunned (the join onto the floor part of the death clip) | join at clip 2.25 s, 1.0 s fade, restarting `stunned` at 0: tail_13 2.0 m in the first frame, hand_l **2.58 m** in one frame at clip 2.58 s (the left arm of the new death clip crosses a blend flip there: plays clean alone, jumps when faded with another pose) | **`DEATH_FROM_FLOOR` 2.6, `DEATH_JOIN_BLEND` 0.6 s, the fade starts from the clip and time she really had** (`_pre_clip`, `_pre_clip_pos`, recorded each physics frame; stunned / stun_start / rise): max **0.62** m/frame, a steady 0.6 s slump, no pop |
| `SNAP_EYES_LOCAL` (camera fit point for the eyes after the fire snap) | (0, 8.93, 4.20) | **(0, 8.48, 3.90)**: measured eyes (-0.07, 8.44, 3.65) at clip 2.0 and (-0.05, 8.13, 4.02) in the stare |

## Checked, unchanged (numbers)
- **Idle (fight start, 4 s strip)**: arms relaxed (right hangs, left raised palm), breathing and weight shift read; clip
  max 0.029 m/frame (tail tip), no pendulum.
- **Stalk**: slither rate = effective speed / manifest `move_speed` 3.2 (approach x0.6 -> 1.0, turn in place x1.04-1.08,
  back-off x-0.6 reversed). Stop on the target, idle after 0.25 s still, then the 0.8 s fade.
- **Gaze** (events unchanged, fire_start 2.0, fire_end 3.25; windup clip speed 1.67x, beam 1.25x): eyes at fire
  y 8.55-8.75 (bot fights, `gaze_fire eyes_y`), windup eyes (-0.07, 8.8, 0.36). Stare held: clip 2.0 -> 3.25 over the 1.0 s
  beam. Neck mark: windup/fire on the neck side toward the hero at y 7.35-7.68 (high = not reachable, as designed);
  hero out of the fan -> lean 1.0 after 0.3 s, neck (-0.06, **2.11-2.25**, 6.87) in her frame = inside NECK_Y 1.0-2.3 and
  the sword box; it eases up over 0.9 s after the window. Hero in the beam (petrified) -> no lunge (lean 0), as coded.
- **Stunned**: neck socket (0.01, **1.45**, 6.81) in her frame both 0.35 s and 1.87 s into the loop = STUN_NECK_LOCAL
  (0, 1.425, 6.825); stun_down neck_y 1.66 -> 1.44-1.45 at the cuts. Bot cuts 2 per stun, 0 glances.
- **Tail ring rule** (`tail_probe4`, ring 8.0 m, fill 1.8 s, one roll): react 0.35 s: 0/50 in every cell (hug, 5, 6, 7 m,
  roll and run); react 0.7 s: hug 1/50 (the one case at 2.4 m, 165 deg, same as polish 3), 0/50 everywhere else. The
  rule is still true with the new poses. Tail capsules follow tail_05/08/11/14 live, so the trailing slither tail is
  what collides.
- **Regression** (headless --speed=3): see the table at the end.

## Still wrong in the clips (for the animation fixer; not fixable in code without slowing the move)
1. `stun_start` 1.43-1.58 s: both hands (hand_r 1.43, hand_l 1.52-1.56) and hair_l_01 (1.30-1.47) travel 0.80-0.82 m per
   1/60 s at 1x (game m; ~49 m/s): the arms fall onto the floor in about 2 frames. In the game (x1.3) 1.06 m/frame: a
   visible pop at the end of the collapse. Fix: spread the hand drop over 0.25-0.3 s (keys 1.35 -> 1.625), keep the end
   pose (= stunned frame 0).
2. `death` 1.85-1.90 s: hair_l_01 1.54 m per 1/60 s (92 m/s): one snake whips in 3 frames. Fix: add an in-between or
   ease the hair_l_01 key at ~1.875 s.
3. `death` ~2.55-2.6 s: the left-arm rotation track (shoulder/upper arm/forearm chain to hand_l) crosses a quaternion
   hemisphere flip: invisible when the clip plays alone, a 2.5 m one-frame hand jump whenever it is cross-faded with
   another clip over that time. The code now joins at 2.6 s; a re-bake with sign-continuous quaternions would make any
   join safe.
4. (minor, known) the gaze fire lunge: hair_r_01/hair_l_01 0.47 m/frame at 1x around 1.92-2.0 s (0.78 in the game at
   1.67x windup speed). It is the strike itself; leave unless the owner notices.

## Regression (headless, --speed=3; before = animfix2's runs on the same GLB without these code changes)
| run | before | after (first) | final |
|---|---|---|---|
| win 11 | 26.19 | 26.22 | 26.20 |
| win 4242 | 25.29 | 25.29 | 25.31 |
| win 7 | 27.28 | 27.28 | 27.26 |
| lose 11 | died 56.32 (4 gaze hits) | died 56.33 (4) | died 56.31 (4) |
| win --pad 11 | - | 26.21 | 26.21 |
0 SCRIPT ERROR / Parse Error in every log. The bot reflects every gaze and keeps 7.5 m, so it never triggers a tail
swipe or a gaze neck cut; those are proven by the probes above.

## Devlog
`docs/devlog/media_inbox/integrate2_medusa/` (+ captions.txt): stalk/turn/back-off movie clip, gaze strip, death-join
strip and clip.
