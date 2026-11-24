# Lead log — raw facts for the devlog (times are local, 2026-11-22 unless noted)

## Before the game: the trailer (same session)
- 16:31 P01: owner pasted a Seedance 2.5 prompt for a 15 s "HERCULES" concept trailer (three boss fights + title).
  No images were attached; the four character sheets were found in ~/Downloads and used as references.
- Lead ran three 480p drafts (45 credits each) and finalized the first in 4K (420 credits): 555 credits total.
  Result looked like a side-on 2D fight; bosses roughly Hercules's size.
- ~17:06 P02: owner rejected the LOOK (not the art): he wants boss fights like a famous dark-fantasy action game
  (never named in prompts): creatures a lot bigger, circle around them dodging, camera right behind the hero.
  He suggested one 15 s clip per fight, stitched.
- Fix that worked: (1) per-fight prompts with explicit CAMERA / SCALE / MOVEMENT blocks; prompt alone still gave a camera
  that drifted high and far (Hercules tiny in the Hydra fight); (2) an opening keyframe per fight made with Nano Banana Pro
  (2 credits) from the sheets — Hercules from behind, boss towering — passed to Seedance as `start_image`.
  Three keyframe-based drafts matched his description. 47 s review cut stitched (Cyclops, Medusa, Hydra, title).
  Round cost 280 credits. 4K finals (1,260 credits) were offered; the owner did not answer and moved on to the game.
- Lesson recorded: show a cheap draft before paying for 4K (the 420-credit 4K of the first look was wasted).

## The game build
- ~17:27 P03: the owner's game request (see PROMPTS.md). Ultracode on. Lead = Claude Fable 5.2; agents = Opus (owner's
  standing rule), effort high.
- 17:30-17:40 scouting: Godot 4.7.2 + export templates present; Blender 5.2.2 LTS; the owner's open Blender holds
  another project -> decision: never touch it, all Blender work headless. No Higgsfield add-on in that Blender.
  Higgsfield 3D catalogue: Meshy 7 image-to-3D (38 credits, 44 with auto-rig), Meshy multi-image (30), Hunyuan3D v3
  multi-view (19 at 50-70k faces, 15 at 40k), Tripo H3.1 (not tried in this build),
  Meshy rigging, 678 preset animation clips (not used: the owner wants his video-matching method).
