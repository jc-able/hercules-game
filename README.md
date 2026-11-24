# Hercules

A third-person boss-fight game made in Godot 4.7.2 by AI coding agents, with every 3D model, reference video, sound and
music track generated on Higgsfield. This repository is the complete project from the build shown in the video: the
Godot game, the source art and rigs, the tools the agents wrote, and a devlog of every prompt, decision and number.
Download it, play it, and keep building it.

## Start here (if you came from the video)

### Just want to play? (Mac)
Download `Hercules-0.1.0-macOS-universal.zip` from the
[Releases page](https://github.com/jc-able/hercules-game/releases/latest), unzip it and open `Hercules.app`
(a universal build for Apple Silicon and Intel, tested on Apple Silicon only; keyboard and mouse or an Xbox controller).
The app is not notarized by Apple, so macOS blocks it the first time:
- macOS 15 or newer: double-click the app, choose **Done** in the warning, then open System Settings > Privacy &
  Security, scroll down to the line that says Hercules was blocked and click **Open Anyway**.
- macOS 14 or older: right-click the app, choose **Open**, then **Open** again.
- Or in Terminal: `xattr -dr com.apple.quarantine ~/Downloads/Hercules.app` (change the path to where you unzipped it).

On Windows or Linux, run the game from the source with Godot (next sections). That was only tested on macOS.

### What you need
- **Godot 4.7.2** (standard build, not .NET): <https://godotengine.org/download/archive/>. Other 4.x versions are untested;
  open the project with exactly 4.7.2 so nothing gets converted.
- To export a standalone app: the **4.7.2 export templates** (Godot editor > Editor > Manage Export Templates > Download).
- Optional, only to change art or animations: **Blender 5.2** (always run headless by the tools) and **Python 3** with
  numpy, Pillow, trimesh and pygltflib; `ffmpeg` for frame grabs and contact sheets.
- About 1.2 GB of disk for the clone (source art, reference videos and devlog media included). No file is over 50 MB.

### Open and run it
1. Clone or download this repository:
   ```sh
   git clone https://github.com/jc-able/hercules-game.git
   cd hercules-game
   ```
2. In the Godot 4.7.2 Project Manager choose **Import** and pick `game/project.godot`, or from a terminal:
   ```sh
   godot --headless --path game --import   # FIRST TIME ONLY after cloning: builds Godot's import cache (game/.godot/)
   godot --path game -e                    # open the editor (the first open also imports every asset: give it a minute)
   godot --path game                       # play
   ```
   A fresh clone has no import cache, so the play command and the harness commands below fail (parse errors such as
   "Identifier 'Tuning' not declared", then a hang) until the project has been imported once: run the `--import` line
   once, or open the editor once with `-e`.
   (`godot` = your Godot 4.7.2 binary, e.g. `/Applications/Godot_4.7.2.app/Contents/MacOS/Godot` on macOS.)
3. Press **F5** in the editor to play. Progress is saved to the game's user folder (`save.json`; on macOS
   `~/Library/Application Support/Hercules/`). **New game** on the title screen resets it.

### Export it
The project has one export preset, **macOS** (universal, ad-hoc signed, not notarized), in `game/export_presets.cfg`.
- Editor: Project > Export > macOS > Export Project.
- Terminal: `godot --headless --path game --export-release "macOS" ../builds/Hercules.app`
- Windows or Linux: add a preset for that platform in the Export dialog (not tested in this build).
- The build used a small wrapper script that also adds the app icon and signs the bundle; it is printed in full in
  `docs/notes/build.md` ("builds/make_app.sh (copy)"). Save it as `builds/make_app.sh` and run `zsh builds/make_app.sh`.
- An app you export on your own Mac opens straight away. A Mac that downloaded the app blocks it the first time: see
  "Just want to play? (Mac)" above for how to allow it.

