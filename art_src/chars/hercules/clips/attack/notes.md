# hercules / attack video: clip notes (animator, 2026-11-22; owner away, decisions noted)

Video: take 1 used (1.75-4.5 s); take 2 (6.0-8.5 s) is the same combo and later in the drift. Framing fitted per key in
`view_offset` (the video character walks ~0.6 m forward and back during the combo; the clips stay in place).
IoU = silhouette overlap front/side of each key pose against its aligned video frame (`ak pose`).

| clip | window (video s) | keys | IoU per key (front/side) | length | events | what does not match |
|---|---|---|---|---|---|---|
| attack_1 | 1.75-3.00 | 8 (5 traced + 1 hold + 2 grounded read-back in-betweens) | k0_ready 0.90/0.92, k1_wind 0.78/0.65, k2_mid 0.75/0.64, k3_ext 0.79/0.60, k4_end 0.68/0.57 (k1a_draw, k1b_slash = read back from the bake and re-grounded) | 1.25 s @24 fps | active_start 0.50, active_end 0.79 | see below |
| attack_2 | 3.00-4.50 | 10 (8 traced + 2 grounded read-backs) | k0_start 0.68/0.57, k1_over 0.74/0.65, k2_over_top 0.80/0.41, k3_chop 0.79/0.58, k4_low 0.73/0.59, k5_low2 0.72/0.58, k6_rise 0.79/0.58, k7_ready 0.84/0.80 (k5b_rise, k6b_settle = read-backs) | 1.50 s @24 fps | active_start 0.42, active_end 0.58 | see below |

Strip IoU mean (every frame): attack_1 0.676, attack_2 0.667. Feet within -1.5 / +0.8 cm of the floor over both clips.
Chain: `poses_attack_1/k4_end.json` == `poses_attack_2/k0_start.json` (identical file content), attack_2 ends on the ready pose (= rest stance of this video).

What does not match and why:
- Slash direction: the prompt asked for a right-to-left slash; the video does a BACKHAND (sword cocked at his LEFT shoulder,
  then swept out to his right). I matched the video.
- Side-panel IoU stays ~0.6: the video character steps ~0.6 m forward and twists his torso; the shield swings behind his back
  in the windup and the chop. Framing absorbs the travel; the remaining mismatch is mostly the shield outline and the
  far-side leg. `k2_over_top` side 0.41: at 3.417 s the video leans back with the shield behind him, ours keeps it in front.
- Lead leg: the video does not show clearly which foot steps forward; I chose the RIGHT foot forward (sword side), left
  leg back. IoU cannot tell left from right.
