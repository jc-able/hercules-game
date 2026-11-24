class_name Player
extends CharacterBody3D
## Hercules (SPEC §2): run / locked-on strafing, roll with i-frames, 2-hit sword combo, shield arc, flinch, petrify.
## Collision layer 2. Creates its own PlayerCamera. All numbers come from Tuning.

signal died
signal health_changed(hp: int, max_hp: int)
signal state_changed(state: StringName)
signal lock_changed(target: Node3D)

var hp: int = Tuning.PLAYER_HP
var max_hp: int = Tuning.PLAYER_HP
var invulnerable := false
var state: StringName = &"idle"
var state_time := 0.0
var control_enabled := true
var lock_target: BossBase = null
var locked := false
var visual: CharacterVisual
var sword: SwordHitbox
var camera: PlayerCamera
var facing := Vector3(0, 0, -1)       ## horizontal unit vector the hero faces
var move_input := Vector2.ZERO        ## last movement stick (x right, y back), for animation + bot checks
var god_mode := false                 ## debug: ignore damage
## Player clock time (see clock(), physics seconds, follows --speed) at which the shield was last raised; -1 while it is
## not raised. Shield up for: clock() - block_since. (Medusa's timed-raise reflect reads it.)
var block_since := -1.0

var _clock := 0.0
var _iframe_until := 0.0           # after a petrify (also stops damage-over-time ticks)
var _hit_iframe_until := 0.0       # after a hit (damage-over-time ticks ignore these)
var _roll_dir := Vector3.ZERO
var _attack_stage := 0
var _attack_buffered := false
var _attack_len := 0.55
var _active := Vector2(0.18, 0.32)
var _knock_vel := Vector3.ZERO
var _knock_time := 0.0
var _knock_left := 0.0
var _petrify_len := 1.5
var _lowering := 0.0
var _clip: StringName = &""
var _step_t := 0.2                    # seconds since the last footstep sound
var _vis_yaw := 0.0                   # the visual's yaw offset from `facing` (circling run, rolls); radians
var _vis_yaw_target := 0.0
var _vis_yaw_vel := 0.0               # rad/s: the body yaw accelerates and brakes (VIS_TURN_ACCEL)
var _attack_end := -10.0              # _clock when the last strike ended (VIS_TURN_ATTACK_AFTER)
var _circling := false               # this frame: locked on and running with the body turned (set by _tick_free)
var _twist := 0.0                     # upper-body twist back toward the boss in the circling run; radians
var _loco_speed := 0.0                # locomotion ground speed (m/s): clip playback = this / clip move_speed
var _side_t := 0.0                    # locked on: how long a full-speed side-step has been asked for
var _hold_until := 0.0                # a finishing one-shot (block_end) keeps playing until then unless the hero moves
var _props_dropped := false
var _carry := 1.0                     # sword carry blend (SWORD_CARRY_*): 1 in locomotion, 0 in actions


func _ready() -> void:
	add_to_group("player")
	collision_layer = 1 << 1
	collision_mask = 1 | (1 << 2)
	floor_snap_length = 0.4
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = Tuning.PLAYER_RADIUS
	cap.height = Tuning.PLAYER_HEIGHT
	cs.shape = cap
	cs.position.y = Tuning.PLAYER_HEIGHT * 0.5
	add_child(cs)
	visual = CharacterVisual.create(&"hercules")
	add_child(visual)
	var sword_prop := visual.attach_prop(&"hand_r", "res://assets/props/sword.glb")
	visual.attach_prop(&"forearm_l", "res://assets/props/shield.glb")
	sword = SwordHitbox.new()
	add_child(sword)
	if not visual.is_standin:
		sword.follow(visual.socket(&"hand_r"), sword_prop)     # the hit volume is the real blade
	sword.struck.connect(func(p: WeakPoint): Game.event("strike", {"point": p.id, "left": p.hits_left}))
	sword.glanced.connect(func(_pos: Vector3): Game.event("glance"))
	camera = PlayerCamera.new()
	camera.player = self
	add_child(camera)
	_apply_facing()
	health_changed.emit(hp, max_hp)


