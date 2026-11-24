# Medusa assembly 2: natural-animation clips into the game (assembler, 2026-11-23 09:39-09:50, owner at the Mac)

The owner was at the Mac and could not be asked, so every decision here is mine and written down. Blender ran only
headless. Godot rendered only through `tools/godot_bg/gdwin`. `builds/Hercules.app` was not touched and nothing was committed.
I was the only writer of `art_src/chars/medusa/medusa.blend` and `game/assets/characters/medusa/`.
Scratch: `work/assemble2_medusa/` holds the logs, `measure.py`, `probe.gd`, `movie_probe.gd`, `strip.py`, the movie and the strips.

## Sources (`art_src/chars/medusa/clip_sources.json`): the newest version of each clip, merged by exact path, never by glob
| clip | action file | origin |
|---|---|---|
| idle | clips/idle_n/action_idle.json | new video idle_n (from the natural stance) |
| slither | clips/slither_n/action_slither.json | new video slither_n |
| gaze, hurt, tail_swipe | clips/<clip>/action_<clip>.json | re-based (rebase_done.json) |
| death | clips/death/action_death.json | re-based, **re-baked by me** (see below) |
| stun_start, stunned, rise | clips/stunned/action_<clip>.json | re-based, **re-baked by me** (see below) |

- **Idle frame 0 against natural_pose.json:** every bone entry is identical (largest difference 0.000 deg). The only
  extra entries are six hair bones with 0 deg, plus the tail chain written out with zeros. Measured on the merged blend:
  every one-shot starts on idle frame 0 with 0.00 deg / 0.000 m difference (death, gaze, hurt, stun_start, tail_swipe),
  and gaze, hurt, tail_swipe and rise end on it exactly. So the re-baser's tool did not need a re-run.
- **Bug in the re-base, fixed (my decision):** the re-baser baked death, stun_start, stunned and rise in place
  (`spec.in_place` true). The original animators had baked them with `--keep-root-motion`, and the in-place bake removed
  the forward root slide of the lean recipe (root.loc y -1.7165 m). The result:
  - in the game, the stunned neck moved from 4.56 m to 2.82 m in front of her (probe: neck (0.01, 1.00, 2.82));
  - medusa.gd's `STUN_NECK_LOCAL` (4.55 x S) no longer matched;
  - the bot fight timed out after 90 s with 0 cuts in 9 stun windows.

  I re-baked those four clips from the re-based keys files (unchanged) with `--keep-root-motion`, and root.loc x/y now
  equal the originals at every old key time. The neck is back at (0.01, 1.00, **4.53**). The re-baser's versions are kept
  in `work/assemble2_medusa/rebaser_inplace/`. **Anyone who re-runs `rebase.py` must bake these four with
  `--keep-root-motion`.**
  ```
  tools/ak bake art_src/chars/medusa/medusa.blend --clip <clip> --keys <dir>/keys_<clip>.json [--loop: stunned] --keep-root-motion --out-action <dir>/action_<clip>.json
  ```

## Commands
```
cp game/assets/characters/medusa/{medusa.glb,medusa_clips.json} art_src/chars/medusa/backup_20261123/   # backup, once
tools/ak merge art_src/chars/medusa/medusa.blend <the 9 paths of clip_sources.json>       # rig_hash df3b7a8d3df2, 9 replaced
tools/ak export art_src/chars/medusa/medusa.blend --out game/assets/characters/medusa/medusa.glb \
    --clips-json game/assets/characters/medusa/medusa_clips.json
# then re-add "size" + "offset_space" from the backup manifest (ak export does not write them) and slither "move_speed": 3.2
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
gdwin --path game --resolution 1280x720 --script $PWD/work/assemble2_medusa/probe.gd -- $PWD/work/assemble2_medusa/shots2
HOME=.../home gdwin --path game --resolution 1600x900 --write-movie work/assemble2_medusa/movie/after.avi --fixed-fps 30 \
    --script $PWD/work/assemble2_medusa/movie_probe.gd -- --start=medusa --harness --seed=11
Godot --headless --path game -- --start=medusa --harness --bot=win|lose --speed=3 --seed=<s> --quit-after=200
```

