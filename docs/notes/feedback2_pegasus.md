# Feedback 2: Pegasus flying animations (pegasus fixer, 2026-11-23)

The owner said "for the horse, obviously we need to fix the flying animations" (16:46). He will not answer
questions, so every decision is mine and is written here. Blender ran headless only, and Godot rendering went only
through `tools/godot_bg/gdwin` with a throwaway HOME. builds/Hercules.app was not touched. Scratch:
`work/feedback2_pegasus/`.

## What read wrong (recording frames 08, 09, 10 of owner_feedback_2 + v3 measured)
I measured the wing tip elevation (wing_01 head -> wing_03 tip, front plane) on the 25 frames of fly v3:
- The wings stayed at about +41 deg for frames 0-7 (0.3 s, "wings held in a V, barely move"), then dropped 100 deg
  in 4 frames. They held at -62 deg for frames 11-18 (0.33 s, hanging straight down "like a second pair of legs"),
  then snapped back up.
- All four legs hung under the body like a standing horse ("a horse standing on air").
- The tail hung down from the rump, so from the chase camera it looked like a column.
- The neck was upright.
- glide held the wings in a V (L +33..+39 deg, R +22..+28: lopsided).
- fly is the clip used for take-off, climb, boost and 2 beats per cruise cycle. glide is used for 3 s per cruise
  cycle and for descent and landing (pegasus_flight.gd `_play_anim`).

## Decisions
- One tool: `work/feedback2_pegasus/gen4.py` (pure numpy, with `pk.py` for pose maths R = Rz Ry Rx in world view
  axes, the same as ak_blender.rot_xyz). It reads the v3 absolute pose files (`fx_k*.json`) and writes
  `poses_<clip>/f4_k*.json` and `keys_<clip>.v4.json`. Those are copied to `keys_<clip>.json` and baked with
  `tools/ak bake --loop --fps 24`.
- **Wings: fly.**
  - New elevation curve: +50 deg at the top (t 0, the same phase as v3), eased down to -30 deg at t 0.583. That is a
    strong 14-frame downstroke. Then a quicker 11-frame upstroke back to the top. No holds.
  - The wing SHAPE for each output frame is slerped from the v3 frame that is at the same progress in the same stroke
    direction, so the downstroke keeps the spread shape and the upstroke keeps the folded shape. The whole chain
    (01/02/03 + 3 feather groups) is then turned rigidly about the body's long axis to reach the target.
  - The 25 deg forward sweep (rider safety) is kept. The right wing stays 1 frame late at 0.97 amplitude, as in v3.
  - Measured on the files: L +50 / +10 / -30 / +4 at frames 0 / 7 / 14 / 19.
- **Wings: glide.** Spread near level: +10 deg with a slow 3 deg breath (2 per 3 s loop). The right wing is 0.125 s
  late (v3 lag kept). Measured: L 10.0 / R 8.5-11.5.
- **Legs.** Aim form, side panel, absolute.
  - Forelegs tucked: upper arm +8, forearm -72 (forward), cannon +42 (folded back), hoof +88.
  - Hind legs trailing: thigh +14, gaskin +68, cannon +46 (the hock bends the right way), hoof +74.
  - Paddle on the beat: 6-12 deg in fly; 0.7 of that, 2 cycles per 3 s, in glide. The v3 de-phase is kept (fr 0.0625,
    bl 0.042, br 0.1 s).
- **Tail.** Streams back: aim 122/110/100/94/91 deg, so the base arches up and the tip is level. A wave lags down the
  chain (2-10 deg in fly, 3-9 deg in glide).
- **Neck.** Stretched forward: neck_01/02/03 lean +10/+8/+6 deg. The head keeps its v3 angle and looks ahead.
- **Body.** The fly root bob is x1.5: 0.12 m at t 0.625, the end of the downstroke (same phase). The body rises with
  the stroke. There is still no body pitch (contract: no rock in the fly<->glide crossfade). glide root unchanged.
- Not changed: clip names (fly, glide, idle), lengths (1.0417 / 3.0 / 8.0), loop, events (none), sockets, the rider
  block offsets/speeds/phase, and idle.

