# Devlog media plan (devlog media agent)

Every devlog image and clip, by chapter folder, so the writer can link them. Paths are relative to `docs/devlog/`
(link as `media/<folder>/<file>`). Images: JPEG <= 1600 px. Clips: MP4 <= 1080p, <= 40 MB, each with a poster JPEG of
the same name. Naming: `NN_name.jpg` single shot; `NN_before_x.jpg` + `NN_after_x.jpg` + `NN_pair_x.jpg` (labelled
BEFORE/AFTER card) for pairs; `NN_name.mp4` + `NN_name.jpg` poster for clips. Full captions with numbers and the
type of every file are in [MEDIA_INDEX.md](MEDIA_INDEX.md). Status: all files below exist (built and looked at).

## media/01_trailer: The trailer the game was built from
| File | Caption (short) |
|---|---|
| `01_trailer_v1.mp4` (+ `01_trailer_v1.jpg`) | The first HERCULES concept trailer |
| `02_trailer_v1_drafts.jpg` | The three 480p drafts of the first trailer |
| `03_keyframes.jpg` | The fix for the look: one opening keyframe per fight made with Nano Banana Pro from the two character sheets |
| `03_keyframe_cyclops.jpg` | Opening keyframe for the Cyclops fight (Nano Banana Pro, 16:9, from the Hercules + Cyclops sheets). |
| `03_keyframe_medusa.jpg` | Opening keyframe for the Medusa fight (Nano Banana Pro, 16:9, from the Hercules + Medusa sheets). |
| `03_keyframe_hydra.jpg` | Opening keyframe for the Hydra fight (Nano Banana Pro, 16:9, from the Hercules + Hydra sheets). |
| `04_before_look.jpg` | First trailer at 1.0 s (4K final, downscaled): side-on fight. |
| `04_after_look.jpg` | Keyframe-based Cyclops draft at 1.0 s (480p): camera behind the hero, giant boss. |
| `04_pair_look.jpg` | The LOOK change the owner asked for |
| `05_before_camera.jpg` | Hydra fight, prompt-only draft vs keyframe-based draft |
| `05_after_camera.jpg` | Hydra fight, prompt-only draft vs keyframe-based draft |
| `05_pair_camera.jpg` | Hydra fight, prompt-only draft vs keyframe-based draft |
| `06_boss_fights_review.mp4` (+ `06_boss_fights_review.jpg`) | The 47 s review cut of the three keyframe-based fight drafts |

## media/02_plan: What was planned and what it cost
| File | Caption (short) |
|---|---|
| `01_reference_bosses.jpg` | The target for the game: one frame per boss from the 47 s keyframe-based review cut |
| `02_higgsfield_credits.jpg` | Higgsfield credits for the game by purpose, from the job ledger |
| `03_method_diagram.jpg` | The owner's method in one card, with real Hercules run files: FRONT/SIDE sheet -> Seedance 480p reference video -> rig keyframed to match |

## media/03_characters_props: Character sheets, 3D candidates, props
| File | Caption (short) |
|---|---|
| `01_character_sheets.jpg` | The five character sheets the owner supplied (Hercules, Cyclops, Medusa, Hydra, Pegasus): the art style every 3D asset was generated in. |
| `02_hercules_sheet.jpg` | Hercules character sheet (owner-supplied, never modified). |
| `03_cyclops_sheet.jpg` | Cyclops character sheet (owner-supplied, never modified). |
| `04_medusa_sheet.jpg` | Medusa character sheet (owner-supplied, never modified). |
| `05_hydra_sheet.jpg` | Hydra character sheet (owner-supplied, never modified). |
| `06_pegasus_sheet.jpg` | Pegasus character sheet (owner-supplied, never modified). |
| `07_cropped_views.jpg` | One figure per image: front / side / back cut out of each sheet |
| `08_3d_candidates.jpg` | Two 3D candidates per character |
| `09_prop_concepts.jpg` | All 18 prop concept images |
| `10_props_contact_sheet.jpg` | all 14 cleaned environment props, front + three-quarter, red bar = 1.8 m person |
| `11_props_verify.jpg` | independent re-import of the 14 cleaned props |
| `12_before_olive_tree.jpg` | Olive tree: the first 3D generation |
| `12_after_olive_tree.jpg` | Olive tree: the first 3D generation |
| `12_pair_olive_tree.jpg` | Olive tree: the first 3D generation |
| `13_before_olive_concept.jpg` | Why the tree was bare: the first concept had thousands of small leaves |
| `13_after_olive_concept.jpg` | Why the tree was bare: the first concept had thousands of small leaves |
| `13_pair_olive_concept.jpg` | Why the tree was bare: the first concept had thousands of small leaves |
| `14_brazier_before_after.jpg` | brazier before/after: the flame was fused to the bowl, so it was cut by texture colour + an above-rim cut |
| `15_weapons.jpg` | Hercules front/side views next to the three weapon concepts |

