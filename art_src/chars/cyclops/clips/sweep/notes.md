# cyclops / video "sweep" — animator notes (2026-11-22)

| clip | video window | keys | length | events | IoU (front/side) | file |
|---|---|---|---|---|---|---|
| sweep | 2.375-4.875 s (take 1; take 2 at 5.5-7.75 s is a near copy) | 17 (16 distinct poses; ready at both ends) | 2.5 s @ 24 fps, one-shot | impact 1.31 | traced keys mean 0.75; all 14 authored keys mean 0.66; strip all-frame mean 0.65 | action_sweep.json |

Per key (clip t / video t: IoU front/side):
k1_lift 0.375/2.75: 0.79/0.67 · k2_cock 0.625/3.0: 0.81/0.75 · k3_behind_neck 0.875/3.25: 0.76/0.70 ·
k4_drawn_back 1.125/3.5: 0.81/0.78 · k5_sweep_right 1.25/3.625: 0.78/0.77 · k6_sweep_left 1.375/3.75: 0.71/0.70 ·
k6b_follow 1.5 (absolute-space in-between): 0.58/0.66 · k7_wrap 1.625/4.0: 0.70/0.72 · k7b_wrap_mid 1.75 (IK, hand kept
out of the chest): 0.47/0.53 · k7c 1.8125 (IK) · k8_over_shoulder 1.875/4.25: 0.60/0.59 · k8b hold 2.0/4.375: 0.52/0.48 ·
k8c_unwind 2.125/4.5: 0.38/0.41 · k9_recover 2.25/4.625: 0.76/0.79 · k9b_settle 2.375/4.75: 0.61/0.76 · ready 0/2.5: 0.88/0.94.

Motion: ready (the rest T-pose with the club upright = the video's ready pose) -> whole body turns ~35-40 deg to its right,
knees out, club cocked over the right shoulder and laid behind the neck -> club drops behind and comes round low on the
right (drawn back, 3.5 s) -> linear (no ease) fast sweep right-to-left through the front (impact 1.31 = club straight in
front) -> body keeps turning to ~75 deg left, hunched, club wraps over the left shoulder -> unwinds over the head -> ready.
Root yaw is real body turn (root.rot); no travel (root drift removed by bake). Feet: left/right foot lifts <= 0.08 m except
k7_wrap (right foot 0.26 m up: the pivot step on the follow-through).

What does not match and why:
- Seedance's two panels disagree during the wind-up: the side panel shows the body turned ~70 deg (chest to the side
  camera) while the front panel shows ~30 deg. Yaw scans peak at -30 (front) vs -75 (side); I used -35/-40.
- The video's arm reaches 3-4 m from the shoulder at 3.5-3.75 s (club grip measured at x -3.6 m / y -3.5 m); the rig's
  club arm reaches 1.6 m (+1.1 m shoulder bone), so the club is right in direction but closer to the body there.
- 4.0-4.5 s (follow-through) the video draws the club end-on in one panel and side-on in the other; keys there score
  0.4-0.6. The right fist sits near the beard and the club handle grazes the left side of the neck for ~5 frames
  (clip 1.85-2.1 s): the right arm cannot reach over the left shoulder (same short-arm limit the slam animator reported).
- The video snaps back to the T-pose in 0.25 s (4.5 -> 4.75); I ended at 4.875 (one extra 1/8 s) and added a settle key.
- Fast big-yaw segments interpolated badly in local bone space (club swung through the torso); fixed with absolute-space
  slerp in-betweens (work/anim/cyclops_sweep/midpose.py) and IK keys (armik.py) checked with a club-clearance test
  (clubchk.py). The game may retime: SPEC wants a 0.6 s wind-up (here 1.125 s to drawn-back).
Tools in work/anim/cyclops_sweep/: mk2.py (world-direction + IK pose builder), measure_club.py (club line from frames),
scan.py/scan2.py (IoU yaw scans), midpose.py, armik.py, clubchk.py.

## Fix pass (anim fixer, 2026-11-22; owner away, decisions noted)
- sweep | 21 keys (+k4b 1.1667, k4c 1.2083, k5b_impact 1.2917, k8d 2.0833) | strip IoU 0.63/0.61 | 2.5 s | impact 1.31 (unchanged) | 1.125-1.375 re-keyed as a LOW backhand (hips ~0.4 m lower, spine +10 forward, right arm re-solved): club-head centre z 1.24-1.76 m, lowest vertex 0.25-0.82 m from 1.208 to 1.375, crossing straight ahead at ~1.31 (yaw -13 at 1.292, +7 at 1.333). The video swings at chest height: deliberate deviation for gameplay. Club clearance: k3 club moved back/up off the neck, k7_wrap re-solved to pass outside the left flank, k8b over the left shoulder, k8d keeps it left of/above the head: club_inside 0 from 1.5 to 2.5 s except <= 2 samples / 0.15 m near the fist.
