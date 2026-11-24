# Pegasus animation fixes (animation fixer, 2026-11-22)

The owner was away, so this agent made the decisions below and notes them here. Scratch: `work/anim_pegasus_fix/`
(the pre-fix sources, blend and GLB are backed up in `work/anim_pegasus_fix/backup/`).
Input: `docs/notes/anim_review_pegasus.md` findings 1-5. No Higgsfield credits used.

## Result
- `game/assets/characters/pegasus/pegasus.glb`: 7.11 MB, clips fly 1.0417 s, glide 3.0 s, idle 7.0 s, all loop.
  GLB scan (`work/anim_pegasus_fix/glb_seam.py`): every channel has seam translation 0.0000 m and rotation <= 0.06 deg.
  - fly root translation Y: 0.0 at t 0 and at t 1.0417. Before the fix it was -0.0804 and 0.1412.
  - Biggest step per frame in fly: wing_*_01 44 deg (was 58), leg_fl_03 12 deg (was 41).
- Manifest: the `rider` block is unchanged (offset, beat_period_s 1.48, rider_clip ride, speeds 1.44 / 0.4). A new
  `rider.fly_bob` note was added and the clearance text was updated.
- Godot: re-imported under `work/.import_lock`. The assembler's `probe.gd` prints `PROBE ok=true` (clips,
  lengths, loop modes, sockets, seated rider). The headless `--start=sea --harness --bot=idle --quit-after=6` run is clean.
  - The saddle socket is now at y 2.127 m in fly AND glide. Before, fly put it at 1.984 m and glide at 2.127 m, so a
    crossfade moved the rider 14 cm and pitched the horse 8 deg.
- Rider pair check (`ridden/pair_check.py` on a temporary copy of ride.blend in art_src/chars/ride/, deleted after):
  0 wing/rider/sword/shield overlaps for fly at 50 samples per beat (rider at beat speed, phase 0 = wing top),
  for glide on 36 frames and for idle on 42 frames (rider at 0.4x).

## Decisions
1. **Seam pop (blocker).** Re-ran the assembler's merge, export and finish_manifest with the current tools (merge bug
   fixed at 20:49). The pop is gone.
2. **fly legs/body (major).** Wrote `art_src/chars/pegasus/clips/fly/make_fly_v2.py`. It turns the animator's matched pose
   files into `poses_fly/v2_*.json` and keeps the matched files as its input.
   - Legs, neck and head get graded in-betweens, using the reviewer's fractions.
   - The forelegs are capped at 75% of k3. At 100% the down phase looked like a standing horse, and the video keeps
     the forelegs half tucked.
   - `root.ground` is dropped. Root z is keyed by hand: 0 / +0.04 / +0.08 / +0.03 at t 0 / 0.33 / 0.625 / 0.9. The
     peak is at 0.625 rather than 0.65, because 0.65 is not on the 24 fps frame grid.
