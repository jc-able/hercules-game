# Hercules · Video outline

Plan for the devlog videos, built from DEVLOG.md (chapters), PROMPTS.md (quotes) and MEDIA_INDEX.md (files). Media paths are
relative to this folder. Numbers come from the chapters; say "about" where the chapter says "about". Episode 5 covers
Chapters 9-10 (integration, the AI play-test, the Mac app, the last look). Episode 6 covers Monday morning (Chapters 11-12):
"Polish them now" and the natural-animation pass, and ends on JC's own play-test of the rebuilt app. Episode 7 covers
Chapter 13: that play-test (he recorded it with his voice, 18 minutes), his six small points and how the agents fixed them.

**Through-line:** "I pasted one prompt for a trailer, then one message for a whole game, and a team of AI agents generated,
rigged and animated every character from my own videos-as-reference method, while a bot played the boss fights."

## Series (7 episodes)

### Episode 1 · "The trailer was the wrong game" (Chapters 1-2) · 8-10 min
- **Hook (first 15 s):** the 4K trailer playing (`media/01_trailer/01_trailer_v1.mp4`), freeze on the side-on Cyclops, my
  line from P02 on screen: "it's not what I'm intending the game to look like". Cut to the same boss from behind, towering over
  Hercules (the prompt asked for five times his height) (`media/01_trailer/04_pair_look.jpg`, wipe).
- **Beats:**
  1. The pasted prompt (P01) scrolling; "19 minutes, 555 credits, 4K" (numbers on screen).
  2. What it got wrong, in Claude's own list: sidestep not roll, hidden sword hit, stone maul.
  3. My feedback (P02 quote). The first fix: CAMERA / SCALE / MOVEMENT blocks. Result: camera too far
     (`media/01_trailer/05_pair_camera.jpg`, wipe).
  4. The real fix: an opening picture per fight (`media/01_trailer/03_keyframes.jpg`). The 47 s review cut
     (`media/01_trailer/06_boss_fights_review.mp4`): "this is the target."
  5. Honest moment: 420 credits spent on a 4K I never wanted; Claude wrote down "draft before 4K" and offered the finals
     (1,260) instead of buying them. I never answered, and it never bought them.
  6. The game request (P03 key lines on screen: "don't stop until the game is completely built", the Seedance method,
     "document the entire process"). Ultracode on.
  7. The plan: the contract page, the boss tables, 12 workflows (`media/02_plan/01_reference_bosses.jpg`,
     `media/02_plan/03_method_diagram.jpg`).
- **Numbers on screen:** 555 + 280 credits for the trailer; 47 s reference; 4 messages from me in total; 0 questions back.
- **Clips to record myself:** my reaction watching the 4K trailer; scrolling my pasted prompt; the Ultracode toggle.
- **Closing tease:** "It didn't ask me a single question. It just started generating ten 3D models."

### Episode 2 · "Ten 3D models, two winners each, and a bald tree" (Chapters 3-4) · 10-12 min
- **Hook:** Medusa from two generators side by side: one tail straight like my sheet, one bent into a J
  (`media/03_characters_props/08_3d_candidates.jpg`). "One of these is wrong. The AI caught it."
- **Beats:**
  1. Sheets cut into single views (`07_cropped_views.jpg`), why (image-to-3D fuses everything in the frame).
  2. Ten jobs, 267 credits, 5 minutes. The zsh trap that silently dropped nine of them (funny AI moment).
  3. The picks per character and why (table from Chapter 3).
  4. Props: concept image then 3D (`09_prop_concepts.jpg`, `10_props_contact_sheet.jpg`); the bald olive tree and the
     "solid leaf clumps" fix (`12_pair_olive_tree.jpg`, wipe); the brazier's fused flame (`14_brazier_before_after.jpg`).
  5. Rigging: Hercules arrives with a skeleton; the monsters get hand-built ones (`media/04_rigging/01_pair_hercules_rig.jpg`
     ... `05_pair_pegasus_rig.jpg`, `09_hydra_bones.jpg`).
  6. The reviewer agent breaks things: Cyclops knees at the ankles (`25_cyclops_knee_fix.jpg`), the Hydra's ghost neck
     (`27_hydra_tenth_tube_fix.jpg`), Hercules's skirt tearing in a run (`22_hercules_skirt_fix.jpg`).
