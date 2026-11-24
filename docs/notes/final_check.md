# Final check + build (2026-11-23 00:33-00:48; owner away, decisions marked **Decision**)

Role: final check + build agent. Files I changed:
- `README.md`
- `docs/notes/build.md` (section 6)
- this note
- `docs/notes/qa_requests.md` (a status section appended)
- `docs/devlog/media_inbox/final_check/` (6 contact sheets + captions.txt)
- `builds/Hercules.app` (rebuilt twice)
- **One fix outside my files**, listed here as required: `game/scripts/player/player_camera.gd` `_boss_tops()`. I applied
  the medusa fixer 3 must-fit hook (qa_requests "medusa fixer 3" request 1), exactly as proposed plus a comment.
  **Decision:** every fixer had finished, the patch was proven by the fixer with the same file, and it only acts for a
  boss that defines `cam_fit_points()` (only Medusa does).

No imports, no git. Scratch, logs and probes are in `work/final_check/`:
- `logs/`, `shots/`, `sheet_*.jpg`
- `shots_run.sh`, `sheet.py`
- `tail_probe_react.gd`: the fixer's tail probe with `--react=<s>`

## 1. Playthrough (headless, `--speed=3`, seed 11 unless noted)
| Run | Result | Scene times (game s) | Fights (fight_start -> victory) |
|---|---|---|---|
| `--start=title --bot=win --campaign --keys` | victory, exit 0 | title 1.3, home 4.0, sea 16.1, cyclops 40.2, sea 28.2, medusa 30.6, sea 23.8, hydra 105.6, ending 3.2, free-flight sea | cyclops 33.7, medusa 24.0, hydra 99.0; 22 strikes, **0 hits taken** |
| same, `--pad` | victory, exit 0 | title 1.3, home 4.0, sea 16.0, cyclops 40.2, sea 28.2, medusa 30.5, sea 23.7, hydra 103.7, ending 3.2, sea | cyclops 33.7, medusa 24.0, hydra 97.1; 22 strikes, 0 hits |
| `--campaign --keys` seed 4242, **after the camera fix** | victory, exit 0 | same flow | cyclops 29.7, medusa 23.9, hydra 99.1 |
| `--start=cyclops --bot=lose` | defeat, exit 1 | - | 4 hits, died 20.05 s, restart 24.72 s, fight_start again 25.74 s |
| `--start=medusa --bot=lose` | defeat | - | 4 gaze hits (30 each), died 55.73 s, restart 60.40 s, fight_start again |
| `--start=hydra --bot=lose` | defeat | - | 9 fire ticks (12 each), died 27.85 s, restart, fight_start again |
| `--start=medusa --bot=win` seeds 11 / 4242, after the camera fix | victory | - | 26.20 / 25.32 s, 3 reflects each |

None of these logs has a `SCRIPT ERROR`, `Parse Error`, `ERROR`, `WARNING` or missing-resource line. That holds for the
windowed shot runs and the exported-app runs too.

