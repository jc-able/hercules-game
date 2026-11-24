# medusa / gaze video — animator notes (2026-11-22)

gaze | window 5.75-10.0 s (second take; the first take 1.0-5.5 s is the same move but slower) | 9 keys (8 poses, k0 reused as the last key) at clip t 0, 0.5, 1.0, 1.875, 2.0, 2.5, 3.25, 3.75, 4.25 | IoU per key (mean of front/side): k0 0.86, k1 0.85, k2 0.84, k3 0.75, k4 0.78, k5 0.76, k6 0.76, k7 0.88, k0(end) 0.86, mean 0.82; strip mean 0.80 over 65 frames (min 0.69 two frames after the thrust) | length 4.25 s, 24 fps, no loop, starts and ends on the same idle pose (k0) | events fire_start 2.0 (the thrust lands), fire_end 3.25 (end of the held stare).

Keys: k0 idle; k1 arms rising, hands in front of the chest; k2 full wind-up (head 46 deg back, arms overhead, snakes up); k3 end of the wind-up hold (linear into the thrust, 3 frames); k4 thrust (arms flung level, column leans 14 deg, spine 18-28 deg); k5/k6 held stare (column lean 16 deg, upper spine 58 deg, arms out and down, head 15-17 deg down); k7 relax.

How the lean is done: the rig's lean recipe (rig.json lean_recipe) without re-parenting: the root bone turns forward by the lean angle,
root.loc puts the tail_03 head back on its rest spot, tail_03 is absolute 0 so tail_03..14 stay flat on the floor (checked with ak solve: tail_03..14 unchanged, ground 0.000).

What does not match and why:
- Seedance drifts the side panel backwards during the stare (the tail tip crosses the divider; fit puts view_offset y 0.45-0.59 m on k4-k6 versus 0 on k0). This is framing only (view_offset, not baked): the clip stays in place.
- k5/k6 side IoU ~0.72: in the side panel the video draws the near arm reaching forward at shoulder height and the far arm behind the back, while the front panel shows both arms out to the sides; we follow the front panel (arms out and down, ~25 deg forward).
- Snake hair: 6 single bones, fitted on k2/k5 (rearing up in the wind-up), small per-snake offsets on k3/k6 so they do not move in unison. No per-snake second bone, so no writhing along a snake.
- The tail lies still in the video and stays still here (no secondary tail motion authored).
- Game timing (SPEC 3.2: windup 1.2 s, beam 1.0 s): the clip's wind-up is 2.0 s and the stare 1.25 s; the game re-times.

Files: keys_gaze.json, poses_gaze/k0..k7.json, action_gaze.json, strip_gaze.jpg. Scratch + full-frame mp4 strip: work/anim/medusa_gaze/ (strip_gaze.mp4, gen.py, setlean.py, fit logs).

- animfix2: arm life in the held stare (k5, new k5b 2.75 s, k5c 3.0 s, k6): right arm higher, elbows out of phase, right hand claw; head/eyes/events unchanged (animfix2 2026-11-23; details in docs/notes/assemble2_medusa.md "Animation fix pass")
