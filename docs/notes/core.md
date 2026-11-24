# Core notes (Godot core builder, 2026-11-22; review fixes applied the same day, see docs/notes/core_review.md)

Follow-up the same day (module requests applied): see docs/notes/core_followup.md.
Play-test fixes (death, framing, menus, mouse, focus pause, `--campaign`, `--fake-save`): see docs/notes/core_fix.md.

## Status
Core v1 is complete and runs headless and windowed with no SCRIPT ERROR (re-checked after the review fixes):
- `Godot --headless --path game -- --start=test --harness --bot=win --quit-after=120` -> `[H] result=victory` (exit 0, ~15.5 s game time)
- `... --bot=lose --quit-after=120` -> dies, "DEFEATED", arena rebuilt, `fight_start` again -> `[H] result=defeat` (exit 1)
- `... --bot=win --pad` / `--keys` -> victory with synthetic joypad / keyboard+mouse events (device + prompts follow)
- `... --start=title --harness --quit-after=5` -> title, `result=quit`
- `... --start=test --harness --probe=ui [--pad]` -> opens the pause menu (focus on Resume), backs out with Esc / pad B
  (press + release); no `roll` follows the resume any more
- `... --start=test_travel --harness --bot=win [--pad|--keys]` -> bot walks to a marker, interacts, "flies" (no Player,
  stick + boost advice) into a ring, lands in `test`, wins: proves the advisor fallback home/sea need
- `... --start=title --harness --probe=goto` -> two gotos in one fade: the later one wins (`probe_goto ok=true`)
- `... --start=test --harness --bot=win --after-victory=1` -> runs LABOR COMPLETE + the goto, ends 1 s after the next scene
- `... --start=home --harness --bot=win` (no world files yet) -> `result=missing_scene` at once (exit 1)
- `--speed=3` runs fights 3x faster (physics ticks scaled with it, so results match speed 1).
- Real-GLB probe `work/core/probe/replay_probe.gd`: a clip played twice restarts (0.266 s -> 0.000); a GLB without a
  manifest maps `run` to `review_run` and loops it.

## Harness flags (SPEC §7.2 + additions)
`--start=<id> --harness [--bot=win|lose|idle] [--pad | --keys] [--seed=<int>] [--defeated=cyclops,medusa|all]
[--ending-seen] [--after-victory=<s>] [--shots=<dir>] [--shot-every=<s>] [--quit-after=<s>] [--speed=<x>] [--probe=ui|goto]`
- `--seed` seeds `seed()` and `Game.rng` (default 1234567); printed in the `[H] harness start=` line with the preset progress.
- `--defeated` presets `Game.defeated` in memory and emits `progress_changed` (harness only, never saved).
- `--after-victory=<s>`: keep running after `victory` and end `<s>` s after the next `scene` event (default: end 1.5 s
  after the victory, before the post-victory flow).
- A start scene without a builder script ends at once with `result=missing_scene`.

## Bot advice (scripts/test/bot.gd)
1. A fighting boss (lock target, else any node in group "boss" with `fighting`): `boss.bot_advice()` as in SPEC §7.1
   (`move_to`, `face`, `roll`, `block`, `attack`).
2. Otherwise the first node in group `"bot_advisor"` with `bot_advice()`, else `Game.world.bot_advice()` (the scene node).
   Generic dictionary, every key optional: `stick: Vector2` (left stick as pushed: x right, y back/down), `move_to: Vector3`
   (walk there; needs a Player, ignored when `stick` is given), `face: Vector3` (free mode, not moving: turn to it),
   `look: Vector2` (right stick), `interact`/`roll`/`attack`/`lock_on: bool` (tapped, with cooldowns: interact 0.5 s),
   `block`/`boost: bool` (held). Return `{}` when nothing should happen. Example: scripts/test/travel_test.gd.
All of it goes through `_set_stick/_set_button/_set_look`, so `--pad` (joypad events, RT axis for boost) and `--keys`
(WASD / Space / Q / E / Shift / mouse buttons) work for world scenes too.

