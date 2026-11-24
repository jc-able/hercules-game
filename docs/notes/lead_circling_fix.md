# Lead fix: Hercules keeps his back to the camera while circling (2026-11-23, about 1:30-2:10 AM)

## What was wrong
Final check item 7 ("minor"): locked on, holding a side direction at full speed for more than 0.3 s turned the whole
body 95 degrees into a "circling run". Seen from the chase camera that is a full side profile for as long as the
player circles, which is the main move of every fight. Two more things showed up in the lead's look probe:

- Changing from right to left turned the body the short way round, through the camera side: for about 0.2 s Hercules
  showed his front (`rotate_toward` from -95 to +95 degrees takes the 170 degree path, not the 190 degree one).
- Holding forward + side (W+D on a keyboard) started as a run, dropped into the 0.3 s side-step at 1.8 m/s when the
  angle to the boss passed 45 degrees, then ran again.

The owner's look statement: the camera stays right behind Hercules. His first trailer was rejected for a side-on view.

## What changed
| File | Change |
|---|---|
| `game/scripts/visual/upper_twist.gd` (new) | A `SkeletonModifier3D`: after the clip is applied it turns the `spine*` bones (and `neck*`/`head*`) about the world vertical. The skeleton restores the clip pose every update, so nothing accumulates |
| `game/scripts/visual/character_visual.gd` | `set_upper_twist(angle, head_extra)`: makes the modifier on the first non-zero call; stand-ins and models without those bones ignore it |
| `game/scripts/player/player.gd` | Circling run: hips turn at most `CIRCLE_TURN_DEG` (85, was 95, so a change of direction passes through the back-to-camera side). The twist follows `-vis_yaw x CIRCLE_TWIST` while he runs locked on and eases to 0 in every other state. A full-speed forward run that swings to the side keeps running (no side-step first) |
| `game/scripts/data/tuning.gd` | `CIRCLE_TURN_DEG 85`, `CIRCLE_TWIST 0.55`, `CIRCLE_HEAD 0.25`, `CIRCLE_TWIST_DEG_S 500` |

Result at full side input: hips 85 degrees (the legs still run along the path: no skating), chest about 38 degrees
from the boss direction, head about 17 degrees. Only the picture changes: `facing`, the shield arc, speeds and
hit tests are untouched.

## How it was checked
- Look probe (windowed 1280x720, Cyclops, seed 11, the same script before and after): hold right 4 s, then left 4 s.
  Before: `vis_yaw` -91 to -95, then -265 (through the front). After: -85 / +85, twist 46.8 degrees.
  Frames: `docs/devlog/media/10_circling_fix/`.
- Transition probe (roll sideways and backward out of the run, strike, shield, stop, reverse, forward-right, back
  away): the twist never exceeds 46.8 degrees and returns to 0 in every other state; the forward-right run stays on
  the run clip.
- Regression: see the table in the devlog chapter 10 (three boss bots, the whole game with keyboard and with pad
  events, the exported app).

## Not done
A keyframed strafe-run clip (made the owner's way from a Seedance front + side video) would replace the procedural
twist. It was not made: the twist needs no new art and reads well from the chase camera.

## Also looked at after the fix (about 1:42-1:44 AM, no change made)
- The same held-input probe in the Medusa and Hydra fights: Hercules keeps his back to the camera while circling, both
  bosses stay in frame (the Hydra's fire sweep and Medusa's gaze decal read clearly from behind him).
- Free run on the home island (no lock-on), holding right / back / left for 3 s each: the camera recentres behind him
  (`CAM_RECENTER_SPEED` 75 deg/s after 1 s without camera input), but because movement is camera-relative he then runs in
  a circle around the camera and is seen from the side, and holding back runs him toward the camera. That is how
  third-person free cameras normally behave, so it was left as it is. The owner steers it with the mouse or right stick.
