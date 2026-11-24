class_name BossBase
extends CharacterBody3D
## Base class for every boss (group "boss", collision layer 3). A state machine: set_state() calls _exit_state(old),
## _enter_state(new); _tick_state(delta) runs each physics frame while the fight is on. Bosses take damage only through
## exposed weak points. Subclasses set boss_id/display_name/max_hp in _init or _ready, build the body in _build(),
## and override _enter_state/_tick_state/_exit_state, get_lock_point() and bot_advice().

signal defeated
signal health_changed(hp: int, max_hp: int)
signal state_changed(state: StringName)

var boss_id: StringName = &"boss"
var display_name := "Boss"
var max_hp := 8
var hp := 8
var player: Player
var visual: CharacterVisual
var arena: ArenaBase
var state: StringName = &"idle"
var state_time := 0.0
var fighting := false
var body_radius := 1.5            ## collision capsule radius (m)
var body_height := 6.0            ## collision capsule height (m)
var lock_height := 0.75           ## lock point as a share of the visual height when no socket says otherwise
var weak_points := {}             ## id -> WeakPoint
var hurt_clip: StringName = &"hurt"  ## played by take_weak_hit (&"" = none); the previous clip resumes after it
var hurt_blend := 0.08
var _state_serial := 0            # bumps on every state change (hurt-clip resume checks it)


func _ready() -> void:
	add_to_group("boss")
	collision_layer = 1 << 2
	collision_mask = 1
	hp = max_hp
	if visual == null:
		visual = CharacterVisual.create(boss_id)
		add_child(visual)
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = body_radius
	cap.height = maxf(body_height, body_radius * 2.0 + 0.01)
	cs.shape = cap
	cs.position.y = cap.height * 0.5
	cs.name = "Body"
	add_child(cs)
	_build()
	health_changed.emit(hp, max_hp)


## Override: extra collision shapes, weak points (add_weak_point), props. Called once from _ready().
func _build() -> void:
	pass


# ------------------------------------------------------------------ fight flow
## Starts the fight (ArenaBase calls this after the title card). Enters the subclass's first state.
func start_fight() -> void:
	fighting = true
	if player == null:
		player = Game.player()
	Game.event("fight_start", {"boss": boss_id, "hp": hp})
	set_state(_first_state())


## Stops all attacks (the player died or the fight ended).
func stop_fight() -> void:
	fighting = false
	for id in weak_points:
		close_weak(id)
	if hp > 0:
		set_state(&"idle")


## Override: the state the fight opens with.
func _first_state() -> StringName:
	return &"idle"


## Changes state: _exit_state(old) then _enter_state(new); resets state_time.
func set_state(s: StringName) -> void:
	var old := state
	_exit_state(old)
	state = s
	state_time = 0.0
	_state_serial += 1
	Game.event("boss_state", {"boss": boss_id, "state": s})
	state_changed.emit(s)
	_enter_state(s)


## Override: called when a state starts.
func _enter_state(_s: StringName) -> void:
	pass


## Override: called each physics frame while fighting.
func _tick_state(_delta: float) -> void:
	pass


## Override: called when a state ends.
func _exit_state(_s: StringName) -> void:
	pass


func _physics_process(delta: float) -> void:
	state_time += delta
	if fighting and hp > 0:
		_tick_state(delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, 20.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 20.0 * delta)
	if is_on_floor():
		velocity.y = -0.5
	else:
		velocity.y -= Tuning.GRAVITY * delta
	move_and_slide()
	if not _limbs.is_empty():
		_update_limbs()


# ------------------------------------------------------------------ limb blockers (feedback 2, clipping)
# A capsule on the boss layer (3) that follows two skeleton bones, so the hero (mask 1|3) is pushed out of a leg instead
# of standing inside it. Its own body (not a shape of the boss): the boss's floor/wall movement (mask 1) never sees it,
# the chase camera (mask 1) never sees it, and it is not in group "boss" (no glance, no lock-on).
var _limbs: Array[Dictionary] = []


## Adds a blocker from bone `from_bone` to bone `to_bone` (names in the visual's skeleton). Real models only.
func add_limb_blocker(from_bone: String, to_bone: String, radius: float) -> void:
	if visual == null or visual.is_standin or Game.args.has("no-limb-blockers"):   # harness A/B switch
		return
	var skel: Skeleton3D = visual.get("_skel")
	if skel == null:
		return
	var a := skel.find_bone(from_bone)
	var b := skel.find_bone(to_bone)
	if a < 0 or b < 0:
		push_warning("%s: limb blocker bones '%s'/'%s' not found" % [boss_id, from_bone, to_bone])
		return
	var body := StaticBody3D.new()
	body.name = "Limb_%s" % from_bone
	body.collision_layer = 1 << 2
	body.collision_mask = 0
	body.top_level = true
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = radius
	cap.height = radius * 2.0 + 0.1
	cs.shape = cap
	body.add_child(cs)
	add_child(body)
	_limbs.append({"body": body, "shape": cap, "skel": skel, "a": a, "b": b, "r": radius})
	_update_limbs()


