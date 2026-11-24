# Build + performance (qa_build, 2026-11-22; owner away, decisions marked **Decision**)

Files created: `game/export_presets.cfg`, `builds/Hercules.app`, `README.md` (repo root), this note. No other game file
was changed. Scratch, probes and logs: `work/qa_build/` (`logs/`, `perf_run.sh`, `analyze.py`, `persec.py`,
`assemble.sh`, `run_app_pty.py`, `tpl/` = the unpacked official 4.7.2 macOS template). The throw-away probe
`game/zz_qa_perf.gd` (a SceneTree `--script` that runs `main.tscn` and records frame times and render counters) was
deleted afterwards. Its copy is in `work/qa_build/zz_qa_perf.gd.txt`.

## 1. Export

### Preset (`game/export_presets.cfg`, preset "macOS")
universal binary, bundle id `com.hercules.game`, app name Hercules, version 0.1.0, category Games, built-in ad-hoc
codesign (no identity), App Sandbox off, no notarization, `include_filter="*.json"` (props.json, `*_clips.json`,
audio.json are read with FileAccess), `exclude_filter="zz_qa_*, *.md"`, scripts exported as binary tokens,
export path `../builds/Hercules.app`. `shader_baker/enabled=false`, for the reason in 3.3.

### The template export fails (needs a core change)
`Godot --headless --path game --export-release "macOS" ../builds/Hercules.app` stops at once:
`Cannot export for universal or arm64 if ETC2 ASTC texture format is disabled. Enable it in the Project Settings
(Rendering > Textures > VRAM Compression > Import ETC2 ASTC).` x86_64 alone would export, but it would run under
Rosetta on Apple Silicon. **Fix for core:** add `rendering/textures/vram_compression/import_etc2_astc=true` to
`work/core/gen_project.py`, regenerate `project.godot`, re-import (take `work/.import_lock`), and the one-line export
above works.

### What shipped instead: the pck route, with the official runtime (**Decision**)
1. `Godot --headless --path game --export-pack "macOS" work/qa_build/Hercules.pck` (2 s). The pck needs no ETC2/ASTC
   check. Its S3TC/BPTC textures are supported by Metal on Apple Silicon and Intel Macs.
2. `work/qa_build/assemble.sh work/qa_build/Hercules.pck builds/Hercules.app` builds the app bundle:
   - the official 4.7.2 **release** template binary (`macos.zip` > `godot_macos_release.universal`), renamed
     `Contents/MacOS/Hercules`
   - `Contents/Resources/Hercules.pck`. A runtime loads `<binary name>.pck` from Resources by itself, so the app needs no
     `--main-pack`.
   - Info.plist filled from the template's own (Hercules, `com.hercules.game`, 0.1.0, games, high-res)
   - template icon and PrivacyInfo
   - `codesign --force --deep --sign -` (ad-hoc)

   `codesign --verify` passes: "valid on disk, satisfies its Designated Requirement".

   This uses the official release runtime, not the editor binary, so it behaves like a template export. Once core
   makes the fix above, run the one-line export and this route is no longer needed.

Rebuild: `zsh builds/make_app.sh` (fixer pass, section 5; it replaced `work/qa_build/assemble.sh`, which lived in the
git-ignored work/ folder and needed a hand-unpacked template).

### Size and start time
- `builds/Hercules.app` is **229 MB**: 170 MB universal runtime + 70.5 MB pck. The pck holds 23 textures, 23 imported
  scenes, 38 scripts, 7 json files, 57 sounds and 5 music tracks. An arm64-only runtime (`lipo -thin arm64`) would
  save about 85 MB. Kept universal so Intel Macs can run it (**Decision**).
- Start time, measured on line-buffered output through a pty:
  - engine banner at 0.07-0.08 s (1.25 s on the first launch after re-signing, while macOS checks the new signature)
  - title ready at 0.38-0.68 s
  - straight into an arena (`--start=<boss>`): scene at 0.85-2.0 s, `fight_start` at 3.0-4.5 s, which includes the
    island title card

