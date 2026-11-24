# Assembler 2: hercules (2026-11-23, natural-animation pass; owner at the Mac, not asked, decisions noted)

Outputs: `game/assets/characters/hercules/hercules.glb` (7.45 MB, 7,454,784 bytes; was 7,369,212) and
`hercules_clips.json`. 14 clips (same names as before), 1 skin, 29 joints, albedo embedded, props stripped, **24 fps**.
`hercules.blend` now holds the 14 new actions. Backups: `art_src/chars/hercules/backup_20261123/` (old GLB + manifest),
`work/assemble2_hercules/hercules.blend.before_merge` (old blend). Scratch, scripts, logs, movies: `work/assemble2_hercules/`.

## Sources (`art_src/chars/hercules/clip_sources.json`)
| clip | action file merged | origin |
|---|---|---|
| idle | clips/idle_n/action_idle.json | new video idle_n |
| run | clips/run_n/run_resampled_24fps.json | new video run_n (see decision 1) |
| strafe_l, strafe_r, walk_back, roll, attack_1, attack_2, block_start, block_idle, block_end, hit | their usual files in clips/strafe, walk_back, roll, attack, block, hit | re-based (`rebase_done.json`) |
| ride | art_src/chars/ride/clips/ride/action_ride.json | re-based |
| death | clips/death/action_death.json | untouched |

`rebase_done.json` was present at the start (no wait). Never merge with a glob: the `*.rest_v1.json` backups carry the same
clip names.

## Decisions
1. **run at 24 fps.** run_n is baked at 30 fps; every other clip is 24 fps. `ak export` exports at the highest fps and
   retimes every clip that is not a whole number of frames there: at 30 fps attack_1 (37.5 frames), hit, roll,
   block_start/end and death would have changed length by up to 1 frame and their events would have shifted
   (attack_1 chain 0.917 -> 0.929). So `run_resampled_24fps.json` = run_n/action_run.json with `fps` 24 and no `spec`:
   `ak merge` replays the animator's baked quaternions at the SAME key times (fractional 24 fps frames; the bezier curves
   are identical in time) and the GLB stays 24 fps with no retime. Cost: merge warns "old action JSON without poses"
   for run (no re-bake on the current rig; rig hash is the same, cab1a3a4339f), and the GLB samples the run at 24 fps
   instead of 30 (17 samples per cycle). If the rig changes, re-make this file from a fresh `ak bake` of
   `clips/run_n/keys_run.json`, then set fps 24 again.
2. **No re-run of the re-baser.** The new idle's frame 0 equals natural_pose.json: quaternion difference to the first and
   last frame of attack_1, attack_2 (end), hit, roll, block_start (start), block_end (end) = 0.00 deg on every bone, root
   height -0.0121 m in all of them.
