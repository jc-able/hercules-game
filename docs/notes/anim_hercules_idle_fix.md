# anim fixer: hercules / idle (2026-11-22)

## Request for the rigger (Hercules skirt, review finding on the idle)
The idle stance has thigh_l rx -56 (forward) and thigh_r rx +48 (back) in every frame. The driven skirt follows them fully:
side view: skirt_b juts out horizontally as a ragged point behind the back thigh, skirt_f lifts with the forward thigh;
front view: jagged hem by the left knee. The reference shows a clean hem at mid-thigh.
- Clamp or scale the skirt_f / skirt_b pitch response in `art_src/chars/hercules/scripts/skirt_drivers.py`
  (e.g. cap at ~25-30 deg of thigh swing, or a soft falloff above ~20 deg).
- Fix the jagged hem weights near thigh_l.
- Then the lead re-bakes with `ak merge`; the idle keys need no change. (Other clips with wide stances benefit too.)

## Note for the lead
- The idle's side IoU is now 0.72-0.73 (was 0.745) because the torso is upright, as the review asked. The remaining gap is
  where the pelvis sits between the feet (the video's is ~8-10 cm further back). A leg re-pose could recover it later.