## Manifest (old -> new, compared key by key)
- `sockets` (head, neck, tail_tip, eyes), `socket_offsets`, `size`, `offset_space`: identical.
- Clip names: the same 9. Loop flags and events: identical.
- `slither.move_speed` **3.2** (new field). This is the animator's planted-point speed: a tail wavelength of 5.6 m per
  1.75 s cycle = 3.20 m/s at clip speed 1, equal to T.slither_speed. medusa.gd reads it through
  `CharacterVisual.move_speed(&"slither")`, so the slither rate stays 1.0 at 3.2 m/s. The probe confirms 3.20.

| clip | length old -> new (s) | loop | events old -> new | moving bones (>= 3 deg) old -> new |
|---|---|---|---|---|
| idle | **3.0 -> 6.0** | yes | none | 18 -> 32 /35 |
| slither | **2.0 -> 1.75** | yes | none | 26 -> 34 |
| gaze | 4.25 | no | fire_start 2.0, fire_end 3.25 (same) | 17 -> 30 |
| hurt | 1.625 | no | none | 15 -> 30 |
| tail_swipe | 2.25 | no | impact 0.833 (same) | 25 -> 31 |
| death | 3.5 | no | none | 30 -> 34 |
| stun_start | 1.625 | no | none | 27 -> 31 |
| stunned | 3.0 | yes | none | 13 -> 27 |
| rise | 2.5 | no | none | 25 -> 31 |
All clips are 24 fps, with no retiming. GLB lengths equal the manifest equal the AnimationPlayer lengths (probe).

## `python3 tools/clip_motion.py medusa` (new GLB)
```
=== medusa: 9 clips, 35 joints
  death                   3.50s moving 34/35  frozen: root
  gaze                    4.25s moving 30/35  frozen: pelvis, tail_01, tail_02, tail_04, tail_05
  hurt                    1.62s moving 30/35  frozen: root, tail_02, tail_03, tail_05, tail_06
  idle                    6.00s moving 32/35  frozen: root, tail_06, tail_10
  rise                    2.50s moving 31/35  frozen: root, tail_01, tail_02, tail_04
  slither                 1.75s moving 34/35  frozen: root
  stun_start              1.62s moving 31/35  frozen: root, tail_01, tail_02, tail_04
  stunned                 3.00s moving 27/35  frozen: pelvis, root, spine_01, spine_02, tail_01, tail_02, tail_03, tail_04
  tail_swipe              2.25s moving 31/35  frozen: pelvis, tail_01, tail_02, tail_03
```
What stays under 3 deg, and why:
- `root` does not deform.
- pelvis and tail_01..06 are the planted base of the column and the floor tail (they move 1.1-2.7 deg).
- In stunned, the pelvis, tail_01..03, head and neck are locked on purpose: they are the weak point, the gaze socket and
  the lean pivot. spine_01 and spine_02 breathe 2.0 and 2.5 deg.

**No limb group is frozen.** The arms, hands, shoulders, head, neck, spine and snakes move in every clip.

## Checks on the merged blend (`work/assemble2_medusa/measure.py`: every frame, skinned mesh evaluated)
| clip | frames | lowest vertex z (m) | loop seam (bones deg / vertices m) | in place |
|---|---|---|---|---|
| idle | 145 | 0.000..0.000 | 0.00 / 0.000 | pelvis drift 0 |
| slither | 43 | -0.002..0.002 | 0.00 / 0.000 | 0 |
| stunned | 73 | -0.008..0.006 | 0.00 / 0.000 | 0 (sits 1.72 m forward, as before) |
| gaze | 103 | -0.002..0.023 | one-shot | 0 |
| hurt | 40 | -0.004..0.001 | one-shot | 0 |
| tail_swipe | 55 | -0.002..0.009 | one-shot | 0 |
| stun_start | 40 | -0.005..0.033 | ends = stunned frame 0 | slides 1.72 m forward (kept, as before) |
| rise | 61 | -0.025..0.006 | starts = stunned frame 0, ends = idle frame 0 | slides back |
| death | 85 | -0.043..0.041 | one-shot, ends lying | original slide kept |

