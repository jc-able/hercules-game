# anim medusa death (animator, 2026-11-22)
- Delivered: art_src/chars/medusa/clips/death/{keys_death.json, poses_death/k0..k7, action_death.json, strip_death.jpg, notes.md}.
- action_death.json is baked with `--keep-root-motion` (spec.in_place = false), so `ak merge` re-bakes it the same way. The body
  travels ~2.9 m forward-right as she falls while the ground tail stays planted; in-place drift removal would slide the tail.
  The game should leave the death clip's root motion as is (the boss does not move after death).
- Decision (owner away): the video has a 1-frame jump cut at 3.0->3.125 s and its panels disagree afterwards (front = lying
  across X, side = lying along Y). Keyed the one 3D pose consistent with both: a diagonal fall forward-right, face down.
- Tool request (animkit): a "planted chain" option (keep a bone head, here tail_05, fixed in world space by solving root.loc)
  would replace work/anim/medusa_death/anchor.py, and `fit` with that option would stop fits from sliding the ground tail
  (one rejected fit pushed the tail 4.6 m under the floor). `fit` also refuses aim-form bones: work/anim/medusa_death/aim2eul.py
  converts them to rx/ry/rz.