func _update_limbs() -> void:
	for l in _limbs:
		var body: StaticBody3D = l["body"]
		var skel: Skeleton3D = l["skel"]
		if not is_instance_valid(body) or not is_instance_valid(skel):
			continue
		var sx := skel.global_transform
		var pa: Vector3 = sx * skel.get_bone_global_pose(int(l["a"])).origin
		var pb: Vector3 = sx * skel.get_bone_global_pose(int(l["b"])).origin
		var r: float = l["r"]
		var d := pb - pa
		var length := d.length()
		if length < 0.05:
			continue
		var y := d / length
		var x := y.cross(Vector3.UP if absf(y.y) < 0.95 else Vector3.RIGHT).normalized()
		var z := x.cross(y)
		(l["shape"] as CapsuleShape3D).height = length + 2.0 * r
		body.global_transform = Transform3D(Basis(x, y, z), (pa + pb) * 0.5)


# ------------------------------------------------------------------ helpers for subclasses
## Horizontal forward vector (+Z of the boss).
func forward() -> Vector3:
	var f := global_transform.basis.z
	f.y = 0.0
	return f.normalized()


## Turns toward a world position at most `deg_per_sec`.
func face_towards(pos: Vector3, deg_per_sec: float, delta: float) -> void:
	var to := pos - global_position
	to.y = 0.0
	if to.length() < 0.01:
		return
	var want := atan2(to.x, to.z)
	var step := deg_to_rad(deg_per_sec) * delta
	rotation.y = rotation.y + clampf(wrapf(want - rotation.y, -PI, PI), -step, step)


## Angle in degrees between the boss's forward and the direction to `pos` (0 = straight ahead).
func angle_to_pos(pos: Vector3) -> float:
	var to := pos - global_position
	to.y = 0.0
	if to.length() < 0.01:
		return 0.0
	return rad_to_deg(forward().angle_to(to.normalized()))


## Horizontal distance to the player (INF when there is none).
func player_distance() -> float:
	if player == null or not is_instance_valid(player):
		return INF
	var d := player.global_position - global_position
	d.y = 0.0
	return d.length()


## Sets horizontal velocity toward `pos` at `speed` (stops inside `stop_at` metres).
func walk_towards(pos: Vector3, speed: float, stop_at := 0.0) -> void:
	var to := pos - global_position
	to.y = 0.0
	if to.length() <= stop_at:
		velocity.x = 0.0
		velocity.z = 0.0
		return
	var v := to.normalized() * speed
	velocity.x = v.x
	velocity.z = v.z


## Stops horizontal movement.
func halt() -> void:
	velocity.x = 0.0
	velocity.z = 0.0


## Creates a weak point on a visual socket (it follows the bone). Closed until expose().
func add_weak_point(id: StringName, socket_name: StringName, radius: float) -> WeakPoint:
	var wp := WeakPoint.new(id, radius)
	wp.boss = self
	visual.socket(socket_name).add_child(wp)
	wp.struck.connect(take_weak_hit)
	weak_points[id] = wp
	return wp


## Opens a weak point for `hits` sword hits.
func expose(id: StringName, hits: int) -> void:
	var wp: WeakPoint = weak_points.get(id)
	if wp == null:
		push_warning("%s: no weak point '%s'" % [boss_id, id])
		return
	wp.open(hits)
	Game.event("weak_open", {"boss": boss_id, "point": id, "hits": hits})


## Closes a weak point.
func close_weak(id: StringName) -> void:
	var wp: WeakPoint = weak_points.get(id)
	if wp != null and wp.exposed:
		wp.close()
		Game.event("weak_close", {"boss": boss_id, "point": id})


## True while the weak point is open.
func is_exposed(id: StringName) -> bool:
	var wp: WeakPoint = weak_points.get(id)
	return wp != null and wp.exposed


