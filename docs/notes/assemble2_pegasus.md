# Pegasus assembly 2 (natural pass, assembler, 2026-11-23)

The owner was at the Mac and could not be asked, so I made every decision below and wrote it down here. Blender ran
headless only. Godot rendering went through `tools/godot_bg/gdwin` only (off-screen, no focus, no sound), with a
throwaway HOME. `builds/Hercules.app` was not touched. Scratch: `work/assemble2_pegasus/`.

## Inputs and decisions
- `art_src/chars/pegasus/rebase_done.json` was present at the start (no wait needed).
- **`art_src/chars/pegasus/clip_sources.json`** (clip -> action file, newest source):

  | clip | source | why |
  |---|---|---|
  | idle | `clips/idle_n/action_idle.json` | new video idle_n (natural stance); replaces `clips/idle/action_idle.json` |
  | fly | `clips/fly/action_fly.json` | re-based on `ridden/fly/action_fly.json`; the 25 deg rider sweep is ALREADY in it |
  | glide | `clips/glide/action_glide.json` | re-based matched glide |

  - Merged exactly these three paths, never a glob (the `*.rest_v1.json` backups carry the same clip names).
  - `ridden/fly/action_fly.json` was NOT merged, and `ridden/make_ridden.py` was NOT run (that would add a second 25 deg
    sweep, docs/notes/rebase_pegasus.md).
  - `art_src/chars/ride/clips/ride/` still holds only the hercules `ride` action (29 bones, other rig hash): no
    pegasus `fly_ridden` to include, same as 2026-11-22.
- **Idle first pose vs `natural_pose.json`:** `clips/idle_n/poses_idle/k00.json` is the natural pose exactly (every bone
  and the root: 0.00 deg difference). So no re-base re-run was needed. Pegasus has no one-shots anyway, and neither
  flight clip starts from the standing stance (rebase_pegasus.md).

## Commands (repo root)
```
mkdir -p art_src/chars/pegasus/backup_20261123
cp -p game/assets/characters/pegasus/{pegasus.glb,pegasus_clips.json} art_src/chars/pegasus/backup_20261123/
cp -p art_src/chars/pegasus/pegasus.blend work/assemble2_pegasus/pegasus_before_merge2.blend.bak
tools/ak merge art_src/chars/pegasus/pegasus.blend art_src/chars/pegasus/clips/idle_n/action_idle.json \
    art_src/chars/pegasus/clips/glide/action_glide.json art_src/chars/pegasus/clips/fly/action_fly.json
tools/ak export art_src/chars/pegasus/pegasus.blend --out game/assets/characters/pegasus/pegasus.glb \
    --clips-json game/assets/characters/pegasus/pegasus_clips.json
python3 art_src/chars/pegasus/ridden/finish_manifest2.py
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
```
- merge: `rebaked` and `replaced_existing` = idle, glide, fly; rig_hash 02e3e4139ce9, ok.
- export: 3 clips at 24 fps, 1 skin, 1 image, GLB lengths fly 1.0417 / glide 3.0 / idle 6.0. Nothing was retimed.
- `finish_manifest2.py` is the 11-22 `finish_manifest.py` with two changes:
  - each clip's `source` is read from clip_sources.json
  - the rider `clearance` text is updated, and a new `rider.idle_clearance` note is added

  The old script would have written the old sources back.

## Manifest: old vs new, key by key
| key | old | new |
|---|---|---|
| sockets, socket_offsets (saddle 0/0.2471/-0.2, head 0/0.2777/-0.0131), offset_space godot, socket_notes | | identical |
| size (2.994 / 1.9 / 2.945 / 2.287 m) | | identical |
| rider.offset, offset_from_saddle_bone_head, hips_seat, beat_period_s, rider_clip(+length), fly_beat_s 1.0417, rider_speed_on_fly 1.44, rider_speed_on_glide 0.4, phase, beat_note, fly_bob | | identical |
| clips.idle.length | 7.0 | **6.0** |
| clips.*.loop / events | true / {} | identical |
| clips.*.source | old paths | the clip_sources.json paths |
| rider.clearance | text | text updated (fly/glide checks from the re-base) |
| rider.idle_clearance | - | NEW note: idle is not rider-safe |
| move_speed | none (Pegasus has no walk clip) | none (not added) |

