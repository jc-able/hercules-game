# Audio notes (audio agent, 2026-11-22)

Owner away: every choice below was taken by the audio agent and is noted here.

## What exists
- `game/assets/audio/sfx/<name>.wav` x57 (mono 44.1 kHz 16-bit) and `game/assets/audio/music/<name>.ogg` x5 (stereo Vorbis q5,
  ffmpeg@4), one per entry of `docs/audio_list.json`. Imported (QOA for the wavs, Godot default).
- `game/assets/audio/audio.json`: per sound `{file, bus, volume_db, pitch_random, loop, loop_offset (music), max_distance,
  unit_size, positional}`. Built by `tools/audio/process.py` (was work/audio/process.py; re-run it from the repo root
  after a regeneration, `python3 tools/audio/process.py <name> ...` rebuilds only those sounds, then
  `--import` under the lock). Numbers per file: `work/audio/processed.json`; raw measurements: `work/audio/measure.json`.
- `game/default_bus_layout.tres`: Master (AudioEffectHardLimiter, ceiling -0.5 dB) <- Music 0 dB, SFX -2 dB, UI 0 dB
  (SFX lowered after the first capture measured -13.2 LUFS; now -14.8). Sfx also builds the buses if the file is missing.
- `game/scripts/autoload/sfx.gd` rewritten (API in its header):
  - `play(name, pos = null, volume_db = 0.0, pitch = 1.0)` unchanged signature. Manifest volume + call volume. Positional
    sounds use a pool of 32 AudioStreamPlayer3D (listener = camera), the rest a pool of 16 AudioStreamPlayer. Same name
    within 30 ms = skipped (no stacked doubles). Pitch variation uses Sfx's own RNG (seeded gameplay randomness untouched).
  - `loop(name, at = null, volume_db = 0.0) -> int` (alias `play_loop`), `stop_loop(id, fade)`, `set_loop_volume(id, db)`,
    `move_loop(id, pos)`, `loop_node(id)`, `is_looping(id)`. `at`: Node3D = follows it and dies with it; other Node = 2D,
    dies with it; Vector3 = fixed point in the current scene; null = global. The manifest decides 2D vs 3D. Loops at a
    Vector3 / null created while a scene is being built are adopted by that scene and stop at the next scene change.
  - `music(name, fade = 1.0)` crossfade (2 players), `stop_music(fade)`, `play_music(name)` kept, `current_music()`.
    Music intros play once, then the stream wraps to `loop_offset`.
  - `set_bus_volume(bus, linear)` / `get_bus_volume(bus)`: hooks for a future settings page (core has none yet).
  - `shutdown()`: stops and drops every stream (see the harness edit below).
  - `--sfx-log`: `[H] event=sfx name=<name> [kind=loop|music]` per start + `[H] sfx_counts name:n,...` at exit.
  - Missing name/file: one push_warning + `[H] event=sfx_missing name=...`, never a crash.

## Processing (tools/audio/process.py, a copy of work/audio/process.py + the follow-up options)
Listening by numbers (I cannot hear): duration, head/tail silence (silencedetect -50 dB + 5 ms RMS envelopes), sample peak,
integrated loudness + true peak (ebur128), clipped samples, spectral balance (FFT bands), sub-40 Hz share.
- Every Mirelo file came out at exactly the requested length (no length flags). No file is fully silent.
- Sub-bass junk is common: glance 56 % of its energy below 40 Hz, step_stone 56 %, medusa_death 57 %, beacon_loop 76 %,
  hydra_fire_sweep_warn 43 %, lava_loop 33 %. Everything is high-passed at 30 Hz, small sounds at 60-220 Hz.
- One-shots: start where the 5 ms RMS first comes within 24 dB of the peak (10-12 dB for sword_hit, hydra_stomp_warn and
  thunder, whose quiet lead-ins would make them late), 3 ms pre-roll on a zero crossing, 2 ms fade-in, cut to the useful
  length, quadratic fade-out, peak -3 dBFS. Head silence after processing: 0-5 ms for every file.
- Levels: `volume_db` = category target - measured max 400 ms RMS (boss attacks -10..-12, warns -14, player -14..-21,
  footsteps -27, UI -19..-20, stings -12..-16, ambience mean RMS -20..-26). Transient-heavy sounds that needed more than
  +3 dB get a look-ahead limiter inside the file first (drive listed below); volume_db is capped at +8.