## -1 hp, flash, `<boss_id>_hurt` sound, hurt clip (see hurt_clip); defeated at 0. Connected to every weak point's
## `struck`. The hurt clip plays BEFORE _on_weak_hit(), so a module that plays its own clip there replaces it.
func take_weak_hit(point: WeakPoint) -> void:
	if hp <= 0:
		return
	hp -= 1
	health_changed.emit(hp, max_hp)
	# feedback 2: shorter whole-body flash (was 0.2 s) so the cut, the ichor and the new wound read through it.
	# Finishing pass: 0.15 strength (was 0.85; 0.3 still turned the Hydra pale pink). The 0.06 s hit pause runs the
	# game at 5 % speed, so the flash held at full
	# strength for the whole pause and whitened the boss over the first frames of the burst; 0.15 only brightens it.
	visual.flash(Color(1.0, 0.95, 0.85), 0.08, WEAK_HIT_FLASH)
	_cut_fx(point)
	Sfx.play("%s_hurt" % boss_id, global_position)
	Game.event("boss_hit", {"boss": boss_id, "hp": hp, "point": point.id})
	if hp <= 0:
		_on_defeated()
	else:
		_play_hurt()
		_on_weak_hit(point)


## Ichor colour of each creature (stylised, not blood): cut burst, streak core, wounds and drips.
## Each contrasts with its body: gold on the purple Cyclops, lime-yellow on green Medusa, cyan on the purple/red Hydra
## (and against its orange fire).
const ICHOR := {&"cyclops": Color(1.0, 0.62, 0.12), &"medusa": Color(0.9, 1.0, 0.22), &"hydra": Color(0.25, 0.92, 1.0)}
const MAX_WOUNDS := 12
const WEAK_HIT_FLASH := 0.15         ## whole-body flash strength on a weak-point hit (CharacterVisual default 0.85)
var wounds: Array[Node3D] = []       ## feedback 2: wound decals that stay for the fight (scene reload clears them)
var _wound_layer_set := false


func ichor_color() -> Color:
	return ICHOR.get(boss_id, Color(1.0, 0.75, 0.25))


## The cut a counted weak-point hit leaves: streak + star + ring + sparks + ichor, then a wound that stays on the bone
## and a slow drip. Real models only for the wound (the stand-in has no surface worth marking).
func _cut_fx(point: WeakPoint) -> void:
	var col := ichor_color()
	var pos := point.last_hit_pos if point.last_hit_pos != Vector3.ZERO else point.global_position
	var from := point.last_from if point.last_from != Vector3.ZERO else (player.global_position if player != null and is_instance_valid(player) else global_position + forward() * 3.0)
	var dir := point.global_position - (from + Vector3.UP * 1.1)
	if dir.length() < 0.01:
		dir = -forward()
	dir = dir.normalized()
	var r := point.radius * point.global_basis.get_scale().x
	var host: Node = arena if arena != null else get_tree().current_scene
	Fx.cut(host, pos, col, dir, point.last_trail, r,
		player.global_position if player != null and is_instance_valid(player) else Vector3.INF)
	point.last_trail = PackedVector3Array()
	if visual == null or visual.is_standin:
		return
	var socket := point.get_parent() as Node3D
	if socket == null:
		return
	if not _wound_layer_set:
		_wound_layer_set = true
		for g in visual.find_children("*", "GeometryInstance3D", true, false):
			var gi := g as GeometryInstance3D
			var under_wp := false
			var p: Node = gi.get_parent()
			while p != null and p != visual:
				if p is WeakPoint:
					under_wp = true
					break
				p = p.get_parent()
			if not under_wp:
				gi.layers |= Fx.WOUND_LAYER
	# spread the marks a little round the cut so three hits show three marks
	var n := wounds.size()
	var jitter := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * r * 0.25 * minf(float(n), 2.0)
	var w := Fx.wound(socket, pos.lerp(point.global_position, 0.5) + jitter, dir, col, r)
	if w != null:
		wounds.append(w)
		if n % 2 == 0:
			Fx.drip(socket, pos, col)
	while wounds.size() > MAX_WOUNDS:
		var old: Node3D = wounds.pop_front()
		if is_instance_valid(old):
			old.queue_free()


## Override: reaction to a weak-point hit that did not kill (default: nothing; flash, sound and hurt clip already played).
func _on_weak_hit(_point: WeakPoint) -> void:
	pass


## Plays hurt_clip over the current clip, then resumes the clip that was playing if the state did not change meanwhile.
func _play_hurt() -> void:
	if hurt_clip == &"" or visual == null or not visual.has_clip(hurt_clip):
		return
	var prev := visual.current_clip
	visual.play(hurt_clip, hurt_blend)
	if prev == &"" or prev == hurt_clip:
		return
	# a connection (not await): it is dropped automatically if the boss is freed first
	get_tree().create_timer(visual.clip_length(hurt_clip, 0.5) * 0.9, false).timeout.connect(_resume_after_hurt.bind(prev, _state_serial))


