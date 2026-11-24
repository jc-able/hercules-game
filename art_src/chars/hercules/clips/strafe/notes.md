# hercules / strafe video: notes

| clip | window | keys | IoU per key (front/side) | length | events | loop | stride |
|---|---|---|---|---|---|---|---|
| strafe_l | 2.50-3.33 s (t0 = 2.5) | 10, one every 2 frames, all `linear` (k00 ... k18) | k00 0.76/0.82, k04 0.77/0.80, k10 0.76/0.80, k14 0.76/0.79 (strip mean 0.73; the last 3 strip frames score 0.43-0.58 only because the video body has travelled ~0.22 m) | 0.833 s (20 frames @ 24 fps) | none | yes | 0.6 m per cycle = 0.72 m/s at speed_scale 1 |
| strafe_r | mirror of strafe_l (no video of its own) | 10, same times | against the strafe_l frames: k04 0.70/0.80, k10 0.74/0.80 (a plain mirror scored 0.59/0.66) | 0.833 s | none | yes | 0.6 m per cycle |

## Fix pass (2026-11-22, animation fixer; owner away: decisions noted)
Originals: `work/anim/hercules_strafe_fix/orig/`. Generators: `work/anim/hercules_strafe_fix/gen_fix2.py` (strafe_l) and
`make_strafe_r.py` (strafe_r). Scratch and test renders are in the same folder.

1. **strafe_r made.** `ak mirror --keys keys_strafe_l.json`, then the un-mirrored strafe_l entries put back for upper_arm_l/r,
   forearm_l/r, hand_r, spine_01, spine_02, neck and head. The mirrored hand_l entry is removed, so the sword stays in
   the right hand and the shield covers the front. Legs, hips and root stay mirrored, so the RIGHT foot steps out in
   frames 0-10 and the left follows in frames 10-20. I checked this by solving all 20 frames. Do not regenerate strafe_r
   with a plain mirror: rerun `make_strafe_r.py` after any strafe_l change.
2. **Stride (decision).** The animator's clip moved the planted foot only 0.27 m per cycle (0.275 m/s). The game moves
   at 4.6 m/s. I chose the clip side of reviewer option (b): ankles now go between x ±0.25 m (narrow) and ±0.55 m (wide)
   from the hips. The video has ±0.32 and ±0.455. That gives 0.30 m per stance phase and 0.6 m per cycle, which is
   2.2x the old clip. It costs about 0.05 front IoU on the legs. The wide stance moved from 0.375 s to 0.417 s (half
   the cycle), so both phases slide at the same speed. `keys_strafe_*.json` carry `stride_m: 0.6` and
   `natural_speed_mps: 0.72`. The clips manifest does not take these fields yet: lead, see
   docs/notes/anim_hercules_strafe_fix.md. A side-step still cannot reach 4.6 m/s without skating; the game side has to
   decide that.
3. **Foot skating.** All keys are `linear`, and every pose is solved with leg IK (`legik.py`) from foot targets. The planted
   foot slides -X at a constant 30 mm/frame (29.5-30.7 mm; it varied 5-22 mm before) and stays within 2 mm of the floor.
   The swing foot follows a cubic curve and lifts 4 cm. The clip has no hold or slide-out after landing any more.
4. **Sword.** I fitted upper_arm_r / forearm_r / hand_r on the 2.500 s frame (`ak fit`), starting from upper_arm_r rx 20
   and forearm_r rx -25. Result: upper_arm_r (20, 4, 29), forearm_r (-9, 43, 62), hand_r (-32, 92, -12.3). The hand is
   now at belt height. The blade points up and screen-left in the front view and forward-up in the side view, as in the
   video. The entries are identical in every key.
5. **Shield fist.** The suggested forearm_l rx -75 / rz -15 did not work. In this rig `rz` is a yaw, so it turned the
   shield edge-on to the camera. The real cause was that the front camera saw the INSIDE of the shield with the forearm
   lying across it. Fix: forearm_l in aim form `{front -114.5, side -109, twist 140}`, then upper_arm_l fitted to
   (-38, -4, -12.5). The front view now shows the emblem face turned out to his left, and the forearm and fist are
   hidden behind it (only a knuckle shows at the outer rim). On k0 with the old legs this scores 0.81/0.82, against
   0.81/0.82 before, so nothing was lost.
6. **Head.** neck rx -16 -> -8 and head rx -24 -> -16 in every key.
7. **Knees.** Both thigh ry values were pushed 4 deg further out before the IK solve. The wider stance also moves the
   knees out (k10 left knee x 0.40 m, was 0.34).

## Still not right
- **Skirt split (rig, not fixable here).** The driven skirt still opens up the middle in the wide frames, and the wider
  stance (thigh ry up to ±45 deg) shows the split for longer. This needs the rigger fix: drive skirt_f/skirt_b from the
  mean of both thighs and limit the skirt_l/skirt_r spread. After that, re-render t = 0.417 s (the wide stance).
- Narrow and wide stances are wider than the video on purpose (see 2). The video also pauses about 0.2 s in each
  stance; the clip is an even, continuous loop.
- strafe_r keeps the strafe_l spine lean (spine_01 ry -18, toward the sword side) and hips ry -2 (mirrored), as the
  review asked. It has no reference video of its own.
- At touchdown, the swing foot is still moving sideways in the last 1 cm above the floor (about 30 mm/frame in world
  space for 1-2 frames). After it lands it does not slide.
- The video's hands and shield are slightly bigger (Seedance redraw).

## Review fix 2 (animation fixer, 2026-11-22; owner away)
- strafe_l: eased lift keys k01 (0.0417) and k11 (0.4583): read-back + IK, the lifting foot keeps 1/3 of its slide and the knee moves 20% of the way; seam velocity jump 7.4 -> 4.8 cm/frame. strafe_r rebuilt with work/anim/hercules_strafe_fix/make_strafe_r.py (12 keys). See docs/notes/anim_hercules_review_fix.md for numbers; scripts in work/anim/hercules_review_fix/.
