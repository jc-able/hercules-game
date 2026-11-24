# cyclops / hurt — animator notes (2026-11-22)

- hurt | window 1.25-3.50 s of ref.mp4 (first take; the second take 6.0-8.0 s is the same move) | 7 keys (6 poses, rest reused at the end) | length 2.25 s @ 24 fps, no loop | events: none (SPEC §8 has none for hurt) |
  IoU front/side per key: k0_rest 0.76/0.83 (t 0.000, video 1.250), k1_jerk 0.82/0.74 (t 0.083, video 1.333), k2_peak 0.85/0.73 (t 0.75, video 2.0),
  k3_hold 0.86/0.74 (t 1.25, video 2.5), k4_rec1 0.85/0.74 (t 1.5, video 2.75), k5_rec2 0.87/0.78 (t 1.75, video 3.0), k0_rest again at t 2.25 (video 3.5).
  Mean key IoU 0.796; per-frame strip IoU over the whole clip 0.79 mean (front 0.79-0.87, side 0.71-0.82 after the snap).
- Motion: the hit snaps the club arm back in 2 video frames (key 0 -> key 1 linear), the club tilts ~35-40 deg back
  (twist of upper_arm_u_r / forearm_u_r / hand_u_r, hand rx -34), the right upper arm drops ~25 deg with the elbow bent,
  head thrown back (head rx -58..-68, slight roll ry 14-20 that the fit asked for in every key), torso leans back,
  knees soften, lower arm pair lifts ~13 deg; holds to 2.5 s in the video, then recovers to the rest pose.
- Starts and ends on the REST pose (= the sheet / first video frame). The idle clip was not finished when this was made:
  if idle's first pose is not the rest pose, the game should blend into/out of hurt (it is a one-shot, ~0.1 s blend is enough).
- Does not match: side panel stays ~0.73 at the peak. Seedance redraws the torso deeper with the chest pushed forward and
  the head tipped back on an upright trunk; our rig gets the silhouette best by leaning the upper spine back (spine_03 -30).
  An upright-trunk variant (k2_peak_up in work/) scored lower (0.79/0.71) and looked worse, so the fitted lean was kept.
  Video frame 1.167 s is a one-frame flinch/glitch (club jumps forward) before the hit: skipped.
- Timing is the video's natural timing (2.25 s); the game may retime it (ak retime) if the hurt state is shorter.

## Fix pass (anim fixer, 2026-11-22; owner away, decisions noted)
- hurt | RE-AUTHORED (no reference: the old ref.mp4 shows a standing hurt, wrong context) | 4 keys: ../slam/poses_stuck/k00_stuck.json at 0 (linear) -> s1_flinch 0.083 -> s2_flinch_hold 0.333 -> k00_stuck 0.667 | 0.667 s, no loop, no events | hurt only plays while he is stuck (BossBase.take_weak_hit), so it is a flinch FROM the stuck pose: head back 25, neck 10, spine_03 8, left upper hand lets go and jerks out/up, lower arms jerk 10 deg; right arm re-solved per key so hand_u_r and the club stay put (club head moves <= 0.03 m, forearm_u_r 2.15-2.23 m). The standing keys are kept in poses_hurt/old_standing/. Seedance reference if wanted: from a sheet of the STUCK pose, "flinches, head snaps back, then settles back to the same pose".