## Checks
- Rider pair check (`art_src/chars/pegasus/ridden/pair_check.py` on a scratch copy of ride.blend in
  `work/feedback2_pegasus/rc/`): fly@beat 0 hits / 25 frames; glide@0.4 0 hits / 36 frames (both glide versions).
- Merge with the exact clip_sources paths (idle_n/action_idle.json, glide/action_glide.json, fly/action_fly.json):
  ok, rig_hash 02e3e4139ce9. Export: 3 clips at 24 fps, GLB lengths fly 1.0417 / glide 3.0 / idle 8.0, 7.23 MB.
  Manifest by `art_src/chars/pegasus/ridden/finish_manifest4.py`, which is finish_manifest3 with the clearance and
  fly_bob texts for v4.
- Import under work/.import_lock: OK. The loader probe (`work/assemble_pegasus/probe.gd` via gdwin) printed
  `PROBE ok=true` twice.
- `tools/clip_motion.py pegasus`, moving joints:
  - fly 38/43; still: hips, root, saddle, spine_01/02 (on purpose: saddle and wing roots)
  - glide 37/43 (was 38; hoof_bl is just under 3 deg)
  - idle 39/43
- Bots headless `--bot=win --speed=3`: cyclops, medusa and hydra all `result=victory`, 0 SCRIPT ERROR.
- Recorded flight: gdwin `--start=sea --harness --bot=win --seed=11 --shots` every 0.25 s for 16 s
  (`work/feedback2_pegasus/shots_sea/`, sheet `sea_after_sheet.jpg`). Seen from the chase camera:
  - The tail no longer hangs as a column. It streams toward the camera as a short blue blob under the rider.
  - The wing strokes are visible (V, level, below the line), and the glide is spread level.
  - The camera itself is the flight agent's.
  - This run used the first glide v4 (paddle 0.35). The final glide only paddles the legs more.

## Notes for other agents
- **Flight (pegasus_flight.gd / home_base.gd):**
  - In the air the hooves now hang 0.29-0.65 m (fly) or 0.31-0.42 m (glide) above the Pegasus origin. Before, they
    hung 0-0.15 m.
  - If the landing touches the ground in glide, Pegasus may look about 0.3 m above the grass until the idle crossfade
    drops the legs. Lower the landing height by about 0.3 m, or start idle slightly before touch-down. But keep the
    idle_clearance rule: never idle with the rider seated.
  - The fly bob is now 0.12 m (was 0.08). The code adds no bob (`visual.position.y = 0`), so nothing to change.
  - No clip was requested (no docs/notes/feedback2_flight.md existed when I finished). A "standing, wings raised" mount
    clip can be made from idle k00 + the fly top wing chain if the flight agent wants one.
- **Sword agent:** the ride clip and the hercules files were not touched. The pair check uses the current ride action.

## Files
- art_src/chars/pegasus/clips/fly/
  - `keys_fly.json` (= keys_fly.v4.json)
  - `action_fly.json` (v4)
  - `poses_fly/f4_k*.json`
  - v3 kept as `keys_fly.v3.json` and `action_fly.v3.json`. Never merge them.
- art_src/chars/pegasus/clips/glide/: the same layout (`f4_k*.json`, v3 kept as `*.v3.json`).
- art_src/chars/pegasus/clip_sources.json: why-texts updated, same paths.
- art_src/chars/pegasus/ridden/finish_manifest4.py; art_src/chars/pegasus/pegasus.blend (merged).
- Backup of the game files before this pass: `art_src/chars/pegasus/backup_20261123_fb2/`. Backup of the blend:
  `work/feedback2_pegasus/pegasus_before_fb2.blend.bak`.
- game/assets/characters/pegasus/pegasus.glb + pegasus_clips.json (+ import files).
- Devlog: `docs/devlog/media_inbox/feedback2_pegasus/`
  - fly_before_after.jpg
  - sea_flight_after_sheet.jpg
  - captions.txt

## Re-fix (Pegasus RE-FIXER, 2026-11-23 13:38-13:59) — fly v5, glide v5, new wings_up
Six reviewer findings, each checked first. All six were right. Every decision below is mine (the owner does not
answer questions). Scratch: `work/feedback2_pegasus/r2/`.