- Loops (hydra_fire, wind, sea, lava, fire, beacon): equal-power crossfade of the tail into the head, so the last sample
  continues into the first one; the limiter runs on a doubled copy so the wrap stays continuous. Godot loop flags are set
  in code (`_make_loop`: WAV loop_mode/loop_begin/loop_end, Ogg loop/loop_offset); the import files stay default.
- Music: leading silence trimmed, the loop region skips quiet/fading intros (kept as a once-only intro through
  `loop_offset`) and drops the fade-out ending, 3 s equal-power crossfade, gain to -16 LUFS (music_flight stops at -17.1
  LUFS to keep 1 dB of true-peak headroom), manifest volume_db -5 so the music sits under the effects.
- Seam check (numbers below): sample jump at the wrap / the 99th-percentile sample step (< 1 = no click), and the RMS of
  the 100 ms around the wrap against the 10th-90th percentile of all 100 ms windows (inside = no level jump). All loops pass
  on both measures; checked again on the decoded .ogg files for the music.

### Fixes made while processing (first pass; see "Follow-up pass" below for what changed with the regenerated takes)
- `hydra_fire_sweep_warn` (v1 only, gone in v2): 0.65 s of digital silence in the middle (0.86-1.52 s): spliced out with a 40 ms crossfade ->
  1.38 s of rumble rising into the furnace roar (the windup is 1.5 s).
- `ui_accept`: the raw file is a steady 294 Hz hum at -35 dBFS. Replaced by a stand-in built from the ui_move lyre pluck
  (root, +4, +7, +12 semitones, 35 ms apart = a short rolled chord). Regenerate (below).
- `cyclops_step`: 1 s of even rumble with no impact: low-passed at 500 Hz and shaped with a 0.16 s exponential decay into
  a thud.
- `sword_hit`: the first 0.54 s is low noise; the game file is the loud slash (0.54-0.99 s).
- `thunder`, `hydra_stomp_warn`: 0.62 s / 0.24 s quiet lead-ins cut so they land with the bolt / the decal.

