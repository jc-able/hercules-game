# Animator: hercules death (2026-11-22)

Clip delivered in `art_src/chars/hercules/clips/death/` (3.75 s @24, no loop, 15 keys, strip IoU mean 0.55). Details in its `notes.md`.

## Requests
- **Game (player death):** the reference video drops the sword and the shield at about clip time 2.0-2.25 s (video 3.0-3.25 s).
  The props are bone-parented in the blend, so the clip cannot drop them. Suggestion: at clip time ~2.1 s in `death`, detach the
  sword/shield attachments and let them fall (or spawn loose copies). Without it the clip still reads: the shield arm and blade end
  flat on the floor. No event was added because SPEC §8 lists no death events; the lead can add e.g. `drop_props: 2.1` to
  `keys_death.json` "events" if the game wants it.
- **animkit:** `ak fit` still refuses aim-form bones. I used my own aim-aware search (`work/anim/hercules_death/tools/opt.py`:
  renders all +-step variants in one `ak pose` call, ~5 s per variant). A `--to-euler` / aim support in fit would help.
- **animkit:** mixing `root.rot` keys with hips-bone-rotation keys in one clip makes the whole body swing sideways between them
  (root bone rotates about the feet origin, loc compensates, both interpolated separately). Worth a warning in `bake`.
- **animkit:** bezier in-betweens of big height changes (kneel drop, topple) put knees/body up to 21 cm through the floor; I added
  read-back grounding keys. A per-frame `ground` option in `bake` would remove the need.
