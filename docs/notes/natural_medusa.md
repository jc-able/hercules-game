# Natural stance + clip plan: medusa (natural-stance agent, 2026-11-23)

Owner at the Mac, no questions: every decision below is mine and written down. Scratch: `work/natural/medusa/`
(`view3.py` = apply a pose with animkit's Rig, render front/side/top + front/3-4/side close-ups, or bake the pose as a
one-frame action into a scratch COPY `medusa_nat.blend`; the source blend was only opened read-only).

## 1. What reads stiff today (`python3 tools/clip_motion.py medusa` + strips in `work/natural/medusa/strip_*.jpg`)
| clip | moving | what reads stiff |
|---|---|---|
| idle 3.0 s | 18/35 | arms locked in the rest A-pose (upper arms, forearms, shoulders frozen), head/neck/spine frozen: a statue whose tail and snakes breathe; tail dead straight back |
| slither 2.0 s | 26/35 | the approach: tail waves, but the arms stay spread in the A-pose (hands, shoulders frozen), spine_03 frozen, head only +-3 deg: a mannequin gliding |
| gaze 4.25 s | 17/35 | the whole tail frozen straight back during the stare, hands and shoulders frozen; acting head/arms fine |
| hurt 1.625 s | 15/35 | whole tail + pelvis frozen: only the upper body flinches |
| stun_start 1.625 s | 27/35 | shoulders, tail_01/02/04/08/09 frozen; starts from the rest pose `{}` (pop when blended from the idle) |
| stunned 3.0 s loop | 13/35 | slumped on the floor, arms, spine and tail_01..09 frozen: no breathing |
| rise 2.5 s | 25/35 | shoulders and half the tail frozen; ends in the rest pose |
| tail_swipe 2.25 s | 25/35 | head and neck frozen while the tail spins 360 deg (she does not watch her own sweep); arms/hands frozen |
| death 3.5 s | 30/35 | only hands/shoulders frozen; starts from the rest pose |
No pops or mesh-through-mesh seen in the strips; the problem is frozen limb groups and the A-pose arms, plus mirror-symmetric
hair snakes (all six fanned out level).

## 2. The natural stance: `art_src/chars/medusa/natural_pose.json`
In words: a towering serpent woman at rest. Torso in a soft S-curve over the tail (pelvis tilted 6 deg to her right, the chest
curving back 8 deg toward her left), shoulders dropped (left 6 deg, right 4 deg: not symmetric), head tilted 9 deg toward her
right shoulder, turned 18 deg to her left (spine_03 4, neck 5, head 9), chin 8 deg down. Right arm hangs relaxed beside the hip with a soft elbow (upper arm
18 deg out, forearm 32 deg forward), right hand open at the side of the hip armour. Left arm a little raised: upper arm 24 deg
forward, forearm almost level and pointing forward (98 deg), open palm turned up-inward (twist 45). The six hair snakes each in
their own direction (one up, one down, forward/back yaw 10-25 deg, none mirrored). The upright tail carries the S (tail_03 +6 deg),
the floor tail runs back, bends 5 deg to her left, then sweeps to her right in a widening curve (yaw per link 0,-5,-3,4,9,13,16,20,34)
and the tip curls (50, 62 deg).
Numbers (pose applied, grounded): lowest vertex z = 0.000 m (tail on the floor; root z -0.009 m), head joint (-0.07, -0.95, 5.43),
hand_r (-0.93, -0.93, 3.70), hand_l (0.68, -1.43, 4.16), tail tip joint (-2.46, 4.74, 0.32); body bbox x -2.67..1.03, y -2.16..5.73,
height 6.81 m. Checked in front, side, top, front close-up, 3/4 close-up, side close-up (`work/natural/medusa/it/nat.png`): no hand
in the hip armour, no forearm through the breastplate, tail curl does not touch itself, no arms held out.
Iterations: v1 right hand sank into the hip armour and the S-curve did not read -> v2: elbow out 18 deg, hand turned out, pelvis
tilt 4 -> 6 deg, chest back +4 deg; tail curve made tighter (front-panel extent -3.48 m -> -2.46 m so the slither waves fit).

## 3. New split sheet
`art_src/chars/medusa/sheet_nat_std.png` + `cam_nat_std.json`: 1280x720, 64.65 px/m in BOTH panels, FRONT 452 px | SIDE 828 px
(faces right), white, ground at 8 %. `--env 3.5,9.8,3.0,7.4` (front x +-3.5 m, side 3.0 m in front .. 9.8 m behind, top 7.4 m):
wider than cam_std (+-3.0 m, ppm 69.9) so the slither waves stay in the front panel and the straightened tail (9.3 m) in the side
panel. Command: `render_split_sheet.py -- --in work/natural/medusa/medusa_nat.blend --out sheet_nat_std.png --cam cam_nat_std.json
--size 1280x720 --frame 1 --env 3.5,9.8,3.0,7.4` (the scratch copy holds the stance as a 2-frame action; textures resolve, no magenta).
Both panels show the same pose, nothing cut off, 16:9. **No nat_wide**: no V clip needs more room (stunned/death/tail_swipe are R).

