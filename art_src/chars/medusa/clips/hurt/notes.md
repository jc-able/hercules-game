# medusa / hurt (animator, 2026-11-22)

hurt | video window 1.25-4.50 s (first take; second take 4.5-8 s is the same move) | 8 keys (k0, kA, k1, k2, k3, k4, k5, k0) at 0, 0.125, 0.25, 0.75, 1.5, 2.25, 2.75, 3.25 s | IoU per key (front/side): k0 0.83/0.75, kA 0.71/0.71, k1 0.72/0.67, k2 0.71/0.66, k3 0.73/0.66, k4 0.79/0.70, k5 0.75/0.72, end k0 vs 4.5 s 0.74/0.73 (key mean 0.72; strip mean 0.71 over 50 samples) | length 3.25 s, 24 fps, no loop | events: none (hurt has none in SPEC 8) | Not matching: (1) the video's tail curls toward her left from frame 0 (visible in the front panel, shorter in the side panel); our tail stays straight back on the ground as in the rig/rest so every clip chains, which caps IoU at ~0.79 even for an exact body pose (rest pose on the 1.25 s rest frame scores 0.83/0.75); (2) the video snakes are drawn bigger/longer than the 6 fused snake bones can reach; (3) the sideways flinch (~0.2 m to her right and forward in the video) is kept as framing (view_offset) not baked root motion, so the tail does not slide; (4) the hold is natural video timing (shriek held ~1.3 s); the game re-times.

- Starts and ends on the rest/sheet pose (the video's idle pose). No idle clip was baked yet when this was made; if idle settles on a different ready pose, swap k0 for idle's first pose file (decision taken with the owner away).
- Acting: kA arms come in, k1 = flinch peak (spine leans back ~27 deg and to her left in the front panel, head thrown back ~35 deg, right hand clutching the neck, left forearm across the chest, snakes thrown up/back), k2/k3 held shriek with snakes thrashing in different directions, k4 recovering (hands at chest, head tilts), k5 right arm swings out, back to rest.
- Trunk, head and snakes fitted with `ak fit` per key; arms posed by eye in aim form.


## Fixer pass (2026-11-22, owner away)
Shortened 3.25 -> 1.625 s: the k3 shriek hold dropped, k4 at 1.0, k5 at 1.292, k0 at 1.625 (reaction keys unchanged).
medusa.gd's recoil and BossBase now freeze her ~1.6 s per side cut instead of ~3.25 s. Strip IoU 0.64/0.61 (vs the slower video).

- animfix2: neck clutch eased (kA travels further) + overshoot k1o 0.333 s and settle k1s 0.458 s on the right arm; flinch timing unchanged (animfix2 2026-11-23; details in docs/notes/assemble2_medusa.md "Animation fix pass")
