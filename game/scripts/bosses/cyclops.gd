extends BossBase
## The Cyclops (SPEC §3.1, as built §10): an 8 m four-armed giant with a 5.5 m club in the upper right hand.
## approach -> sweep (blockable low swing) / slam (tracked two-handed slam, breaks guard) -> stuck (club in the earth,
## right upper forearm exposed for 2 hits) -> pull_free (roar) -> approach. Pattern: sweep, sweep, slam with a 25 %
## chance to skip a sweep. Below half health: windups x0.8 and sometimes a double slam (the first one rebounds,
## the second one sticks). Loaded by path from cyclops_arena.gd (no class_name, SPEC §10).
##
## Real model (game/assets/characters/cyclops): every clip is stretched so its `impact` event lands on the SPEC time;
## the giant turns and steps during the slam windup so the club tip comes down on the tracked circle; the crack,
## chunks and dust go where the real club tip enters the earth (the club sinks 0.32 m while stuck, raised earth lip
## around it); the forearm weak point rides the real forearm (socket forearm_ur).
## Club-path numbers below were measured on the GLB with work/cyclops_int/probe_clips.gd (boss-local, +Z forward,
## -X = his right, where the club is).

const T := Tuning.CYCLOPS

# Not in Tuning.CYCLOPS yet (requested in docs/notes/cyclops.md); read through _k() so Tuning wins once core adds them.
const ENGAGE_DIST := 6.5            ## attack once the hero is this close and roughly in front (m)
const ENGAGE_ANGLE := 30.0          ## degrees either side of forward
const APPROACH_TIMEOUT := 5.0       ## after this long walking, attack anyway when within ATTACK_ANYWAY_DIST
const ATTACK_ANYWAY_DIST := 7.0     ## <= the sweep's visible reach - 0.5, so the timeout never pops a sweep that cannot reach
const CLOSE_TURN_DIST := 5.0        ## inside this range he pivots faster (a strafing hero cannot out-turn him)
const CLOSE_TURN_DEG := 110.0
const STALL_TIME := 2.0             ## hero kept close but off his forward this long: attack anyway if inside the sweep arc
const LUNGE_SPEED := 1.2            ## m/s at most while shifting to put the club over the slam circle (was 3.2: a slide)
const LUNGE_ACCEL := 6.0            ## m/s^2: the windup shift gathers and loses speed (no snap at the slam start)
const SLAM_TURN_DEG := 40.0         ## deg/s while turning the club onto the slam circle (was 120: a statue turn)
const SLAM_WINDOW := 1.0            ## a slam starts with the hero within this many m of LAND_LOCAL.z (the walk closes the rest)
const SLAM_CLOSE_WAIT := 1.0        ## s a hero hugging him (closer than the window) may delay the slam
const SLAM_BRAKE_SPEED := 0.6       ## m/s: a due slam waits until the walk has slowed to this (he plants, then winds up)
const SLAM_REBOUND := 0.35          ## seconds between the first and second slam of a double slam
const STEP_INTERVAL := 0.65         ## fallback half walk cycle (the clip's own length wins)
const WEAK_RADIUS := 0.85           ## stand-in forearm weak point radius
const LEG_R_THIGH := 0.55           ## feedback 2: leg blockers (hero pushed out of the legs), real model
const LEG_R_SHIN := 0.42
const WEAK_RADIUS_REAL := 0.7       ## real model: on the real forearm (~0.33 m thick); glow 0.49 m
const WEAK_Y_RANGE := Vector2(0.9, 2.4)  ## stand-in: the weak point centre is kept in sword reach (see notes)
const WEAK_LINE_Y := 1.9            ## stand-in: clamped forearm glow slides down the forearm->club-head line to this height

# Real club path (cyclops_clips.json clips as of 2026-11-22, measured in Godot):
## Slam: the club tip (club.global_transform * (0, 5.05, 0)) is at (0.19, -0.06, 6.08) at the impact frame and at
## (0.19, -0.38, 5.96) once sunk (CLUB_SINK) in the stuck pose; the head centre (4.6 m up the club) at (0.18, 0.19, 5.75).
## LAND_LOCAL = where the sunk tip enters the floor, boss-local (measured crack point 0.16, 5.92): the giant steers so
## it lands on the slam circle's centre, and the crack, chunks and inner dust go there (integration check 2: they used
## to sit 0.45 m short of the tip, at the head centre).
const LAND_LOCAL := Vector3(0.17, 0.0, 5.93)
## While stuck the club pivots about the grip so the tip sinks this far into the earth (the clip leaves it at -0.06 m,
## which read as a club lying on the ground); eased in over CLUB_SINK_IN s, out over the first part of pull_free.
const CLUB_SINK := 0.32
const CLUB_SINK_IN := 0.12
## Sweep: the club is at hero height (lowest vertex < 1.9 m) from -115 deg (his right) to +40 deg, head 6.6-7.2 m
## out (head radius ~0.7 m). The hit cone and its decal cover exactly that: centre -37.5 deg, 155 deg wide, 7.6 m.
const SWEEP_CENTER_DEG := -37.5
const SWEEP_ARC_DEG := 155.0
const SWEEP_REACH := 7.6
const SWEEP_TRAIL_CLIP := Vector2(1.06, 1.44)   ## clip seconds while the club head is below ~4 m: the trail ribbon
## Death (falls backward, root motion): knees down ~1.0 s, back hits the ground ~3.35 s. The club is let go at once
## (play-test: carried by the falling hand it swept through the camera) and topples onto the floor away from the camera.
const DEATH_KNEES := 1.0
const DEATH_BODY := Vector3(0.0, 0.0, -3.2)
const DEATH_BODY_T := 3.35
const CLUB_DROP_DELAY := 0.0        ## s after death before the club starts to topple (final check: let go at once)
const CLUB_DROP_TIME := 0.7         ## s of the topple (eased in: it falls)
## While it topples the club's near fade reaches much further out (final check: the near end of the stuck club still
## crossed the right third of the frame for ~0.6 s under the LABOR COMPLETE card): nothing of it closer than
## CLUB_DROP_HIDE m to the camera is drawn, dithered up to CLUB_DROP_FULL m; back to CLUB_NEAR_* once it lies.
const CLUB_DROP_HIDE := 6.0
const CLUB_DROP_FULL := 8.5
const CLUB_DROP_FADE_BACK := 0.6    ## s to ease the near fade back to CLUB_NEAR_* after the club lands
## Near fade (play-test: the 5.5 m club, stuck in the earth toward the hero, passed through the chase camera and the
## boss mesh is camera_ignore): every toon/ink surface of the boss and its club dithers out closer than NEAR_FULL m
## to the camera and is gone inside NEAR_HIDE m. Uses core's toon/outline uniforms near_fade_hide / near_fade_full
## through CharacterVisual.set_near_fade() (core adopted the fade 2026-11-23; the runtime shader copy is gone).
const NEAR_HIDE := 0.9
const NEAR_FULL := 2.6
## The club fades from further out: stuck in the earth it runs from his hand to ~1.9 m beside the chase camera, and
## at 2.6 m its near end still filled the lower right of the strike frames (windowed check, work/cyclops_fix4).
const CLUB_NEAR_HIDE := 1.8
const CLUB_NEAR_FULL := 4.6
## Stuck club (final check open item 5): in the strike frames the club runs from his hand past the chase camera and
## covered ~50 % of the lower-right quarter (work/cyclops_polish2). While stuck (and the first part of pull_free) its
## fade reaches further out; the forearm (body fade NEAR_*) and its weak-point glow are not touched. Eased over
## CLUB_STUCK_FADE_T s both ways. Re-fix: 4.2-6.8 m hid the whole club (only its shadow stayed): now only the half near
## the camera fades (near point 3.2-3.6 m, grip and weak point 4.6-5.1 m), and the club casts no shadow while faded.
const CLUB_STUCK_HIDE := 3.8
const CLUB_STUCK_FULL := 5.6
const CLUB_STUCK_FADE_T := 0.3
## The dropped club lands with its head at least this far (flat) from the camera (it slides away as it topples).
const CLUB_DROP_CAM_MIN := 7.5
## Real model skin: the GLB albedo (median ~#BF92A2) rendered as a bleached pale lavender (~#C2A8BC lit) under the
## quarry's sun + sky ambient + filmic tonemap; this factor brings the lit band to the sheet's dusty mauve (~#A88DA8).
## Body only (the club keeps its colours).
const SKIN_FACTOR := Color(0.76, 0.70, 0.76)   # windowed: skin median #AD869E, lit #BC93AB (was #C2A8BC / #DDC0CD)
## Enraged sweep: windups x0.8 below half health, but the sweep (the tightest warning in the game) never drops
## under this many seconds (play-test: 0.48 s left 0.13 s to raise the shield after a 0.35 s reaction).
const ENRAGED_SWEEP_MIN := 0.55
## Seconds a turn in progress takes to run out when the sweep starts (the body never stops turning dead).
const TURN_SETTLE := 0.25

