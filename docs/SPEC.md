# HERCULES — game spec and technical contract (v1, 2026-11-22)

This file is the contract every agent builds against. If something here is wrong or missing, do not improvise
silently: write the question/decision in `docs/notes/<your-role>.md` and pick the simplest reading.

Source of truth for the design: `docs/Hercules Boss Fight Requirements.docx` (owner's brief, summarized in §2-§4),
the gameplay reference video `art_src/reference_video/gameplay_reference_480p.mp4` (look + camera + boss scale),
and the owner's words: "like a boss fight where the creatures are a lot bigger, you circle around them dodging
their attacks, and the camera stays right behind the character being controlled" (never name another game anywhere).

## 1. Pillars
1. Third-person boss fights against towering creatures. Camera sits right behind Hercules.
2. Read the warning, dodge or block, reach the exposed weak point, strike. Same sword, shield, health all game.
3. Cel-shaded look that matches the owner's character sheets (`art_src/sheets/`).
4. Three islands + a home base, linked by flying Pegasus over open water. Beating a boss opens the next island.

Engine: **Godot 4.7.2** (`/Applications/Godot_4.7.2.app/Contents/MacOS/Godot`), Forward+, Jolt physics, GDScript.
Project root: `~/HerculesGame/game` (the repo root `~/HerculesGame` also holds docs, tools and art sources).
Input: keyboard + mouse AND Xbox controller, prompts follow the last-used device.

## 2. Player — Hercules (1.9 m)
| Thing | Value |
|---|---|
| Health | 100. No healing in a fight. A loss restarts the same fight, both sides at full health |
| Run (free) | 6.0 m/s, turns toward movement |
| Locked-on movement | 4.6 m/s, always faces the boss: circle left/right, close in, back away |
| Roll | 0.70 s, 4.8 m in the stick direction (or backward with no input), invulnerable 0.08-0.45 s, 0.12 s recovery |
| Sword | 2-hit combo: `attack_1` (0.55 s, active 0.18-0.32) then `attack_2` (0.65 s, active 0.22-0.38) if pressed again |
| Sword damage | 1 per hit, ONLY on an exposed weak point. Any other boss contact = glance: spark + clang, 0 damage |
| Shield (hold) | Blocks quick frontal blows inside a 120 degree front arc. Cannot attack or roll while raised (0.1 s to lower) |
| Petrified | Stone material, no control, 1.5 s, then 1.0 s of invulnerability |
| Hit | 0.4 s flinch, 0.8 s invulnerability, knockback |

Lock-on engages automatically when a fight starts; a button toggles it. Free camera orbit when not locked.

## 3. Bosses
Common: each boss is a state machine with a readable warning before every attack (animation + ground decal +
sound). Bosses take damage only on a weak point while it is exposed. Below half health they speed up.
All numbers live in `game/scripts/data/tuning.gd` (one place).

### 3.1 Cyclops — quarry island (height 8.0 m, 8 hit points)
Arena: flat ring of packed earth (radius 30 m) in a sunlit seaside quarry, broken columns on the rim, sea beyond.
| State | Warning | Effect | Answer |
|---|---|---|---|
| approach | - | walks toward the player (2.6 m/s), turns 70 deg/s | - |
| sweep (quick backhand) | 0.6 s windup, club drawn back low, arc decal | 150 degree front arc, 10 m reach, 25 dmg, blockable | raise the shield (or roll through) |
| slam (two-handed) | 1.4 s windup, club high with the upper two arms, shadow circle decal that follows the player until 0.35 s before impact | circle r 3.4 m, 45 dmg, BREAKS guard | roll sideways as the club falls |
| stuck | club stuck in the earth 3.0 s, forearm low | weak point `forearm` exposed, max 2 hits | strike the forearm |
| pull_free | 0.8 s, roar | - | back off |
Pattern: sweep, sweep, slam (25% chance a sweep is skipped). Below half: windups x0.8, sometimes two slams in a row.

### 3.2 Medusa — sanctuary island (upright 6.5 m, tail ~14 m, 6 hit points)
Arena: circular pale marble courtyard (radius 28 m) ringed by petrified warriors standing OUTSIDE the fighting lane.
| State | Warning | Effect | Answer |
|---|---|---|---|
| stalk | - | slithers to keep 9-14 m, turns 90 deg/s | - |
| gaze | eyes light up 1.2 s, a narrow fan of light on the floor (24 deg, 26 m). Direction locks 0.5 s into the windup | beam 1.0 s: 30 dmg + petrify 1.5 s | (a) circle past the fan and cut the exposed side of her neck (weak point `neck` exposed from fire start to 0.8 s after), or (b) raise the shield facing her as it fires: the gaze reflects |
| stunned (reflected) | she recoils and lowers her head to the floor 3.0 s | weak point `neck` exposed, max 2 hits | run in and strike |
| tail_swipe | if the player stays within 5.5 m for 1.5 s: 0.7 s coil, ring decal | 360 degree low sweep r 7 m, 20 dmg, knockback | roll or back off |
Below half: a second gaze 0.6 s after the first at a new angle.

### 3.3 Hydra — volcano island (shoulder 6.5 m, heads to ~11 m, body+tail ~18 m, 8 hit points)
(The brief calls it "Dragon"; the owner confirmed it is the nine-headed black, violet and crimson Hydra.)
Arena: broad black basalt shelf (radius 34 m), lava glowing beyond the rim, scorched arcs mark the fire's reach.
| State | Warning | Effect | Answer |
|---|---|---|---|
| guard | - | stays near the centre, turns toward the player 35 deg/s | - |
| fire_sweep | centre head rears back and inhales 1.5 s, throat glows, scorched arc decal lights up | fire rakes a 140 degree arc out to 30 m over 2.2 s (longer than a roll), 12 dmg per 0.25 s | circle toward the shoulder (outside the arc) while it inhales |
| head_down | flames stop, the smoking head drops to the ground 2.5 s | weak point `jaw` (soft underside) exposed, 1 hit per opening | strike beneath the jaw |
| stomp | the near foreleg lifts 0.9 s, ring decal | circle r 5 m around that foot, 35 dmg | withdraw / roll |
| bite | a side head draws back 0.8 s with a hiss, circle decal on the player | r 2.5 m, 25 dmg | roll |
Order after a fire sweep is always head_down then stomp. Below half: the fire sweeps there and back.

## 4. World and flow
`title` -> `home` (home base island, on foot) -> mount Pegasus -> `sea` (fly over open water) -> land on an
island -> boss arena (`cyclops` / `medusa` / `hydra`) -> victory -> back on Pegasus over the sea.
- Islands on the sea map (metres, +X east, -Z north): home (0, 0), cyclops (520, -380), medusa (-640, -700),
  hydra (120, -1350). Unlock order cyclops -> medusa -> hydra. Locked islands sit inside a dark storm wall;
  unlocked ones have a pillar of light. After the Hydra: ending card, then free flight.
- Flight: third person behind Pegasus, 28 m/s (boost 46), steer yaw + pitch, height 12-140 m. Flying into an
  island's landing ring lands (fade, then the arena scene). The home ring lands at home.
- Home base: small green plateau with a temple, three trophy pedestals (one fills per defeated boss), a sign
  with the controls, Pegasus waiting. Interact with Pegasus to mount.
- Save: `user://save.json` (bosses defeated). Harness runs never touch it.

## 5. Camera, controls, HUD
Camera: SpringArm chase camera, right behind and slightly above Hercules, FOV 70. Locked on: the camera stays
behind the player on the player->boss line and tilts up so the boss's upper body stays in frame (aim point =
boss `get_lock_point()`), distance 6.5 m, height 2.4 m. It never shows the player from the front in play.
| Action | Keyboard/mouse | Xbox |
|---|---|---|
| move | WASD | left stick |
| camera | mouse | right stick |
| roll | Space | B |
| attack | left mouse | RB (also X) |
| shield (hold) | right mouse | LB |
| lock-on toggle | Q / middle mouse | R3 |
| interact / mount / land | E | A |
| boost (flight) | Shift | RT |
| pause | Esc | Start |
Menus: B = back, A = accept, D-pad/left stick navigate.
HUD: player health top-left, boss name + health bar bottom centre, lock-on reticle, prompts, island title card,
"LABOR COMPLETE" / "DEFEATED" overlays, pause menu (Resume, Controls, Restart fight, Return home, Quit), title
screen (New game, Continue, Controls, Quit). Original wording only.

