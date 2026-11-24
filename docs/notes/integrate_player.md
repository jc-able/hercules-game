# Hero + shared visuals integration (integrate_player, 2026-11-22; owner away, decisions marked **Decision**)

Files changed (all mine): `game/scripts/visual/character_visual.gd`, `game/scripts/player/player.gd`,
`game/scripts/player/player_camera.gd`, `game/scripts/combat/sword_hitbox.gd`, `game/scripts/combat/weak_point.gd` (one line:
group `weak_point`), `game/shaders/outline.gdshader`, `game/scripts/data/tuning.gd` (player + camera keys only),
`game/scripts/test/dummy_boss.gd` (bot stand point). No asset imports, no class_name added, no other module touched.
Scratch, probes and logs: `work/integrate_player/` (tools/blade_probe.gd, tools/look_probe.gd, tools/runfights.sh, logs/, shots_*).

## 1. Requests addressed to core / CharacterVisual - status
| From | Request | Status |
|---|---|---|
| assemble_cyclops | `model_top()` counted the club (11.45 m, camera arm 9.86 m) | done: meshes under a BoneAttachment3D are props, skipped by `model_top()` and `model_top_points()`. Cyclops now 8.000 m, 22 top points |
| assemble_hydra C1 | `set_speed(s)` without restarting the clip | done (`set_speed`, `get_speed`); anim_hydra_fix says hydra no longer needs it, the hero uses it |
| assemble_hydra C2 | doubleSided GLB materials lose their back faces (toon is cull_back) | done: `CULL_DISABLED` source material -> toon copy with `cull_disabled` (`CharacterVisual.toon_shader(true)`, made once from the same code). Hydra and hercules both export doubleSided |
| assemble_hercules / anim_hercules_review_fix 1 | locomotion playback = ground speed / manifest move_speed, clamp 0.6-2.5 | done (`CharacterVisual.move_speed(clip)` + `set_speed`), see §3 |
| anim_hercules_review_fix 2 | play `block_end` when the shield is lowered | done (0.25 s, plays out while standing; moving cross-fades into locomotion) |
| anim_hercules_review_fix 3 | drop sword/shield at death `events.drop_props` (2.1 s) | done: `CharacterVisual.drop_props(parent, floor_y)` - props leave the sockets and settle flat on the floor in 0.4 s |
| anim_hercules_review_fix 4 | backward roll | done: `play(roll, blend, -speed)` plays it in reverse (new: negative speed = backwards from the end) |
| anim_hercules_review_fix 5 | hit at 0.458 / 0.4 so the flinch ends on idle | done |
| anim_hercules_review_fix decision | ATTACK_CHAIN_FROM must stay 0.40 | kept 0.40 (attack_1 chain pose at clip 0.917 = game 0.40 s) |
| assemble_pegasus | nothing for core | - |
| anim_fix_cyclops / animfix_medusa / anim_hydra_fix A1-A5 / anim_pegasus_fix + ride_anim | requests for the cyclops, medusa, hydra and world modules | not mine (module files); unchanged |

## 2. CharacterVisual with real models
- Loop flags and events from `<id>_clips.json` (as before); new `move_speed(clip)` (manifest `move_speed`, 0 = unknown).
- Playback: `play(clip, blend, speed)` - negative speed plays from the end backwards; `set_speed(s)` changes the rate of
  the clip that is playing; petrify freezes through the same path (`speed_scale` 0) and restores the current rate.
- Sockets: BoneAttachment3D + manifest `socket_offsets` (`offset_space` blender | godot) - unchanged and checked on screen:
  hercules sword in `hand_r`, shield on `forearm_l` (face out); cyclops club rides joint `hand_u_r` inside its GLB
  (node `cyclops_rig/Skeleton3D/hand_u_r/club`, a BoneAttachment3D: the upper right hand). Pegasus saddle/head as built.
- `model_top()`: rest-pose bounds of the skinned body only (BoneAttachment meshes and later attachments excluded).
  hercules 1.900, cyclops 8.000 (was 11.45), medusa 6.5, hydra 14.38, pegasus 2.994.
