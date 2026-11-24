class_name Telegraph
extends Node3D
## Ground warning decal (circle, cone/arc or ring): a flat unshaded quad just above the floor whose fill grows over
## the warning time, flashes at the moment of impact, then frees itself. Move it freely (e.g. follow the player).

const SHADER := preload("res://shaders/telegraph.gdshader")
const LIFT := 0.04
const STRIKE_TIME := 0.22
## Below the default 0: every transparent VFX (dust, fire, beams, glows) draws on top of the decals without setting a
## priority. Decals still draw over the opaque floor (they are transparent, depth test only).
const RENDER_PRIORITY := -10
const DEFAULT_EDGE := Color(1.0, 0.92, 0.75)

var seconds := 1.0
var elapsed := 0.0
var _mat: ShaderMaterial
var _mesh: MeshInstance3D
var _done := false


## A filled circle of `radius`.
static func circle(radius: float, secs: float, color := Color.RED) -> Telegraph:
	return _make(0, radius, secs, color)


## A cone/arc: `half_angle_deg` either side of the node's +Z, out to `length`.
static func cone(half_angle_deg: float, length: float, secs: float, color := Color.RED) -> Telegraph:
	var t := _make(1, length, secs, color)
	t._mat.set_shader_parameter("half_angle", deg_to_rad(half_angle_deg))
	return t


## A ring between `inner` and `outer` radius.
static func ring(inner: float, outer: float, secs: float, color := Color.RED) -> Telegraph:
	var t := _make(2, outer, secs, color)
	t._mat.set_shader_parameter("inner", clampf(inner / maxf(outer, 0.01), 0.0, 0.99))
	return t


static func _make(mode: int, radius: float, secs: float, color: Color) -> Telegraph:
	var t := Telegraph.new()
	t.name = "Telegraph"
	t.seconds = maxf(secs, 0.01)
	t._mat = ShaderMaterial.new()
	t._mat.shader = SHADER
	t._mat.render_priority = RENDER_PRIORITY
	t._mat.set_shader_parameter("mode", mode)
	t._mat.set_shader_parameter("color", color)
	t._mat.set_shader_parameter("edge_color", DEFAULT_EDGE)
	t._mat.set_shader_parameter("edge", clampf(0.18 / maxf(radius, 0.5), 0.008, 0.06))
	t._mesh = MeshInstance3D.new()
	t._mesh.mesh = _quad(radius)
	t._mesh.material_override = t._mat
	t._mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	t._mesh.position.y = LIFT
	t.add_child(t._mesh)
	return t


static func _quad(r: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var corners := [Vector3(-r, 0, -r), Vector3(r, 0, -r), Vector3(r, 0, r), Vector3(-r, 0, r)]
	for i in [0, 2, 1, 0, 3, 2]:
		var c: Vector3 = corners[i]
		st.set_normal(Vector3.UP)
		st.set_uv(Vector2(c.x / (2.0 * r) + 0.5, c.z / (2.0 * r) + 0.5))
		st.add_vertex(c)
	return st.commit()


## Points the decal (cones) along a horizontal direction.
func aim(dir: Vector3) -> void:
	var d := Vector3(dir.x, 0, dir.z)
	if d.length() > 0.001:
		global_rotation = Vector3(0, atan2(d.x, d.z), 0)


## Recolours the decal: `fill` (the warning colour, alpha scales the whole decal) and optionally the `edge` line
## colour (default cream; use a dark edge on pale floors such as marble). Returns self for chaining.
func set_colors(fill: Color, edge: Variant = null) -> Telegraph:
	_mat.set_shader_parameter("color", fill)
	if edge is Color:
		_mat.set_shader_parameter("edge_color", edge)
	return self


## Seconds left until impact.
func time_left() -> float:
	return maxf(seconds - elapsed, 0.0)


## Removes the decal now, without the impact flash.
func cancel() -> void:
	_done = true
	queue_free()


func _process(delta: float) -> void:
	if _done:
		return
	elapsed += delta
	_mat.set_shader_parameter("progress", clampf(elapsed / seconds, 0.0, 1.0))
	if elapsed >= seconds:
		var k := clampf((elapsed - seconds) / STRIKE_TIME, 0.0, 1.0)
		_mat.set_shader_parameter("strike", 1.0 - k)
		if k >= 1.0:
			_done = true
			queue_free()