- 17:41 repo `~/HerculesGame` created (outside iCloud Desktop on purpose), devlog scaffold.
- 17:42 character sheets cropped into one figure per image (image-to-3D fuses everything in a frame into one object).
  First cropper bug: bounding boxes of neighbouring figures overlapped (Hydra's tail tip inside the front crop); fixed by
  blanking pixels that belong to another connected blob.
- 17:44 ten 3D jobs submitted, two candidates per character. A zsh trap cost one round: `$J args` is not word-split, nine
  of ten submissions silently did nothing; Meshy jobs also needed `--enable_rigging false --enable_animation false` spelled
  out because the CLI could not evaluate the model's validation rule without them.
- 17:49 all ten done (about 3-5 minutes each). 267 credits. Picks from 4-view renders:
  - Hercules: Meshy 7 (31,105 triangles, 2048 texture, comes auto-rigged: 24 bones) — the Hunyuan one was also good.
  - Cyclops: Meshy 7 from the FRONT view only (41,209 triangles): crisper ink lines; back was invented but fine.
  - Medusa: Hunyuan (70,000): only it kept the owner's "straight rear tail"; Meshy multi-image made a hanging J tail.
  - Hydra: Hunyuan (69,992): nine clear heads in a fan; Meshy multi-image stacked the necks.
  - Pegasus: Hunyuan (69,986): real wings; Meshy multi-image made paper-thin vertical wings.
- During the build the Higgsfield balance went from 4,022.96 to 7,022.96 (+3,000 credits appeared on the account).
- 17:52 weapon concepts (sword, lion shield, club) with Nano Banana Pro using the Hercules sheet as style reference
  (2 credits each), then Hunyuan 3D (15 each). Fourteen environment prop concepts the same way (28 credits) + 3D (210).
- 17:53 first FRONT | SIDE split sheet of Hercules rendered headless (Workbench flat texture, two orthographic cameras at
  the same pixels-per-metre). Two framing bugs fixed: Meshy's rig ships a helper mesh "Icosphere" that inflated the
  bounding box (character tiny and floating); the side panel was too narrow for a run.
- 17:55 the owner's method tested with two Seedance 2.5 videos (480p, 10 s, 30 credits each, sheet as first frame):
  a run in place and a dodge roll. RESULT: the split layout held, both panels stayed in sync, the character stayed
  on-model, cameras static. The method works.
- ~18:00 workflows launched: foundation (animation toolkit + Godot core), rigs (five characters), props.
- 18:21 props workflow done (2 agents, 11 min): 13 of 14 props good. The olive tree came out as a bare trunk (Hunyuan could
  not build a leafy canopy). Fix: a new concept image that asks for "ONE big solid rounded canopy built from a few large
  chunky leaf clumps (solid closed shapes, no individual leaves)" -> the second 3D generation has a canopy (17 more credits).
- 18:14 audio: 56 sound effects (Mirelo, 0.25 credits per second) + 5 music tracks (ElevenLabs Music v2.5, about 9-13 credits
  each) generated in about 12 minutes; four submissions failed on the first pass and went through on the second.
- 18:58 foundation + rigs workflows finished (58 min each): animkit 24 tests + selftest on all five rigs; core passes bot
  win/lose/pad; rigs: hercules 29 bones, cyclops 29, medusa 35, hydra 76, pegasus 43. Review verdicts before fixes:
  cyclops FAIL (1 blocker), hydra FAIL (2 blockers), others pass-with-fixes; all fixed in the third stage.
  Notable: the animkit builder found that Seedance re-frames the video (character ~21% larger than the sheet, divider moved)
  and added calibration of video frame 0 against the sheet; the reviewer found 14 majors (mixed-fps export, framing vs body
  motion, driven skirt bones, mirror names, chain bends on vertical chains...), all fixed.
- 19:00 lead rendered final split sheets with explicit motion envelopes (std / wide framings) — the first sheets had no
  room for a body falling forward or a club raised overhead.
- 19:00 modules workflow launched (cyclops, medusa, hydra, world). Ride-sheet workflow launched.
- 19:05 first attempt to submit all 32 reference videos: only 6 accepted — the Higgsfield account allows 6 concurrent
  jobs; 26 submissions were rejected (no credits lost). Generator changed to batches of 6.
- 19:10 animation wave 1 launched on the six Hercules videos that exist (idle, run, strafe, walk_back, roll, attack).
- 19:36 ride sheet done: Hercules seated on Pegasus's saddle bone, both real rigs, checked by a second agent (it widened the
  frame: the first sheet left only 3.4 cm for a fully spread wing).
- 19:40-19:55 reference videos: 33 in total (9 Hercules, 6 Cyclops, 7 Medusa, 7 Hydra, 3 Pegasus, 1 ride), 480p 10 s,
  30 credits each. The Cyclops "death" video came back with status "nsfw" (content filter); a reworded prompt
  ("exhausted and defeated ... lies still like a sleeping giant") passed. The ride video shows Hercules on the flying
  horse from front and side with full wing beats.
- 19:40 usage check: weekly all-models at 40% (25% before the build). Decision: later animation waves run animators only;
  one reviewer per character checks all clips after the merge (instead of one reviewer + one fixer per video).

## Mon Nov 23 2026: the owner comes back (lead's raw facts for the devlog)
- 08:40:06 AM JC clicks the reply button "Polish them now" under the hand-over question
  ("Polish the 9 open minor items before your test?"; the other button was "After my test").
- 08:42 the lead starts scouting the nine items in the code.
- 08:46:57 AM JC sends a message while the lead is working (queued, delivered mid-turn), word for word:
  "Make sure that all animations look natural throughout the whole gameplay. Right now, some of the animations. Don't look
  natural, especially when the monsters are walking towards Hercules. Some of them are still in the static pose in terms of
  limbs. They seem a little stiff. Make every movement throughout the process natural, as well as the idle animation when
  the game first starts."
