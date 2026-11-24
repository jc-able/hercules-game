# Medusa assembly (assembler, 2026-11-22, owner away)

Output: `game/assets/characters/medusa/medusa.glb` (8.31 MB, texture embedded; Godot import also extracts
`medusa_medusa_albedo.png`, 4.9 MB) + `medusa_clips.json`. Blend: `art_src/chars/medusa/medusa.blend` (9 actions merged, rig_hash df3b7a8d3df2).
Scratch: `work/assemble_medusa/` (merge/export/import logs, `probe.gd`, `sample.gd`, shots, fight logs).

## Clips (SPEC §8: idle, slither, gaze, stun_start, stunned, rise, tail_swipe, hurt, death) — all 9 present, none missing
| clip | length s | loop | events | source |
|---|---|---|---|---|
| idle | 3.0 | yes | - | clips/idle |
| slither | 2.0 | yes | - | clips/slither |
| gaze | 4.25 | no | fire_start 2.0, fire_end 3.25 | clips/gaze |
| stun_start | 1.625 | no | - | clips/stunned |
| stunned | 3.0 | yes | - | clips/stunned |
| rise | 2.5 | no | - | clips/stunned |
| tail_swipe | 2.75 | no | impact 1.0 | clips/tail_swipe |
| hurt | 3.25 | no | - | clips/hurt |
| death | 3.5 | no | - | clips/death |
All at 24 fps, no retiming. `ak merge` re-baked all 9 on the current rig (no warnings).

## Manifest
sockets head/neck/tail_tip (+ extra `eyes`) and socket_offsets copied from rig.json by `ak export`; added by me:
`"size"` (height 6.5, width_x 3.734, length_z 9.89, tail_on_ground 9.9, tris 70000, bones 35) and `"offset_space": "blender"`
(the default, written out). Note: `ak export` does not write `size`; re-add it after any re-export (or animkit could copy
rig.json `height`/`size_m`).

## Checks
- pygltflib: 9 animations, lengths = manifest exactly, 1 skin (35 joints), 1 PNG image embedded (bufferView), 1 material,
  44,589 verts, bounds x +-1.87, y 0..6.5, z -8.44..+1.45 (faces +Z, tail toward -Z).
- `Godot --headless --path game --import` under `work/.import_lock`: exit 0.
- `work/assemble_medusa/probe.gd` (windowed, own SubViewport 1280x720): CharacterVisual.create("medusa") -> real GLB,
  9/9 has_clip + clip_length = manifest = AnimationPlayer length, loop modes right (idle/slither/stunned loop), 3/3 events,
  4/4 sockets on BoneAttachment3D. Upright, faces +Z, 6.5 m (model_top 6.5), toon + ink outline, texture on, no exploded mesh.
  No props for Medusa (none in SPEC).
- Real fight with the GLB from game/assets: `--start=medusa --harness --bot=win --speed=3` -> victory at 24.45 s, 3 reflects,
  6 neck cuts, no SCRIPT ERROR. Windowed `--shots` run looks right (stalk, gaze windup with fan, stunned bow).

## Findings for other roles (not fixed: not my files)
1. **stunned head distance (medusa module / animator):** the stunned clip alone puts the neck at (0, 0.76, 2.79) m and the
   head at (-0.1, 0.47, 3.13) — head on the floor but ~3 m in front of her origin, not the ~4.6 m the module notes expected
   (the animator's 2.4 m `back` slide). In the game the module's LeanMod still reports `lean_deg` 92-95 and `neck_y` 2.14-2.20
   during `stunned` (log `work/assemble_medusa/fight_win.log`), i.e. it seems to act on top of a clip that is already lower
   than its 2.1 m target; in the windowed shots she is bowed with the head around 2 m, not lying on the floor. Cuts land, so
   the fight works; whoever owns medusa.gd should check that LeanMod adds nothing when the clip's neck is already below 2.1 m.
2. **tail_swipe impact (animator / lead):** at the keyed impact 1.0 s the tail tip is still ~3 m up (tail_08..14 max height:
   0.75 s 5.95 m, 1.0 s 3.11 m, 1.125 s 1.55 m, 1.25 s 0.35 m = flat on the floor, reach 8.44 m). Kept 1.0 as keyed
   (manifest carries the keys file events). Suggest impact ~1.15-1.2 s if the damage should land when the tail hits the floor.
   The swipe is an overhead whip ending at her front-right (~225 deg), not a flat 360 sweep (animator note).
3. stunned loop seam: the lowest bone head dips 8 cm below the floor at loop t = 0 (and the floor tail rides 0.1-0.4 m up in
   the breathing loop); cosmetic.
4. The non-deforming `root` bone sits at y -2.6 m during stunned (lean recipe root.loc); harmless (no weights), but anything
   that reads the root bone for placement should use pelvis instead.
5. Hero is still the grey-box stand-in in the arena (no hercules GLB in game/assets yet).
No request for core's CharacterVisual: everything loaded and mapped through the stock loader.
