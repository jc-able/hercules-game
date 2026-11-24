# Cyclops assembly 2: the natural-animation pass (assembler, 2026-11-23; the owner was at the Mac, nothing was shown or played)

Delivered: `art_src/chars/cyclops/cyclops.blend` (8 actions re-merged), `game/assets/characters/cyclops/cyclops.glb`
(9.10 -> **9.17 MB**, 1 skin / 29 joints, 2 embedded PNGs, meshes `cyclops` + `club`, export_fps 24, no clip retimed) and
`cyclops_clips.json`. Backup of the old pair: `art_src/chars/cyclops/backup_20261123/` (the old blend is git HEAD).
Scratch: `work/assemble2_cyclops/`.

## Sources (`art_src/chars/cyclops/clip_sources.json`, newest source per clip)
| clip | action JSON | source |
|---|---|---|
| idle | clips/idle_n/action_idle.json | new video idle_n (replaces clips/idle) |
| walk | clips/walk_n/action_walk.json | new video walk_n (replaces clips/walk) |
| sweep | clips/sweep/action_sweep.json | re-based (rebase_done.json) |
| slam, stuck, pull_free | clips/slam/action_{slam,stuck,pull_free}.json | re-based |
| hurt | clips/hurt/action_hurt.json | re-based |
| death | clips/death/action_death.json | re-based (keeps root motion) |
No clip was left untouched. `*.rest_v1.json` backups were never passed to merge.

Idle first pose vs `natural_pose.json`: `idle_n/poses_idle/k00.json` is identical to it (only `_note` differs), so the
re-baser's tool was NOT re-run. In the GLB every one-shot starts/ends on the idle's frame 0 (max joint deviation 0.000 m,
table below); before this pass the one-shots started 0.49 m away from idle frame 0 (the old T pose).

## Commands
```
mkdir -p art_src/chars/cyclops/backup_20261123 && cp game/assets/characters/cyclops/{cyclops.glb,cyclops_clips.json} art_src/chars/cyclops/backup_20261123/
python3 tools/clip_motion.py --glb art_src/chars/cyclops/backup_20261123/cyclops.glb      # before table
tools/ak merge art_src/chars/cyclops/cyclops.blend <the 8 paths of clip_sources.json, in its order>   # ONE call: the
      # cmd_merge frame-0 bug from assemble_cyclops.md is fixed (clear_anim before bake_data); seams verified below
tools/ak export art_src/chars/cyclops/cyclops.blend --out game/assets/characters/cyclops/cyclops.glb \
      --clips-json game/assets/characters/cyclops/cyclops_clips.json
python3 work/assemble2_cyclops/finish_manifest.py      # carries offset_space/size/sockets/socket_offsets/death root_motion
      # over from the backup manifest, adds walk move_speed, prints the key-by-key diff (asserts socket_offsets identical)
python3 tools/clip_motion.py cyclops
python3 work/assemble2_cyclops/glb_check.py <glb> <out.json>   # numpy FK + skinning: seams, chains, ground, club, top
python3 work/assemble2_cyclops/walk_speed.py <glb>             # planted foot/toe joint speed of walk
until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock
tools/godot_bg/gdwin --path game --resolution 1280x720 --script <abs>/work/assemble2_cyclops/probe.gd -- --harness --out=<abs>/work/assemble2_cyclops/shots
tools/godot_bg/gdwin --path game --resolution 1280x720 --fixed-fps 30 --write-movie <abs>/after.avi --script <abs>/work/assemble2_cyclops/movie.gd -- --harness [--before]
python3 work/assemble2_cyclops/strip.py <avi> <jpg> <label>
Godot --headless --path game -- --start=cyclops --harness --bot=win --seed=1 --speed=3 --quit-after=100
```
(Godot runs with HOME/CFFIXED_USER_HOME = work/assemble2_cyclops/home; windowed ones only through gdwin.)

## Manifest: old vs new, key by key (61 keys, 59 identical)
| key | old | new |
|---|---|---|
| clips.idle.length | 3.3333 | **6.0** |
| clips.walk.move_speed | (absent: cyclops.gd fell back to Tuning walk_move_speed 2.43) | **2.54** (+ `speed_note`) |
| source.clips_from | clips/<video>/action_<clip>.json | clip_sources.json |
Identical: sockets, socket_offsets (asserted), offset_space "godot", size, every loop flag, every event name and time,
death root_motion true, every other length.

