# Owner feedback 2: what must change (intake, 2026-11-23 13:15-13:40)

Source: the owner's play-test recording (17:58.9, READ-ONLY, kept outside the repo), cropped to the game window, its
transcript and his message sent at about 1:10 PM (the last user message in the session, logged 13:12:03 EST).
How it was watched: contact sheets every 10 s of the whole recording (108 frames), then close sheets every 0.1-0.75 s
at each moment below. Frames and captions: `docs/devlog/media_inbox/owner_feedback_2/` (24 JPEGs + captions.txt).
Times below are recording times (m:ss.s).

## His words

His message (P07), word for word:

> Everything looks good. There's just a few things that need to be adjusted. I left the feedback on the screen recording inside of [my recording app, project name removed]. The last recording on there has my gameplay along with my voiceover of the feedback that I have. Most of it coming from just the sword, the holding of the sword from Hercules. Some of the animation of getting on and off the horse can be improved, and then also, um, yeah, Hercules' sword is he has his hands like backwards, so we gotta adjust that and fix it. And then the flying animations for Pegasus needs to be adjusted as well. Other than that, everything else looks good. I want to make sure to also add a quick note. It'd be great if we can see the creatures in the maps whenever we're flying over them. So them animated walking around. And then a little bit more visual effects for the striking of the creatures whenever you cut them. There should be a little bit more visual effects and damage made to the creatures. That would add a little bit more to the gameplay. So take a quick look and make those slight adjustments. Pay attention and just adjust the small details, and everything else will be done already.

In the recording (app transcript):
- 0:02.96 "Alright, the game is ready. Let's go ahead and play test."
- 1:57.7 (first flight, 18 s after the first mount) "Okay, off the bat, some of the animation is not the best."
- 2:00.7 "Controlling the horse, also a little bit off, that you can move." 2:08.5 "Like the camera, you can change
  the camera with the right stick and then the turning with the left stick." 2:14.4 "It's a little off."
  2:16.3 "So in reality, you just want to use the left stick to go left and right."
- 2:49.5 "It actually doesn't let us go into the other islands, so you have to take them in order, I guess." (no request)
- 3:47.3 "Alright, so it's not too easy to play, which is good. We don't want it to be too easy." (PRAISE)
- 7:19.8 (flying to the Sanctuary) "The panning around the horse while it's flying that needs to be fixed."
- 16:46.4 "Alright, so that was the game. A couple of things that we noticed was I think the gameplay for the dragon was
  good. For the horse, obviously we need to fix the flying animations. The sword is also... [9 s pause] I think should
  be better and I think that the locations can be a little bit improved in terms of actually being able to see the
  creatures in the islands. Other than that everything else looks good."
- 17:25.9 "A little bit of clipping through some of the areas as well so we'll go ahead and give that feedback."

## What he praised: do NOT change
- The Hydra fight ("the gameplay for the dragon was good", 16:50) - frame 18.
- Difficulty ("not too easy to play, which is good", 3:47) - keep every boss's timing, damage and health as is.
- "Everything looks good" / "everything else looks good": title, controls page, home island, HUD, islands in order,
  storm walls, landing rings, bosses' looks and attacks, LABOR COMPLETE / DEFEATED / ending card. He lost once to the
  Hydra (10:20 DEFEATED) and once more to the Cyclops (4:46 "let me actually try a little harder") and did not complain.
- "Pay attention and just adjust the small details": every fix below is local; no redesign.

## The list (in priority order)

### 1. How Hercules holds the sword: "he has his hands like backwards"
Seen (frames 01, 02, 03, 10):
- Idle, walk and run (1:20, 17:28 front, 17:33 back, 5:46, 5:47.5, 5:55): the fist is NOT closed round the grip. The
  hand is half open, the grip lies across the finger tips or hangs under the fingers (5:55 front: a clawed hand above
  the guard, the grip below it). The blade leaves the hand from the little-finger side and points DOWN and OUT/BACK,
  about 30-45 degrees off the leg, tip behind and outside the heel (17:16, 17:33). From the front (17:28) the blade
  points down-outward away from the body with the hand beside, not round, the hilt. This is the "backwards" look: the
  hand reads as turned the wrong way round the grip (palm and fingers facing away from it), like a loose reverse grip.