## 4. Plan for every clip (V = new video, R = re-base frozen groups onto the stance + quiet life, K = keep)
| clip | plan | what to do |
|---|---|---|
| idle | **V idle_n** (nat_std) | the start-of-fight idle. Cut a 6.0 s loop (two 3 s breaths + one full weight shift; was 3.0 s, no events, nothing times on it). Frame 0 = natural stance exactly (one-shots blend from it). Key all groups: spine breath +-2 deg, hips/torso weight shift, head turn, both arms, 6 snakes with separate phases, tail tip flick. |
| slither | **V slither_n** (nat_std) | the approach toward Hercules. Cut a 2.0 s loop (keep length: `move_speed` and the tail wave period are tuned to it; change only if the video's wave period differs, then report old/new). Key arms swinging against the hip sway, torso counter-sway + slight lean, level head, lagging snakes; tail S-waves as before. |
| gaze | R | head thrust, arm raise/throw-out and rearing snakes stay as keyed (events 2.0/3.25 unchanged). Tail (frozen 01..14) re-based onto the stance curve with a slow wave that tightens/braces during the stare (2.0-3.25) and relaxes after; shoulders follow the arm raise (shrug 5-8 deg), wrists flex. First/last 0.3 s blend from/to the natural stance. |
| hurt | R | flinch, neck clutch and head throw stay as keyed. Pelvis dips 0.08 m and recoils; a recoil ripple runs down the tail (phase lag ~0.06 s per link, decaying); free arm and shoulders react. Starts and ends in the natural stance. |
| stun_start | R | recoil + collapse as keyed. Replace the rest-pose first key with the natural stance (blend over 0.25 s); shoulders follow the arms over the eyes; tail_01/02/04/08/09 get the natural curve and lag the body. End pose unchanged (it hands over to stunned). |
| stunned | R | slumped pose kept (head stays where it is: weak point / gaze socket). Add breathing in spine_01..03 (+-2 deg, one breath per 3 s), weak twitches of hands/forearms (2-4 deg, out of phase), slow tail-tip curl +-8 deg and a faint wave down tail_05..09. Loop 3.0 s unchanged. |
| rise | R | push-up as keyed; the last 0.5 s now ends EXACTLY on frame 0 of the new idle (natural stance) instead of the rest pose; shoulders and the frozen tail links follow with lag. |
| tail_swipe | R | the tail is the acting limb: tail_04..14 stay exactly as keyed (impact 0.833 s, hit radius tuned on it). Head/neck turn to watch the sweep (yaw lagging the tail ~0.1 s, up to 25 deg split neck/head/spine_03), arms counterbalance against the spin, shoulders/hands alive. Starts from and returns to the natural stance. |
| death | R (light) | shriek, arch, collapse kept. Replace the rest-pose start with the natural stance (blend over 0.3 s); shoulders/hands follow the rising arms; final lying pose unchanged. |

## 5. Seedance motion texts (the lead adds the fixed split-screen header; 480p, 10 s, first frame = sheet_nat_std.png)
**idle_n** (sheet nat_std, cut: idle): She rests upright on the spot and holds her design. Her chest rises and falls in one slow breath every 3 seconds, her shoulders lifting slightly. Over 6 seconds her torso shifts its weight to her left and back again in a soft S-curve, never rocking like a pendulum. Her head tilts and turns a little to her left, then returns. Her right arm hangs loosely by her hip, fingers curling; her raised left hand slowly turns its open palm. The six snakes of her hair move separately, each at its own pace. Her curved tail stays on the ground; its curled tip lifts and flicks gently twice.

**slither_n** (sheet nat_std, cut: slither): She glides forward on the spot, staying in place and holding her design. Her tail drives continuous S-shaped waves along its whole length on the ground, one wave every 2 seconds, travelling from her hips back to the curled tip. Her upright body rides the waves: her hips sway from side to side and her torso counter-sways, leaning slightly forward. Her arms swing loosely and alternately, elbows bent, the left forward as the right goes back. Her head stays level and looks ahead, tilting slightly into each sway. The six snakes of her hair trail behind her head and sway separately, each with its own delay.

No generation submitted, no credits spent.