- **Ground contact:** the floor tail stays on the floor in every loop.
- **Below the floor:** rise dips 2.5 cm and death 4.3 cm below the floor during the fall (cosmetic).
- **Seams:** the loop seams are exact (the bake copies the first pose, and the curves are cyclic).
- **Slither first pose:** it differs from idle frame 0 by up to 50.6 deg (the floor-tail wave). The game blends between
  them over 0.35 s.

## Godot
- **Import** under the lock: exit 0, no errors.
- **Loader probe:** `work/assemble2_medusa/probe.gd` is the probe from last time plus a move_speed check. Run through
  gdwin, it reports 19 OK and 0 FAIL:
  - real GLB loaded;
  - size 6.5, model_top 6.5;
  - 9/9 clips with length = manifest = animation and loop modes right;
  - 3/3 events, 4/4 sockets on BoneAttachment3D.

  Stunned sockets: neck (0.01, 1.00, 4.53), head (-0.05, 0.67, 4.91).
- **Movie** (chase camera, 30 fps, seed 11, 1600x900, `movie/after.avi`): a stalk approach from 15 m, then a 7 s idle at
  7.7 m, then a forced tail swipe. I looked at the strips in `work/assemble2_medusa/strips/`:
  - idle: arms relaxed and the S-curve weight shift reads;
  - slither: the arms swing against the sway;
  - tail_swipe: watches the sweep, back to the stance.

  The movie used the first export. idle, slither and tail_swipe are byte-identical sources in both exports, so it still holds.
- **Fights** (headless, `--speed=3`):

  | run | polish 3 (old GLB) | new GLB |
  |---|---|---|
  | win, seed 11 | victory 26.21 s | victory 26.22 s |
  | win, seed 4242 | victory 25.28 s | victory 25.32 s |
  | win, seed 7 | victory 27.27 s | victory 34.94 s, 4 gazes instead of 3 |
  | lose, seed 11 | defeat 56.32 s | defeat 56.32 s |

  No SCRIPT ERROR or Parse Error in any run.
- **The seed-7 difference:** in the third stun window the bot's first swings glanced 4 times before a cut landed.
  - The cut landed at neck_y 1.57; normally it lands at 1.43.
  - The re-based stunned breath now moves the neck bone 0.09 m (Blender), about 0.12 m in the game. Before, it was still.
  - So a swing timed for a still neck can pass under it.

  The fight is still won on every seed. For the medusa module owner: if this matters, aim the bot or the weak-point radius
  at the live neck height.

## What the game code must know
- idle is 6.0 s (was 3.0). Nothing times on it.
- slither is 1.75 s (was 2.0) and has `move_speed` 3.2. medusa.gd already scales the rate by it.
- No event time changed. The stunned neck is where `STUN_NECK_LOCAL` expects it (4.53 vs 4.55 x S).
- GLB: 8,446,016 bytes (8.45 MB; was 8,309,072 = 8.31 MB). It has 1 skin with 35 joints and 1 embedded PNG.

## Devlog
`docs/devlog/media_inbox/assemble2_medusa/` holds these files (with captions.txt):
- `medusa_idle_before_after.jpg` and `medusa_slither_before_after.jpg`: the same probe moment, old GLB vs new;
- `medusa_slither_then_idle_after.mp4` (10.5 s);
- `medusa_slither_then_idle_before.mp4`: from the polish-2 movie, which used the old GLB.

## Animation fix pass (animfix2, 2026-11-23 10:00-10:20, owner at the Mac)
I was the only writer of `art_src/chars/medusa/` and `game/assets/characters/medusa/`. Blender ran headless only, Godot
rendered only through `tools/godot_bg/gdwin`, `builds/Hercules.app` was not touched, nothing was committed. Scratch, scripts
and logs: `work/animfix2_medusa/` (backup of every clip source before the pass: `backup_asm2/`; the assemble-2 GLB and
manifest: `art_src/chars/medusa/backup_20261123/assemble2/`). All seven review findings were checked first and all were right.

