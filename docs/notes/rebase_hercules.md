# Re-base pass: hercules (2026-11-23, re-base animator; owner at the Mac, not asked, decisions noted)

Clips with their OLD reference video that were re-based onto `natural_pose.json` and given quiet life. Machine summary:
`art_src/chars/hercules/rebase_done.json`. Every file I replaced sits beside it as `<name>.rest_v1.json` / `.rest_v1.jpg`
(keys, action, strip). Not touched: the blend, game/assets, idle / run (V clips, new videos idle_n / run_n), death (K).

## The tool (work/rebase/hercules/)
- `rebase.py build <clip,...>` -> `rebase_bl.py` (headless Blender, blend opened read-only, never saved) -> `ak bake --out-action`.
  `life.py` holds every clip's life spec (degrees, view axes, periods). `strips.py <clip> <folder>` = old/new strip pair,
  `measure.py` = moving joints / pops / events old vs new (`measure.txt`).
- Method, per frame of the clip (24 fps): read the ORIGINAL action back (`action_<clip>.rest_v1.json`), then per bone:
  - **rest bones** (local turn < 3 deg in the whole clip: no key lists them) -> the natural-stance local basis; any small
    motion they had is kept as a delta on top. Typical: spine_03, shoulders, hand_l, fingers (now closed on sword and
    shield grips), toes, hips in the one-shots.
  - **acting bones** -> kept in their ORIGINAL world orientation (absolute, as the animator keyed them). One-shots blend
    that orientation from / to the natural stance over the first / last 0.15-0.3 s (slerp, smoothstep).
  - **hit** only: every bone is moved as a delta from the old ready pose onto the natural stance (the flinch keeps its shape).
  - **life** = small view-axis rotations on top (children ride along, except the attacks' sword arm: `no_ride`).
    Loops: every period = length / whole number (seam exact). One-shots: life fades to 0 at both ends and at chain points.
- Output keys: one inline absolute pose per frame in `keys_<clip>.json` (every original key time is still a key, same
  interp per span; `rebase` block names the source and the bone classes). `ground: lowest` per key as before (ride: none).
- Ground and contracts: lengths, loop flags and events are byte-identical to before for all 11 clips (measure.py).

## Per clip (moving joints >= 3 deg, as tools/clip_motion.py counts them, of 24 posed joints)
| clip | moving old -> new | what I did | still stiff / why |
|---|---|---|---|
| block_idle (loop 2.5 s) | 5 -> 19 | guard and crouch kept (world orientation); breathing in spine_01-03 + shoulders (one breath per 2.5 s loop: a 3.5 s breath cannot loop seamlessly in 2.5 s and the plan keeps 2.5 s), hips weight shift 2.7 deg with the thighs counter-rotated (feet stay), head peeks over the rim (chin up 5 deg) and back, neck/head turn on 2.5 s and 1.25 s periods (never in unison), sword hand re-grips (fingers pulse 10 deg, wrist 5 deg), shield arm rises with the breath | hips (kept: natural hips would change the skirt line under the crouch), fingers_l, hand_l, toes. Max 2.1 deg/frame. block_start end / block_end start differ from block_idle frame 0 by 0.92 deg (shoulder_r: breath phase offset), invisible under the game's 0.1 s blend |
| strafe_l (loop 0.833 s) | 8 -> 19 | legs, hips exactly as keyed; sword arm counter-swings 9 deg out at the widest step, sword tip lags, shield arm bobs at the step rate 1 frame late, spine_03 counter-rotates 5 deg, neck/head cancel it (eyes stay on the target) with a small bob, shoulders follow the arms, breathing at the cycle | fingers_l, hand_l, toes, hips |
| strafe_r | 8 -> 19 | `ak mirror --keys` of the new strafe_l, then the strafe_l upper body (shoulders, arms, hands, fingers, spine_01-03, neck, head) restored per frame, same rule as the previous strafe_r (sword stays right) | as strafe_l |
| walk_back (loop 0.5 s) | 8 -> 19 | legs/stride/feet exactly as keyed; sword arm swings 6 deg against the legs, shield arm 3.8 deg opposite, chest counter-rotates 4.5 deg (spine_01/02 opposite twist), head cancels it and bobs with each step, sword tip sways behind the hand, shoulders follow | fingers_l, hand_l, toes, hips |
| block_start (0.25 s) | 15 -> 16 | starts on the natural stance (was the old lunge idle k0), shield raise kept, ends on block_idle frame 0 | the raise itself is the original 0.25 s snap (43 deg/frame on upper_arm_l, as before) |
| block_end (0.25 s) | 15 -> 16 | starts on block_idle frame 0, lowers into the natural stance | as block_start |
| attack_1 (1.25 s, active 0.458-0.708, chain 0.917) | 14 -> 16 | sword arm exact (world angle diff at every original key 0.0001 deg), legs as keyed; first 0.25 s blends from the natural stance into the original step-into-lunge, last 0.3 s (after the 0.917 chain pose) back to natural; shield arm tucks in during the swing (-13 deg forward, 8 deg in), left shoulder, chest twist and head track the blade (pulses that end before 0.917) | fingers stay closed (grip, not frozen-open), hips. Chain pose at 0.917 == attack_2 frame 0 to 0.00 deg |
| attack_2 (0.833 s, active 0.25-0.458) | 12 -> 15 | chop arm exact (0.0002 deg); head/neck nod and turn with the chop, chest follows, shield arm braces; ends on the natural stance over the last 0.25 s | forearm_l twist flips 85-88 deg/frame at 0.583-0.625: that is in the ORIGINAL keys too (85.1, 78.0), I did not change it; worth a look by the attack animator |
| hit (0.458 s) | 10 -> 16 | flinch kept as a delta on the natural stance; knees give (thigh -7, shin +12 deg, ~2-3 cm) and recover, shoulders hunch, head snaps, off-hand pulls in | feet planted (correct) |
| roll (0.708 s) | 16 -> 16 | tumble untouched in the middle; first/last 0.2 s blend from/to the natural stance (was the old lunge) | hand_l, fingers (closed), hips |
| ride (loop 1.5 s, art_src/chars/ride/clips/ride/) | 4 -> 9 | seat untouched (root, hips, legs identical; lowest point still 0.19 m as before); torso pitches 2 deg per spine bone with each wing beat with lag down the spine, breathing, neck counters the pitch, head looks left/right 8 deg once per beat and nods at the double rate, free sword arm balances a quarter beat late (out 7, fore/back 4 deg), shield arm rides a frame behind, hands closed | legs keep their grip (by design: seat must not move); shoulders and spine_02/03 under 3 deg each though the chest moves ~5 deg in total. Not checked against Pegasus' wings in ride_check.blend (the rider moves by a few cm at most; wing clearance there was 0 hits with the 10 deg sweep) |

All one-shots start and end on the SAME natural pose (max difference between their first/last frames: 0.00 deg).

## Looked at (strips, work/rebase/hercules/strips/<clip>_cmp.jpg: OLD rows above NEW rows; clip folders have strip_<clip>.jpg)
block_idle, strafe_l, walk_back, attack_1, hit, roll, ride: no limb through the body, no pop at start/end/seam, sword and
shield readable; one-shots now stand naturally at both ends instead of the wide lunge. ride's strip uses the ride cam (small figure).

## For the assembler / lead
- `ak merge` re-bakes from the `poses` in each action JSON: the new clips have 7-61 keys (one per frame), all inline.
- If the idle_n animator's new idle frame 0 differs from natural_pose.json, re-run `python3 work/rebase/hercules/rebase.py build
  block_start,block_end,attack_1,attack_2,hit,roll` after pointing `NAT` in rebase.py at that pose (1 min).
- Requests: attack_2 shield forearm twist flip (original); block_idle could become 3.5 s for a slower breath if the lead allows a length change.
