# cyclops / walk_n reference: animator notes (2026-11-23, natural-animation pass)

walk | video window 2.583-4.083 s (t0 2.583, one 1.5 s cycle = two steps), retimed x0.9444 to the game loop | loop, 1.4167 s
(34 frames @ 24 fps, unchanged) | 10 keys (6 traced + fitted: R lift/high/contact, L lift/high/contact; 4 authored:
settle + mid-stance per step) | key IoU front/side vs the video at the matching (scaled) time: 0.93/0.73, 0.90/0.81,
0.89/0.75, 0.83/0.76, 0.84/0.75, 0.83/0.73, 0.81/0.70, 0.79/0.74, 0.85/0.84, 0.91/0.79 (mean 0.86/0.76) | strip mean IoU
0.72 (24 samples, compared 1:1 in time, so up to 0.08 s off the scaled video, and the video zooms in ~5%) | events: step 0.40
(right heel strike, name and time kept; left heel strike at 1.125 = step + length/2, which is what cyclops.gd assumes).

## Gait numbers (measured on the bake with `ak solve`, every frame)
- Footfalls every 0.708 s (17 frames), right at 0.4167, left at 1.125. Each foot is planted ~14 frames (0.58 s).
- Planted foot travels 1.48 m per stance at an even 0.09-0.12 m/frame: planted-foot speed ~2.54 m/s at clip speed 1
  (old clip 2.6 m/s; `walk_speed` 2.6 is within 2.5%: no re-tune needed). Stride (ground covered per 1.4167 s cycle at that
  speed) ~3.6 m, two steps of ~1.8 m. Swing foot lifts 0.14-0.23 m (video: 0.23 m). Feet -0.03..+0.06 m in the strip.

## Every limb group moves (local rotation range over the clip, degrees; 28 of 29 bones move >= 3 deg, only the
## non-deforming `root` bone is still)
legs 73-75 (thigh/shin), feet 28, toes 31 (toe stays flat at toe-off) | hips 12, spine 8-16, neck 20 (counter-turn), head 5
(level, looks ahead, small nod + turn per step) | upper left arm 48 / forearm 21 / shoulder 8 (swings opposite the left leg)
| lower arms 24-36 (opposite the legs, lagging) , hands 9 | club arm: shoulder 13, upper arm 7, forearm 6, hand 3.3
(club bounces: dips ~3 deg after each footfall, by the shoulder drop and a +-1.5 deg grip roll).
Every key is the natural stance (natural_pose.json) merged with the bones this clip changes: no bone comes from the rest pose.

## Decisions (owner not asked)
- The video is clean and usable: calib_iou 0.95/0.96, panels in sync (front foot lifts match the side steps), cycle 1.5 s
  (`ak cycle` 3.0 = two cycles). 4.4-5.3 s has a stutter (right foot steps twice); window chosen before it.
- The video's left step is longer than its right (feet land 0.65 s / 0.85 s apart). The game needs footfalls exactly half a
  cycle apart, so the left step's LEGS are the mirror of the fitted right step; trunk, arms, head and club stay unmirrored
  (the club is on the right shoulder).
- Body sway: the video keeps the pelvis at +0.3 m (over the left leg) even while the left foot swings, which cannot balance.
  Used a physical sway instead: pelvis 0.25 m left over the left foot, 0.12 m during the right-foot stance.
- Foot slide: the raw key poses moved the planted foot unevenly (1-4.6 m/s). Fixed with a per-key body surge (root.loc y
  -0.23..+0.15 m, a heavy forward-back lurch the side view also shows, ~0.35 m) so the planted foot moves evenly.
- Club: kept exactly the natural-stance grip (resting on the right shoulder) so walk <-> idle blends have no pop. The video
  draws the club ~10 deg flatter (more horizontal) than the sheet; not matched. Changing the hand aim by 3 deg flips the club
  roll (aim form near 180 deg is unstable for hand_u_r): the bounce is done with shoulder/upper-arm drop and the hand twist.
- Trunk: `ak fit` used spine_01/hips to absorb framing (+-16 deg); replaced by a smooth forward lean 12-17 deg at spine_03
  with a 2-3 deg dip at each contact.

## Files
keys_walk.json, poses_walk/k*.json (10), action_walk.json, strip_walk.jpg, strip_walk.mp4 (this folder).
Scratch work/anim2/cyclops_walk_n/: gen.py (first poses), fit logs, ana.py (foot lift per frame), sway.py, feet.sh
(foot speed per frame via ak solve), motion.py (rotation range per bone from an action JSON), strips v1-v11.
