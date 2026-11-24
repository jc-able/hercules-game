# Natural stance: hercules (2026-11-23, natural-stance agent; owner at the Mac, not asked, decisions noted)

Files: `art_src/chars/hercules/natural_pose.json` (animkit pose), `art_src/chars/hercules/sheet_nat_std.png` +
`cam_nat_std.json`. No `sheet_nat_wide`: both planned videos (idle_n, run_n) stay in place, and every existing Hercules
clip was matched on the std framing (all clip `cam.json` = 191.0 px/m, centre_y -0.25).
Scratch (stance helper, posed blend copy, views, strips): `work/natural/hercules/` (`stance.py` renders front / side /
three-quarter / back of any pose JSON and prints ground and prop positions; `nat_stance.blend` = a COPY of hercules.blend
with absolute texture paths and the stance keyed on frame 1, only for render_split_sheet.py; never use it for clips).

## What reads stiff now (`python3 tools/clip_motion.py hercules` + `ak strip` of idle, run, strafe_l, walk_back, block_idle)
| clip | moving | what the strip shows |
|---|---|---|
| idle | 6/29 | a wide lunge (left leg forward, right back) held like a statue: 6 frames over 3.5 s are identical to the eye; head, neck, spine, legs, hands frozen |
| run | 19/29 | arms pump and the sword swings, legs fine; head, spine_03, left hand frozen; the head does not bob or look |
| strafe_l / strafe_r | 10/29 | crab walk in a deep crouch, the whole upper body (both arms, head, neck, spine_03) locked in the guard |
| walk_back | 10/29 | legs step, sword arm, head, neck and spine locked in the guard |
| block_idle | 5/29 | shield up, crouch, only 5 joints move: no breathing, no head |
| ride | 3/29 | a seated statue on the horse |
| hit | 10/29 | the upper body flinches, the legs do not react |
| attack_1/2, block_start/end, roll | 16-21/29 | acting limbs fine; shoulders, hand_l, fingers, head (attack_2) frozen; all start/end on the OLD idle k0 lunge |
| death | 23/29 | fine (full-body fall) |