func _resume_after_hurt(prev: StringName, serial: int) -> void:
	if hp > 0 and serial == _state_serial and visual.current_clip == hurt_clip:
		visual.play(prev, 0.15)


func _on_defeated() -> void:
	fighting = false
	for id in weak_points:
		close_weak(id)
	halt()
	var old := state
	_exit_state(old)        # module cleanup (beams, fire, decals, loops) runs even when the killing blow lands mid-attack
	state = &"dead"
	state_time = 0.0
	_state_serial += 1
	visual.play(&"death", 0.2)
	Sfx.play("%s_death" % boss_id, global_position)
	Sfx.stop_music(0.4)
	Sfx.play("victory")
	Game.shake(0.6)
	Game.event("boss_state", {"boss": boss_id, "state": state})
	state_changed.emit(state)
	_enter_state(state)     # modules may react to &"dead" (e.g. a different death clip); _tick_state no longer runs
	Game.event("boss_defeated", {"boss": boss_id})
	defeated.emit()


## The point the camera and lock-on reticle aim at (default: "head" socket, else lock_height x height).
func get_lock_point() -> Vector3:
	if visual != null and visual.has_method("socket") and not visual.is_standin:
		return visual.socket(&"head").global_position.lerp(global_position + Vector3.UP * visual.height * 0.6, 0.4)
	return global_position + Vector3.UP * (visual.height if visual != null else body_height) * lock_height


## The point a locked-on hero at `from` faces (his body, shield arc and strikes; integrate2_hero). Default: the boss's
## root. Override for a weak point that lies away from the body (the Hydra's jaw on the ground beside him).
func strike_point(_from: Vector3) -> Vector3:
	return global_position


## World height of the boss's top from the model's real bounds (CharacterVisual.model_top: rest pose, props not
## counted). The lock camera keeps it inside the frame when it can (SPEC §10). Override for a pose that is much taller.
func frame_top() -> float:
	if visual != null:
		return global_position.y + visual.model_top() * absf(visual.global_transform.basis.get_scale().y)
	return global_position.y + body_height


## World points spread over the top of the model (CharacterVisual.model_top_points: rest pose, props not counted).
## The lock camera keeps the highest-looking of them inside the frame when it can. Override for special cases.
func frame_top_points() -> PackedVector3Array:
	var out := PackedVector3Array()
	if visual == null:
		out.append(global_position + Vector3.UP * body_height)
		return out
	var xf := visual.global_transform
	for p in visual.model_top_points():
		out.append(xf * p)
	return out


## Damages the player when inside the circle (horizontal). Returns the try_hit result or "miss".
func hit_circle(center: Vector3, radius: float, dmg: int, opts := {}) -> StringName:
	if player == null or not is_instance_valid(player):
		return &"miss"
	var d := player.global_position - center
	d.y = 0.0
	if d.length() > radius + Tuning.PLAYER_RADIUS * 0.5:
		return &"miss"
	return player.try_hit(dmg, center, opts)


## Damages the player when inside the cone (horizontal angle + length from origin). Returns try_hit result or "miss".
func hit_cone(origin: Vector3, dir: Vector3, half_angle_deg: float, length: float, dmg: int, opts := {}) -> StringName:
	if player == null or not is_instance_valid(player):
		return &"miss"
	var to := player.global_position - origin
	to.y = 0.0
	var d := Vector3(dir.x, 0, dir.z).normalized()
	var dist := to.length()
	if dist > length + Tuning.PLAYER_RADIUS * 0.5:
		return &"miss"
	if dist > 0.5 and rad_to_deg(d.angle_to(to.normalized())) > half_angle_deg:
		return &"miss"
	return player.try_hit(dmg, origin, opts)


## True when hp is at or below half.
func enraged() -> bool:
	return hp <= int(float(max_hp) * Tuning.ENRAGE_FRACTION)


## Advice for the test bot: {move_to: Vector3, face: Vector3, roll: bool, block: bool, attack: bool}.
## Default: approach an exposed weak point and strike it, else keep 8 m from the boss. Bosses override this.
func bot_advice() -> Dictionary:
	var adv := {"move_to": global_position, "face": global_position, "roll": false, "block": false, "attack": false}
	if player == null:
		return adv
	for id in weak_points:
		var wp: WeakPoint = weak_points[id]
		if wp.exposed:
			adv["move_to"] = wp.global_position
			var d := player.global_position - wp.global_position
			d.y = 0.0
			adv["attack"] = d.length() < Tuning.SWORD_REACH + 0.6
			return adv
	var away := player.global_position - global_position
	away.y = 0.0
	adv["move_to"] = global_position + away.normalized() * 8.0
	return adv