- **Numbers on screen:** triangles per character (31,025 / 41,209 / 70,000 / 69,992 / 69,986); bones 29 / 29 / 35 / 76 / 43;
  2 of 5 rigs failed review; Hydra 14.4 m tall.
- **Clips to record myself:** spinning each GLB in a viewer; a phone shot of my screen while the rig agents' images arrive.
- **Closing tease:** "Now the hard part: making them move using my method."

### Episode 3 · "My animation method, tested on 33 AI videos" (Chapters 5-6) · 12-15 min
- **Hook:** the ride video (`media/06_reference_videos_clips/38_ride_ref.mp4`): Hercules on Pegasus, front and side, wings
  beating, then our rig matching it (`39_ride_proof_close.jpg`). "Every animation in this game started as a video like this."
- **Beats:**
  1. The method card (`media/02_plan/03_method_diagram.jpg`) with my words from P03.
  2. The two test videos (`media/05_animation_method/01_test_run.mp4`, `02_test_roll.mp4`): "60 credits to find out if it works. It does."
  3. Seedance zooms 21 % and moves the divider; the toolkit lines it back up (`06_seedance_calibration_overlay.jpg`).
  4. How a pose is scored: target / ours / overlay / difference (`08_run_key0_compare.jpg`). Explain IoU in one sentence.
  5. 33 videos, 6 at a time (26 refused on the first try); the content filter on the Cyclops death and the gentler wording.
  6. 22 animators at once (wave 2). Per-character score table (Chapter 6).
  7. Where Seedance lies: treadmill runs (`04_run_stride_before_after.jpg`), the Hydra's 1.5x neck
     (`29_hydra_fire_sweep_match.mp4`), the frozen side panel, the wrong head biting, Medusa's jump cut.
  8. AI mistakes caught by AI: the Hydra head 0.48 m under the floor (`33_hydra_death_neck_through_floor.jpg`), the shield
     held like a tray.
- **Numbers on screen:** 33 videos x 30 credits; 41 clips; IoU ranges per character (0.55-0.922 overall); 22 agents at once.
- **Clips to record myself:** a 10 s reference video playing full-screen next to my narration; the Blender result of one
  clip turning (only on a COPY of the blend, never the working file).
- **Closing tease:** "The animations exist. But does the game work?"

### Episode 4 · "A bot beat every boss before the animations existed" (Chapters 7-8) · 10-12 min
- **Hook:** `media/07_game/29_cyclops_fight.mp4` with sound, then the core v1 grey-box fight
  (`01_core_v1_test_fight.jpg`). "The first version of this fight was won by a bot, on grey boxes, in 15.6 seconds."
- **Beats:**
  1. Core: camera behind the hero, lock-on, roll, shield, glances; the title screen drawn in code (`02_title_screen.jpg`).
  2. Each boss on stand-ins: warnings and weak points (`05_cyclops_sweep_warning.jpg`, `09_medusa_fight_beats.jpg`,
     `14_hydra_fire_real_mesh.jpg`).
  3. Reviewer finds: the bite you could block facing away, the boss that kept fighting after you died, rings that landed
     you by themselves.
  4. One checkbox: fire that looked like smoke (`17_pair_fire_colour.jpg`, wipe). The storm wall (`19_pair_storm_wall.jpg`).
     Framing a 14.4 m Hydra (`18_pair_hydra_lock_framing.jpg`).
  5. The world: home island, flight, islands, ending card (`21_world_home_spawn.jpg`, `23_world_flight_volcano.jpg`,
     `28_world_ending_card.jpg`).
  6. Sound: 62 sounds for about 92 credits, the 294 Hz "lyre" (`media/08_sound/01_raw_vs_game_waveforms.jpg`), warnings on
     the same frame as the red circle (`02_cyclops_fight_audio_track.jpg`).