### Generator now in the repo (finding 6)
- `art_src/chars/pegasus/scripts/`:
  - `gen5.py`: makes v5 from the v3 pose files of BOTH clips.
  - `pk.py`: reads `rig_info.json` next to it, a copy of work/feedback2_pegasus/info.json.
  - `gen4.py`: the v4 tool, copied for history.
  - `gen_wings_up.py`.
- Usage: `python3 art_src/chars/pegasus/scripts/gen5.py fly|glide --write`. This writes `poses_<clip>/f5_k*.json` and
  `keys_<clip>.v5.json`. Copy that to `keys_<clip>.json`, then run
  `tools/ak bake art_src/chars/pegasus/pegasus.blend --clip <c> --keys .../keys_<c>.json --loop --fps 24 --out-action .../action_<c>.json`.
- clip_sources.json and the keys files point at the repo path.
- v4 is kept as `keys_<c>.v4.json` / `action_<c>.v4.json` / `poses_<c>/f4_k*.json`. Never merge it.

### What changed and why (per finding)
1. **Hind legs (major), confirmed.**
   - I first stretched them back along the body line (thigh 30, gaskin 84, cannon 74, hoof 92). The hooves then sat
     at belly height, but from the chase camera the legs come TOWARD the camera, so they still projected as two long
     white columns down to the bottom of the frame (work/feedback2_pegasus/r2/z34.jpg).
   - Final: the legs point back and slightly UP, in line with the camera's view (body frame thigh 38, gaskin 96,
     cannon 90, hoof 102, +-4..6 deg paddle). Physically the hooves are now above the belly line.
   - From the chase camera the hooves sit just under the rump. The leg mass under the body is shorter than the
     rider's torso (z34b.jpg: shot 34 v4 vs v5; shot 40).
   - Forelegs are tucked like a jumping horse: 20 / -88 / 62 / 88. The hoof lags the cannon, so the fetlock flexes.
