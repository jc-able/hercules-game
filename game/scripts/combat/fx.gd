class_name Fx
extends RefCounted
## Small one-shot effects built in code (sparks, dust puffs).

static var _soft: Texture2D = null


## A soft round white sprite (radial gradient), made once.
static func soft_dot() -> Texture2D:
	if _soft == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.45, Color(1, 1, 1, 0.85))
		var t := GradientTexture2D.new()
		t.gradient = g
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
		t.width = 64
		t.height = 64
		_soft = t
	return _soft


## A burst of sparks at a world position (gold = strike, white = glance, blue = block).
static func spark(parent: Node, pos: Vector3, color := Color(1.0, 0.85, 0.4), amount := 18, size := 0.07) -> void:
	if parent == null or not parent.is_inside_tree():
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.emitting = false
	p.amount = amount
	p.lifetime = 0.35
	p.explosiveness = 1.0
	p.direction = Vector3.UP
	p.spread = 180.0
	p.initial_velocity_min = 3.0
	p.initial_velocity_max = 7.0
	p.gravity = Vector3(0, -9.0, 0)
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.2
	var qm := QuadMesh.new()
	qm.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_color = color
	m.albedo_texture = soft_dot()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.emission_enabled = true
	m.emission = color
	qm.material = m
	p.mesh = qm
	parent.add_child(p)
	p.global_position = pos
	p.emitting = true
	p.finished.connect(p.queue_free)


## A ground dust puff (impacts, slams).
static func dust(parent: Node, pos: Vector3, radius := 2.0, color := Color(0.75, 0.68, 0.55, 0.8)) -> void:
	if parent == null or not parent.is_inside_tree():
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 24
	p.lifetime = 0.8
	p.explosiveness = 0.95
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	p.emission_ring_axis = Vector3.UP
	p.emission_ring_radius = radius * 0.6
	p.emission_ring_inner_radius = 0.0
	p.emission_ring_height = 0.1
	p.direction = Vector3.UP
	p.spread = 60.0
	p.initial_velocity_min = 1.0
	p.initial_velocity_max = 3.0
	p.gravity = Vector3(0, -1.0, 0)
	p.scale_amount_min = 0.8
	p.scale_amount_max = 1.6
	var qm := QuadMesh.new()
	qm.size = Vector2(radius * 0.35, radius * 0.35)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = color
	m.albedo_texture = soft_dot()
	qm.material = m
	p.mesh = qm
	parent.add_child(p)
	p.global_position = pos + Vector3(0, 0.2, 0)
	p.emitting = true
	p.finished.connect(p.queue_free)


# ------------------------------------------------------------------ strike effects (feedback 2, vfx)
# Every cut effect uses one of two material kinds that the warm-up already compiles: the "dot" (Fx.spark's billboard
# sprite) and the "ribbon" (unshaded, alpha, no cull, vertex colour: the Cyclops sweep ribbon). Wounds are Decals
# (no spatial shader of their own). Fx.warm_strike() runs the real code once in ArenaBase.prewarm_in.

const IMPACT_TO_CAM := 0.1            ## m the impact star/ring sits toward the camera from the cut
const IMPACT_CLEAR := 1.5             ## m: hero this close to the camera->cut line => smaller star/ring
const IMPACT_FRONT := 0.45            ## x size the star/ring sits toward the camera (the cut point lies inside the limb)
const IMPACT_HERO_GAP := 0.6          ## m the star/ring stays behind the hero when he is near the camera->cut line
const IMPACT_NEAR_SHIFT := 0.25      ## x size: hero near the camera->cut line => star/ring centre moved this far away from him
const SLASH_WIDTH := 0.34            ## m, the cut streak at its new end (finishing pass: was 0.22, read faint)
const WOUND_LAYER := 1 << 11         ## visual layer 12: boss meshes get it at the first wound; wound decals see only it

static var _wound_albedo: Texture2D = null
static var _wound_emission: Texture2D = null