# ------------------------------------------------------------------ public API
## Applies an attack. opts: blockable=true, guard_break=false, petrify=0.0, knockback=4.0, reflect=false, dot=false.
## dot = a damage-over-time tick (fire): hit i-frames do not stop it (roll and petrify i-frames do), no flinch, no
## knockback, no new i-frames, it can kill.
## Returns "hit" | "blocked" | "dodged" | "reflected".
func try_hit(dmg: int, from: Vector3, opts := {}) -> StringName:
	if state == &"dead":
		return &"dodged"
	if bool(opts.get("reflect", false)) and is_blocking_towards(from):
		Sfx.play("reflect", global_position)
		Fx.spark(get_parent(), global_position + facing * 0.6 + Vector3.UP * 1.3, Color(0.7, 1.0, 0.9), 26, 0.1)
		Game.event("reflect")
		return &"reflected"
	if bool(opts.get("dot", false)):
		return _dot_tick(dmg, from, opts)
	if _is_invulnerable():
		Game.event("dodge")
		return &"dodged"
	var guard_break := bool(opts.get("guard_break", false))
	if bool(opts.get("blockable", true)) and not guard_break and is_blocking_towards(from):
		_push_back(from, Tuning.BLOCK_PUSHBACK, 0.2)
		Sfx.play("block", global_position)
		Fx.spark(get_parent(), global_position + facing * 0.6 + Vector3.UP * 1.2, Color(0.75, 0.85, 1.0), 16, 0.07)
		Game.shake(0.12)
		Game.event("block", {"dmg": dmg})
		return &"blocked"
	if guard_break and state == &"block":
		Sfx.play("block", global_position, 2.0, 0.7)   # no guard_break sound in the registry: a lower, louder clang
		Game.event("guard_break")
	if not god_mode:
		hp = maxi(hp - dmg, 0)
	health_changed.emit(hp, max_hp)
	visual.flash(Color(1.0, 0.25, 0.2), 0.18)
	Sfx.play("hurt", global_position)
	Game.shake(clampf(float(dmg) / 50.0, 0.15, 0.8))
	Controls.rumble(0.5, 0.9, 0.25)
	Game.event("player_hit", {"dmg": dmg, "hp": hp})
	sword.set_active(false)
	if hp <= 0:
		_die()
		return &"hit"
	var pet := float(opts.get("petrify", 0.0))
	if pet > 0.0:
		_petrify_len = pet
		_set_state(&"petrified")
		visual.set_petrified(true)
		Sfx.play("petrify", global_position)
		Game.event("petrified", {"secs": pet})
	else:
		_push_back(from, float(opts.get("knockback", Tuning.DEFAULT_KNOCKBACK)), Tuning.HIT_FLINCH)
		_hit_iframe_until = _clock + Tuning.HIT_IFRAMES
		_set_state(&"hit")
	return &"hit"


## One damage-over-time tick (try_hit with opts.dot): see try_hit.
func _dot_tick(dmg: int, from: Vector3, opts: Dictionary) -> StringName:
	if _is_invulnerable(true):
		Game.event("dodge", {"dot": true})
		return &"dodged"
	if bool(opts.get("blockable", true)) and is_blocking_towards(from):
		Game.event("block", {"dmg": dmg, "dot": true})
		return &"blocked"
	if not god_mode:
		hp = maxi(hp - dmg, 0)
	health_changed.emit(hp, max_hp)
	visual.flash(Color(1.0, 0.45, 0.1), 0.12)
	Sfx.play("hurt", global_position, -4.0, 1.15)
	Controls.rumble(0.3, 0.6, 0.15)
	Game.event("player_hit", {"dmg": dmg, "hp": hp, "dot": true})
	if hp <= 0:
		_die()
	return &"hit"


## True when the shield is raised and `pos` lies inside its front arc.
func is_blocking_towards(pos: Vector3) -> bool:
	if state != &"block":
		return false
	var to := pos - global_position
	to.y = 0.0
	if to.length() < 0.01:
		return true
	return rad_to_deg(facing.angle_to(to.normalized())) <= Tuning.SHIELD_ARC_DEG * 0.5


