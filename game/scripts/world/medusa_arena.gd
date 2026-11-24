extends ArenaBase
## Scene id "medusa": the sanctuary island (SPEC §3.2, keyframe art_src/reference_video/key_medusa.png).
## A pale veined-marble courtyard (radius 28 m) with inlaid rings, a raised step at the lane edge carrying the
## petrified warriors, a ring of columns under a continuous entablature, a tall curved wall behind the north half
## and a low parapet on the south half so the sea shows through. Everything decorative sits OUTSIDE the fighting
## lane (ArenaBase's invisible boundary is at radius + 0.5). No class_name (loaded by path).

const BOSS_SCRIPT := "res://scripts/bosses/medusa.gd"

# QA fixer: the floor read nearly flat white (hero + decals carried all the contrast): marble albedo ~0.8, warm, and
# a darker shadow band on the marble pieces (MARBLE_SHADE: toon shade_dark / shade_mid, default 0.42 / 0.74)
const MARBLE := Color(0.81, 0.78, 0.73)
const MARBLE_SHADE := Vector2(0.34, 0.66)
const INLAY := Color(0.46, 0.51, 0.58)
const INLAY_GOLD := Color(0.70, 0.57, 0.31)
const STEP := Color(0.76, 0.74, 0.70)
const WALL := Color(0.60, 0.64, 0.71)
const WALL_DARK := Color(0.45, 0.49, 0.57)
const PLATEAU := Color(0.80, 0.78, 0.72)
const GRASS := Color(0.56, 0.63, 0.40)
const CLIFF := Color(0.62, 0.60, 0.56)

const STEP_R := Vector2(28.0, 30.6)        # raised step (inner, outer)
const STEP_H := 0.35
const STATUE_R := 36.4                     # in the column bays: the lock camera reaches ~34.6 m from the centre
const COLUMN_R := 36.6
const COLUMN_SCALE := 1.35                 # 8.1 m columns: the courtyard reads enclosed, like the keyframe
const COLUMN_COUNT := 28
const WALL_R := 39.6
const WALL_H := 11.0
const PARAPET_H := 1.3
const ENTAB_Y := Vector2(8.1, 9.2)         # entablature bottom / top (props column = 6.0 m x COLUMN_SCALE)
const GATE_HALF_DEG := 9.0                 # no columns this close to the south / north axis (gates there)

var _marble_tex: Texture2D
var _stone_tex: Texture2D


func _init() -> void:
	arena_id = &"medusa"
	radius = float(Tuning.MEDUSA["arena_radius"])


func build_environment() -> void:
	var env := EnvKit.sky(self, Color(0.17, 0.39, 0.80), Color(0.74, 0.83, 0.92), Color(0.36, 0.52, 0.68), 0.40, 0.22)
	env.fog_density = 0.0011
	env.tonemap_exposure = 0.86
	EnvKit.sun(self, Vector3(-52, -28, 0), Color(1.0, 0.96, 0.90), 1.05)
	_marble_tex = _noise_tex(Color(0.80, 0.80, 0.82), 0.010, 42, true)
	_stone_tex = _noise_tex(Color(0.86, 0.86, 0.88), 0.020, 7, false)
	# floor: EnvKit collision, our own planar-UV marble disc on top (the kit's cylinder cap is hidden)
	var floor_body := EnvKit.floor_disc(self, radius, MARBLE)
	for c in floor_body.get_children():
		if c is MeshInstance3D:
			(c as MeshInstance3D).visible = false
	_mesh(_disc(STEP_R.x + 0.05, 128, 0.0, 14.0), _shade(CharacterVisual.make_toon(MARBLE, _marble_tex, 0.0, 0.0)), "MarbleFloor")
	_build_inlays()
	_build_step()
	_build_island()
	EnvKit.sea(self, 3000.0, -12.0)
	Sfx.loop("sea_loop", self, -3.0)  # the sea far below the sanctuary (stops with the arena)
	_build_colonnade()
	_build_walls()
	_build_statues()
	_build_braziers()
	_build_outer_dressing()


