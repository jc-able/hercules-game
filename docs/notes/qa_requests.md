
## From the build fixer (2026-11-22) — for core (`work/core/gen_project.py` -> `game/project.godot`)
1. **ETC2/ASTC import (blocks the one-line template export).** Add `rendering/textures/vram_compression/import_etc2_astc=true`
   under `[rendering]` in gen_project.py, regenerate project.godot, then re-import with the lock
   (`until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; Godot --headless --path game --import; rmdir work/.import_lock`).
   Without it `Godot --headless --path game --export-release "macOS" ../builds/Hercules.app` stops with
   "Cannot export for universal or arm64 if ETC2 ASTC texture format is disabled". The preset in game/export_presets.cfg is
   ready for it; the build fixer will switch builds/make_app.sh to the one-line export when the setting lands.
2. **Own user folder for the game (optional, recommended).** Under `[application]`: `config/use_custom_user_dir=true` and
   `config/custom_user_dir_name="Hercules"`. Then the app (and editor runs) save to `~/Library/Application Support/Hercules/`
   instead of the shared `~/Library/Application Support/Godot/app_userdata/Hercules/`. Tell the build fixer (or note it in
   core_followup.md) so README's save path is updated.
   **Core fixer (2026-11-22): both done** in `work/core/gen_project.py` -> `game/project.godot` (`import_etc2_astc=true`,
   custom user dir "Hercules": saves now go to `~/Library/Application Support/Hercules/save.json`; README path to update).
   Re-import with the lock: see docs/notes/core_fix.md for whether it ran.

## From the core fixer (2026-11-22, play-test findings)
1. **medusa owner — weak point socket.** `neck_wp` (medusa.gd ~line 223) sits where the exposed-neck glow covered her face
   and eyes during the gaze. Move it to the SIDE of the neck below the jaw (e.g. local x +-0.45, y a little under the jaw)
   so the eyes stay readable. Core already made the glow a faint additive rim (alpha <= 0.35) and hides the lock diamond
   while the weak-point ring shows.
2. **medusa owner — tail ring.** The as-built tail hit radius is 9.3 m (SPEC said 7 m): locked on, backing off at 2.4 m/s
   cannot clear it in the 0.7 s coil, only a roll does. Either bring the hit radius back toward 7 m or keep 9.3 m; any
   player-facing hint must say "roll out" (SPEC §10.1 now says so).
3. **art / hercules manifest owner — shield and sword from behind.** In `game/assets/characters/hercules/hercules_clips.json`
   `socket_offsets.forearm_l.rot_deg` [5.81, 0, -90]: turn the shield ~50-70 deg about the forearm axis so its face turns
   back and outward in idle/run (from the chase camera it reads as a thin stick); `hand_r` angle the blade a little
   outward so it shows beside the leg. Core reads the offsets as they are; no code change needed.
4. **world owner — home sign / README.** If the controls sign or README gives a Medusa tail answer, use "roll out".

## From the hydra fixer (2026-11-22, play-test findings)
1. **core (player.gd) — public push-back.** hydra.gd's death now slides the hero back to 14.5 m from the centre so the
   collapsing beast lies in front of him (finding "death topples onto the hero"). It calls the private
   `Player._push_back(from, dist, secs)` through `call()` (guarded by `has_method`). Please expose it as a documented public
   `push_back(from: Vector3, dist: float, secs: float)` (no damage, collision kept); hydra.gd will then call that name.
2. **core (toon / outline shader) — near-camera fade for bosses.** The play-test asked hydra to "apply the near-camera fade
   from the cyclops finding". There is no such fade in core yet and the boss meshes use core's toon + outline shaders, so a
   module cannot add it. Suggested: a `near_fade` uniform pair (start 1.5 m, end 4 m) that dithers (`discard` on a 4x4
   Bayer threshold against the view depth) in toon.gdshader and outline.gdshader, enabled for real boss models only. The
   hydra side is covered without it (hero pushed out of the corpse + camera snapped behind him).

