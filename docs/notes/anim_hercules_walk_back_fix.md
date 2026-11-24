# anim fixer: hercules / walk_back (2026-11-22)

## Request for core (player.gd / character_visual.gd)
walk_back is now a real backpedal: **stride 0.60 m per 0.5 s cycle = 1.2 m/s at playback speed 1.0**.
Locked-on back-away moves at 4.6 m/s (SPEC §2), which would need 3.8x playback and look frantic. Pick one (owner decides):
- play walk_back at `speed_scale = back_speed / 1.2` (clamp ~0.6-2.0), and/or
- lower the back-away speed to ~2.5 m/s (2.1x playback). Feet then still skate a little at full speed, but read as steps.

## Optional for the lead (credits)
Re-prompt Seedance for walk_back with "each foot reaches 30 cm behind the body" if a traced stride is wanted later;
the current clip's stride is authored (IK), not traced, because the video marches in place.
