# rig_cyclops notes (cyclops cleanup + rig, 2026-11-22)

Scripts: `art_src/chars/cyclops/scripts/01_clean.py` .. `09_verify.py` (run order 01, dump_mesh, make_joints, 02, 03a, 03,
04, 05, 06, 07, 08, 09). Intermediate blends live in `work/rig_cyclops/` (git-ignored); rerun from 01 to rebuild.

- Mesh: 41,209 tris kept (< 70k), welded UV-seam duplicates (36,868 -> 20,606 verts; UVs kept), 1 connected piece.
  Scaled x4.2216 to 8.0 m; size 8.03 x 2.39 x 8.0 m; feet centred on Y, X centred on the bbox.
- Skeleton (29 bones, 28 deform): root, hips, spine_01..03, neck, head, shoulder_u/upper_arm_u/forearm_u/hand_u (_l/_r),
  upper_arm_d/forearm_d/hand_d (_l/_r, parented to spine_03 — no clavicle for the lower pair), thigh/shin/foot/toe (_l/_r).
  Joint positions measured from numpy slices (`joints.json`, `make_joints.py`).
- Skin: bone heat NOT tried as the brief predicted failure on this fused shell; own weights in `03a_weights.py`:
  cost = 3 x distance-to-bone-segment / bone radius, relaxed over mesh edges (geodesic-ish, uniform walking cost),
  falloff band 0.65 radii, side rules (_l bones never weight x < -0.05), beard rides the head, crotch shares hips + thighs,
  12 smoothing rounds, top-4, normalised.
  Mistakes fixed on the way: (1) plain distance gave the torso sides to the lower-arm bone (its head sits closer to the
  torso surface than the spine) -> costs measured in bone radii; (2) then the wide hips bone reached down the legs through
  the surface (walk cost was divided by the big radius) -> uniform walk cost; (3) shoulder radius 0.55 grabbed the armband
  -> 0.42; (4) textures went magenta in the work blend (relative path) -> absolute paths in 01.
- Checks (05_check.py): 0 unweighted, max 4 influences, root move error 3e-6 m, rotating each upper arm 90 deg leaves 0
  hand verts behind and drags 0 lower-arm verts (and vice versa); worst absolute edge stretch 0.22 m (inner thigh in an
  80 deg crouch), every other test pose <= 0.15 m.
- Club: `art_src/props/club/club.blend` + `club_albedo.png` -> `game/assets/props/club.glb`: 4,850 tris (from 40,000),
  1024 px texture, 5.5 m long, origin on the grip 0.45 m above the butt, head along +Z (Blender) / +Y (Godot).
  A copy is bone-parented to `hand_u_r` in `cyclops.blend` (so the blend holds mesh + armature + that club copy).
  Held like a bat: the T-pose hands have thumbs up / palms forward, so the handle runs vertically through the fist.
- socket_offsets in rig.json are in the glTF joint frame (= Godot bone global rest, Y up) with rot_deg in Godot's YXZ
  order + a quaternion. Not yet verified inside Godot (game import of the character is the anim/boss agents' step).

## Rev 2 (2026-11-22, rig fixer after the independent review)
- BLOCKER fixed: leg joints were one segment low. Slices (left leg x > 0.15): ankle narrowing z 0.8-1.1 (y centre 0.57),
  calf z 1.4-1.8, knee hollow z 2.2-2.3. New knee (+-0.80, 0.33, 2.22), ankle (+-0.97, 0.57, 0.95); hip/ball/toe kept.
- 03a_weights.py step 6 "chain banding": inside each limb chain the chain's total weight is kept but re-split by joint
  planes (normal = bisector of the bone directions, linear blend): upper arm elbow blend |x| 1.87-2.37, wrist +-0.12
  (forearm_u = 1.0 for |x| 2.37-2.90; elbow-90 mid-forearm deviation 0.21/0.32 m -> 0.0); lower arm elbow +-0.35,
  wrist +-0.15 (forearm_d peak 0.80 -> 1.0); knee +-0.25 (thigh 0 below z 1.97), ankle +-0.15 (shin <= 0.33 on 9 back
  verts at z 0.71-0.79, 0 below 0.7), ball on a y plane (toe 1.0 for y < -0.55, 0 for y > -0.35; toe-45 mid-foot move
  0.16-0.19 m -> 0). Heel (y > 0.3, z < 0.6): foot weight 1.0 on all 238 / 281 verts.
  First try used +-0.12 everywhere: the elbow creases then took the stretch (0.32-0.42 m edges in elbow/kneel poses);
  widened the elbow blends on the parent side (numpy LBS checker work/rig_cyclops/fix/lbs.py matches 05_check exactly).
- 03a step 7 posterior armpit: upper_arm_d fades out on the back above z 5.5 (spine_03 takes it) + 14 local smoothing
  rounds in the back strip. Back-armpit edges stretched > 0.1 m in the reviewer poses: R1 47 -> 29, R2 94 -> 57,
  R3 30 -> 14, R4 43 -> 16, R5 49 -> 28 (max ~0.19 m). Forcing upper_arm_d >= 0.7 at the lower-arm root (env ROOT_D=1)
  was tried and rejected: it moved a 0.29-0.35 m stretch onto the torso side under the lower arm.
- rig.json: hand_ul note corrected (left palm, NOT on the club); new socket `club_grip2` (bone hand_u_r, 0.7 m above
  the grip along the club axis) = two-hand IK target for the left upper hand on the club.
- cyclops.blend image paths now relative (//cyclops_albedo.png, //../../props/club/club_albedo.png), done in 07_final.py.
- split_sheet.png / cam.json re-rendered with --mw 1.3 --mh 1.55: 35.7 px/m, front +-9.1 m, side +-8.9 m.
- New test poses in poses_test.json: walk_passing, kneel, death_knees, elbows90_toes_up; zoom sheets deform_zoom_legs,
  deform_zoom_elbow; deform_zoom_armpits / _hips re-rendered on the new rig.