### Levels per sound
| sound | raw s | raw peak dBFS / LUFS | game s | trim start s | max 400 ms RMS dBFS | volume_db | notes |
|---|---|---|---|---|---|---|---|
| sword_swing | 1.0 | -1.4 / -18.4 | 0.45 | 0.017 | -20.3 | 2.3 |  |
| sword_hit | 1.0 | -1.6 / -16.7 | 0.45 | 0.536 | -17.6 | 3.6 | limiter +1.9 dB; v1 kept (v2 rejected) |
| glance (v2) | 1.0 | -1.2 / -18.5 | 0.45 | 0.017 | -18.6 | 3.6 | HP 220 Hz + v1 ring (HP 1500, -6 dB), limiter +1.7 dB |
| roll | 1.0 | -17.6 / -34.5 | 0.7 | 0.0 | -20.1 | -0.9 |  |
| step_dirt | 1.0 | -15.1 / -35.0 | 0.28 | 0.0 | -23.3 | -3.7 |  |
| step_stone (v2) | 1.0 | -14.5 / -40.3 | 0.16 | 0.64 | -19.7 | -7.3 | 2nd of 3 steps (heel click) |
| shield_up | 1.0 | -3.3 / -25.4 | 0.7 | 0.017 | -23.8 | 3.8 | limiter +2.7 dB |
| block | 1.0 | -7.4 / -29.3 | 0.8 | 0.015 | -19.4 | 5.4 | limiter +3.0 dB |
| reflect | 2.0 | -9.7 / -20.5 | 1.6 | 0.002 | -14.8 | 0.8 |  |
| hurt (v2) | 1.0 | -1.7 / -16.1 | 0.4 | 0.017 | -15.8 | -0.2 | clean grunt, no limiter |
| death | 2.0 | -6.4 / -26.3 | 1.99 | 0.007 | -16.6 | 2.6 | limiter +4.2 dB |
| petrify | 2.0 | -1.1 / -27.5 | 1.6 | 0.037 | -21.1 | 6.1 | limiter +4.4 dB |
| cyclops_roar | 3.0 | -6.5 / -21.5 | 3.0 | 0.0 | -14.5 | 2.5 |  |
| cyclops_step (v2) | 1.0 | -2.5 / -15.8 | 0.4 | 0.016 | -17.9 | -1.1 | HP 35, decay 0.09 s keeps the 1st boom (no LP) |
| cyclops_sweep_warn | 1.0 | -16.5 / -31.5 | 0.7 | 0.0 | -17.4 | 3.4 | limiter +3.1 dB |
| cyclops_sweep | 1.0 | -12.9 / -34.7 | 0.6 | 0.0 | -17.0 | 5.0 | limiter +5.4 dB |
| cyclops_slam_warn | 2.0 | -0.2 / -17.3 | 1.5 | 0.002 | -15.2 | 1.2 |  |
| cyclops_slam | 2.0 | -1.0 / -21.6 | 1.6 | 0.027 | -19.4 | 8.0 | limiter +9.1 dB |
| cyclops_stuck | 3.0 | -0.9 / -27.6 | 2.98 | 0.017 | -17.4 | 2.4 | limiter +2.2 dB |
| cyclops_pull_free | 2.0 | -19.4 / -41.3 | 1.2 | 0.0 | -17.9 | 3.9 | limiter +2.8 dB |
| cyclops_hurt | 2.0 | -11.5 / -26.3 | 1.3 | 0.0 | -13.9 | 1.9 |  |
| cyclops_death | 4.0 | -2.2 / -16.3 | 3.98 | 0.016 | -9.8 | -1.2 |  |
| medusa_hiss | 3.0 | -0.5 / -12.7 | 3.0 | 0.0 | -17.7 | 0.7 |  |
| medusa_gaze_warn | 2.0 | -0.2 / -16.0 | 1.3 | 0.022 | -13.7 | -0.3 |  |
| medusa_gaze | 2.0 | -0.3 / -10.6 | 1.4 | 0.002 | -14.3 | 2.3 |  |
| medusa_stun | 2.0 | -6.3 / -22.7 | 1.6 | 0.0 | -14.6 | 2.6 | limiter +1.1 dB |
| medusa_tail_swipe_warn | 1.0 | -16.1 / -35.9 | 0.75 | 0.017 | -20.0 | 6.0 | limiter +6.7 dB |
| medusa_tail_swipe | 1.0 | -0.0 / -18.4 | 0.6 | 0.022 | -18.2 | 6.2 | limiter +5.6 dB |
| medusa_hurt | 2.0 | -0.2 / -13.7 | 1.3 | 0.001 | -14.7 | 2.7 |  |
| medusa_death | 4.0 | -0.2 / -16.2 | 3.97 | 0.027 | -14.4 | 3.4 | limiter +2.4 dB |
| hydra_roar | 3.0 | -0.0 / -14.3 | 3.0 | 0.0 | -13.6 | 2.6 |  |
| hydra_fire_sweep_warn (v2) | 2.0 | -3.5 / -22.7 | 1.6 | 0.016 | -16.4 | 2.4 | no gap (no splice), limiter +1.6 dB |
| hydra_fire (loop) | 3.0 | -7.7 / -26.5 | 2.5 | - | -16.3 mean | 2.3 | limiter +1.7 dB; seam jump 0.61 x p99, seam RMS -25.3 (p10..p90 -27.0..-12.6) |
| hydra_head_down | 2.0 | -0.1 / -22.0 | 1.6 | 0.002 | -16.3 | 3.3 | limiter +2.0 dB |
| hydra_stomp_warn | 1.0 | 0.0 / -13.3 | 0.76 | 0.241 | -12.3 | -1.7 | 20 clipped raw samples (cut away) |
| hydra_stomp | 2.0 | -1.1 / -16.8 | 1.8 | 0.032 | -12.8 | 2.8 |  |
| hydra_bite_warn | 1.0 | -11.8 / -31.5 | 0.8 | 0.0 | -15.5 | 1.5 |  |
| hydra_bite (v2) | 1.0 | -5.4 / -25.8 | 0.4 | 0.536 | -19.2 | 7.2 | starts on the jaw snap; limiter +10 dB, reaches its target now |
| hydra_hurt | 2.0 | -2.9 / -18.3 | 1.3 | 0.0 | -14.8 | 2.8 | limiter +3.5 dB |
| hydra_death | 4.0 | -3.9 / -27.3 | 3.99 | 0.002 | -13.9 | 2.9 | limiter +7.4 dB |
| wing_flap | 1.0 | -9.9 / -24.2 | 0.8 | 0.017 | -15.4 | -4.6 |  |
| neigh | 2.0 | -20.7 / -39.3 | 2.0 | 0.0 | -18.9 | 2.9 | limiter +1.7 dB |
| mount | 1.0 | -4.2 / -27.7 | 0.9 | 0.021 | -21.7 | 3.7 | limiter +2.0 dB |
| land | 1.0 | -7.0 / -29.2 | 0.98 | 0.017 | -19.5 | 3.5 | limiter +5.0 dB |
| wind_loop | 6.0 | -1.6 / -17.1 | 5.2 | - | -17.9 mean | -2.1 | seam jump 0.07 x p99, RMS -22.6 (p10..p90 -24.5..-15.2) |
| sea_loop | 6.0 | -1.4 / -18.6 | 5.2 | - | -20.9 mean | -5.1 | seam jump 0.50 x p99, RMS -24.9 (-26.5..-16.5) |
| lava_loop | 6.0 | -0.3 / -18.7 | 5.2 | - | -21.2 mean | -2.8 | seam jump 0.02 x p99, RMS -31.3 (-40.8..-15.9) |
| fire_loop (v2 + v1) | 4.0 | -0.1 / -14.4 | 2.3 | - | -24.3 mean | 2.3 | v2 roar 0.1-2.9 s (level flattened, HP 60) + v1 crackle (HP 1500) -10 dB; limiter +4.6 dB; seam jump 0.53 x p99, RMS -24.4 (-25.6..-23.4) |
| beacon_loop | 4.0 | -1.4 / -22.3 | 3.4 | - | -16.5 mean | -7.5 | HP 60 Hz; seam jump 0.49 x p99, RMS -18.7 (-19.9..-14.0) |
| thunder | 3.0 | -0.7 / -13.6 | 2.38 | 0.62 | -14.9 | 2.9 | 3D unit 90 m, max 900 m (bolts are 50-130 m up, up to 400 m away) |
| ui_move | 1.0 | 0.0 / -17.7 | 0.3 | 0.017 | -16.4 | -3.6 | 13 clipped raw samples |
| ui_accept (v2 ping) | 1.0 | -5.9 / -30.5 | 0.38 | - | -18.0 | -1.0 | ui_move chord + the v2 2.76 kHz ping (HP 1000, 0 dB) |
| ui_back | 1.0 | -23.2 / -46.5 | 0.6 | 0.012 | -21.9 | 1.9 |  |
| victory | 4.0 | -3.8 / -18.3 | 3.98 | 0.016 | -13.6 | 1.6 |  |
| defeat | 3.0 | -11.7 / -27.0 | 3.0 | 0.002 | -13.1 | -0.9 |  |
| title_card | 2.0 | -3.7 / -19.3 | 1.98 | 0.017 | -12.1 | 0.1 |  |
| trophy (v2) | 2.0 | -25.1 / -42.7 | 1.98 | 0.017 | -18.9 | 2.9 | HP 1500, chimes at 0 / 0.8 s + 1 s ring, limiter +3.6 dB |

