# Asset check (asset check agent, 2026-11-22 ~21:25; owner away, decisions noted)

Task: after the `ak merge` stale-first-key fix (tools/animkit/ak_blender.py, 20:49:58), check every shipped character
GLB for loop-seam gaps and frame-0 floor offsets, rebuild any character over the limits (seam > 1 cm, floor > 2 cm),
and check that each manifest lists exactly the clips in its GLB with matching lengths.

**Result: all five characters pass. Nothing was rebuilt, re-imported or re-keyed; no file under art_src/chars/** or
game/assets/characters/** was changed by this pass.** "Before" and "after" are therefore the same numbers.

## Why they are clean
Every shipped GLB was exported AFTER the merge fix (fix 20:49:58; exports: medusa 21:04, pegasus 21:07, hydra 21:12,
cyclops 21:17, hercules 21:20). Medusa (fixer re-merged with the fixed tool), pegasus (fixer rebuilt), hydra (fixer
re-merged all 17 clips in one call with the fixed tool), cyclops and hercules (fixers merged one file per call).
The gaps reported in anim_pegasus_fix.md (medusa stunned 0.354 m, hydra walk 0.052 m, medusa slither 0.032 m) were
measured on earlier GLBs and are gone.

## Method (read-only, `work/asset_check/`)
- `scan.py <id> [glb]`: pygltflib + numpy forward kinematics and full linear-blend skinning of the shipped GLB.
  - seam = max world distance of any joint between the first and the last sample of each LOOP clip.
  - floor = lowest skinned vertex (Godot y) at frame 0 vs the clip's action JSON `ground[0].lowest_z`; also at every
    grounded key time (`floorK`), and |root joint offset from rest| vs |action JSON root.loc| at every key (`root`).
  - manifest: clip set and lengths vs the GLB animations.
- `dips.py`: lowest skinned vertex on every exported frame of every clip (informational, `dips.json`).
- Validation that the scan sees the bug: on the pre-fix backups it reports hydra walk seam **0.0515 m** (frame-0 floor
  +0.0515 vs JSON 0; `work/animfix_hydra/backup/hydra.glb`) and pegasus fly seam **0.2216 m**, frame-0 low -0.222 vs
  JSON -0.032 (`work/anim_pegasus_fix/backup/pegasus.glb`). Frame-0 lows on the shipped GLBs equal the JSON values to
  0.1 mm, which also proves the skinning math.
- Raw results: `work/asset_check/before_<id>.json`, `validate_*_old.json`, `dips.json`.

## Numbers (shipped GLBs; before = after)
| id | clips (GLB = manifest) | length mismatches | worst loop seam | worst frame-0 floor offset vs JSON | worst root key mismatch |
|---|---|---|---|---|---|
| hercules | 14 = 14 | 0 | 0.0000 m (6 loops) | 0.0000 m | 0.0042 m (roll, mid-key, not frame 0) |
| cyclops | 8 = 8 | 0 | 0.0000 m (3 loops) | 0.0000 m | 0.0000 m |
| medusa | 9 = 9 | 0 | 0.0000 m (3 loops: idle, slither, stunned) | 0.0000 m | 0.0000 m |
| hydra | 17 = 17 | 0 | 0.0000 m (3 loops: idle, walk, head_down) | 0.0000 m | 0.0389 m (death, mid-key; see below) |
| pegasus | 3 = 3 | 0 | 0.0000 m (3 loops) | 0.0001 m | 0.0000 m |

Frame-0 lowest points that are not 0 are authored, and equal their JSON: medusa stunned / rise -0.0089 m (lean recipe),
pegasus fly -0.032 m (fixer's note: hoof dips 3 cm at the wing top), pegasus glide +0.137 m (airborne), hercules ride
+0.190 m (seated rider; the ride action has no ground record), hydra fire_sweep / fire_sweep_return -0.0019 m.

Also checked: every manifest event lies inside its clip; manifest loop flags, lengths and events equal the action JSONs
(pegasus `fly` = `ridden/fly`, hercules `ride` = `art_src/chars/ride`); every socket bone is a joint of its GLB.

## Not merge problems (for the animation track; nothing done here, re-keying is out of scope)
- Hydra mid-clip key mismatches (bite 2.7 cm, bite_l/r 1.8 cm, death 1.6 cm, death_standing 3.4 cm at grounded key
  times): these clips were keyed at 24 fps and exported at 30 fps, so a 24 fps key such as 1.4167 s falls between GLB
  samples; frame 0 and the 30 fps-baked fire clips match exactly.
- Floor dips between keys (lowest vertex on any frame, < -2 cm): hydra death_standing -0.179 m at 3.83 s (unused
  clip), hydra bite -0.059 m at 1.47 s (2 frames at the strike), cyclops sweep -0.051 m at 1.0 s (10 frames),
  medusa death -0.043 m, cyclops pull_free -0.039 m, hydra fire_sweep_return(_l) -0.031 m, cyclops death -0.030 m,
  medusa rise -0.027 m, hercules death -0.023 m, hydra death -0.022 m. All others are within 2 cm.
  Small, mostly hidden by the outline and the camera; an animation fixer could re-ground those in-betweens.

## Decisions (owner away)
- No rebuild: the task makes a rebuild conditional on a seam > 1 cm or a frame-0 floor offset > 2 cm, and none exists.
  Rebuilding unchanged sources would only risk new differences, so the shipped files stay as they are, and no Godot
  re-import or probe re-run was needed (the GLBs and their .import files are unchanged since the fixers' probes passed).
