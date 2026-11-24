# World module notes (world builder, 2026-11-22)

Files (all world-owned, no `class_name`, loaded by path; shared code via `preload`):
- `game/scripts/world/island_proxy.gd`: one island on the sea map (body, dressing, ring, pillar, storm, smoke) and
  static helpers shared by the world scenes (`plateau_mesh`, `cone_mesh`, `glow_material`, `make_loop`,
  `build_clouds`, `hide_hud_health`, `compass_word`).
- `game/scripts/world/home_base.gd`: scene `home`.
- `game/scripts/world/sea_world.gd`: scene `sea`.
- `game/scripts/world/pegasus_flight.gd`: the flight controller used by `sea`.
- `game/scripts/world/ending.gd`: scene `ending` (Game.BUILDERS prefers it over core's `ui/ending_card.gd`).

## Real-model integration (world integrator, 2026-11-22; owner away, decisions marked **Decision**)
Done with the real GLBs in game/assets/characters (no asset imports, no core files touched). Logs: work/world_int/logs/.
- **Rider seat**: `IslandProxy.mount_rider(mount, rider)` parents the hercules visual to Pegasus's `saddle` socket with
  the manifest `rider.offset` ((0.0041, -1.0836, 0.0299), identity; = ride_game.json's saddle-bone form plus the socket
  offset). He now rides the saddle bone (fly v2 bob, no per-frame code). Stand-ins keep the old hips glue
  (`seat_rider`). Probe `--world-probe=seat` (sea): hips 0.000 m from the socket, up/forward within 1.4 deg of
  Pegasus's over 10 s of take-off, boost and glide.
- **Rider in phase with the wing beat** (anim_pegasus_fix / ride_anim requests): `IslandProxy.sync_rider` each frame:
  fly -> ride at `rider_speed_on_fly` 1.44 x the fly rate (x1.25 boosting = 1.80), phase = fmod(fly_pos / fly_beat_s,
  1) x 1.5 read from the Pegasus AnimationPlayer, re-seek when off by > 1 frame (measured error <= 0.01 s);
  glide / idle -> ride at `rider_speed_on_glide` 0.4, free-running.
- **Code bob removed** (fly v2 has its own 8 cm bob). `wing_flap` now plays on each fly loop wrap (wing top = start of
  the downstroke) instead of a clock.
- **fly / glide choice**: fly while boosting, climbing (> 5 deg), taking off, accelerating (> 3 m/s under the wanted
  speed) or hovering; glide while descending (< -4 deg) or landing; level cruise = 3.0 s glide then 2 wing beats,
  repeating (**Decision**: the brief says glide when cruising; a never-flapping horse read as dead, so it flaps between
  glides). A clip is held >= 0.6 s; boost on/off re-times fly without restarting it.
- **Camera**: 6.0 m behind, 4.2 m above Pegasus's feet (was 7.5 / 5.2), FOV 70 -> 78 boosting (+0.8 m; was 82, +1.6 m);
  leans into the bank by 30 % of Pegasus's roll. Bug fixed: it smoothed the WORLD position, so it trailed by
  speed / rate (6.5 m extra at 46 m/s) and the pair shrank to a speck while boosting; it now smooths the offset.
  Pair ~1/3 of the frame width, wing tips in frame at the top of the stroke, rider in the lower centre.
- **Take-off**: every sea start beside an island (home mount, arena victory, after the ending) begins 9 m lower at half
  speed, nose up 18 deg, beating, and climbs for 1.8 s (`take_off`, event `take_off`); skipped when the scene routes to
  the ending. **Landing**: entering/landing keeps the 1.5 s auto-land, then Pegasus glides down at -14 deg for 0.9 s
  before the scene fade starts (`LAND_DELAY`).
- **Home mount beat** (was: hero vanishes, rider pops onto a rising horse): a second hercules visual playing `ride`
  starts exactly at the walking hero's transform and hops onto the saddle on a 0.7 m arc (0.55 s, facing slerped to
  Pegasus's), then is socketed like in flight; Pegasus switches idle -> fly, settles 0.35 s, lifts 6.5 m up and 9 m
  ahead with a 16 deg nose-up over 1.6 s; a mount camera eases from the hero's chase camera to 7 m behind / 3.4 m above
  the pair. The fade starts at 60 % of the lift (event `mount_seated socketed=true` at +0.55 s, sea at +2.1 s).
- **Wing clearance in game** (owner's ride ref_sheet.jpg): checked in windowed shots over a full beat from behind and
  from the side (harness `--world-cam-yaw=<deg>` holds the camera at an orbit angle aimed at the pair): rider on the
  back, feet outside, wings out to the sides and the near wing passing outside him; no wing through his legs seen.
- Proof (headless, no SCRIPT ERROR / ERROR / WARNING in any log): `--start=home --bot=win` (speed 1) mount 1.0 s,
  sea 3.1 s, lands at cyclops 18.0 s, `scene id=cyclops`, fight won at speed 3; `--start=sea --defeated=cyclops` ->
  medusa 21.6 s; `cyclops,medusa` -> hydra 30.4 s; `--defeated=all` -> `ending_shown` once, then free flight home;
  `--start=cyclops --after-victory=30 --speed=4` -> sea from cyclops -> medusa -> hydra; `--pad` and `--keys` home ->
  cyclops; storm probe 122.9 m (wall 88 m) ok; limit 2210.9 m ok; seat probe ok.
- Devlog: docs/devlog/media_inbox/world_int/ (mount beat, chase camera, 8-phase ride strips).

## Play-test fixes (world fixer 2, 2026-11-22; owner away, decisions marked **Decision**)
Logs, probes and shots: work/world_fix2/ (run_proof.sh, p_mount_race.gd, p_track.gd, logs/, shots/).
- **Pause during the landing glide / mount lift** (Quit to title / Return home sent the player into the arena or the
  sea): the LAND_DELAY timer (pegasus_flight `_land`) and the home mount timer now go only when
  `not Game.is_switching() and Game.world == <this scene>`. QA probe `work/qa_bugs/p_menu_race.gd --qa=land` at
  0.3 / 0.6 / 0.8 s -> title; Resume -> still lands at cyclops. Home: `p_mount_race.gd` at 1.6 / 1.78 s -> title;
  Resume -> sea.
- **Dives never worked (found here)**: `_ahead_climb_pitch()` returns 0 over flat sea and `if climb > target_pitch`
  replaced every nose-down target with level flight, so a player who climbed could never come down (seen as the bot
  stuck at 108 m for 116 s after the ending). Now only a climb > 0 overrides the stick. Probes: dive bottoms out at
  12.00 m, volcano pass min 3.91 m above ground (as before), low approach at the taller quarry isle max 0.52 m/frame.
- **Free flight after the ending**: `sea` is free flight when opts.free_flight OR all three labors are won and the
  card was seen (mounting at home afterwards used to be a normal flight with home as the target). Free flight starts
  facing AWAY from home (home itself: north); the ring Pegasus starts beside lands on interact only for the first
  10 s (`NO_AUTO_LAND_TIME`, any start, `flight.no_auto_land_island/_until`). Beaten rings already land on interact
  (rematch). If the away-from-home side is the hydra's volcano, the start turns a quarter round (east, open sea).
- **Fight controls in play**: the home sign's back now has a fight block (`{attack} strike {shield} shield (hold)
  {roll} roll {lock_on} lock on`, font 34) and the first flight to the first labor (nothing beaten) shows the same line
  for 7 s after the title card (`event=combat_hint`). Flight messages (this hint, storm and world-limit warnings) are
  drawn by the flight overlay UNDER the compass strip (`flight.show_hint`): the Hud toast (y 40-80) sat on the strip.
- **Sky** (`IslandProxy.world_sky`, home + sea): zenith (0.05, 0.23, 0.64), horizon (0.53, 0.72, 0.90), fog colour
  (0.60, 0.76, 0.91), fog 0.0002 sea / 0.00025 home (were 0.00045 / 0.0006), painted cloud streaks 0.2 (were 0.45:
  they whitened the band above the horizon; the 3D cloud banks stay).
- **Islands**: Quarry Isle top_h 10 -> 20 m, green top (0.50, 0.62, 0.31) with a packed-earth quarry floor disc r 30,
  sandstone cliffs, a horseshoe quarry wall of cliff_rock in three receding tiers (~27 m, 0-135 deg on the NE rim),
  5 cypresses on the SW rim, columns x1.4; struct_h 27, ring_up 38 (ring 58 m above the sea). Sanctuary Isle top_h
  16 -> 20 m, green rim, pale grey cliffs, 14 columns x2 (12 m) carrying a continuous architrave ring, statues x1.6,
  gate x1.5 moved out to z -38 (it overlapped a column); struct_h 14, ring_up 30 (ring 50 m). Hydra unchanged.
  **Decision**: the proxies are scenery only (arenas build their own ground), so no arena file changes.
- Proof (headless `--speed=3`, work/world_fix2/run_proof.sh, final pass, no SCRIPT ERROR / Parse Error in any log):
  home --bot=win seeds 11 / 4242 -> cyclops won; cyclops --bot=lose -> defeat; sea --defeated=cyclops -> medusa won;
  cyclops,medusa -> hydra won; --defeated=all -> ending once, free flight from hydra (east side) -> home at 37.5 s;
  home --defeated=all --ending-seen -> `free=true`, bot (interact) lands home; same with --bot=idle: no landing in
  14 s; storm 122.9 m vs wall 88 m; limit 2210.9 m; --keys / --pad home -> cyclops won (combat_hint at +3.2 s).
  First pass: two runs hit mid-edit parse errors in cyclops_arena.gd / hydra_arena.gd (other fixers); re-run clean.
  Windowed: work/world_fix2/shots/sheet2.jpg, sheet3.jpg (flight approach, tour of cyclops/medusa/hydra/home).

## Status
v1 is complete and dressed. Every route runs headless with no SCRIPT ERROR / Parse Error / WARNING:
| Command (all with `--harness`) | Result |
|---|---|
| `--start=home --bot=win --speed=3` | mount at 1.0 s, sea, lands in the cyclops ring at 16.6 s, `event=scene id=cyclops`, fight won |
| `--start=sea --bot=win --speed=3` | lands at cyclops at 14.4 s |
| `--start=home --bot=win --defeated=cyclops` | flies to medusa (lands 23.3 s) |
| `--start=sea --bot=win --defeated=cyclops,medusa` | flies to hydra (lands 29.9 s) |
| `--start=sea --bot=win --defeated=all` | ending card once (`ending_shown`), then free flight from hydra, the bot lands at home |
| `--start=cyclops --bot=win --after-victory=40 --speed=4` | cyclops won -> sea from cyclops -> medusa won -> sea -> hydra won (whole chain by the bot) |
| `--start=hydra --defeated=cyclops,medusa --bot=win --after-victory=10 --speed=4` | hydra won -> `ending` -> sea free flight -> home |
| `--start=home/sea --bot=win --pad` and `--keys` | same travel with synthetic joypad / keyboard events (boost on RT axis / Shift) |
| `--start=sea --bot=idle --world-probe=storm` | Pegasus flies straight at locked Medusa: turned away at 133 m, closest 123 m (wall 88 m), `ok=true` |
| `--start=sea --bot=idle --world-probe=limit` | starts at 2150 m flying outward: turned back at 2200 m, max 2211 m, `ok=true` |
Re-run after the review fixes (2026-11-22, fixer): every row above again with no SCRIPT ERROR (home/sea/keys/pad ->
cyclops; `--defeated=cyclops` -> medusa 23.3 s; `cyclops,medusa` -> hydra; `all` -> one `ending_shown`, then free
flight lands at home; cyclops chain -> medusa -> hydra; storm 123 m vs wall 88 m; limit 2211 m). Windowed: flight to
medusa (target island above the rider at 534 / 413 / 302 / 194 m), home spawn view (sign readable), real GLB rigs
via `--world-glb=work/world/glb` (rider seated through the shared helper, island above him).
Windowed `--shots` looked at: home spawn view, home trophies, flight toward each island, storm wall, ending card,
real rigs on the saddle. Copies in `docs/devlog/media_inbox/world/` (captions.txt has the numbers).

## Layout numbers
Sea map (SPEC §4, sea level y = 0 in `sea`): home (0, 0), cyclops (520, -380), medusa (-640, -700), hydra (120, -1350).
`IslandProxy.PROFILES` (metres, relative to the island centre at sea level):
| id | top radius | waterline radius | top height | ring radius | ring height (above sea) | dressing |
|---|---|---|---|---|---|---|
| home | 24 | 38 | 14 | 24 | 44 | temple, cypresses, olive trees |
| cyclops | 46 | 64 | 20 | 28 | 58 | quarry floor disc r 30, 9 columns / broken columns (x1.4) on r 32, 3-tier quarry wall (~27 m) on the NE rim, 5 cypresses SW, boulders |
| medusa | 40 | 58 | 20 | 26 | 50 | marble disc r 30, 14 columns x2 r 34 + architrave ring, 10 statues x1.6 r 30 facing in, gate x1.5 at z -38 |
| hydra | 70 | 92 | 12 | 28 | 42 | 8 basalt spires r ~38; volcano cone at (0, 0, -82): base r 64, peak 88, crater r 15, 6 lava rivers, 18 smoke puffs |
- Landing zone: horizontal distance < ring radius and |height - ring height| < 18 m.
- `ground_height` (what the flight keeps clear of): plateau top inside top_r, linear slope to 0 at base_r, plus the
  tallest dressing `struct_h` faded out with `1 - smoothstep(top_r, top_r + 30, d)` (it used to be a step at top_r + 6,
  which made Pegasus pop up 17 m in one frame), plus the volcano cone for hydra.
- Pillar of light: r 7, 700 m tall, additive (open + undefeated only). Storm wall (locked only): cylinder of radius
  waterline radius + 30 (hydra: 176 m because of the volcano), 175 m tall (above the 140 m ceiling).
- Home scene: plateau top y = 0, sea y = -14 (so the plateau matches the home proxy's 14 m top), rim r 23.5, low wall
  r 21.6 (invisible boundary at r ~21.2), temple (0, 0, 11) facing north, hero spawn (0, 0.1, -4) facing north,
  Pegasus (5.5, 0, -10.5) facing west, mount spot = its south side (+1.75 z), interact within 3.2 m, pedestals
  cyclops (-6, 0, 2.6) / medusa (0, 0, 3.4) / hydra (6, 0, 2.6), braziers (+-3.4, 0, 5).
  Sign (-4, 0, -5.5), board 3.4 x 2.0 m: the face toward the spawn shows the goal in three big lines
  ("NEXT LABOR / <island> / to the <direction>", Label3D 56 px at 0.0058 m/px, readable from the spawn view), the back
  shows the controls. The home title card's subtitle is the same goal ("Next: The Quarry Isle, to the north-east").
  The three other islands stand on the horizon at their sea-map coordinates (same IslandProxy, sea y = -14).
- Clouds: 34 banks of 5-8 toon spheres, 175-260 m above the sea (never in the flight band), fixed seed.

## Flight (pegasus_flight.gd)
- Speed 28 m/s, boost 46 (Tuning), 13 m/s inside the TARGET landing ring only; acceleration 16 m/s^2 (29 when slowing).
- Yaw 70 deg/s at full stick, pitch up to 32 deg, auto-level (pitch eases back with no input), bank 38 deg.
- Height: at least 12 m above the sea (hard clamp, SPEC) and 9 m above any island top + its dressing
  (`ground_height`); at most 140 m. Terrain handling, in order each frame:
  1. Look-ahead: the ground is sampled 0.5 / 1 / 1.75 / 2.5 / 3.25 s ahead; if it rises above the flight height minus
     9 m, the wanted pitch becomes the climb angle needed (up to 45 deg, response 5/s), winning over the stick.
  2. A dive eases out within 6 m above the floor.
  3. Below the floor: pushed up at most 20 m/s (`move_toward`, no snapping).
  4. Hard limits: >= sea + 12 m and >= island surface + 2 m.
  Probes (work/world_fixer/probe.gd): low approach at Cyclops max 0.41 m per frame (was 16.74 m); low approach into
  the volcano from the north max 0.57 m per frame, never closer than 3.9 m to the cone; full dive bottoms out at 12.00 m.
- Locked island: within storm radius + 45 m and heading in, Pegasus turns away (150 deg/s, 1.4 s) with
  a message naming the island that opens it; it is also clamped outside the wall. Past 2200 m from the centre it turns back.
- (Superseded for camera, bob and rider by "Real-model integration" above.)
- Camera: own Camera3D, 7.5 m behind, 5.2 m up, aims 120 m ahead and 4 m up (horizon near the screen middle, Pegasus
  and the rider in the lower third, so the target island shows above the rider from ~550 m in), FOV 70 -> 82 and
  +1.6 m distance while boosting; mouse / right stick orbit it, it recentres after 1 s.
- Look: Pegasus plays `fly` (x1.25 while boosting) or `glide` (not boosting and pitched down > 6 deg, or landing),
  wing-beat bob 0.22 m on the fly beat, `wing_flap` sound per beat, speed lines + compass strip (CanvasLayer 5): ticks,
  N/E/S/W, a diamond per island (gold open, blue home, white beaten, violet locked; edge arrows when off the strip),
  target name + distance.
- Rider: `CharacterVisual.create("hercules")` (sword + shield attached) playing `ride`, a child of the Pegasus visual
  (same facing). Each frame its position puts its `hips` bone (any bone named *hip* / *pelvis*; stand-in: 47% of its
  height) on Pegasus's `saddle` socket. The code is shared: `IslandProxy.find_hips(rider)` + `IslandProxy.seat_rider(
  mount, rider, hips)`, used by the flight every frame and by the home mount beat every frame of its tween, so the
  rider sits the same way in both scenes once the real GLBs are in. (The brief says "parented to the saddle socket"; following the socket's
  position keeps the rider upright whatever the saddle bone's orientation is.) Checked with the real
  art_src exports: the hips sit on the saddle bone.

## How landing works
1. Each physics frame the flight asks every island `in_ring(pos)`. Entering one: event `ring_enter island=<id>
   target=<bool>` and a prompt. The target is `world.next_target()` (first undefeated island; home in free flight).
2. Target ring: prompt `{interact} Land - <island>`, speed eases to 13 m/s, interact lands at once, otherwise it lands
   by itself after 1.5 s inside. Any other ring (a beaten island, home before the ending): prompt
   `{interact} Land - replay the labor (<island>)` (home: `{interact} Land - Home Isle`), no slow-down, lands on
   interact only, so crossing it is quick and never forces a replay. (Review fix: the probe that flew level through
   the beaten Cyclops ring used to land and restart the fight; now `ring_enter target=false` and it flies on.)
3. `_land(id)`: event `land island=<id>`, `Sfx land`, Pegasus glides down, `Game.goto(<id>, {from = "sea"})` (`home`
   for the home ring). Beaten islands keep a white ring, so a fight can be replayed. Locked islands have no ring.
4. After a fight ArenaBase sends `sea {from = <id>}`; the sea starts Pegasus 55 m outside that island's ring, facing the
   next open island (the first undefeated one in unlock order, else home), at the ring's height.
5. Ending: `sea_world._ready()` routes to `ending` when `Game.ending_pending()`; `ending.gd` calls
   `Game.mark_ending_seen()`, fades in the card (title + the brief's credit lines), and after 11 s (harness 3 s) or
   interact / accept goes to `sea {from, free_flight = true}`. In free flight the compass target and the bot go home.

## Bot advice
- Home (scene node): `{move_to: mount spot, interact: within 2.8 m of Pegasus, face: Pegasus}`.
- Flight (node in group `bot_advisor`): stick x from the heading error to the target ring (x2.5, clamped), stick y from
  the height error (-dy/12), boost when lined up (< 0.35 rad) and farther than 220 m, interact inside the target ring.
  Returns `{}` while frozen, landing or during a scene fade.

## Harness probes (world module self-tests, harness only)
- `--world-probe=storm | limit` (sea, use `--bot=idle`): see Status.
- Out-of-game probe `work/world_fixer/probe.gd` (a copy of the reviewer's, plus `volcano`):
  `Godot --headless --path game --script ../work/world_fixer/probe.gd -- --start=sea --harness --probe-kind=<beaten|floor|dive|volcano> [--defeated=..]`.
- `--world-probe=tour` (sea): parks Pegasus (frozen) in front of home, cyclops, medusa, hydra, 3 s each, switching
  half-way between 3 s screenshots: `--shots=<dir> --shot-every=3`.
- `--world-probe=trophies` (home): the hero turns to the temple and the trophy pedestals.
- `--world-probe=seat` (sea, e.g. with `--bot=win`): rider seat + wing-beat phase every 0.25 s, `probe_result` at 10 s.
- `--world-cam-yaw=<deg>` (sea, windowed): flight camera held at that orbit angle, aimed at the pair (side views).
- `--world-glb=<dir>` (sea): loads `pegasus.glb` / `hercules.glb` (+ `<id>_clips.json`) from a folder through
  `CharacterVisual.create_from_file`, to check the saddle fit before the real models are in res://assets.

## Requests for core
1. `Hud`: a public switch for the hero health panel (e.g. `set_health_visible(false)`). Home and sea hide it through
   the private `_hp_bar` today (`IslandProxy.hide_hud_health`, guarded, does nothing if the field is renamed).
2. `toon.gdshader`: OmniLight / SpotLight light gets banded like the sun, so any light > 0 becomes a full band step and
   the light's clustered cut-off shows as square tiles (seen on the home grass around the brazier lights). Please band
   only the directional (sun) term, or band before applying attenuation. Until then the world scenes use no
   OmniLights (emissive flames, lava and smoke only). Boss arenas with braziers will hit the same thing.
3. Nothing else is needed: home, sea and ending use the existing API (goto, ending_pending/mark_ending_seen,
   capture_mouse + wants_mouse_captured, Hud prompts/messages/title card, Controls.fill, Sfx, EnvKit, CharacterVisual).

## For the art track
- `pegasus_clips.json` must map socket `saddle` -> bone `saddle` (the rider follows it) and keep `idle`, `fly`, `glide`.
- `hercules` needs a `ride` clip; whatever its root motion, the `hips` bone is glued to the saddle every frame.
- Without manifests the real GLBs load with the socket warnings core prints; the stand-ins are fine meanwhile.

## Decisions (owner away)
- Pitch: stick up / W climbs, stick down / S dives (non-inverted, friendlier for keyboard). `INVERT_PITCH` flips it.
- Home music: the title theme continues at home (`music_title`); the sea plays `music_flight`. Ambient `sea_loop`
  (home + sea), `wind_loop` in flight (louder with speed), `thunder` from storm walls when within 400 m: silent until
  those files exist.
- The temple is on the SOUTH rim facing north, because all three islands lie north of home: the hero spawns looking
  at the open sea and the islands with Pegasus in view.
- The landing ring is a horizontal glowing hoop 28-30 m above each island top with a faint disc (reads from above and
  from the side); entering the zone counts, no need to thread the hoop.
- Ring speed cap 13 m/s (target ring only) so the 1.5 s auto-land always happens before Pegasus crosses the ring.
- Only the target ring auto-lands (review fix, owner away): replaying a beaten labor or going home early is a choice
  (interact), never an accident.
- Automatic climb over rising ground may exceed the 32 deg stick pitch (up to 45 deg): the volcano's upper cone is
  nearly vertical, and anything less pops Pegasus up at its rim.
- Free flight after the ending: the compass and the bot target home.

## Known gaps
- (Real models are in and used; the stand-in path remains only as a fallback.)
- The hop onto the saddle uses the `ride` pose in the air (hercules has no mount/jump clip); a 0.5 s `mount` clip from
  the art track would read better. The flight camera has no landing move of its own (the 0.9 s glide + fade cover it).
- `IslandProxy.anim_player()` reads CharacterVisual's private `_anim` (falls back to a node search); a public
  `CharacterVisual.clip_position()` from core would be cleaner.
- Island bodies are procedural (faceted toon meshes + props), not sculpted; no collision in the sea (flight keeps
  Pegasus above them analytically).
- No foam ring painted around the island bases beyond what the core water shader's depth foam gives.
- No lightning bolt mesh in the storm wall: the flash lives in the shader (plus thunder).
- The mount beat at home is short (0.9 s hop + lift) and has no camera move. Its rider uses the shared hips-to-saddle
  helper, checked in flight with the real GLBs (`--world-glb`) but not at home (home has no `--world-glb` switch;
  it will be exercised once the GLBs are in game/assets).
- Camera: no sideways offset (the reviewer's optional idea); within ~120 m of the target the island is below the
  horizon and Pegasus overlaps its near half (it is wider than Pegasus there, so it still reads).
- Ring prompts are plain text; there is no different ring colour for "target" vs "replay" beyond the existing gold
  (open) / white (beaten) / blue (home) colours.
- No landing camera move: the fade covers it.
