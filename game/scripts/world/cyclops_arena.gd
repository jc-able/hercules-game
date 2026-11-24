extends ArenaBase
## Scene id "cyclops": the quarry island arena (SPEC §3.1, keyframe art_src/reference_video/key_cyclops.png).
## A 30 m ring of packed earth with a low marble curb, on a sunlit plateau above the sea. Ruined colonnades and broken
## columns stand on the terrace OUTSIDE the curb, a quarry face of stacked sandstone closes the south side (behind the
## hero's start), and the open sea lies north, behind the giant. Loaded by path (Game.BUILDERS), no class_name (SPEC §10).

const BOSS_SCRIPT := preload("res://scripts/bosses/cyclops.gd")

const EARTH := Color(0.58, 0.42, 0.29)       # darker packed brown, as in key_cyclops.png
const MARBLE := Color(0.90, 0.87, 0.80)
const SANDSTONE := Color(0.84, 0.72, 0.55)
const CLIFF := Color(0.72, 0.60, 0.46)
const TERRACE := Color(0.80, 0.74, 0.64)
const SEA_Y := -12.0
const PLATEAU_R := 47.0
const AMBIENT := 0.26
## Play-test: the colonnades read tiny on the far rim (key_cyclops frames the giant between big ruins close by).
## The framing colonnades stand just outside the curb (r 33-34 m, ~20-25 m from the lock camera across the ring) at
## 1.4x scale (8.4 m columns), with gaps between them for the sea.
const COLONNADE_SCALE := 1.4

var _rng := RandomNumberGenerator.new()


func _init() -> void:
	arena_id = &"cyclops"
	radius = float(Tuning.CYCLOPS["arena_radius"])


func build_environment() -> void:
	_rng.seed = 7071          # the set dressing is the same every run
	# sky ambient 0.34 -> 0.26 (play-test: the blue sky light lifted the giant's shadow band toward a pale lavender)
	var env := EnvKit.sky(self, Color(0.10, 0.40, 0.86), Color(0.66, 0.83, 0.96), Color(0.20, 0.45, 0.70), AMBIENT, 0.12)
	env.fog_density = 0.0009
	EnvKit.sun(self, Vector3(-46, -28, 0), Color(1.0, 0.94, 0.82), 1.15)
	_floor()
	_plateau()
	_curb()
	EnvKit.sea(self, 3000.0, SEA_Y)
	Sfx.loop("sea_loop", self)        # surf below the seaside quarry (stops with the arena)
	_colonnades()
	_ruins()
	_quarry_face()
	_quarry_wall()
	_trees()
	_sea_stacks()
	_near_fade_dressing()


## Final check open item 4: pushed to the rim, the lock camera sits outside the ring (r ~32.5 m, 1.2 m high) and the
## marble curb between it and the hero filled the bottom ~25-55 % of the frame (DEFEATED view too); rim ruins and
## colonnade drums could do the same. Every dressing body (curb, ruins, colonnades, quarry blocks, props; not the floor)
## gets core's toon/ink near fade: gone closer than RIM_NEAR_HIDE m to the camera, dithered in up to RIM_NEAR_FULL m.
## Inside the ring the camera never comes that close to any of it, so normal play is unchanged.
const RIM_NEAR_HIDE := 2.6
const RIM_NEAR_FULL := 4.6


func _near_fade_dressing() -> void:
	var shaders := [CharacterVisual.TOON_SHADER, CharacterVisual.toon_shader(true), CharacterVisual.OUTLINE_SHADER]
	for body in get_children():
		if not body is StaticBody3D or body.name == "Floor":
			continue
		var stack: Array[Node] = [body]
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			stack.append_array(n.get_children())
			if not n is MeshInstance3D:
				continue
			var mi := n as MeshInstance3D
			var mats: Array = [mi.material_override]
			if mi.mesh != null:
				for i in mi.mesh.get_surface_count():
					mats.append(mi.get_surface_override_material(i))
			for first in mats:
				var m: Variant = first
				while m is ShaderMaterial:
					var sm := m as ShaderMaterial
					if sm.shader in shaders:
						sm.set_shader_parameter("near_fade_hide", RIM_NEAR_HIDE)
						sm.set_shader_parameter("near_fade_full", RIM_NEAR_FULL)
					m = sm.next_pass


