extends Control
## Scene id "ending" (world module; Game.BUILDERS prefers this file over core's ending_card.gd). Shown once, after
## the Hydra falls the first time (ArenaBase routes here, or the sea scene does when the card is still pending).
## The card fades in line by line; accept (or a few seconds) continues to free flight over the sea.

const HOLD := 11.0                 ## seconds before it moves on by itself (harness: HOLD_HARNESS)
const HOLD_HARNESS := 3.0

var opts: Dictionary = {}
var _lines: Array[Control] = []
var _t := 0.0
var _hold := HOLD
var _done := false
var _prompt: Label


## Called by Game before the scene enters the tree.
func setup(o: Dictionary) -> void:
	opts = o


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_hold = HOLD_HARNESS if Game.harness else HOLD
	var bg := ColorRect.new()
	bg.color = Color(0.05, 0.05, 0.09)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var glow := _Glow.new()
	glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(glow)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.offset_left = -820
	v.offset_right = 820
	v.offset_top = -330
	v.offset_bottom = 330
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 18)
	add_child(v)
	var band := UiStyle.KeyBand.new()
	band.custom_minimum_size = Vector2(0, 34)
	v.add_child(band)
	_add(v, UiStyle.label("The three labors are done.", 70, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	_add(v, UiStyle.label("The giant, the gorgon and the nine-headed serpent have fallen.", 30, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 24)
	v.add_child(gap)
	_add(v, UiStyle.label("Design and direction  -  JC", 28, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	_add(v, UiStyle.label("Built with Claude", 28, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	_add(v, UiStyle.label("3D models, images and animation references generated on Higgsfield", 26, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
	var band2 := UiStyle.KeyBand.new()
	band2.custom_minimum_size = Vector2(0, 34)
	v.add_child(band2)
	_prompt = UiStyle.label("", 26, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER)
	_add(v, _prompt)
	_refresh_prompt()
	Controls.device_changed.connect(func(_p: bool): _refresh_prompt())
	Sfx.play_music("music_title")
	Sfx.play("victory")
	Game.mark_ending_seen()
	Game.event("ending_shown", {"from": String(opts.get("from", "hydra"))})


func _add(parent: Control, c: Control) -> void:
	c.modulate.a = 0.0
	parent.add_child(c)
	_lines.append(c)


func _refresh_prompt() -> void:
	if _prompt != null:
		_prompt.text = Controls.fill("{interact} Take to the sky")


func _process(delta: float) -> void:
	_t += delta
	for i in _lines.size():
		var start := 0.25 + 0.32 * float(i)
		_lines[i].modulate.a = clampf((_t - start) / 0.6, 0.0, 1.0)
	if _done:
		return
	if _t > 1.0 and (Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact")):
		_continue()
	elif _t >= _hold:
		_continue()


func _continue() -> void:
	_done = true
	Sfx.play("ui_accept")
	Game.goto(&"sea", {"from": String(opts.get("from", "hydra")), "free_flight": true})


## A soft warm glow behind the text and a slow drifting ring of light (no texture assets needed).
class _Glow extends Control:
	var _t := 0.0

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()

	func _draw() -> void:
		var c := size * 0.5
		for i in 12:
			var k := float(i) / 12.0
			draw_circle(c, size.y * (0.62 - k * 0.45), Color(0.55, 0.36, 0.14, 0.035))
		var r := size.y * 0.42 + sin(_t * 0.7) * 8.0
		draw_arc(c, r, 0.0, TAU, 96, Color(0.95, 0.76, 0.34, 0.18), 3.0, true)
		draw_arc(c, r + 14.0, _t * 0.2, _t * 0.2 + PI * 1.2, 64, Color(0.95, 0.76, 0.34, 0.10), 2.0, true)