| music | raw | loop | game length | level | seam (decoded ogg) |
|---|---|---|---|---|---|
| music_title | 75.05 s, -12.7 LUFS | whole track to 72.5 s (fade-out dropped), loop_offset 0 | 69.5 s | -16.0 LUFS, TP -3.4 | jump 0.82 x p99, RMS -21.6 (p10..p90 -23.7..-17.5) |
| music_flight | 75.05 s, -17.3 LUFS | 2.25 s silence cut; intro 9.75 s once; loop 12.0-71.0 s of the raw | 65.75 s | -17.1 LUFS, TP -1.0 | jump 0.78 x p99, RMS -20.1 (-39.4..-18.4) |
| music_cyclops | 89.99 s, -12.4 LUFS | 0-89.5 s, loop_offset 0 | 86.5 s | -16.1 LUFS, TP -3.3 | jump 0.48 x p99, RMS -16.5 (-24.1..-18.0: a loud bar, no jump) |
| music_medusa | 90.04 s, -13.5 LUFS | 0.1-79.0 s (12 s decay ending dropped) | 75.9 s | -16.0 LUFS, TP -2.0 | jump 0.19 x p99, RMS -19.3 (-22.4..-16.4) |
| music_hydra | 90.04 s, -11.8 LUFS | 0.65 s silence cut; 1.85 s fade-in once; loop 2.5-90.0 s | 86.35 s | -16.1 LUFS, TP -4.3 | jump 0.74 x p99, RMS -20.4 (-29.4..-19.1) |