### Controls
| Action | Keyboard + mouse | Xbox controller |
|---|---|---|
| Move | W A S D | Left stick |
| Camera (on foot) | Mouse | Right stick |
| Roll (dodge) | Space | B |
| Attack (press again for the second hit) | Left mouse button | RB (or X) |
| Shield (hold) | Right mouse button | LB |
| Lock-on on/off | Q or middle mouse button | R3 |
| Interact / mount Pegasus / land | E | A |
| Boost (flying) | Shift | RT |
| Pause | Esc | Start |

In flight the left stick / WASD steer and the camera follows by itself. More detail is in "Controls" further down.

### How it was made
- **The devlog**: `docs/devlog/README.md` is the way in: every prompt word for word (`PROMPTS.md`), every decision with
  its options (`DECISIONS.md`), the chapters with time, tokens and credits (`DEVLOG.md`), the timeline, and the
  before/after pictures and clips in `docs/devlog/media/`.
- **The animation method** (rigged model -> FRONT | SIDE sheet -> Seedance video at 480p -> keyframes matched to the
  video): `docs/ANIM_PIPELINE.md`, and `docs/briefs/anim_natural.md` for the second pass that fixed stiff limbs by
  starting the videos from a natural stance instead of the rest pose.
- **The contract the agents built against**: `docs/SPEC.md`. The briefs each agent got: `docs/briefs/`. What each agent
  wrote down: `docs/notes/`.

### Keep building it with an AI coding agent
- Give the agent `docs/SPEC.md` (design and module ownership) and `docs/AGENT_RULES.md` (how agents work in this repo:
  headless Blender, scratch folders under `work/`, edit only your own files, test with the harness). `CLAUDE.md` holds
  the standing rules the original sessions followed (keep the devlog current); adapt or drop it.
- **Test without playing**: every run with `-- --harness` prints one `[H] ... event=` line per event and ends with
  `[H] result=victory|defeat|timeout|quit`. The bots play for you (after the one-time `--import` from "Open and run it"):
  ```sh
  godot --headless --path game --import                                                  # once after cloning
  godot --headless --path game -- --start=cyclops --harness --bot=win --speed=3          # one fight, about 15 s
  godot --headless --path game -- --start=title --harness --bot=win --campaign --speed=3 # the whole game
  ```
  `--bot=win|lose|idle`, `--pad` / `--keys` (send controller or keyboard events), `--seed=`, `--shots=<dir>` and the
  other flags are listed under "Test flags" below.
- **Probes** (`tools/probes/`): scripts that hold an input, show every clip of a character on one sheet, measure frame
  times or record effects. See `tools/probes/README.md`.
- **Frozen limbs**: `python3 tools/clip_motion.py hercules cyclops medusa hydra pegasus` lists, per clip, which joints
  move and which stay frozen (a joint that turns less than 3 degrees in a whole clip).
- **Animation kit**: `tools/ak` (Blender headless; manual in `docs/ANIM_PIPELINE.md`) poses rigs against reference frames,
  scores the match, bakes, merges and exports the GLBs the game loads.
- `tools/godot_bg/gdwin` (macOS only) runs a rendering Godot window off-screen, silent and without taking the keyboard
  focus, so agents can take screenshots while you keep using the computer.
- `tools/workflows/` holds the multi-agent workflow scripts of the original build, as a record of how the work was split
  (they name the original repo path `~/HerculesGame`).

### Paid services
Generating NEW assets used **Higgsfield** (credits on a signed-in Higgsfield account and its `higgsfield` CLI):
`tools/hf/hfjob.py` (job wrapper and credit ledger), `tools/hf/gen_anim_refs.py` (Seedance reference videos) and
`tools/hf/gen_audio.py` (sound effects and music). Every job of this build is listed in `docs/higgsfield/jobs.jsonl`
(model, purpose, credits, status). **None of that is needed to run, change, test or export the game**: every
generated asset the game uses is already in the repo. Godot, Blender, Python and ffmpeg are free.