### The exported app works outside the editor (all runs use the app's own binary)
| Run | Result |
|---|---|
| windowed 1920x1080 `-- --start=cyclops --harness --bot=win` | `result=victory`, 39.3 s wall, 0 ERROR lines |
| windowed `-- --start=title --harness --quit-after=4` | title, `result=quit` |
| headless `-- --start=cyclops --harness --bot=lose --speed=3` | 3 hits, `player_died` at 20.05 s, fight restarted, `result=defeat` |
| headless `-- --start=home --harness --bot=win --speed=3` | home > sea > lands at cyclops > `result=victory` (exit 0) |
| headless `-- --start=sea --defeated=all --harness --bot=win --speed=3 --after-victory=3` | sea > ending > sea (free flight) > home |
| windowed shots, editor vs app, same seed | identical frames (`docs/devlog/media_inbox/qa_build/editor_vs_exported_app.jpg`) |

Notes: the release template refuses `--main-pack` ("compiled without support for path overrides") and silently ignores
`--script`. Debug probes therefore run against the same pck with the 4.7.2 editor binary
(`Godot --main-pack <pck> --script res://zz_qa_perf.gd`). The app and editor runs of the project share
`~/Library/Application Support/Godot/app_userdata/Hercules/` (save.json + shader_cache), because `config/name` is the
same and no custom user dir is set.

## 2. Performance (M5 Max, 120 Hz built-in display, windowed 1920x1080, vsync on, Forward+/Metal)
Probe: frame time = wall time between SceneTree `_process` calls. Counters come from `Performance` (draw calls,
primitives, objects in frame, video memory). The first 3 s are skipped. Full-length `--bot=win` fights at speed 1 in
the editor runtime. Logs: `work/qa_build/logs/perf_*.json|log`. Summary: `python3 work/qa_build/analyze.py <json>`.

| Scene | frames | avg ms (fps) | median | p99 | 1% low | worst | >16.7 ms | draw calls avg/max | primitives avg/max | VRAM |
|---|---|---|---|---|---|---|---|---|---|---|
| cyclops | 2883 | 11.99 (83) | 8.64 | 39.9 | 23 fps | 76.8 | 19 % | 465 / 580 | 1.15 M / 1.38 M | 521 MB |
| medusa | 2201 | 11.90 (84) | 8.62 | 40.2 | 16 fps | 331 (first reflected gaze) | 18 % | 366 / 445 | 1.64 M / 1.83 M | 545 MB |
| hydra | 9083 | 10.81 (92) | 8.45 | 35.2 | 23 fps | 346 (first jaw strike) | 15 % | 173 / 207 | 1.04 M / 1.32 M | 473 MB |
| sea flight + landing + cyclops | 4523 | 11.19 (89) | 8.48 | 36.9 | 23 fps | 227 (scene switch, under the fade) | 17 % | flight 118-232 | flight 0.9-1.08 M (1.5 M near the island) | 526 MB |
| test arena (grey boxes) | 1120 | 10.89 (92) | 8.58 | 35.6 | 26 fps | 42.5 | 16 % | 123 / 140 | 0.33 M / 0.36 M | - |
| title (2D) | 1443 | 8.34 (120) | 8.07 | 9.4 | 98 fps | 20.3 | 0 % | 92 | 2.5 k | 93 MB |
Scene loads draw 897 calls / 1.89 M primitives for a frame or two. Physics stays at 2-3 ms on average, 5-8 ms at most.

### 2.1 Frame pacing: spikes of 30-45 ms in every 3D scene (cause not found)
The averages stay above 60 fps, but 15-19 % of frames miss 16.7 ms. The misses come in bursts: one frame of 25-45 ms
followed by 2-3 ms catch-up frames, roughly every 8-11 frames, on a ~4 s cycle (2 s bins alternate ~208 and ~162
frames). They appear even in the grey-box test arena (0.33 M primitives, 123 draw calls). The title screen shows none.
A/B runs (cyclops 30 s, variants set at runtime by the probe):
| Variant | >16.7 ms | worst | primitives avg |
|---|---|---|---|
| baseline | ~19 % | 76.8 | 1.15 M |
| no vsync | 17 % (median still 8.4: the compositor caps at 120) | 296 (first block) | 1.18 M |
| no directional shadows | 16 % | 43 | **0.46 M** (draw calls 472 > 184) |
| no MSAA | 18 % | 46 | 1.19 M |
| physics 120 Hz (test arena) | 16 % | 41 | - |
| no bot (cyclops, standing) | 16 % | 45 | 1.43 M |
| `--max-fps 60` | 7 % over 20 ms, 4 % over 25 ms | 355 | 1.24 M |
So shadows, MSAA, the physics rate, the bot and the asset load are ruled out. During every run the machine was also
running another project's background Blender render and, at times, other agents' Godot windows. GPU contention is the
leading suspect. **Re-measure on an idle machine** before acting. If the spikes remain, profile one fight with
Instruments (Metal System Trace) or the Godot profiler.