## Wiring (where each sound plays)
Player: step_dirt / step_stone (new, player.gd `_footsteps`, two per locomotion clip cycle, stone only in `medusa`), roll,
sword_swing, sword_hit, glance, shield_up, block (+ guard break = block at pitch 0.7), reflect, hurt, petrify, death.
Bosses: every `<boss>_<attack>_warn` plays in the same frame as its ground decal (checked in cyclops.gd, medusa.gd,
hydra.gd; the files start within 5 ms, most warn files reach -6 dB of their peak within 20-60 ms); `<boss>_<attack>` on the
impact; `<boss>_hurt` / `_death` from BossBase; roars (cyclops opening/pull free/enrage, hydra opening/enrage), medusa_hiss
(stalk + gaze lock), medusa_stun, cyclops_stuck / pull_free, hydra_head_down, hydra_fire (loop for the whole sweep, moves
with the mouth), cyclops_step on the walk clip beat (new).
World: music_title (title, home, ending), music_flight (sea), music_<id> starts right after `boss.start_fight()` and
fades out (0.4 s) at the victory / defeat sting; sea_loop at home, sea, quarry and sanctuary; lava_loop at the volcano;
fire_loop at the 2 home braziers and the 4 sanctuary braziers (positional, 28 m); beacon_loop at the landing ring of each
open island (the pillar of light); wind_loop (volume follows speed) + wing_flap on Pegasus; mount, neigh, land; thunder in
the storm walls; trophy chime at the pedestals 1.6 s after arriving home with at least one trophy; title_card, victory,
defeat; ui_move / ui_accept / ui_back.

Audit (`grep -rn 'Sfx\.' game/scripts`): 78 calls, every name is in the manifest or ALIASES (dynamic `%s_hurt`, `%s_death`,
`music_<id>` resolve to registry names; the `test` arena uses music_cyclops and the cyclops sounds via ALIASES), and every
registry sound is used. Not heard in the bot runs (the bots never trigger them, code checked): glance, hydra_bite(_warn),
medusa_tail_swipe(_warn), thunder (needs the camera within 400 m of a storm wall), ui_accept in menus.

## Edits made in other scripts (only Sfx calls and the loop/footstep plumbing they need; no gameplay change)
- `scripts/bosses/hydra.gd`: `_fire_audio` is now an Sfx loop id; `Sfx.loop("hydra_fire", _head_pos())`,
  `Sfx.stop_loop(_fire_audio, 0.25)` in `_stop_fire`, `Sfx.move_loop(_fire_audio, mouth)`; removed `_loop_sound()`
  (its own AudioStreamPlayer3D).
- `scripts/world/hydra_arena.gd`: `_ambience()` = `Sfx.loop("lava_loop", self)` (was its own AudioStreamPlayer).
- `scripts/world/island_proxy.gd`: `make_loop()` is now a thin wrapper returning `Sfx.loop(sound, parent, volume_db)` (int
  id, offset from the manifest level; no caller left); `refresh()` starts `beacon_loop` on the landing ring while the island
  is open and stops it otherwise (`_beacon_sfx`).
- `scripts/world/pegasus_flight.gd`: `_wind` is an Sfx loop id (`Sfx.loop("wind_loop", self, -8.0)`), speed sets
  `Sfx.set_loop_volume(_wind, -12..+3 dB)`; wing_flap offset -14 -> -6 dB (the manifest now sets its level).
- `scripts/world/home_base.gd`: `Sfx.loop("sea_loop", self)`, `Sfx.loop("fire_loop", flame)` per brazier, trophy chime.
- `scripts/world/sea_world.gd`: `Sfx.loop("sea_loop", self, -5.0)`.
- `scripts/world/cyclops_arena.gd`, `medusa_arena.gd`: `Sfx.loop("sea_loop", self)` (medusa -3 dB) + medusa braziers
  `Sfx.loop("fire_loop", pos)`.
- `scripts/world/arena_base.gd`: music moved from `_ready` (now `Sfx.stop_music(1.0)`) to right after `boss.start_fight()`;
  `Sfx.stop_music(0.4)` before the defeat sting.
