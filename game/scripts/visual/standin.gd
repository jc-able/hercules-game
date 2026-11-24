class_name StandIn
extends Node3D
## Grey-box stand-in body built from Tuning.CHARS (capsules, spheres, boxes) with named socket markers and pivots
## that CharacterVisual drives procedurally. Faces +Z, feet on y = 0, real size. Used until the rigged GLB lands.

var char_id: StringName
var info: Dictionary
var h := 2.0
var sockets := {}          # logical name -> Node3D marker
var pivots := {}           # pivot name -> Node3D
var materials: Array[ShaderMaterial] = []
var _rest := {}            # pivot name -> rest rotation
var _body_mat: ShaderMaterial
var _accent_mat: ShaderMaterial
var _dark_mat: ShaderMaterial


## Builds the stand-in for a character id.
static func build(id: StringName) -> StandIn:
	var s := StandIn.new()
	s.name = "StandIn"
	s.char_id = id
	s.info = Tuning.char_info(id)
	s.h = float(s.info.get("height", 2.0))
	s._make()
	return s


func _make() -> void:
	var ow: float = CharacterVisual.outline_width_for(h)
	_body_mat = CharacterVisual.make_toon(info.get("color", Color.GRAY), null, ow)
	_accent_mat = CharacterVisual.make_toon(info.get("accent", Color.DIM_GRAY), null, ow)
	_dark_mat = CharacterVisual.make_toon(Color(0.12, 0.10, 0.09), null, ow)
	for m in [_body_mat, _accent_mat, _dark_mat]:
		materials.append(m)
	var root := _pivot("root", self, Vector3.ZERO)
	match String(info.get("shape", "humanoid")):
		"serpent":
			_make_serpent(root)
		"hydra":
			_make_hydra(root)
		"horse":
			_make_horse(root)
		_:
			_make_humanoid(root)
	for k in pivots:
		_rest[k] = (pivots[k] as Node3D).rotation


# ------------------------------------------------------------------ builders
func _make_humanoid(root: Node3D) -> void:
	var r: float = info.get("radius", 0.4)
	var hip_y := h * 0.48
	var shoulder_y := h * 0.80
	var upper := _pivot("upper", root, Vector3(0, hip_y, 0))
	for side in [-1.0, 1.0]:
		var leg := _pivot("leg_l" if side > 0 else "leg_r", root, Vector3(side * r * 0.45, hip_y, 0))
		_limb(leg, Vector3.ZERO, Vector3(0, -hip_y + r * 0.25, 0), r * 0.32, _accent_mat)
		_box(leg, Vector3(0, -hip_y + r * 0.12, r * 0.25), Vector3(r * 0.55, r * 0.25, r * 1.0), _dark_mat)
	_limb(upper, Vector3(0, r * 0.2, 0), Vector3(0, shoulder_y - hip_y - r * 0.1, 0), r * 0.85, _body_mat)
	_box(upper, Vector3(0, r * 0.05, 0), Vector3(r * 2.0, r * 0.7, r * 1.6), _accent_mat)   # kilt / belt
	var neck := _pivot("neck", upper, Vector3(0, shoulder_y - hip_y, 0))
	var head_r := h * 0.075
	var head := _sphere(neck, Vector3(0, head_r * 1.5, 0), head_r, _body_mat)
	_marker("head", neck, Vector3(0, head_r * 1.5, 0))
	_marker("chest", upper, Vector3(0, (shoulder_y - hip_y) * 0.7, r * 0.6))
	if info.get("four_arms", false):
		_sphere(neck, Vector3(0, head_r * 1.6, head_r * 0.85), head_r * 0.38, _dark_mat)       # the one eye
	else:
		_sphere(neck, Vector3(0, head_r * 1.95, -head_r * 0.2), head_r * 0.75, _dark_mat)      # hair
	head.name = "Head"
	var arm_len := h * 0.36
	var sh_x := r + h * 0.04
	for side in [-1.0, 1.0]:
		var sfx := "_l" if side > 0 else "_r"
		var arm := _pivot("arm" + sfx, upper, Vector3(side * sh_x, shoulder_y - hip_y - r * 0.15, 0))
		_limb(arm, Vector3.ZERO, Vector3(0, -arm_len, 0), r * 0.26, _body_mat)
		_marker("forearm" + sfx, arm, Vector3(0, -arm_len * 0.62, 0))
		_marker("hand" + sfx, arm, Vector3(0, -arm_len, 0)).rotation_degrees = Vector3(90, 0, 0)   # props point forward
		_marker("hand_u" + sfx, arm, Vector3(0, -arm_len, 0))
		_marker("forearm_u" + sfx, arm, Vector3(0, -arm_len * 0.62, 0))
		if info.get("four_arms", false):
			var low := _pivot("arm_d" + sfx, upper, Vector3(side * sh_x * 0.95, shoulder_y - hip_y - h * 0.13, 0))
			_limb(low, Vector3.ZERO, Vector3(0, -arm_len * 0.85, 0), r * 0.22, _body_mat)
			_marker("hand_d" + sfx, low, Vector3(0, -arm_len * 0.85, 0))
	# alias names the spec uses for the cyclops (hand_ur = upper right ...)
	sockets["hand_ur"] = sockets["hand_u_r"]
	sockets["hand_ul"] = sockets["hand_u_l"]
	sockets["forearm_ur"] = sockets["forearm_u_r"]
	sockets["forearm_ul"] = sockets["forearm_u_l"]