## The stance (natural_pose.json)
A hero at ease but ready. All angles in animkit view axes (absolute unless marked local_delta).
- Weight a little on the RIGHT (sword) leg: hips ry 2 (left hip drops), rz -5 (left hip comes forward); right thigh rx -3
  ry 0 (more upright than rest's 7 deg splay, so the pelvis sits over the right foot), right shin rx 4 (soft knee), right
  foot toes out (rz -8).
- Relaxed LEFT leg: thigh rx -11 (forward), ry -8 (out), rz 10 (turned out), shin rx 3, foot rx 4 (toe touches first), rz 12.
  Feet about shoulder width (ankles 0.48 m apart; shoulders 0.45 m).
- Torso: spine_01 local_delta rx -2 ry -4 rz 4, spine_02 rx -3 ry -1.5 rz 2 (chest open and up, shoulders tilt against
  the pelvis = contrapposto), spine_03 rx 1. Neck rx 3 rz 3, head rx -3 ry -2 rz 6: head up, glancing a little to his left.
- Sword arm: upper_arm_r aim front 14 / side 4, forearm_r front 10 / side -14 (elbow soft), hand_r local_delta rx 30 ry 10:
  the blade hangs DOWN and a little OUT beside the right leg (tip 0.13 m above the floor, x -0.45 m: shows beside the right
  leg from behind). fingers_r curled 75 deg about its own X (grip).
- Shield arm: upper_arm_l front -16 / side 8, forearm_l front -14 / side -62 / twist -20 (bent ~60 deg, forearm forward-down),
  fingers_l curled 70 deg: the shield hangs vertical at his left side, face outward (+X), bottom rim 0.74 m.
- Root: ground "lowest" (root z -0.012).
- Checks (ak solve): lowest vertex left foot 0.0011 m, right foot 0.000 m. Views (front, side, 3/4, back) show no arm through
  the torso, no shield through the arm or head, sword clear of the leg (`work/natural/hercules/v4/`, `v5/`).
  Iterations: v1 sword pointed 45 deg forward and the shield top leaned into the left shoulder, left foot 3 cm up;
  v2 hand_r rx 30 / ry 10 and forearm_l twist -20 (the +20 twist tilted the shield into the chest); v3/v4 straightened
  the left knee and tipped the left toe down until the foot touched (2.4 cm -> 0.1 cm).
- Note: the finger curls are stored as view-axis local_delta eulers computed for THIS hand pose (stance.py `--curl`); if an
  animator changes the hand a lot, re-curl with `stance.py --curl fingers_r=75,fingers_l=70`.
- The game turns the sword -25 deg about hand_r Z and the shield +40 deg about forearm_l Y on top of the blend (socket_offsets
  note in hercules_clips.json); the sheet shows the blend's props, as the old sheets did.

## Sheet
`sheet_nat_std.png` 1280x720, FRONT | SIDE (facing right), white, 191.04 px/m in both panels, front_w 650 / side_w 630,
centre_y -0.25: rendered with `--env 1.7,1.4,1.9,3.39`, which reproduces `cam_std.json` exactly, so the new videos frame like
the old ones. Both panels show the same pose, nothing cut off.

## Plan per clip (V = new Seedance video from sheet_nat_std, R = re-base + quiet life, K = keep)
| clip | action | what to do |
|---|---|---|
| idle | V idle_n | the stance on the home island; whole new idle from idle_n |
| run | V run_n | his locomotion clip (he has no walk): re-key from run_n so head, chest, shield hand and sword swing all act |
| strafe_l | R | legs as keyed; sword arm counter-swings 5-8 deg with the steps, shield arm bobs 1 frame late, spine_03 counter-rotates 3-4 deg, head steady on the target with a small bob, breathing |
| strafe_r | R | `ak mirror --keys` of the new strafe_l (as before) |
| walk_back | R | legs as keyed; small arm swing against the legs, torso bob, head level looking ahead, sword tip sways |
| block_idle | R | keep the guard (shield up, crouch); breathing in spine_01-03 + shoulders, head peeks a little over the rim and back, sword hand re-grips, slow weight shift in the hips; 2.5 s loop kept |
| block_start | R | first key -> new idle frame 0 (was the old lunge idle k0), last key = block_idle frame 0; shield raise kept |
| block_end | R | rebuilt as block_start reversed (same rule as now) |
| attack_1 | R | sword arm and legs exactly as keyed (active 0.458-0.708, chain 0.917 unchanged); first/last key -> new idle frame 0 with the left foot stepping into the lunge in the first ~0.15 s (no foot slide); shield arm tightens to the chest in the swing, shoulders and spine_03 follow through, fingers_r closed |
| attack_2 | R | acting arm as keyed; head and neck track the swing; last key -> new idle frame 0; start stays the attack_1 chain pose |
| hit | R | upper-body flinch kept; knees give 2-3 cm and recover, shoulders hunch; start/end on new idle frame 0 |
| roll | R | tumble kept; only the first/last key re-based onto new idle frame 0 (was the old lunge) |
| death | K | full-body fall, 23/29 joints move, ends in its own pose; the game's blend from the new idle covers its first frames |
| ride | R | seat and leg grip kept; torso pitch with Pegasus' wingbeat (1.5 s loop), head counter-moves and looks around, arms bob a frame behind the torso; no video (no two-character renders) |

Timing contracts: names, loop flags, events unchanged. `idle` has no events: its length may move from 3.5 s to the cycle
measured on idle_n (2-4 s). `run` may change length and `move_speed` (currently 0.833 s / 3.64 m/s): the animator measures
both on the new keys and reports old and new numbers (player.gd speed_scale uses move_speed).

## Prompts (the lead adds the fixed split-screen header; 480p, 10 s, first frame = sheet_nat_std.png)
**idle_n** (game clip: idle)
Motion: He stands at ease but ready on the spot, feet planted shoulder-width apart, weight mostly on his right leg, left
knee soft. He breathes slowly, one breath every 3.5 seconds: chest rises, shoulders lift a little, then settle. Around 4
seconds he shifts his weight onto his left leg and back by 7 seconds, hips swaying. His head turns slowly
to look left, then ahead with a small nod. His right hand flexes its grip, the sword swaying slightly beside his
right leg, blade down. His bent left arm holds the round shield at his side, rising and falling with each breath. He
stays in place and keeps his design.

**run_n** (game clip: run)
Motion: Starting from the relaxed stance, he runs in place on the spot like on a treadmill at a steady athletic run,
about two and a half steps per second. His knees lift and his feet strike the ground under his hips. His arms swing
opposite to his legs with bent elbows: the right arm carries the sword low, blade angled back, swinging forward and back
with each stride; the bent left arm pumps the round shield at his side. His torso leans slightly forward and twists
against his hips, his chest heaving, and his head stays level, looking ahead and bobbing gently with each step. He keeps
his design.

No generation submitted, no credits spent.
