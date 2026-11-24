# Final check 2: after the natural-animation pass (2026-11-23, about 11:14-11:30; owner at the Mac, not asked)

Role: final check agent (natural pass). Files I wrote:
- this note
- `docs/devlog/media_inbox/final_check2/` (5 strips + captions.txt)

Scratch, logs, movies, strips and run scripts are in `work/final_check2/`:
- `logs/`, `perf/`, `movie/`, `strips/`
- `run_cold.sh`, `cold_chain.sh`, `movie_chain.sh`, `lose_chain.sh`, `spikes.py`, `strip.py`
- `clip_motion_now.txt` / `.json`

**Decision: no code edits.** Every run below was clean, and I found no mechanical leftover worth touching while other agents
were editing. No GLB or clips json was edited. No import, no git. `builds/Hercules.app` and the owner's save folder were not
touched. Every rendering run went through `tools/godot_bg/gdwin` with a throwaway HOME. Headless runs after the first two
campaigns also used a throwaway HOME. Every process I started has ended.

## 1. Whole game, headless (`--speed=3 --seed=11 --harness`)
| Run | Result | Fights (fight_start -> victory, game s) | Notes |
|---|---|---|---|
| `--start=title --bot=win --campaign --keys` | victory, exit 0 | cyclops 35.16, medusa 23.98, hydra 97.08 | title -> home -> sea -> cyclops -> sea -> medusa -> sea -> hydra -> ending (3.2 s) -> free-flight sea. 22 strikes, **0 hits taken**, 8 blocks, 3 reflects, 3 glances |
| same with `--pad` | victory, exit 0 | cyclops 34.42, medusa 23.96, hydra 96.82 | same flow; 22 strikes, 0 hits taken, 4 glances |
| `--start=cyclops --bot=lose` | defeat, exit 1 | - | 4 hits, died 21.08, restart 25.75, fight_start again 26.76 |
| `--start=medusa --bot=lose` | defeat | - | 4 gaze hits, died 56.31, restart 61.07, fight_start again 62.08 |
| `--start=hydra --bot=lose` | defeat | - | fire burns, died 27.86, restart 32.54, fight_start again 33.55 |
| `--start=title --probe=ui` | quit, exit 0 | - | focus = New_game, backs out |
| `--start=cyclops --probe=ui --pad` | quit, exit 0 | - | pause opens with focus = Resume, B closes it (paused=false) |

No `SCRIPT ERROR`, `Parse Error`, `ERROR`, `WARNING` or missing-resource line appears in any of these logs. The same holds
for the 4 cold perf runs and the 8 movie runs. The one exception is a forced `--quit-after` exit (see §5, item 9).

Compared with this morning's check (`final_check.md`): the fights now take cyclops 35.2 s (was 33.7), medusa 24.0 s (24.0)
and hydra 97.1 s (99.0). Every result is the same.

## 2. Moving joints per clip (`python3 tools/clip_motion.py hercules cyclops medusa hydra pegasus`)
Before = `work/lead_natural/before/clip_motion.txt` (this morning). After = now, with the clip-fix GLBs of 11:04-11:11.
"x/N" = joints that turn >= 3 deg.

| id | clip | len before -> now | moving before -> now |
|---|---|---|---|
| hercules | idle | 3.50 -> **6.00** | 6 -> **23**/29 |
| hercules | run | 0.83 -> **0.67** | 19 -> 28 |
| hercules | strafe_l / strafe_r | 0.83 | 10 -> 21 |
| hercules | walk_back | 0.50 | 10 -> 21 |
| hercules | block_idle | 2.50 | 5 -> 19 |
| hercules | block_start / block_end | 0.25 / 0.25 -> **0.33** | 19 -> 20 |
| hercules | hit | 0.46 | 10 -> 19 |
| hercules | ride | 1.50 | 3 -> 9 (legs grip the saddle: frozen on purpose) |
| hercules | attack_1 / attack_2 / roll / death | same | 18->20 / 16->19 / 21->21 / 23->25 |
| cyclops | idle | 3.33 -> **6.00** | 9 -> **25**/29 |
| cyclops | walk | 1.42 | 13 -> **28** |
| cyclops | stuck / hurt | same | 11 -> 22 / 15 -> 22 |
| cyclops | sweep / slam / pull_free / death | same | 21->27 / 24->26 / 24->26 / 26->29 |
| medusa | idle | 3.00 -> **6.00** | 18 -> **33**/35 |
| medusa | slither | 2.00 -> **1.75** | 26 -> 34 |
| medusa | gaze / hurt / stunned | same | 17->30 / 15->30 / 13->28 |
| medusa | rise / stun_start / tail_swipe / death | same | 25->31 / 27->31 / 25->31 / 30->34 |
| hydra | idle | 3.00 -> **6.00** | **0 -> 43**/76 |
| hydra | walk | 2.17 | 24 -> **67** |
| hydra | walk_turn_l / walk_turn_r | new, 2.17 | 67 |
| hydra | stomp / stomp_r | 3.00 | 25 -> 64 |
| hydra | head_down / head_up | 1.50 | 25 -> 48 / 47 -> 53 |
| hydra | bite / bite_l / bite_r | 3.50 | 45 -> 62 / 43 -> 57 / 43 -> 57 |
| hydra | fire_sweep(_l), fire_sweep_return(_l) | same | 47 -> 61-62, 41-45 -> 54-56 |
| hydra | hurt / hurt_standing / death / death_standing | same | 39->55 / 51->59 / 63->71 / 60->69 |
| pegasus | idle | 7.00 -> **8.00** | 16 -> **39**/43 |
| pegasus | fly / glide | same | 28 -> 38 / 13 -> 38 |