## media/04_rigging: Rigging: raw mesh to rigged pose
| File | Caption (short) |
|---|---|
| `01_before_hercules_rig.jpg` | Higgsfield/Meshy raw mesh, 4 views (31,025 tris, 2048 px texture, 24 Meshy bones, armature scale 0.01) |
| `01_after_hercules_rig.jpg` | block test pose with sword (hand_r) and shield (forearm_l) sockets (sword 0.85 m 3,880 tris, shield 0.90 m 3,880 tris) |
| `01_pair_hercules_rig.jpg` | Hercules: raw Meshy 7 mesh vs rigged block pose with sword and shield sockets |
| `02_before_cyclops_rig.jpg` | the generated Cyclops |
| `02_after_cyclops_rig.jpg` | deform test: two-handed slam windup with the club, lower arms forward, head back - no bone heat, own geodesic distance weights |
| `02_pair_cyclops_rig.jpg` | Cyclops: raw mesh vs the rigged two-handed slam wind-up |
| `03_before_medusa_rig.jpg` | Higgsfield raw mesh of Medusa |
| `03_after_medusa_rig.jpg` | Deform test: tail swipe curl, 15-18 deg per tail joint, torso lean and twist |
| `03_pair_medusa_rig.jpg` | Medusa: raw mesh vs rigged tail-swipe curl |
| `04_before_hydra_rig.jpg` | the generated Hydra GLB before cleanup |
| `04_after_hydra_rig.jpg` | deform test: side heads strike / draw back / twist while neighbours stay put (5 edges stretched >3x median edge, none >6x) |
| `04_pair_hydra_rig.jpg` | Hydra: raw mesh vs rigged bite test (side heads strike, draw back, twist) |
| `05_before_pegasus_rig.jpg` | Higgsfield raw pegasus mesh, 4 views |
| `05_after_pegasus_rig.jpg` | Deform test: wings spread for gliding (one 100-deg rotation at each wing root) (wingspan 3.98 m, 33 of 105k edges stretched more than 2x) |
| `05_pair_pegasus_rig.jpg` | Pegasus: raw mesh vs rigged glide pose (wings spread) |
| `06_hercules_bones.jpg` | renamed skeleton over the cleaned mesh (blue = left, green = right, red dots = joints) (23 bones (22 deform + root), 1.90 m) |
| `07_cyclops_bones.jpg` | own 29-bone skeleton placed from numpy slices of the mesh |
| `08_medusa_bones.jpg` | Own 35-bone skeleton placed from vertex-cloud slices: spine, arms, 14-segment tail along the measured centre line, 6 snake bones |
| `09_hydra_bones.jpg` | the hand-built skeleton over the cleaned mesh: spine, tail, 4 legs, 9 necks found by slicing the mesh |
| `10_pegasus_bones.jpg` | Hand-placed skeleton over the cleaned mesh: joints taken from mesh cross-sections |
| `11_deform_hercules.jpg` | Hercules deform test sheet: 17 stress poses rendered headless after the rig fixes (art_src/chars/hercules/sheets). |
| `12_deform_cyclops.jpg` | Cyclops deform test sheet: 17 stress poses rendered headless after the rig fixes (art_src/chars/cyclops/sheets). |
| `13_deform_medusa.jpg` | Medusa deform test sheet: 10 stress poses rendered headless after the rig fixes (art_src/chars/medusa/sheets). |
| `14_deform_hydra.jpg` | Hydra deform test sheet: 12 stress poses rendered headless after the rig fixes (art_src/chars/hydra/sheets). |
| `15_deform_pegasus.jpg` | Pegasus deform test sheet: 11 stress poses rendered headless after the rig fixes (art_src/chars/pegasus/sheets). |
| `16_split_sheets.jpg` | Final FRONT / SIDE split sheets |
| `17_before_sheet_framing.jpg` | Split-sheet framing: the first Hercules sheet |
| `17_after_sheet_framing.jpg` | Split-sheet framing: the first Hercules sheet |
| `17_pair_sheet_framing.jpg` | Split-sheet framing: the first Hercules sheet |
| `18_before_hydra_sheet_framing.jpg` | FRONT (SIDE reference sheet in the rest pose, margins sized for head-down, fire sweep and stomp / 1280x720, 28.8 px per metre) |
| `18_after_hydra_sheet_framing.jpg` | Split reference sheet re-rendered with a motion envelope |
| `18_pair_hydra_sheet_framing.jpg` | Hydra sheet re-framed with a motion envelope for head-down, fire sweep and stomp |
| `19_hercules_arms_up_fix.jpg` | arms overhead: tunic flaps torn up by upper-arm weights vs repaired armholes (max edge stretch x6.0 -> tunic wings gone; 3,538 vertices re-weighted) |
| `20_hercules_review_skirt.jpg` | independent rig review: run stride |
| `21_hercules_lunge_stretch.jpg` | reviewer lunge pose with stretched edges |
| `22_hercules_skirt_fix.jpg` | review fix: sprint |
| `23_hercules_ride_fix.jpg` | review fix: ride straddle |
| `24_cyclops_knee_review.jpg` | independent rig review: walk back-leg |
| `25_cyclops_knee_fix.jpg` | cyclops leg rig fix, side close-ups of the same walk and kneel poses: before, the rig's 'knee' was really the ankle |
| `26_hydra_neck_seam_fix.jpg` | same test pose before/after: the touching necks are fused in the generated mesh, so spreading them pulled pink membranes; ripping the 547 fused … |
| `27_hydra_tenth_tube_fix.jpg` | Rig fix round 1: reviewer's head-down pose before/after. The headless 10th tube behind the centre neck |
| `28_hydra_head_down_bow.jpg` | New 'bow' head_down pose for the jaw weak point: spine pitch + front legs folded by IK |
| `29_medusa_armpit_fix.jpg` | Bug and fix: arms raised 95 deg; top = skin sheet left hanging under the arms |
| `30_medusa_review_seams.jpg` | reviewer stress test: textured |
| `31_medusa_weights_fix.jpg` | medusa weight repair after review: stretch heat before/after on a shrug+look and a 45 deg head turn |
| `32_pegasus_review_mane.jpg` | side close-ups rest vs head-lowered vs full downstroke + stretch map: mane smeared across the wing-root feathers |
| `33_pegasus_rigfix.jpg` | Pegasus skin fix round 1, before/after |
| `34_before_pegasus_stretch.jpg` | Edge-stretch heat map |
| `34_after_pegasus_stretch.jpg` | Same pose after spreading the weight change over 8 rings / 30 smoothing passes in the mane-wing and wing-flank contact zones |
| `34_pair_pegasus_stretch.jpg` | Pegasus edge-stretch heat map, neck bent 60 deg + turned: mane/wing-root tearing before, smoothed weights after |
| `35_ride_sheet.jpg` | FRONT |
| `36_ride_first_vs_final.jpg` | first combined build vs final: shins/feet inside the horse and the sword through the right wing, fixed by straddling wider |
| `37_ride_check_views.jpg` | checker's own views of ride.blend: 3/4 front right/left, top, and shield close-ups |