## 6. Art direction
Cel-shaded: flat albedo from the generated textures, 2-3 light bands, soft rim light, dark ink outline
(inverted hull) on characters and large props. Sunny Mediterranean quarry; pale marble sanctuary; black basalt
and orange lava. Painted-looking gradient sky, flat stylized sea with foam bands. Match the keyframes in
`art_src/reference_video/key_*.png`.

## 7. Project layout and ownership
```
game/project.godot                     core
game/scenes/main.tscn                  core (only scene file required; everything else is built in code)
game/scripts/autoload/game.gd          core   autoload `Game`
game/scripts/autoload/controls.gd      core   autoload `Controls` (device-aware prompts, pad handling)
game/scripts/autoload/sfx.gd           core   autoload `Sfx` (play(name, pos?) - silent if the file is missing)
game/scripts/data/tuning.gd            core   class `Tuning` - every number in §2-§4
game/scripts/visual/character_visual.gd core  class `CharacterVisual`
game/scripts/visual/telegraph.gd       core   ground decals (circle, cone/arc, ring)
game/scripts/player/*.gd               core   `Player`, `PlayerCamera`
game/scripts/combat/*.gd               core   `WeakPoint`, sword hitbox
game/scripts/bosses/boss_base.gd       core   class `BossBase`
game/scripts/world/arena_base.gd       core   class `ArenaBase`
game/scripts/ui/*.gd                   core   HUD, title, pause, overlays
game/scripts/test/*.gd                 core   harness + bot
game/shaders/*.gdshader                core   toon, outline, water, sky
game/scripts/bosses/cyclops.gd + game/scripts/world/cyclops_arena.gd     cyclops module
game/scripts/bosses/medusa.gd  + game/scripts/world/medusa_arena.gd      medusa module
game/scripts/bosses/hydra.gd   + game/scripts/world/hydra_arena.gd       hydra module
game/scripts/world/home_base.gd, sea_world.gd, pegasus_flight.gd, island_proxy.gd   world module
game/assets/characters/<id>/<id>.glb + <id>_clips.json                   art track (ids: hercules, cyclops, medusa, hydra, pegasus)
game/assets/props/*.glb, game/assets/audio/**, game/assets/ui/**         art / audio track
```
A module edits only its own files. A change needed in someone else's file goes in `docs/notes/<role>.md` as a
request (core applies it), unless the lead says otherwise.

