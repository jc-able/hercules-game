# Pegasus rig notes (rig agent)

Outputs: `art_src/chars/pegasus/` (`pegasus.blend`, `pegasus_albedo.png`, `rig.json`, `split_sheet.png`, `cam.json`,
`sheets/deform_*.jpg`, `export/pegasus.glb`).

## Rebuild order (all headless, scripts in `art_src/chars/pegasus/scripts/`, scratch in `work/rig_pegasus/`)
1. `01_clean.py -- <chardir> <workdir>`: import raw, weld UV-seam duplicates (49,332 -> 34,981 verts, 69,986 tris kept),
   scale 3.2255 (withers measured on the back strip = 1.9 m), ground Z=0, centre X, 2048 px PNG, material `pegasus_mat`.
2. `01b_colors.py -- <workdir>`: per-vertex albedo colour (separates the blue mane/tail hair from the white body/wings).
3. `02_bones.py -- <workdir>`: armature (joint coordinates measured from mesh sections; comments in the script).
4. `python3 03a_weights.py stage1.npz bones.json weights.npz vcol.npy`: geodesic weights (see docstring).
5. `03_skin.py -- <workdir> weights.npz stage3.blend`, then `05_final.py -- stage3.blend <chardir>`.
6. Tests: `04_test.py -- pegasus.blend poses.json <outdir> 180 [--stretchviz]`, `make_deform_sheets.py`.

## Posing the wings (for the animation agent)
The rest wings are raised and folded back: the arm (`wing_*_01`) points UP from a broad root on the shoulder and the
long feathers hang below/behind it. A flap is therefore NOT a single roll about the body axis. Tested whole-wing
rotations at `wing_l_01`, armature-space Euler XYZ degrees (applied in the rest frame; mirror Y and Z for `wing_r_01`):

| pose | wing_l_01 | result |
|---|---|---|
| glide (spread flat, primaries out, secondaries trailing back) | (74.5, 62.3, 23.3) | span 3.98 m, clean |
| downstroke end (wings down-out) | (-147.1, 57.9, 150.9) = same rotation family, ~110 deg | clean, slight smear where the mane touches the wing root |
| upstroke top (wings up, tips over the back) | (55.7, 10.5, 17.5) | small stretched patch on the flank where the wing's lower inner edge is fused to the body |

Add curl with `wing_*_02` / `wing_*_03` (<= 20 deg) and fan with `wing_*_feather_0x` (<= 15-20 deg): neighbouring
feather groups are fused in the generated mesh, so larger relative rotations stretch the feathers between them.
`feather_02` (lower primaries) is a child of `wing_*_02` on purpose, so a hand curl only moves the upper primaries.

## Known limits
- The generator fused the mane to the wing roots and the wing's lower inner edge to the flank (y -0.25..0, z 1.55-1.85).
  Weights are blended across those contacts (8 rings), so big neck bends (> ~60 deg) or the upstroke smear a little
  there instead of tearing. A cleaner fix would be a re-generation with the mane and wings clear of the body.
- Rider (saddle bone, z 1.88 on the back, y +0.10) sits between the raised wing roots: a straddling rider's legs will
  overlap the wing roots in the rest pose; in flight poses the wings rotate away.
- No jaw, ears or eyelids. Tail is 3 bones (stiff curls only).

## Fix round 1 (rig fixer, 2026-11-22, after docs/notes/rig_review_pegasus.md)
Owner away: decisions below were made by the fixer and are noted here.

### New rebuild order (scratch `work/rig_pegasus/`, scripts in `art_src/chars/pegasus/scripts/`)
1. `01_clean.py`, `01b_colors.py` unchanged.
2. `02_bones.py`: tail is now 5 bones (`tail_01..05`, 0.25 m each on the measured tail-hair centre line) -> 43 bones.
3. `01c_rip.py -- <wk> weights_v1.npz --no-rip`: labels only (1 = hanging feather lobe behind the true wing root,
   2 = flank under it). Writes stage2r.blend / stage1r.npz / vcolr.npy / labels.npy (same topology as stage1).
