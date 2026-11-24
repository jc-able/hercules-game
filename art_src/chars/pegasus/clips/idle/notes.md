# pegasus / idle (video "idle")

| clip | window | keys | IoU per key (front/side) | length | events |
|---|---|---|---|---|---|
| idle | 2.5-9.5 s of ref.mp4 (clip t = video t - 2.5) | 21 keys + loop seam copy (17 pose files in poses_idle/) | neutral 0.94/0.94, tail_rise 0.93/0.88, tail_hi 0.92/0.89, tail_str 0.92/0.92, tail_fall 0.94/0.92, tail_down 0.94/0.92, breath 0.94/0.93, head_a 0.90/0.93, head_b 0.89/0.93, head_c 0.91/0.94, head_d 0.89/0.93, head_e 0.92/0.92, head_f 0.93/0.94, wing_mid 0.80/0.92, wing_max 0.73/0.90, wing_hold 0.72/0.91, wing_back 0.86/0.92; mean 0.90; strip mean 0.915 | 7.0 s loop, 24 fps | none |

- Content: tail flick (clip 0.25-1.9 s), head toss (2.6-4.5 s), wing ruffle/spread (5.2-6.9 s), neutral holds between with a tiny breath key.
  The seam 2.5 s vs 9.5 s scores 0.98/0.98 on the video masks; first and last key are the same pose file (k_neutral).
- Not used: 0-2.5 s (settle out of the sheet pose plus a foreleg paw at 0.75-2.0 s, front panel only); `ak cycle` found no real period (near-static video).
- Does not match: (1) the wing spread: Seedance draws the open wings bigger and higher than the mesh can reach and leaves the side
  panel unchanged, so front IoU tops out ~0.73 (fit from 0.45). wing_*_02 local deltas are ~24 deg (rig note says <= 20): no stretching
  seen in the fit render, but the lead may want to check the wing root at clip 5.9-6.3 s in the GLB. (2) the head toss in the video is mostly
  mane redraw: our head/neck keys (yaw + tilt, neck_03/head local_delta) are authored to the frames by eye; they gain nothing in IoU over rest.
  (3) tail hair is a broad flowing mass in the video; our 5-bone tail follows its centre line (tail_01 kept <= 45 deg, the rest bend on tail_02-05).
- Tool problem (worked around, see docs/notes/anim_pegasus_idle.md): animkit's silhouette counts the green sheet background as character,
  so all ak scoring was done through the scratch wrapper work/anim/pegasus_idle/akg.py (green key). Plain `tools/ak` gives meaningless IoU on this video.
- Final check video: work/anim/pegasus_idle/strip_idle.mp4.

- Fix (animation fixer, 2026-11-22): k_wing_max / k_wing_hold wing_*_02 capped at 20 deg (rig note), and the 4 deg moved to wing_*_01 (rz 2 + ry 2). IoU unchanged: 0.72/0.90 and 0.72/0.91. Rider pair check: 0 hits on 42 frames.
