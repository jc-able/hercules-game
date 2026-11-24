# medusa / stunned video -> stun_start, stunned, rise (animator, 2026-11-22)

Reference: calib_iou front 0.929 / side 0.952 (usable; static camera). Ceiling note: Seedance redraws the floor tail
(swung to her right and visibly shorter in the side panel from ~0.75 s on) and collapses her body almost straight down
(about 3 m of tail "disappear" in the side view), so even the rest pose scores only 0.76 against the 0.75 s frame.
All clips baked with `--keep-root-motion` (lead: keep it; the root drift is only 0.1 m but removing it would break the
exact pose chaining stun_start -> stunned -> rise). fps 24. No SPEC events for these clips.

| clip | window (video t) | keys | IoU per key (mean of front/side) | length | events | loop |
|---|---|---|---|---|---|---|
| stun_start | 0.75-2.375 (clip t = t-0.75) | 5: rest 0.76, cover 0.66, recoil 0.67, fall 0.59, slump 0.54 | strip mean 0.63 | 1.625 s | none | no |
| stunned | 2.75-7.0 hold (strip vs 3.5-6.5) | 2: slump 0.54, breath 0.60 | strip mean 0.61 | 3.0 s | none | yes |
| rise | 6.5-9.0 (clip t = t-6.5) | 6: slump 0.54, push 0.56, hunch 0.54, lift 0.57, up 0.53, rest 0.71 | strip mean 0.57 | 2.5 s | none | no |

Chaining: stun_start ends on `poses_stunned/k0_slump.json`, stunned loops on it, rise starts from it (same file).
stun_start starts and rise ends on the rest pose (`poses_stun_start/k0_rest.json` = the sheet A-pose). If the idle clip's
first pose differs from rest, re-point those two keys at the idle k0 and re-bake.

How the collapse is built (rig.json lean recipe, pivot moved down to the tail_04 head (0,-0.69,0.82) so she gets low enough):
pelvis rx = lean, tail_04 absolute rx 0 (floor tail stays flat), root.loc on the arc about the pivot, plus a `back` slide
of the whole body along +Y (fall 0.9 m, slump 2.4 m, rise 1.3/0.4/0.15/0 m) so the torso lands where the video puts it
instead of 2.5 m in front. Generator: `work/anim/medusa_stunned/gen.py`.

Does not match / authored:
- Floor tail: the video swings it to her right and curls the tip up; authored as a 25-60 deg sideways swing spread over
  tail_05-07 plus a tip curl in the recoil. Because of the `back` slide the floor tail slides ~2.4 m back during the
  collapse and forward again during the rise (the video hides the same length change by redrawing).
- Stunned: the video barely moves for 3.5 s; the loop is authored breathing (shoulders/head lift 6-10 deg, head roll,
  tail tip twitch, snake phases).
- Snake hair: authored secondary motion (local_delta, different amount/phase per snake), not traced.
- Recoil (1.375-1.75 s) leans back less than the video; slump hands reach a little less far forward than the video.
- Fit-only values were cleaned: the trunk ry zig-zags (+-24 deg) the fitter added to chase hair were dropped.


## Fixer pass (2026-11-22, owner away)
Rebuilt with the rig.json lean recipe AS WRITTEN (generator: `work/animfix_medusa/gen_stun.py` + `stunlib.py`): pivot = tail_03
head (0, -0.9145, 1.622), pelvis rx = lean, tail_03 absolute rx 0, exact root.loc on the arc, NO `back` slide and no root.ground
on the lean keys. tail_03..14 stay planted in all three clips (tail_05 moves <= 1.4 cm, floor-tail lowest vertex -0.006..+0.004).
Generated in-between keys (`g*_t*.json`) keep the pivot on the arc wherever the lean changes > 13 deg between anchors.
- slump (k0_slump, shared end/loop/start): lean 100, neck bone (0, -4.45, 1.04) = 4.45 m forward (Godot probe: neck 4.56 m fwd,
  0.98 m up; head 4.97 m fwd), head_min_z +0.018, hands -0.009, tail on the floor. stunned loop: neck 1.04-1.07 m, head lifts 0.15 m.
- stun_start: k0 rest 0, k1 cover 0.25, k2 recoil 0.875, k3_fall 1.125 (lean 25), then ONE ease-in fall through the mid pose to the
  slump at 1.625 (keys every 2 frames): head 4.33 (1.333) -> 3.35 (1.417) -> 1.89 (1.5) -> 0.36 (1.583) -> 0.02 m; lowest vertex
  -0.009..+0.003 on every frame (was +0.325 float / -0.11 dip).
- rise: press keys 0.25/0.375, push at 0.5 s (hands planted, head 0.55 m), hunch 1.0, lift 1.5, up 2.0, rest 2.5. lowest vertex
  >= -0.027 (hands, 0.125 s). Head never below the floor.
- Side IoU drops to ~0.3 in the slumped part (Seedance collapses her in place; the game needs the head 4.6 m forward): accepted.
- Strip means (front/side): stun_start 0.66/0.50, stunned 0.54/0.32, rise 0.57/0.40.

- animfix2: stunned neck held (root fixed at the slump height, spine_02/03 counter the breath; neck socket range 0.014 m); stun_start/rise left arm 0.1 s behind + elbow/wrist offset (mirror symmetry broken); rise grounded key kf1_ground at 0.125 s (animfix2 2026-11-23; details in docs/notes/assemble2_medusa.md "Animation fix pass")