- `scripts/bosses/boss_base.gd`: `Sfx.stop_music(0.4)` before the victory sting.
- `scripts/bosses/cyclops.gd`: footstep timer uses `_step_beat()` = half the walk clip (fallback STEP_INTERVAL); `_step_t`
  is re-phased when the walk clip starts (optional `step` event in cyclops_clips.json, default half a beat).
- `scripts/player/player.gd`: `_footsteps(delta, inp)` called from `_tick_free` + `_step_t` var.
- `scripts/test/dummy_boss.gd`: dummy_sweep_warn / dummy_slam_warn with the decals, dummy_sweep on impact (ALIASES -> cyclops).
- `scripts/test/harness.gd` `_finish()`: pauses the tree, `Sfx.shutdown()`, waits 0.15 s real time, then quits. Without it
  every run ended with "4-6 ObjectDB instances leaked / resources still in use" (a stream playing at quit keeps its
  playback). `[H] result=` is still printed first.

## Proof runs (headless, `--sfx-log`, logs in work/audio/runs/)
- cyclops / medusa / hydra `--bot=win --speed=3`: victory, no SCRIPT ERROR / ERROR / WARNING. Counts e.g. cyclops:
  cyclops_sweep_warn 8 / cyclops_sweep 8 / cyclops_slam_warn 6 / cyclops_slam 7 / block 8 / sword_hit 8 / cyclops_hurt 8 /
  cyclops_step 4 / step_dirt 32; medusa: gaze_warn 3 / gaze 3 / reflect 3 / stun 3 / hurt 6 / fire_loop 4 / step_stone 22;
  hydra: fire_sweep_warn 8 / hydra_fire 8 / head_down 8 / stomp_warn 7 / stomp 7 / hurt 8.
- `--bot=lose`: hurt, petrify (medusa x3), death, defeat, music fades and restarts with the next fight.
- Movie Maker capture, windowed: `Godot --path game --write-movie <abs>/work/audio/movie/cyclops.avi --fixed-fps 30 --
  --start=cyclops --harness --bot=win --quit-after=22 --sfx-log` (the movie path must be absolute: a relative one resolves
  inside game/ and fails with ERR_CANT_OPEN). Audio track 22.3 s, 48 kHz stereo: -14.8 LUFS integrated, sample peak
  -0.5 dBFS (the limiter ceiling, reached by 8 frames), 0 full-scale samples, per-second RMS -9..-17 dB (never silent).
  72 logged starts. Picture + markers: docs/devlog/media_inbox/audio/cyclops_fight_audio_track.jpg.
- home -> sea -> cyclops (`--bot=win --after-victory=1`), sea -> medusa, `--start=sea --defeated=all` (ending), home with
  `--defeated=cyclops` (trophy), `--probe=ui` (ui_move, ui_back): no errors.

## Regenerate (lead, Higgsfield) - better prompts
1. glance: "a single bright metallic clang of a bronze sword striking hard stone hide, high ringing ping and a short scrape,
   sparks, dry and close, impact at the very start, no low rumble, 0.6 seconds" (raw is 56 % sub-bass, centroid 43 Hz).
2. ui_accept: "a short bright plucked lyre chord, three notes rolled quickly upward with a tiny bronze bell ping, clean and
   dry, starts immediately, 0.5 seconds" (raw is a 294 Hz hum; a synthesized stand-in ships now).
3. hurt: "one short deep male grunt of pain as a warrior is struck, close microphone, loud and clear, starts immediately,
   no breathing after, 0.5 seconds" (raw -44 LUFS, no clear grunt).
4. trophy: "a loud sparkling magical chime, quick rising arpeggio of small bright bells with a warm shimmering tail,
   clearly audible from the start, 1.5 seconds" (raw -47 LUFS, the chime is 0.4 s).
5. cyclops_step: "one single enormous footstep, a heavy deep boom on packed earth at the very start, a little gravel
   scatter, then silence, 0.6 seconds" (raw is 1 s of even rumble; shaped by an envelope now).
6. sword_hit: "a sword slicing into thick monster hide, sharp wet slash and a heavy thud, impact at the very start,
   short, 0.4 seconds" (the slash is at 0.54 s of the raw).
