class_name Hud
extends CanvasLayer
## In-game HUD (SPEC §5): hero health top-left, boss name + bar bottom centre, lock-on reticle, device-aware prompts,
## island title card, big overlays ("LABOR COMPLETE" / "DEFEATED") and short toasts. Any scene can add one.

var player: Player
var boss: BossBase
var _hp_box: Control
var _health_visible := true
var _hp_bar: UiStyle.Bar
var _hp_label: Label
var _boss_box: Control
var _boss_bar: UiStyle.Bar
var _boss_name: Label
var _reticle: Reticle
var _prompt: Label
var _prompt_raw := ""
var _card: Control
var _card_title: Label
var _card_sub: Label
var _overlay: Control
var _overlay_title: Label
var _overlay_sub: Label
var _overlay_box: VBoxContainer
var _overlay_tween: Tween
var _band_hold := -1.0               # >= 0: bottom_band_fraction() keeps this value while the boss bar is hidden
var _toast: Label
var _toast_left := 0.0


func _ready() -> void:
	layer = 10
	add_to_group("hud")
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	_build_health(root)
	_build_boss(root)
	_reticle = Reticle.new()
	_reticle.hud = self
	_reticle.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(_reticle)
	_prompt = UiStyle.label("", 28, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	_prompt.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.offset_left = -500
	_prompt.offset_right = 500
	_prompt.offset_top = -210
	_prompt.offset_bottom = -170
	root.add_child(_prompt)
	_toast = UiStyle.label("", 26, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	_toast.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_toast.offset_left = -500
	_toast.offset_right = 500
	_toast.offset_top = 40
	_toast.offset_bottom = 80
	root.add_child(_toast)
	_build_card(root)
	_build_overlay(root)
	Controls.device_changed.connect(func(_p: bool): _refresh_prompt())


func _build_health(root: Control) -> void:
	var box := PanelContainer.new()
	_hp_box = box
	box.visible = _health_visible
	box.add_theme_stylebox_override("panel", UiStyle.panel_box(0.7))
	box.position = Vector2(36, 32)
	box.custom_minimum_size = Vector2(440, 0)
	root.add_child(box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	box.add_child(v)
	_hp_label = UiStyle.label("HERCULES", 22, UiStyle.GOLD)
	v.add_child(_hp_label)
	_hp_bar = UiStyle.Bar.new()
	_hp_bar.custom_minimum_size = Vector2(410, 22)
	v.add_child(_hp_bar)


func _build_boss(root: Control) -> void:
	_boss_box = Control.new()
	_boss_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_boss_box.offset_left = -560
	_boss_box.offset_right = 560
	_boss_box.offset_top = -108     # 12 px lower than v1: more room for the hero's feet above it
	_boss_box.offset_bottom = -28
	_boss_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_box.visible = false
	root.add_child(_boss_box)
	var back := Panel.new()       # dark band behind the boss name + bar (bright sand / sky / lava behind it)
	# near-opaque backing + a thin light rim: the half-clear band let the orange fill vanish over the hydra's orange
	# inhale decal and the lava, and fade on white marble (QA)
	var back_sb := UiStyle.panel_box(0.88, false)
	back_sb.border_color = Color(0.95, 0.86, 0.64, 0.75)
	back_sb.set_border_width_all(2)
	back.add_theme_stylebox_override("panel", back_sb)
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	back.offset_left = -18
	back.offset_right = 18
	back.offset_top = -6
	back.offset_bottom = 4
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_box.add_child(back)
	_boss_name = UiStyle.label("", 30, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	_boss_name.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_boss_name.offset_bottom = 40
	_boss_box.add_child(_boss_name)
	_boss_bar = UiStyle.Bar.new()
	_boss_bar.fill = UiStyle.BOSS
	_boss_bar.outlined = true
	_boss_bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_boss_bar.offset_top = -30
	_boss_bar.offset_bottom = -6
	_boss_box.add_child(_boss_bar)


func _build_card(root: Control) -> void:
	# a soft dark plate (PanelContainer) behind the card text: light text over bright sand / sky was hard to read
	var plate := PanelContainer.new()
	# a thin strip in the top ~12 % of the screen, clear of the hero panel: lower down it sat over the boss at the
	# start of the fight and hid Medusa (QA)
	var sb := UiStyle.panel_box(0.4, false)
	sb.content_margin_left = 24
	sb.content_margin_right = 24
	sb.content_margin_top = 4
	sb.content_margin_bottom = 8
	plate.add_theme_stylebox_override("panel", sb)
	plate.set_anchors_preset(Control.PRESET_CENTER_TOP)
	plate.offset_left = -440
	plate.offset_right = 440
	plate.offset_top = 14
	plate.offset_bottom = 134
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.modulate.a = 0.0
	root.add_child(plate)
	_card = plate
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.add_child(v)
	_card_title = UiStyle.label("", 56, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	v.add_child(_card_title)
	_card_sub = UiStyle.label("", 26, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	v.add_child(_card_sub)
	var band := UiStyle.KeyBand.new()
	band.unit = 5.0
	band.custom_minimum_size = Vector2(0, 18)
	v.add_child(band)


func _build_overlay(root: Control) -> void:
	_overlay = ColorRect.new()
	(_overlay as ColorRect).color = Color(0, 0, 0, 0.35)
	_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.visible = false
	root.add_child(_overlay)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.offset_left = -800
	v.offset_right = 800
	v.offset_top = -120
	v.offset_bottom = 120
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	_overlay.add_child(v)
	_overlay_box = v
	_overlay_title = UiStyle.label("", 110, UiStyle.GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	v.add_child(_overlay_title)
	_overlay_sub = UiStyle.label("", 34, UiStyle.TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	v.add_child(_overlay_sub)


# ------------------------------------------------------------------ binding
## Follows a player's health.
func bind_player(p: Player) -> void:
	player = p
	p.health_changed.connect(_on_player_hp)
	_on_player_hp(p.hp, p.max_hp)


## First-use warm-up (ArenaBase.prewarm, under the island title card): draws the lock reticle's primitives for
## `frames` frames, invisible, so their canvas pipeline is compiled before the fight starts.
func warm_canvas(frames := 4) -> void:
	if _reticle != null:
		_reticle.warm = frames


## Shows a boss's name + health bar and follows it.
func bind_boss(b: BossBase) -> void:
	boss = b
	_boss_box.visible = true
	_boss_name.text = b.display_name
	_boss_bar.segments = b.max_hp
	b.health_changed.connect(_on_boss_hp)
	_on_boss_hp(b.hp, b.max_hp)


## Shows or hides the hero health panel (home and flight hide it: no fight there).
func set_health_visible(on: bool) -> void:
	_health_visible = on
	if _hp_box != null:
		_hp_box.visible = on


## Share of the screen height (0..1, from the bottom) covered by the boss name + bar band, 0 when it is hidden.
## The lock camera keeps the hero's feet above it.
func bottom_band_fraction() -> float:
	if _band_hold >= 0.0:
		return _band_hold
	if _boss_box == null or not _boss_box.visible:
		return 0.0
	var h := get_viewport().get_visible_rect().size.y
	if h <= 1.0:
		return 0.0
	var top := _boss_box.get_global_rect().position.y - 6.0     # the dark band reaches 6 px above the box
	return clampf((h - top) / h, 0.0, 0.5)


## Hides (or shows again) the boss name + bar and the lock reticle, e.g. during the hero's death hold so the fallen
## hero is not covered. While hidden with keep_framing, bottom_band_fraction() keeps its last value, so the lock camera
## does not re-aim.
func set_boss_visible(on: bool, keep_framing := true) -> void:
	if _boss_box == null:
		return
	if not on and keep_framing and _boss_box.visible:
		_band_hold = bottom_band_fraction()
	elif on:
		_band_hold = -1.0
	_boss_box.visible = on and boss != null
	_reticle.visible = on


func _on_player_hp(hp: int, max_hp: int) -> void:
	_hp_bar.set_value(float(hp) / float(maxi(max_hp, 1)))


func _on_boss_hp(hp: int, max_hp: int) -> void:
	_boss_bar.set_value(float(hp) / float(maxi(max_hp, 1)))


# ------------------------------------------------------------------ messages
## Shows a prompt; "{interact}" style placeholders become the button of the device in use. "" hides it.
func show_prompt(text: String) -> void:
	_prompt_raw = text
	_refresh_prompt()


func _refresh_prompt() -> void:
	_prompt.text = Controls.fill(_prompt_raw)


## Island title card that fades in and out over `seconds`.
func show_title_card(title: String, sub: String, seconds := 2.5) -> void:
	_card_title.text = title
	_card_sub.text = sub
	var tw := create_tween()
	tw.tween_property(_card, "modulate:a", 1.0, 0.4)
	tw.tween_interval(maxf(seconds - 0.8, 0.2))
	tw.tween_property(_card, "modulate:a", 0.0, 0.6)


## Big overlay ("LABOR COMPLETE", "DEFEATED"); seconds <= 0 keeps it up. `delay`: seconds before it fades in;
## `upper`: centred in the upper third of the screen instead of the middle (keeps the hero's body clear).
func show_overlay(title: String, sub := "", seconds := 3.0, color := UiStyle.GOLD, delay := 0.0, upper := false) -> void:
	_overlay_title.text = title
	_overlay_title.add_theme_color_override("font_color", color)
	_overlay_sub.text = sub
	# anchor the text box at the screen middle (0.5) or the middle of the upper third (1/6)
	var ay := 1.0 / 6.0 if upper else 0.5
	_overlay_box.anchor_top = ay
	_overlay_box.anchor_bottom = ay
	_overlay_box.offset_top = -120
	_overlay_box.offset_bottom = 120
	(_overlay as ColorRect).color = Color(0, 0, 0, 0.18 if upper else 0.35)
	if _overlay_tween != null and _overlay_tween.is_valid():
		_overlay_tween.kill()
	_overlay.visible = delay <= 0.0
	_overlay.modulate.a = 0.0
	var tw := create_tween()
	_overlay_tween = tw
	if delay > 0.0:
		tw.tween_interval(delay)
		tw.tween_callback(func(): _overlay.visible = true)
	tw.tween_property(_overlay, "modulate:a", 1.0, 0.35)
	if seconds > 0.0:
		tw.tween_interval(seconds)
		tw.tween_property(_overlay, "modulate:a", 0.0, 0.4)
		tw.tween_callback(func(): _overlay.visible = false)


## A short message at the top of the screen.
func show_message(text: String, seconds := 2.5) -> void:
	_toast.text = Controls.fill(text)
	_toast_left = seconds
	_toast.modulate.a = 1.0


func _process(delta: float) -> void:
	if _toast_left > 0.0:
		_toast_left -= delta
		if _toast_left <= 0.5:
			_toast.modulate.a = maxf(_toast_left / 0.5, 0.0)


## Lock-on reticle drawn at the boss's lock point on screen.
class Reticle extends Control:
	var hud: Hud
	var _t := 0.0
	var warm := 0                  # frames left of warm_canvas(): the reticle's draw calls, invisible, at a corner

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()

	func _draw() -> void:
		if warm > 0:
			warm -= 1
			# the same primitives as below (thick polylines, circle, arc, filled triangle), alpha ~0: on a cold
			# cache the first diamond compiled a canvas pipeline in the fight_start frame (57 ms, last_fixes)
			var c := Color(1, 1, 1, 0.004)
			var o := Vector2(4, 4)
			var pts := PackedVector2Array([o, o + Vector2(2, 2), o + Vector2(0, 4), o])
			draw_polyline(pts, c, 5.0)
			draw_polyline(pts, c, 2.5)
			draw_circle(o, 1.0, c)
			draw_arc(o, 2.0, 0.0, TAU, 32, c, 6.0)
			draw_colored_polygon(PackedVector2Array([o, o + Vector2(-1, -2), o + Vector2(1, -2)]), c)
			draw_polyline(pts, c, 2.0)
		if hud == null or hud.player == null or not is_instance_valid(hud.player):
			return
		var cam := get_viewport().get_camera_3d()
		if cam == null:
			return
		var rings := _draw_weak_points(cam)
		# the weak-point ring + arrow replace the diamond on that boss (QA: diamond stacked on Medusa's exposed neck)
		if rings and hud.player.lock_target == hud.boss:
			return
		var lp = hud.player.lock_point()
		if lp == null or cam.is_position_behind(lp):
			return
		var p := cam.unproject_position(lp)
		var s := 18.0 + 3.0 * sin(_t * 5.0)
		var pts := PackedVector2Array([p + Vector2(0, -s), p + Vector2(s, 0), p + Vector2(0, s), p + Vector2(-s, 0), p + Vector2(0, -s)])
		draw_polyline(pts, Color(0, 0, 0, 0.6), 5.0)
		draw_polyline(pts, UiStyle.GOLD, 2.5)
		draw_circle(p, 3.0, UiStyle.GOLD)

	## A pulsing marker + arrow over every exposed weak point of the bound boss (visible even behind the hero).
	## Returns true when at least one ring was drawn.
	func _draw_weak_points(cam: Camera3D) -> bool:
		if hud.boss == null or not is_instance_valid(hud.boss):
			return false
		var drawn := false
		for id in hud.boss.weak_points:
			var wp: WeakPoint = hud.boss.weak_points[id]
			if not wp.exposed or cam.is_position_behind(wp.global_position):
				continue
			var p := cam.unproject_position(wp.global_position)
			drawn = true
			var k := 0.5 + 0.5 * sin(_t * 8.0)
			var r := 16.0 + 6.0 * k
			draw_arc(p, r + 2.0, 0.0, TAU, 32, Color(0, 0, 0, 0.7), 6.0)
			draw_arc(p, r, 0.0, TAU, 32, WeakPoint.MARK_COLOR, 3.0)
			var top := p + Vector2(0, -r - 10.0 - 6.0 * k)
			var tri := PackedVector2Array([top, top + Vector2(-11, -16), top + Vector2(11, -16)])
			draw_colored_polygon(tri, WeakPoint.MARK_COLOR)
			draw_polyline(PackedVector2Array([tri[0], tri[1], tri[2], tri[0]]), Color(0, 0, 0, 0.8), 2.0)
		return drawn
