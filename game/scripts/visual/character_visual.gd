class_name CharacterVisual
extends Node3D
## A character's look: the rigged GLB from the art track (res://assets/characters/<id>/<id>.glb + <id>_clips.json)
## when present, else a StandIn grey box with procedural clips. Same API either way. Faces +Z, feet on y = 0.

signal clip_finished(clip: StringName)

const TOON_SHADER := preload("res://shaders/toon.gdshader")
const OUTLINE_SHADER := preload("res://shaders/outline.gdshader")
const UpperTwist := preload("res://scripts/visual/upper_twist.gd")
const PoseFade := preload("res://scripts/visual/pose_fade.gd")
const GripFix := preload("res://scripts/visual/grip_fix.gd")

## Stand-in clip table: name -> [length s, loop, kind, windup fraction (strike moment / length)].
const STANDIN_CLIPS := {
	"idle": [2.0, true, "idle", 0.0], "walk": [1.3, true, "walk", 0.0], "run": [0.7, true, "walk", 0.0],
	"slither": [1.6, true, "slither", 0.0], "fly": [0.8, true, "fly", 0.0], "glide": [2.0, true, "glide", 0.0],
	"strafe_l": [0.8, true, "walk", 0.0], "strafe_r": [0.8, true, "walk", 0.0], "walk_back": [0.9, true, "walk", 0.0],
	"ride": [1.0, true, "idle", 0.0], "block_idle": [1.0, true, "block", 0.0], "block_start": [0.15, false, "block", 0.0],
	"roll": [0.70, false, "roll", 0.0],
	"attack_1": [0.55, false, "strike_r", 0.33], "attack_2": [0.65, false, "strike_l", 0.34],
	"sweep": [1.4, false, "sweep", 0.43], "slam": [2.2, false, "slam", 0.64], "stuck": [3.0, true, "low", 0.0],
	"pull_free": [0.8, false, "rise", 0.0], "gaze": [2.4, false, "gaze", 0.5], "stun_start": [0.6, false, "drop", 0.0],
	"stunned": [3.0, true, "low", 0.0], "rise": [0.8, false, "rise", 0.0], "tail_swipe": [1.4, false, "tail", 0.5],
	"fire_sweep": [3.9, false, "fire", 0.38], "head_down": [2.5, true, "low", 0.0], "head_up": [0.8, false, "rise", 0.0],
	"stomp": [1.5, false, "stomp", 0.6], "bite": [1.2, false, "strike_r", 0.66],
	"hurt": [0.5, false, "hurt", 0.0], "hit": [0.4, false, "hurt", 0.0], "death": [2.5, false, "death", 0.0],
}

## Stand-in hydra: extra dip of the centre neck in head_down (low/drop/rise) so the head lies on the ground (jaw ~1 m
## high) instead of hanging at head height in front of the hero. Only the hydra stand-in has that pivot.
const HEAD_C_DIP := 0.15

var char_id: StringName
var is_standin := true
var height := 2.0
var manifest: Dictionary = {}
var current_clip: StringName = &""

var _standin: StandIn = null
var _model: Node3D = null
var _anim: AnimationPlayer = null
var _skel: Skeleton3D = null
var _twist_mod: UpperTwist = null   # set_upper_twist(): made on the first non-zero call
var _aim := {}                   # set_socket_aim(): socket -> {holder, bone, base, axis, dir, w}
var _fade: PoseFade = null       # frame-clock characters: skeleton cross-fade (play())
var _grip: GripFix = null        # manifest "grip_fix" (the hero's sword fist): made when the prop is attached
var _anim_names := {}            # clip -> AnimationPlayer animation name
var _sockets := {}               # logical name -> Node3D
var _materials: Array[ShaderMaterial] = []
var _outlines: Array[ShaderMaterial] = []
var _warned := {}
var _clip_t := 0.0
var _clip_speed := 1.0
var _clip_len := 1.0
var _clip_loop := true
var _clip_kind := "idle"
var _clip_windup := 0.0
var _prev_pose := {}
var _from_pose := {}
var _blend_t := 0.0
var _blend_len := 0.0
var _finished_sent := false
var _flash_tween: Tween
var _petrify := 0.0
var _clock := 0.0
var _top := 0.0                  # model_top() cache (measured once at creation)
var _top_pts := PackedVector3Array()          # model_top_points() cache
var _body_meshes: Array[MeshInstance3D] = []  # the model's own skinned meshes, recorded at creation (props excluded)
var _props: Array[Node3D] = []   # attach_prop() results (drop_props() lets them fall)
var _custom_speed := 1.0         # real model: +1 / -1 passed to AnimationPlayer.play (direction)
var _speed := 1.0                # real model: wanted playback rate of the current clip (play() / set_speed())
var _physics_clock := false      # clips advance on the physics clock (bosses), see use_physics_clock()
var _top_bone := PackedInt32Array()       # per model_top_points() entry: skeleton bone that carries it (-1 = none)
var _top_local := PackedVector3Array()    # per entry: the point in that bone's rest space (live_top_points())
var _bone_boxes: Array = []      # [bone, centre, half extents] in bone rest space (live_top_points())
var _boxes_done := false
const BOX_MIN_VERTS := 12

## Characters whose clips run on the physics clock (their state machines time attacks against the clips).
const PHYSICS_CLOCK_IDS := ["cyclops", "medusa", "hydra", "dummy"]

static var _toon_double: Shader = null   # toon variant without back-face culling (GLB doubleSided materials)

## Ink line of real models and their props: about this many pixels wide at 720 p at any distance, between
## OUTLINE_MIN_M metres and OUTLINE_MAX_FRAC x the model's height (so a 1.9 m hero and a 14 m hydra both read).
const OUTLINE_PX := 2.2
const OUTLINE_MIN_M := 0.004
const OUTLINE_MAX_FRAC := 0.012


## Builds the visual for a character id: the GLB when present, else a grey-box stand-in.
static func create(id: StringName) -> CharacterVisual:
	var v := CharacterVisual.new()
	v.name = "Visual"
	v.char_id = id
	v.height = float(Tuning.char_info(id).get("height", 2.0))
	var path := "res://assets/characters/%s/%s.glb" % [id, id]
	if ResourceLoader.exists(path):
		v._load_model(path)
	if v._model == null:
		v._standin = StandIn.build(id)
		v.add_child(v._standin)
		v._materials = v._standin.materials.duplicate()
		for m in v._materials:
			if m.next_pass is ShaderMaterial:
				v._outlines.append(m.next_pass)
	v._top = v._measure_top()
	v.use_physics_clock(PHYSICS_CLOCK_IDS.has(String(id)))
	v.play(&"idle", 0.0)
	return v


# ------------------------------------------------------------------ materials (shared helpers)
## Outline width in metres for a character of this height.
static func outline_width_for(h: float) -> float:
	return clampf(h * 0.008, 0.018, 0.07)


