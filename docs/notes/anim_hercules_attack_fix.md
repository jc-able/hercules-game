# Animation fixer: hercules attack_1 / attack_2 (2026-11-22)

Fixed the review findings in `art_src/chars/hercules/clips/attack/` (details in its notes.md). For other modules:

## For core / game (Player attack playback)
- attack_1 ends on the raised wind-up of attack_2 (sword up and back, crouched, root z -0.11) so the combo chains seamlessly.
  When no second press comes, blend attack_1's end to idle over 0.15-0.2 s (AnimationPlayer cross-fade). If that still
  reads as an unfinished swing in play, ask for an `attack_1` recovery variant ending on k3_ext and returning to ready.
- New events: attack_1 active 0.458-0.708 of 1.25 s; attack_2 active 0.417-0.625 of 1.5 s.

## For the lead (retime before merge)
- attack_1: `ak retime --scale 0.44` -> 0.55 s, active 0.20-0.31 s.
- attack_2: do not retime uniformly (0.433 leaves a 90 ms window). Scale keys <= 0.75 by ~0.55 and the recovery keys after 0.75
  by ~0.32 (needs a split retime: `ak retime` has one scale; edit the key times by hand or add a `--after/--scale2` option).
  Result 0.65 s, active ~0.23-0.34 s.