### Licence
The code and tools are under the MIT licence (`LICENSE`). The art, animations, sound and devlog media are under
CC BY 4.0 (`LICENSE-ASSETS.md`): use and change them for anything, with credit.

### What is not in this repository
The exported app (`builds/`), the agents' scratch folders (`work/`), the raw 3D downloads (`art_src/raw3d/`) and Godot's
import cache (`game/.godot/`) are not in git. The notes still name some of those paths: they describe the original
build machine. Private paths, account ids and generation result links were removed from the notes and the devlog for
this public copy. Some one-off art scripts under `art_src/` read files from `work/` and will not run as they are; the
art_src scripts also assume the original clone location `~/HerculesGame` (change the path at the top of a script, or
clone there, before running one).

---

## About the game

A third-person boss-fight game made in Godot 4.7.2. You play Hercules (1.9 m tall) against three towering creatures:
a four-armed Cyclops (8 m), Medusa (almost 10 m upright, with a long serpent tail) and a nine-headed Hydra (heads up to
about 14 m). The camera sits right behind Hercules. Every attack is announced by an animation, a decal on the
ground and a sound: read the warning, roll or raise the shield, then reach the glowing weak point and strike.
Between fights you fly Pegasus over open sea from a home island to each boss island in turn.

Same sword, same shield and 100 health all game. There is no healing during a fight. Losing restarts that fight with
both sides at full health. The full design contract is `docs/SPEC.md`.

## Start the game

### The app (macOS)
Download it from the Releases page (see "Just want to play? (Mac)" at the top), or export it yourself (see "Export it"
above; `builds/` is not in git) and open `builds/Hercules.app`, by double-clicking it or with:

```sh
open builds/Hercules.app
```

The app is a universal build (Apple Silicon and Intel), ad-hoc signed and not notarized. On the Mac that built it, it
opens straight away. A Mac that downloaded it blocks it the first time: allow it under System Settings > Privacy &
Security > **Open Anyway** (macOS 14 or older: right-click the app, **Open**, then **Open** again). The title screen is up in under a
second (0.4 s measured on the build machine; about 1.2 s on the first launch after a rebuild while macOS checks the new
signature). The app is 231 MB.

Progress (which bosses are beaten, and whether the ending was seen) is saved to
`~/Library/Application Support/Hercules/save.json`. To reset progress, choose **New game** on the title screen
(it asks first when there is progress), or quit the game and delete that file:

```sh
rm ~/Library/Application\ Support/Hercules/save.json
```

Running the project from the Godot editor without `--harness` uses the same file, so an editor session can change
the progress the app loads. Test runs with `--harness` never write it.

### Rebuild the app
```sh
zsh builds/make_app.sh
```
It exports the project with the official 4.7.2 macOS template (installed under
`~/Library/Application Support/Godot/export_templates/4.7.2.stable/`) and the "macOS" preset in
`game/export_presets.cfg`, adds the Hercules icon (`game/icon/`) and signs the app ad hoc. About 4 seconds. Run it
with `zsh` (it uses zsh path syntax; `bash builds/make_app.sh` fails). `builds/` is not in git: the script is also
printed in full in `docs/notes/build.md`: copy it to `builds/make_app.sh` first.

### From the Godot project
```sh
/Applications/Godot_4.7.2.app/Contents/MacOS/Godot --path game
```
Use the 4.7.2 binary (the path above is the macOS install used for the build; other Godot versions are not supported).
To open the editor instead, add `-e`.

## Controls
Keyboard and mouse and an Xbox controller both work at any time. On-screen prompts follow the device you used last.

| Action | Keyboard + mouse | Xbox controller |
|---|---|---|
| Move | W A S D | Left stick |
| Camera (on foot) | Mouse | Right stick |
| Roll (dodge) | Space | B |
| Attack (press again for the second hit) | Left mouse button | RB (or X) |
| Shield (hold) | Right mouse button | LB |
| Lock-on on/off | Q or middle mouse button | R3 (click the right stick) |
| Interact / mount Pegasus / land | E | A |
| Boost (flying) | Shift | RT |
| Pause | Esc | Start |