## A toon ShaderMaterial (colour x optional albedo texture) with the ink outline as next pass when width > 0.
## rim: soft rim-light strength (0 for floors and walls, where grazing angles would wash out).
## double_sided: no back-face culling (GLB materials marked doubleSided, e.g. the hydra's split necks).
static func make_toon(color: Color, tex: Texture2D = null, outline_width := 0.0, rim := 0.22, double_sided := false) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = toon_shader(double_sided)
	m.set_shader_parameter("albedo_color", color)
	m.set_shader_parameter("rim_strength", rim)
	if tex != null:
		m.set_shader_parameter("albedo_tex", tex)
		m.set_shader_parameter("use_texture", true)
	if outline_width > 0.0:
		var o := ShaderMaterial.new()
		o.shader = OUTLINE_SHADER
		o.set_shader_parameter("width", outline_width)
		m.next_pass = o
	return m


## The toon shader, or its copy with `cull_disabled` (made once from the same code, so both stay in step).
static func toon_shader(double_sided := false) -> Shader:
	if not double_sided:
		return TOON_SHADER
	if _toon_double == null:
		_toon_double = Shader.new()
		_toon_double.code = TOON_SHADER.code.replace("cull_back", "cull_disabled")
	return _toon_double


## Switches an outline material to a screen-constant ink line (OUTLINE_PX at 720 p) clamped to [OUTLINE_MIN_M, max_m].
static func set_outline_px(o: ShaderMaterial, max_m: float) -> void:
	o.set_shader_parameter("width", maxf(max_m, OUTLINE_MIN_M))
	o.set_shader_parameter("min_width", OUTLINE_MIN_M)
	o.set_shader_parameter("px_width", OUTLINE_PX)


# ------------------------------------------------------------------ real model
## Builds a visual from any GLB file (res:// or an absolute path loaded at runtime) + an optional clips manifest.
## For tools and tests; the game uses create().
static func create_from_file(id: StringName, glb_path: String, manifest_path := "") -> CharacterVisual:
	var v := CharacterVisual.new()
	v.name = "Visual"
	v.char_id = id
	v.height = float(Tuning.char_info(id).get("height", 2.0))
	v._load_model(glb_path, manifest_path)
	if v._model == null:
		v._standin = StandIn.build(id)
		v.add_child(v._standin)
		v._materials = v._standin.materials.duplicate()
	v._top = v._measure_top()
	v.use_physics_clock(PHYSICS_CLOCK_IDS.has(String(id)))
	v.play(&"idle", 0.0)
	return v


## Height of the character's top above its feet (m, visual-local) from the model's own mesh bounds: rest pose for a
## GLB, rest pose for a stand-in; props and anything a module adds later are not counted (measured at creation).
## Camera framing uses it (SPEC §10: real bounds, not constants).
func model_top() -> float:
	return _top if _top > 0.1 else height


## Up to 36 points (visual-local, rest pose) spread over the top 15 % of the model's height: where the top really is
## (a hydra's horn tips sit well ahead of its body centre). Computed on the first call from the vertex arrays of the
## model's own meshes (recorded at creation, so props are not counted).
func model_top_points() -> PackedVector3Array:
	if _top_pts.is_empty():
		_top_pts = _measure_top_points()
	return _top_pts


func _measure_top_points() -> PackedVector3Array:
	var top := model_top()
	var band := top * 0.85
	var pts: Array[Vector3] = []
	var pt_bones: Array[int] = []
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for mi in _body_meshes:
		if not is_instance_valid(mi) or mi.mesh == null:
			continue
		var xf := _local_xform(mi)
		if (xf * mi.get_aabb()).end.y < band:
			continue
		for si in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(si)
			if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null:
				continue
			var verts := arr[Mesh.ARRAY_VERTEX] as PackedVector3Array
			var bones := PackedInt32Array()
			var weights := PackedFloat32Array()
			if _skel != null and mi.skin != null and arr[Mesh.ARRAY_BONES] != null and arr[Mesh.ARRAY_WEIGHTS] != null:
				bones = arr[Mesh.ARRAY_BONES]
				weights = arr[Mesh.ARRAY_WEIGHTS]
			var stride := bones.size() / verts.size() if verts.size() > 0 and bones.size() == weights.size() else 0
			for vi in verts.size():
				var w: Vector3 = xf * verts[vi]
				if w.y >= band:
					pts.append(w)
					pt_bones.append(_dominant_bone(mi.skin, bones, weights, vi, stride) if stride > 0 else -1)
					lo = Vector2(minf(lo.x, w.x), minf(lo.y, w.z))
					hi = Vector2(maxf(hi.x, w.x), maxf(hi.y, w.z))
	var out := PackedVector3Array()
	_top_bone = PackedInt32Array()
	_top_local = PackedVector3Array()
	if pts.is_empty():
		out.append(Vector3(0, top, 0))
		_top_bone.append(-1)
		_top_local.append(Vector3.ZERO)
		return out
	# keep the highest vertex of each cell of a 6 x 6 grid over the band's footprint, per carrying bone (so a head that
	# shares a cell with a higher horn still has its own point when it rears up: live_top_points())
	var cells := {}
	var size := (hi - lo).max(Vector2(0.01, 0.01))
	for i in pts.size():
		var w := pts[i]
		var key := Vector3i(clampi(int((w.x - lo.x) / size.x * 6.0), 0, 5), clampi(int((w.z - lo.y) / size.y * 6.0), 0, 5), pt_bones[i])
		if not cells.has(key) or pts[int(cells[key])].y < w.y:
			cells[key] = i
	var skel_inv := _local_xform(_skel).affine_inverse() if _skel != null else Transform3D.IDENTITY
	for k in cells:
		var i := int(cells[k])
		out.append(pts[i])
		var b := pt_bones[i]
		_top_bone.append(b)
		_top_local.append(_skel.get_bone_global_rest(b).affine_inverse() * (skel_inv * pts[i]) if b >= 0 else Vector3.ZERO)
	return out


## Skeleton bone with the largest skin weight on vertex `vi` (-1 when it cannot be mapped).
func _dominant_bone(skin: Skin, bones: PackedInt32Array, weights: PackedFloat32Array, vi: int, stride: int) -> int:
	var best := -1
	var best_w := 0.0
	for j in stride:
		var wt := weights[vi * stride + j]
		if wt > best_w:
			best_w = wt
			best = bones[vi * stride + j]
	if best < 0 or best >= skin.get_bind_count():
		return -1
	var bname := skin.get_bind_name(best)
	var b := _skel.find_bone(String(bname)) if bname != &"" else skin.get_bind_bone(best)
	return b if b >= 0 and b < _skel.get_bone_count() else -1