| finding | what I changed | measured before -> after |
|---|---|---|
| slither: J-curl fans like a wiper, floor tail slides | `slither_n/poses_slither/gen_slither_n.py` got `stance_tail_fade` (stance rz of tail_05..14 x (1 - fade)); `gen_params.json`: fade 1.0, wave 50 -> 40 deg, 6.67 -> 7.0 links per wave, amplitude x1.03 per link toward the tip (picked from 31 sweeps, `sweep1.log`, `sweep2.log`). Upper body, arms, snakes, sway: unchanged; view offsets pasted back | slip (`slip2.py`): best no-slip speed 1.30 -> **3.21 m/s** (old clip 3.01); sideways slip at 3.2 m/s rms 2.24 -> **1.21 m/s**, p90 4.11 -> 1.85 (old clip 1.29 / 2.07); tail_13/14 3.69/3.78 -> 1.53/1.79. Top view: `work/animfix2_medusa/topview_final.png` (the tail trails back in an S again). `move_speed` stays 3.2 |
| idle: still - lurch - still, everything peaks on one frame | new generator `work/animfix2_medusa/idle_gen.py` + `idle_params.json` (copies in `idle_n/poses_idle/`): lean x0.5 and re-split (pelvis -6.5, spine -7/-7/-7, neck -2, head -4 deg at full lean; hips +0.22 m to her left), rise 1.5-2.7 s, hold to 3.0, **return 3.0 -> 4.2 s**; groups follow each other (pelvis + upright tail 0, chest +0.1, shoulders/head +0.25, arms +0.35/+0.38 with a small pendulum lag, snakes +0.4 with a trailing term); a 0.35x counter-shift to her LEFT 4.1-5.6 s (+offsets, ends by 6.0); breath 2.0 deg spine, 3.8 deg shoulders. Frame 0 = natural_pose.json, deltas exactly 0 at 0 and 6 s | head shift to her right 0.66 -> **0.33 m**, drop 0.29 -> **0.09 m**; head-top peak speed 1.59 -> **0.45 m/s**; peak frames pelvis 51, right hand 53, head top 89, left hand 113 (were all 77-79); head-top mean speed per 0.5 s never below 0.04 m/s and 0.18-0.42 from 1.5 to 5.5 s. Moving bones 32 -> 30/35 (frozen: root, tail_01/02, tail_06/10 = planted base and floor tail). Strip IoU vs video 0.878 |
| stunned: breath lifts the "locked" neck 0.099 m | `stunned/poses_stunned/l_t*.json`, `k1_breath.json`: root height fixed at the slump's grounded z (-1.8611) instead of per-key `ground: lowest` (the grounding made the whole body bob 7 cm whenever a twitching hand was the lowest point); spine_02/03 absolute rx counter the breath per key by 2-link IK so the neck head stays on k0_slump's (`stun_ik.py`); the arm twitch keeps its size but its sign is flipped per key on the arm/shoulder group that pushed a hand into the floor (`stun_arms.py`). k0_slump untouched (shared with stun_start / rise) | neck socket over the loop: range 0.099 -> **0.014 m**, max deviation from its mean 0.016 m; mean (0.007, 0.965, 4.541) (assemble2 1.001 / 4.544; original 0.969 / 4.544); probe: stunned neck (0.01, 0.97, 4.54) vs STUN_NECK_LOCAL 4.55 x S. Seed-7 bot fight: victory **27.28 s, 0 glances, 3 gazes** (assemble2 34.94 s, 4 glances; polish 3 27.27 s) |
| rise / stun_start: arms mirror-symmetric | `work/animfix2_medusa/arm_delay.py`: in every inner key the LEFT arm (shoulder, upper arm, forearm, hand) is read back from the action 0.1 s earlier (2.4 frames) + forearm rx +6 / hand rx -7 (half that next to the ends). k0_rest and k0_slump untouched | joints of L vs mirrored R within 2 cm: rise 27/61 -> 1/61 frames, stun_start 19/40 -> 0/40 (median 0.024 -> 0.092 m and 0.021 -> 0.154 m) |
| gaze stare: arms held in a near-T | `gaze/poses_gaze/k5.json`, `k6.json` edited and `k5b.json` (2.75 s), `k5c.json` (3.0 s) added (read back from the action, then arm deltas): right upper arm 5-10 deg higher, forearms breathe +-5 deg out of phase, right hand claws 6-12 deg, left wrist turns 3-4 deg. Neck, head, eyes, events untouched | right hand 0.21-0.25 m higher than the left (was 0.12-0.14); hand_l travel 0.25 -> 0.35 m, forearm_l 0.11 -> 0.17 m in 2.3-3.25 s; eyes socket max 0.007 m from the assemble-2 clip over the whole clip; events 2.0 / 3.25 unchanged |
| hurt: forearm snaps 160 deg in 3 frames, dead stop | `hurt/poses_hurt/kA.json`: the clutch travels further by 0.125 s (forearm side -95 -> -128, front -70 -> -85; upper arm 40/-15 -> 48/-24); new `k1o.json` (0.333 s, 6 deg overshoot forearm, 3 upper arm, hand rx +8) and `k1s.json` (0.458 s, settle 1.5 deg short). Flinch keys and timing unchanged | forearm_r per frame 13 29 34 55 87 39 2 1 ... -> 21 45 28 13 9 6 8 7 4 8 5 0 (no snap, a visible settle); hand_r likewise. Looked at the in-betweens (`work/animfix2_medusa/hurtlook/look.jpg`): the hand goes straight to the neck, nothing through the body |
| death / rise below the floor | grounded keys read back from the action at the dip frames: death `kf1_ground` 0.333, `kf2_ground` 0.792, `kf4_ground` 2.042, `kf5_ground` 2.125, `kf6_ground` 2.208, `kf3_ground` 2.25 s (fall segments keep `linear`); rise `poses_rise/kf1_ground.json` 0.125 s | lowest vertex death -0.043 -> **-0.0085 m**, rise -0.025 -> **-0.010 m** |

