# Rules for every agent on the Hercules build

Read `docs/SPEC.md` (the contract) and your brief in `docs/briefs/`. Then make a trivial tool call first (e.g. `ls`).

## THE OWNER IS AT THIS MAC — nothing you launch may disturb the person using this computer
(Shared-machine mode. During the original build the owner worked and play-tested on the same computer while the agents
ran.) No window may appear on the screen, nothing may take the keyboard focus, nothing may make a sound.
- A Godot run that needs rendering (screenshots, movies, frame times): ONLY through the wrapper
  `tools/godot_bg/gdwin <the same arguments you would give Godot>`. It puts the window off-screen, never takes the
  focus, shows no Dock icon and is silent. Example:
  `tools/godot_bg/gdwin --path game --resolution 1280x720 -- --start=cyclops --harness --seed=11 --shots=$PWD/work/<role>/shots --shot-every=0.5`
  Never start the Godot binary without `--headless` any other way, never use `open`, never AppleScript / `osascript`.
  Headless runs (`Godot --headless ...`) are unchanged. Blender stays headless as below.
  The exported app (`builds/Hercules.app`) cannot be injected (hardened runtime): run it only with `--headless`; for a
  rendered check of the exported game use the editor binary on its pck: `tools/godot_bg/gdwin --main-pack builds/Hercules.app/Contents/Resources/Hercules.pck ...`.
- Do NOT rebuild, replace, move or delete `builds/Hercules.app` and do not run `builds/make_app.sh` (the person at the
  computer may be running the app). The lead rebuilds at the end.
- Never touch `~/Library/Application Support/Hercules/` (the player's save and caches). A test that needs a cold shader cache
  or a save file uses a throwaway home ON THE SAME COMMAND LINE:
  `HOME=$PWD/work/<role>/home CFFIXED_USER_HOME=$PWD/work/<role>/home tools/godot_bg/gdwin ...` (make the folder first).
- At most 2 heavy jobs at once per agent (a Blender render, a rendering Godot run). A play-test on the same computer shares the GPU.
- Stop only a process you started, by the PID you saved, after checking its working folder is yours
  (`lsof -a -p <PID> -d cwd`). Never `pkill` / `killall`.

## Paths
- Repo: `~/HerculesGame` (the original build kept it outside any cloud-synced folder; use the path of your clone). Godot project: `game/`. Scratch: `work/<your-role>/` (git-ignored).
- Never write under `~/Desktop`, `~/Documents` or `~/Downloads` (cloud-synced on the build machine). Never modify `art_src/sheets` or `art_src/reference_video`.
- Godot: `/Applications/Godot_4.7.2.app/Contents/MacOS/Godot` (never `/Applications/Godot.app`, that is 4.6.3).
- Blender: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script> -- <args>` ALWAYS
  headless with `--factory-startup`. A Blender window the person at the computer has open may hold another project:
  never connect to it, never use a Blender MCP / live-Blender tool, never `open` a .blend file (it would land in that window).
- Python: `python3` (3.14, has numpy, Pillow, trimesh, pygltflib; no OpenCV, no scipy). `ffmpeg`/`ffprobe` are installed
  (no drawtext filter: draw text with Pillow).

## Processes and memory
- Before each Blender or windowed Godot launch, check that there is enough free memory (about 4 GB per job; the
  original build used a small free-memory gate script that is not part of this repo). Never run more than 3 heavy jobs at once yourself.
- Stop only processes you started, by the PID you saved (`cmd & echo $!`). Never `pkill` / `killall` by name.
- Never edit a shell script that may still be running: write a new file name.
- Long commands (> 90 s) go in the background; poll with short calls. A silent agent is killed after 180 s.
- When you finish, stop every process you started.

## Images
- Before you `Read` an image make sure its long side is <= 1024 px (`sips -Z 1024 in.png --out small.png`).
- At most ~20 image reads per agent. Prefer one contact sheet over many single frames.

## Code and files
- Edit only the files your brief gives you. Requests for other modules go in `docs/notes/<your-role>.md`.
- Do NOT `git commit`, `git add`, `git stash` or switch branches: the lead commits.
- Do not write files named REPORT*.md or FINDINGS*.md (the harness refuses them). Return findings in your final
  answer; durable notes go in `docs/notes/<your-role>.md`.
- GDScript: Godot 4.7 syntax, typed where cheap, tabs for indentation. After adding a `class_name` script run
  `Godot --headless --path game --import` once. A change is not done until
  `Godot --headless --path game --quit-after 2` (or the harness run in your brief) prints no SCRIPT ERROR / Parse Error.
- Godot test runs always carry `-- --harness` (no save file, no mouse capture). Never run the game without it.
- Original content only: no names, logos, quotes or UI wording from existing games or films.

## Higgsfield credits
- Only the lead spends credits (3D, video, image, audio generation). If you need a generation, describe it in your
  final answer or in `docs/notes/<your-role>.md`.

## Devlog
- When you finish something a viewer would want to see (a first render, a before/after, a failure and its fix),
  save a JPEG (<= 1600 px) in `docs/devlog/media_inbox/<your-role>/` and add one line to
  `docs/devlog/media_inbox/<your-role>/captions.txt`: `file | what it shows | numbers`.
- Record real numbers (triangles, bones, seconds, IoU scores). Record mistakes and how you fixed them.
