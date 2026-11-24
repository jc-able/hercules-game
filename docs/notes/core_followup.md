# Core follow-up (core follow-up agent, 2026-11-22)

Every request for core in docs/notes/cyclops.md, medusa.md, hydra.md and world.md, with what was done. The owner was
away: decisions are marked **Decision** with the reason. Sound requests belong to the audio agent (skipped).

## Checklist
| # | From | Request | Status |
|---|---|---|---|
| C1 | cyclops req 1 | `Tuning.CYCLOPS`: engage_dist, engage_angle, approach_timeout, attack_anyway_dist, close_turn_dist, close_turn_deg, stall_time, slam_reach, lunge_speed, slam_rebound, step_interval, weak_radius, weak_line_y | **not moved (Decision)**, see below |
| C2 | cyclops req 2 | `Tuning.CHARS["cyclops"]` stand-in colours: skin lilac (0.66, 0.53, 0.68), red kilt (0.55, 0.14, 0.14) | done |
| C3 | cyclops req 3 | StandIn death falls backward (away from the hero); club pose (nice to have) | death done (`fall` key); club pose not done (the module's `club_holder` covers it) |
| M1 | medusa req 1 | `Tuning.MEDUSA`: tail_length 9.9 + the module keys | done |
| M2 | medusa req 2 | `Tuning.CHARS["medusa"]["tail"]` 9.9 | done (StandIn default also 9.9) |
| M3 | medusa req 3 / world req 2 | toon.gdshader light(): omni/spot lights light every pixel of their cluster tiles | done |
| M4 | medusa req 4 | negative telegraph render priority | done (-10) |
| M5 | medusa req 5 | stand-in hero not obviously stone-grey when petrified | done in the shader (not checked on screen) |
| M6 | medusa req 6 | `Telegraph.set_colors(fill, edge)` | done; medusa now uses it |
| M7 | medusa req 7 | audio files into game/assets/audio | skipped (audio agent) |
| H1 | hydra req 1 | `Tuning.HYDRA`: EXTRA keys + head_height 13.5, length 16.0 | done |
| H2 | hydra req 2 | `Tuning.CHARS["hydra"]`: length 16.0, head_height 13.0 | done |
| H3 | hydra req 3 | `Sfx.loop(name, pos)` | skipped (sfx.gd belongs to the audio agent; passed on here) |
| H4 | hydra req 4 | `Player.try_hit` opts `dot`; drop hydra's `_burn_player` hp write | done |
| H5 | hydra req 5 | lock camera: hero's feet above the boss bar | done (camera framing + bar 12 px lower) |
| H6 | hydra req 6 | StandIn hydra head_down: centre head hides the hero | done (head lies on the ground) |
| W1 | world req 1 | `Hud.set_health_visible(on)` | done; island_proxy uses it |
| W2 | world req 2 | = M3 | done |
| S1 | SPEC §10 | camera frames a 14.4 m Hydra and an 8 m Cyclops from right behind the hero, from the model's real bounds | done |

## What changed (core files)
- `scripts/data/tuning.gd`: MEDUSA tail_length 9.9 + 13 module keys; HYDRA head_height 13.5, length 16.0 + all 30 EXTRA
  keys of hydra.gd; CHARS cyclops colours, medusa tail 9.9, hydra length 16 / head_height 13, new `fall` key
  (hercules forward, cyclops + dummy back, others side); camera constants `CAM_LOCK_MAX_EXTRA` 3.5,
  `CAM_LOCK_FEET_MARGIN` 0.025, `CAM_LOCK_TOP_FRAC` 0.96.
- `shaders/toon.gdshader`: `light()` bands only the directional light (ATTENUATION = its shadow, as before). Omni/spot:
  `LIGHT_COLOR * ATTENUATION * (0.25 + 0.75 * smoothstep(0, 0.6, N.L)) / PI`, no band floor, so the light ends at its
  range and the cluster tiles are gone. Modules may use OmniLight3D again (hydra already has three: fire, throat, bite).
  Petrify: stone colour cooler (0.66, 0.67, 0.70; was warm 0.63, 0.61, 0.57, close to the tan stand-in skin) and the
  warm rim light drops 60 % while petrified.
- `scripts/visual/telegraph.gd`: `set_colors(fill, edge = null) -> Telegraph`; `RENDER_PRIORITY = -10` (was 10): any
  transparent VFX at the default priority 0 now draws over the decals. Medusa's VFX at 12 still do. Floors are opaque, so
  the decals still show on them (checked: no transparent floor overlay in any arena).
- `scripts/player/player.gd`: `try_hit` opts `dot = true` -> `_dot_tick`: dodged by the roll window, the petrify state
  and the 1.0 s after a petrify (`_iframe_until`), NOT by the 0.8 s after a hit (now `_hit_iframe_until`); blockable only
  if opts.blockable (default true, hydra passes false); no flinch, no knockback, no new i-frames, orange flash, soft
  `hurt` (-4 dB, pitch 1.15), small rumble, `player_hit ... dot=true`; at 0 hp the hero dies.
- `scripts/player/player_camera.gd`: lock framing (below). Harness flag `--cam-debug` prints `event=cam_frame` once a
  second while locked (arm, camera distance, top, limits, axis, band).
- `scripts/ui/hud.gd`: `set_health_visible(on)` (works before `_ready` too), `bottom_band_fraction()` (screen share under
  the top of the boss band), Hud joins group `hud`; the boss box sits 12 px lower (offset_top -108, bottom -28).
- `scripts/visual/character_visual.gd`: `model_top()` (rest-pose mesh bounds measured at creation: props and module
  meshes added later are not counted) and `model_top_points()` (up to 36 vertices spread over the top 15 % of the height,
  read once from the vertex arrays). Stand-in death follows `CHARS[id].fall`. Stand-in head_down/low/drop/rise poses add
  `head_c_dip` 0.15 rad (`HEAD_C_DIP`) to the hydra's centre neck.
- `scripts/visual/standin.gd`: `head_c_dip` pose key (hydra centre neck only); serpent tail default 9.9.
- `scripts/bosses/boss_base.gd`: `frame_top()` and `frame_top_points()` (world).

## Lock framing (SPEC §5 + §10) — Decision
The camera stays on the boss->hero line, right behind the hero, at CAM_HEIGHT 2.4 m above his feet. Two limits on the
view axis elevation, both from the camera's actual position:
1. highest: the hero's feet stay `CAM_LOCK_FEET_MARGIN` (2.5 % of the screen) above the top of the HUD boss band
   (`Hud.bottom_band_fraction`, 0.106 at 1280x720). Applied again after smoothing, so the feet never slip under the bar.
2. lowest: every point of `boss.frame_top_points()` stays below 96 % of the screen height.
The aim between hero and lock point (old weighting) is clamped into [lowest, highest]. When lowest > highest the arm
grows in 0.25 m steps up to 6.5 + 3.5 = 10 m (smoothed, rate 3.5/s, same camera height) until both fit; past that the
feet win. No FOV change. Why: SPEC asks for both "camera right behind" and "frame a 14 m Hydra"; from 6.5 m a 14.4 m top
and the hero's feet do not fit in a 70 degree frame once the hero is within ~12 m, so the distance gives.
Measured (windowed, real rest-pose hydra GLB via `--hydra-glb`, 20 top points): guard at 7.5 m arm 7.3-7.7 m, jaw
strike 8.4-8.7 m, at the shoulder during the fire 8.7-9.2 m; whole beast in frame at the jaw strike; heads cut only
when the hero stands within ~3 m of the lock point (shoulder during the fire), feet above the bar in every frame
(`docs/devlog/media_inbox/core_followup/hydra_lock_framing_after.jpg`). Cyclops (8 m): the arm never grows (6.5 m).
First try used one top point above the lock point: the hydra's horn tips sit ahead of it and were cut (`..._before.jpg`);
fixed by sampling the real top vertices.

## Decisions taken with the owner away
- **C1 not moved**: cyclops.gd reads its 13 numbers from upper-case constants with no Tuning fallback. The brief for this
  pass moves module numbers into Tuning only when the module already reads Tuning with a fallback; adding unread keys
  would make two places for one number. When the cyclops owner reads e.g. `T.get("engage_dist", ENGAGE_DIST)`, core adds
  the keys under the names in cyclops.md request 1.
- Hydra and medusa fallback tables (`EXTRA`, `DEFAULTS`) stay in the modules (Tuning wins, values identical); their owners
  may delete them. medusa.gd line ~126 still forces tail_length from DEFAULTS: same 9.9 now, redundant.
- Fire ticks are damage-over-time: no knockback on any tick (request 4 says so), so `fire_knockback` is unused (kept in
  Tuning with a comment). Standing in the fire: 36 HP per pass; `--bot=lose` on the hydra now dies at 27.9 s (3 passes)
  instead of ~38 s.
- Damage-over-time is stopped by petrify i-frames as well as roll i-frames (a statue cannot burn, same rule as the gaze).
- Hydra stand-in head_down: the 0.15 rad extra dip puts the jaw ~0.9 m high, ~11.8 m ahead (the head lies on the floor,
  below the hero's eye line). 0 `jaw_fallback` events in the stand-in runs; the real model still uses its clip / fallback.
- Death falls: cyclops and the dummy fall backward (away from the hero and the chase camera), the hero forward (away from
  the camera behind him), medusa and the hydra keep the side topple (a backward fall swings a long tail/body through the floor).
- Boss bar moved 12 px lower instead of thinner (the name + bar keep their size).

## Module files edited (small edits required by the core API changes)
1. `game/scripts/bosses/hydra.gd` `_burn_player()`: now one `player.try_hit(fire_dmg, origin, {blockable = false, dot = true})`,
   reports `burn` for a landed tick. The direct `player.hp` write, its own flash/sound/rumble/event are gone.
2. `game/scripts/bosses/medusa.gd` `_tint_decal()`: calls `Telegraph.set_colors(fill, edge)` instead of reaching into the
   decal's quad material.
3. `game/scripts/world/island_proxy.gd` `hide_hud_health()`: calls `Hud.set_health_visible(false)`; the old `_hp_bar` path
   remains only as a fallback.

## Regression (headless unless noted; logs in work/core_followup/logs/, final pass = summary3.txt + summary4.txt)
| Run | Result |
|---|---|
| `--start=test --bot=win --speed=3`, seeds 11 / 4242 | victory 16.9 / 16.9 s, 0 hits |
| `--start=cyclops --bot=win --speed=3`, seeds 11 / 4242 | victory 39.4 / 35.1 s, 8 strikes, 0 hits |
| `--start=medusa --bot=win --speed=3`, seeds 11 / 4242 | victory 24.1 / 23.3 s, 6 strikes, 0 hits |
| `--start=hydra --bot=win --speed=3`, seeds 11 / 4242 | victory 86.5 / 86.6 s, 8 strikes, 0 hits, 0 jaw_fallback |
| `--start=cyclops --bot=lose --speed=3` | dies at 20.4 s, rebuilt, `fight_start` again, `result=defeat` |
| `--start=hydra --bot=lose --speed=3` | 9 fire ticks `dot=true` (12 each), the 9th kills at 27.9 s, `result=defeat` |
| `--start=home --bot=win --speed=3` | home -> sea -> cyclops arena, fight won |
| `--start=sea --defeated=cyclops --bot=win --speed=3` | sea -> medusa, fight won |
| `--start=test_travel --bot=win --speed=3` | test_travel -> test, victory |
| windowed `--start=hydra --bot=win --shots --cam-debug --hydra-glb=<real GLB>` (two runs: before and after the top-point fix) | framing above |
No SCRIPT ERROR / Parse Error in any log. Mid-way, runs printed `ERROR: Tween (bound to /root/Sfx): started with no
Tweeners.` from the audio agent's sfx.gd while it was being edited; gone in the final pass (only `Sfx: no sound` warnings remain).

## Open / for others
- Audio agent: `Sfx.loop(name, pos) -> Node` (hydra request 3); hydra.gd and hydra_arena.gd loop their own players.
- Cyclops owner: switch the 13 constants to a Tuning fallback (then core adds them, see C1).
- Petrify look: re-check on screen once the real hercules GLB is in (stand-in tan vs cool stone).
- `Hud.bottom_band_fraction()` reads 0.06 headless vs 0.106 windowed (headless viewport size); only the framing numbers in
  headless `--cam-debug` logs differ.