func _make_serpent(root: Node3D) -> void:
	var r: float = info.get("radius", 1.0)
	var tail_len: float = info.get("tail", 9.9)
	var base_y := r * 0.9
	var upper := _pivot("upper", root, Vector3(0, base_y, 0))
	_limb(upper, Vector3.ZERO, Vector3(0, h * 0.62 - base_y, 0), r * 0.75, _body_mat)
	var neck := _pivot("neck", upper, Vector3(0, h * 0.68 - base_y, 0))
	_limb(neck, Vector3.ZERO, Vector3(0, h * 0.12, 0), r * 0.32, _body_mat)
	_marker("neck", neck, Vector3(0, h * 0.06, r * 0.1))
	var head_r := h * 0.07
	_sphere(neck, Vector3(0, h * 0.14 + head_r, 0), head_r, _body_mat)
	_marker("head", neck, Vector3(0, h * 0.14 + head_r, 0))
	_marker("eyes", neck, Vector3(0, h * 0.14 + head_r * 1.1, head_r * 0.9))
	for i in 6:   # snake hair
		var a := TAU * float(i) / 6.0
		_limb(neck, Vector3(0, h * 0.14 + head_r * 1.3, 0), Vector3(cos(a) * head_r * 1.6, h * 0.14 + head_r * 2.3, sin(a) * head_r * 1.6), head_r * 0.18, _accent_mat)
	for side in [-1.0, 1.0]:
		var sfx := "_l" if side > 0 else "_r"
		var arm := _pivot("arm" + sfx, upper, Vector3(side * r * 0.95, h * 0.58 - base_y, 0))
		_limb(arm, Vector3.ZERO, Vector3(0, -h * 0.26, 0), r * 0.2, _body_mat)
		_marker("hand" + sfx, arm, Vector3(0, -h * 0.26, 0))
	var tail := _pivot("tail", root, Vector3(0, base_y, 0))
	var n := 14
	var prev := Vector3.ZERO
	for i in n:
		var t := float(i + 1) / float(n)
		var p := Vector3(sin(t * PI * 1.2) * r * 0.6, -base_y * minf(1.0, t * 3.0) + r * 0.55 * (1.0 - t), -tail_len * t)
		_limb(tail, prev, p, r * (0.85 - 0.6 * t), _accent_mat if i % 2 == 0 else _body_mat)
		prev = p
	_marker("tail_tip", tail, prev)