- Toon on every real model and prop: GLB albedo texture x factor (a near-black factor next to a texture is ignored, so a
  texture is never darkened), banded sun, soft rim, flash/tint/petrify uniforms as before.
- Ink outline: real models and their props now use a screen-constant line (`OUTLINE_PX` 2.2 px at 720 p, i.e. it scales
  with the output resolution) clamped to [0.004 m, 0.012 x model height]: hero max 0.023 m, cyclops 0.096 m, hydra 0.17 m.
  Same look on a 1.9 m hero at 4 m and a 14 m hydra at 25 m. `outline.gdshader` got `px_width` / `min_width` (default 0 =
  the old metre width, so EnvKit props, arenas and stand-ins are unchanged).
- Petrify on the real hero: frozen pose + cool stone + grey ink (devlog `hero_petrified.jpg`); flash unchanged.

## 3. Hercules in play
| State | Clip | Notes |
|---|---|---|
| idle | idle | 0.2 s blend in |
| free run (6.0 m/s) | run x1.65 (6.0 / 3.64) | exact, below the 2.5 cap |
| locked, forward (4.6) | run x1.26, body turned toward the move direction | |
| locked, side-step | strafe_l / strafe_r up to 1.8 m/s (x2.5) | **Decision** below |
| locked, full-speed side input > 0.3 s | run x1.26 at 4.6 m/s, body turned into the run (max 95 deg: never the front to the camera) | |
| locked, backing away | walk_back x2.0 at 2.4 m/s | **Decision** below |
| roll | roll x1.01; locked side rolls turn the body onto the roll line; backward rolls play the clip reversed | free mode with no input no longer spins the hero to face the camera |
| attack_1 -> attack_2 | x2.27 / x1.28; active 0.202-0.312 s and 0.195-0.357 s (manifest events / speed) | chain at 0.40 s |
| block | block_start (0.25) -> block_idle; release -> block_end (0.25) | re-press during the 0.1 s lowering goes back to block_idle |
| hit | hit x1.146 (0.458 / 0.4) | |
| death | death; sword + shield dropped at 2.1 s | |
| petrified | frozen current pose + stone | |
`facing` (shield arc, lock, camera) always stays on the boss while locked; only the visual turns (`visual.rotation.y`, 900 deg/s).