### 2.2 First-use hitches (300-350 ms) with a cold shader cache
- medusa: 331 / 344 / 345 ms on the frame of the first reflected gaze (3 cold runs)
- hydra: 346 ms on the first jaw strike
- cyclops: 296 ms on the first blocked sweep (1 run)
- 182-311 ms frames at scene build
- 100-135 ms around the boss death / LABOR COMPLETE

Once `user://shader_cache` is warm, a re-run shows none of them (worst 74 ms at the victory). A new player meets them
once, at the key moments.

### 2.3 Where the primitives go
The directional shadow pass (4096 atlas, soft shadow quality 2) accounts for about 60 % of all primitives (cyclops:
1.18 M with shadows, 0.46 M without). Medusa is the heaviest scene (1.64 M average: the 70 k-triangle Medusa plus the
ring of petrified-warrior statues, drawn again in every shadow cascade). This is fine on an M5 Max and heavy for a base
M1/M2. Cheap wins: `directional_shadow_max_distance` of about 60-80 m per arena, 2 cascades, `cast_shadow` off on
rim props beyond ~25 m, and LODs (or decimated shadow meshes) for the 66-70 k-triangle characters.

### 2.4 Re-measured on the idle machine (lead, 2026-11-23 1:36-1:39 AM)
Same probe (`work/qa_build/zz_qa_perf.gd.txt` copied to `game/zz_qa_perf.gd` for the runs, then deleted), full
`--bot=win --seed=11` fights at speed 1, windowed 1920x1080, vsync on, 120 Hz, editor runtime, after the lead's circling
fix. No agent, Godot window or Blender render was running. JSON and logs: `work/lead_final2/perf/`.

| Scene | frames | avg ms (fps) | median | p99 | p99.9 | worst | >16.7 ms | >33 ms | draw calls avg/max | primitives avg/max |
|---|---|---|---|---|---|---|---|---|---|---|
| cyclops | 4196 | 8.35 (120) | 8.37 | 11.03 | 15.58 | 28.6 | 4 | 0 | 543 / 675 | 1.21 M / 1.47 M |
| medusa | 3041 | 8.34 (120) | 8.33 | 11.02 | 16.24 | 24.0 | 2 | 0 | 358 / 424 | 1.67 M / 1.78 M |
| hydra | 11875 | 8.37 (119) | 8.32 | 10.86 | 15.17 | 306.5 (t=8.42 s, first use of an effect) | 5 | 3 | 175 / 245 | 0.83 M / 1.07 M |

So the 30-45 ms bursts of 2.1 came from the machine load during the build (GPU contention), not from the game. The
first-use hitch of 2.2 is still there (one 307 ms frame in the Hydra fight).

## 3. Decisions taken with the owner away
1. Shipped the pck route on the official release runtime (section 1) rather than waiting for a core setting change.
2. Universal over arm64-only (+85 MB).
3. Shader baker off. It runs only in a windowed export (headless skips it). It baked 389 shader variants (+12 MB), but
   with a cold cache it did NOT remove the first-reflect hitch: 345 ms baked vs 344 ms plain. The likely reason is that
   the game builds its materials in code, so the baker cannot see those variants. The real fix is a warm-up pass (see
   findings).
4. README "Known limits" states the performance and hitch numbers plainly instead of leaving them out.

## 4. Open (for core / modules)
- core: `import_etc2_astc=true` in gen_project.py, so the one-line template export works.
- core: a material warm-up at boot or under the island title card. Draw each VFX material once (spark, dust,
  block/reflect flash, gaze beam/fan, petrify stone, fire, hit flash, weak-point glow, telegraph decals,
  LABOR COMPLETE overlay), or turn the code-built materials into `.tres` files so the shader baker can reach them.
