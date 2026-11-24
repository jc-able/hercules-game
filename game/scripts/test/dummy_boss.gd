class_name DummyBoss
extends BossBase
## Core regression boss ("Straw Colossus", 6 m): a blockable sweep, then a tracked slam whose club sticks in the ground
## and opens the weak point `core` for 2 hits. Proves the whole chain (telegraphs, block, roll, strike, victory).

const T := Tuning.DUMMY
const PATTERN: Array[StringName] = [&"sweep", &"slam"]

var _pattern_i := 0
var _decal: Telegraph = null
var _impact_at := 0.0
var _impact_done := false
var _slam_center := Vector3.ZERO


func _init() -> void:
	boss_id = &"dummy"
	display_name = "The Straw Colossus"
	max_hp = T["hp"]
	body_radius = 1.2
	body_height = 5.6


func _build() -> void:
	# regression check for modules: arena and player are already set when _build() runs
	Game.event("boss_built", {"boss": boss_id, "arena": arena != null, "player": player != null})
	visual.add_socket(&"core_spot", Vector3(0, 0.9, 2.4))
	add_weak_point(&"core", &"core_spot", 0.9)


func _first_state() -> StringName:
	return &"approach"


func _enter_state(s: StringName) -> void:
	_impact_done = false
	match s:
		&"approach":
			visual.play(&"walk", 0.2)
		&"sweep":
			halt()
			_impact_at = T["sweep_windup"]
			visual.play(&"sweep", 0.12, visual.clip_length(&"sweep", 1.4) * 0.43 / _impact_at)
			_decal = arena.telegraph_cone(global_position, forward(), T["sweep_arc_deg"] * 0.5, T["sweep_reach"], _impact_at) as Telegraph
			Sfx.play("dummy_sweep_warn", global_position)
		&"slam":
			halt()
			_impact_at = T["slam_windup"]
			visual.play(&"slam", 0.12, visual.clip_length(&"slam", 2.2) * 0.64 / _impact_at)
			_slam_center = player.global_position
			_decal = arena.telegraph_circle(_slam_center, T["slam_radius"], _impact_at) as Telegraph
			Sfx.play("dummy_slam_warn", global_position)
		&"stuck":
			visual.play(&"stuck", 0.15)
			expose(&"core", T["stuck_hits"])
		&"recover":
			visual.play(&"pull_free", 0.15)
		&"idle":
			halt()
			visual.play(&"idle", 0.2)


func _exit_state(s: StringName) -> void:
	if s == &"stuck":
		close_weak(&"core")
	if s in [&"sweep", &"slam"] and is_instance_valid(_decal) and not _impact_done:
		_decal.cancel()


func _tick_state(delta: float) -> void:
	match state:
		&"approach":
			face_towards(player.global_position, T["turn_deg"], delta)
			var d := player_distance()
			if d > T["engage_dist"]:
				walk_towards(player.global_position, T["walk_speed"])
			else:
				halt()
			if (d <= T["engage_dist"] + 1.0 and angle_to_pos(player.global_position) < 25.0) or state_time > 5.0:
				var next := PATTERN[_pattern_i % PATTERN.size()]
				_pattern_i += 1
				set_state(next)
		&"sweep":
			if not _impact_done and state_time >= _impact_at:
				_impact_done = true
				var r := hit_cone(global_position, forward(), T["sweep_arc_deg"] * 0.5, T["sweep_reach"], T["sweep_dmg"], {"blockable": true, "knockback": 3.0})
				Sfx.play("dummy_sweep", global_position + forward() * 4.0)
				Game.event("attack_resolved", {"attack": "sweep", "result": r})
			if state_time >= _impact_at + 0.7:
				set_state(&"approach")
		&"slam":
			var track_end: float = _impact_at - T["slam_track_until"]
			if state_time < track_end:
				_slam_center = _slam_center.lerp(player.global_position, 1.0 - exp(-6.0 * delta))
				_decal.global_position = _slam_center
				face_towards(_slam_center, T["turn_deg"] * 1.5, delta)
			if not _impact_done and state_time >= _impact_at:
				_impact_done = true
				var r2 := hit_circle(_slam_center, T["slam_radius"], T["slam_dmg"], {"guard_break": true, "knockback": 5.0})
				Fx.dust(arena, _slam_center, T["slam_radius"])
				Sfx.play("cyclops_slam", _slam_center)
				Game.shake(0.6)
				Game.event("attack_resolved", {"attack": "slam", "result": r2})
				_move_core_to(_slam_center)
				set_state(&"stuck")
		&"stuck":
			if state_time >= T["stuck_time"]:
				set_state(&"recover")
		&"recover":
			if state_time >= T["recover_time"]:
				set_state(&"approach")


## The club lands where the decal was: the weak point sits between the boss and that spot (reachable on foot).
func _move_core_to(center: Vector3) -> void:
	var spot := visual.socket(&"core_spot")
	var local := to_local(center)
	local.y = 0.0
	var dist := clampf(local.length(), body_radius + 1.0, 4.0)
	spot.position = Vector3(0, 0.9, dist)


func get_lock_point() -> Vector3:
	return global_position + Vector3.UP * 4.2


func bot_advice() -> Dictionary:
	var adv := {"move_to": player.global_position, "face": global_position, "roll": false, "block": false, "attack": false}
	var to_player := player.global_position - global_position
	to_player.y = 0.0
	var away := to_player.normalized() if to_player.length() > 0.1 else Vector3.BACK
	match state:
		&"sweep":
			adv["block"] = player_distance() < T["sweep_reach"] + 1.5
		&"slam":
			var left := _impact_at - state_time
			var side := away.cross(Vector3.UP)
			adv["move_to"] = player.global_position + side * 6.0
			adv["roll"] = left < 0.32 and left > 0.05 and player.global_position.distance_to(_slam_center) < T["slam_radius"] + 1.0
			if left > 0.4:
				adv["move_to"] = player.global_position
		&"stuck":
			# the real blade reaches ~1.4 m (+ SWORD_TIP_EXTRA): stand 1.2 m short of the core on the boss->core line
			var wp: WeakPoint = weak_points[&"core"]
			var radial := wp.global_position - global_position
			radial.y = 0.0
			radial = radial.normalized() if radial.length() > 0.1 else away
			var stand := Vector3(wp.global_position.x, player.global_position.y, wp.global_position.z) + radial * 1.2
			adv["move_to"] = stand
			var d := player.global_position - wp.global_position
			d.y = 0.0
			adv["attack"] = d.length() < 1.2 + wp.radius
		_:
			adv["move_to"] = global_position + away * (T["engage_dist"] + 0.5)
	return adv
