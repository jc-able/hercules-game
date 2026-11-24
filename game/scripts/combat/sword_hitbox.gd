class_name SwordHitbox
extends Area3D
## The player's sword hit box (collision layer 4, sees boss bodies on 3 and weak points on 5). Active only inside the
## attack window: an exposed weak point takes one hit per swing; any other boss contact is a glance (spark + clang).
##
## Real hero model: follow(socket, sword_prop) makes the hit volume the REAL blade - a capsule (radius
## Tuning.SWORD_HIT_RADIUS) from the grip to the blade tip (+ Tuning.SWORD_TIP_EXTRA), swept between physics frames so a
## fast swing cannot skip a weak point. Weak points are tested as spheres (group "weak_point"), boss bodies with a
## shape query. Stand-in hero: the old box in front of the chest (SWORD_WIDTH x SWORD_HEIGHT x SWORD_REACH).

signal struck(point: WeakPoint)
signal glanced(pos: Vector3)

var active := false
var _hit := {}
var _glanced := false
var _cs: CollisionShape3D
var _blade_root: Node3D = null       # the socket that holds the sword (follows the hand bone)
var _blade_a := Vector3.ZERO         # grip, socket frame
var _blade_b := Vector3.ZERO         # tip (+ SWORD_TIP_EXTRA), socket frame
var _prev_a := Vector3.ZERO
var _prev_b := Vector3.ZERO
var _have_prev := false
var _query: PhysicsShapeQueryParameters3D
var _capsule: CapsuleShape3D
var last_blade := PackedVector3Array()   ## [grip, tip] world positions of the last test (debug / harness)


func _init() -> void:
	name = "SwordHitbox"
	collision_layer = 1 << 3
	collision_mask = (1 << 2) | (1 << 4)
	monitoring = true
	monitorable = false
	_cs = CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(Tuning.SWORD_WIDTH, Tuning.SWORD_HEIGHT, Tuning.SWORD_REACH)
	_cs.shape = sh
	_cs.position = Vector3(0, 0.1 + Tuning.SWORD_HEIGHT * 0.5, Tuning.PLAYER_RADIUS + Tuning.SWORD_REACH * 0.5 - 0.2)
	add_child(_cs)


## Uses the real sword: `holder` is the socket node the sword prop hangs on, `prop` the sword. The tip is the prop vertex
## farthest from the grip (the socket origin).
func follow(holder: Node3D, prop: Node3D) -> void:
	if holder == null or prop == null:
		return
	var tip := Vector3.ZERO
	var meshes: Array = prop.find_children("*", "MeshInstance3D", true, false)
	if prop is MeshInstance3D:
		meshes.append(prop)
	for n in meshes:
		var mi := n as MeshInstance3D
		if mi.mesh == null:
			continue
		var xf := _rel(mi, holder)
		for si in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(si)
			if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null:
				continue
			for v in (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array):
				var w: Vector3 = xf * v
				if w.length() > tip.length():
					tip = w
	if tip.length() < 0.2:
		return
	_blade_root = holder
	_blade_a = Vector3.ZERO
	_blade_b = tip + tip.normalized() * Tuning.SWORD_TIP_EXTRA
	monitoring = false
	_cs.disabled = true
	_capsule = CapsuleShape3D.new()
	_query = PhysicsShapeQueryParameters3D.new()
	_query.shape = _capsule
	_query.collision_mask = 1 << 2            # boss bodies (weak points are tested as spheres)
	_query.collide_with_bodies = true
	_query.collide_with_areas = false


## True when the hit volume is the real blade (follow() succeeded).
func follows_blade() -> bool:
	return _blade_root != null and is_instance_valid(_blade_root)


## Opens (true) or closes the hit window. Opening resets the one-hit-per-swing memory.
func set_active(on: bool) -> void:
	if on and not active:
		_hit.clear()
		_glanced = false
		_have_prev = false
		_dbg_min = INF
	elif active and not on and _dbg_min < INF and Game.harness and Game.args.has("sword-debug"):
		# harness `--sword-debug`: how close the real blade came to the nearest weak point in this swing
		Game.event("swing", {"gap": snappedf(_dbg_min, 0.01), "point": _dbg_point, "y": snappedf(_dbg_y, 0.01), "struck": not _hit.is_empty()})
	active = on


var _dbg_min := INF          # --sword-debug: smallest (distance - radii) to a weak point this swing
var _dbg_point := ""
var _dbg_y := 0.0


var _trail := PackedVector3Array()   # feedback 2: the blade's recent path [grip, tip, ...] (world), newest last
const TRAIL_SAMPLES := 9             # ~0.15 s at 60 Hz physics: the slash streak drawn on a cut


func _physics_process(_delta: float) -> void:
	if follows_blade():
		var xf := _blade_root.global_transform
		_trail.append(xf * _blade_a)
		_trail.append(xf * _blade_b)
		if _trail.size() > TRAIL_SAMPLES * 2:
			_trail = _trail.slice(_trail.size() - TRAIL_SAMPLES * 2)
	if active:
		check()


## The blade's recent path for a slash streak, only the part that moved (a still blade gives an empty path).
func blade_trail() -> PackedVector3Array:
	if _trail.size() < 4:
		return PackedVector3Array()
	var tips := 0.0
	for i in range(3, _trail.size(), 2):
		tips += _trail[i].distance_to(_trail[i - 2])
	return _trail if tips > 0.6 else PackedVector3Array()


