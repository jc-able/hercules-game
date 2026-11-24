# anim2_hercules_run_n (2026-11-23)
- REQUEST (lead / export): the new `run` (art_src/chars/hercules/clips/run_n/action_run.json) is 0.667 s (was 0.833 s) at 30 fps
  and its planted foot moves at 4.59 m/s at clip speed 1: set `move_speed` 4.59 in hercules_clips.json (was 3.64). With
  speed_scale = ground_speed / move_speed the feet do not skate; at RUN_SPEED 6.0 the scale is 1.31.
  `suggested_speed_scale` 1.3 / the old speed_note are obsolete.
- DECISION (owner not asked): legs keep the authored running stride (retimed x0.8), not the video's treadmill jog; the
  upper body follows run_n. Details in art_src/chars/hercules/clips/run_n/notes.md.
