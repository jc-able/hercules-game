# hercules / block video: animator notes (2026-11-22; owner away, decisions noted)

The reference is usable: calib IoU front 0.952 / side 0.977, the views stay in sync and the camera holds still.
Video: 0-0.75 s sheet A-pose, 0.875-1.25 s shield comes up (fast, about 0.4 s), 1.375-9.0 s braced hold (`ak cycle` from
2.0 s: period 1.25 s, frame IoU 0.995, so almost no motion; the 6-7 s "impact" is barely visible), 9.0-9.5 s it jumps
back to the A-pose.
IoU = silhouette overlap front/side of the pose against its aligned video frame (`ak pose` / `ak strip`).

| clip | video window | keys | IoU per key (front/side) | length | events | loop |
|---|---|---|---|---|---|---|
| block_start | 0.875-1.29 s | 3 | k0 idle stance 0.44/0.47 (not traced: it is the game's ready pose, the video starts from the A-pose); k1 step + raise (0.167 s) about 0.73/0.59 vs 1.04 s; k2 block 0.88/0.62 vs 1.29 s | 0.417 s @24 fps | none | no |
| block_idle | 2.0-4.5 s (2 x the 1.25 s period) | 2 | k0 block 0.880/0.620 (2.0 s), k1 brace 0.849/0.603 (3.25 s); strip mean 0.740 | 2.5 s @24 fps | none | yes |

Chain: `poses_block_start/k2.json` == `poses_block_idle/k0.json` (byte-identical). `poses_block_start/k0.json` = the idle
clip's `poses_idle/k0.json` (only `view_offset` differs, which is render-only), so idle -> block_start -> block_idle chains.
Feet: both planted in every block key (ground left 0.000 / right 0.001 m); bake strips stay within +-0.4 mm.

## Decisions (owner away)
- block_start starts from the game's idle stance, not the video's A-pose. That stance has the right foot 0.64 m back, the block
  has the feet square and wide (as in the video), so the back foot steps up at 0.167 s (lifted 13 cm, `ground: left`) while
  the shield comes up. The shield arm leads (80 % of the way at k1) like the video, where the shield is up by 1.08 s.
- Length 0.417 s (the video's raise is about 0.4 s); the game can speed it up.
- block_idle: the video holds still, so the loop is slowed to 2.5 s with an authored brace: knees 3-4 deg deeper,
  chest 1.5 deg, shield arm 2 deg. It is subtle on purpose.
- Shield: a shield's face is always square to the forearm. The video's side view shows the shield turned about 40 deg toward
  the camera and held far forward, while its front view shows it face-on: the two views disagree. I matched the front
  (forearm across the chest, angled 20 deg forward, twist solved so the face points forward, normal [0.14, -0.97, -0.19]).
- Sword hand: local rx -35 scored best (tried -20 / -5 / +10: all lower).
- Tools: `work/anim/hercules_block/tools/gen.py` writes every pose + keys file from `p/block.json` (the traced block pose) and
  the idle k0; `tools/conv.py` converts aim form (front/side/twist, plus `dir` and `face` for the shield) into rx/ry/rz,
  because `ak fit` only accepts rx/ry/rz.

## What does not match and why
- Side panel stays around 0.60-0.62: the video's shield is drawn bigger, turned toward the side camera and about 0.2 m
  further forward than a forearm-across hold can reach (see above). The video's upper back and drawn-back sword elbow also sit a
  little further back than ours.
- Sword in the front view: the video hides the blade (it points at the camera); ours shows it rising past the right hand.
  The side view matches (blade forward-up in front of the shield's lower edge).
- The video's 6-7 s impact (slide back) is not used: no clip asks for it. A `block_hit` could be cut from 6.0-7.0 s if wanted.
- The legs move from the idle stagger to the square block stance inside block_start; if the game blends block_idle straight
  back to idle (0.1 s lower), the feet will slide back to the stagger during that blend.

Files: `keys_block_start.json`, `keys_block_idle.json`, `poses_block_start/k0-k2.json`, `poses_block_idle/k0-k1.json`,
`action_block_start.json`, `action_block_idle.json`, `strip_block_start.jpg`, `strip_block_idle.jpg`;
scratch + `strip_block_*.mp4` in `work/anim/hercules_block/`.

## Review fix 2 (animation fixer, 2026-11-22; owner away)
- block_start retimed x0.6 to 0.25 s (k1 at 0.083) so it ends with player.gd's 0.15 s switch + 0.1 s blend. New block_end (keys_block_end.json, action_block_end.json, 0.25 s) = block_start reversed, for lowering the shield (core must play it). See docs/notes/anim_hercules_review_fix.md for numbers; scripts in work/anim/hercules_review_fix/.

animfix_hercules 2026-11-23: re-based again on natural_pose.json v2 (work/animfix_hercules/build.py + edits.py; see the 'animfix' entry in keys_*.json and docs/notes/assemble2_hercules.md). Old files in art_src/chars/hercules/backup_animfix_20261123/clips/block/.


## clipfix2_hercules 2026-11-23
block_end 0.25 -> 0.3333 s: whole clip time-warped (Hermite: original speed at the block_idle seam, 0 at the end), forearm_l world turn in the last 24 fps frames 43.9 / 34.3 -> 14.2 / 5.1 deg. work/clipfix2_hercules/ease.py; strip_block_end.jpg = new.
