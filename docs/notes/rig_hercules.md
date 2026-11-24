# Rig agent: hercules (2026-11-22)

Outputs in `art_src/chars/hercules/`: `hercules.blend`, `hercules_albedo.png`, `rig.json`, `sheets/deform_*.jpg` (9 poses),
`split_sheet.png` + `cam.json`, `export/hercules.glb`. Props: `art_src/props/{sword,shield}.blend` + `_albedo.png`,
`game/assets/props/{sword,shield}.glb`. Steps are rerunnable: `scripts/01_clean.py` .. `08_validate.py`; intermediates
in `art_src/chars/hercules/work/` (git-ignored).

## For the lead / game / animkit
- 23 bones (22 deform + `root`), 31,025 triangles, 15,509 welded vertices (23,559 after glTF seam split), height 1.90 m.
- `hercules.blend` holds the mesh, the armature AND the two props, bone-parented (sword to `hand_r`, shield to `forearm_l`) so the
  sheets show them. `export/hercules.glb` is mesh + skeleton only (no props, no animation): one skin, 23 joints.
- `socket_offsets` are in the socket bone's own frame (+Y along the bone). glTF keeps Blender bone frames for joints,
  so a Godot `BoneAttachment3D` + this offset should reproduce the blend. I did not check this in Godot (I did not run a Godot
  import because other agents may be using the project): please check it once in the game.
- Chest socket = `spine_02`. Meshy's `Spine` (now `spine_03`) only has 2 weighted vertices.
- Shield emblem convention: on the forearm the face points out from the back of the arm, and the lion's top points to the thumb
  side. A block with the forearm across the chest shows the lion upright (see `sheets/deform_block.jpg`). To change it,
  edit the `forearm_l` rot in `rig.json`.
- The split sheet is centred on the bounding box of the body plus props (centre_x 0.048, centre_y -0.141). Margins are mw 2.2, mh 1.6:
  there is room for the sword raised overhead (about 2.9 m) and for falling about 1.3 m either way in the side panel.
- Higgsfield credits: none needed.

## Weight repairs (Meshy auto-weights)
1. Tunic armholes: the upper-arm weights reached far down the tunic sides. With the arms overhead or swung forward, the
   tunic tore up into "wings" (edges stretched up to 6x). Fix: cloth vertices above the belt keep upper-arm weight only
   within 7 cm (geodesic) of the arm skin, with a quadratic falloff (max 80%). The rest goes to `shoulder_*` above the
   armpit and to `spine_02` below it. The armhole was then smoothed. A first try zeroed it completely, which moved the tear
   into a dark smear at the armpit (stretch 24x). The falloff spreads that stretch out.
2. Skirt: I tried capping the thigh weights on the skirt (hips weight from belt to hem). It made crouch and roll worse
   (the thighs came out through the skirt, stretch 22x against 5.8x), so I dropped it. The skirt keeps Meshy's thigh
   blend and is only smoothed. I also tried smoothing the belt, which pulled thigh weight up into the belt, so I reverted it.
3. Crotch seam under the skirt: at the centre line, 60% of the leg weight now goes to `hips`.
4. glTF had split the mesh into 2,557 UV-seam islands. I welded them (the duplicates had identical weights), so the
   smoothing works across seams.
Remaining stretch (hidden): the inner crotch skin under the skirt in leg splits (about 13x on tiny edges), and a slight
smear in the armpit with the arms fully overhead.

## Review fixes (rig fixer, 2026-11-22, owner away: decisions noted)
Rerun order now: `01_clean` -> `02_classify` -> `03_skin` -> **`03b_fix`** (new) -> `04_props` -> `05_assemble` (now reads
`work/hercules_03b_fix.blend`) -> `06_deform_sheets.sh` -> `tools/blender/render_split_sheet.py ... --env 1.65,2.1,2.1,3.1`
-> `07_export` -> `08_validate` -> **`09_tests`** (new, numeric mirror/stretch tests). 29 bones now (28 deform + root),
30,529 triangles (496 glue faces removed), 15,490 vertices.