**Decision - locked-on speeds vs. skating.** SPEC §2 says 4.6 m/s locked on; the strafe clip carries 0.72 m/s and
walk_back 1.2 m/s at x1, so 4.6 m/s would need x6.4 / x3.8 (heavy skating). The fixer asked to cap sideways at ~1.8.
Capping all circling at 1.8 m/s would break the dodges the bosses are built around (hydra "circle toward the shoulder
while it inhales", medusa "circle past the fan"), so: a side-step uses the strafe clip at <= 1.8 m/s; holding a full side
input for 0.3 s turns the hero into a circling run at the SPEC 4.6 m/s on the run clip (no skating either way); backing
away is capped at 2.4 m/s (walk_back x2.0) - the roll covers fast retreats. Numbers: `Tuning.LOCK_STRAFE_SPEED`,
`LOCK_STRAFE_TIME`, `LOCK_BACK_SPEED`, `LOCO_ACCEL`, `VIS_TURN_DEG`, `ANIM_SPEED_MIN/MAX`.

**Decision - the sword hit volume follows the real blade.** `SwordHitbox.follow(socket, sword_prop)`: a capsule from the grip
(hand_r socket) to the blade tip (sword vertex farthest from the grip, 0.77 m) + `SWORD_TIP_EXTRA` 0.7 m, radius
`SWORD_HIT_RADIUS` 0.45 m, swept between physics frames (up to 10 sub-steps) so the 90-160 ms swing cannot skip a target.
Weak points are tested as spheres (group `weak_point`), boss bodies with a shape query (glance). Only inside the scaled
active window. Measured blade (hero-local, attack_1 active): a flat slash at 1.4-1.7 m height reaching 1.4 m ahead;
attack_2: an overhead chop from 2.6 m down to 0.5 m, 1.1-1.4 m ahead. The extra reach/radius was tuned so the bots'
existing approach distances (`SWORD_REACH + radius` formulas in cyclops/medusa/hydra) still connect: with the bare blade
(r 0.3, +0.15) the dummy fight never landed a hit and the hydra took 174 s. Stand-in hero: the old box.
Harness flag `--sword-debug` prints `event=swing gap=<m> point=<id(x,y,z)> y=<blade height> struck=` per swing.

## 4. Camera (lock-on) - compared with art_src/reference_video/key_cyclops.png
Before: arm 6.5 m, camera 2.4 m above the feet, aim between hero and boss -> hero ~20 % of the frame height, mid-frame.
After: `CAM_LOCK_DISTANCE` 3.7 m, `CAM_LOCK_HEIGHT` 1.3 m (chest height, the reference horizon crosses the hero's chest),
the view axis takes the highest elevation that keeps the hero's feet 2.5 % above the boss bar, so the hero stands in the
lower centre (~36-38 % of the frame height) and the boss towers above him; the arm grows at most `CAM_LOCK_MAX_EXTRA`
1.0 m (was 3.5) when the boss's top would not fit - past that the top is cut (low camera tilting up, not pulled back).
Cyclops: axis +8 to +10 deg, arm 3.7 m (4.5 m only when the hero stands under him); whole giant + club in frame.
Hydra: arm grows to 4.7 m, heads cut when the hero is under them. Free camera: `CAM_DISTANCE` 6.5 -> 5.0 m.
Devlog: `docs/devlog/media_inbox/integrate_player/camera_before_after.jpg` (before | after | reference).

## 5. Proof (logs in work/integrate_player/logs/, final pass = z_*.log + f_*.log, regress_final.txt)
| Run | Result |
|---|---|
| test --bot=win --speed=3 seeds 11 / 4242 | victory 17.07 / 17.07 s, 4 strikes, 0 hits |
| cyclops --bot=win --speed=3 seeds 11 / 4242 | victory 36.86 / 32.97 s, 8 strikes in 8 swings, 0 hits |
| medusa --bot=win --speed=3 seeds 11 / 4242 | victory 23.73 / 22.89 s (no regression) |
| hydra --bot=win --speed=3 seeds 11 / 4242 | victory 92.31 / 92.30 s, 8 strikes in 19 swings (was 86.5 s with the box) |
| cyclops --bot=lose / test --bot=lose | defeat, arena rebuilt, `fight_start` again |
| cyclops --bot=win --pad | victory 36.86 s |
| home --bot=win (home -> sea -> cyclops) | victory, rider props fine |
| windowed --shots test / cyclops / hydra / medusa | hero on-model, sword in hand, shield on forearm, run/block/roll/attack visible, camera as above |
No SCRIPT ERROR / Parse Error / WARNING in any of these logs.

## 6. For boss / world integrators
- **Sockets:** `visual.socket(&"name")` = a Node3D under a BoneAttachment3D with the manifest offset; parent props/VFX/weak
  points to it. Props exported INSIDE a GLB (the cyclops club) ride a BoneAttachment3D the importer made; find them by name
  (`visual.find_child("club", true, false)`), e.g. club head = `club.global_transform * Vector3(0, 5.05, 0)`.
- **Events:** `visual.event_time(clip, &"impact", fallback)` is CLIP time; at playback speed s the game time is t / s.
- **Speed:** `visual.play(clip, blend, speed)` (negative = backwards); `visual.set_speed(s)` re-times the running clip
  (e.g. stretch fire_sweep between fire_start and fire_end); `visual.move_speed(clip)` for walk loops (cyclops/hydra
  manifests have no move_speed yet: add it in the manifest or pass the measured value: cyclops walk ~0.95 m/s).
- **Bounds:** `visual.model_top()` / `model_top_points()` = skinned body at rest, props excluded; `BossBase.frame_top()` and
  `frame_top_points()` (world) feed the camera. Do not add props to the top: the camera cuts the top on purpose when
  the boss is close.
- **Props:** `visual.attach_prop(socket, path)` (toon + ink applied); `visual.drop_props(scene, floor_y)` drops all of them.
- **Ink:** real models get the screen-constant line automatically; module meshes made with `make_toon(...)` keep metres.
- **Sword reach for bot advice:** the real blade volume reaches about 1.4 + 0.7 + 0.45 = 2.5 m ahead of the hero at
  1.4-1.7 m height (attack_1) and ~2.3 m at 0.5-1.0 m (end of attack_2) - plus the weak point radius. Stand within
  ~1.2 m + radius of a low weak point (see `dummy_boss.gd`). Hydra: the first jaw opening still misses by 0-0.3 m from
  the bot's stand point (fight 92 s); hydra owner may move `stand` ~0.5 m closer.

## Open
- `reset_health()` (restart without rebuilding the scene) does not re-attach dropped props; every arena rebuilds today.
- strafe at the 2.5x cap is quick (0.33 s cycle); a longer-stride strafe clip from the art track would allow ~2.5 m/s.
- The hero's skirt/thigh patches noted by the anim fixer remain (art track).

## Fixer pass after the integration check (player_fix, 2026-11-22; owner away, decisions marked **Decision**)
Files: `player/player_camera.gd`, `visual/character_visual.gd`, `data/tuning.gd`, `test/harness.gd`. Scratch: `work/player_fix/`
(tools/top_probe.gd, tools/runfights.sh, logs/, shots_hydra/, sheet_hydra.jpg). No asset import, no class_name, no other module file.

| Finding | Status |
|---|---|
| major: hydra heads cut at the top of the lock frame (guard spot, inhale, centre bite) | fixed, see below |
| minor 1: Tuning CYCLOPS module keys | done: the 12 keys of cyclops.md request 1, same values as the module fallbacks (`_k()` now reads Tuning) |
| minor 2: Tuning MEDUSA rise_time / tail_sweep_radius | done: `rise_time` 1.2, `tail_sweep_radius` 9.3 (medusa.gd still merges AS_BUILT and sets tail_radius from TAIL_SWEEP_R: same numbers; its owner may now read the Tuning keys) |
| minor 3: public clip clock API | done: `CharacterVisual.seek(t, update)`, `clip_position()`, `play(clip, blend, speed, from_time)`. medusa.gd (`_anim.seek`, `_anim.current_animation_position`) and island_proxy.gd (`anim_player()`) are module files: request below |
| minor 4: boss clips on the frame clock | done: `use_physics_clock(on)`; cyclops, medusa, hydra and the dummy (`PHYSICS_CLOCK_IDS`) run their AnimationPlayer (and stand-in poses) on the physics clock. The hero and Pegasus stay on the frame clock |
| minor: hero ~34 % of the frame vs ~53 % in key_cyclops | not changed (**Decision**, lead to approve with the §4 camera decisions) |

**Hydra framing - cause and fix.** Two causes, not one: (1) the camera's "top of the boss" was the REST pose
(`frame_top_points`), and the centre neck rears ABOVE its rest top while it inhales (probe: 14.38 m rest -> 15.2 m at
clip 0.77 s) and swings toward the camera at the end of the centre bite (elevation 59 -> 64 deg from the guard spot), so a
longer arm alone would not have helped; (2) the arm could grow only 1.0 m. Fix:
- `CharacterVisual.live_top_points()` (world): the rest top-band vertices each ride the bone with the largest skin weight
  (rigid, from their rest offset; the 6x6 grid now keeps one point per cell AND bone), plus one point per bone box: the
  bone-space bounds of the vertices each bone mainly carries (weight >= 0.5, >= 12 vertices), whose live top is added.
  Hydra: 30 points + 75 boxes, measured once in 20 ms (first camera frame), then 0.015 ms per frame. At rest pose the
  points equal the old ones (max distance 0.000 m).
- `PlayerCamera._boss_tops()` uses it for real models (stand-ins keep `BossBase.frame_top_points()`).
- `PlayerCamera.max_extra_for(boss)`: the boss's own `cam_max_extra()` when it has one, else
  `Tuning.CAM_LOCK_MAX_EXTRA_BY_BOSS[boss_id]`, else `CAM_LOCK_MAX_EXTRA` 1.0. **Decision:** hydra 3.0 m (not 2.5): with
  2.5 the glowing head still touched the top edge at the close inhale (hero 5.6 m out, arm capped at 6.2 m). The hook
  lives in the camera + Tuning because boss_base.gd / hydra.gd are not my files; a module can still override it by
  defining `cam_max_extra()`.
- Windowed `--cam-debug` (seed 11, final 3.0): guard 6.6 m `lo 16.1 <= hi 16.3`, inhale `lo 15.7 <= hi 16.1`, centre bite
  `lo 13.2 <= hi 15.2` (whole beast in frame). The top is still cut, on purpose, only with the hero under the necks
  (flat distance < ~5.5 m: at the shoulder during the fire, at the jaw strike). Cyclops/medusa keep the 1.0 m.
- Shots (`work/player_fix/sheet_hydra.jpg`, 2.5 m pass): guard, inhale (rearing head + throat glow in frame), centre bite
  (glow on the biting head in frame), close inhale (head at the top edge -> the 3.0 m change). Devlog:
  `docs/devlog/media_inbox/player_fix/hydra_lock_live_top.jpg`.

**Harness:** `--shot-on=<event>@<delay>[:<count>],...` takes aimed shots N game seconds after harness events (e.g.
`--shot-every=0 --shot-on=fight_start@1.0,inhale@0.9:2,bite_start@0.45`); `--shot-every=0` turns the timed series off.

**Decision - hero size vs key_cyclops (minor 3).** Not changed. A 3.0 m lock arm would bring the hero to ~45 % of the frame
but push the 8 m cyclops' top out of frame at engage distance (the arm may only grow 1.0 m for him). The per-boss hook
now allows a per-boss distance too; if the lead wants the reference size, add a per-boss CAM_LOCK_DISTANCE next to
CAM_LOCK_MAX_EXTRA_BY_BOSS.

**Requests (not my files).**
1. medusa owner: replace `visual._anim.seek(...)` / `visual._anim.current_animation_position` with `visual.seek(t)` /
   `visual.clip_position()` (lines ~536, ~945-956); `_sync_clip` can stay as a guard but should now rarely fire (physics
   clock). Read `T["tail_sweep_radius"]` and drop AS_BUILT if you like (Tuning now has rise_time 1.2).
2. world owner: `IslandProxy.anim_player()` reads the private `_anim`; `visual.clip_position()` gives the same position.
3. boss_base owner (optional): `func cam_max_extra() -> float: return float(Tuning.CAM_LOCK_MAX_EXTRA_BY_BOSS.get(String(boss_id), Tuning.CAM_LOCK_MAX_EXTRA))`
   as a documented BossBase hook; the camera already calls it when present.
4. cyclops owner: the CYCLOPS constants in cyclops.gd are now duplicates of Tuning (Tuning wins); delete them when convenient.

**Proof (headless `--speed=3`, logs `work/player_fix/logs/`, summaries a_summary.txt / c_summary.txt):**
| Run | Result |
|---|---|
| test --bot=win seeds 11 / 4242 | victory 17.75 / 17.75 s, 4 strikes, 0 hits |
| cyclops --bot=win seeds 11 / 4242 | victory 36.82 / 32.97 s, 8 strikes, 0 hits |
| medusa --bot=win seeds 11 / 4242 | victory 27.52 / 26.60 s, 6 strikes, 0 hits (same as verify2 27.70 / 26.83) |
| hydra --bot=win seeds 11 / 4242 | victory 100.18 / 100.18 s, 8 strikes, 0 hits (= verify2); re-run with the final 3.0 m: 100.19 / 100.17 s, 8 strikes, 0 hits |
| cyclops / test / hydra --bot=lose | defeat (death at 20.0 / 26.0 / 27.9 s), arena rebuilt, fight_start again |
| home --bot=win | home -> sea -> cyclops, victory |
| windowed hydra --shots (5 images) + windowed --cam-debug on the final value | framing above |
No SCRIPT ERROR / Parse Error (one cyclops --bot=lose run started while harness.gd was half edited and failed to parse; re-run clean).

## Hero props from the chase camera (core_fix2, 2026-11-23; owner away, decisions marked **Decision**)
QA: from behind the shield read edge-on (a thin stick) and the sword hid behind the leg in idle/run. Changed only
`game/assets/characters/hercules/hercules_clips.json` `socket_offsets` (each entry now has a `note` with the old value).
**A manifest rebuild must keep these numbers**: `work/assemble_hercules/finalize_manifest.py` copies
`art_src/chars/hercules/rig.json` `socket_offsets` (the old values) over the manifest; re-apply the two entries below after
any rebuild (or put them into rig.json).

| socket | rig.json (old) | manifest now | what it is |
|---|---|---|---|
| forearm_l | loc (-0.0713, 0.151, 0.0074), rot_deg (5.81, 0, -90) | loc (-0.0499, 0.151, 0.0515), rot_deg (-34.19, 0.0, -90.0) | old offset turned **+40 deg about the forearm bone Y** (loc rotated with it, so the shield stays strapped on) |
| hand_r | loc (-0.0574, 0.1027, 0.0093), rot_deg (-1.33, -50.27, -83.11) | loc (-0.0086, 0.1173, 0.0093), rot_deg (-1.33, -50.27, -108.11) | old offset turned **-25 deg about the hand bone Z** (blade tip outward, away from the leg) |
Blender-space XYZ Euler as before (`offset_space` blender); new = R_bone(axis, angle) * old, checked to 1e-16.

Measured (probe `work/core_fix2/tools/socket_probe.gd`, hero-local, shield normal = its outer face; "cam" = facing toward
a chase camera behind him, |value| = how broad the disc reads; logs `work/core_fix2/logs/socket_probe1.log`, `socket_probe2.log`):
| pose | shield cam before -> after | shield fwd (block: must stay front) | sword tip x (right = negative) before -> after |
|---|---|---|---|
| idle | -0.05 -> -0.30 | - | -0.53 -> -0.81 (beside the hip, was in front of the hand) |
| run (2 phases) | -0.24 / -0.21 -> -0.71 / -0.67 | - | -0.28 / -0.47 -> -0.57 / -0.76 (was behind the body) |
| block_idle | - | normal (0.32,-0.16,0.94) -> (0.40,0.50,0.77): still faces forward, tilted ~30 deg up; centre unchanged (0.09,1.36,0.49) | - |
| attack_1 mid / attack_2 mid | - | - | tip (0.42,1.68,1.05) -> (0.30,1.94,0.95); (-0.03,1.17,1.38) -> (-0.32,1.11,1.36): still in front at the same reach |
| ride | -0.39 -> -0.41 | - | tip (-0.59,1.15,-1.11) -> (-0.29,1.13,-1.13) (blade along the flank, smaller) |
**Decision - +40 deg, and the camera sees the shield's back.** The brief suggested 50-70 deg so the shield FACE shows to a
camera behind him. Measured: turning the face toward the camera (negative angles) points it at the floor in the block
pose (-30 deg: block normal y -0.62; -60 deg: y -0.92, the face looks down), because the forearm pitches ~90 deg between
idle and block. Turning the other way the disc reads broad from behind (its painted back), and at +40 the block face
still points forward (0.77); +60 tilts it 50 deg up (fwd 0.54). So +40: broad disc in idle/run, block still covers him.
The sword's hit capsule follows the socket (SwordHitbox.follow), so the attack reach moves with the blade: all bot wins
below still land 8/8 (cyclops), 6/6 (medusa), 8/8 (hydra) strikes.
Shots: `work/core_fix2/sheet_free.jpg` (idle/run/ride, 4 variants), `sheet_lock.jpg` (block/attacks), `sheet_props.jpg`
(windowed cyclops fight); devlog `docs/devlog/media_inbox/core_fix2/hero_props_chase_before_after.jpg`.
