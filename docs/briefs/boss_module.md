# Brief — a boss module (cyclops / medusa / hydra)

Read `docs/AGENT_RULES.md`, ALL of `docs/SPEC.md` and `docs/notes/core.md` (how to add an arena + boss, the real API).
You own exactly two files for YOUR boss `<id>`: `game/scripts/bosses/<id>.gd` (class extends BossBase) and
`game/scripts/world/<id>_arena.gd` (class extends ArenaBase), plus `docs/notes/<id>.md`. Nothing else under `game/`.
The core's dummy boss + `test` arena are your working example.

## Build
1. The arena of SPEC §3 for your boss: floor disc with the given radius (collision), a rim that keeps the player in,
   set dressing OUTSIDE the fighting lane, sun/sky/fog/colour to match `art_src/reference_video/key_<id>.png`
   (look at it once, <= 1024 px). Use the generated props when present (`game/assets/props/<name>.glb`, list + sizes in
   `game/assets/props/props.json`; names: column, column_broken, boulder, cliff_rock, statue_a, statue_b, gate,
   basalt_spire, brazier, amphora, olive_tree, cypress, temple, pedestal) through a small helper that falls back to a
   coloured box when a file is missing — the props are being produced in parallel. Beyond the rim: sea (core water shader)
   for the quarry and the sanctuary, lava (emissive, animated) for the volcano. Keep the centre open.
2. The boss state machine of SPEC §3 with the exact numbers from `Tuning` (add your constants to
   `game/scripts/data/tuning.gd` ONLY through a request in `docs/notes/<id>.md` if they are missing — until core adds them,
   keep them as constants at the top of your boss script, named identically).
   - Every attack: warning animation clip (`visual.play(...)`, names in SPEC §8) + ground decal (`arena.telegraph_*`) +
     `Sfx.play("<id>_<attack>_warn")`, then the hit via `hit_circle` / `hit_cone` with the right opts
     (blockable, guard_break, petrify, reflect, knockback).
   - Weak points: `add_weak_point(id, socket, radius)` at start; `expose(id, hits)` / `close_weak(id)` exactly in the
     windows SPEC gives. Hits outside the window must glance (core does that).
   - Clip timing: read `visual.event_time(clip, "impact", default)` so real animations can shift the moment of impact;
     scale playback speed so a clip fits the SPEC duration (`visual.clip_length`).
   - Below half health: the enrage changes of SPEC.
   - VFX with built-in nodes only (GPUParticles3D / simple meshes + unshaded materials): dust ring on the slam, the gaze
     beam + petrify flash, the fire stream (must read as fire from the chase camera), stomp shockwave, hit sparks.
     Mind the trap: a fullscreen `hint_screen_texture` quad deletes all transparents — do not use one.
3. `bot_advice()`: enough for `--bot=win` to win the fight the way SPEC intends (e.g. cyclops: block sweeps, roll out of
   the slam circle, run to the forearm and hit twice, back off). The bot proves a tester can win with the starting gear.
4. Intro: boss idle at the centre, player at the edge, island title card (core). Death: `death` clip, then `defeated`.

## Done when
- `Godot --headless --path game -- --start=<id> --harness --bot=win --quit-after=240` prints `[H] result=victory`, and
  `--bot=lose` prints `[H] result=defeat`; no SCRIPT ERROR lines. Run the win bot 3 times (different `--seed=` if core has it).
- A windowed run with `--shots` (1280x720, <= 6 frames looked at, <= 1024 px): camera behind the player, boss towering,
  every warning decal readable on your floor, arena dressed and matching the keyframe mood.
- `docs/notes/<id>.md`: states + timings as built, the bot's strategy, anything you needed from core, known gaps.
Write a simple complete v1 of the whole fight first (grey boxes are fine), prove the bot can win, then dress and polish.
