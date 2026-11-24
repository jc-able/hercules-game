# Brief — Godot core

Read `docs/AGENT_RULES.md` and ALL of `docs/SPEC.md`. You own everything marked `core` in SPEC §7 and nothing else.
Good patterns to copy from the owner's earlier Godot 4.7.2 games (read-only, not part of this repo): their
`scripts/autoload/controls.gd` (device-aware prompts, pad traps), `scripts/autoload/game.gd`, and their harness flags.

## Goal
A playable grey-box of the whole core loop that the boss, world and art agents plug into WITHOUT touching your files:
`Godot --path game -- --start=test --harness --bot=win` must run a full fight against a built-in dummy boss.

## Build, in this order (commit nothing; run the checks in AGENT_RULES after each step)
1. `project.godot`: name "Hercules", 1920x1080 window (stretch canvas_items/expand), Forward+, Jolt, input map from SPEC §5
   (keyboard+mouse and joypad on device -1), autoloads Game / Controls / Sfx, main scene `scenes/main.tscn`,
   collision layer names from SPEC §7.1.
2. `Tuning` (`scripts/data/tuning.gd`): every number of SPEC §2-§4 as constants + `CHARS` (id -> height, radius, colour,
   stand-in shape) so stand-ins have the right size (Cyclops 8 m, Medusa 6.5 m + tail, Hydra 6.5 m shoulder / 18 m long, ...).
3. `Game` autoload: arg parsing after `--`, scene routing with fade (`goto`), progress + save (`user://save.json`; in harness
   mode use memory only), pause handling. Scene ids map to builder scripts: "title","home","sea","cyclops","medusa","hydra",
   "ending" and "test" (your dummy arena). If a builder script for an id does not exist yet, show a clear on-screen message
   instead of crashing (the other modules arrive later): look the script up by path (`res://scripts/world/<id>_arena.gd`,
   `home_base.gd`, `sea_world.gd`) with `ResourceLoader.exists`.
4. `CharacterVisual`: SPEC API. Stand-in = capsules/boxes built from `Tuning.CHARS` with named socket markers (so
   `socket("hand_r")` etc. always return a node) and a few procedural "clips" (bob for idle, lean for windups) so fights are
   readable before the art lands. Real path: if `res://assets/characters/<id>/<id>.glb` exists, instance it, find the
   AnimationPlayer + Skeleton3D, read `<id>_clips.json`, create BoneAttachment3D sockets, apply the toon material
   (`shaders/toon.gdshader` + outline next pass) to every surface keeping its albedo texture. `play()` cross-fades; looping
   comes from the manifest. Weapon props: `attach_prop(socket, "res://assets/props/sword.glb")` with a stand-in box if missing.
5. `Player` + `PlayerCamera`: SPEC §2 and §5 exactly (states idle/move/roll/attack/block/hit/petrified/dead; lock-on strafing;
   i-frames; 2-hit combo with buffered input; shield arc; `try_hit` results). Camera = SpringArm3D, behind the player; locked:
   stays on the player->boss line, frames the boss via `get_lock_point()`, smooth, never clips under the floor, never shows the
   player's front in play. Free: mouse / right stick orbit with clamped pitch. In harness mode never capture the mouse.
6. Combat: sword hitbox active only in the attack window; `WeakPoint` (struck only while `exposed`; otherwise glance: spark +
   `Sfx.play("glance")`); damage numbers are not needed. Hit pause (0.06 s) and camera shake on big impacts are welcome.
7. `BossBase` + `ArenaBase`: SPEC API. ArenaBase flow: build environment -> spawn boss + player -> island title card ->
   `boss.start_fight()` -> on `defeated`: "LABOR COMPLETE", `Game.mark_defeated`, then `Game.goto("sea", {from = id})`;
   on player death: "DEFEATED", restart this arena. Telegraph decals (`telegraph.gd`): circle, cone/arc, ring — flat meshes
   just above the floor with a fill that grows over the warning time (unshaded, readable on bright sand and on black basalt).
8. HUD + shell: health bars, boss bar, reticle, prompts via `Controls`, title screen, pause menu, overlays, controls page.
   Clean flat style (dark panels, warm gold accents, Greek-key line) drawn in code; no external fonts/images required.
9. Shaders: `toon.gdshader` (albedo texture, 2-3 bands, rim, optional tint/flash uniform, petrify blend to stone),
   `outline.gdshader` (inverted hull, width in metres scaled so an 8 m boss and a 1.9 m hero both get a sensible line),
   `water.gdshader` (flat stylized sea, foam bands, gentle waves), `sky.gdshader` (gradient + painted cloud bands).
10. Harness (`scripts/test/`): SPEC §7.2. Bot `win` follows `boss.bot_advice()`; `lose` stands still; `idle` does nothing.
    `--shots` saves viewport PNGs. Always end with `[H] result=...` and quit with exit code 0 (victory/quit) or 1.
11. Dummy boss + `test` arena (flat disc, one boss with one telegraphed circle attack and one weak point that opens after it)
    to prove the whole chain. Keep it: it is the regression test for core.

## Rules of thumb
- Everything is built in code in `_ready()`; only `scenes/main.tscn` exists as a scene file.
- Typed GDScript, `class_name` on shared classes, signals for cross-module talk, no `get_node("/root/...")` chains into
  other modules. Document each public function with one comment line.
- Controller: bind joypad events with `device = -1`; B must work as back in menus and A as accept; analog sticks need a dead
  zone (0.2); prompts switch with the last-used device. Test with synthetic joypad events (`--pad`).
- Performance: 60 fps at 1080p on an M5 Max is easy — do not optimise early, but avoid per-frame allocations in hot loops.

## Done when
- `Godot --headless --path game --import` then `Godot --headless --path game -- --start=test --harness --bot=win --quit-after=120`
  prints `[H] result=victory` with no SCRIPT ERROR; `--bot=lose` prints `[H] result=defeat` after at least one restart check.
- A windowed run `-- --start=test --harness --bot=win --shots=work/core/shots --shot-every=2` produces frames where the
  camera is behind the player and the dummy boss towers (look at 3-4 of them, <= 1024 px).
- `-- --start=title --harness --quit-after=5` shows the title screen without errors; `--pad` run of the test fight passes.
- `docs/notes/core.md` lists: how to add an arena/boss (10 lines), every public class + file, known gaps.
Write a simple complete v1 of steps 1-7 early (stand-ins everywhere), run it, then improve in small steps.