- Strikes: the reach strike (5:50.5) shows a fist seen from the knuckles with the grip poking out between the fingers;
  the end of the side cut (5:53) and the overhead (5:48.5, 5:52.5) read better (blade up from the thumb side).
- On Pegasus (1:57, 2:08, 2:11, 6:25, 6:30.5, 7:15, 16:10): same open hand at the hip, blade straight down beside or
  into Pegasus's flank (6:30.5) or flat across his own thigh (2:08, 16:10).
- Code: `game/scripts/visual/character_visual.gd` (the sword rides a BoneAttachment socket; the locomotion aim at
  line ~442 turns the socket "along dir"; the 2026-11-22 note at line ~621 says "sword forward").
Acceptance:
- Front, side and back renders (gdwin, 1280x720 plus a close crop of the hand) of idle, walk, run, attack_1, attack_2,
  block, roll and the seated flight pose: the grip runs THROUGH a closed fist (fingers wrapped round it, thumb over the
  fingers, no visible gap between palm and grip), the guard sits against the index-finger side, the pommel below the
  little finger, the wrist straight (not bent back).
- The blade leaves the fist on the THUMB side. In idle/walk/run it points forward and down (tip ahead of the hand,
  20-60 degrees below horizontal, never behind the heel or flaring outward); in strikes the edge leads along the swing.
- On Pegasus the blade never enters the horse or the rider's thigh (check 5 flight frames from behind and the side).
- Same check against `art_src/chars/hercules/split_sheet.png` (sword forward). Before/after sheet into the devlog.

### 2. Getting ON and OFF Pegasus
Seen (frames 04, 05, 06):
- Mount 1 (1:38.3-1:41.3): he walks to Pegasus's left side; at 1:39.5 he is still standing on the ground in front of
  the flank with the near wing raised; at 1:39.7 (0.2 s later) he is seated. No hop, no leg over: a snap. Seated, his
  sword arm sticks straight out sideways like a T with the blade horizontal (1:39.7-1:40.9) while Pegasus rears and
  walks off; the near wing hangs down to the grass in front (1:39.7-1:40.1).
- Mount 2 (6:58-7:05.5): standing beside Pegasus at 7:02.0, seated at 7:02.5 (snap again); at 7:03.0 the near wing
  sweeps down over his legs; take-off at 7:04.0, fade at 7:04.5.
- Dismount 1 (arriving home, 6:48.8-6:51.4) and dismount 2 (16:59.8-17:02.4) are the same: Pegasus lands at
  6:49.6 / 17:01.0, the rider is NOT visible 6:49.8-6:50.2 and 17:01.2-17:01.6 (hidden by the raised near wing, about
  0.4-0.6 s), reappears seated, then stands on the grass one 0.2 s step later (6:50.6 -> 6:50.8, 17:02.0 -> 17:02.2).
- The README already lists "During the mount and the dismount the near wing covers the rider for about 0.2 to
  0.35 s"; in his play it was longer, and the jump on/off is not seen at all.
- Code: `game/scripts/world/home_base.gd` (mount / dismount on arriving home).
Acceptance (record `--start=home --harness --bot=win` and an arrival home, 30 fps, every 0.1 s sheet, camera as in game):
- Mount: a visible hop of 0.6-1.0 s: plant, spring, right leg swings over the back, settle into the seat. Every 0.1 s
  frame shows the hero between ground and seat (no frame jump > 0.35 m), never inside Pegasus's body or wing.
- The rider is visible (at least head and torso) in every frame of mount and dismount; the near wing may pass in front
  for at most 0.1 s.
- Seated pose right after the mount: sword arm relaxed at the side, blade forward-down along the horse (as in 1), not
  stuck out sideways.
- Dismount: leg swings over, drop to the ground beside Pegasus over 0.5-0.8 s, feet land on the grass, then he stands.
- Both run while the camera follows as today (it pans to them: keep that).