### REQUEST for animkit / core (blocking for good-looking clips)
The skirt now has its own bones `skirt_f`, `skirt_b`, `skirt_l`, `skirt_r` (children of `hips`). They must be DRIVEN from
the thighs on every pose/frame, never keyed by hand. Without the driver the skirt stays rigid with the hips and the
thighs pass through it in run/lunge. Reference implementation (pure mathutils, no bpy needed):
`art_src/chars/hercules/scripts/skirt_drivers.py`, function `skirt_matrices(rest, posed)` where `rest`/`posed` are
`{bone: 4x4 armature-space matrix}` = exactly animkit's `Rig.rest` and the dict `Rig.solve()` returns. Suggested patch at
the end of `Rig.solve()` (before the root transform is applied, or after; it works in the hips frame either way):
```python
drv = rj.get('driven')   # rig.json "driven" block (keep rigjson on self in __init__)
if drv:
    sys.path.insert(0, os.path.join(REPO, os.path.dirname(drv['code'].split(' ')[0])))
    import skirt_drivers
    P.update(skirt_drivers.skirt_matrices(self.rest, P))
```
Godot alternative (if clips are ever posed at runtime): same formulas, listed in `rig.json` -> `driven.spec`.
Formulas: thigh pitch/abduction measured in the hips frame vs rest; `skirt_f` pitch = 0.85 x max(thigh pitches) (0.15 x
if negative), `skirt_b` = 0.85 x min(...) (0.15 x if positive), `skirt_l/r` abduction = 0.85 x own thigh abduction and
pitch = 0.5 x own thigh pitch forward / 0.35 x backward; clamp +-95 deg; each turns about its own head (0, 0.03, 1.12).

### What changed and why
- Skirt: the generated mesh glued the hem underside to both thighs (496 faces, ring at z 0.70-0.79 outside, 0.91 at the
  crotch). Re-weighting alone cannot fix that: any leg swing stretches the glue band into a membrane (first try with skirt
  bones + glue kept: 150-230x stretch). Deleted the glue faces (19 glue-only vertices go too); the skirt now hangs free
  and the thigh tops are open inside it (material is double-sided in the GLB, so a glimpse shows skin colour).
  Weights: hips at the belt -> skirt bones at the hem (height-based blend, z 1.10 -> 0.66: a geodesic blend gave a
  pleat's inner and outer crease different values and 15-20% more stretched edges), angular cos^2 split between the two
  nearest skirt bones. No thigh weight anywhere on cloth, belt or buckle (the buckle is skin-coloured and had kept
  thigh weight: 77x stretch in crouch until stripped).
- Driver gains differ from the review's 0.6: 0.6 left the front skirt below the lifted thigh (visible poke in side
  view); 0.85 lays it over the thigh. Side panels at 0.85 doubled the shear against the back panel (run 120 stretched
  edges) so they use 0.5 forward / 0.35 back (run 63).
- Feet: ankles (+-0.205, 0.070, 0.140), balls (+-0.237, -0.085, 0.045); left foot/toe/lower-shin weights mirrored from the
  right (1,199 of 1,278 vertices had a partner within 1 cm, the rest inverse-distance from 4 neighbours). Mirror test
  foot 30 deg: p95 7.5 mm, max 9.8 mm (was 5.6 / 6.2 cm). Toe: p95 6.6 mm.
- Skin under the skirt: opposite-leg weight removed beyond a 1.2 cm centre seam (ramp 3 cm); crotch seam 45/45 thighs
  + 10% hips. Crotch skin in ride: 5 stretched edges max 2.8x (was 113, max 11.9x).
- Neck: right back mirrored from the left; shoulder weight ramps out above z 1.55-1.59 (all classes: the spike vertex
  was tunic-coloured); 2,448 micro edges (< 4 mm) share weights. shoulder_r +-60 deg: max 5.6x (was 16x).
- spine_03: up to 45% of the upper-chest spine_02 weight (106 vertices); spine_03 45 deg: 3 stretched edges (was 35-37).
- Armpits: extra smoothing pass (4 cm geodesic): no measurable change (arms overhead still 10.5x on tiny hidden edges).
- Fingers: `fingers_l` / `fingers_r` curl bones (knuckles -> tips); +X about the bone's own axis closes the hand
  (75 deg looks like a grip; 4 edges > 2.5x). Rest pose stays open (brief: no re-posing); close it in clips.
- Sword rest: pitched 35 deg down, 25 deg out, flat toward the front camera; socket_offsets.hand_r updated with it
  (game and sheet agree): rot_deg changed from (-8.39, -4.96, -143.24) to the value now in rig.json.
- Split sheet: `--env 1.65,2.1,2.1,3.1` -> 170.7 px/m (was 208), side panel +-2.1 m around the feet, front +-1.65 m,
  top 3.78 m. Seedance prompts no longer need "in place" for roll/death.
- Known limits: a front view of a lifted knee shows the skirt's inner hem edge (ragged, it was the glue line);
  the back panel hangs straight down in crouch/ride (it sits inside the horse in ride); armpit stretch with the
  arms fully overhead (hidden).
