# Core fixer after the play-test (core_fix, 2026-11-22; owner away, decisions marked **Decision**)

Scratch, probes, logs, shots: `work/core_fix/` (p_menu.gd probe, tools/runfights.sh, logs/, shots/sheet.jpg).
Devlog: `docs/devlog/media_inbox/core_fix/death_framing_title_after.jpg`.

## Findings
| Sev | Finding | Status / what changed |
|---|---|---|
| major | Death invisible (stood upright under DEFEATED, restart before the fall) | fixed: `Player._die()` plays `death` from clip 0.25 s at 1.6x (`Tuning.DEATH_CLIP_FROM/SPEED`): struck at once, on his knees ~0.9 s, props drop ~1.2 s (drop time converted to game time), flat ~2.2 s. `ArenaBase._on_player_died` holds `Tuning.DEFEAT_HOLD` 4.5 s (was 3.0; small edit in arena_base.gd). Shots: kneeling at +1.2 s, lying at +3.4 s |
| major | Hero framed small (30-34 %) | fixed (**Decision**: match the reference). `Tuning.CAM_LOCK_BY_BOSS` cyclops/medusa: arm 2.9 m, height 1.2 m, `cut_inside` 6 m (inside it the arm's growth fades out over `CAM_LOCK_CUT_RAMP` 1.5 m, so the top may be cut only when the hero is close). Hydra unchanged (3.7 m / 1.3 m / +3.0 m). Measured: arm 2.90-3.37 m in the cyclops fight, hero ~45-50 % of the frame |
| major | Weak-point marker = big opaque sphere over Medusa's eyes, reticle stacked on it | fixed: additive fresnel rim shader, alpha <= 0.35 (pulse 0.2-0.35), the dark inverted-hull shell is gone; the HUD diamond is hidden while a weak-point ring shows on the locked boss. Medusa socket move = request (qa_requests.md, medusa owner) |
| major | Title Controls page not modal for focus | fixed twice over: the title's menu buttons get FOCUS_NONE + mouse ignore while any page is open; ControlsPage's Back has itself as every focus neighbour / next / previous (pause menu too). Probe: up x3 + left on the page -> focus stays on Back |
| major x2 + minor | New game wipes progress with no confirmation | fixed: `Game.new_game_needs_confirm()` (save + a beaten boss or the ending seen) -> "START OVER? Your beaten labors will be forgotten." with Keep my progress (focused) / Start over; B / Esc / Start = keep; focus locked to the two buttons. Probe: B keeps `cyclops=true`; Start over -> home with all false |
| major | Focus loss does not pause | fixed: `Game._notification` APPLICATION_FOCUS_OUT -> `set_paused(true)` (not in harness, during a fade, on title/ending/missing); FOCUS_IN re-captures the mouse when no menu is open and the scene wants it. Probe (harness flag cleared around the notification): paused=true, menu shown |
| major | Mouse never captured after a scene change | fixed: `_switch()` frees the mouse BEFORE `add_child`. Windowed non-harness probe (work/qa_bugs/p_mouse.gd): `home loaded via goto: mouse=CAPTURED` (was VISIBLE) |
| minor | Quit leaks (ObjectDB / resources in use) | fixed: `Game.quit_game()` (pause, `Sfx.shutdown()`, 0.15 s, quit), used by the title Quit and the window close button (`set_auto_accept_quit(false)` + WM_CLOSE_REQUEST). Probe runs ending in quit_game print no leak lines |
| minor | Harness cannot run the campaign | done: title `bot_advice()` -> `{accept: true}` after 1 s; bot `accept` key (Enter with --keys, pad A with --pad, else InputEventAction ui_accept); harness `--campaign` (no victory ends the run, `[H] campaign scene=.. prev=.. prev_secs=..` per scene, result=victory 5 s after the free-flight sea) |
| minor | Boss bar low contrast | fixed: backing alpha 0.88 + 2 px light rim; `Bar.outlined` (dark outer line, brighter top highlight, dark bottom edge on the fill) |
| minor | Shield edge-on / sword hidden from behind | NOT changed: socket offsets live in `game/assets/characters/hercules/hercules_clips.json` (art track): request in qa_requests.md |
| minor | Title card over the boss | fixed: thin strip in the top ~12 % (title 56 px, sub 26 px, one small key band, plate alpha 0.4, x +-440 clear of the health panel) |
| minor | Title sky banding | fixed: the sky is a canvas shader (smooth gradient + triangular +-1 code value dither) instead of 24 drawn steps |
| minor | SPEC numbers out of date | done: SPEC §10.1 "Combat as built" table (speeds, sword windows, cyclops sweep, medusa ranges/tail "roll out", enraged windups, death, lock camera). Tail radius choice + hints = requests (medusa / world) |
| minor | Disabled Continue takes focus | fixed: FOCUS_NONE when disabled (probe: down from New game -> Controls) |
| minor | Hover and focus look the same | fixed: hover = slightly brighter fill, no gold frame; a real mouse move over a button moves the focus there (a cursor that just appears over a button does not) |
| minor | Held shield/boost dropped on resume | fixed: resume releases only the tap actions (`release_gameplay_buttons(true)`, HOLD_BUTTONS shield/boost kept). Probe: shield held through pause -> state stays `block` |
| minor | Pause-menu leave unpaused before the fade | fixed: `PauseMenu._leave()` hides + disables the menu and calls `Game.goto()` while paused; `_switch()` unpauses. Probe: 0.12 s after Restart fight paused=true, boss state_time delta 0.000 |

## Other core work in this pass
- Build fixer requests (qa_requests.md 1+2) applied in `work/core/gen_project.py`: `rendering/textures/vram_compression/import_etc2_astc=true`,
  `config/use_custom_user_dir=true`, `config/custom_user_dir_name="Hercules"` (saves now in `~/Library/Application Support/Hercules/`).
  project.godot was regenerated (it had been re-saved by the editor without default-valued keys; same settings).
  **The ETC2/ASTC re-import was NOT run**: it rewrites many imported textures while other fixers' Godot runs are live. Run it
  when nothing else is running: `until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock`.
- Harness-only `--fake-save`: `Game.has_save()` is true (title shows Continue, New game asks), nothing is written.

## Proof (headless --speed=3 unless noted; logs work/core_fix/logs/)
| Run | Result |
|---|---|
| test --bot=win seeds 11 / 4242 | victory 17.74 / 17.75 s |
| test --bot=lose | defeat, restarted, fight_start again (32.6 s with the 4.5 s hold) |
| test --bot=win --pad / --keys | victory / victory |
| --probe=ui / --probe=ui --pad | focus Resume, resumed, no roll |
| cyclops --bot=win seeds 11 / 4242 | victory 37.36 / 33.37 s |
| cyclops --bot=lose | death 20.04 s, defeat, restarted |
| medusa --bot=win seed 11 | victory 86.4 s, 6 strikes, 9 reflects (was ~27 s; medusa.gd was being edited by its fixer during this pass: one earlier run hit its mid-edit parse error) |
| title --bot=win --campaign seed 11 | victory in ONE run: title 1.2 s -> home 3.8 -> sea 16.1 -> cyclops 40.2 -> sea 28.2 -> medusa 30.5 -> sea 23.7 -> hydra 103.4 -> ending 3.2 -> free-flight sea, 0 script errors |
| probes p_menu.gd title_save / title_nosave / pause, windowed p_mouse.gd | as in the table above |
| windowed --shots (cyclops lose + win, title, card) | sheet `work/core_fix/shots/sheet.jpg` |

# Core fixer pass 2 (core_fix2, 2026-11-23; owner away, decisions marked **Decision**)
Scratch, probes, logs, shots: `work/core_fix2/` (tools/socket_probe.gd, tools/sheet.py, tools/runfights_a.sh / _b.sh,
logs/, shots*/, sheet_*.jpg). Devlog: `docs/devlog/media_inbox/core_fix2/` (death + props before/after).

| Item | What changed |
|---|---|
| Death presentation | `ArenaBase._on_player_died`: `hud.set_boss_visible(false)` at the blow (boss name/bar + reticle hidden; the lock camera keeps its framing because `bottom_band_fraction()` holds its last value), DEFEATED fades in after `Tuning.DEFEAT_OVERLAY_DELAY` 1.4 s **and** sits in the upper third (dim 0.18 instead of 0.35); hold still 4.5 s. `Hud.show_overlay(title, sub, seconds, color, delay := 0.0, upper := false)`, `Hud.set_boss_visible(on, keep_framing := true)`. **Decision:** both the delay and the upper third, plus the camera: `PlayerCamera` eases up `Tuning.CAM_DEATH_RAISE` 0.6 m over `CAM_DEATH_EASE` 1.0 s while `player.state == dead` and (locked) moves the aim `CAM_DEATH_AIM` 35 % onto the fallen hero. Shots: medusa mid-arena +2.4 s = hero lying in the lower middle, nothing over him; cyclops `--bot=lose` +3.6 s = hero clear, but the cyclops arena's low curb fills the bottom ~20 % when the hero dies at the rim (the camera is outside the curb; it was there before, under the old boss bar): request to the cyclops owner in qa_requests.md |
| Near fade | `near_fade_hide` / `near_fade_full` (0/0 = off, checked first so the cost is one branch) in toon.gdshader + outline.gdshader, same 4x4 Bayer dither on `length(VERTEX)` as cyclops's copy; `CharacterVisual.set_near_fade(hide_m, full_m, under := null)`. cyclops.gd: `_install_near_fade/_fade_material/_near_fade_shader/_fade_shaders` deleted, `_set_near_fade(n, h, f)` now calls `visual.set_near_fade(h, f, n)` (club drop fade unchanged). Club dither visible in the windowed cyclops shots |
| push_back | public `Player.push_back(from, dist, secs)` (wraps `_push_back`); hydra.gd calls it (`death_clear from=7.19 to=14.50` in both hydra wins) |
| block_since | `Player.block_since` (player clock when the state entered `block`, -1 otherwise) + `Player.clock()`; medusa.gd maps it onto its own clock in 3 lines (its `_was_blocking` var is now unused) |
| Hero props | socket_offsets in hercules_clips.json: shield +40 deg about the forearm, sword -25 deg about the hand Z; numbers and the **Decision** in integrate_player.md |
| Build settings | `import_etc2_astc=true` + custom user dir "Hercules" were already in gen_project.py / project.godot (pass 1); the **re-import ran now** under `work/.import_lock` (exit 0, no errors); one-line `--export-release "macOS"` to a scratch folder: exit 0, 231 MB, codesign valid, the exported binary wins `--start=test --bot=win --speed=3`. builds/ was not touched (the lead runs `zsh builds/make_app.sh`, route A now) |

## Proof (headless `--speed=3`; logs `work/core_fix2/logs/r_*.log` and `f_*.log`)
| Run | Result |
|---|---|
| test --bot=win seeds 11 / 4242 | victory 15.69 / 15.67 s |
| cyclops --bot=win seeds 11 / 4242 | victory 36.00 / 32.00 s, 8 strikes, 0 hits |
| medusa --bot=win seeds 11 / 4242 | victory 26.19 / 25.29 s, 6 strikes, 0 hits, 3 reflects (raised 0.43 s before the fire) |
| hydra --bot=win seeds 11 / 4242 | victory 100.12 / 100.08 s, 8 strikes, 0 hits, death_clear push 7.19 -> 14.50 m |
| cyclops --bot=lose | death 20.03 s, defeat, fight_start again 25.72 s |
| title --bot=win --campaign --pad seed 11 | victory: title 1.3 -> home 3.9 -> sea 16.1 -> cyclops 40.3 -> sea 28.1 -> medusa 30.5 -> sea 23.7 -> hydra 103.8 -> ending 3.2 -> sea |
| windowed: cyclops lose (death), medusa lose (death), cyclops win (props) | sheets above |
No SCRIPT ERROR / Parse Error / ERROR / WARNING in any log.
Final pass after the death-camera change (`f_*.log`): test --bot=win seed 11 victory 15.68 s; test --bot=lose and cyclops
--bot=lose seed 4242 die (26.04 / 20.02 s), restart, `result=defeat`; title --campaign --pad seed 4242 victory (cyclops 36.2,
medusa 30.4, hydra 102.1 s, ending, free-flight sea), 0 SCRIPT ERROR / ERROR / WARNING.
