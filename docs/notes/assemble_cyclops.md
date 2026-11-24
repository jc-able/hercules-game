# Cyclops assembly (assembler, 2026-11-22; owner away, decisions noted)

Delivered: `art_src/chars/cyclops/cyclops.blend` (8 actions), `game/assets/characters/cyclops/cyclops.glb` (9.12 MB,
1 skin / 29 joints, 2 embedded PNGs: body 5.5 MB + club 1.3 MB, body + club meshes) and `cyclops_clips.json`.
Probe: `work/assemble_cyclops/probe.gd` (CharacterVisual.create("cyclops"), 0 errors), shots in `work/assemble_cyclops/shots/`.

## Clips (SPEC §8: idle, walk, sweep, slam, stuck, pull_free, hurt, death) - all 8 present, none missing
| clip | length s | loop | events |
|---|---|---|---|
| idle | 3.3333 | yes | - |
| walk | 3.9167 | yes | - |
| sweep | 2.5 | no | impact 1.31 |
| slam | 1.75 | no | impact 1.5 |
| stuck | 1.5 | yes | - |
| pull_free | 1.75 | no | - |
| hurt | 2.25 | no | - |
| death | 4.5 | no | - (root_motion: true, see below) |

Manifest extras written by `work/assemble_cyclops/finish_manifest.py` (re-run after every `ak export`):
`offset_space: "godot"` (rig.json offsets are glTF-joint-frame / Godot YXZ; verified: socket hand_ur sits exactly on the
GLB club grip, club_grip2 exactly 0.7 m up the club axis), sockets + socket_offsets from rig.json (hand_ur, hand_ul,
forearm_ur, head, club_grip2), `size` {height 8.0, width_arms 8.03, depth 2.39, club_length 5.5, club_top_rest 11.45}.
The GLB now carries the club mesh (node `club` under joint hand_u_r), so cyclops.gd skips its own club prop (checked).

## Bug found and worked around: `ak merge` with several files corrupts frame 0
One `ak merge` call with all 8 files gave every clip after the first a wrong root height on its FIRST key (stuck +0.155
instead of -0.159 m, walk +0.307 instead of +0.004, sweep -0.312 instead of 0, slam -0.168, pull_free +0.022): a 0.3 m
pop at every loop seam and a floating giant at the start of stuck / pull_free. Cause: in `cmd_merge`
(tools/animkit/ak_blender.py) `bake_data()` runs while the previous file's action is still on the armature (clear_anim
comes after the bake), so the first key's `root.ground` is measured on a stale pose. Workaround: one `ak merge` call per
file (8 calls, 2.5 s each); afterwards slam end = stuck start = pull_free start (hips 2.79 m), walk/stuck seams exact.
**Request for animkit:** call `clear_anim(arm)` before `bake_data()` in cmd_merge (and add a multi-file merge test).

## Requests for the art track (animation re-keys; nothing here was faked)
1. **stuck (and slam impact): the club head is NOT in the ground.** Measured in Godot: lowest club vertex 0.34-0.40 m
   ABOVE the floor in stuck (0.22 m at the slam impact), club head at boss-local (+3.1, 1.0, 6.3): 6.3 m ahead and 3.1 m
   to his LEFT, not ~5 m straight ahead. The weak-point forearm (socket forearm_ur) is at 2.50-2.61 m: at the top of the
   wanted 1-2.5 m band (game clamps it, `forearm_clamped raw_y=2.53 mode=club_line`). Wanted: club head ~0.3 m into the
   earth ~5 m ahead near his centre line, forearm_u_r at ~1.5-2 m (deeper crouch / club pitched ~10 deg further down).
2. **death falls forward and must change.** He lands on his front toward the hero: head ends 4.3 m in front of his feet
   (top of the head ~5.4 m), right where the hero stands for the last forearm hit (~2-3 m in front of him), so the 8 m body
   falls through the hero and toward the chase camera. Tuning.CHARS cyclops says `fall: "back"`. Wanted: a backward (or
   straight-down) death, keep root motion. The current clip stays in the GLB until then.
3. **sweep impact is too high:** at the impact event the club head passes 3.9-4.5 m above the ground, 7.4 m ahead; a 1.9 m
   hero it "hits" is well under it. Wanted: club at ~1-2 m height at impact (SPEC: "club drawn back low").
4. walk is OK: the two steps alternate correctly (right foot lifts 0.16-0.98 s, left 2.12-2.94 s, exact mirror, no
   double-lift), feet planted, loop seam exact. Its stance foot travels only ~0.95 m/s at speed 1 (step ~1.86 m).

## Requests for the cyclops module (game/scripts/bosses/cyclops.gd)
- Play `walk` at about 2.7x while walking at 2.6 m/s (feet slide otherwise; step thud then every ~0.72 s, footfalls at
  clip 0.98 s and 2.94 s - no `step` event in the keys, so none was written).
- With the real model the crack/chunks sit at the slam centre but the club head lands ~3.2 m away (see art request 1):
  until the clip is re-keyed, put the crack at the club head (club node `club`, head = club.global_transform * (0, 5.05, 0)).
- Fight check with the real GLB: `--start=cyclops --harness --bot=win --seed=1 --speed=3` -> victory, 0 SCRIPT ERROR /
  ERROR / WARNING, but the bot lands only 1 hit per stuck window (fight 62 s vs 31-37 s with the stand-in).
- death: the club cannot leave the hand inside the GLB (see anim_cyclops_death.md); detach node `club` if wanted.
- death has root motion (hips +0.6 m, head +4 m): play it without moving the boss body.

## Request for core (CharacterVisual)
- `model_top()` counts the club mesh now that it is in the GLB: 11.45 m instead of the body's 8.0 m (the doc comment says
  props are not counted). If the lock camera should frame the body, skip meshes under a BoneAttachment3D in
  `_measure_top()` (or read manifest `size.height`). Nothing else needed: create/has_clip/clip_length/event_time/socket
  all work on the real GLB.
