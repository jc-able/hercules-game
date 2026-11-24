# Pegasus assembly (assembler, 2026-11-22)

The owner was away, so this agent made the decisions below and notes them here. Scratch: `work/assemble_pegasus/`.

## Result
- `game/assets/characters/pegasus/pegasus.glb`: 7.12 MB, 1 skin with 43 joints, 1 embedded PNG albedo, 1 mesh
  (69,986 triangles), 3 clips at 24 fps. Mesh bounds in Godot: 2.29 m wide, 2.99 m tall (wing tops), 2.95 m long,
  feet on y = 0, head toward +Z.
- `game/assets/characters/pegasus/pegasus_clips.json`: clips, sockets, socket offsets, `size` and `rider`.

| clip | length | loop | events | source |
|---|---|---|---|---|
| idle | 7.000 s | yes | none | `art_src/chars/pegasus/clips/idle` (as matched) |
| fly | 1.0417 s | yes | none | `art_src/chars/pegasus/ridden/fly`: the matched fly with both wings swept 25 deg forward (see below) |
| glide | 3.000 s | yes | none | `art_src/chars/pegasus/clips/glide` (as matched) |

SPEC §8 lists idle, fly and glide, and all three are present. `docs/anim_clips.json` also plans `pegasus:fly_ridden`
from the ride video. The ride animator did not make a Pegasus action: `art_src/chars/ride/clips/ride/` holds only the
hercules `ride` action. So the GLB has no separate `fly_ridden` clip. The game's `fly` is the rider-safe clip instead,
because the game only flies Pegasus with Hercules on board.

## Wing clearance (the main decision)
- Check: `art_src/chars/pegasus/ridden/pair_check.py`. It runs on a temporary copy of `art_src/chars/ride/ride.blend`
  (the copy was deleted afterwards). It applies the baked Pegasus action and the baked hercules `ride` action, timed
  so that one rider loop spans one fly loop, with both starting at the wing top. Glide and idle use the rider at
  0.4x. On every sampled frame it counts triangle overlaps between the Pegasus WING region and the rider's body,
  sword and shield.
- Matched clips:
  - `fly`: hits on 10 of 25 frames, up to 598 triangle pairs (thighs and shins). The hits come at the wing top, the
    spread and the start of the downstroke (clip t 0-0.33 and 1.0). The folded-back hanging feather lobe passes
    through his legs.
  - `glide`: 0 hits on 36 frames.
  - `idle`: 0 hits on 42 frames, including the wing spread.
- The ~10 deg sweep from ride_anim.md is not enough on this fly clip. ride_anim.md measured it on a different wing
  family, the make_poses extremes.

  | forward sweep | result |
  |---|---|
  | 10 deg | 8 frames hit, up to 500 pairs |
  | 15 deg | 2 frames hit, up to 395 |
  | 20 deg | 1 frame hits (k2, mid_down, t 0.333): 211 |
  | 15 deg with 25 deg on k2/k2b | hits at frame 7.5 |
  | **25 deg on all keys** | **0 hits at 50 samples per beat (every half frame)** |

- Chosen: a uniform 25 deg sweep. `make_ridden.py` adds it as an outermost body-frame Rz on every wing bone the pose
  gives in absolute space: `rz -= 25` for the left wing and `rz += 25` for the right. The local_delta wing_02 curls
  ride along.
  - Cost: the strip IoU against the fly reference video drops from 0.708 to 0.645 (green-key `akg` wrapper).
  - By eye (`ridden/fly/strip_fly_ridden.jpg`), the wing tops now reach a little in front of the withers, and the
    wings do not cut through the neck.
- Results are in `ridden/fly/pair_check_matched.json` and `ridden/fly/pair_check_trials.json`.
- Rebuild, from the repo root:
  1. `python3 art_src/chars/pegasus/ridden/make_ridden.py art_src/chars/pegasus/clips/fly/action_fly.json 25 art_src/chars/pegasus/ridden/fly`
  2. `tools/ak bake art_src/chars/pegasus/pegasus.blend --clip fly --keys art_src/chars/pegasus/ridden/fly/keys_fly.json --loop --fps 24 --out-action art_src/chars/pegasus/ridden/fly/action_fly.json`
  3. `tools/ak merge art_src/chars/pegasus/pegasus.blend art_src/chars/pegasus/clips/idle/action_idle.json art_src/chars/pegasus/clips/glide/action_glide.json art_src/chars/pegasus/ridden/fly/action_fly.json`
  4. `tools/ak export art_src/chars/pegasus/pegasus.blend --out game/assets/characters/pegasus/pegasus.glb --clips-json game/assets/characters/pegasus/pegasus_clips.json`
  5. `python3 art_src/chars/pegasus/ridden/finish_manifest.py`

  Do NOT merge `clips/fly/action_fly.json` together with the ridden one: both carry the clip name `fly`.