- **Numbers on screen:** bot win times (Cyclops 34-37 s, Medusa 22.5-23.4 s, Hydra about 84 s); 38 GDScript files / 11,125
  lines at the time; -14.8 LUFS.
- **Clips to record myself:** me playing a fight with the Xbox controller (screen + phone camera on my hands); the flight.
- **Closing tease:** "Next: the real models go in, and I get to play it."

### Episode 5 · "Six AI play-testers, then me" (Chapters 9-10) · 12-15 min
- **Hook (first 15 s):** the final Cyclops fight with sound (`media/09_integration_playtest/14_clip_cyclops_fight.mp4`),
  freeze on LABOR COMPLETE, then hard cut to my hands on the Xbox controller: "A bot beat this whole game from the title
  screen to the ending without a single error. Now it's my turn." Optional cold open instead: the Medusa before/after
  wipe (`03_pair_medusa_scale.jpg`) with "She was supposed to tower."
- **Beats:**
  1. 8:40 PM: every animation exists, the game still shows grey boxes. The first real models in Godot
     (`01_first_real_models.jpg`).
  2. The agents' own tool bug: every clip after the first started at the wrong height. Medusa sank 0.354 m through the
     floor, Pegasus dropped 22 cm on every wing beat (`21_animation_fixes.jpg`). Two of five characters failed review.
  3. Real models in every scene, and the camera comes in close behind Hercules: 6.5 m -> 3.7 m
     (`02_pair_camera.jpg`, wipe), hero about 20 % -> 36 % of the screen height. Hercules rides Pegasus for real
     (`media/09_integration_playtest/15_clip_flight.mp4`).
  4. The lead looks for itself: "Medusa does not tower" (`16_lead_look_sheet.jpg`).
  5. Six AI play-testers, 54 findings (`17_qa_playtest_sheet.jpg`). Read the best ones out: you never saw Hercules die,
     the club through the camera, the pink Hydra, one wrong press of New game wipes your save, the mouse camera that never
     worked outside test mode, a shield you could hold up all fight.
  6. The fixes: Medusa x1.5 (`03_pair_medusa_scale.jpg`, wipe; `23_medusa_x15_sheet.jpg`), the Hydra's colours
     (`09_hydra_colour_fix.jpg`), the death you can now see (`10_defeated_card_fix.jpg`), the club that leaves the frame
     (`19_cyclops_death_club_fix.jpg`). Funny moment: Pegasus could never dive, and nobody had reported it.
  7. My reference vs the finished game, one per boss (`11_ref_vs_game_cyclops.jpg`, `12_ref_vs_game_medusa.jpg`,
     `13_ref_vs_game_hydra.jpg`, wipes).
  8. The Mac app: the export that failed, the workaround, the fix (231 MB, title in under half a second;
     `18_editor_vs_app.jpg`).
  9. The lead's last two tweaks at 12:48 AM (Medusa's tail warning 1.5 -> 1.8 s, the Hydra's jaw 1.1 -> 1.3 m), the last
     bot run: 3 victories, 0 defeats, 0 errors.
  10. The last look (Chapter 10): the message to me was being written when the lead held "right" for four seconds and
      looked. Hercules ran side-on, and turned his front to the camera at every change of direction: the look I had
      rejected in the trailer, filed as "minor" by its own final check. Eleven minutes later the camera kept his back
      (`media/10_circling_fix/12_clip_circling_side_by_side.mp4`, `03_pair_01_circle_right.jpg`,
      `09_pair_03_reverse_direction.jpg`, wipes).
  11. **My play-test** (to record): each fight with my controller, the flight, my verdict on feel, difficulty and look.
  12. The totals card (below), then what the AI says it could not test: no person had played it before me, no real
      controller had been connected, and 9 minor issues were still open.