## Enables or disables player control (title cards, victory, cutscenes). Disabled = stands idle.
func set_control(enabled: bool) -> void:
	control_enabled = enabled
	if not enabled and state in [&"block", &"attack"]:
		sword.set_active(false)
		_set_state(&"idle")


## Sets (or clears with null) the lock-on target; the fight start calls this.
func set_lock_target(boss: BossBase) -> void:
	lock_target = boss
	locked = boss != null
	lock_changed.emit(boss)


## The point the camera and reticle aim at, or null when not locked.
func lock_point():
	if locked and is_instance_valid(lock_target):
		return lock_target.get_lock_point()
	return null


## Full health and idle (used by restarts that do not rebuild the scene).
func reset_health() -> void:
	hp = max_hp
	_set_state(&"idle")
	visual.set_petrified(false)
	health_changed.emit(hp, max_hp)


# ------------------------------------------------------------------ frame
func _physics_process(delta: float) -> void:
	_clock += delta
	state_time += delta
	invulnerable = _is_invulnerable()
	if locked and (not is_instance_valid(lock_target) or lock_target.hp <= 0):
		set_lock_target(null)
	var inp := Controls.get_move() if control_enabled else Vector2.ZERO
	move_input = inp
	var wish := _world_dir(inp)
	if control_enabled and Input.is_action_just_pressed("lock_on"):
		_toggle_lock()
	var hv := Vector3.ZERO
	_circling = false
	match state:
		&"idle", &"move":
			hv = _tick_free(delta, inp, wish)
		&"roll":
			hv = _tick_roll()
		&"attack":
			hv = _tick_attack(delta)
		&"block":
			hv = _tick_block(delta, wish)
		&"hit":
			if state_time >= Tuning.HIT_FLINCH:
				_set_state(&"idle")
		&"petrified":
			if state_time >= _petrify_len:
				visual.set_petrified(false)
				_iframe_until = _clock + Tuning.PETRIFY_IFRAMES
				_set_state(&"idle")
		&"dead":
			# the death clip's drop_props event: sword and shield leave the hands and fall flat
			# (clip time -> game time: the clip starts at DEATH_CLIP_FROM and plays at DEATH_CLIP_SPEED)
			var drop_at := maxf(visual.event_time(&"death", &"drop_props", 2.1) - Tuning.DEATH_CLIP_FROM, 0.0) / Tuning.DEATH_CLIP_SPEED
			if not _props_dropped and state_time >= drop_at:
				_props_dropped = true
				visual.drop_props(get_parent(), global_position.y)
	_turn_visual(delta)
	# circling run: the upper body turns back toward the boss by a share of the hips' turn. Anything else (a strike, a
	# stop, the shield) unwinds it together with the hips while they turn back; a roll or a death eases it to 0. It never
	# exceeds the circling amount.
	var follow := -wrapf(_vis_yaw, -PI, PI) * Tuning.CIRCLE_TWIST
	var twist_to := 0.0
	if _circling:
		twist_to = follow
	elif state != &"roll" and state != &"dead" and signf(follow) == signf(_twist) and absf(follow) < absf(_twist):
		twist_to = follow
	_twist = move_toward(_twist, twist_to, deg_to_rad(Tuning.CIRCLE_TWIST_DEG_S) * delta)
	visual.set_upper_twist(_twist, _twist * Tuning.CIRCLE_HEAD / Tuning.CIRCLE_TWIST)
	# sword carry: aimed low out to the right in locomotion (reads from behind), blended out for every action: with the
	# arm (SWORD_CARRY_OUT), or for a strike before its active window opens (SWORD_CARRY_OUT_STRIKE)
	var carry_on := state == &"idle" or state == &"move"
	var out_t := Tuning.SWORD_CARRY_OUT
	if state == &"attack":
		out_t = minf(Tuning.SWORD_CARRY_OUT_STRIKE, maxf(_active.x * 0.85, 0.02))
	_carry = move_toward(_carry, 1.0 if carry_on else 0.0, delta / (Tuning.SWORD_CARRY_IN if carry_on else out_t))
	var run_k := clampf(Vector2(velocity.x, velocity.z).length() / Tuning.RUN_SPEED, 0.0, 1.0)
	var carry_wt := lerpf(Tuning.SWORD_CARRY_WEIGHT, Tuning.SWORD_CARRY_WEIGHT_RUN, run_k)
	visual.set_socket_aim(&"hand_r", Tuning.SWORD_CARRY_DIR.rotated(Vector3.UP, _twist), _carry * _carry * (3.0 - 2.0 * _carry) * carry_wt)
	if _knock_left > 0.0:
		_knock_left -= delta
		hv += _knock_vel * clampf(_knock_left / maxf(_knock_time, 0.01), 0.0, 1.0)
	velocity.x = hv.x
	velocity.z = hv.z
	if is_on_floor():
		velocity.y = -0.5
	else:
		velocity.y -= Tuning.GRAVITY * delta
	move_and_slide()
	_apply_facing()
	if global_position.y < -30.0:
		global_position = Vector3(0, 2, 0)
		velocity = Vector3.ZERO