## Same flags as Fx.spark's material (billboard, alpha, emission, soft dot): no new shader.
static func _dot_mat(color: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_color = color
	m.albedo_texture = soft_dot()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.emission_enabled = true
	m.emission = color
	return m


## Same flags as the Cyclops sweep ribbon (unshaded, alpha, no cull, vertex colour): no new shader.
static func _ribbon_mat(alpha := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = true
	m.albedo_color = Color(1, 1, 1, alpha)
	return m


static func _fade_free(mi: MeshInstance3D, m: StandardMaterial3D, hold: float, fade: float) -> void:
	var tw := mi.create_tween()
	tw.tween_interval(hold)
	tw.tween_property(m, "albedo_color:a", 0.0, fade)
	tw.tween_callback(mi.queue_free)


## A slash streak along the blade's recent path. `trail` = [grip0, tip0, grip1, tip1, ...] in world space, oldest first.
## Feedback 2 re-fix (reviewer: the band of blade quads read as a pale sheet/shard): built from the TIP samples only
## (samples < 3 cm apart dropped, a jump > 1.2 m = stale samples before it dropped), Catmull-Rom smoothed (4 steps per
## sample), drawn as a camera-facing ribbon `width` m wide at the new end that tapers to nothing at the old end. Near-
## opaque white core, `color` at the edges. Same "ribbon" material kind (no warm-up change).
## `frac` picks the blade point the streak follows (1 = the tip; Fx.cut passes the cut's own place on the blade, a
## little toward the tip, so the streak runs through the cut: on Medusa the tip passed ~1 m above her neck).
static func slash(parent: Node, trail: PackedVector3Array, color: Color, strength := 1.0, width := 0.22, frac := 1.0) -> void:
	if parent == null or not parent.is_inside_tree() or trail.size() < 4:
		return
	var tips := PackedVector3Array()
	var n := trail.size() / 2
	for i in n:
		var t := trail[i * 2].lerp(trail[i * 2 + 1], frac)
		if tips.is_empty():
			tips.append(t)
			continue
		var step := tips[tips.size() - 1].distance_to(t)
		if step > 1.2:
			tips = PackedVector3Array([t])       # a jump: the samples before it are stale
		elif step >= 0.03 or (i == n - 1 and tips.size() == 1 and step > 0.00001):
			tips.append(t)
	# keep only the samples since the blade last turned back (> 90 deg): a reversal folded the ribbon into a pale shard
	for i in range(tips.size() - 2, 0, -1):
		if (tips[i] - tips[i - 1]).dot(tips[i + 1] - tips[i]) < 0.0:
			tips = tips.slice(i)
			break
	if tips.size() < 2:
		return
	var pts := PackedVector3Array()
	var m := tips.size()
	for i in m - 1:
		var p0 := tips[maxi(i - 1, 0)]
		var p1 := tips[i]
		var p2 := tips[i + 1]
		var p3 := tips[mini(i + 2, m - 1)]
		for s in 4:
			var u := float(s) / 4.0
			var u2 := u * u
			var u3 := u2 * u
			pts.append(0.5 * ((2.0 * p1) + (p2 - p0) * u + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2 \
				+ (3.0 * p1 - p0 - 3.0 * p2 + p3) * u3))
	pts.append(tips[m - 1])
	var cam := parent.get_viewport().get_camera_3d() if parent.get_viewport() != null else null
	var blade := trail[trail.size() - 1] - trail[trail.size() - 2]     # last tip - last grip: fallback side
	var k_n := pts.size()
	var verts := PackedVector3Array()
	var cols := PackedColorArray()
	var prev_side := Vector3.UP
	for i in k_n:
		var p := pts[i]
		var tan := pts[mini(i + 1, k_n - 1)] - pts[maxi(i - 1, 0)]
		var to_cam := (cam.global_position - p) if cam != null else Vector3.BACK
		var side := tan.cross(to_cam)
		if side.length() < 0.0001:
			side = blade
		side = side.normalized() if side.length() > 0.0001 else Vector3.UP
		if i > 0 and side.dot(prev_side) < 0.0:          # no twist where the path bends past the view line
			side = -side
		prev_side = side
		var k := float(i) / float(k_n - 1)                # 0 = old end, 1 = newest
		var half := width * 0.5 * pow(k, 0.7)
		var a_core := minf(0.9 * strength * (0.25 + 0.75 * k), 0.95)
		var a_edge := minf(0.8 * strength * k, 0.9)
		verts.append(p - side * half)
		cols.append(Color(color.r, color.g, color.b, a_edge))
		verts.append(p)
		var core := Color(1.0, 1.0, 0.95).lerp(color, 0.25)   # white-hot, a touch of the creature's colour (pale sky)
		cols.append(Color(core.r, core.g, core.b, a_core))
		verts.append(p + side * half)
		cols.append(Color(color.r, color.g, color.b, a_edge))
	var idx := PackedInt32Array()
	for i in k_n - 1:
		var o := i * 3
		idx.append_array([o, o + 1, o + 3, o + 1, o + 4, o + 3, o + 1, o + 2, o + 4, o + 2, o + 5, o + 4])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.mesh = am
	var mat := _ribbon_mat()
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	mi.global_transform = Transform3D.IDENTITY
	_fade_free(mi, mat, 0.16 * strength, 0.2)


## A flat star (8 rays) and an expanding ring at `pos`, facing the camera: the cel "impact" mark.
## Feedback 2 re-fix (reviewer: on the Hydra the star/ring covered the hero): it sits only IMPACT_TO_CAM m toward the
## camera (was 0.35 x size), and when the hero (`avoid`, his feet) stands within IMPACT_CLEAR m of the camera->point
## line, between them, star and ring were drawn at 0.6x (replaced, see below).
## Finishing pass (final check 3: on the first Cyclops hit no star showed in any frame; the Hydra's read small): the star
## starts at FULL size (a 1.15x pop settling to 1.0 in 0.07 s; it used to grow from 0.35x, and the 0.06 s hit pause runs
## the game at 5 % speed, so it sat at 0.35x through the pause). It sits IMPACT_FRONT x size toward the camera, out of
## the struck limb that hid its centre. The hero-near case keeps the full size too (was 0.6x): it steps toward the
## camera only while it stays IMPACT_HERO_GAP m behind the hero, and its centre moves IMPACT_NEAR_SHIFT x size away from
## him across the view, so the cut stays inside the inner star and the dense core is off his body.
static func impact(parent: Node, pos: Vector3, color: Color, size := 1.6, avoid := Vector3.INF) -> void:
	if parent == null or not parent.is_inside_tree():
		return
	var cam := parent.get_viewport().get_camera_3d() if parent.get_viewport() != null else null
	var to_cam := Vector3.BACK
	var to_cam_m := maxf(IMPACT_TO_CAM, size * IMPACT_FRONT)     # out of the struck limb (the cut point is inside it)
	var shift := Vector3.ZERO
	if cam != null:
		to_cam = (cam.global_position - pos)
		if to_cam.length() > 0.01:
			to_cam = to_cam.normalized()
		if avoid != Vector3.INF:
			var seg := cam.global_position - pos
			var hero := avoid + Vector3.UP * 1.0 - pos
			var t := clampf(hero.dot(seg) / maxf(seg.length_squared(), 0.0001), 0.0, 1.0)
			if t > 0.0 and (hero - seg * t).length() < IMPACT_CLEAR:
				# toward the camera only while it stays IMPACT_HERO_GAP m behind the hero (Hydra jaw beside him: 0)
				to_cam_m = clampf(hero.dot(to_cam) - IMPACT_HERO_GAP, 0.0, size * IMPACT_FRONT)
				var across := hero - to_cam * hero.dot(to_cam)       # hero's offset in the view plane
				if across.length() > 0.01:
					shift = -across.normalized() * size * IMPACT_NEAR_SHIFT
	# star: centre white, ray tips in colour, alternating long/short rays, a random twist
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rays := 8
	var twist := randf() * TAU
	for i in rays * 2:
		var a0 := twist + TAU * float(i) / float(rays * 2)
		var a1 := twist + TAU * float(i + 1) / float(rays * 2)
		var r0 := 1.0 if i % 2 == 0 else 0.32
		var r1 := 1.0 if (i + 1) % 2 == 0 else 0.32
		st.set_color(Color(1, 1, 0.95, 1.0))
		st.add_vertex(Vector3.ZERO)
		st.set_color(Color(color.r, color.g, color.b, 0.35 if r0 > 0.5 else 1.0))
		st.add_vertex(Vector3(cos(a0) * r0, sin(a0) * r0, 0))
		st.set_color(Color(color.r, color.g, color.b, 0.35 if r1 > 0.5 else 1.0))
		st.add_vertex(Vector3(cos(a1) * r1, sin(a1) * r1, 0))
	var star := MeshInstance3D.new()
	star.mesh = st.commit()
	var sm := _ribbon_mat()
	star.material_override = sm
	star.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(star)
	var p := pos + to_cam * to_cam_m + shift
	star.global_transform = Transform3D(Basis.looking_at(-to_cam, Vector3.UP if absf(to_cam.y) < 0.95 else Vector3.FORWARD), p)
	star.scale = Vector3.ONE * size * 1.15
	var tw := star.create_tween()
	tw.tween_property(star, "scale", Vector3.ONE * size, 0.07).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(sm, "albedo_color:a", 0.0, 0.14)
	tw.tween_callback(star.queue_free)
	# ring: a thin annulus that grows and fades
	var rs := SurfaceTool.new()
	rs.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 28
	for i in seg:
		var a0 := TAU * float(i) / float(seg)
		var a1 := TAU * float(i + 1) / float(seg)
		var o0 := Vector3(cos(a0), sin(a0), 0)
		var o1 := Vector3(cos(a1), sin(a1), 0)
		var cin := Color(color.r, color.g, color.b, 0.0)
		var cout := Color(color.r, color.g, color.b, 0.95).lerp(Color(1, 1, 1, 0.95), 0.3)
		rs.set_color(cin); rs.add_vertex(o0 * 0.8)
		rs.set_color(cout); rs.add_vertex(o0)
		rs.set_color(cout); rs.add_vertex(o1)
		rs.set_color(cin); rs.add_vertex(o0 * 0.8)
		rs.set_color(cout); rs.add_vertex(o1)
		rs.set_color(cin); rs.add_vertex(o1 * 0.8)
	var ring := MeshInstance3D.new()
	ring.mesh = rs.commit()
	var rm := _ribbon_mat()
	ring.material_override = rm
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(ring)
	ring.global_transform = star.global_transform
	ring.scale = Vector3.ONE * size * 0.55
	var tw2 := ring.create_tween()
	tw2.set_parallel(true)
	tw2.tween_property(ring, "scale", Vector3.ONE * size * 0.95, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw2.tween_property(rm, "albedo_color:a", 0.0, 0.2).set_delay(0.04)
	tw2.chain().tween_callback(ring.queue_free)


## Ichor droplets thrown out of a cut along `dir` (heavier and slower than sparks, in the creature's colour).
static func ichor(parent: Node, pos: Vector3, color: Color, dir := Vector3.UP, amount := 26, size := 0.16) -> void:
	if parent == null or not parent.is_inside_tree():
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.emitting = false
	p.amount = amount
	p.lifetime = 0.7
	p.explosiveness = 0.92
	p.direction = dir.normalized() if dir.length() > 0.01 else Vector3.UP
	p.spread = 55.0
	p.initial_velocity_min = 3.5
	p.initial_velocity_max = 8.5
	p.gravity = Vector3(0, -15.0, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.3
	var qm := QuadMesh.new()
	qm.size = Vector2(size, size)
	qm.material = _dot_mat(color)
	p.mesh = qm
	parent.add_child(p)
	p.global_position = pos
	p.emitting = true
	p.finished.connect(p.queue_free)


## Everything a weak-point CUT shows at `pos`: slash streak (when a blade trail is known), star + ring, gold sparks,
## ichor in the creature's colour thrown along `dir` (away from the hero). `size` ~ the weak point's radius.
static func cut(parent: Node, pos: Vector3, color: Color, dir: Vector3, trail := PackedVector3Array(), size := 0.8,
		avoid := Vector3.INF) -> void:
	var frac := 1.0
	if trail.size() >= 2:
		var g := trail[trail.size() - 2]
		var ab := trail[trail.size() - 1] - g
		frac = clampf((pos - g).dot(ab) / maxf(ab.length_squared(), 0.000001) + 0.12, 0.35, 1.0)
	slash(parent, trail, color, 1.0, SLASH_WIDTH, frac)
	impact(parent, pos, color, clampf(size * 1.3, 0.7, 1.5), avoid)
	spark(parent, pos, Color(1.0, 0.85, 0.4), 34, 0.13)
	ichor(parent, pos, color, dir + Vector3.UP * 0.6, 28, clampf(size * 0.22, 0.12, 0.26))


## The weaker version for a glance (blade on the body, not a weak point): a faint white streak only.
static func glance_streak(parent: Node, trail: PackedVector3Array) -> void:
	slash(parent, trail, Color(0.9, 0.95, 1.0), 0.45, 0.14)


## Wound textures (made once): a tapered slash, dark core + light rim (albedo) and a glowing rim (emission).
## Decal.modulate tints both with the creature's colour.
static func _wound_textures() -> void:
	if _wound_albedo != null:
		return
	var w := 128
	var h := 64
	var ia := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var ie := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var u := (float(x) + 0.5) / float(w)            # along the cut
			var v := ((float(y) + 0.5) / float(h)) * 2.0 - 1.0   # across
			var half := 0.9 * pow(sin(PI * u), 0.7)        # tapered at both ends
			var bend := 0.18 * sin(PI * u * 1.3 + 0.4)     # a slight curve
			var d := absf(v - bend) / maxf(half, 0.001)
			if half < 0.02 or d > 1.0:
				ia.set_pixel(x, y, Color(0, 0, 0, 0))
				ie.set_pixel(x, y, Color(0, 0, 0, 1))
				continue
			var core := 1.0 - smoothstep(0.35, 0.6, d)
			var rim := smoothstep(0.35, 0.62, d) * (1.0 - smoothstep(0.8, 1.0, d))
			var c := Color(0.12, 0.05, 0.04).lerp(Color(1, 1, 1), rim)
			ia.set_pixel(x, y, Color(c.r, c.g, c.b, clampf(core + rim, 0.0, 1.0)))
			var g := clampf(rim * 1.0 + core * 0.25, 0.0, 1.0)
			ie.set_pixel(x, y, Color(g, g, g, 1))
	_wound_albedo = ImageTexture.create_from_image(ia)
	_wound_emission = ImageTexture.create_from_image(ie)


## A wound that stays: a Decal on `socket` (follows the bone) at world `pos`, projected along `dir` (from the hero into
## the creature), seen only by WOUND_LAYER meshes (the boss: never the hero standing next to it). `size` ~ weak radius.
static func wound(socket: Node3D, pos: Vector3, dir: Vector3, color: Color, size := 0.8) -> Decal:
	if socket == null or not socket.is_inside_tree():
		return null
	_wound_textures()
	var d := Decal.new()
	d.texture_albedo = _wound_albedo
	d.texture_emission = _wound_emission
	d.modulate = color.lerp(Color(1, 1, 1), 0.15)
	d.emission_energy = 1.6
	d.albedo_mix = 1.0
	d.normal_fade = 0.3
	d.upper_fade = 0.15
	d.lower_fade = 0.15
	d.cull_mask = WOUND_LAYER
	d.size = Vector3(size * 1.5, size * 2.6, size * 0.6)
	socket.add_child(d)
	var fwd := dir.normalized() if dir.length() > 0.01 else Vector3.FORWARD
	var y := -fwd
	var x := y.cross(Vector3.UP if absf(y.y) < 0.9 else Vector3.RIGHT).normalized()
	x = x.rotated(y, randf_range(-0.9, 0.9))
	var z := x.cross(y).normalized()
	d.global_transform = Transform3D(Basis(x, y, z), pos)
	return d


## A slow drip of ichor from a wound (a few dots falling), parented to the socket so it follows the cut.
static func drip(socket: Node3D, pos: Vector3, color: Color) -> CPUParticles3D:
	if socket == null or not socket.is_inside_tree():
		return null
	var p := CPUParticles3D.new()
	p.amount = 3
	p.lifetime = 0.8
	p.local_coords = false
	p.direction = Vector3.DOWN
	p.spread = 20.0
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.6
	p.gravity = Vector3(0, -9.0, 0)
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.0
	var qm := QuadMesh.new()
	qm.size = Vector2(0.1, 0.1)
	qm.material = _dot_mat(color)
	p.mesh = qm
	socket.add_child(p)
	p.global_position = pos
	return p


## Runs the real code of every strike effect once, tiny, under `holder` (ArenaBase.prewarm_in): compiles nothing new
## but builds the wound textures and puts a decal on screen once (decal atlas) before the fight.
static func warm_strike(holder: Node3D, tiny: float) -> void:
	var p := holder.global_position
	var tr := PackedVector3Array([p, p + Vector3(tiny, 0, 0), p + Vector3(0, tiny, 0), p + Vector3(tiny, tiny, 0)])
	slash(holder, tr, Color.WHITE, 1.0)
	impact(holder, p, Color.WHITE, tiny)
	ichor(holder, p, Color.WHITE, Vector3.UP, 1, tiny)
	var d := wound(holder, p, Vector3.FORWARD, Color.WHITE, tiny)
	if d != null:
		d.cull_mask = 0xFFFFF
		holder.get_tree().create_timer(0.3, true, false, true).timeout.connect(d.queue_free)
