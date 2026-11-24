extends CanvasLayer
## Pause menu (created by Game.set_paused): Resume, Controls, Restart fight (arenas), Return home, Quit to title.
## Start / Esc / B resumes. B (ui_cancel) closes on its RELEASE: pad B is also `roll`, and closing on the press let
## the same press reach the player in the first unpaused frame (probe_pad.log: resumed, then roll at once). The press
## lands while the tree is paused, so the player never sees it. Buttons (Resume, A) already act on release.

var _first: Button
var _box: VBoxContainer
var _page: Control = null
var _cancel_armed := false
var _leaving := false


func _ready() -> void:
	layer = 60
	process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box(0.92))
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_left = -300
	panel.offset_right = 300
	panel.offset_top = -330
	panel.offset_bottom = 330
	add_child(panel)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 12)
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	panel.add_child(_box)
	_box.add_child(UiStyle.label("PAUSED", 56, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	var band := UiStyle.KeyBand.new()
	band.custom_minimum_size = Vector2(0, 28)
	_box.add_child(band)
	_first = _add("Resume", func(): Game.set_paused(false))
	_add("Controls", _show_controls)
	if Game.world is ArenaBase:
		_add("Restart fight", func(): _leave(Game.scene_id, {"restart": true}))
	_add("Return home", func(): _leave(&"home"))
	_add("Quit to title", func(): _leave(&"title"))
	_first.grab_focus.call_deferred()


## Leaves the scene with the tree still PAUSED: the menu hides, the fade-out runs (Game's tweens process while
## paused) and Game._switch() unpauses. Unpausing first let the boss keep attacking behind the 0.35 s fade (QA).
func _leave(id: StringName, opts := {}) -> void:
	if _leaving:
		return
	_leaving = true
	for b in _box.get_children():
		if b is Button:
			(b as Button).disabled = true
	visible = false
	Game.goto(id, opts)


func _add(text: String, cb: Callable) -> Button:
	var b := UiStyle.button(text)
	b.custom_minimum_size = Vector2(480, 60)
	b.pressed.connect(cb)
	_box.add_child(b)
	return b


func _show_controls() -> void:
	_page = ControlsPage.new()
	add_child(_page)
	_page.closed.connect(func(): _page = null; _first.grab_focus())


func _unhandled_input(e: InputEvent) -> void:
	if _page != null or _leaving:
		return
	if e.is_action_pressed("pause"):
		get_viewport().set_input_as_handled()
		_close()
	elif e.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_cancel_armed = true
	elif e.is_action_released("ui_cancel") and _cancel_armed:
		get_viewport().set_input_as_handled()
		_close()


func _close() -> void:
	Sfx.play("ui_back")
	Game.set_paused(false)
