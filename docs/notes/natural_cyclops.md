# Natural stance + clip plan: cyclops (natural-stance agent, 2026-11-23)

Scratch: `work/natural/cyclops/` (pose iterations `p/v1..v6c`, `nat_render.py` = front/side/three-quarter renders +
ground + mesh-overlap check, `club_scan.py` = hand aim search for the club angle, `cyclops_nat.blend` = scratch copy with
the one-frame action `natural_stance`). `art_src/chars/cyclops/cyclops.blend` was only opened read-only.

## 1. What reads stiff today (`python3 tools/clip_motion.py cyclops` + `ak strip`, work/natural/cyclops/strip_*.jpg)
| clip | moving | what reads stiff |
|---|---|---|
| walk (1.42 s loop) | 13/29 | all four arms, both shoulders, head, spine_03 frozen: he steps in the T pose with the club straight up; lower arms only rock 2-10 deg. Legs fine. |
| idle (3.33 s loop) | 9/29 | T pose with the club up; only upper arms / neck-head barely move; legs, spine, forearms, hands frozen: a statue that breathes a little. |
| sweep (2.5 s) | 21/29 | acting arm and trunk good; starts and ends in the T pose (club up); head, hips, left shoulder, lower hands frozen. |
| slam (1.75 s) | 24/29 | starts in the T pose (k00_ready = rest); lower hands frozen. Strike itself is fine. |
| pull_free (1.5 s) | 24/29 | ends in the T pose (k00_ready); lower hands frozen. |
| stuck (1.5 s loop) | 11/29 | legs, spine, neck, lower forearms + hands frozen while he tugs the planted club: only the upper arms work. |
| hurt (0.67 s) | 15/29 | flinch from the stuck pose; legs, hips, spine_01, neck, lower hands frozen. |
| death (4.5 s) | 26/29 | fine overall; starts from the rest pose (k0_ready), shoulders frozen. |
No pops seen in the strips; the problem is frozen limb groups and the T-pose start/end, as the lead measured.

## 2. The natural stance (`art_src/chars/cyclops/natural_pose.json`, animkit pose format, absolute)
A heavy giant standing ready, weight on his LEFT leg, club resting on his right shoulder.
- Trunk: slight forward slouch, spine_01/02/03 rx 4/9/13 deg (absolute), small contrapposto (spine ry 2/4/6, spine_03 rz -4);
  neck rx 6, head rx -2 rz 5 (eye level, looking a little to his left).
- Pelvis: shifted 0.25 m toward the standing left leg, hips ry -6 (drops on the free right side).
- Legs: left (standing) thigh rx -3 ry 4, shin rx 3 (soft knee); right (free) thigh rx -21 ry 9, shin rx 14 (knee bent ~35 deg),
  foot turned out 10 deg. Both feet flat: `ak solve` lowest vertex left 0.000 m, right 0.002 m (`root.ground: lowest`, root z -0.085).
- Upper right arm (club): shoulder_u_r front 76 (shrugged up under the club), upper arm front 48 / side -40 (elbow out and
  forward), forearm folded up (front 178 / side -165), hand front -150 / side -150 / twist 78 = fist in front of the right
  shoulder at (-1.52, -0.62, 6.19) m, club axis (-0.16, 0.79, 0.60): up and back over the shoulder, head at z 9.86 m,
  3.8 m behind the heels. Club rests 0.05 m above the trapezius (0 intersecting triangles outside the gripping hand).
  Chosen over "hanging at his side": the 5.5 m club cannot hang head-down from a 4 m hand (it goes through the floor) and
  a forward-pointing club hides the body in the front panel; on the shoulder it is compact, readable in both panels and
  bounces naturally in a walk. Lower shrugs (68/72) put the handle 0.03 m into the shoulder (28-42 triangles).
- Upper left arm: hangs slightly back and out with a bent elbow (shoulder -64, upper arm front -32 / side 14, forearm
  front -16 / side -22, hand twist 120: palm toward the thigh).
- Lower arms, not mirrored: left upper_arm_d front -26 / side -32, forearm front 30 / side -48, hand front 36 / side -28
  (hand hangs in front of the left hip, further forward); right upper_arm_d front 26 / side -16, forearm front -24 / side -40,
  hand front -28 / side -20 (closer to the skirt, lower). Hands cannot close: the rig has no finger bones (half-closed
  fists are not possible; palms are turned toward the thighs instead).
- Mesh checks (BVH overlap between strongest-bone vertex groups): 0 for arm_u_l/arm_u_r/arm_d_l/arm_d_r vs trunk, lower
  arms vs thighs, lower vs upper arm (v1 had 189 between the left arms, fixed by hanging the upper left arm 14 deg back),
  arms vs head, leg vs leg.
- Verified: `ak pose` with `cam_nat_std.json` against the new sheet: IoU 0.999 front / 0.999 side (the sheet is exactly
  this pose in that framing), gain over rest 0.53.

