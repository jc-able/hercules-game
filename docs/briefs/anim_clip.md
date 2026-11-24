# Brief — animate the clips of ONE reference video (one agent per video)

Read `docs/AGENT_RULES.md`, then `docs/ANIM_PIPELINE.md` (the manual for `tools/ak` — follow its 15-step recipe).
Your prompt names the character `<id>`, the video `<video>` and the game clips to cut from it.

## What you have (read-only)
- `art_src/chars/<id>/<id>.blend` — the rigged character (never write to it; other agents use it at the same time).
- `art_src/chars/<id>/clips/<video>/cam.json` + `sheet.png` — the exact framing and first frame THIS video was generated
  from (framings differ per video: use these two files for every `ak` call, never another clip's or the character-level ones).
- `art_src/chars/<id>/rig.json` — bones, chains, sockets, notes from the rigger. `docs/notes/rig_<id>.md` — rig limits.
- `art_src/chars/<id>/clips/<video>/ref.mp4` — the Seedance 2.5 reference (480p, 10 s, left = front view, right = side view),
  `ref_sheet.jpg` (2 frames per second overview) and `prompt.txt` (what the video was asked to show, with the timing).
- What the game needs from each clip: `docs/SPEC.md` §2-§3 (durations and what the move means) and §8 (events).

## What you produce (in `art_src/chars/<id>/clips/<video>/`)
For EACH clip named in your prompt: `keys_<clip>.json`, its pose files (`poses_<clip>/k*.json`), `action_<clip>.json`
(from `ak bake ... --out-action`), `strip_<clip>.jpg` (from `ak strip`), and one line in `notes.md`:
clip, video window used (t0-t1), key count, IoU per key, length, events, what does not match and why.
Scratch goes in `work/anim/<id>_<video>/`.

## How to cut clips from the video
- Many videos show the move twice: use the cleaner take. Skip the first ~0.5-1 s (the character settles out of the sheet pose).
- Loops (idle, run, strafe, walk, slither, fly, glide, stuck, stunned, block_idle, head_down): one clean cycle found with
  `ak cycle`; `"loop": true`; the seam must be invisible. Idle-type loops may be slowed to 2-4 s cycles with small motion.
- One-shots (attacks, roll, hit, hurt, death, slam, sweep, gaze, stomp, bite, ...): start from and return to the ready /
  idle pose of that character when the move allows it (death, stun_start, slam->stuck end in their own pose).
  A video with several clips in a row (e.g. slam -> stuck -> pull_free; stun_start -> stunned -> rise; fire_sweep ->
  head_down -> head_up; attack_1 -> attack_2; block_start -> block_idle): the LAST pose of one clip must equal the FIRST
  pose of the next (reuse the same pose file), so the game can chain them.
- Keep everything in place: no travel across the floor (the game moves the body). Vertical motion and leans are fine.
  A roll turns the body with `root.rot` and ends upright at the start position.
- Events (clip time, seconds) in `keys.json` "events": attack_1 / attack_2 `active_start`, `active_end` (blade moving
  through the target zone); sweep, slam, tail_swipe, stomp, bite `impact`; gaze `fire_start`, `fire_end` (the held stare);
  fire_sweep `fire_start`, `fire_end` (the sweep with the mouth open). Natural timing from the video; the game re-times.

## Quality bar
- Key poses line up with the video in BOTH panels (IoU about 0.75+ where the model's proportions allow; say when a
  creature's redraw in the video makes that impossible). Read every `ak pose` comparison you rely on.
- In-betweens are clean in the strip: no limb through the body, no pops, no flipped twists. Add keys where needed.
- Weapons follow the hands (they are parented in the blend): check the sword / shield / club reads correctly.
- Long chains (hydra necks, medusa tail and snakes, pegasus wings, tails): use the `chain` helper / local_delta. Match the
  acting part (the centre head, the striking tail, the wings) and the body to the video; give the other chains believable
  secondary motion with phase offsets (heads that all move identically look dead). Nine necks cannot all be traced: say what
  you traced and what you authored.
- If the reference is unusable (layout broken, views out of sync, wrong move), do not invent a match: say so in your final
  answer with the timestamps, and still deliver the best clip you can author from the usable parts.

## Limits
At most ~20 image reads (<= 1024 px each): contact sheets and comparison images, not single frames. 4-8 keys per clip is
normal. `ak fit` after a rough pose saves rounds (about 30 s per 10 bones). Check free memory before Blender runs, as in AGENT_RULES.
Final answer: per clip — file paths, window, keys, mean IoU, length, events, honest problems.
