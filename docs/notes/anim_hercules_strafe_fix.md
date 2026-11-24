# anim_hercules_strafe_fix notes (2026-11-22; the owner was away, so these decisions are noted for the lead)

Files are in `art_src/chars/hercules/clips/strafe/`: `action_strafe_l.json`, `action_strafe_r.json` (NEW), `keys_strafe_*.json`,
`poses_strafe_*/k00..k18.json`, `strip_strafe_*.jpg/.mp4`. Details are in that folder's `notes.md`.

## For the lead
- **Merge `action_strafe_r.json` as well.** It is NOT a plain `ak mirror`: the arms, spine and head are taken from
  strafe_l so the sword and shield stay correct. Do not regenerate it with `ak mirror --keys`. After any strafe_l
  change, run `cd work/anim/hercules_strafe_fix && python3 make_strafe_r.py` and re-bake.
- Once strafe_r is in the GLB, the fallback at `player.gd` lines 428-429 (strafe_r -> strafe_l) stops firing.
- **Speed (decision needed in game code; I cannot edit it).** The strafe clips now cover `stride_m` 0.6 m per 0.833 s
  cycle, or 0.72 m/s at speed_scale 1. They covered 0.27 m (0.275 m/s) before. Locked-on movement is 4.6 m/s
  (`Tuning.LOCK_SPEED`). My recommendation:
  1. For strafe_l and strafe_r, set `_anim.speed_scale = clamp(lateral_speed / 0.72, 1.0, 2.5)` (the foot then matches
     the ground up to 1.8 m/s);
  2. either cap the locked-on SIDEWAYS speed at about 1.8-2 m/s (forward and back can stay faster), or, above about
     2 m/s, blend to a side-run clip. That clip would need a new reference video, which costs Higgsfield credits.
  At 4.6 m/s with no cap, the feet still skate by about 2.5x.
- **Manifest.** `ak export` writes only length/loop/events. `keys_strafe_*.json` carry `stride_m` (0.6) and
  `natural_speed_mps` (0.72), which the game could read once animkit copies them into `<id>_clips.json`. Until then,
  hard-code 0.72 m/s for the strafe clips.

## For the rigger (rig_hercules)
- The driven skirt splits up the centre front in wide stances (thigh ry beyond about ±17 deg). The dark crotch triangle
  is visible in `strip_strafe_l.jpg` at 0.35-0.49 s. The new wider strafe (thigh ry up to ±45 deg) shows it for longer.
  Suggested fix (from the review): drive skirt_f/skirt_b from the mean of both thighs and limit how far skirt_l and
  skirt_r separate, or add weight across the centre of the hem. Then re-render strafe_l at t = 0.417 s.

## Tool notes
- In this rig, `rz` on a near-horizontal forearm is a yaw: it swings the bone and does not twist it. To turn a shield
  about the forearm, use aim form `{"front", "side", "twist"}`. A twist sweep (0-300 deg in 60 deg steps, then fit
  upper_arm_l) found the face-out pose in 8 renders.
- `ak strip --sheet sheet.png` (without `--video`) works for a clip that has no reference video of its own (strafe_r).
