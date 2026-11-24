# Hydra assembly 2: natural-animation pass (assembler, 2026-11-23)

The owner was at the Mac. Blender ran only headless (`tools/ak`). Godot rendered only through `tools/godot_bg/gdwin`
(off-screen, no focus, no sound). `builds/Hercules.app` was not touched. Nothing was generated, no credits were spent, and
nothing was committed. Scratch, scripts and logs are in `work/assemble2_hydra/`.

## Files written
- `art_src/chars/hydra/backup_20261123/hydra.glb` and `hydra_clips.json`: the GLB and manifest from before this pass
  (assembled 11-22 21:12).
- `art_src/chars/hydra/clip_sources.json`: maps each clip to the action file that was merged (the newest source).
- `art_src/chars/hydra/hydra.blend`: 17 actions re-baked by `ak merge` (rig hash e682e3c4dce2, unchanged).
  The blend from before the merge is kept in `work/assemble2_hydra/hydra.blend.pre_merge_backup` (a backup only; never
  render from it, its texture paths are relative).
- `game/assets/characters/hydra/hydra.glb` (10.90 MB, was 10.39 MB) and `hydra_clips.json`, plus Godot's re-import.

## Sources (`clip_sources.json`)
| clip | action file | source |
|---|---|---|
| idle | `clips/idle_n/action_idle.json` | new video idle_n (anim2) |
| walk | `clips/walk_n/action_walk.json` | new video walk_n (anim2) |
| bite, bite_l, bite_r | `clips/bite/action_bite*.json` | re-base (`rebase_done.json`) |
| fire_sweep, fire_sweep_l, fire_sweep_return, fire_sweep_return_l, head_down, head_up | `clips/fire_sweep/action_*.json` | re-base |
| hurt, hurt_standing | `clips/hurt/action_*.json` | re-base |
| stomp, stomp_r | `clips/stomp/action_*.json` | re-base |
| death, death_standing | `clips/death/action_*.json` | re-base |

`rebase_done.json` was already there when I started (09:21), so I did not have to wait for it. The 15 re-based paths
come from that file. No `*.rest_v1.json` file was merged; the script that builds the list asserts this, and it also
asserts that each file's internal action name matches its clip.

**Idle first pose and natural stance.** The new idle's first pose matches the re-based one-shots' first pose. I measured
this in the GLB as the largest local-rotation difference on any of the 76 bones: 0.0 deg for bite, bite_l, bite_r,
fire_sweep, fire_sweep_l, stomp, stomp_r and hurt_standing. The animator also measured 0.0 deg against
natural_pose.json. So the re-baser's tool did not need to run again.

The one-shots end within 0.05-0.3 deg of the idle's first pose (bite 0.3, stomp 0.27, head_up 0.05). The only
exceptions are the clips that end in their own pose by design: the fire_sweep* family, hurt and head_down end on the
chin rest, and death and death_standing end lying down.

## Commands
```
P=$(python3 -c "import json;print(' '.join(json.load(open('art_src/chars/hydra/clip_sources.json'))['clips'].values()))")
tools/ak merge art_src/chars/hydra/hydra.blend $=P          # zsh: $=P splits the list. 6.3 s, 17 merged/rebaked/replaced
tools/ak export art_src/chars/hydra/hydra.blend --out game/assets/characters/hydra/hydra.glb \
    --clips-json game/assets/characters/hydra/hydra_clips.json                    # 4.6 s, export fps 30
python3 work/assemble2_hydra/finish_manifest2.py   # = assemble_hydra/finish_manifest.py (sockets, offsets, weak_points,
                                                   #   size, source date 11-23) + walk move_speed 1.73
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
tools/godot_bg/gdwin --path game --resolution 1280x720 --script $PWD/work/assemble_hydra/probe.gd -- <out> --harness
Godot --headless --path game --script $PWD/work/animfix_hydra/probe_fix.gd -- --harness
tools/godot_bg/gdwin --path game --resolution 1280x720 --fixed-fps 30 --write-movie <abs>/after.avi \
    --script <abs>/work/assemble2_hydra/movie.gd -- --harness [--before]
python3 tools/clip_motion.py hydra; python3 work/assemble2_hydra/group_motion.py <glb> <json>   # FK per limb group
python3 work/assemble2_hydra/skin_ground.py <glb> <json>     # lowest skinned vertex per frame (numpy skinning)
```
The export retimed `death` from 3.7917 to 3.8 s (-0.22 %, the 24 -> 30 fps grid), the same as on 11-22.