## model_top_points() in WORLD space as the model stands NOW: each point rides the bone that carries it (rigid, from its
## rest offset), so a neck that rears above its rest height (the hydra's inhale and centre bite) or a head lowered to
## the floor moves the camera's "top of the boss" with it. Stand-ins and unmapped points use the rest pose.
## Also one point per bone box (the bone-space bounds of the vertices that bone carries): the top of the box as posed
## now, so a neck segment that is below the rest top band but rears up during a clip counts as well.
func live_top_points() -> PackedVector3Array:
	var rest := model_top_points()
	var out := PackedVector3Array()
	var xf := global_transform
	var live := _skel != null and is_instance_valid(_skel) and _skel.is_inside_tree() and _top_bone.size() == rest.size()
	var sxf := _skel.global_transform if live else Transform3D.IDENTITY
	for i in rest.size():
		var b := _top_bone[i] if live else -1
		out.append(sxf * (_skel.get_bone_global_pose(b) * _top_local[i]) if b >= 0 else xf * rest[i])
	if not live:
		return out
	if not _boxes_done:
		_measure_bone_boxes()
	for row in _bone_boxes:
		var bx := sxf * _skel.get_bone_global_pose(int(row[0]))
		var h: Vector3 = row[2]
		var c: Vector3 = bx * (row[1] as Vector3)
		var up := absf(bx.basis.x.y) * h.x + absf(bx.basis.y.y) * h.y + absf(bx.basis.z.y) * h.z
		out.append(Vector3(c.x, c.y + up, c.z))
	return out