7. fire_loop: "a close bronze brazier fire, dense steady crackling with a soft continuous roar of flames, even level,
   no pauses, seamless loop" (raw -36.6 LUFS, sparse crackles; +10 dB limiter + +8 dB volume now).
8. hydra_fire_sweep_warn: "a huge dragon inhaling deeply without pause for 1.5 seconds, continuous rumbling intake that
   rises steadily in pitch and loudness into a furnace roar, starts immediately" (raw had 0.65 s of silence in the middle).
9. step_stone: "a single leather sandal footstep on polished marble, crisp heel click and soft scuff, starts immediately,
   close, 0.25 seconds, no rumble" (raw -44 LUFS, 56 % sub-bass).
10. hydra_bite: "huge dragon jaws snapping shut, a loud sharp crack with a meaty bone crunch, impact at the very start,
    0.5 seconds" (only a transient: even after +10 dB limiting it is the quietest boss sound).
After a regeneration: put the mp3 in art_src/audio/raw/, `python3 tools/audio/process.py [names]`, then the locked `--import`.
All ten were regenerated on 2026-11-22: results in the next section.

## Follow-up pass (audio follow-up agent, 2026-11-22)
Owner away: choices below are mine. New raws in `art_src/audio/raw/`, first takes in `art_src/audio/raw_v1/`. Measured
both takes with the same tools (work/audio_followup/measure10.py, detail.py, peaks.py: 20 ms / 10 ms envelopes, centroid,
band shares, spectral peaks per segment). `tools/audio/process.py` gained `skip` (find the onset after N s), `layer`
(sum a second take onto a one-shot or loop), `region` + `agc` (loop part of a take, flatten its level drift) and the
names-only CLI. The one-shot repairs for the old takes are gone: the `splice_gap` setting (hydra_fire_sweep_warn), the
500 Hz low-pass + 0.16 s envelope on cyclops_step. The `ui_chord` stand-in stays, with the new ping on top.
| sound | new take, measured | decision |
|---|---|---|
| hurt | clean grunt 0.02-0.30 s, -16.1 LUFS (v1 -44.4) | v2, 0.4 s, no limiter needed |
| hydra_fire_sweep_warn | no gap, rises to its peak at 0.6 s then holds; sub-40 Hz 5 % (v1 43 %) | v2, 1.6 s, splice dropped |
| cyclops_step | real boom at 0.04 s, then more booms every ~0.2 s, 89 % < 100 Hz | v2, 0.4 s, decay 0.09 s keeps only the 1st boom (2nd one -20 dB) |
| hydra_bite | hiss 0-0.36 s, crack 0.38 s, jaw snap + crunch 0.54 s | v2 from the snap (skip 0.5, onset 12 dB); 4.8 dB louder in play than v1 |
| step_stone | 3 steps (0.02 / 0.64 / 0.95 s), centroid 624 Hz, no sub-bass (v1 56 %) | v2, the 0.64 s step (heel click), 0.16 s |
| trophy | 2 chimes (0.0 / 0.8 s, 5.3/8.4/9.4 kHz) + 1 s ring, -42.7 LUFS (v1 -47.4, one 11.9 kHz chime) | v2, HP 1500; still thin and high (see below) |
| glance | knock at 0.02 s (86-180 Hz) + noisy scrape; the bright part (0.7-1.0 s) is cut off by the file end; no ring | v2 knock + the 3.4 kHz ring of v1 (HP 1500, -6 dB) layered: 50 % of the energy 2-6 kHz, peak at 15 ms |
| ui_accept | only a 60 ms 2.76 kHz bell ping, no chord | ui_move chord stand-in kept + the v2 ping layered at 0 dB |
| fire_loop | loud low roar (84 % < 150 Hz), no crackle, fades out after 3.0 s | v2 roar 0.1-2.9 s + v1 crackle 10 dB under it; one 0.5 s crossfade -> 2.3 s loop (was 3.4 s); volume_db 8.0 -> 2.3 |
| sword_hit | low rumble 0-0.6 s, thud at 0.60 s, bright crack at 0.80 s, still loud when the file ends | **worse: v1 kept** (copied back to raw/; the v2 take is in `art_src/audio/raw_v2_rejected/sword_hit.mp3`) |
Checks on the game files (work/audio_followup/verify.py): every one-shot reaches -20 dB of its peak within 0-35 ms (hurt
10 ms, hydra_fire_sweep_warn 35 ms: an inhale), played level (max 400 ms RMS + volume_db) on its category target, end of
file >= 30 dB under the peak (fades). fire_loop seam: jump at the wrap 0.53 x the 99th-percentile step, 100 ms RMS over
two cycles -27.6..-22.5 dB (std 0.97 dB), wrap window -24.4 dB inside the p10..p90 band; centroid 767 Hz before the wrap,
363 Hz after (the crossfade blends it). Re-imported under the lock (only the changed wavs re-imported; 0 errors).
Waveforms before/after: docs/devlog/media_inbox/audio_followup/ten_sounds_before_after.jpg.
A full `process.py` run also re-encodes the five music .ogg files: same settings and numbers (LUFS, true peak, seam
match the table above), new bytes (Vorbis stream serials are random). Use the names-only form to avoid that churn.
Runs (headless, `--sfx-log`, logs in work/audio_followup/runs/), 0 SCRIPT ERROR / ERROR / sfx_missing:
- medusa `--bot=win --speed=3`: victory; step_stone 35, fire_loop 4 (braziers), sword_hit 6.
- hydra `--bot=win --speed=3`: victory; hydra_fire_sweep_warn 9, hydra_fire 9, sword_hit 8.
- cyclops `--bot=lose --speed=3`: defeat; cyclops_step 14, hurt 4, death 1.
- home `--defeated=cyclops`: trophy at t=1.60, fire_loop 2 (braziers).
- Not fired by any bot (code paths unchanged): glance, hydra_bite, ui_accept.
Still weak (for a later regeneration by the lead, optional):
- trophy: "a warm magical chime, a rising arpeggio of three bell notes in the middle register (around 1-2 kHz) with a soft
  shimmering tail, loud from the first note, 1.5 seconds" (both takes are only very high tones above 5 kHz).