## Clips: old vs new
| clip | length old -> new | loop | events | samples in the GLB | loop seam (first = last, all channels) | moving bones old -> new |
|---|---|---|---|---|---|---|
| idle | 7.000 -> **6.000 s** | yes | none -> none | 169 -> 145 | 0.000 deg, 0.00000 m | 16 -> **32** of 43 |
| fly | 1.0417 -> 1.0417 s | yes | none | 26 -> 26 | 0.000 deg, 0.00000 m | 28 -> **38** |
| glide | 3.000 -> 3.000 s | yes | none | 73 -> 73 | 0.000 deg, 0.00000 m | 13 -> **38** |

GLB size: 7,113,520 -> 7,189,940 bytes (7.12 -> 7.19 MB).

## `python3 tools/clip_motion.py pegasus`
Before (backup GLB):
```
  fly                     1.04s moving 28/43  frozen: hips, neck_03, root, saddle, spine_01, spine_02, spine_03, wing_l_03, wing_l_feather_01, wing_l_feather_02, wing_l_feather_03, wing_r_03, wing_r_feather_01, wing_r_feather_02, wing_r_feather_03
  glide                   3.00s moving 13/43  frozen: head, hips, hoof_bl, hoof_br, hoof_fl, hoof_fr, leg_bl_01, leg_bl_02, leg_bl_03, leg_br_01, leg_br_02, leg_br_03, leg_fl_01, leg_fr_01, neck_01, neck_02, neck_03, root, saddle, spine_01, spine_02, spine_03, tail_01, tail_05, wing_l_feather_01, wing_l_feather_02, wing_l_feather_03, wing_r_feather_01, wing_r_feather_02, wing_r_feather_03
  idle                    7.00s moving 16/43  frozen: hips, hoof_bl, hoof_br, hoof_fl, hoof_fr, leg_bl_01, leg_bl_02, leg_bl_03, leg_br_01, leg_br_02, leg_br_03, leg_fl_01, leg_fl_02, leg_fl_03, leg_fr_01, leg_fr_02, leg_fr_03, neck_01, root, saddle, spine_01, spine_02, spine_03, wing_l_03, wing_l_feather_02, wing_r_03, wing_r_feather_02
```
After (game GLB):
```
=== pegasus: 3 clips, 43 joints
  fly                     1.04s moving 38/43  frozen: hips, root, saddle, spine_01, spine_02
  glide                   3.00s moving 38/43  frozen: hips, root, saddle, spine_01, spine_02
  idle                    6.00s moving 32/43  frozen: hips, hoof_fl, hoof_fr, leg_fl_01, leg_fl_02, leg_fl_03, leg_fr_01, leg_fr_02, leg_fr_03, root, saddle
```
- `root` and `saddle` do not deform.
- idle:
  - The 8 foreleg bones are the planted feet. This is allowed.
  - hips moves 3.0 deg, just under the 3 deg line (the idle animator called it borderline). The whole body still
    rolls and yaws through the root during the weight shift.
- fly / glide: hips, spine_01 and spine_02 stay still on purpose. The saddle and both wing roots hang there, and the
  rider and the wing beat must not move (rebase_pegasus.md). spine_03, the neck and the root bob carry the body's
  answer to the beat.
- No limb group is frozen.

## Ground contact (lowest vertex per key, from the action JSONs)
| clip | lowest_z min..max | left side | right side |
|---|---|---|---|
| idle | 0.000..0.000 m | 0.000..0.009 | 0.000..0.014 |
| fly (in the air) | -0.034..0.113 | 0.088..0.113 | -0.034..0.169 |
| glide (in the air) | 0.109..0.150 | | |

- idle stands on the floor on every key.
- The flight clips are only played in the air. fly's -0.034 m is a dangling hoof at the wing top. The old ridden fly
  had the same value (-0.032 m), and the root bob is unchanged.

## Godot proof
- Import under the lock: OK.
- Loader probe `work/assemble_pegasus/probe.gd` (unchanged) through gdwin, 1280x720, printed `PROBE ok=true`:
  - real GLB, 1 toon material, model_top 2.994
  - every clip has `has_clip` true, length = manifest = AnimationPlayer length (fly 1.0417, glide 3.0, idle 6.0),
    loop mode linear
  - both sockets are BoneAttachment3D: saddle (0, 2.127, -0.300), head (0, 2.450, 1.250), as on 11-22
  - bounds 2.287 x 2.994 x 2.945 m
  - Shots: `work/assemble2_pegasus/shots/`.
- Movie `work/assemble2_pegasus/movie.gd`: gdwin `--write-movie` at 30 fps, recorded once BEFORE the export (old GLB)
  and once after.
  - Segments: idle 6 s from a 3/4 home-island view (no rider), then fly (2 beats) and glide (3 s) with the seated
    hercules from the flight chase camera.
  - The frames are 1600x900, and segment frames start 3 frames into the file.
  - Files: `before.avi` / `after.avi` (+ mp4).
  - Contact sheets: `idle_after_check.jpg` and `flight_after_check.jpg`.
