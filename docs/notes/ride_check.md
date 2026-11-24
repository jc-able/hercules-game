# Ride sheet independent check (ride_check agent, 2026-11-22)

The owner was away, so this agent made every decision below and notes it here. Scratch files are in `work/ride_check/` (check_ride.py, diag.py,
render_views.py, check.json, diag.json, views.png, views2.png, orig/ = the builder's sheet + cam before the fix).
No changes to hercules.blend, pegasus.blend or ride.blend.

## Fixed: framing envelope (mechanical)
- Wing length, measured on the blend: 1.81 m from the `wing_*_01` head (x +-0.24, y -0.38, z 1.92) to the farthest wing vertex.
  A fully stretched horizontal wing reaches |x| 2.054 m. The builder's frame (`--env 2.09,...`) had a front half-width of 2.088 m:
  3.4 cm margin (5 px).
- Re-rendered `sheet_std.png` + `cam_std.json` with `--env 2.25,2.25,2.0,3.76`: 146.3 px/m (was 151.8), front_w 658,
  side_w 622. New margins for the worst case (a wing straight out, up or down from its root): side 0.20 m, top 0.79 m, bottom 0.50 m.
  The side panel is unchanged in metres (y -2.00..2.25; muzzle -1.79, tail 2.10).
- The rebuild line in `docs/notes/ride.md` still says `--env 2.09,2.25,2.0,3.76`. Use 2.25,2.25,2.0,3.76.

## Verified OK
- ride.json vs blend: the formula `saddle_global @ T(loc) @ R(rot)` matches hercules_rig to 3e-5. The armature-axes form matches too.
  Fresh copy: both characters appended from their own blends, ride.json poses applied with ak Rig, rider_offset applied.
  Every evaluated vertex matches ride.blend within 0.05 mm (Pegasus 0.0). The hips sit at (0, 0.20, 0.247) from the saddle head, as reported.
- Seat: the lowest seat-skin vertex is 0.0 cm from the back (no sinking, no floating). Shins sit at x +-0.47 and the barrel is +-0.40,
  so the legs go around the flanks. Feet hang below the barrel.
- Sword: 0 triangle hits with the horse or the wings. Its only hits on Hercules are hand_r/fingers_r (the grip).
- Wings: 0 hits from the legs. Both wings show in the front panel. In the side panel the far wing lies behind the near one, which is expected in a pure side view.
- Pose reads as flying (forelegs tucked, hind legs trailing, neck forward, tail streaming).
- Background (sRGB 160,221,182): no character or prop texel is green-dominant (G - max(R,B) > 20: 0 %). The closest texel is 40 units away
  (white Pegasus body), so the colours separate by hue.

## Still open (not mechanical; reported, not changed)
- The inner thighs sink into the upper flank behind the wing roots: 31 vertices confirmed inside by ray parity, 8-17 cm deep.
  This is hidden in every view. Raising him would float the seat, and the builder already tried wider thighs. It needs a pose or
  corrective rethink if the game camera ever sees under the thighs.
- The shield overlaps his own upper_arm_l (149 tris) and shoulder_l (69). The upper arm is behind the shield in every view, so it does not show.
  Its lower edge goes into the blue mane hair (279 tris, visible as hair over the rim in the front-low view).
- The skirt goes into the back (hidden) and brushes the inner feathers (66 tris).
