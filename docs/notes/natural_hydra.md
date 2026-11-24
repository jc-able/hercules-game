# Natural stance + clip plan: hydra (natural-stance agent, 2026-11-23)

Owner at the Mac, no questions asked: every decision below is mine and written down. Scratch: `work/natural/hydra/`.
The source blend `art_src/chars/hydra/hydra.blend` was only opened read-only (ak, and `render_nat.py`, which applies a pose
with animkit's Rig and can save a one-frame COPY `work/natural/hydra/hydra_nat.blend` with absolute texture paths).
Nothing was generated and no credits were spent.

## 1. What reads stiff today (`python3 tools/clip_motion.py hydra`; strips `work/natural/hydra/strip_*_old.jpg`, `strips_old.jpg`)
| clip | moving | what reads stiff |
|---|---|---|
| idle 3.0 s loop | 0/76 | a statue: every bone frozen, the nine heads in the mirror-symmetric rest fan (4 pairs at 8.3 / 10.0 / 11.4 / 12.8 m) |
| walk 2.17 s loop | 24/76 | only legs and tail move; all nine heads, the jaw, all neck links except tiny bobs, spine frozen: a fan of heads carried rigidly over walking legs (the owner's complaint) |
| bite / bite_l / bite_r 3.5 s | 43-45/76 | the acting neck strikes, the other heads stay in the rest fan; hind legs and tail frozen; starts and ends in the rest pose |
| fire_sweep(_l) 4.6 s, fire_sweep_return(_l) 2.77 s | 41-47/76 | centre neck sweeps, all eight side HEADS frozen (necks only splay), hind legs, spine_03, tail frozen |
| stomp / stomp_r 3.0 s | 25/76 | one foreleg acts; all heads frozen, the necks barely move, spine/hips frozen (no weight shift onto three legs), tail tip frozen |
| head_down 1.5 s loop | 25/76 | centre bow is right; the eight side heads and five necks frozen, no breathing |
| head_up 1.5 s | 47/76 | side heads frozen; ends in the rest pose |
| hurt 0.9 s | 39/76 | side heads, front legs, spine, tail frozen: only the centre neck flinches |
| hurt_standing 1.63 s | 51/76 | head_c and jaw frozen (the hit head does not react), spine frozen |
| death 3.8 s / death_standing 5.5 s | 60-63/76 | fine thrash; tail_03..08 frozen (the tail end hangs dead during the thrash); starts from the rest pose |
No pops or limbs through the body were seen in the strips; the problem is frozen limb groups and the symmetric rest fan
that every clip starts from (and returns to).

## 2. The natural stance: `art_src/chars/hydra/natural_pose.json`
A nine-headed beast standing ready, relaxed: body settled 0.10 m on soft elbows/knees, weight on the right-fore / left-hind
diagonal (left fore 6 deg forward, right hind 5 deg back), chest turned a little to its left (spine yaw 1.2 deg per link),
tail curled to its left (bend_side 3-8 deg per link, 54 deg in total, tip lifting slightly). The nine necks are loose
S-curves (base bends one way, the top links bend back; no hooks), every head at a different height and direction:

| head | joint position x / y / z (m) | looks | role |
|---|---|---|---|
| centre (head_c) | 0.36 / -2.99 / 12.23 | 7 deg to its right, 25 deg down, jaw_c 8 deg ajar | high, watching |
| 4 (right inner) | -3.09 / -2.80 / 10.99 | 7 deg to its left, 26 deg down | mid-high, leaning in toward the centre |
| 5 (left inner) | 2.20 / -2.40 / 11.48 | 23 deg left, 32 deg down | high, arching forward |
| 3 (right) | -4.87 / -0.69 / 10.37 | 71 deg to its right (sideways) | turned out to the right side |
| 6 (left) | 3.70 / -2.70 / 10.29 | 41 deg left, 22 deg down | forward-left |
| 2 (right) | -2.09 / -3.07 / 9.11 | 10 deg right, 29 deg down | low and forward |
| 7 (left) | 4.96 / -0.24 / 8.95 | 96 deg to its left (sideways, a little back) | out to the left side |
| 8 (left outer) | 3.14 / -2.54 / 8.43 | 63 deg left, 6 deg UP | low, looking out, alert |
| 1 (right outer) | -2.94 / -3.50 / 7.16 | 29 deg right, 29 deg down | lowest, forward, nosing down |
Rest for comparison: pairs at 8.32 / 10.00 / 11.42 / 12.75 m, mirror images, centre at 12.35 m.
Feet: every foot joint at 0.391 m (rest 0.380), lowest vertex left side 0.000 m, right side +0.008 m (within 0.02 m).
Bounds: x -6.32..6.59, y -5.32..10.13, z 0..14.24 m. Silhouette IoU against the rest pose 0.65 front / 0.73 side.

Decisions:
- Only the centre head has a jaw (`jaw_c`, fused mouth that stretches, <= 20 deg): it is 8 deg ajar. The eight side heads
  have no jaw bone, so "one or two jaws open" = the centre one only.
- Necks 3-6 cannot bring a head low AND in front of the chest: their bases sit 0.2-0.4 m behind the shoulders and the
  neck is 4.7 m long, so a low head lands on the shoulder plates. The low, forward heads are therefore 1 and 2 (bases at
  the front of the shoulders) and 8 low at the side; 3 and 7 are the side-lookers; 4, 5, 6 the mid-high group.
- Format: legs in absolute space (soft knees solved so every foot is flat at the same height, `work/natural/hydra/legs.py`),
  necks/spine/tail as `chain` bends (local_delta per link; index 4 of each neck_1..8 chain is the head, neck_c index 5 is
  head_c, index 6 jaw_c), root loc z -0.10 + `ground: lowest`. The heads were placed with a small numeric tuner on
  `ak solve` (`work/natural/hydra/tune.py`, targets in `targets4.json`, result `p_final.json`), then checked by eye in
  front, side, both three-quarter views and close-ups (`work/natural/hydra/look_v4.jpg`, `close_v4.jpg`).
- Known minor: from the three-quarter views heads 1 and 8 sit close above the shoulder plates (no visible penetration);
  necks overlap in the front projection but do not pass through each other in the 3/4 views.

## 3. New split sheet
`art_src/chars/hydra/sheet_nat_std.png` + `cam_nat_std.json`: FRONT | SIDE (faces right), white, 1280x720, 38.79 px/m in
both panels (old std 40.5), `--env 7.5,11.0,7.0,15.5` (x +-7.5 m because the side-looking heads reach x -6.3 / +6.6 and
sway in the idle; 7 m in front of the feet centre for the walk's forward reach and head nods; 11 m behind for the tail).
Rendered with `tools/blender/render_split_sheet.py --frame 1` from the scratch copy `work/natural/hydra/hydra_nat.blend`
(stance baked as the one-frame action `natural_stance`). Check: `ak pose` of natural_pose.json with cam_nat_std.json
against the sheet scores IoU 0.997 front / 0.998 side, nothing cut off. No `sheet_nat_wide`: no planned video needs it
(the old wide sheet only served fire_sweep and death, which are R clips).

## 4. Plan for every clip (game/assets/characters/hydra/hydra_clips.json, 17 clips)
V = new Seedance reference from sheet_nat_std; R = acting limbs stay as keyed, frozen groups re-based onto the natural
stance and given quiet life; one-shots start from and return to the natural stance unless they end in their own pose.
Contracts unchanged everywhere: names, loop flags, events and their times, sockets, `jaw` weak point, ground contact, in place.

| clip | plan | what to do |
|---|---|---|
| idle | V idle_n | re-match from idle_n: breathing every ~3.5 s, slow weight shift, centre head looks around, eight heads weave on their own rhythms, tail sways. Loop length may grow from 3.0 s to the measured idle cycle (no events depend on it). |
| walk | V walk_n | re-match from walk_n. Keep the existing leg generator (`clips/walk/poses_walk/gen_walk.py`, lateral sequence, duty 0.8) and the 2.167 s cycle / move_speed; necks, heads, jaw, spine, tail come from the new video on top of the natural stance (heads bob with phase lag, centre head level and looking ahead). |
| bite | R | centre strike as keyed (impact 1.5 s). Side heads from the natural stance: pull back and up 0.3 s before the strike, flinch outward at impact, settle with lag; hind legs brace (weight back in the coil, forward at the snap, feet planted); tail counter-swings. Start/end natural stance. |
| bite_l | R | acting left heads as keyed; right heads 1-4 and the centre neck (frozen today) re-based, centre head turns to watch the strike, the rest weave and recoil; hind legs, tail as in bite. |
| bite_r | R | mirror of bite_l: acting right heads as keyed, heads 5-8 and centre re-based + reaction. |
| fire_sweep | R | centre sweep and fire events as keyed (1.5-4.05 s). Side heads re-based onto the stance, lean away from the fire side and lift as the stream passes, phase-lagged, never in unison; tail counter-sweeps; hind legs/hips shift weight with the sweep. |
| fire_sweep_l | R | same as fire_sweep, other direction. |
| fire_sweep_return | R | same treatment; ends in the natural stance. |
| fire_sweep_return_l | R | same, mirrored; neck_4 (frozen) included in the re-base. |
| head_down | R | centre bow as keyed (jaw socket z <= 1.5 m contract). The eight side heads droop from the stance to tired low positions and pant/weave slowly; flanks breathe (spine), tail tip stirs. Loop seam clean. |
| head_up | R | centre rise as keyed; the side heads lift back with lag and the clip ENDS in the natural stance (not rest). |
| hurt | R | plays over head_down, so start/end on head_down's new side-head pose; centre recoil as keyed; side heads jerk up/back 0.1-0.2 s after the hit and settle; tail lash; front legs stay planted. |
| hurt_standing | R | start/end natural stance; head_c and jaw get a real flinch (they are frozen today), spine shudder; legs planted. |
| stomp | R | left foreleg and impact 1.75 s as keyed. Hips roll ~2 deg onto the three planted legs during the lift; heads rear up 0.5-1.5 s and whip down/forward at the impact with phase lag and a small bounce; tail lifts for balance. Start/end natural stance. |
| stomp_r | R | mirror of stomp. |
| death | R | re-base the first 0.3-0.5 s from the natural stance; thrash as keyed; tail_03..08 (frozen) get whip-like follow-through and a final flop. Ends in its own pose. |
| death_standing | R | same as death; spine follow-through in the thrash. |

V total: 2 (idle_n, walk_n). No K: every clip either starts/ends on the old rest fan or leaves a limb group frozen.

## 5. Seedance motion texts (what follows "Motion:"; the lead adds the split-screen header)
**idle_n** (sheet nat_std; game clip: idle), 108 words:
> The nine-headed beast stands relaxed on its four planted legs. Its chest and belly swell with one slow breath every 3.5 seconds, and its weight drifts from the right legs to the left and back over 7 seconds. The tall centre head looks calmly left, then right, its jaw easing open and shut. The eight side heads keep their loose S-shaped necks at different heights and weave independently, each on its own slow rhythm: the low heads sniff toward the ground and lift, the outer heads turn to look sideways, never two moving together. The tail sways lazily. It stays on the spot and keeps its exact design.

**walk_n** (sheet nat_std; game clip: walk), 107 words:
> The nine-headed beast walks in place on the spot with a slow, heavy four-legged gait, one full stride every 2.2 seconds: left foreleg, right hind leg, right foreleg, left hind leg, each foot lifting clearly and planting flat. The body rolls and dips with every step, shoulders rising over the planted foreleg. The tall centre head stays high, looks straight ahead and nods slightly on each footfall. The eight side heads keep their loose S-shaped necks and bob and sway with the steps, each a beat later than its neighbour, never in unison. The tail swings side to side against the shoulders. It keeps its exact design.

## 6. Files
- `art_src/chars/hydra/natural_pose.json`, `sheet_nat_std.png`, `cam_nat_std.json`
- `work/natural/hydra/`: `tune.py`, `legs.py`, `heads.py` (numbers from `ak solve`), `render_nat.py`, `p_final.json`,
  `targets4.json`, `hydra_nat.blend` (scratch copy with the `natural_stance` action), renders in `rend/`
- devlog: `docs/devlog/media_inbox/natural_hydra/` (4 JPEGs + captions.txt)