## Free run (run clip, turns toward the stick) or, locked on, the boss-facing set: walk_back when backing away
## (LOCK_BACK_SPEED), strafe_l / strafe_r for a side-step (LOCK_STRAFE_SPEED), and after LOCK_STRAFE_TIME of full-speed
## side input a circling run at LOCK_SPEED with the body turned into the run (`facing` stays on the boss for the
## shield and the camera). Every locomotion clip plays at ground speed / its manifest move_speed: no skating.
func _tick_free(delta: float, inp: Vector2, wish: Vector3) -> Vector3:
	_vis_yaw_target = 0.0
	if not control_enabled:
		_loco_speed = 0.0
		_anim_loco(&"idle")
		return Vector3.ZERO
	if Input.is_action_just_pressed("roll"):
		_start_roll(wish)
		return _tick_roll()
	if Input.is_action_just_pressed("attack"):
		_start_attack(1)
		return Vector3.ZERO
	if Input.is_action_pressed("shield"):
		_set_state(&"block")
		_lowering = 0.0
		visual.play(&"block_start", 0.08)
		_clip = &"block_start"
		Sfx.play("shield_up", global_position)
		Game.event("shield_up")
		return Vector3.ZERO
	var demand := minf(inp.length() * 1.15, 1.0)
	var dir := wish.normalized() if wish.length() > 0.01 else Vector3.ZERO
	var clip := &"idle"
	var want := 0.0
	if locked:
		_face_lock(1.0)
		if demand > 0.05:
			var fwd := dir.dot(facing)
			var side := dir.dot(facing.cross(Vector3.UP))   # > 0 = to the hero's right
			var full := Tuning.LOCK_SPEED * demand
			if absf(side) > absf(fwd):
				_side_t = _side_t + delta if full > Tuning.LOCK_STRAFE_SPEED else 0.0
				if _side_t < Tuning.LOCK_STRAFE_TIME:
					clip = &"strafe_r" if side > 0.0 else &"strafe_l"
					want = minf(full, Tuning.LOCK_STRAFE_SPEED)
				else:
					clip = &"run"
					want = full
					# the hips turn into the run (just under side-on); the spine twists back to the boss (see
					# _physics_process), so the chase camera keeps seeing his back
					var lim := deg_to_rad(Tuning.CIRCLE_TURN_DEG)
					_vis_yaw_target = clampf(facing.signed_angle_to(dir, Vector3.UP), -lim, lim)
					_circling = true
			elif fwd > 0.0:
				# a full-speed run toward the boss that swings to the side keeps running (no side-step first)
				_side_t = Tuning.LOCK_STRAFE_TIME if full > Tuning.LOCK_STRAFE_SPEED else 0.0
				clip = &"run"
				want = full
				_vis_yaw_target = facing.signed_angle_to(dir, Vector3.UP)
				_circling = true        # same twist share on a diagonal run: no jump where the two branches meet
			else:
				_side_t = 0.0
				clip = &"walk_back"
				want = minf(full, Tuning.LOCK_BACK_SPEED)
		else:
			_side_t = 0.0
	else:
		_side_t = 0.0
		if wish.length() > 0.05:
			_turn_towards(wish, Tuning.TURN_SPEED_DEG * delta)
		if demand > 0.05:
			clip = &"run"
			want = Tuning.RUN_SPEED * demand
	# starts and stops are instant (responsive); changes between gaits ease (strafe 1.8 -> circling run 4.6)
	if want < 0.05 or _loco_speed < 0.05:
		_loco_speed = want
	else:
		_loco_speed = move_toward(_loco_speed, want, Tuning.LOCO_ACCEL * delta)
	state = &"move" if want > 0.05 else &"idle"
	_anim_loco(clip)
	_footsteps(delta, inp)
	return dir * _loco_speed


