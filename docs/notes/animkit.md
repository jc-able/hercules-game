# animkit builder notes (2026-11-22)

## Decisions (owner away; simplest reading taken)
- Pose axes = the view axes (world X/Y/Z of the sheet, character faces -Y), not the armature object's axes. For an
  unrotated armature they are the same; for a rotated one the view axes are what the agents see. Converted internally.
- `root.rot` turns the whole posed body about the root bone's head; bone angles are measured before it (a rolling body
  keeps its limb angles). `root.loc` in metres.
- `chain` helper: per-link local_delta; `bend_side` = rz, `bend_up` = rx (rx/ry/rz lists also accepted).
- Bake removes the straight-line horizontal root drift (first -> last key) by default = "root motion kept in place";
  `--keep-root-motion` disables it. Key times + length snap to whole frames (GLB length == manifest length).
- Non-loop clip with `length` past the last key: the last pose is held to `length`.
- `ak export` exports EVERY action in the blend (each pushed to its own NLA track); helper meshes are removed first.
- Seedance re-frames the sheet (test video: character x1.21 in native px, divider moved from 700/1280 to the middle), so
  `ak frames/strip/cycle` rectify frames with a calibration from video frame 0 vs the sheet (`--sheet` or `--calib`).
- Silhouettes of video frames: fitted grey background surface per panel + colourfulness test (floor shadows stay bg).
- Extra commands beyond the brief: `prep` (glb -> clean blend), `cycle` (loop length), `mirror` (L/R pose mirror),
  `selftest` (pose math on any rig). `fit` shipped: synthetic test recovers visible limbs within 1 deg, IoU 0.73 -> 0.96;
  it cannot find limbs hidden behind the body (documented).

## Requests / notes for the lead and other modules
- Seedance prompts: ask for a "static locked-off camera, no zoom, no pan". The test run drifts/zooms a few % after frame 0;
  calibration only fixes frame 0's framing; root.loc can absorb a shift, not a zoom.
- Core (`CharacterVisual`): glTF has no loop flag, Godot imports clips with loop off -> set loop from `<id>_clips.json`.
- Pegasus (white) or any white/grey character: render its split sheet with a coloured `--bg`, otherwise silhouettes fail.
- Rig agents: `rig.json` next to `<id>.blend` may carry `sockets`, `socket_offsets`, `chains` ({name: [bones]}); `ak info`
  and `ak export` read it. Without rig.json, `ak export --clips-json` keeps the sockets already in an existing clips json.
- Animation agents must use `ak bake --out-action` (JSON) and never write the shared blend; the lead runs `ak merge` once.