## Manifest: old vs new, key by key
| key | result |
|---|---|
| sockets, socket_offsets, offset_space, weak_points (`jaw: jaw_c`), size | identical |
| source | `assembled` 2026-11-22 -> 2026-11-23 |
| clip names | the same 17 |
| idle | length **3.0 -> 6.0 s**, loop true, no events |
| walk | length 2.1667 (unchanged), loop true, no events, **NEW `move_speed` 1.73** |
| all 15 other clips | length, loop and events identical |

**move_speed decision.** The animator measured the planted-foot speed at clip speed 1: 1.73 m/s for the forefeet (the
generator's value; the median is 1.72 for fl and 1.52 for fr) and 1.96 m/s for the hind feet. The animator suggested
1.8 m/s as a single value. I set **1.73**, because `hydra.gd _walk_rate()` multiplies the turn rate by the FOREFOOT
radius (r = 2.99 m measured in Godot), so the forefoot speed is the one that matches.

Until now the manifest had no `move_speed`, so the code fell back to 0.9x at 35 deg/s. It now takes the exact path:
deg_to_rad(35) x 2.99 / 1.73 = **1.06x** at the full 35 deg/s turn. The walk therefore steps about 17 % faster than
before at full turn rate, and proportionally slower during the ease-in and ease-out (clamped to 0.3-1.8).

## Lengths and events, old vs new (GLB = manifest = Godot AnimationPlayer, checked by probe.gd)
| clip | loop | old length | new length | events (old = new) |
|---|---|---|---|---|
| idle | yes | 3.0 | **6.0** | - |
| walk | yes | 2.1667 | 2.1667 | - (move_speed 1.73 new) |
| bite / bite_l / bite_r | no | 3.5 | 3.5 | impact 1.5 |
| fire_sweep / fire_sweep_l | no | 4.6 | 4.6 | fire_start 1.5, fire_end 4.05 |
| fire_sweep_return / _l | no | 2.7667 | 2.7667 | fire_start 0.0, fire_end 2.2 |
| head_down | yes | 1.5 | 1.5 | - |
| head_up | no | 1.5 | 1.5 | - |
| hurt | no | 0.9 | 0.9 | - |
| hurt_standing | no | 1.6333 | 1.6333 | - |
| stomp / stomp_r | no | 3.0 | 3.0 | impact 1.75 |
| death | no | 3.8 | 3.8 | - |
| death_standing | no | 5.5 | 5.5 | - |

## `python3 tools/clip_motion.py hydra` (bones turning >= 3 deg; before = backup GLB)
| clip | before | after | still frozen after (clip_motion list) |
|---|---|---|---|
| bite | 45/76 | 63/76 | feet bl/br, hips, leg_br_01, root, tail_01..08 |
| bite_l | 43 | 58 | feet bl/br, hips, jaw_c, leg_br_01, neck_1_03, neck_c_03..05, root, tail_01..08 |
| bite_r | 43 | 58 | feet bl/br, hips, jaw_c, leg_br_01, neck_5_03/04, neck_c_04/05, root, tail_01..08 |
| death | 63 | 69 | four feet, hips, root, spine_03 |
| death_standing | 60 | 69 | feet bl/br, hips, root, spine_01..03 |
| fire_sweep | 47 | 62 | feet bl/br, hips, leg_br_01, root, spine_03, tail_01..08 |
| fire_sweep_l | 47 | 63 | feet bl/br, hips, leg_br_01, root, spine_03, tail_01..07 |
| fire_sweep_return | 45 | 55 | four feet, hind legs, leg_f*_01, hips, root, neck_8_01/02, spine_02/03, tail_01..03 |
| fire_sweep_return_l | 41 | 53 | four feet, hind legs, leg_f*_01, hips, root, spine_02/03, tail_01..07 |
| head_down | 25 | 38 | all legs and feet, head_c, hips, neck_1_01, neck_4_01..04, neck_8_01/02, neck_c_01..05, root, spine_01..03, tail_01..08 |
| head_up | 47 | 53 | feet bl/br, head_8, hips, leg_br_01, neck_3_01/02, neck_4_01/02, neck_6_01..04, root, spine_03, tail_01..08 |
| hurt | 39 | 47 | all legs and feet, hips, neck_c_01/02, root, spine_01/02, tail_02..08 |
| hurt_standing | 51 | 53 | all legs and feet, hips, root, spine_01..03, tail_04/05 |
| **idle** | **0** | **39** | all legs and feet (planted), hips, root, spine_03, tail_02, the base links of necks 2, 3, 5, 6, 7, 8 and neck_c_01..04 |
| stomp | 25 | 50 | feet bl/br, hips, jaw_c, 18 mid neck links, root, spine_01..03, tail_06..08 |
| stomp_r | 25 | 48 | same pattern, mirrored |
| **walk** | **24** | **67** | hips, root, neck_c_02..05, spine_01..03 |

The per-bone count does not show the motion that is spread along a chain. Each link of the tail or spine turns less
than 3 deg, but the whole chain moves. To see this I ran `group_motion.py`, which does forward kinematics on the GLB and
measures how far the tip of each limb group moves over the clip. The result: **no limb group is still as a whole in any
clip except the planted legs.**
- idle: every one of the nine heads moves 0.29-1.23 m and turns 10-32 deg; the tail tip moves 1.25 m / 31 deg; the chest
  (spine_03) slides 0.09 m. Before this pass: heads 0.08-0.24 m, everything 0/76.
- walk: heads 0.78-1.30 m / 15-27 deg (before 0.23-0.49 m); the centre head moves 1.03 m / 17 deg (before 0.23 m);
  spine_03 turns 5.0 deg (before 1.5); tail 2.5 m.
- bite*: tail tip 0.38-0.62 m / 7-10 deg (before 0.0-0.1 m); every side head moves 0.9-3.0 m.
- fire_sweep*: tail tip 0.47-0.74 m / 11-14 deg (before 0.01 m).
- head_down: tail tip 0.50 m / 8 deg (before 0.01). The centre neck is held on the floor (the jaw weak-point contract),
  and the spine turns 2.5 deg in total: this is the quietest group of any clip.
- head_up: the tail tip moves only 0.19 m / 4 deg in the 1.5 s. The hind legs stay planted.

## Loop seams (local rotation, first frame vs last frame, max over 76 bones)
idle 0.00 deg, walk 0.00 deg, head_down 0.00 deg (before: 0.00 / 0.00 / 0.00).

## Ground contact (lowest skinned vertex over the clip, metres, numpy skinning of the GLB every 2nd frame)
| clip | before | after |
|---|---|---|
| idle | -0.000..+0.000 | -0.001..+0.002 |
| walk | -0.006..+0.018 | -0.011..+0.008 |
| bite | -0.059..-0.000 | -0.061..+0.001 |
| bite_l / bite_r | -0.014..0.000 | -0.009..+0.000 |
| fire_sweep / _l | -0.002..+0.006 | -0.002..+0.006 |
| fire_sweep_return / _l | -0.031..+0.006 | -0.031..+0.006 |
| head_down | -0.002..+0.006 | -0.002..+0.006 |
| head_up | -0.015..+0.005 | -0.015..+0.005 |
| hurt | 0.000..+0.011 | 0.000..+0.011 |
| hurt_standing | 0.000 | 0.000..+0.000 |
| stomp / stomp_r | -0.009..+0.001 | -0.008..+0.003 |
| death | -0.022..+0.013 | -0.022..+0.013 |
| death_standing | -0.124..+0.107 | -0.148..+0.107 (the thrash; this clip is not used by the fight) |

## Problem found: forefeet slide in the re-based one-shots' 0.3 s blend windows (re-base track)
The re-base starts each one-shot on the natural legs. It then blends the legs over 0.3 s to the original keyed legs,
which were keyed from the rest stance (see `rebase_hydra.md`, "Legs are one group"). The planted feet slide while
they do this.

I measured the foot-joint drift on the floor (`group_motion.py`):
- bite, bite_l, bite_r, fire_sweep, fire_sweep_l, head_up: the forefeet move 0.18-0.22 m, and foot_br 0.19 m. Before
  this pass the drift was 0.01-0.07 m. foot_fl x goes 2.14 -> 1.98 m in bite's first 0.3 s and back in its last 0.3 s.
- hurt_standing: the forefeet move 0.21-0.24 m and lift 0.09 m during the flinch. This is the root motion over the
  natural legs. The fight does not use this clip (BossBase plays `hurt`).

On a 16 m creature this reads as a small shuffle of the feet at the start and end of the bite and fire clips. I did not
change it, because a fix means re-keying those clips' legs on the natural stance with leg IK. That work belongs to the
re-base track. Request R1: bake the natural leg offset into the acting legs for the whole clip, solved per frame with
foot IK, instead of blending in and out. Or blend in only the trunk and keep the feet fixed.

## Godot
- Import under `work/.import_lock`: OK (no errors).
- `work/assemble_hydra/probe.gd` (through gdwin): **fails=0**.
  - The real GLB loads, 76 bones.
  - The 9 core clips have length = manifest = AnimationPlayer, and correct loop flags (idle 6.0000).
  - Events: fire_start 1.500, fire_end 4.050, stomp impact 1.750, bite impact 1.500.
  - The 12 sockets sit on their bones.
  - head_down jaw_c: 0.51-0.70 m high, 6.97 m ahead, x 0.00 (unchanged).
  - Chain seams: fire_sweep end -> head_down 0.005 m, head_down -> head_up 0.022 m.
  - stomp lifts foot_fl to 1.63 m; foot_fr stays at y <= 0.07.
  - bite impact: the centre head lands 1.20 m high, 5.13 m ahead.
  - idle mirror pairs now move differently: head_1 0.59 m vs head_8 0.31 m, head_4 1.10 m vs head_5 0.35 m.
- `work/animfix_hydra/probe_fix.gd` (headless; the 8 extra clips, their events and chains): **fails=0**.
- Movie `work/assemble2_hydra/movie.gd` (gdwin, 30 fps, chase-camera view 12.6 m in front of the beast at 3.6 m high,
  aimed at its chest).
  - Segments: idle 6 s, then walk for 2 cycles while the body turns in place at +/-35 deg/s at the hydra.gd clip rate
    (new 1.06x, old 0.9x), then bite out of the idle.
  - Files: `movie/after.avi` / `after.mp4` (this GLB) and `before.avi` / `before.mp4` (the backup GLB loaded at runtime
    with `CharacterVisual.create_from_file`).
  - Contact sheets: `idle_after_grid.jpg`, `walk_after_grid.jpg`, `bite_after_grid.jpg`.
- What I saw:
  - idle: the centre head looks left (0.7 s) and then right (3.7 s); the heads sit at different heights and move on
    their own; the feet stay planted; no pops.
  - walk: the feet lift and plant while the body turns, and the heads bob out of step.
  - bite: the centre head strikes down at the camera, the side heads rear back at the impact and settle, and it ends on
    the stance.
- Headless fight `--start=hydra --harness --bot=win --seed=11` (`work/assemble2_hydra/fight_win.log`): result=victory at
  99.46 s (11-22: 99.42-99.57 s), 0 SCRIPT ERROR / Parse Error, no `jaw_fallback`.

## For the game code
- `idle` is 6.0 s (was 3.0). No event depends on it. Code that waits for whole idle cycles, if any, now waits twice
  as long.
- `walk` has a `move_speed` of 1.73 m/s. `hydra.gd _walk_rate()` now takes its exact path: 1.06x at 35 deg/s (was the
  0.9x fallback). `walk_turn_speed` in tuning.gd is no longer used for the hydra.
- No other length, event time, socket or weak point changed.

## Devlog
`docs/devlog/media_inbox/assemble2_hydra/`: `hydra_idle_before_after.jpg`, `hydra_walk_before_after.jpg`,
`hydra_idle_walk_before_after.mp4` and `captions.txt`.

---------------------------------------------------------------------------------------------------------------------
# Fix 3: animation fixer, hydra (2026-11-23, after the review's 12 findings)

The owner was at the Mac. Blender ran only headless (`-b --factory-startup`, `tools/ak`). Godot rendered only through
`tools/godot_bg/gdwin`; everything else ran `--headless`. `builds/Hercules.app` was not touched. No credits were spent and
nothing was committed. Scratch: `work/animfix3_hydra/`. I was the only writer of `art_src/chars/hydra/` and
`game/assets/characters/hydra/`. I also edited `game/scripts/bosses/hydra.gd`, because findings 1 and 2 ask for it.

## Tool
`art_src/chars/hydra/scripts/fix3/fix_bl.py` + `fix_params.json` (headless Blender; it uses animkit's Rig). It is
re-base v2: `rebase_bl.py`'s composition (originals `*.rest_v1.json`, acting groups exact, passive groups on
`q_natural x q_original` plus life) with these changes:
- **Legs (R1, findings 6/7).** The legs are never blended between the stance and the rest-keyed legs any more. Every
  frame the legs are `q_N x q_O` (the keyed crouch on top of the stance). Each leg is then re-solved by a Gauss-Newton
  leg IK (rx/ry at `_01`, rx at `_02`, plus a heavily regularised hoof tilt as a last resort). Each planted foot keeps
  its natural floor point. The hoof unit (`leg_*_03` + foot) keeps its natural world orientation, so the hoof skin does
  not deform: a first try with free `_03` put toes 3-10 cm under the floor. A foot that the original LIFTS (only the
  stomp foot, 1.77 m) follows the original's lift path relative to its lift-off point, with horizontal travel only once
  the hoof is up. The path is corrected linearly so the foot lands where it lifted (on the natural spot).
- The natural body drop (root, 0.10 m) uses the old leg-window weight, as before. stomp/stomp_r keep it for the whole
  clip, because their 0.6 m hip shift is otherwise out of reach of the planted hind legs (br missed by 0.16 m).
- The re-based clips are keyed at 30 fps, one key per GLB frame. At 24 fps the feet drifted 3 cm between keys where the
  original snaps (bite strike).
- Passive heads scale the original's motion relative to a reference that runs from its first pose to its last pose, so
  both boundary poses stay exact. The per-head stagger fades out over the last 0.5 s.
- idle: base = the anim2 idle (kept in `clips/idle_n/base/`) plus breathing, root bob, hip sway, and leg IK per frame.
- walk_turn_l / walk_turn_r: upper body, bob and lift timing come from `clips/walk_n/action_walk.json` (walk is
  unchanged). The legs are re-solved per frame on arcs about the body origin.
Checks: `scripts/fix3/verify.py` (FK on the GLB: foot slide, turning at the game rate, transitions, joins, loop seams,
idle, stomp, hurt, head_down, contracts), `pen3.py` (numpy skinning: vertices inside a 0.35 m neck core),
`work/animfix3_hydra/probe_turn.gd` (headless end-to-end: the real game, with the hero walked round the beast).

## Findings: check and result (PREV = assemble2 GLB, backed up in `backup_20261123/fix3_pre/`)
1. **Walk turning in place: confirmed.** At the game rate the old walk clip slid its planted feet 1.35-3.66 m/s at
   35 deg/s and 0.46-1.25 m/s at 12 deg/s. Fix: new clips `walk_turn_l` / `walk_turn_r` (2.1667 s, same gait and
   footfalls). Every planted foot moves on its circle about the body origin at Omega = move_speed / 2.99 m (the
   forefoot radius hydra.gd measures on the sockets).
   **Decision: move_speed 1.2, not 1.73.** With 1.73 the stance sweep is 57 deg, and the hind feet (r 3.7 m) cannot
   reach the ends of their arcs (IK misses 0.3-0.56 m). 1.2 gives a 40 deg sweep. The body crouches 0.12 m while
   turning, the walk's bob is cut to 40 % and its hip roll to 30 %.
   Result: world stance slide at the game rate is 0.005-0.027 m/s at 35 deg/s and 0.005-0.023 m/s at 12 deg/s (both
   directions). The IK still misses by up to 7 cm on one or two frames at the bl touch-down (reach limit). In game
   (probe_turn.gd, headless real fight, hero walked round): `walk_turn_l` / `walk_turn_r` are chosen by the sign of
   `_yaw_vel`, and the planted foot sockets move at median 0.08 m/s (p90 0.25) once the 0.35 s blend-in is over. The
   remaining slide comes from the rate floor while the turn eases in and out, and from toe-off/landing frames.
2. **Walk <-> idle transitions: confirmed** (walk feet are 0.63-1.16 m from the stance, mean 0.88). Fix: the turn clips'
   arcs are shifted 25 % toward the stance at phase 0.73, where all four feet are planted. A turn walk now STARTS there
   (`start_time` 1.5833 s, feet 0.45 m from the stance). It stops inside `stop_window` 1.48-1.68 s (0.45-0.47 m), or after
   waiting at most 0.35 s, then blends to idle over 0.4 s. Not fully solved: a stop outside the window still blends from
   0.5-0.97 m. A zero-slide stop needs a settle clip or engine foot locking (not done).
3. **Idle body a statue: confirmed.** Two breaths per 6 s: spine_02 0.6 deg + spine_03 0.45 deg + neck bases 0.5 deg.
   spine_03 now moves +-0.035 m (was 0.005 m in total) and the chest front (neck_c_01) 0.14 m. Root bob +-0.02 m, high on
   the inhale. Hip sway 0.073 m in phase with the chest drift (hips were 0.000). Every leg is re-solved per frame: feet
   move <= 0.5 mm and stay at 0.390-0.391 m. Hind legs flex 0.03 m. First key = last key = natural stance
   (idle -> bite/stomp join 0.000 m). Moving joints 39 -> 43/76; the loop seam is exact.
4. **stomp neck_5 through neck_c: confirmed.** neck_5 bends +5 deg/link toward +X over 0.1-2.7 s. Result:
   neck_5_04 vertices inside the neck_c core are 0/902 at 1.0 / 1.4 / 1.8 / 2.2 s (PREV 71 / 77). The closest upper-link
   pair c-5 is 0.62 m (PREV 0.25). The natural stance itself has c-5 at 0.69 m (idle, walk), so ">= 0.8 m" is not
   reachable without moving head_5 in the stance.
5. **fire_sweep_l / return_l head_8 through neck_6: confirmed.** neck_8 ducks (lift -10 deg/link, side -7 / -4
   deg/link) while neck_6 leans over it. Result: head_8 vertices inside the core are 0/1580 at every sampled time
   (PREV up to 358). The closest pair is 0.75 m (fire_sweep_l, PREV 0.21) and none (return_l, PREV 0.34).
6. **R1 blend-window foot slide: confirmed.** Planted-foot slide per clip is now <= 0.017 m (target 0.05). Old -> new:
   bite fore 0.69 -> 0.005, br 0.37 -> 0.001; fire_sweep fore 0.33 -> 0.002; head_up 0.25 -> 0.009;
   hurt_standing 0.61 -> 0.001.
7. **stomp planted feet: confirmed.** Slide is now 0.002-0.010 m (PREV fr 0.53, br 0.50, bl 0.30). The stomping foot
   lands on its lift-off spot. Contract change: the stomp impact foot moved 0.265 m to the natural spot (stomp_r
   0.061 m). The ring centre (the foot socket at stomp start) is now 0.000 m from the landing (was 0.19-0.26 m). The
   foot_fl socket at the impact is (2.15, 0.01, 2.25) in Godot. The peak lift is unchanged (1.65 m).
8. **Chain joins: confirmed.** Every life layer of head_down is zero at t = 0. Its side heads hold the original's chin
   rest; the original loop carried head_5's 1.7 m/s seam jump, so to keep them alive the weave/tail stir is x1.8 there.
   The stagger and scaling keep both clip ends exact. Joins (largest joint gap): fire_sweep* -> head_down 0.000,
   head_down -> head_up 0.000, hurt -> head_down 0.004, head_down -> death 0.000 (PREV 0.21-0.43). Godot probe:
   0.005 / 0.027 m.
9. **stomp centre-head hitch: confirmed.** The whip is a smooth pulse (0.1 s) and the rebound is damped and delayed.
   The centre neck adds a follow-through that keeps going down while the KEYED body bounces up. head_c per-frame
   speed: PREV 2.7 14.6 22.5 2.2 13.4 -> NEW 10.1 24.4 19.2 7.1 5.8 6.8 7.9. The dead stop and snap are gone. The
   remaining 24 m/s peak is the original's acting body impact (spine is acting, kept exact).
10. **stomp heads barely react: confirmed.** The side heads rear up by a LIFT about each neck's own horizontal cross axis.
    A world-X bend_up only twisted the sideways-fanned necks, which is why the old rear-up showed 0.1-0.4 m. The rear-up
    is staggered 0.05-0.15 s and done before the whip. Head rise is now 1.0-1.6 m on heads 1, 2, 3, 4, 6, 7, and 0.5-0.8 m
    on heads 5 and 8 (kept lower: neck_5 near the centre neck, neck_8 under neck_6). Short of the 1.5-2.5 m asked: more
    put necks 6/7 at 0.35 m from each other (necks 7 and 3 now lean outward).
11. **hurt flinch snaps: confirmed.** The passive heads' staggered original is low-passed (5-tap 1-2-3-2-1) and the
    flinch eases in. Peak speeds: head_5 44 -> 20, head_4 35 -> 19.5, head_3 37 -> 16.7 m/s. The acting head_c is
    unchanged (19.4).
12. **head_down quiet body: confirmed.** Flank pant as a spine bulge: spine_01 +a, spine_02 -(1 + l1/l2)a,
    spine_03 +(l1/l2)a, with a = 1.2 deg, one pant per loop. That keeps spine_03's tip and direction, so the centre neck
    and the jaw stay where they were. The jaw is identical: 1.106-1.340 m bone height, mm-level, both GLBs. Mid-back
    0.020 -> 0.053 m, tail tip 0.50 -> 0.86 m, moving joints 38 -> 48/76. Loop seam: worst excess over the bone's p95 is
    now 0.07 m/s (head_5 PREV 0.51).

## Not fixed / found
- bite_l: neck_6 (acting strike, exact) passes 0.17 m from neck_7 over 1.40-3.07 s. This is pre-existing and was not in
  the findings, so it is unchanged.
- death: the lowest vertex is +0.03 m at 0.12-0.2 s, while the leg IK fades into the keyed collapse. death_standing is
  -0.03 m at 2.0 s (pre-existing).
- hurt: the hind feet miss by up to 3 mm (bl) in the hit jolt (IK reach). At walk_turn bl touch-down the IK misses by up
  to 7 cm on one or two frames.
- head_down: the side heads no longer carry the original loop's own motion (life only, x1.8).

## Manifest / contracts
Every existing clip has the same name, length, loop flag and events. sockets, socket_offsets, weak_points and size are
identical. walk: move_speed 1.73 (unchanged clip). NEW clips: walk_turn_l / walk_turn_r (2.1667 s, loop, no events,
move_speed 1.2, `stop_window` [1.48, 1.68], `start_time` 1.5833). `clip_sources.json` now lists 19 clips.
`ak export` retimes death 3.7917 -> 3.8 as before. GLB 11.19 MB (was 10.90).
The other contract change is the stomp landing spot (finding 7), as recommended. The stomp body is also 0.10 m lower in
mid-clip (natural drop kept). The bite impact head positions are identical (head_c (0, 2.146, 6.378) GLB coordinates).

## hydra.gd (findings 1 and 2)
- `_turn_clip()` (sign of `_yaw_vel`) and `_start_turn_walk()` (plays at the manifest `start_time`).
- `_update_turn_walk()`: same-phase switch when the turn reverses, and the rate on the real turn.
- `_in_stop_window()`: the stop waits up to 0.35 s for the window.
- `_walk_rate(deg, clip)`: the turn clips use their own move_speed, clamped 0.1-2.6, with a 4 deg/s floor. The old walk
  keeps 0.3-1.8 and the 12 deg/s floor.
- Harness events `turn_walk_start` / `turn_walk_stop`.
- The forced-fire stepping uses the turn clips too.
- Falls back to `walk` when the turn clips are missing.

## Commands (repeatable)
```
B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup"
$B --python art_src/chars/hydra/scripts/fix3/fix_bl.py -- work/animfix3_hydra/keys <clips...>      # ~5 s for all 18
art_src/chars/hydra/scripts/fix3/bake_set.sh <clips...>    # (expects keys in work/animfix3_hydra/keys) -> act/
# copy keys_/action_ into the clip folders (walk_turn -> clips/walk_turn/), then exactly as the assembler:
P=$(python3 -c "import json;print(' '.join(json.load(open('art_src/chars/hydra/clip_sources.json'))['clips'].values()))")
tools/ak merge art_src/chars/hydra/hydra.blend $=P
tools/ak export art_src/chars/hydra/hydra.blend --out game/assets/characters/hydra/hydra.glb --clips-json game/assets/characters/hydra/hydra_clips.json
python3 art_src/chars/hydra/scripts/fix3/finish_manifest3.py game/assets/characters/hydra/hydra_clips.json
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
```
## Godot (final GLB)
- Import under the lock: OK.
- `--quit-after 2`: no SCRIPT ERROR / Parse Error.
- probe.gd through gdwin: fails=0. The 9 core clips match lengths, loops and events. The 12 sockets are on their bones.
  head_down jaw 0.48-0.74 m high, 6.93 m ahead. Seams 0.005 / 0.027 m. Stomp foot peak 1.65 m.
- probe_fix.gd headless: fails=0.
- Headless fight `--start=hydra --harness --bot=win --seed=11`: victory at 99.28 s (assemble2 99.46 s), 0 script
  errors, no jaw_fallback.
- probe_turn.gd: see finding 1.
- `tools/clip_motion.py hydra`: 19 clips; walk_turn_l/r move 67/76.
- Strips: `clips/*/strip_<clip>.jpg` (cam_nat_std). I looked at stomp (rear-up at 1.2 s, three planted feet),
  walk_turn_l and fire_sweep_l.

## For the lead
- SPEC lists the hydra clips. Add walk_turn_l / walk_turn_r and their manifest keys `stop_window` / `start_time`.
- `builds/Hercules.app` still has the old hydra: it needs your rebuild.
- Devlog: `docs/devlog/media_inbox/animfix3_hydra/` (2 strips + captions).