## From the cyclops fixer (2026-11-22, play-test findings)
1. **core (toon / outline shader) — near-camera fade, done module-side for now.** cyclops.gd `_near_fade_shader()` makes
   a copy of core's toon (both cull variants) and outline shaders at runtime with two uniforms `near_fade_hide` /
   `near_fade_full` and a 4x4 Bayer `discard` on `length(VERTEX)` at the top of `fragment()` (defaults 0/0 = off), and
   swaps the boss + club materials to it (same material objects, parameters copied, so flash/tint/petrify still work).
   Cyclops uses body 0.9-2.6 m, club 1.8-4.6 m. If core adds the same two uniforms (same names, same 0/0 = off default)
   to toon.gdshader and outline.gdshader, tell the cyclops owner: `_fade_material()` then only needs to set the two
   parameters (the shader copy can go). Hydra/medusa could call the same code until then (copy the three functions).
2. **core (optional) — release a GLB prop.** cyclops.gd lets go of its club at death with `Node.reparent(arena, true)` on
   the GLB's own `club` mesh (under a BoneAttachment3D). Works; a `CharacterVisual.detach_prop(node, parent)` helper would
   make it a documented API (drop_props() only handles attach_prop props).

## From the medusa fixer (2026-11-22, play-test findings; details in docs/notes/medusa.md "QA fixer pass")
1. **core camera (optional, for more tower) — per-boss base lock arm.** Medusa is now x1.5 (9.75 m) and gazes from ~7 m;
   her module also defines `cam_max_extra()` (2.0 m, already read by `PlayerCamera.max_extra_for`). The lock arm only grows
   when her top would not fit, so the boss/hero screen ratio is capped by the 3.7 m arm. If the lead wants more than the
   measured ratio, read an optional boss hint in `_lock_distance`: `if boss.has_method("lock_arm_extra"): d = max(d,
   Tuning.CAM_LOCK_DISTANCE + boss.lock_arm_extra())` (medusa.gd already has `lock_arm_extra()`), or add a per-boss
   `CAM_LOCK_DISTANCE_BY_BOSS` next to `CAM_LOCK_MAX_EXTRA_BY_BOSS`. A longer arm makes the hero smaller and her taller.
2. **core (player.gd, optional) — shield raise time.** medusa.gd now tracks when `Player.state` turns `&"block"` itself
   (timed-raise reflect, REFLECT_RAISE_WINDOW 0.6 s). A public `Player.block_since` (clock time the shield went up) would
   let other bosses use the same rule; medusa would then read it instead of its own tracker.
3. **art track — medusa albedo.** Some snake heads show muddy brown / yellow blotches in
   `game/assets/characters/medusa/medusa.glb`'s albedo (visible in the stunned close-up, work/qa_visual/sheets/07_med_zoom.jpg):
   paint them to the snake green. Module code cannot fix texture content.
4. **world owner / README / home sign.** Medusa answers to write: reflect = raise the shield JUST before her eyes fire (a
   shield held up long only blocks: no damage, no stun); tail = roll out (the sweep reaches ~14 m now).

## Status after the core fixer pass 2 (2026-11-23, details in docs/notes/core_fix.md "Core fixer pass 2")
- build fixer 1 + 2: settings were already in gen_project.py / project.godot; **the re-import has now run** under
  work/.import_lock, and the one-line `--export-release "macOS"` was checked to a scratch folder (exit 0, 231 MB, codesign
  valid, its binary wins `--start=test --bot=win`). make_app.sh takes route A by itself now. Saves:
  `~/Library/Application Support/Hercules/save.json`.
- core fixer 3 (hero props): done in hercules_clips.json socket_offsets, numbers in integrate_player.md (keep them on rebuilds).
- hydra fixer 1: `Player.push_back(from, dist, secs)` is public; hydra.gd now calls it (the `call("_push_back")` is gone).
- hydra fixer 2 / cyclops fixer 1: `near_fade_hide` / `near_fade_full` uniforms (0/0 = off) are in toon.gdshader and
  outline.gdshader; `CharacterVisual.set_near_fade(hide_m, full_m, under := null)` sets them for the whole character or
  only the meshes below `under`. cyclops.gd switched (its runtime shader copy is deleted; club dither checked on screen).
  Hydra / medusa can now call `visual.set_near_fade(0.9, 2.6)` if they want it.