## 3. New split sheet
`art_src/chars/cyclops/sheet_nat_std.png` + `cam_nat_std.json`: 1280x720 (16:9), FRONT | SIDE (facing right), white,
57.86 px/m in both panels, `--env 3.6,4.3,2.8,11.2` (half width 3.6 m, 4.3 m behind for the club, 2.8 m in front for the
stride and the lower hands, 11.2 m top; club head at 9.86 m leaves ~1.3 m headroom for the walk bob). Front panel 644 px,
side 636 px. Rendered with `tools/blender/render_split_sheet.py --in work/natural/cyclops/cyclops_nat.blend --frame 1`.
No wide sheet: no clip needs a new video with more room (slam/sweep are re-based, not re-generated).

## 4. Plan for every clip
| clip | plan | what to do |
|---|---|---|
| idle | **V** idle_n | New reference from sheet_nat_std; keyframe every limb group to it; loop. Length may change from 3.33 s to the measured cycle (breath 3.5 s, weight shift 7 s: a 7 s loop is fine for an idle). |
| walk | **V** walk_n | New reference from sheet_nat_std; keyframe all four arms, trunk, head, club bounce to it; keep the 1.4167 s loop, the `step` event 0.40 s (right heel strike) and the planted-foot speed (retime the video steps to 0.71 s each). |
| slam | R | Keep k01_lift..k07_impact and impact 1.5 s exactly. Replace the t=0 key (k00_ready = rest T pose) with natural_pose.json (club comes up off the shoulder: check the 0-0.25 s in-between for the club crossing the head). Lower forearms/hands: brace forward during the overhead (1.0 s) and snap down with the impact. |
| sweep | R | Keep k1..k9 and impact 1.31 s. Replace k0_ready at t=0 and t=2.5 with the natural stance (k8_over_shoulder at 1.88 s is already a club-on-shoulder pose: the recovery flows into it). Head follows the club (looks into the swing then forward), hips counter-turn 5-8 deg, left upper arm balances outward, lower hands trail the swing by 2 frames. |
| pull_free | R | Keep k00..k07 (k07_shoulder already puts the club on the shoulder); replace the last key k00_ready (1.5 s) with natural_pose.json, so he ends in the idle stance. Lower hands: grab-and-release overlap (they currently freeze). |
| stuck | R | Upper arms keep the tug as keyed. Add life to the frozen groups: knees bend 5-8 deg on each tug, spine leans back 3-4 deg with it, head shakes slightly, lower arms brace on the thighs and push, breathing in spine_03. Keep the 1.5 s loop. |
| hurt | R | Acting arms keep the flinch. Frozen legs/hips/spine_01/neck: knees dip ~6 deg at 0.08-0.33 s, spine_01 recoils 4 deg, neck snaps 8 deg and recovers; lower hands open/flinch. Start/end stay on k00_stuck (hurt is played while stuck). |
| death | R | Keep 0.38-4.5 s as is (traced + re-authored fall). Replace k0_ready at t=0 (rest T pose) with the natural stance so the death does not flash the T pose; give the shoulders a slump (shoulder_u 5-10 deg down from 0.4 s). |
No clip is K: every clip either starts/ends in the rest T pose or leaves a limb group frozen.

## 5. Seedance motion texts (after "Motion:"; the lead adds the fixed split-screen header). Not submitted, 0 credits.
**idle_n** (sheet nat_std, game clip `idle`, 110 words):
The four-armed giant stands ready in place on the spot and keeps his exact design, club and proportions. He breathes slowly and deeply, one breath every 3.5 seconds: chest and shoulders rise and fall. His weight shifts slowly from the left leg to the right and back over 7 seconds, knees soft, feet flat. The upper right hand keeps the club resting on his right shoulder; it bobs with each breath. The upper left arm hangs with a bent elbow and sways a little. The lower pair of arms hangs in front of the hips, fingers flexing, each hand at its own time. His head turns slowly left, then right.

**walk_n** (sheet nat_std, game clip `walk`, 107 words):
The four-armed giant walks in place on the spot with heavy, deliberate steps, one step every 0.7 seconds, and keeps his exact design and proportions. His knees bend, each foot lifts and stomps down flat. His torso sways over the planted foot, twists against the legs and dips on every footfall. The upper right hand keeps the club resting on his right shoulder; the club bounces with each step. The upper left arm swings forward and back opposite the left leg. The lower pair of arms swings loosely in front of the hips, opposite the legs and a little later. His head stays level and looks ahead.

Note for the lead: the last walk video came out at 1.96 s per step for a "one step per second" prompt; expect it slower
than 0.7 s and retime (the game clip stays 1.4167 s).

## Devlog
`docs/devlog/media_inbox/natural_cyclops/`: 00 old walk strip (T pose), 01 rest vs natural (front + three-quarter), 02 new sheet.