## Resolves contacts now: strikes exposed weak points, otherwise glances off the boss once per swing.
func check() -> void:
	if follows_blade():
		_check_blade()
		return
	var touched_boss := false
	var points: Array[WeakPoint] = []
	for a in get_overlapping_areas():
		if a is WeakPoint:
			points.append(a as WeakPoint)
	if _hit.is_empty():
		for b in get_overlapping_bodies():
			if b.is_in_group("boss"):
				touched_boss = true
				break
	_resolve(points, touched_boss, global_transform * Vector3(0, 1.2, Tuning.PLAYER_RADIUS + Tuning.SWORD_REACH * 0.5))


func _check_blade() -> void:
	var xf := _blade_root.global_transform
	var a := xf * _blade_a
	var b := xf * _blade_b
	if not _have_prev:
		_prev_a = a
		_prev_b = b
		_have_prev = true
	var r := Tuning.SWORD_HIT_RADIUS
	var steps := clampi(int(ceil(maxf(_prev_a.distance_to(a), _prev_b.distance_to(b)) / maxf(r, 0.05))), 1, 10)
	var points: Array[WeakPoint] = []
	var touched_boss := false
	var space := get_world_3d().direct_space_state
	for i in range(1, steps + 1):
		var k := float(i) / float(steps)
		var pa := _prev_a.lerp(a, k)
		var pb := _prev_b.lerp(b, k)
		for n in get_tree().get_nodes_in_group("weak_point"):
			var wp := n as WeakPoint
			if wp == null or points.has(wp) or not wp.is_inside_tree():
				continue
			var wr := wp.radius * wp.global_basis.get_scale().x
			var gap := _seg_point_dist(pa, pb, wp.global_position) - wr - r
			if gap < _dbg_min:
				_dbg_min = gap
				_dbg_point = "%s(%.2f,%.2f,%.2f)" % [wp.id, wp.global_position.x, wp.global_position.y, wp.global_position.z]
				_dbg_y = (pa.y + pb.y) * 0.5
			if gap <= 0.0:
				points.append(wp)
		if not touched_boss and _hit.is_empty() and space != null:
			for hit in space.intersect_shape(_segment_query(pa, pb, r), 8):
				var c: Object = hit.get("collider")
				if c is Node and (c as Node).is_in_group("boss"):
					touched_boss = true
					break
	_prev_a = a
	_prev_b = b
	last_blade = PackedVector3Array([a, b])
	_resolve(points, touched_boss, a.lerp(b, 0.7))


func _resolve(points: Array[WeakPoint], touched_boss: bool, center: Vector3) -> void:
	var struck_any := false
	for wp in points:
		if wp.exposed and wp.hits_left > 0:
			if not _hit.has(wp):
				_hit[wp] = true
				# feedback 2: where the blade crossed and its path, for the cut effects + wound (BossBase.take_weak_hit;
				# the gold sparks moved there too, so a strike the boss turns into a glance shows no cut)
				wp.last_hit_pos = _cut_point(wp)
				wp.last_from = global_position
				wp.last_trail = blade_trail()
				if wp.strike():
					struck_any = true
					struck.emit(wp)
					Sfx.play("sword_hit", wp.global_position)
					Game.hit_pause()
					Game.shake(0.35)
					Controls.rumble(0.4, 0.7, 0.15)
		elif not _hit.has(wp):
			touched_boss = true
	if touched_boss and not struck_any and not _glanced and _hit.is_empty():
		_glanced = true
		glanced.emit(center)
		Fx.spark(get_tree().current_scene, center, Color(1, 1, 0.9), 14, 0.06)
		Fx.glance_streak(get_tree().current_scene, blade_trail())
		Sfx.play("glance", center)
		Game.shake(0.08)


func _segment_query(pa: Vector3, pb: Vector3, r: float) -> PhysicsShapeQueryParameters3D:
	var d := pb - pa
	var l := maxf(d.length(), 0.01)
	var y := d / l
	var x := y.cross(Vector3.UP if absf(y.y) < 0.95 else Vector3.RIGHT).normalized()
	var z := x.cross(y)
	_capsule.radius = r
	_capsule.height = l + 2.0 * r
	_query.transform = Transform3D(Basis(x, y, z), (pa + pb) * 0.5)
	return _query


## The point where the blade (last tested segment) passed the weak point: the blade point nearest its centre, pulled
## to the sphere's surface on the blade's side. Stand-in hero: the point's centre.
func _cut_point(wp: WeakPoint) -> Vector3:
	var c := wp.global_position
	if last_blade.size() < 2:
		return c
	var a := last_blade[0]
	var b := last_blade[1]
	var ab := b - a
	var t := clampf((c - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
	var p := a + ab * t
	var r := wp.radius * wp.global_basis.get_scale().x
	var off := p - c
	return c + off.limit_length(r * 0.6)


static func _seg_point_dist(a: Vector3, b: Vector3, p: Vector3) -> float:
	var ab := b - a
	var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
	return p.distance_to(a + ab * t)


static func _rel(n: Node3D, top: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var p: Node = n
	while p != null and p != top:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf
