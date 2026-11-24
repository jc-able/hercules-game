# anim_pegasus_fly (animator, 2026-11-22)

Owner away: decisions noted here.

## Request for the animkit owner (tools/animkit/akimg.py, not edited by me)
`akimg.silhouette` marks every pixel with chroma > 0.10 as character. The pegasus sheets/videos use a green background
(sRGB 160,221,182, chroma 0.24), so the whole panel becomes "character": `ak frames` calibration fell back to the
resolution ratio (scale 1.546 instead of 0.812, calib_iou 0.66/0.77 with the warning "wrong sheet"), aligned frames were
~1.9x too big, and pose/fit/strip IoU would score any pose alike. This affects every pegasus clip (idle, fly, glide) and any
character rendered with `--bg`.
Workaround used: `work/anim/pegasus_fly/akg` = tools/ak with `akimg.silhouette` replaced by a green key
(fg = G - max(R,B) < 0.5 x the panel's border greenness, or max |rgb - border bg| > 0.30; falls back to the original when
the panel border is not green). With it: calib_iou 0.938/0.937, cycle self-IoU 0.986. Suggest folding this into
`silhouette` (key on cam.json `bg_srgb8` / the panel border colour when it is saturated).
Also: Seedance zoomed this video ~1.9x versus the sheet (character fills 72% of the frame height vs 39% in the sheet), and
it changed the panel split from 790/490 to 50/50; calibration handles both once the silhouette is right.

## Decisions
- fly window 1.000-2.042 s (first clean beat after the settle; every later beat matches it, period 1.0417 s).
- Wing poses symmetric (fits came out asymmetric because the side view cannot separate the wings; I mirrored the better side
  or averaged when close). wing_*_02 curls as local_delta, clamped to 20 deg (rig notes).
- Rejected IoU-higher downstroke fits that hooked the wing tips outward (unnatural); kept a straighter hanging wing.