- What I saw:
  - idle: a natural stance with the wings folded and uneven, and weight on alternating hind legs (the resting hoof
    changes between 2.2 and 5.2 s). The head turns, the tail flicks at 2.2 s and the wings flare at 5.2 s. No pops, no
    mesh through mesh, hooves on the floor.
  - fly / glide: the rider sits on the back with the wings outside his legs on every frame. The beat reads as before,
    with softer wing tips. (Pegasus has no walk and no attack: fly and glide are its moving clips.)
- Headless `--start=home` and `--start=sea` with `--harness --bot=idle --quit-after=6`: `result=quit`, no SCRIPT ERROR.

## What changed for the game code
1. **idle length 7.0 -> 6.0 s.** No events, and nothing in the game times on it (home_base.gd plays it as a loop).
2. **Mounting (world: home_base.gd), needs a code change.**
   - The new idle folds the wings where the rider's legs hang. The idle animator's `ridden/pair_check.py` run found
     hits on 36 of 36 frames, including the first pose.
   - Today `_mount()` keeps Pegasus in `idle` during the 0.55 s hop (MOUNT_HOP) and only calls `pegasus.play(&"fly", 0.3)`
     once the rider is seated (line ~188). The rider therefore lands in the folded wings.
   - Fix: call `pegasus.play(&"fly", 0.3)` at the start of `_mount()` (around line 131, next to the neigh), so the
     wings are up before he arrives. The play at line 188 can stay (same clip, no restart) or go.
   - Any future dismount must leave fly/glide only after the rider is off.
   - The manifest says this in `rider.idle_clearance`.
3. fly and glide: lengths, beat phase (t 0 = wing top), root bob (fly_bob) and the rider numbers are unchanged. No
   change is needed.
4. No `move_speed` (Pegasus has no walk clip; flight speed is game code).

## Files written
- `art_src/chars/pegasus/pegasus.blend`:
  - the merged actions idle (new), glide and fly (re-based)
  - pre-merge copy: `work/assemble2_pegasus/pegasus_before_merge2.blend.bak`
- `art_src/chars/pegasus/backup_20261123/`: the old pegasus.glb + pegasus_clips.json.
- `art_src/chars/pegasus/clip_sources.json`, `art_src/chars/pegasus/ridden/finish_manifest2.py`.
- `game/assets/characters/pegasus/pegasus.glb`, `pegasus_clips.json` (+ the Godot import files).
- Devlog: `docs/devlog/media_inbox/assemble2_pegasus/`:
  - idle and flight before/after JPEGs + side-by-side mp4s
  - captions.txt
- No Higgsfield credits used.

---
# Animation fixer pass (2026-11-23, after the natural review of pegasus)

The owner was at the Mac and could not be asked; every decision is written here. Blender ran headless only, Godot rendering
only through `tools/godot_bg/gdwin` with a throwaway HOME (`work/anim2/pegasus_fix/home`), `builds/Hercules.app` untouched.
I am the only writer of `art_src/chars/pegasus/` and `game/assets/characters/pegasus/` for this pass. Scratch:
`work/anim2/pegasus_fix/`.

## Findings: checked, then fixed
| # | finding | check (my measurement) | fix |
|---|---|---|---|
| 1 major | idle: both hind hooves slide | TRUE. pk.py on v1 every half frame: hoof_bl / hoof_br heads travel 0.47 / 0.50 m in y, planted (lowest vertex < 1.2 cm) the whole time, up to 0.94 / 0.98 m/s | idle v2: four staged IK steps (below) |
| 2 major | home_base.gd keeps idle during the mount hop | TRUE. `_mount()` plays `fly` only at line 188 (after MOUNT_HOP), `git diff HEAD` shows no change. Idle v2 also hits a seated rider on 48 of 48 frames (pair_check at 1.0x) | NOT my file: see "Game code" below |
| 3 minor | idle: forehooves float 2-3 cm | TRUE. v1 hoof_fl lowest vertex 0.000 -> 0.028 m at 2.75 s | v2: forehooves IK-planted, lowest 0.000 (+-0.0002), head z constant |
| 4 minor | fly: mirror-symmetric beat, legs on one curve | TRUE. wing_01/02 L/R corr 1.000, max diff 0.0 deg; legs corr 1.000 | fly v3: right wing 1 frame late x0.97, legs de-phased |
| 5 minor | fly: downstroke jerk, wing_02 hitch at the top | TRUE. wing_01 2.9, 4.8, 7.2, **44.4**, 31, 27, 29 deg/frame (frames 3-10); wing_02 into the seam 9.1, 5.3, out 1.4 | fly v3: time warp of both wing chains (numbers below) |
| 6 minor (opt.) | glide: quiet, wing roots in unison | TRUE. wing_01 L/R corr 1.000 | glide v3: right wing 0.125 s late, 1.5 deg forehand bank |