### 7.1 Core API (GDScript, exact names)
```gdscript
# autoload Game
signal progress_changed
var defeated := {"cyclops": false, "medusa": false, "hydra": false}
var args: Dictionary            # parsed user args after "--" (e.g. {"start":"cyclops","harness":true})
var harness: bool               # true in automated runs: no mouse capture, no save, fixed seed
func is_unlocked(island: StringName) -> bool
func mark_defeated(boss: StringName) -> void
func goto(scene_id: StringName, opts := {}) -> void   # "title","home","sea","cyclops","medusa","hydra","ending"; fades
func player() -> Player         # current player or null

# class CharacterVisual extends Node3D
static func create(char_id: StringName) -> CharacterVisual
    # loads res://assets/characters/<id>/<id>.glb when present, else a grey-box stand-in built from Tuning.CHARS[id]
func play(clip: StringName, blend := 0.15, speed := 1.0) -> void     # unknown clip: ignored with one warning
func has_clip(clip: StringName) -> bool
func clip_length(clip: StringName, fallback := 1.0) -> float
func event_time(clip: StringName, event: StringName, fallback: float) -> float  # from <id>_clips.json
func socket(name: StringName) -> Node3D      # follows a bone (or a stand-in marker): "hand_r","forearm_l","head", weak points...
func flash(color: Color, seconds := 0.12) -> void
func set_petrified(on: bool) -> void
func set_upper_twist(angle: float, head_extra := 0.0) -> void   # radians about the vertical on top of the clip, spread
    # over the "spine*" bones (+ head_extra over "neck*"/"head*"); (0, 0) = off. The hero's locked-on run uses it (§10 note)
signal clip_finished(clip: StringName)

# class Player extends CharacterBody3D            (group "player")
signal died
signal health_changed(hp: int, max_hp: int)
var hp: int
var invulnerable: bool
func try_hit(dmg: int, from: Vector3, opts := {}) -> StringName
    # opts: blockable=true, guard_break=false, petrify=0.0, knockback=4.0, reflect=false
    # returns "hit" | "blocked" | "dodged" | "reflected" (reflect only when opts.reflect and shield raised facing `from`)
func is_blocking_towards(pos: Vector3) -> bool
func set_control(enabled: bool) -> void
func set_lock_target(boss: BossBase) -> void

# class WeakPoint extends Area3D                    (collision layer 5)
var exposed := false
var hits_left := 0                                  # set when exposed; 0 = closed
signal struck(point: WeakPoint)

# class BossBase extends CharacterBody3D           (group "boss")
signal defeated
signal health_changed(hp: int, max_hp: int)
var boss_id: StringName; var display_name: String; var max_hp: int; var hp: int
var player: Player; var visual: CharacterVisual; var arena: ArenaBase; var state: StringName; var state_time: float
func start_fight() -> void
func set_state(s: StringName) -> void               # calls _exit_state(old), _enter_state(new); _tick_state(delta) each physics frame
func face_towards(pos: Vector3, deg_per_sec: float, delta: float) -> void
func add_weak_point(id: StringName, socket_name: StringName, radius: float) -> WeakPoint
func expose(id: StringName, hits: int) -> void ; func close_weak(id: StringName) -> void
func take_weak_hit(point: WeakPoint) -> void        # -1 hp, flash, hurt clip, defeated at 0
func get_lock_point() -> Vector3
func hit_circle(center: Vector3, radius: float, dmg: int, opts := {}) -> StringName   # calls player.try_hit when inside
func hit_cone(origin: Vector3, dir: Vector3, half_angle_deg: float, length: float, dmg: int, opts := {}) -> StringName
func enraged() -> bool                              # hp <= max_hp / 2
func bot_advice() -> Dictionary                     # for the test bot: {move_to: Vector3, face: Vector3, roll: bool, block: bool, attack: bool}

# class ArenaBase extends Node3D
var radius: float; var player: Player; var boss: BossBase; var hud
func build_environment() -> void                    # override: floor, props, light, sky
func spawn_boss() -> BossBase                       # override
func telegraph_circle(center: Vector3, radius: float, seconds: float, color := Color.RED) -> Node3D
func telegraph_cone(origin: Vector3, dir: Vector3, half_angle_deg: float, length: float, seconds: float, color := Color.RED) -> Node3D
func telegraph_ring(center: Vector3, inner: float, outer: float, seconds: float, color := Color.RED) -> Node3D
```
Collision layers: 1 world, 2 player body, 3 boss body, 4 player sword, 5 boss weak points, 6 triggers.

