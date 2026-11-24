# Medusa animation fixer (2026-11-22, owner away)

Scratch: `work/animfix_medusa/` (generators `gen_stun.py` + `stunlib.py`, `gen_swipe.py`; headless metric tools `probe_poses.py`
(poses + baked action JSONs, uses animkit's own Rig, never saves) and `measure2.py` (per-frame table of the merged blend);
logs `merge.log`, `export.log`, `import.log`, `probe.log`, `fight_win.log`; Godot shots `probe_shots/`; backups of the blend, clips,
manifest and the original `ak_blender.py` in `backup/`).

## animkit merge bug (fixed in tools/animkit/ak_blender.py, two lines)
`ak merge` re-baked each clip while the PREVIOUS clip's action was still assigned, so `apply_grounded` measured the first key of
every clip after the first on a stale evaluated mesh (= the previous clip's last pose). Fix: `cmd_merge` calls `clear_anim(arm)`
before `bake_data`, and `apply_grounded` forces `evaluated_depsgraph_get().update()` after posing. Verified: re-merging the
animators' unchanged JSONs gave slither root z frame 0 == frame 48 (-0.0255) and stunned frame 0 == stun_start's last frame.
animkit test suite re-run after the change: see the final answer.
**Lead:** every character merged before this fix can have the same first-key ground error on clips 2..n. Re-run `ak merge`
for cyclops / hydra / hercules / pegasus and compare frame 0 with frame N on their loops.

## Decisions (owner away)
1. tail_swipe is now an authored FLAT 360 deg spin sweep (counter-clockwise, tail <= 0.82 m high, impact 0.833 s mid-spin),
   not the video's overhead whip, because the game deals and draws a 360 deg low ring (SPEC: "360 degree low sweep").
   Wind-up (0-0.5 s) is still the video trace. Old whip keys kept unused in `poses_tail_swipe/k2-k8`.
2. Stun chain uses the rig.json lean recipe as written (pivot tail_03 head, no `back` slide): head on the floor 4.45 m (blend) /
   4.56 m (Godot, neck socket) in front; tail planted. Lower side IoU vs the video accepted.
3. hurt shortened to 1.625 s by dropping the shriek hold (not a uniform 0.45 retime: the flinch keeps its speed).
4. idle keys rotated 1.5 s so frame 0 is the rest pose; stun_start/rise/gaze/hurt/tail_swipe keep the true rest pose `{}`
   (differs from idle frame 0 by ~1 deg on the arms only).

## Requests for the medusa module (medusa.gd, not my file)
- `_update_lean` in state `stunned`: use goal 0 while `stun_start` plays (state_time < ~1.6 s at clip speed 1). The clip now
  lowers the neck to 1.04 m itself at 1.625 s; LeanMod currently bows her to 2.1 m during the blinded recoil. In the fight run
  (`fight_win.log`) the bot's first stunned cut lands ~0.8-1.0 s after the reflect at neck_y 2.14 / lean 85-94, i.e. on the
  LeanMod bow, before the clip's collapse. With goal 0 the bot must wait until ~1.6 s (head on the floor, neck ~1.0-1.1 m,
  ~4.5 m forward; the weak-point clamp 1.0-2.3 m still holds).
- tail_swipe: impact is 0.833 s of 2.25 s; clip speed = impact / coil (0.7 s) -> 1.19x, so the visible spin starts ~0.42 s
  into the coil and the whole clip lasts ~1.9 s at that speed (recover 0.9 s still fits after the impact).
- rise: still 2.5 s; at rise_time 0.8 s (3.125x) the push is 0.16 s. Optional: rise_time ~1.2-1.4 s reads better.
- hurt is 1.625 s now (recoil waits the clip length).
- The root bone sits at (0, -1.92, 1.72) Godot in stunned (was -2.6): still read pelvis, not root, for placement.
