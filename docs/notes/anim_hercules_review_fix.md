# Animation fixer: hercules review findings (2026-11-22; the owner was away, so the decisions below are noted for the lead)

Source: the independent review (`docs/notes/anim_review_hercules.md`, 14 findings). Scratch, scripts, logs and the
before/after numbers are in `work/anim/hercules_review_fix/`. Backups from before the fix: `orig/` (clip folders),
`hercules.blend.before_fix`, `hercules.glb.before_fix`, `hercules_clips.json.before_fix`.

## Rebuild (in this order)
1. `work/anim/hercules_review_fix/merge_each_fix.sh` (one `ak merge` per clip, 14 clips incl. the new block_end)
2. `work/anim/hercules_review_fix/rebuild_glb.sh` = `ak export` -> `work/assemble_hercules/strip_props.py` -> `measure.py`
   -> `finalize_manifest.py` -> `manifest_addons.py` (suggested_speed_scale + game_note per clip) -> reviewer's analyze.py
3. Import under the lock (SPEC §10), then `work/assemble_hercules/probe.gd` (result: PASS, 13 core clips, 4 sockets).

## What changed
| clip | length (was) | game speed | what |
|---|---|---|---|
| attack_1 | 1.25 s (1.25) | x2.27 | starts/ends on idle k0; k1a_draw re-solved (IK) so the back (right) foot steps into the lunge; left (back) foot planted wind -> slash; swing 0.458-0.667 = 5 frames (92 ms game; was 2 frames / 37 ms) from 4 read-back in-betweens; shield keeps the k1_wind twist at release; chain pose (k4_end == attack_2 k0_start) at 0.917 = game 0.40 s = Tuning.ATTACK_CHAIN_FROM; then steps back to idle k0 by 1.25. Events active 0.458-0.708 (game 0.202-0.312), `chain` 0.917 |
| attack_2 | 0.833 s (1.5) | x1.28 | split retime: wind-up x0.5, chop 0.25 -> 0.375 over 3 frames (98 ms game; was 1 frame / 18 ms), recovery x0.33, k6b_settle re-solved to step back, ends on idle k0. Active 0.25-0.458 (game 0.195-0.357; was 0.181-0.271) |
| hit | 0.458 s (2.167) | x1 | idle k0 -> impact 0.042 -> peak 0.083 -> arch 0.167 -> hold 0.292 -> recover 0.375 -> idle k0; traced spine/neck/head/arm angles on the idle k0 legs (ground left) |
| block_start | 0.25 s (0.417) | x1 | retimed x0.6: ends exactly when player.gd's 0.15 s switch + 0.1 s blend into block_idle ends (foot gap at the switch 0.10 m, was 0.44 m) |
| block_end | 0.25 s (new) | x1 | block_start reversed (block_idle frame 0 -> idle k0) for lowering the shield; core does not play it yet |
| death | 3.75 s | x1 | sword above the floor: k4b_sword 2.792 + hand_r aimed on k5..k6f and k8_h (blade tip min +0.064 m in the GLB, was -0.261); topple = re-grounded read-backs every 2 frames 2.875-3.208, linear (old k5b/k6/k6b dropped); `events.drop_props` 2.1 |
| strafe_l / strafe_r | 0.833 s | - | eased lift: new k01 / k11 (read-back + IK, the foot keeps 1/3 of its slide and the knee turns gently); seam velocity jump 7.4 -> 4.8 cm/frame (largest interior step now 5.2 at frame 1); strafe_r rebuilt with make_strafe_r.py |
| skirt (rig) | - | - | `scripts/skirt_drivers.py`: skirt_f/b from the MEAN thigh pitch with a soft cap (24 deg), seated clearance eased in (both thighs > 30-60 deg forward: ride), side-panel spread 1:1 to 20 deg then 0.65 per degree. rig.json `driven.spec` updated. All 14 clips re-merged |

Transitions in the GLB (reviewer's compat.py): idle -> attack_1, attack_1@0.917 -> attack_2, attack_2 -> idle,
idle <-> hit, idle -> block_start, block_start@0.25 -> block_idle, idle <-> roll, idle -> death: all 0.000 m.
Lowest skinned vertex per frame within +-1.0 cm in attack_1/attack_2/hit/block/strafe; death topple within +-1.1 cm.

## Decisions
- **Chain timing done in the clip, not in core.** The chain pose sits at the game's current ATTACK_CHAIN_FROM (0.40 s),
  and the rest of attack_1 is the recovery to idle, so the no-chain case needs no core change either. Consequence:
  **do not set ATTACK_CHAIN_FROM = ATTACK_1_TIME** (the reviewer's preferred core option) without re-timing attack_1.
- block_start was retimed instead of asking core to change the switch time.
- Roll: the optional extra tuck at k6 was not done (the roll was not otherwise touched).
- The skirt fix is a driver change only (no new hem weights): mesh weights in the blend were not edited.

## Requests for core (game code; I did not change it)
1. `_anim_loco`: set the AnimationPlayer speed to `clamp(ground_speed / clips[c].move_speed, 0.6, 2.5)` (needs a
   `CharacterVisual.set_speed()`); manifest now has `suggested_speed_scale` (run 1.3, strafe 2.5, walk_back 2.0). Cap the
   locked-on sideways speed at ~1.8 m/s.
2. Lowering the shield: play `block_end` (0.25 s) instead of the 0.15 s locomotion blend (that slides the right foot 0.68 m).
3. death: detach the sword/shield attachments at `events.drop_props` (2.1 s).
4. Backward roll (`_roll_dir = -facing`): play `roll` at speed -1 (starts/ends on idle k0) or turn the visual 180 deg.
5. hit: HIT_FLINCH 0.4 at 1x shows all but the last 2 frames; `play(hit, 0.05, 0.458 / 0.4)` would show the end too.
6. Lead: `docs/notes/hercules.md` (named as a source of game requirements) does not exist: create it or point briefs at
   `docs/notes/core.md` + `tuning.gd`.

## Still not right
- Idle: the forward left thigh now pushes through the front-left hem (skin patch seen from the front); strafe/ride
  wide stances show small thigh patches at the side panels. Mostly invisible from the chase camera behind him. A real fix
  needs hem weights across the centre (blend edit), which I did not attempt headless.
- attack_1 is in place, so feet slide while stepping into/out of the lunge (planted left foot median 0.38 m/s); the
  game's 0.7 m lunge covers the active part.
- death lying pose (3.25-3.75 s): the shield rim is ~5 cm under the floor (pre-existing, not in the review).
- Strips' reference rows use the old video windows: for retimed clips (attack_1/2, hit, block) they no longer line up.
