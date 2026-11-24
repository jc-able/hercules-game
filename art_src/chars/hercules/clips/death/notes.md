# hercules / death video: animator notes (2026-11-22, owner away: decisions noted)

| clip | video window | keys | IoU per key (front/side, mean) | length | events | loop |
|---|---|---|---|---|---|---|
| death | 1.0-4.75 s (clip t = video t - 1.0) | 15 (10 hand-posed + 5 grounding keys read back from the bake) | k0 idle 0.34/0.37 (on purpose, see below) · k0b recoil step 0.66/0.57 (0.61) · k1 struck 0.82/0.76 (0.79) · k2 stagger 0.69/0.60 (0.64) · k3 kneel 0.72/0.63 (0.67) · k4 slumped 0.43/0.54 (0.48) · k5 sits back 0.42/0.65 (0.54) · k6 back hits floor 0.35/0.64 (0.50) · k7 rolling flat 0.37/0.55 (0.46) · k8 lying 0.56/0.68 (0.62); strip mean 0.55 (12 samples), 0.57 per frame | 3.75 s @24 fps | none (SPEC §8 names no death event) | no |

Keys (clip time / video time): k0 0.0/1.0 · k0b 0.25/1.25 · k1 0.5/1.5 · k2 1.25/2.25 · k2a/k2b/k2c 1.375/1.5/1.625 (grounding) ·
k3 1.75/2.75 · k4 2.625/3.625 · k5 2.875/3.875 · k5b 2.958 (grounding) · k6 3.0/4.0 · k6b 3.083 (grounding) · k7_h 3.25/4.25 ·
k8_h 3.75/4.75 (4.75-10 s of the video is the same still pose; the game holds the last frame).
Ground check over the whole bake: lowest vertex between -1.7 and +1.9 cm on every strip sample (read-back checks: max -3 cm at 3.12 s,
+5 cm while the body is in the air at 2.9-3.0 s).

## What the video shows
0-1 s he stands in the sheet A-pose (not a combat stance). 1.25-1.5 s struck in the chest: head thrown back, chest arched, arms
flung out. 2.25 s staggers with bent knees, 2.75 s on both knees. 3.0-3.25 s the shield slides off his arm onto the floor and he lets go
of the sword. 3.625 s slumped on his knees. 3.875-4.0 s he sits back and topples to his right and backwards, one arm flung up.
4.25-4.75 s rolls flat; 4.75-10 s lies still. Calibration IoU 0.95 / 0.95, no camera drift.

## Decisions (owner away)
- Start = idle k0 (same pose file content as `idle/poses_idle/k0.json`, framing removed) so the game can blend idle/hit -> death.
  The video's first second is a plain A-pose, so k0 scores low against it on purpose. A recoil step (k0b) lifts the front (left)
  foot and brings it back beside the right one so the feet do not slide while going from the wide stance to the video's narrow one.
- The lying pose is inconsistent in the video: BOTH panels draw him full length (front: head to screen-left; side: head to
  screen-left). One 3D body cannot do both. Tested: lying back along Y (front 0.41 / side 0.55), diagonal 45 deg (0.37/0.50),
  across X with the head to his right (0.44/0.61): chose across X (on his back, head at -X). It also matches the front view of the
  topple (he falls to his right). The side view is therefore foreshortened in k7/k8 (scores ~0.55-0.68 only because the body
  overlaps the long silhouette).
- Topple (k5-k8) is done by turning the `hips` bone (absolute view-axis angles) with the legs given in world angles, so the knees
  stay on the floor. A first version turned the whole body with `root.rot` about the hips: the folded legs swung up and the body
  hovered 0.6 m (IoU 0.05-0.35). k7/k8 were authored with `root.rot` and then converted to the same hips form (read back from
  the bake, hips = the old root.rot): mixing the two forms made the hips swing 0.5-1 m sideways between keys.
- Clip length kept at the video's natural 3.75 s; the game re-times (`ak retime` if a shorter death is wanted).
- Hips land ~0.27 m further to screen-left in the video's front view than ours (he falls sideways); kept as `view_offset` only:
  the clip plays in place.

## What does not match and why
- Sword and shield cannot be dropped: both are bone-parented in the blend (sword -> hand_r, shield -> forearm_l). The video drops
  them at 3.0-3.25 s (front IoU of k4 0.43 is mostly the shield lying on the floor in the video vs on his arm in ours). Ours keeps
  them: the shield arm is laid on the floor with the forearm twisted so the shield lies flat (forearm_l twist -60 in k8), the sword
  arm is twisted so the blade lies flat beside him (forearm_r twist -90). During the arm fling (clip 3.0-3.1 s) the shield is up in
  the air for ~3 frames. Request for the game in `docs/notes/anim_hercules_death.md` (detach props at ~2.1 s clip time).
- 0.8-1.2 s: our sword points forward almost level in the side view; the video's points forward-down (~30 deg). Minor.
- The fall is a little less sideways-sliding than the video and the side view of the lying pose is foreshortened (see decision).
- Strip check: no limb through the body, no flipped twists, no pops; the in-betweens of the knee drop and the topple needed the
  5 grounding keys (without them knees went 21 cm and the body 17 cm through the floor).

Files: `keys_death.json`, `poses_death/*.json`, `action_death.json`, `strip_death.jpg`; scratch, generators (`tools/gen2.py`,
`tools/opt.py`: aim-aware coordinate-descent on IoU) and `strip_death.mp4` in `work/anim/hercules_death/`.

## Review fix 2 (animation fixer, 2026-11-22; owner away)
- death: sword kept above the floor (k4b_sword 2.792; hand_r aimed on k5, k5a-k6f, k8_h; tip min +0.064 m, was -0.26); topple 2.875-3.208 = re-grounded read-backs every 2 frames, linear (k5b/k6/k6b dropped, files kept); events.drop_props 2.1. Lying pose: shield rim ~5 cm under the floor (not fixed). See docs/notes/anim_hercules_review_fix.md for numbers; scripts in work/anim/hercules_review_fix/.

animfix_hercules 2026-11-23: first 0.5 s re-based (work/animfix_hercules/edits.fix_death): frame 0 = natural_pose.json v2 (was the old lunge: hips 23 cm, toe_r 55 cm off); 0.25 s (DEATH_CLIP_FROM) = natural legs + 40 % of the recoil in the upper body; 0.25-0.42 s the left foot steps (7 cm lift) toward k1 while the right stays planted, 0.375-0.5 s the right settles (3 cm). From 0.5 s on (k1, the fall, drop_props 2.1, length 3.75) identical. Original files: action_death.rest_v1.json, keys_death.rest_v1.json.
