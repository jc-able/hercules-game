# cyclops / video "idle" — animator notes (2026-11-22)

- idle | window t0 2.708 - t1 6.042 s (two video breaths, period 1.67 s measured from the silhouette: shoulder top
  +-5 px = 0.19 m, head 0.1 m, lower arms 0.13 m further out at the top of each breath) | 4 keys (k0_low at 0 and 1.667,
  k1_high_l 0.792, k3_high_r 2.5) + loop seam | IoU front/side per key: k0 0.865/0.936, k1 0.858/0.943, k0@1.667
  0.864/0.940, k3 0.864/0.945 (strip mean 0.902, all 8 strip frames 0.857-0.865 / 0.936-0.945) | length 3.333 s
  (80 frames @ 24 fps), loop | events: none |
  Not matched: the video's flexed arm/chest muscles are bulkier than the mesh (red rim on every arm, ~0.86 front ceiling;
  the rest pose already scores 0.86 front); video fists vs our open hands (rig has no finger bones). Authored, not
  traced: head yaw +-3 deg (prompt asks for a slight side-to-side turn, the video shows none measurable). Club arm is
  kept at its rest orientation (absolute) so the club only rises/falls with the shoulder, as in the video (club top
  moves ~5 px). Calibration: calib_iou 0.947/0.950; ak cycle period 1.667 s (IoU 0.993); reference usable.