## media/05_animation_method: Proving the owner's method
| File | Caption (short) |
|---|---|
| `01_test_run.mp4` (+ `01_test_run.jpg`) | Method test 1 |
| `02_test_roll.mp4` (+ `02_test_roll.jpg`) | Method test 2: Seedance 2.5 dodge roll from the same sheet (480p, 10 s, 30 credits). The split layout held through a full roll. |
| `03_test_run_frames.jpg` | Frames of method test 1 (run in place) in a grid: front and side panels move together frame by frame. |
| `04_test_roll_frames.jpg` | Frames of method test 2 (dodge roll) in a grid. |
| `05_hercules_bones.jpg` | ak info: the Meshy Hercules rig learned from one picture (front+side, every joint named) (24 bones, 31025 tris, 0.9 s per call) |
| `06_seedance_calibration_overlay.jpg` | Seedance re-frames the split sheet |
| `07_pose_axes.jpg` | the pose format: angles in the view axes |
| `08_run_key0_compare.jpg` | one key of the run: target frame vs our render, 50% overlay and red/blue silhouette difference |
| `09_run_match_strip.jpg` | proof match: 0.708 s run loop |
| `10_proof_match.mp4` (+ `10_proof_match.jpg`) | First proof match of the toolkit, looped x4: Seedance run (top) vs our keyframed rig (bottom); 0.708 s loop, 5 keys, mean strip IoU 0.72. |
| `11_before_animkit_tools.jpg` | review run strip with the old tools: framing offset baked into root.loc then stripped by the in-place step, video frames sampled one frame late |
| `11_after_animkit_tools.jpg` | same 4 keys after the fix: framing moved to view_offset |
| `11_pair_animkit_tools.jpg` | Toolkit fix: framing offset moved out of the root motion and the strip sampled at the exact video frame; same 4 run keys score 0.600 -> 0.753 |
| `12_skirt_ground_aim.jpg` | animkit fixes on the real Hercules rig: skirt bones driven from the thighs |
| `13_independent_tester.jpg` | independent tester's first clip with only ANIM_PIPELINE.md: 4 keys |
| `14_before_green_key.jpg` | first pose with stock ak masks: green sheet background counted as character, flat wings scored 0.93 |
| `14_after_green_key.jpg` | 4 glide keys vs the video with green-key masks: wide V wings, tucked legs (IoU front/side 0.78/0.80, 0.75/0.80, 0.78/0.79, 0.76/0.80) |
| `14_pair_green_key.jpg` | Pegasus: the green sheet background was counted as horse, so every pose scored ~0.94 and IoU meant nothing; with green-key masks the glide keys … |
| `15_pegasus_green_key.jpg` | Rest pose scored with a green-key silhouette |

