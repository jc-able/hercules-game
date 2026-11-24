class_name UiStyle
extends RefCounted
## The flat HUD/menu look drawn in code: dark panels, warm gold accents, a Greek-key line. No external fonts/images.

const PANEL := Color(0.07, 0.06, 0.05, 0.82)
const PANEL_EDGE := Color(0.55, 0.42, 0.20, 0.9)
const GOLD := Color(0.95, 0.76, 0.34)
const GOLD_DIM := Color(0.62, 0.48, 0.22)
const TEXT := Color(0.97, 0.93, 0.85)
const TEXT_DIM := Color(0.75, 0.70, 0.62)
const HEALTH := Color(0.80, 0.18, 0.14)
const HEALTH_BACK := Color(0.20, 0.06, 0.05, 0.9)
const BOSS := Color(0.86, 0.55, 0.16)


## A flat panel StyleBox with a thin gold edge.
static func panel_box(alpha := 0.82, edge := true) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(PANEL.r, PANEL.g, PANEL.b, alpha)
	if edge:
		s.border_color = PANEL_EDGE
		s.set_border_width_all(2)
	s.set_corner_radius_all(3)
	s.set_content_margin_all(14)
	return s


## A label with the house colours; size in px.
static func label(text: String, size := 24, color := TEXT, align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = align
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	# a dark outline + soft shadow so light text reads on bright sand and sky (reviewed at 1280x720)
	l.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.02, 0.95))
	l.add_theme_constant_override("outline_size", clampi(size / 5, 4, 12))
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.55))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 3)
	l.add_theme_constant_override("shadow_outline_size", clampi(size / 5, 4, 12))
	return l


## A menu button: dark, gold edge on focus/hover, accepts pad A / Enter / click.
static func button(text: String, size := 30) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_ALL
	b.custom_minimum_size = Vector2(420, 62)
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_color_override("font_color", TEXT_DIM)
	b.add_theme_color_override("font_hover_color", TEXT)
	b.add_theme_color_override("font_focus_color", GOLD)
	b.add_theme_color_override("font_pressed_color", GOLD)
	b.add_theme_color_override("font_disabled_color", Color(0.4, 0.38, 0.34))
	var normal := panel_box(0.6, false)
	var focus := panel_box(0.85, true)
	focus.border_color = GOLD
	# hover is lighter than focus (no gold frame): with the mouse resting on one button and the pad/keyboard focus
	# on another, only one button looks selected (QA: Resume focused + Restart fight hovered looked like two picks)
	var hover := panel_box(0.72, false)
	hover.bg_color = Color(0.16, 0.13, 0.09, 0.78)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("focus", focus)
	b.add_theme_stylebox_override("pressed", focus)
	b.add_theme_stylebox_override("disabled", normal)
	# a real mouse move over a button moves the focus there, so hover and focus agree once the mouse is used
	# (a cursor that merely appears over a button, e.g. when Esc frees it, does not steal the focus)
	b.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseMotion and (e as InputEventMouseMotion).relative.length() > 0.5 \
				and b.focus_mode != Control.FOCUS_NONE and not b.disabled and not b.has_focus():
			b.grab_focus())
	b.focus_entered.connect(func(): Sfx.play("ui_move"))
	b.pressed.connect(func(): Sfx.play("ui_accept"))
	return b


## Draws a Greek-key (meander) line on a CanvasItem from x0 to x1 at y, unit = step size in px.
static func draw_greek_key(ci: CanvasItem, x0: float, x1: float, y: float, unit := 8.0, color := GOLD, width := 2.0) -> void:
	var x := x0
	while x + unit * 4.0 <= x1:
		var pts := PackedVector2Array([
			Vector2(x, y + unit), Vector2(x, y - unit), Vector2(x + unit * 2.0, y - unit), Vector2(x + unit * 2.0, y),
			Vector2(x + unit, y), Vector2(x + unit, y + unit), Vector2(x + unit * 3.0, y + unit), Vector2(x + unit * 3.0, y - unit),
			Vector2(x + unit * 4.0, y - unit)])
		ci.draw_polyline(pts, color, width)
		x += unit * 4.0
	ci.draw_line(Vector2(x0, y + unit * 1.6), Vector2(x, y + unit * 1.6), color, width * 0.6)
	ci.draw_line(Vector2(x0, y - unit * 1.6), Vector2(x, y - unit * 1.6), color, width * 0.6)


## A full-screen Control that draws a horizontal Greek-key band (for title / menus).
class KeyBand extends Control:
	var unit := 8.0
	var color := UiStyle.GOLD

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		custom_minimum_size = Vector2(0, unit * 4.0)

	func _draw() -> void:
		UiStyle.draw_greek_key(self, 0.0, size.x, size.y * 0.5, unit, color)


## A bar (health) drawn flat: background, a trailing "damage" fill and the live fill, with a gold frame.
class Bar extends Control:
	var value := 1.0
	var trail := 1.0
	var fill := UiStyle.HEALTH
	var segments := 0
	var outlined := false    ## dark outline around the frame + a brighter top highlight (boss bar over bright floors)

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func set_value(v: float) -> void:
		value = clampf(v, 0.0, 1.0)
		queue_redraw()

	func _process(delta: float) -> void:
		if trail > value:
			trail = maxf(value, trail - delta * 0.6)
			queue_redraw()
		elif trail < value:
			trail = value

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, UiStyle.HEALTH_BACK)
		draw_rect(Rect2(Vector2.ZERO, Vector2(size.x * trail, size.y)), Color(1.0, 0.85, 0.6, 0.8))
		draw_rect(Rect2(Vector2.ZERO, Vector2(size.x * value, size.y)), fill)
		draw_rect(Rect2(Vector2(0, 0), Vector2(size.x * value, size.y * 0.3)), Color(1, 1, 1, 0.3 if outlined else 0.14))
		if outlined and value > 0.0:
			draw_line(Vector2(0, size.y - 1.0), Vector2(size.x * value, size.y - 1.0), Color(0.25, 0.10, 0.02, 0.9), 2.0)
		if segments > 1:
			for i in range(1, segments):
				var x := size.x * float(i) / float(segments)
				draw_line(Vector2(x, 0), Vector2(x, size.y), Color(0, 0, 0, 0.6), 2.0)
		if outlined:
			draw_rect(r.grow(2.0), Color(0.02, 0.01, 0.0, 0.95), false, 2.0)
		draw_rect(r, UiStyle.GOLD_DIM, false, 2.0)
