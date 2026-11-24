extends Control
## Title screen (scene id "title"): New game, Continue, Controls, Quit over a painted sea-and-sky backdrop.
## Pages opened over the menu (Controls, the New game confirmation) are modal: the menu buttons lose their focus
## mode while a page is open, so D-pad / arrows can never reach a button hidden behind it.

var _menu: VBoxContainer
var _first: Button
var _cont: Button
var _t := 0.0
var _page_open := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := Backdrop.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.offset_left = -520
	v.offset_right = 520
	v.offset_top = -380
	v.offset_bottom = 420
	v.add_theme_constant_override("separation", 14)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(v)
	var band := UiStyle.KeyBand.new()
	band.unit = 10.0
	band.custom_minimum_size = Vector2(0, 40)
	v.add_child(band)
	v.add_child(UiStyle.label("HERCULES", 150, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(UiStyle.label("Three labors beyond the wine-dark sea", 34, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	var band2 := UiStyle.KeyBand.new()
	band2.unit = 10.0
	band2.custom_minimum_size = Vector2(0, 40)
	v.add_child(band2)
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 30)
	v.add_child(spacer)
	_menu = VBoxContainer.new()
	_menu.add_theme_constant_override("separation", 10)
	_menu.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(_menu)
	_cont = _add("Continue", func(): Game.goto(&"home"))
	_cont.disabled = not Game.has_save()
	var newg := _add("New game", _on_new_game)
	_add("Controls", _show_controls)
	_add("Quit", func(): Game.quit_game())
	if _cont.disabled:
		_menu.move_child(_cont, 1)
		_first = newg
	else:
		_first = _cont
	for b in _menu.get_children():
		(b as Button).size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_set_menu_focus(true)
	_first.grab_focus.call_deferred()
	var hint := UiStyle.label("", 22, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER)
	hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	hint.offset_left = -600
	hint.offset_right = 600
	hint.offset_top = -60
	hint.offset_bottom = -24
	hint.text = "Keyboard + mouse or Xbox controller"
	add_child(hint)
	Sfx.play_music("music_title")
	Game.event("title_ready", {"continue": not _cont.disabled})


func _add(text: String, cb: Callable) -> Button:
	var b := UiStyle.button(text)
	b.pressed.connect(cb)
	_menu.add_child(b)
	return b


## Menu buttons focusable (on) or not (a page is open). A disabled Continue (no save) never takes the focus.
func _set_menu_focus(on: bool) -> void:
	for b in _menu.get_children():
		var btn := b as Button
		btn.focus_mode = Control.FOCUS_ALL if on and not btn.disabled else Control.FOCUS_NONE
		btn.mouse_filter = Control.MOUSE_FILTER_STOP if on else Control.MOUSE_FILTER_IGNORE


func _open_page(page: Control) -> void:
	_page_open = true
	_set_menu_focus(false)
	add_child(page)


func _page_closed() -> void:
	_page_open = false
	_set_menu_focus(true)
	_first.grab_focus()


func _show_controls() -> void:
	if _page_open:
		return
	var page := ControlsPage.new()
	page.closed.connect(_page_closed)
	_open_page(page)


func _on_new_game() -> void:
	if _page_open:
		return
	if not Game.new_game_needs_confirm():
		Game.new_game()
		return
	var page := ConfirmPage.new()
	page.closed.connect(func(start_over: bool):
		Game.event("new_game_confirm", {"start_over": start_over})
		if start_over:
			Game.new_game()
		else:
			_page_closed())
	_open_page(page)
	Game.event("new_game_asked")


## The bot (harness --bot=win from the title) presses accept once the menu has settled: Continue when there is a
## save, else New game (the focused button).
func bot_advice() -> Dictionary:
	if _page_open or _t < 1.0:
		return {}
	return {"accept": true}


func _process(delta: float) -> void:
	_t += delta


## "Start over?" confirmation for New game when a save has progress. Keep my progress is focused; B / Esc keeps.
class ConfirmPage extends Control:
	signal closed(start_over: bool)
	var _keep: Button
	var _done := false

	func _ready() -> void:
		set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		var dim := ColorRect.new()
		dim.color = Color(0, 0, 0, 0.72)
		dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		add_child(dim)
		var panel := PanelContainer.new()
		panel.add_theme_stylebox_override("panel", UiStyle.panel_box(0.94))
		panel.set_anchors_preset(Control.PRESET_CENTER)
		panel.offset_left = -480
		panel.offset_right = 480
		panel.offset_top = -200
		panel.offset_bottom = 200
		add_child(panel)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 16)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		panel.add_child(v)
		v.add_child(UiStyle.label("START OVER?", 52, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
		var band := UiStyle.KeyBand.new()
		band.custom_minimum_size = Vector2(0, 28)
		v.add_child(band)
		var msg := UiStyle.label("Your beaten labors will be forgotten.", 30, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
		v.add_child(msg)
		_keep = UiStyle.button("Keep my progress")
		_keep.name = "Keep"
		_keep.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		_keep.pressed.connect(func(): _finish(false))
		v.add_child(_keep)
		var over := UiStyle.button("Start over")
		over.name = "Over"
		over.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		over.pressed.connect(func(): _finish(true))
		v.add_child(over)
		# focus stays inside the two buttons
		var kp := NodePath("../" + String(over.name))
		var op := NodePath("../" + String(_keep.name))
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			_keep.set_focus_neighbor(side, kp)
			over.set_focus_neighbor(side, op)
		_keep.focus_next = kp
		_keep.focus_previous = kp
		over.focus_next = op
		over.focus_previous = op
		_keep.grab_focus.call_deferred()

	func _finish(start_over: bool) -> void:
		if _done:
			return
		_done = true
		if not start_over:
			Sfx.play("ui_back")
		closed.emit(start_over)
		queue_free()

	func _unhandled_input(e: InputEvent) -> void:
		if e.is_action_pressed("ui_cancel") or e.is_action_pressed("pause"):
			get_viewport().set_input_as_handled()
			_finish(false)


## Painted backdrop: sky gradient (smooth, dithered in a shader: the old 24 drawn steps showed bands), sun, layered
## sea bands, a distant island silhouette.
class Backdrop extends Control:
	const SKY_SHADER := """
shader_type canvas_item;
uniform float horizon = 0.62;
uniform vec3 top_col = vec3(0.20, 0.38, 0.70);
uniform vec3 low_col = vec3(0.98, 0.80, 0.55);
void fragment() {
	float k = clamp(UV.y / horizon, 0.0, 1.0);
	vec3 c = mix(top_col, low_col, pow(k, 1.6));
	// triangular dither of +-1 code value hides 8-bit steps
	float n1 = fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453);
	float n2 = fract(sin(dot(FRAGCOORD.xy + 17.17, vec2(39.3468, 11.135))) * 24634.6345);
	c += (n1 + n2 - 1.0) / 255.0;
	COLOR = vec4(c, 1.0);
}
"""
	var _t := 0.0

	func _ready() -> void:
		var sky := ColorRect.new()
		sky.mouse_filter = Control.MOUSE_FILTER_IGNORE
		sky.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		sky.show_behind_parent = true
		var sh := Shader.new()
		sh.code = SKY_SHADER
		var m := ShaderMaterial.new()
		m.shader = sh
		sky.material = m
		add_child(sky)

	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()

	func _draw() -> void:
		var w := size.x
		var h := size.y
		var hz := h * 0.62
		draw_circle(Vector2(w * 0.72, hz * 0.78), h * 0.09, Color(1.0, 0.88, 0.6))
		draw_circle(Vector2(w * 0.72, hz * 0.78), h * 0.12, Color(1.0, 0.88, 0.6, 0.25))
		var isl := PackedVector2Array([Vector2(w * 0.05, hz), Vector2(w * 0.12, hz - h * 0.07), Vector2(w * 0.2, hz - h * 0.11),
			Vector2(w * 0.27, hz - h * 0.06), Vector2(w * 0.34, hz)])
		draw_colored_polygon(isl, Color(0.32, 0.30, 0.38))
		for i in 6:
			var y := hz + (h - hz) * float(i) / 6.0
			var c2 := Color(0.16, 0.42, 0.62).lerp(Color(0.05, 0.18, 0.32), float(i) / 6.0)
			draw_rect(Rect2(0, y, w, (h - hz) / 6.0 + 1.0), c2)
			var off := fmod(_t * (12.0 + i * 6.0), 160.0)
			var x := -160.0 + off
			while x < w:
				draw_line(Vector2(x, y + 6), Vector2(x + 50.0 + i * 8.0, y + 6), Color(0.9, 0.96, 1.0, 0.35), 2.0)
				x += 160.0 + i * 20.0
