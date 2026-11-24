# Animator: hercules attack video (2026-11-22)

Outputs: `art_src/chars/hercules/clips/attack/` (keys_attack_{1,2}.json, poses_attack_{1,2}/, action_attack_{1,2}.json,
strip_attack_{1,2}.jpg, notes.md). Strip mp4s: `work/anim/hercules_attack/strip_attack_{1,2}.mp4`.

## Tips for other animators (things that cost time)
- Framing drifts a lot when the move travels: fit `view_offset` per key (here side offset went 0.18 -> -0.52 m).
  `ak fit` refuses aim-form bones ("fit works on rx/ry/rz"): `work/anim/hercules_attack/gen.py` converts 3D bone
  directions (+ twist) to exact rx/ry/rz (R = Rz Ry Rx, absolute) so poses can be written as directions and still fitted.
- Hercules' sword blade is ~40 deg off the hand_r bone axis (rest blade dir -0.346,-0.743,-0.573); the shield face normal at
  rest is (0.787, 0.111, 0.607) on forearm_l. gen.py solves hand direction + twist for a wanted blade direction
  (`"hand_r": {"dir": hint, "prop": blade}`) and forearm twist for a wanted shield facing (`"forearm_l": {..., "prop": n}`).
- Bake does not ground in-betweens: scan with `ak pose --from-action --t` (ground numbers), then add the read-back pose
  with `"root": {"ground": "lowest"}` as a key. Here in-betweens dipped 5 cm through the floor before that.
- Request (animkit): `ak fit` with a ground constraint (both feet planted) would save the groundfix loop
  (work/anim/hercules_attack/groundfix2.py adjusts thigh_r + shin_l until both feet touch).
