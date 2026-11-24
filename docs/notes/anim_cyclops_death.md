# anim_cyclops_death (animator, 2026-11-22)
- Delivered art_src/chars/cyclops/clips/death/{keys_death.json, poses_death/, action_death.json, strip_death.jpg, notes.md}.
- action_death.json is baked with --keep-root-motion. He falls forward from his knees: the hips end ~0.6 m forward and the
  head ~4 m forward. The lead's `ak merge` should keep that. If merge re-bakes in place, the knees would slide back
  while he falls.
- Request for the cyclops module: the club cannot leave the hand inside the GLB (bone-parented to hand_u_r). If the game
  wants the video's dropped club, detach the club node at about 0.6 s into `death` and let it fall to the floor at his right
  side. The animation already lowers the arm so the club lies on the floor beside him.
- No Higgsfield generation needed.
