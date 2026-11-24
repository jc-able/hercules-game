class_name EnvKit
extends RefCounted
## Building blocks for scenes built in code: sun, painted sky + environment, floor disc, stylized sea, invisible
## arena boundary, simple columns/rocks. Used by ArenaBase and free for the world/boss modules.

const SKY_SHADER := preload("res://shaders/sky.gdshader")
const WATER_SHADER := preload("res://shaders/water.gdshader")


## A shadow-casting sun. `rot_deg` = (pitch, yaw, 0) in degrees (pitch negative = from above).
static func sun(parent: Node, rot_deg := Vector3(-50, -35, 0), color := Color(1.0, 0.95, 0.85), energy := 1.0) -> DirectionalLight3D:
	var l := DirectionalLight3D.new()
	l.name = "Sun"
	l.rotation_degrees = rot_deg
	l.light_color = color
	l.light_energy = energy
	l.shadow_enabled = true
	l.directional_shadow_max_distance = 140.0
	l.shadow_blur = 0.6
	parent.add_child(l)
	return l


## WorldEnvironment with the painted sky shader; colours are the sky gradient. Returns the Environment.
static func sky(parent: Node, top := Color(0.18, 0.42, 0.80), horizon := Color(0.78, 0.86, 0.92), bottom := Color(0.30, 0.52, 0.66), ambient := 0.3, clouds := 0.35) -> Environment:
	var sm := ShaderMaterial.new()
	sm.shader = SKY_SHADER
	sm.set_shader_parameter("top_color", Vector3(top.r, top.g, top.b))
	sm.set_shader_parameter("horizon_color", Vector3(horizon.r, horizon.g, horizon.b))
	sm.set_shader_parameter("bottom_color", Vector3(bottom.r, bottom.g, bottom.b))
	sm.set_shader_parameter("cloud_amount", clouds)
	var s := Sky.new()
	s.sky_material = sm
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = s
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = ambient
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 0.9
	env.tonemap_white = 1.8
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.05
	env.fog_enabled = true
	env.fog_light_color = horizon
	env.fog_density = 0.0016
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	we.environment = env
	parent.add_child(we)
	return env


## A flat round floor whose top is at y = 0 (collision layer 1).
static func floor_disc(parent: Node, radius: float, color: Color, tex: Texture2D = null) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = "Floor"
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = radius + 12.0
	shape.height = 2.0
	cs.shape = shape
	cs.position.y = -1.0
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = radius + 4.0
	cm.bottom_radius = radius + 6.0
	cm.height = 2.0
	cm.radial_segments = 96
	mi.mesh = cm
	mi.position.y = -1.0
	mi.material_override = CharacterVisual.make_toon(color, tex, 0.0, 0.0)
	body.add_child(mi)
	parent.add_child(body)
	return body


## A big flat stylized sea plane at height y.
static func sea(parent: Node, size := 4000.0, y := -2.0, subdivide := 200) -> MeshInstance3D:
	var pm := PlaneMesh.new()
	pm.size = Vector2(size, size)
	pm.subdivide_width = subdivide
	pm.subdivide_depth = subdivide
	var m := ShaderMaterial.new()
	m.shader = WATER_SHADER
	var mi := MeshInstance3D.new()
	mi.name = "Sea"
	mi.mesh = pm
	mi.material_override = m
	mi.position.y = y
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


## An invisible ring wall at `radius` (layer 1, group "camera_ignore" so it never pushes the camera in).
static func boundary(parent: Node, radius: float, height := 12.0, segments := 40) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = "Boundary"
	body.collision_layer = 1
	body.collision_mask = 0
	body.add_to_group("camera_ignore")
	var seg_len := TAU * radius / float(segments) * 1.08
	for i in segments:
		var a := TAU * float(i) / float(segments)
		var cs := CollisionShape3D.new()
		var b := BoxShape3D.new()
		b.size = Vector3(seg_len, height, 1.0)
		cs.shape = b
		cs.position = Vector3(sin(a) * (radius + 0.5), height * 0.5, cos(a) * (radius + 0.5))
		cs.rotation.y = a
		body.add_child(cs)
	parent.add_child(body)
	return body


## A (possibly broken) column with collision, toon shaded with an outline.
static func column(parent: Node, pos: Vector3, radius := 0.8, height := 6.0, color := Color(0.9, 0.86, 0.78)) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = height
	cs.shape = shape
	cs.position.y = height * 0.5
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = radius * 0.9
	cm.bottom_radius = radius
	cm.height = height
	cm.radial_segments = 14
	mi.mesh = cm
	mi.position.y = height * 0.5
	mi.material_override = CharacterVisual.make_toon(color, null, CharacterVisual.outline_width_for(height))
	body.add_child(mi)
	parent.add_child(body)
	body.position = pos
	return body