const CLUB_PATH := "res://assets/props/club.glb"
const CLUB_LENGTH := 5.0            ## stand-in: grip to head along the club axis (club.glb spans y -0.45..5.05)
const CLUB_TIP := 5.05              ## club tip along the club axis from the grip (club.glb / GLB node `club`)
const CLUB_HEAD_C := 4.6            ## club head centre along the club axis
const CLUB_REST_DEG := Vector3(120, 0, 0)   ## stand-in holder rest tilt (club forward-down from the hand)
## Stand-in only: where hand_ur sits in the procedural `stuck` pose, boss-local (measured, work/cyclops logs).
const STANDIN_STUCK_HAND := Vector3(-2.02, 2.95, 3.51)
const REACT_DELAY := 0.25           ## bot: seconds before it starts for the forearm (a human's reaction to the impact)
const ENRAGE_TINT := Color(1.0, 0.80, 0.74)    # lighter than before (0.68 / 0.62): the real skin is darker now (SKIN_FACTOR)

var _queue: Array[StringName] = []
var _decal: Telegraph = null
var _impact_at := 0.0
var _impact_done := false
var _recover_at := 0.0
var _slam_center := Vector3.ZERO
var _slam_double := false           # this slam rebounds into a second one
var _rebound_entry := false         # the slam state was re-entered after a rebound (softer blend out of the ground)
var _sweep_dir := Vector3.FORWARD   # centre of the sweep cone (world, flat)
var _sweep_speed := 1.0             # playback rate of the sweep clip
var _trail: MeshInstance3D = null
var _trail_pts: Array = []          # [outer, inner] world points along the club's swing
var _trail_dust_t := 0.0
var _was_enraged := false
var _crack: Node3D = null
var _wp_marker: Node3D = null       # stand-in only
var _clamp_reported := false
var _roared := false
var _club: Node3D = null            # the club (GLB node `club` on joint hand_u_r, or the stand-in prop)
var _club_holder: Node3D = null     # stand-in only: module-owned socket that tilts the club
var _club_axis := Vector3.UP        # grip -> head direction in the club's space
var _club_target := Vector3.ZERO    # floor point where the club head sits while stuck (crack + dust go here)
var _club_aim := 0.0                # stand-in: 0 = rest tilt, 1 = head driven into _club_target
var _land_wait := -1.0              # >= 0 after a slam impact until the real club head is seen in the ground
var _land_rebound := false
var _land_prev := Vector3.INF
var _club_rest := Transform3D.IDENTITY   # real model: the club node's own (static) local transform from the GLB
var _club_sink := 0.0               # 0..1: how far the stuck club is pivoted down into the earth (CLUB_SINK at 1)
var _club_in_glb := false           # the club is the GLB's own node (not the fallback prop): it may be sunk
var _stall_t := 0.0
var _pose_reported := false
var _club_released := false         # death: the club left the hand and lies on the floor (arena child)
var _club_fade := 0.0               # 0..1: club near fade from CLUB_NEAR_* to CLUB_STUCK_* (stuck)
# natural movement (gait): he steps whenever the body turns or moves; idle only when both are calm
var _gait := &""                    # &"walk" / &"idle" while approach owns the clip; &"" = an attack clip plays
var _gait_calm := 0.0               # seconds both turn and ground speed have been under the step thresholds
var _yaw_vel := 0.0                 # deg/s, eased (no instant start or stop of a turn)
var _speed := 0.0                   # m/s along his facing, eased
var _yaw_prev := 0.0
var _yaw_rate := 0.0                # measured deg/s of the body this tick
var _turn_goal := 0.0               # deg/s the turn is heading for
var _yaw_vel_entry := 0.0           # |deg/s| of the turn when an attack started (it runs out over TURN_SETTLE s)
var _walk_prev_t := -1.0            # walk clip position last tick (footfalls on the clip's step events)
var _slam_origin := Vector3.ZERO    # where the club would land at the slam start: the circle stays within _slam_budget of it
var _slam_budget := 0.0             # m the windup shift (lunge_speed, lunge_accel) can cover before the impact
var _slam_wait := 0.0               # s a slam has been due with the hero closer than the slam window
var _slam_brake := false            # a slam is due: he stops walking (feet in time) before the windup starts
var _club_shadow := -1              # the club's own cast_shadow setting (-1 = not read yet); off while the stuck fade hides it
## Feedback 2 re-fix (clipping 5:00, hero standing inside the stuck club's shaft): two capsules on the boss layer (3)
## along the club, [from, to, radius] in metres along the club axis from the grip (club.glb radius measured: ~0.5 m at
## 1.5-2.5 m, ~0.8 m at the head). The near surface stops CLUB_BLOCK_FREE m from the grip so the forearm weak point
## (beside the hand) stays reachable. Only while the club stands still: stuck, early pull_free, and lying after death.
const CLUB_BLOCKS := [[2.0, 3.0, 0.55], [3.0, 4.6, 0.8]]
const CLUB_BLOCK_FREE := 1.5
var _club_blocks: Array[StaticBody3D] = []


func _init() -> void:
	boss_id = &"cyclops"
	display_name = "Brontes the Quarry Giant"
	max_hp = T["hp"]
	body_radius = 1.5
	body_height = float(T["height"])
	hurt_blend = 0.2                # BossBase default 0.08 snapped the body into the flinch


## A module number: Tuning.CYCLOPS wins when core has added the key (docs/notes/cyclops.md request 1).
func _k(key: String, fallback: float) -> float:
	return float(T.get(key, fallback))


func _build() -> void:
	_attach_club()
	if visual.is_standin:
		# the stand-in forearm is never in sword reach: the weak point rides a marker kept within reach
		_wp_marker = visual.add_socket(&"forearm_wp", Vector3(0, 2.0, 2.0))
		add_weak_point(&"forearm", &"forearm_wp", _k("weak_radius", WEAK_RADIUS))
		_update_weak_marker()
	else:
		# real model: the stuck clip puts the right upper forearm at 2.15-2.24 m, inside the sword's reach (y <= 2.9 m)
		add_weak_point(&"forearm", &"forearm_ur", WEAK_RADIUS_REAL)
		_apply_looks(visual)
		# feedback 2 (clipping 5:51): the hero's head went into the leg; the legs now push him out (boss layer only)
		add_limb_blocker("thigh_l", "shin_l", LEG_R_THIGH)
		add_limb_blocker("shin_l", "foot_l", LEG_R_SHIN)
		add_limb_blocker("thigh_r", "shin_r", LEG_R_THIGH)
		add_limb_blocker("shin_r", "foot_r", LEG_R_SHIN)
		_make_club_blockers()
	visual.set_near_fade(NEAR_HIDE, NEAR_FULL)     # core toon/outline near-fade uniforms (was a runtime shader copy)
	if _club != null:
		_set_near_fade(_club, CLUB_NEAR_HIDE, CLUB_NEAR_FULL)


func _set_near_fade(n: Node, hide_m: float, full_m: float) -> void:
	visual.set_near_fade(hide_m, full_m, n)


## Real model: SKIN_FACTOR on every body surface (not the club).
func _apply_looks(n: Node) -> void:
	if n == _club:
		return
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for m in _shader_mats(mi):
			if m.shader == CharacterVisual.TOON_SHADER or m.shader == CharacterVisual.toon_shader(true):
				var c: Color = m.get_shader_parameter("albedo_color")
				m.set_shader_parameter("albedo_color", Color(c.r * SKIN_FACTOR.r, c.g * SKIN_FACTOR.g, c.b * SKIN_FACTOR.b, c.a))
	for c in n.get_children():
		_apply_looks(c)


func _shader_mats(mi: MeshInstance3D) -> Array[ShaderMaterial]:
	var out: Array[ShaderMaterial] = []
	if mi.material_override is ShaderMaterial:
		out.append(mi.material_override)
	if mi.mesh != null:
		for i in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(i)
			if m is ShaderMaterial and not out.has(m):
				out.append(m)
	return out




## The club: inside the GLB (node `club` under joint hand_u_r) for the real model; a prop on a tilting holder for the
## stand-in.
func _attach_club() -> void:
	if not visual.is_standin:
		_club = _find_named(visual, "club") as Node3D
		if _club != null:
			_club_rest = _club.transform
			_club_in_glb = true
			return
		_club = visual.attach_prop(&"hand_ur", CLUB_PATH)
	else:
		# stand-in hand marker has no rotation: tilt the club forward-down so it reads as held; while stuck,
		# _update_club() turns this holder so the club head is driven into the ground at _club_target
		_club_holder = visual.add_socket(&"club_holder", Vector3.ZERO, &"hand_ur")
		_club_holder.rotation_degrees = CLUB_REST_DEG
		_club = visual.attach_prop(&"club_holder", CLUB_PATH)
	# the fallback box club (no GLB) hangs along -Y from the grip, the GLB club points along +Y
	if _club != null and String(_club.name).begins_with("Prop_"):
		_club_axis = Vector3.DOWN


func _find_named(n: Node, part: String) -> Node:
	if part in String(n.name).to_lower() and n is MeshInstance3D:
		return n
	for c in n.get_children():
		var f := _find_named(c, part)
		if f != null:
			return f
	return null


