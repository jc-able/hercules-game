# Medusa rig notes (rig agent, 2026-11-22)

- Outputs: `art_src/chars/medusa/{medusa.blend, medusa_albedo.png, rig.json, split_sheet.png, cam.json, sheets/deform_*.jpg, export/medusa.glb}`.
- Rebuild: `scripts/01_clean.py` -> `02_bones.py` -> `03_skin.py` -> `04_final.py` -> `05_deform_sheets.sh` (intermediates in `work/rig_medusa/`).
  Bone positions come from `scripts/bones_spec.json` (made by `centerline.py` + `make_spec.py` from vertex slices).
- Tail length: SPEC 3.2 says "tail ~14 m"; the generated mesh scaled to the 6.5 m upright height gives 9.9 m of tail on the ground
  (11.8 m along the centre line from the pelvis). Kept the mesh proportions. For a longer tail, scale the tail bones in Godot or ask
  for a regenerated mesh (lead decision).
- Hierarchy (for the animation agent): root -> pelvis -> {spine_01.., tail_01..tail_14}. Pelvis is the COG and carries the grounded
  tail: to drop the head to the floor (stunned) or rise, move/rotate pelvis and counter-rotate tail_01..04 so the tail stays on the ground.
- Snake hair is fused to the head mesh: 6 `hair_{l,r}_{01..03}` bones (01 top), one per snake; no per-snake second bone.
- Back hair is fused to the upper back: head turns over ~45 deg visibly stretch the hair over the shoulders (split big turns
  between neck and head and the spine).
- Extra socket `eyes` (on the face between the eyes, child of head) for the gaze beam origin, besides SPEC's head / neck / tail_tip.

## Review fixes (rig fixer, 2026-11-22, after work/rig_review_medusa)
- New step `scripts/03b_reweight.py` (numpy solver `scripts/weights_solve.py`) between 03 and 04: 03_skin.blend -> 03b_skin.blend;
  `04_final.py` now loads 03b. Rebuild order: 01 -> 02 -> 03 -> 03b -> 04 -> 05 (`05_deform_sheets.sh [pose.json ...]`, per-pose
  `_box`/`_cubox` allowed) -> split sheets (below).
- Method: harmonic (Laplace, uniform edge weights) blends between anchor sets instead of distance weights + hard region masks.
  The neck+head share is a separate harmonic field that is 0 on the shoulder tops (|x| > 0.38, z < 5.2 in front; z < 5.0 behind,
  where the back-hair curtain lies on the shoulders) and 1 on the head core above the jaw line (z 5.48 at the chin, rising to
  ~5.93 at the back of the skull) and on a front neck ring at z 5.25-5.31. Snakes: hair weight ramps 0 -> 1 geodesically over
  mesh edges from 5 cm inside the hair mass to 20 cm along the snake (55 cm for the low hair_*_03 snakes); no hair weight
  below z 5.25 on shoulder/spine vertices. Clavicles faded to 0 across the midline. Soft restricted smoothing, limit 4.
- Max edge stretch (reviewer's stress2.py, rerun on the new blend): clavicle up 30 25.7 -> 3.2 cm, neck turn 35 23.4 -> 4.2,
  upper arm fwd 90 12.8 -> 4.5, head turn 45 26.6 -> 5.3, head nod 40 23.3 -> 5.1, hair_l_01 up 45 17.1 -> 5.0,
  hair_l_03 fwd 60 17.1 -> 3.6, hair_r_02 fwd 60 14.5 -> 2.2. Spike vertices in the reviewer's 6 poses: 113 -> 0.
- Deviation from the review text: the hair_*_03 roots sit inside the neck/head ramp of the back-hair curtain, so their snake
  roots blend from the local head/neck/spine_03 mix (not head only) into the hair bone; this is what keeps the head turn under 6 cm.
- Framing: `split_sheet.png` + `cam.json` (1920x1080, ppm 69.1, front x +-6 m, side y -6.2..9.6) for idle, slither, gaze,
  stun_start, stunned, rise, hurt, death; `split_sheet_tail_swipe.png` + `cam_tail_swipe.json` (1920x1080, ppm 47.4, front
  +-10 m, side y -10.5..10) for tail_swipe only. Commands:
  `render_split_sheet.py -- --in medusa.blend --out split_sheet.png --cam cam.json --rest --size 1920x1080 --env 6.0,9.6,6.2,7.4`
  `... --out split_sheet_tail_swipe.png --cam cam_tail_swipe.json --rest --size 1920x1080 --env 10.0,10.0,10.5,7.4`
  (then the `clips` / `coverage_m` / `framing_note` keys are added to both cam files).
- Lean recipe (owner away, decision: no tail re-parenting): pelvis moves on an arc about the tail_03 head (0, -0.9145, 1.622),
  rotates by the lean angle, tail_03 counter-rotates by the same angle. In rig.json `notes` and `lean_recipe`; deform sheet
  `deform_stunned_head_floor.jpg` uses it. Suggest an animkit helper for it.
- For the lead: SPEC §3.2/§8 says "tail back ~14 m"; the mesh gives 9.9 m on the ground (tip 9.3 m from the pelvis axis).
  Recommend changing SPEC to "~10 m" (owner-sheet proportions); tail_swipe r 7 m is still covered.
- Not touched (not in the review): tail hat weights; tail_09 side 60 = 9.7 cm and the reviewer's coiled-tail stun pose = 14 cm
  on the ground tail (wide 26 deg-per-segment coil).
