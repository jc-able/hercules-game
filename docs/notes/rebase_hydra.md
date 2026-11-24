# Re-base of the hydra clips onto the natural stance (re-base animator, 2026-11-23)

The owner was at the Mac. Everything ran headless (Blender `-b --factory-startup`, `tools/ak`), with no window, no focus change and no sound.
The blend was opened only read-only and in place. I did not write `game/assets`. Nothing was generated and no credits were spent.
Scratch is in `work/rebase/hydra/`. Machine-readable summary: `art_src/chars/hydra/rebase_done.json`.

## Tool: `work/rebase/hydra/rebase_bl.py` (headless Blender; uses animkit's own Rig / write_action)
1. Reads the ORIGINAL action (`action_<clip>.rest_v1.json`), puts it on the rig and evaluates its F-curves **per frame**
   (no depsgraph). The output is one key per frame, so every original key time (and every hold/linear snap) is preserved.
2. Groups: spine (hips + spine_01..03), tail, legs (all four together), neck_c (+head_c, jaw_c), n1..n8 (side necks + heads).
   - **Acting** group: the original local rotation, exactly. A check at the original key times outside the 0.3 s boundary
     windows gives a max deviation of 0.08-0.17 deg, which is Euler rounding.
   - **Passive** group: `q_natural * q_original(t - stagger)`. The original motion (for example bite's unison 33 deg pull-back) is
     kept on top of the natural stance, but each head is delayed 0.02-0.12 s and scaled 0.7-1.1 so no two heads move together.
   - Boundaries: per-group weight ramps over 0.3 s (0.35 s for death). `natural` = every group on `q_N * q_O`.
     `down` = the shared chin rest: neck_c/spine/legs are the original, and the side necks/tail are natural + a per-head droop
     (-1.5..-3.5 deg per link). So head_down, hurt, head_up start, fire_sweep* end and death start are the same pose.
     `own` = original.
3. Life is added as local_delta world-axis rotations on the chain axes (bend_up / bend_side), weighted by the group weight,
   so acting limbs get none:
   - breathing on the spine and the neck roots (3.5 s period; 1.5 s panting in the head_down loop)
   - a weave on every head with its own amplitude (1.2-2.2 deg per link), frequency (0.19-0.37 Hz) and phase, with 0.45 rad lag per link
   - head look turns
   - a tail sway with 0.5 rad lag per link
   - per-clip reactions, listed below
   On a loop every frequency is rounded to a whole number of cycles per loop length, so the seam is exact.
4. Output: inline absolute poses (all bones that differ from following their parent) plus `root.loc`. `ground: lowest` is
   used only where the legs are being blended (so foot height stays right while the soft knees change).
   Then `tools/ak bake ... --out-action` and `tools/ak strip` with `cam_nat_std.json` (n 6, 3 columns).

## Per clip
Columns: moving joints (>= 3 deg over the clip) before -> after, of 76. Names, loop flags, lengths and events are all unchanged.

| clip | moving | what I did | still stiff / known |
|---|---|---|---|
| bite | 48 -> 65 | centre strike exact; side heads on the stance, staggered pull-back/up before 1.33 s, outward flinch at 1.5 s + delay, damped settle, look turns; tail counter-swing; start/end natural | hind legs planted (legs follow the original: the crouch is keyed on the forelegs) |
| bite_l | 43 -> 62 | neck_6 strike exact; centre + 7 heads natural, turn 14 deg toward the strike, recoil; tail counter-swing | same |
| bite_r | 43 -> 64 | mirror idea with neck_3 | same |
| fire_sweep | 48 -> 69 | centre sweep exact (fire 1.5-4.05 s); side heads lift and lean away as the stream x passes them (-X -> +X over 1.7-3.95 s), flinch at the stream start; tail counter-sweep; droop into the chin rest over the last 0.65 s | hind legs planted |
| fire_sweep_l | 48 -> 66 | same, stream +X -> -X | same |
| fire_sweep_return | 44 -> 57 | own start (sweep pose); heads lean away from the return stream; ends on the chin rest | end window has a lowest vertex at -0.03 m at 2.43-2.50 s (at the warning threshold) |
| fire_sweep_return_l | 44 -> 55 | same, mirrored; neck_4 included | -0.03 m at 2.47 s |
| head_down | 25 -> 41 | centre bow exact (jaw socket unchanged); side heads natural + droop, 1.5 s panting + weave with phase offsets; tail stirs; seam exact | legs planted; panting is 1 breath per 1.5 s because the loop length is fixed at 1.5 s |
| head_up | 47 -> 56 | centre rise exact; side heads lift out of the droop with 0.1-0.35 s lag per head; ENDS on the natural stance (was rest) | legs blend from the kneel to the natural legs in the last 0.3 s (feet may slide a few cm) |
| hurt | 44 -> 54 | centre recoil exact; side heads jerk up/out 0.1-0.2 s after the hit with lag; tail lash; chin rest at both ends | 0.9 s is short: the reactions are still settling at the end window |
| hurt_standing | 51 -> 53 | head_c jerks up 12 deg, jaw opens 10 deg, spine shudder, tail lash; the side-head reaction is kept, staggered, on the stance; legs natural | the count barely rises because most bones already moved; the visible change is the natural stance and the hit head |
| stomp | 43 -> 65 | legs + spine + impact 1.75 s exact; heads rear up 0.5-1.45 s and whip down at the impact with lag and bounce; tail lifts for balance, thumps | no hip roll: it would move the planted feet (no IK in this pass) |
| stomp_r | 43 -> 65 | mirror | same |
| death | 63 -> 69 | starts on the chin rest (side necks blend into the traced thrash over 0.35 s); thrash/collapse exact; tail_03..08 whip with lag, fading out 1.75-2.05 s so the tail lies flat | first pass put the tail's natural curl into the floor (-0.21 m at 2.13 s): fixed by fading the tail stance out with the collapse (now no floor notes) |
| death_standing | 60 -> 72 | starts natural; spine sway + tail whip in the thrash, faded by 3.45 s | ak bake notes -0.03..-0.05 m at about 2.0-2.2 s (tail during the thrash); strip lowest z range -0.05..+0.07 m |

## Decisions (the owner does not answer questions)
- Legs are one group per clip and keep the original. Mixing natural soft knees on two legs with keyed legs on the
  other two would float or sink feet by about 0.1 m. So weight shift is carried by the spine and heads, not the hips. Exception: hurt_standing,
  whose legs were never keyed, uses the natural legs throughout.
- One key per frame instead of a few authored keys: it is the only way to keep the acting limbs exact while adding
  life with lag. The keys files are larger (inline poses), and `ak merge` re-bakes them as usual.
- No length changed. Every event is unchanged. Sockets, the jaw weak point and in-place motion are untouched.

## For the assembler (important)
Backups sit beside the new files: `keys_<clip>.rest_v1.json`, `action_<clip>.rest_v1.json`, `strip_<clip>.rest_v1.jpg`.
`action_<clip>.rest_v1.json` matches a glob `action_*.json` and carries the SAME clip name, and in sorted order it comes after the new file,
so a glob merge would silently restore the OLD clip. Merge the paths in `rebase_done.json`, or exclude `*.rest_v1.json`.

## Devlog
`docs/devlog/media_inbox/rebase_hydra/bite_before_after.jpg`, `fire_sweep_before_after.jpg` + `captions.txt`.
