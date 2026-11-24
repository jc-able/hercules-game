# Probes (SceneTree scripts run next to the game; copy one to your scratch folder and change it)
All of them run with the game's harness flags after `--`. Rendering runs go through `tools/godot_bg/gdwin`
(off-screen, no focus, silent). Example (screenshots every 0.33 s into a folder you made):

    tools/godot_bg/gdwin --path game --resolution 1280x720 --script $PWD/tools/probes/hold_side_input.gd -- \
        --start=cyclops --harness --seed=11 --shots=$PWD/work/<role>/shots --shot-every=0.33

| File | What it does |
|---|---|
| `hold_side_input.gd` | waits for the fight, holds "right" 4 s then "left" 4 s through the real input actions (the move a person makes to circle a boss). Prints the body turn and clip |
| `circling_transitions.gd` | roll, strike, shield, stop, reverse and diagonal runs out of the circling run; prints the largest upper-body twist per phase |
| `home_free_run.gd` | free run on the home island: forward, right, back, left |
| `perf_probe.gd` | frame times and render counters for a whole run: add `--perf-out=<file.json>` after `--`; summary with `python3 tools/probes/perf_analyze.py <file.json>`. For a COLD shader cache prefix the command with `HOME=<new folder> CFFIXED_USER_HOME=<new folder>` on the same line |
| `freeze_probe.gd` | (freeze_fix) prints `[P] t=<game s> ms=<frame> pipe(c,m,s,d,sp)=[...]` live for every frame over 50 ms and every frame that compiled a GPU pipeline, so the `[H]` events around it stay in order. A new HOME only empties Godot's cache; macOS keeps a Metal compiler cache per **bundle id**, so a truly cold run (what a fresh export meets) also needs a cloned Godot.app with a new id: make an APFS copy of `Godot_4.7.2.app` (`cp -c`), give the copy a new `CFBundleIdentifier` in its `Contents/Info.plist` for every run, sign it ad hoc (`codesign --force --deep -s - <copy>.app`) and run that copy's binary with a new HOME on the same line (details in `docs/notes/freeze_fix.md`). `--no-prewarm` after `--` turns the warm-up off for an A/B |
| `fx_capture.gd` | (headless is fine) records the material of every mesh/particle node added after the fight starts; `--cap-out=<dir>` saves one `.tres` per kind of shader. Run it per fight with `--bot=win` and `--bot=lose` into ONE folder |
| `fx_warm_build.gd` | `Godot --headless --path game --script $PWD/tools/probes/fx_warm_build.gd -- --cap-dir=<that folder>` rebuilds `game/assets/fx/warm_fx.tscn`, which `ArenaBase.prewarm()` draws under the island title card. Re-run both after an effect gets a new kind of material (a new flag, texture or shader) |

Contact sheet of a shots folder: `ffmpeg -v error -y -pattern_type glob -i "<dir>/*.png" -vf "scale=400:-1,tile=4x6" -frames:v 1 -q:v 4 sheet.jpg`
(no drawtext filter: write labels with Pillow). Movies: add `--write-movie <file.avi> --fixed-fps 30` before `--script`.
