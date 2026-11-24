extends Node
## Test bot. mode "win": drives the game through the real input actions; "lose": stands still; "idle": does nothing.
## Runs before the player each physics frame. Input goes out three ways: Input.action_press (default), synthetic
## joypad events (use_pad, `--pad`) or synthetic keyboard / mouse events (use_keys, `--keys`, exercises the keyboard
## bindings and the switch back to keyboard prompts).
##
## Who advises the bot:
##  1. a fighting boss: `boss.bot_advice()` (SPEC §7.1: move_to, face, roll, block, attack);
##  2. otherwise the first node in group "bot_advisor" with bot_advice(), else `Game.world.bot_advice()` (home, sea,
##     any scene). Generic advice dictionary, every key optional:
##       stick: Vector2   left stick as a player would push it (x right, y back/down; length <= 1)
##       move_to: Vector3 walk there (needs a Player: converted to a stick through its camera; ignored if `stick` given)
##       face: Vector3    when not locked on and not moving: turn toward it (a short stick nudge)
##       look: Vector2    right stick (camera)
##       interact, roll, attack, lock_on: bool  tapped (with a cooldown)
##       block, boost: bool                     held while true
##       accept: bool     tap ui_accept (menus, e.g. the title screen): Enter with --keys, pad A with --pad,
##                        else an InputEventAction

var mode := "win"
var use_pad := false
var use_keys := false
var _held := {}            # action -> true while held
var _tap_release := {}     # action -> physics frames left before release
var _cd := {}              # action -> seconds before it may be tapped again
var _stick := Vector2.ZERO
var _look := Vector2.ZERO
var _keys_down := {}       # keycode -> true (keys mode movement)

const PAD_BUTTONS := {"roll": JOY_BUTTON_B, "attack": JOY_BUTTON_RIGHT_SHOULDER, "shield": JOY_BUTTON_LEFT_SHOULDER, "lock_on": JOY_BUTTON_RIGHT_STICK, "interact": JOY_BUTTON_A}
const PAD_AXES := {"boost": JOY_AXIS_TRIGGER_RIGHT}
const KEY_BUTTONS := {"roll": KEY_SPACE, "lock_on": KEY_Q, "interact": KEY_E, "boost": KEY_SHIFT}
const MOUSE_BUTTONS := {"attack": MOUSE_BUTTON_LEFT, "shield": MOUSE_BUTTON_RIGHT}
const COOLDOWN := {"roll": 0.9, "attack": 0.22, "lock_on": 1.0, "interact": 0.5, "accept": 1.5}


func _ready() -> void:
	process_physics_priority = -100
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _physics_process(delta: float) -> void:
	for a in _cd.keys():
		_cd[a] -= delta
	for a in _tap_release.keys():
		_tap_release[a] -= 1
		if _tap_release[a] <= 0:
			_tap_release.erase(a)
			_set_button(a, false)
	if mode == "idle":
		return
	if mode == "lose":
		_release_all()
		return
	var p := Game.player()
	var boss := _fighting_boss(p)
	if boss != null:
		if p.state == &"dead":
			_release_all()
			return
		_follow_boss(p, boss)
		return
	var adv := _world_advice()
	if adv.is_empty():
		_release_all()
		return
	_follow_generic(p, adv)


## The boss to fight (the lock target, else any boss in the tree), or null when none is fighting.
func _fighting_boss(p: Player) -> BossBase:
	if p == null:
		return null
	var boss: BossBase = p.lock_target
	if boss == null:
		for b in get_tree().get_nodes_in_group("boss"):
			boss = b
			break
	if boss == null or not is_instance_valid(boss) or not boss.fighting:
		return null
	return boss


## Advice from a "bot_advisor" node or the current scene node, or {} when nobody advises.
func _world_advice() -> Dictionary:
	for n in get_tree().get_nodes_in_group("bot_advisor"):
		if n.has_method("bot_advice"):
			var a = n.bot_advice()
			if a is Dictionary:
				return a
	var w := Game.world
	if w != null and is_instance_valid(w) and w.has_method("bot_advice"):
		var a2 = w.bot_advice()
		if a2 is Dictionary:
			return a2
	return {}


func _follow_boss(p: Player, boss: BossBase) -> void:
	if not p.locked:
		_tap("lock_on")
	var adv := boss.bot_advice()
	_set_look(Vector2.ZERO)
	_set_button("boost", false)
	var stick := _stick_to(p, adv.get("move_to", p.global_position))
	stick = _face_nudge(p, adv, stick)
	_set_stick(stick)
	var block := bool(adv.get("block", false))
	_set_button("shield", block)
	if bool(adv.get("roll", false)) and not block:
		_tap("roll")
	elif bool(adv.get("attack", false)) and not block:
		_tap("attack")


func _follow_generic(p: Player, adv: Dictionary) -> void:
	var stick := Vector2.ZERO
	if adv.has("stick"):
		stick = adv["stick"]
	elif adv.has("move_to") and p != null:
		stick = _stick_to(p, adv["move_to"])
	if p != null:
		stick = _face_nudge(p, adv, stick)
	_set_stick(stick.limit_length(1.0))
	_set_look(adv.get("look", Vector2.ZERO))
	var block := bool(adv.get("block", false))
	_set_button("shield", block)
	_set_button("boost", bool(adv.get("boost", false)))
	for a in ["interact", "lock_on", "accept"]:
		if bool(adv.get(a, false)):
			_tap(a)
	if bool(adv.get("roll", false)) and not block:
		_tap("roll")
	elif bool(adv.get("attack", false)) and not block:
		_tap("attack")