- **Numbers on screen:** 54 findings / 0 blockers / 19 majors; 6 testers; Medusa 6.5 m -> 9.75 m; camera 6.5 m -> 2.9 m;
  the bot's last run 3 victories, 0 defeats, 0 errors; app 231 MB; 120 fps in all three fights on an idle machine (83 to
  93 fps with spikes while the build was running). Totals card: 9.2 hours from the first prompt (8.1 h for
  the game), 136 AI agents, 40.8 agent-hours, about 1.76 billion tokens read and written (9.1 M written), Higgsfield
  1,748 credits for the game + 835 for the trailer, 4 messages from me.
- **Clips to record myself:** playing the Cyclops, Medusa and Hydra fights with the Xbox controller (screen capture + a
  phone shot of my hands); one deliberate death per fight (the new death animation); the flight between islands; opening
  `builds/Hercules.app` from Finder (title in under a second); reading the README's known limits; my reaction to the
  first Medusa gaze; whether I can roll out of her tail ring on the first try.
- **Closing line:** what I'd change after playing it, and the open question: should the trailer get its 4K finals now?

### Episode 6 · "They seem a little stiff" (Chapters 11-12) · 12-15 min
- **Hook (first 15 s):** my own sentence on screen, word for word: "Some of them are still in the static pose in terms of
  limbs. They seem a little stiff." (P06). Under it, the old Cyclops walking toward Hercules in a T pose with his club
  straight up, then a hard cut (or a split screen) to the new walk with the club on his shoulder and four arms swinging
  (`media/12_natural_animations/27_clip_cyclops_walk_ref_old_vs_new.mp4` for the reference videos; in the game
  `media/12_natural_animations/73_clip_cyclops_approach_after.mp4`; there is no same-seconds recording of the old game, so the
  "before" side is the old reference video or `40_cyclops_idle_walk_before_after.jpg`).
  Line: "The AI had noticed this the night before. It wrote it down, and copied it anyway."
- **Beats:**
  1. 1:45 AM: the hand-over question with its two buttons (Q02). 8:40 AM: I click "Polish them now" (P05).
  2. The thing I didn't see: its first two test launches took my keyboard for ten seconds each. The fix: sixty lines of
     Objective-C, every game window off-screen, silent, never in front (Chapter 11, section 1). Honest moment: "sorry,
     that happened twice just now".
  3. Six minutes later I type the stiffness message while it works (P06 on screen, full).
  4. It counts frozen joints before it plans: Hydra idle 0 of 76, Cyclops walk 13 of 29, Hercules idle 6 of 29
     (`media/12_natural_animations/01_moving_joints_chart.jpg`).
  5. The cause, in my own method: every reference video started from the rest pose (`18_rest_vs_natural_hercules.jpg` ..
     `23_rest_vs_natural_pegasus.jpg`, `24_sheet_old_vs_new_hercules.jpg`). The animator's own note: "the video keeps the
     arms in the T pose and the club still". The silhouette score rewarded the copy.
  6. The fix keeps the method and changes the first frame: natural stances, five new sheets (`25_new_sheets_all.jpg`),
     nine new Seedance videos, 270 credits, no retakes; the old and new Cyclops walk videos side by side
     (`26_cyclops_walk_ref_old_vs_new.jpg`, `27_clip_cyclops_walk_ref_old_vs_new.mp4`).
  7. 41 more clips moved off the rest pose by five agents in 14 minutes (re-base pairs `30_rebase_cyclops_slam.jpg` ..
     `39_rebase_pegasus_fly.jpg`).
  8. Meanwhile, the nine polish items with reviewers who try to break every fix: the curb (`media/11_polish/09_curb_before_after.jpg`,
     wipe), the stuck club that vanished and left its shadow (`media/11_polish/13_stuck_club_refix_before_after.jpg`),
     the Hydra's fire warning (`media/11_polish/17_hydra_inhale_before_after.jpg`), the first-use freeze and the second
     shader cache (`media/11_polish/31_first_use_freeze_chart.jpg`).
  9. The naturalness reviews, 49 findings (44 handed to the fixers): a shield inside Hercules's chest, Medusa's tail swinging like a windscreen
     wiper, a Hydra skating on the spot that got two new turn clips, Pegasus sliding its hooves
     (`58_pegasus_idle_hind_skate_review.jpg`).
  10. Before/after sheets of every clip, as wipes (`04_pair_hercules_all_clips.jpg`, `07_pair_cyclops_all_clips.jpg`,
      `10_pair_medusa_all_clips.jpg`, `13_pair_hydra_all_clips.jpg`, `16_pair_pegasus_all_clips.jpg`).
  11. The idle I asked for by name: the first new one was still too quiet from behind; it caught that in its own
      recording and did it again (`61_home_idle_v1_vs_v2.jpg`).
  12. The lead's strips of the Cyclops and Medusa walking up to a standing Hercules (`59_ingame_cyclops_approach_after.jpg`,
      `60_ingame_medusa_approach_after.jpg`), then the home island start (`75_clip_home_idle_pegasus.mp4`).
  13. What is still not perfect, said out loud: the flat shield from the front, the Hydra's feet at the start of a turn,
      the Cyclops hidden behind Hercules in his walk-in, nobody has rendered banked flight turns, the side bites or the
      tail swipe, and no person had played it before me.
  14. **My play-test of the rebuilt app**: it exists now, my own 18-minute recording with my voice (Chapter 13). End this
      episode on its first seconds ("Alright, the game is ready. Let's go ahead and play test.") and open Episode 7 with it.
