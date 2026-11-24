# Pegasus animation review (independent reviewer, 2026-11-22)

The owner was away, so this agent made the calls below and notes them here. Scratch is in `work/anim_review_pegasus/`.
Nothing under art_src/chars/pegasus or game/assets was edited.

## Verdict: pass with fixes. One must-fix: the shipped `fly` has a 22 cm loop-seam pop

| clip | GLB | video match | seam | rider clearance (game seating) |
|---|---|---|---|---|
| idle 7.0 s | ok | good (strip 0.915). The wing spread is smaller than the video's (front 0.72) | exact | 0 hits, 42 samples x 4 rider phases |
| fly 1.0417 s (rider-safe, 25 deg sweep) | **root z pop at the seam** | wing beat ok. The legs and body step between held poses | **-0.080 vs 0.141 m** | 0 hits, 50 samples synced + 25 x 4 phases. Min leg gap 3.0 cm at t 0.333 |
| glide 3.0 s | ok | good (0.78) | exact | 0 hits, 36 synced + 18 x 4 phases. Min gap 8.1 cm |

All 108 crossfade blends (fly->glide and glide->fly over 0.35 s, idle->fly over 0.3 s, at 12 phases and weights
0.25/0.5/0.75) gave 0 hits. The matched (unswept) fly, seated the game's way, hits on 10 of 25 frames with up to 625 pairs,
which confirms the assembler's decision to use the swept version.

## Findings
1. **fly seam pop (blocker, mechanical).** In pegasus.blend and the GLB, root loc z is -0.0804 at frame 0 but 0.1412 at frame 25.
   The action JSON (`ridden/fly/action_fly.json`) has 0.1412 at both ends. The cause is the stale first-key ground bug
   in the old `ak merge`. It was fixed in `tools/animkit/ak_blender.py` at 20:49, after the 20:39 merge. Re-running the
   assembler's rebuild steps 3-5 with the current tools fixes it: a scratch-copy merge gave 0.1412 at frame 0.
   The same scan found loop-seam translation gaps in other GLBs that should be checked:
   - medusa `stunned` root: 0.354 m
   - hydra `walk` root: 0.052 m
   - medusa `slither` root: 0.032 m
2. **fly legs and body step-hold-snap (major).**
   - The leg angles and `root.ground` change only between the key pairs 0.25->0.333, 0.375->0.417 and 0.708->0.833,
     and are held flat in between. In the GLB, leg_fl_03 turns 41 deg in one frame at t 0.375->0.417 and 82 deg
     over 3 frames at 0.708->0.833.
   - Root z drops 9 cm over 2 frames as the downstroke starts. The body is lowest during the downstroke, which is the
     reverse of the ride video (lowest at the wing top, highest at the end of the downstroke).
3. **fly downstroke ends in a dead stop (minor).** wing_*_01 turns 26, 58 and 29 deg per frame, then 0.5 deg per frame
   at t 0.417. The upstroke starts about 0.1 s early compared with the video (1.750 s).
4. **Game integration (minor, world module).**
   - The rider plays `ride` at 1.0x free-running, not at the manifest's 1.44 with phase re-sync.
   - The 0.22 m code bob `sin(_clock...)` is not phased to the AnimationPlayer.
   - The rider is glued by position only, so Pegasus's 8 deg nose-up in fly (0 in glide) rocks under an upright rider
     during the 0.35 s crossfade.
5. idle wing spread: a slight crease at the wing root at 5.9-6.3 s. There is no tearing (checked by eye).
   glide: the forelegs fold less tightly than in the video (cosmetic).