## idle v2 (8.0 s, was 6.0)
- Generator `work/anim2/pegasus_fix/gen2_bl.py` + `params2.json` (headless Blender, pegasus.blend read-only). Life layer =
  the v1 gen.py terms on an 8 s loop. Legs solved by IK on every key: each hoof has a world target (fetlock head position +
  hoof world orientation, absolute bone space corrected for root.rot); root z is fixed, no root.ground. Max IK error 0.33 mm.
- Steps (clip time): 2.45-2.85 the resting LEFT hind lifts (toe clears 6.9 cm, hoof curls 14 deg) and plants under the hip;
  2.85-3.25 the RIGHT hind lifts 5.7 cm and is set down in the resting spot, toe down; 6.85-7.25 right hind back under the
  hip (6.8 cm); 7.25-7.65 left hind back to rest (5.7 cm). Root roll and hip yaw lead each pair by 0.1 s.
- **Length 6.0 -> 8.0 s.** Why: one shift at video 4 s and the shift back at 8 s (the prompt), each stance held ~3.5 s
  instead of two shifts in 6 s (read fidgety). Breathing is now one breath per 4 s (L/2; brief: 3-4 s). No events; nothing
  in the game times on the idle (home_base.gd loops it).
- **natural_pose.json changed** (= idle k00): the resting hind hoof is 0.20 m (was 0.48 m) ahead of the standing one and 4 cm
  inward, toe tipped as before; the forehooves are put on the floor (they floated 0.9-1.1 cm); explicit root z 0.0054, no
  root.ground. Old file: `natural_pose.v1.json` (gen2 reads it as its base). The sheet `sheet_nat_std.png` and the idle_n
  video started from v1; the difference is the resting hind leg only.
- Proof (`pk.py` + `slide.py`, every half frame): planted fetlock heads move <= 0.65 cm in xz (forehooves 0.00 cm) while
  the other hoof is in the air; lowest vertex 0.000 on every planted hoof. In-game check: gdwin movie
  `work/anim2/pegasus_fix/after.avi` (idle 8 s home view, idle 8 s low side view, fly, glide); side frames
  `side_movie.jpg`: each hind hoof visibly lifts and is set down, the others stay.

## fly v3 / glide v3
- fly (1.0417 s, t 0 = wing top, fly_bob root curve unchanged, rider-safe 25 deg sweep inherited, make_ridden.py NOT run):
  `work/anim2/pegasus_fix/fly/fly2_bl.py` + `fly_params.json` on `keys_fly.rebase.json`. wing_01 per-frame turn at the
  downstroke start 7.2 -> 44.4 became 8.1, 17.5, 28.0, 30.5, 28.8, 23.0, 9.9 (frame 5 = t 0.208 is 13 deg into the stroke);
  upstroke start 2.4 -> 21.3 -> 40.0 became 4.5, 12.0, 23.9, 29.9, 23.9; wing_02 eases into the top 10.2, 8.8, 6.5, 4.2.
  Right wing chain 1 frame late, swing x0.97 (L/R corr 0.965 / 0.825). leg_fr 0.0625 s, leg_bl 0.042 s, leg_br 0.1 s late.
- glide (3.0 s): `glide2_bl.py`: right wing chain 0.125 s late (corr 0.846), spine_03 subtree banks 1.5 deg over the loop.
- Rider pair check (`ridden/pair_check.py` on a scratch copy of ride.blend, `work/anim2/pegasus_fix/rc/`): fly 0 hits / 50
  samples (one rider loop per beat), glide 0 hits / 72 (0.4x). Strips (akg): fly 0.587 (re-base 0.589), glide 0.595 (0.595).