- core/arenas: shadow distance and cascade limits per arena (2.3).
- ~~art: a 1024x1024 app icon~~ done in the fixer pass (section 5).
- re-measure frame pacing (2.1) on an idle machine.

## 5. Fixer pass after the play-test (build fixer, 2026-11-22; owner away, decisions marked **Decision**)
Files: `game/export_presets.cfg` (icon), `builds/make_app.sh` (new), `builds/Hercules.app` (rebuilt), `README.md`, this
note, and a new folder `game/icon/` (`.gdignore`, `make_icon.py`, `hercules_icon_1024.png`, `hercules.icns`). Requests for
core: `docs/notes/qa_requests.md`. Scratch and logs: `work/build_fix/` (`logs/`, `shots/`, `sheet.jpg`, `home/` = sandbox HOME).

| Finding | Status |
|---|---|
| major: nothing to launch (no builds/, preset, README) | already fixed by qa_build (section 1); this pass adds the save sessions on the exported data and a tracked rebuild script |
| major: one-line template export fails (ETC2/ASTC off) | **needs core** (request 1 in qa_requests.md: `import_etc2_astc=true` in gen_project.py). `make_app.sh` uses the one-line export by itself once project.godot has the setting; until then it builds the app from the pck + the official release template, with no hand steps |
| minor: default Godot icon | fixed: new icon, preset `application/icon="res://icon/hercules.icns"`, copied into the bundle by make_app.sh |
| minor: app and editor share one user folder | **needs core** (request 2: `config/use_custom_user_dir=true`, `custom_user_dir_name="Hercules"`). README now warns that editor runs without `--harness` change the app's save |

**Icon (Decision).** No Higgsfield credits (only the lead spends them): drawn in code with Pillow (`game/icon/make_icon.py`,
re-run with `python3 game/icon/make_icon.py`). A round bronze hoplite shield (terracotta face like the hero's tunic, gold
16-ray star, cel highlight band, 16 rivets) over a sword, inside a gold Greek-key frame on a navy rounded square (824 px
body on the 1024 canvas, Apple grid). `hercules.icns` holds 10 sizes (16-1024 px), 736 KB. The folder has a `.gdignore`,
so Godot never imports it and nothing from it goes into the pck; the export reads the .icns directly by path. Checked at
128 px: shield, star and frame still read.

**make_app.sh (Decision).** builds/ is git-ignored, so the script is copied below. It takes `work/.import_lock`, unzips the
template from the installed export templates to a temp folder (no `work/qa_build/tpl` needed), and cleans up. 4.2 s.
Result: 230 MB, `codesign --verify` valid, 309 files in the pck incl. the 7 json files (audio.json, 5 `*_clips.json`,
props.json); no `zz_qa_*`, `.md` or `icon/` files.

**Proof (exported app binary `builds/Hercules.app/Contents/MacOS/Hercules`, logs work/build_fix/logs/)**
| Run | Result |
|---|---|
| headless `--start=cyclops --harness --bot=win --speed=3 --seed=11` | `fight_start` 2.41 s, `victory` 35.48 s, `result=victory`, exit 0 |
| same, `--seed=4242` | `victory` 31.60 s, exit 0 |
| headless `--bot=lose --speed=3` | 4 hits, `player_died` 20.03 s, `fight_start` again 24.21 s, `result=defeat` |
| windowed `--bot=win --shots --shot-every=5 --quit-after=26` | 6 shots, hero, cyclops, club, HUD on-model (`work/build_fix/sheet.jpg`) |
No SCRIPT ERROR / Parse Error / ERROR line in any of them.