### 7.2 Test harness (core)
`Godot --path game [--headless] -- --start=<scene_id> --harness [--bot=win|lose|idle] [--shots=<dir>] [--shot-every=<s>] [--quit-after=<s>] [--speed=<time scale>] [--pad]`
Prints one line per event `[H] t=12.34 event=<name> k=v ...` and ends with `[H] result=victory|defeat|timeout|quit`.
`--bot=win` drives the player from `boss.bot_advice()` (proves the fight can be won); `--bot=lose` stands still.
`--shots` needs a real window (not `--headless`); keep it 1280x720. `--pad` feeds the same inputs as joypad events.

## 8. Character assets (art track -> game)
Blender: Z up, character faces -Y, feet on Z=0, metres. Export GLB (+Y up, faces +Z in Godot).
| id | Size | Rig | Sockets / weak points (logical names) |
|---|---|---|---|
| hercules | 1.9 m | Higgsfield (Meshy) auto-rig, humanoid | hand_r (sword), forearm_l (shield), head, chest |
| cyclops | 8.0 m | auto-rig body + own bones for the lower arm pair | hand_ur, hand_ul (club), forearm_ur (weak point `forearm`), head |
| medusa | 6.5 m upright, tail back ~14 m | own rig: spine, neck, head, arms, tail chain, snakes | head, neck (weak point `neck`), tail_tip |
| hydra | shoulder 6.5 m | own rig: body, 4 legs, tail, 9 necks x chain + jaws | head_c, jaw_c (weak point `jaw`), foot_fl, foot_fr, head_1..8 |
| pegasus | withers 1.9 m | own rig: spine, neck, head, 4 legs, tail, 2 wings | saddle (rider), head |
`<id>_clips.json`: `{"sockets": {logical: bone}, "socket_offsets": {...}, "clips": {name: {"length": s, "loop": bool, "events": {name: s}}}}`.