Bakes (flags as before): idle, slither `--loop`; gaze, hurt in place; death, stun_start, rise `--keep-root-motion`; stunned
`--loop --keep-root-motion`. Then exactly the assembler's route: `ak merge` with the 9 paths of `clip_sources.json`
(unchanged), `ak export ... --clips-json`, `size`, `offset_space` and slither `move_speed` 3.2 re-added from the assemble-2
manifest (the manifest is now key-for-key identical to it), import under `work/.import_lock` (exit 0, no errors).
GLB 8,444,608 bytes.

Checks on the result:
- `tools/clip_motion.py medusa`: death 34, gaze 30, hurt 30, idle 30, rise 31, slither 34, stun_start 31, stunned 28,
  tail_swipe 31 of 35 moving. Under 3 deg only root, pelvis/tail_01..05 (the planted column base), tail_06/10 in idle
  (floor tail), and in stunned pelvis, spine_01, tail_01..04 (the lean pivot; neck and head are locked on purpose).
- Blender measure (`work/animfix2_medusa/measure2.py`, every frame, skinned mesh): loop seams 0.00 deg / 0.000 m
  (idle, slither, stunned); gaze, hurt, tail_swipe start and end on idle frame 0 exactly; death starts on it; stun_start ->
  stunned -> rise chain on the same slump pose; rise ends on idle frame 0. Lowest vertex: idle 0.000, slither +-0.002,
  gaze -0.002, hurt -0.004, tail_swipe -0.002, stun_start -0.005, stunned -0.006, rise -0.010, death -0.0085.
- Loader probe (`work/animfix2_medusa/probe.gd` = the assembler's, through gdwin): 19 OK, 0 FAIL (9/9 clips, lengths,
  loops, 3/3 events, 4/4 sockets, move_speed 3.20).
- Bot fights (headless, --speed=3): win seed 11 26.19 s, seed 4242 25.29 s, seed 7 27.28 s, lose seed 11 defeat 56.32 s.
  No SCRIPT ERROR or Parse Error.

Still not right (for the lead / the medusa module owner):
- **idle <-> slither hand-over**: with the curl gone from slither, the floor tail must uncurl / re-curl in the 0.35 s
  cross-fade: joints move up to 2.9-3.6 m and the tip 3.5-4.6 m (the assemble-2 clip 1.3-2.0 m, the old clip 1.6-2.2 m).
  It will read as a quick tail whip when she starts or stops moving. A partial fade costs the slip (fade 0.75: best
  speed 2.77 m/s, rms 1.32; fade 0.5: 2.13 m/s, rms 1.61), so I kept the full fade the review asked for. Suggestion
  (medusa.gd, not my file): a longer blend for idle <-> slither only, about 0.6-0.8 s.