func spawn_boss() -> BossBase:
	var b: BossBase = load(BOSS_SCRIPT).new()
	b.name = "Medusa"
	b.position = Vector3(0, 0.05, -3.0)       # centre, facing the hero (+Z); the tail lies toward the north wall
	return b


func player_spawn() -> Vector3:
	# in the south lane, 7 m in from the floor's edge: inside her 17 m stalk area + 6.3 m close-in range, so even a hero
	# who stands still is gazed from close (she towers on screen), not from the 7.6 m the stalk area allowed at 24 m
	return Vector3(0, 0.1, radius - 7.0)


# ------------------------------------------------------------------ pieces
func _build_inlays() -> void:
	var dark := _flat(INLAY)
	var gold := _flat(INLAY_GOLD)
	_mesh(_annulus(27.15, 27.55, 160, 0.012), dark, "InlayEdge")
	_mesh(_annulus(26.6, 26.75, 160, 0.012), gold, "InlayEdgeGold")
	_mesh(_annulus(16.0, 16.3, 128, 0.012), dark, "InlayMid")
	_mesh(_annulus(7.0, 7.25, 96, 0.012), gold, "InlayInner")
	_mesh(_annulus(3.2, 3.45, 64, 0.012), dark, "InlayCentre")
	# sixteen short spokes between the middle and the edge ring (a sun pattern, like a sanctuary pavement)
	for i in 16:
		var a := TAU * float(i) / 16.0
		var mi := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(0.22, 10.6)
		mi.mesh = pm
		mi.material_override = dark if i % 2 == 0 else gold
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = Vector3(sin(a) * 21.6, 0.012, cos(a) * 21.6)
		mi.rotation.y = a
		add_child(mi)


func _build_step() -> void:
	var m := _shade(CharacterVisual.make_toon(STEP, _stone_tex, 0.0, 0.0))
	_mesh(_ring_wall(STEP_R.x, STEP_R.y, 0.0, STEP_H, 160), m, "Step")
	# a second, wider low tier under the columns
	_mesh(_ring_wall(STEP_R.y, WALL_R + 1.0, 0.0, STEP_H + 0.25, 160), _shade(CharacterVisual.make_toon(STEP.darkened(0.06), _stone_tex, 0.0, 0.0)), "Tier")


func _build_island() -> void:
	# plateau the sanctuary stands on, its cliff dropping into the sea
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 78.0
	cm.bottom_radius = 66.0
	cm.height = 40.0
	cm.radial_segments = 64
	mi.mesh = cm
	mi.position.y = -20.02
	mi.material_override = CharacterVisual.make_toon(CLIFF, null, 0.0, 0.0)
	mi.name = "Island"
	add_child(mi)
	_mesh(_annulus(WALL_R + 0.9, 46.0, 96, -0.01), CharacterVisual.make_toon(PLATEAU, _stone_tex, 0.0, 0.0), "Paving")
	_mesh(_annulus(46.0, 78.2, 96, -0.01), CharacterVisual.make_toon(GRASS, null, 0.0, 0.0), "Grass")


func _build_colonnade() -> void:
	var top_y := STEP_H + 0.25
	for i in COLUMN_COUNT:
		var a := TAU * (float(i) + 0.5) / float(COLUMN_COUNT)
		if _near_axis(a, GATE_HALF_DEG):
			continue
		var pos := Vector3(sin(a) * COLUMN_R, top_y, cos(a) * COLUMN_R)
		EnvKit.prop(self, "column", pos, rad_to_deg(a), COLUMN_SCALE, false)
	# continuous entablature (architrave + cornice) over the columns
	var ent := CharacterVisual.make_toon(STEP, _stone_tex, CharacterVisual.outline_width_for(6.0), 0.0)
	_mesh(_ring_wall(COLUMN_R - 1.5, COLUMN_R + 1.5, top_y + ENTAB_Y.x, top_y + ENTAB_Y.y, 128), ent, "Architrave")
	_mesh(_ring_wall(COLUMN_R - 1.85, COLUMN_R + 1.85, top_y + ENTAB_Y.y, top_y + ENTAB_Y.y + 0.35, 128), ent, "Cornice")
	# gates on the south (entrance) and north axes
	EnvKit.prop(self, "gate", Vector3(0, top_y, COLUMN_R), 0.0, COLUMN_SCALE, false)
	EnvKit.prop(self, "gate", Vector3(0, top_y, -COLUMN_R), 180.0, COLUMN_SCALE, false)