**Save sessions against the exported data (Decision on method).** The release runtime ignores `--script` and refuses
`--main-pack`, and the harness never saves, so a fully scripted save test cannot run inside the release binary. Done
instead, with a sandbox `HOME=work/build_fix/home` (the owner's real save is never touched):
1. the 4.7.2 runtime on the app's own pck (`Godot --headless --main-pack builds/Hercules.app/Contents/Resources/Hercules.pck
   --script work/build_fix/qa_play.gd -- --start=title --qa-save=1`, qa_playthrough's driver): title shows
   `[New game, Continue(disabled), Controls, Quit]`, New game -> home, save.json written all false, `mark_defeated(cyclops)`
   -> `{"cyclops":true,...}`, home shows the cyclops trophy and next island medusa, quit.
2. `--qa-save=2`: title now `[Continue, New game, Controls, Quit]` with focus on Continue, `has_save=true`; Continue -> home
   with cyclops beaten, trophy shown, next island medusa.
3. the release app itself, no `--harness`, same HOME, `--start=title`: it opened its user folder at the same path
   (`.../app_userdata/Hercules/` gained its log file, `shader_cache` and `vulkan` next to the save.json from step 1), so the
   app reads the same file the script runtime wrote with the same GDScript. Stopped by PID after 6 s. (A screen grab of
   its title was not possible: the shell has no screen-recording permission.)
Both script sessions end with `ERROR: 1|2 resources still in use at exit`, as in qa_playthrough's save logs: the driver
quits the SceneTree directly; not a game fault.

**Route A checked ahead of the core change.** In a throw-away copy of game/ (work/build_fix/routeA, deleted afterwards)
with `import_etc2_astc=true` added: `--import` then the one-line `--export-release "macOS"` both exit 0 with the preset
as it is; the app carries our icon.icns (735,568 bytes, `CFBundleIconFile` icon.icns), 231 MB, `codesign --verify` valid,
and its binary wins `--start=cyclops --bot=win --speed=3 --seed=11` (victory 36.01 s, no ERROR). So once core lands
request 1, make_app.sh's route A works unchanged. Logs: work/build_fix/logs/routeA_*.log.

**Note for the lead.** Other fixers edit game files at the same time, so this build is a snapshot of 23:28. After the last
fixer finishes, run `zsh builds/make_app.sh` once more (4 s) and repeat one `--bot=win` run from the app binary.

### builds/make_app.sh (copy)
```sh
#!/bin/zsh
# Builds builds/Hercules.app from game/ with the official Godot 4.7.2 macOS template.
# Usage (from anywhere):  zsh builds/make_app.sh
#
# Route A (used when game/project.godot has rendering/textures/vram_compression/import_etc2_astc=true):
#   the one-line template export with the "macOS" preset in game/export_presets.cfg.
# Route B (until then): export the game data as a .pck (no ETC2/ASTC check), then put the official 4.7.2 RELEASE
#   template binary, the pck, the Hercules icon and a filled Info.plist into an app bundle and sign it ad hoc.
# Both routes take the shared import lock work/.import_lock (SPEC section 10). A copy of this script is in
# docs/notes/build.md (builds/ is git-ignored).
set -e
REPO=${0:A:h:h}
GODOT=/Applications/Godot_4.7.2.app/Contents/MacOS/Godot
TPL_ZIP="$HOME/Library/Application Support/Godot/export_templates/4.7.2.stable/macos.zip"
APP="$REPO/builds/Hercules.app"
ICON="$REPO/game/icon/hercules.icns"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/hercules_build.XXXXXX")
LOCK="$REPO/work/.import_lock"
mkdir -p "$REPO/work"

lock()   { until mkdir "$LOCK" 2>/dev/null; do sleep 2; done; }
unlock() { rmdir "$LOCK" 2>/dev/null || true; }
trap 'unlock; rm -rf "$TMP"' EXIT

if grep -q '^textures/vram_compression/import_etc2_astc=true' "$REPO/game/project.godot" \
   || grep -q 'vram_compression/import_etc2_astc=true' "$REPO/game/project.godot"; then
  echo "route A: one-line template export"
  rm -rf "$APP"
  lock
  "$GODOT" --headless --path "$REPO/game" --export-release "macOS" "$APP"
  unlock
else
  echo "route B: pck + official release template (import_etc2_astc is off in project.godot)"
  lock
  "$GODOT" --headless --path "$REPO/game" --export-pack "macOS" "$TMP/Hercules.pck"
  unlock
  unzip -q "$TPL_ZIP" -d "$TMP/tpl"
  T="$TMP/tpl/macos_template.app/Contents"
  rm -rf "$APP"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  cp "$T/MacOS/godot_macos_release.universal" "$APP/Contents/MacOS/Hercules"
  chmod +x "$APP/Contents/MacOS/Hercules"
  cp "$T/Resources/PrivacyInfo.xcprivacy" "$T/PkgInfo" "$APP/Contents/Resources/" 2>/dev/null || true
  mv "$APP/Contents/Resources/PkgInfo" "$APP/Contents/PkgInfo"
  cp "$ICON" "$APP/Contents/Resources/icon.icns"
  cp "$TMP/Hercules.pck" "$APP/Contents/Resources/Hercules.pck"
  python3 - "$T/Info.plist" "$APP/Contents/Info.plist" <<'PY'
import sys
s = open(sys.argv[1]).read()
rep = {"$binary": "Hercules", "$name": "Hercules", "$liquid_glass_icon": "", "$bundle_identifier": "com.hercules.game",
       "$short_version": "0.1", "$signature": "????", "$version": "0.1.0", "$platfbuild": "", "$sdkver": "",
       "$sdkbuild": "", "$sdkname": "", "$xcodever": "", "$xcodebuild": "", "$usage_descriptions": "",
       "$copyright": "", "$app_category": "games", "$min_version_arm64": "11.00", "$min_version_x86_64": "10.12",
       "$highres": "\t<true/>", "$additional_plist_content": ""}
for k in sorted(rep, key=len, reverse=True):
    s = s.replace(k, rep[k])
open(sys.argv[2], "w").write(s)
PY
  plutil -lint "$APP/Contents/Info.plist"
  codesign --force --deep --sign - "$APP"
fi
codesign --verify --verbose=2 "$APP"
touch "$APP"   # Finder/Dock pick up the new icon
du -sh "$APP"
```

## 6. Final check + build (2026-11-23 00:36, after the three QA fixers; owner away, decisions marked **Decision**)
Full results: `docs/notes/final_check.md`. Scratch and logs: `work/final_check/` (`logs/`, `shots/`, `sheet_*.jpg`,
`shots_run.sh`, `sheet.py`, `tail_probe_react.gd`).
- `game/project.godot` now has `import_etc2_astc=true` and the custom user dir "Hercules" (core fixer 2), so
  `make_app.sh` took **route A** (the one-line `--export-release "macOS"`) by itself. Route B stays in the script as a
  fallback. Run it with `zsh`: `bash builds/make_app.sh` stops at `${0:A:h:h}` (bad substitution). It stops harmlessly
  before it touches anything (**Decision**: kept zsh, README says so).
- Result: `builds/Hercules.app` **231 MB** (universal binary 163 MB + pck 67.3 MB + icon 0.7 MB). Export 3.9 s wall.
  `codesign --verify`: valid on disk, satisfies its Designated Requirement. Info.plist: Hercules, com.hercules.game,
  0.1 / 0.1.0, icon.icns.
- Start times of the exported binary, stamped through a pty:
  - headless title: engine banner 1.21 s on the first launch after the re-sign, then 0.02 s; title scene 0.15 s
  - windowed title (1280x720): banner 0.08 s, title scene 0.44 s
  - windowed cyclops: scene 0.95 s, `fight_start` 3.67 s (after the island card)
- Exported binary runs: windowed `--start=title --quit-after=4` gave `result=quit`. Windowed
  `--start=cyclops --bot=win --seed=11` won (victory 35.89 s game time, 39.3 s wall). Headless
  `--start=medusa --bot=win --speed=3 --seed=11` won at 26.19 s (3 reflects). No SCRIPT ERROR / ERROR / WARNING in any of them.
- The saves path in README is now `~/Library/Application Support/Hercules/save.json`, with a reset command.
- **Final build: 00:45.** It was rebuilt after the final check's one-function camera change (player_camera.gd
  `_boss_tops`). Same size (231 MB), route A, 3.8 s, codesign valid. Re-run from the new binary:
  - headless title: banner 1.25 s on the first launch after the re-sign
  - windowed title: scene 0.39 s
  - windowed medusa `--bot=win --seed=11`: scene 0.86 s, `fight_start` 3.09 s, victory 26.14 s game time, 28.9 s wall
  - headless medusa `--speed=3`: victory 26.23 s
  No ERROR / WARNING in any of them.