- sword_hit: "a sword cutting into thick monster hide: a sharp wet slash at the very start followed at once by a short
  heavy thud, then silence, 0.4 seconds, no rumble before the hit".
- glance: "a sword glancing off hard stone-like hide: a bright metallic ring at the very start, ringing for half a second,
  no low thud, no rumble, 0.6 seconds".

## Open / for core
- No settings page yet: `Sfx.set_bus_volume("Music"|"SFX"|"UI"|"Master", 0..1)` is ready for one (persist it in core's save).
- Export: `assets/audio/audio.json` is read with FileAccess; include `*.json` in the export filter (core already notes this).
- A quit that does not go through the harness (`Godot --headless --path game --quit-after 2` = engine flag, title music
  playing) still prints "ObjectDB instances leaked / resources still in use" at exit: the AudioServer releases a playing
  stream only on its next mix step, and the engine flag quits in the same frame. No SCRIPT ERROR. Harness runs are clean
  (harness `_finish` waits 0.15 s after `Sfx.shutdown()`); a real build's Quit shows nothing to the player.
- My `--import` runs created `.uid` files next to the module scripts (cyclops.gd.uid, hydra_arena.gd.uid, ...): Godot
  writes them for every script; harmless, the lead decides whether to commit them.

## Play-test fix (audio fixer, 2026-11-22)
Owner away: choices below are mine.
- Finding (minor, lead): the hero played `step_dirt` on the Hydra's black basalt shelf. Fixed inside `sfx.gd` (no edit to
  player.gd, which belongs to core): `STEP_SURFACES` = {medusa: step_stone x1.0, hydra: step_stone x0.8}. Any footstep
  name (step_dirt / step_stone / aliases step, footstep) played in a listed scene becomes that sound at that pitch (the
  call's pitch is multiplied; manifest pitch_random still applies); other scenes keep the caller's choice. Pitch 0.8 =
  ~3.9 semitones under the marble heel click (0.16 s -> 0.20 s), heavier and duller rock. New helper `Sfx.footstep(pos,
  volume_db)` picks the surface by itself (player.gd may call it instead of choosing a name; optional, not requested).
- Proof (headless, `--sfx-log`, logs in work/audio_fix/runs/): hydra `--bot=win --speed=3` seeds 1 and 2: victory,
  step_stone 245, step_dirt 0; hydra `--bot=lose`: defeat; cyclops win: step_dirt 56 (unchanged); medusa win: step_stone.
  0 SCRIPT ERROR / ERROR / sfx_missing. Nothing visible changed, so no --shots sheet.
