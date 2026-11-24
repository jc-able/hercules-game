# Brief — world module (home base, sea, Pegasus flight, progression)

Read `docs/AGENT_RULES.md`, ALL of `docs/SPEC.md` (§4 above all) and `docs/notes/core.md`.
You own `game/scripts/world/home_base.gd`, `sea_world.gd`, `pegasus_flight.gd`, `island_proxy.gd`, `ending.gd` and
`docs/notes/world.md`. Nothing else under `game/` (requests for core go in your notes file).

## Build
1. **Home base** (`home`): a small green plateau island (about 45 m across) above the sea: the temple, three trophy
   pedestals (a trophy appears on each when `Game.defeated[...]` is true: a piece of the club, a stone snake head, a
   Hydra horn — simple shapes are fine), olive trees / cypresses / amphorae, a brazier, low walls at the edge so the
   player cannot fall. Hercules spawns in front of the temple with the normal Player controller (free camera).
   Pegasus (`CharacterVisual.create("pegasus")`, `idle` clip) waits on the grass with a prompt (`Controls` prompt
   for interact): "Fly". Interact -> short mount beat -> `Game.goto("sea", {from = "home"})`.
   A sign shows the next goal: which island is open (text from progress).
2. **Sea** (`sea`): open water (core water shader on a huge plane), sky, sun, distant haze. Four islands at the SPEC
   coordinates, each an `IslandProxy`: a rocky island body (procedural mesh or stacked `cliff_rock` / `boulder` props +
   a flat top) dressed to hint at what lives there (quarry columns; marble ring with statues; a black volcano cone with a
   glowing crater and smoke for the hydra). Unlocked + undefeated island: tall pillar of light + landing ring.
   Defeated island: calm, small flag of smoke gone, ring still there (the fight can be replayed). Locked island: wrapped
   in a dark storm wall (rotating cloud cylinder + lightning flashes); flying into it turns Pegasus away with a message.
   Home always has a ring.
3. **Flight** (`pegasus_flight.gd`): Hercules rides Pegasus (rider = `CharacterVisual.create("hercules")` playing `ride`,
   parented to Pegasus's `saddle` socket; Pegasus plays `fly`, or `glide` when not boosting and descending). Third-person
   chase camera behind and above. Controls: left stick / WASD steer (yaw + pitch), boost button, auto-level; speed 28 m/s
   (boost 46), height clamped 12-140 m, soft world bounds (turn back past 2200 m from the centre). Banking into turns,
   wing-beat bob, speed lines / wind streaks when boosting, a compass strip or edge arrows that point to open islands.
   Start position: near the island named in `opts.from`, facing the next open island.
   Entering a landing ring: prompt "Land" (interact) — or automatic after 1.5 s inside — then `Game.goto("<id>")`
   (`home` for the home ring).
4. **Progress + ending**: after the Hydra falls the first time, the sea scene shows the ending card once
   ("The three labors are done." + credits lines: design + direction JC; built with Claude; 3D models, images and
   animation references generated on Higgsfield), then free flight continues.
5. `bot` support for the harness: expose `bot_advice()` on the flight controller (steer toward the next open ring, land)
   and on the home scene (walk to Pegasus, interact) so `--bot=win` can travel: home -> sea -> next island.

## Look
Bright Mediterranean day: blue-turquoise sea with foam bands near shores, big painted clouds, warm sun. The volcano
island glows orange under a dark smoke plume even from far away. It should feel good to fly: nothing blocks the view,
islands are visible from the home base, wing tips frame the screen.

## Done when
- `Godot --headless --path game -- --start=home --harness --bot=win --quit-after=180` reaches the cyclops arena
  (`[H] event=scene id=cyclops` or the equivalent line core prints) with no SCRIPT ERROR; same from `--start=sea`.
- With a save state where cyclops is defeated (harness arg `--defeated=cyclops`), the bot flies to medusa; with all three
  defeated the ending card shows once.
- Windowed `--shots` of home and of the flight (<= 6 frames looked at): islands visible, rider on Pegasus, camera behind.
- `docs/notes/world.md`: layout numbers, how landing works, what you needed from core, known gaps.
Write a simple complete v1 first (boxes for islands), prove the bot can travel, then dress and polish.
