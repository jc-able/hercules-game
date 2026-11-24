class_name PlayerCamera
extends Node3D
## Chase camera (SPEC §5): a SpringArm3D right behind and slightly above Hercules, FOV 70. Locked on: it sits on the
## boss->player line behind the hero and tilts up so the boss's upper body (get_lock_point()) stays in frame.
## Towering bosses (SPEC §10): the hero's feet always stay above the HUD boss bar, the boss's top (real model bounds)
## stays in frame when it fits (live: the top vertices ride their bones), and the arm grows up to max_extra_for(boss)
## (Tuning.CAM_LOCK_MAX_EXTRA, per boss in CAM_LOCK_MAX_EXTRA_BY_BOSS) so it does (see "lock framing").
## Free: mouse / right-stick orbit with clamped pitch, easing back behind the hero while running.
## Static bodies in group "camera_ignore" (invisible arena walls) never push the camera in.

const PIVOT_HEIGHT := 1.6

var player: Player
var yaw := 0.0                 ## radians; the camera looks along (-sin yaw, 0, -cos yaw)
var pitch := deg_to_rad(-12.0) ## radians; negative = above, looking down
var cam: Camera3D
var arm: SpringArm3D
var _end: Node3D
var _shake := 0.0
var _idle_input := 10.0
var _look := Vector3.ZERO
var _cam_pos := Vector3.ZERO
var _excluded := {}
var _exclude_check := 0.0
var _snap := true
var _arm_len := Tuning.CAM_DISTANCE   ## current arm length (grows for towering bosses while locked)
var _hud: Node = null
var _tops := PackedVector3Array()     # the locked boss's top points this frame (BossBase.frame_top_points)
var _debug_t := 0.0                   # harness `--cam-debug`: one cam_frame event per second while locked
var _death_k := 0.0                   # 0..1 eased in while the hero lies dead (camera raised, aim lowered onto him)


func _ready() -> void:
	name = "PlayerCamera"
	top_level = true
	arm = SpringArm3D.new()
	arm.spring_length = Tuning.CAM_DISTANCE
	arm.collision_mask = 1
	arm.margin = 0.25
	var sh := SphereShape3D.new()
	sh.radius = 0.25
	arm.shape = sh
	add_child(arm)
	_end = Node3D.new()
	arm.add_child(_end)
	cam = Camera3D.new()
	cam.top_level = true
	cam.fov = Tuning.CAM_FOV
	cam.near = 0.1
	cam.far = 4000.0
	add_child(cam)
	cam.current = true
	if player != null:
		arm.add_excluded_object(player.get_rid())
		yaw = atan2(-player.facing.x, -player.facing.z)
	Game.camera_shake.connect(shake)


## Adds camera shake (0..1); decays quickly.
func shake(amount: float) -> void:
	_shake = clampf(maxf(_shake, amount), 0.0, 1.0)


## Puts the camera straight behind the hero at once (scene start, respawn).
func snap_behind() -> void:
	if player != null:
		yaw = atan2(-player.facing.x, -player.facing.z)
	_snap = true


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if player != null and player.locked:
			return
		yaw -= deg_to_rad(e.relative.x * Tuning.CAM_MOUSE_SENS)
		pitch = clampf(pitch - deg_to_rad(e.relative.y * Tuning.CAM_MOUSE_SENS), deg_to_rad(Tuning.CAM_FREE_PITCH_MIN), deg_to_rad(Tuning.CAM_FREE_PITCH_MAX))
		_idle_input = 0.0


