# pegasus / fly (animator, 2026-11-22)

fly | video window 1.000-2.042 s (one wing beat; `ak cycle` period 1.0417 s = 25 frames at 24 fps, self-IoU 0.986, the beat repeats cleanly for the whole video) | 7 keys + loop seam | length 1.0417 s, loop, 24 fps | events: none (SPEC lists none for fly)
IoU per key (front/side, `ak pose` against `ak frames` output): k0 up t0.000 0.86/0.72; k1 up_spread t0.250 0.77/0.66; k2 mid_down t0.333 0.77/0.66; k2b mid_down_late t0.375 0.75/0.67; k3 down t0.417 0.60/0.68 (scored on the 1.500 frame, held to 0.708); k4 down_end t0.708 0.62/0.73 (scored on 1.750); k5 mid_up t0.833 0.81/0.69. Key mean 0.74 front / 0.69 side. Strip (17 frames over the loop, `strip_fly.mp4`): mean 0.708, seam 0.865/0.702 on both ends.
What does not match and why:
- Down poses top out at ~0.60 front: Seedance redrew the wings much broader in the downstroke (the fan reaches the floor and sits wider of the body than the rig's wing can). The rig's wing hangs at the sides with the primaries splayed slightly outward (wing_*_02 curl -10/10/-10, within the rig's 20 deg limit); IoU-optimal fits that hook the tips further out were rejected as unnatural.
- The video keeps the hind hooves near the floor the whole time (a hover "on a treadmill"); every key uses `root.ground: lowest`, so the body bob (0-7 cm) comes from the leg tuck/extend, which follows the video.
- Body pitch is a constant 8 deg nose-up (`root.rot`); the video's body barely pitches.
- Tail: authored secondary wave (chain bend_up/bend_side, lagging the wing beat), not traced. Mane/feather fan (wing_*_feather_0x) not animated. Neck within the rig notes' limits (neck_01 <= 20, neck_02 <= 15 deg).
- Strip frames sit a few video frames off the key frames (fast wings), so strip IoU at the keys reads lower than the per-key numbers above.
- IMPORTANT tooling note: animkit's silhouette counts the pegasus' green background as character (calibration and IoU are meaningless with plain `tools/ak` on this video). All matching here used the green-key wrapper `work/anim/pegasus_fly/akg` (same ak, patched silhouette); details in docs/notes/anim_pegasus_fly.md. Bake used plain `tools/ak` (no silhouette involved).

## v2 (animation fixer, 2026-11-22, after docs/notes/anim_review_pegasus.md)
fly v2 | same window 1.000-2.042 s | 9 keys + loop seam (`make_fly_v2.py` writes `poses_fly/v2_*.json` + `keys_fly.json` from the matched k*.json above) | length 1.0417 s, loop, 24 fps | events: none
- Legs, neck and head are graded between the tucked k0 and the extended k3 (fraction 0 / .30 / .40 / .65 / .85 / .92 / 1.0 / .68 / .40 at t 0 / .25 / .292 / .375 / .417 / .458 / .625 / .75 / .875; forelegs go only 75% of the way). Max step leg_fl_03 12 deg/frame (was 41).
- No `root.ground`, no body pitch (root.rot 0, as in glide). The 8 deg nose-up is put into the legs, neck and head (absolute rx -8) so they hang as before. Root z keyed by hand: 0 at the wing top, +0.04 at 0.33, +0.08 at 0.625, +0.03 at 0.9. The lowest hoof is 3 cm below z 0 at the wing top. That does not matter in flight; the glide hooves are 14 cm above z 0.
- Wings: mid_down 0.333 -> 0.292, settle at 0.458 (wing_*_01 ry 5 deg further down, wing_*_02 rz 5 deg more curl), a hang key at 0.625, down_end at 0.750 at the k3 height (the old k4 lifted the wing from 0.417 on), mid_up 0.833 -> 0.875, so the snap-up of the video is spread over 3 frames. Max wing_*_01 step 44 deg/frame (was 58).
- Strip (akg, 17 frames): mean 0.635 (front 0.82 at the wing top, 0.49-0.55 while the wings hang: Seedance draws them wider; side 0.56-0.69). Some of the drop is framing: the video holds the hooves on its floor line, and the hand-keyed bob does not.

## Re-base (natural pass, 2026-11-23, re-base animator)
fly rebase | base = art_src/chars/pegasus/ridden/fly/action_fly.json (the game's rider-safe fly WITH the 25 deg sweep) | 25 keys, one per frame (incl. the 9 base key times, values unchanged) | 1.0417 s, loop, no events, t 0 = wing top | wing_03 + feathers lag the beat 0.10-0.11 s, spine_03/neck/head counter-nod, cannons paddle, tail wave | moving joints 28 -> 38 of 41 | rider pair check 0 hits / 50 samples. action_fly.json here is now the rider-safe game clip: merge it INSTEAD of ridden/fly/action_fly.json and never run ridden/make_ridden.py on it. The matched v2 is kept as keys_fly.rest_v1.json / action_fly.rest_v1.json / strip_fly.rest_v1.*. Details: docs/notes/rebase_pegasus.md.

## fly v3 (animation fixer, 2026-11-23)
fly v3 | base = keys_fly.rebase.json (the re-based rider-safe fly, 25 per-frame keys rb_k*.json) | 25 keys fx_k*.json | 1.0417 s, loop, no events, t 0 = wing top, root bob unchanged | tool `work/anim2/pegasus_fix/fly/fly2_bl.py` + `fly_params.json`
- All edits on whole chains (absolute pose bones do not follow their parents): time warp of both wing chains (01/02/03 +
  feathers) on frames 4-11 (downstroke ease-in: wing_01 per-frame turn 2.9, 4.8, 7.2, 44.4, 31, 27, 29, 5 -> 2.9, 8.1, 17.5,
  28.0, 30.5, 28.8, 23.0, 9.9), 16-21 (upstroke ease-in: 1.1, 2.4, 21.3, 40.0, 29.5 -> 4.5, 12.0, 23.9, 29.9, 23.9) and 21-25
  (wing_02 eases into the top: 10.2, 6.1, 9.1, 5.3 -> 10.2, 8.8, 6.5, 4.2, then 1.4 after the seam).
- Right wing chain 1 frame late (wraps) and its swing x0.97 about its loop mean: wing_01 L/R corr 1.000 -> 0.965, wing_02 0.825.
- Legs de-phased: leg_fr_* 0.0625 s, leg_bl_* 0.042 s, leg_br_* 0.1 s behind leg_fl_* (fore pair corr 1.00 -> 0.92, hind 0.78).
- Rider pair check (`ridden/pair_check.py`, rider one loop per beat, 50 samples): 0 hits. Strip (akg, 8): 0.587 (re-base 0.589).
- Re-base version kept: keys_fly.rebase.json, action_fly.rebase.json, strip_fly.rebase.* (clip name fly: never merge it).
  make_ridden.py was NOT run (the 25 deg sweep is in the base).
