# Cyclops animation review (independent reviewer, 2026-11-22; owner away, decisions noted)

Measured on the shipped GLB (game/assets/characters/cyclops/cyclops.glb) frame by frame in headless Blender
(work/anim_review_cyclops/measure_glb.py -> glb_frames.json, ana.py), plus the animators' strips and check renders
(work/anim_review_cyclops/checks_A.jpg, checks_B.jpg). Verdict: FAIL until the hurt/stuck problem is fixed.

## Blocker
- **hurt plays during stuck.** BossBase.take_weak_hit plays `hurt` (blend 0.08 s) on every non-lethal forearm hit, and the
  forearm is only open in `stuck`. The delivered hurt is a 2.25 s UPRIGHT clip that starts from the rest pose (club held
  up), so after the first hit the giant snaps out of the bent-over stuck pose and stands with the club in the air for
  ~2.0 s of the 3.0 s window (resume timer = 0.9 x 2.25 s), then snaps back. Joint jump stuck -> hurt start: 5.0 m.
  Forearm goes from 2.5 m to ~6.4 m, the weak point falls back to the straight clamp: this is the likely reason the
  real-model bot lands only 1 hit per stuck window (assembler: fight 62 s instead of 31-37 s).
  Fix (art): re-key `hurt` as a stuck-pose flinch, 0.6-0.7 s, first and last key = poses_stuck/k00_stuck.json; the right
  hand and club stay put (club head moves < 0.1 m); the flinch is head rx about -25 (thrown back), spine_03 rx -8, the
  left upper arm and lower arms jerk, linear 2-frame snap like the current k0 -> k1. Fallback (module), until then:
  `hurt_clip = &""` in cyclops.gd.

## Requests for the cyclops module
- Walk: plays at speed 1 now, planted foot ~0.95 m/s vs 2.6 m/s body: feet skate. Preferred fix is in the art (retime
  walk x0.365 -> ~1.43 s cycle, so `_step_beat()` = 0.71 s matches STEP_INTERVAL); otherwise play walk at ~2.7x.
- Crack / chunks: put them at the club head (node `club`, head = club.global_transform * (0, 5.05, 0)) until stuck is re-keyed.
- Death keeps root motion (head ends 4.9 m forward today): play it without moving the body.