- **Numbers on screen:** 2 messages from me this morning (one was a button); 0 of 76 -> 43 of 76 (Hydra idle); 13 -> 28 of
  29 (Cyclops walk); 53 % -> 80 % of all joints moving; 9 new videos, 270 credits, 0 retakes; 41 clips re-based; 23 + 49
  review findings; first-use freezes 362-910 ms -> 0 over 50 ms; Medusa's slow-roll tail hits 28 of 50 -> 1 of 50; this
  morning 56 agents, 12.0 agent-hours, about 709 M tokens (3.6 M written) in 2.8 hours; whole project 192 agents,
  52.8 agent-hours, about 2.48 billion tokens (12.7 M written), about 2,018 game credits + 835 for the trailer.
- **Clips to record myself:** my desk while the agents test (no window appears; the front app stays mine); typing the
  stiffness message; the home island idle and each boss walking toward me with the controller in hand; the mount and a
  banked turn in flight (nobody has rendered one steered by a person); a Medusa tail swipe; a Hydra side bite.
- **Closing line:** my verdict on the new animations, and what I would ask for next.

### Episode 7 · "Everything looks good" (Chapter 13) · 10-12 min
- **Hook (first 15 s):** my own recording, my voice: "Okay, off the bat, some of the animation is not the best ... you just
  want to use the left stick to go left and right" over Pegasus being thrown round the frame
  (`media/13_owner_feedback/51_before_owner_first_flight.mp4`), hard cut to the same flight now, Pegasus locked in the centre
  while the right stick does nothing (`58_after_now_flight_steer_probe.mp4`). Line: "I played it myself for the first time.
  Then I told it what was off."
