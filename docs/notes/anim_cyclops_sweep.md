# anim_cyclops_sweep notes
- Ready pose used for start/end of sweep = the rest T-pose (club upright in hand_u_r), as in every cyclops reference video's
  first frame. If the idle clip settles on a different ready pose, the game should blend into sweep (or the idle animator
  should start/end idle on the rest pose).
- Rig limit (same as anim_cyclops_slam): club arm chain is short (0.8 + 0.8 m); over-the-left-shoulder follow-through puts the
  right fist at the beard. Longer upper arm/forearm bones would remove the clip at sweep 1.85-2.1 s.
- ak suggestion: an option for `bake` to interpolate in absolute (world) space between keys would avoid the club swinging
  through the body when root yaw changes 60+ deg between keys (I worked around it with midpose.py in-between keys).
