# Hydra module notes (hydra boss builder 2026-11-22; review fixes by the hydra fixer the same day)

Files: `game/scripts/bosses/hydra.gd` (extends BossBase, loaded by path, no class_name),
`game/scripts/world/hydra_arena.gd` (extends ArenaBase, scene id `hydra`). Scratch: `work/hydra/` (fixer logs: `work/hydra/fix/`).

## Play-test fixes (hydra fixer 2, 2026-11-22) — win over everything below where they differ
Scratch/logs: `work/hydra_fix2/` (`probe_death.gd`, `logs/`, `shots*/`, `sheet1.jpg`, `zoom2.jpg`). Owner away: decisions inline.
| finding | fix |
|---|---|
| major: pink bite warning (column + sphere) | circle crimson (0.92, 0.18, 0.08), lock (1.0, 0.55, 0.15); the 3.2 m pillar is now a 0.3 m ember rim on the circle's edge; the biting head's glow is a soft ember billboard (2.2 m quad, scale 0.7-1.25) + ember light. No pink left in the module |
| major: colours off the sheet | the albedo has dark purple (hue 260-320, 63%) and raspberry (320-360, 37%) texels; one multiply tint cannot fix both (tried (0.44, 0.36, 0.74): legs violet, belly pink). **Decision:** the hydra's materials get a copy of core's toon shader with `hydra_recolour()` injected before the tint line (by redness: purple x (0.66, 1, 1.18) -> violet, raspberry x (0.86, 0.78, 0.38) -> crimson); core's file is untouched and re-read (anchor `c.rgb *= tint.rgb;`, warning + tint-only fallback if it changes). MODEL_TINT now (0.78, 0.72, 0.84). Violet rim (0.70, 0.55, 1.0, strength 0.30) on the boss materials, a boss-only violet DirectionalLight (render layer 11 = cull mask, energy 0.35). Arena sun whiter: (1.0, 0.89, 0.80) x1.0 (was (1.0, 0.78, 0.6) x1.05) |
| major: death covers the hero / camera | probe: the `death` clip collapses IN PLACE from head_down (no side topple: centroid x stays 0, necks splay to x +-6 m, heads up to z 7.7 m) around a hero striking from ~7.1-7.6 m. At death the hero slides back to 14.5 m from the centre in 1.1 s (core's knockback slide `_push_back`, collision kept, no damage) and the camera snaps behind him (`death_clear` event). Near-camera fade: none exists in core yet -> request in qa_requests.md |
| minor: inhale cone = flat orange paint | Telegraph fill alpha x0.38 (max fill 0.23; 0.33 still read as paint once glow/tonemap brighten it) + module overlay `INHALE_SHADER` (additive pulsing edge, sparse diagonal hatch sliding outward, grows with the inhale). Basalt and cracks show through; the boss bar separates from it |
| minor: arena lacks drama | rim: cliff_rock/boulder stacks replaced by jagged hexagonal basalt column clusters (one flat-shaded mesh per cluster, ink outline, a lava light at each foot); horizon: big column clusters (h 22-48 m) instead of the giant rounded blocks; floor cracks domain-warped (wandering, forking, broken into runs) + thin twigs + a soft emissive halo; molten lava inlets at the shelf edge (radius +0.25..+1.5, outside the walkable boundary) |
| minor (bot only): enraged bite too short to roll after the lock | bite windup floored at 0.75 s (enraged was 0.64): lock leaves 0.48 s (was 0.41), enough for a 0.35 s reaction + the 0.08 s roll i-frame start |
| minor: head_down head not solid, jaw hittable through it | `RestingHead` capsule (r 0.7, 2 m, on the boss body) laid along the head from 1.7 m behind head_c to 0.1 m ahead, enabled only in head_down (real model). Jaw strikes from behind the head glance (`take_weak_hit` override: spark + `glance`, weak point re-opened, `jaw_glance` event) when dot(hero - jaw, head dir) <= -0.45 (**Decision:** the finding's -0.3 glanced a hero standing right beside the jaw, 110 deg round). Probe `--hydra-probe=head_through`: the hero walking through the head slides along its side (x 1.07 = 0.7 + hero radius) |
| minor: head_down smoke in front of the camera | lifetime 2.2 -> 1.4 s, 20 particles, pixel distance fade 2.5-6.5 m from the camera, and at head_down end the emitter stops and the rest fades out in 0.5 s, then hides |

Proof (final code, `work/hydra_fix2/logs/f*.log`): `--bot=win --speed=3` seeds 11 / 4242 -> victory 100.6 s (defeated at
99.25 s), 8 jaw hits, 0 hits taken, 0 jaw_glance, `death_clear` 6.98/7.07 -> 14.5 m; `--bot=lose --speed=3` -> 9 fire
ticks, dies 27.85 s, rebuilt, `result=defeat`; windowed `--shots` seed 11 (6 aimed shots, `sheet_final.jpg`) victory.
No SCRIPT ERROR / Parse Error. Requests for core (public push_back, boss near-camera fade): `docs/notes/qa_requests.md`.

## Real model integration (hydra integrator, 2026-11-22) — wins over the older sections below where they differ
Scratch/logs: `work/hydra_int/` (`probe_clips.gd` = socket sampler over every clip, `logs/`, `shots*/`, `sheet.py`).
Model: `game/assets/characters/hydra/hydra.glb` (76 bones, 66,440 tris, 17 clips, rest height 14.38 m).

### Measured in the real clips (probe_clips.gd, boss at the origin facing +Z)
| clip | what | numbers |
|---|---|---|
| head_down (loop 1.5 s) | jaw_c socket | **0.51-0.70 m high, 6.94-6.97 m ahead, x 0.00**: inside the sword's reach, no fallback needed (0 `jaw_fallback` in every run; the fallback code stays for a clip that would leave it high) |
| hurt / death | start on the chin rest | hurt lifts the jaw to 1.9 m at 0.15 s, back at 0.51 m by 0.3 s; death spasm to 3.1 m then collapses |
| fire_sweep(_l) | centre head angle seen from the arc apex (0, 0, 2.5) | -46 deg at 1.6 s, -1.7 at 2.8 s (slows at the centre), +42 at 4.0 s; head 3-5 m high, ~7 m ahead during the rake. `_l` = mirror |
| fire_sweep_return(_l) | head | +43.8 -> -43.8 deg over 0-2.2 s, chin rest at 2.77 s |
| bite | head_c at impact 1.5 s | (0, 1.29, 5.67); the head snaps 10.6 m down between 1.25 and 1.5 s |
| bite_r / bite_l | head_3 / head_6 at impact | (-5.35, 2.99, 1.43) / (5.35, 2.99, 1.43) |
| stomp / stomp_r | foot_fl (+X) / foot_fr (-X) | lifts 1.6 m forward to z 4.5, lands back at (+-1.9, 0, 2.25) at 1.75 s |
| walk | root | in place (root bone never moves): usable for turning on the spot |

### What changed (requests A1-A7 of anim_hydra_fix.md, H1-H5 of assemble_hydra.md)
- **Fire (A1, A2, A3)**: `fire_sweep_l` when the first pass starts on +X (`_fire_side` +1), `fire_sweep` for -1. Inhale speed =
  fire_start / inhale (x1.0, x1.25 enraged); at fire start `set_speed` so fire_start -> fire_end lasts lead-in + one pass (x1.0).
  Enraged: at the end of the first pass `fire_sweep_return(_l)` (blend 0.1, x1.0), then head_down. head_down blends over what
  is left of the fire clip (0.55 s) so the head lands on the chin rest instead of snapping.
- **The stream follows the real head**: flame angle = `fire_head_gain` 1.65 x the mouth's angle from the apex (mouth = midway
  head_c/jaw_c + 0.7 m along the head bone), clamped to 70 + 12 deg. The damage reads the same angles (`_flame_hist`, last
  0.3 s = the burning trail), so the damage arc is exactly the flame that is drawn. Stand-in: the old scripted sweep.
  The visible stream starts once the mouth is below 6.5 m (the head is still diving at fire start). Throat glow at the mouth.
- **Forced fire** (hero kept off the front 4.5 s): the body now turns to the aimed direction (clamped 60 deg) during the
  first 60% of the inhale, because the clip sweeps around the body's forward (before, the arc and the head disagreed).
- **Scorched arc decal**: a soot + ember shader on a disc sector (`ScorchArc`, render priority -12, under the telegraphs),
  painted over the angles the stream has burned, embers cool in 1.6 s, the soot fades in `scorch_fade_time` 7 s.
- **Fire never hides the hero**: stream, core, ground fire and smoke fade out closer than 3 m to the camera (full at 9 m,
  `DISTANCE_FADE_PIXEL_ALPHA`). Stream + ground fire are additive now, ramps end on black (see bug below).
- **head_down (H1)**: the jaw is "reachable" as soon as it is at/below the limit at any moment or once struck (`jaw_ok`
  event), so the hurt flinch can no longer trigger the fallback. Smoke follows the head on the ground.
- **Stomp (A4)**: `stomp_r` when the near forefoot is foot_fr, `stomp` for foot_fl; ring on that foot's planted spot.
- **Bite (A5)**: real head lunges. bite_r (head_3, creature's right -X) / bite_l (head_6, +X) for a hero 25-120 deg off the
  snout, the centre `bite` (head_c) for a hero within 25 deg (once per guard cycle). The warning circle (r 2.5) lies where
  that head lands (`BITES` spots: (+-5.7, 1.6) / (0, 6.0), from the impact sockets pushed ~0.4 m toward the snout) and rides
  on the spot while the body turns (35% of the windup), then locks (pillar, hot glow on the real biting head). A bite is
  chosen only when the hero stands within bite_radius + 1.5 m of a landing spot. The strike resolves when the lunging head is
  below 4.5 m (max 0.15 s late) so damage and the visible landing coincide. `bite_land` event: head 0.14-0.2 m from the
  circle centre for the side bites, 0.3-0.85 m for the centre bite. Stand-in keeps the old hero-following circle.
- **Guard**: the walk clip (x0.9) plays while the body turns more than 6 deg, idle under 2 deg. Idle = the clip's nine heads.
- **Look**: `MODEL_TINT` 0.62/0.52/0.70 -> 0.52/0.40/0.62 (the belly read pink; key_hydra is crimson on black-violet).
- **Arena (hydra_arena.gd)**: a lava moat like key_hydra: EnvKit's grey-box floor disc mesh hidden (its collision kept), the
  cracked shelf ends at radius + 1.5 m with a basalt cliff face into the lava, lava raised to y -0.45, rim rocks/spires stand
  in the lava from radius + 8 m. The glowing lava band now runs across the frame behind the beast.
- **Bot**: jaw stand point 0.7 m outside the jaw (was 1.1), swings only from <= 2.2 m, goes round the outside of the head when it
  arrives on the body side; bite: runs out of the landing circle, rolls 0.3 s before impact if still inside.
- `--hydra-side` now also freezes the guard turn (test only) so the bot can wait by a side head's landing spot (7.2 m, 86 deg).

### Bug found and fixed: black / orange balls in the air
Windowed shots showed a hard black ball (and an orange one) hanging where the mouth had been after every fire, and a
black blob at the smoke emitter. Isolated in the arena with test emitters: CPUParticles3D draws its idle particle slots at
the emitter in the colour ramp's LAST colour. Fix: fire ramps end on black with additive blending (invisible), the smoke
uses a plain grey material (no ramp), and the fire emitters are hidden 1.5 s after the fire. Devlog:
`docs/devlog/media_inbox/hydra_int/before_black_blobs_bright_scorch.jpg` (also the first, far too bright ember pattern).

### Proof (2026-11-22, final code; logs in work/hydra_int/logs/)
| run | result |
|---|---|
| `--bot=win --speed=3` seeds 11 / 4242 / 7 (win2_*.log) | victory at 98.86 / 98.89 / 98.84 s, 8 jaw hits in 8 openings, 0 hits taken |
| `--bot=lose --speed=3` (lose2.log) | 9 fire ticks (dot), dies at 27.86 s, arena rebuilt, fight_start again, `result=defeat` |
| `--bot=win --pad --speed=3` (pad2.log) | victory, 8 hits, 0 taken |
| `--bot=win --hydra-side --speed=3` (side_final.log) | victory; bite_r and bite_l used, every bite escaped |
| windowed `--shots` 1280x720 (shots_final, shots_final2) | camera behind the hero, hero lower centre, whole beast towering at guard (top heads cut ~1 m when the hero is within ~8 m), fire from the real head, no black balls. At `--speed=2` windowed the bot is clumsier (one fire tick taken, two enraged openings missed -> timeout at 110 s); headless is the proof |
No SCRIPT ERROR / Parse Error in any log.

### Open / for others
- Camera (core): heads are cut by ~1 m whenever the hero is within ~8 m (CAM_LOCK_MAX_EXTRA 1.0 m). key_hydra shows the whole
  beast; a per-boss allowance (e.g. 2.5 m for the hydra, or a `BossBase.cam_max_extra()` hook) would fix it.
- Art track: the idle keeps the side heads bunched in a vertical crest; key_hydra fans them out wide. The side necks of
  the rig cannot reach far (bite_r snout ~5.5 m out).
- Tuning (core): the module now reads `fire_head_gain`, `bite_spot_reach`, `bite_side_max_deg`, `walk_turn_start_deg`,
  `walk_turn_stop_deg`, `walk_turn_speed`, `fire_fade_near`, `fire_fade_far`, `scorch_fade_time` from its EXTRA table
  (Tuning wins once added). `bite_min_dist` / `bite_max_dist` / `bite_max_deg` are only used by the stand-in now.

## Status (after the review fixes)
- `Godot --headless --path game -- --start=hydra --harness --bot=win --quit-after=240` -> `[H] result=victory`
  (seeds 1/2/3 at speed 1, `--pad`, speed 3), 8/8 jaw hits, 0 player hits, ~84 s game time. No SCRIPT ERROR.
- `--bot=lose` (stands in front) -> fire only, 36 HP per pass (12 + 2 burn ticks), dies at ~38 s (was 86.7 s), `result=defeat`.
- `--hydra-side` (bites from any spot, bot waits 9 m out) -> every bite now escaped by the side step (lock at 35%), victory.
- `--hydra-jaw-fallback` (forces the jaw fallback) -> victory, the jaw is struck on the ground marker.
- Probes (`--hydra-probe=...`, see "Harness-only flags"): block facing the beast -> `blocked` (shield angle to the bite
  origin 49-54 deg, i.e. a hero facing away is at 126-131 deg and is hit); strafing with the shield up -> still
  `blocked`; standing 7 m behind -> bitten (2 bites per cycle) and the forced fire aims at him (clamped 60 deg).

## States as built (numbers: Tuning.HYDRA, then `EXTRA` in hydra.gd)
| state | what happens | timing |
|---|---|---|
| guard | stays at the centre, turns to the player 35 deg/s, idle clip, roar on the first guard | 1.4 s (1.0 s enraged) then picks: stomp if the player is < 4.5 m from a forefoot; bite if 4.5-12 m away and 25-180 deg off the snout (sides AND behind; max 2 bites between fires); fire if the player is within 50 deg of the snout; after 4.5 s in guard a FORCED fire aimed at the hero, clamped to +-60 deg of the snout |
| fire_sweep | inhale: `fire_sweep` clip (speed fits event `fire_start` to the inhale), cone decal 140 deg x 30 m from the neck base (2.5 m ahead of the centre, direction locked at inhale start), glowing throat + light, `hydra_fire_sweep_warn`. The START side is chosen at inhale start (the hero's side) and shown as a bright pulsing line on that edge of the arc. Fire: the stream sweeps in from just outside the start edge (+-(70+12) deg -> 70 deg in 0.35 s), then rakes the arc; first damage tick 0.25 s after fire start; a faint arc outline stays on the floor for the whole sweep. Damage: 12 per 0.25 s inside the stream (+-12 deg) or on the ground it burned in the last 0.3 s, clipped to the arc, unblockable, knockback 1.5 on the first tick; `hydra_fire` loop | inhale 1.5 s (x0.8 enraged); lead-in 0.35 s; each pass 2.2 s; enraged = there and back (4.4 s) |
| head_down | flames stop, `head_down` clip, smoke at the head, `hydra_head_down`, weak point `jaw` (socket `jaw_c`, r 1.1) open for 1 hit. Jaw check: from 0.3 s, once the jaw stops dropping (or at 1.0 s), if it is above 0.1 + SWORD_HEIGHT + r + 0.5 = 4.5 m the weak point moves to a ground marker `jaw_ground` (6.8 m ahead, 1.2 m high) + push_warning + `[H] event=jaw_fallback` | 2.5 s; after the hit the head rises 0.6 s later |
| head_up | jaw closed (back on `jaw_c`), `head_up` clip stretched to 0.8 s | 0.8 s |
| stomp | always after head_up; else from guard. Near forefoot (`foot_fl`/`foot_fr`) lifts: `stomp` clip (event `impact` fitted), ring decal 0.8-5 m, `hydra_stomp_warn`; impact: r 5, 35 dmg, unblockable, knockback 5, dust + sparks + shockwave ring + shake, `hydra_stomp` | 0.9 s (x0.8 enraged) + 0.7 s recover |
| bite | side head on the player's side (`head_1..4` right/-X, `head_5..8` left/+X), `bite` clip (event `impact` fitted), the biting head glows; circle decal r 2.5 follows the player for 35% of the windup, then LOCKS: the decal is replaced by a hot pink-white one, a light pillar (r 2.5, 3.2 m high) stands on it, the head glows hot and pulses, second hiss (pitch 1.35); impact 25 dmg, BLOCKABLE from the biting head's ground position (pulled in so it never lies past the hero), knockback 3.5, `hydra_bite` | 0.8 s (x0.8 enraged), lock leaves 0.52 s (0.41 s enraged) + 0.5 s recover |
| dead | BossBase death clip; `_exit_state` stops fire, loops, decals, bite glow/pillar, restores the jaw | - |
Enraged (hp <= 4): windups x0.8, guard 1.0 s, fire there and back, tint + roar once.

## Decisions taken with the owner away
- Fire sweep direction: the first pass STARTS on the side the player stands on when the inhale begins (shown by the
  bright start edge) and moves away; you follow the flame in and are near the head when it drops. Enraged, the
  return pass comes back at you: wait at the shoulder, then run to the head.
- The arc's apex is the neck base (2.5 m ahead of the body centre), not the centre (escape from 6-7.5 m in front fits
  the 1.5 s inhale at 4.6 m/s).
- Fire damage-over-time (review fix): SPEC's 12 per 0.25 s now really applies. Core's try_hit gives 0.8 s hit i-frames,
  so a tick that lands inside HIT i-frames is applied by hydra.gd itself through the public `player.hp` +
  `health_changed` (flash, soft hurt sound, rumble, `player_hit dot=true`), with no flinch or knockback and never as the
  killing blow (that one waits for try_hit after the i-frames). Roll i-frames still dodge. `dot = true` is already passed
  to try_hit for when core supports it (request 4 below; then delete `_burn_player`'s shim branch).
  Measured standing still in the stream: 36 HP per pass (was 12); taking every fire = 4 x 36 + 4 x 72.
- Burning trail 0.3 s behind the stream (ground-fire VFX lifetime 0.7 s): a roll through the stream needs timing.
- The stream enters from outside the start edge and the first tick comes 0.25 s after fire start (review fix: a hero
  a few degrees short of the shoulder is no longer burned on frame 0).
- Bite is blockable (SPEC §2: the shield blocks quick frontal blows); the shield arc is tested against the biting head
  (review fix: hit_circle tested it against the hero's own position, so any raised shield blocked). The SPEC answer
  "roll" still works; with the lock at 35% a sideways run also escapes (bot: 0 hits in all bite runs).
- Behind the beast is no longer safe (review fix): side heads bite out to 180 deg; the forced fire aims at the hero
  (clamped 60 deg off the snout).
- Stomp only near a forefoot (and always after head_up).
- 1 jaw hit per opening: after the hit the head rises 0.6 s later instead of lying there 2.5 s.
- Real model tint: the generated albedo is bright magenta-violet (mean sRGB 123/24/88) and read pink under the volcano
  light; `MODEL_TINT` (0.62, 0.52, 0.70) multiplies it toward the sheet's black-violet + crimson (stand-ins untouched).
  Lead: drop the tint if the art track darkens the texture.
- Boss stays put at the centre (no walking); collision: BossBase capsule r 2.6 + a horizontal torso capsule
  (r 2.4, chest to hips). Tail and necks have no collision so the hero can reach the head on the ground.
- Lock camera (review fix, hydra side only): the lock point drops toward 4 m height when the hero is closer than 9 m
  (full at 5 m) and blends 35% toward the stream (where it crosses the hero's distance) while the fire rakes.
- Arena mood (review fix): sky ~40% darker, no sun disc (`sun_size` 0.0001, dim halo colour: 0 would make the sky
  shader's smoothstep edges equal), cliff_rock/boulder tint 0.15; scorched band centred at 32.5 m (fire reach + apex
  offset) with a gradient from ~29 m to the rim.
- Loops: `_loop_sound` / the arena's lava loop duplicate the stream and loop WAV through `loop_mode` (Ogg/MP3 `loop`).

## Bot strategy (bot_advice)
1. Guard: stand on the boss->player line 7.5 m out (6.6 m enraged): in front of the snout (no bites), > 4.5 m from the
   forefeet (no stomp), close enough to reach a shoulder during the inhale.
2. Inhale: run to the nearer shoulder (outside the arc, 84 deg from the fire direction, 4.5-6 m from the apex).
3. Fire: outside the arc wait; when the LAST pass has gone by (stream half + trail + 8 = 39 deg behind it) follow it in
   toward the predicted jaw spot; inside the arc with the stream coming, roll through it when it is < 1.8 m away.
4. Head down: stand 1.1 m outside the jaw on the boss->jaw line (the locked hero faces the boss, so the jaw must be in
   front of him) and attack when the jaw is inside the sword box.
5. Head up / stomp: back away to 8 m from the near forefoot; roll if still inside the ring 0.3 s before impact.
6. Bite: step sideways, roll 0.3 s before impact when inside the circle.

## Harness-only flags in this module (no effect in play)
- `--hydra-side`: bites from any angle + the bot waits 9 m out (exercises bite + roll).
- `--hydra-debug`: `dbg_fire` (flame vs hero angle per tick), `dbg_jaw`, `dbg_choose`, `dbg_bite_from` events.
- `--hydra-jaw-fallback`: forces the head_down jaw fallback (ground marker) to test it with the stand-in.
- `--hydra-probe=block_front|block_strafe|bite_run|behind|edge|head_through` (with `--bot=win`; head_through logs `probe_head`): scripted hero for the review
  measurements (doc comment above `_probe_advice` in hydra.gd). The core bot re-locks every frame, so a "facing away"
  hero cannot be driven; `dbg_bite_from` logs the shield angle to the bite origin instead.
- `--hydra-glb=<abs path> --hydra-manifest=<abs path>`: load a GLB that is not in res://assets yet
  (used: `art_src/chars/hydra/export/hydra.glb` + `work/hydra/probe/hydra_clips.json` built from rig.json sockets).
- Extra harness events: `inhale` (with `side`) and `fire_start` (player angle/distance from the apex), `bite_lock`,
  `enraged`, `attack_resolved` (fire result `burn` = a damage-over-time tick), `jaw_fallback`.

## Probe with the real mesh (art_src export, 66,440 tris, 76 bones, no clips yet)
Loads, scales right (towers over the hero), fire leaves the centre mouth, sockets resolve from rig.json. Without clips it
only warns `no clip 'idle'/'fire_sweep'/...`. The jaw is only hittable if the `head_down` clip brings `jaw_c` low (rig
recipe `head_down_bow`: jaw socket 1.17 m high, ~6.8 m ahead); otherwise the jaw fallback (above) moves it to the
ground marker and warns, so the fight stays winnable.

## Requests for core (docs say: core applies)
1. `Tuning.HYDRA`: add the `EXTRA` keys of hydra.gd (same names; Tuning wins automatically once present), and update to
   SPEC §10: `"head_height": 13.5` (heads 12.2-13.5 m), `"length": 16.0`.
2. `Tuning.CHARS["hydra"]`: `"length": 16.0, "head_height": 13.0` so the stand-in matches §10 (now 18 m / 11 m). After
   that, re-run `--shots` with `--hydra-glb` (or the installed GLB) to check the lock framing at 14.4 m.
3. Optional: `Sfx` has no loop helper; hydra.gd plays `hydra_fire` (and the arena `lava_loop`) with its own
   AudioStreamPlayer(3D). A shared `Sfx.loop(name, pos) -> Node` would be cleaner.
4. `Player.try_hit` option `dot = true` (damage-over-time tick): ignore HIT i-frames (not roll i-frames), no flinch, no
   knockback, can kill. hydra.gd passes it already; it then drops its `_burn_player` shim (writes `player.hp` directly).
5. Camera/HUD at the shoulder: clamp the lock pitch so the hero's feet stay above the boss bar, or move the boss bar
   lower / make it thinner (it covers the hero's feet in every locked frame).
6. StandIn hydra `head_down` pose: lower or shrink the centre head (or fade it when it is between the camera and the
   hero); at the strike it hides most of the hero. The real model lies lower and closer (6.8 m vs 10.5 m).

## Requests for the art / audio track
- hydra clips with events: `fire_sweep` (`fire_start`, `fire_end`), `stomp` and `bite` (`impact`), `head_down` reaching the
  `head_down_bow` pose (see above), a `bite` that lunges the head on the attacking side if possible (the code picks
  `head_1..8` by side; a per-side clip `bite_l`/`bite_r` would read better: tell me and I will pick it).
- Audio files listed in docs/audio_list.json (hydra_*, lava_loop) are played already; silent until they exist.

## Known gaps
- Stand-in: one bite clip for all heads (no lunge; the glow + pillar carry the read); the stand-in head in head_down
  blocks much of the view when the hero stands at the jaw (core request 6).
- Stand-in is still 11 m tall / 18 m long until core request 2.
- The hero's lock-on facing means the jaw must be struck from outside (snout side); striking from the side of the head
  needs the player to unlock (works, the bot does not do it).
- Fire-loop / lava-loop WAV path only checked in code (no audio files exist yet).
- No footstep/body sounds for the boss; no per-head idle motion.
- Decals sit at y 0.04 on a flat floor (the shelf is flat, so fine).

## Final-check fixer pass (2026-11-23, cyclops + hydra fixer; owner away, decisions marked **Decision**)
Scratch/logs: `work/cychyd_fix/` (logs/F_*.log = final runs, m*/n*/q* = the iterations below, shots/hyd1, sheet_hyd.jpg).
Finding: the win bot missed jaw openings (final_verify campaign `--keys` seed 11: 12 openings for 8 strikes, ~155 s).
Cause, measured with `--sword-debug --hydra-debug`: (1) the bot swung from up to 2.2 m ahead / 1.65 m to the side;
on the LYING jaw (y 0.5-0.65, enraged openings) the slash's gap is about (flat distance - 1.33 m), so a swing from
1.3 m scraped (gap -0.02) and one from 1.6 m beside it glanced (+0.05) and the 2-hit combo ate the rest of the opening;
(2) enraged, the return pass of the fire ends on the hero's flank, ~6-7 m from the jaw, and the walk round the old
waypoint (1.4 m out, 1.3 m aside) took ~1.9 s of the 2.5 s opening.
Bot changes (hydra.gd `bot_advice`, real model only; the stand-in keeps the old rules):
- front stand 0.7 -> 0.2 m past the jaw (`BOT_JAW_STAND`): inside the resting-head collider, so the hero stops against
  its rounded end ~1.0 m from the jaw (the bot's stick stops 0.6 m short of any target, so the old 0.7 left him at ~1.3 m);
- from the flank: a waypoint just clear of the head's rounded end (1.3 m past, 0.8 m to his side), then the front stand;
- swing at the lying jaw only within 1.15 m flat (`BOT_JAW_REACH`), from past the jaw (rel > 0.3: beside the head the
  swing's forward step carries him toward the body, gap ~0) and with the jaw within 1.2 m of the hero -> boss line; the
  dropping jaw (y >= 1 m, first ~0.5 s) keeps the old reach. It keeps swinging while the jaw stays exposed.
- Tried and dropped: a roll toward the stand point (strikes 1.80 s vs 1.68 s running: the locked roll curves round the
  beast), aiming inside the head's side (he stuck against it, or slid slowly: --keys 2.4 s), a front stand offset to
  his side (no gain).
Harness probes (harness only): `--jaw-stand=<m>`, `--jaw-reach=<m>`, `--jaw-wait=<s>`.
Person-like reach (**check asked by the lead**): from where the head visibly lies, i.e. standing against its rounded
end (~1.0 m from the jaw centre), both swings connect: attack_1 gap -0.25..-0.44 m, attack_2 (chop) -0.36 m. From
~1.3 m out attack_1 only scrapes (~0), from the side of the head ~0 (+0.04..-0.09). So a player must step right up to
the snout. **Decision**: no gameplay change (jaw_radius lives in core's Tuning: 1.1). If play-testers whiff, raise
`Tuning.HYDRA.jaw_radius` to ~1.3 (+0.2 m of reach; the glow grows with it).
Runs (headless `--speed=3`, final code): win seeds 11 / 4242 / 7 = victory 99.48 / 99.57 / 99.48 s, 8 openings for 8
strikes, 0 hits (strike 0.53-0.58 s into the opening, enraged ~1.9 s of 2.5 s); `--keys` seed 11: 8/8, 98.21 s
(enraged strikes 2.23-2.42 s: the WASD bot's locked side-steps are slow, small margin); `--pad` seed 7 (iteration m1):
8/8, 96.84 s. Lose seed 11: 9 hits, died 27.85 s, fight_start again, `result=defeat`. No SCRIPT ERROR / Parse Error.
Visual check (windowed, 6 shots: guard, inhale, jaw, bite, LABOR COMPLETE x2): nothing clips the camera or hides the
hero. Still open, not mine or not quick: the inhale warning paints most of the floor in front a flat orange (reads as
paint, not lava glow as in key_hydra.png); while circling at full side input the hero's front is half shown (core
locomotion, 95 deg body turn).