`move_speed` 2.54 m/s = the walk_n animator's planted-foot speed (`ak solve` every frame: 1.48 m per 0.58 s stance).
GLB re-measure (foot joint while the foot is <= 3 cm from the floor): mean 2.60 m/s, median 2.68 (toe joint 2.84, it
rolls); in the Godot probe the planted right foot travels 1.18 m in 0.472 s = 2.50 m/s. So 2.54 is kept.

## Clips old vs new (GLB)
| clip | length s old -> new | loop | events old -> new | moving joints old -> new (of 29) | seam / chain (max joint dev) | lowest body vertex min..max m | club lowest m |
|---|---|---|---|---|---|---|---|
| idle | **3.3333 -> 6.0** | yes | none | 9 -> 25 | seam 0.000 | 0.000..0.002 | 5.95 (on the shoulder) |
| walk | 1.4167 | yes | step 0.40 (same) | 13 -> 27 | seam 0.000; frame 0 is 0.41 m from idle f0 (cross-faded by loco_blend) | -0.032..0.050 | 5.91 |
| sweep | 2.5 | no | impact 1.31 (same) | 21 -> 27 | start = end = idle f0 (0.000) | -0.055..0.039 | 0.25 |
| slam | 1.75 | no | impact 1.5 (same) | 24 -> 26 | start = idle f0, end = stuck f0 (0.000) | -0.002..0.008 | -0.68 (in the ground) |
| stuck | 1.5 | yes | none | 11 -> 22 | seam 0.000 | -0.009..0.009 | -0.70 |
| pull_free | 1.5 | no | none | 24 -> 26 | start = stuck f0, end = idle f0 (0.000) | -0.039..0.018 | -0.68 |
| hurt | 0.6667 | no | none | 15 -> 22 | start = end = stuck f0 (0.000) | 0.000..0.000 | -0.73 |
| death | 4.5 | no | none (root_motion) | 26 -> 29 | start = idle f0 (0.000); ends lying (own pose) | -0.030..0.043 | -0.16 |

