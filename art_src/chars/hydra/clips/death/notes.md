# hydra / death video: notes (animator, 2026-11-22)

| clip | video window | keys | length | loop | events |
|---|---|---|---|---|---|
| death | 1.5-7.0 s (clip t = video t - 1.5) | 21 (13 traced + 8 authored/grounded in-betweens) | 5.5 s @ 24 fps | no | none (SPEC §8 lists none for death) |

The reference is usable: calib IoU front 0.947 / side 0.954, the views are in sync, it shows the prompted move (idle 0-1.5 s,
thrash 1.5-4.5 s, legs buckle 4.5-5.25 s, belly down 5.5 s, necks fall 5.5-6.75 s, still from 7 s on).

death: k0 starts from the exact idle k0 (`poses_idle/k0.json`), so idle -> death chains. The clip ends lying flat and holds that pose.

## Key IoU (front / side) against the aligned video frame
| key | clip t | video t | what | front | side |
|---|---|---|---|---|---|
| k0 | 0.00 | 1.50 | idle ready pose | 0.909 | 0.944 |
| k1 | 0.75 | 2.25 | thrash: heads splay | 0.805 | 0.849 |
| k1b | 1.25 | 2.75 | thrash | 0.804 | 0.898 |
| k2 | 1.75 | 3.25 | thrash: crown wide, centre neck back | 0.814 | 0.875 |
| k2b | 2.25 | 3.75 | thrash | 0.821 | 0.799 |
| k3 | 2.75 | 4.25 | necks bunched up | 0.753 | 0.770 |
| k3b | 3.00 | 4.50 | last standing pose | 0.691 | 0.700 |
| k4 | 3.50 | 5.00 | legs buckled, body 1.8 m down | 0.764 | 0.717 |
| k4b | 3.75 | 5.25 | kneeling, belly nearly down | 0.758 | 0.656 |
| k5 | 4.00 | 5.50 | belly on the floor, necks still up | 0.662 | 0.689 |
| k6 | 4.50 | 6.00 | outer necks 1/2/7/8 down, inner up | 0.619 | 0.661 |
| k7 | 5.00 | 6.50 | all down but the centre neck (half raised) | 0.593 | 0.567 |
| k8 | 5.50 | 7.00 | lying flat, necks fanned on the floor | 0.553 | 0.682 |
Mean 0.744. Strip (12 samples) mean 0.727. In-betweens: kg1, kg2, kg7, kg3, kg5, kg4, kg6 (3.125-3.958 s) are read back from the bake
and re-grounded (`root.ground: lowest`) so the feet do not sink or float while the legs fold. k5b (4.25 s) is authored: it holds the
outer necks in a raised sideways arch, because without it a right head swung 0.48 m under the floor at 4.30 s.

## Floor contact
Checked on every 24 fps frame from 3.0 to 4.5 s and on every strip/mp4 sample (83 samples): lowest vertex within
-0.18 / +0.25 m (single frames at 3.83 s and 3.92 s, during the 0.5 s belly drop), 0.00 everywhere else. That is under 2% of the 14.4 m height.

## What does not match and why
- Lying pose (k7, k8, IoU ~0.6): Seedance flattens the creature into a pancake (body about 2.5 m tall, skirt spread to the panel edges).
  The rig's torso is ~3.5 m thick and cannot squash, so ours lies higher and narrower. The authored lying pose: belly on the floor
  (root -2.64 m), legs splayed out and diagonal (front legs forward, hind legs back), each neck laid on the floor along its own direction
  (centre forward, then 35/70/95/118 deg out for necks 4-5 / 3-6 / 2-7 / 1-8), heads level.
- Thrash keys k1-k3b: the 9 necks were traced by `ak fit` on the base angle of each neck (+ neck_c_03). Fit cannot tell which neck is which:
  the silhouette matches but neck identities are not guaranteed. The heads differ from each other in every key, so they do not move as one.
- Centre neck at 6.5 s: the video shows a short vertical stalk. Ours rises forward and curls the head down (good enough at game scale).
- The video thrash is longer (3 s) than a game death may want. The game can play it faster (it re-times), or the lead can `ak retime --scale 0.7`.

## Files
keys_death.json, poses_death/k*.json + kg*.json + k5b.json, action_death.json, strip_death.jpg.
Scratch: work/anim/hydra_death/ (gen.py makes k0-k8 from fits + lay helpers; strip_death.mp4 = final preview; ground_scan.sh = floor check).

## animfix_hydra (2026-11-22)
See docs/notes/anim_hydra_fix.md for what changed in this folder (new/retimed clips, generators in work/animfix_hydra/).