func _tick_roll() -> Vector3:
	var t := state_time
	if t >= Tuning.ROLL_TIME + Tuning.ROLL_RECOVERY:
		_set_state(&"idle")
		return Vector3.ZERO
	if t >= Tuning.ROLL_TIME:
		# the roll clip has ended: instead of holding its last frame (a freeze) go straight into the gait the held stick
		# asks for (no stand-up between the roll and the run), or settle into idle with no input
		if visual.current_clip == &"roll":
			var next := _held_loco_clip()
			visual.play(next, Tuning.SETTLE_BLEND if next == &"idle" else Tuning.GAIT_BLEND)
			_clip = next
		return Vector3.ZERO
	var base := Tuning.ROLL_DISTANCE / Tuning.ROLL_TIME
	var k := 1.3 - 0.6 * (t / Tuning.ROLL_TIME)          # fast start, slower end; averages to 1.0
	return _roll_dir * base * k


func _tick_attack(delta: float) -> Vector3:
	var t := state_time
	# a press counts toward attack_2 only from ATTACK_BUFFER before the chain point (earlier presses are ignored)
	if control_enabled and Input.is_action_just_pressed("attack") and _attack_stage == 1 and t >= Tuning.ATTACK_CHAIN_FROM - Tuning.ATTACK_BUFFER:
		_attack_buffered = true
	var on := t >= _active.x and t <= _active.y
	sword.set_active(on)
	if locked:
		_face_lock(1.0)
	if _attack_stage == 1 and _attack_buffered and t >= Tuning.ATTACK_CHAIN_FROM:
		_start_attack(2)
		return Vector3.ZERO
	if control_enabled and t > _active.y and Input.is_action_just_pressed("roll"):
		sword.set_active(false)
		_start_roll(_world_dir(move_input))
		return _tick_roll()
	# attack_1's recovery (sword back to the stance, a step back) at the strike's 2.3x speed brought the arm down in 3
	# frames (53-58 deg/frame) and stopped dead: past the chain point with no chain asked for, the rest of the clip plays
	# at ATTACK_RECOVER_SPEED and finishes under _hold_until after control returns (any move cuts it with SETTLE_BLEND)
	if _attack_stage == 1 and not _attack_buffered and t >= Tuning.ATTACK_CHAIN_FROM and visual.current_clip == &"attack_1" \
			and visual.get_speed() > Tuning.ATTACK_RECOVER_SPEED:
		visual.set_speed(Tuning.ATTACK_RECOVER_SPEED)
	if t >= _attack_len:
		sword.set_active(false)
		var rest := 0.0
		if visual.current_clip == &"attack_1" and absf(visual.get_speed()) > 0.01:
			rest = maxf(visual.clip_length(&"attack_1", 0.0) - visual.clip_position(), 0.0) / absf(visual.get_speed())
		_set_state(&"idle")
		if rest > 0.0:
			_hold_until = _clock + rest
		return Vector3.ZERO
	if on:
		return facing * Tuning.ATTACK_LUNGE / maxf(_active.y - _active.x, 0.05)
	return Vector3.ZERO