## Merge, export, import (same commands as above)
```
cp -p game/assets/characters/pegasus/{pegasus.glb,pegasus_clips.json} art_src/chars/pegasus/backup_20261123_fix/
cp -p art_src/chars/pegasus/pegasus.blend work/anim2/pegasus_fix/pegasus_before_fix.blend.bak
tools/ak merge art_src/chars/pegasus/pegasus.blend art_src/chars/pegasus/clips/idle_n/action_idle.json \
    art_src/chars/pegasus/clips/glide/action_glide.json art_src/chars/pegasus/clips/fly/action_fly.json
tools/ak export art_src/chars/pegasus/pegasus.blend --out game/assets/characters/pegasus/pegasus.glb \
    --clips-json game/assets/characters/pegasus/pegasus_clips.json
python3 art_src/chars/pegasus/ridden/finish_manifest3.py
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
```
- merge: rebaked + replaced idle, glide, fly; rig_hash 02e3e4139ce9. export: 24 fps, GLB lengths fly 1.0417 / glide 3.0 /
  idle 8.0, nothing retimed, 7.23 MB (was 7.19).
- `finish_manifest3.py` = finish_manifest2 with updated `rider.clearance` / `rider.idle_clearance` texts and a new
  `rider.mount` note. Manifest diff vs the assemble2 one: `clips.idle.length` 6.0 -> 8.0 and those three texts; sockets,
  socket_offsets, size, rider offsets/speeds/phase, loops, events (none) identical.
- clip_sources.json: same three paths (the files were regenerated in place); "why" texts updated; the backups
  `*.v1.json` (idle) and `*.rebase.json` (fly, glide) carry the clip names: never merge them.

## Checks after the import
```
=== pegasus: 3 clips, 43 joints
  fly                     1.04s moving 38/43  frozen: hips, root, saddle, spine_01, spine_02
  glide                   3.00s moving 38/43  frozen: hips, root, saddle, spine_01, spine_02
  idle                    8.00s moving 39/43  frozen: hips, leg_fl_03, root, saddle
```
- idle 32 -> 39 moving: the forelegs now flex with the trunk (leg_fl_03 2.8 deg is a planted cannon); hips 3.0 deg as before.
- Loop seams in the GLB (check_glb.py): 0.000 deg / 0.00000 m on every channel of all three clips; idle 193 samples.
- Events: none in any clip (as before). socket_offsets unchanged.
- Loader probe (`work/assemble_pegasus/probe.gd` via gdwin 1280x720): `PROBE ok=true`; has_clip, manifest length =
  AnimationPlayer length (fly 1.0417, glide 3.0, idle 8.0), loop linear; saddle socket at fly t 0 / 0.333 and glide t 0.75
  identical to the assemble2 run (0, 2.127, -0.300) / (0, 2.168, -0.300) / (0.011, 2.127, -0.300).
- Headless `--start=home` and `--start=sea` with `--harness --bot=idle --quit-after=6`: result=quit, no SCRIPT ERROR.

## Game code (lead / world owner): needed, NOT done by me
1. `game/scripts/world/home_base.gd` `_mount()`: add `pegasus.play(&"fly", 0.3)` at the start (next to the neigh, line
   ~133), so the wings rise during the 0.55 s hop; the call at line 188 can stay (same clip, no restart). Idle v2 still
   folds the wings over the saddle: 48 of 48 frames hit a seated rider. Re-check with a gdwin movie from the mount camera.
2. Where the rider mounts: from the side at the saddle (MOUNT_OFFSET 1.75 m) is clear: the folded wings reach ~1.1 m from
   the centre line, the hind hooves step 0.2 m fore-aft at 0.26-0.30 m from the centre line (2.45-3.25 s, 6.85-7.65 s),
   the forehooves never move. Manifest `rider.mount` says the same.
3. idle length 6.0 -> 8.0 s: nothing to re-tune (no events, loop only).

## Files written
- `art_src/chars/pegasus/`: natural_pose.json (+ natural_pose.v1.json), clip_sources.json, pegasus.blend (merged),
  ridden/finish_manifest3.py, backup_20261123_fix/ (assemble2 GLB + manifest),
  clips/idle_n/{keys_idle.json, poses_idle/k00-k66, action_idle.json, strip_idle.jpg, notes.md} (+ *.v1 backups),
  clips/fly/{keys_fly.json, poses_fly/fx_k*.json, action_fly.json, strip_fly.jpg/mp4, notes.md} (+ *.rebase backups),
  clips/glide/{keys_glide.json, poses_glide/fx_k*.json, action_glide.json, strip_glide.jpg/mp4, notes.md} (+ *.rebase).
- `game/assets/characters/pegasus/pegasus.glb`, `pegasus_clips.json` (+ import files).
- Devlog: `docs/devlog/media_inbox/anim_fix_pegasus/` (idle_weight_shift_steps.jpg, fly_v3_strip.jpg, captions.txt).
- No Higgsfield credits used.