In flight: the left stick / WASD steer (left/right turns, up climbs, down dives); the camera follows behind Pegasus by
itself (the right stick and the mouse do nothing). Menus: A or Enter accepts, B or Esc goes back, and the D-pad, left
stick or arrow keys move the selection.

Combat basics:
- Lock-on switches on by itself when a fight starts. While locked on, the camera stays behind Hercules and on the boss.
  Hold a direction to the side to circle the boss: he runs along the circle with his chest turned toward it.
- The sword only hurts a weak point while it glows (orange, with a ring and arrow on screen). Any other hit glances
  off with a spark and a clang.
- The shield blocks quick blows from the front. It cannot stop a guard-breaking slam, a ground stomp or a fire sweep:
  roll out of those instead. A roll makes you invulnerable for a moment.
- Medusa's gaze turns you to stone. You can circle past the beam and cut her neck, or raise the shield facing her
  just before her eyes fire to reflect it back (a shield held up the whole time only blocks: no damage, no stun).
  If you stay close to her, her tail coils and a red ring lights up around her: roll out of the ring before it fills
  (about 1.8 s; roll twice if you were right beside her). Backing away while locked on is too slow.

## How a playthrough goes
1. **Title screen**: New game, Continue, Controls, Quit.
2. **Home island**: a green plateau with a temple, three trophy pedestals (one fills for each beaten boss), a sign that
   shows the controls, and Pegasus waiting. Walk to Pegasus and press interact to mount. The hop takes about a second:
   Hercules steps in, springs up beside the flank and swings over the back, and Pegasus spreads its wings as he sits.
   When you fly home later, Hercules rides Pegasus in and hops off beside it.
3. **Flight over the sea**: a compass strip points to the next open island and shows its distance. Each island whose
   boss you have not beaten shows that creature walking about on it (drawn larger so it reads from the air). Islands you cannot visit yet sit
   inside a dark storm wall. Open ones have a pillar of light. Fly into the island's landing ring to land.
4. **Boss fight**: the Quarry Isle (Cyclops) first, then the Sanctuary (Medusa), then the Volcano (Hydra). Each win
   shows **LABOR COMPLETE**, fills a trophy at home and opens the next island. A loss shows **DEFEATED** and restarts
   the fight.
5. **Ending**: beating the Hydra shows the ending card, then you can fly freely. Landing in the home ring takes you
   home.

The pause menu has Resume, Controls, Restart fight (in a fight), Return home and Quit to title.

## Known limits
- JC, the owner, played this build on the evening of Nov 23, after the fixes from his first play-test (sword grip,
  mount and dismount, flight camera and Pegasus's flight clips, creatures on the islands, strike effects and wounds,
  clipping), and said "Game looks good." Feel, difficulty, mouse camera and sound are still yours to judge.