- 08:44 JC is at the Mac (the machine is in use). The lead's first two test launches
  took the keyboard focus for about 10 s each ("front app: Godot"). `open -g` did not help (Godot activates itself), and
  a non-focusable window sent the focus to Finder for 5.5 s. Fix at 08:55: a 60-line Objective-C library
  (`tools/godot_bg/nofocus.m`) injected with DYLD_INSERT_LIBRARIES (the Godot editor binary's signature allows it): it
  turns app activation into a no-op, sets the activation policy to accessory (no Dock icon) and orders the window to the
  back; the wrapper `tools/godot_bg/gdwin` also places the window off-screen (6000,6000) and uses the dummy audio driver.
  Test: front app unchanged for the whole run, 11.4 s (same as a normal run), 20 valid screenshots, no sound.
- 08:50 frozen-joint measurement (`tools/clip_motion.py`, a joint that turns < 3 degrees in a whole clip = frozen):
  cyclops walk 13/29 joints move (all four arms, head frozen), cyclops idle 9/29, hydra idle 0/76 (a statue), hydra walk
  24/76 (nine heads, jaw and necks frozen), medusa slither 26/35, medusa idle 18/35, hercules idle 6/29, block_idle 5/29,
  ride 3/29, strafe 10/29, pegasus idle 16/43.
- 08:53 root cause: the Seedance reference videos started from split sheets of the rigs in the REST pose. The cyclops
  walk video shows the T pose with the club straight up for all 10 s; only the legs step. The animator's own note from
  the night before said so ("the video keeps the arms in the T pose and the club still") and matched the video faithfully.
- 08:57 plan written (docs/briefs/anim_natural.md): a natural stance per character -> new sheets from that stance -> new
  Seedance videos (480p, 10 s) for every walk and idle -> keyframe all limb groups -> every other clip re-based from the
  rest pose onto the natural stance with quiet life. Not in scope: a settings menu (never one of the nine items).
- 08:59 two workflows launched: `hercules-natural-stance` (5 agents) and `hercules-polish-2` (4 fixers, 4 independent
  reviewers, re-fixers, then the first-use freeze).
- 09:00 the lead tells JC: about 3 to 3.5 hours; test windows are off-screen and silent; the game will stutter if he
  plays during the run.
- 09:11 `hercules-natural-stance` done: 5 agents, 12.1 min, 0.97 M tokens. A natural stance, a new FRONT | SIDE sheet
  (sheet_nat_std.png) and a per-clip plan for every character. Plan: 9 clips need a new video (V), 41 are re-based (R),
  1 is kept (K: Hercules's death). The lead looked at all five sheets: the Cyclops rests the club on his right shoulder
  with the other three arms hanging; the Hydra's necks sit at different heights; Hercules stands relaxed, sword down,
  shield at his side; Medusa's arms are relaxed; Pegasus has its wings half folded.
- 09:12-09:28 nine new Seedance 2.5 reference videos (480p, 10 s, 30 credits each = 270): hercules idle_n, run_n; cyclops
  idle_n, walk_n; medusa idle_n, slither_n; hydra idle_n, walk_n; pegasus idle_n. Two batches (6 + 3: the account runs 6
  jobs at a time). No retakes. The lead looked at a contact sheet of each: the natural stance is kept, the limbs move,
  both panels agree. Ledger after: 1,928.29 quoted credits, 163 jobs (plus the 90 unpriced from Nov 22).
- 09:15 lead tool `tools/probes/clip_showcase.gd`: every clip of a character, 8 poses each, on one sheet with its
  moving-joint count. BEFORE sheets of all five saved before any game file changed.
- 09:26 `hercules-natural-rebase` done: 5 agents, 13.8 min, 1.09 M tokens: all 41 R clips re-based onto the natural stance
  with quiet life; lengths, loop flags and events unchanged. Each agent wrote its own headless Blender tool.
- 09:28 / 09:30 `hercules-natural-animate` launched twice (hercules+cyclops+medusa; hydra+pegasus): per character one
  animator per new video, then an assembler (merge, export, import, in-game probe), an independent naturalness
  reviewer and a fixer.
- 09:57 `hercules-polish-2` done: 13 agents (4 fixers, 4 reviewers, 4 re-fixers, 1 freeze fixer), 57.5 min, 2.71 M
  tokens. Every reviewer returned "pass with fixes"; every finding the re-fixers checked was real.
  First-use freeze: cause = GPU shaders compiled at an effect's first draw; a fully cold run needs a new HOME AND a new
  bundle id (macOS keeps a Metal cache per bundle id; the agent cloned the Godot app with APFS for that). Cold, before:
  cyclops 685 / 418 / 427 / 910 ms, medusa 400 / 379 / 362 ms, hydra 454 / 416 ms. After: 0 frames over 50 ms after the
  fight starts in all three. Cost: the scene switch frame under the black fade is 1,655 ms instead of 253 ms.
- 10:36 first animate run done: 15 agents, 68.5 min, 3.49 M tokens. 10:58 second run done: 9 agents, 89.5 min, 2.16 M.
  Moving joints before -> after: cyclops walk 13 -> 28 of 29, idle 9 -> 25; hercules idle 6 -> 21 of 29, run 19 -> 28,
  strafe 10 -> 21, block_idle 5 -> 19, ride 3 -> 9; medusa idle 18 -> 30 of 35, slither 26 -> 34, stunned 13 -> 28;
  hydra idle 0 -> 43 of 76, walk 24 -> 67, stomp 25 -> 64 (and two new clips, walk_turn_l / walk_turn_r, so its feet
  stay planted when it turns on the spot); pegasus idle 16 -> 39 of 43, glide 13 -> 38, fly 28 -> 38.
  Changed for the game: cyclops idle 3.33 -> 6.0 s, walk move_speed 2.54; hercules idle 3.5 -> 6.0 s, run 0.833 ->
  0.667 s, move_speed 3.64 -> 4.59; medusa idle 3.0 -> 6.0 s, slither 2.0 -> 1.75 s; pegasus idle 7.0 -> 8.0 s.
- 10:54 integration A done (hero, cyclops, medusa): 3 agents, 15.2 min, 0.68 M tokens.
- 10:57 the lead records the game: the Cyclops and Medusa approach a standing Hercules with natural arms. On the home
  island the new Hercules idle is relaxed but TOO QUIET from behind: 18 frames half a second apart look identical
  (head 16 degrees, hips 7 degrees over 6 s). A clip-fix pass is sent (`hercules-natural-clipfix`).
- 11:00 integration B launched (hydra, world, then the final check).
- Decisions by the lead today: the no-focus wrapper before any agent runs a window (08:55); natural stance + new videos
  for walks and idles, re-base for the rest (08:57); a settings menu is not in this pass; keep Medusa's snake-hair
  recolour although the snakes' eyes lost their yellow (looked at close-ups 10:00: cleaner at game distance); leave the
  flat shield in strafe / walk_back as seen from the front (not visible from the chase camera); integrate the three
  finished characters before the last two are done (10:39) to save time.
- 11:13 `hercules-natural-clipfix` done: 3 agents, 17 min, 0.71 M tokens. Hercules idle: hips travel 4.5 -> 7.5 cm, look
  to his left 27 -> 37 degrees, sword tip 7.6 -> 24.5 cm, two shoulder shrugs per loop; block_end 0.25 -> 0.333 s with an
  eased end; attack_1 recovery eased. Cyclops pull_free: club-head peak 50.3 -> 27.0 m/s, the right foot takes one real
  0.37 m step instead of gliding 1.25 m; idle amplitudes raised (club head range 0.8 -> 2.1 m). Medusa: stun_start arm
  drop spread out, death hair whip and arm flip fixed. The lead recorded the home island again: the idle is now visibly
  alive from behind (12 frames half a second apart differ: weight shift, head turned left, sword hand).
- 11:25 integration B + final check done: 3 agents, 26 min, 0.64 M tokens. hydra integrator: an attack picked in the
  middle of a turn walk now waits for the stop window (walk-to-attack foot slide peaks 4.4-5.5 -> 2.2-3.3 m/s), body
  turn waits for the walk blend; jaw_radius back to 1.0 because locked strikes now aim at the jaw (hits from 0 to 90
  degrees at 1.2 / 2.0 / 2.6 m). world integrator: mounting = Pegasus's 12 wing bones start the fly beat as an overlay
  when interact is pressed (legs stay planted), hop 0.55 -> 0.9 s with a small camera push-in, the rider starts from the
  walking hero's own pose; arriving home Pegasus glides in over 1.9 s and settles into the idle.
  FINAL CHECK 2 (docs/notes/final_check2.md): campaign with keyboard events and with pad events: victory, 22 strikes,
  0 hits taken, 0 errors (cyclops 35.16 / 34.42 s, medusa 23.98 / 23.96 s, hydra 97.08 / 96.82 s); lose bots restart
  every fight; ui probe passes. Fully cold: cyclops 0 frames over 50 ms after the fight starts, medusa and hydra 1 frame
  each (57-58 ms, the HUD boss bar appearing), flight 0. Moving joints, morning -> now: hydra idle 0 -> 43 of 76, walk
  24 -> 67; cyclops walk 13 -> 28 of 29, idle 9 -> 25; hercules idle 6 -> 23 of 29, run 19 -> 28; medusa idle 18 -> 33
  of 35, slither 26 -> 34; pegasus idle 16 -> 39 of 43.
  Still open after it (all minor or cosmetic): Pegasus lands at home WITHOUT its rider while the hero already stands on
  the path (new today; a last fix is sent); the Hydra's turn-walk feet slide a little when the turn starts and stops
  (needs step-in / settle clips); the idle shield is edge-on from straight behind; the shield passes through the body in
  the roll; the Cyclops stands right behind the hero in the frame during his walk-in, so the new walk is partly hidden;
  not rendered by anyone: banked flight turns with a person steering, the Hydra's side bites, Medusa's tail swipe.
- 11:28 `hercules-last-fixes` (one agent: riderless landing, HUD boss bar warm-up) and `hercules-devlog-3` launched;
  the lead records the Hydra fight and the mount and flight to look at them.
- 11:41 `hercules-last-fixes` done: 1 agent, 13.6 min, 0.2 M tokens. Arriving home from the sea, Hercules now rides
  Pegasus through the 1.9 s glide-in, Pegasus stands 0.3 s, he hops off beside it (0.85 s) and the camera eases onto the
  chase view; the first arrival of a new game is unchanged. The cold fight_start frame was the lock reticle's first
  lines, not the boss bar: now drawn invisibly during the warm-up (Medusa 0 frames over 50 ms, Hydra 53 ms with no
  compile in it).
- 11:41 the lead's own regression on the final code: Cyclops victory 36.82 s, Medusa 27.37 s, Hydra 99.37 s; the whole
  game with keyboard events (261.23 s) and with pad events (260.17 s): 3 victories, 0 defeats, 0 errors.
- 11:42 app rebuilt: `zsh builds/make_app.sh`, 232 MB, signature valid, universal. Its own binary wins the Cyclops fight
  (38.17 s) and the whole game with pad events (260.13 s, 3 victories, 0 errors).
- 11:45 LEAD MISTAKE: to look at the rebuilt app in a rendered run, the lead started the exported binary through the
  off-screen wrapper without first reading its signature. The exported app has the hardened runtime, so macOS ignored the
  injected library: the window stayed off-screen and silent, but it took JC's keyboard focus for about 14 s
  ("front during: Hercules"). The wrapper now refuses any binary it cannot inject (exit 96) and AGENT_RULES says how to
  check the exported game instead (the editor binary on its pck). The 14 frames it captured show the new stance and
  walk in the rebuilt app.
- README "Known limits" rewritten for today's state (lead).
- 12:00 PM (about) JC asks the lead to launch the game; `open builds/Hercules.app`; he plays it with his controller
  and records 18 minutes with voiceover in his screen-recording app.
- 1:10 PM JC's feedback message (P07, in the transcript): everything looks good; adjust the sword hold ("hands like
  backwards"), mounting and dismounting, Pegasus's flying animations; add the creatures walking on their islands seen
  from the air, and more strike effects and visible damage. From the recording's own transcript: flight steering should
  use the left stick only, the camera panning around the horse in flight needs fixing, some clipping in places; "the
  gameplay for the dragon was good", "not too easy to play, which is good".
- 1:15 PM `hercules-feedback-2` launched (intake -> 4 fixers -> reviewers -> re-fixers -> final check -> devlog).
