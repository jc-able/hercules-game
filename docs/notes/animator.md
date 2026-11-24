
## hercules walk_back (2026-11-22)
- Request for animkit: `ak fit` refuses aim-form bones (front/side). Workaround used: bake a 2-key action from the aim
  pose and read it back with `ak pose --from-action --t 0 --save-pose` (gives rx/ry/rz), see
  `work/anim/hercules_walk_back/conv.sh`. A `--to-euler` option on `ak pose` (or aim support in fit) would save this.

## medusa idle (2026-11-22)
- `chain` helper on the tail overrides absolute entries of the same links (tail_04/tail_05 absolute rx were replaced by the
  chain's local_delta 0 and the floor tail lifted 13 cm). Workaround: per-bone local_delta `rz` on tail_06..14 instead.
  Suggest: chain entries of 0 should not override listed absolute bones, or ak should warn.
- Medusa idle video: Seedance draws the side-view tail past the side panel into the front panel, capping full-frame IoU ~0.78.
  I scored the upper body (z > 1 m) separately with `work/anim/medusa_idle/ubiou.py`; an `--ignore-below` option on
  `ak pose` / `ak fit` would help for serpent tails.

## pegasus glide (2026-11-22)
- **animkit bug, affects every Pegasus clip:** `akimg.silhouette` treats colourful pixels (chroma > 0.10) as character,
  so on the green `--bg` split sheet the background is masked as character (93% of the frame). `ak pose` IoU reads
  ~0.93 for any pose, `ak frames` calibration and `ak fit` are meaningless. Workaround (no tool edit):
  `python3 work/anim/pegasus_glide/akg.py <ak args>` swaps in a green-key silhouette (bg = g - max(r,b) >= 0.08). Suggest
  akimg uses `cam['bg_srgb8']` (or the bg colour of the sheet) to key the background when the sheet bg is coloured.
- Seedance's pegasus glide video does not start from the sheet (frame 0 already in the glide pose, divider centred),
  so bounds calibration fails; calibrating against a render of a first rough pose (`--sheet <render-out png>`) works.
- `work/anim/pegasus_glide/aim2euler.py in.json out.json` converts aim-form bones to rx/ry/rz (same maths as
  ak's aim_rotation) so `ak fit` accepts them; checked against ak info rest angles.

## hydra stomp (animator, 2026-11-22)
- The stomp reference (art_src/chars/hydra/clips/stomp/ref.mp4) has a STATIC side panel in both takes (1.0-4.5 s and 4.5-8 s): the foreleg lift only shows in the front panel. The clip was delivered with the side motion authored. If the lead wants a traced side view, regenerate the video (credits: lead only) with a prompt that names the side-panel leg motion explicitly, e.g. "in the RIGHT panel the near foreleg rises forward to chest height".
