# Last fixes (last_fixes, 2026-11-23 ~11:10-11:45; owner at the Mac, could not be asked, decisions marked **Decision**)

Rendering only through `tools/godot_bg/gdwin`, with a throwaway HOME (`work/last_fixes/home`, `work/last_fixes/homes/*`).
`builds/Hercules.app` and the owner's save folder untouched. No git writes. Scratch: `work/last_fixes/` (rec.sh, run_cold.sh,
zoom.py, movie/, perf/, strips/, logs/; `bin/GA.app` and `bin/GB.app` are APFS clones of Godot 4.7.2 for the fully cold runs).

## 1. Riderless landing (final_check2 §5 item 1): FIXED with a real dismount (not the fade fallback)
`game/scripts/world/home_base.gd` only (island_proxy, sea_world and pegasus_flight unchanged).
- **Rider through the glide-in.** Arriving from the sea (`opts.from == "sea"`), a rider (hercules visual, sword + shield) is seated
  with `IslandProxy.mount_rider()` (the same seat as in flight) and plays `ride`. `sync_rider()` keeps it on the wing beat each frame,
  as in flight. The walking hero is hidden and has no control.
- **Wings stay up while he is on.** The Pegasus idle folds its wings where a seated rider's legs are (integrate2_world). At the 78 %
  idle switch, a `WingOverlay` keeps `fly` on the 12 wing bones from the fly clip's current time, so the wings do not jump. Only
  the legs and body settle into the stance.
- **Dismount, the mirror of the mount.** At touch-down (`pegasus_landed`, now with `rider=true`) the invisible hero is put on the
  mount spot beside Pegasus, facing away from the camera. After `DISMOUNT_WAIT` 0.3 s (the idle blend is done), the rider leaves
  the socket. He eases from `ride` into the hero's idle (0.5 s) and hops in an arc (0.55 m high) onto the hero's spot and pose over
  `DISMOUNT_HOP` 0.85 s. At 50 % of the hop (he is clear of the wings), the overlay stops its beat and fades out over 0.55 s, so the
  wings fold into the idle with no extra flap (`WingOverlay.close()`). At the end, the walking hero replaces the rider (same clip
  and clip time, same transform), and the player gets control. Events: `dismount`, `dismount_done`.
- **Camera.** A beat camera eases (smoothstep, 1.15 s from touch-down) from the landing view to exactly the hero's chase-camera view
  at the new spot. That is a push-in of about 5 m toward Pegasus. The chase camera takes over where it ends, with no cut.
- **Decision**: the hero ends beside Pegasus, facing away from the camera (the smallest camera move), not at the old spawn.
- The first arrival of a new game (`from` is not sea) is unchanged: the hero stands at the spawn and Pegasus waits (headless
  `--start=home --bot=win`: mount 1.04, seated 0.90 s later, take_off 3.43, the same as before).
- Harness only: `--home-from=sea` makes `--start=home` arrive as if flown home (quick to record).
- Bot / input: no mount prompt and no bot advice until `dismount_done`.

Seen (gdwin 1600x900 movies, 30 fps):
| movie | timing | seen |
|---|---|---|
| `movie/after_land.avi` `--start=sea --defeated=all --ending-seen --bot=win` (the real path) | home scene 6.16, landed 8.06, hop 8.36, control 9.22 | strip `strips/s7_land_after.jpg`: rider on the back through the glide and flare, hop off on the near side, hero beside Pegasus, the bot re-mounts at 9.22. It loops home<->sea 3 times in 44 s: 0 SCRIPT ERROR |
| `movie/after_quick.avi` `--start=home --home-from=sea --bot=idle` | landed 1.93, hop 2.23-3.09 | `strips/a1_quick.jpg` + `a1_zoom.jpg` (crop): seated through the glide, he rises out of the saddle and drops beside the flank. The near wing is in a downstroke at the start of the hop and covers his near leg for about 0.2 s (the same fly clip as the mount) |

## 2. Boss-bar/fight_start warm-up: DONE (small)
The fight_start canvas compile was not the boss bar. `bind_boss()` shows the bar in `_ready`, so it is drawn under the title card
already. It was the **lock reticle**: `player.set_lock_target()` at fight_start draws its first thick `draw_polyline` diamond +
`draw_circle`. `hud.gd`: `warm_canvas(frames)` makes the Reticle draw the same primitives (polylines 5 / 2.5 / 2 px, circle, arc,
filled triangle) at a corner with alpha 0.004 for 4 frames. `arena_base.gd` `prewarm()` calls it (it honours `--no-prewarm`).
Fully cold (new HOME + new bundle id clone, 1920x1080, freeze_probe, `--bot=win --quit-after=8`):
| fight | before (final_check2) | after |
|---|---|---|
| medusa | 57-58 ms at fight_start, canvas pipe 1 | **0** frames > 50 ms; the canvas compiles now happen in the first frame (t 0.18, pipe c=5) |
| hydra | 57 ms, canvas pipe 1 | fight_start frame 53 ms with **0** pipeline compiles (proc 10 ms; load average 6.6 from other jobs). A first run beside the medusa run had 10 load frames with 0 compiles. What is left is not a compile (perhaps the music start in that frame); not chased |

## 3. Regression (headless, seed 11)
| run | result |
|---|---|
| `--start=title --campaign --bot=win --pad --speed=3` | victory, victories=3, t 260.63 (title->home->sea->cyclops->sea->medusa->sea->hydra->ending->sea) |
| same with `--keys` | victory, victories=3, t 261.43 |
| `--start=home --bot=win --quit-after=12` | mount 1.04, seated 1.95, take_off 3.43 (unchanged) |
| `--start=home --home-from=sea --bot=win --quit-after=8` | landed 1.90, dismount 2.20, done 3.05, mount 3.08, take_off 5.47 |
| `--start=cyclops --probe=ui` (`--pad` too) | focus=Resume, resumed, paused=false. It does not quit by itself on cyclops: I stopped it at 168 s / added `--quit-after=6` |
0 SCRIPT ERROR / Parse Error in every run, headless and rendered. (The first try had one "Lambda capture was freed" error, from freeing
the overlay in `_open_wings`; fixed with a weakref and no early free.)

## Open
- The near wing covers the rider's near leg for about 0.2 s at the start of the hop (a downstroke). It is the same as the mount's
  "wing hides the rider" (final_check2 item 7). A "stand with wings raised" Pegasus clip would remove both.
- `builds/Hercules.app` needs the lead's rebuild for these changes.
