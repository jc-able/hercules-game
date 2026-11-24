extends Control
## Ending card (scene id "ending", after the Hydra): a few lines, then free flight over the sea.

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = Color(0.06, 0.05, 0.08)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.offset_left = -800
	v.offset_right = 800
	v.offset_top = -300
	v.offset_bottom = 300
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 20)
	add_child(v)
	var band := UiStyle.KeyBand.new()
	band.custom_minimum_size = Vector2(0, 36)
	v.add_child(band)
	v.add_child(UiStyle.label("THE THREE LABORS ARE DONE", 72, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(UiStyle.label("The giant, the gorgon and the nine-headed serpent have fallen.", 30, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(UiStyle.label("The sea is yours. Fly where you like.", 30, UiStyle.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
	var band2 := UiStyle.KeyBand.new()
	band2.custom_minimum_size = Vector2(0, 36)
	v.add_child(band2)
	var b := UiStyle.button("Take to the sky")
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(func(): Game.goto(&"sea", {"from": "hydra", "free_flight": true}))
	v.add_child(b)
	b.grab_focus.call_deferred()
	Sfx.play_music("music_title")   # the main theme returns (the registry has no separate ending track)
	Game.mark_ending_seen()
	Game.event("ending_shown")
