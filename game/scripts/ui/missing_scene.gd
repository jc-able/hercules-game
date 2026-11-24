extends Control
## Shown when a scene id has no builder script yet (the module has not landed): explains and offers a way back.

var _id := ""
var _path := ""


func setup(opts: Dictionary) -> void:
	_id = str(opts.get("id", "?"))
	_path = str(opts.get("path", ""))


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = Color(0.08, 0.07, 0.06)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.offset_left = -700
	v.offset_right = 700
	v.offset_top = -200
	v.offset_bottom = 200
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 18)
	add_child(v)
	v.add_child(UiStyle.label("This place is not built yet", 56, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(UiStyle.label("Scene '%s' needs %s" % [_id, _path if _path != "" else "a builder in Game.BUILDERS"], 26, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
	var b := UiStyle.button("Back to title")
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(func(): Game.goto(&"title"))
	v.add_child(b)
	b.grab_focus.call_deferred()
