extends Node
## Autoload `Controls`: which device is in use (keyboard+mouse or Xbox pad), button names for prompts, stick reading
## with a dead zone, menu repeat for a held D-pad / stick, menu navigation on the left stick, vibration.

signal device_changed(using_pad: bool)

const PAD_NAMES := {
	"move": "Left stick", "camera": "Right stick", "roll": "B", "attack": "RB", "shield": "LB", "lock_on": "R3",
	"interact": "A", "boost": "RT", "pause": "Start", "accept": "A", "back": "B",
}
const KEY_NAMES := {
	"move": "WASD", "camera": "Mouse", "roll": "Space", "attack": "LMB", "shield": "RMB", "lock_on": "Q",
	"interact": "E", "boost": "Shift", "pause": "Esc", "accept": "Enter", "back": "Esc",
}
const STICK_SWITCH := 0.35
const MOUSE_SWITCH := 8.0
const REPEAT_DELAY := 0.4
const REPEAT_RATE := 0.09
const _REPEAT := {
	"ui_up": [JOY_BUTTON_DPAD_UP, JOY_AXIS_LEFT_Y, -1.0],
	"ui_down": [JOY_BUTTON_DPAD_DOWN, JOY_AXIS_LEFT_Y, 1.0],
	"ui_left": [JOY_BUTTON_DPAD_LEFT, JOY_AXIS_LEFT_X, -1.0],
	"ui_right": [JOY_BUTTON_DPAD_RIGHT, JOY_AXIS_LEFT_X, 1.0],
}

var using_pad := false
var pad_device := 0
var _mouse_travel := 0.0
var _ignore_mouse_ms := 0
var _repeat_action := ""
var _repeat_t := 0.0
var _rumble_until := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_ui_stick()
	var pads := Input.get_connected_joypads()
	if not pads.is_empty():
		pad_device = pads[0]
	Input.joy_connection_changed.connect(_on_joy_connection)


## Menus: A accepts and B goes back on every pad; the left stick also moves the focus (D-pad and arrows already do).
func _ensure_ui_stick() -> void:
	for pair in [["ui_accept", JOY_BUTTON_A], ["ui_cancel", JOY_BUTTON_B]]:
		var b := InputEventJoypadButton.new()
		b.device = -1
		b.button_index = pair[1]
		if InputMap.has_action(pair[0]) and not InputMap.action_has_event(pair[0], b):
			InputMap.action_add_event(pair[0], b)
	for a in _REPEAT:
		var r: Array = _REPEAT[a]
		var m := InputEventJoypadMotion.new()
		m.device = -1
		m.axis = r[1]
		m.axis_value = r[2]
		if InputMap.has_action(a) and not InputMap.action_has_event(a, m):
			InputMap.action_add_event(a, m)


# ------------------------------------------------------------------ prompt names
## The button name for an action on the device in use ("B" / "Space").
func key(action: String) -> String:
	return str((PAD_NAMES if using_pad else KEY_NAMES).get(action, action))


## The button name in brackets: "[B]".
func tag(action: String) -> String:
	return "[%s]" % key(action)


## Replaces {action} placeholders: "Mount {interact}" -> "Mount [A]".
func fill(text: String) -> String:
	if not "{" in text:
		return text
	var out := text
	for a in KEY_NAMES:
		out = out.replace("{%s}" % a, tag(a))
	return out


## Rows of [action label, keyboard/mouse, Xbox] for the controls pages.
func control_rows() -> Array:
	return [
		["Move", "WASD", "Left stick"], ["Camera", "Mouse", "Right stick"], ["Roll", "Space", "B"],
		["Attack", "Left mouse", "RB / X"], ["Shield (hold)", "Right mouse", "LB"], ["Lock-on", "Q / Middle mouse", "R3"],
		["Interact / mount / land", "E", "A"], ["Boost (flight)", "Shift", "RT"], ["Pause", "Esc", "Start"],
	]


# ------------------------------------------------------------------ reading input
## Movement stick / WASD as a Vector2 (x right, y back), dead zone applied, length <= 1.
func get_move() -> Vector2:
	return Input.get_vector("move_left", "move_right", "move_forward", "move_back", Tuning.STICK_DEADZONE)


## Right-stick camera input (x right, y down), dead zone applied.
func get_look_stick() -> Vector2:
	return Input.get_vector("cam_left", "cam_right", "cam_up", "cam_down", Tuning.STICK_DEADZONE)


# ------------------------------------------------------------------ device tracking
func _input(event: InputEvent) -> void:
	if event is InputEventJoypadButton:
		if event.pressed:
			pad_device = event.device
			_set_pad(true)
	elif event is InputEventJoypadMotion:
		if absf(event.axis_value) > STICK_SWITCH:
			pad_device = event.device
			_set_pad(true)
	elif event is InputEventKey or event is InputEventMouseButton:
		if event.pressed:
			_set_pad(false)
	elif event is InputEventMouseMotion:
		if Time.get_ticks_msec() < _ignore_mouse_ms:
			return
		_mouse_travel += event.relative.length()
		if _mouse_travel > MOUSE_SWITCH:
			_set_pad(false)


func _set_pad(on: bool) -> void:
	_mouse_travel = 0.0
	if on == using_pad:
		return
	using_pad = on
	device_changed.emit(on)
	Game.event("device", {"pad": on})


## Mouse-mode changes go through here so the warp they cause does not count as mouse use.
func set_mouse_mode(mode: Input.MouseMode) -> void:
	if Input.mouse_mode == mode or DisplayServer.get_name() == "headless":
		return
	Input.mouse_mode = mode
	_ignore_mouse_ms = Time.get_ticks_msec() + 300


func _process(delta: float) -> void:
	_mouse_travel = maxf(0.0, _mouse_travel - delta * 40.0)
	_update_repeat(delta)
	if _rumble_until > 0 and Time.get_ticks_msec() > _rumble_until:
		Input.stop_joy_vibration(pad_device)
		_rumble_until = 0


## Godot repeats held keys but not held pad buttons: repeat a held D-pad / stick direction while a menu has focus.
func _update_repeat(delta: float) -> void:
	var held := ""
	if using_pad and get_viewport().gui_get_focus_owner() != null:
		for a in _REPEAT:
			var r: Array = _REPEAT[a]
			if Input.is_joy_button_pressed(pad_device, r[0]) or Input.get_joy_axis(pad_device, r[1]) * float(r[2]) > 0.6:
				held = a
				break
	if held != _repeat_action:
		_repeat_action = held
		_repeat_t = REPEAT_DELAY
		return
	if held == "":
		return
	_repeat_t -= delta
	if _repeat_t <= 0.0:
		_repeat_t = REPEAT_RATE
		for pressed in [true, false]:
			var e := InputEventAction.new()
			e.action = held
			e.pressed = pressed
			Input.parse_input_event(e)


## Short controller vibration (weak, strong motor 0..1) when the pad is in use.
func rumble(weak: float, strong: float, seconds: float) -> void:
	if not using_pad:
		return
	Input.start_joy_vibration(pad_device, weak, strong, seconds)
	_rumble_until = Time.get_ticks_msec() + int(seconds * 1000.0)


func _on_joy_connection(device: int, connected: bool) -> void:
	if connected:
		pad_device = device
		return
	if device == pad_device and using_pad:
		_set_pad(false)
		# a controller dropping out mid-fight pauses the game
		if not get_tree().paused and not String(Game.scene_id) in Game.NOT_PAUSABLE:
			Game.set_paused(true)