func _first_state() -> StringName:
	return &"approach"


# ------------------------------------------------------------------ numbers that change with enrage
func _windup(base_key: String) -> float:
	var w: float = T[base_key]
	if not enraged():
		return w
	w *= float(T["enraged_windup_scale"])
	return maxf(w, ENRAGED_SWEEP_MIN) if base_key == "sweep_windup" else w


func _next_attack() -> StringName:
	_peek_attack()
	return _queue.pop_front()


## The attack the pattern will pick next (rolls a new pattern when the queue is empty).
func _peek_attack() -> StringName:
	if _queue.is_empty():
		_queue = [&"sweep", &"sweep", &"slam"]
		var roll := Game.rng.randf()
		Game.event("cyclops_pattern", {"roll": snappedf(roll, 0.001), "skip": roll < float(T["skip_sweep_chance"])})
		if roll < float(T["skip_sweep_chance"]):
			_queue.remove_at(0)
	return _queue[0]


## Sweep cone: the real club's visible low arc (offset to his right), or the SPEC symmetric arc for the stand-in.
func _sweep_center_deg() -> float:
	return 0.0 if visual.is_standin else SWEEP_CENTER_DEG


func _sweep_half() -> float:
	return (float(T["sweep_arc_deg"]) if visual.is_standin else SWEEP_ARC_DEG) * 0.5


func _sweep_reach() -> float:
	return float(T["sweep_reach"]) if visual.is_standin else SWEEP_REACH


## Signed angle (deg) of a world point seen from the boss: 0 = straight ahead, negative = his right (-X).
func _signed_angle(pos: Vector3) -> float:
	var l := global_transform.affine_inverse() * pos
	return rad_to_deg(atan2(l.x, l.z))


func _in_sweep_arc(pos: Vector3) -> bool:
	return absf(wrapf(_signed_angle(pos) - _sweep_center_deg(), -180.0, 180.0)) <= _sweep_half()


# ------------------------------------------------------------------ states
func _enter_state(s: StringName) -> void:
	_impact_done = false
	match s:
		&"approach":
			_gait = &""             # _update_gait() picks walk or idle from the real motion, with a loco_blend cross-fade
			_gait_calm = 0.0
			_speed = maxf(Vector3(velocity.x, 0.0, velocity.z).dot(forward()), 0.0)
			_yaw_prev = rotation.y         # _yaw_vel carries on: a turn in progress continues smoothly
			_stall_t = 0.0
			_slam_wait = 0.0
			_slam_brake = false
			if not _roared:
				_roared = true          # the opening bellow as the fight starts
				Sfx.play("cyclops_roar", global_position)
		&"sweep":
			_gait = &""             # no halt(): the body eases to a stop over ~0.2 s while the walk fades out (_tick_state)
			_impact_at = _windup("sweep_windup")
			# the body still turns _yaw_vel x TURN_SETTLE / 2 degrees while that turn runs out: aim the cone where he ends up
			_yaw_vel_entry = absf(_yaw_vel)
			_sweep_dir = forward().rotated(Vector3.UP, deg_to_rad(_sweep_center_deg() + _yaw_vel * TURN_SETTLE * 0.5))
			var ev := visual.event_time(&"sweep", &"impact", visual.clip_length(&"sweep", 1.4) * 0.43)
			_sweep_speed = ev / _impact_at
			visual.play(&"sweep", _k("attack_blend", 0.22), _sweep_speed)
			_recover_at = _impact_at + clampf((visual.clip_length(&"sweep", 1.4) - ev) / _sweep_speed, 0.4, 1.0)
			_decal = arena.telegraph_cone(global_position, _sweep_dir, _sweep_half(), _sweep_reach(), _impact_at)
			Sfx.play("cyclops_sweep_warn", global_position)
			_start_trail()
		&"slam":
			_gait = &""             # no halt(): the walk speed eases out at lunge_accel in _steer_club_to (no snap)
			_slam_wait = 0.0
			_slam_brake = false
			_impact_at = _windup("slam_windup")
			# the shift reaches lunge_speed after lunge_speed / lunge_accel s and must settle by the impact
			var top := _k("lunge_speed", LUNGE_SPEED)
			_slam_budget = top * maxf(_impact_at - top / _k("lunge_accel", LUNGE_ACCEL) - 0.15, 0.2)
			# ... from where the walk's momentum (eased out at lunge_accel) carries the landing point
			var hv := Vector3(velocity.x, 0.0, velocity.z)
			_slam_origin = _floor_point(global_transform * LAND_LOCAL) + hv * (hv.length() / (2.0 * _k("lunge_accel", LUNGE_ACCEL)))
			var ev2 := visual.event_time(&"slam", &"impact", visual.clip_length(&"slam", 2.2) * 0.64)
			# out of a rebound the club springs back up from the ground (softer blend), else from the stance
			visual.play(&"slam", 0.3 if _rebound_entry else _k("attack_blend", 0.22), ev2 / _impact_at)
			_rebound_entry = false
			_slam_center = _slam_reachable(_floor_point(player.global_position))
			_decal = arena.telegraph_circle(_slam_center, float(T["slam_radius"]), _impact_at)
			Sfx.play("cyclops_slam_warn", global_position)
		&"stuck":
			halt()
			_yaw_vel = 0.0
			if not fighting:
				return              # never open the forearm after the fight stopped (player died on the slam)
			visual.play(&"stuck", _k("attack_blend", 0.22))
			expose(&"forearm", int(T["stuck_hits"]))
			Sfx.play("cyclops_stuck", _club_target)
			_pose_reported = false
		&"pull_free":
			halt()
			var pf: float = T["pull_free_time"]
			visual.play(&"pull_free", _k("attack_blend", 0.22), visual.clip_length(&"pull_free", pf) / pf)
			Sfx.play("cyclops_pull_free", _club_target)
			Sfx.play("cyclops_roar", global_position)
			Fx.dust(arena, _club_target, 2.0)
			_clear_crack()
		&"idle":
			halt()
			_gait = &""
			_land_wait = -1.0
			visual.play(&"idle", _k("loco_blend", 0.3))
		&"dead":
			halt()
			_land_wait = -1.0
			_clear_crack()
			_death_dust()
			_release_club()


func _exit_state(s: StringName) -> void:
	if s == &"stuck":
		close_weak(&"forearm")
	if s in [&"sweep", &"slam"] and is_instance_valid(_decal) and not _impact_done:
		_decal.cancel()
	if s in [&"sweep", &"slam"]:
		_decal = null


func _tick_state(delta: float) -> void:
	_check_enrage()
	match state:
		&"approach":
			_tick_approach(delta)
		&"sweep":
			# the walk's momentum dies out over ~0.2 s (was an instant halt: the body stopped dead as the swing began)
			var hv := Vector2(velocity.x, velocity.z).move_toward(Vector2.ZERO, float(T["walk_speed"]) / 0.2 * delta)
			velocity.x = hv.x
			velocity.z = hv.y
			_speed = 0.0
			# a turn in progress runs out over turn_settle s instead of stopping dead (_sweep_dir already includes it)
			_yaw_vel = move_toward(_yaw_vel, 0.0, _yaw_vel_entry / TURN_SETTLE * delta)
			rotation.y = wrapf(rotation.y + deg_to_rad(_yaw_vel * delta), -PI, PI)
			if not _impact_done and state_time >= _impact_at:
				_impact_done = true
				_sweep_impact()
				if not fighting or state != &"sweep":
					return          # the sweep killed the hero: stop_fight() already set idle
			if state_time >= _recover_at:
				set_state(&"approach")
		&"slam":
			_tick_slam(delta)
		&"stuck":
			if state_time >= float(T["stuck_time"]):
				set_state(&"pull_free")
		&"pull_free":
			if state_time >= float(T["pull_free_time"]):
				set_state(&"approach")