4. `python3 03a_weights.py stage1r.npz bones.json weights_raw.npz vcolr.npy --labels=labels.npy` (tail blend 0.20).
5. `python3 03b_fix.py stage1r.npz vcolr.npy labels.npy weights_raw.npz weights.npz` (targeted repairs, docstring).
6. `03_skin.py -- <wk> weights.npz <wk>/stage3.blend <wk>/stage2r.blend`, then `05_final.py -- stage3.blend <chardir>`.
7. Texture: `06a_hidden_flank_uv.py -- stage2r.blend labels.npy hidden_uv.npz` +
   `python3 06b_paint_hidden_flank.py hidden_uv.npz work/rig_pegasus/pegasus_albedo_orig.png <chardir>/pegasus_albedo.png`
   (repaints the junk the generator left on the flank under the feather lobe; visible once the lobe rides the wing).
   Re-run 05_final after it so the GLB embeds the new texture.
8. Split sheet: `render_split_sheet.py -- --in <abs>/pegasus.blend --out <abs>/split_sheet.png --cam <abs>/cam.json --rest
   --bg 0.35,0.72,0.47 --env 2.6,3.1,2.9,4.3` (front panel 5.2 m, side 6.0 m; use absolute paths). `bg_srgb8`
   [160,221,182] added to cam.json by hand.
Reviewer stress test (own copy with a saddle metric + tail/full-up poses): `work/rig_pegasus/fix/stress.py`.

### What changed (numbers = reviewer's stress poses, edges > 2x; before -> after)
- Saddle area: neck weight on the bare back behind the wing roots = 0 (was 0.24 avg). Skin motion relative to the
  saddle socket: neck forward 25/10 0.19 m -> 0.000 m, head toss 0.15 -> 0.000, head turn 0.11 -> 0.000.
- Rear mane (y > -0.6): neck_01 + spine_03 only, neck_02+ = 0 (fade from y -1.0). Withers edges: neck forward 183 -> 48,
  head toss 30 -> 3, head turn 28 -> 3, head lowered 738 -> 300, graze 827 -> 353. No blue streaks over the back
  from the game camera.
- Feather lobe: wing-only behind the root, flank under it wing-free; upstroke flank 325 -> 77, full-up (R1) 490 -> 132,
  R1 flips 1596 -> 1371. The lobe no longer smears down the flank.
- Breastplate + chest front on spine_03 (2-ring neck blend at the top edge); head toss chest 1 edge, no fold.
- Brisket: verts with both forelegs > 0.05: 289 -> 17; forearm weight above z 1.20 = 0.
- Tail: 5 bones, wider blend.

### Decisions
- RIPS NOT USED. Both rips (mane/wing-root and lobe/flank) were built and tested: they opened see-through holes in every
  flap pose (mane seam up to 0.19 m, lobe seam up to 0.28 m; Godot culls back faces). The contacts are blended
  instead (03b steps 2b and 3). Code kept in 01c_rip.py (run without --no-rip to see it).
- A z-limited rear-mane rule (keep high strands on neck_02/03) was tried and reverted: the high strands hang into the
  low mane, head lowered withers 330 -> 1115.
- Gentler brisket fades (forearm 1.06-1.20, leg_01 0.06-0.18) were tried and reverted: chest edges went up (R1 251 -> 327).

### Known limits after round 1
- Wing moves stretch the wing-root armpit and the fused lobe/flank band (|x| 0.3-0.45, y -0.3..-0.1, z 1.6-1.8) more
  than before, because the lobe now really follows the wing: withers edges upstroke 67 -> 135, glide 35 -> 116,
  downstroke 95 -> 163; flank in glide 37 -> 54. Mostly under the feathers. The reviewer's < 30 flank target is not met
  (upstroke 77, full up 91): it needs a rip that does not open holes (a regenerated mesh with the wing clear of the
  flank) or a wing_*_root helper / corrective shape.
- Leg tucks stretch the brisket more now that the midline is spine_03: one foreleg forward chest 27 -> 74, R1 98 -> 251,
  R2 114 -> 277 (white on white, under the chest).
- Tail lift 80 deg still ~190 edges at the dock (tail_01/hips). Keep tail_01 within 45 deg (45 + curl: 134).
- Animators: neck_01 / neck_02 within ~25 / 15 deg in fly/glide/ride; full-down and full-up wing poses still pinch the
  wing root (flips ~900 at the downstroke).

### Request for the lead (shared tool)
- `tools/blender/render_split_sheet.py`: also write the displayed 8-bit background into cam.json (`bg_srgb8`), and make
  `--out` work with a relative path (it failed with "Couldn't create directory" when run from the char folder).