# ------------------------------------------------------------------ ground
## Packed earth: EnvKit's floor disc (collision) with a mottled noise texture.
func _floor() -> void:
	var body := EnvKit.floor_disc(self, radius, EARTH)
	var noise := FastNoiseLite.new()
	noise.seed = 31
	noise.frequency = 0.012
	noise.fractal_octaves = 4
	var ramp := Gradient.new()
	ramp.set_color(0, Color(0.70, 0.66, 0.62))
	ramp.set_color(1, Color(1.0, 1.0, 1.0))
	ramp.add_point(0.5, Color(0.90, 0.88, 0.85))
	var tex := NoiseTexture2D.new()
	tex.width = 512
	tex.height = 512
	tex.seamless = true
	tex.noise = noise
	tex.color_ramp = ramp
	for c in body.get_children():
		if c is MeshInstance3D:
			(c as MeshInstance3D).material_override = CharacterVisual.make_toon(EARTH, tex, 0.0, 0.0)
	# darker scuffs, pale dusty patches and reddish quarry dirt break up the big disc (flat, no collision)
	for i in 18:
		var a := _rng.randf() * TAU
		var d := _rng.randf_range(4.0, radius - 3.0)
		var col := EARTH.darkened(0.12) if i % 3 == 0 else (EARTH.lightened(0.09) if i % 3 == 1 else Color(0.62, 0.40, 0.26))
		_flat_patch(Vector3(sin(a) * d, 0.012 + 0.0007 * i, cos(a) * d), _rng.randf_range(1.8, 5.0), col)
	_floor_cracks()


## Thin dark cracks in the packed earth (flat ribbons just above the floor and the patches, no collision): a few
## branching lines, as in key_cyclops.png.
func _floor_cracks() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 16:
		var a := _rng.randf() * TAU
		var p := Vector3(sin(a), 0, cos(a)) * _rng.randf_range(3.0, radius - 2.5)
		var heading := _rng.randf() * TAU
		var w := _rng.randf_range(0.06, 0.11)
		for seg in _rng.randi_range(4, 7):
			heading += _rng.randf_range(-0.6, 0.6)
			var q := p + Vector3(sin(heading), 0, cos(heading)) * _rng.randf_range(0.6, 1.4)
			if q.length() > radius - 1.0:
				break
			_crack_seg(st, p, q, w)
			if _rng.randf() < 0.3:          # a short branch
				var b := heading + _rng.randf_range(0.7, 1.2) * (1.0 if _rng.randf() < 0.5 else -1.0)
				_crack_seg(st, q, q + Vector3(sin(b), 0, cos(b)) * _rng.randf_range(0.4, 0.9), w * 0.6)
			p = q
			w *= 0.85
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := CharacterVisual.make_toon(EARTH.darkened(0.45), null, 0.0, 0.0)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	mi.position.y = 0.03


func _crack_seg(st: SurfaceTool, a: Vector3, b: Vector3, w: float) -> void:
	var side := (b - a).normalized().cross(Vector3.UP) * w * 0.5
	for v in [a + side, b + side * 0.6, b - side * 0.6, a + side, b - side * 0.6, a - side]:
		st.set_normal(Vector3.UP)
		st.add_vertex(v)


