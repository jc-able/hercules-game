# Re-base of medusa's old clips onto the natural stance (re-base animator, 2026-11-23)

The owner was at the Mac and nobody could be asked, so every decision here is mine and written down. Blender ran only
headless. No window, no Godot run, the blend opened read-only (never copied, never saved), nothing written under game/.
Scratch: `work/rebase/medusa/`.

## Tool
`work/rebase/medusa/rebase.py <clip> ...` (run order: stunned, stun_start, rise, then the others). It always starts from the
`*.rest_v1.json` originals, so it is safe to run again.
- `nat_ld.py` (headless Blender, uses animkit's Rig) turns `natural_pose.json` into `natural_ld.json`: every bone as a
  `local_delta`, so the stance can ride on any parent. It solves back to the same pose (0.0000 deg error).
- Bones are sorted from the OLD action's key quaternions:
  - **acting**: turns >= 3 deg in the clip. Kept exactly as keyed: same entries, key times, interp, events, length and loop.
  - **frozen_rest**: still, and at its rest orientation relative to its parent. Gets the natural stance plus life.
  - **frozen_posed**: still, but held away from rest. Keeps its keyed entry, and life is added on top.
- An acting bone that a key leaves unlisted, within 0.3-0.6 s of a stance key, also gets the stance.
- One-shot boundary keys that used the rest pose are now `natural_pose.json` exactly (the same as idle_n frame 0).
- A key whose pose file belongs to another clip is a chained boundary. It is used as it is.
- Life is sums of sines. Every bone has its own period and phase, so the heads and snakes never move in unison:
  - breath: 3.5 s (3.0 s in stunned)
  - sway: 6.5-7 s
  - head: 4.3-6.1 s; neck: 5.2 s
  - floor tail: a 4.2 s wave with a 0.5 rad lag per link, 1.5 deg at tail_04 growing to 8.5 deg at the tip
  - per-clip accents, listed below
- Life fades in over the first 0.3 s and out over the last 0.3 s, so a one-shot begins and ends on the exact stance.
- Stun chain (`tail_nat_add`): the whole tail keeps the natural curve. Each keyed tail delta is conjugated by the natural
  yaw built up along the tail (turned into the curve's frame). Without that, a keyed curl-up on a tail turned more than
  90 deg became a curl-down. The first try sank the tail 0.24-0.29 m into the floor during the fall; it is fixed (now 0.000).

## Per clip (moving bones = turns >= 3 deg over the key samples, of 34)
| clip | length / loop / events (unchanged) | keys | moving | what changed |
|---|---|---|---|---|
| gaze | 4.25 s, one-shot, fire_start 2.0, fire_end 3.25 | 9 -> 9 | 16 -> 29 | Tail 01..14 move from frozen straight to the natural S-curve with a slow wave; the wave calms (x0.3) and the tip braces (up to +6 deg per link) during the stare, then relaxes (x1.3). Pelvis tilts and sways. Shoulders shrug up to 7 deg with the arm raise. Hands curl 12 deg in the wind-up and fan 15 deg in the stare. k0 = stance. |
| hurt | 1.625 s, one-shot, none | 7 -> 7 | 15 -> 30 | Tail curve, plus a recoil ripple down the floor tail (0.06 s lag per link, decay 0.5 s). Pelvis recoils 4 deg back. Shoulders flinch 6 deg, hands tense 10 deg. Every key grounded: the pelvis recoil had floated the tail 3 cm. k0 = stance. |
| tail_swipe | 2.25 s, one-shot, impact 0.833 | 11 -> 11 | 24 -> 30 | Head and neck turn into the spin (neck 10 deg + head 14 deg, a -0.25 overshoot at 1.708 s), so she watches her own sweep. Shoulders lift 5 deg, hands trail 10 deg. Pelvis and tail_01..03 take the stance. tail_04..14, the arms and the root spin are as keyed. k0 = stance. |
| death | 3.5 s, one-shot, none | 14 -> 14 | 30 -> 34 | k0_ready changes from the rest pose to the stance. Shoulders follow the rising arms (7 deg). Hands splay 14 deg in the shriek. Life is 0 from 2.4 s (dead after the 2.375 s impact). The final lying pose is unchanged. |
| stun_start | 1.625 s, one-shot, none | 12 -> 12 | 27 -> 31 | k0_rest changes from the rest pose to the stance (the old pop from idle is gone). Shoulders follow the hands over the eyes, then drop. Natural tail curve with the conjugated keyed deltas. Ends on the shared re-based `poses_stunned/k0_slump.json`. |
| stunned | 3.0 s, LOOP, none | 3 -> 9 | 13 -> 27 | 6 in-between keys added every 0.375 s: cosine in-betweens of k0/k1, needed to sample the life. Breath in spine 2.0/2.5/2.2 deg, one per 3 s. Shoulders shrug with it. Arm and hand twitches of 1.5-4 deg, out of phase, on 3 s and 1.5 s periods. Natural tail curve with a faint wave down tail_04..09. Every key grounded: the slump now sits up to 6 cm higher than before, because it had sunk 6-10 cm once the arms and shoulders moved. All periods divide 3.0 s, so the seam is exact. Head and neck (weak point, gaze socket), pelvis and tail_03 are untouched. |
| rise | 2.5 s, one-shot, none | 14 -> 14 | 25 -> 31 | Starts on the shared k0_slump. Ends EXACTLY on the stance (`poses_stun_start/k0_rest.json` = `natural_pose.json`). Shoulders load up 6 deg in the push. Natural tail curve under the keyed deltas. |

## Checks
- The bake's lowest vertex is within -0.006..+0.021 m in every clip. Strip in-betweens are within -0.006..+0.021 m.
- Key times are a superset of the old ones. Length, loop and events are identical (asserted).
- I looked at strips of all 7 clips (`strip_<clip>.jpg`, rendered without the old video):
  - start and end are on the stance, with no pop
  - the stunned loop seam is invisible
  - no limb goes through the body
  - she holds no weapon

## Still stiff, and why
- Pelvis and tail_01/02 move less than 3 deg in gaze, tail_swipe and the stun chain. I chose this: they are the planted base
  of the column (sway 1.6-2 deg). tail_03 is the lean-recipe pivot (absolute 0) and is never touched.
- stunned spine_01/02 read just under 3 deg on key samples; the breath is +-2.0/2.5 deg (the brief asked for +-2).
- hurt tail_02/03/05/06: the ripple is sampled at the 7 old keys only (0.125-0.375 s apart), so it is coarse.
  Adding keys would need the acting limbs read back from the old curve. I did not do that, so the acting limbs stay exact.
- stun_start: the tail lash up during the recoil (0.46-1.16 s) is the original keyed curl, now drawn on the curved tail.
- hurt: one in-between of the first strip went 5 cm below the floor before the grounding. After the grounding the range is
  -0.003..+0.001 m.
- The stunned in-between keys are cosine in-betweens of the keyed entries. They match the old bezier only approximately
  (the hold was 2 keys).

## Files
For each clip: `keys_<clip>.json`, the pose files, `action_<clip>.json` and `strip_<clip>.jpg`. The old versions are beside them
as `*.rest_v1.*`. New files: `poses_stunned/l_t*.json` and `art_src/chars/medusa/rebase_done.json`. Devlog:
`docs/devlog/media_inbox/rebase_medusa/`.