func _tick_block(_delta: float, wish: Vector3) -> Vector3:
	if locked:
		_face_lock(1.0)
	if state_time > 0.15 and _clip == &"block_start":
		visual.play(&"block_idle", 0.1)
		_clip = &"block_idle"
	var holding := control_enabled and Input.is_action_pressed("shield")
	if holding:
		if _lowering > 0.0 and _clip == &"block_end":      # raised again while lowering
			visual.play(&"block_idle", 0.08)
			_clip = &"block_idle"
		_lowering = 0.0
	else:
		if _lowering == 0.0 and visual.has_clip(&"block_end"):
			# lowering: the block_end clip (block pose -> idle, 0.25 s) instead of a locomotion blend that slid the foot
			visual.play(&"block_end", 0.05)
			_clip = &"block_end"
			_hold_until = _clock + visual.clip_length(&"block_end", 0.25)
		_lowering += get_physics_process_delta_time()
		if _lowering >= Tuning.SHIELD_LOWER_TIME:
			_set_state(&"idle")
			Game.event("shield_down")
			return Vector3.ZERO
	return wish * Tuning.BLOCK_MOVE_SPEED


# ------------------------------------------------------------------ actions
## Rolls along the stick (or straight back with no input). The roll clip is a forward roll: the body lines up with the
## roll line (locked-on side rolls turn the visual, `facing` stays on the boss); a backward roll plays the clip in
## reverse instead of turning the hero's front to the camera.
func _start_roll(wish: Vector3) -> void:
	var has_dir := wish.length() > 0.1
	_roll_dir = wish.normalized() if has_dir else -facing
	if not locked and has_dir:
		facing = _roll_dir
	_set_state(&"roll")
	var spd := visual.clip_length(&"roll", Tuning.ROLL_TIME) / Tuning.ROLL_TIME
	var a := facing.signed_angle_to(_roll_dir, Vector3.UP)
	if absf(a) > deg_to_rad(120.0):
		_vis_yaw_target = wrapf(a + PI, -PI, PI)
		spd = -spd
	else:
		_vis_yaw_target = a
	_vis_yaw = _vis_yaw_target
	_vis_yaw_vel = 0.0
	visual.rotation.y = _vis_yaw
	visual.play(&"roll", Tuning.ROLL_BLEND, spd)
	_clip = &"roll"
	Sfx.play("roll", global_position)
	Game.event("roll")


func _start_attack(stage: int) -> void:
	_attack_stage = stage
	_attack_buffered = false
	var clip := &"attack_1" if stage == 1 else &"attack_2"
	_attack_len = Tuning.ATTACK_1_TIME if stage == 1 else Tuning.ATTACK_2_TIME
	var act := Tuning.ATTACK_1_ACTIVE if stage == 1 else Tuning.ATTACK_2_ACTIVE
	var clen := visual.clip_length(clip, _attack_len)
	var speed := clen / _attack_len
	# events from the manifest are in clip time; scale them to game time
	_active = Vector2(visual.event_time(clip, &"active_start", act.x * speed) / speed, visual.event_time(clip, &"active_end", act.y * speed) / speed)
	if locked:
		_face_lock(1.0)
	elif move_input.length() > 0.1:
		facing = _world_dir(move_input).normalized()
	_set_state(&"attack")
	visual.play(clip, Tuning.ATTACK_BLEND if stage == 1 else 0.06, speed)
	_clip = clip
	Sfx.play("sword_swing", global_position)
	Game.event("attack", {"stage": stage})


func _die() -> void:
	_set_state(&"dead")
	visual.set_petrified(false)
	visual.play(&"death", 0.1, Tuning.DEATH_CLIP_SPEED, Tuning.DEATH_CLIP_FROM)
	_clip = &"death"
	Sfx.play("death", global_position)
	control_enabled = false
	Game.event("player_died")
	died.emit()


func _toggle_lock() -> void:
	if locked:
		set_lock_target(null)
		Game.event("lock", {"on": false})
		return
	var best: BossBase = null
	var best_d := Tuning.LOCK_MAX_DISTANCE
	for b in get_tree().get_nodes_in_group("boss"):
		if b is BossBase and (b as BossBase).hp > 0:
			var d := global_position.distance_to((b as BossBase).global_position)
			if d < best_d:
				best_d = d
				best = b
	if best != null:
		set_lock_target(best)
		Game.event("lock", {"on": true})