func _make_hydra(root: Node3D) -> void:
	var r: float = info.get("radius", 2.5)
	var length: float = info.get("length", 18.0)
	var head_h: float = info.get("head_height", 11.0)
	var body_y := h * 0.62
	var upper := _pivot("upper", root, Vector3(0, body_y, 0))
	_box(upper, Vector3(0, 0, -length * 0.08), Vector3(r * 2.0, h * 0.42, length * 0.38), _body_mat)
	_box(upper, Vector3(0, h * 0.22, -length * 0.08), Vector3(r * 1.2, h * 0.08, length * 0.3), _accent_mat)
	var legs := {"fl": Vector3(r * 0.95, 0, length * 0.06), "fr": Vector3(-r * 0.95, 0, length * 0.06),
		"bl": Vector3(r * 0.95, 0, -length * 0.24), "br": Vector3(-r * 0.95, 0, -length * 0.24)}
	for k in legs:
		var leg := _pivot("leg_" + k, root, legs[k] + Vector3(0, body_y, 0))
		_limb(leg, Vector3.ZERO, Vector3(0, -body_y + r * 0.3, 0), r * 0.32, _body_mat)
		_box(leg, Vector3(0, -body_y + r * 0.15, r * 0.2), Vector3(r * 0.7, r * 0.3, r * 0.9), _dark_mat)
		_marker("foot_" + k, leg, Vector3(0, -body_y + 0.1, 0))
	var tail := _pivot("tail", upper, Vector3(0, -h * 0.05, -length * 0.27))
	var prev := Vector3.ZERO
	for i in 8:
		var t := float(i + 1) / 8.0
		var p := Vector3(sin(t * 2.5) * r * 0.5, -body_y * 0.85 * minf(1.0, t * 1.5), -length * 0.45 * t)
		_limb(tail, prev, p, r * (0.55 - 0.45 * t), _body_mat)
		prev = p
	# nine necks: centre (index 0 -> "c") rises highest, eight side heads fan out
	for i in 9:
		var key := "c" if i == 0 else str(i)
		var side := 0.0 if i == 0 else (1.0 if i % 2 == 1 else -1.0)
		var rank := 0 if i == 0 else int((i + 1) / 2)
		var base := Vector3(side * r * 0.25 * rank, h * 0.12, length * 0.1)
		var neck := _pivot("neck_" + key, upper, base)
		var top_y := head_h - body_y - (0.0 if i == 0 else 1.0 + 0.9 * rank)
		var tip := Vector3(side * (1.4 + 1.5 * rank), top_y, 3.2 - 0.25 * rank)
		_limb(neck, Vector3.ZERO, tip, r * (0.36 if i == 0 else 0.26), _body_mat if i != 0 else _accent_mat)
		var hr := r * (0.42 if i == 0 else 0.32)
		_sphere(neck, tip + Vector3(0, 0, hr * 0.6), hr, _body_mat)
		_box(neck, tip + Vector3(0, -hr * 0.6, hr * 1.2), Vector3(hr * 1.0, hr * 0.4, hr * 1.6), _accent_mat)
		_marker("head_" + key, neck, tip + Vector3(0, 0, hr * 0.6))
		if i == 0:
			_marker("jaw_c", neck, tip + Vector3(0, -hr * 0.8, hr * 1.2))


func _make_horse(root: Node3D) -> void:
	var r: float = info.get("radius", 0.7)
	var body_y := h * 0.72
	var upper := _pivot("upper", root, Vector3(0, body_y, 0))
	_limb(upper, Vector3(0, 0, -h * 0.45), Vector3(0, 0, h * 0.45), r * 0.55, _body_mat)
	for p in [Vector3(r * 0.3, 0, h * 0.35), Vector3(-r * 0.3, 0, h * 0.35), Vector3(r * 0.3, 0, -h * 0.38), Vector3(-r * 0.3, 0, -h * 0.38)]:
		_limb(upper, p, p + Vector3(0, -body_y + 0.05, 0), r * 0.14, _body_mat)
	var neck := _pivot("neck", upper, Vector3(0, r * 0.3, h * 0.42))
	_limb(neck, Vector3.ZERO, Vector3(0, h * 0.42, h * 0.18), r * 0.28, _body_mat)
	_box(neck, Vector3(0, h * 0.45, h * 0.32), Vector3(r * 0.4, r * 0.4, h * 0.3), _body_mat)
	_marker("head", neck, Vector3(0, h * 0.45, h * 0.32))
	_marker("saddle", upper, Vector3(0, r * 0.55, h * 0.05))
	for side in [-1.0, 1.0]:
		var wing := _pivot("wing_l" if side > 0 else "wing_r", upper, Vector3(side * r * 0.4, r * 0.4, h * 0.12))
		_box(wing, Vector3(side * h * 0.85, 0, -h * 0.1), Vector3(h * 1.7, 0.06, h * 0.55), _accent_mat)
	var tail := _pivot("tail", upper, Vector3(0, r * 0.2, -h * 0.5))
	_limb(tail, Vector3.ZERO, Vector3(0, -h * 0.35, -h * 0.25), r * 0.15, _accent_mat)


