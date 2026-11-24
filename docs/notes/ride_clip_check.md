# Ride clip independent check (ride_clip_check agent, 2026-11-22)

The owner was away, so this agent made every decision below and notes it here. Scratch files are in `work/ride_clip_check/`:
check_render.py (own Blender check + renders), beat.py / beat2.py (own video measurement), gltf_offset.py + pair_test.glb
(rider offset in glTF space), check.json, sheet_side.jpg / sheet_q34.jpg / sheet_q34r.jpg, action_rebake.json.
A copy `art_src/chars/ride/ride_check2.blend` was used, never saved, and has been deleted.
**Nothing in `art_src/chars/ride/clips/ride/` was changed: no mechanical fault was found.**

## Verified
- **Bake:** re-baking `keys_ride.json` on hercules.blend gives the same result as `action_ride.json`: max quaternion difference 0, same rig_hash cab1a3a4339f.
  `ak pose --from-action` read-back at t 0.375 / 0.75 gives the key spine angles exactly. `ak strip` runs fine.
  The bake's "floating 0.19 m" notes are expected for a seated rider.
- **Loop seam:** frame 0 and frame 36 match exactly (rotation difference 0.0). The per-frame change across the seam
  (0.0032 / 0.0038) is the same as in the rest of the loop (max 0.0098): no velocity jump.
- **Root:** the root has no loc keys and its rotation is identity. The hips stay at (0, 0.20, 0.247) from the saddle head at every frame.
- **Seated rider (12 frames, the rider plus a Pegasus wing beat and an 8.3 cm bob, wings swept 10 deg forward):**
  - 0 hits between the wings and his body, skirt, sword or shield.
  - The sword touches only his own hand and fingers.
  - The left hand stays 4.2-4.8 cm from the mane. The sword hand stays about 45 cm from it, as the base pose intends.
  - Renders from the side and two three-quarter views show him on the back in all 6 frames, with nothing through the horse.
  - Contacts left over from the base pose are not made worse by the clip:
    - inner thighs into the upper flank: 309-408 triangle pairs, up to 13.5 cm deep, hidden;
    - skirt into the back: 335-444;
    - shins on the barrel: shin_l 0-42 (0 while the heels are drawn back);
    - shield rim in the mane hair: 268-296.
- **Unswept wings** (the plain make_poses family): 0 hits near the top of the stroke, rising to 942 at the bottom. This
  confirms the animator's finding that the Pegasus fly clip needs the forward sweep.
- **Beat:** wing-top plateaus in the front panel are at 0.44, 1.94, 3.35, 4.77, 6.35, 7.77 and 9.35 s. The mean is 1.486 s and
  the line fit is 1.479 s, which matches the 1.48 in ride_game.json.
- **ride_game.json vs ride.json:** loc, rot, quat, matrix and the armature-axes form are identical.
  The Godot form `Transform3D(Basis.IDENTITY, Vector3(0.0041, -0.8365, -0.1701))` was checked by exporting the pair to glTF
  (+Y up, Pegasus at rest). The hercules_rig node in the saddle joint frame is exactly that: identity basis, translation
  (0.0041, -0.8365, -0.1701). This is checked at the glTF level only; it has not been run in Godot.

## Small corrections (reported, not changed)
- The video holds only 12 unique frames per second: every frame is doubled.
- The local period inside the clip window (video 1-4 s) is 34 frames (1.417 s), not 36. The 36-frame period holds from
  about 3 s on. ride_anim.md says "the first 3 s repeat exactly every 36 frames"; that is not right. This does not
  matter for the rider, who is rigid in the video and is time-scaled by the game.
- The wing-bottom phase in the video is around clip t 0.75-0.95, not exactly 0.75. This is irrelevant at ±1.5 deg of rider motion.
- ride_anim.md says "head stays absolute, so his gaze holds". The head key itself changes by ∓1 deg, so the gaze moves by 1 deg. This is cosmetic.
- Compared with the video: the video's sword points back and down, while ours is horizontal and back. The video sits him slightly
  more upright. Both come from the base pose (ride.json), not from the clip.
