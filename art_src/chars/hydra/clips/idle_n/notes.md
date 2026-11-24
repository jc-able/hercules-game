# hydra / idle_n video: animator notes (anim2, 2026-11-23)

| clip | video window | keys | IoU per key (front/side -> mean) | length | events | loop |
|---|---|---|---|---|---|---|
| idle | 0.000-7.000 s (one `ak cycle` period from 1.0: 6.958 s, IoU 0.992; the cycle starts on the natural stance at 0.0 and returns to it at 7.0), compressed x0.857 to 6.0 s | 12 (every 0.5 s; video time = t x 7/6) | k00 0.935/0.966 (0.950) · k01 0.887/0.941 (0.914) · k02 0.834/0.931 (0.882) · k03 0.817/0.921 (0.869) · k04 0.834/0.899 (0.866) · k05 0.838/0.892 (0.865) · k06 0.817/0.894 (0.856) · k07 0.858/0.890 (0.874) · k08 0.864/0.916 (0.890) · k09 0.840/0.925 (0.882) · k10 0.849/0.917 (0.882) · k11 0.876/0.926 (0.901); mean 0.886. Rest pose scores 0.63-0.64 front / 0.68-0.74 side | 6.0 s @24 fps (old 3.0 s) | none (old clip had none) | yes |

Files: `keys_idle.json`, `poses_idle/k00-k11.json`, `action_idle.json`, `strip_idle.jpg` (shipped 6.0 s action against the video at
video speed, strip mean 0.885: rows drift by up to 1 s because the clip is 6/7 of the video cycle). Phase-aligned check:
`work/anim2/hydra_idle_n/strip_idle_videotimed.jpg` (same poses retimed x7/6, 8 frames, mean 0.896). Generator:
`python3 work/anim2/hydra_idle_n/tools/gen.py work/anim2/hydra_idle_n/p_final_out.json art_src/chars/hydra/clips/idle_n/poses_idle`
(then move `poses_idle/keys.json` to `keys_idle.json`).

## What the video shows (masks, 38.8 px/m)
- Layout fine: calib IoU front 0.927 / side 0.970, views in sync. The side panel is narrower than the sheet: the tail tip is cut off.
- One 7 s cycle that starts and ends on the natural stance. About half of the visible "breath" is the CAMERA: Seedance zooms
  in ~2 % (view_scale 1.02 at 2.3-3.5 s) and back. Under it: the side heads rise and spread at 1.5-3.5 s (inhale), sink a
  little at 5-6.5 s (body ~0.1 m lower at 5.8 s), the head mass drifts to the character's right (2 s) then left (3.5 s).
- The prompt's independent weaving of the eight heads and the centre head's look left/right are barely visible in the video.

## Decisions (owner at the Mac, no questions)
- Length 6.0 s (video cycle 6.96 s, brief: idle loop 3-6 s). Breath = the video's lift cycle (one per loop) plus two
  smaller weave beats per loop; no event depends on the length (old 3.0 s). The game reads loop length from the manifest.
- First = last key = `natural_pose.json` exactly (every delta is zero at t = 0; checked: max diff 0.0 deg). Every key is the
  full stance merged with deltas, so no bone falls back to the rest pose.
- TRACED (fitted on the video with a batched coordinate search over per-neck bend_up / bend_side / head pitch, `tools/nfit.py`,
  framing fitted per key on the stance and interpolated, render only): per-neck rise/spread at the peak (video 2.33 s, IoU
  0.868 -> 0.903) and the sink at the trough (5.83 s, 0.924 -> 0.929), driven by the measured lift curve with a 0.05-0.45 s
  delay per neck so they never move in unison. Traced-only clip: mean 0.914 vs 0.907 for the stance held still.
- AUTHORED on top (the owner's stiffness complaint; costs 0.028 mean IoU, 0.914 -> 0.886): each side neck weaves sideways and
  up/down on its own rhythm (1-3 cycles per loop, phase lag 0.35 rad per link toward the head), outer heads 3 and 7 turn to
  look sideways (+-13 deg), the others +-5-7 deg; low heads 1, 2, 8 (and 6) sniff down and lift (5-11 deg nose-down bumps);
  centre head looks left then right (+-16 deg yaw, neck following 35 %), small nod, jaw eases open 8 -> 14 deg twice per loop
  (limit 20); tail travelling wave (1 + 2 cycles, up to ~6 deg/link at the tip) plus the traced lift; weight drift = spine S-bend
  (spine_01 +-3.5 deg, spine_02 opposite: the chest slides ~0.1 m sideways without turning) with the front legs leaning
  0.38 deg per deg (ry) so the front feet stay put.
- Feet: planted, foot joints move <= 8 mm (solve at k03/k06/k09), lowest vertex 0.000, right side <= 0.016 m.

## What does not match and why
- The video's 2 % zoom is framing (view_scale per key), not baked. The 0.1 m body sink at 5.8 s is not keyed (it needs leg
  IK on four planted legs for 10 cm); the necks' traced sink carries that beat instead.
- Hind legs (leg_b*) and feet stay still (planted); front legs move ~1.3 deg (weight drift compensation). spine_02/03 and
  the base links of necks 5, 6, 7, neck_c and tail_02 turn 0.4-2.9 deg (< the 3 deg "moving" threshold of clip_motion.py);
  every neck's upper links and every head turn >= 3 deg, so no limb group is frozen.
- Side IoU tops out ~0.92-0.97 for the cut-off tail (constant across keys).