2. **Upstroke fold (major), confirmed.** v4 had no fold.
   - The hand (wing_02, wing_03) is swept back 55 deg and bent down 15 deg about the elbow (the wing_02 head).
   - Feather groups follow the back sweep by 0.45 (feather_01) / 0.75 (feather_02) / 1.0 (feather_03), plus an 8 deg
     trail scaled the same way.
   - Fold weight: starts at upstroke u 0.1, full from u 0.4 to 0.7, open again by u 0.85 (the last 2 frames before
     the top).
   - Two failed tries, recorded:
     - The fold with all feathers following fully swung the inner secondaries INWARD into the rider: pair_check 3/25
       frames, 706 tri pairs, thighs/skirt.
     - With feather_01 not following at all, the mesh sheared: black slivers at the folded wing (zoom_fold2.jpg).
       The 0.45/0.75 split fixed both.
   - Measured span, back view, same hand-tip height:
     - Model: up vs down 22 % / 28 % / 31 % narrower (tip z 2.26 / 2.49 / 2.67 m).
     - Render (sc_back_b, whole silhouette incl. the body): about 19 % narrower.
     - The early upstroke (tip below the rider's thighs) is only 1-13 % narrower, because a fold there hits the rider.
3. **Glide curtain (major), confirmed.**
   - The glide wing chain now comes from the fly v3 DOWNSTROKE shape at progress 0.6 (the flat level wing), not from
     v3 glide.
   - Kept: +10 deg, 3 deg breath (2 per loop), right wing 0.125 s late.
   - Added: primaries roll +-3 deg alternately (3 per loop) and a 2 deg tip flex.
   - Lowest feather tip 1.66-1.76 m, i.e. 0.2 m under the shoulder. In v4 the feathers reached the belly.
   - Back view: a thin horizontal wing (back_cmp.jpg). The in-game landing glide is spread flat (landing_b.jpg).
4. **Neck (minor), confirmed.**
   - Absolute rx targets: neck 21 / 19 / 17, head -28, the same in fly and glide. Half of the v3 life is kept.
   - Glide also gets a slow 2-3.5 deg reach, because the v3 glide neck barely moved.
   - The muzzle is about 20 deg below level.
   - The body has a constant **9 deg nose-down pitch** as `root.rot [9,0,0]` in BOTH clips. It turns about the hips.
     Because it is a constant, the fly<->glide crossfade does not rock.
   - The rider rides the saddle socket and leans with the body (seat offset unchanged; pair check 0).
   - Only the root bone's track carries the pitch, so the wing-only WingOverlay is not affected.
5. **Stroke dwell (minor), confirmed.**
   - Downstroke 0.625 s (15 frames). Upstroke 0.417 s (10 frames).
   - Each half is 50 % sine ease + 50 % power curve. The wing reaches the bottom at about 90 deg/s and leaves at
     about 110 deg/s.
   - Within 8 deg of the bottom: 3 frames (0.1 s; v4 0.26 s). The top dwell is about 0.17 s (kept).
   - The bob peak is still at t 0.625, now exactly the end of the downstroke.
6. **Generator in work/ (minor), confirmed.** Moved, see above.

### New clip `wings_up` (flight agent's request in feedback2_flight.md)
- 2.0 s loop:
  - idle k00 stance
  - wings = fly v5 top, raised 15 deg more
  - 4 deg breath
- **Decision: swept FORWARD 20 deg, not back.** Swept back 45 deg as asked, the wings cut the seated rider on 24/24
  frames (2606 tri pairs, `r2/pair_wu_back45.json`): the wing roots sit in front of the saddle, so a swept-back wing
  passes through his torso. Forward 20 / raise 15: 0/24.
- Not checked from the mount camera: the showcase seats no rider.
- **Flight agent:** to use it, change the `"fly"` lookup in home_base `_make_wing_overlay` to `"wings_up"` (with
  `hold_top` its t 0 is a good hold). I did not touch home_base.gd.

### Notes for the flight agent (pegasus_flight.gd / home_base.gd, not my files)
- Seated on the ground during the mount, fly now also pitches the body 9 deg nose-down and stretches the hind legs
  back. The lift follows right after.
- On landing, the fly/glide -> idle crossfade (0.7 s) levels the body.
- If either reads badly, play idle a little longer before the lift.

### Checks (final files)
- pair_check (copy of ride.blend in work/feedback2_pegasus/rc), all 0 hits:
  - fly@beat: 0/25 frames
  - glide@0.4: 0/36
  - wings_up@1.0: 0/24
- Merge with the exact clip_sources paths (idle_n, glide, fly, wings_up): ok, rig_hash 02e3e4139ce9.
- Export: fly 1.0417 / glide 3.0 / idle 8.0 / wings_up 2.0 s, 7.26 MB. Clip names, lengths, loops and events are
  unchanged for the 3 old clips. Sockets unchanged.
- Manifest: `art_src/chars/pegasus/ridden/finish_manifest5.py` (finish_manifest4 + v5 clearance/fly_bob texts:
  pitch).
- Import under work/.import_lock: 0 errors.
- Loader probe (gdwin): `PROBE ok=true`. All 4 clips pass has/length/loop.
- clip_motion moving joints:
  - fly 37/43
  - glide 36/43 (v4 37; frozen only the hips/spine/root/saddle and the wing_02 elbows)
  - idle 39/43
  - wings_up 12/43 (wings only, by design)
- Bots headless `--bot=win --speed=3 --seed=11`: cyclops, medusa and hydra all victory, 0 SCRIPT ERROR.
- Recorded flights (gdwin, throwaway HOME), 0 SCRIPT ERROR each:
  - `--start=home --bot=win --seed=11`, shots every 0.25 s: `r2/flight_close_b.jpg`, `r2/landing_b.jpg`
  - `--start=sea --bot=win`: `r2/shots_sea`, `r2/shots_sea_final`
- Devlog: `docs/devlog/media_inbox/feedback2_pegasus/refix_before_after.jpg`, `sea_flight_v5_sheet.jpg`
  (captions.txt).
- Backups:
  - `work/feedback2_pegasus/r2/pegasus_before_v5.blend.bak`
  - `r2/pegasus_v4.glb.bak`
  - `r2/pegasus_clips_v4.json.bak`