func _flat_patch(pos: Vector3, r: float, col: Color) -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = 0.01
	cm.radial_segments = 20
	mi.mesh = cm
	mi.material_override = CharacterVisual.make_toon(col, null, 0.0, 0.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.scale = Vector3(1.0, 1.0, _rng.randf_range(0.5, 0.9))
	mi.rotation.y = _rng.randf() * TAU
	add_child(mi)
	mi.position = pos


## The island plateau under the arena: a pale terrace ring outside the curb, then cliffs down to the sea.
func _plateau() -> void:
	var terrace := MeshInstance3D.new()
	var tm := CylinderMesh.new()
	tm.top_radius = PLATEAU_R
	tm.bottom_radius = PLATEAU_R + 1.0
	tm.height = 1.0
	tm.radial_segments = 96
	terrace.mesh = tm
	terrace.material_override = CharacterVisual.make_toon(TERRACE, null, 0.0, 0.0)
	add_child(terrace)
	terrace.position.y = -0.53
	var cliff := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = PLATEAU_R + 1.0
	cm.bottom_radius = PLATEAU_R + 9.0
	cm.height = absf(SEA_Y) + 4.0
	cm.radial_segments = 40
	cliff.mesh = cm
	cliff.material_override = CharacterVisual.make_toon(CLIFF, null, 0.0, 0.0)
	add_child(cliff)
	cliff.position.y = -1.0 - cm.height * 0.5
	# boulders along the cliff edge
	for i in 26:
		var a := TAU * float(i) / 26.0 + _rng.randf_range(-0.08, 0.08)
		var d := PLATEAU_R + _rng.randf_range(-0.5, 2.5)
		EnvKit.rock(self, Vector3(sin(a) * d, -0.6, cos(a) * d), _rng.randf_range(2.0, 4.2), CLIFF.darkened(_rng.randf_range(0.0, 0.15)))


## Low marble curb on the arena rim (the invisible boundary from ArenaBase does the real stopping).
func _curb() -> void:
	var n := 56
	var r0 := radius + 0.9
	var seg := TAU * r0 / float(n)
	for i in n:
		if i % 9 == 4:
			continue          # worn gaps
		var a := TAU * (float(i) + 0.5) / float(n)
		var h := 0.45 if i % 5 != 2 else 0.3
		var blk := _block(Vector3(sin(a) * r0, h * 0.5, cos(a) * r0), Vector3(seg * 0.94, h, 1.2), rad_to_deg(a), MARBLE.darkened(_rng.randf_range(0.0, 0.08)), false)
		# no shadow: near-faded from a rim camera, the curb's own dark shadow band stayed in the bottom of the frame
		for c in blk.get_children():
			if c is MeshInstance3D:
				(c as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				# no ink shell either: with the faces near-faded, the shell's dark inside showed as a grey stipple band
				var cm := (c as MeshInstance3D).material_override as ShaderMaterial
				if cm != null:
					cm.next_pass = null


# ------------------------------------------------------------------ dressing (all outside the fighting lane)
## Ruined colonnades with architraves: two flank the sea view behind the giant, two more on the east and west.
func _colonnades() -> void:
	var s := COLONNADE_SCALE
	_colonnade(deg_to_rad(208.0), 33.5, 3, true, s)   # north-west, behind the boss on the left: frames the giant
	_colonnade(deg_to_rad(152.0), 33.5, 3, true, s)   # north-east (the sea shows between the two, 180 deg)
	_colonnade(deg_to_rad(268.0), 34.0, 3, false, s)  # west
	_colonnade(deg_to_rad(92.0), 34.0, 4, true, s)    # east
	_colonnade(deg_to_rad(236.0), 38.0, 2, true, 1.0) # smaller ones further back fill the gaps without closing the sea
	_colonnade(deg_to_rad(124.0), 38.5, 2, false, 1.0)


## A row of columns along the tangent at angle `a`, distance `d`, with a beam on top (the last span broken).
## `s` scales the columns, the beam and the debris.
func _colonnade(a: float, d: float, count: int, broken_end: bool, s := 1.0) -> void:
	var center := Vector3(sin(a) * d, 0, cos(a) * d)
	var tangent := Vector3(cos(a), 0, -sin(a))
	var spacing := 4.6 * s
	var yaw := rad_to_deg(a)
	var tops: Array[Vector3] = []
	for i in count:
		var off := (float(i) - float(count - 1) * 0.5) * spacing
		var p := center + tangent * off
		if broken_end and i == count - 1:
			_prop("column_broken", p, yaw + 30.0, s)
		else:
			_prop("column", p, yaw, s)
			tops.append(p)
	if tops.size() >= 2:
		var a0: Vector3 = tops[0]
		var a1: Vector3 = tops[tops.size() - 1]
		var mid := (a0 + a1) * 0.5
		var length := a0.distance_to(a1) + 2.4 * s
		_block(mid + Vector3(0, 6.55 * s, 0), Vector3(length, 1.1 * s, 1.9 * s), yaw, MARBLE, false)
		_block(mid + Vector3(0, 7.35 * s, 0), Vector3(length - 0.6 * s, 0.5 * s, 1.6 * s), yaw, MARBLE.darkened(0.06), false)
		if broken_end:
			# the broken lintel span: one end still on the last column, the other on the ground
			var last: Vector3 = tops[tops.size() - 1]
			var top_y := 6.0 * s
			var run := spacing * 0.8
			var lint := _block(last + tangent * (run * 0.5) + Vector3(0, top_y * 0.5, 0),
				Vector3(sqrt(run * run + top_y * top_y), 1.0 * s, 1.7 * s), yaw, MARBLE.darkened(0.04), false)
			lint.rotate_object_local(Vector3.BACK, -atan2(top_y, run))
	# a fallen drum and a chunk of beam at the foot (pushed outward so nothing enters the curb)
	var fall := center + tangent * (float(count) * spacing * 0.5 + 2.0 * s) + center.normalized() * 1.0
	var drum := _prop("column", fall + Vector3(0, 0.45 * s, 0), 0.0, 0.42 * s)
	drum.rotation_degrees = Vector3(0, yaw + 70.0, 90.0)
	_block(fall + tangent * 2.5 * s + Vector3(0, 0.4 * s, 0), Vector3(3.2, 0.8, 1.5) * s, yaw + 18.0, MARBLE.darkened(0.05), true)


## Lone broken columns, statues and debris on the terrace ring.
func _ruins() -> void:
	_rim_ruins()
	var spots := [[20.0, 34.0], [58.0, 33.5], [178.0, 34.0], [300.0, 34.5], [332.0, 33.8]]   # clear of the colonnades
	for s in spots:
		var a := deg_to_rad(float(s[0]))
		var d: float = s[1]
		var p := Vector3(sin(a) * d, 0, cos(a) * d)
		if int(s[0]) % 3 == 0:
			_prop("column", p, _rng.randf() * 360.0, _rng.randf_range(0.55, 0.8))
		else:
			_prop("column_broken", p, _rng.randf() * 360.0, _rng.randf_range(0.9, 1.2))
	_prop("statue_a", _polar(166.0, 41.0), 166.0 + 180.0, 1.6)
	_prop("statue_b", _polar(196.0, 41.5), 196.0 + 180.0, 1.5)
	for i in 10:
		var a2 := _rng.randf() * 360.0
		_prop("boulder", _polar(a2, _rng.randf_range(34.0, 44.0)), _rng.randf() * 360.0, _rng.randf_range(0.5, 1.1))
	for i in 6:
		var a3 := _rng.randf_range(0.0, 360.0)
		_prop("amphora", _polar(a3, _rng.randf_range(33.0, 36.0)), _rng.randf() * 360.0, 1.0)


## Broken columns and fallen drums right on the rim (just outside the curb, r 31.6-32.4) on the north half, behind
## the giant's start, so the ring reads as a ruined quarry floor and not an empty disc (SPEC: "broken columns on the rim").
func _rim_ruins() -> void:
	# angles clear of the framing colonnades (141-163, 197-219, 257-279, 75-108 deg at r 33.5-34)
	for s in [[113.0, 32.0, 0], [134.0, 32.3, 1], [171.0, 31.8, 0], [189.0, 32.2, 0], [225.0, 31.9, 1], [249.0, 32.2, 0]]:
		var deg: float = s[0]
		var p := _polar(deg, float(s[1]))
		if int(s[2]) == 0:
			_prop("column_broken", p, _rng.randf() * 360.0, _rng.randf_range(1.3, 1.6))
		else:
			# a fallen drum lying along the curb
			var drum := _prop("column", p + Vector3(0, 0.6, 0), 0.0, 0.55)
			drum.rotation_degrees = Vector3(0, deg + 90.0 + _rng.randf_range(-20.0, 20.0), 90.0)


## The quarry: stacked sandstone walls and cut blocks closing the south side (behind the hero's start).
func _quarry_face() -> void:
	for i in 13:
		var deg := lerpf(-62.0, 62.0, float(i) / 12.0) + _rng.randf_range(-3.0, 3.0)
		var d := 42.0 + _rng.randf_range(0.0, 3.0)
		var s := _rng.randf_range(1.8, 2.6)
		_prop("cliff_rock", _polar(deg, d), deg + 180.0 + _rng.randf_range(-15.0, 15.0), s)
		if i % 2 == 0:
			_prop("cliff_rock", _polar(deg + 4.0, d + 3.5) + Vector3(0, s * 3.4, 0), deg + 160.0, s * 0.8, false)
	# cut blocks waiting to be hauled away
	for i in 9:
		var deg2 := _rng.randf_range(-55.0, 55.0)
		var p := _polar(deg2, _rng.randf_range(34.5, 39.0))
		var sz := Vector3(_rng.randf_range(1.4, 2.6), _rng.randf_range(0.9, 1.5), _rng.randf_range(1.2, 2.0))
		_block(p + Vector3(0, sz.y * 0.5, 0), sz, _rng.randf() * 90.0, SANDSTONE.darkened(_rng.randf_range(0.0, 0.1)), true)
		if i % 3 == 0:
			var sz2 := sz * 0.7
			_block(p + Vector3(0, sz.y + sz2.y * 0.5, 0), sz2, _rng.randf() * 90.0, SANDSTONE, true)


## A stepped, cut quarry wall (three tiers of sandstone blocks stepping back and up) on the west-south-west, joining
## the south quarry face, so the ring reads as a working quarry from the side views too. Visual only (outside the
## boundary).
func _quarry_wall() -> void:
	for tier in 3:
		var r := 39.5 + 2.6 * float(tier)
		var h := 3.0
		var y := 3.0 * float(tier)
		var deg := 288.0
		while deg < 326.0:
			var w := _rng.randf_range(3.2, 4.6)
			var step := rad_to_deg(w / r)
			var p := _polar(deg + step * 0.5, r)
			var hh := h + _rng.randf_range(-0.3, 0.5)
			var col := SANDSTONE.darkened(_rng.randf_range(0.02, 0.16)) if (int(deg) + tier) % 2 == 0 else SANDSTONE.lightened(0.04)
			_block(p + Vector3(0, y + hh * 0.5, 0), Vector3(w * 0.97, hh, 2.6), deg + step * 0.5, col, false)
			deg += step


func _trees() -> void:
	for deg in [-78.0, -40.0, 34.0, 70.0, 104.0, 250.0]:
		_prop("olive_tree", _polar(deg, _rng.randf_range(40.0, 44.0)), _rng.randf() * 360.0, _rng.randf_range(0.9, 1.2))
	for deg in [-88.0, -24.0, 22.0, 92.0, 124.0, 238.0, 262.0]:
		_prop("cypress", _polar(deg, _rng.randf_range(43.0, 45.5)), 0.0, _rng.randf_range(0.8, 1.1))


## Distant rock stacks in the sea so the horizon has depth.
func _sea_stacks() -> void:
	for s in [[200.0, 230.0, 7.0], [150.0, 320.0, 10.0], [245.0, 280.0, 6.0], [110.0, 420.0, 14.0], [300.0, 380.0, 9.0]]:
		var p := _polar(float(s[0]), float(s[1]))
		p.y = SEA_Y - 2.0
		_prop("cliff_rock", p, _rng.randf() * 360.0, float(s[2]), false)


# ------------------------------------------------------------------ helpers
func _polar(deg: float, d: float) -> Vector3:
	var a := deg_to_rad(deg)
	return Vector3(sin(a) * d, 0, cos(a) * d)


## A generated prop (EnvKit: GLB + props.json collision); a coloured box of the manifest size when the GLB is missing.
func _prop(prop_name: String, pos: Vector3, yaw := 0.0, scale := 1.0, collide := true) -> Node3D:
	if ResourceLoader.exists("res://assets/props/%s.glb" % prop_name):
		return EnvKit.prop(self, prop_name, pos, yaw, scale, collide)
	var fallback := {"column": [Vector3(1.6, 6.0, 1.6), MARBLE], "column_broken": [Vector3(1.6, 2.4, 1.6), MARBLE],
		"statue_a": [Vector3(1.3, 2.6, 1.2), MARBLE], "statue_b": [Vector3(2.6, 2.6, 1.7), MARBLE],
		"boulder": [Vector3(2.2, 2.2, 2.1), CLIFF], "cliff_rock": [Vector3(3.8, 3.9, 4.0), CLIFF],
		"olive_tree": [Vector3(1.0, 5.0, 1.0), Color(0.45, 0.55, 0.30)], "cypress": [Vector3(1.6, 8.0, 1.6), Color(0.20, 0.36, 0.20)],
		"amphora": [Vector3(0.9, 1.3, 0.9), Color(0.75, 0.42, 0.25)]}
	var row: Array = fallback.get(prop_name, [Vector3.ONE, Color(0.6, 0.6, 0.6)])
	var sz: Vector3 = row[0] * scale
	return _block(pos + Vector3(0, sz.y * 0.5, 0), sz, yaw, row[1], collide)


## A toon-shaded box with an ink outline (and box collision on layer 1 when `collide`).
func _block(pos: Vector3, size: Vector3, yaw_deg: float, col: Color, collide: bool) -> Node3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1 if collide else 0
	body.collision_mask = 0
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = CharacterVisual.make_toon(col, null, CharacterVisual.outline_width_for(maxf(size.y, 2.0)), 0.12)
	body.add_child(mi)
	if collide:
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = size
		cs.shape = bs
		body.add_child(cs)
	add_child(body)
	body.position = pos
	body.rotation_degrees.y = yaw_deg
	return body


func spawn_boss() -> BossBase:
	var b: BossBase = BOSS_SCRIPT.new()
	b.name = "Cyclops"
	b.position = Vector3(0, 0.05, -3.0)        # near the centre, facing +Z toward the hero
	return b


## The hero starts near the south edge of the ring, facing the giant (and the sea behind him).
func player_spawn() -> Vector3:
	return Vector3(0, 0.1, radius - 9.0)
