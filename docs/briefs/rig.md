# Brief — character cleanup + rig (one agent per character)

Read `docs/AGENT_RULES.md` and SPEC §8. You own `art_src/chars/<id>/**` for YOUR character only (and, for hercules /
cyclops, the listed weapon props in `art_src/props/` and `game/assets/props/`).

## Input
`art_src/chars/<id>/raw.glb` — the mesh generated on Higgsfield from the owner's sheet `art_src/sheets/<id>_sheet.png`
(views in `art_src/views/<id>_{front,side,back}.png`). Inspect it first:
`Blender -b --factory-startup --python tools/blender/inspect_render.py -- <glb> <out.jpg> 400` (stats + 4-view sheet).

## Output (all inside `art_src/chars/<id>/`)
1. `<id>.blend` — ONE cleaned mesh object + ONE armature, nothing else:
   - Z up, character faces **-Y**, lowest point on Z = 0, centred on X = 0; real size from SPEC §8;
     object transforms applied (location 0, rotation 0, scale 1 on mesh AND armature);
   - texture <= 2048 px, saved as PNG next to the blend (`<id>_albedo.png`), one material `<id>_mat` (Principled, base colour
     texture only; no metallic/normal maps); keep the mesh's triangle count unless it is > 70k (then decimate to ~60k);
   - rest pose = the generated neutral pose (do not re-pose the mesh);
   - armature: a non-deforming `root` bone at the origin on the ground, then the skeleton. Bone names lowercase snake_case,
     side suffix `_l` / `_r` = the CHARACTER's left / right (its left is at +X when it faces -Y). No bone rolls to worry about
     (animation is authored in armature-space angles), but keep bones along the limb they drive.
   - skin: every vertex weighted, max 4 influences, normalised, smooth blends at joints; no vertex left behind when a bone
     moves (test it!).
2. `rig.json` — `{"id","height","bones":[{"name","parent","head","tail","deform"}], "chains": {...}, "sockets": {logical: bone},
   "socket_offsets": {logical: {"loc":[...],"rot_deg":[...]}}, "pairs": [["x_l","x_r"],...], "notes": "..."}`
   Sockets: the logical names of SPEC §8 for your character.
3. `sheets/deform_*.jpg` — proof renders (front + side) of at least 6 strong test poses that cover every joint group
   (use `tools/blender/render_split_sheet.py`-style ortho flat renders; write your own small pose script).
4. `split_sheet.png` + `cam.json` — the FRONT | SIDE reference sheet made with
   `tools/blender/render_split_sheet.py -- --in <id>.blend --out split_sheet.png --cam cam.json --rest [--mw .. --mh ..] [--bg r,g,b]`
   in the rest pose, with any weapon props attached. Choose margins so every planned clip of SPEC §8 fits in frame
   (a slam with a raised club, a spread wing, a head dropped to the ground, a roll). bg: white `1,1,1` (pegasus: `0.35,0.72,0.47`
   soft green, because the horse is white).
5. `export/<id>.glb` — test export of mesh + skeleton (no animation yet): Blender glTF exporter, +Y up. Check it re-imports.

## How to rig
- **hercules**: the raw GLB is already auto-rigged by Higgsfield (Meshy): 24 bones, armature object scale 0.01, helper mesh
  `Icosphere` (delete it). Keep that skeleton and its weights; apply the scale; rename bones to the convention:
  hips, spine_01 (Spine02), spine_02 (Spine01), spine_03 (Spine), neck, head, shoulder_l, upper_arm_l, forearm_l, hand_l,
  thigh_l, shin_l, foot_l, toe_l (+ `_r`); drop `head_end`/`headfront` if unweighted; add `root`. Check the auto weights in
  hard poses (arms overhead, deep crouch, roll tuck) and repair what tears (tunic skirt between the thighs is the usual spot).
  Weapons: `art_src/props/raw/prop_sword.glb` and `prop_shield.glb` (generated; may appear a few minutes after you start —
  wait up to 10 minutes, then note it and continue without). Clean each prop: real size (sword 0.85 m long, shield 0.9 m
  across), origin at the grip (sword) / at the arm strap centre on the back (shield), decimate to <= 4000 triangles, texture
  1024, export `game/assets/props/sword.glb` and `shield.glb` (+Y up; sword blade along +Y of the prop in Godot = up when the
  socket has no rotation; shield face along +Z). Parent copies to `hand_r` (sword) and `forearm_l` (shield) in the blend so
  the sheets show them, and write the offsets into `rig.json` `socket_offsets`.
