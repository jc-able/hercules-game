# anim_medusa_tail_swipe (2026-11-22)
- Delivered art_src/chars/medusa/clips/tail_swipe/{keys_tail_swipe.json, poses_tail_swipe/k*.json, action_tail_swipe.json, strip_tail_swipe.jpg, notes.md}. Scratch + generator: work/anim/medusa_tail_swipe/gen.py.
- Lead decision needed: the reference shows an overhead whip ending front-right (~225 deg), not the SPEC's low 360 sweep. Clip matches the video. A flat 360 sweep needs a new video or an authored clip.
- animkit request: chain bend_up/bend_side are fixed view-axis deltas; after a big yaw (rz) bend_up no longer lifts a tail. A chain mode that bends in each link's own frame (or an aim-per-link helper for chains) would help tails/necks. `ak fit` on alternating links produces zigzags: a "smooth chain" fit option would help.
