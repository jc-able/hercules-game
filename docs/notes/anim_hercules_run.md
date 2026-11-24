# anim_hercules_run notes (2026-11-22)

- REQUEST (rig_hercules / core): during the run's high knee (thigh pitch about -65 deg), the driven skirt opens a vertical
  slit at the centre front (front view) and `skirt_f` pokes out as a stiff pointed flap (side view). See
  art_src/chars/hercules/clips/run/strip_run.jpg at 0.119 s and 0.595 s. A lower `skirt_f` factor (0.85 now), or
  `skirt_l/skirt_r` following pitch a little, would probably close it. I did not change anything (driven bones are off limits).
- Tool tip: `ak fit` refuses aim-form bones. To convert, bake a 2-key keys file and read each key back with
  `ak pose --from-action <action> --t <t> --save-pose`: the result uses rx/ry/rz (bones that sit at rest relative to their
  parent are left out, and root.ground is dropped, so add it back).
