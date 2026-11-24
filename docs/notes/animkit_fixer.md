# animkit fixer notes (2026-11-22)

Fixed the animkit review findings in `tools/animkit/**` + `docs/ANIM_PIPELINE.md`. Tests: `tools/animkit/tests/run_tests.sh`
(24 tests). `ak selftest` passes on all five real rigs (hercules with its driven skirt, cyclops, hydra, medusa, pegasus).

## Decisions (owner away; simplest safe reading taken)
- Mixed fps: each action keeps its own fps in the blend; `ak export` writes the GLB at the highest clip fps and rescales
  every action to it. A clip whose length is not a whole frame at that fps is retimed by < 1 frame (e.g. 17/24 s ->
  0.700 s, +1.19% speed) so the GLB loop seam stays exact; the manifest carries the GLB length (`retimed` in the JSON).
  Export fails if any GLB clip length differs from the manifest by more than one frame.
- Framing vs motion: new pose fields `view_offset` [x,y,z] m and `view_scale` move/scale the RENDER only (camera moved
  inversely). `pose`/`fit`/`strip` use them (strip interpolates them per key), bake never writes them into the action,
  mirror keeps them. `root.loc` = real body motion only (mirror still negates its x). `fit --bones ...,view_offset`.
- Driven bones: `rig.json "driven"` {bones, code}. Code accepts "file.py:function" and the rig agent's
  "file.py (function(rest, posed))"; the path is tried next to the blend and in every parent folder (repo-relative works).
  Applied after every solve (renders, bakes, merge, read-back). Posing a driven bone is an error.
- Pivot of `root.rot`: rig.json `pivot`, else the root-most deforming bone (hips). Hercules: head moves 0.19 m for
  rx 20 (was 0.53 m about the feet).
- Ground: every pose/solve/bake reports the lowest vertex overall and per side (x > pivot x = left). `root.ground`
  ("lowest"|"left"|"right") sets root.loc z. Bake adds a note when a key floats or sinks > 3 cm. No planted-foot
  slide check between keys (not done).
- Mirror needs the rig (`--blend` or `--rig`): rig.json pairs first, then token swap (l/r, L/R, fl/fr, bl/br,
  Left/Right incl. CamelCase). A sided-looking bone without a partner fails. Chains mirror to the chain with the mirrored
  bone list; `bend_side` flips except on lateral chains (there it is a forward sweep).
- Chain bend axes come from the chain's rest direction class (vertical / fore-aft / lateral), see the table in
  ANIM_PIPELINE.md; `ak info` prints per chain what bend_up / bend_side do and in which panel. Note: Pegasus' wings
  rest pointing up (class vertical) and Hydra's outer necks 1/8 are lateral while 2-7 are vertical.
- Aim form `{"front": a, "side": b, "twist": c}` = bone direction as drawn (0 = down, clockwise +), minimal rotation from
  the rest direction (joint -> single child joint), always absolute. Contradicting angles (one up, one down) fail.
- Merge re-bakes from the poses stored in each action JSON (`spec`) on the current rig; warns on rig-hash change; a
  renamed bone fails naming the file; duplicate clip names need `--replace`. Old action JSONs without `spec` replay
  their rotations with a warning.
- Video frames: every requested time snaps to frame round(t*fps); ffmpeg seeks half a frame early. Strip reference time
  = t0 + clip time (`--t1` only checked, warns if inconsistent).
- Keys starting at t != 0 shift keys AND events (`shifted_by`); events outside 0..length fail.
- Blender launches: file-lock semaphore (AK_SLOTS=6, /tmp/animkit_slots) + memgate (`--need 4`, AK_MEMGATE=0 disables).
- Images: every ak image has a long side <= 1024 (contact sheets paginate: contact_p2.jpg ...). `ak pose` takes several
  --pose/--target pairs into one image and reports iou_limbs (outside a trunk hull) and iou_rest (baseline).

## Not done (see the final report)
- Seedance zoom drift: no `frames --recalib-at`; `view_scale` per key (fittable) is the workaround.
- L/R tint of the render itself: a blue/orange skeleton over OURS instead.
- Planted-foot slide warning between keys; two-character renders (ride).

## Requests for other modules
- Rig agents: rig.json "driven".code should preferably use the "path.py:function" form; "pivot" may be set explicitly.
- Lead: re-bake old action JSONs made before today (they have no `spec`), and move framing offsets from root.loc to
  view_offset in existing pose files (work/animkit_review used root.loc [0.05,-0.08,0]: strip IoU 0.60 -> 0.75 after).