- The front foot lifts ~7 cm at 0.58 s of attack_1 (a stamp-step during the slash, like the video's short step).
- Lengths are the video's natural timing (1.25 s / 1.5 s); SPEC wants 0.55 / 0.65 s. The game stretches clip speed;
  or `ak retime keys_attack_1.json --scale 0.44` / `keys_attack_2.json --scale 0.433` before merging.
- Fingers of the sword hand are not curled (rig note says fingers_r can close on the grip); hand reads fine at game scale.
- Sword: blade is aimed per key (it sits 40 deg off the hand bone axis; solved with hand twist, see work/anim/hercules_attack/gen.py).

## Review fixes (animation fixer, 2026-11-22; owner away, decisions noted)
Scripts: `work/anim/hercules_attack_fix/` (fixgen.py = new key poses as 3D directions via gen.py, fix2.py = twists + slash legs,
blend.py = slerp in-betweens, plant.py = both feet down, arcs.py = world-space turn per key). Originals backed up in `orig/`.

| clip | keys now | changed keys, IoU front/side (video frame) | events | strip IoU mean |
|---|---|---|---|---|
| attack_1 | 9: k0_ready 0, k1a_draw .208 (read back from the new bake), k1_wind .375 + hold to .458, k1b_slash .542, k1c_release .583 (new, slerp + both feet planted), k2_mid .667 (was .625), k3_ext .875, k4_end 1.25 | k1_wind 0.77/0.65 (2.125; was 0.78/0.58 in review), k1b_slash 0.72/0.54 (2.292; was 0.74/0.40), k1c_release 0.62/0.64 (2.333) | active_start 0.458, active_end 0.708 | 0.687 (was 0.676) |
| attack_2 | 12: k0_start 0, k1_over .25, k1c_cock .333 (new), k2_over_top .417, k2b_down .458 (new), k3_chop .5, k4_low .625, k5_low2 .75, k5b_rise .875, k6_rise 1.0, k6b_settle 1.25, k7_ready 1.5 | k1_over 0.68/0.61 (3.167), k1c_cock 0.74/0.61 (3.333), k2_over_top 0.79/0.43 (3.417; was 0.80/0.41), k2b_down 0.70/0.43 (3.458) | active_start 0.417, active_end 0.625 | 0.662 (was 0.667) |

What changed:
- attack_1 wind-up: spine_01 rx 3 / ry 4 / rz 25 (was -39/34/20), neck rz 8 + head 0 listed so the face stays forward; sword
  arm across the chest at shoulder height (upper arm front -42 / side -61, forearm front -87 / side -81), blade up and a little back;
  shield arm hangs slightly back (belt height, behind the hip in the side view, as in the video).
- attack_1 release: hold released at 0.458, k1b_slash at 0.542 (arm reaching straight forward, blade back over the forearm, as
  at 2.292 s), new k1c_release at 0.583 (sword still cocked as at 2.333 s, legs 55% toward the lunge, right foot planted
  right_z 0.005), k2_mid moved to 0.667. Root z per key: -0.011 (.458) -0.012 (.542) -0.054 (.583) -0.106 (.667); was one 11.5 cm
  frame. The blade sweep back->front happens 0.583-0.667 (2 frames, hand_r 148 deg world) = the video's 2.333->2.417 timing;
  the read-back at 0.625 shows the blade passing over the top, no flip.
- attack_2 wind-up order now matches the video: k1_over blade horizontal toward his left (front panel screen right) ->
  k1c_cock blade back and slightly down behind the head -> k2_over_top arm up and forward, blade up/back -> k2b_down arm forward
  and up on his RIGHT side, blade up -> k3_chop. World blade turn per segment 71 / 48 / 80 / 86 deg (all < 90).
- k2b_down: shield arm halfway between over_top and chop (forearm_l 81 + 81 deg over 2 frames instead of 162 in one segment).
- Arm twists of all new keys: forearm_r twist chosen so the wrist turns least (hand_r is absolute), upper_arm_r so the elbow
  turns least (e.g. k1c_cock upper arm 172 -> 57 deg off its forearm). No forearm candy-wrap in the read-backs.
- Ground: keys planted (feet within 0.0-1.6 cm); the bake's in-betweens dip at most 1.5 cm (0.5 s of attack_1).

Still not right / decided:
- Shield-behind-the-back during the chop (review item 8, optional): tried on over_top..low2; front IoU fell from ~0.73 to ~0.57
  and side did not rise (the gen.py shield "prop" axis is an in-plane axis, so the facing was hard to aim). Reverted: the shield
  stays in front (fine for the camera behind the player). Side IoU 0.43 at 3.417-3.458 is that shield.
- attack_1 k1c_release front IoU 0.62: the shield turns edge-on for a frame while it travels from the hip to the front.
- attack_1 ends mid-raise (chain to attack_2): see `docs/notes/anim_hercules_attack_fix.md` (0.15-0.2 s blend to idle).
- Lengths still the natural 1.25 / 1.5 s. Retime advice for attack_2: scale the strike (keys <= 0.75) and the recovery (keys
  after 0.75) separately, e.g. 0.55 and 0.32 -> 0.41 + 0.24 = 0.65 s, active window 0.23-0.34 s (SPEC 0.22-0.38).
  attack_1 x0.44 -> 0.55 s, active 0.20-0.31 s (SPEC 0.18-0.32).

## Review fix 2 (animation fixer, 2026-11-22; owner away)
- attack_1: 1.25 s, 20 keys; k0 = idle k0 (was the rest A-pose); k1a_draw legs re-solved (right foot steps into the lunge); swing 0.458-0.667 with 4 read-back keys (k1d_swing1-4); chain pose k4_end at 0.917 (= game 0.40 s) then steps back to idle k0 (k5_recmid, grounded read-backs g_*.json); active 0.458-0.708, chain 0.917.
- attack_2: 0.833 s (was 1.5), 17 keys; chop 0.25-0.375 over 3 frames (k2c_chop1, k2d_chop2, k3b_follow read-backs); k6b_settle steps back; k7_ready = idle k0; active 0.25-0.458. See docs/notes/anim_hercules_review_fix.md for numbers; scripts in work/anim/hercules_review_fix/.

animfix_hercules 2026-11-23: re-based again on natural_pose.json v2 (work/animfix_hercules/build.py + edits.py; see the 'animfix' entry in keys_*.json and docs/notes/assemble2_hercules.md). Old files in art_src/chars/hercules/backup_animfix_20261123/clips/attack/.


## clipfix2_hercules 2026-11-23
attack_1 recovery 0.917-1.25: sword-arm chain (upper_arm_r, forearm_r, hand_r, fingers_r locals) re-timed by arc length (profile 10,26,36,40,37,27,14,4), hand_r world turn in the last two 24 fps frames 22.6 / 9.1 -> 12.3 / 3.5 deg. Events, the chain pose at 0.917 and every other bone unchanged. strip_attack_1_recovery.jpg = new recovery.