func _tick_approach(delta: float) -> void:
	var d := player_distance()
	var engage := _k("engage_dist", ENGAGE_DIST)
	var close_d := _k("close_turn_dist", CLOSE_TURN_DIST)
	_turn_smooth(player.global_position, float(T["turn_deg"]) if d > close_d else _k("close_turn_deg", CLOSE_TURN_DEG), delta)
	# he walks along his own facing (never sideways or backwards toward the hero), slower the further he still has to
	# turn: a hero behind him gets an arc / a turn on the spot, not a moonwalk
	var ang := angle_to_pos(player.global_position)
	var want := 0.0
	if d > LAND_LOCAL.z + _k("slam_window", SLAM_WINDOW):
		_slam_brake = false
	if d > engage and not _slam_brake:
		want = float(T["walk_speed"]) * clampf((cos(deg_to_rad(ang)) - 0.3) / 0.7, 0.0, 1.0)
	_speed = move_toward(_speed, want, (_k("walk_accel", 4.0) if want > _speed else _k("walk_decel", 5.0)) * delta)
	var f := forward()
	velocity.x = f.x * _speed
	velocity.z = f.z * _speed
	# intent counts as motion: a walk or turn about to start starts on walk (no one-tick idle flicker)
	_update_gait(delta, want > 0.01 or absf(_turn_goal) > _k("step_on_turn_deg", 15.0))
	var in_front := ang < _k("engage_angle", ENGAGE_ANGLE)
	# a hero circling close to his flank cannot stall him forever: after STALL_TIME he swings if the arc can reach
	_stall_t = _stall_t + delta if (d < close_d and not in_front) else 0.0
	var stalled := _stall_t > _k("stall_time", STALL_TIME) and _in_sweep_arc(player.global_position)
	if stalled:
		Game.event("cyclops_stall_break", {"angle": snappedf(_signed_angle(player.global_position), 0.1), "dist": snappedf(d, 0.01)})
	var timeout := state_time > _k("approach_timeout", APPROACH_TIMEOUT) and d < _k("attack_anyway_dist", ATTACK_ANYWAY_DIST) and in_front
	if (d <= engage + 0.5 and in_front) or timeout or stalled:
		# a slam starts only with the hero near the club's landing distance (the slam clip has no step: the windup
		# shift is short and slow); the walk closes a far gap, a hugging hero delays it at most slam_close_wait s
		if _peek_attack() == &"slam" and not visual.is_standin:
			if absf(d - LAND_LOCAL.z) > _k("slam_window", SLAM_WINDOW):
				_slam_wait += delta
				if d > LAND_LOCAL.z or _slam_wait < _k("slam_close_wait", SLAM_CLOSE_WAIT):
					return
			# he plants his feet first (the walk eases out with the clip) and only then raises the club: entering the
			# slam at walking speed slid him ~0.6 m under the slam clip
			if _speed > _k("slam_brake_speed", SLAM_BRAKE_SPEED):
				_slam_brake = true
				return
		var next := _next_attack()
		if next == &"slam":
			_slam_double = enraged() and Game.rng.randf() < float(T["enraged_double_slam_chance"])
		set_state(next)


## Turns toward `pos` at most `max_deg` deg/s, with an eased start and stop (turn_accel_deg; the rate falls off within
## max_deg / turn_ease degrees of the goal), so a turn never starts or ends with a jerk.
func _turn_smooth(pos: Vector3, max_deg: float, delta: float) -> void:
	var to := pos - global_position
	to.y = 0.0
	var err := 0.0
	if to.length() > 0.01:
		err = rad_to_deg(wrapf(atan2(to.x, to.z) - rotation.y, -PI, PI))
	var goal := clampf(err * _k("turn_ease", 4.0), -max_deg, max_deg)
	_turn_goal = goal
	_yaw_vel = move_toward(_yaw_vel, goal, _k("turn_accel_deg", 360.0) * delta)
	var step := _yaw_vel * delta
	if absf(step) > absf(err) and signf(step) == signf(err):
		step = err                  # never past the goal
		_yaw_vel = err / maxf(delta, 0.0001)
	rotation.y = wrapf(rotation.y + deg_to_rad(step), -PI, PI)


## The gait (owner, 2026-11-23: "the giant must never rotate or slide like a statue"). From the body's real motion this
## tick: walk whenever it turns faster than step_on_turn_deg or moves faster than step_on_speed, idle once both have been
## calm for step_calm s. Walk playback = ground speed / the clip's move_speed (feet do not slide), or the turn rate /
## turn_step_ref_deg when he turns on the spot, clamped to walk_rate_min..max. Footfalls on the clip's step events.
func _update_gait(delta: float, intent := false) -> void:
	_yaw_rate = rad_to_deg(wrapf(rotation.y - _yaw_prev, -PI, PI)) / maxf(delta, 0.0001)
	_yaw_prev = rotation.y
	var ground := Vector2(velocity.x, velocity.z).length()
	var busy := absf(_yaw_rate) > _k("step_on_turn_deg", 15.0) or ground > _k("step_on_speed", 0.3) or intent
	_gait_calm = 0.0 if busy else _gait_calm + delta
	var want := &"walk" if (busy or (_gait == &"walk" and _gait_calm < _k("step_calm", 0.25))) else &"idle"
	if want != _gait:
		var first := _gait == &""
		_gait = want
		visual.play(want, _k("loco_blend", 0.3))
		_walk_prev_t = 0.0
		Game.event("cyclops_gait", {"gait": want, "turn": snappedf(_yaw_rate, 0.1), "speed": snappedf(ground, 0.01), "entry": first})
	if _gait != &"walk":
		return
	var ms := visual.move_speed(&"walk")
	if ms <= 0.01:
		ms = _k("walk_move_speed", float(T["walk_speed"]))
	var rate := maxf(ground / ms, absf(_yaw_rate) / _k("turn_step_ref_deg", 60.0))
	visual.set_speed(clampf(rate, _k("walk_rate_min", 0.5), _k("walk_rate_max", 1.3)))
	_walk_footfalls()


## Thud + shake when the walk clip passes one of its footfalls: every event whose name starts with "step" (one per foot
## when the clip has two), else `step` and `step` + half the clip (two steps per cycle).
func _walk_footfalls() -> void:
	if visual.current_clip != &"walk":
		return
	var clip_len := visual.clip_length(&"walk", _k("step_interval", STEP_INTERVAL) * 2.0)
	var t := visual.clip_position()
	var beats: Array[float] = []
	var ev: Dictionary = ((visual.manifest.get("clips", {}) as Dictionary).get("walk", {}) as Dictionary).get("events", {})
	for k in ev:
		if String(k).begins_with("step"):
			beats.append(float(ev[k]))
	if beats.size() == 1:
		beats.append(fmod(beats[0] + clip_len * 0.5, clip_len))
	elif beats.is_empty():
		beats = [clip_len * 0.25, clip_len * 0.75]
	var p := _walk_prev_t
	_walk_prev_t = t
	if p < 0.0:
		return
	for b in beats:
		if (p < b and b <= t) or (t < p and (b > p or b <= t)):
			_footstep()


func _tick_slam(delta: float) -> void:
	var track_end: float = _impact_at - float(T["slam_track_until"])
	if not _impact_done:
		if state_time < track_end:
			# the shadow circle follows the hero until slam_track_until before the impact
			_slam_center = _slam_reachable(_slam_center.lerp(_floor_point(player.global_position), 1.0 - exp(-6.0 * delta)))
			if is_instance_valid(_decal):
				_decal.global_position = _slam_center
		# all through the windup he turns and steps so the club head will come down on the circle's centre
		_steer_club_to(_slam_center, delta)
	else:
		_ease_velocity(Vector2.ZERO, delta)    # rebound: any shift left dies out instead of stopping dead
	if not _impact_done and state_time >= _impact_at:
		_impact_done = true
		halt()
		var rebound := _slam_double
		_slam_impact(rebound)
		if not fighting or state != &"slam":
			return                           # the slam killed the hero: stop_fight() already set idle
		if rebound:
			_slam_double = false
			_impact_at += _k("slam_rebound", SLAM_REBOUND)   # short rebound, then a fresh tracked slam
		else:
			set_state(&"stuck")
			return
	if _impact_done and state_time >= _impact_at:
		_rebound_entry = true
		set_state(&"slam")


## Turns (at most SLAM_TURN_DEG) and steps (at most LUNGE_SPEED, forward or back) so that the club's landing point,
## LAND_LOCAL in his own frame, sits on `center`. Stand-in: the old lunge (its club is re-aimed while stuck).
func _steer_club_to(center: Vector3, delta: float) -> void:
	var to := center - global_position
	to.y = 0.0
	if to.length() > 0.05:
		# eased like the approach turn (_turn_smooth): no instant start or stop of the body's turn
		var want := atan2(to.x, to.z) - atan2(LAND_LOCAL.x, LAND_LOCAL.z)
		var err := rad_to_deg(wrapf(want - rotation.y, -PI, PI))
		var cap := _k("slam_turn_deg", SLAM_TURN_DEG)
		var goal := clampf(err * _k("turn_ease", 4.0), -cap, cap)
		_yaw_vel = move_toward(_yaw_vel, goal, _k("turn_accel_deg", 360.0) * 1.5 * delta)
		var step := _yaw_vel * delta
		if absf(step) > absf(err) and signf(step) == signf(err):
			step = err
			_yaw_vel = err / maxf(delta, 0.0001)
		rotation.y = wrapf(rotation.y + deg_to_rad(step), -PI, PI)
	if visual.is_standin:
		if to.length() > LAND_LOCAL.z:
			walk_towards(center, _k("lunge_speed", LUNGE_SPEED), LAND_LOCAL.z)
		else:
			halt()
		return
	var err := center - global_transform * LAND_LOCAL
	err.y = 0.0
	var e2 := Vector2(err.x, err.z)
	# wanted speed: err / 0.15 s, capped by lunge_speed and by what still stops in time at lunge_accel (no overshoot)
	var acc := _k("lunge_accel", LUNGE_ACCEL)
	var top := minf(_k("lunge_speed", LUNGE_SPEED), sqrt(2.0 * acc * e2.length()))
	var v := e2 / 0.15
	if v.length() > top:
		v = v.normalized() * top
	_ease_velocity(v, delta)


