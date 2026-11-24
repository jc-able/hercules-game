# Re-base of the cyclops clips (re-base animator, 2026-11-23)

Scope: every clip marked R in `docs/notes/natural_cyclops.md` (slam, sweep, pull_free, stuck, hurt, death). idle and
walk are V (new videos, other animators: `clips/idle_n`, `clips/walk_n`); no clip was K. Never wrote the blend or
`game/assets`; the assembler merges `action_*.json`.

## Tool (`work/rebase/cyclops/`)
- `rb_resolve.py` (headless Blender, read-only blend, imports `tools/animkit/ak_blender.py`): resolves every pose file
  (and read-backs of the old baked actions) into per-bone local and absolute rotations + bone positions.
- `rebase.py <clip> [--write]`: classifies bones over the clip's original keys: ACTING = listed and turning >= 4.5 deg
  (local), STILL = never listed or turning less. Then per key:
  - acting cells are copied verbatim (same entry, same key time, same interp);
  - the old rest "ready" keys are replaced by `natural_pose.json` (club on the shoulder);
  - gap cells (an acting bone a key does not list = it snapped back to rest at that key) = local slerp between the
    neighbouring keys that list it (or the natural / shared boundary key);
  - STILL cells = own pose (or natural, for never-listed bones, slid toward the shared boundary pose) + life offsets in
    the parent's rest axes (conjugated with the parent's rotation), written as per-bone `local_delta`;
  - the shared `slam/poses_stuck/k00_stuck.json` (end of slam, start of pull_free, start/end of hurt, seam of stuck) is
    never touched, so the chains keep their boundary pose.
- Backups: every overwritten pose/keys/action file has a `.rest_v1.json` twin, strips `.rest_v1.jpg`.
- Verification: `res3.json` = old vs new read-backs at every old key time (world orientation of acting bones, club-hand
  position).

## Decision: where the natural stance stands (root x)
`ak bake` subtracts the first key's horizontal `root.loc` (plus the first->last drift). natural_pose has root x 0.25,
so idle_n will bake the natural stance onto x 0. Replaced keys of slam, sweep and death therefore use root x 0 (the
same in-game spot as idle_n, and no shift of the acting part: a 0.25 at t=0 would have moved the whole slam/sweep
0.25 m, measured). pull_free keeps 0.25 at its last key: the bake's in-place ramp then glides the body 0.25 m over
1.5 s and lands the natural stance on x 0. Cost: in slam/sweep/death the feet glide up to 0.25 m between the natural
stance and the first acting key (slam over 1.33 s, sweep over 0.375 s while he turns 35 deg anyway, death while
collapsing).

## Per clip (numbers from the bakes and res3.json)
| clip | length / loop / events (unchanged) | keys old -> new | what changed | moving bones (>= 3 deg) |
|---|---|---|---|---|
| slam | 1.75 / no / impact 1.5 | 10 -> 10 | t0 = natural; gap-fill legs 0.25-1.0, hips/neck/head/shoulder_u_l/lower arms 0.25; lower hands: natural -> stuck, cock -18 deg at 1.333, snap +16 at 1.5 | 24 -> 26 of 29 |
| stuck | 1.5 / loop / - | 2 -> 4 (+0.375, +1.125 life keys) | tug at 0.75: knees 8-9 (shins 11-12, feet -3), spine_01/02 back 3-3.5, neck back 4, lower arms push (-7/-8/-12); breath spine_03 3 deg 1x/loop; head/neck turns 3-4 deg counter-phase, head tilt 2x/loop. All cycles 1x or 2x per 1.5 s, zero at the seam | 12 -> 24 |
| pull_free | 1.5 / no / - | 9 -> 9 | end = natural (new file poses_pull_free/k08_natural.json, the old k00_ready stays for slam); lower arms 1.125-1.375 and shoulder_u_l 1.25-1.375 gap-filled toward natural; lower hands clench -16 / release +10, right one key later | 24 -> 26 |
| sweep | 2.5 / no / impact 1.31 | 21 -> 21 | t0 and t2.5 = natural; k9b_settle (2.375) 50% toward natural (return over the last 0.25 s); head (never keyed) looks at the target: +11 in the wind-up, dips 7 at the strike, -13 in the follow-through; shoulder_u_l lifts 7 at the strike; hand_u_l cock -12 / flick +14; lower hands trail 8-12 deg, left one key later. Hips untouched (the spine is local_delta there: a hips turn would move the club) | 21 -> 27 |
| hurt | 0.667 / no / - | 4 -> 5 (+0.5 overshoot) | knees dip 4-5 / shins 6-7, spine_01 recoils 4, neck snaps back 7 and overshoots at 0.5, lower hands fling 11-14 | 15 -> 22 |
| death | 4.5 / no / - (keep root motion) | 35 -> 35 | t0 = natural; spine_03 gap-filled 0.375-1.25, head 0.875-1.125, spine_02 at 1.25/3.875/3.917; shoulders slump 8-9 deg from 0.4 s; hips leave the natural tilt by 0.75 s | 26 -> 29 |

Contract checks: length, loop, events identical in every action; every old key time kept. Acting bones' world
orientation at the kept keys: max 0.05 deg (slam, stuck, pull_free, hurt); sweep/death differ only in the gap cells.
Club hand (hand_u_r) position vs the old clip: slam 0.000 m at 1.333-1.75 (windup, chop, swing, fall, impact, stuck)
= the club lands where the slam circle is; sweep 0.000 m at every key 0.375-2.25 (whole strike); pull_free 0.04-0.23 m
(the in-place ramp); stuck 0.10-0.16 m at the tug (the body now dips with the knees); hurt 0.03-0.06 m; death 0.15 m
(shoulder slump, club stays above the floor in the strip).

## What is still stiff, and why
- Toes are never keyed (planted feet: correct).
- hurt: feet, hips and spine_02 stay < 3 deg: he is stuck with the club in the ground, the feet are planted.
- stuck: spine_02 2.7 deg and foot_r 2.5 deg (just under the 3 deg line): feet planted; spine_02 rides the bigger
  spine_01/03 motion.
- slam 0.25-0.5: the gap-filled right (free) leg lifts the right heel 6-12 cm while the pelvis glides from the natural
  spot; reads as a weight shift in the strip, but a planted-foot purist would key a small step.
- The acting arms of death (arms flung out at 0.4 s, lower arms spread on the knees) and of pull_free (arms wide at
  1.25 s) are traced keys and stay as they were (not my brief to re-act them).
- Old `strip_*.mp4` files are stale (made from the old actions); `strip_*.jpg` are the new strips (no reference row:
  the reference videos still show the old T-pose start).

## Image reads: 6 (strips + one contact sheet).