`python3 tools/clip_motion.py cyclops` (after):
```
  death                   4.50s moving 29/29  frozen:
  hurt                    0.67s moving 22/29  frozen: foot_l, foot_r, hips, root, spine_02, toe_l, toe_r
  idle                    6.00s moving 25/29  frozen: foot_r, root, toe_l, toe_r
  pull_free               1.50s moving 26/29  frozen: root, toe_l, toe_r
  slam                    1.75s moving 26/29  frozen: root, toe_l, toe_r
  stuck                   1.50s moving 22/29  frozen: foot_l, foot_r, hips, root, spine_02, toe_l, toe_r
  sweep                   2.50s moving 27/29  frozen: toe_l, toe_r
  walk                    1.42s moving 27/29  frozen: hand_u_r, root
```
Before: idle 9, walk 13, stuck 11, hurt 15, sweep 21, slam 24, pull_free 24, death 26 (work/assemble2_cyclops/motion_before.txt).
Frozen entries left: `root` (non-deforming), feet/toes planted, hips + spine_02 in hurt/stuck (2-3 deg: stuck in the
ground with planted feet; spine_02 rides spine_01/03, re-baser's note). **walk `hand_u_r` 2.7 deg**: the club hand alone;
its limb group moves (shoulder 13, upper arm 3.7, forearm 3.4) and the club bounces in the movie. The walk animator kept
the grip fixed on purpose (aim near 180 deg flips the club roll). No limb group is frozen.

Small notes: walk has a 2-frame moment (t 0.29-0.33 s) where the lowest vertex is 4-5 cm up (heel off before the other
heel lands): 0.6 % of his height, not visible in the movie. The death still falls forward toward the hero (unchanged
fall, request 2 of assemble_cyclops.md stays open).

## Godot
- Import under work/.import_lock: exit 0, no errors.
- Loader probe (`work/assemble2_cyclops/probe.gd`, a copy of last time's): 0 errors, GLB not the stand-in, all 8 clips with
  the manifest lengths and loop modes, sweep impact 1.310, slam impact 1.500, all 5 sockets bone-attached, hand_ur socket
  on the club grip 0.000 m, club_grip2 0.000 m off the club axis. Slam impact club head (0.19, -0.04, 6.09), lowest club
  vertex 0.65 m in the ground: same as before (strike untouched). Shots: `work/assemble2_cyclops/shots/`, sheet probe_contact.jpg.
- Movie (gdwin, 30 fps, 17 s, chase camera behind a 1.9 m hero stand-in): idle 6 s, walk toward the hero at 2.6 m/s
  (rate 1.02), walk from the side, sweep, idle. `after.avi` / `before.avi` (old GLB through create_from_file), strips
  `strip_after.jpg` / `strip_before.jpg`. Looked: old = T pose with the club straight up in idle and walk; new = club on
  the shoulder, arms hang and swing, torso leans and bobs in the walk, sweep leaves and returns to the stance, no pops.
- Fight: `--start=cyclops --harness --bot=win --seed=1 --speed=3` headless -> victory at 32.8 s game time, 0 SCRIPT ERROR / ERROR.

## What the game code must know
- `idle` is 6.0 s (was 3.333). Nothing in cyclops.gd times off idle's length that I found; it loops.
- `walk` now has manifest `move_speed` 2.54: cyclops.gd uses it instead of Tuning `walk_move_speed` 2.43, so the walk
  plays at walk_speed 2.6 / 2.54 = 1.02x (was 1.07x). Tuning's fallback can stay (or be set to 2.54).
- Everything else unchanged: walk 1.4167 s with step 0.40 (left heel 1.125 = step + length/2), sweep impact 1.31,
  slam impact 1.5, stuck/pull_free/hurt/death lengths, sockets.

## Devlog
`docs/devlog/media_inbox/assemble2_cyclops/`: 01 idle + walk before/after (JPEG), 02 after strip (idle, walk, sweep),
03 side-by-side movie (mp4, 12.5 s). Image reads: 4.

---

# Animation fix after the naturalness review (animation fixer, 2026-11-23; owner at the Mac: headless Blender, Godot only headless or through gdwin, nothing shown or played)

Only writer of `art_src/chars/cyclops/` and `game/assets/characters/cyclops/` for this pass. Every overwritten key/pose/action/strip
has a `*.rest_v2.json` / `*.rest_v2.jpg` twin (the state the assembler merged above). Scratch: `work/animfix_cyclops2/`.
Generators (re-run them to rebuild a clip): `art_src/chars/cyclops/scripts/animfix2/build_{slam,pf,death,stuck,sweep,walk}.py`
(+ `fx.py`: resolve poses in headless Blender read-only, edit them as world rotation matrices, 2-bone leg/arm IK; `measure.py`:
numpy FK + skinning checks on a GLB). They read the `*.rest_v2.json` sources and write the live files.

## Each finding: checked, then fixed (numbers on the GLB, 24 fps)
| # | clip | check (before) | fix | after |
|---|---|---|---|---|
| 1 | slam | TRUE: club head 32-47 m/s at 0.08-0.17 s; at 0.25 forearm_u_l/r 2-3 deg, upper arms 21/38 deg from rest | k01_lift rewritten: club arm 35-40% of the way natural -> k02 (forearm stays bent), left elbow out-forward with the hand rising in front of the chest (a first version sent the elbow behind the neck: the triangle pass caught it), lower arms brace forward-down | club head 0-0.6 s: 1.8-13.7 m/s; no arm group near rest; no new body crossing; hand_ur/club_grip2 from 1.333 s and the impact club head (0.677, 0.393, 6.218) identical to 0.000 m |
| 6 | slam | TRUE, and worse than described: the right foot swings 1.2 m forward and back on the floor during the 4-frame chop (z -0.55 -> +0.68 -> -0.25 at 1.33-1.5 s), the left foot too (0.6 m); left glide 0-1.42 s path 1.27 m | feet planted by leg IK at every key 0.25-1.458 with root.loc = the old bake (so hips, spine, arms, club are unchanged); left weight-shift step 0.25-0.75 onto the impact spot (new key k025_step), right step 1.125-1.333 lifting 0.30 m (new keys k035_plant, k037_step) | left foot path 0.045 m (0-0.33 s) + 0.116 m (0.67-1.75 s), right 0.032 m then 0.000 m; strike untouched. The right foot is 1.7 cm off the floor at 0.5-0.75 s (leg fully stretched while the hips rise in k02) |
| 2 | pull_free | TRUE: last 3 frames hand_u_l 640-1338 deg/s, club head 83/70 m/s | k06/k07: left upper arm 40%/75% and lower arms 40%/75% toward natural, club arm 15%/55%; keys retimed k04 1.0->0.9583, k05 1.125->1.0833, k06 1.25->1.1667, k07 1.375->1.2917, new k075_settle 1.375 (~60%), k078_settle 1.4583 (~90%, the four hands staggered 0.8-1.0) | last 4 frames club head 22/15/6/2 m/s, hands <= 442 deg/s; length 1.5, no events |
| 3 | death | TRUE: mean arm deviation from rest 10 deg at 0.375-1.0 s, lower arms identical l/r | arms of g0375..g112 and k2_kneel re-posed (root, hips, legs, spine, fall path unchanged): left upper arm thrown up and back (elbow 41-55 deg) then falls limp, club arm drops and drags the club out (slerp natural -> the kneeling club pose), lower arms reach toward the knees, right one 2 frames later and ~15 deg higher. k2_kneel is included (left as it was it re-created the T pose at 1.25 s) | mean arm deviation 26-48 deg; lower hands at different heights (0.04-0.5 m apart); max 700 deg/s in the fling; no body crossing |
| 9 | death | TRUE: shoulder local speed 248, 248, 0, 305 deg/s at 3.25-3.42 | shoulder_u_l/r written absolute so that their rotation relative to spine_03 equals k3b_hold (2.6 s) on every later key (entries measured before root.rot) | 0 deg/s at 3.0-3.6 s |
| 10 | stuck | TRUE: club lowest -0.66 -> -0.54 m, hand_ur 0.20 m, feet 5-9 cm | keys every frame (read-backs of the re-based loop) with both feet, both club hands and the club pinned to k00_stuck by IK; the tug stays in knees/hips (dip 0.12 m), spine_01, head (0.19 m); spine_02/03 tug x0.6 and spine_03 hunches 0-6 deg forward where the left hand could not reach club_grip2 otherwise | club lowest -0.656 every frame, hand_ur 0.000 m, hand_ul on grip2 0.001 m, feet 0.002 m; weak point forearm_ur moves 0.20 m (radius 0.33); moving joints 22/29 (same frozen set as before: feet, toes, hips, spine_02, root) |
| 7 | sweep | TRUE: d_l x trunk up to 251 edges (0.21-0.46 s), 164 (1.83-2.0 s), also 0.75-0.96 s | upper_arm_d_l chain abducted in the spine_03 frame: 20/14/18 deg at k1/k2/k3, 22/30/20/12 at k7c/k8/k8b/k8d | 0 crossings for the lower arms |
| 8 | sweep | PARTLY WRONG: cyclops.gd plays sweep at impact/sweep_windup = 1.31/0.6 = 2.18x (enraged: windup >= ENRAGED_SWEEP_MIN), so (2.5-1.31)/2.18 = 0.55 s < 1.0 and `_recover_at` lands exactly on the clip end: the settle IS shown (the cut at 2.31 s only happens below 1.19x, i.e. windup >= 1.1 s). True: the return was crammed into 2.25-2.5 (~0.11 s in game) and the root zig-zagged 60 -> 0 -> 30 -> 0 deg (k8d read-back had root rot 0) | return starts at k8c (22%), k9 50%, k9b 85% toward natural (upper body only; hips/legs/feet unchanged); k8d lower body turned to the root yaw 42 and its upper body 12% toward natural | pose at 2.3125 is 0.63 m from idle f0 (was 1.47); root 446 deg/s max (was 807), hips 372; impact 1.31, strike unchanged |
| 4 | walk | TRUE: d_r x trunk 101-374 edges 0-0.58 s, d_l 12-159 at 0.83-1.21 | (see below) lower arms abducted 14 (left) / 19 (right) deg in the spine_03 frame | 0 crossings, every group |
| 5 | walk | TRUE on the GLB: stance-foot x range 0.20-0.24 m (hip sway 0.13 m) | stance foot x pinned by leg IK to its contact x, correction fading over 4 frames after lift-off | stance x range 0.006 (L) / 0.024 (L, 0-0.25 s) / 0.027 (R) m; planted-foot speed mean 2.49-2.50 m/s (lateral part removed): manifest move_speed 2.54 kept |
| 11 | walk | TRUE: hand_u_r 2.7-3.2 deg, lower arms mirror amplitudes | club dip 4 deg (forearm_u_r chain) + hand roll +-5 deg, 2.5 frames after each footfall; lower arms delayed 2 frames (relative to spine_03), right amplitude x0.82 | hand_u_r range 9.7 deg, forearm_u_r 7.7; walk moving joints 27 -> 28/29 (only `root`) |

Walk is now 34 per-frame keys `walk_n/poses_walk/f00..f33.json` = read-backs of the walk_n bake + the edits above (the animator's
k*.json keys and `keys_walk.rest_v2.json` stay as the source; `build_walk.py` regenerates). Stuck likewise 35 per-frame keys
(`poses_stuck/kf*.json` + k005_life/k01_tug/k015_life) from `keys_stuck.rest_v2.json`. k00_stuck (shared) never touched.

## Merge / export / import (exactly as above)
`tools/ak merge` (8 paths of clip_sources.json, ok, rig_hash fe38d0652353) -> `tools/ak export` (9.17 MB, 1 skin, 2 images,
export_fps 24, nothing retimed) -> `python3 work/assemble2_cyclops/finish_manifest.py`: 61 keys, 59 identical to the backup
manifest, the same 2 differences as before (idle 6.0, walk move_speed 2.54); socket_offsets asserted identical; lengths, loop
flags, events (sweep impact 1.31, slam impact 1.5, walk step 0.4) unchanged. Import under work/.import_lock: exit 0, 0 errors.
- Seams (max joint deviation): slam0/sweep0/sweepEnd/pull_freeEnd/death0 = idle f0, slamEnd/pull_free0/hurt0/hurtEnd = stuck f0,
  idle/walk/stuck loops: all 0.000 m. idle0 ~ walk0 0.447 m (was 0.41; cross-faded by loco_blend).
- `python3 tools/clip_motion.py cyclops`: death 29, hurt 22, idle 25, pull_free 26, slam 26, stuck 22, sweep 27, **walk 28** of 29.
- Triangle pass (lower/upper arm groups vs trunk, legs, head; every 1-6 frames): walk, idle, stuck, death 0; sweep lower arms 0.
- Loader probe (`work/animfix_cyclops2/probe.gd` through tools/godot_bg/gdwin, HOME = work/animfix_cyclops2/home): errors=0, GLB
  not the stand-in, 8 clips with the manifest lengths/loop modes, sweep impact 1.310, slam impact 1.500, 5 sockets bone-attached,
  hand_ur on the club grip 0.000 m, club_grip2 on the club axis 0.000 m; slam impact club head (0.19, -0.04, 6.09), lowest club
  vertex 0.65 m in the ground (same as before); stuck t=0.75 hand_ur = t=0 (pinned).
- Headless fight `--start=cyclops --harness --bot=win --seed=1 --speed=3`: victory at 32.84 s, 0 SCRIPT ERROR / ERROR.
- Looked: Blender strips (clip folders `strip_*.jpg`, re-rendered) and an in-game close-up sheet through gdwin
  (`work/animfix_cyclops2/close_sheet.jpg`: walk from behind, slam 0.125/0.25/0.375, pull_free 1.25/1.333, death 0.375/0.625,
  sweep 2.3125). Image reads: 9.

## Still not right (measured, not fixed: outside the findings or the acting limb the contract keeps)
- pull_free: moving k04-k06 earlier makes the over-swing faster: club head peaks 46-50 m/s at 1.04-1.13 s (old 24-42 there).
  The right foot still glides 1.25 m (path) over the clip (in-place ramp of the root 0.25 m + body heave; was 1.36).
  d_r x trunk 24-38 edges at 0.92-1.13 s (pre-existing).
- slam: arms cross the head/trunk around the original acting keys (u_l x head 12-26 edges 0.5-0.67 s, u_r x head 7-20 at
  0.63-0.83, u_l x head 38 at 1.333, lower arms x trunk 43/134 at 1.375): identical in the GLB before this pass.
- sweep: u_l x trunk 210 edges at 1.917, u_r x head 18-31 at 1.83-1.92 (pre-existing); the feet still slide while he turns
  (left foot x range 1.34 m at 1.46-1.83 s, pre-existing); the pivot at 2.0-2.2 is eased, not slow.
- hurt: u_l x trunk 12-14 edges (pre-existing). walk: heel-off float 4-5 cm at 0.29-0.33 / 1.0-1.04 s (pre-existing).
- No chase-camera movie this round (close-up stills only).

---

# Clip fix 2 (clip fixer, 2026-11-23; owner at the Mac: Blender headless, Godot only headless or through gdwin, HOME = work/clipfix2_cyclops/home)

Only writer of `art_src/chars/cyclops/` and `game/assets/characters/cyclops/` for this pass. Scratch: `work/clipfix2_cyclops/`
(before.glb / before_clips.json = the pair this pass started from). Every overwritten key/pose/action/strip has a `*.rest_v3.*` twin.
Only `pull_free` and `idle` changed in the GLB (max joint difference before -> after: death, hurt, slam, stuck, sweep, walk 0.0000 m).

## 1. pull_free: heave re-timed, feet planted (generator `scripts/animfix2/build_pf2.py`)
- Method: the animfix2 bake (`action_pull_free.rest_v3.json`) is read back at TIME-WARPED clip times (35 per-frame keys
  `poses_pull_free/pf2_f01..f35.json`; first key k00_stuck, last key k08_natural, so both seams stay exact). From 0.20 s the
  club head follows a target speed K x envelope (eases in over 0.08 s from rate 1, eases out over the last 0.30 s), clamped to
  0.25-2.0x of the source rate; K = 24.4 m/s found by bisection so the length stays 1.5 s. The club path, the hand stagger and
  the body coordination are animfix2's, only the timing changed. Club head = hand_u_r head + R(hand_u_r) x (0.0844, -0.875, 5.0616)
  m (calibrated on the GLB, 0.4 mm spread).
- Feet: leg IK on every frame. Left foot keeps its own step (frames 9-12, 0.375-0.5 s), plants pinned; right foot: one real step
  (frames 14-19, 0.58-0.79 s, lift 0.16 m, 0.37 m to the stance) that starts 1 frame after the left foot lands (never both feet up).
  The bake removes the k00_stuck -> k08_natural root drift (x 0 -> 0.25 m) from every key, so the generator adds it back
  (a first build without it slid both feet 0.24 m).
- Decision: "spread the heave over 0.9-1.3 s" read as the heave LASTING about that long: the club path from leaving the crack to
  the shoulder is ~25 m, which cannot fit in a 0.4 s window at <= 30 m/s. Now the club moves > 8 m/s from 0.25 to 1.42 s (1.17 s).

| measure (GLB, 24 fps unless noted) | before | after |
|---|---|---|
| club head peak, per frame | 50.3 m/s at 1.167 s (7 frames > 30) | **27.0** m/s at 0.917 s (0 frames > 30) |
| club head peak, 96 Hz | 62.6 m/s | 29.2 m/s |
| on screen at 1.875x | ~94 m/s | ~51 m/s |
| hand_u_r / forearm_u_r / upper_arm_u_r max world ang. speed 0.75-1.5 s | 941 / 1014 / 1025 deg/s | 557 / 600 / 606 deg/s |
| last 4 frames club head | 15.2 / 5.9 / 1.8 (1.42-1.5) | 13.3 / 8.9 / 5.0 / 2.1 (eased) |
| right foot sole glide while on the floor | 1.248 m path (0-1.5 s, never lifted) | 0.001 m (0-0.54) + 0.001 m (0.83-1.5), one step between |
| left foot glide on the floor | 0.299 + 0.432 m | 0.000 + 0.015 m |
| lowest body vertex | -0.042..0.016 m | -0.000..0.016 m |
| moving joints (clip_motion) | 26/29 | 26/29 |
Length 1.5, no events, start = stuck f0, end = idle f0 (0.000 m). Strip: `clips/slam/strip_pull_free.jpg` (+ .mp4), looked:
even progression, no pops, right step visible in the side view.

## 2. Walk generator keeps the footfalls
`build_walk.py` now sets `EVENTS = {step_r: 0.4167, step_l: 1.125}` (= FALLS frames 10 / 27, asserted) and the integrator's
`note_integrate2` on the keys it writes. Re-run (`--write`): the 34 pose files are byte-identical, `keys_walk.json` differs only in
notes, re-baked `action_walk.json` identical in bones/poses/events (integrator note restored). Exported manifest walk events:
`{"step_r": 0.4167, "step_l": 1.125}` (cyclops.gd thuds on every `step*` event). `ak export` does not write `events_note`: it is
carried over from the previous manifest after `finish_manifest.py`. Manifest vs the one before this pass: **0 keys differ**.

## 3. Idle from the start camera (generator `scripts/animfix2/gen_idle2.py`, copy of work/anim2/cyclops_idle_n/gen.py)
Looked first: game shots every 0.5 s through gdwin (`--start=cyclops --seed=11 --shot-every=0.5 --quit-after=8.6`): the idle
plays only 0-2.4 s (fight_start -> walk at 2.40 s), the giant ~20-24 m away (~5 cm per pixel); before, the four idle shots looked
identical except a slight club tilt. Raised amplitudes (factors on the old layered deltas, all still 0 at t = 0 and 6 s):
breath (spine/neck rx) x2, shoulders rise x3.5, club bob (upper arm/forearm/hand of the club arm) x3, upper left arm x2, lower
arms x2, weight shift (pelvis 0.12 -> 0.168 m, hips/spine tilt) x1.4, head turns x1.5. Legs re-solved per key (ankles <= 4.5 mm).
k00 = natural_pose.json untouched; length 6.0, loop, seam 0.000 m.

| idle (GLB) | before | after |
|---|---|---|
| club head range x / y / z | 0.80 / 0.39 / 0.38 m | 2.10 / 1.23 / 0.94 m |
| shoulders (upper_arm_u_l / _r heads) y range | 0.12 / 0.16 m | 0.40 / 0.45 m |
| head range x / y / z | 0.21 / 0.035 / 0.13 m | 0.30 / 0.063 / 0.25 m |
| hips sway | 0.12 m | 0.17 m |
| upper left hand / lower hands max displacement | 0.32 / 0.23 / 0.26 m | 0.60 / 0.43 / 0.48 m |
| largest point move per 0.5 s | 0.22-0.51 m | 0.69-1.48 m |
| game crop around the giant, pixels changed > 30 per 0.5 s (shots 0-3) | 2309 / 2643 / 3089 | 3365 / 3874 / 4385 |
Sheet: `work/clipfix2_cyclops/crop_before_after.jpg` (top before, bottom after): club tilts left/upright/right, head turns,
the body shifts. Blender strip `work/clipfix2_cyclops/strip_idle_after.jpg`: club stays on the shoulder, no contact with the head.

## Merge / export / import / checks (exactly as above)
`tools/ak merge` with the 8 paths of clip_sources.json in its order (ok, rig_hash fe38d0652353) -> `tools/ak export` (9.17 MB,
1 skin, 2 images, export_fps 24, nothing retimed) -> `python3 work/assemble2_cyclops/finish_manifest.py` (socket_offsets asserted
identical) -> walk `events_note` carried over. Import under work/.import_lock: exit 0, 0 errors.
- Seams (max joint dev): slam0, sweep0/End, pull_freeEnd, death0 = idle f0; slamEnd, pull_free0, hurt0/End = stuck f0;
  idle/walk/stuck loops: all 0.000 m.
- `tools/clip_motion.py cyclops`: death 29, hurt 22, idle 25, pull_free 26, slam 26, stuck 22, sweep 27, walk 28 (unchanged).
- Loader probe (`work/clipfix2_cyclops/probe.gd` = animfix2's, gdwin): errors=0, not the stand-in, 8 clips with manifest lengths
  and loop modes, sweep impact 1.310, slam impact 1.500, 5 sockets bone-attached, hand_ur on the grip 0.000 m, club_grip2 on the
  axis 0.000 m; slam impact club head (0.19, -0.04, 6.09), club 0.65 m in the ground (identical to before).
- Headless fight `--start=cyclops --harness --bot=win --seed=1 --speed=3`: victory at 32.78 s (was 32.84), stuck -> pull_free twice,
  0 SCRIPT ERROR / Parse Error.
- Not done: no chase-camera movie of pull_free in the game (Blender strip only); clip_showcase.gd not run.

## What the game code must know
Nothing changes for the code: same clip names, lengths (pull_free 1.5, idle 6.0), loop flags, events (walk step_r 0.4167 /
step_l 1.125, sweep impact 1.31, slam impact 1.5), sockets and socket_offsets. pull_free still plays at 1.875x (pull_free_time 0.8):
the club now peaks ~51 m/s on screen around 0.49 s into the 0.8 s, and the right foot steps at 0.31-0.42 s of it.