Still frozen (by design, or acceptable):
- planted feet and toes, `root`, Pegasus `saddle`, hips and spine_01/02 (fly/glide: the rider and wing roots hang there);
- hydra `walk`: centre neck c_02..c_05 (head_c moves: the centre head stays level and looks ahead);
- hydra `head_down`: the centre neck and head (a held pose);
- hydra `idle`: the root joints of some side necks (their upper necks and all 9 heads move).

Every limb group the owner named (boss walks, every idle, the hero's start idle) now moves.

## 3. Cold-cache freeze table
Each run is FULLY cold: a new throwaway HOME plus a new bundle id on an APFS clone of Godot 4.7.2 (the Metal cache is per
bundle id; recipe from freeze_fix). Rendered through gdwin at 1920x1080 with `tools/probes/perf_probe.gd`, `--bot=win --seed=11`,
speed 1, one run at a time with nothing else of mine running.

| Run | Result | Frames | Frames > 50 ms after fight_start | Before the fight (scene build) |
|---|---|---|---|---|
| cyclops | victory 37.47 | 4668, avg 8.95 ms, p99 10.7 | **0** (worst 33 ms at fight_start) | first frame 2692 ms, then 150 ms |
| medusa | victory 26.13 | 3290, avg 9.35 ms, p99 10.9 | **1**: 58 ms at 2.42 = fight_start | 3124 ms, then 140 ms |
| hydra | victory 99.26 | 12092, avg 8.70 ms, p99 10.8 | **1**: 57 ms at 2.41 = fight_start | 4303 ms |
| sea flight -> cyclops landing (fight 18.51 -> 45 s) | timeout (as asked) | 5356 | **0**; flight 0-16 s: 0 | island switch 1665 ms on black + 61 ms at the fade-in |

The only remaining frame over 50 ms in a fight is the fight_start frame (57-58 ms) in medusa and hydra. freeze_fix measured
this as 36-52 ms: one canvas-pipeline compile when the HUD boss bar appears, with the music starting in the same frame. Every
effect's first use costs nothing now.

## 4. Recorded passes from the chase camera (gdwin, 1600x900 window, 30 fps movies, throwaway HOME)
Movies are in `work/final_check2/movie/`, strips in `work/final_check2/strips/`. Images read: 11, including 2 wasted on a wrong crop.

| Strip | What | Seen |
|---|---|---|
| `s1_home_idle.jpg` | `--start=home --bot=idle`, 0.5-6.5 s | Hero idle: sword angle and weight change across the 6 frames, no pop. From straight behind, the shield is edge-on (known). Pegasus: head turns and raises, wings folded, hooves planted |
| `s2_mount.jpg` + `s2c_mount_zoom.jpg` | mount: interact 1.02, seated 1.96, lift | The rider hops in and is on the saddle at 1.60. Wings open on the wing bones while the legs stay planted (1.60-1.75). The legs tuck from 2.05. From this camera the raised near wing hides the rider at 1.85-2.2 s (his shield shows through) |
| `s3_sea.jpg` | flight to the quarry ring and landing | Wing beats vary from frame to frame, the rider sits upright, no pop. The camera is tight at 0.5 s (wings out of frame) |
| `s4_cyclops.jpg` | walk-in, sweep, slam, strike, pull_free | The Cyclops walks in with the club up on his shoulder. He stands almost exactly behind the hero in the frame, so his gait is hard to read in 2.6-4.2 s. Slam, stuck strike and pull_free read well (dust) |
| `s5_medusa.jpg` | stalk, gaze windup, stun, stunned, rise, stalk | Arms differ left and right, snakes and tail alive. Stun clutch, floor slump and rise all read. No statue frames |
| `s6_hydra.jpg` | guard, inhale (glowing cracks), fire, head_down, head_up, stomp, bite, guard | The heads sit at different heights and angles in every frame, the centre head acts, and the rest follow. No frozen fan of heads |
| `s7_land.jpg` | free-flight landing at home | Pegasus glides in, flares and settles into the idle in 1.9 s. **But the hero already stands on the path at 6.3 s while Pegasus flies in riderless** (§5, item 2) |
| `s8_hydra_turn.jpg` | `hold_side_input.gd` on hydra: the hero circles right, `walk_turn_l` 3.09-5.12, then fire_sweep out of it | The body turns to keep the hero in front, and the inhale cracks follow. At 17-18 m from the chase camera the feet cannot be judged. Foot numbers: integrate2_hydra |

Nothing in these passes stands, turns or travels like a statue. I saw no pop at a clip change.

## 5. Still open (most important first)
1. **minor (look, world)**: arriving home from the sea, the hero is already on foot at the path while Pegasus glides in
   **without a rider**, although he flew home on it (`s7_land.jpg`, 6.3-8.1 s). Either keep the rider seated through the
   1.9 s glide-in and dismount when it stands, or place the hero (fade in) only after `pegasus_landed`. Owner:
   home_base.gd (world).
2. **minor (clip, hydra)**: the turn walk's feet slide at start and stop. Turn-walk blend-in: 0.4-1.1 m/s. Walk to
   attack: 2.2-3.3 m/s peaks. Steady turn walk: 1.5 m/s on toe-off/touch-down frames of foot_bl/fl. This needs
   step-in/settle clips (integrate2_hydra clip_problems). My chase-camera pass shows the Hydra at 17 m, where the feet
   cannot be read.
3. **minor (perf)**: on a fully cold cache, the fight_start frame takes 57-58 ms in medusa and hydra (HUD boss bar canvas
   pipeline). Drawing the boss bar once inside `ArenaBase.prewarm()` under the title card would remove it (core).
4. **minor (clip, hercules)**: from straight behind the idle shield is edge-on. In roll the shield passes through the body
   (100-900 vertices). In walk_back the shield sits 14 cm into the chest; in strafe, 6 cm. All are known and are the lead's
   call (assemble2_hercules).
5. **minor (clip, cyclops)**: in pull_free the right foot glides 1.25 m. In sweep the feet slide while he turns (left foot
   1.34 m at 1.46-1.83 s). Arms cross the head and trunk in slam and sweep (pre-existing).
6. **minor (camera, cyclops)**: in the walk-in he stands right behind the hero in the frame, so the new natural walk is
   mostly hidden at the start of the fight.
7. **cosmetic (mount)**: from the chase camera the raised near wing hides the seated rider for about 0.35 s.
8. **cosmetic (clip, medusa)**: in death the left upper arm passes 180 deg at 1.78-1.85 s; the game joins only at 0 and
   2.6 s, so it is safe. In stun_start, hair_l_01 moves 0.92 m per frame at the game's 1.3x (the head falling).
9. **info**: `Godot --headless --path game --quit-after 2`, and any run cut by `--quit-after`, ends with "WARNING: 6
   ObjectDB instances were leaked" and "ERROR: 2 resources still in use at exit". `--verbose` shows the leak: the title
   music ogg playback and the `ui_move.wav` playback are still alive at the forced exit. Harness-ended runs are clean. A
   player never sees it.
10. **info**: the direct `--start=<boss>` first frame takes 2.7-4.3 s on a cold cache. On the game path it is under the
    black fade (landing switch 1665 ms on black).
11. **not rendered by me**: a human-banked turn in flight, the hydra side bites (bite_l/_r), and a medusa tail swipe (the
    bot never triggers one).
12. **for the lead**: `builds/Hercules.app` predates today's GLBs and code (hydra wind-down, jaw_radius 1.0, mount and
    landing, sync_rider). It needs your rebuild.
