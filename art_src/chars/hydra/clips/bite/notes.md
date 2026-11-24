# hydra / bite (video `bite`)

| clip | window (video) | keys | key IoU front/side | length | events |
|---|---|---|---|---|---|
| bite | 1.0-4.5 s (first take) | 7 (k0 rest 1.0, k1 coil 2.333, k2 arch 2.417, k3 strike 2.5, k4 head down 3.25, k5 recover 3.75, k6 rest 4.5) | k0 0.91/0.89, k1 0.91/0.85, k2 0.89/0.84, k3 0.80/0.76, k4 0.79/0.74, k5 0.83/0.77, k6 0.91/0.88; mean 0.84 (front 0.86, side 0.82) | 3.5 s @24 fps, one-shot | impact 1.5 s |

Strip (`strip_bite.jpg`, ref time = 1.0 + clip time): IoU mean 0.82; lowest vertex -0.04 m at the snap (jaw at the floor), feet planted.
Starts and ends on the rest pose (= the idle pose: the idle clip only adds a few cm of motion).
The coil eases in (bezier), coil peak -> high arch -> strike is linear over 4 frames, then it eases into the head-down hold and back up.

## What does not match and why
- **Wrong head (decided while the owner was away).** prompt.txt and SPEC 3.3 want an OUTER head on the right side. In the video the
  CENTRE head (neck_c) coils and strikes the floor, in both takes (2.33-2.5 s and about 5.9-6.25 s). I traced the centre head, for two reasons. First, the
  video only shows that head. Second, the rig's outer necks cannot reach the floor: neck_1 is 3.8 m long including the head, from a base at 6.8 m, so
  pointing straight down its snout stops about 3 m above the floor (about 2 m with the full bow). Only neck_c (9.4 m with the head) reaches the floor. If the game must bite with a side head, it needs a
  longer side neck in the rig, or a bite at chest height. Lead call.
- **Body bow.** The video keeps the back level and draws a longer neck. The rig needs a bow to reach the floor, so the strike uses about 70% of
  `clip_recipes.head_down_bow` (spine 7/8/17 deg instead of 10/12/25). The front feet stay planted with 2-bone IK (same solver as the recipe). The front legs
  fold a little, where the video's stay straight. This is the main red/blue area at k3/k4 (IoU 0.74-0.80).
- **Side heads.** They are counter-rotated against the bow (link 1 undoes the spine bend) so they stay up, as in the video. They pull in at the
  strike (the outer pair lifts and pulls in by about 30 deg in total, the inner pair by 7 deg), splay out during the hold, then settle. Each pair has its own
  phase factor (0.85-1.15), so they never move as one. These are authored to the video's silhouette, not traced per head.
- **Tail.** From about 1.5 s on, Seedance draws the tail shorter/curled. Left at rest (blue tail tip in every diff, about -0.02 IoU on the side panel).
- **Neck_c bends.** The fitted keys bend neck_c_02/03 by up to 50/45 deg (the rig note says about 25 per joint is comfortable). The strip shows no tear at
  this size. Check the thick neck base at the strike frame in-game.
- jaw_c opens 15 deg at the strike (limit 20).

## Files
`keys_bite.json`, `poses_bite/k0-k6.json` (made by `poses_bite/gen.py poses_bite/params_final.json`: per-key spine bow + leg IK,
neck_c angles, side-neck splay/lean/phase), `action_bite.json`, `strip_bite.jpg`. Scratch + fits: `work/anim/hydra_bite/`.

## animfix_hydra (2026-11-22)
See docs/notes/anim_hydra_fix.md for what changed in this folder (new/retimed clips, generators in work/animfix_hydra/).