## Bone boxes for live_top_points(): for every skeleton bone that is the main influence (weight >= 0.5) of at least
## BOX_MIN_VERTS vertices of the model's own meshes, the bounds of those vertices in the bone's rest space.
## Measured once, on the first call (one pass over the vertex arrays).
func _measure_bone_boxes() -> void:
	_boxes_done = true
	_bone_boxes.clear()
	if _skel == null:
		return
	var skel_inv := _local_xform(_skel).affine_inverse()
	var rest_inv := {}
	var acc := {}   # bone -> [min, max, count]
	for mi in _body_meshes:
		if not is_instance_valid(mi) or mi.mesh == null or mi.skin == null:
			continue
		var to_skel := skel_inv * _local_xform(mi)
		for si in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(si)
			if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null or arr[Mesh.ARRAY_BONES] == null or arr[Mesh.ARRAY_WEIGHTS] == null:
				continue
			var verts := arr[Mesh.ARRAY_VERTEX] as PackedVector3Array
			var bones: PackedInt32Array = arr[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
			if verts.is_empty() or bones.size() != weights.size():
				continue
			var stride := bones.size() / verts.size()
			var map := {}  # bind index -> skeleton bone
			for vi in verts.size():
				var best := -1
				var best_w := 0.0
				for j in stride:
					var wt := weights[vi * stride + j]
					if wt > best_w:
						best_w = wt
						best = bones[vi * stride + j]
				if best < 0 or best_w < 0.5:
					continue
				if not map.has(best):
					map[best] = _dominant_bone(mi.skin, PackedInt32Array([best]), PackedFloat32Array([1.0]), 0, 1)
				var b: int = map[best]
				if b < 0:
					continue
				if not rest_inv.has(b):
					rest_inv[b] = _skel.get_bone_global_rest(b).affine_inverse()
				var p: Vector3 = (rest_inv[b] as Transform3D) * (to_skel * verts[vi])
				if not acc.has(b):
					acc[b] = [p, p, 0]
				var a: Array = acc[b]
				a[0] = (a[0] as Vector3).min(p)
				a[1] = (a[1] as Vector3).max(p)
				a[2] = int(a[2]) + 1
	for b in acc:
		var a: Array = acc[b]
		if int(a[2]) < BOX_MIN_VERTS:
			continue
		var lo: Vector3 = a[0]
		var hi: Vector3 = a[1]
		_bone_boxes.append([int(b), (lo + hi) * 0.5, (hi - lo) * 0.5])


## Mesh -> visual transform through the local transforms (works before the visual enters the tree).
func _local_xform(n: Node) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var p: Node = n
	while p != null and p != self:
		if p is Node3D:
			xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


func _measure_top() -> float:
	var root: Node3D = _model if _model != null else _standin
	if root == null:
		return height
	var top := 0.0
	_body_meshes.clear()
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null or _is_prop_mesh(mi, root):
			continue
		_body_meshes.append(mi)
		top = maxf(top, (_local_xform(mi) * mi.get_aabb()).end.y)
	return top


## A mesh that rides a bone instead of being skinned (a club / sword exported inside the GLB: glTF imports it under a
## BoneAttachment3D) is a prop: model_top() and the top points ignore it (the Cyclops club would add 3.4 m).
func _is_prop_mesh(mi: MeshInstance3D, root: Node) -> bool:
	if is_standin:
		return false
	var p := mi.get_parent()
	while p != null and p != root:
		if p is BoneAttachment3D:
			return true
		p = p.get_parent()
	return false


func _load_model(path: String, manifest_path := "") -> void:
	if path.begins_with("res://"):
		var ps := load(path) as PackedScene
		if ps != null:
			_model = ps.instantiate() as Node3D
	else:
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		if doc.append_from_file(path, st) == OK:
			_model = doc.generate_scene(st) as Node3D
	if _model == null:
		push_warning("CharacterVisual: cannot load %s, using stand-in" % path)
		return
	add_child(_model)
	is_standin = false
	var mpath := manifest_path if manifest_path != "" else "res://assets/characters/%s/%s_clips.json" % [char_id, char_id]
	if FileAccess.file_exists(mpath):
		var d = JSON.parse_string(FileAccess.get_file_as_string(mpath))
		if d is Dictionary:
			manifest = d
	_anim = _find_type(_model, "AnimationPlayer") as AnimationPlayer
	_skel = _find_type(_model, "Skeleton3D") as Skeleton3D
	if _anim != null:
		_index_animations()
		_anim.animation_finished.connect(_on_anim_finished)
	_make_sockets()
	_top = _measure_top()              # before the toon pass: its outline width follows the real height
	_apply_toon(_model)


## Turns the upper body about the vertical axis on top of the playing clip: `angle` radians (+ = to the character's
## left, like rotation.y) spread over the spine bones, `head_extra` more over neck and head. (0, 0) switches it off.
## Bones are found by name ("spine*", "neck*", "head*"); stand-ins and models without them ignore the call.
## The player's locked-on circling run uses it: the legs run along the circle, the chest and head stay on the boss.
func set_upper_twist(angle: float, head_extra := 0.0) -> void:
	if _skel == null:
		return
	if _twist_mod == null:
		if is_zero_approx(angle) and is_zero_approx(head_extra):
			return
		var m := UpperTwist.new()
		m.name = "UpperTwist"
		for b in _skel.get_bone_count():
			var bn := _skel.get_bone_name(b).to_lower()
			if bn.begins_with("spine"):
				m.spine.append(b)
			elif bn.begins_with("neck") or bn.begins_with("head"):
				m.head.append(b)
		_skel.add_child(m)
		_twist_mod = m
		if _grip != null:
			_skel.move_child(_grip, -1)      # the sword fist turns after the twist
	_twist_mod.angle = angle
	_twist_mod.head_extra = head_extra


## Aims the prop on a socket (the hero's sword in locomotion) along `dir` (visual space: +Z front, +Y up, -X the
## character's right) by turning the socket about its own origin (the grip) after every skeleton update, on top of the
## clip and the upper twist. `weight` 0..1 blends from the clip's own angle (0 = off, the socket keeps its manifest
## offset). The prop's axis is its vertex farthest from the socket origin. Stand-ins ignore it.
func set_socket_aim(socket_name: StringName, dir: Vector3, weight: float) -> void:
	var s := String(socket_name)
	if _skel == null or not _sockets.has(s):
		return
	if _grip != null and String((manifest.get("grip_fix", {}) as Dictionary).get("socket", "")) == s:
		# feedback 2: the carry turns the HAND round the grip (grip_fix.gd), not the sword inside the hand
		_grip.carry_dir = (_local_xform(_skel).basis.inverse() * dir).normalized()
		_grip.carry_w = clampf(weight, 0.0, 1.0)
		return
	if not _aim.has(s):
		if weight <= 0.0005:
			return
		var holder: Node3D = _sockets[s]
		var bone := _skel.find_bone(String((manifest.get("sockets", {}) as Dictionary).get(s, "")))
		var axis := Vector3.ZERO
		for n in holder.find_children("*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			if mi.mesh == null:
				continue
			var xf := _rel_xform(mi, holder)
			for si in mi.mesh.get_surface_count():
				var arr := mi.mesh.surface_get_arrays(si)
				if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null:
					continue
				for v in (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array):
					var w: Vector3 = xf * v
					if w.length() > axis.length():
						axis = w
		if bone < 0 or axis.length() < 0.05:
			return
		_aim[s] = {"holder": holder, "bone": bone, "base": holder.transform, "axis": axis.normalized(), "dir": dir, "w": 0.0}
		if not _skel.skeleton_updated.is_connected(_apply_aims):
			_skel.skeleton_updated.connect(_apply_aims)
	var row: Dictionary = _aim[s]
	row["dir"] = dir
	var nw := clampf(weight, 0.0, 1.0)
	# a falling weight (the carry blending out for a strike or the shield) latches the correction in the bone's frame
	# (_apply_aims), so the blade rides with the hand and unwinds evenly: re-aimed live, the shortest arc flipped while
	# the wind-up swung the blade past the carry direction (109-131 deg in one frame)
	if nw <= 0.0005 or nw > float(row["w"]) + 0.00001:
		row["fading"] = false
		row.erase("lq")
	elif nw < float(row["w"]) - 0.00001:
		row["fading"] = true
	row["w"] = nw


## Current set_socket_aim() weight of a socket (0 when off).
func socket_aim_weight(socket_name: StringName) -> float:
	return float((_aim.get(String(socket_name), {}) as Dictionary).get("w", 0.0))


func _apply_aims() -> void:
	var to_skel := _local_xform(_skel).basis.inverse()
	for s in _aim:
		var row: Dictionary = _aim[s]
		var holder: Node3D = row["holder"]
		if not is_instance_valid(holder):
			continue
		var base: Transform3D = row["base"]
		var w := float(row["w"])
		if w <= 0.0005:
			holder.transform = base
			continue
		var bp := _skel.get_bone_global_pose(int(row["bone"]))
		if row.get("fading", false) and row.has("lq"):
			holder.transform = Transform3D(Basis(Quaternion.IDENTITY.slerp(row["lq"] as Quaternion, w)) * base.basis, base.origin)
			continue
		var sx := bp * base
		var d := (sx.basis * (row["axis"] as Vector3)).normalized()
		var t := (to_skel * (row["dir"] as Vector3)).normalized()
		if d.dot(t) > 0.99999:
			if row.get("fading", false):
				row["lq"] = Quaternion.IDENTITY
			holder.transform = base
			continue
		if row.get("fading", false):
			# first frame of a blend-out: the full correction, expressed in the bone's frame (same picture this frame)
			var bq := bp.basis.get_rotation_quaternion()
			row["lq"] = (bq.inverse() * Quaternion(d, t) * bq).normalized()
			holder.transform = Transform3D(Basis(Quaternion.IDENTITY.slerp(row["lq"] as Quaternion, w)) * base.basis, base.origin)
			continue
		var q := Quaternion.IDENTITY.slerp(Quaternion(d, t), w)
		holder.transform = bp.affine_inverse() * Transform3D(Basis(q) * sx.basis, sx.origin)


func _find_type(n: Node, type: String) -> Node:
	if n.is_class(type):
		return n
	for c in n.get_children():
		var f := _find_type(c, type)
		if f != null:
			return f
	return null


## Maps logical clip names (manifest clips + the stand-in clip table) to AnimationPlayer names. An exact name match
## always wins; exporter decorations ("hercules_run", "Armature|run", "run.001") are stripped before comparing; a
## suffix match ("xx_idle") is used only when no exact match exists and never claims a name that is itself a clip
## ("block_idle" never stands in for "idle"). Loop flags: manifest "loop", else the stand-in table's loop flag.
func _index_animations() -> void:
	var clips: Dictionary = manifest.get("clips", {})
	var wanted := {}
	for c in STANDIN_CLIPS:
		wanted[String(c)] = true
	for c in clips:
		wanted[String(c)] = true
	var norm := {}                    # normalized base -> full animation name
	for lib_name in _anim.get_animation_library_list():
		var lib := _anim.get_animation_library(lib_name)
		for a in lib.get_animation_list():
			var full := String(a) if String(lib_name) == "" else "%s/%s" % [lib_name, a]
			_anim_names[String(a).to_lower()] = full        # raw names stay reachable
			var n := _normalize_anim(String(a))
			if not norm.has(n) or String(a).to_lower() == n:
				norm[n] = full
	for c in wanted:
		var lc := String(c).to_lower()
		if norm.has(lc):
			_anim_names[String(c)] = norm[lc]
			continue
		for n in norm:
			if String(n).ends_with("_" + lc) and not wanted.has(String(n)):
				_anim_names[String(c)] = norm[n]
				break
	for c in _anim_names.keys():
		if not wanted.has(String(c)):
			continue
		var anim := _anim.get_animation(_anim_names[c])
		if anim == null:
			continue
		var row: Dictionary = clips.get(String(c), {})
		var loop := false
		if row.has("loop"):
			loop = bool(row["loop"])
		elif STANDIN_CLIPS.has(String(c)):
			loop = bool(STANDIN_CLIPS[String(c)][1])
		else:
			continue
		anim.loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE


## "Armature|Hercules_Run.001" -> "run" (lower case, no armature prefix, no ".001", no "<char_id>_" prefix).
func _normalize_anim(raw: String) -> String:
	var n := raw.to_lower()
	if "|" in n:
		n = n.get_slice("|", n.get_slice_count("|") - 1)
	if "." in n:
		n = n.get_slice(".", 0)
	var pre := String(char_id).to_lower() + "_"
	if n.begins_with(pre):
		n = n.substr(pre.length())
	return n


func _make_sockets() -> void:
	var socks: Dictionary = manifest.get("sockets", {})
	var offs: Dictionary = manifest.get("socket_offsets", {})
	for logical in socks:
		var bone := String(socks[logical])
		var holder := Node3D.new()
		holder.name = "S_" + String(logical)
		if _skel != null and _skel.find_bone(bone) >= 0:
			var ba := BoneAttachment3D.new()
			ba.name = "B_" + String(logical)
			ba.bone_name = bone
			_skel.add_child(ba)
			ba.add_child(holder)
		else:
			_warn_once("bone_" + bone, "CharacterVisual %s: bone '%s' for socket '%s' not found" % [char_id, bone, logical])
			add_child(holder)
			holder.position = Vector3(0, height * 0.6, 0)
		var o: Dictionary = offs.get(logical, {})
		holder.transform = offset_transform(o, String(manifest.get("offset_space", "blender")))
		_sockets[String(logical)] = holder


## Socket offset {loc, rot_deg} -> Transform3D in the Godot bone frame. space "blender" (default): loc + XYZ Euler of
## the prop object relative to its bone, as the rig agents read them in Blender. glTF keeps Blender bone frames, but a
## prop GLB's mesh coordinates are Y-up converted (Blender (x, y, z) -> Godot (x, z, -y)), hence the trailing C^-1.
## Verified 2026-11-22 against art_src/chars/hercules/split_sheet.png (sword forward, shield face outward).
## space "godot": loc + Godot (YXZ) Euler, used as is.
static func offset_transform(o: Dictionary, space := "blender") -> Transform3D:
	var l: Array = o.get("loc", [0, 0, 0])
	var r: Array = o.get("rot_deg", [0, 0, 0])
	var loc := Vector3(l[0], l[1], l[2])
	var rad := Vector3(deg_to_rad(r[0]), deg_to_rad(r[1]), deg_to_rad(r[2]))
	if space == "godot":
		return Transform3D(Basis.from_euler(rad), loc)
	var rb := Basis(Vector3(0, 0, 1), rad.z) * Basis(Vector3(0, 1, 0), rad.y) * Basis(Vector3(1, 0, 0), rad.x)
	var c := Basis(Vector3(1, 0, 0), Vector3(0, 0, -1), Vector3(0, 1, 0))
	return Transform3D(rb * c.inverse(), loc)


## Toon + ink outline on every surface of a real model or prop. The GLB albedo is used as is (its factor too, but a
## near-black factor from an exporter is ignored so a texture is never darkened); doubleSided materials keep both
## faces; the ink line is screen-constant (OUTLINE_PX) and capped from the model's real height.
func _apply_toon(n: Node) -> void:
	var h := maxf(model_top(), 0.5) if not is_standin else height
	var ow := outline_width_for(h)
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.mesh != null:
			for i in mi.mesh.get_surface_count():
				var src := mi.get_active_material(i)
				var col := Color.WHITE
				var tex: Texture2D = null
				var double := false
				if src is BaseMaterial3D:
					var bm := src as BaseMaterial3D
					col = bm.albedo_color
					tex = bm.albedo_texture
					double = bm.cull_mode == BaseMaterial3D.CULL_DISABLED
					if tex != null and col.get_luminance() < 0.05:
						col = Color.WHITE
				var m := make_toon(col, tex, ow, 0.22, double)
				mi.set_surface_override_material(i, m)
				_materials.append(m)
				if m.next_pass is ShaderMaterial:
					var o := m.next_pass as ShaderMaterial
					if not is_standin:
						set_outline_px(o, h * OUTLINE_MAX_FRAC)
					_outlines.append(o)
	for c in n.get_children():
		_apply_toon(c)


# ------------------------------------------------------------------ API
## Plays a clip with a cross-fade; unknown clips are ignored with one warning.
## from_time >= 0 starts the clip at that CLIP time (seconds) instead of its start (or its end when speed < 0).
func play(clip: StringName, blend := 0.15, speed := 1.0, from_time := -1.0) -> void:
	var c := String(clip)
	if not is_standin:
		if _anim == null or not _anim_names.has(c):
			_warn_once("clip_" + c, "CharacterVisual %s: no clip '%s'" % [char_id, c])
			return
		current_clip = clip
		_finished_sent = false
		var full: String = _anim_names[c]
		# AnimationPlayer.play() on the clip already assigned RESUMES it (4.7.2): restart it from 0 instead.
		# A negative speed plays the clip backwards from its end (e.g. the hero's roll used as a backward roll).
		var again := String(_anim.assigned_animation) == full
		var back := speed < 0.0
		_custom_speed = -1.0 if back else 1.0
		_speed = speed
		_apply_speed()
		# the AnimationPlayer runs its cross-fade on the scaled clock (speed_scale = |speed|): a 0.15 s blend into a
		# clip played at 2.5x lasted 0.06 s, a one-frame snap (core_polish2: idle -> strafe turned the shield forearm
		# 168 deg in one frame). Frame-clock characters (hero, Pegasus) get `blend` in real seconds; bosses keep the
		# blends their modules tuned on the scaled clock.
		# They fade at the skeleton (pose_fade.gd) from the pose on screen: the player's own cross-fade, started while
		# another one runs, cut the older clip's remaining weight in one frame (a roll -> strafe popped 125 deg), and
		# play_with_capture() did not fade skeleton tracks in 4.7.2.
		if not _physics_clock and _skel != null:
			if _fade == null:
				_fade = PoseFade.new()
				_fade.name = "PoseFade"
				_skel.add_child(_fade)
			var first := 0
			for ch in _skel.get_children():
				if ch is SkeletonModifier3D:
					break
				first += 1
			if _fade.get_index() > first:
				_skel.move_child(_fade, first)        # before the upper twist and the socket aims
			_fade.start(blend)
			_anim.play(full, 0.0, _custom_speed, back)
		else:
			_anim.play(full, blend, _custom_speed, back)
		if from_time >= 0.0:
			_anim.seek(minf(from_time, _anim.current_animation_length), true)
		elif again:
			_anim.seek(_anim.current_animation_length if back else 0.0, true)
		return
	if not STANDIN_CLIPS.has(c):
		_warn_once("clip_" + c, "CharacterVisual %s (stand-in): no clip '%s'" % [char_id, c])
		return
	var row: Array = STANDIN_CLIPS[c]
	current_clip = clip
	_clip_t = 0.0
	_clip_speed = speed
	_clip_len = row[0]
	_clip_loop = row[1]
	_clip_kind = row[2]
	_clip_windup = row[3]
	_finished_sent = false
	_from_pose = _prev_pose.duplicate()
	_blend_len = maxf(blend, 0.0)
	_blend_t = 0.0
	if from_time >= 0.0:
		_clip_t = from_time


## Jumps the clip that is playing to CLIP time `t` (seconds), keeping its speed; `update` applies the pose at once.
## Use it to keep a timed clip on the game (physics) clock instead of reaching into the AnimationPlayer.
func seek(t: float, update := true) -> void:
	if is_standin:
		_clip_t = maxf(t, 0.0)
		return
	if _anim != null and String(_anim.assigned_animation) != "":
		_anim.seek(clampf(t, 0.0, _anim.current_animation_length), update)


## CLIP time (seconds) of the clip that is playing: 0 at its start, its length at its end (looping clips wrap).
func clip_position() -> float:
	if is_standin:
		return fmod(_clip_t, maxf(_clip_len, 0.01)) if _clip_loop else minf(_clip_t, _clip_len)
	if _anim == null or String(_anim.assigned_animation) == "":
		return 0.0
	return _anim.current_animation_position


## Bosses (PHYSICS_CLOCK_IDS) advance their clips on the physics clock, the same clock as their state machines, so a
## frame hitch (windowed --shots, a slow machine) cannot let a timed clip (slam, fire_sweep, gaze) drift off the game
## timers. The hero and Pegasus stay on the frame clock (smooth at any refresh rate; their logic follows the clips).
func use_physics_clock(on: bool) -> void:
	_physics_clock = on
	if _anim != null:
		_anim.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS if on else AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE


func uses_physics_clock() -> bool:
	return _physics_clock


## Changes the playback rate of the clip that is playing, without restarting or re-blending it (locomotion speed
## matching, fire-sweep timing). Negative = backwards. The next play() sets its own speed again.
func set_speed(speed: float) -> void:
	if is_standin:
		_clip_speed = speed
		return
	_speed = speed
	_apply_speed()


## Current playback rate of the clip (1.0 = as authored).
func get_speed() -> float:
	return _clip_speed if is_standin else _speed


func _apply_speed() -> void:
	if _anim != null:
		_anim.speed_scale = 0.0 if _petrify > 0.5 else _speed / _custom_speed


## Ground speed (m/s) the clip's planted feet travel at playback speed 1.0 (manifest `move_speed`), 0 when unknown.
## Locomotion code plays the clip at ground_speed / move_speed so the feet do not skate.
func move_speed(clip: StringName) -> float:
	var row: Dictionary = (manifest.get("clips", {}) as Dictionary).get(String(clip), {})
	return float(row.get("move_speed", 0.0))


## True when the clip exists (in the GLB manifest, or in the stand-in table).
func has_clip(clip: StringName) -> bool:
	if not is_standin:
		return _anim_names.has(String(clip))
	return STANDIN_CLIPS.has(String(clip))


## Clip length in seconds (manifest / animation / stand-in table), or `fallback`.
func clip_length(clip: StringName, fallback := 1.0) -> float:
	var c := String(clip)
	if not is_standin:
		var clips: Dictionary = manifest.get("clips", {})
		if clips.has(c) and clips[c].has("length"):
			return float(clips[c]["length"])
		if _anim != null and _anim_names.has(c):
			return _anim.get_animation(_anim_names[c]).length
		return fallback
	if STANDIN_CLIPS.has(c):
		return float(STANDIN_CLIPS[c][0])
	return fallback


## Time of a named event inside a clip (from <id>_clips.json), or `fallback`.
func event_time(clip: StringName, event: StringName, fallback: float) -> float:
	var clips: Dictionary = manifest.get("clips", {})
	var row: Dictionary = clips.get(String(clip), {})
	var ev: Dictionary = row.get("events", {})
	return float(ev.get(String(event), fallback))


## A node that follows a bone (or a stand-in marker). Unknown names get a marker at chest height (one warning).
func socket(socket_name: StringName) -> Node3D:
	var s := String(socket_name)
	if _sockets.has(s):
		return _sockets[s]
	if _standin != null and _standin.sockets.has(s):
		return _standin.sockets[s]
	_warn_once("sock_" + s, "CharacterVisual %s: unknown socket '%s' (marker added)" % [char_id, s])
	var m := Node3D.new()
	m.name = "S_" + s
	add_child(m)
	m.position = Vector3(0, height * 0.6, 0)
	_sockets[s] = m
	return m


## Adds (or moves) a named socket marker at a local position, parented to another socket (or the visual root).
func add_socket(socket_name: StringName, local_pos: Vector3, parent_socket: StringName = &"") -> Node3D:
	var s := String(socket_name)
	var m: Node3D = _sockets.get(s)
	if m == null:
		m = Node3D.new()
		m.name = "S_" + s
		var parent: Node3D = self if parent_socket == &"" else socket(parent_socket)
		parent.add_child(m)
		_sockets[s] = m
	m.position = local_pos
	return m


## Attaches a prop scene (GLB) to a socket; a stand-in box/disc when the file is missing. Returns the prop node.
func attach_prop(socket_name: StringName, path: String) -> Node3D:
	var sock := socket(socket_name)
	var prop: Node3D = null
	if ResourceLoader.exists(path):
		var ps := load(path) as PackedScene
		if ps != null:
			prop = ps.instantiate() as Node3D
	if prop != null:
		_apply_toon(prop)
	else:
		prop = _standin_prop(path)
	sock.add_child(prop)
	_props.append(prop)
	_make_grip_fix(socket_name)
	return prop


## Manifest "grip_fix" {socket, bone, forearm, authored_offset, forearm_share, swing_max_deg, clip_dirs}: the hand turns
## round the prop's grip (grip_fix.gd) so the blade leaves the fist on the thumb side, pointing where the clip authored
## it (authored_offset = the socket offset the clips were keyed with) or along a carry (set_socket_aim / clip_dirs).
## The prop's axis is its local +Y (the sword's blade).
func _make_grip_fix(socket_name: StringName) -> void:
	var gf: Dictionary = manifest.get("grip_fix", {})
	if _grip != null or _skel == null or gf.is_empty() or String(gf.get("socket", "")) != String(socket_name):
		return
	var hb := _skel.find_bone(String(gf.get("bone", "")))
	if hb < 0:
		return
	var space := String(manifest.get("offset_space", "blender"))
	var cur: Dictionary = (manifest.get("socket_offsets", {}) as Dictionary).get(String(socket_name), {})
	var m := GripFix.new()
	m.name = "GripFix"
	m.visual = self
	m.hand = hb
	m.forearm = _skel.find_bone(String(gf.get("forearm", "")))
	m.blade_new = (offset_transform(cur, space).basis * Vector3.UP).normalized()
	m.grip_local = offset_transform(cur, space).origin
	m.blade_old = (offset_transform(gf.get("authored_offset", cur), space).basis * Vector3.UP).normalized()
	m.forearm_share = float(gf.get("forearm_share", 0.45))
	m.swing_max = deg_to_rad(float(gf.get("swing_max_deg", 40.0)))
	var to_skel := _local_xform(_skel).basis.inverse()
	var cdirs: Dictionary = gf.get("clip_dirs", {})
	for c in cdirs:
		var d: Array = cdirs[c]
		m.clip_dirs[String(c)] = (to_skel * Vector3(d[0], d[1], d[2])).normalized()
	var rolls: Dictionary = gf.get("clip_roll_deg", {})
	for c in rolls:
		m.clip_roll[String(c)] = deg_to_rad(float(rolls[c]))
	var rfrom: Dictionary = gf.get("clip_roll_from", {})
	for c in rfrom:
		m.clip_roll_from[String(c)] = float(rfrom[c])
	m.clip_dir_blend = float(gf.get("clip_dir_blend", 0.4))
	_skel.add_child(m)           # last modifier: after the pose fade and the upper twist (set_upper_twist keeps it last)
	_grip = m
	# a second hero visual (the mount rider, made where the walking hero stands) starts with the hero's sword carry
	var pl := get_tree().get_first_node_in_group("player") if is_inside_tree() else null
	if pl != null and pl.get("visual") is CharacterVisual and pl.get("visual") != self:
		copy_grip_state(pl.get("visual"))


## Copies another visual's sword-fist state (grip_fix carry + twist) so this one takes over without a jump.
func copy_grip_state(from: CharacterVisual) -> void:
	if _grip != null and from != null and from._grip != null:
		_grip.copy_state(from._grip)


## The props added with attach_prop() (still attached or dropped).
func props() -> Array[Node3D]:
	return _props


## Lets every attached prop fall from where it is now and come to rest flat on the floor at world height `floor_y`
## (e.g. the hero's sword and shield at the death clip's `drop_props` event). The props move under `parent` (the scene)
## so they stay where they land. Returns the dropped props.
func drop_props(parent: Node, floor_y: float, secs := 0.4) -> Array[Node3D]:
	var out: Array[Node3D] = []
	for p in _props:
		if not is_instance_valid(p) or p.get_parent() == parent:
			continue
		var xf := p.global_transform
		p.get_parent().remove_child(p)
		parent.add_child(p)
		p.global_transform = xf
		# local bounds -> the thinnest axis ends up vertical (the shield lies on its face, the sword on its flat)
		var ab := AABB()
		var first := true
		var meshes: Array = p.find_children("*", "MeshInstance3D", true, false)
		if p is MeshInstance3D:
			meshes.append(p)
		for mi in meshes:
			var m := mi as MeshInstance3D
			if m.mesh == null:
				continue
			var b := _rel_xform(m, p) * m.get_aabb()
			ab = b if first else ab.merge(b)
			first = false
		var ax := 0
		for i in [1, 2]:
			if ab.size[i] < ab.size[ax]:
				ax = i
		var axis := Vector3.ZERO
		axis[ax] = 1.0
		var up := (xf.basis * axis).normalized()
		if up.y < 0.0:
			up = -up
		var basis := (Basis(Quaternion(up, Vector3.UP)) * xf.basis).orthonormalized()
		var half_thin := ab.size[ax] * 0.5 * xf.basis.get_scale()[ax]
		var origin := xf.origin
		origin.y = floor_y + half_thin + 0.01 - (basis * ab.get_center()).y
		var q0 := xf.basis.get_rotation_quaternion()
		var q1 := basis.get_rotation_quaternion()
		var sc := xf.basis.get_scale()
		var o0 := xf.origin
		var tw := p.create_tween()
		tw.tween_method(func(k: float) -> void:
			var e := k * k                                  # falls (accelerates), then rests
			p.global_transform = Transform3D(Basis(q0.slerp(q1, k)) * Basis.from_scale(sc), o0.lerp(origin, e)), 0.0, 1.0, secs)
		out.append(p)
	return out


static func _rel_xform(n: Node3D, top: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var p: Node = n
	while p != null and p != top:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


func _standin_prop(path: String) -> Node3D:
	var f := path.get_file().to_lower()
	var mi := MeshInstance3D.new()
	mi.name = "Prop_" + f.get_basename()
	var ow := outline_width_for(height) * 0.6
	if "shield" in f:
		var cm := CylinderMesh.new()
		cm.top_radius = 0.45
		cm.bottom_radius = 0.45
		cm.height = 0.06
		mi.mesh = cm
		mi.rotation_degrees = Vector3(90, 0, 0)
		mi.position = Vector3(0, 0, 0.12)
		mi.material_override = make_toon(Color(0.72, 0.55, 0.18), null, ow)
	elif "club" in f:
		var cm2 := CylinderMesh.new()
		cm2.top_radius = 0.45
		cm2.bottom_radius = 0.18
		cm2.height = 5.5
		mi.mesh = cm2
		mi.position = Vector3(0, -2.4, 0)
		mi.material_override = make_toon(Color(0.42, 0.30, 0.18), null, ow)
	else:
		var bm := BoxMesh.new()
		bm.size = Vector3(0.07, 0.85, 0.025)
		mi.mesh = bm
		mi.position = Vector3(0, -0.45, 0)
		mi.material_override = make_toon(Color(0.85, 0.86, 0.88), null, ow)
	if mi.material_override is ShaderMaterial:
		_materials.append(mi.material_override)
		if (mi.material_override as ShaderMaterial).next_pass is ShaderMaterial:
			_outlines.append((mi.material_override as ShaderMaterial).next_pass)
	return mi


## Briefly flashes the whole character (hit feedback). `strength` = the added emission at the start (0.85 = near-white).
func flash(color: Color, seconds := 0.12, strength := 0.85) -> void:
	if _flash_tween != null and _flash_tween.is_valid():
		_flash_tween.kill()
	for m in _materials:
		m.set_shader_parameter("flash_color", color)
		m.set_shader_parameter("flash", strength)
	_flash_tween = create_tween()
	_flash_tween.tween_method(_set_flash, strength, 0.0, seconds)


func _set_flash(v: float) -> void:
	for m in _materials:
		m.set_shader_parameter("flash", v)


## Turns the character to stone (or back).
func set_petrified(on: bool) -> void:
	_petrify = 1.0 if on else 0.0
	for m in _materials:
		m.set_shader_parameter("petrify", _petrify)
	for o in _outlines:
		o.set_shader_parameter("petrify", _petrify)
	_apply_speed()


## Multiplies the albedo of every surface (e.g. a red tint while enraged). White = none.
func set_tint(color: Color) -> void:
	for m in _materials:
		m.set_shader_parameter("tint", color)


## Near-camera fade (toon + ink `near_fade_hide` / `near_fade_full`): hidden closer than hide_m metres to the camera,
## fully drawn from full_m on, dithered between. 0 / 0 = off (the default). `under` = null: every surface of this
## character (its props too); a node: only the toon / ink materials of the meshes below it (e.g. a club with its own range).
func set_near_fade(hide_m: float, full_m: float, under: Node = null) -> void:
	if under == null:
		for m in _materials:
			m.set_shader_parameter("near_fade_hide", hide_m)
			m.set_shader_parameter("near_fade_full", full_m)
		for o in _outlines:
			o.set_shader_parameter("near_fade_hide", hide_m)
			o.set_shader_parameter("near_fade_full", full_m)
		return
	var shaders := [TOON_SHADER, toon_shader(true), OUTLINE_SHADER]
	var stack: Array[Node] = [under]
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
					sm.set_shader_parameter("near_fade_hide", hide_m)
					sm.set_shader_parameter("near_fade_full", full_m)
				m = sm.next_pass


func _warn_once(key: String, msg: String) -> void:
	if _warned.has(key):
		return
	_warned[key] = true
	push_warning(msg)


func _on_anim_finished(anim_name: StringName) -> void:
	for c in _anim_names:
		if _anim_names[c] == String(anim_name):
			clip_finished.emit(StringName(c))
			return


# ------------------------------------------------------------------ stand-in procedural clips
func _process(delta: float) -> void:
	if not _physics_clock:
		_tick_standin(delta)


func _physics_process(delta: float) -> void:
	if _physics_clock:
		_tick_standin(delta)


func _tick_standin(delta: float) -> void:
	if _standin == null or _petrify > 0.5:
		return
	_clock += delta
	_clip_t += delta * _clip_speed
	var u := _clip_t / maxf(_clip_len, 0.01)
	if _clip_loop:
		u = fmod(u, 1.0)
	elif u >= 1.0:
		u = 1.0
		if not _finished_sent:
			_finished_sent = true
			clip_finished.emit(current_clip)
	var p := _standin_pose(_clip_kind, u)
	if _blend_len > 0.0 and _blend_t < _blend_len:
		_blend_t += delta
		var k := clampf(_blend_t / _blend_len, 0.0, 1.0)
		for key in p:
			p[key] = lerpf(float(_from_pose.get(key, 0.0)), float(p[key]), k)
		for key in _from_pose:
			if not p.has(key):
				p[key] = lerpf(float(_from_pose[key]), 0.0, k)
	_prev_pose = p
	_standin.pose(p)


## Pose parameters for a procedural clip kind at normalized time u (0..1).
func _standin_pose(kind: String, u: float) -> Dictionary:
	var w := _clip_windup
	var s := sin(u * TAU)
	match kind:
		"idle":
			return {"bob": sin(_clock * 1.6) * height * 0.008, "arm_r": 0.05, "arm_l": -0.05, "wing": 0.15}
		"block":
			return {"arm_l": -1.35, "lean": 0.05}
		"walk", "slither":
			return {"stride": s * 0.55, "bob": absf(s) * height * 0.015, "arm_r": -s * 0.45, "arm_l": s * 0.45, "tail_twist": s * 0.25, "lean": 0.06}
		"fly":
			return {"wing": s * 0.7, "stride": 0.4, "bob": s * 0.05}
		"glide":
			return {"wing": 0.1 + s * 0.08}
		"roll":
			return {"spin": u * TAU, "lean": 0.0}
		"strike_r", "strike_l", "sweep", "slam", "gaze", "tail", "fire", "stomp":
			return _strike_pose(kind, u, w)
		"low":
			return {"lean": 0.32, "head_dip": 0.9, "head_c_dip": HEAD_C_DIP, "arm_r": -0.9, "arm_l": -0.5, "bob": -height * 0.06 + sin(_clock * 2.0) * 0.02}
		"drop":
			var k := _ease(u)
			return {"lean": 0.32 * k, "head_dip": 0.9 * k, "head_c_dip": HEAD_C_DIP * k, "arm_r": -0.9 * k, "arm_l": -0.5 * k, "bob": -height * 0.06 * k}
		"rise":
			var k2 := 1.0 - _ease(u)
			return {"lean": 0.32 * k2, "head_dip": 0.9 * k2, "head_c_dip": HEAD_C_DIP * k2, "arm_r": -0.9 * k2 - 0.3 * sin(u * PI), "arm_l": -0.5 * k2, "bob": -height * 0.06 * k2}
		"hurt":
			var j := sin(u * PI)
			return {"lean": -0.25 * j, "head_dip": -0.3 * j, "arm_r": 0.3 * j, "arm_l": 0.3 * j}
		"death":
			var d := _ease(minf(u * 1.4, 1.0))
			var info := Tuning.char_info(char_id)
			var lift := float(info.get("radius", 0.5)) * 0.5 * d     # lying bodies rest on their side, not half in the floor
			match String(info.get("fall", "side")):
				"back":       # bosses: away from the hero and the chase camera
					return {"lean": -1.45 * d, "bob": lift, "head_dip": 0.4 * d, "arm_r": 0.6 * d, "arm_l": 0.6 * d}
				"forward":    # the hero: away from the camera behind him
					return {"lean": 1.4 * d, "bob": lift, "head_dip": -0.3 * d, "arm_r": -1.2 * d, "arm_l": -1.0 * d}
			return {"topple": 1.45 * d, "lean": -0.1 * d, "bob": -height * 0.05 * d, "head_dip": 0.4 * d}
	return {}


## Windup -> strike -> recover shape shared by every attack kind (w = strike moment as a fraction of the clip).
func _strike_pose(kind: String, u: float, w: float) -> Dictionary:
	var wind := _ease(clampf(u / maxf(w, 0.01), 0.0, 1.0))
	var after := clampf((u - w) / maxf(1.0 - w, 0.01), 0.0, 1.0)
	var hit := 1.0 - _ease(clampf(after * 4.0, 0.0, 1.0))    # snaps through in the first quarter after the strike
	var back := 1.0 - _ease(clampf((after - 0.5) * 2.0, 0.0, 1.0))
	var a := wind * (1.0 - after)                              # windup amount, released at the strike
	var f := (1.0 - hit) * back if u >= w else 0.0             # follow-through amount
	match kind:
		"strike_r":
			return {"arm_r": -2.4 * a + -1.2 * f, "lean": -0.08 * a + 0.12 * f, "twist": 0.35 * a - 0.3 * f, "head_dip": 0.5 * f}
		"strike_l":
			return {"arm_r": -1.6 * a - 0.9 * f, "lean": -0.06 * a + 0.12 * f, "twist": -0.4 * a + 0.4 * f}
		"sweep":
			return {"arm_r": -1.0 * a - 1.3 * f, "arm_l": -0.4 * a, "twist": 0.9 * a - 0.9 * f, "lean": -0.05 * a + 0.08 * f}
		"slam":
			return {"arm_r": -3.0 * a - 1.0 * f, "arm_l": -3.0 * a - 1.0 * f, "lean": -0.18 * a + 0.32 * f, "head_dip": 0.3 * f, "bob": -height * 0.04 * f}
		"gaze":
			return {"head_dip": -0.25 * a + 0.1 * f, "lean": -0.1 * a + 0.08 * f, "arm_r": 0.4 * a, "arm_l": 0.4 * a}
		"tail":
			return {"tail_twist": -0.8 * a + 2.4 * f, "lean": 0.1 * a, "twist": -0.3 * a + 0.4 * f}
		"fire":
			return {"head_dip": -0.6 * a + 0.35 * f, "lean": -0.1 * a + 0.05 * f}
		"stomp":
			return {"leg_lift": 0.9 * a, "lean": -0.1 * a + 0.08 * f, "bob": -height * 0.02 * f, "stride": 0.0}
	return {}


func _ease(x: float) -> float:
	return x * x * (3.0 - 2.0 * x)