## How to add an arena + boss (cyclops / medusa / hydra modules)
1. `scripts/world/<id>_arena.gd`: `extends ArenaBase`; in `_init()` set `arena_id = &"<id>"` and `radius = Tuning.<ID>["arena_radius"]`.
2. Override `build_environment()` (use `EnvKit.sky/sun/floor_disc/sea/prop/column/rock`) and `spawn_boss()` (create the boss,
   set `b.position`, return it UNPARENTED: ArenaBase then sets `b.arena` and `b.player` and adds it, so both are valid in the
   boss's `_ready()`/`_build()`; the Player already exists when spawn_boss() runs). Optional: `player_spawn()`.
   Game finds the file by path: no registration needed.
3. `scripts/bosses/<id>.gd`: `extends BossBase`; in `_init()` set `boss_id`, `display_name`, `max_hp`, `body_radius`, `body_height`
   (boss_id must be set in `_init` so `CharacterVisual.create(boss_id)` picks the right model).
4. `_build()`: `add_weak_point(&"forearm", &"forearm_ur", 0.9)` etc. (weak points follow sockets; `visual.add_socket()` makes new ones).
5. `_first_state()` returns the opening state; write `_enter_state/_tick_state/_exit_state` using `face_towards`, `walk_towards`,
   `halt`, `arena.telegraph_circle/cone/ring`, `hit_circle/hit_cone` (opts: blockable, guard_break, petrify, knockback, reflect),
   `expose/close_weak`, `enraged()`. Numbers from `Tuning.<ID>`. Play clips with `visual.play(clip, blend, speed)`; stretch speed
   with `visual.clip_length(clip, fallback) / wanted_seconds`; read impact times with `visual.event_time(clip, &"impact", fallback)`.
   Play `<boss_id>_<attack>_warn` / `<boss_id>_<attack>` sounds yourself (docs/audio_list.json); the telegraphs are silent.
   take_weak_hit already plays `<boss_id>_hurt`, a flash and the `hurt` clip, then resumes the clip that was playing (same
   state only, at speed 1). Set `hurt_clip = &""` to switch it off, or play your own clip in `_on_weak_hit()`.
   On death BossBase calls `_exit_state(old)` then `_enter_state(&"dead")`: clean up beams/fire/decals/loops in `_exit_state`.
6. Override `bot_advice()` so `--bot=win` can beat it, and `get_lock_point()` if the head socket is not a good aim point.
7. Test: `Godot --headless --path game -- --start=<id> --harness --bot=win --quit-after=300 --speed=3`. `scripts/test/dummy_boss.gd`
   is a complete small example (sweep, tracked slam, stuck weak point, bot advice).

## Public classes and files (all core-owned)
| Class / autoload | File | Role |
|---|---|---|
| `Game` (autoload) | scripts/autoload/game.gd | args, `goto(id, opts)` with fade (a request during a fade is queued, latest wins), `restart_scene()`, `register_scene(id, path)`, `builder_path(id)`, `is_switching()`, progress/save (`defeated`, `ending_seen`, `ending_pending()`, `mark_ending_seen()`), pause (`set_paused`, `release_gameplay_buttons()`), `hit_pause`, `shake`, `event()` harness lines, `rng` + `seed_used` |
| `Controls` (autoload) | scripts/autoload/controls.gd | device tracking + `device_changed`, `key/tag/fill` prompts, `get_move/get_look_stick` (dead zone 0.2), menu repeat, `rumble`, pad A/B added to ui_accept/ui_cancel |
| `Sfx` (autoload) | scripts/autoload/sfx.gd | `play(name, pos?, volume_db, pitch)` from assets/audio/sfx/<name>.(ogg/wav/mp3), silent if missing; `play_music(name)` from assets/audio/music/; names = docs/audio_list.json, `ALIASES` maps old names |
| `Tuning` | scripts/data/tuning.gd | every SPEC §2-§4 number, `CHARS`, `ISLANDS`, `ISLAND_TITLES` |
| `CharacterVisual` | scripts/visual/character_visual.gd | GLB or stand-in; `create`, `create_from_file`, `play`, `has_clip`, `clip_length`, `event_time`, `socket`, `add_socket`, `attach_prop`, `flash`, `set_petrified`, `set_tint`, `model_top` (real-bounds height, rest pose, props excluded), `make_toon`, `outline_width_for`, `offset_transform` |
| `StandIn` | scripts/visual/standin.gd | grey-box bodies (humanoid / four arms, serpent, hydra, horse) with sockets + procedural pose |
| `Telegraph` | scripts/visual/telegraph.gd | ground decals `circle/cone/ring`, `aim`, `time_left`, `cancel`, `set_colors(fill, edge?)`; render priority -10 so any VFX draws on top (ArenaBase.telegraph_* now return `Telegraph`) |
| `EnvKit` | scripts/visual/env_kit.gd | `sun`, `sky`, `floor_disc`, `sea`, `boundary`, `column`, `rock`, `prop` (props.json collision incl. `collision_parts`) |
| `Player` | scripts/player/player.gd | SPEC §2 hero; `try_hit` (opts incl. `dot`: damage-over-time tick), `is_blocking_towards`, `set_control`, `set_lock_target`, `lock_point`, `reset_health`; signals died, health_changed, state_changed, lock_changed |
| `PlayerCamera` | scripts/player/player_camera.gd | SpringArm chase cam, lock framing (feet above the boss bar, boss top from `frame_top()` in frame, arm grows up to +3.5 m), free orbit + recenter, `shake`, `snap_behind`; bodies in group `camera_ignore` never push it |
| `WeakPoint` | scripts/combat/weak_point.gd | layer 5 Area3D, `open/close/strike`, orange glow + ink rim while exposed (`MARK_COLOR`); the HUD draws a ring + arrow over it |
| `SwordHitbox` | scripts/combat/sword_hitbox.gd | layer 4, strike exposed weak points once per swing, else glance (spark + `Sfx glance`) |
| `Fx` | scripts/combat/fx.gd | `spark`, `dust` |
| `BossBase` | scripts/bosses/boss_base.gd | SPEC §7.1 API + helpers (`forward`, `angle_to_pos`, `player_distance`, `walk_towards`, `halt`, `is_exposed`, `stop_fight`, `frame_top`, `_first_state`, `_build`, `_on_weak_hit`) |
| `ArenaBase` | scripts/world/arena_base.gd | SPEC §7.1 API + flow (title card, lock-on, LABOR COMPLETE -> sea / ending, DEFEATED -> rebuild) |
| `Hud` | scripts/ui/hud.gd | health, boss bar, reticle, `show_prompt("{interact} Mount")`, `show_title_card`, `show_overlay`, `show_message`, `set_health_visible`, `bottom_band_fraction`; group `hud` |
| `UiStyle`, `ControlsPage` | scripts/ui/ui_style.gd, controls_page.gd | look helpers (panel, label, button, Greek key, Bar), controls table |
| (scripts) | scripts/ui/title_screen.gd, pause_menu.gd, ending_card.gd, missing_scene.gd | scene id title, the fallback ending card, pause menu, "not built yet" page |
| (scripts) | scripts/test/harness.gd, bot.gd, dummy_boss.gd (`DummyBoss`), test_arena.gd, travel_test.gd | SPEC §7.2 harness, bot, regression fight (scene id `test`), advisor/travel regression (scene id `test_travel`) |
| shaders | shaders/toon, outline, water, sky, telegraph .gdshader | cel look, ink hull, sea, painted sky, decals |
`project.godot` is generated by `work/core/gen_project.py` (input map, layers, autoloads); edit the script and re-run it.

## Conventions other modules rely on
- Everything faces +Z (characters, bosses, props); feet on y = 0; arena floors at y = 0.
- Scene builders: any Node script; `setup(opts)` is called before it enters the tree. Control scenes must use
  `set_anchors_and_offsets_preset(PRESET_FULL_RECT)` (plain `set_anchors_preset` keeps zero offsets -> size 0).
- Harness events: `Game.event("name", {k = v})` prints `[H] t=.. event=name k=v` only in harness runs.
- socket_offsets in `<id>_clips.json`: default `"offset_space": "blender"` = loc + XYZ Euler of the prop relative to its bone as
  read in Blender (the rig agents' rig.json). Verified with the real hercules export + sword/shield: matches split_sheet.png.
  Use `"offset_space": "godot"` for offsets measured in Godot.
- Stand-in clip lengths: `CharacterVisual.STANDIN_CLIPS`; real clips: manifest length, else the animation length.
- The player is invulnerable while petrified (otherwise a 1 s gaze beam would keep hitting a statue).
- `knockback` in try_hit opts = metres slid, decaying over the flinch.

## Scene flow agreed for the world module (ending, sounds, mouse)
- `ending` is a SCENE ID. Its builder is `res://scripts/world/ending.gd` when that file exists, else core's
  `scripts/ui/ending_card.gd` (BUILDERS lists candidates; the first that exists wins).
- ArenaBase sends a victory to `sea` {from = <id>}, except when `Game.ending_pending()` (all three beaten, card not yet
  seen): then to `ending` {from = <id>}. The ending builder shows the card, calls `Game.mark_ending_seen()` (saved), then
  `Game.goto(&"sea", {from = "hydra", free_flight = true})`. The sea shows the card "once" by routing: in `sea_world._ready()`
  call `Game.goto(&"ending")` when `Game.ending_pending()` (covers `--start=sea --defeated=all`). Do not draw a second card in the sea.
- Music: `music_title` (title and the core ending card), `music_flight` (sea: world plays it), `music_<island id>` (ArenaBase).
- Home and sea must call `Game.capture_mouse(true)` in `_ready()` and implement `wants_mouse_captured() -> bool` (Game
  re-captures after the pause menu). Harness runs never capture.
- Poll `interact` with `Input.is_action_just_pressed` as usual: Game releases every gameplay button on resume and on scene
  change, and the pause menu closes on the B RELEASE, so menu presses never leak into the game.

## Gotchas for module authors
- `arena.telegraph_*` return `Telegraph` (SPEC says Node3D; Telegraph extends Node3D): call `aim()`, `cancel()`, move it.
- `hit_circle` / `hit_cone` default to `blockable = true` and test the shield arc against the CENTRE of the circle / the cone
  origin. Stomps, rings and anything from behind or around the player must pass `blockable = false`.
- The default `get_lock_point()` uses socket `head` (real models; stand-ins use `lock_height`). Hydra must override it
  (its socket is `head_c`); any boss whose head is far from the body centre should too.
- Sword reach: the sword box spans y 0.1-2.9 m above the hero's feet and about 0.2-2.2 m in front of the hero's centre. An exposed weak
  point must come within about 2.9 m + its radius of the floor to be hittable (Medusa's neck during the gaze: give the
  `neck` weak point a low socket or a radius big enough, or only count the exposed side once the head is down).
- `CharacterVisual.play()` on a clip that is already playing restarts it from 0 (no cross-fade with itself).
- Without a manifest entry, a real clip loops when the stand-in table says so (idle, walk, run, stuck, fly, ...). Exact clip
  names win over decorated ones; "block_idle" never stands in for "idle".
- `EnvKit.prop()` warns once (push_warning + `[H] event=missing_prop`) for a name with neither a GLB nor a props.json entry.
- New scene ids: add them to `Game.BUILDERS` via a core request, or call `Game.register_scene(id, path)` before `goto(id)`.

## Decisions taken with the owner away
- Walking with the shield raised: 2.2 m/s (`Tuning.BLOCK_MOVE_SPEED`); SPEC gives no number.
- attack_2 chains from 0.40 s into attack_1 when the press was buffered; a press counts from 0.05 s (ATTACK_CHAIN_FROM -
  ATTACK_BUFFER) on, earlier presses are ignored; a roll can cancel an attack after its active window.
- Sounds with no registry entry: guard break = `block` at pitch 0.7, +2 dB; the dummy uses the cyclops sounds via ALIASES;
  the generic telegraph sound is gone (modules play `<id>_<attack>_warn`). `title_card` plays with the island card.
- The pause menu closes on the B release (Start / Esc still close on press).
- Free camera eases back behind the hero after 1 s without camera input while running, except when running at the camera
  (> 120 degrees off), so the hero's front can still be seen in free mode if the player turns the camera: lock-on is the default in fights.
- Pause "Quit" returns to the title (the title has the real Quit).
- Title subtitle "Three labors beyond the wine-dark sea" (classical epithet, original line).

## Known gaps
- No footstep sounds yet (`step_dirt` / `step_stone` exist in the registry).
- The hurt-clip resume replays the previous clip at speed 1 from its start (fine for loops like stuck / stunned / head_down).
- `--keys` presses the camera actions directly (no synthetic mouse motion).
- strafe_r falls back to strafe_l (no runtime mirroring of the clip yet; the art track could export strafe_r baked).
- Real-model clip cross-fades use AnimationPlayer blends only (no AnimationTree, no upper/lower body layering).
- Outline is an inverted hull: hard-edged meshes (stand-in boxes) show small gaps at corners.
- Telegraph decals are flat quads at y + 0.04: on uneven ground modules should place them at the local floor height.
- No settings menu (sensitivity, volume, invert-Y); no rebinding.
- Builds: export presets are not part of core yet; whoever exports must include `*.json` (props.json, *_clips.json) in the
  export filter, since they are read with FileAccess.
- The real hercules GLB is not in game/assets yet; the probe used art_src/chars/hercules/export/hercules.glb via
  `CharacterVisual.create_from_file` (work/core/probe/probe_visual.gd).
