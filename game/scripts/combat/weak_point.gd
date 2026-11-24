class_name WeakPoint
extends Area3D
## A boss weak point (collision layer 5). The sword only damages it while `exposed` and `hits_left > 0`; every other
## sword contact with the boss is a glance. BossBase.add_weak_point() creates these on a socket.

signal struck(point: WeakPoint)

const MARK_COLOR := Color(1.0, 0.42, 0.08)     ## saturated orange: glow + HUD marker (reads on sand, marble, basalt)
const GLOW_STRENGTH := 0.3                     ## additive glow strength (pulses 0.2-0.35, alpha never above 0.35)

var id: StringName
var radius := 0.8
var exposed := false
var hits_left := 0                  ## set when exposed; 0 = closed
var boss: Node = null
## Set by the sword just before strike() (feedback 2 strike effects): where the blade crossed the point, the hero's
## position and the blade's recent path [grip, tip, ...] in world space. Read by BossBase.take_weak_hit.
var last_hit_pos := Vector3.ZERO
var last_from := Vector3.ZERO
var last_trail := PackedVector3Array()
var _glow: MeshInstance3D
var _mat: ShaderMaterial
var _t := 0.0


func _init(point_id: StringName = &"weak", r := 0.8) -> void:
	id = point_id
	radius = r
	name = "Weak_%s" % point_id
	collision_layer = 1 << 4
	collision_mask = 0
	monitoring = false
	monitorable = true
	add_to_group("weak_point")          # the real-blade sword test (SwordHitbox) checks these spheres directly
	var cs := CollisionShape3D.new()
	var sh := SphereShape3D.new()
	sh.radius = r
	cs.shape = sh
	add_child(cs)
	# a soft additive fresnel glow (rim bright, centre almost clear) at low strength: the old filled orange sphere
	# (alpha 0.6-0.9 + a dark inverted-hull shell) covered Medusa's face and eyes during the gaze (QA). The HUD's ring +
	# arrow (Hud.Reticle) is the main marker; this only makes the spot glow on the body.
	_mat = ShaderMaterial.new()
	_mat.shader = _glow_shader()
	_mat.set_shader_parameter("color", MARK_COLOR)
	_mat.set_shader_parameter("strength", GLOW_STRENGTH)
	var sm := SphereMesh.new()
	sm.radius = r * 0.7
	sm.height = r * 1.4
	_glow = MeshInstance3D.new()
	_glow.mesh = sm
	_glow.material_override = _mat
	_glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_glow.visible = false
	add_child(_glow)


static var _shader: Shader = null

static func _glow_shader() -> Shader:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = """
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;
uniform vec4 color : source_color = vec4(1.0, 0.42, 0.08, 1.0);
uniform float strength = 0.3;
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	ALBEDO = color.rgb;
	ALPHA = clamp(strength * (0.12 + 0.88 * rim), 0.0, 0.35);
}
"""
	return _shader


## Opens the weak point for `hits` sword hits.
func open(hits: int) -> void:
	exposed = hits > 0
	hits_left = maxi(hits, 0)
	_glow.visible = exposed


## Closes the weak point.
func close() -> void:
	exposed = false
	hits_left = 0
	_glow.visible = false


## Called by the sword: true when the hit counted (exposed with hits left). Closes itself after the last hit.
func strike() -> bool:
	if not exposed or hits_left <= 0:
		return false
	hits_left -= 1
	struck.emit(self)
	if hits_left <= 0:
		close()
	return true


func _process(delta: float) -> void:
	if not _glow.visible:
		return
	_t += delta
	var k := 0.5 + 0.5 * sin(_t * 9.0)
	_mat.set_shader_parameter("strength", lerpf(0.2, 0.35, k))
	_glow.scale = Vector3.ONE * (0.95 + 0.1 * k)