### 3. Pegasus flight: steering, camera ("panning around the horse"), flying animation
Seen (frames 07, 08, 09, 10, 19):
- Camera. While he flew, Pegasus jumped round the frame every 0.5-1 s: 2:06.0 completely out of frame, 2:06.5 at the
  left edge, 2:07.0 large on the left seen from the side, 2:07.5 centre from behind, 2:09.0 side view on the right,
  2:10.0 cut by the left edge. After the Cyclops win the flight starts with Pegasus BELOW the bottom edge for 4.5 s
  (6:20.0-6:24.5, only sea and sky; frame 19), then it is large and close above centre (6:26-6:28). The horizon tilts
  about 10-15 degrees in turns (1:47, 1:49, 2:16-2:19, 6:32-6:34). On a straight line (7:06-7:21) the camera sits still
  behind, Pegasus small at the bottom centre. On approach to the rings it swings to a side view again (3:02, 9:36).
- Steering. Today: left stick x = yaw, y = pitch; right stick / mouse orbit the camera (`pegasus_flight.gd`
  `_look_yaw/_look_pitch`, CAM_PAD_SPEED 2.4 rad/s, pitch -0.5..0.9, CAM_BANK 0.3). His words: the right-stick camera
  plus left-stick turning "is a little off ... you just want to use the left stick to go left and right".
- Animation. From behind, Pegasus shows its rump with the blue tail hanging straight DOWN like a column (1:57, 6:25,
  7:11-7:15); in the side views (2:07.5, 2:08, 2:09) the body reads upright / rearing with the legs dangling under it,
  more a horse standing on air than flying. The wings are held in a V and barely move in level flight (1:56.0-1:58.1
  every 0.3 s: only a small rise and fall); in the glide (7:11-7:13) they sweep down like a second pair of legs. The
  rider is frozen in one pose: knees wide, feet in the air away from the flanks, open hand at the hip, blade down.
DECISION (he will not answer; written here): in flight the right stick and the mouse no longer orbit the camera. The
camera stays behind Pegasus and follows its heading smoothly; the left stick / WASD do everything (x = turn,
y = climb/dive). A small "look" offset is NOT kept (he asked for left stick only). Boost stays on RT / Shift.
Acceptance:
- Probe (copy `tools/probes/hold_side_input.gd` pattern) on `--start=sea`: hold left full 4 s, right full 4 s, up 2 s,
  down 2 s, and push the right stick / move the mouse during all of it. Every frame (shots every 0.25 s, 1280x720):
  Pegasus and rider fully inside the frame, their centre inside the middle 40 % of the width and the lower-middle half
  of the height, camera yaw within 15 degrees of Pegasus's heading, horizon roll at most 5 degrees. Right stick / mouse
  change nothing.
- The first frame after every scene start into flight ("The Open Sea" title, after each win, the take-off at home)
  already shows Pegasus in that box (no 4 s with Pegasus off-screen as at 6:20).
- Approaching a landing ring the camera stays behind (no swing to a side view as at 3:02 / 9:36).
- Pegasus clips: in level flight the body is within 15 degrees of horizontal along the flight direction, the tail
  streams back (not down), the front legs tuck, the hind legs trail; the wings make full strokes (tips clearly above
  and below the body line, about 1-1.5 strokes per second, faster when climbing/boosting); the glide holds the wings
  spread out level; turns bank the body into the turn. A side-view sheet and a behind sheet of fly / glide / boost / turn.
- Rider: legs along the flanks (feet within a hand of the body), slight forward lean, a small sway with each wing
  stroke; sword as in item 1.

### 4. NEW: see the creatures on their islands when flying over them, animated, walking around
Seen (frame 11): from the air the Quarry Isle (2:58-3:06) shows stone blocks and columns, the Sanctuary (7:20-7:23.5)
a ring of columns, the Volcano (9:33-9:44.5) the lava cone; no creature on any island, also in free flight after the
ending (16:30-16:57). Code: `game/scripts/world/island_proxy.gd` (the island as seen from the air).
DECISION: an island whose boss is NOT beaten shows its creature (Cyclops on the Quarry Isle, Medusa on the Sanctuary,
Hydra on the Volcano) walking a slow loop round its arena with the walk clip (idle and turn clips at the ends of the
loop are fine). Beaten bosses are not shown (the ending card says they have fallen). On islands still behind the storm
wall the creature walks too, but the wall may hide it. The proxy creature has no collision and no AI, and uses a light
copy of the model (no extra fight logic, keep the 120 fps hold).
Acceptance:
- `--start=sea --harness --bot=win` shots every 0.5 s: the next open island's creature is recognisable (at least
  30 px tall at 1280x720) from 300 m out and moves between shots (position changes, legs cycle); seen from above when
  passing over it.
