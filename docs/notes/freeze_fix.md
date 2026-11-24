# First-use freeze fix (freeze_fix, 2026-11-23 09:20-10:20; owner at the Mac, decisions marked **Decision**)

Open item 10 of `final_check.md` §4 (the rest of it): a freeze of about 0.3-0.9 s the first time an effect appears in a fight.

## Files
- `game/scripts/world/arena_base.gd`: `prewarm(roots)` + `static prewarm_in(scene, roots, frames)` + `_warm_proxies()`,
  consts `WARM_FX_SCENE`, `WARM_FRAMES` (4), `WARM_SIZE` (4 mm), `WARM_DIST` (1.5 m); `_intro()` calls `prewarm([self])` right after
  the island title card is shown (not on a restart: the cache is already warm in the process).
- `game/assets/fx/warm_fx.tscn` (new, 8 materials, built by the tool below, materials embedded, one ext link to `shaders/telegraph.gdshader`).
- `tools/probes/freeze_probe.gd`, `tools/probes/fx_capture.gd`, `tools/probes/fx_warm_build.gd` (new) and 3 rows in `tools/probes/README.md`.
- No module script was changed. No import, no git. Scratch, logs, run scripts: `work/freeze_fix/` (`run_cold2.sh`, `chain.sh`, `spikes.py`, `logs/`).

## 1. Cause
**Every freeze is a GPU shader compiled at its first draw** (Metal), for materials that are built in code at the moment the effect
is used (or that sit hidden until then). No resource load, audio decode or node build came close: the frames show
`pipe(s,sp)` compiles and render-thread time, and `proc` stays at its normal 12-18 ms.

| Fight | Game time | Event | Shader compiled |
|---|---|---|---|
| cyclops | 4.86 | first sweep (shield up) | telegraph decal + sweep ribbon (unshaded, alpha, vertex colour, no cull) |
| cyclops | 5.42 / 5.69 | first block | `Fx.spark` (billboard, alpha, emission, texture) and `Fx.dust` |
| cyclops | 9.22 | first slam lands | slam ring (unshaded alpha), crack decal (unshaded, no cull), debris chunks (lit, shadow-casting CPU particles) |
| medusa | 5.77 | first gaze wind-up | gaze materials built hidden by the boss (scan of hidden geometry) + telegraph |
| medusa | 6.97 / 7.25 | first reflect, stun | reflect flash/burst (additive) + sparks + dust |
| hydra | 3.81 | first inhale | inhale floor ShaderMaterial + fire particles (hidden, built ahead) |
| hydra | 8.42 | first jaw hit | `Fx.spark` |
| hydra | 10.70 | first stomp | stomp ring (unshaded alpha) |

**The cold cache has two layers.** A new HOME empties Godot's `shader_cache` only. macOS keeps its own Metal compiler cache per
**bundle id** (`$(getconf DARWIN_USER_CACHE_DIR)/<bundle id>/com.apple.metal`). With only HOME cold, the same moments cost just 20-70 ms
(my first baseline, `logs/base_*.log`). A fresh export on the owner's Mac has both layers cold. So every A/B below runs fully cold:
A run script (scratch, not in this repo) clones `Godot_4.7.2.app` (APFS clone), gives it a new bundle id for every run, signs it ad hoc,
and runs it through `gdwin` (`GDWIN_BIN`) with a new HOME on the same command line. The owner's caches were not touched. Each run leaves a
small Metal cache folder named `com.hercules.freezefix.*` in the user cache dir. That is harmless, and macOS clears it.

## 2. Fix
**Decision:** one shared warm-up in `ArenaBase`. No module needs a call, because the base runs it for every arena:
- **Hidden and off-screen geometry**: every GeometryInstance3D under the arena, the boss's pre-built hidden effects included (beam,
  fire, weak-point glow, props behind the camera). One proxy is made per material not seen yet: a 4 mm quad 1.5 m in front of the camera, of the same kind
  (mesh / CPU particles / GPU particles + process material) and with the same shadow setting. It is drawn for 4 frames, then freed.
- **Effects built at use time**: `game/assets/fx/warm_fx.tscn`, one proxy per kind of shader, captured from bot runs.
- **The core effects through their own code**: `Fx.spark(holder, ..., 1 particle, 4 mm)` and `Fx.dust(...)`. The first capture
  merged two spark variants by mistake, so the real code path is the only safe one for the core effects.
- It touches no game state, no physics and no `Game.rng` (CPU particles use their own RNG). It is skipped headless, and
  `-- --no-prewarm` turns it off for an A/B.