## 2. The three fixers' changes, checked
| Item | Verdict | Evidence |
|---|---|---|
| Tail swipe avoidable by a person-like reaction | **pass at 0.5 s; part at 0.7 s** | I ran the fixer's probe again with `--react` (100 roll cases each, normal + enraged, 5 distances x 10 angles). React 0.35 s (fixer) and **0.5 s: 0/100 hit**. At 0.5 s, 9 of the 100 are still inside the ring and are saved by the roll's i-frames. **0.7 s: 28/100 hit**, all of them starting 4 m or closer to her body (in each mode, 14 of the 30 cases at 2.38 m, 3 m and 4 m: 5, 5 and 4 of 10 angles). From 5 m and from the trigger edge, still 0. The linger bot in a windowed run got 2 swipes and both missed (hero 11.6-12.0 m out). The hint "[Space] roll out of the ring" shows at the top of the screen |
| DEFEATED no longer covers the fall | **pass** | windowed cyclops lose run: at death +0.6 s the hero falls with no boss bar or reticle. At +2.0 s DEFEATED sits in the upper third with the boss's legs behind it, and the hero lies fully visible in the lower middle (`final_lose.jpg`) |
| Shield and sword visible from behind; block/attack still right | **pass (shield), part (sword)** | from the chase camera the shield reads as a broad disc in run and block (cyclops and medusa fight starts). The sword shows only as a short foreshortened blade above the right hand when running toward the boss. It is clearly beside him in the side views (block, tail roll). Block: every sweep blocked (8/8 per cyclops fight) and every gaze reflected. Attacks: 22/22 strikes per campaign, 0 glances lost |
| Club gone from the Cyclops death | **pass** | shots at boss_defeated +0.25 s, club_dropped +0.35 s and victory +1.0 s: no club anywhere in the frame under LABOR COMPLETE. The log has `cyclops_club_dropped cam_dist=7.49` |
| Hydra bot time back near 90-105 s | **pass** | fight time 99.0 s (`--keys`), 97.1 s (`--pad`), 99.1 s (`--keys` seed 4242), 99.54 s (windowed `--speed=2`); 8 strikes for 8 openings, 0 hits |
| Medusa gaze eyes in frame (fixer 3's open item) | **pass after my fix** | before the fix, the windowed gaze_fire +0.15 shot showed her head cut at the top edge. After it, `cam_probe.gd --probe-hold=7` on the real camera gives eyes 10.4-11.5 % below the top edge through windup, beam and after, in 4 gazes. Before: up to 5.3 % above the edge. The windowed windup and fire shots show the whole head (`work/final_check/sheet_medusa_cam.jpg`) |

Windowed contact sheets (1280x720), one per scene, in `docs/devlog/media_inbox/final_check/`:
- `final_title.jpg`
- `final_home_sea.jpg`
- `final_cyclops.jpg`
- `final_medusa.jpg`
- `final_hydra.jpg`
- `final_lose.jpg`

Images read: 10.

## 3. Build
- `zsh builds/make_app.sh` took **route A** (one-step `--export-release "macOS"`): `import_etc2_astc=true` is in project.godot.
  It finished in 3.8 s and `codesign --verify` passes.
- **Decision:** it was run with `zsh`, not `bash`. The script uses zsh path syntax, and `bash builds/make_app.sh` fails
  at line 12 before it does anything. README says so.
- `builds/Hercules.app`: **231 MB** (universal binary 163 MB + pck 67.3 MB + icon). Final build: 00:45.
- Exported binary runs:

| Run | Result | Timings |
|---|---|---|
| windowed title | `result=quit` | scene 0.39-0.44 s |
| headless title | `result=quit` | engine banner 1.21-1.25 s on the first launch after a re-sign, else 0.02 s; scene 0.15 s |
| windowed cyclops `--bot=win` (first build) | victory | fight_start 3.67 s wall; victory 35.89 s game, 39.3 s wall |
| windowed medusa `--bot=win` (final build) | victory | fight_start 3.09 s wall; victory 26.14 s |
| headless medusa `--speed=3` (both builds) | victory | 26.19 / 26.23 s |

- README checked and updated:
  - how to start: double-click, right-click > Open, or the Godot command line
  - start time and size
  - save path `~/Library/Application Support/Hercules/save.json` and the reset (New game or `rm`)
  - controls for keyboard/mouse and Xbox, and the flow
  - the Medusa tail answer is now "roll out of the ring before it fills"
  - `--campaign` and `--fake-save` added to the test flags
  - known limits made complete and honest
  - devlog at `docs/devlog/README.md`

## 4. Still open (severity)
1. **minor**: Medusa tail with a slow reaction. Hugging her (4 m or closer from her centre), a roll that starts 0.7 s after the ring
   appears is hit about half the time (28/100 over all cases). At 0.5 s or faster it is always clear. Fair once learned, harsh
   for a first try. A 1.7-1.8 s fill (medusa.gd `TAIL_COIL`) or a 6.5 m trigger would help. Not changed (module tuning).
2. **minor**: from the chase camera the sword shows only as a short blade above the right hand when running toward the
   boss (the blade points forward). The shield reads well.
3. **minor**: Hydra jaw reach. The player must step right up to the snout (about 1 m). From 1.3 m or from the side of the
   head the sword scrapes for 0 damage. The fixer suggests `Tuning.HYDRA.jaw_radius` 1.1 -> 1.3 if testers whiff.
4. **minor**: Cyclops quarry curb. When the hero is knocked to the rim (the lose deaths), the white curb fills the bottom
   ~25 % of the frame, DEFEATED view included. A seam between two curb blocks sits in the middle of that view. Core's
   suggestion: a near fade on the curb material or a layer-1 collider for the spring arm.
5. **minor**: the stuck Cyclops club fills the lower-right quarter in the strike frame (it does not cover the hero).
6. **minor**: Hydra inhale warning. The floor in front turns a flat orange (reads as paint, not lava glow).
7. **minor**: when circling at full side input the hero turns ~95 deg and shows half his front (core locomotion).
   **Fixed by the lead after this check (about 1:30 AM): see `docs/notes/lead_circling_fix.md`.** In the lead's look
   probe this was a full side profile for as long as the player circled, and a front view at each change of direction.
8. **cosmetic**: muddy brown and yellow patches on some of Medusa's snake heads (texture; art track).
9. **cosmetic**: `Tuning.MEDUSA` still holds the old tail keys (tail_sweep_radius 9.3 / tail_coil 0.7). medusa.gd
   overrides them, so the game is right but the one-place-for-numbers rule is not.
10. **perf (re-measured by the lead on the idle machine at 1:36 AM: the 30-45 ms spikes are gone, 119-120 fps in all
    three fights, see build.md 2.4; the first-use shader hitch stays)**. Original entry: **perf (unverified on an idle machine)**: frame spikes of 30-45 ms and first-use shader hitches of ~0.3 s
    (build.md 2.1-2.2). They were not re-measured: the machine was again busy with other jobs.
11. **info**: the LABOR COMPLETE card sits over the boss's body while he falls (Cyclops, Medusa, Hydra). Readable, and
    the hero stays visible.