## A rough boulder (squashed sphere) with collision.
static func rock(parent: Node, pos: Vector3, size := 2.0, color := Color(0.55, 0.5, 0.45)) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := SphereShape3D.new()
	shape.radius = size * 0.5
	cs.shape = shape
	body.add_child(cs)
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = size * 0.5
	sm.height = size * 0.8
	sm.radial_segments = 8
	sm.rings = 4
	mi.mesh = sm
	mi.material_override = CharacterVisual.make_toon(color, null, CharacterVisual.outline_width_for(size * 2.0))
	body.add_child(mi)
	parent.add_child(body)
	body.position = pos
	return body


static var _props_manifest: Dictionary = {}
static var _missing_props := {}


## Places a prop from res://assets/props/<prop_name>.glb (toon + outline) with collision from props.json
## (cylinder / box / collision_parts), scaled uniformly. A grey box stand-in when the file is missing.
static func prop(parent: Node, prop_name: String, pos: Vector3, yaw_deg := 0.0, scale := 1.0, collide := true) -> Node3D:
	if _props_manifest.is_empty() and FileAccess.file_exists("res://assets/props/props.json"):
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/props/props.json"))
		if d is Dictionary:
			_props_manifest = d
	var info: Dictionary = _props_manifest.get(prop_name, {})
	var size_arr: Array = info.get("size", [1.0, 1.0, 1.0])
	var height := float(size_arr[1]) * scale
	var body := StaticBody3D.new()
	body.name = "Prop_" + prop_name
	body.collision_layer = 1
	body.collision_mask = 0
	var path := "res://assets/props/%s.glb" % prop_name
	var vis: Node3D = null
	if ResourceLoader.exists(path):
		var ps := load(path) as PackedScene
		if ps != null:
			vis = ps.instantiate() as Node3D
	if vis != null:
		_toon_all(vis, CharacterVisual.outline_width_for(height))
	else:
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(size_arr[0], size_arr[1], size_arr[2])
		mi.mesh = bm
		mi.position.y = float(size_arr[1]) * 0.5
		mi.material_override = CharacterVisual.make_toon(Color(0.6, 0.6, 0.6), null, 0.02)
		vis = mi
		if info.is_empty() and not _missing_props.has(prop_name):
			_missing_props[prop_name] = true
			push_warning("EnvKit.prop: unknown prop '%s' (no %s and no props.json entry): grey 1 m box" % [prop_name, path])
			Game.event("missing_prop", {"name": prop_name})
	vis.scale = Vector3.ONE * scale
	body.add_child(vis)
	if collide:
		var parts: Array = info.get("collision_parts", [])
		if parts.is_empty():
			parts = [{"type": info.get("collision", "box"), "size": info.get("collision_size", size_arr),
				"offset": info.get("collision_offset", [0.0, float(size_arr[1]) * 0.5, 0.0])}]
		for part in parts:
			var cs := CollisionShape3D.new()
			var sz: Array = part.get("size", [1, 1, 1])
			if String(part.get("type", "box")) == "cylinder":
				var cyl := CylinderShape3D.new()
				cyl.radius = float(sz[0]) * scale
				cyl.height = float(sz[1]) * scale
				cs.shape = cyl
			else:
				var box := BoxShape3D.new()
				box.size = Vector3(sz[0], sz[1], sz[2]) * scale
				cs.shape = box
			var off: Array = part.get("offset", [0, 0, 0])
			cs.position = Vector3(off[0], off[1], off[2]) * scale
			body.add_child(cs)
	parent.add_child(body)
	body.position = pos
	body.rotation_degrees.y = yaw_deg
	return body


## Applies the toon material (keeping albedo textures) and an outline to every mesh under `n`.
static func _toon_all(n: Node, outline: float) -> void:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		var mi := n as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var src := mi.get_active_material(i)
			var col := Color.WHITE
			var tex: Texture2D = null
			if src is BaseMaterial3D:
				col = (src as BaseMaterial3D).albedo_color
				tex = (src as BaseMaterial3D).albedo_texture
			mi.set_surface_override_material(i, CharacterVisual.make_toon(col, tex, outline))
	for c in n.get_children():
		_toon_all(c, outline)
