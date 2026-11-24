# feedback 2: strike effects, visible damage, clipping (vfx fixer, 2026-11-23 ~13:20-14:10)

Owner items 5 (more visual effects when a strike cuts a creature, visible damage) and part of 6 (clipping) from
`docs/notes/owner_feedback_2.md`. Scratch: `work/vfx2/` (movies, sheets, logs, probes/leg_gap.gd, run_cold.sh).

## What changed (files)
- `game/scripts/combat/fx.gd` (+ functions only, nothing old changed): `slash()` (streak along the blade's recent path),
  `impact()` (flat 8-ray star + growing ring facing the camera), `ichor()` (heavier droplets in the creature's colour),
  `cut()` (all of these + the old gold sparks, bigger), `glance_streak()` (faint white streak), `wound()` (Decal on the
  weak point's socket = follows the bone), `drip()` (3 slow drops from every 2nd wound), `warm_strike()` (warm-up).
- `game/scripts/combat/sword_hitbox.gd`: records the real blade (grip, tip) every physics frame (9 samples, ~0.15 s);
  before `wp.strike()` it writes `last_hit_pos` (blade point nearest the sphere, inside it), `last_from`, `last_trail`
  on the weak point. The gold spark on a counted hit moved to BossBase (so a Hydra wrong-side jaw strike, which the
  Hydra turns into a glance, shows no cut). Glance: same spark + clang + shake as before, plus a faint white streak.
  Hit pause (0.06 s), shake 0.35 and rumble unchanged.
- `game/scripts/combat/weak_point.gd`: 3 vars (`last_hit_pos`, `last_from`, `last_trail`).
- `game/scripts/bosses/boss_base.gd`: `take_weak_hit` flash 0.2 s -> 0.08 s (colour unchanged warm white; a cyan-tinted
  flash on the Hydra was tried and looked wrong), then `_cut_fx(point)`: `Fx.cut` + a wound decal + drip. `ICHOR` per boss
  (contrasts with the body): Cyclops gold `(1, .62, .12)`, Medusa lime-yellow `(.9, 1, .22)`, Hydra cyan `(.25, .92, 1)`
  (also reads inside the orange fire). `wounds` (max 12, oldest freed). At the first wound the boss's meshes (not the
  weak-point glow) get visual layer 12 (`Fx.WOUND_LAYER`) and the decals see only that layer, so a wound never lands on
  the hero standing next to it. A fight restart reloads the scene: marks are gone.
  New: limb blockers (`add_limb_blocker(bone_a, bone_b, r)`, `_update_limbs()` after `move_and_slide`): a StaticBody3D
  capsule on the boss layer (3) following two skeleton bones. Not a shape of the boss body (its floor/wall movement,
  mask 1, never sees it), not seen by the chase camera (mask 1), not in group "boss" (no glance, no lock-on).
  Harness A/B switch `-- --no-limb-blockers`.
- `game/scripts/bosses/cyclops.gd`: 4 leg blockers (thigh->shin r 0.55, shin->foot r 0.42; consts LEG_R_THIGH/SHIN).
- `game/scripts/bosses/hydra.gd`: resting-head collider radius 0.7 -> `HEAD_COL_R` 0.85, centre moved back 0.15 m so
  its front end (jaw side) is where it was.
- `game/scripts/world/arena_base.gd`: one line, `Fx.warm_strike(holder, WARM_SIZE)` in `prewarm_in`.
- No contract changed: no clip, event, socket or length; no new event.

## Proof
- Bots headless `--bot=win --speed=3 --seed=11` (after the last code change): cyclops victory 36.79 (was 37.60; the hero is
  now pushed out of the legs), medusa 26.20 (26.21), hydra 99.38 (99.44). No SCRIPT ERROR / Parse Error.
- Hit times in the rendered runs unchanged (cyclops 10.86 / 11.19 / 18.80 / 19.13; medusa 8.42 / 8.79; hydra 8.42 / 20.16).
- Looked at (gdwin 1280x720, 30 fps movies, contact sheets every 1/15 s around each hit): cyclops, medusa, hydra. Each hit
  shows the star + ring + sparks + coloured ichor in the first frame after the hit; the streak is a gold-white band along
  the overhead swing; after 4 Cyclops hits 4 glowing gold cuts sit on the right forearm and move with it.
  Devlog: `docs/devlog/media_inbox/feedback2_vfx/strike_fx_before_after.jpg` (owner 5:50.4 vs after).
- Warm-up: `fx_capture.gd` on the 3 fights (win) gives exactly the same 8 material signatures as `work/freeze_fix/capall`
  (all new effects reuse the spark "dot" material kind and the sweep "ribbon" kind; decals have no spatial shader).
  So `warm_fx.tscn` was NOT rebuilt; `Fx.warm_strike` runs the real code once (and shows one decal for the atlas).
- Fully cold run (new HOME + new bundle id on my own clone `work/vfx2/bin/G.app`, freeze_probe, 1920x1080, cyclops bot
  win to t=21): 0 frames over 50 ms after fight start; the frames of the hits were 3.1 and 2.9 ms.
- Leg clipping probe `work/vfx2/probes/leg_gap.gd --push` (hero put 0.1 m into a shin every 1.5 s, measured after 12
  physics frames): with blockers worst 0.05 m inside (26 pushes), without (`--no-limb-blockers`) up to 0.47 m.

## Decisions (owner will not answer)
- Glancing hits: the intake said "keep today's spark and clang"; the brief asked for a weaker version. Kept both: spark,
  clang, shake unchanged + a faint short white streak.
- "Looks more hurt as health falls": the wounds add up (one per hit) and every 2nd one drips; no posture/limp change
  (would touch the boss clips the owner praised).
- Ichor colours chosen for contrast, not the body colour (green on green Medusa and violet on the violet Hydra did not read).

## Still open (for the reviewer / lead)
- Cyclops club (5:00, the hero standing inside the stuck club): NOT changed. The hand holds the club next to the forearm
  weak point, so a club blocker would stand between the hero and the weak point and could stop the bot; the stuck club
  already fades its near half. Needs a look by whoever owns the club timing.
- Hydra head: radius change verified only by the bot win; no dedicated push probe like the legs.
- Mounting / wing / home props / flight camera clipping belong to other fixers.

## Re-fix after the review (vfx re-fixer, 2026-11-23 13:47-14:25; scratch `work/vfx3/`)
All four findings checked and fixed; none was wrong.
1. **Club clipping (major), `cyclops.gd`**: two StaticBody3D capsules on layer 3 (mask 0, top_level, not in group "boss",
   same recipe as `add_limb_blocker`), `CLUB_BLOCKS = [[2.0, 3.0, 0.55], [3.0, 4.6, 0.8]]` m along the club axis from the
   grip. The reviewer's r 0.35/0.45 is thinner than the real club: the GLB `club` node measures p80 radius 0.48-0.62 m at
   1.5-2.5 m and 0.71-0.88 m at 3-5 m (trimesh on cyclops.glb), and with r 0.72 a 0.1 m push at 3.5 m was not undone.
   The near surface stops `CLUB_BLOCK_FREE` = 1.5 m from the grip (forearm weak point untouched). Moved every physics
   frame from `_club.global_transform` (`_physics_process` override calls `super`); collision layer on only in `stuck`,
   `pull_free` < 0.4 s and, after death, once the dropped club lies (drop time + 0.05 s); off in sweep/slam (no damage
   change). `--no-limb-blockers` also switches them off.
   Probe `work/vfx3/probes/club_gap.gd` (hero put 0.1 m into the shaft at 1.5/2.5/3.5 m from the grip, camera side,
   measured after 12 physics frames, both stuck phases): with blockers 0.02 / -0.06 / 0.02 m; without 0.16 / 0.10 / 0.09.
   Bot: forearm hits 10.85 / 11.19 / 18.82 / 19.13, victory 37.61.
2. **Hydra snout (minor), `hydra.gd`**: measured, not guessed. `work/vfx3/probes/hydra_snout.gd` CPU-skins the head_down
   mesh: the snout reaches **1.36 m** past head_c (half-width 0.50 m at 0.8-1.0, 0.31 at 1.0-1.2, 0.23 at 1.2-1.36), the
   capsule ended at 0.91 m. Instead of stretching the r 0.85 capsule (it would also widen the sides beside the jaw) a
   thin upright capsule `RestingSnout` (r 0.42, 1.5 m tall, centre 0.95 m past head_c, front 1.37 m) is enabled and
   disabled with `_head_col` and placed in `_place_head_col`. Push test (0.1 m into the mesh, 12 frames): front 0.10 ->
   -0.01 m (was 0.10, not pushed), sides at head_c -0.10, at the jaw -0.05 / -0.07. Jaw weak point unchanged; the bot
   still lands every jaw strike (8.43 / 20.15 / 31.90 / 43.64), victory 99.09 (was 99.38). gdwin push movie
   `work/vfx3/mov/snout.avi` (head at the hero's side like the owner's 15:00): he stands beside the head, not in it.
   Note: the sword arm and blade still enter the head when he strikes; the jaw sphere centre (jaw_c, 0.29 m past head_c,
   0.5 m high) is inside the mesh, so a hit must reach into it. Only the body is kept out.
3. **Slash streak (minor), `fx.gd`**: `Fx.slash` rebuilt: one blade point per sample (Fx.cut passes the cut's own place
   on the blade + 12 % toward the tip, >= 35 %; the glance uses the tip), samples < 3 cm apart dropped, a jump > 1.2 m
   drops the stale samples before it, only the samples since the blade last turned back (> 90 deg) kept, Catmull-Rom
   4 steps, camera-facing ribbon 0.22 m wide (glance 0.14 m) tapering to 0 at the old end, side vector kept continuous
   (no twist), core alpha 0.9 white with 25 % of the ichor colour, edges in the ichor colour. Why the tip alone was not
   enough: on Medusa the tip passes ~1 m above her neck and the swing turns back, which drew a folded pale shard at the
   upper right (seen in my own first re-fix movie `work/vfx3/mov/med2.avi` at 8.82). Movies after: Medusa 8.42/8.79,
   Hydra 8.42/20.16, Cyclops 10.86 show a thin tapered arc at the cut, nothing floating away from it.
4. **Impact over the hero (minor), `fx.gd` + `boss_base.gd`**: the star/ring sits `IMPACT_TO_CAM` 0.1 m toward the camera
   (was 0.35 x size, up to 0.53 m), and when the hero (BossBase passes `player.global_position` through `Fx.cut` ->
   `Fx.impact(..., avoid)`) is within `IMPACT_CLEAR` 1.5 m of the camera -> cut line, between them, both are drawn at
   0.6x. Hydra 8.47: the ring (~0.85 m) sits at his shield side, his torso and head clear.
- Warm-up: `fx_capture.gd` on the three fights (win) -> the same 8 signatures as `work/freeze_fix/capall` (no new material
  kind), `warm_fx.tscn` not rebuilt. Fully cold run (own clone `work/vfx3/bin/G.app`, new HOME + bundle id, hydra bot to
  t=22, 1920x1080): 0 frames over 50 ms after fight start; the hit frames 3.0 ms and 9.1 ms.
- Final headless `--bot=win --speed=3 --seed=11`: cyclops 37.61, medusa 26.22, hydra 99.09, 0 SCRIPT ERROR / Parse Error.
- Devlog: `docs/devlog/media_inbox/feedback2_vfx3/clipping_and_slash_before_after.jpg` (+ captions.txt).
- Contracts: no clip, event, socket or length changed. New signature params are optional (`Fx.slash(..., frac)`,
  `Fx.impact(..., avoid)`, `Fx.cut(..., avoid)`); `Fx.slash`'s `width` now means metres (only fx.gd calls it).
