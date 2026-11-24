# Pegasus re-base (natural pass, 2026-11-23, re-base animator)

The owner was at the Mac and could not be asked, so I made every decision myself and wrote it down here. Blender ran headless only and nothing opened a window.
Plan source: `docs/notes/natural_pegasus.md` §4 (idle = V, glide = R, fly = R). I re-based **glide** and **fly**. idle is a V clip
(`idle_n`, another animator). `art_src/chars/ride/` holds no pegasus action (only the hercules `ride`), so there is no
fly_ridden for me to leave to anyone.

## Method (one tool for both clips)
- `work/rebase/pegasus/rebase_bl.py` runs in headless Blender. It opens `pegasus.blend` in place and read-only and never saves it.
  It loads the base action, then on every key time it reads the posed bone matrices and adds a life layer from
  `work/rebase/pegasus/life.json`. The life layer has two parts:
  - sines `[axis, amp, cycles per loop, phase]` in view axes, applied as a local delta. Children ride along.
  - lagged follow-through: `slerp(I, R_src(t - lag) R_src(t)^-1, gain)`, capped. It wraps around the loop.
  The tool then writes ABSOLUTE pose files (the same maths as `ak pose --save-pose`), `poses_<clip>/rb_kNN.json`, and
  `keys_<clip>.json`. The clips are baked with `tools/ak bake ... --loop --fps 24 --out-action`.
- Every sine has a whole number of cycles per loop, and the lags wrap, so the loop seam is exact. bake also copies key 0 to the seam.
- The base key times are keys in the new clip, with the base values. Check (`work/rebase/pegasus/check_keys.py`): wing_*_01/02,
  hips, spine_01/02 and saddle differ by < 0.15 deg at every base key time. That is the noise floor of 6-decimal quaternions,
  0.0 for the untouched trunk. Root loc diff is 0 m.
- The natural stance (`natural_pose.json`) is a STANDING pose: folded wings, a resting hind leg, a ground contact. Neither
  flight clip uses it. The plan for them is life only (natural_pegasus.md §4), so no stance entries were added.
- hips, spine_01 and spine_02 stay still on purpose in both clips. The saddle and both wing roots hang on spine_02, and the
  rider and the matched wing beat must not move. The trunk life is on spine_03 (forehand, neck).
- Rider check: `ridden/pair_check.py` on a copy of ride.blend in `work/rebase/pegasus/rc/chars/ride/`. Symlinks
  `rc/chars/{hercules,pegasus}` and `rc/props` make its relative textures resolve, because peg_regions reads the albedo. The copy
  was deleted afterwards.

## glide (3.000 s, loop, no events; unchanged)
- Base: the matched clip, kept as `clips/glide/action_glide.rest_v1.json` (+ keys/strip `.rest_v1`).
- 24 keys, one every 3 frames, including the matched key times 0 / 0.75 / 1.625 / 2.375.
- Life (peak world change per bone, cumulative down each chain):
  - spine_03: 2.8 deg. It answers the 1.5 s wing breath, plus one 3 s breath.
  - Neck look/nod with lag: neck_01 4.5, neck_02 6.7, neck_03 8.6, head 10.5. The phase lags 0.07-0.30 cycle, so the head steers and never moves in unison with the neck.
  - Tucked legs paddle at 2.4-4 deg per joint (hooves 9-14 deg world). Fore and hind pairs are out of phase, and so are left and right.
  - The tail streams with lag down the chain: tail_01 2.5 deg, tail_05 18.7 deg.
  - wing_*_03 trails the wing breath by 0.20 / 0.24 s (L/R): 7.1 / 5.8 deg.
  - Feather groups trail and flutter at 0.75 s: 3-8 deg. Neighbouring groups change by <= 3.7 deg relative to each other (rig limit ~20).
- `clip_motion`-style count on the action: **13 -> 38 of 41 joints move** (>= 3 deg). Still under 3 deg: hips, spine_01 and spine_02 (on purpose).
- Rider pair check (rider at 0.4x): **0 hits on 72 frames**.
- Look: the strip shows no pops, no limb through the body and an exact seam. The front view is no longer mirror-symmetric.

## fly (1.0417 s, loop, no events, t 0 = wing top; unchanged)
- Base: **`ridden/fly/action_fly.json`, the game's rider-safe fly with the 25 deg forward sweep**. The matched v2 is not the
  game clip.
- The output is in `clips/fly/` (my folder). The old matched v2 is kept as `keys_fly.rest_v1.json`, `action_fly.rest_v1.json` and
  `strip_fly.rest_v1.{jpg,mp4}`.
- **Assembler:** merge `clips/fly/action_fly.json` in place of `ridden/fly/action_fly.json`. Never merge both, because both are
  clip `fly`. Never run `ridden/make_ridden.py` on the new file: the 25 deg sweep is already in it, and the script would add a
  second one. `keys_fly.json` carries `ridden_sweep_deg: 25` and a WARNING.
- 25 keys, one per frame. They include the 9 base key times.
- What stays the same:
  - the wing beat: wing_*_01/02 and the sweep
  - the leg and neck grading
  - the root bob (fly_bob)
  - the beat phase
- Follow-through:
  - wing_*_03 lags the beat by 0.100 / 0.110 s (L/R), with gain 0.50 / 0.44, capped at 18 / 16 deg. It hits the cap at the fastest part of the stroke. The tips curl up on the downstroke and trail on the upstroke.
  - feather_01 / 02 / 03 lag with gains 0.18 / 0.30 / +0.06 (L) and 0.16 / 0.26 / +0.05 (R). Neighbouring groups change by <= 10 deg relative to each other.
  - spine_03 breathes 2 deg once per beat.
  - Counter-nod with lag: neck_03 5.5 deg, head 7.2 deg world.
  - The cannons paddle 1.3-2 deg, out of phase.
  - The tail wave lags down the chain: tip 8 deg on top of the existing authored wave.
- Count: **28 -> 38 of 41 joints move**. hips, spine_01 and spine_02 stay still on purpose.
- Rider pair check (one rider loop per beat, both starting at the wing top, every half frame): **0 hits on 50 samples**. The
  feather lag did not bring the lobe back into the rider's legs.

## Still stiff, and why
- hips, spine_01 and spine_02 have no life in either clip. The saddle and the wing roots hang there, and the fly_bob and glide/fly
  crossfade contracts keep the root as keyed. The body still answers the beat through spine_03, the neck and the root bob.
- In fly, the head look is only 1.4 deg of yaw per beat. A slow look would need a cycle longer than the 1.04 s loop, which
  would break the seam. Slow steering belongs in game code (e.g. a look-at on the head) if wanted.
- glide keeps the matched pose family. The legs paddle only a little (3-4 deg per joint) so they stay inside the video's
  silhouette.

## Files
- Clips:
  - `art_src/chars/pegasus/clips/{glide,fly}/keys_<clip>.json`
  - `poses_<clip>/rb_k*.json`
  - `action_<clip>.json`
  - `strip_<clip>.{jpg,mp4}`
  - `*.rest_v1.*` (the previous versions)
- `art_src/chars/pegasus/rebase_done.json`
- Tools and scratch:
  - `work/rebase/pegasus/` (`rebase_bl.py`, `life.json`, `check_keys.py`, `motion.py`, `crop_sheet.py`)
  - `pair_rebase.json`
  - before/after mp4s
- Devlog: `docs/devlog/media_inbox/rebase_pegasus/{glide,fly}_before_after.jpg` and `captions.txt`.