## media/06_reference_videos_clips: 33 reference videos, 41 clips
| File | Caption (short) |
|---|---|
| `01_reference_videos_contact.jpg` | All 33 Seedance 2.5 reference videos |
| `02_hercules_run_ref.mp4` (+ `02_hercules_run_ref.jpg`) | Hercules run reference video (Seedance 2.5 from the std sheet): running in place, front + side. |
| `03_before_hercules_run_fit.jpg` | Hercules run: first hand-posed keys against the video (red = video only, blue = ours only) (IoU 0.69 and 0.68 mean; gain over rest pose 0.04-0.05) |
| `03_after_hercules_run_fit.jpg` | the same keys plus two mirrored keys after ak fit (legs, arms, hand, framing) (IoU front 0.87-0.90, side 0.79-0.86) |
| `03_pair_hercules_run_fit.jpg` | Hercules run keys: first hand-posed guess vs after ak fit |
| `04_run_stride_before_after.jpg` | Hercules run before/after the stride fix: traced jog-on-the-spot vs authored running stride with flight phase |
| `05_hercules_run_match.mp4` (+ `05_hercules_run_match.jpg`) | Hercules run loop after the stride fix, looped: reference row above our rig (0.833 s loop at 24 fps). |
| `06_hercules_roll_ref.mp4` (+ `06_hercules_roll_ref.jpg`) | Hercules dodge-roll reference video. |
| `07_roll_fix_before_after.jpg` | Hercules dodge roll before/after the review fixes |
| `08_hercules_block_ref.mp4` (+ `08_hercules_block_ref.jpg`) | Hercules block reference video: shield up, braced, hold. |
| `09_hercules_block_first_try.jpg` | first hand-written block pose vs the video frame at 3.0 s: the shield lies flat like a tray (forearm twist missing) (IoU front 0.655 / side 0.439) |
| `10_hercules_block_shield_sideways.jpg` | mistake: aiming the forearm forward turned the shield face sideways (a shield's face is always square to the forearm) (IoU 0.660 / 0.656, wrong look) |
| `11_hercules_block_after_fit.jpg` | fixed: forearm across the chest, twist solved so the shield faces forward, then ak fit on spine/arms/legs (IoU front 0.873 / side 0.617) |
| `12_hercules_hit_match.mp4` (+ `12_hercules_hit_match.jpg`) | Hercules hit reaction, looped: reference above, our rig below (2.17 s, strip IoU 0.838, the best-matching Hercules clip). |
| `13_cyclops_slam_ref.mp4` (+ `13_cyclops_slam_ref.jpg`) | Cyclops slam reference video: lift, overhead wind-up, smash, club stuck. |
| `14_cyclops_slam_first_try.jpg` | first hand-typed poses vs the Seedance video |
| `15_cyclops_slam_strip.jpg` | finished slam clip |
| `16_cyclops_sweep_before_after_fit.jpg` | wind-up keys: hand-typed poses |
| `17_cyclops_sweep_match.mp4` (+ `17_cyclops_sweep_match.jpg`) | Cyclops club sweep, looped: reference above, our rig below (17 keys, 2.5 s). |
| `18_cyclops_death_ref.mp4` (+ `18_cyclops_death_ref.jpg`) | Cyclops death reference video |
| `19_cyclops_death_match.mp4` (+ `19_cyclops_death_match.jpg`) | Cyclops death: reference above, our rig below (11 traced keys + 10 grounded in-betweens, 4.5 s). |
| `20_medusa_gaze_ref.mp4` (+ `20_medusa_gaze_ref.jpg`) | Medusa gaze reference video: wind-up, petrifying stare, thrust. |
| `21_medusa_gaze_first_guess.jpg` | first hand-written keys |
| `22_medusa_gaze_match.mp4` (+ `22_medusa_gaze_match.jpg`) | Medusa gaze: reference above, our rig below (9 keys, 4.25 s, strip IoU 0.80). |
| `23_medusa_slither_ref.mp4` (+ `23_medusa_slither_ref.jpg`) | Medusa slither reference video: the tail swings side to side as she moves. |
| `24_medusa_slither_rest_vs_video.jpg` | rest pose vs video 1.0 s / 2.0 s: red = her tail swinging out to the sides in the video, which the straight rest tail lacks |
| `25_medusa_slither_match.mp4` (+ `25_medusa_slither_match.jpg`) | Medusa slither loop, looped: travelling wave down the 14-segment tail (2.0 s, strip IoU 0.82 front / 0.86 side). |
| `26_medusa_tail_swipe_strip.jpg` | Medusa tail_swipe: Seedance reference |
| `27_hydra_fire_sweep_ref.mp4` (+ `27_hydra_fire_sweep_ref.jpg`) | Hydra fire-sweep reference video (the prompt asks for no fire effects; the game adds the flames). |
| `28_before_hydra_fire_sweep_fit.jpg` | first hand-written centre-neck poses vs the video |
| `28_after_hydra_fire_sweep_fit.jpg` | same keys after aiming the neck by 3D direction + ak fit (rx/ry) + an IoU grid on side-neck spread/lean (IoU 0.65-0.69, gain over rest +0.01..+0.05) |
| `28_pair_hydra_fire_sweep_fit.jpg` | Hydra fire sweep keys: necks bent at the top vs aimed from the base |
| `29_hydra_fire_sweep_match.mp4` (+ `29_hydra_fire_sweep_match.jpg`) | Hydra fire sweep: reference above, our rig below (5.0 s, 8 keys). |
| `30_hydra_walk_ref.mp4` (+ `30_hydra_walk_ref.jpg`) | Hydra walk reference video (in place). |
| `31_hydra_walk_match.mp4` (+ `31_hydra_walk_match.jpg`) | Hydra walk cycle, looped: reference above, our rig below (2.17 s, 27 keys, mean IoU 0.877). |
| `32_hydra_walk_inbetweens.jpg` | Hydra walk in-betweens of the IK walk |
| `33_hydra_death_neck_through_floor.jpg` | mistake caught by a per-frame floor scan: between two keys a right-side head swung 0.48 m under the floor at 4.30 s |
| `34_hydra_idle_video_motion.jpg` | how little the reference moves: video silhouette at 1.0 s |
| `35_pegasus_fly_ref.mp4` (+ `35_pegasus_fly_ref.jpg`) | Pegasus fly reference video: wing beats on the soft green sheet. |
| `36_pegasus_fly_strip.jpg` | Pegasus fly loop: Seedance reference |
| `37_pegasus_glide_match.mp4` (+ `37_pegasus_glide_match.jpg`) | Pegasus glide loop, looped: reference above, our rig below (3.0 s, strip IoU 0.75-0.81). |
| `38_ride_ref.mp4` (+ `38_ride_ref.jpg`) | The ride reference video: real rigged Hercules seated on the real Pegasus |
| `39_ride_proof_close.jpg` | Hercules ride loop vs the Seedance ride video, rider close-ups |
| `40_ride_proof_strip.jpg` | 8 phases of one wing beat, video row over our render row |
| `41_ride_loop_side.jpg` | independent check: Hercules ride loop on Pegasus, side view, 6 frames of the 1.5 s loop |

## media/07_game: The Godot game
| File | Caption (short) |
|---|---|
| `01_core_v1_test_fight.jpg` | first playable core loop: hero |
| `02_title_screen.jpg` | title screen drawn entirely in code |
| `03_weak_point_before_after.jpg` | core review fix: exposed weak point was a faint additive glow on sand; now a saturated orange core with an ink rim plus a HUD ring+arrow marker, … |
| `04_cyclops_fight_sheet.jpg` | Cyclops fight v1 on the grey-box stand-in: sweep cone warning, tracked slam circle, club stuck with the forearm weak point lit, death + LABOR COMPLETE |
| `05_cyclops_sweep_warning.jpg` | Sweep warning from the chase camera: red 150 degree cone on the packed earth, colonnades and sea behind the 8 m giant |
| `06_cyclops_stuck_weak_point.jpg` | Club stuck after the slam: crack decal, orange forearm weak point open for 2 sword hits (weak point radius 0.85 m kept 0.9-2.4 m above the floor) |
| `07_cyclops_fix_club_planted.jpg` | review fix: stand-in club now driven into the ground at the crack while stuck, forearm glow sits on the club |
| `08_cyclops_fix_enrage.jpg` | review fix: stronger enrage tint |
| `09_medusa_fight_beats.jpg` | Medusa v1 |
| `10_medusa_arena.jpg` | Sanctuary courtyard: veined marble r 28 m, inlaid rings, 8.1 m colonnade at r 36.6, statues in the bays, 11 m blue-grey wall behind the north … |
| `11_medusa_fix_gaze_lock.jpg` | review fix: gaze fan before/after the 0.5 s direction lock |
| `12_medusa_real_model_lean.jpg` | first fight with the real rigged Medusa: procedural lean |
| `13_hydra_fire_standin.jpg` | Hydra fire sweep on the grey-box stand-in: the hero waits at the shoulder outside the 140 deg arc while the stream rakes the basalt shelf |
| `14_hydra_fire_real_mesh.jpg` | Same moment with the real rigged Hydra mesh |
| `15_hydra_stomp_ring.jpg` | Stomp warning: red ring decal around the near forefoot during the 0.9 s lift, white flash at impact (ring 0.8-5.0 m, 35 dmg, unblockable) |
| `16_hydra_fix_review_sheet.jpg` | Hydra after the review fixes: darker sunless sky + black basalt, lower lock camera at the shoulder |
| `17_before_fire_colour.jpg` | Mistake: the fire read as pale yellow smoke puffs |
| `17_after_fire_colour.jpg` | Fix: vertex_color_is_srgb = true on the particle materials + fog off: orange-red flames with a hot yellow core (one flag per material, no shader) |
| `17_pair_fire_colour.jpg` | Hydra fire: pale yellow smoke puffs vs orange-red flames after one flag per particle material (vertex_color_is_srgb) |
| `18_before_hydra_lock_framing.jpg` | lock camera on the real 14.4 m Hydra |
| `18_after_hydra_lock_framing.jpg` | same fight after sampling 20 real top points of the mesh: whole Hydra framed at the jaw strike, hero's feet above the boss bar in every frame |
| `18_pair_hydra_lock_framing.jpg` | Lock-on camera on the real 14.4 m Hydra: horns cut off vs whole Hydra framed |
| `19_before_storm_wall.jpg` | bug: storm wall's far side blended over its near side and the sea painted over its lower half (storm radius 176 m, camera 260 m out) |
| `19_after_storm_wall.jpg` | fix: cull back faces + draw after the sea (render_priority 1); Pegasus turns away 133 m from the centre (closest approach 123 m to an 88 m wall) |
| `19_pair_storm_wall.jpg` | World: storm wall drawn wrong (far side over near side, sea painted over it) vs fixed (back faces culled, drawn after the sea) |
| `20_world_first_run_bug.jpg` | first windowed run: home plateau top missing |
| `21_world_home_spawn.jpg` | home plateau as spawned: sign with next goal + controls, Pegasus waiting, medusa pillar + hydra storm on the horizon |
| `22_world_trophies.jpg` | trophy pedestals with all three bosses beaten (horn, stone snake head, club piece) in front of the temple (3 pedestals, 1.1 m) |
| `23_world_flight_volcano.jpg` | flying at the open Volcano Isle: lava rivers, smoke plume, pillar of light, landing ring (cone 88 m tall, ring r 28 m at 42 m) |
| `24_world_flight_sanctuary.jpg` | a beaten island: calm, white ring kept so the fight can be replayed (ring r 26 m) |
| `25_world_real_rider.jpg` | real Pegasus + Hercules rigs (rest pose, clips not in yet): rider hips glued to the saddle bone each frame (pegasus 43 bones, hercules 29) |
| `26_world_fix_flight_camera.jpg` | review fix: chase camera raised |
| `27_world_fix_home_sign.jpg` | review fix: home sign rewritten to 3 big lines |
| `28_world_ending_card.jpg` | ending card after the Hydra (shown once, then free flight) (6 lines, 11 s hold) |
| `29_cyclops_fight.mp4` (+ `29_cyclops_fight.jpg`) | A 22 s Godot Movie Maker capture of the Cyclops fight with the game's sound |
| `30_real_cyclops_real_model_stuck.jpg` | first fight with the real rigged Cyclops GLB |
| `31_real_cyclops_probe_chase_cam_4clips.jpg` | assembly probe through CharacterVisual.create: idle, sweep at impact, slam at impact, stuck, from a chase-camera position |
| `32_real_hercules_ingame_block.jpg` | First in-engine Hercules from the assembled GLB: block_idle, lion shield face out on the left forearm, sword in the right hand, toon bands + ink … |
| `33_real_hydra_ingame_fire_sweep.jpg` | first in-engine frame of the assembled, animated Hydra |
| `34_real_hydra_probe_4clips.jpg` | loader probe through CharacterVisual.create("hydra"): idle, fire_sweep, head_down |
| `35_real_medusa_ingame_gaze_windup.jpg` | first in-engine frame of the real rigged + animated Medusa in her arena: gaze windup, green fan decal, hero |
| `36_real_medusa_probe_4clips.jpg` | loader probe |
| `37_real_pegasus_ingame_q34.jpg` | Pegasus in Godot through CharacterVisual.create("pegasus"), fly downstroke, Hercules seated on the saddle socket |
| `38_real_pegasus_chase_rider_clear.jpg` | game chase camera |

## media/08_sound: Sound
| File | Caption (short) |
|---|---|
| `01_raw_vs_game_waveforms.jpg` | 8 sounds before/after processing |
| `02_cyclops_fight_audio_track.jpg` | audio track of a 22 s Movie Maker capture of the Cyclops fight with every logged sound start marked |

## media/09_integration_playtest: Real models in the game, play-test, final check
Status: all files below exist (built and looked at by the final-pass media agent). Full captions with numbers in MEDIA_INDEX.md.
| File | Caption (short) |
|---|---|
| `01_first_real_models.jpg` | First real models in Godot, one per character: Hercules, Cyclops, Medusa, Hydra, Pegasus + rider |
| `02_before_camera.jpg` / `02_after_camera.jpg` / `02_pair_camera.jpg` | Lock-on camera 6.5 m vs 3.7 m behind the hero (hero ~20% -> ~36% of frame height), same view |
| `03_before_medusa_scale.jpg` / `03_after_medusa_scale.jpg` / `03_pair_medusa_scale.jpg` | Medusa before vs after the x1.5 scale (+ closer stalk), same seed and game time |
| `04_cyclops_fight.jpg` | Cyclops fight, final build: sweep warning, slam dodged, forearm strike, LABOR COMPLETE |
| `05_medusa_fight.jpg` | Medusa fight, final build: gaze wind-up, gaze reflected, neck cut, death |
| `06_hydra_fight.jpg` | Hydra fight, final build: inhale warning, fire sweep, jaw strike, LABOR COMPLETE |
| `07_home_flight_rider.jpg` | Home isle: mount, lift-off, flight with the rider, landing ring |
| `08_title_overlays.jpg` | Title screen, sea + island title cards, LABOR COMPLETE, DEFEATED, ending card |
| `09_hydra_colour_fix.jpg` | Hydra colour fix: pink bite pillar + pink belly -> ember circle, violet legs, crimson belly |
| `10_defeated_card_fix.jpg` | DEFEATED card fix: card + boss bar covered the fallen hero -> bar hidden, card later in the upper third |
| `11_ref_vs_game_cyclops.jpg` | key_cyclops.png vs the game's sweep wind-up (close match) |
| `12_ref_vs_game_medusa.jpg` | key_medusa.png vs the game's gaze wind-up |
| `13_ref_vs_game_hydra.jpg` | key_hydra.png vs the game's Hydra guard |
| `14_clip_cyclops_fight.mp4` (+ `14_clip_cyclops_fight.jpg`) | 22 s Movie Maker clip of the final Cyclops fight with sound (bot, 0 hits taken) |
| `15_clip_flight.mp4` (+ `15_clip_flight.jpg`) | 18 s Movie Maker clip: mount at home, flight with the rider, landing at the Quarry Isle |
| `16_lead_look_sheet.jpg` | The lead's look check after integration-2 ("Medusa does not tower") |
| `17_qa_playtest_sheet.jpg` | The visual play-tester's contact sheets (before the QA fixes; 19 findings, 9 major) |
| `18_editor_vs_app.jpg` | Editor run vs the exported Hercules.app: identical frames |
| `19_cyclops_death_club_fix.jpg` | Cyclops death: the falling club swept the frame -> dropped out of view |
| `20_hydra_fire_blobs_before.jpg` | Hydra fire bug BEFORE the fix: black/orange particle blobs, bright scorch (no same-view after frame) |
| `21_animation_fixes.jpg` | Animation fixes from the finalize pass (Cyclops, Hercules, Hydra, Medusa, Pegasus) |
| `22_integrators_sheet.jpg` | What the four integrators delivered: Cyclops, Medusa, Hydra, ride wing beat |
| `23_medusa_x15_sheet.jpg` | Medusa x1.5: start, wind-up, reflect, stun, neck cut, petrified hero |
| `24_hydra_lock_live_top.jpg` | Hydra lock camera: rearing neck cut off -> camera follows the live pose |

## media/11_polish: Polish of the nine open items (Mon Nov 23, "Polish them now")
Status: all files below exist (built and looked at by the devlog-3 media agent). Full captions in MEDIA_INDEX.md. Sources: media_inbox/{core,cyclops,medusa,hydra}_polish2 (fixers, re-fixers after the independent reviews) and the first-use freeze numbers in docs/notes/freeze_fix.md. The natural-integrate frames (integrate2_*) are in 12_natural_animations because they show the new natural clips.
| File | Caption (short) |
|---|---|
| `01_sword_carry_variants.jpg` | Sword carry from behind: the clip's own angle vs four aim directions in six moves; row A chosen |
| `02_sword_before_after_ingame.jpg` | The same five moments in the game, before and after the sword carry (blade on screen 36 -> 124 px in idle) |
| `03_transitions_before_after.jpg` | Clip changes at 30 fps before/after the real-time skeleton cross-fade (worst one-frame bone turn 156-166 -> 53 deg) |
| `04_refix_strike_before.jpg` | Reviewer's strip, BEFORE the re-fix: the sword flicks on its own and the legs spin 85 deg in 3 frames at a strike out of the run |
| `05_refix_roll_before.jpg` | Reviewer's strip, BEFORE the re-fix: side roll settles into idle, then runs 4 frames later |
| `06_refix_transitions_after.jpg` | AFTER the re-fix: circling strike, run strike, shield raise, roll straight into the run |
| `07_victory_card_cyclops_hydra.jpg` | LABOR COMPLETE now waits for the fall and sits in the upper third (Cyclops 2.95 s, Hydra 2.35 s) |
| `08_victory_card_medusa.jpg` | The same for Medusa (card after 1.3 s) |
| `09_curb_before_after.jpg` | Quarry rim: the white curb no longer fills the bottom of the frame (bottom-quarter cover 0.67 -> 0.07) |
| `10_curb_8angles_before.jpg` / `11_curb_8angles_after.jpg` | 8 rim angles before / after the near fade (mean cover 0.547 -> 0.109) |
| `12_stuck_club_before_after.jpg` | Strike on the stuck club's forearm: the club no longer fills the lower-right quarter (0.53 -> 0.28) |
| `13_stuck_club_refix_before_after.jpg` | Re-fix after the review: the club had vanished leaving its shadow; now the upper club stays solid |
| `14_cyclops_gait_turn_strip.jpg` / `15_cyclops_gait_refix_strip.jpg` | Cyclops walks at ground speed, eases into attacks and turns on the spot stepping (fix, then re-fix) |
| `16_cyclops_defeated_view_after.jpg` | Cyclops lose run: death and DEFEATED with no curb band at the bottom |
| `17_hydra_inhale_before_after.jpg` | Inhale warning: flat orange fill vs glowing cracks, embers and heat fronts |
| `18_hydra_inhale_before_sheet.jpg` | The old inhale, 8 frames |
| `19_hydra_inhale_refix_before_after.jpg` / `20_hydra_inhale_refix_strip.jpg` | Re-fix after the review: even crack net -> white-hot fronts running toward the head |
| `21_hydra_move_strip.jpg` / `22_hydra_move_refix_strip.jpg` | Hydra approach, stepping turn, eased stop before the inhale (fix, then re-fix) |
| `23_medusa_turn.jpg` / `24_medusa_turn_crop.jpg` | Medusa turning ~120 deg: statue rotation before, slither clip matched to the turn after |
| `25_medusa_approach.jpg` | Stalk: she gathers speed and brakes into 7.7 m instead of full speed and a hard stop |
| `26_medusa_gaze.jpg` / `27_medusa_tail.jpg` | Gaze and tail-swipe starts/ends blended (0.12 -> 0.25 s; recovery no longer cut) |
| `28_medusa_hair.jpg` / `29_medusa_hair_polish3.jpg` | Snake hair: brown/yellow patches repainted green (polish 2, then the re-fix) |
| `30_medusa_moves_polish3.jpg` | Medusa after the review re-fix: turn, gaze end, backing off, tail-swipe start |
| `31_first_use_freeze_chart.jpg` | First-use freeze: worst frame per fight on a fully cold start, before vs after (from freeze_fix.md) |

## media/12_natural_animations: "Make every movement natural" (Mon Nov 23)
Status: all files below exist except 74 (see its row); built and looked at by the devlog-3 media agent. Full captions in MEDIA_INDEX.md. Sources: media_inbox/lead_natural (the lead's before/after clip sheets, in-game strips), natural_* (stances, sheets), rebase_*, assemble2_*, natural_review_pegasus, integrate2_*, the reference videos in art_src/chars/*/clips/*/ref.mp4, tools/clip_motion.py (before file + a fresh run) and two new gameplay clips recorded off-screen with tools/godot_bg/gdwin.
| File | Caption (short) |
|---|---|
| `01_moving_joints_chart.jpg` | Moving joints per clip, before vs after the pass (tools/clip_motion.py, a joint turning < 3 deg in a whole clip = frozen) |
| `02_before_hercules_all_clips.jpg` / `03_after_hercules_all_clips.jpg` / `04_pair_hercules_all_clips.jpg` | Every Hercules clip, 8 poses each, before vs after (same tool and camera) |
| `05_..07_` `cyclops`, `08_..10_` `medusa`, `11_..13_` `hydra`, `14_..16_` `pegasus` | The same before / after / pair for each character (`NN_before_<id>_all_clips.jpg`, `NN_after_<id>_all_clips.jpg`, `NN_pair_<id>_all_clips.jpg`) |
| `17_after_hercules_from_behind.jpg` | Seven new Hercules clips seen from behind like the game camera |
| `18_rest_vs_natural_hercules.jpg` .. `23_rest_vs_natural_pegasus.jpg` | Rest pose (what every old reference video started from) vs the new natural stance: 18 hercules, 19 cyclops, 20 medusa, 21 hydra (3/4), 22 hydra (front), 23 pegasus |
| `24_sheet_old_vs_new_hercules.jpg` | Old split sheet (rest A-pose) above the new natural-stance sheet |
| `25_new_sheets_all.jpg` | The five new FRONT / SIDE sheets the nine new Seedance videos started from |
| `26_cyclops_walk_ref_old_vs_new.jpg` | Cyclops walk reference video: old (T pose, club straight up) vs new (club on the shoulder), same second |
| `27_clip_cyclops_walk_ref_old_vs_new.mp4` (+ `.jpg`) | 6 s side by side of the two Seedance walk videos |
| `28_cyclops_old_walk_strip.jpg` / `29_hydra_before_strips.jpg` | BEFORE strips: the old Cyclops walk and the old Hydra walk/bite/stomp/fire with frozen heads |
| `30_rebase_cyclops_slam.jpg` .. `39_rebase_pegasus_fly.jpg` | Re-based clips before/after: 30 cyclops slam, 31 cyclops pull_free, 32 hercules block_idle, 33 hercules strafe_l, 34 hydra bite, 35 hydra fire_sweep, 36 medusa gaze, 37 medusa tail_swipe, 38 pegasus glide, 39 pegasus fly |
| `40_cyclops_idle_walk_before_after.jpg` / `41_cyclops_after_strip.jpg` / `42_clip_cyclops_idle_walk_before_after.mp4` | Cyclops in Godot, old vs new GLB (the assembler's images and side-by-side movie) |
| `43_hercules_idle_before_after.jpg` / `44_hercules_run_before_after.jpg` / `45_hercules_run_attack_chase.jpg` / `46_clip_hercules_before_after.mp4` | Hercules idle and run, old vs new, in the game |
| `47_hydra_idle_before_after.jpg` / `48_hydra_walk_before_after.jpg` / `49_clip_hydra_idle_walk_before_after.mp4` | Hydra idle (was 0 of 76 joints moving) and turning walk, before vs after |
| `50_medusa_idle_before_after.jpg` / `51_medusa_slither_before_after.jpg` / `52_clip_medusa_slither_idle_before.mp4` / `53_clip_medusa_slither_idle_after.mp4` | Medusa idle and slither, before vs after |
| `54_pegasus_idle_before_after.jpg` / `55_clip_pegasus_idle_before_after.mp4` / `56_pegasus_flight_before_after.jpg` / `57_clip_pegasus_flight_before_after.mp4` | Pegasus idle and flight with the rider, before vs after |
| `58_pegasus_idle_hind_skate_review.jpg` | Naturalness review finding: the new Pegasus idle's hind hooves slide along the floor |
| `59_ingame_cyclops_approach_after.jpg` / `60_ingame_medusa_approach_after.jpg` | The lead's in-game strips: Cyclops and Medusa walking up to a standing Hercules after the pass |
| `61_home_idle_v1_vs_v2.jpg` | AI mistake + fix: the first new Hercules idle was too quiet from behind (top) vs after the clip fix (bottom) |
| `62_cyclops_natural_fight.jpg` .. `72_home_landing_settle.jpg` (72 also shows the riderless-landing bug) | Natural clips integrated in each fight: 62 cyclops fight, 63 hero idle/run/circling, 64 hero attack recovery, 65 hydra turn-walk, 66 hydra fire chain, 67 medusa gaze, 68 medusa death join, 69/70 medusa clips (`69_clip_medusa_stalk_turn_backoff.mp4`, `70_clip_medusa_death_from_stun.mp4`), 71 mount hop, 72 home landing |
| `73_clip_cyclops_approach_after.mp4` (+ `.jpg`) | New gameplay clip (gdwin, off-screen): the Cyclops walks up to a standing Hercules, 12 s (he is mostly hidden behind Hercules from this camera) |
| ~~`74_clip_cyclops_approach_old_vs_new.mp4`~~ | NOT MADE: the old fight clip 09/14 covers game time 16.0-37.8 s (winning bot), the new clip 0-12 s, so no same-seconds "before" exists; use 42 for old vs new walk |
| `75_clip_home_idle_pegasus.mp4` (+ `.jpg`) | New gameplay clip: the home island start, Hercules's new idle and Pegasus's idle |

## 13_owner_feedback (Chapter 13, made by the devlog agent of `hercules-feedback-2`)
| File | What |
|---|---|
| `01`-`03` | His play-test, one frame every 10 s (0-4 min, 4-8 min, 16-18 min) |
| `04`-`18` | Frames and sheets from his recording per point: sword (04-06), mount and dismount (07-09), flight and Pegasus (10-12), empty islands (13), hits (14), clipping (15-17), the Hydra fight he praised (18) |
| `19`-`30` | Four BEFORE / AFTER pairs with cards: the first seconds of a flight (21), the Quarry Isle approach (24), a Cyclops hit (27), the stuck club (30) |
| `31`-`42` | The fixers' and re-fixers' sheets (sword, flight and mount, dismount, creatures, Pegasus v3 -> v5, strike effects, clipping) |
| `43`-`49` | Final check 3: each point beside his frames |
| `50`-`57` | Clips from his recording (720p, his voice and game sound): mount snap, first flight, sword fight, Pegasus off-screen, dismount, "the panning", his verdict in two parts |
| `58`-`64` | Clips now (final check movies, no sound): steering probe, mount and take-off, dismount, the Cyclops on his island, Cyclops hits, slow-motion hits on the Cyclops and the Hydra |