func _build_walls() -> void:
	# tall curved wall behind the north half (110..250 deg), low parapet on the rest: the sea shows over it
	var tall := CharacterVisual.make_toon(WALL, _stone_tex, CharacterVisual.outline_width_for(WALL_H), 0.0)
	var low := CharacterVisual.make_toon(WALL, _stone_tex, CharacterVisual.outline_width_for(2.0), 0.0)
	var y0 := STEP_H + 0.25
	_mesh(_ring_wall(WALL_R, WALL_R + 1.0, y0, y0 + WALL_H, 64, deg_to_rad(110.0), deg_to_rad(250.0)), tall, "WallNorth")
	_mesh(_ring_wall(WALL_R - 0.2, WALL_R + 1.2, y0 + WALL_H, y0 + WALL_H + 0.45, 64, deg_to_rad(110.0), deg_to_rad(250.0)), _flat_toon(WALL_DARK), "WallCap")
	_mesh(_ring_wall(WALL_R, WALL_R + 0.8, y0, y0 + PARAPET_H, 96, deg_to_rad(-110.0), deg_to_rad(110.0)), low, "Parapet")
	# shallow niches (dark panels) along the tall wall, one between each pair of columns
	for i in COLUMN_COUNT:
		var a := TAU * float(i) / float(COLUMN_COUNT)
		var deg := fposmod(rad_to_deg(a), 360.0)
		if deg < 118.0 or deg > 242.0 or absf(deg - 180.0) < GATE_HALF_DEG + 4.0:
			continue
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(2.6, 5.6, 0.12)
		mi.mesh = bm
		mi.material_override = _flat_toon(WALL_DARK)
		mi.position = Vector3(sin(a) * (WALL_R - 0.04), y0 + 3.6, cos(a) * (WALL_R - 0.04))
		mi.rotation.y = a
		add_child(mi)


func _build_statues() -> void:
	# petrified warriors on plinths in the column bays, facing the centre (well outside the lane)
	var y := STEP_H + 0.25
	for i in COLUMN_COUNT:
		var a := TAU * float(i) / float(COLUMN_COUNT)
		if _near_axis(a, GATE_HALF_DEG + 4.0):
			continue
		var pos := Vector3(sin(a) * STATUE_R, y, cos(a) * STATUE_R)
		EnvKit.prop(self, "pedestal", pos, 0.0, 0.9, false)
		EnvKit.prop(self, "statue_a" if i % 2 == 0 else "statue_b", pos + Vector3.UP * 0.97, rad_to_deg(a) + 180.0, 1.3, false)
		if i % 5 == 2:
			var side := Vector3(cos(a), 0, -sin(a)) * 1.6
			EnvKit.prop(self, "amphora", pos + side - Vector3(sin(a), 0, cos(a)) * 1.2, rad_to_deg(a) + 30.0, 0.8, false)


func _build_braziers() -> void:
	for deg in [45.0, 135.0, 225.0, 315.0]:
		var a := deg_to_rad(deg)
		var pos := Vector3(sin(a) * 31.6, STEP_H + 0.25, cos(a) * 31.6)
		EnvKit.prop(self, "brazier", pos, 0.0, 1.3, false)
		_fire(pos + Vector3(0, 0.9 * 1.3, 0))
		Sfx.loop("fire_loop", pos + Vector3(0, 1.2, 0))   # crackle at each brazier (positional, dies with the scene)


