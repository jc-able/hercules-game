class_name ControlsPage
extends Control
## Full-screen controls table (keyboard/mouse and Xbox side by side). B / Esc / Back button closes it.

signal closed

var _back: Button


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.72)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box(0.92))
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_left = -560
	panel.offset_right = 560
	panel.offset_top = -400
	panel.offset_bottom = 400
	add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	panel.add_child(v)
	v.add_child(UiStyle.label("CONTROLS", 52, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	var band := UiStyle.KeyBand.new()
	band.custom_minimum_size = Vector2(0, 30)
	v.add_child(band)
	var g := GridContainer.new()
	g.columns = 3
	g.add_theme_constant_override("h_separation", 40)
	g.add_theme_constant_override("v_separation", 8)
	v.add_child(g)
	for h in ["Action", "Keyboard + mouse", "Xbox controller"]:
		g.add_child(UiStyle.label(h, 26, UiStyle.GOLD_DIM))
	for row in Controls.control_rows():
		g.add_child(UiStyle.label(row[0], 26, UiStyle.TEXT))
		g.add_child(UiStyle.label(row[1], 26, UiStyle.TEXT_DIM))
		g.add_child(UiStyle.label(row[2], 26, UiStyle.TEXT_DIM))
	v.add_child(UiStyle.label("Menus: A accept, B back, D-pad / left stick to move", 22, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
	_back = UiStyle.button("Back")
	_back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_back.pressed.connect(close)
	v.add_child(_back)
	# modal focus: every direction / Tab from Back stays on Back, so D-pad up can never reach the buttons hidden
	# behind the page (QA: on the title it focused an invisible button and A then started a new game)
	var self_path := NodePath(".")
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
		_back.set_focus_neighbor(side, self_path)
	_back.focus_next = self_path
	_back.focus_previous = self_path
	_back.grab_focus.call_deferred()


## Closes the page and emits `closed`.
func close() -> void:
	Sfx.play("ui_back")
	closed.emit()
	queue_free()


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("ui_cancel") or e.is_action_pressed("pause"):
		get_viewport().set_input_as_handled()
		close()