- medusa fixer 2: `Player.block_since` (hero clock when the shield went up, -1 while lowered) + `Player.clock()`;
  medusa.gd's own tracker now reads it (one small edit, same REFLECT_RAISE_WINDOW rule; reflects still at 0.43 s).
- New for the cyclops owner (optional): the low marble curb at the rim fills the bottom ~20 % of the frame when the hero
  is knocked to the edge (camera outside the curb, e.g. `--bot=lose` deaths). Its toon material can take the new near fade
  (`m.set_shader_parameter("near_fade_hide", 0.6)` / `near_fade_full` 2.0) or the curb could get a collider in layer 1
  so the spring arm stops in front of it.

## From the medusa fixer 3 (2026-11-23; details in docs/notes/medusa.md "QA fixer 3")
1. **core camera (player_camera.gd) — must-fit points hook (needed for "eyes in frame during the gaze").** There is no
   must-fit hook yet (only `cam_max_extra()`). medusa.gd now defines `cam_fit_points() -> PackedVector3Array` (world
   points to keep in frame on top of the live tops: during the gaze her eyes + where they land after the fire snap).
   Please append them in `_boss_tops`:
   ```gdscript
   func _boss_tops(boss: BossBase) -> PackedVector3Array:
   	var out := PackedVector3Array()
   	var v = boss.get("visual")
   	if v != null and is_instance_valid(v) and v.has_method("live_top_points") and not v.is_standin:
   		out = v.live_top_points()
   	if out.is_empty():
   		out = boss.frame_top_points()
   	if boss.has_method("cam_fit_points"):
   		out.append_array(boss.call("cam_fit_points"))
   	return out
   ```
   Proven with exactly this patch swapped in at runtime (work/medusa_fix3/player_camera_patched.gd, probe
   `cam_probe.gd --probe-hold=7 --probe-patch-cam`): hero held in the beam at 7 m, her eyes stay >= 10 % below the top
   edge through windup, beam and lunge (unpatched: up to 5 % ABOVE the top edge for ~0.25 s at the fire, because the
   gaze clip throws her eyes 3.8 m toward the camera in two frames and the arm lerp (3.5/s) catches up too late).
   Other bosses are unaffected (no method = no points).
2. **core Tuning.MEDUSA (optional, module overrides today):** `"tail_coil": 1.5`, `"tail_sweep_radius": 9.0` (hit/ring),
   `"tail_trigger_dist": 6.0`.
3. **README owner (line 73) / world owner (home sign):** the tail answer is now "**roll out of the ring before it fills**"
   (the ring is the hit zone, 9 m; it fills in 1.5 s). README's "watch the tail come round and roll as it reaches you"
   is no longer the rule. Suggested line: "When her tail coils, a red ring lights up around her: roll out of it before it
   fills (twice if you were right beside her)."

## Status after the final check (2026-11-23 00:45, details in docs/notes/final_check.md)
- medusa fixer 3 request 1 (must-fit hook): **applied by the final check** in `game/scripts/player/player_camera.gd`
  `_boss_tops()` (the proposed code, plus a 2-line comment). Probe `cam_probe.gd --probe-hold=7` on the real camera: her
  eyes stay 10.4-11.5 % below the top edge through windup, beam and after (same as the fixer's patched run). Medusa win
  seeds 11 / 4242 = 26.20 / 25.32 s, campaign `--keys` seed 4242 won, app rebuilt.
- medusa fixer 3 request 3 (README line 73): done ("roll out of the ring before it fills").
- medusa fixer 3 request 2 (Tuning.MEDUSA tail keys) and core fixer 2's cyclops curb note: still open (not applied).
