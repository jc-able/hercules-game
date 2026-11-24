extends ArenaBase
## Scene id "hydra" (SPEC §3.3): a broad black basalt shelf (radius 34 m) over a sea of lava under an ember sky.
## Glowing cracks and the scorched arcs of the fire's reach on the floor, basalt spires and cliffs beyond the rim,
## a smoking volcano on the horizon. The centre stays open for the Hydra. Loaded by path (no class_name).

const T := Tuning.HYDRA
const BASALT := Color(0.12, 0.11, 0.12)
const FIRE_ORIGIN_FWD := 2.5      # = hydra.gd EXTRA.fire_origin_fwd (the fire arc's apex ahead of the body centre)
const ROCK_TINT := 0.15           # generated cliff/boulder props darkened to black basalt
const SHELF_EDGE := 1.5           # the shelf's edge, this far beyond the invisible boundary (radius); lava beyond it
const LAVA_Y := -0.45             # lava surface height (visible across the moat from the hero's low camera)

const FLOOR_SHADER := """
shader_type spatial;
render_mode cull_back, specular_disabled;
uniform vec3 rock_a : source_color = vec3(0.10, 0.095, 0.10);
uniform vec3 rock_b : source_color = vec3(0.17, 0.15, 0.15);
uniform vec3 glow : source_color = vec3(1.0, 0.42, 0.06);
uniform float arena_r = 34.0;
uniform float scorch_r = 30.0;
varying vec3 wpos;
vec2 h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float h1(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 15731.743); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h1(i), h1(i + vec2(1, 0)), f.x), mix(h1(i + vec2(0, 1)), h1(i + vec2(1, 1)), f.x), f.y);
}
// distance to the nearest Voronoi cell edge
float edge_dist(vec2 p) {
	vec2 n = floor(p); vec2 f = fract(p);
	vec2 mg; vec2 mr; float md = 8.0;
	for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
		vec2 g = vec2(float(i), float(j)); vec2 o = h2(n + g); vec2 r = g + o - f;
		float d = dot(r, r); if (d < md) { md = d; mr = r; mg = g; }
	}
	md = 8.0;
	for (int j = -2; j <= 2; j++) for (int i = -2; i <= 2; i++) {
		vec2 g = mg + vec2(float(i), float(j)); vec2 o = h2(n + g); vec2 r = g + o - f;
		if (dot(mr - r, mr - r) > 0.00001) md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
	}
	return md;
}
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 p = wpos.xz;
	float r = length(p);
	// qa fix (cracks were long straight Voronoi edges): domain-warp the slab pattern so the seams wander and fork,
	// and add a thin branching layer; the glow gets a soft emissive falloff around each crack
	vec2 wq = p + vec2(vnoise(p * 0.21 + 7.0), vnoise(p * 0.21 - 4.0)) * 3.2 + vec2(vnoise(p * 0.9 + 1.0), vnoise(p * 0.9 - 9.0)) * 0.7;
	float slabs = edge_dist(wq / 3.4);
	float fine = edge_dist(wq / 1.3 + 17.0);
	float n = vnoise(p * 0.35);
	vec3 col = mix(rock_a, rock_b, smoothstep(0.25, 0.9, n));
	col *= 0.8 + 0.2 * smoothstep(0.0, 0.25, slabs);                       // dark slab seams
	// glowing cracks: slab seams over most of the shelf (broken where the noise says), more toward the rim, and
	// short branching twigs off them
	float patch = smoothstep(0.30, 0.62, vnoise(p * 0.07 + 3.0)) + smoothstep(arena_r - 8.0, arena_r + 2.0, r);
	float seam = 1.0 - smoothstep(0.008, 0.032, slabs);
	float broken = smoothstep(0.35, 0.55, vnoise(wq * 0.5 + 11.0));        // the seam glows in runs, not everywhere
	float crack = seam * clamp(patch, 0.0, 1.0) * broken;
	float twig = (1.0 - smoothstep(0.008, 0.03, fine)) * smoothstep(0.55, 0.75, vnoise(wq * 0.8 - 5.0));
	crack = max(crack, twig * 0.55 * clamp(patch + 0.3, 0.0, 1.0));
	crack = max(crack, (1.0 - smoothstep(0.01, 0.035, fine)) * 0.5 * smoothstep(arena_r - 3.0, arena_r + 3.0, r));
	float halo = (1.0 - smoothstep(0.03, 0.16, slabs)) * clamp(patch, 0.0, 1.0) * broken;   // warm falloff
	// lava pools at the shelf's broken edge (beyond the walkable radius): molten inlets the cracks run into
	float pool = smoothstep(arena_r + 0.25, arena_r + 0.8, r) * smoothstep(0.5, 0.62, vnoise(vec2(atan(p.y, p.x) * 9.0, r * 0.3) + 21.0));
	float pulse = 0.8 + 0.2 * sin(TIME * 1.3 + n * 6.0);
	// scorched band at the fire's reach: soot + ember specks. The fire reaches 30 m from an apex 2.5 m ahead of the
	// body, so 30-32.5 m from the centre depending on the angle: a soft gradient from ~29 m, darkest at scorch_r (32.5)
	float band = smoothstep(scorch_r - 3.8, scorch_r - 0.3, r) * (1.0 - smoothstep(scorch_r + 0.5, scorch_r + 2.0, r));
	col = mix(col, vec3(0.04, 0.035, 0.035), band * 0.8);
	float ember = step(0.985, h1(floor(p * 2.5))) * band;
	col = mix(col, vec3(0.30, 0.07, 0.02), pool);
	ALBEDO = col;
	ROUGHNESS = 0.95;
	EMISSION = glow * (crack * 2.6 * pulse + halo * 0.22 * pulse + ember * 1.6 * pulse + pool * 1.9 * pulse);
}
"""

