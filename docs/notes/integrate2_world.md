# World integration 2 (natural-animation pass, 2026-11-23)

The owner was at the Mac and could not be asked: every decision is mine and written here. Rendering only through
`tools/godot_bg/gdwin` with a throwaway HOME (`work/integrate2_world/home`); `builds/Hercules.app` untouched; no GLB or
clips-json edit (Pegasus has no events or move_speed to correct). Scratch: `work/integrate2_world/`.

## Code changes
### `game/scripts/world/home_base.gd`
1. **Mount: wings open at the hop, legs stay planted.** The new Pegasus idle folds the wings where the rider's legs go
   (48 of 48 idle frames hit a seated rider). Playing the whole `fly` clip at the hop would also tuck the legs while
   Pegasus still stands on the grass, so `_open_wings()` adds a small `WingOverlay` (SkeletonModifier3D, last on the
   Pegasus skeleton) that plays `fly` on the 12 `wing_*` bones only, eased in over 0.35 s (`MOUNT_WINGS_OPEN`).
   When the rider is seated, `_body_joins_beat()` plays the full `fly` from the overlay's clip time (wings continuous)
   with a 0.4 s blend (`MOUNT_FLY_BLEND`, the legs tuck) and frees the overlay after it. Stand-ins: plain `fly` at the hop.
2. **Hop 0.55 -> 0.9 s** (`MOUNT_HOP`), arc 0.7 -> 0.75 m. Seated at 0.93 s after interact (headless and rendered).
3. **Rider starts from the walking hero's pose.** The rider visual is created playing the hero's current clip at the
   same clip time and rate (same pose on screen), and on the next frame eases into `ride` over 0.6 s
   (`MOUNT_RIDE_BLEND`). Before, it faded from the rig REST pose over 0.25 s (a T-pose flash). No core change needed,
   so I did not ask for `CharacterVisual.copy_pose_from()`.
4. **Mount camera.** Hop: a small push in (1.2 m toward the saddle, 0.4 m up) turning to keep the hop and saddle in
   frame. Lift: the camera rides along with Pegasus and turns at most 45 deg toward behind it (the old full swing to
   behind crossed close to the wings within ~1 s, seen in the first movie); the sea scene's chase camera takes over
   after the fade.
5. **Landing settles into the idle.** Arriving home from the sea (`opts.from == "sea"`, not with `--world-probe`):
   Pegasus starts 4.5 m up and 7 m back along its facing in `glide`, eases down over 1.9 s (`LAND_TIME`), flares at
   45 % (fly, nose up to 14 deg, a wing flap), and at 78 % fades into `idle` over 0.7 s (legs reach down, wings fold).
   Event `pegasus_landed`. No mounting (and no bot advice) until it stands.
### `game/scripts/world/island_proxy.gd` — `sync_rider()`
The rider's `ride` clip was pulled onto the wing beat with `seek()` whenever it drifted > 1 frame: every glide -> fly
change jumped the rider's pose by up to half a ride cycle. It now runs the ride clip faster or slower (rate x0.5..x1.6,
catch-up in ~0.6 s, dead band 1/48 s) instead. Glide/idle rate unchanged (rider_speed_on_glide).

Not changed: pegasus_flight.gd (fly/glide already cross-fade 0.35 s at the skeleton from the pose on screen; banking
38 deg, pitch lerps: no pop seen), sea_world.gd, ending.gd.

## What I looked at (gdwin movies, 30 fps, 1600x900 frames; contact strips)
| movie | what | seen |
|---|---|---|
| `a_idle.avi` 8 s `--start=home --bot=idle` | hero idle + Pegasus idle (strips `a_hero_s.jpg`, `a_peg_s.jpg`) | Pegasus: head turns, tail flick, hind leg weight shift, wing shrug, hooves planted. Hero: subtle head turn, shield/sword sway (alive, quiet; the clip-fix agent is reworking it) |
| `b_mount.avi` (first try) | hop + lift | wings open, legs planted; camera pulled the pair smaller in the hop and swung close past the wings on the lift -> fixed (item 4) |
| `b2_mount.avi` 30 s `--start=home --bot=win` | hop, lift, flight to the cyclops ring, fight start | rider eases from the walk into ride; wings up before he lands; take-off from the side; flight alternates glide / fly beats with no pop |
| `c_land.avi` 11 s `--start=sea --defeated=all --ending-seen --bot=win` | free-flight landing at home | glides in from the east, flares, legs reach down, wings fold into the idle, stands |

## Regression (headless unless noted)
- `--start=home --harness --bot=win --quit-after=12`: mount 1.04, wings 12 bones, seated 0.90 s later, take_off + sea
  at 3.43. 0 SCRIPT ERROR.
- `--start=title --harness --bot=win --campaign --pad --speed=3`: result=victory (ending -> free-flight sea), 0 SCRIPT ERROR
  (run before and after the camera edit; both result=victory, campaign scenes title->home->sea->cyclops->sea->medusa->sea->hydra->ending->sea).
- `--start=sea --defeated=all --harness --bot=win --after-victory=3`: ending shown 0.40, free flight 3.58, lands home
  36.6, `pegasus_landed` 1.9 s after the home scene, the bot re-mounts, and this loops home <-> sea (no victory in free
  flight, so the run never ends by itself: stopped after ~60 s game time). 0 SCRIPT ERROR. Use `--quit-after`.
- Rendered runs above: 0 SCRIPT ERROR.

## Open / for others
- None of the clips need the animation fixer for my scenes. A dedicated "stand with wings raised" Pegasus clip would let
  the mount skip the overlay, but the overlay looks right.
- Not rendered: a human-driven banked turn in flight (the bot flies straight); banking code is unchanged.