3. **run move_speed = 4.59 m/s** (the run_n animator's planted-foot speed, measured on the 30 fps keys). My GLB re-measure
   (work/assemble_hercules/measure.py, 24 fps samples, median) gives 4.71 (+2.6 %, sampling); I used the animator's value
   as the brief says. strafe/walk_back re-measured 0.72 / 0.72 / 1.20 = unchanged.
4. **socket_offsets kept from the old manifest** (core_fix2 turns: sword -25 deg, shield +40 deg), not from rig.json:
   the new manifest is the old one with only length / loop / events from `ak export` + the run speed fields.

## Rebuild (in this order)
1. `work/assemble2_hercules/merge_sources.sh` (one `ak merge` per clip_sources.json entry, in its order)
2. `tools/ak export art_src/chars/hercules/hercules.blend --out work/assemble2_hercules/hercules.glb --clips-json work/assemble2_hercules/hercules_clips_raw.json` (export_fps 24, no retimed clips)
3. `python3 work/assemble_hercules/strip_props.py work/assemble2_hercules/hercules.glb` (9.92 -> 7.45 MB)
4. `python3 work/assemble_hercules/measure.py work/assemble2_hercules/hercules.glb > work/assemble2_hercules/measure.json`
5. `python3 work/assemble2_hercules/finalize_manifest2.py work/assemble2_hercules/hercules.glb work/assemble2_hercules/hercules_clips.json`
   (old manifest from backup_20261123 + export lengths/loops/events; prints GLB checks and the key-by-key diff)
6. copy both into `game/assets/characters/hercules/`, then `work/assemble2_hercules/import.sh` (import under work/.import_lock)
7. probe: `tools/godot_bg/gdwin --path game --resolution 1280x720 --script ../work/assemble2_hercules/probe.gd -- --harness`
8. movie: `tools/godot_bg/gdwin --path game --resolution 1280x720 --fixed-fps 30 --write-movie <abs>/after.avi --script ../work/assemble2_hercules/movie.gd -- --harness [--before]`,
   strips with `python3 work/assemble2_hercules/contact.py <avi> <jpg> <cols> <label> t1,t2,...`

## Clips old vs new (manifest; events in clip seconds)
| clip | length old -> new | loop | events old -> new | moving joints old -> new (of 29) | seam (loops) / start=end |
|---|---|---|---|---|---|
| idle | **3.5 -> 6.0** | yes | none | 6 -> 21 | 0.000 deg |
| run | **0.8333 -> 0.6667** | yes | none | 19 -> 28 | 0.000 deg |
| strafe_l | 0.8333 | yes | none | 10 -> 21 | 0.000 deg |
| strafe_r | 0.8333 | yes | none | 10 -> 21 | 0.000 deg |
| walk_back | 0.5 | yes | none | 10 -> 21 | 0.000 deg |
| block_idle | 2.5 | yes | none | 5 -> 19 | 0.000 deg |
| ride | 1.5 | yes | none | 3 -> 9 | 0.000 deg |
| block_start | 0.25 | no | none | 19 -> 20 | natural -> block_idle f0 |
| block_end | 0.25 | no | none | 19 -> 20 | block_idle f0 -> natural |
| attack_1 | 1.25 | no | active 0.458-0.708, chain 0.917 (same) | 18 -> 20 | natural -> natural (0.000 deg) |
| attack_2 | 0.8333 | no | active 0.25-0.458 (same) | 16 -> 19 | chain pose -> natural |
| hit | 0.4583 | no | none | 10 -> 19 | natural -> natural (0.000 deg) |
| roll | 0.7083 | no | none | 21 -> 21 | natural -> natural (0.000 deg) |
| death | 3.75 | no | drop_props 2.1 (same) | 23 -> 23 | own end pose (unchanged clip) |

Largest per-frame rotation jumps are the same as before (inherited, not new): roll forearm_l 146.6 deg/frame (was 149.3),
attack_2 forearm_l twist 88.0 (was 85.1, the original flip the re-baser reported), attack_1 upper_arm_r 63.4, hit 64.5.
The loops move at most 1.4 (idle), 2.1 (block_idle), 2.3 (ride) deg/frame: no pops.

## `python3 tools/clip_motion.py hercules` (after)
```
=== hercules: 14 clips, 29 joints
  attack_1                1.25s moving 20/29  frozen: fingers_l, fingers_r, hand_l, hips, root, shoulder_r, spine_02, toe_l, toe_r
  attack_2                0.83s moving 19/29  frozen: fingers_l, fingers_r, hand_l, hips, root, shoulder_l, shoulder_r, spine_02, toe_l, toe_r
  block_end               0.25s moving 20/29  frozen: fingers_l, fingers_r, hand_l, root, shoulder_l, shoulder_r, spine_03, toe_l, toe_r
  block_idle              2.50s moving 19/29  frozen: fingers_l, hand_l, hips, root, skirt_b, skirt_f, skirt_l, skirt_r, toe_l, toe_r
  block_start             0.25s moving 20/29  frozen: fingers_l, fingers_r, hand_l, root, shoulder_l, shoulder_r, spine_03, toe_l, toe_r
  death                   3.75s moving 23/29  frozen: fingers_l, fingers_r, hand_l, root, shoulder_l, shoulder_r
  hit                     0.46s moving 19/29  frozen: fingers_l, fingers_r, foot_l, foot_r, hand_l, hips, root, skirt_b, toe_l, toe_r
  idle                    6.00s moving 21/29  frozen: root, shin_l, shin_r, skirt_b, skirt_f, skirt_r, toe_l, toe_r
  ride                    1.50s moving  9/29  frozen: fingers_l, fingers_r, foot_l, foot_r, forearm_l, hand_l, hips, root, shin_l, shin_r, shoulder_l, shoulder_r, skirt_b, skirt_f, skirt_l, skirt_r, thigh_l, thigh_r, toe_l, toe_r
  roll                    0.71s moving 21/29  frozen: fingers_l, fingers_r, hand_l, hips, shoulder_l, shoulder_r, toe_l, toe_r
  run                     0.67s moving 28/29  frozen: root
  strafe_l                0.83s moving 21/29  frozen: fingers_l, hand_l, hips, root, skirt_b, skirt_f, toe_l, toe_r
  strafe_r                0.83s moving 21/29  frozen: fingers_l, hand_l, hips, root, skirt_b, skirt_f, toe_l, toe_r
  walk_back               0.50s moving 21/29  frozen: fingers_l, hand_l, hips, root, skirt_b, skirt_f, toe_l, toe_r
```
No limb GROUP is frozen in any clip: arms, head/neck and spine move everywhere. What stays under 3 deg is planted feet and
shins (idle, hit), the shield hand (hand_l, fingers_l: the shield hangs on the forearm socket), closed sword fingers, toes,
the non-deforming root, the driven skirt bones (they follow the thighs), and in ride the seated legs (by design: the seat
must not move) plus shoulders/forearm_l (the chest moves ~5 deg over spine_01-03 in total).

## Ground contact
- Every key of every clip has `lowest_z` 0.000 m (action JSON `ground`), except run 0.000-0.09 m in its flight phases
  (the animator: lowest vertex -0.002..+0.116 m, flight 0.17-0.30 and 0.50-0.63 s) and ride 0.19 m (rider on the horse, as before).
- In Godot (probe): idle lowest toe joint 0.046 m (same as before; the toe joint sits 4.6 cm above the sole), hips 1.071 m.
- Idle feet slide <= 4 mm (animator), GLB planted-foot speed 0.001 m/s median.

## Godot
- Import under the lock: exit 0 (`work/assemble2_hercules/import.log`).
- Loader probe (`work/assemble2_hercules/probe.gd`, through gdwin): **PASS**. is_standin false, model_top 1.900, 14 clips;
  every length = manifest = Animation, loop modes right, run move_speed 4.59, attack_1 active 0.202-0.312 game s (x2.273),
  attack_2 0.195-0.357 (x1.282), roll x1.012; 4 sockets on BoneAttachment3D. 0 SCRIPT ERROR / Parse Error.
- Movie (`work/assemble2_hercules/movie/after.avi` and `before.avi`, 30 fps, 280 frames, 1600x900 on this display):
  contact strips `after_idle.jpg`, `after_run_attack.jpg`, `ba_idle.jpg`, `ba_run.jpg`, `idle_shots_cmp.jpg`. Looked at:
  idle stands relaxed (no lunge), breathes and turns the head, feet planted, sword tip clear of the floor; run pumps the
  arms against the legs, feet strike under the hips, no skating at x1.31; attack_1 unchanged, ends back in the stance.

## For the game code (core / lead)
- **idle length 3.5 -> 6.0 s** (no events). Anything that timed itself on the idle length must use clip_length().
- **run length 0.8333 -> 0.6667 s, move_speed 3.64 -> 4.59 m/s.** player.gd already plays locomotion at
  ground_speed / move_speed: at RUN_SPEED 6.0 that is x1.31 (was x1.65), no skating. Nothing to change in code.
- All other lengths, loop flags, events (attack_1 active 0.458-0.708 / chain 0.917, attack_2 0.25-0.458, death
  drop_props 2.1), sockets, socket_offsets, socket_props, offset_space and size are identical to the old manifest.
- One-shots now start and end on idle frame 0 (= natural stance) instead of the old lunge; the game_note texts say so.
- **Look item (shield offset):** core_fix2's +40 deg shield turn was tuned on the old lunge idle. With the natural stance
  (forearm forward-down) the shield shows nearly edge-on from the chase camera in the idle (a diagonal plank at his left
  side, `work/assemble2_hercules/movie/idle_shots_cmp.jpg`) and turns edge-on at the back of each run arm pump. The old
  idle showed it as a disc from behind. I did not change socket_offsets (contract); core may re-tune the forearm_l
  offset against the new idle if the owner wants the disc read from behind.
- The new run carries the sword low and back (animator, from the video): from the chase camera the blade is mostly
  hidden behind the body while running (before: blade up and visible).

---
# Animation fixer (animfix_hercules), 2026-11-23 10:00-10:30 — the naturalness review's 8 findings
Owner at the Mac, not asked; decisions below. Scratch, scripts, logs: `work/animfix_hercules/`. Backups of every replaced
art file: `art_src/chars/hercules/backup_animfix_20261123/` (natural_pose.v1.json, clips/<folder>/keys|action|strip|poses).
Previous GLB = `work/assemble2_hercules/hercules.glb` (+ its manifest). Blend before this merge:
`work/animfix_hercules/hercules.blend.before_merge`.

## What changed
| finding | check | fix | result (measured) |
|---|---|---|---|
| shield cuts into him (idle, run, one-shot ends) | confirmed: game shield (socket_offsets, +40 deg) at idle f0 = 110 body vertices inside the shield shell, upper arm 10.9 cm through the FACE (that is the "fist on the face" in c_close.jpg; the hand itself stays behind), tilt 39 deg | natural_pose.json v2: upper_arm_l front -16 -> -22, forearm_l front -14 -> -20, twist -20 -> -62, fingers_l curl x0.5; chosen by a grid on the game socket transform (`score_grid.py`) + a real-mesh check (`bl_meshcheck.py`) | idle: 0 vertices inside on every key, upper arm behind the face, gap to the body >= 4.6 cm (skirt), chest/shoulder >= 5 cm, shield normal (0.99, 0.10, -0.14) = vertical at his side, face out and 8 deg back; fingertip estimate 4.2 cm past the rim plane (was 7.4) |
| run shield | confirmed (90-126 vertices inside, upper arm up to 17 cm through the face) | run_n left arm re-keyed per key (`run_edit.py`, per-key search `run_grid.py`): upper arm 6-22 deg further out, forearm twist -45..-68 | 0 vertices inside on 14 of 21 frames, <= 14 (left shoulder top, under the strap) at 0.23-0.43 s; upper arm never through the face; capsule check clean |
| left foot drags in attack recoveries | confirmed (attack_2 last 3 frames 82 cm of floor drag, attack_1 57 + 53 cm) | `edits.step_window`: legs between the window ends re-timed into steps with explicit root height and 2-bone IK of BOTH feet to world targets (planted foot fixed, stepping foot on a sin arc) | attack_1 0-0.333: right steps forward (lift 7.6 cm) then left back (9.2); 0.917-1.25: right back (5.5), left forward (9.3); attack_2 0.583-0.833: right back (5.1), left forward (sole 8.6 cm, toe joint 0.196 m = 15 cm up, lands on the last frame). Lifts = lowest sole vertex. A planted foot does not move; the stepping foot touches down on the window's last frame (its last 4-19 cm of travel fall in that frame). Active windows untouched (sword path within 2.6 cm of the pre-natural clip, as before) |
| idle quiet from the chase cam | confirmed (head yaw 9.4-10.0 deg for 0-3.5 s) | `gen_idle_v3.py` (see idle_n/notes.md) | head yaw 5.5-13 in 0-3.5 s, spine_02 up to 5.0, shoulders 9.5, shield arm drift 7.9, wrist roll +-4; seam 0.000 |
| forearm_l twist pops | confirmed (roll 146.6 deg local at 0.167: the elbow folded past 160 deg; attack_2 90.6 + 90.8 at 0.625/0.667) | `edits.smooth_local`: forearm_l local rotation slerped (short path, even speed), hand + shield ride along: roll 0.125-0.25, attack_2 0.167-0.333 (the 75 deg brace at the chop too) and 0.542-0.75 | roll 37.4 deg local per frame x3; attack_2 27.2 and 31.1 per frame; attack_2 recovery face turn <= 15 deg/frame (was 57/61); roll world face turn 64/59/32/31 (the body itself rolls ~100 deg/frame there) |
| block_start/end stomp | confirmed (right foot 24.5 cm lift, left toe 12-19 cm slide) | step_window: right steps (lift 8) then left (5); block_end reversed | right lift 7.0 cm, left 4.5 cm, no slide |
| death start | confirmed | `edits.fix_death`: frame 0 = natural, 0.25 s = natural legs + 40 % recoil, left foot steps 0.25-0.42 | feet still until 0.25, then a 7 cm step; from 0.5 s identical; drop_props 2.1 |
| hit whiplash | confirmed (head 80 deg from vertical, upper_arm_r 47+56 deg out-and-back in 2 frames) | neck/head local delta x0.4, spine_01-03 x0.75; fling frames 1-2 placed at 1/3, 2/3 of the arc | head 48 deg from vertical at the peak, 17 against the chest; fling steps 26/24/34 deg |
| run foot speed (optional) | true (keys' own planted travel 0.14-0.17 m per 30 fps frame) | NOT changed: a 24 fps re-key of the legs is its own job; blade-outward is the owner's call | move_speed 4.59 kept |

Also: every re-base job except ride re-run on natural v2 (`regen.py` = the re-baser's rebase_bl.py/life.py unchanged;
re-running it on natural v1 reproduced the current keys to 0.0000 deg first). Loops change only in fingers_l (their
left arm is the keyed one). ride (art_src/chars/ride) is outside my write scope: untouched.

## Contracts (checked on the imported GLB)
Manifest = previous manifest except `source.built_by` (lengths, loops, events incl. attack_1 chain 0.917 and
drop_props 2.1, sockets, socket_offsets, socket_props, move_speed, size). Loop seams 0.000 deg (all 7 loops); one-shot
start/end = idle frame 0 at 0.000 deg; attack_1@0.917 = attack_2@0 within 0.008 deg; block_start end vs block_idle f0
0.924 deg (shoulder_r, inherited, same as before). `tools/clip_motion.py hercules`: same counts as before except death
23 -> 25 of 29 (`work/animfix_hercules/clip_motion_after.txt`).

## Rebuild (same as above, steps 1-7, with this folder)
`work/assemble2_hercules/merge_sources.sh`; `tools/ak export ... --out work/animfix_hercules/hercules.glb --clips-json
work/animfix_hercules/hercules_clips_raw.json` (export_fps 24, no retime); `strip_props.py`; `measure.py >
work/animfix_hercules/measure.json`; `python3 work/animfix_hercules/finalize_manifest3.py work/animfix_hercules/hercules.glb
work/animfix_hercules/hercules_clips.json`; copy both into game/assets/characters/hercules/; `work/animfix_hercules/import.sh`
(lock; exit 0). To rebuild the art: `regen.py <natural> v2 <clips>` then `build.py v2 <out> <clips>` (NOEDIT=1 for the
plain re-base), idle `gen_idle_v3.py`, run `run_edit.py`.

## Godot (through tools/godot_bg/gdwin)
Loader probe (`work/assemble2_hercules/probe.gd`): PASS, 14 clips, 0 SCRIPT ERROR (its shots landed in
work/assemble2_hercules/shots/: the probe writes there). Movies: `work/animfix_hercules/movie/closeup.avi`,
`review.avi`; contact sheets `c_close.jpg`, `c_idle.jpg`, `c_run_attack.jpg`. Looked at: shield vertical at his left
side with the lion out, no arm through it; run shows the shield as a disc from behind; attacks return to the stance.

## Still not right / for the lead
- From directly behind (chase camera at 0 deg) the idle shield is now edge-on (a vertical shield at the side). To read as
  a disc from behind it must turn its face ~30-45 deg back, which brings the rear rim into the hip/skirt unless the arm
  goes further out; or core re-tunes socket_offsets.forearm_l (contract: lead's call).
- roll: the 0.9 m shield still passes through the curled body mid-roll (100-900 vertices at 0.04-0.6 s, inherited from
  the keyed roll; the arm tuck would need re-authoring).
- walk_back (shield 14 cm into the chest capsule at 0.208) and strafe (6 cm) keep their keyed left arm (not in the
  findings, unchanged from before).
- run: 0-14 vertices of the left shoulder top touch the shield's inner strap side at 0.23-0.43 s.
- ride keeps the v1 stance finger curl (other folder).

---
# Clip fix 2 (clipfix2_hercules), 2026-11-23 10:57-11:20 — idle alive from behind, block_end + attack_1 ease-outs
Owner at the Mac, not asked; decisions below. Scratch, scripts, logs, movies: `work/clipfix2_hercules/`. Backups of every
replaced file: `art_src/chars/hercules/backup_clipfix2_20261123/` (idle_n keys/action/poses/strip, block_end and attack_1
keys/action/strip, the previous game GLB + manifest). Blend before this merge: `work/clipfix2_hercules/hercules.blend.before_merge`.

## What changed (numbers before -> after)
| problem | fix | measured |
|---|---|---|
| 1 idle too quiet from behind | `clips/idle_n/gen_idle_v4.py` (v3 layers + bigger shift, knee/heel, counter-tilt, shrug, look, re-grip, shield settle; `--A '{"look":0.85,"regrip":0.65,"kf":10}'`) | pelvis sideways 4.5 -> 7.5 cm and back; shoulder line counter-tilt -1.7..1.4 -> -0.7..8.1 deg; left knee (shin) 4.2 -> 10.3 deg, heel lifts, toe tip planted (left lowest vertex <= 2.7 mm, right foot <= 0.8 mm); shoulder tops (upper-arm heads) +1.5 -> +2.5 cm, 2 breaths (1.5 / 4.5 s); look to his left (head world yaw) 26.9 -> 37.2 deg at 4.75 s; sword tip in the 1.25-2.25 s re-grip 7.6 -> 24.5 cm; GLB joint max turn (local, 30 fps) forearm_l 18 -> 18, head 16 -> 20, upper_arm_l 12 -> 20, thigh_l 11 -> 18, shin_l <3 -> 15, fingers_r 16 -> 24; joints moving 21 -> 23 of 29. Home island movie (1600x900, hero box 227x266 px): mean abs pixel change 1 s apart 4.63 -> 6.08 levels (max 7.39 -> 11.16), pixels changed > 24 levels 8.1 -> 11.1 % |
| 2 block_end stops dead | `ease.py block_end`: whole clip time-warped 6 -> 8 frames (Hermite: original speed at the block_idle seam, speed 0 at the end) | **length 0.25 -> 0.3333 s**; forearm_l/hand_l/fingers_l world turn per 24 fps frame, last 4: 19.1 43.9 34.3 (stop) -> 35.3 23.0 14.2 5.1 (~ per 30 fps frame: 35 27 -> 11 4); GLB local forearm_l last 30 fps step 14.9 -> 2.2 |
| 3 attack_1 recovery | `ease.py attack_1`: sword-arm chain locals over 0.917-1.25 re-timed by arc length (profile 10,26,36,40,37,27,14,4) | hand_r world turn per 24 fps frame, last 3: 30.0 22.6 9.1 -> 23.8 12.3 3.5; upper_arm_r 10.7 4.1 -> 5.7 1.6; forearm_r 13.5 5.2 -> 7.2 2.0. Events 0.458-0.708 / chain 0.917 and the chain pose unchanged (attack_1@0.917 vs attack_2@0 0.008 deg) |
| 4 shield face from behind (optional) | NOT done | no time left for the grid + mesh check; the idle shield stays vertical at his side (normal 0.99, 0.10, -0.14), edge-on from straight behind. Same open item as the animfix note |

The upper back joint itself (spine_03) cannot rise with planted feet: the breath shows as the shoulder shrug (+2.5 cm at
the shoulder tops) and the chest extension; spine_03 moves -0.3 cm. Decision: rise measured at the shoulder tops.

## Contracts (on the imported GLB)
Manifest = previous manifest except `clips.block_end.length` 0.25 -> 0.3333 and `source.built_by`. Loop seams 0.000 deg (7
loops); one-shot start/end = idle frame 0 at 0.000 deg (block_end end at 0.333 too); attack_1@0.917 vs attack_2@0 0.008;
block_start end vs block_idle f0 0.924 (inherited). Events, socket_offsets, sockets, move_speed identical.
`work/clipfix2_hercules/seams.txt`, `clip_motion_after.txt`.

## Rebuild
`work/assemble2_hercules/merge_sources.sh` (14 x ok); `tools/ak export ... --out work/clipfix2_hercules/hercules.glb
--clips-json work/clipfix2_hercules/hercules_clips_raw.json` (export_fps 24, no retime); `strip_props.py` (7.46 MB);
`measure.py > work/clipfix2_hercules/measure.json`; `python3 work/clipfix2_hercules/finalize_manifest4.py <glb> <manifest>`;
copy into game/assets/characters/hercules/; `work/animfix_hercules/import.sh` (lock, exit 0).

## Godot
Loader probe (gdwin, `work/assemble2_hercules/probe.gd`): PASS, 0 SCRIPT ERROR. Home island movies (gdwin, 9 s, 30 fps):
`work/clipfix2_hercules/movie/home_before.avi`, `home_after.avi`, strips `home_ba_strip.jpg` (18 frames 0.5 s apart, top
before / bottom after), `after_zoom.jpg`. Looked at: from behind the pelvis shifts, the sword turns in the re-grip, the
head turns to his left with the face in profile, shield stays at his side. Headless bot fight cyclops seed 1 x3: victory,
blocks and attacks used, 0 SCRIPT ERROR (`fight_cyclops.log`).

## For the game code
- **block_end length 0.25 -> 0.3333 s** (the game reads clip_length; block_end plays under `_hold_until` like before).
- Idle still 6.0 s, no events; everything else unchanged.