- **Beats:**
  1. "Go ahead and launch the game for me to play test" (P07, 12:51 PM). It launches the app, nothing else running.
  2. **The owner plays it for the first time:** the 18 minutes as a fast montage (`01_before_owner_overview_0m-4m.jpg` ..
     `03_before_owner_overview_16m-18m.jpg`), I lose to the Cyclops ("let me actually try a little harder this time") and to
     the Hydra, and I say "it's not too easy to play, which is good". My verdict clips (`56_before_owner_summary_1.mp4`,
     `57_before_owner_summary_2.mp4`): "the gameplay for the dragon was good".
  3. My message on screen (P08): "Everything looks good ... he has his hands like backwards ... Pay attention and just adjust
     the small details". The AI watches my whole recording and adds three things I only said out loud (S08, S15, S27).
  4. The list: six points with times and frames (`docs/notes/owner_feedback_2.md`; `04_before_owner_sword_hands.jpg`,
     `07_before_owner_mount_snap.jpg`, `13_before_owner_islands_empty.jpg`, `14_before_owner_strike_fx.jpg`,
     `15_before_owner_clipping.jpg`).
  5. The backwards hand: it finds the thumb on the mesh and two of its own fixes stacked into a reverse grip; the grip
     modifier (`31_after_sword_grip_sheet.jpg`, `43_after_check_sword.jpg`).
  6. Left stick only, the camera follows (`21_pair_flight_scene_start.jpg`, `46_after_check_flight.jpg`); Pegasus v3 -> v5,
     "two long white columns" (`39_after_pegasus_refix.jpg`).
  7. The mount: from a 0.2 s snap to step, spring, over the back (`50_before_owner_mount_snap.mp4` -> `59_after_now_mount_takeoff.mp4`).
     Honest moment: the first fix still hid me behind the wing for 0.55 s getting off; its own reviewer caught it
     (`35_after_dismount_refix.jpg`).
  8. The creatures on their islands (`24_pair_quarry_approach.jpg`, `61_after_now_cyclops_on_island.mp4`): the Cyclops walks
     beside me as I fly in; Medusa and the Hydra are still small.
  9. Hits that leave marks (`27_pair_cyclops_hit.jpg`, `62_after_now_cyclops_hits.mp4`, slow motion `63`, `64`); the white
     flash still covers the first frames.
  10. Clipping: the stuck club (`30_pair_stuck_club.jpg`).
  11. What is still open, said out loud (Chapter 13 "Still open"), then my next play-test of the rebuilt app (to record).
- **Numbers on screen:** 18 minutes of play, 3 wins, 2 losses; 5 written + 3 spoken points; 15 agents; 25 review findings,
  6 major; Pegasus on screen x -0.95..15.5 -> 0.49..0.51; mount 0.2 s snap -> 0.4 s with the rider always visible; 0 -> 3
  creatures on the islands; flash 0.2 -> 0.08 s; 0 Higgsfield credits; 1 h 11 min from my message to the final check.
- **Clips to record myself:** my next play-test of the rebuilt app: steering with the left stick only, the mount and the
  dismount, flying past the Cyclops on his island, a few cuts on each boss, and the sword from behind.
- **Closing line:** my verdict on the second build.

## Single long video (35-40 min, chapter markers)
0:00 Hook: trailer -> "wrong game" -> the reference cut · 1:30 The game request (P03) · 3:00 3D candidates and picks ·
6:00 Rigs and the reviewer who broke them · 10:00 My animation method and the two tests · 13:00 33 videos, 41 clips, where
Seedance lies · 19:00 The code and the bots · 23:00 Sound · 25:00 Real models in the game and the close camera ·
27:00 Six AI play-testers, 54 findings and the fixes · 31:00 The Mac app, the last bot run and the last look (side-on Hercules) ·
32:30 Monday: "Polish them now", and the keyboard it took twice · 34:00 "They seem a little stiff": frozen joints, the
rest-pose cause, nine new videos · 38:00 Reviews, the quiet idle, before/after sheets · 40:00 I play it for the first time,
my six points · 42:00 The backwards hand, left-stick flight, the mount, creatures on the islands, hit marks · 45:00 The
totals and what the AI could not test. (With Episodes 6 and 7 the long cut runs about 47 min.)
Use the episode beats above, one or two media items per beat.

## Shorts (under 60 s, 9:16)
1. **"Same prompt, different camera"**: first trailer vs keyframe draft, wipe (`media/01_trailer/04_pair_look.jpg`,
   `05_pair_camera.jpg`). Line: "Words didn't fix the camera. A picture did."
2. **"The AI's tree was bald"**: `media/03_characters_props/12_pair_olive_tree.jpg`. Line: "Ask for leaf clumps, not leaves."
3. **"The Cyclops's knees were its ankles"**: `media/04_rigging/25_cyclops_knee_fix.jpg`.
4. **"My animation method in 30 seconds"**: sheet -> 480p video -> keyed rig (`media/02_plan/03_method_diagram.jpg`,
   `media/06_reference_videos_clips/05_hercules_run_match.mp4`).