## Horizontal velocity eased toward `v` (m/s, x/z) at lunge_accel: the slam windup never starts or stops a shift dead.
func _ease_velocity(v: Vector2, delta: float) -> void:
	var hv := Vector2(velocity.x, velocity.z).move_toward(v, _k("lunge_accel", LUNGE_ACCEL) * delta)
	velocity.x = hv.x
	velocity.z = hv.y


## The slam circle centre `p`, kept within _slam_budget of where the club would land at the slam start: the windup shift
## (slow, no step in the slam clip) can always bring the club down on it.
func _slam_reachable(p: Vector3) -> Vector3:
	if visual.is_standin:
		return p
	var off := p - _slam_origin
	off.y = 0.0
	return _slam_origin + off.limit_length(_slam_budget)


# ------------------------------------------------------------------ impacts
func _sweep_impact() -> void:
	var r := hit_cone(global_position, _sweep_dir, _sweep_half(), _sweep_reach(), int(T["sweep_dmg"]),
		{"blockable": true, "knockback": 3.5})
	Sfx.play("cyclops_sweep", global_position + forward() * 5.0)
	if visual.is_standin:
		_sweep_fx()
	Game.shake(0.18)
	Game.event("attack_resolved", {"attack": "sweep", "result": r})


## `rebound`: first slam of an enraged double slam. It bounces back up: no crack, a lighter burst and a sharp
## bellow, so it cannot be mistaken for a slam that sticks.
func _slam_impact(rebound := false) -> void:
	var r := hit_circle(_slam_center, float(T["slam_radius"]), int(T["slam_dmg"]), {"guard_break": true, "blockable": true, "knockback": 5.5})
	Sfx.play("cyclops_slam", _slam_center)
	var aim := _floor_point(global_transform * LAND_LOCAL)
	Game.event("slam_aim", {"err": snappedf(aim.distance_to(_slam_center), 0.01), "rebound": rebound})
	_ring_fx(_slam_center, rebound)
	if visual.is_standin:
		_club_target = _slam_center if rebound else _club_landing(_slam_center)
		_land_fx(_club_target, rebound)
	else:
		# chunks, inner dust and the crack wait for the real club head to be seen in the earth (_process)
		_club_target = aim
		_land_wait = 0.0
		_land_prev = Vector3.INF
		_land_rebound = rebound
	Game.shake(0.45 if rebound else 0.7)
	Controls.rumble(0.6, 1.0, 0.3)
	if rebound:
		Sfx.play("cyclops_roar", global_position, -2.0, 1.35)     # short, high bellow: "again!"
		Game.event("slam_rebound", {})
	Game.event("attack_resolved", {"attack": "slam", "result": r})


## Stand-in: floor point where the club head goes in while stuck, as close to `aim` as the club can reach from the
## procedural stuck pose's hand (STANDIN_STUCK_HAND) with a club that the holder can turn.
func _club_landing(aim: Vector3) -> Vector3:
	var hand := global_transform * STANDIN_STUCK_HAND
	var hy := maxf(hand.y - global_position.y, 0.0)
	var reach := CLUB_LENGTH - 0.4          # a little slack so the head ends up buried, never hovering
	var max_flat := sqrt(maxf(reach * reach - hy * hy, 0.0))
	var flat := Vector3(aim.x - hand.x, 0.0, aim.z - hand.z)
	if flat.length() > max_flat:
		flat = flat.normalized() * max_flat
	return Vector3(hand.x + flat.x, 0.0, hand.z + flat.z)


func _footstep() -> void:
	Sfx.play("cyclops_step", global_position, -4.0)
	if player_distance() < 18.0:
		Game.shake(0.05)


func _check_enrage() -> void:
	var e := enraged()
	if e and not _was_enraged:
		_was_enraged = true
		visual.set_tint(ENRAGE_TINT)
		visual.flash(Color(1.0, 0.3, 0.2), 0.3)
		Sfx.play("cyclops_roar", global_position)
		Game.event("boss_enraged", {"boss": boss_id, "hp": hp})


## Horizontal position on the arena floor (y = 0).
func _floor_point(p: Vector3) -> Vector3:
	return Vector3(p.x, 0.0, p.z)


# ------------------------------------------------------------------ club blockers (feedback 2 re-fix, clipping 5:00)
func _make_club_blockers() -> void:
	if _club == null or Game.args.has("no-limb-blockers"):   # same harness A/B switch as the leg blockers
		return
	for i in CLUB_BLOCKS.size():
		var body := StaticBody3D.new()
		body.name = "ClubBlock_%d" % i
		body.collision_layer = 0            # off until the club stands still (_update_club_blockers)
		body.collision_mask = 0
		body.top_level = true
		var cs := CollisionShape3D.new()
		var cap := CapsuleShape3D.new()
		cap.radius = float(CLUB_BLOCKS[i][2])
		cap.height = cap.radius * 2.0 + 0.1
		cs.shape = cap
		body.add_child(cs)
		add_child(body)
		_club_blocks.append(body)


func _club_blockers_on() -> bool:
	if _club_released:
		return state == &"dead" and state_time > CLUB_DROP_DELAY + CLUB_DROP_TIME + 0.05
	return fighting and (state == &"stuck" or (state == &"pull_free" and state_time < 0.4))


func _update_club_blockers() -> void:
	if _club_blocks.is_empty() or _club == null or not is_instance_valid(_club) or not _club.is_inside_tree():
		return
	var on := _club_blockers_on()
	var g := _club.global_transform
	var sc := g.basis.get_scale()
	var rs := (sc.x + sc.z) * 0.5
	for i in _club_blocks.size():
		var body := _club_blocks[i]
		body.collision_layer = (1 << 2) if on else 0
		if not on:
			continue
		var r := float(CLUB_BLOCKS[i][2]) * rs
		var pa: Vector3 = g * (_club_axis * maxf(float(CLUB_BLOCKS[i][0]), CLUB_BLOCK_FREE + float(CLUB_BLOCKS[i][2])))
		var pb: Vector3 = g * (_club_axis * float(CLUB_BLOCKS[i][1]))
		var d := pb - pa
		var length := d.length()
		if length < 0.05:
			continue
		var y := d / length
		var x := y.cross(Vector3.UP if absf(y.y) < 0.95 else Vector3.RIGHT).normalized()
		var z := x.cross(y)
		var cap := (body.get_child(0) as CollisionShape3D).shape as CapsuleShape3D
		cap.radius = r
		cap.height = length + 2.0 * r
		body.global_transform = Transform3D(Basis(x, y, z), (pa + pb) * 0.5)


func _physics_process(delta: float) -> void:
	super(delta)
	_update_club_blockers()


# ------------------------------------------------------------------ per frame: club, weak point, trail, landing
func _process(delta: float) -> void:
	_update_club(delta)
	_update_sink(delta)
	_update_club_fade(delta)
	_update_weak_marker()
	_update_trail(delta)
	_update_landing(delta)
	_report_stuck_pose()


## Real model: after a slam impact, wait until the club head is seen in the earth (the skeleton pose lags the physics
## tick by a frame), then put the chunks, the inner dust and the crack exactly there.
func _update_landing(delta: float) -> void:
	if _land_wait < 0.0:
		return
	_land_wait += delta
	var head := _club_head()
	# down = in the earth and at rest: slower than 1.5 m/s of game time (a per-frame distance alone let a slow-motion
	# --speed=0.3 run accept the head while still settling: crack 0.2 m off)
	var down := head.y - global_position.y < 0.7 and head.distance_to(_land_prev) < maxf(1.5 * delta, 0.004)
	_land_prev = head
	if not down and _land_wait < 0.3:
		return
	# the crack goes where the club enters the earth: the tip as it sits once sunk (a rebound: the tip as it is)
	var p := (_floor_point(_club_tip()) if _land_rebound else _entry_point()) if down else _club_target
	Game.event("slam_land", {"club": _v(p), "center": _v(_slam_center), "err": snappedf(p.distance_to(_slam_center), 0.01),
		"seen": down, "rebound": _land_rebound})
	_club_target = p
	_land_wait = -1.0
	_land_fx(p, _land_rebound)


## Stand-in club: while stuck the module-owned holder turns so the club head is driven into the ground at
## _club_target (where the crack is); it eases back to the rest tilt during pull_free.
func _update_club(delta: float) -> void:
	if _club_holder == null or not _club_holder.is_inside_tree():
		return
	var aiming := state == &"stuck" and fighting
	_club_aim = move_toward(_club_aim, 1.0 if aiming else 0.0, delta / (0.12 if aiming else float(T["pull_free_time"])))
	var rest := Quaternion.from_euler(CLUB_REST_DEG * (PI / 180.0))
	if _club_aim <= 0.0:
		_club_holder.quaternion = rest
		return
	var parent := _club_holder.get_parent() as Node3D
	var head := _club_target + Vector3(0, -0.35, 0)       # a little below the surface: buried, not resting
	var dir := head - _club_holder.global_position
	if dir.length() < 0.1:
		return
	var local_dir := (parent.global_transform.basis.orthonormalized().inverse() * dir.normalized()).normalized()
	var aimed := Quaternion(_club_axis, local_dir)
	_club_holder.quaternion = rest.slerp(aimed, _club_aim)