func _set_state(s: StringName) -> void:
	if s != &"attack":
		sword.set_active(false)
	if s == &"block" and state != &"block":
		block_since = _clock
	elif s != &"block":
		block_since = -1.0
	if state == &"attack" and s != &"attack":
		_attack_end = _clock
	state = s
	state_time = 0.0
	if s != &"idle" and s != &"move":
		_hold_until = 0.0
		if s != &"roll":
			_vis_yaw_target = 0.0
	if s == &"hit":
		# the whole flinch clip (idle -> flinch -> idle) inside HIT_FLINCH
		visual.play(&"hit", Tuning.HIT_BLEND, visual.clip_length(&"hit", Tuning.HIT_FLINCH) / Tuning.HIT_FLINCH)
		_clip = &"hit"
	elif s == &"idle":
		# re-picks the locomotion clip, unless a locomotion clip already plays (the roll's recovery goes into it)
		_clip = visual.current_clip if visual.current_clip in [&"idle", &"run", &"strafe_l", &"strafe_r", &"walk_back"] else &""
	state_changed.emit(s)


## The hero's own clock (physics seconds since he was created; game time, so it follows --speed). Compare block_since
## with it.
func clock() -> float:
	return _clock


## Slides the hero `dist` metres straight away from `from` over `secs` seconds (the knockback slide: no damage, no state
## change, collision kept). Bosses use it to clear the hero out of a falling body, etc.
func push_back(from: Vector3, dist: float, secs: float) -> void:
	_push_back(from, dist, secs)


func _push_back(from: Vector3, dist: float, secs: float) -> void:
	var away := global_position - from
	away.y = 0.0
	if away.length() < 0.01:
		away = -facing
	_knock_time = maxf(secs, 0.05)
	_knock_left = _knock_time
	_knock_vel = away.normalized() * (2.0 * dist / _knock_time)


## Roll window, petrified, the i-frames after a petrify and (unless `ignore_hit_iframes`) the i-frames after a hit.
func _is_invulnerable(ignore_hit_iframes := false) -> bool:
	if state == &"roll" and state_time >= Tuning.ROLL_IFRAME_START and state_time <= Tuning.ROLL_IFRAME_END:
		return true
	if state == &"petrified":
		return true
	if _clock < _iframe_until:
		return true
	return not ignore_hit_iframes and _clock < _hit_iframe_until


# ------------------------------------------------------------------ helpers
## Camera-relative world direction for a stick vector (x right, y back).
func _world_dir(inp: Vector2) -> Vector3:
	if inp.length() < 0.01:
		return Vector3.ZERO
	var yaw := camera.yaw if camera != null else 0.0
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	var right := Vector3(cos(yaw), 0, -sin(yaw))
	var d := right * inp.x - fwd * inp.y
	return d.normalized() * minf(inp.length(), 1.0)


## Locked on: faces the boss's strike_point (BossBase: the root by default, the Hydra's lying jaw from beside it). Small
## changes follow at once (the boss walks, the hero circles); a jump of the point (the jaw goes down, a new lock) turns
## at LOCK_FACE_JUMP_DEG instead of snapping the whole body in one frame.
func _face_lock(_k: float) -> void:
	if not is_instance_valid(lock_target):
		return
	var to := lock_target.strike_point(global_position) - global_position
	to.y = 0.0
	if to.length() <= 0.05:
		return
	var d := to.normalized()
	if rad_to_deg(facing.angle_to(d)) <= Tuning.LOCK_FACE_SNAP_DEG:
		facing = d
	else:
		_turn_towards(d, Tuning.LOCK_FACE_JUMP_DEG * get_physics_process_delta_time())


func _turn_towards(dir: Vector3, max_rad_deg: float) -> void:
	var d := Vector3(dir.x, 0, dir.z).normalized()
	var a := facing.signed_angle_to(d, Vector3.UP)
	var step := deg_to_rad(max_rad_deg)
	facing = facing.rotated(Vector3.UP, clampf(a, -step, step)).normalized()


func _apply_facing() -> void:
	rotation = Vector3(0, atan2(facing.x, facing.z), 0)