## Stick vector (x right, y back) that walks the player toward `target`, relative to its camera.
func _stick_to(p: Player, target: Vector3) -> Vector2:
	var to: Vector3 = target - p.global_position
	to.y = 0.0
	if to.length() <= 0.6:
		return Vector2.ZERO
	var want := to.normalized() * clampf(to.length() / 1.5, 0.4, 1.0)
	return _world_to_stick(p, want)


func _world_to_stick(p: Player, want: Vector3) -> Vector2:
	var yaw := p.camera.yaw if p.camera != null else 0.0
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	var right := Vector3(cos(yaw), 0, -sin(yaw))
	return Vector2(want.dot(right), -want.dot(fwd))


## SPEC `face`: when free (not locked) and not moving, nudge the stick toward the face point so the hero turns to it.
func _face_nudge(p: Player, adv: Dictionary, stick: Vector2) -> Vector2:
	if p.locked or stick.length() > 0.05 or not adv.has("face"):
		return stick
	var to: Vector3 = adv["face"] - p.global_position
	to.y = 0.0
	if to.length() < 0.3 or rad_to_deg(p.facing.angle_to(to.normalized())) < 12.0:
		return stick
	return _world_to_stick(p, to.normalized() * 0.3)


func _release_all() -> void:
	_set_stick(Vector2.ZERO)
	_set_look(Vector2.ZERO)
	_set_button("shield", false)
	_set_button("boost", false)


func _tap(action: String) -> void:
	if float(_cd.get(action, 0.0)) > 0.0 or _tap_release.has(action):
		return
	_cd[action] = COOLDOWN.get(action, 0.3)
	_set_button(action, true)
	_tap_release[action] = 2


func _set_button(action: String, on: bool) -> void:
	if action == "accept":
		_send_accept(on)
		return
	# skip only when both the bot and Input agree (Game releases buttons on resume / scene change)
	if bool(_held.get(action, false)) == on and Input.is_action_pressed(action) == on:
		return
	_held[action] = on
	if use_pad:
		if PAD_AXES.has(action):
			var m := InputEventJoypadMotion.new()
			m.device = 0
			m.axis = PAD_AXES[action]
			m.axis_value = 1.0 if on else 0.0
			Input.parse_input_event(m)
			return
		var e := InputEventJoypadButton.new()
		e.device = 0
		e.button_index = PAD_BUTTONS[action]
		e.pressed = on
		e.pressure = 1.0 if on else 0.0
		Input.parse_input_event(e)
	elif use_keys:
		if MOUSE_BUTTONS.has(action):
			var mb := InputEventMouseButton.new()
			mb.button_index = MOUSE_BUTTONS[action]
			mb.pressed = on
			Input.parse_input_event(mb)
		else:
			_key(KEY_BUTTONS[action], on)
	elif on:
		Input.action_press(action)
	else:
		Input.action_release(action)


## Menu accept (ui_accept) as the device in use would send it.
func _send_accept(on: bool) -> void:
	if bool(_held.get("accept", false)) == on:
		return
	_held["accept"] = on
	if use_pad:
		var e := InputEventJoypadButton.new()
		e.device = 0
		e.button_index = JOY_BUTTON_A
		e.pressed = on
		e.pressure = 1.0 if on else 0.0
		Input.parse_input_event(e)
	elif use_keys:
		_key(KEY_ENTER, on)
	else:
		var a := InputEventAction.new()
		a.action = &"ui_accept"
		a.pressed = on
		Input.parse_input_event(a)


func _key(code: Key, on: bool) -> void:
	if bool(_keys_down.get(code, false)) == on:
		return
	_keys_down[code] = on
	var k := InputEventKey.new()
	k.keycode = code
	k.physical_keycode = code
	k.pressed = on
	Input.parse_input_event(k)


func _set_stick(v: Vector2) -> void:
	if v.distance_to(_stick) < 0.02:
		return
	_stick = v
	if use_pad:
		for axis in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y]:
			var e := InputEventJoypadMotion.new()
			e.device = 0
			e.axis = axis
			e.axis_value = v.x if axis == JOY_AXIS_LEFT_X else v.y
			Input.parse_input_event(e)
		return
	if use_keys:
		# WASD are digital: a component past 0.3 holds its key (diagonals = two keys)
		_key(KEY_D, v.x > 0.3)
		_key(KEY_A, v.x < -0.3)
		_key(KEY_S, v.y > 0.3)
		_key(KEY_W, v.y < -0.3)
		return
	_axis("move_right", "move_left", v.x)
	_axis("move_back", "move_forward", v.y)


func _set_look(v: Vector2) -> void:
	if v.distance_to(_look) < 0.02:
		return
	_look = v
	if use_pad:
		for axis in [JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y]:
			var e := InputEventJoypadMotion.new()
			e.device = 0
			e.axis = axis
			e.axis_value = v.x if axis == JOY_AXIS_RIGHT_X else v.y
			Input.parse_input_event(e)
		return
	_axis("cam_right", "cam_left", v.x)     # keyboard has no camera keys: the actions are pressed directly
	_axis("cam_down", "cam_up", v.y)


func _axis(pos_action: String, neg_action: String, value: float) -> void:
	if value > 0.0:
		Input.action_press(pos_action, value)
		Input.action_release(neg_action)
	elif value < 0.0:
		Input.action_press(neg_action, -value)
		Input.action_release(pos_action)
	else:
		Input.action_release(pos_action)
		Input.action_release(neg_action)