## The club tip in world space (the grip socket when there is no club).
func _club_tip() -> Vector3:
	if _club == null or not _club.is_inside_tree():
		return visual.socket(&"hand_ur").global_position
	return _club.global_transform * (_club_axis * (CLUB_TIP if not visual.is_standin else CLUB_LENGTH))


## Floor point where the stuck club enters the earth: the tip of the fully sunk club (CLUB_SINK), on y = 0.
func _entry_point() -> Vector3:
	if _club_in_glb and _club != null and _club.is_inside_tree():
		var pg := (_club.get_parent() as Node3D).global_transform
		return _floor_point(pg * _sink_local(1.0) * (_club_axis * CLUB_TIP))
	return _floor_point(_club_tip())


## The GLB club's local transform pivoted about the grip by `s` (0..1) of the sink: the club turns down in its own
## vertical plane until the tip is CLUB_SINK lower. Only the club node moves (it has no animation track).
func _sink_local(s: float) -> Transform3D:
	var parent := _club.get_parent() as Node3D
	if s <= 0.0 or parent == null:
		return _club_rest
	var pg := parent.global_transform
	var g := pg * _club_rest
	var d := (g.basis * _club_axis).normalized()
	var a := d.cross(Vector3.UP)
	if a.length() < 0.05:
		return _club_rest
	var sa := clampf(-d.y, -1.0, 1.0)
	var phi := asin(clampf(sa + CLUB_SINK / CLUB_TIP, -1.0, 1.0)) - asin(sa)
	var b := Basis(a.normalized(), -phi * s) * g.basis
	return pg.affine_inverse() * Transform3D(b, g.origin)


## Real model: while stuck the club sinks (CLUB_SINK_IN s), and rises back over 0.2 s as he pulls it free (the
## pull_free clip lifts the club above the floor after ~0.2 s of game time).
func _update_sink(delta: float) -> void:
	if not _club_in_glb or _club_released or _club == null or not _club.is_inside_tree():
		return
	var want := 1.0 if (state == &"stuck" and fighting) else 0.0
	if want == 0.0 and _club_sink <= 0.0:
		return
	_club_sink = move_toward(_club_sink, want, delta / (CLUB_SINK_IN if want > 0.0 else 0.2))
	_club.transform = _sink_local(_club_sink)


## While stuck the club's near fade eases out to CLUB_STUCK_* and back (not after death: _release_club owns it then).
func _update_club_fade(delta: float) -> void:
	if _club == null or _club_released or not _club.is_inside_tree():
		return
	var want := 1.0 if (fighting and (state == &"stuck" or (state == &"pull_free" and state_time < 0.4))) else 0.0
	if is_equal_approx(_club_fade, want):
		return
	_club_fade = move_toward(_club_fade, want, delta / CLUB_STUCK_FADE_T)
	var u := smoothstep(0.0, 1.0, _club_fade)
	_set_near_fade(_club, lerpf(CLUB_NEAR_HIDE, CLUB_STUCK_HIDE, u), lerpf(CLUB_NEAR_FULL, CLUB_STUCK_FULL, u))
	# the near fade does not reach the shadow pass: a faded club would leave its full shadow on the bare floor
	_set_club_shadow(_club_fade <= 0.5)


## The club's own shadow on (its GLB setting) or off.
func _set_club_shadow(on: bool) -> void:
	if not _club is GeometryInstance3D:
		return
	var gi := _club as GeometryInstance3D
	if _club_shadow < 0:
		_club_shadow = gi.cast_shadow
	gi.cast_shadow = _club_shadow if on else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## The centre of the club head in world space.
func _club_head() -> Vector3:
	if _club == null or not _club.is_inside_tree():
		return visual.socket(&"hand_ur").global_position
	return _club.global_transform * (_club_axis * CLUB_HEAD_C)


## Stand-in only: follows socket forearm_ur, but keeps the centre within sword reach (the sword reaches y 2.9 m).
## When the forearm is too high and the club head is low (stuck), the glow slides down the forearm -> club-head line
## to WEAK_LINE_Y, so it sits on the arm or the club, never in mid-air; otherwise it is clamped straight down.
func _update_weak_marker() -> void:
	if _wp_marker == null or visual == null or not _wp_marker.is_inside_tree():
		return
	var src := visual.socket(&"forearm_ur").global_position
	var floor_y := global_position.y
	var raw_y := src.y - floor_y
	var pos := Vector3(src.x, floor_y + clampf(raw_y, WEAK_Y_RANGE.x, WEAK_Y_RANGE.y), src.z)
	var mode := "clamp"
	if raw_y > WEAK_Y_RANGE.y:
		var tip := _club_tip()
		var line_y := _k("weak_line_y", WEAK_LINE_Y)
		if tip.y - floor_y < line_y and src.y - tip.y > 0.1:
			pos = src.lerp(tip, (src.y - (floor_y + line_y)) / (src.y - tip.y))
			mode = "club_line"
	if state == &"stuck" and not _clamp_reported and absf(pos.y - src.y) > 0.6 and state_time > 0.5:
		_clamp_reported = true
		Game.event("forearm_clamped", {"raw_y": snappedf(raw_y, 0.01), "used_y": snappedf(pos.y - floor_y, 0.01), "mode": mode})
	_wp_marker.global_position = pos


## Once per stuck window: where the hand, club tip, crack and weak point really are (boss-local), and whether the
## forearm is inside the sword's reach (real model: no clamp).
func _report_stuck_pose() -> void:
	if state != &"stuck" or _pose_reported or state_time < 0.6 or not weak_points.has(&"forearm"):
		return
	_pose_reported = true
	var inv := global_transform.affine_inverse()
	var wp: WeakPoint = weak_points[&"forearm"]
	var wy := wp.global_position.y - global_position.y
	Game.event("cyclops_stuck_pose", {"hand_local": _v(inv * visual.socket(&"hand_ur").global_position),
		"tip_local": _v(inv * _club_tip()), "crack_local": _v(inv * _club_target), "wp_local": _v(inv * wp.global_position),
		"wp_y": snappedf(wy, 0.01), "in_reach": wy <= 2.9 + wp.radius * 0.5, "clamped": _wp_marker != null})


func _v(p: Vector3) -> String:
	return "(%.2f,%.2f,%.2f)" % [p.x, p.y, p.z]


# ------------------------------------------------------------------ VFX (built-in nodes only)
## Real model: a ribbon that follows the real club head through the low part of the swing (tip to 3 m down the
## shaft), dust kicked up wherever the head skims the ground, fading 0.45 s after the swing.
func _start_trail() -> void:
	_trail_pts.clear()
	_trail_dust_t = 0.0
	if is_instance_valid(_trail):
		_trail.queue_free()
	_trail = null
	if visual.is_standin:
		return
	_trail = MeshInstance3D.new()
	_trail.mesh = ImmediateMesh.new()
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = true
	m.albedo_color = Color(1, 1, 1, 0.95)
	_trail.material_override = m
	_trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(_trail)
	_trail.global_transform = Transform3D.IDENTITY


func _update_trail(delta: float) -> void:
	if not is_instance_valid(_trail):
		return
	var u := state_time * _sweep_speed if state == &"sweep" else INF
	if u >= SWEEP_TRAIL_CLIP.x and u <= SWEEP_TRAIL_CLIP.y:
		var tip := _club_tip()
		var grip := _club.global_transform * Vector3.ZERO if _club != null else tip
		_trail_pts.append([tip, tip.lerp(grip, 3.0 / CLUB_TIP)])
		_trail_dust_t -= delta
		if tip.y - global_position.y < 1.3 and _trail_dust_t <= 0.0:
			_trail_dust_t = 0.05
			Fx.dust(arena, _floor_point(tip), 1.1)
		_draw_trail()
	elif u > SWEEP_TRAIL_CLIP.y or state != &"sweep":
		var m := _trail.material_override as StandardMaterial3D
		var tr := _trail
		_trail = null
		if _trail_pts.size() < 2:
			tr.queue_free()
			return
		var tw := tr.create_tween()
		tw.tween_property(m, "albedo_color:a", 0.0, 0.45)
		tw.tween_callback(tr.queue_free)


## Rebuilds the ribbon: alpha grows along the swing (newest brightest), 0 at the inner edge.
func _draw_trail() -> void:
	var im := _trail.mesh as ImmediateMesh
	im.clear_surfaces()
	var n := _trail_pts.size()
	if n < 2:
		return
	im.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for i in n:
		var a := pow(float(i + 1) / float(n), 0.8)
		var pr: Array = _trail_pts[i]
		im.surface_set_color(Color(1.0, 0.97, 0.9, a))
		im.surface_add_vertex(pr[0])
		im.surface_set_color(Color(1.0, 0.97, 0.9, 0.0))
		im.surface_add_vertex(pr[1])
	im.surface_end()