- The remaining base-pose contacts (inner thighs into the flank, skirt into the back) are rider-vs-body contacts and
  are documented in ride_clip_check.md. They are not wing contacts.

## Manifest fixes (mechanical, my file)
- **Socket offsets frame.**
  - The problem: rig.json gives `socket_offsets` in ARMATURE axes relative to the bone head, but
    `CharacterVisual._make_sockets` applies them in the BONE frame. The raw head offset would have put the head
    socket in the wrong place.
  - The fix: the offsets are converted with the rest bone matrices from pegasus.blend and written with
    `"offset_space": "godot"` (loc as is, identity basis).
- **Saddle socket = the rider's hips seat point.**
  - The problem: the game glues the rider's hips bone onto the `saddle` socket
    (`IslandProxy.seat_rider`), but the saddle bone head lies ON the back. With offset 0, his hips would have sunk
    0.247 m into the horse, 0.20 m too far forward.
  - The fix: the socket is now at bone-frame (0, 0.2471, -0.20), which is the ride.json seated pose.
  - In Godot: saddle socket (0, 2.127, -0.300) at rest. Head socket (0, 2.450, 1.250) = middle of the skull.
- **`rider` block:**
  - `offset`: the hercules scene root relative to the saddle socket, (0.0041, -1.0836, 0.0299), identity rotation.
  - `offset_from_saddle_bone_head`: the ride_game.json form.
  - `beat_period_s` 1.48 (ride video) and `rider_clip` "ride".
  - `fly_beat_s` 1.0417, `rider_speed_on_fly` 1.44, `rider_speed_on_glide` 0.4, plus the phase rule.
- **`size`:** height 2.994, withers 1.9, length 2.945, width 2.287 (m).

## Godot proof (work/assemble_pegasus/probe.gd, windowed 1280x720 via --script, `PROBE ok=true`)
- `create("pegasus")` loads the real GLB (standin=false, 1 toon material). `model_top` 2.994.
- Every clip:
  - `has_clip` is true and `clip_length` equals the manifest and the AnimationPlayer length.
  - Loop mode is linear.
  - `event_time` falls back correctly (no events).
- Both sockets are BoneAttachment3D.
- Chase-camera shots (fly top, fly downstroke, glide, idle) with the res:// hercules seated by the same hips-to-socket
  math as `IslandProxy.seat_rider` (hips land exactly on the socket):
  - Pegasus is upright, faces away from the camera (+Z forward) and is 3 m tall.
  - It has the toon look with the ink outline. No exploded mesh.
  - The rider sits on the back, holding his sword and shield, with the wings outside his legs.
  - Shots: `work/assemble_pegasus/shots/`. Devlog: `docs/devlog/media_inbox/assemble_pegasus/`.
- `--start=sea --harness --bot=idle --quit-after=6` (headless) runs with the real assets and no errors.

## Requests / notes for other modules
- **world (pegasus_flight.gd, home_base.gd):**
  - The rider plays `ride` at 1.0x and free-runs. To match the wing beat:
    - Use `rider_speed_on_fly` (1.44; x1.25 more while boosting, like the fly clip).
    - Re-sync the phase each fly loop: `rider_pos = fmod(fly_pos / fly_beat_s, 1) * 1.5`.
    - Use about 0.4x during glide.
  - The rider's motion is small (<= 3 deg), so this is polish.
  - world.md says the hips were checked "on the saddle bone". With this manifest he now sits 0.25 m higher, which is
    where ride.json seats him. Re-check `--world-glb` shots if any were taken with an older manifest.
  - Chase camera: at the rest pose, Pegasus's lower legs fall off the bottom edge of a 1280x720 frame (lower third
    framing). This is a framing choice; flagged for information only.
- **core:**
  - Nothing is needed in CharacterVisual.
  - For probes: a `--script` SceneTree cannot preload `res://scripts/world/island_proxy.gd`, because it references
    the `Game` autoload identifier and fails to compile. The probe copies the two helpers instead.
- **glide** (cosmetic, no fix): at the widest key, a few right-wing primary tips poke out of the outline as a thin
  spike in the chase view.

## Files written
- `art_src/chars/pegasus/pegasus.blend`: the merged actions idle, glide, fly. The blend held no actions before.
  The pre-merge copy is `work/assemble_pegasus/pegasus_before_merge.blend.bak`.
- `art_src/chars/pegasus/ridden/`: make_ridden.py, pair_check.py, finish_manifest.py, and
  fly/{keys_fly.json, poses/, action_fly.json, strip_fly_ridden.jpg, pair_check_*.json}.
- `game/assets/characters/pegasus/`: pegasus.glb + pegasus_clips.json. The Godot import made the .import files and
  the extracted albedo.
- No Higgsfield credits used.