- `--start=sea --defeated=cyclops` shows Medusa and the Hydra, not the Cyclops; `--defeated=all` shows none.
- Frame times on the sea do not get worse than today's (perf_probe on `--start=sea`, 99 % under 11.1 ms at 1920x1080).
- Landing still works and the fight scene starts as before (the proxy creature is removed when the fight loads).

### 5. NEW: more visual effects when a strike cuts a creature, and visible damage
Seen (frames 12, 13): a weak-point hit on the Cyclops (5:50.4) flashes the WHOLE Cyclops near-white for about 0.1-0.2 s
(`character_visual.gd` `flash()`, 0.85 strength, 0.12 s), then a few small yellow dots at the hand (5:50.6) and small
dust puffs (5:51.0). Nothing stays on the body. A Hydra hit (13:39.9) shows one orange-white puff with sparkles at the
neck, hard to read inside the fire breath. No slash trail on the sword, no cut, no wound.
DECISION: stylised, not gory (golden/dark ichor and glowing cuts, no realistic blood), in the game's cel look.
Acceptance (each fight, `--bot=win` with `--shot-on=<weak point hit event>@0.0:6` style shots, plus a 30 fps movie
of 3 hits):
- Every weak-point hit shows within 0.05 s: a sword trail along the swing arc, a burst of sparks plus ichor droplets at
  the hit point clearly larger than today's dots (readable at 1280x720 from the game camera, also inside the Hydra's
  fire), a hit-stop of about 50-80 ms and a small camera shake; the creature flinches.
- Visible damage: a cut / wound mark appears on the creature at the hit point and stays until the fight ends; marks add
  up with each hit (the third hit shows three marks); after the hit the weak point area looks hurt.
- The whole-body white flash can stay but must not hide the new effects (shorter or weaker is fine).
- Glancing hits (not a weak point) keep today's spark and clang, unchanged.
- No new first-use freeze: re-run `fx_capture.gd` + `fx_warm_build.gd` for new materials (tools/probes/README.md);
  no frame over 60 ms in a cold-cache fight.

### 6. "A little bit of clipping through some of the areas"
He did not say where. Seen in the recording (frames 14-17, 04, 05, 10), in order of how visible they are:
- 5:51.0 (Cyclops): standing against the Cyclops's leg, Hercules's head and shoulder are inside the leg (frame 16).
- 5:00 (Cyclops): Hercules stands INSIDE the club lying on the ground after the slam (frame 15).
- 13:30 and 15:00 (Hydra): Hercules stands inside the lowered head; at 15:00 his sword arm is inside it; 10:10 the
  shield goes into the lowered head (frame 17).
- Mounting: 1:39.5 he stands in the flank/wing just before the snap; 7:03.0 the near wing passes through his legs.
- In flight: the blade enters Pegasus's flank (6:30.5) or lies across his thigh (2:08, 16:10) (fixed by item 1).
- Home island (small, seen at sheet scale only): he walks into the amphorae at 1:34.5-1:36.0 and the shield overlaps the
  brazier/urn at 6:59.0 (probably no collision on those props; check at close range before fixing).
- 9:43-9:44.5 the flight camera is very close to the volcano's slope at the landing ring (possible camera clipping;
  check).
Acceptance:
- Probes that put the hero against each boss's legs and the lowered Hydra head (and the Cyclops club on the ground):
  the hero's body never overlaps the boss mesh by more than 0.1 m (he is pushed out or blocked), screenshots from the
  game camera show no head, arm or legs inside a boss or the club.
- Home: walking straight into the amphorae, the brazier, the pedestals and the sign stops at their surface.
- Flight: the camera never enters island geometry (no frame with the camera inside a mesh on the 3 landings).

## Not requested (noted, leave unless a fix above touches it)
- Flying into the landing ring's light pillar turns the screen bright yellow-white for about 1 s (7:23.5-7:25.5).
- The home sign/HUD wording, the pause menu, the controls page: unchanged.