func _process(delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	_exclude_walls(delta)
	var pivot := player.global_position + Vector3(0, PIVOT_HEIGHT, 0)
	global_position = pivot
	var lp = player.lock_point()
	var look_target: Vector3
	var stick := Controls.get_look_stick()
	if lp != null:
		var to: Vector3 = lp - player.global_position
		to.y = 0.0
		var want_yaw := atan2(-to.x, -to.z) if to.length() > 0.3 else yaw
		yaw = lerp_angle(yaw, want_yaw, 1.0 - exp(-7.0 * delta)) if not _snap else want_yaw
		_tops = _boss_tops(player.lock_target)
		var want_len := _lock_distance(lp)
		_arm_len = want_len if _snap else lerpf(_arm_len, want_len, 1.0 - exp(-3.5 * delta))
		# same camera height (CAM_LOCK_HEIGHT above the feet: low, chest height) at any arm length
		var want_pitch := -asin(clampf((_lock_height() - PIVOT_HEIGHT) / _arm_len, -0.9, 0.9))
		pitch = want_pitch if _snap else lerpf(pitch, want_pitch, 1.0 - exp(-6.0 * delta))
		look_target = _locked_look(pivot, lp)
	else:
		_arm_len = lerpf(_arm_len, Tuning.CAM_DISTANCE, 1.0 - exp(-2.5 * delta))
		if stick.length() > 0.0:
			yaw -= deg_to_rad(stick.x * Tuning.CAM_PAD_SPEED) * delta
			pitch = clampf(pitch - deg_to_rad(stick.y * Tuning.CAM_PAD_SPEED * 0.6) * delta, deg_to_rad(Tuning.CAM_FREE_PITCH_MIN), deg_to_rad(Tuning.CAM_FREE_PITCH_MAX))
			_idle_input = 0.0
		_idle_input += delta
		_recenter(delta)
		var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
		look_target = pivot + fwd * 2.0 + Vector3(0, -0.2, 0)
	arm.spring_length = _arm_len
	arm.rotation = Vector3(pitch, yaw, 0)
	arm.force_update_transform()
	var want_pos := _end.global_position
	want_pos.y = maxf(want_pos.y, player.global_position.y + 0.4)
	# death hold: raise the camera (Tuning.CAM_DEATH_RAISE) and lower the aim onto the fallen hero, so nothing low
	# near the camera (an arena curb behind a hero knocked to the rim) or the HUD covers him
	var dead := player.state == &"dead"
	_death_k = move_toward(_death_k, 1.0 if dead else 0.0, delta / Tuning.CAM_DEATH_EASE)
	var dk := smoothstep(0.0, 1.0, _death_k)
	want_pos.y += Tuning.CAM_DEATH_RAISE * dk
	if _snap:
		_cam_pos = want_pos
	else:
		_cam_pos = _cam_pos.lerp(want_pos, 1.0 - exp(-14.0 * delta))
	if lp != null:
		look_target = _frame_locked(_cam_pos, look_target, lp)
		if dk > 0.0:
			look_target = look_target.lerp(player.global_position + Vector3(0, 0.3, 0), Tuning.CAM_DEATH_AIM * dk)
	if _snap:
		_look = look_target
		_snap = false
	else:
		_look = _look.lerp(look_target, 1.0 - exp(-9.0 * delta))
	if lp != null:
		_look = _keep_feet_in_view(_cam_pos, _look, lp)
		if Game.harness and Game.args.has("cam-debug"):
			_debug_t -= delta
			if _debug_t <= 0.0:
				_debug_t = 1.0
				var top_y := -INF
				for tp in _tops:
					top_y = maxf(top_y, tp.y)
				var lim := _axis_limits(_cam_pos)
				Game.event("cam_frame", {"arm": snappedf(_arm_len, 0.01), "cam_d": snappedf(_cam_pos.distance_to(player.global_position), 0.01),
					"top": snappedf(top_y, 0.01), "top_pts": _tops.size(), "lp_flat": snappedf(Vector2(lp.x - player.global_position.x, lp.z - player.global_position.z).length(), 0.01),
					"lo": snappedf(rad_to_deg(lim.x), 0.1), "hi": snappedf(rad_to_deg(lim.y), 0.1), "axis": snappedf(rad_to_deg(_elev(_cam_pos, _look)), 0.1),
					"band": snappedf(_bottom_band(), 0.001)})
	var shake_off := Vector3.ZERO
	if _shake > 0.0:
		var s := _shake * _shake * 0.35
		shake_off = Vector3(randf_range(-s, s), randf_range(-s, s), randf_range(-s, s))
		_shake = maxf(0.0, _shake - delta * 2.2)
	cam.global_position = _cam_pos + shake_off
	if cam.global_position.distance_to(_look) > 0.05:
		cam.look_at(_look + shake_off * 0.5, Vector3.UP)


## Aim point while locked: between the hero and the boss's lock point (the framing limits come after, see
## _frame_locked).
func _locked_look(pivot: Vector3, lp: Vector3) -> Vector3:
	var flat := Vector2(lp.x - pivot.x, lp.z - pivot.z).length()
	var w := clampf(0.42 - flat * 0.004, 0.25, 0.45)
	return pivot.lerp(lp, w)


# ------------------------------------------------------------------ lock framing for towering bosses (SPEC §10)
# Angles are elevations (radians) of the view axis seen from the camera. Two limits:
#  - highest: the hero's feet stay above the HUD's boss band (+ CAM_LOCK_FEET_MARGIN), always;
#  - lowest: the boss's top (BossBase.frame_top_points, real model bounds) stays below CAM_LOCK_TOP_FRAC of the screen.
# When both cannot hold at CAM_DISTANCE the arm grows (up to CAM_LOCK_MAX_EXTRA, same camera height) until they do;
# past that the feet win. The camera stays on the boss->hero line right behind the hero throughout.

## Arm length that fits the boss's top and the hero's feet, from CAM_DISTANCE up to CAM_DISTANCE + CAM_LOCK_MAX_EXTRA.
func _lock_distance(lp: Vector3) -> float:
	var boss := player.lock_target
	var feet := player.global_position
	var back := Vector3(feet.x - lp.x, 0.0, feet.z - lp.z)
	var base := _lock_base()
	if boss == null or not is_instance_valid(boss) or back.length() < 0.3:
		return base
	var flat := back.length()
	back = back.normalized()
	var h := _lock_height()
	var extra := max_extra_for(boss)
	var cut := float(_lock_cfg().get("cut_inside", 0.0))
	if cut > 0.0:
		# close to the boss the arm stays short (hero big, the top may be cut); growth fades in up to cut_inside
		extra *= clampf((flat - (cut - Tuning.CAM_LOCK_CUT_RAMP)) / Tuning.CAM_LOCK_CUT_RAMP, 0.0, 1.0)
	var d := base
	var max_d := base + extra
	while d < max_d:
		var c := feet + back * sqrt(maxf(d * d - pow(h - PIVOT_HEIGHT, 2.0), 1.0)) + Vector3.UP * h
		var lim := _axis_limits(c)
		if lim.x <= lim.y:
			break
		d += 0.25
	return minf(d, max_d)


## Tuning.CAM_LOCK_BY_BOSS entry of the locked boss ({} when none).
func _lock_cfg() -> Dictionary:
	if player == null:
		return {}
	var b := player.lock_target
	if b == null or not is_instance_valid(b):
		return {}
	return Tuning.CAM_LOCK_BY_BOSS.get(String(b.boss_id), {})


## Lock arm length before any growth (per boss, else CAM_LOCK_DISTANCE).
func _lock_base() -> float:
	return float(_lock_cfg().get("distance", Tuning.CAM_LOCK_DISTANCE))


## Lock camera height above the hero's feet (per boss, else CAM_LOCK_HEIGHT).
func _lock_height() -> float:
	return float(_lock_cfg().get("height", Tuning.CAM_LOCK_HEIGHT))


## How far the lock arm may grow past CAM_LOCK_DISTANCE for this boss: the boss's own `cam_max_extra()` when it has
## one, else Tuning.CAM_LOCK_MAX_EXTRA_BY_BOSS[boss_id], else Tuning.CAM_LOCK_MAX_EXTRA. The 14 m hydra needs 2.5 m so
## a rearing centre neck stays in frame from the bot's 7.5 m guard spot (key_hydra.png shows the whole beast).
static func max_extra_for(boss: Node) -> float:
	if boss == null or not is_instance_valid(boss):
		return Tuning.CAM_LOCK_MAX_EXTRA
	if boss.has_method("cam_max_extra"):
		return maxf(float(boss.call("cam_max_extra")), 0.0)
	var id := String(boss.get("boss_id")) if boss.get("boss_id") != null else ""
	return float(Tuning.CAM_LOCK_MAX_EXTRA_BY_BOSS.get(id, Tuning.CAM_LOCK_MAX_EXTRA))


## The locked boss's top points as it stands now (CharacterVisual.live_top_points: rest top vertices carried by their
## bones), so a neck rearing above its rest height counts; bosses without a real visual use BossBase.frame_top_points().
func _boss_tops(boss: BossBase) -> PackedVector3Array:
	var out := PackedVector3Array()
	var v = boss.get("visual")
	if v != null and is_instance_valid(v) and v.has_method("live_top_points") and not v.is_standin:
		out = v.live_top_points()
	if out.is_empty():
		out = boss.frame_top_points()
	# must-fit hook (final check, medusa fixer 3 request 1): extra world points a boss wants in frame (Medusa: her eyes
	# during the gaze). Bosses without the method are unaffected.
	if boss.has_method("cam_fit_points"):
		out.append_array(boss.call("cam_fit_points"))
	return out


## Moves the aim point up or down (same horizontal spot). Reference framing (key_cyclops.png): the hero stands in the
## lower centre with his feet just above the boss bar and the boss towers over him, so the view axis takes the highest
## elevation the feet allow (the boss's top fits as long as `lowest <= highest`, see _lock_distance).
func _frame_locked(cam_pos: Vector3, target: Vector3, _lp: Vector3) -> Vector3:
	var boss := player.lock_target
	if boss == null or not is_instance_valid(boss):
		return target
	var lim := _axis_limits(cam_pos)
	return _point_at_elev(cam_pos, target, lim.y)


## After smoothing: never let the aim drift above the feet limit (the hero's feet stay above the boss bar).
func _keep_feet_in_view(cam_pos: Vector3, look: Vector3, _lp: Vector3) -> Vector3:
	var hi := _axis_limits(cam_pos).y
	if _elev(cam_pos, look) > hi:
		return _point_at_elev(cam_pos, look, hi)
	return look


## [lowest, highest] view-axis elevation from `cam_pos` (lowest keeps every boss top point inside the top of the frame,
## highest keeps the hero's feet above the boss band). lowest > highest means both cannot hold.
func _axis_limits(cam_pos: Vector3) -> Vector2:
	var tan_h := tan(deg_to_rad(cam.fov * 0.5))      # Camera3D keeps the height: fov is vertical
	var feet_frac := maxf(_bottom_band(), 0.03) + Tuning.CAM_LOCK_FEET_MARGIN
	var below_feet := -atan((2.0 * feet_frac - 1.0) * tan_h)
	var below_top := atan((2.0 * Tuning.CAM_LOCK_TOP_FRAC - 1.0) * tan_h)
	var top_elev := -PI * 0.5
	for tp in _tops:
		top_elev = maxf(top_elev, _elev(cam_pos, tp))
	return Vector2(top_elev - below_top, _elev(cam_pos, player.global_position) + below_feet)


func _bottom_band() -> float:
	if _hud == null or not is_instance_valid(_hud):
		_hud = get_tree().get_first_node_in_group("hud")
	if _hud != null and _hud.has_method("bottom_band_fraction"):
		return float(_hud.call("bottom_band_fraction"))
	return 0.0


static func _elev(from: Vector3, to: Vector3) -> float:
	return atan2(to.y - from.y, maxf(Vector2(to.x - from.x, to.z - from.z).length(), 0.01))


static func _point_at_elev(from: Vector3, target: Vector3, elev: float) -> Vector3:
	var flat := maxf(Vector2(target.x - from.x, target.z - from.z).length(), 0.01)
	return Vector3(target.x, from.y + tan(elev) * flat, target.z)


## Free mode: ease back behind the hero while running and the camera is left alone (not when running at it).
func _recenter(delta: float) -> void:
	if _idle_input < Tuning.CAM_RECENTER_DELAY or player.move_input.length() < 0.3:
		return
	var behind := atan2(-player.facing.x, -player.facing.z)
	var diff := wrapf(behind - yaw, -PI, PI)
	if absf(diff) > deg_to_rad(120.0):
		return
	var step := deg_to_rad(Tuning.CAM_RECENTER_SPEED) * delta
	yaw += clampf(diff, -step, step)


func _exclude_walls(delta: float) -> void:
	_exclude_check -= delta
	if _exclude_check > 0.0:
		return
	_exclude_check = 1.0
	for n in get_tree().get_nodes_in_group("camera_ignore"):
		if n is CollisionObject3D and not _excluded.has(n):
			_excluded[n] = true
			arm.add_excluded_object((n as CollisionObject3D).get_rid())