## Stand-in: the club-head trail as a static curved ribbon at the cone's reach, plus a dust line on the ground.
func _sweep_fx() -> void:
	var half := deg_to_rad(_sweep_half())
	var reach := _sweep_reach()
	var mi := MeshInstance3D.new()
	mi.mesh = _ribbon_mesh(reach * 0.82, half, 0.5, 1.5, 2.6)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = true
	m.albedo_color = Color(1, 1, 1, 0.85)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(mi)
	mi.global_position = global_position
	mi.global_rotation = Vector3(0, atan2(_sweep_dir.x, _sweep_dir.z), 0)
	var tw := mi.create_tween()
	tw.tween_property(m, "albedo_color:a", 0.0, 0.35)
	tw.tween_callback(mi.queue_free)
	for i in 5:
		var a := lerpf(-half, half, float(i) / 4.0)
		var p := global_position + _sweep_dir.rotated(Vector3.UP, a) * reach * 0.75
		Fx.dust(arena, _floor_point(p), 1.4)


## Curved ribbon at radius r from +half (start, his left) to -half (end, his right); alpha 0 at the bottom (y0) and
## top (y2) edges, peak at y1, growing along the swing.
func _ribbon_mesh(r: float, half: float, y0: float, y1: float, y2: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 28
	for i in n:
		var u0 := float(i) / n
		var u1 := float(i + 1) / n
		var a0 := lerpf(half, -half, u0)
		var a1 := lerpf(half, -half, u1)
		var d0 := Vector3(sin(a0) * r, 0, cos(a0) * r)
		var d1 := Vector3(sin(a1) * r, 0, cos(a1) * r)
		var c0 := Color(1.0, 0.97, 0.9, pow(u0, 1.4))
		var c1 := Color(1.0, 0.97, 0.9, pow(u1, 1.4))
		var z := Color(1.0, 0.97, 0.9, 0.0)
		for band in [[y0, z, y1, true], [y1, z, y2, false]]:
			var ya: float = band[0]
			var yb: float = band[2]
			var low_is_peak := not bool(band[3])
			var ca0 := c0 if low_is_peak else z
			var ca1 := c1 if low_is_peak else z
			var cb0 := z if low_is_peak else c0
			var cb1 := z if low_is_peak else c1
			var v := [[d0 + Vector3(0, ya, 0), ca0], [d1 + Vector3(0, ya, 0), ca1], [d1 + Vector3(0, yb, 0), cb1],
				[d0 + Vector3(0, ya, 0), ca0], [d1 + Vector3(0, yb, 0), cb1], [d0 + Vector3(0, yb, 0), cb0]]
			for q in v:
				st.set_color(q[1])
				st.add_vertex(q[0])
	return st.commit()


## Slam, at the impact: dust ring + expanding shockwave over the hit circle (`center`).
func _ring_fx(center: Vector3, rebound := false) -> void:
	var r: float = T["slam_radius"]
	Fx.dust(arena, center, r * (0.8 if rebound else 1.2), Color(0.72, 0.58, 0.42, 0.85))
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.85
	tm.outer_radius = 1.0
	tm.rings = 48
	tm.ring_segments = 6
	ring.mesh = tm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(1.0, 0.92, 0.75, 0.8)
	ring.material_override = m
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(ring)
	ring.global_position = center + Vector3(0, 0.15, 0)
	ring.scale = Vector3(r * 0.5, 0.4, r * 0.5)
	var tw := ring.create_tween().set_parallel(true)
	tw.tween_property(ring, "scale", Vector3(r * 2.6, 0.15, r * 2.6), 0.45).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.45)
	tw.chain().tween_callback(ring.queue_free)


## Slam, where the club head went in (`club_at`): inner dust burst, flying earth chunks and the crack decal (stays
## while stuck). A rebound gets only a small puff.
func _land_fx(club_at: Vector3, rebound := false) -> void:
	if rebound:
		Fx.dust(arena, club_at, 1.2, Color(0.62, 0.48, 0.34, 0.9))
		return
	Fx.dust(arena, club_at, float(T["slam_radius"]) * 0.6, Color(0.62, 0.48, 0.34, 0.9))
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 22
	p.lifetime = 1.1
	p.explosiveness = 1.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 0.8
	p.direction = Vector3.UP
	p.spread = 55.0
	p.initial_velocity_min = 5.0
	p.initial_velocity_max = 10.0
	p.gravity = Vector3(0, -22.0, 0)
	p.angular_velocity_min = -360.0
	p.angular_velocity_max = 360.0
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.3
	var bm := BoxMesh.new()
	bm.size = Vector3(0.35, 0.3, 0.4)
	var cm := StandardMaterial3D.new()
	cm.albedo_color = Color(0.45, 0.33, 0.22)
	bm.material = cm
	p.mesh = bm
	arena.add_child(p)
	p.global_position = club_at + Vector3(0, 0.3, 0)
	p.emitting = true
	p.finished.connect(p.queue_free)
	_make_crack(club_at)


func _make_crack(center: Vector3) -> void:
	_clear_crack()
	var mi := MeshInstance3D.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 9
	for i in n:
		var a := TAU * float(i) / n + Game.rng.randf_range(-0.2, 0.2)
		var w := 0.16
		var l := Game.rng.randf_range(1.6, 3.2)
		var dir := Vector3(sin(a), 0, cos(a))
		var side := dir.cross(Vector3.UP) * w
		for v in [Vector3.ZERO + side, dir * l, Vector3.ZERO - side]:
			st.set_normal(Vector3.UP)
			st.add_vertex(v)
	# dark pit in the middle
	for i in 12:
		var a0 := TAU * float(i) / 12.0
		var a1 := TAU * float(i + 1) / 12.0
		for v in [Vector3.ZERO, Vector3(sin(a1), 0, cos(a1)) * 0.9, Vector3(sin(a0), 0, cos(a0)) * 0.9]:
			st.set_normal(Vector3.UP)
			st.add_vertex(v)
	mi.mesh = st.commit()
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = Color(0.22, 0.15, 0.10)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(mi)
	mi.global_position = center + Vector3(0, 0.03, 0)
	if not visual.is_standin:
		_add_crack_rim(mi)
	_crack = mi


## Real model: a raised lip of thrown-up earth around the club's entry point plus a few clods, so the club reads as
## driven into the ground rather than lying on it (integration check 2). Children of the crack: they fade with it.
func _add_crack_rim(crack: Node3D) -> void:
	var rng := RandomNumberGenerator.new()          # own generator: Game.rng (attack pattern) is not touched
	rng.seed = hash(Vector2i(roundi(crack.global_position.x * 10.0), roundi(crack.global_position.z * 10.0)))
	var earth := CharacterVisual.make_toon(Color(0.50, 0.36, 0.24))
	var rim := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.55
	tm.outer_radius = 1.15
	tm.rings = 24
	tm.ring_segments = 8
	rim.mesh = tm
	rim.material_override = earth
	rim.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	crack.add_child(rim)
	rim.position = Vector3(0, -0.01, 0)
	rim.scale = Vector3(1.0, 0.6, 1.0)          # lip ~0.17 m above the floor
	for i in 6:
		var a := TAU * float(i) / 6.0 + rng.randf_range(-0.3, 0.3)
		var clod := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.32, 0.2, 0.26) * rng.randf_range(0.7, 1.3)
		clod.mesh = bm
		clod.material_override = earth
		clod.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		crack.add_child(clod)
		clod.position = Vector3(sin(a), 0.0, cos(a)) * rng.randf_range(1.2, 1.7) + Vector3(0, 0.05, 0)
		clod.rotation = Vector3(rng.randf_range(-0.4, 0.4), rng.randf(), rng.randf_range(-0.4, 0.4))


func _clear_crack() -> void:
	if is_instance_valid(_crack):
		var c := _crack
		var tw := c.create_tween()
		tw.tween_property(c, "scale", Vector3(0.01, 1, 0.01), 0.4)
		tw.tween_callback(c.queue_free)
	_crack = null


## Dust where the falling body meets the ground. Real death clip (backward fall): knees, club, then the back.
func _death_dust() -> void:
	if visual.is_standin:
		_death_puff(1.3, _floor_point(global_position - global_transform.basis.x.normalized() * 4.0), 5.0, 0.8, true)
		_death_puff(1.3, _floor_point(global_position), 3.0, 0.0, false)
		return
	_death_puff(DEATH_KNEES, _floor_point(global_position + forward() * 0.6), 2.4, 0.25, false)
	_death_puff(DEATH_BODY_T, _floor_point(global_transform * DEATH_BODY), 5.0, 0.8, true)