- Where the cost went: the compiles now run in the first frames of the arena. Through `Game.goto` that frame is drawn while the fade is fully
  black (landing: 1655 ms on black instead of 253 ms, then 0 freezes in the fight). On a direct `--start=<boss>` it is part of the first frame
  (1.7-4.0 s -> 2.9-4.8 s). Once the cache is warm this is a few ms.
- Keeping it complete: after an effect gets a new kind of material (a new flag, texture or shader), run `fx_capture.gd` per fight
  (`--bot=win` and `--bot=lose`, one folder), then `fx_warm_build.gd` (`tools/probes/README.md`). If you forget, only that one effect's first-use freeze comes back.

## 3. Proof: fully cold (new HOME + new Metal bundle id), windowed 1920x1080 via gdwin, `--bot=win --seed=11`, speed 1
Frames over 50 ms from fight start (flight: from take-off) to the end. "load" = a frame with no compile in it. Those frames came from other jobs on
the machine (load average 15-17, other agents' Godot runs and my own parallel run). They appear in the before runs as well (`logs/base_hydra.log` t=27-31).

| Run | Before (`--no-prewarm`) | After |
|---|---|---|
| cyclops (victory 37.49 both) | **4**: 685 ms sweep 4.86, 418 ms block 5.42, 427 ms 5.69, 910 ms slam 9.22 | **0** |
| medusa (victory 26.15 / 26.14) | **4**: 52 ms fight_start (HUD canvas) 2.41, 400 ms gaze wind-up 5.77, 379 ms reflect 6.97, 362 ms 7.25 | **0** |
| hydra (victory 99.40 / 99.36) | **2**: 454 ms inhale 3.81, 416 ms first jaw hit 8.42 | **0** (run alone, 3.1; an earlier after-run beside the chain had 18 load frames of 50-107 ms, all with 0 compiles) |
| sea flight + landing + cyclops (fight_start 18.52 both) | flight 0-15 s: 0; landing switch 253 ms (on black); fight: 626 ms sweep, 362 ms block, 370 ms, 808 ms slam | flight: 0; landing switch 1655 ms + 90 ms (on black / fade-in); fight: **0** |

Frames with a surface-pipeline compile after the fight starts stay at 16-45 per fight in both runs. Every new spark, dust or ribbon material
instance counts as one, but each costs only 2-10 ms (the shader is already compiled). It is a counter, not a stall.

**Same fight**: boss-hit times, cyclops before / after: 10.83/10.83, 11.18/11.16, 18.74/18.73, 19.08/19.07, 27.33/27.33, 27.67/27.68,
37.18/37.19, 37.49/37.49. Hydra: 8.41/8.41, 20.13/20.10, 31.87/31.88, 43.61/43.62, victory 99.40/99.36. Medusa: 8.43, 8.79, 17.69,
18.06/18.05, 25.80/25.79. The differences are frame jitter (≤ 0.03 s).

### 3.1 Hydra rerun alone
`logs/cold_post3_hydra.log`, fully cold, with nothing else of mine running: **0 frames over 50 ms** from fight start to victory (99.45 s).

## 4. Regression (headless, speed 3, seed 11; the warm-up is skipped headless, so these runs only show that nothing broke)
| Run | Result |
|---|---|
| `--start=cyclops --bot=win` | victory 37.60 |
| `--start=medusa --bot=win` | victory 26.21 |
| `--start=hydra --bot=win` | victory 99.44 |
| `--start=title --bot=win --campaign --pad` | victory: cyclops 23.64 -> 58.02, medusa 94.63 -> 118.61, hydra 149.16 -> 246.20, `victories=3` |
No `SCRIPT ERROR`, `Parse Error`, `ERROR` or `WARNING` line in these runs or in the windowed after-runs.

## 5. Notes for the lead
- At the start of this task (09:35) `--bot=win` medusa did not win: 0 hits in 170 s, windowed and headless (`logs/hl_medusa_pre.log`). Another agent's
  medusa.gd/glb work was in progress. At 10:05 it won again (26.21 s headless, 26.14 s windowed). Not caused by this change: medusa.gd is untouched
  and the warm-up does not run headless.
- Left alone (under 50 ms): at `fight_start` one canvas pipeline compile (36-52 ms: the HUD boss bar appears). Music starts in the same frame.
- The big first frame on a cold machine (2.4-4.8 s at scene build, before this change too) is the whole scene's shaders. On the game path it is under the black
  fade; the exported app pays it once.
- Shader baker: still off (build.md 3.3). The warm-up does what it could not, because our materials are built in code.