## The locomotion clip _tick_free would pick for the stick held now (used at the end of a roll).
func _held_loco_clip() -> StringName:
	var inp := move_input
	if inp.length() * 1.15 <= 0.05:
		return &"idle"
	var dir := _world_dir(inp).normalized()
	if not locked:
		return &"run"
	var fwd := dir.dot(facing)
	var side := dir.dot(facing.cross(Vector3.UP))
	if absf(side) > absf(fwd):
		if _side_t >= Tuning.LOCK_STRAFE_TIME and Tuning.LOCK_SPEED * minf(inp.length() * 1.15, 1.0) > Tuning.LOCK_STRAFE_SPEED:
			return &"run"
		var c := &"strafe_r" if side > 0.0 else &"strafe_l"
		return c if visual.has_clip(c) else &"strafe_l"
	return &"run" if fwd > 0.0 else &"walk_back"


## Turns the visual's yaw toward _vis_yaw_target the short way (a change of side passes the back-to-camera side): it
## accelerates at VIS_TURN_ACCEL up to VIS_TURN_DEG (VIS_TURN_ATTACK_DEG into and just after a strike) and brakes to stop
## on the target, instead of the constant-rate turn that spun the legs 85 deg in 3 frames. Only the picture: hit tests
## use `facing`.
func _turn_visual(delta: float) -> void:
	var rem := angle_difference(_vis_yaw, _vis_yaw_target)
	var slow := state == &"attack" or _clock - _attack_end < Tuning.VIS_TURN_ATTACK_AFTER
	var vmax := deg_to_rad(Tuning.VIS_TURN_ATTACK_DEG if slow else Tuning.VIS_TURN_DEG)
	var acc := deg_to_rad(Tuning.VIS_TURN_ACCEL)
	var want := signf(rem) * minf(vmax, sqrt(2.0 * acc * absf(rem)))
	_vis_yaw_vel = move_toward(_vis_yaw_vel, want, acc * delta)
	var step := _vis_yaw_vel * delta
	if absf(rem) < 0.001 or (signf(step) == signf(rem) and absf(step) >= absf(rem)):
		_vis_yaw = _vis_yaw_target
		_vis_yaw_vel = 0.0
	else:
		_vis_yaw = wrapf(_vis_yaw + step, -PI, PI)
	visual.rotation.y = _vis_yaw


## Plays a locomotion clip (cross-fade on change) at ground speed / manifest move_speed, clamped to
## [ANIM_SPEED_MIN, ANIM_SPEED_MAX]. A finishing one-shot (block_end) is left to end while the hero stands still.
func _anim_loco(clip: StringName) -> void:
	if clip == &"strafe_r" and not visual.has_clip(&"strafe_r"):
		clip = &"strafe_l"
	if clip == &"idle" and _clock < _hold_until:
		return
	var ms := visual.move_speed(clip)
	var spd := clampf(_loco_speed / ms, Tuning.ANIM_SPEED_MIN, Tuning.ANIM_SPEED_MAX) if ms > 0.01 and _loco_speed > 0.01 else 1.0
	if clip != _clip:
		_clip = clip
		# the play speed goes in with the clip so the cross-fade lasts its real seconds (CharacterVisual.play); out of
		# an action (strike, flinch, roll, lowering the shield) the settle is longer than a change of gait
		var from := visual.current_clip
		var settle := not from in [&"idle", &"run", &"strafe_l", &"strafe_r", &"walk_back"]
		visual.play(clip, Tuning.SETTLE_BLEND if settle else (Tuning.IDLE_BLEND if clip == &"idle" else Tuning.GAIT_BLEND), spd)
	elif ms > 0.01 and _loco_speed > 0.01:
		visual.set_speed(spd)


## Footsteps on the locomotion clip's beat (two per cycle). Surface from the scene id: marble at the sanctuary
## (step_stone), packed earth / basalt / grass everywhere else (step_dirt).
func _footsteps(delta: float, inp: Vector2) -> void:
	if inp.length() <= 0.1 or not is_on_floor():
		_step_t = 0.2                    # the first step lands ~0.15 s after the hero starts moving
		return
	var beat := visual.clip_length(_clip, 0.7) * 0.5 / maxf(absf(visual.get_speed()), 0.3)
	_step_t += delta
	if _step_t >= beat:
		_step_t = fmod(_step_t - beat, beat)
		Sfx.play("step_stone" if Game.scene_id == &"medusa" else "step_dirt", global_position, 0.0 if inp.length() > 0.6 else -4.0)