## Real model: the dying giant lets go of the club. It leaves the hand (arena child, same world transform) and topples
## about its tip onto the floor, the grip end falling to his right-back or left-back, whichever lies farther from the
## camera, so it never swings through the view with the falling body (play-test shots cyc_win 0061/0063).
func _release_club() -> void:
	if visual.is_standin or _club == null or not _club.is_inside_tree() or _club_released:
		return
	_club_released = true
	_set_club_shadow(true)              # killed while stuck: the stuck fade had switched its shadow off
	var from := _club.global_transform
	_club.reparent(arena, true)
	_club.global_transform = from
	var tip := _floor_point(_club_tip())
	var cam := get_viewport().get_camera_3d()
	var cam_pos := cam.global_position if cam != null else player.global_position
	var best := Transform3D.IDENTITY
	var best_d := -1.0
	for sx in [-1.0, 1.0]:                       # -1 = his right (where the club is), +1 = his left
		var dir := global_transform.basis * Vector3(sx, 0.0, -0.55)
		dir.y = 0.0
		dir = dir.normalized()
		var head_c := tip + dir * (CLUB_TIP - CLUB_HEAD_C) + Vector3(0, 0.6, 0)
		var grip := head_c + dir * CLUB_HEAD_C
		grip.y = 0.2
		# the stuck tip sits beside the camera: the falling club slides away from it along the camera -> boss line
		# (both ends at least CLUB_DROP_CAM_MIN from the camera), but stays inside the ring
		var push_dir := _floor_point(global_position - cam_pos)
		push_dir = push_dir.normalized() if push_dir.length() > 0.1 else forward() * -1.0
		for _i in 6:
			var near := minf(_floor_point(head_c - cam_pos).length(), _floor_point(grip - cam_pos).length())
			if near >= CLUB_DROP_CAM_MIN - 0.01:
				break
			head_c += push_dir * (CLUB_DROP_CAM_MIN - near)
			grip += push_dir * (CLUB_DROP_CAM_MIN - near)
		var ctr := _floor_point(arena.global_position)
		for p in [head_c, grip]:
			var excess := _floor_point(p).distance_to(ctr) - (arena.radius - 1.5)
			if excess > 0.0:
				var inward := (ctr - _floor_point(p)).normalized() * excess
				head_c += inward
				grip += inward
		var d := minf(_floor_point(grip).distance_to(_floor_point(cam_pos)), _floor_point(head_c).distance_to(_floor_point(cam_pos))) \
			+ (1.0 if sx < 0.0 else 0.0)   # prefer his right (the club hand)
		if d > best_d:
			best_d = d
			best = _lying_transform(grip, head_c, from.basis.get_scale())
	_set_near_fade(_club, CLUB_DROP_HIDE, CLUB_DROP_FULL)
	var tw := _club.create_tween()
	if CLUB_DROP_DELAY > 0.0:
		tw.tween_interval(CLUB_DROP_DELAY)
	tw.tween_method(func(u: float) -> void:
		if is_instance_valid(_club):
			_club.global_transform = from.interpolate_with(best, u), 0.0, 1.0, CLUB_DROP_TIME) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		if not is_instance_valid(self) or arena == null or not is_instance_valid(arena):
			return
		var g := best.origin
		var h := best * (_club_axis * CLUB_HEAD_C)
		Fx.dust(arena, _floor_point(h), 1.8, Color(0.72, 0.6, 0.45, 0.9))
		Fx.dust(arena, _floor_point(g), 1.0, Color(0.72, 0.6, 0.45, 0.9))
		Sfx.play("cyclops_slam", h, -3.0, 0.7)
		Game.shake(0.3)
		Game.event("cyclops_club_dropped", {"head": _v(h), "grip": _v(g),
			"cam_dist": snappedf(_floor_point(h).distance_to(_floor_point(cam_pos)), 0.01)}))
	tw.tween_method(func(u: float) -> void:
		if is_instance_valid(self) and is_instance_valid(_club):
			_set_near_fade(_club, lerpf(CLUB_DROP_HIDE, CLUB_NEAR_HIDE, u), lerpf(CLUB_DROP_FULL, CLUB_NEAR_FULL, u)),
		0.0, 1.0, CLUB_DROP_FADE_BACK)


## World transform of a club whose grip (origin) is at `grip` and whose axis points at `head`, keeping its scale.
func _lying_transform(grip: Vector3, head: Vector3, scale_v: Vector3) -> Transform3D:
	var y := (head - grip).normalized() * (1.0 if _club_axis.y >= 0.0 else -1.0)
	var x := Vector3.UP.cross(y)
	x = x.normalized() if x.length() > 0.01 else Vector3.RIGHT
	var z := x.cross(y).normalized()
	var b := Basis(x * scale_v.x, y * scale_v.y, z * scale_v.z)
	return Transform3D(b, grip)


func _death_puff(after: float, at: Vector3, r: float, shake: float, thud: bool) -> void:
	var t := get_tree().create_timer(after, false)
	t.timeout.connect(func() -> void:
		if not is_instance_valid(self) or arena == null or not is_instance_valid(arena):
			return
		Fx.dust(arena, at, r, Color(0.72, 0.6, 0.45, 0.9))
		if thud:
			Sfx.play("cyclops_slam", at, -3.0, 0.7)
		if shake > 0.0:
			Game.shake(shake))


# ------------------------------------------------------------------ camera + bot
## Lock point on his vertical axis (so the chase camera does not swing when the head dips forward in the slam and
## stuck poses), at upper-chest height (head socket height blended 40 % toward 60 % of the body height).
func get_lock_point() -> Vector3:
	if visual != null and not visual.is_standin:
		var hy := visual.socket(&"head").global_position.y
		return Vector3(global_position.x, lerpf(hy, global_position.y + visual.height * 0.6, 0.4), global_position.z)
	return global_position + Vector3.UP * float(T["height"]) * 0.72


## Body top points (rest pose, BossBase) plus, during the slam windup only, the raised club (tip and head top, up to
## 12.2 m), so the lock camera grows its arm (within CAM_LOCK_MAX_EXTRA) to keep the raised club in frame as in
## key_cyclops.png. Not in approach/sweep: integrate_player asks that props stay out of the top in general.
func frame_top_points() -> PackedVector3Array:
	var out := super.frame_top_points()
	if state == &"slam" and not _impact_done and _club_in_glb and _club != null and _club.is_inside_tree():
		out.append(_club_tip())
		out.append(_club_head() + Vector3.UP * 0.55)
	return out


## The same raised-club points for the real model (integrate2_cyclops): the lock camera frames a real visual by its live
## BODY top points (CharacterVisual.live_top_points, props such as the club left out), so frame_top_points() above is
## only read for the stand-in. PlayerCamera adds these must-fit points during the slam windup; the hero's feet and the
## per-boss cut_inside rule still win (the club top is cut when the hero stands close).
func cam_fit_points() -> PackedVector3Array:
	var out := PackedVector3Array()
	if visual == null or visual.is_standin:
		return out
	if state == &"slam" and not _impact_done and _club_in_glb and _club != null and _club.is_inside_tree():
		out.append(_club_tip())
		out.append(_club_head() + Vector3.UP * 0.55)
	return out


## Block sweeps facing him, roll sideways out of the slam circle as the club falls, run to the stuck forearm (after a
## human reaction delay) and strike twice, back off while he pulls free.
func bot_advice() -> Dictionary:
	var adv := {"move_to": player.global_position, "face": global_position, "roll": false, "block": false, "attack": false}
	var to_player := player.global_position - global_position
	to_player.y = 0.0
	var away := to_player.normalized() if to_player.length() > 0.1 else Vector3.BACK
	match state:
		&"sweep":
			var left := _impact_at - state_time
			adv["block"] = player_distance() < _sweep_reach() + 1.5 and left > -0.25
		&"slam":
			var left2 := _impact_at - state_time
			var side := away.cross(Vector3.UP)
			var inside := player.global_position.distance_to(_slam_center) < float(T["slam_radius"]) + 1.2
			if _impact_done:
				adv["move_to"] = player.global_position     # rebound of a double slam: wait for the next circle
			elif left2 > 0.42:
				# harness `--cyclops-strafe`: circle sideways while the shadow tracks (tests the club steering)
				var strafe := Game.harness and Game.args.has("cyclops-strafe")
				adv["move_to"] = player.global_position + side * 6.0 if strafe else player.global_position
			else:
				adv["move_to"] = player.global_position + side * 6.0
				adv["roll"] = left2 < 0.33 and left2 > 0.04 and inside
		&"stuck":
			if state_time < REACT_DELAY:
				adv["move_to"] = player.global_position
			elif is_exposed(&"forearm"):
				var wp: WeakPoint = weak_points[&"forearm"]
				var w := wp.global_position
				var radial := w - global_position
				radial.y = 0.0
				radial = radial.normalized() if radial.length() > 0.1 else away
				var stand := Vector3(w.x, player.global_position.y, w.z) + radial * 1.1
				adv["move_to"] = stand
				var d := player.global_position - Vector3(w.x, player.global_position.y, w.z)
				adv["attack"] = d.length() < Tuning.SWORD_REACH + wp.radius * 0.6
			else:
				adv["move_to"] = global_position + away * 9.0
		&"pull_free":
			adv["move_to"] = global_position + away * 9.0
		_:
			adv["move_to"] = global_position + away * 6.0
	return adv
