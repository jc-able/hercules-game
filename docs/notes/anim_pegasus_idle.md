# anim_pegasus_idle (animator, 2026-11-22) — owner away, decisions noted here

## Tool bug for the lead / animkit owner (not fixed: tools/ is not mine)
`tools/animkit/akimg.py::silhouette` marks any pixel with chroma > 0.10 as character. The pegasus sheets and Seedance videos use the
green background (160,221,182) -> chroma 0.24, so the whole background becomes "character": calibration falls back to the resolution
ratio and every IoU is ~0.95 for any pose (rest pose vs the wide-wing frame scored 0.94). The fly and glide animators hit the same bug and
wrote their own wrappers. I used a copy of the fly animator's wrapper (`work/anim/pegasus_idle/akg.py`: green-key silhouette, then the
normal ak main). Suggested fix: in silhouette(), estimate the panel background colour from the border and treat pixels close to it as
background before the chroma test (or read cam.json `bg`/`bg_srgb8`). After the fix, calibration of this video gives iou 0.95/0.96.

## Decisions
- Idle = one 7.0 s loop from video 2.5-9.5 s (tail flick, head toss, wing ruffle), not a 2-4 s cycle: the video has no short cycle and
  the three actions read as natural idle variety. The game can slow or speed it.
- Wing spread uses wing_*_01 rz/ry/rx + wing_*_02 local ~24 deg (slightly over the rig note's 20 deg) for the best front match.