- No settings menu: you cannot change mouse sensitivity, volume or invert-Y, or rebind keys.
- Animations. On Nov 23 every idle and every walk (and the hero's run) was keyframed again from a new reference video
  that starts from a natural stance, and every other clip had its frozen limbs moved off the rest pose and given life
  (`docs/briefs/anim_natural.md`, devlog chapter 12). What is still not right:
  - The Hydra's feet slide a little (about 0.45 m) when a turn on the spot starts or stops.
  - From straight behind, Hercules's shield hangs edge-on at his side in the idle. In the roll the shield passes
    through his body. Seen from the FRONT he holds the shield flat in the side-step and walk-back clips (the game camera
    is behind him in those).
  - The Cyclops's feet slide while his sweep turns him, and his arms cross his head or trunk for a moment in the slam
    and the sweep.
  - The side-step to the right is the left side-step with the legs mirrored (the sword stays in the right hand).
  - Circling a boss: his legs run along the circle while his chest and head stay turned toward the boss. That turn of
    the upper body is computed by the game (a twist of the spine on top of the run clip), not a keyframed clip.
  - During the mount and the dismount Pegasus spreads its wings level and the rider stays in view; at the first wing
    beat of the take-off the near wing hides most of the rider for about 0.15 to 0.2 s. Hercules has no mount clip: he
    blends from standing into the riding pose while he climbs.
  - Hercules carries the sword in a closed fist, blade forward and down beside his right leg. From the camera behind
    him it reads as pointing down and a little outward. In the reaching strike the flat of the blade, not the edge,
    leads for a moment just after the hit.
  - In flight, seen from behind, Pegasus's hind hooves show under its rump.
- At the start of the Cyclops fight he walks in right behind Hercules in the frame, so the hero's body hides part of
  the walk until he is close.
- A weak-point hit shows a sword trail, a star burst with a ring, ichor in a colour per boss (Cyclops gold, Medusa
  lime, Hydra cyan) and a glowing cut mark that stays until the fight ends (up to 12). The star is at full size from
  the first frame after the hit on all three bosses (60 fps recordings, Nov 23); the whole-body flash is now a light
  brightening, not white. In the volcano's glow the Hydra still turns pale pink for about 0.1 s. When Hercules stands
  beside the cut (the Hydra's lowered jaw) the burst is moved a little away from him and drawn behind him, at the same
  size. The sword trail is wider and stays longer than before; it reads on Medusa, but on the Cyclops's first hit,
  which lands early in the swing, it is short and hard to see.
- Hercules is kept out of the Cyclops's legs and stuck club and the Hydra's lowered head (probes: at most 0.05 m
  inside). His sword arm still goes into the Hydra's head when he strikes its jaw.
- From the air Medusa and the Hydra are small (about 40 px tall at 1280x720) and pass behind the near wing or the
  island's columns when you come close; the Cyclops walks beside your approach for about 5 s.
- Not recorded in motion by anyone: the new flight camera and the mouse in flight (only the left stick / WASD steer
  now), the Hydra's side bites and Medusa's tail swipe (the bots never trigger them). They were checked by probes and
  logs only.
- First-use freezes: every effect is drawn once while the island title card is up. In fully cold test runs on Nov 23
  (2 PM) the Cyclops fight had no frame over 50 ms (largest 26 ms) and the Hydra fight one 60 ms frame at the moment the
  fight starts (no shader compile); the wait under the black fade before an island is about 1.4 s longer the very first
  time.
- On the M5 Max test machine at 1920x1080 (120 Hz screen, vsync on) the three fights hold 119 to 120 fps: 8.3 to 8.4 ms
  per frame on average, 99 % of frames under 11.1 ms, and 2 to 5 frames over 16.7 ms in a whole fight. That was measured
  on Nov 23 at 1:36 AM with nothing else running, before the natural-animation pass (`docs/notes/build.md` 2.1 and 2.4).
- Flying over the sea with the creatures on the islands: 119 fps average (8.4 ms), the same with them switched off; on
  a busy machine 99 % of frames were under 12-14 ms.
- Medusa's tail: the red ring reaches 8.0 m from her body and fills in 1.8 s. One roll started up to 0.7 s after the
  ring appears clears it from 4 m or more (0 hits in 50 tries); right beside her it cleared 49 of 50. When you close in
  she backs off slowly, so hugging her brings the ring.
- Medusa's snake heads were recoloured to remove muddy brown patches; the snakes' eyes are pale green now, not yellow.
- Hydra: a locked-on strike aims at the lowered jaw. In the probe it hit from the front and from up to 90 degrees to
  the side at 1.2, 2.0 and 2.6 m, and missed at 3.0 m.
- The home and sea islands are built from simple shapes plus props, not sculpted models.
- The app is not notarized.

## Test flags (for automated runs)
Anything after `--` is passed to the game. Always pass `--harness` for test runs. In harness mode the game never saves
and never captures the mouse, and it prints one `[H] t=<seconds> event=<name> ...` line per event, ending with
`[H] result=victory|defeat|timeout|quit`.

```sh
# from the project
/Applications/Godot_4.7.2.app/Contents/MacOS/Godot --path game -- --start=cyclops --harness --bot=win
# headless and 3x faster
/Applications/Godot_4.7.2.app/Contents/MacOS/Godot --headless --path game -- --start=hydra --harness --bot=win --speed=3
# the exported app takes the same flags
builds/Hercules.app/Contents/MacOS/Hercules -- --start=cyclops --harness --bot=win
builds/Hercules.app/Contents/MacOS/Hercules -- --start=title --harness --quit-after=5
```

| Flag | Meaning |
|---|---|
| `--start=<id>` | First scene: `title`, `home`, `sea`, `cyclops`, `medusa`, `hydra`, `ending`, `test` (grey-box fight), `test_travel` |
| `--harness` | Test mode (needed for every flag below) |
| `--bot=win\|lose\|idle` | `win` plays the fight (or the home-to-island trip) from each boss's advice. `lose` stands still. `idle` does nothing |
| `--pad` / `--keys` | The bot sends Xbox-pad events / keyboard and mouse events instead of setting actions directly |
| `--speed=<x>` | Time scale (physics scales with it, so results match speed 1) |
| `--quit-after=<s>` | End after that many game seconds (`result=timeout`) |
| `--seed=<int>` | Random seed (default 1234567) |
| `--defeated=cyclops,medusa\|all` | Preset progress in memory (never saved). `--ending-seen` too |
| `--after-victory=<s>` | Keep running after a win, until `<s>` seconds into the next scene |
| `--shots=<dir>` `--shot-every=<s>` `--shot-on=<event>@<delay>[:<count>],...` | Screenshots (needs a window, 1280x720) |
| `--campaign` | With `--start=title --bot=win`: the whole game in one run (title, home, the three islands, ending, free flight) |
| `--fake-save` | The title acts as if a save exists (Continue shown, New game asks); nothing is written |
| `--probe=ui\|goto` | Menu and scene-switch self-tests |
| `--cam-debug`, `--sword-debug` | Extra camera and sword log lines |

Examples: the whole game is `--start=title --harness --bot=win --campaign --speed=3` (about 100 s of wall time
headless; add `--pad` or `--keys` to send controller or keyboard events). The full trip from home to the first fight
is `--start=home --harness --bot=win`. The ending is
`--start=sea --defeated=all --harness --bot=win --after-victory=3`. More flags, and the world module's own probes, are
in `docs/notes/core.md`, `docs/notes/core_followup.md`, `docs/notes/integrate_player.md` and `docs/notes/world.md`.

## Where things are
| Path | What |
|---|---|
| `game/` | The Godot project (`project.godot`, scripts, shaders, assets, `export_presets.cfg`, `icon/` = app icon and its generator) |
| `builds/Hercules.app` | The macOS build (not in git: export it, or rebuild with `builds/make_app.sh` copied from `docs/notes/build.md`) |
| `docs/SPEC.md` | Design and technical contract |
| `docs/notes/` | Notes from each part of the build. `build.md` covers export and performance |
| `docs/devlog/` | The devlog: every prompt, decision, timeline, screenshots and the video outline. Start at `docs/devlog/README.md` |
| `art_src/` | Character sheets, rigs, Blender files and reference videos |
| `tools/` | Animation kit, Blender scripts, generation and workflow scripts. `tools/probes/` holds the scripts that hold an input or show every clip of a character on one sheet; `tools/godot_bg/gdwin` runs the game off-screen, silent and without taking the keyboard focus (for tests while someone is using the computer; macOS only); `tools/clip_motion.py` counts the joints that move in every clip |