# ------------------------------------------------------------------ pose (called each frame by CharacterVisual)
## Applies procedural pose parameters (radians / metres): lean, bob, twist, spin, topple, arm_r, arm_l, head_dip,
## stride (leg swing phase amount), leg_lift (front right leg), tail_twist, wing, head_c_dip (hydra centre neck only).
func pose(p: Dictionary) -> void:
	var root: Node3D = pivots["root"]
	root.rotation = Vector3(float(p.get("lean", 0.0)) + float(p.get("spin", 0.0)), 0.0, float(p.get("topple", 0.0)))
	root.position = Vector3(0, float(p.get("bob", 0.0)), 0)
	if p.get("spin", 0.0) != 0.0:
		root.position.y += h * 0.35 * absf(sin(float(p["spin"]) * 0.5))
	_rot("upper", Vector3(0, float(p.get("twist", 0.0)), 0))
	var ar: float = p.get("arm_r", 0.0)
	var al: float = p.get("arm_l", 0.0)
	_rot("arm_r", Vector3(ar, 0, 0))
	_rot("arm_l", Vector3(al, 0, 0))
	_rot("arm_d_r", Vector3(ar * 0.6, 0, 0))
	_rot("arm_d_l", Vector3(al * 0.6, 0, 0))
	var hd: float = p.get("head_dip", 0.0)
	_rot("neck", Vector3(hd, 0, 0))
	_rot("neck_c", Vector3(hd + float(p.get("head_c_dip", 0.0)), 0, 0))
	var st: float = p.get("stride", 0.0)
	_rot("leg_l", Vector3(st, 0, 0))
	_rot("leg_r", Vector3(-st, 0, 0))
	_rot("leg_fl", Vector3(st * 0.5, 0, 0))
	_rot("leg_br", Vector3(st * 0.5, 0, 0))
	_rot("leg_bl", Vector3(-st * 0.5, 0, 0))
	_rot("leg_fr", Vector3(-st * 0.5 - float(p.get("leg_lift", 0.0)), 0, 0))
	_rot("tail", Vector3(0, float(p.get("tail_twist", 0.0)), 0))
	var w: float = p.get("wing", 0.0)
	_rot("wing_l", Vector3(0, 0, w))
	_rot("wing_r", Vector3(0, 0, -w))


func _rot(name: String, r: Vector3) -> void:
	var n: Node3D = pivots.get(name)
	if n != null:
		n.rotation = _rest[name] + r


# ------------------------------------------------------------------ helpers
func _pivot(n: String, parent: Node3D, pos: Vector3) -> Node3D:
	var p := Node3D.new()
	p.name = "P_" + n
	p.position = pos
	parent.add_child(p)
	pivots[n] = p
	return p


func _marker(n: String, parent: Node3D, pos: Vector3) -> Node3D:
	var m := Node3D.new()
	m.name = "S_" + n
	m.position = pos
	parent.add_child(m)
	sockets[n] = m
	return m


func _limb(parent: Node3D, a: Vector3, b: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var d := b - a
	var len := d.length()
	var cm := CapsuleMesh.new()
	cm.radius = radius
	cm.height = maxf(len + radius * 2.0, radius * 2.01)
	cm.radial_segments = 12
	cm.rings = 4
	var mi := MeshInstance3D.new()
	mi.mesh = cm
	mi.material_override = mat
	parent.add_child(mi)
	var y := d.normalized() if len > 0.0001 else Vector3.UP
	var x := y.cross(Vector3.FORWARD if absf(y.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT).normalized()
	var z := x.cross(y).normalized()
	mi.transform = Transform3D(Basis(x, y, z), (a + b) * 0.5)
	return mi


func _sphere(parent: Node3D, pos: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	sm.radial_segments = 16
	sm.rings = 8
	var mi := MeshInstance3D.new()
	mi.mesh = sm
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var bm := BoxMesh.new()
	bm.size = size
	var mi := MeshInstance3D.new()
	mi.mesh = bm
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi
