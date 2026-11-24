# Brief — animkit (the animation-matching toolkit)

Read `docs/AGENT_RULES.md` first. You own `tools/animkit/**`, `tools/ak` and `docs/ANIM_PIPELINE.md`.

## Why
The owner's method for every animation in this game:
1. screenshot the real rigged 3D asset from the FRONT and the SIDE in Blender and stitch them into one split-screen sheet
   (already works: `tools/blender/render_split_sheet.py`, writes `cam.json` with the exact framing);
2. give that sheet to Seedance 2.5 (480p, 10 s) as the first frame and ask for the animation — the result is a split-screen
   video: left half front view, right half side view of the same motion;
3. keyframe the rig in Blender so its front and side views match the video frames.
The lead does step 2. You build the tools for step 3 so that ~35 animation agents (one per clip, each a vision model that can
look at images) can match a clip in about 20 tool calls. Make the tools boring, fast and hard to misuse.

## What to build (Python; Blender 5.2 headless; no OpenCV/scipy — numpy + Pillow + ffmpeg only)
`tools/ak <command> ...` = one launcher (shell or python) that runs the right backend:
plain `python3` for video/image work, `Blender -b --factory-startup --python tools/animkit/ak_blender.py -- ...` for rig work.
Every command prints one final line `###AK### {json}` and exits non-zero on failure.

1. `ak info <char.blend>` — bones (name, parent, rest head/tail in armature space, length, deform), chains, sockets from
   `rig.json` if it sits next to the blend, mesh stats. Also writes `<char>_bones.jpg`: front+side render with bone names
   drawn at the joints (Pillow) so an agent can learn the rig from ONE image.
2. `ak frames <video.mp4> --cam cam.json --times 0.5,1.0,... | --every 0.25 [--t0 a --t1 b] --out <dir>` — extracts frames,
   scales them to the cam.json size, saves full frames + a numbered contact sheet (<= 1024 px wide, timestamps drawn with Pillow).
   Also `--mask`: writes the character silhouette per panel (background = the sheet's bg colour, tolerance arg).
3. `ak pose <char.blend> --cam cam.json --pose pose.json [--target frame.png] --out cmp.jpg` — applies ONE pose, renders
   front+side with the SAME framing/look as the sheet, and writes a comparison image: target on top, render below, plus a
   50% overlay, plus silhouette IoU per panel in the JSON line. Must take < 6 s.
4. `ak bake <char.blend> --clip <name> --keys keys.json [--loop] [--fps 30]` — creates/replaces the Action `<name>` from a
   list of timed poses (seconds), Bezier interpolation, optional seamless loop (first pose copied to the end), root motion
   kept in place. Saves the blend (keep `<char>.blend` as the single library of all clips; write atomically: temp file then
   rename; one clip per call so parallel agents on DIFFERENT characters never clash; agents on the SAME character must not
   bake at the same time — provide `--out-action <file.json>` to export the baked action as JSON and `ak merge` to import many
   such files into the blend in one go. Parallel agents will use the JSON route.)
5. `ak strip <char.blend> --cam cam.json --action-json <file> | --clip <name> --video ref.mp4 --t0 a --t1 b --n 8 --out strip.jpg`
   — review image: N evenly spaced frames, reference on top, our render below, same framing. And `--mp4 out.mp4` side-by-side
   preview (render PNG sequence, assemble with ffmpeg).
6. `ak export <char.blend> --out <char>.glb --clips-json <char>_clips.json` — GLB with ALL actions (push each action to an
   NLA track; export_animation_mode NLA_TRACKS; verify the clip count in the written file with pygltflib), Y up, +Z front,
   plus the clips manifest of SPEC §8 (length, loop, events from `keys.json` "events" entries).
7. (only if 1-6 are solid and tested) `ak fit <char.blend> --cam cam.json --pose start.json --target frame.png --bones a,b,c`
   — coordinate-descent refinement of the listed bones' angles to maximise silhouette IoU in both panels. Ship it only if a
   synthetic test (render a known pose, perturb, recover) improves IoU; otherwise leave it out and say so.

## The pose format (the important design decision)
Agents look at a front view and a side view. So angles are given in the ARMATURE's fixed axes, not in bone-local axes:
```json
{"root": {"loc": [0, 0, 0], "rot": [0, 0, 0]},
 "bones": {"upper_arm_l": {"rx": 0, "ry": -60, "rz": 0}, "forearm_l": {"ry": -95}},
 "space": "absolute"}
```
- Axes (Blender, character faces -Y): X = character's left(+)/right(-) ... confirm and DOCUMENT the signs with a picture;
  Z = up; Y = back(+)/front(-). `ry` turns a bone in the FRONT view plane, `rx` in the SIDE view plane, `rz` is twist/yaw.
- "absolute": each listed bone's rotation is its total rotation away from its REST orientation, measured in armature space
  (applied as Rz * Ry * Rx on the rest orientation), independent of what its parent does. A bone that is NOT listed keeps
  its rest orientation RELATIVE TO ITS PARENT (it follows the parent rigidly).
- Also support `"space": "local_delta"` (same axes, but the delta is applied on top of the parent-following pose) because
  chains (tails, necks) are easier that way. Document both with one worked example each.
- `root.loc` in metres, `root.rot` degrees, for whole-body moves (roll, jump, fall, flight bob).
- Helper `"chain": {"name": "tail", "bend_side": [..per bone deg..], "bend_up": [...]}` for long chains.
Convert to pose-bone matrices yourself (matrix math in armature space; do not rely on euler modes of the bones).
Unit-test it: for random poses, read back each bone's world direction and compare with the direct rotation of the rest
direction (tolerance 0.5 deg).

## Look and framing
Renders must look like the sheet: Workbench, flat texture colour, same bg colour, orthographic, same pixels-per-metre
(read everything from `cam.json`). Hide helper meshes (bone custom shapes, e.g. Meshy's `Icosphere`: no material).
Props that are parented to bones (sword, shield, club) must render.

## Test asset
`art_src/chars/hercules/raw.glb` = Meshy auto-rigged Hercules (24 bones: Hips, Spine02, Spine01, Spine, neck, Head, Left/Right
Shoulder/Arm/ForeArm/Hand, Left/Right UpLeg/Leg/Foot/ToeBase; armature object scale 0.01; helper mesh `Icosphere`).
Make a throw-away test blend from it in `work/animkit/` (the rig agents are producing the real `art_src/chars/<id>/<id>.blend`
in parallel — do not touch those). The tools must not depend on bone names: read the armature.
A real reference video for a smoke test: `work/test/test_hercules_run.mp4` with `work/test/hercules_cam.json`
(may still be rendering when you start; if it is missing after 10 minutes, synthesize a test video by rendering a simple
animation of your own with `ak`).

## Done when
- `tools/animkit/tests/run_tests.sh` passes: pose math test, frames/mask test, pose render timing, bake -> strip -> export
  round trip (GLB reopened with pygltflib: clips present, skin present), loop seam test (first/last frame equal).
- `docs/ANIM_PIPELINE.md` explains the method for the owner's audience AND is the manual for animation agents: exact
  commands, the pose format with pictures, a 15-step recipe for matching one clip, common mistakes. Keep it under 250 lines.
- You matched ONE short clip yourself end to end as proof (e.g. 1 second of the run video: 5 key poses) and saved the strip
  in `docs/devlog/media_inbox/animkit/`.
Write a simple complete v1 of commands 1-3 within your first ~8 tool calls, then grow it in small steps with a test after each.