func _build_outer_dressing() -> void:
	EnvKit.prop(self, "temple", Vector3(0, 0, -56.0), 0.0, 1.25, false)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2207
	for i in 18:
		var a := TAU * float(i) / 18.0 + rng.randf_range(-0.12, 0.12)
		var r := rng.randf_range(42.0, 64.0)
		var pos := Vector3(sin(a) * r, 0, cos(a) * r)
		if pos.distance_to(Vector3(0, 0, -56.0)) < 12.0:
			continue
		if i % 3 == 2:
			EnvKit.prop(self, "olive_tree", pos, rng.randf_range(0, 360), rng.randf_range(0.9, 1.2), false)
		else:
			EnvKit.prop(self, "cypress", pos, rng.randf_range(0, 360), rng.randf_range(0.85, 1.25), false)


func _fire(pos: Vector3) -> void:
	var p := GPUParticles3D.new()
	p.name = "BrazierFire"
	p.amount = 28
	p.lifetime = 0.7
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 0.28
	pm.direction = Vector3.UP
	pm.spread = 12.0
	pm.initial_velocity_min = 0.6
	pm.initial_velocity_max = 1.3
	pm.gravity = Vector3(0, 1.6, 0)
	pm.scale_min = 0.6
	pm.scale_max = 1.0
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.5))
	curve.add_point(Vector2(0.3, 1.0))
	curve.add_point(Vector2(1, 0.0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	var grad := Gradient.new()
	grad.set_color(0, Color(1.0, 0.85, 0.35, 1.0))
	grad.set_color(1, Color(0.9, 0.25, 0.05, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = grad
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.55, 0.7)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = Fx.soft_dot()
	q.material = m
	p.draw_pass_1 = q
	p.position = pos
	add_child(p)
	# no OmniLight3D: the toon light() adds its shade_dark floor to every pixel of the light's cluster tiles
	# (pale screen rectangles); the flame is emissive enough on its own (core note in docs/notes/medusa.md)


# ------------------------------------------------------------------ mesh helpers
func _near_axis(a: float, half_deg: float) -> bool:
	var deg := fposmod(rad_to_deg(a), 360.0)
	return deg < half_deg or deg > 360.0 - half_deg or absf(deg - 180.0) < half_deg


func _mesh(m: Mesh, mat: Material, n: String) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = n
	mi.mesh = m
	mi.material_override = mat
	add_child(mi)
	return mi


func _flat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = c
	return m


## Darker shadow band for the pale marble (shadows of the hero and Medusa read on the floor).
func _shade(m: ShaderMaterial) -> ShaderMaterial:
	m.set_shader_parameter("shade_dark", MARBLE_SHADE.x)
	m.set_shader_parameter("shade_mid", MARBLE_SHADE.y)
	return m


func _flat_toon(c: Color) -> ShaderMaterial:
	return CharacterVisual.make_toon(c, null, 0.0, 0.0)


## Veined-marble (or plain stone) albedo from a warped noise; seamless so planar UVs can repeat it.
func _noise_tex(vein: Color, freq: float, seed_v: int, veins: bool) -> NoiseTexture2D:
	var n := FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.seed = seed_v
	n.frequency = freq
	n.fractal_type = FastNoiseLite.FRACTAL_FBM
	n.fractal_octaves = 5
	n.domain_warp_enabled = veins
	n.domain_warp_amplitude = 40.0
	n.domain_warp_frequency = 0.01
	var g := Gradient.new()
	if veins:
		g.offsets = PackedFloat32Array([0.0, 0.44, 0.49, 0.51, 0.56, 1.0])
		g.colors = PackedColorArray([Color.WHITE, Color(0.97, 0.97, 0.97), vein, vein.lightened(0.05), Color(0.97, 0.97, 0.97), Color(0.99, 0.99, 0.98)])
	else:
		g.offsets = PackedFloat32Array([0.0, 1.0])
		g.colors = PackedColorArray([vein, Color.WHITE])
	var t := NoiseTexture2D.new()
	t.width = 512
	t.height = 512
	t.seamless = true
	t.noise = n
	t.color_ramp = g
	return t


## Adds a triangle facing `nrm` (Godot front faces wind clockwise: flip when the right-hand normal points along nrm).
func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, nrm: Vector3, uv_scale: float) -> void:
	if (b - a).cross(c - a).dot(nrm) > 0.0:
		var t := b
		b = c
		c = t
	for v in [a, b, c]:
		st.set_normal(nrm)
		st.set_uv(Vector2(v.x, v.z) / uv_scale if absf(nrm.y) > 0.5 else Vector2(atan2(v.x, v.z) * 6.0, v.y) / uv_scale)
		st.add_vertex(v)


func _disc(r: float, segs: int, y: float, uv_scale: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c := Vector3(0, y, 0)
	for i in segs:
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(i + 1) / float(segs)
		_tri(st, c, Vector3(sin(a0) * r, y, cos(a0) * r), Vector3(sin(a1) * r, y, cos(a1) * r), Vector3.UP, uv_scale)
	return st.commit()


func _annulus(r0: float, r1: float, segs: int, y: float, uv_scale := 8.0) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in segs:
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(i + 1) / float(segs)
		var p00 := Vector3(sin(a0) * r0, y, cos(a0) * r0)
		var p01 := Vector3(sin(a1) * r0, y, cos(a1) * r0)
		var p10 := Vector3(sin(a0) * r1, y, cos(a0) * r1)
		var p11 := Vector3(sin(a1) * r1, y, cos(a1) * r1)
		_tri(st, p00, p10, p11, Vector3.UP, uv_scale)
		_tri(st, p00, p11, p01, Vector3.UP, uv_scale)
	return st.commit()


## A thick ring (or an arc a0..a1): flat top at y1, inner wall facing the centre, outer wall facing out, end caps.
func _ring_wall(r0: float, r1: float, y0: float, y1: float, segs: int, a_start := 0.0, a_end := TAU) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var uvs := 6.0
	for i in segs:
		var a0 := lerpf(a_start, a_end, float(i) / float(segs))
		var a1 := lerpf(a_start, a_end, float(i + 1) / float(segs))
		var d0 := Vector3(sin(a0), 0, cos(a0))
		var d1 := Vector3(sin(a1), 0, cos(a1))
		var dm := (d0 + d1).normalized()
		# top
		_tri(st, d0 * r0 + Vector3.UP * y1, d0 * r1 + Vector3.UP * y1, d1 * r1 + Vector3.UP * y1, Vector3.UP, uvs)
		_tri(st, d0 * r0 + Vector3.UP * y1, d1 * r1 + Vector3.UP * y1, d1 * r0 + Vector3.UP * y1, Vector3.UP, uvs)
		# inner wall (faces the centre) and outer wall
		for side in [[r0, -dm], [r1, dm]]:
			var r: float = side[0]
			var n: Vector3 = side[1]
			_tri(st, d0 * r + Vector3.UP * y0, d1 * r + Vector3.UP * y0, d1 * r + Vector3.UP * y1, n, uvs)
			_tri(st, d0 * r + Vector3.UP * y0, d1 * r + Vector3.UP * y1, d0 * r + Vector3.UP * y1, n, uvs)
	if a_end - a_start < TAU - 0.001:
		for e in [[a_start, -1.0], [a_end, 1.0]]:
			var a: float = e[0]
			var d := Vector3(sin(a), 0, cos(a))
			var n := Vector3(cos(a), 0, -sin(a)) * float(e[1]) * -1.0
			_tri(st, d * r0 + Vector3.UP * y0, d * r1 + Vector3.UP * y0, d * r1 + Vector3.UP * y1, n, uvs)
			_tri(st, d * r0 + Vector3.UP * y0, d * r1 + Vector3.UP * y1, d * r0 + Vector3.UP * y1, n, uvs)
	return st.commit()
