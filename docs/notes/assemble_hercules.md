# Assembler: hercules (2026-11-22; the owner was away, so the decisions below are noted for the lead)

Outputs: `game/assets/characters/hercules/hercules.glb` (7.38 MB, 13 clips, 1 skin, 29 joints, albedo embedded) and
`hercules_clips.json`. Scratch, scripts and logs are in `work/assemble_hercules/`. `hercules.blend` now holds the 13 actions.
Backup from before the merge: `work/assemble_hercules/hercules.blend.before_merge`.

## Rebuild (in this order)
1. `work/assemble_hercules/merge_each.sh` (one `ak merge` per clip: see bug 1)
2. `tools/ak export art_src/chars/hercules/hercules.blend --out game/assets/characters/hercules/hercules.glb --clips-json game/assets/characters/hercules/hercules_clips.json`
3. `python3 work/assemble_hercules/strip_props.py game/assets/characters/hercules/hercules.glb` (see bug 2)
4. `python3 work/assemble_hercules/measure.py game/assets/characters/hercules/hercules.glb > work/assemble_hercules/measure.json`
5. `python3 work/assemble_hercules/finalize_manifest.py` (adds size, move_speed, offset_space, socket_props; checks the GLB)
6. Import under the lock, then the probe: `Godot --path game --resolution 1280x720 --script ../work/assemble_hercules/probe.gd -- --harness`

## Clips
All 13 SPEC §8 clips are present: idle, run, strafe_l, strafe_r, walk_back, roll, attack_1, attack_2, block_start,
block_idle, hit, death, ride. None are missing and none were invented.
- **strafe_r (decision).** I kept the fixer's `action_strafe_r.json`. It is NOT re-made with a plain `ak mirror --keys`.
  A plain mirror moves the sword to the left hand. The fixer's version mirrors the legs, hips and root, and keeps the
  strafe_l upper body. I checked it against a fresh `ak mirror --keys keys_strafe_l.json`: the legs and root of every key
  are identical (0 differences), so it matches the current strafe_l.
- `ride` = `art_src/chars/ride/clips/ride/action_ride.json`. The rider sits at rest hip height, so his feet are 0.27 m
  above y = 0. Place him with `art_src/chars/ride/ride_game.json`.

## Bugs found and worked around (requests for animkit)
1. **`ak merge` with several files grounds clip N while the action of clip N-1 is still on the armature.** In
   `cmd_merge`, `bake_data` runs before `clear_anim`. As a result, `root.ground` on the first key reads a stale mesh.
   With the one-call merge, the frame-0 root height was wrong in 4 loops, and each one popped at the loop seam:
   | clip | frame 0 root z | correct |
   |---|---|---|
   | run | 0.000 | -0.037 |
   | strafe_l | 0.000 | -0.213 |
   | strafe_r | -0.106 | -0.212 |
   | walk_back | -0.052 | -0.194 |

   Fix in `ak_blender.cmd_merge`: call `clear_anim(arm)` BEFORE `bake_data(rig, data['spec'])`. Also add a test that
   merges 2 grounded loops in one call and compares them with `ak bake`. Until then, merge one file per call.
2. **`ak export` also exports the bone-parented props** (prop_sword on hand_r, prop_shield on forearm_l). `player.gd`
   attaches `res://assets/props/sword.glb` / `shield.glb` to the sockets, so the props would show twice.
   `strip_props.py` removes the two prop nodes and everything only they used, then compacts the buffer (10.1 -> 7.4 MB).
   Request: `ak export --no-props` (skip unskinned meshes parented to a bone). Cyclops (club) has the same issue.

## Manifest (`hercules_clips.json`)
- `clips`: length, loop and events, taken from the keys files through `ak export`.
  - attack_1: active 0.458-0.708 of 1.25 s.
  - attack_2: active 0.417-0.625 of 1.5 s.
  - Other clips: no events.
- `sockets` + `socket_offsets` come from rig.json (hand_r, forearm_l, head, chest -> spine_02).
  `"offset_space": "blender"` is now explicit. `socket_props` comes from rig.json.
- `size`: height 1.9 (rig.json), measured 1.900 m, width 1.286 (A-pose arms), depth 0.407, rest bounds. Props are not counted.
- `move_speed` (planted-foot ground speed at playback speed 1.0, measured from the GLB by forward kinematics) and
  `move_dir`:
  | clip | move_speed (m/s) | direction |
  |---|---|---|
  | run | 3.64 | +Z |
  | strafe_l | 0.72 | +X = his left |
  | strafe_r | 0.72 | -X |
  | walk_back | 1.20 | -Z |

## Probe result (through CharacterVisual.create("hercules"), Godot 4.7.2)
PASS. The real model loads (is_standin false, model_top 1.900). For every clip: has_clip is true, clip_length equals the
manifest and the Animation, and the loop modes are right. The 4 sockets sit on BoneAttachment3D (hand_r, forearm_l, head,
spine_02). The toes point +Z, so he faces +Z. Lowest toe joint is 0.046 m.
Screenshots are in `work/assemble_hercules/shots/` (01-04 + zoom.jpg). They show: upright, textured toon look with the
ink outline, sword in the right hand, lion shield on the left forearm with its face out (devlog shot), no exploded mesh.
No CharacterVisual change is needed.

## For core (game code; I did not change it)
- **attack_2 hit window is short.** At 0.65 s (x2.31) the window is 0.181-0.271 s of game time (90 ms; SPEC 0.22-0.38).
  attack_1 at 0.55 s gives 0.202-0.312 (SPEC 0.18-0.32), which is fine. A wider attack_2 window needs the split retime
  the attack fixer proposed (recovery keys compressed more than the swing). That changes the animation, so it is the
  lead's call.
- **hit** is 2.167 s long, but the flinch lasts 0.4 s. At speed 1, only the first 0.4 s shows before the next clip takes
  over. Either accept that, or play it at about 2x and blend out.
- **Locomotion speed scale:** `speed_scale = ground_speed / clips[c].move_speed`.
  - Run at 6 m/s: 1.65x for no skating. The animator suggests ~1.3x as a compromise.
  - At the locked-on 4.6 m/s, strafe would need 6.4x and walk_back 3.8x. Cap the scale (strafe about 2.5x, walk_back
    about 2x) and/or lower the sideways and back speeds, as the strafe and walk_back fixers recommend.
- The `strafe_r -> strafe_l` fallback in player.gd no longer fires.
- **death:** the sword and shield are separate props now, so the game can drop them at clip time ~2.1 s (animator
  suggestion; there is no event for it).
