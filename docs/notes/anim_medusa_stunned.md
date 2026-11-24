# anim_medusa_stunned (2026-11-22)
- Clips stun_start / stunned / rise in art_src/chars/medusa/clips/stunned/ (action_*.json, keys_*.json, poses_*/, strips, notes.md).
- Baked with --keep-root-motion (exact chaining; drift only 0.1 m). Merge as is.
- animkit request: a `lean` helper (pivot bone + angle -> pelvis rot + root arc + counter-rotation), and fit should skip ry
  on a bone chain or regularise it (it adds +-24 deg zig-zags along the spine to chase hair).
- stun_start/rise start/end on the rest A-pose, not on the idle clip's k0 (idle was not finished when this ran).