5. **"Hercules rides Pegasus"**: `media/06_reference_videos_clips/38_ride_ref.mp4` + `39_ride_proof_close.jpg`.
6. **"Fire or smoke? One checkbox"**: `media/07_game/17_pair_fire_colour.jpg`.
7. **"The content filter didn't like a dying Cyclops"**: the two prompt lines (DECISIONS D40) over
   `media/06_reference_videos_clips/19_cyclops_death_match.mp4`.
8. **"She was supposed to tower"**: Medusa before/after the x1.5 scale (`media/09_integration_playtest/03_pair_medusa_scale.jpg`).
   Line: "Two agents tried the camera. The lead just made her bigger."
9. **"One button wiped your save"**: the AI play-tester's finding and the new "START OVER?" question (Chapter 9), over
   the title screen (`media/09_integration_playtest/08_title_overlays.jpg`).
10. **"Pegasus could never dive"**: the flight clip (`media/09_integration_playtest/15_clip_flight.mp4`) with the bug in
    one sentence: a climb check returned zero over flat sea.
11. **"The AI called it minor"**: the side-by-side circling clip (`media/10_circling_fix/12_clip_circling_side_by_side.mp4`).
    Line: "Its own check said minor. It was the exact thing I had rejected: Hercules from the side."

12. **"Zero of seventy-six"**: the Hydra's old idle (a statue) next to the new one, the counter going 0 -> 43
    (`media/12_natural_animations/13_pair_hydra_all_clips.jpg`, `47_hydra_idle_before_after.jpg` or
    `49_clip_hydra_idle_walk_before_after.mp4`). Line: "I said they looked stiff. It counted the joints."
13. **"It copied the T pose on purpose"**: the old Cyclops walk reference video next to the new one
    (`media/12_natural_animations/27_clip_cyclops_walk_ref_old_vs_new.mp4`), with the animator's note on screen: "the video
    keeps the arms in the T pose and the club still". Line: "The AI matched my reference perfectly. My reference was the problem."

14. **"His hands were backwards"**: my close-ups (`media/13_owner_feedback/04_before_owner_sword_hands.jpg`) -> the fix
    (`43_after_check_sword.jpg`). Line: "Two of its own fixes stacked up into a reverse grip. It found the thumb on the mesh."
15. **"Left stick only"**: my voice from the recording over the old flight (`51_before_owner_first_flight.mp4`), then the
    new camera (`58_after_now_flight_steer_probe.mp4`).

## Quotes to put on screen (from PROMPTS.md, verbatim)
- "it's not what I'm intending the game to look like" (P02)
- "The creatures should be a lot bigger, and you should circle around them, dodging the attacks from the creatures." (P02)
- "And don't stop until the game is completely built." (P03)
- "I want you to use Cdance 2.5 on the lowest resolution level to generate a front view and a side view of the animation that you want to make." (P03)
- "so that I can share that with my audience after the game is complete." (P03)
- "let me know when it's complete for me to test." (P03)
- "Polish them now" (P05, a reply button)
- "especially when the monsters are walking towards Hercules. Some of them are still in the static pose in terms of limbs. They seem a little stiff." (P06)
- "Make every movement throughout the process natural, as well as the idle animation when the game first starts." (P06)
- "Go ahead and launch the game for me to play test." (P07)
- "Alright, so it's not too easy to play, which is good." (S12, spoken in his play-test)
- "So in reality, you just want to use the left stick to go left and right." (S08, spoken)
- "The panning around the horse while it's flying that needs to be fixed." (S15, spoken)
- "Everything looks good." (P08)
- "Hercules' sword is he has his hands like backwards, so we gotta adjust that and fix it." (P08)
- "Pay attention and just adjust the small details, and everything else will be done already." (P08)

## Privacy check before publishing
The game is never named in prompts, code or files; JC names it himself in P02, so blur or skip that word if the video
should not mention it. Credit balances are fine to show; the Higgsfield result links in the transcript contain an account
id and are not in this folder.
