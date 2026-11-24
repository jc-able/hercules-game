# Props agent notes (2026-11-22)

## Pipeline (reproducible)
- `art_src/props/clean/scripts/clean_props.py` (headless Blender, table-driven): import raw -> join -> apply transforms ->
  merge doubles (1e-4) -> optional brazier flame strip / ground-card strip -> collapse-decimate to budget ->
  outward normals + smooth by angle 40 deg -> scale to real size -> centre X/Y, base Z=0 -> one Principled material with
  base colour only (texture resized to 1024, temple 2048) -> export GLB (+Y up) -> re-import and verify.
  Per-prop stats go to `work/props/stats/<name>.json` (git-ignored).
- `render_views.py` renders front + three-quarter (Workbench, textured, red 1.8 m reference bar).
- `build_manifest.py` re-reads the GLBs with trimesh/pygltflib and writes `game/assets/props/props.json`.
- Run: `Blender -b --factory-startup --python clean_props.py -- all` then `python3 build_manifest.py`.
- No front rotation was needed: every Hunyuan raw already faced -Y (Blender) = +Z (Godot), checked against the concepts.

## Decisions taken with the owner away
- Brazier: flame was fused to the bowl (only a 970-face tongue was separate), so it was cut by fire colour + everything
  4% above the widest rim section. Scaled from the RAW height (with flame) to 1.5 m, so the body is 0.97 m and the
  game's fire (at y ~= 0.9) makes up the rest.
- column_broken: the generator baked the concept's drop shadow as a ground card fused to the mesh; removed (991 raw faces).
  A thin sliver may remain flat at y = 0 under the fallen drum.
- gate: a single box would block the walkable opening, so the manifest also has `collision_parts` (2 posts + lintel)
  and `opening_height` (5.2 m). Core should prefer `collision_parts` when present.
- Statues: collision box = plinth footprint at full height (not the spear/shield bounds).
- pedestal is round -> cylinder. cypress -> full-height cylinder (dense canopy). olive_tree -> trunk cylinder, half height.
- Extra manifest keys beyond the brief: `collision_offset` (shape centre in Godot axes), `texture_px`, `materials`,
  plus `_conventions`.
- The clean `.blend` files were not kept (they carry the 4k source image, ~20 MB each); GLB + albedo PNG are the source.
- sword/shield/club in the same folder belong to the rig agents and are not in props.json.

## Requests for the lead
- REGENERATE olive_tree: the Hunyuan output has no canopy at all (bare twisted trunk with stubby branch ends), the
  concept `img_olive_tree.png` has a full grey-green canopy. Suggest re-running image->3D on the same concept (or a
  concept with a denser, more solid canopy silhouette), then `clean_props.py -- olive_tree` + `build_manifest.py`.
- Optional: brazier interior still shows pale stubs where the flame met the coals; invisible once the game fire is on.
