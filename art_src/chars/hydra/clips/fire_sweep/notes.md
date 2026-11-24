# hydra / fire_sweep video: animator notes (2026-11-22)

All clips are 24 fps and were baked with `ak bake --out-action` from this folder. Scratch, generator and logs are in `work/anim/hydra_fire_sweep/`
(`gen.py` writes every pose; `fit2aim.py` turns `ak fit` output back into aim directions). Calibration IoU was 0.92 front / 0.95 side.
IoU = (front + side) / 2 per key, against `ak frames` output at the key's video time. "gain" = gain over the rest pose on the same frame.

| clip | video window | keys | IoU per key | length | events | loop |
|---|---|---|---|---|---|---|
| fire_sweep | 1.0-6.0 s | 8 | rest 0.94, rear 0.68, rear2 0.66, lunge 0.69, low_r 0.67, sweep_c 0.64*, sweep_l 0.62*, down 0.61 (mean 0.69, strip 0.68) | 5.0 s | fire_start 3.3, fire_end 4.3 | no |
| head_down | 6.0-7.5 s | 4 (+seam) | down 0.61, down_in 0.63, down_b 0.62, down_in2 0.64 (strip 0.62) | 1.5 s (2 pants of 0.75 s, `ak cycle` period 0.75) | none | yes |
| head_up | 8.0-9.5 s | 6 | down 0.64, up1 0.73, up2 0.73, up3 0.73, up4 0.80, rest 0.92 (strip 0.78) | 1.5 s | none | no |

Chaining: `fire_sweep` ends on the same pose as the first pose of `head_down` and `head_up` (identical files, `k7_down` = `k0_down`). `head_up` ends on the rest pose, which is also where `fire_sweep` starts.
The head_down chin rest is a bow: spine_01 -9, spine_02 -4, front legs bent 30/41 deg. All four feet stay at rest height (within 1 cm), the jaw_c joint sits at 1.13 m (the rig asks for <= 1.5 m), and nothing goes below the floor.
I chose this chin-on-ground pose over a fitted pose with the head hanging 0.5 m above the floor, although the hanging pose scored 0.66 against 0.61. The video, the SPEC (jaw exposed at ground level) and the rig recipe all put the chin on the ground. The video's body bows less than ours: our shorter neck needs the bow to reach the floor. Our head rests at x -0.8 m, just to the creature's right of centre. The video's head lies about 3 m to its right: with the rig's shorter neck it cannot reach both that far out and the floor.

What does not match, and why:
- The video stretches the centre neck. Its top reaches 17.4 m while the rig reaches 14.4 m, and the head reaches 9.3 m forward and 8.7 m sideways while the rig's limit is about 8 m. Seedance redrew the neck about 1.5x longer, so the centre-neck keys stay near 0.62-0.70. Directions were matched, not lengths. The side necks in the video are also taller than the model's.
- *The sweep's left half is authored, not traced. Between 4.75 and 5.5 s the video's head only drifts from the creature's right towards the centre, then drops. The SPEC and prompt ask for a right-to-left arc, so sweep_c (4.85) and sweep_l (5.25) carry the head low across to the creature's left, and it settles back at the centre-right chin rest by 6.0 s. That is why those two keys score lower in the front panel.
- 8 side necks are authored, not traced. They use the chain helper with spread and lean picked by an IoU grid (`grid/*.log`), plus a per-neck phase wobble so they never move as one. The centre neck_c and head_c were traced (aim form, then `ak fit` on rx/ry with view_offset).
- jaw_c opens 18-20 deg during the inhale and the fire (the rig limit is 20). The mouth is a painted line, so the opening is subtle.
- A fire_sweep in-between dips 2.7 cm below the floor (lowest_z -0.027, during the low sweep). Keys are on the floor. Front feet stay within 7 cm of rest height in every key (leg bends solved per spine bow with `ak solve`).
- view_offset per key: x -0.2 to -0.54 m on the lunge and low keys, -0.4 m on the chin rest. It comes from fit and is render-only, not baked.

## animfix_hydra (2026-11-22)
See docs/notes/anim_hydra_fix.md for what changed in this folder (new/retimed clips, generators in work/animfix_hydra/).