const LAVA_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;
uniform vec3 crust : source_color = vec3(0.16, 0.04, 0.02);
uniform vec3 hot : source_color = vec3(1.0, 0.42, 0.05);
uniform vec3 white_hot : source_color = vec3(1.0, 0.85, 0.35);
varying vec3 wpos;
float h1(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 15731.743); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h1(i), h1(i + vec2(1, 0)), f.x), mix(h1(i + vec2(0, 1)), h1(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float a = 0.5; float s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; } return s; }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 p = wpos.xz * 0.06;
	vec2 flow = vec2(TIME * 0.05, TIME * 0.03);
	float n = fbm(p + fbm(p * 1.7 - flow) * 1.3 + flow);
	float heat = smoothstep(0.38, 0.72, n);
	vec3 col = mix(crust, hot, heat);
	col = mix(col, white_hot, smoothstep(0.72, 0.9, n));
	float far = clamp(length(wpos.xz) / 900.0, 0.0, 1.0);
	ALBEDO = mix(col * (1.3 + 0.25 * sin(TIME * 0.8 + n * 9.0)), vec3(0.45, 0.16, 0.06), far * 0.6);
}
"""


func _init() -> void:
	arena_id = &"hydra"
	radius = T["arena_radius"]


func build_environment() -> void:
	# dark burnt-orange sky, no sun disc (key_hydra.png); about 40% darker than the first pass
	var env := EnvKit.sky(self, Color(0.042, 0.015, 0.015), Color(0.43, 0.155, 0.042), Color(0.17, 0.05, 0.02), 0.4, 0.3)
	var sm := env.sky.sky_material as ShaderMaterial
	if sm != null:
		sm.set_shader_parameter("cloud_color", Vector3(0.22, 0.095, 0.055))
		sm.set_shader_parameter("cloud_shade", Vector3(0.085, 0.036, 0.03))
		# hide the disc: a vanishing size (0 would make the shader's smoothstep edges equal) and a dim colour for the halo
		sm.set_shader_parameter("sun_color", Vector3(0.35, 0.13, 0.04))
		sm.set_shader_parameter("sun_size", 0.0001)
	env.fog_light_color = Color(0.30, 0.11, 0.05)
	env.fog_density = 0.0022
	env.glow_intensity = 0.6
	env.glow_bloom = 0.12
	env.tonemap_exposure = 0.95
	# qa fix: a whiter sun (was 1.0/0.78/0.6): the orange one turned the Hydra's violet maroon (hydra.gd adds a violet
	# fill on the boss only); the warmth stays in the sky, the lava fill and the rim lights
	var sun := EnvKit.sun(self, Vector3(-32, 160, 0), Color(1.0, 0.89, 0.80), 1.0)
	sun.directional_shadow_max_distance = 120.0
	# lava glow from below the rim: a soft warm fill light from the ground up
	var fill := DirectionalLight3D.new()
	fill.name = "LavaFill"
	fill.rotation_degrees = Vector3(35, -20, 0)
	fill.light_color = Color(1.0, 0.4, 0.12)
	fill.light_energy = 0.35
	fill.shadow_enabled = false
	add_child(fill)
	# the collision floor stays EnvKit's; its wide grey-box disc (radius + 4..6) would hide the lava moat, so the shelf
	# is drawn here instead (radius + SHELF_EDGE, with a basalt cliff face dropping into the lava)
	var fl := EnvKit.floor_disc(self, radius, BASALT)
	for c in fl.get_children():
		if c is MeshInstance3D:
			(c as MeshInstance3D).visible = false
	_crack_floor()
	_shelf_face()
	_lava()
	_rim()
	_horizon()
	_embers()
	_ambience()


## The visible shelf top: basalt slabs with glowing cracks and the scorched band at the fire's reach (no collision;
## EnvKit.floor_disc below carries it).
func _crack_floor() -> void:
	var mi := MeshInstance3D.new()
	mi.name = "Shelf"
	var cm := CylinderMesh.new()
	cm.top_radius = radius + SHELF_EDGE
	cm.bottom_radius = radius + SHELF_EDGE
	cm.height = 0.02
	cm.radial_segments = 128
	cm.rings = 1
	mi.mesh = cm
	var m := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = FLOOR_SHADER
	m.shader = sh
	m.set_shader_parameter("arena_r", radius)
	m.set_shader_parameter("scorch_r", float(T["fire_reach"]) + FIRE_ORIGIN_FWD)
	mi.material_override = m
	mi.position.y = 0.0
	add_child(mi)


## The shelf's cliff face: dark basalt dropping from the floor into the lava (seen across the moat from the arena).
func _shelf_face() -> void:
	var mi := MeshInstance3D.new()
	mi.name = "ShelfFace"
	var cm := CylinderMesh.new()
	cm.top_radius = radius + SHELF_EDGE
	cm.bottom_radius = radius + SHELF_EDGE + 1.6
	cm.height = 2.4
	cm.radial_segments = 128
	cm.cap_top = false
	mi.mesh = cm
	mi.material_override = CharacterVisual.make_toon(Color(0.09, 0.08, 0.085), null, 0.0, 0.15)
	add_child(mi)
	mi.position.y = -1.2 + 0.005


func _lava() -> void:
	var pm := PlaneMesh.new()
	pm.size = Vector2(2400, 2400)
	var mi := MeshInstance3D.new()
	mi.name = "Lava"
	mi.mesh = pm
	var m := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = LAVA_SHADER
	m.shader = sh
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = LAVA_Y
	add_child(mi)
	# glow lights along the rim so the lava lights the shelf's edge and the beast's flanks
	for i in 6:
		var a := TAU * float(i) / 6.0 + 0.4
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.42, 0.1)
		l.light_energy = 1.6
		l.omni_range = 16.0
		l.shadow_enabled = false
		add_child(l)
		l.position = Vector3(sin(a) * (radius + 6.0), 0.8, cos(a) * (radius + 6.0))


## Set dressing on and beyond the rim (outside the fighting lane): columnar basalt and spires standing in the lava.
## qa fix: the stacked rounded cliff_rock / boulder props read as cardboard blocks; now clusters of jagged hex basalt
## columns (key_hydra's columnar cliffs) with the basalt_spire props between them, each lit from below by the lava.
func _rim() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 3313
	var n := 22
	for i in n:
		var a := TAU * (float(i) + rng.randf_range(-0.25, 0.25)) / float(n)
		# beyond a lava moat (shelf edge radius + SHELF_EDGE, props from radius + 8): the glowing lava band of key_hydra
		var r := radius + 8.0 + rng.randf_range(0.0, 5.0)
		var pos := Vector3(sin(a) * r, LAVA_Y - 0.4, cos(a) * r)     # standing in the lava
		if i % 3 == 1:
			EnvKit.prop(self, "basalt_spire", pos, rng.randf_range(0, 360), rng.randf_range(0.8, 1.6))
		else:
			_columns(pos, a, rng, rng.randf_range(4.0, 9.0) if i % 3 == 0 else rng.randf_range(2.0, 4.5))
	# a few tall spires standing in the lava just off the shelf
	for i in 9:
		var a2 := TAU * (float(i) + 0.5) / 9.0 + rng.randf_range(-0.2, 0.2)
		var r2 := radius + rng.randf_range(10.0, 22.0)
		EnvKit.prop(self, "basalt_spire", Vector3(sin(a2) * r2, -0.6, cos(a2) * r2), rng.randf_range(0, 360), rng.randf_range(1.6, 3.2), false)


## A cluster of jagged hexagonal basalt columns standing in the lava at `pos` (one mesh, flat faces, ink outline), with
## a warm lava light at its foot so the undersides glow. `h` = height of the tallest column.
func _columns(pos: Vector3, ang: float, rng: RandomNumberGenerator, h: float, sc := 1.0, lit := true) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tang := Vector3(cos(ang), 0.0, -sin(ang))        # along the rim
	var radial := Vector3(sin(ang), 0.0, cos(ang))       # outward
	var count := rng.randi_range(5, 9)
	for k in count:
		var off := (tang * rng.randf_range(-3.2, 3.2) + radial * rng.randf_range(-1.2, 2.0)) * sc
		var rad := rng.randf_range(0.55, 1.05) * sc
		var ch := h * rng.randf_range(0.45, 1.0) * (1.0 - 0.35 * absf(off.dot(tang)) / (3.2 * sc))
		var lean := Vector3(rng.randf_range(-0.12, 0.12), 0.0, rng.randf_range(-0.12, 0.12)) * ch
		var top_tilt := Vector2(rng.randf_range(-0.35, 0.35), rng.randf_range(-0.35, 0.35))
		var spin := rng.randf_range(0.0, TAU)
		var ring_b: Array[Vector3] = []
		var ring_t: Array[Vector3] = []
		for s in 6:
			var t := spin + TAU * float(s) / 6.0
			var rr := rad * rng.randf_range(0.82, 1.12)          # jagged, not a perfect prism
			var v := Vector3(cos(t) * rr, 0.0, sin(t) * rr)
			ring_b.append(off + v * 1.15)
			ring_t.append(off + lean + v * rng.randf_range(0.85, 1.0) + Vector3(0.0, ch + v.x * top_tilt.x + v.z * top_tilt.y, 0.0))
		for s in 6:
			var s2 := (s + 1) % 6
			_quad(st, ring_b[s], ring_b[s2], ring_t[s2], ring_t[s], off + lean * 0.5 + Vector3(0.0, ch * 0.5, 0.0))
		var cen := Vector3.ZERO
		for q in ring_t:
			cen += q
		cen /= 6.0
		for s in 6:
			_tri(st, cen, ring_t[(s + 1) % 6], ring_t[s], cen - Vector3(0.0, ch, 0.0))
	var mi := MeshInstance3D.new()
	mi.name = "BasaltColumns"
	mi.mesh = st.commit()
	mi.material_override = CharacterVisual.make_toon(Color(0.11, 0.095, 0.10), null, CharacterVisual.outline_width_for(h), 0.12)
	add_child(mi)
	mi.position = pos
	if not lit:
		return
	var l := OmniLight3D.new()
	l.light_color = Color(1.0, 0.40, 0.08)
	l.light_energy = 1.3
	l.omni_range = 7.5
	l.shadow_enabled = false
	add_child(l)
	l.position = pos + Vector3(0.0, 0.9, 0.0) - radial * 2.0     # on the lava between the column foot and the shelf


## One flat triangle facing away from `inside` (Godot front faces wind clockwise seen from the front).
func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, inside: Vector3) -> void:
	var cw := (c - a).cross(b - a)          # = the front normal of a clockwise a, b, c
	var out := (a + b + c) / 3.0 - inside
	if cw.dot(out) < 0.0:
		var tmp := b
		b = c
		c = tmp
		cw = -cw
	var nrm := cw.normalized()
	for v in [a, b, c]:
		st.set_normal(nrm)
		st.add_vertex(v)


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, inside: Vector3) -> void:
	_tri(st, a, b, c, inside)
	_tri(st, a, c, d, inside)


## The generated cliff/boulder props are sandy quarry stone: darken them to basalt (toon `tint` uniform).
func _basalt(n: Node, k := ROCK_TINT) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.mesh != null:
			for i in mi.mesh.get_surface_count():
				var m := mi.get_surface_override_material(i)
				if m is ShaderMaterial:
					(m as ShaderMaterial).set_shader_parameter("tint", Color(k, k * 0.88, k * 0.9))
		if mi.material_override is ShaderMaterial:
			(mi.material_override as ShaderMaterial).set_shader_parameter("tint", Color(k, k * 0.88, k * 0.9))
	for c in n.get_children():
		_basalt(c, k)


## Far cliffs ringing the lava sea and a smoking volcano behind the beast (the hero looks north from the spawn).
func _horizon() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 909
	for i in 26:
		var a := TAU * float(i) / 26.0 + rng.randf_range(-0.08, 0.08)
		var r := rng.randf_range(120.0, 190.0)
		# qa fix: columnar basalt cliffs (key_hydra) instead of the giant rounded cliff_rock blocks
		_columns(Vector3(sin(a) * r, -2.0, cos(a) * r), a, rng, rng.randf_range(22.0, 48.0), rng.randf_range(4.0, 7.0), false)
	# the volcano
	var cone := MeshInstance3D.new()
	cone.name = "Volcano"
	var cm := CylinderMesh.new()
	cm.top_radius = 38.0
	cm.bottom_radius = 230.0
	cm.height = 170.0
	cm.radial_segments = 24
	cone.mesh = cm
	cone.material_override = CharacterVisual.make_toon(Color(0.14, 0.10, 0.10), null, 0.0, 0.1)
	add_child(cone)
	cone.position = Vector3(40.0, 82.0, -470.0)
	var crater := MeshInstance3D.new()
	var dm := CylinderMesh.new()
	dm.top_radius = 33.0
	dm.bottom_radius = 33.0
	dm.height = 0.5
	crater.mesh = dm
	var cmat := StandardMaterial3D.new()
	cmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	cmat.albedo_color = Color(1.6, 0.7, 0.15)
	crater.material_override = cmat
	cone.add_child(crater)
	crater.position.y = 85.2
	var smoke := CPUParticles3D.new()
	smoke.name = "VolcanoSmoke"
	smoke.amount = 60
	smoke.lifetime = 14.0
	smoke.preprocess = 14.0
	smoke.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	smoke.emission_sphere_radius = 18.0
	smoke.direction = Vector3(0.25, 1, 0)
	smoke.spread = 12.0
	smoke.initial_velocity_min = 6.0
	smoke.initial_velocity_max = 10.0
	smoke.gravity = Vector3(1.0, 0.5, 0)
	var curve := Curve.new()
	curve.max_value = 3.0
	curve.add_point(Vector2(0, 1.0))
	curve.add_point(Vector2(1, 3.0))
	smoke.scale_amount_curve = curve
	var g := Gradient.new()
	g.set_color(0, Color(0.45, 0.22, 0.12, 0.8))
	g.set_color(1, Color(0.12, 0.08, 0.08, 0.0))
	smoke.color_ramp = g
	var qm := QuadMesh.new()
	qm.size = Vector2(26, 26)
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.vertex_color_use_as_albedo = true
	sm.vertex_color_is_srgb = true
	sm.albedo_texture = Fx.soft_dot()
	qm.material = sm
	smoke.mesh = qm
	add_child(smoke)
	smoke.position = cone.position + Vector3(0, 88.0, 0)


## Embers drifting up from the lava across the whole shelf.
func _embers() -> void:
	var p := CPUParticles3D.new()
	p.name = "Embers"
	p.amount = 160
	p.lifetime = 7.0
	p.preprocess = 7.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(radius + 12.0, 1.0, radius + 12.0)
	p.direction = Vector3.UP
	p.spread = 35.0
	p.initial_velocity_min = 0.8
	p.initial_velocity_max = 2.2
	p.gravity = Vector3(0.3, 0.25, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.2
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.7, 0.25, 0.0))
	g.set_color(1, Color(1.0, 0.3, 0.05, 0.0))
	g.add_point(0.15, Color(1.0, 0.65, 0.2, 1.0))
	g.add_point(0.7, Color(1.0, 0.35, 0.08, 0.8))
	p.color_ramp = g
	var qm := QuadMesh.new()
	qm.size = Vector2(0.12, 0.12)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.albedo_texture = Fx.soft_dot()
	qm.material = m
	p.mesh = qm
	add_child(p)
	p.position = Vector3(0, 0.5, 0)


## Bubbling lava loop (Sfx loop owned by the arena: it stops when the arena is freed).
func _ambience() -> void:
	Sfx.loop("lava_loop", self)


func spawn_boss() -> BossBase:
	var b: BossBase = load("res://scripts/bosses/hydra.gd").new()
	b.name = "Hydra"
	b.position = Vector3(0, 0.05, 0)
	return b


func player_spawn() -> Vector3:
	return Vector3(0, 0.1, 20.0)