- **stunned floor tail floats 5.5 cm** (it already did after the re-base: the slump is grounded on a hand, and the
  re-based tail curve sits higher). Lowering the shared k0_slump would push the hands 5 cm into the floor. Not changed.
- The slither front-view IoU against its video dropped from .77 to .71 (the tail now lies on the travel axis); the side view
  is unchanged (.82).
- Idle head drop is 0.09 m (the review asked for about 0.12); the lateral shift is 0.33 m as asked.
- The strips in the stunned and gaze clip folders are now ours-only rows (no video row).
- **Anyone who re-runs `work/rebase/medusa/rebase.py` overwrites these key edits** in gaze, hurt, death, stun_start,
  stunned and rise (it rebuilds the pose files from the `*.rest_v1.json` originals).

## Clip fix 2 (clipfix2, 2026-11-23 10:57-11:20, owner at the Mac)
I was the only writer of `art_src/chars/medusa/` and `game/assets/characters/medusa/`. Blender ran headless only, Godot
rendered only through `tools/godot_bg/gdwin` (throwaway HOME), `builds/Hercules.app` was not touched, nothing was
committed. Scratch, scripts, logs, strips: `work/clipfix2_medusa/` (backup of every key/pose file I touched, the three old
action JSONs, the old GLB and manifest: `work/clipfix2_medusa/backup/`). The owner could not be asked; every choice below
is mine. Measures: `speed_probe.gd` (Godot, headless: largest bone-head jump per 1/60 s at 1x, game metres; the
integrator's clip_speed_probe plus per-bone windows), `meas.py`/`report.py` (Blender, 60 Hz), `glb_restangle.py` (each
bone's rotation away from its rest in the GLB, the quantity Godot's cross-fade slerps), `join_probe.gd` (stunned -> death
cross-fade at several join times, headless).

| problem | what I changed | before -> after |
|---|---|---|
| 1 stun_start arms fall in 2 frames | `fix_stun.py`: in g05 (1.375), g06 (1.458), g07 (1.542) only the arm bones (shoulder, upper arm, forearm, hand, both sides) were rewritten as absolute entries: their local rotation = slerp(local at g05, local at k0_slump) with a smoothstep, right arm over 1.333-1.625 s (0.29 s), left over 1.375-1.625 s (0.25 s, keeps the animfix2 lag). Body, root, key times, k0_slump untouched | Godot: hand_r **0.823 -> 0.609**, hand_l **0.823 -> 0.578**, forearm_r 0.510 -> 0.467, forearm_l 0.561 -> 0.462 m per 1/60 s. hair_l_01 0.706 -> 0.706: it is not an arm, it rides on the falling head (head 0.71 in the same frames), so it is the fall itself. End pose = stunned frame 0 (min quaternion dot 0.999999, root loc identical) |
| 2 death hair_l_01 whip at 1.85 s | `fix_death.py`: k3a_turn rebuilt as the pose at fraction 0.65 (slerp of every bone + root, ground lowest) between k3_arch (1.75) and the new k3b_twist (1.875). Note: at 24 fps the 1.8125 key snaps to frame 44 = 1.833 s, so 0.65 makes both segments the same speed. The rebuild floated the body 10.7 cm at 1.7917 s: new grounded read-back key `kf7_ground.json` (1.7917, linear) | Godot: hair_l_01 **1.536 -> 0.966** (now at 1.93 s, the untouched k3b -> k3c part of the fall, same level as the rest of the fall 0.91-0.96), hand_l 1.339 -> 0.768, head 0.928 -> 0.654. Lowest vertex of death -0.0085..0.0407 (unchanged) |
| 3 death left arm flip ~2.55-2.6 s | The upper arms lie rolled ~175-180 deg about their own axis away from rest; Godot's cross-fade slerps each bone from its rest the short way, so crossing 180 flips the arm. `fix_death.py` rolls both upper arms toward rest about their own axis from 1.875 s (15 deg at 1.875, 30 at 1.917, 50 from 2.0 to the end; left +, right -), the forearm takes half the roll about its own axis, the hand keeps its world orientation. Fall timing, root, body: unchanged | Rotation from rest in the GLB after 1.95 s: upper_arm_l max **180 -> 148** deg (2.5-2.7 s: 177-180 -> 145-138), upper_arm_r **179 -> 153**. Join probe (stunned -> death, 0.6 s fade): joins at 2.25 / 2.4 / 2.5 / 2.55 / 2.6 / 2.75 s all max **0.69** m/frame (the tail settling), no hand jump (integrator before: join 2.25 -> hand_l 2.58 m in one frame). Strip `death_lie.jpg`: the lying pose reads the same |
| 4 idle frozen at fight-start distance | Recorded `--start=medusa` (gdwin, 1280x720, shots every 0.5 s): she idles only 0-2.4 s (title card, wide shot, she is ~200 px tall), then stalks. Frames 0.5/1.0/1.5/2.0 s looked identical. `idle_params.json` only (generator unchanged, re-run): breath x1.7 (spine 2 -> 3.5, head 1.5 -> 2.5, shoulders 3.8 -> 6.5 deg), snakes amplitude x2.2 and 2-3 cycles per 6 s (were 1-2), lean_k 0.5 -> 0.65 and the lean starts at 0.3 s (was 1.5 s; lean 0.3-1.8, hold to 2.2, back by 3.5), counter-shift 0.35 -> 0.5 at 3.5-5.3 s (all group offsets end by 5.95 s), tail flick 0.5 -> 1.0, tail wave 1.8 -> 3.0 | changed pixels on her between 0.5 s frames 685 / 528 / 2262 -> **3410 / 4180 / 2120** (`idle_crop_ba.png`: snakes, lean and breath now read); per 0.5 s (Blender m) head top median 0.126 -> 0.170, first 2 s 0.025-0.049 -> 0.044-0.317; snake tips 0.10-0.36 -> **0.29-0.53**; chest median 0.040 -> 0.058. Still calm: largest jump 0.029 -> 0.044 m/frame (game). Frame 0 unchanged (= natural_pose.json), loop seam 0.00 deg / 0.000 m |

