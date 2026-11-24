# rig_hydra notes (rig agent, hydra)

Outputs: `art_src/chars/hydra/{hydra.blend, hydra_albedo.png, rig.json, split_sheet.png, cam.json, sheets/deform_*.jpg, export/hydra.glb}`.

## Decisions taken while the owner was away
- Scale: shoulder (top of the torso at the neck base, dorsal plates excluded) measured at raw z = 0.40 -> x16.25 so that
  shoulder = 6.5 m. Result: 14.4 m to the top of the centre head, 16.0 m nose to tail tip, 10.1 m wide. SPEC 3.3 says
  "heads to ~11 m, body+tail ~18 m": the generated proportions cannot hit all three, the brief's 6.5 m shoulder won.
- Neck numbering: 1-4 on the character's right (-X), 5-8 on its left, left to right in the front view; on each side the
  outer/lowest head is 1 / 8 and the inner top head is 4 / 5. Mirror pairs 1-8, 2-7, 3-6, 4-5.
- Neck seams ripped: the generated mesh fuses touching necks (547 seam edges). With hard per-neck weights those faces became
  membranes when necks separate, so the seams are split (548 vertices duplicated, 0 faces added, 69,992 tris kept).
  A neck pulled far from its neighbour shows a narrow open seam on its side instead (backface-cull off hides it best).
- (superseded by fix round 1) The centre neck had a second headless tube behind it that rode neck_c by height; it is now deleted.
- Jaw: the mouth is fused (solid head, painted mouth line). jaw_c exists and opens the lower face by stretching (~20 deg max,
  no mouth interior). The game can do without it.

## Rerun order (all headless, Blender 5.2 `-b --factory-startup`)
01_clean.py -> work/rig_hydra/wip/01_clean.blend; 01b_trim.py (deletes the rear tube listed in rear_tube_verts.json, caps the
opening, writes wip/01b_trim.blend + wip/cap.json); dump_mesh.py -- wip/01b_trim.blend work/rig_hydra/clean3.npz;
02a_joints.py (python3, necks/heads; uses the ORIGINAL clean npz, joints are unchanged) -> joints_necks.json;
02b_bones.py (loads 01b_trim.blend when present) -> 02_bones.blend + bones.json;
03a_weights.py clean3.npz wip/bones.json wip/weights.npz; 03b_skin.py (island relabel + rip + vertex groups) -> 03_skin.blend;
04_test.py -- wip/03_skin.blend <out> all 0,1.5,7.5,23 (poses.json); 05_finalize.py (hydra.blend, rig.json incl. clip_recipes,
GLB + re-import check); 06_sheets.py; render_split_sheet.py --rest --bg 1,1,1 --env 7.4,12.0,10.0,18.0 (absolute paths).
One-shot runner used in fix round 1: work/rig_hydra/fix/run_all.sh.

## Fix round 1 (rig review findings, 2026-11-22)
- BLOCKER rear tube: the headless 10th tube behind the centre neck (1,775 verts, z 7.5-13.7) is deleted in 01b_trim.py and the
  opening between neck_c / neck_4 / neck_5 is capped with three fans (81 faces, cap centres take the mean of their ring's
  weights). Reviewer's R1b head-down: new edges > 3x median 483 -> 94, edges > 2x 632 -> 145, no second-head sheet.
  The remaining stretch is the outer (back) side of the 2.8 m thick neck_c base in deep bends; the back of that base is now
  weighted by height spine_03 -> neck_c_01 -> neck_c_02 so it stretches gradually (a smooth slope, no tear).
  Tried and dropped: smoothing across the neck_c/neck_4/neck_5 junction (made neck_4/5 bites worse: R3 107 -> 189).
- BLOCKER head_down reach: new `head_down_bow` pose (poses.json + rig.json clip_recipes): spine_01 +10, spine_02 +12,
  spine_03 +25, neck_c 25/25/20/15/10, head_c -30, front legs by 2-bone IK with the feet planted (leg_f*_01 -28, _02 -94,
  _03 +75), hind legs untouched. jaw_c socket z 1.17 m (target <= 1.5 m), snout 0.16 m above ground. The flipped-elbow
  solution (elbows forward) stretched twice as much (gt2 ~740 vs ~363), so the elbows stay behind as in the rest mesh.
  Search script: work/rig_hydra/fix/bow.py.
- MAJOR tail root: the body 'ext' segment behind the hips is gone; body+tail skin behind y 3.3 is weighted along the tail axis
  (hips -> tail_01 -> tail_02 ...), then 4 extra smoothing rounds. tail_01..05 rz 15: edges > 2x 75 -> 48, no flap in R7.
- MAJOR hind hips: body skin within 1.3 m of a leg (z above hip - 2.4 m) takes up to 50% of that leg vertex's weights
  (all four legs) + 40 smoothing rounds within 1.8 m of the hind hip joints. leg_bl_01 +30: edges > 2x 153 -> 85 (target was
  < 30: not reached; the thigh front sits 1.4 m ahead of the hip joint, so a 30 deg swing stretches it whatever the blend).
- minor chest/neck_c_01: neck_c_01's spine_03 blend reaches 0.9 bone lengths into the chest (f0) and chest skin within 1.4 m
  of the neck base takes up to 30% neck_c_01. neck_c_01 +20: edges > 2x 104 -> 18.
- minor seams/islands: the 8 loose 4-6 vertex fragments are gone (tiny neck face islands get their surroundings' label before
  the rip): 1 connected mesh. hydra_mat exports doubleSided = true (Godot imports it with culling off), so seam slits are not
  see-through.
- minor split sheet: re-rendered with --env 7.4,12.0,10.0,18.0 -> 34.8 px/m (was 28.8), covers x +-7.4, y -10..12, z 0..18.
- NOT done here (lead): SPEC 3.3 scale wording (kept 6.5 m shoulder, see the Scale decision above), jaw mouth decal.

## For the animation agent
- Bone rolls are 0; posing.py applies armature-space Euler angles. Leg chains point down, so +X rotation swings a foot backward.
- jaw_c opens with +X (keep <= 20 deg). neck_c forward/down with +X. head_down = rig.json clip_recipes.head_down_bow.
- Sockets: head_c, jaw_c (weak point `jaw`, offset = soft underside), foot_fl, foot_fr, head_1..8 (rig.json socket_offsets,
  bone-local; model-space rest points also listed for Blender and Godot axes).