- **cyclops**: no rig yet. Build a humanoid skeleton plus a second, lower arm pair: hips, spine_01..03, neck, head, jaw is
  not needed; shoulder_u_l / upper_arm_u_l / forearm_u_l / hand_u_l (upper pair), upper_arm_d_l / forearm_d_l / hand_d_l
  (lower pair), thigh/shin/foot/toe, all with `_r` twins. Fingers are not needed (hands are mittens: the upper hands hold the
  club). Skinning: bone-heat automatic weights usually FAIL on generated meshes ("failed to find solution"); expect that and
  fall back to a robust method (distance-to-bone-segment weights with smooth falloff computed in numpy, then several rounds of
  weight smoothing; limit 4; normalise). The lower arms sit close under the upper arms and beside the torso: make sure an
  upper-arm move does not drag the lower arm. Club: `art_src/props/raw/prop_club.glb` -> real size 5.5 m long, origin at the
  handle, <= 5000 triangles, `game/assets/props/club.glb`; parent a copy to `hand_u_r` held like a bat; record offsets.
  Scale: height 8.0 m.
- **medusa**: upright torso + long tail lying straight back along +Y. Skeleton: root, pelvis (where the tail meets the
  torso), spine_01..03, neck, head, shoulder/upper_arm/forearm/hand `_l/_r`, tail_01..tail_14 (even segments from the pelvis
  down to the ground and back to the tip), and snake hair: one or two bones per visible snake (`snake_01_a`, `snake_01_b`, ...)
  if the mesh has separable snakes, else 6 `hair_*` bones around the head. Upright height 6.5 m.
- **hydra**: root, hips, spine_01..03 (hips -> shoulders), tail_01..tail_08, four legs (`leg_fl_01..03` + `foot_fl`,
  same for fr, bl, br), and NINE necks: find each neck by slicing the mesh above the shoulders; `neck_c_01..05` + `head_c` +
  `jaw_c` for the centre one, `neck_1_01..04` + `head_1` ... `neck_8_..` for the others (number them left to right in the
  front view, 1-4 on the character's right, 5-8 on its left). The necks touch each other in places: weights must not bleed
  between neighbouring necks (assign vertices to the nearest neck CENTRE LINE, not the nearest bone point). Shoulder height
  6.5 m. The jaw may be fused in the mesh: if the mouth cannot open, say so (the game can do without).
- **pegasus**: root, hips, spine_01..03, neck_01..03, head, tail_01..03, legs (`leg_fl_01..03` + `hoof_fl`, ...), wings:
  `wing_l_01` (shoulder) .. `wing_l_03` (tip) + 2-3 feather-fan bones if the mesh allows, same `_r`; `saddle` = a
  non-deforming bone on the back where the rider sits. Withers 1.9 m. Mane can ride with the neck bones.

## Method that works
- One Blender script per step in `art_src/chars/<id>/scripts/` (`01_clean.py`, `02_bones.py`, `03_skin.py`, `04_test.py` ...),
  each loads the previous result and saves the next, so you can rerun a step. Run headless; render a check sheet after each
  step; LOOK at it (<= 1024 px) before going on.
- Place joints from the mesh itself: slice the vertex cloud (numpy) to find limb centre lines, joint narrowings and the
  ground contact points; never guess coordinates from the 2D sheet.
- Deform tests: bend each joint group 45-90 degrees; a good skin shows no spikes, no stretched islands, no stray vertices.
  Fix weights (not the pose) until the sheets look clean. Record what failed and how you fixed it.
- Triangle islands that belong to another part (a snake touching a shoulder, a wing feather near the back) are the classic
  cause of spikes: detect connected components / use geodesic-ish growth from seed vertices when distance weights fail.

## Done when
All five outputs exist, the deform sheets look clean, `export/<id>.glb` re-imports with one skin, and your final answer
gives: bone count, triangle count, size, what the auto-rig/automatic weights got wrong, what you repaired, known limits.
Save 2-4 good devlog images (raw mesh, bones over mesh, a strong test pose, the split sheet) per AGENT_RULES.