3. **Body pitch removed (the reviewer's optional item, my decision).** fly root.rot -8 is now 0, the same as glide.
   - A rider glued by position no longer rocks 8 deg in the crossfade.
   - To keep the flying look, the 8 deg goes into the legs, neck and head (absolute rx -8), so they hang in the world
     as before. The wings are not compensated: they sit 8 deg flatter than in the match.
4. **Downstroke timing (minor).**
   - mid_down moved to 0.292.
   - A settle key was added at 0.458: wing_*_01 ry 5 deg lower, wing_*_02 rz 5 deg more curl. Smaller ry = lower on
     this rig, checked with `ak solve`.
   - A hang key was added at 0.625, and down_end moved to 0.750 at the k3 height. The old k4 (ry 82) had already
     lifted the wing.
   - mid_up moved 0.833 -> 0.875. The video snaps from hanging (1.750) to horizontal (1.792) to 30 deg up (1.833).
     With mid_up at 0.833 that snap was 46 + 53 deg per frame. Now it is 21 / 45 / 33 / 15.
   - Downstroke steps are 44 / 32 / 26 / 29 deg per frame, about the 40 the reviewer asked for. The one 44 deg frame
     is k1->k2, and moving k2 further would put it ahead of the video.
5. **Rider sweep.** `make_ridden.py` was re-run with 25 deg on the v2 clip and baked to `ridden/fly/`. The pair check is
   above. The 25 deg uniform sweep stays (the assembler measured that 10 deg is not enough on this wing family).
6. **glide (cosmetic).**
   - leg_fl_02 / leg_fr_02 rx -10 on all keys.
   - wing_r_03 ry -4 on k1/k3.
   - Strip 0.781, the same as before.
7. **idle (optional).** wing_*_02 capped at 20 deg at k_wing_max / k_wing_hold, with the 4 deg moved to wing_*_01.
   IoU unchanged at 0.72 front.

## What is still not right
- **fly video match is lower.** The strip mean is 0.635 for the clip and 0.60 for the ridden clip; before the fix they
  were 0.708 and 0.645. The causes:
  - Hand-keyed bob versus the video's floor-locked hooves.
  - No pitch.
  - Wings hanging close to the body, where Seedance drew them wide.
  By eye the beat reads correctly and the motion is smooth.
- **fly's lowest hoof dips 3 cm below z 0 at the wing top.** The baseline was kept equal to glide (root z 0), so the
  crossfade does not jump. If the game ever uses the origin as a floor during flight, add 0.035 m to BOB_Z in
  make_fly_v2.py.
- **No `fly_ridden` clip.** `fly` itself is the rider-safe clip, as the assembler decided.
  - The ride reference video exists (`art_src/chars/ride/clips/ride/ref.mp4`, 1.48 s beat).
  - A separate ridden clip matched to it would need a Pegasus pass on that video. That is not required, because the
    game only flies Pegasus with Hercules on board.

## Requests for other modules
- **world (pegasus_flight.gd), from review finding 4.** Not my files, so not changed.
  - Rider sync: set `rider position = fmod(fly_pos / fly_beat_s, 1) * 1.5` every frame (manifest `rider` block).
    Use speed 1.44 on fly (x1.25 while boosting, like the fly clip) and 0.4 on glide. Today it free-runs at 1.0.
  - Bob: fly now carries its own 8 cm bob, peaking at clip t 0.625. Remove the 0.22 m `sin(_clock*TAU/beat)` code
    bob, or phase it from the fly AnimationPlayer position. Otherwise it fights the clip.
  - Pitch: the fly pitch is gone, so position-only seating no longer rocks in the crossfade. Nothing to do.
- **Lead: other GLBs with loop-seam translation gaps** (from the review scan; same stale merge, so re-merge with the
  current tools): medusa stunned root 0.354 m, hydra walk root 0.052 m, medusa slither root 0.032 m.
- **animkit owner:** the green-key silhouette (`work/anim/pegasus_fly/akg`) is still a scratch wrapper. All Pegasus
  IoU numbers need it.

## Rebuild (from the repo root)
1. `python3 art_src/chars/pegasus/clips/fly/make_fly_v2.py`, then
   `cd art_src/chars/pegasus/clips/fly && ../../../../../tools/ak bake ../../pegasus.blend --clip fly --keys keys_fly.json --loop --fps 24 --out-action action_fly.json`
2. `python3 art_src/chars/pegasus/ridden/make_ridden.py art_src/chars/pegasus/clips/fly/action_fly.json 25 art_src/chars/pegasus/ridden/fly`
   + the ridden bake (docs/notes/assemble_pegasus.md step 2)
3. glide / idle: `tools/ak bake ... --keys keys_<clip>.json --loop --fps 24 --out-action action_<clip>.json` in their folders
4. assemble_pegasus.md steps 3-5 (merge idle, glide, ridden fly; export; finish_manifest.py), then the Godot import
   under the lock and `work/assemble_pegasus/probe.gd`.