Clips (every clip gets a Seedance 2.5 front+side reference video and is keyframed to match it — see `docs/ANIM_PIPELINE.md`):
- hercules: idle, run, strafe_l (strafe_r = mirror), walk_back, roll, attack_1, attack_2, block_start, block_idle, hit, death, ride
- cyclops: idle, walk, sweep, slam, stuck, pull_free, hurt, death
- medusa: idle, slither, gaze, stun_start, stunned, rise, tail_swipe, hurt, death
- hydra: idle, walk, fire_sweep, head_down, head_up, stomp, bite, hurt, death
  (as built 2026-11-23 also: bite_l, bite_r, fire_sweep_l, fire_sweep_return, fire_sweep_return_l, stomp_r, hurt_standing,
  death_standing, and the turn-in-place walks **walk_turn_l / walk_turn_r** (2.1667 s loops, `move_speed` 1.2 = forefoot
  speed along its arc at x1; manifest keys `start_time` 1.5833 = the phase a turn walk starts at, `stop_window`
  [1.48, 1.68] = the phase where all four feet are nearest the stance: hydra.gd stops a turn walk, and starts an attack
  out of one, inside it). hydra.gd plays walk_turn_l / _r by the sign of the body's turn rate; `walk` keeps `move_speed` 1.73.)
- pegasus: idle, fly, glide
Events the game reads: attack_1/attack_2 `active_start`,`active_end`; sweep/slam/tail_swipe/stomp/bite `impact`;
gaze `fire_start`,`fire_end`; fire_sweep `fire_start`,`fire_end`. Game logic uses the §3 numbers as defaults and
stretches clip speed to fit them, so animation lengths do not have to match exactly.

## 9. Definition of done
1. From the title screen a player can: walk at home, mount Pegasus, fly to each island in order, fight and beat
   the three bosses, see the ending — with keyboard/mouse and with an Xbox controller.
2. `--bot=win` wins each fight and `--bot=lose` loses and restarts it, headless, no script errors in the log.
3. Every attack has a visible warning; weak points only take damage while exposed; glancing hits clang.
4. Real generated, rigged, animated characters (not grey boxes) in every scene; camera behind the player; bosses tower.
5. macOS app in `builds/`, README with controls, devlog complete.

## 10. As built (2026-11-22, after rigging) — these numbers win over §3/§8 where they differ
| id | bones | triangles | real size of the rigged model |
|---|---|---|---|
| hercules | 29 (Meshy auto-rig 22 deform + root + driven skirt bones) | 30,529 | 1.90 m |
| cyclops | 29 | 41,209 | 8.0 m tall; club 5.5 m in `hand_u_r` (rest pose: club held up, top at 11.4 m) |
| medusa | 35 | 70,000 | 6.5 m upright; tail 9.9 m along the ground behind her (not 14 m) |
| hydra | 76 | 66,440 | shoulder 6.5 m, heads 12.2-13.5 m, horn tips 14.4 m, 16.0 m long, 10.1 m wide across the necks |
| pegasus | 43 | 69,986 | withers 1.9 m, 3.0 m to the wing tops at rest, 2.9 m long |
Exact bones, sockets, chains and limits: `art_src/chars/<id>/rig.json` and `docs/notes/rig_<id>.md`.
Camera and arena code must frame a 14 m tall Hydra and an 8 m Cyclops (use the model's real bounds, not constants).
Module scripts must not use `class_name` (core loads them by path; it keeps parallel Godot runs from fighting over the
class cache). If you ever need `Godot --headless --path game --import`, take the lock first:
`until mkdir work/.import_lock 2>/dev/null; do sleep 2; done; <import>; rmdir work/.import_lock`.

### 10.1 Combat as built (play-test QA, 2026-11-22) — these win over §2/§3 where they differ
Numbers live in `game/scripts/data/tuning.gd` and the boss scripts; reasons in `docs/notes/integrate_player.md` and the module notes.
| Thing | SPEC §2/§3 | As built |
|---|---|---|
| Locked-on backing away | 4.6 m/s | 2.4 m/s (walk_back clip, no skating); a roll covers fast retreats |
| Locked-on side-step | 4.6 m/s | 1.8 m/s for 0.3 s, then a circling run at 4.6 m/s |
| Sword active windows | 0.18-0.32 / 0.22-0.38 s | 0.20-0.31 / 0.195-0.357 s (clip events at the play speed) |
| Cyclops sweep | 150 deg front arc, 10 m | 155 deg cone offset to his right (-115 to +40 deg), 7.6 m reach: 45 deg to his left or 8.5 m away is safe |
| Medusa stalk / gaze | keeps 9-14 m, gaze from 10 m | keeps 6-9 m, gazes from 8 m |
| Medusa tail_swipe | if within 5.5 m for 1.5 s: 0.7 s coil, ring r 7 m, "roll or back off" | Medusa x1.5: trigger within 6.0 m of her root for 1.5 s. Rule: **roll out of the ring before it fills**. Ring = hit radius 9.0 m from her body centre (only the inner part of the 14 m visual tail counts), fills in 1.5 s (enraged too; enraged only the sweep is faster), the sweep comes once it is full. One roll clears it from the trigger edge, two from beside her body; unlocked running out also works; backing off locked (2.4 m/s) does not. On-screen hint on the first two swipes. Proof: work/medusa_fix3/tail_probe.gd |
| Medusa gaze neck cut | 2 hits | 1 hit per gaze (stunned: 2) |
| Enraged windups | x0.8 | Cyclops x0.8, Medusa x0.85, Hydra x0.8 |
| Hero death | - | death clip from 0.25 s at 1.6x (props drop ~1.2 s, lying ~2.2 s); DEFEATED hold 4.5 s before the restart; boss bar + reticle hidden at the blow, camera rises 0.6 m, DEFEATED fades in at 1.4 s in the upper third |
| Lock camera | 6.5 m arm, 2.4 m high | per boss: cyclops/medusa 2.9 m arm, 1.2 m high (hero ~50 % of the frame, top of the boss cut only inside ~6 m); hydra 3.7 m, 1.3 m, grows up to +3.0 m |
