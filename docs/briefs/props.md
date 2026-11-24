# Brief — environment props cleanup

Read `docs/AGENT_RULES.md`. You own `game/assets/props/**` (except sword.glb / shield.glb / club.glb, made by the rig
agents), `art_src/props/clean/**` and `docs/notes/props.md`.

## Input
`art_src/props/raw/prop_<name>.glb` — generated on Higgsfield (Hunyuan3D v3, ~40k triangles, 4096 px texture) from the
concept images in `art_src/props/concepts/img_<name>.png`. Names: column, column_broken, statue_a, statue_b,
basalt_spire, boulder, temple, olive_tree, brazier, amphora, pedestal, gate, cypress, cliff_rock.
(Some may still be downloading when you start: process what is there, poll every few minutes for up to 20 minutes.)

## For each prop (one headless Blender script, data-driven from a table)
- upright (+Z up in Blender), sitting on Z = 0, centred on X/Y, front of the object facing -Y;
- real size (longest relevant dimension): column 6.0 m tall; column_broken 2.4 m tall; statue_a / statue_b 2.6 m tall
  with plinth; basalt_spire 7.0 m tall; boulder 2.2 m; temple 9.0 m wide; olive_tree 5.0 m tall; brazier 1.5 m tall;
  amphora 1.3 m tall; pedestal 1.1 m tall; gate 7.0 m tall; cypress 8.0 m tall; cliff_rock 4.0 m;
- triangles: decimate to a budget (temple 12000; statues, trees, gate 6000; others 3000) without wrecking the silhouette;
  recalculate normals outward; merge doubles; ONE material, base colour texture only, resized to 1024 px (temple 2048);
- brazier: delete the flame geometry if it is separable (the game adds real fire), else keep;
- export `game/assets/props/<name>.glb` (+Y up) and re-import it once to verify (triangles, texture, size).
- contact sheet of all cleaned props (front + three-quarter), look at it (<= 1024 px).

## Manifest
`game/assets/props/props.json`: `{name: {"size": [x, y, z] metres in Godot axes, "triangles": n,
"collision": "box" | "cylinder" | "none", "collision_size": [...], "notes": "..."}}` — pick the simplest collision shape
that matches (trees: cylinder around the trunk; boulders/rocks: box; temple: box).

## Done when
All available props are exported, the manifest matches the files, the contact sheet looks right, and your final answer
lists each prop with triangles, size and any that came out badly (so the lead can regenerate it).
Save the contact sheet for the devlog (AGENT_RULES).
