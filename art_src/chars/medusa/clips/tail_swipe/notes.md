# medusa / tail_swipe video — animator notes (2026-11-22)

tail_swipe | window 5.75-8.50 s (second take; the first take 1.75-4.5 s is the same move) | 11 keys (10 poses, k0 reused as the last key) at clip t 0, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 2.25, 2.75 | IoU per key (front/side): k0 0.74/0.79, k1 0.58/0.55, k1b 0.50/0.49, k2 0.58/0.56, k3 0.66/0.59, k4 0.59/0.34, k5 0.65/0.38, k6 0.64/0.64, k7 0.60/0.57; key mean 0.58; strip mean 0.60 over 42 frames (min 0.38 at t 0.80, a motion-smear frame) | length 2.75 s, 24 fps, no loop, starts and ends on the rest/idle pose (k0) | events impact 1.0 (the tail comes down low on her right and sweeps forward; video 6.75 s).

Keys: k0 rest; k1/k1b wind-up (torso turned 50-60 deg to her right, arms out level, tail curled on her LEFT with the tip hooked up); k2 tail rises in a loop on her back-left; k3 tail stands up behind her and arcs over her head; k4 tail thrown up and out on her right (~50 deg); k5 tail low on her right sweeping forward (impact); k6 tail flat on the floor to her right-front (yaw ~115 deg), left arm reaching forward; k7 same with the arms dropping; k8 (authored) tail dragged back to her right-back; k0 rest.

What does not match and why:
- The video does not show the prompt's "low horizontal 360 sweep": the tail goes left (coil) -> up behind and over her head -> down on her right -> low forward-right, i.e. an overhead whip that ends on the floor at her front-right (about 225 deg of yaw, not 360). I matched the video, not the prompt. The game's 360 damage ring does not depend on it, but if a true flat 360 sweep is wanted, it needs a new video or an authored clip (lead decision).
- 6.58-7.1 s are smeared (Seedance motion-blur ghosts) and the side view shows the tail looping in front of the body base, which does not agree with the front view; IoU there (0.35-0.45 side) is not meaningful. Front-view tail direction was traced, side-view loop approximated.
- The video's tail is longer than the rig's (rig: 9.9 m on the floor, 8.4 m from tail_05); at 6.5 s the video column reaches ~7.5 m, ours ~6 m.
- The video drifts (character moves ~0.5 m and zooms 0.90-0.985 between keys): absorbed per key in view_offset/view_scale (framing only, never baked).
- Recovery: the video holds the tail at her front-right until 8.25 s and then pops back to rest by 8.6 s; k8 + final k0 are authored so the clip returns to idle (tail drags back round her right side, on the floor).
- Tail is posed with ABSOLUTE per-link rz (yaw) + rx (pitch) for tail_04..tail_14 (chain bend_up/bend_side are view-axis deltas and tilt the tail off the floor once it is yawed). Airborne-tail keys k2-k5 use root.ground "lowest" (body drops <= 0.14 m so the coil base stays on the floor); lowest_z over the clip -0.007..+0.010 m.
- Snakes (hair_*) and the back tail links have no separate secondary motion keys; they ride along.


## Fixer pass (2026-11-22, owner away)
Re-authored as a FLAT 360 deg SWEEP (decision with the owner away; the game deals a 360 low ring r 7 m and draws a 360 swoosh,
SPEC says 360 low sweep). Generator `work/animfix_medusa/gen_swipe.py`. k0/k1/k1b (video wind-up, 0-0.5 s) kept; s1-s7 authored:
one counter-clockwise body spin (root.rot rz 0 -> 360 over 0.5-1.33 s), tail trailing low (tail_05..14 rx 2.5 deg up, tip 0.69 m,
tail_09..14 max 0.82 m), follow-through and settle to rest at 2.25 s. Tail tip sweeps 0 -> 381 deg around her at r 8.4-9.3 m.
impact = 0.833 s (mid-spin, tail passing in front of her). length 2.75 -> 2.25 s. Lowest vertex 0.000 on every frame.
The old overhead-whip keys k2-k8 stay in poses_tail_swipe/ (unused) in case the lead wants the video version back.
