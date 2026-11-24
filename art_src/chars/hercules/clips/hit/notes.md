# hercules / hit video: animator notes (2026-11-22; owner away, decisions noted)

| clip | video window | keys | IoU per key (front/side) | length | events | loop |
|---|---|---|---|---|---|---|
| hit | take 1, 0.667-2.833 s (t0 0.667) | 9 (8 poses, k0 used at start and end) | k0_ready 0.93/0.95 (end copy 0.86/0.85), k1_impact 0.77/0.83, k2_peak 0.81/0.81, k2b_arch 0.88/0.85, k3_hold 0.87/0.85, k3b_hold 0.87/0.86, k4_hold2 0.81/0.82, k5_recover 0.87/0.86; strip mean 0.838 (33 frames, lowest frame 0.70 at 0.083 s) | 2.167 s @24 fps | none (SPEC §8 names no hit event) | no |

Key times (clip s / video s): k0 0.000/0.667 ready · k1 0.167/0.833 buckles forward (knees bend, chest folds, head
down) · k2 0.250/0.917 snaps back: arched, right foot stepped back on its toes · k2b 0.458/1.125 deepest arch, head
thrown back · k3 0.667/1.333 · k3b 0.917/1.583 · k4 1.167/1.833 holds the arch · k5 1.667/2.333 chest still lifted,
legs straight again · k0 2.167/2.833 back to ready. k2b and k3b are read back from the bake and refitted with `ak fit`.
Feet: left foot planted on every key (`ground: left`), right toe within -1.1/+1.1 cm of the floor; nothing passes
through the body in the strip, no pops, the sword and shield follow the hands.

## What the video shows (reference check)
- The video is usable (calib IoU 0.95 front / 0.98 side, views in sync), but it differs from the prompt:
  1. He never takes a combat-ready stance: from 0 s to the end he stands in the sheet A-pose (arms hanging out, sword
     low, feet together). The hit therefore starts and ends on the video's own stance = the rig's rest pose, not on the
     idle clip's wide ready stance. Same choice the attack animator made (its "ready" is also this video's rest stance).
  2. Timing: the hits land at ~0.75 s and ~5.6 s (prompt: 1 s and 5 s). Take 1 (0.67-2.83 s) is used; take 2 (5.6-8 s)
     is the same move and later in any drift.
  3. "Torso jerks back" is preceded by a 2-3 frame forward buckle (0.75-0.83 s) — traced as k1, it sells the impact.
  4. During the arch the video body drifts ~18-21 cm forward in the side panel (hips thrust). That is in `view_offset`
     only (framing); the clip stays in place with the left foot planted.

## Decisions (owner away)
- Natural video timing (2.17 s). SPEC wants a 0.4 s flinch: the snap to the arch is already fast (0.25 s), so the game
  can play the start and blend out, or the lead can run `ak retime keys_hit.json --scale 0.5` (1.08 s) before merging.
  I did not retime because the strip check needs video time.
- Start/end on the rest stance (see 1. above). If the game crossfades idle -> hit, the legs move from the wide idle stance
  to the narrow one during the blend. If that looks wrong in game, a variant with the same spine/head/arm motion over
  the idle legs is the fix (not done: it cannot be checked against this video).

## What does not match and why
- Frame 0.083 s (video 0.75) scores 0.70: the video's buckle starts one frame earlier than our ease-in.
- Sword during the arch: the video blade points forward almost level in the side view, ours points forward-down
  ~25 deg (hand twist not keyed; reads fine at game scale).
- Shield arm during the arch: the video flings the shield further out to his left than our pose; fit preferred a
  closer arm on the in-between frames, so the extreme flare at 1.33 s is slightly under-done.

Files: `keys_hit.json`, `poses_hit/*.json`, `action_hit.json`, `strip_hit.jpg`. Scratch (generator `gen.py`, fit logs,
comparison images, `strip_hit.mp4`) in `work/anim/hercules_hit/`.

## Review fix 2 (animation fixer, 2026-11-22; owner away)
- hit: retimed to a 0.458 s flinch (7 keys: idle k0, k1_impact .042, k2_peak .083, k2b_arch .167, k4_hold2 .292, k5_recover .375, idle k0 .458) on the idle k0 legs (ground left); k3_hold/k3b_hold are no longer used. Strip reference row no longer matches (video time). See docs/notes/anim_hercules_review_fix.md for numbers; scripts in work/anim/hercules_review_fix/.

animfix_hercules 2026-11-23: re-based again on natural_pose.json v2 (work/animfix_hercules/build.py + edits.py; see the 'animfix' entry in keys_*.json and docs/notes/assemble2_hercules.md). Old files in art_src/chars/hercules/backup_animfix_20261123/clips/hit/.