Route afterwards, exactly the assembler's: bakes with the same flags (stun_start, death `--keep-root-motion`; idle
`--loop`), `ak merge` with the 9 paths of `clip_sources.json`, `ak export ... --clips-json`, `size`, `offset_space`,
slither `move_speed` 3.2 re-added from the old manifest: the manifest is **byte-identical** to the previous one (sockets,
socket_offsets, events, loops, lengths). Import under `work/.import_lock`: exit 0, no errors. GLB 8,444,460 bytes.

Checks on the result:
- `tools/clip_motion.py medusa`: death 34, gaze 30, hurt 30, **idle 33** (was 30), rise 31, slither 34, stun_start 31,
  stunned 28, tail_swipe 31 of 35.
- Blender measure (`work/animfix2_medusa/measure2.py` on the merged blend): every number equal to animfix2's except the
  death end pose (the rolled arms: end-vs-idle0 302.4 -> 315.5 deg, vertices 8.6287 m unchanged). Seams 0.00 deg / 0.000 m
  (idle, slither, stunned); gaze, hurt, tail_swipe start and end on idle frame 0; death starts on it; stun_start ->
  stunned -> rise chain on k0_slump; rise ends on idle frame 0.
- Loader probe (animfix2's probe.gd through gdwin): **19 OK, 0 FAIL**.
- Bot fights (headless, --speed=3): win seed 11 **26.21 s**, win seed 7 **27.27 s** (3 reflected gazes each), lose seed 11
  defeat **56.32 s** (4 gaze hits). integrate2's final: 26.20 / 27.26 / 56.31. No SCRIPT ERROR or Parse Error.

Still not right / for the lead:
- death 1.78-1.85 s: the left upper arm still passes 180 deg from rest during the turn (its roll runs from +96 deg at
  1.75 to -114 at 1.875; there is no short way between them without a different arm path). The clip alone is smooth; a
  game cross-fade that starts inside 1.75-1.9 s would flip it. The game joins only at 0 and 2.6 s (DEATH_FROM_FLOOR).
- stun_start: hair_l_01 0.71 m/frame at 1.43-1.47 s (0.92 at the game's 1.3x) is the head falling; the arms no longer pop.
- The death end pose changed slightly (upper arms rolled 50 deg about their own axis, forearms 25, hands unchanged).
- Anyone who re-runs `work/rebase/medusa/rebase.py` or the old idle_params overwrites these edits.
