# medusa / death (animator, 2026-11-22)

death | video window 1.0-4.0 s (t0 = 1.0; clip t = video t - 1.0 up to the tip at 2.0) | 8 keys | length 3.5 s @ 24 fps, one-shot, ends lying still | events: none (SPEC §8 lists no death events) | baked with `--keep-root-motion` (spec in_place=false)
IoU per key (front/side, view_offset+view_scale per key): k0_ready 0.81/0.76 (v1.0), k1_rise 0.65/0.58 (v1.5), k2_shriek 0.69/0.63 (v2.0), k3_arch 0.69/0.63 (v2.75), k4_tip 0.62/0.50 (v3.0), k5_impact 0.51/0.32 (v3.125, authored), k6_slap 0.76/0.49 (v3.375), k7_still 0.76/0.49 (v4.0); mean 0.62. With no view correction the lying pose scores 0.67/0.47.
Clip timing: 0 ready -> 0.5 arms rise -> 1.0 shriek, arms up, arched back -> 1.75 deepest arch -> 2.0 tips forward-right (linear segment = falling) -> 2.375 hits the floor, tail end whips up -> 2.75 tail slaps down -> 3.125 still -> hold to 3.5.

What does not match and why:
- The reference breaks at 3.0 -> 3.125 s: in ONE video frame she goes from tipping to lying flat (a jump cut). The fall (clip 2.0-2.375) is authored, not traced.
- After 3.125 s the two panels disagree as drawn: the front panel shows her lying across X, the side panel lying along Y. The one 3D pose that fits both is a DIAGONAL fall forward-right (body yawed 50 deg toward her right, head about (-3.4, -4.5) m); that is what is keyed. Face-down, arms forward on the floor.
- Seedance shortens the ground tail in the side panel from ~1.5 s on (about 3-4 m shorter than the model's 9.9 m) and draws the body thicker: side IoU tops out near 0.63 upright and 0.5 lying. The model's tail stays its real length and planted.
- The front panel's tail "hook" (tail end curling to her right, 1.5-2.75 s) is only suggested by a small sideways curl of tail_09-14; lifting it as drawn would show a raised tail tip in the side panel, where the video has none.
- The ground tail stays planted: every pose is anchored so the tail_05 head (start of the ground tail) sits at its rest spot (work/anim/medusa_death/anchor.py); the body travels forward-right onto the floor, so root motion is kept (no in-place drift removal: removing it would slide the tail backward ~2.7 m). For the lying pose the tail behind tail_05 swings 35 deg toward +X (limp).
- Snake hair: authored secondary motion (flare on the shriek, droop when dead, different phase per snake); on the lying head a few snakes still point upward.


## Fixer pass (2026-11-22, owner away)
The fall dipped through the floor (-0.82 m at 1.92 s between k3_arch and k4_tip, -0.37 m at 2.12 s). Grounded read-back keys
k3a_turn 1.8125, k3b_twist 1.875, k3c_tip 1.9167, k4c_fall 2.0833, k4b_fall 2.1667 (linear 1.75-2.375): lowest vertex now
-0.043..+0.041 m over the whole clip. Snakes droop on the dead head: hair_*_01/02 rx +25 in k6_slap / k7_still.
Root motion kept (ends 5 m forward-right of the capsule, cosmetic).

- animfix2: grounded read-back keys kf1..kf6 (0.333, 0.792, 2.042, 2.125, 2.208, 2.25 s); lowest vertex -0.043 -> -0.0085 m (animfix2 2026-11-23; details in docs/notes/assemble2_medusa.md "Animation fix pass")
