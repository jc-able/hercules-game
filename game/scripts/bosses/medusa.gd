extends BossBase
## Medusa, the second labor (SPEC §3.2; sizes from SPEC §10: 6.5 m upright, tail 9.9 m along the ground).
## States: stalk -> gaze (x2 when enraged) -> stunned (gaze reflected) -> rise -> stalk; tail_swipe when the hero
## lingers inside 5.5 m for 1.5 s; recoil after a side-of-the-neck cut during a gaze. No class_name (loaded by path).
##
## Weak point `neck` (real model): rides the REAL `neck` socket (module socket `neck_wp` copies it every frame).
## The gaze clip holds the neck at 5.05 m (out of a 1.9 m hero's reach), so after the beam fires she lunges down it
## (LeanMod, neck bone to LEAN_NECK_Y); the stunned clips put the head on the floor themselves (neck 0.95 m, 4.55 m
## ahead), so no lean there. Stand-in: the old placement (no skeleton). Measurements: docs/notes/medusa.md.

# Numbers: every gameplay number is in Tuning.MEDUSA (the one place; reasons in docs/notes/medusa.md and
# docs/notes/medusa_polish2.md). The constants below are model measurements and visual details only.
const GAZE_COLOR := Color(0.24, 0.78, 0.30)        # windup fan: saturated mid green (reads on white marble)
const GAZE_EDGE := Color(0.06, 0.36, 0.12)         # windup fan edge (shader edge colour)
const GAZE_LOCK_COLOR := Color(0.03, 0.46, 0.13)   # after the direction lock: deep green
const GAZE_LOCK_EDGE := Color(0.01, 0.12, 0.04)    # after the lock: ink edge
const FAN_LINE_WIDTH := 0.22          # own full-opacity fan edge lines (m, grows with distance), visible beside the hero
const VFX_PRIORITY := 12             # transparent VFX draw ON TOP of the telegraph decals (telegraph material = 10)
const BEAM_TICK := 0.1                # gaze hit test rate (s): fewer duplicate dodge events than every frame
const NECK_Y_MIN := 1.0               # weak point height window (sword box y 0.1 .. 2.9)
const NECK_Y_MAX := 2.3
const LEAN_NECK_Y := 2.1              # procedural lean target: real `neck` bone head at most this high (socket +0.13 m)
const LEAN_IN_TIME := 0.35            # gaze: the lunge down the beam takes this long after the fire starts
# Size (QA fixer 2026-11-22, owner away, Decision in docs/notes/medusa.md): the whole boss is scaled uniformly x1.5
# (6.5 m -> 9.75 m upright, tail 9.9 -> 14.9 m): visual, tail/torso/hair colliders, body capsule, weak point, sweep
# ring, stunned neck spot. Every model measurement below is the 1.0 GLB value times S.
const S := 1.5
const TAIL_SEGS := [[-1.6 * S, 2.6 * S, 0.55 * S], [-4.3 * S, 2.8 * S, 0.45 * S], [-6.9 * S, 2.4 * S, 0.35 * S]]   # stand-in tail capsules: centre z, length, radius
# real model (measured on medusa.glb with work/medusa_int/probe/*.gd, see docs/notes/medusa.md)
const TAIL_CHAIN := [&"tail_05", &"tail_08", &"tail_11", &"tail_14"]   # live tail capsules between these bone heads + the tip
const TAIL_RADII := [0.55 * S, 0.45 * S, 0.35 * S, 0.25 * S]
const TORSO_R := 0.55 * S             # pelvis -> head capsule, only while the upper body lies on the floor (stunned)
const HAIR_R := 0.55 * S              # stunned: snake hair capsule across the lowered head (the hero's legs went through it)
const HAIR_HALF := 0.9 * S            # half length of that capsule (sideways, her right axis)
const HAIR_AHEAD := 0.3 * S           # its centre sits this far ahead of the head socket
const WEAK_R := 1.2                   # neck weak point radius (0.9 at size 1.0; the neck is 1.5x thicker now)
const TAIL_SWEEP_R := 9.3 * S         # tail_swipe: tail tip radius from the body centre while it sweeps the front (visual)
# Tail swipe rule (QA fixer 3, owner away, Decision in docs/notes/medusa.md): ONE readable rule, "the ring lights up
# around her: roll out of it before it fills". Only the inner part of the 14 m tail counts: the hit radius, the ring
# decal and the green sweep crescent are all T.tail_radius; the tail beyond it passes over the hero harmlessly. The ring
# fills in T.tail_coil (normal and enraged alike: the time to get out is always the same); the sweep comes once it is full.
# Proof: work/medusa_fix3/tail_probe.gd (every trigger distance and angle, roll 0.35 s after the warning -> out).
# (ring/hit radius = Tuning.MEDUSA.tail_radius from her body centre: a hero is hit while his centre is within it
# + 0.19 m; ring fill = Tuning.MEDUSA.tail_coil)
const SWEEP_CLIP_SPEED := 1.0         # the flat sweep plays at this clip speed once the ring is full (0.54 s), enraged / 0.85
const SWEEP_DEG_PER_S := 707.0        # tail_swipe: the tip circles 383 deg in 0.54 clip-s (clip 0.625 -> 1.167 s)
const SWEEP_TIP_AT_START := 125.0     # tail_swipe: tip angle (deg, her frame, 0 = ahead) when the flat sweep starts
                                      # (measured in game, work/medusa_fix2/logs/tail_probe.log; bot prediction only)
const SWEEP_SPAN := Vector2(0.625, 1.167)   # tail_swipe clip time of the flat 360 deg sweep
const STUN_START_SPEED := 1.3         # stun_start 1.625 s -> 1.25 s: the head is on the floor sooner
const STUN_NECK_LOCAL := Vector3(0.0, 0.95 * S, 4.55 * S)   # stunned clip: neck socket (her frame) with the head on the floor
const STUN_RECOIL := 3.0              # reflected: she is thrown back this far (m) during the recoil, so her head lands in
const STUN_RECOIL_TIME := 0.9         # front of a hero who reflected from her ~7 m gaze range (ease-out slide, s)
const DEATH_FROM_FLOOR := 2.6         # death clip time where her pelvis is already down: joined from stunned (integrate2:
										# 2.25 -> 2.6 with a 0.6 s blend; the new death clip's left arm crosses a blend
										# flip near clip 2.58 s that made a 2.6 m one-frame hand jump when blended over it)
const DEATH_JOIN_BLEND := 0.6
const BODY_FWD := 0.5 * S             # her upright body stands this far ahead of the root (tail behind)
const REFLECT_RAISE_WINDOW := 0.6     # a gaze reflects only when the shield went up at most this long before the fire (or
                                      # during the beam); a shield held up longer just blocks it (no damage, shove, no stun)
# integration + QA decisions (docs/notes/medusa.md): rise clip 2.5 s reads at 1.2 s; at x1.5 she gazes from ~7 m
# (stalk band 6.5-9.5 m, gaze range 8.5 m; SPEC 9-14 / 10), towering ~1.6x the hero on screen; her area shrinks to 12 m
# so the 14.9 m tail stays inside the 28 m courtyard; the tail trigger grows with her body (5.5 -> 6.0 m)
# (those as-built values now live in Tuning.MEDUSA)
const GAZE_APPROACH := 1.7            # gaze due, hero beyond gaze range: she slithers in to gaze_max_dist - this
const BOT_KEEP := 7.5                 # default win bot holds this range (inside keep_min .. gaze range, outside 6 m)
const BOT_REACT := 0.35               # bot (and the tail probe) react this long after a warning starts, like a person
const SHEET_STOP := 0.6               # beam light sheet lands on the floor this far short of the hero (never over the camera)
const CAM_MAX_EXTRA := 2.0            # lock arm may grow this much for her (PlayerCamera.max_extra_for): her head stays in frame
const SNAP_EYES_LOCAL := Vector3(0.0, 5.65 * S, 2.6 * S)   # gaze clip: her eyes (her frame) right after the fire snap
										# (integrate2, re-based gaze: eyes (-0.07, 8.44, 3.65) at clip 2.0, (-0.05, 8.13, 4.02) in the stare; was 5.95/2.8 x S)


## Procedural forward lean of the real model (rig.json lean_recipe): pelvis rotates about the tail_03 head, tail_03
## keeps its pose (the grounded tail stays put). The angle adapts so the neck bone ends at LEAN_NECK_Y whatever the
## clip already does (a clip that leans far enough gets no extra lean). Runs after the AnimationPlayer.
class LeanMod extends SkeletonModifier3D:
	var weight := 0.0                 # 0 = upright as animated, 1 = neck down at target_y
	var target_y := 2.1               # world height above `floor_node` for the neck bone head
	var floor_node: Node3D            # the boss (feet at its origin)
	var right_node: Node3D            # the visual (its +X = the lean axis: +angle tips +Y toward +Z = forward)
	var pelvis := -1
	var pivot := -1
	var neck := -1
	var head := -1
	var head_keep := 0.8              # share of the lean the neck + head bend back (face level)
	var last_angle := 0.0

	func _process_modification_with_delta(_delta: float) -> void:
		last_angle = 0.0
		var sk := get_skeleton()
		if sk == null or weight <= 0.001 or pelvis < 0 or pivot < 0 or neck < 0 or floor_node == null:
			return
		var xf := sk.global_transform
		var piv_pose := sk.get_bone_global_pose(pivot)
		var c := xf * piv_pose.origin
		var n := xf * sk.get_bone_global_pose(neck).origin
		var axis := right_node.global_basis.x.normalized()
		var up := Vector3.UP
		var fwd := axis.cross(up).normalized()
		var v := n - c
		v -= axis * v.dot(axis)
		var length := v.length()
		if length < 0.1:
			return
		var phi0 := atan2(v.dot(fwd), v.dot(up))          # current lean of pivot->neck from vertical
		var want := acos(clampf((floor_node.global_position.y + target_y - c.y) / length, -1.0, 1.0))
		var a := maxf(want - phi0, 0.0) * clampf(weight, 0.0, 1.0)
		if a < 0.001:
			return
		last_angle = a
		var ax_local := (xf.basis.inverse() * axis).normalized()
		var cl := piv_pose.origin
		var about := Transform3D(Basis.IDENTITY, cl) * Transform3D(Basis(ax_local, a), Vector3.ZERO) * Transform3D(Basis.IDENTITY, -cl)
		sk.set_bone_global_pose(pelvis, about * sk.get_bone_global_pose(pelvis))
		sk.set_bone_global_pose(pivot, piv_pose)
		# the face keeps looking along the gaze (toward the hero) instead of down at the floor
		if head_keep > 0.0:
			for b: int in [neck, head]:          # split over two joints (rig notes: big single-joint bends stretch the hair)
				if b < 0:
					continue
				var bp := sk.get_bone_global_pose(b)
				var back := Transform3D(Basis.IDENTITY, bp.origin) * Transform3D(Basis(ax_local, -a * head_keep * 0.5), Vector3.ZERO) * Transform3D(Basis.IDENTITY, -bp.origin)
				sk.set_bone_global_pose(b, back * bp)

var T: Dictionary = {}

var _moving := false                  # the slither clip is on (she moves or turns), see _update_loco
var _loco_speed := 0.0                # effective locomotion speed (m/s): max(ground speed, turn rate x slither_turn_radius)
var _stalk_v := 0.0                   # slither ground speed now (accelerates / brakes, T.slither_accel)
var _loco_prev_pos := Vector3.INF
var _loco_prev_yaw := 0.0
var _loco_fwd := 0.0                  # smoothed signed ground speed along her facing (m/s, < 0 = backing off)
var _yaw_rate := 0.0                  # signed turn rate now (rad/s): face_towards accelerates it (T.turn_accel_deg)
var _yaw_frame := -10                 # physics frame of the last face_towards call (a gap resets _yaw_rate)
var _retreat_side := 0.0              # stalk: +-1 = side of her retreat arc (0 = not backing off)
var _exit_blend := 0.35               # cross-fade of the one-shot -> idle / slither hand-over (gaze: T.gaze_exit_blend)
var _still_t := 0.0                   # time the effective speed has been under slither_stop_speed
var _finishing := false               # stalk entered while a one-shot (tail_swipe, gaze, rise) still plays out its end
var _close_t := 0.0                   # time the hero has spent inside tail_trigger_dist
var _gaze_wait := 2.5
var _gaze_index := 0                  # 0 = first gaze of a volley, 1 = enraged follow-up
var _gaze_windup := 1.2
var _gaze_dir := Vector3.FORWARD
var _gaze_locked := false
var _fired := false
var _beam_done := false
var _beam_tick_t := 0.0
var _beam_resolved := false
var _neck_close_in := -1.0            # gaze neck window countdown (< 0 = none)
var _decal: Telegraph = null
var _coil := 0.7
var _impact_done := false
var _stun_looping := false
var _recoil_len := 0.5
var _eyes: Node3D = null
var _eye_halo: MeshInstance3D = null
var _beam: MeshInstance3D = null
var _beam_mesh: ImmediateMesh = null
var _neck_socket: Node3D = null
var _fan_edges: MeshInstance3D = null
var _fan_mesh: ImmediateMesh = null
var _fan_pulse := 0.0                 # > 0 right after the lock: edge lines widen
var _hit_at := -1.0                   # state_time of a gaze HIT in this gaze (< 0 = none)
var _lean: LeanMod = null
var _lean_goal := 0.0
var _turn_blocked_t := 0.0
var _turn_detour := 0.0              # +-1 while she turns the long way round (the short way swings the tail into the hero)
var _closing_in := false              # stalk: the gaze is due and she slithers in; she gazes once she is in close (towering)
var _skel: Skeleton3D = null
var _tail_shapes: Array[CollisionShape3D] = []
var _tail_live: Array = []            # real model: [[a: Vector3, b: Vector3, r: float, enabled: bool], ...] in her local frame
var _torso_shape: CollisionShape3D = null
var _hair_shape: CollisionShape3D = null
var _tail_off := false                # tail capsules off (tail_swipe: the ring hit is the damage; dead)
var _swipe_speed := 1.0               # tail_swipe clip speed during the coil (wind-up stretched over the ring fill)
var _sweep_speed := 1.0               # tail_swipe clip speed once the ring is full (the flat sweep)
var _sweep_at := 0.625                # tail_swipe clip time where the flat sweep begins
var _tail_count := 0                  # tail swipes this fight (the first two show the on-screen hint)
var _sweep_prev := NAN               # tail_swipe: last measured tip angle (deg); NAN = sweep not started
var _sweep_a0 := 0.0                  # tip angle when the flat sweep started
var _sweep_acc := 0.0                 # degrees the tip has swept since then (signed)
var _clock := 0.0                     # module clock (physics time) for the shield-raise timing
var _shield_up_at := -100.0           # _clock when the hero last raised the shield
var _was_blocking := false
var _fire_clock := 0.0                # _clock at the current gaze's fire
var _blocked_beam := false            # this beam was already blocked by a held (late) shield: no repeated shoves
var _recoil_dir := Vector3.ZERO       # stunned: slide direction of the recoil (away from the hero)
var _sweep_fx: MeshInstance3D = null
var _stun_down_at := 1.25             # stunned: state time when the head lies on the floor
var _last_state: StringName = &""
var _beam_phase := 0                  # gaze clip timing: 0 windup, 1 beam (fire_start..fire_end), 2 recover
var _g_fs := 2.0                      # gaze clip: fire_start, fire_end, length (manifest)
var _g_fe := 3.25
var _g_len := 4.25
var _pre_clip: StringName = &""       # clip and clip time of the last physics frame (death join from the floor)
var _pre_clip_pos := 0.0


func _init() -> void:
	T = Tuning.MEDUSA.duplicate(true)
	boss_id = &"medusa"
	display_name = "Medusa"
	max_hp = int(T["hp"])
	body_radius = 1.3 * S
	body_height = 6.0 * S
	lock_height = 0.78
	hurt_blend = 0.2      # integrate2: the flinch out of the gaze lunge snapped the right hand 0.88 m per frame at 0.08 s
	# test hook: fight the real rigged model before game/assets/characters/medusa/ exists
	# (--medusa-glb=<abs .glb> [--medusa-manifest=<abs clips json>]); BossBase keeps a visual that is already set
	var glb := str(Game.args.get("medusa-glb", ""))
	if glb != "":
		visual = CharacterVisual.create_from_file(boss_id, glb, str(Game.args.get("medusa-manifest", "")))
		add_child(visual)


func _build() -> void:
	# her upright body stands ~0.86 m ahead of the root (rig.json pelvis at Blender y -0.86); the tail lies behind (-Z)
	visual.scale = Vector3.ONE * S                # she towers (x1.5): every bone, socket and live top point follows
	var body := get_node_or_null("Body") as CollisionShape3D
	if body != null and not visual.is_standin:
		body.position.z = BODY_FWD
	var found := visual.find_children("*", "Skeleton3D", true, false)
	if not visual.is_standin and not found.is_empty():
		_skel = found[0] as Skeleton3D
	# hit, ring decal and sweep crescent: T.tail_radius, the inner part of the tail only (the 14 m visual tail sweeps beyond it)
	_add_tail_colliders()
	_neck_socket = visual.add_socket(&"neck_wp", Vector3(0, NECK_Y_MAX, 1.0))
	add_weak_point(&"neck", &"neck_wp", WEAK_R)
	_make_eyes()
	_make_beam()
	_make_fan_edges()
	_make_lean()
	_hair_recolour()
	_update_tail_colliders()
	_update_neck_socket()


## Snake-hair patches (final check item 8, medusa_polish2): the generated albedo atlas lets ~19 % of the vertices
## skinned to the hair_* bones sample brown / yellow / gold texels (hue 12-67 deg) bled in from the skin and armour
## islands. Her own copy of core's toon shader repaints those warm texels snake green ONLY where the vertex is skinned
## to a hair_* bone (BONE_INDICES / BONE_WEIGHTS in vertex()), so the gold armour, the skin and the face keep their
## colours. Same pattern as hydra.gd's recolour (core's shader file untouched and re-read). Real model only.
const HAIR_FN := """
varying float hair_w;
uniform ivec4 hair_binds_a = ivec4(-1);
uniform ivec4 hair_binds_b = ivec4(-1);
void vertex() {
	hair_w = 0.0;
	for (int k = 0; k < 4; k++) {
		ivec4 b = ivec4(int(BONE_INDICES[k]));
		if (any(equal(b, hair_binds_a)) || any(equal(b, hair_binds_b))) {
			hair_w += BONE_WEIGHTS[k];
		}
	}
}
vec3 hair_recolour(vec3 t) {
	float mx = max(t.r, max(t.g, t.b));
	float mn = min(t.r, min(t.g, t.b));
	float sat = (mx - mn) / max(mx, 0.001);
	// warm texel: brown / orange / yellow (hue ~20-75 deg): red over blue, saturated, green between ~0.3x and ~1.2x red.
	// Pure reds (hue < ~15 deg: the forked tongues) keep their colour
	float gr = t.g / max(t.r, 0.001);
	// deep in the hair (hair_w > ~0.6) the red cut drops to g/r ~0.2 (hue ~8 deg): the orange-red patches go too,
	// the deep-red forked tongues (g/r < ~0.17) stay. Bright yellow (value and g/r > ~0.85: the snake eyes) is kept.
	float deep = smoothstep(0.55, 0.65, hair_w);
	float lo = mix(smoothstep(0.26, 0.36, gr), smoothstep(0.17, 0.24, gr), deep);
	float eye = smoothstep(0.62, 0.72, mx) * smoothstep(0.75, 0.85, gr);     // patch yellow is darker (value p90 0.54)
	float warm = smoothstep(0.18, 0.32, sat) * smoothstep(0.0, 0.08, t.r - t.b) * lo * (1.0 - smoothstep(1.05, 1.35, gr)) * (1.0 - eye);
	// the snake green of her texture (median 0.05, 0.33, 0.07; value 0.22-0.45), keeping the texel's own shading
	vec3 green = vec3(0.155, 1.0, 0.21) * clamp(mx * 0.6, 0.18, 0.42);
	return mix(t, green, warm * smoothstep(0.35, 0.6, hair_w));
}
"""
const HAIR_ANCHOR := "c.rgb *= tint.rgb;"
static var _hair_cache := {}          # original Shader instance id -> hair-recoloured Shader


func _hair_recolour() -> void:
	if visual.is_standin or _skel == null:
		return
	for mi in visual.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.skin == null or m.mesh == null:
			continue
		var binds: Array[int] = []
		for i in m.skin.get_bind_count():
			var bn := String(m.skin.get_bind_name(i))
			if bn == "" and m.skin.get_bind_bone(i) >= 0:
				bn = _skel.get_bone_name(m.skin.get_bind_bone(i))
			if bn.begins_with("hair"):
				binds.append(i)
		if binds.is_empty() or binds.size() > 8:
			continue
		while binds.size() < 8:
			binds.append(-1)
		var mats: Array = [m.material_override]
		for i in m.mesh.get_surface_count():
			mats.append(m.get_surface_override_material(i))
		for mat in mats:
			if not (mat is ShaderMaterial) or (mat as ShaderMaterial).shader == null:
				continue
			var sm := mat as ShaderMaterial
			var rs := _hair_shader(sm.shader)
			if rs == sm.shader:
				continue
			var keep := {}
			for u in sm.shader.get_shader_uniform_list():
				keep[u["name"]] = sm.get_shader_parameter(u["name"])
			sm.shader = rs
			for k in keep:
				if keep[k] != null:
					sm.set_shader_parameter(k, keep[k])
			sm.set_shader_parameter("hair_binds_a", Vector4i(binds[0], binds[1], binds[2], binds[3]))
			sm.set_shader_parameter("hair_binds_b", Vector4i(binds[4], binds[5], binds[6], binds[7]))
			Game.event("medusa_hair_recolour", {"binds": binds.filter(func(b: int) -> bool: return b >= 0).size()})


func _hair_shader(src: Shader) -> Shader:
	var key := src.get_instance_id()
	if _hair_cache.has(key):
		return _hair_cache[key]
	var code := src.code
	var out := src
	if code.contains(HAIR_ANCHOR) and code.contains("void fragment()") and not code.contains("void vertex()"):
		code = code.replace("void fragment()", HAIR_FN + "\nvoid fragment()")
		code = code.replace(HAIR_ANCHOR, "c.rgb = hair_recolour(c.rgb);\n\t" + HAIR_ANCHOR)
		out = Shader.new()
		out.code = code
	else:
		push_warning("Medusa: toon shader anchor not found (or it has its own vertex()); snake-hair recolour skipped")
	_hair_cache[key] = out
	return out


## Real model only: the procedural lean that brings the neck into sword reach during the gaze and the stun.
func _make_lean() -> void:
	if visual.is_standin:
		return
	var found := visual.find_children("*", "Skeleton3D", true, false)
	if found.is_empty():
		return
	var sk := found[0] as Skeleton3D
	var m := LeanMod.new()
	m.name = "MedusaLean"
	m.pelvis = sk.find_bone("pelvis")
	m.pivot = sk.find_bone("tail_03")
	m.neck = sk.find_bone("neck")
	m.head = sk.find_bone("head")
	m.target_y = LEAN_NECK_Y
	m.floor_node = self
	m.right_node = visual
	if m.pelvis < 0 or m.pivot < 0 or m.neck < 0:
		push_warning("medusa: rig lacks pelvis/tail_03/neck, no procedural lean")
		m.free()
		return
	sk.add_child(m)
	_lean = m


func _add_tail_colliders() -> void:
	# low capsules along the tail so the hero cannot run through it (sword contact = glance). Stand-in: static, along
	# the resting tail. Real model: they follow the tail bones every physics frame (slither sway, stunned curl).
	if _skel == null:
		for s in TAIL_SEGS:
			var cs := CollisionShape3D.new()
			var cap := CapsuleShape3D.new()
			cap.radius = s[2]
			cap.height = float(s[1]) + float(s[2]) * 2.0
			cs.shape = cap
			cs.rotation.x = PI * 0.5
			cs.position = Vector3(0, float(s[2]) + 0.12, s[0])
			cs.name = "Tail"
			add_child(cs)
		return
	for i in TAIL_CHAIN.size():
		var cs := CollisionShape3D.new()
		var cap := CapsuleShape3D.new()
		cap.radius = TAIL_RADII[i]
		cap.height = 2.0
		cs.shape = cap
		cs.name = "Tail%d" % i
		add_child(cs)
		_tail_shapes.append(cs)
		_tail_live.append([Vector3.ZERO, Vector3.ZERO, float(TAIL_RADII[i]), true])
	_torso_shape = CollisionShape3D.new()
	var tc := CapsuleShape3D.new()
	tc.radius = TORSO_R
	tc.height = 2.0
	_torso_shape.shape = tc
	_torso_shape.name = "Torso"
	_torso_shape.disabled = true
	add_child(_torso_shape)
	_hair_shape = CollisionShape3D.new()
	var hc := CapsuleShape3D.new()
	hc.radius = HAIR_R
	hc.height = HAIR_HALF * 2.0 + HAIR_R * 2.0
	_hair_shape.shape = hc
	_hair_shape.name = "Hair"
	_hair_shape.disabled = true
	add_child(_hair_shape)


## Tail tip (manifest socket tail_tip = tail_14 + offset) straight from the skeleton pose: a BoneAttachment3D only
## catches up on the next frame after a seek.
func _tip_world() -> Vector3:
	var i := _skel.find_bone("tail_14")
	var off := CharacterVisual.offset_transform((visual.manifest.get("socket_offsets", {}) as Dictionary).get("tail_tip", {}), String(visual.manifest.get("offset_space", "blender")))
	return _skel.global_transform * (_skel.get_bone_global_pose(i) * off).origin


## Tail tip angle around her body centre (deg, her frame, 0 = ahead, + = toward her +X).
func _tip_deg() -> float:
	var lt := to_local(_tip_world())
	return rad_to_deg(atan2(lt.x, lt.z - BODY_FWD))


## The hero's angle around her body centre (same frame as _tip_deg).
func _hero_deg() -> float:
	if player == null or not is_instance_valid(player):
		return 0.0
	var lp := to_local(player.global_position)
	return rad_to_deg(atan2(lp.x, lp.z - BODY_FWD))


## Bone head (or socket) in her local frame.
func _bone_local(bone: StringName) -> Vector3:
	var i := _skel.find_bone(bone)
	if i < 0:
		return Vector3.ZERO
	return to_local(_skel.global_transform * _skel.get_bone_global_pose(i).origin)


## Real model: tail capsules between TAIL_CHAIN bone heads (+ the tail tip socket), torso capsule pelvis -> head while
## she lies on the floor. A capsule only (re)enables where it does not start inside the hero (no shove); raised parts
## (tail above 1.6 m) and everything during the swipe / after death are off.
func _update_tail_colliders() -> void:
	if _skel == null:
		return
	var pts: Array[Vector3] = []
	for b in TAIL_CHAIN:
		pts.append(_bone_local(b))
	pts.append(to_local(_tip_world()))
	var hero := to_local(player.global_position) if player != null and is_instance_valid(player) else Vector3(0, 0, 1000)
	for i in _tail_shapes.size():
		var r: float = TAIL_RADII[i]
		var a := pts[i]
		var b := pts[i + 1]
		a.y = maxf(a.y, r + 0.12)                  # never into the floor (her body would be pushed up)
		b.y = maxf(b.y, r + 0.12)
		var on := not _tail_off and (a.y + b.y) * 0.5 < 1.6 * S
		_tail_live[i] = [a, b, r, on]
		_place_capsule(_tail_shapes[i], a, b, r, on, hero)
	if _torso_shape != null:
		var p := _bone_local(&"pelvis")
		var h := to_local(visual.socket(&"head").global_position)
		var low := (p.y + h.y) * 0.5 < 1.5 * S and state != &"dead"
		p.y = maxf(p.y, TORSO_R + 0.12)
		h.y = maxf(h.y, TORSO_R + 0.12)
		_place_capsule(_torso_shape, p, h, TORSO_R, low, hero)
		if _hair_shape != null:
			# the snakes spread sideways around the lowered head: a capsule across it (her right axis), a little ahead
			var hd := h + Vector3(0, 0, HAIR_AHEAD)
			hd.y = maxf(hd.y, HAIR_R + 0.12)
			var hair_low := low and h.y < 1.5 * S
			_place_capsule(_hair_shape, hd - Vector3(HAIR_HALF, 0, 0), hd + Vector3(HAIR_HALF, 0, 0), HAIR_R, hair_low, hero)


func _place_capsule(cs: CollisionShape3D, a: Vector3, b: Vector3, r: float, on: bool, hero: Vector3) -> void:
	var d := b - a
	var length := d.length()
	if length < 0.05:
		cs.disabled = true
		return
	var y := d / length
	var x := y.cross(Vector3.FORWARD if absf(y.dot(Vector3.FORWARD)) < 0.9 else Vector3.RIGHT).normalized()
	var z := x.cross(y)
	cs.transform = Transform3D(Basis(x, y, z), (a + b) * 0.5)
	(cs.shape as CapsuleShape3D).height = length + r * 2.0
	if not on:
		cs.disabled = true
		return
	if cs.disabled:
		# hero capsule (radius, 0..1.9 m) vs this segment: only switch on when they are apart
		var t := clampf((hero - a).dot(d) / (length * length), 0.0, 1.0)
		var q := a + d * t
		var flat := Vector2(hero.x - q.x, hero.z - q.z).length()
		if flat > r + Tuning.PLAYER_RADIUS + 0.05 or q.y - r > 1.9:
			cs.disabled = false


func _make_eyes() -> void:
	_eyes = Node3D.new()
	_eyes.name = "GazeEyes"
	visual.socket(&"eyes").add_child(_eyes)
	if visual.is_standin:
		_eyes.position = Vector3.ZERO
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(0.8, 1.0, 0.55)
	mat.emission_enabled = true
	mat.emission = GAZE_COLOR
	mat.emission_energy_multiplier = 4.0
	for side in [-1.0, 1.0]:
		var e := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		e.mesh = sm
		e.material_override = mat
		e.position = Vector3(side * 0.12, 0.0, 0.02)
		e.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_eyes.add_child(e)
	# a soft additive halo instead of an OmniLight3D (omni lights draw pale cluster rectangles with the toon shader)
	_eye_halo = MeshInstance3D.new()
	var hq := QuadMesh.new()
	hq.size = Vector2(1.1, 1.1)
	_eye_halo.mesh = hq
	var hm := StandardMaterial3D.new()
	hm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	hm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	hm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	hm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	hm.albedo_texture = Fx.soft_dot()
	hm.albedo_color = Color(GAZE_COLOR.r, GAZE_COLOR.g, GAZE_COLOR.b, 0.0)
	_eye_halo.material_override = hm
	_eye_halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_eyes.add_child(_eye_halo)
	_eyes.visible = false


func _make_beam() -> void:
	_beam_mesh = ImmediateMesh.new()
	_beam = MeshInstance3D.new()
	_beam.name = "GazeBeam"
	_beam.mesh = _beam_mesh
	_beam.top_level = true
	_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.render_priority = VFX_PRIORITY
	m.vertex_color_use_as_albedo = true
	m.no_depth_test = false
	# anything of the beam that comes near the chase camera fades out (the core ray ends at the hero, >= 3.7 m away)
	m.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_ALPHA
	m.distance_fade_min_distance = 1.0
	m.distance_fade_max_distance = 3.0
	_beam.material_override = m
	add_child(_beam)
	_beam.global_transform = Transform3D.IDENTITY
	_beam.visible = false


## Two solid lines along the gaze fan's edges (drawn above the decal): they stay visible beside the hero, whose body
## hides the middle of the fan from the chase camera. Green during the windup, ink-dark and wider after the lock.
func _make_fan_edges() -> void:
	_fan_mesh = ImmediateMesh.new()
	_fan_edges = MeshInstance3D.new()
	_fan_edges.name = "GazeFanEdges"
	_fan_edges.mesh = _fan_mesh
	_fan_edges.top_level = true
	_fan_edges.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.render_priority = VFX_PRIORITY
	m.vertex_color_use_as_albedo = true
	_fan_edges.material_override = m
	add_child(_fan_edges)
	_fan_edges.global_transform = Transform3D.IDENTITY
	_fan_edges.visible = false


func _draw_fan_edges() -> void:
	_fan_mesh.clear_surfaces()
	var o := _gaze_origin() + Vector3.UP * 0.06
	var half := deg_to_rad(float(T["gaze_fan_deg"]) * 0.5)
	var length := float(T["gaze_length"])
	var col := Color(GAZE_LOCK_EDGE.r, GAZE_LOCK_EDGE.g, GAZE_LOCK_EDGE.b, 1.0) if _gaze_locked else Color(GAZE_EDGE.r, GAZE_EDGE.g, GAZE_EDGE.b, 0.8)
	var w := FAN_LINE_WIDTH * ((1.4 if _gaze_locked else 1.0) + 1.2 * _fan_pulse)
	_fan_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for s: float in [-1.0, 1.0]:
		var dir := _gaze_dir.rotated(Vector3.UP, half * s)
		var out := dir.cross(Vector3.UP) * -s           # away from the fan centre
		var a := o + dir * 1.0
		var b := o + dir * length
		var wa := out * w
		var wb := out * w * 2.2                           # keep the far end readable at a grazing camera angle
		for v in [a, a + wa, b + wb, a, b + wb, b]:
			_fan_mesh.surface_set_color(col)
			_fan_mesh.surface_add_vertex(v)
	_fan_mesh.surface_end()


## Recolours a core Telegraph decal (fill + edge) through core's Telegraph.set_colors.
func _tint_decal(t: Telegraph, fill: Color, edge: Color) -> void:
	if is_instance_valid(t):
		t.set_colors(fill, edge)


# ------------------------------------------------------------------ state machine
func _first_state() -> StringName:
	if str(Game.args.get("medusa-probe", "")) == "tailturn":
		return &"probe_turn"
	return &"stalk"


func _enter_state(s: StringName) -> void:
	_impact_done = false
	match s:
		&"stalk":
			_moving = false
			_still_t = 0.0
			_stalk_v = Vector2(velocity.x, velocity.z).length()
			# a one-shot that still has its recovery to play (the tail swipe ends ~0.7 s before its clip) plays it out;
			# _update_loco then cross-fades to idle / slither (no cut back to the idle pose mid-motion)
			_exit_blend = float(T["gaze_exit_blend"]) if _last_state == &"gaze" else float(T["loco_blend"])
			_finishing = not visual.is_standin and visual.current_clip in [&"tail_swipe", &"gaze", &"rise"] \
				and visual.clip_length(visual.current_clip, 1.0) - visual.clip_position() > 0.1
			if not _finishing:
				visual.play(&"idle", _exit_blend)
			var rng: Array = T["gaze_interval_enraged"] if enraged() else T["gaze_interval"]
			_gaze_wait = Game.rng.randf_range(float(rng[0]), float(rng[1]))
			_gaze_index = 0
			_closing_in = false
			if Game.rng.randf() < 0.35:
				Sfx.play("medusa_hiss", global_position, -4.0)
		&"gaze":
			_stalk_v = Vector2(velocity.x, velocity.z).length()     # she brakes over the first ~0.35 s (_coast), no dead stop
			_fired = false
			_beam_done = false
			_beam_resolved = false
			_gaze_locked = false
			_gaze_windup = float(T["gaze_windup"]) * (float(T["enraged_windup_scale"]) if enraged() else 1.0)
			_gaze_dir = _dir_to_player()
			_beam_phase = 0
			# clip 0 .. fire_start fills the windup exactly; _tick_gaze re-times fire_start .. fire_end to the beam
			var fire_at := visual.event_time(&"gaze", &"fire_start", visual.clip_length(&"gaze", 2.4) * 0.5)
			_g_len = visual.clip_length(&"gaze", 2.4)
			_g_fs = fire_at
			_g_fe = visual.event_time(&"gaze", &"fire_end", minf(fire_at + float(T["gaze_beam_time"]), _g_len))
			visual.play(&"gaze", float(T["action_blend"]), maxf(fire_at, 0.05) / _gaze_windup)
			_decal = arena.telegraph_cone(_gaze_origin(), _gaze_dir, float(T["gaze_fan_deg"]) * 0.5, float(T["gaze_length"]), _gaze_windup, GAZE_COLOR)
			_tint_decal(_decal, GAZE_COLOR, GAZE_EDGE)
			_hit_at = -1.0
			_fan_pulse = 0.0
			_fan_edges.visible = true
			_draw_fan_edges()
			Sfx.play("medusa_gaze_warn", global_position)
			_eyes.visible = true
			Game.event("gaze_windup", {"index": _gaze_index, "windup": snappedf(_gaze_windup, 0.01), "dist": snappedf(player_distance(), 0.1), "close_t": snappedf(_close_t, 0.01)})
		&"stunned":
			halt()
			_neck_close_in = -1.0
			_stun_looping = false
			# recoil + collapse (head on the floor at the clip's end), then SPEC's 3.0 s with the head down (stunned loop)
			visual.play(&"stun_start", float(T["action_blend"]), STUN_START_SPEED)
			_stun_down_at = visual.clip_length(&"stun_start", 0.6) / STUN_START_SPEED
			hurt_clip = &""            # the standing flinch would lift her head off the floor: flash + sound only
			# thrown back by her own reflected glare, so the 7 m long collapse lays her head in front of the hero
			_recoil_dir = global_position - player.global_position if player != null else -forward()
			_recoil_dir.y = 0.0
			_recoil_dir = _recoil_dir.normalized() if _recoil_dir.length() > 0.1 else -forward()
			Sfx.play("medusa_stun", global_position)
			Game.shake(0.3)
			expose(&"neck", int(T["stun_hits"]))
		&"rise":
			halt()
			visual.play(&"rise", float(T["action_blend"]), visual.clip_length(&"rise", 0.8) / float(T["rise_time"]))
			_close_t = 0.0
		&"recoil":
			halt()
			_recoil_len = visual.clip_length(&"hurt", 0.5)
		&"tail_swipe":
			_stalk_v = Vector2(velocity.x, velocity.z).length()     # she brakes over T.tail_brake_time (_coast), no dead stop
			# the ring fill (= coil) is the time to get out, the same when enraged; enraged, the sweep itself is faster
			_coil = float(T["tail_coil"])
			_sweep_speed = SWEEP_CLIP_SPEED / (float(T["enraged_windup_scale"]) if enraged() else 1.0)
			# the ring fills exactly when the tail's flat sweep BEGINS (clip SWEEP_SPAN.x), so no hit can land before it
			# is full (QA: timing it to the impact event let heroes behind her right side be struck 0.16 s early)
			_sweep_at = SWEEP_SPAN.x if _skel != null else visual.event_time(&"tail_swipe", &"impact", visual.clip_length(&"tail_swipe", 1.4) * 0.5)
			_swipe_speed = maxf(_sweep_at, 0.05) / _coil      # the coil (wind-up) part of the clip fills the ring time
			_sweep_prev = NAN
			_sweep_acc = 0.0
			visual.play(&"tail_swipe", float(T["action_blend"]), _swipe_speed)
			# ring = the part of the tail that hits (T.tail_radius), not the 14 m visual tip
			_decal = arena.telegraph_ring(_body_center(), 1.4 * S, float(T["tail_radius"]), _coil)
			_tail_off = true
			Sfx.play("medusa_tail_swipe_warn", global_position)
			_tail_count += 1
			if _tail_count <= 2 and arena != null and arena.hud != null and arena.hud.has_method("show_message"):
				arena.hud.show_message("Tail sweep: {roll} roll out of the ring", _coil + 0.4)
			Game.event("tail_coil", {"ring_r": snappedf(float(T["tail_radius"]), 0.01), "coil": snappedf(_coil, 0.01), "clip_speed": snappedf(_swipe_speed, 0.01),
				"sweep_speed": snappedf(_sweep_speed, 0.01), "dist": snappedf(_body_center().distance_to(Vector3(player.global_position.x, _body_center().y, player.global_position.z)), 0.01)})
		&"idle":
			halt()
			visual.play(&"idle", 0.2)
		&"probe_turn":
			# harness probe (--medusa-probe=tailturn --bot=idle): hero 1 m beside the mid-tail, she turns 180 deg in 1 s
			halt()
			player.global_position = to_global(Vector3(1.0 + TAIL_RADII[1] + Tuning.PLAYER_RADIUS, 0.0, -4.3 * S))
			Game.event("probe_turn_start", {"hero_dist": snappedf(player_distance(), 0.01), "gap": snappedf(_tail_gap(), 0.01)})
		&"dead":
			_end_beam()
			_tail_off = true
			_free_sweep_fx()
			if _last_state in [&"stunned", &"rise"] and not visual.is_standin:
				# she dies with her head on the floor: the death clip starts upright, so join it where she already lies
				# on the floor (clip DEATH_FROM_FLOOR) with a long blend: she slumps onto her side instead of getting up first.
				# The fade starts from the pose she really had (clip + time of the last frame): restarting stunned at 0
				# popped the tail ~2 m in one frame (integrate2)
				var src := _pre_clip if _pre_clip in [&"stunned", &"stun_start", &"rise"] else &"stunned"
				visual.play(src, 0.0, 1.0, _pre_clip_pos if src == _pre_clip else 0.0)
				visual.play(&"death", DEATH_JOIN_BLEND)
				visual.seek(DEATH_FROM_FLOOR, false)


func _exit_state(s: StringName) -> void:
	_last_state = s
	match s:
		&"gaze":
			_end_beam()
			if not _fired and is_instance_valid(_decal):
				_decal.cancel()
			_decal = null
		&"tail_swipe":
			if not _impact_done and is_instance_valid(_decal):
				_decal.cancel()
			_decal = null
			_tail_off = false
			_free_sweep_fx()
		&"stunned":
			close_weak(&"neck")
			hurt_clip = &"hurt"


func _tick_state(delta: float) -> void:
	_tick_neck_window(delta)
	match state:
		&"stalk":
			_tick_stalk(delta)
		&"gaze":
			_tick_gaze(delta)
		&"stunned":
			if state_time < STUN_RECOIL_TIME:
				# ease-out slide: v = 2D/T * (1 - t/T) covers STUN_RECOIL metres (the boundary and tail colliders may cut it)
				var v := 2.0 * STUN_RECOIL / STUN_RECOIL_TIME * (1.0 - state_time / STUN_RECOIL_TIME)
				var nxt := _clamp_to_area(global_position + _recoil_dir * v * delta, float(T["stalk_area"]) + STUN_RECOIL)
				velocity.x = (nxt.x - global_position.x) / maxf(delta, 0.0001)
				velocity.z = (nxt.z - global_position.z) / maxf(delta, 0.0001)
			else:
				halt()
			if Game.args.has("medusa-trace") and int(state_time * 4.0) != int((state_time - delta) * 4.0):
				Game.event("trace_stun", {"hero_local": to_local(player.global_position).snapped(Vector3.ONE * 0.01),
					"wp_local": to_local(_neck_socket.global_position).snapped(Vector3.ONE * 0.01), "me": global_position.snapped(Vector3.ONE * 0.1),
					"pst": player.state})
			if not _stun_looping:
				_sync_clip(&"stun_start", state_time * STUN_START_SPEED)
			if not _stun_looping and state_time >= _stun_down_at:
				_stun_looping = true
				visual.play(&"stunned", 0.15)
				Game.event("stun_down", _neck_info({}))
			if state_time >= _stun_down_at + float(T["stun_time"]):
				set_state(&"rise")
		&"rise":
			_sync_clip(&"rise", state_time * visual.clip_length(&"rise", 0.8) / float(T["rise_time"]))
			if state_time >= float(T["rise_time"]):
				set_state(&"stalk")
		&"recoil":
			if state_time >= _recoil_len:
				set_state(&"stalk")
		&"probe_turn":
			if state_time > 0.3 and state_time <= 1.3:
				face_towards(global_position - forward().rotated(Vector3.UP, 0.3) * 5.0, 180.0, delta)
			elif state_time > 2.0:
				Game.event("probe_turn_end", {"hero_dist": snappedf(player_distance(), 0.01), "turned_deg": snappedf(rad_to_deg(rotation.y), 0.1), "gap": snappedf(_tail_gap(), 0.01), "blocked_s": snappedf(_turn_blocked_t, 0.01)})
				set_state(&"stalk")
		&"tail_swipe":
			_tick_tail_swipe()


func _physics_process(delta: float) -> void:
	# when did the hero raise his shield? (a reflect needs a timed raise, see REFLECT_RAISE_WINDOW)
	_clock += delta
	# Player.block_since (hero clock when the shield went up, -1 while lowered), moved onto this module clock
	if player != null and is_instance_valid(player) and player.block_since >= 0.0:
		_shield_up_at = _clock - (player.clock() - player.block_since)
	super(delta)
	if hp > 0 and not visual.is_standin:
		_pre_clip = visual.current_clip
		_pre_clip_pos = visual.clip_position()
	_update_loco(delta)
	_update_tail_colliders()


## Natural locomotion (owner 2026-11-23: no gliding, no statue turns). Measures what her body really did this physics
## step (ground speed after move_and_slide, turn rate) and, in stalk, plays the slither clip whenever she moves OR
## turns, at a rate matched to it (reference = manifest move_speed, else slither_speed); idle only when she has been
## really still for slither_stop_hold. A one-shot finishing its recovery hands over to slither / idle with loco_blend.
func _update_loco(delta: float) -> void:
	var pos := global_position
	if _loco_prev_pos == Vector3.INF or delta <= 0.0:
		_loco_prev_pos = pos
		_loco_prev_yaw = rotation.y
		return
	var ground := Vector2(pos.x - _loco_prev_pos.x, pos.z - _loco_prev_pos.z).length() / delta
	var turn := absf(wrapf(rotation.y - _loco_prev_yaw, -PI, PI)) / delta
	var fwd_v := Vector3(pos.x - _loco_prev_pos.x, 0.0, pos.z - _loco_prev_pos.z).dot(forward()) / delta
	_loco_prev_pos = pos
	_loco_prev_yaw = rotation.y
	var eff := maxf(ground, turn * float(T["slither_turn_radius"]))
	_loco_speed = lerpf(_loco_speed, eff, 1.0 - exp(-12.0 * delta))
	_loco_fwd = lerpf(_loco_fwd, fwd_v, 1.0 - exp(-12.0 * delta))
	if not (state == &"stalk" or state == &"probe_turn") or hp <= 0 or visual.is_standin:
		return
	var blend := float(T["loco_blend"])
	# integrate2: idle <-> slither fades in real seconds (the tail uncurls 4-5 m between the two). The boss AnimationPlayer
	# fades on the clip clock (speed_scale = |rate|), so the blend argument is real seconds x the new clip's rate.
	var start_blend := float(T["loco_blend_start"]) * absf(_slither_rate())
	var stop_blend := float(T["loco_blend_stop"])
	var cur := visual.current_clip
	if _finishing:
		blend = _exit_blend
		if cur not in [&"tail_swipe", &"gaze", &"rise"]:
			_finishing = false
		elif _loco_speed >= float(T["slither_start_speed"]) or visual.clip_position() >= visual.clip_length(cur, 1.0) - blend * absf(visual.get_speed()):
			_finishing = false
			_moving = _loco_speed >= float(T["slither_start_speed"])
			visual.play(&"slither" if _moving else &"idle", maxf(blend, start_blend) if _moving else blend, _slither_rate() if _moving else 1.0)
		return
	if cur != &"slither" and cur != &"idle":
		return                       # a flinch (hurt) plays over it; BossBase resumes the clip after it
	if not _moving:
		if _loco_speed >= float(T["slither_start_speed"]):
			_moving = true
			_still_t = 0.0
			visual.play(&"slither", start_blend, _slither_rate())
	elif _loco_speed < float(T["slither_stop_speed"]):
		_still_t += delta
		if _still_t >= float(T["slither_stop_hold"]):
			_moving = false
			visual.play(&"idle", stop_blend)
	else:
		_still_t = 0.0
	if _moving and visual.current_clip == &"slither":
		visual.set_speed(_slither_rate())


## Slither playback rate for the current effective speed (the clip's own reference speed, never a hard-coded stride).
## Signed: backing off (signed speed along her facing < T.slither_back_play) plays the loop backwards, so the body
## wave travels the way she moves instead of a forward slither gliding back.
func _slither_rate() -> float:
	var ref := visual.move_speed(&"slither")
	if ref <= 0.01:
		ref = float(T["slither_speed"])
	var r := clampf(_loco_speed / ref, Tuning.ANIM_SPEED_MIN, Tuning.ANIM_SPEED_MAX)
	return -r if _loco_fwd < float(T["slither_back_play"]) else r


## Gaze start: she brakes from her slither speed instead of stopping dead (heading kept).
func _coast(delta: float) -> void:
	_stalk_v = move_toward(_stalk_v, 0.0, float(T["slither_accel"]) * 1.5 * delta)
	var h := Vector2(velocity.x, velocity.z)
	if _stalk_v <= 0.01 or h.length() < 0.01:
		halt()
		_stalk_v = 0.0
		return
	h = h.normalized() * _stalk_v
	velocity.x = h.x
	velocity.z = h.y


func _process(delta: float) -> void:
	_update_lean(delta)
	if _skel != null:
		_update_neck_socket()
		if state == &"dead" and int((state_time - delta) * 2.0) != int(state_time * 2.0) and state_time < 3.0:
			Game.event("death_pose", {"t": snappedf(state_time, 0.1), "pelvis_y": snappedf(_bone_local(&"pelvis").y, 0.01), "head_y": snappedf(to_local(visual.socket(&"head").global_position).y, 0.01)})


## The flat 360 degree sweep. The ring fills when the sweep begins (clip SWEEP_SPAN.x). Real model: the hero is struck
## when the MEASURED tail tip (unwrapped angle swept since the sweep began) reaches HIS angle, so a hero straight
## behind her is struck when the tip comes round at the end, never before the ring is full; the swoosh rides the tip.
## Stand-in: one ring hit when the ring is full, the old swoosh.
func _tick_tail_swipe() -> void:
	var c := _body_center()
	if state_time < float(T["tail_brake_time"]) and _stalk_v > 0.0:
		_coast(get_physics_process_delta_time())     # brakes from her stalk speed (<= 0.6 m at 3.2 m/s); the ring rides along
		if is_instance_valid(_decal) and not _impact_done:
			_decal.global_position = Vector3(c.x, _decal.global_position.y, c.z)
	else:
		halt()
		_stalk_v = 0.0
	# clip time: the wind-up (clip 0 .. sweep start) fills the ring time, then the flat sweep at its own speed
	var ct := state_time * _swipe_speed
	if state_time >= _coil:
		ct = _sweep_at + (state_time - _coil) * _sweep_speed
		if not visual.is_standin and absf(visual.get_speed() - _sweep_speed) > 0.001:
			visual.set_speed(_sweep_speed)
	_sync_clip(&"tail_swipe", ct)
	var real := _skel != null
	if real and ct >= SWEEP_SPAN.x and ct <= SWEEP_SPAN.y + 0.05:
		_follow_sweep_fx(c)
	elif _sweep_fx != null and ct > SWEEP_SPAN.y + 0.05:
		_free_sweep_fx()
	if not _impact_done:
		var hero_deg := _hero_deg()
		var due := state_time >= _coil
		if real:
			due = false
			if ct >= SWEEP_SPAN.x:
				var tip_deg := _tip_deg()
				if is_nan(_sweep_prev):
					_sweep_a0 = tip_deg
					_sweep_acc = 0.0
				else:
					_sweep_acc += wrapf(tip_deg - _sweep_prev, -180.0, 180.0)
				_sweep_prev = tip_deg
				var rel := fposmod(hero_deg - _sweep_a0, 360.0) if _sweep_acc >= 0.0 else fposmod(_sweep_a0 - hero_deg, 360.0)
				due = absf(_sweep_acc) >= rel or ct > SWEEP_SPAN.y + 0.08
		if due and state_time >= _coil - 0.0001:          # safety: never before the ring is full
			_impact_done = true
			var r := hit_circle(c, float(T["tail_radius"]), int(T["tail_dmg"]), {"blockable": false, "knockback": float(T["tail_knockback"])})
			var tip := _tip_world() if real else c
			Sfx.play("medusa_tail_swipe", tip if real else c)
			Fx.dust(arena, Vector3(tip.x, c.y, tip.z) if real else c, float(T["tail_radius"]) * (0.35 if real else 0.8), Color(0.9, 0.88, 0.84, 0.8))
			if not real:
				_swoosh(c)
			Game.shake(0.35)
			var tip_flat := Vector2(tip.x - c.x, tip.z - c.z)
			Game.event("attack_resolved", {"attack": "tail_swipe", "result": r, "hero_deg": snappedf(hero_deg, 1.0),
				"hero_r": snappedf(Vector2(player.global_position.x - c.x, player.global_position.z - c.z).length(), 0.01),
				"clip_t": snappedf(ct, 0.01), "after_ring": snappedf(state_time - _coil, 0.001), "tip_r": snappedf(tip_flat.length(), 0.01),
				"tip_deg": snappedf(_tip_deg(), 1.0) if real else 0.0, "swept": snappedf(_sweep_acc, 1.0)})
	if state_time >= _coil + float(T["tail_recover"]):
		_close_t = 0.0
		set_state(&"stalk")


func _tick_stalk(delta: float) -> void:
	var turn_deg := float(T["turn_deg"])
	if _last_state == &"gaze" and state_time < float(T["post_gaze_turn_time"]):
		turn_deg = minf(turn_deg, float(T["post_gaze_turn_deg"]))     # she settles out of the gaze before turning hard
	face_towards(player.global_position, turn_deg, delta)
	var d := player_distance()
	if Game.args.has("medusa-trace") and int(state_time * 4.0) != int((state_time - delta) * 4.0):
		Game.event("trace", {"d": snappedf(d, 0.1), "close_t": snappedf(_close_t, 0.01), "me": global_position.snapped(Vector3.ONE * 0.1), "p": player.global_position.snapped(Vector3.ONE * 0.1), "pst": player.state})
	var away := global_position - player.global_position
	away.y = 0.0
	away = away.normalized() if away.length() > 0.1 else forward() * -1.0
	var target := global_position
	var gaze_due := state_time >= _gaze_wait
	var gaze_gate := float(T["gaze_max_dist"])
	var close_to := maxf(gaze_gate - GAZE_APPROACH, float(T["keep_min"]))     # ~6.3 m: she towers over the hero there
	# out of the band, or the gaze is due with the hero beyond gaze range: she commits to closing in to close_to
	# (no stop at the band edge, no gaze the moment she crosses the 8 m gate), so the windup is seen up close
	if d > float(T["keep_max"]) or (gaze_due and d > gaze_gate):
		_closing_in = true
	elif _closing_in and not gaze_due and d <= close_to + 0.4:
		_closing_in = false
	if _closing_in:
		gaze_gate = close_to + 0.4
	var backing := false
	if d < float(T["keep_min"]):
		# she backs off on an arc (target turned retreat_arc_deg to one side, the side with more room, kept for the
		# whole retreat), never straight back like a statue on rails
		backing = true
		var arc := deg_to_rad(float(T["retreat_arc_deg"]))
		# the arc turns HER path (back and to one side), not a point around him: a target turned around the hero made
		# her circle him tangentially at full speed (person probe, 2026-11-23 polish 3)
		var go := (float(T["keep_min"]) + 1.5 - d) / cos(arc) + 0.6
		if _retreat_side == 0.0:
			var ta := _clamp_to_area(global_position + away.rotated(Vector3.UP, arc) * go)
			var tb := _clamp_to_area(global_position + away.rotated(Vector3.UP, -arc) * go)
			_retreat_side = 1.0 if ta.distance_to(player.global_position) >= tb.distance_to(player.global_position) else -1.0
		target = global_position + away.rotated(Vector3.UP, arc * _retreat_side) * go
	elif _closing_in:
		target = player.global_position + away * (close_to - 0.4)     # she stops 0.6 m short of a target: ~6.5 m
	if not backing:
		_retreat_side = 0.0
	target = _clamp_to_area(target)
	var move := target.distance_to(global_position) > 0.6
	if _closing_in and not move:
		gaze_gate = float(T["gaze_max_dist"])     # held back by the stalk area (hero at the rim): gaze from where she is
	if move:
		# gathers speed and brakes into the target (v = sqrt(2 a d)), never jumps to / from full speed
		var a := float(T["slither_accel"])
		var want := minf(float(T["slither_speed"]), sqrt(2.0 * a * maxf(target.distance_to(global_position) - 0.6, 0.0)) + 0.3)
		var to_t := target - global_position
		to_t.y = 0.0
		if backing or (to_t.length() > 0.01 and to_t.normalized().dot(forward()) < -0.3):
			want = minf(want, float(T["slither_back_speed"]))     # moving against her facing: slow (the clip plays backwards)
		_stalk_v = move_toward(_stalk_v, want, a * delta)
		walk_towards(target, _stalk_v)
	else:
		_stalk_v = 0.0
		halt()
	# tail swipe: the hero lingers close
	if d < float(T["tail_trigger_dist"]):
		_close_t += delta
	else:
		_close_t = 0.0
	if _close_t >= float(T["tail_trigger_time"]):
		set_state(&"tail_swipe")
		return
	if not gaze_due:
		return
	if d <= gaze_gate:
		var ang := angle_to_pos(player.global_position)
		if ang < float(T["gaze_max_angle"]) or (state_time >= _gaze_wait + 2.5 and ang < float(T["gaze_timeout_angle"])):
			set_state(&"gaze")
	elif state_time >= _gaze_wait + float(T["gaze_chase_limit"]) and d < float(T["gaze_length"]) - 1.0:
		set_state(&"gaze")             # a hero who keeps running away still gets gazed (from long range)


func _tick_gaze(delta: float) -> void:
	_coast(delta)
	var t := state_time
	var beam_t := float(T["gaze_beam_time"])
	var want := t * _g_fs / _gaze_windup
	if t >= _gaze_windup + beam_t:
		want = _g_fe + (t - _gaze_windup - beam_t) * (_g_len - _g_fe) / float(T["gaze_recover"])
	elif t >= _gaze_windup:
		want = _g_fs + (t - _gaze_windup) * (_g_fe - _g_fs) / beam_t
	_sync_clip(&"gaze", minf(want, _g_len))     # the clip holds its last frame while the lunge eases out (below)
	if not _gaze_locked:
		_gaze_dir = _dir_to_player()
		face_towards(player.global_position, float(T["turn_deg"]) * 2.0, delta)
		if is_instance_valid(_decal):
			_decal.global_position = _gaze_origin()
			_decal.aim(_gaze_dir)
		if t >= float(T["gaze_lock_at"]):
			_gaze_locked = true
			_on_gaze_lock()
	else:
		face_towards(global_position + _gaze_dir, float(T["turn_deg"]) * 2.0, delta)
	_fan_pulse = maxf(_fan_pulse - delta / 0.18, 0.0)
	if not _beam_done:
		_draw_fan_edges()
	var glow := clampf(t / _gaze_windup, 0.0, 1.0)
	var pulse := _fan_pulse * 0.9
	_eyes.scale = Vector3.ONE * (0.6 + glow * 1.2 + pulse)
	(_eye_halo.material_override as StandardMaterial3D).albedo_color.a = clampf(glow * 0.9 + pulse, 0.0, 1.0)
	if not _fired and t >= _gaze_windup:
		_fired = true
		_beam_tick_t = 0.0
		_beam_phase = 1
		_fire_clock = _clock
		_blocked_beam = false
		# the clip's fire_start .. fire_end span is stretched onto the SPEC beam time
		var fs := visual.event_time(&"gaze", &"fire_start", visual.clip_length(&"gaze", 2.4) * 0.5)
		var fe := visual.event_time(&"gaze", &"fire_end", fs + beam_t)
		visual.set_speed(maxf(fe - fs, 0.05) / beam_t)
		expose(&"neck", int(T["gaze_neck_hits"]))
		_neck_close_in = beam_t + float(T["neck_open_after_fire"])
		Sfx.play("medusa_gaze", global_position)
		Game.shake(0.15)
		Game.event("gaze_fire", _neck_info({"index": _gaze_index, "clip_t": _clip_pos(), "fire_start": fs,
			"eyes_y": snappedf(visual.socket(&"eyes").global_position.y - global_position.y, 0.01)}))
		_beam.visible = true
	if _fired and not _beam_done:
		_draw_beam(clampf((t - _gaze_windup) / beam_t, 0.0, 1.0))
		_beam_tick_t -= delta
		if _beam_tick_t <= 0.0 and not _beam_resolved:
			_beam_tick_t = BEAM_TICK
			# timed raise (QA: a shield held up all fight made her trivial): only a shield raised within
			# REFLECT_RAISE_WINDOW before the fire (or during the beam) reflects; one already up just blocks (0 damage,
			# the usual block shove once, no stun). Lowering it mid-beam lets the beam through again.
			var raised_for := _clock - _shield_up_at
			var timed := _shield_up_at >= _fire_clock - REFLECT_RAISE_WINDOW
			var r := &""
			if not (_blocked_beam and player.is_blocking_towards(_gaze_origin())):
				r = hit_cone(_gaze_origin(), _gaze_dir, float(T["gaze_fan_deg"]) * 0.5, float(T["gaze_length"]), int(T["gaze_dmg"]),
					{"blockable": not timed, "reflect": timed, "petrify": float(T["gaze_petrify"]), "knockback": 0.0})
			if r == &"reflected":
				Game.event("attack_resolved", {"attack": "gaze", "result": r, "raised_before_fire": snappedf(_fire_clock - _shield_up_at, 0.01)})
				_on_reflected()
				return
			if r == &"blocked" and not _blocked_beam:
				_blocked_beam = true
				Game.event("attack_resolved", {"attack": "gaze", "result": r, "held_s": snappedf(raised_for, 0.01)})
			if r == &"hit":
				_beam_resolved = true          # petrified (invulnerable) for longer than the beam: one hit per beam
				_hit_at = t
				_petrify_flash()
				Game.event("attack_resolved", {"attack": "gaze", "result": r})
		if t >= _gaze_windup + beam_t:
			_beam_done = true
			_beam_phase = 2
			var len_g := visual.clip_length(&"gaze", 2.4)
			var fe2 := visual.event_time(&"gaze", &"fire_end", len_g * 0.75)
			visual.set_speed(maxf(len_g - fe2, 0.05) / float(T["gaze_recover"]))
			_end_beam()
			Game.event("gaze_beam_end", {"index": _gaze_index, "clip_t": _clip_pos(), "fire_end": fe2})
			if not _beam_resolved and not _blocked_beam:
				Game.event("attack_resolved", {"attack": "gaze", "result": "miss"})
	if _beam_done:
		var after := t - _gaze_windup - beam_t
		if enraged() and _gaze_index == 0:
			var due := float(T["enraged_second_gaze_delay"])
			if _hit_at >= 0.0:
				# the first beam petrified him: give him control back before the follow-up starts tracking
				due = maxf(due, _hit_at + float(T["gaze_petrify"]) + float(T["gaze_hit_followup_gap"]) - _gaze_windup - beam_t)
			if after >= due:
				_gaze_index = 1             # the follow-up (enter keeps the volley index; stalk resets it)
				set_state(&"gaze")
		elif after >= float(T["gaze_recover"]) and ((_neck_close_in < 0.0 and (_lean == null or _lean.weight < 0.1)) \
				or after >= float(T["gaze_recover"]) + 3.0):
			# she leaves the gaze only once the neck window is shut and the lunge has eased out on the gaze clip, so the
			# hand-over to idle / slither (T.gaze_exit_blend) starts from an upright pose (review: a 0.2 s snap upright)
			set_state(&"stalk")


## The gaze neck window (fire start .. beam end + neck_open_after_fire) runs across state changes.
func _tick_neck_window(delta: float) -> void:
	if _neck_close_in >= 0.0:
		_neck_close_in -= delta
		if _neck_close_in < 0.0 and state != &"stunned":
			close_weak(&"neck")
	_update_neck_socket()


## The moment sidestepping starts to work: the fan turns deep green with ink edges, the edge lines widen and pulse,
## the eyes flare and she hisses.
func _on_gaze_lock() -> void:
	_tint_decal(_decal, GAZE_LOCK_COLOR, GAZE_LOCK_EDGE)
	_fan_pulse = 1.0
	_draw_fan_edges()
	var eyes := visual.socket(&"eyes").global_position
	_burst(eyes, 1.4, Color(0.6, 1.0, 0.5, 0.85))
	Sfx.play("medusa_hiss", eyes, 3.0, 1.15)
	Game.event("gaze_lock", {"index": _gaze_index, "cue": "tint+lines+eyes+hiss"})


## Procedural lean weight (real model): ramps in over the gaze windup and holds while the neck is exposed; drops in
## over the stun_start; eases out over the rise / after the window.
func _update_lean(delta: float) -> void:
	if _lean == null:
		return
	# windup: none (the gaze clip stands tall, eyes glowing, like key_medusa.png); fire: she lunges down the beam;
	# held while the gaze neck window is open; stunned / rise: none (the clips lay the head on the floor themselves)
	var goal := 0.0
	if state == &"dead" or state == &"stunned" or state == &"rise" or state == &"recoil":
		goal = 0.0
	elif (_neck_close_in >= 0.0 or (state == &"gaze" and _fired and not _beam_done)) and _hit_at < 0.0 and not _blocked_beam:
		goal = 1.0            # no lunge onto a hero standing in the beam (petrified or blocking): her head would plunge through him
	var out_t := float(T["lean_out_time"]) if state == &"gaze" or state == &"stalk" else float(T["rise_time"])
	var rate := 1.0 / LEAN_IN_TIME if goal > _lean.weight else 1.0 / out_t
	_lean.weight = move_toward(_lean.weight, goal, rate * delta)


## Tail-aware turn: a turn that would swing a tail capsule into the hero is refused (the capsules turn by setting
## rotation, which would shove him metres). She then turns the long way round, or waits.
func face_towards(pos: Vector3, deg_per_sec: float, delta: float) -> void:
	var to := pos - global_position
	to.y = 0.0
	if to.length() < 0.01:
		return
	var diff := wrapf(atan2(to.x, to.z) - rotation.y, -PI, PI)
	if absf(diff) <= deg_to_rad(deg_per_sec) * delta:
		_turn_detour = 0.0
	var dir := _turn_detour if _turn_detour != 0.0 else signf(diff)
	# eased turn (review: 0 <-> 90 deg/s in one frame): the signed rate gathers / loses speed at T.turn_accel_deg and
	# the wanted rate shrinks with the angle left (T.turn_ease), so she starts and settles a turn instead of snapping
	var frame := Engine.get_physics_frames()
	if frame - _yaw_frame > 1:
		_yaw_rate = 0.0                                # no turn last frame (other state): start from rest
	_yaw_frame = frame
	var cap := deg_to_rad(deg_per_sec)
	var want_rate := dir * (cap if _turn_detour != 0.0 else minf(cap, absf(diff) * float(T["turn_ease"])))
	_yaw_rate = move_toward(_yaw_rate, want_rate, deg_to_rad(float(T["turn_accel_deg"])) * delta)
	_yaw_rate = clampf(_yaw_rate, -cap, cap)
	var step := absf(_yaw_rate) * delta
	if signf(_yaw_rate) != dir:
		# still unwinding a turn the other way (it decelerates); refused like any turn if it swings the tail into him
		if step > 0.000001:
			var g0 := _tail_gap()
			rotation.y += _yaw_rate * delta
			var g1 := _tail_gap()
			if g1 < 0.0 and g1 < g0:
				rotation.y -= _yaw_rate * delta
				_yaw_rate = 0.0
		return
	var amount := step if _turn_detour != 0.0 else minf(absf(diff), step)
	if amount < 0.000001:
		return
	var before := rotation.y
	var gap0 := _tail_gap()
	rotation.y = before + dir * amount
	var gap1 := _tail_gap()
	if gap1 >= 0.0 or gap1 >= gap0:
		return
	rotation.y = before - dir * step                   # the other way round
	var gap2 := _tail_gap()
	if gap2 < 0.0 and gap2 < gap0:
		rotation.y = before                            # wedged both ways: wait
		_yaw_rate = 0.0
	else:
		_yaw_rate = -dir * step / maxf(delta, 0.0001)
		if _turn_detour == 0.0:
			_turn_detour = -dir                        # keep going the long way until she faces the target
			Game.event("tail_turn_blocked", {"gap": snappedf(gap1, 0.01)})
	_turn_blocked_t += delta


## Smallest clearance between the hero's capsule and the tail capsules (m, negative = overlapping).
func _tail_gap() -> float:
	if player == null or not is_instance_valid(player):
		return INF
	var lp := to_local(player.global_position)
	var best := INF
	if _skel != null:
		for s in _tail_live:
			if not s[3]:
				continue
			var a: Vector3 = s[0]
			var d: Vector3 = s[1] - a
			var t := clampf((lp - a).dot(d) / maxf(d.length_squared(), 0.0001), 0.0, 1.0)
			var q := a + d * t
			best = minf(best, Vector2(lp.x - q.x, lp.z - q.z).length() - float(s[2]) - Tuning.PLAYER_RADIUS)
		return best
	for s in TAIL_SEGS:
		var half := float(s[1]) * 0.5
		var z := clampf(lp.z, float(s[0]) - half, float(s[0]) + half)
		var g := Vector2(lp.x, lp.z - z).length() - float(s[2]) - Tuning.PLAYER_RADIUS
		best = minf(best, g)
	return best


func _on_reflected() -> void:
	var shield := _shield_point()
	set_state(&"stunned")
	# the glare flashes on the shield face first
	_burst(shield, 1.5, Color(1.0, 1.0, 0.85, 0.95))
	Fx.spark(arena, shield, Color(0.85, 1.0, 0.75), 30, 0.12)
	Game.event("reflect_flash", {"shield_y": snappedf(shield.y - player.global_position.y, 0.01), "shield_fwd": snappedf((shield - player.global_position).dot(player.facing), 0.01)})
	# keep the gaze visible for a beat, then the glare bounces off the shield back into her eyes
	_beam.visible = true
	_draw_beam(0.3, shield)
	get_tree().create_timer(0.22, false).timeout.connect(_after_reflect.bind(shield))


## Centre of the hero's raised shield (the prop on his forearm_l socket), a little out in front of it.
func _shield_point() -> Vector3:
	var pv: CharacterVisual = player.visual
	var p := player.global_position + Vector3.UP * 1.3 + player.facing * 0.5
	if pv != null:
		var fl := pv.socket(&"forearm_l")
		for pr in pv.props():
			if is_instance_valid(pr) and pr.get_parent() == fl:
				var aabb := _world_aabb(pr)
				if aabb.size != Vector3.ZERO:
					return aabb.get_center() + player.facing * 0.15
		var s := pv.socket(&"forearm_l")
		if s != null:
			p = s.global_position + player.facing * 0.25
	return p


func _world_aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	for mi in n.find_children("*", "MeshInstance3D", true, false) + ([n] if n is MeshInstance3D else []):
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		var b := m.global_transform * m.get_aabb()
		out = b if first else out.merge(b)
		first = false
	return out


func _after_reflect(shield: Vector3) -> void:
	if state != &"gaze":
		_beam.visible = false
		_beam_mesh.clear_surfaces()
	if hp > 0 and is_instance_valid(player):
		var eyes := visual.socket(&"eyes").global_position
		_flash_line(shield, eyes)
		_burst(eyes, 1.8, Color(0.8, 1.0, 0.7, 0.9))       # the glare hits her own eyes: readable above the hero's head
		Game.shake(0.25)


func _on_weak_hit(_point: WeakPoint) -> void:
	Game.event("neck_cut", _neck_info({"state": String(state), "dist": snappedf(player_distance(), 0.1)}))
	if state == &"gaze":
		# a side cut mid-gaze: she recoils, the beam dies, the window is spent
		_neck_close_in = -1.0
		close_weak(&"neck")
		set_state(&"recoil")


# ------------------------------------------------------------------ helpers
## Harness detail: real neck socket height, weak point height and the procedural lean angle.
func _neck_info(d: Dictionary) -> Dictionary:
	d["neck_y"] = snappedf(visual.socket(&"neck").global_position.y - global_position.y, 0.01)
	d["wp_y"] = snappedf(_neck_socket.global_position.y - global_position.y, 0.01) if _neck_socket != null else -1.0
	if _lean != null:
		d["lean_deg"] = snappedf(rad_to_deg(_lean.last_angle), 0.1)
	return d


## Keeps a timed clip on the game clock: after a frame hitch (e.g. a screenshot) the AnimationPlayer can trail the
## physics clock by tenths of a second, which would move the beam off the clip's fire_start..fire_end span. Seeks
## when it drifts more than 0.04 s (clip time). Real model only.
func _sync_clip(clip: StringName, expected: float) -> void:
	if visual.is_standin or visual.current_clip != clip:
		return
	if absf(visual.clip_position() - expected) > 0.04:
		visual.seek(expected, true)


## Harness detail: playback position of the real model's current clip (-1 on the stand-in).
func _clip_pos() -> float:
	if visual.is_standin:
		return -1.0
	return snappedf(visual.clip_position(), 0.01)


func _dir_to_player() -> Vector3:
	var d := player.global_position - _gaze_origin()
	d.y = 0.0
	return d.normalized() if d.length() > 0.1 else forward()


## Floor point under her face: the fan and the hit cone start here.
func _gaze_origin() -> Vector3:
	var o := global_position + forward() * 0.9 * S
	o.y = global_position.y
	return o


func _body_center() -> Vector3:
	var c := global_position + forward() * (BODY_FWD if not visual.is_standin else 0.0)
	c.y = global_position.y
	return c


func _clamp_to_area(p: Vector3, limit := -1.0) -> Vector3:
	var lim := float(T["stalk_area"]) if limit < 0.0 else limit
	var flat := Vector2(p.x, p.z)
	if flat.length() > lim:
		flat = flat.normalized() * lim
	return Vector3(flat.x, p.y, flat.y)


func _update_neck_socket() -> void:
	if _neck_socket == null:
		return
	var n := visual.socket(&"neck").global_position
	if _skel != null:
		# real model: ON the real neck (reachable only while it is low). While the neck is high (gaze windup / fire) the
		# mark sits on the side of the neck toward the hero, a little under the jaw, so its glow leaves her eyes readable
		# (core fixer request in docs/notes/qa_requests.md)
		var high := n.y - global_position.y > 3.0
		if high and player != null and is_instance_valid(player):
			var right := forward().cross(Vector3.UP)
			var side := signf(right.dot(player.global_position - global_position))
			n += right * (side if side != 0.0 else 1.0) * 0.45 * S - Vector3.UP * 0.15 * S
		_neck_socket.global_position = n
		return
	var p := n
	if state == &"gaze" and player != null:
		var right := forward().cross(Vector3.UP)
		var side := signf(right.dot(player.global_position - global_position))
		# the side of the neck toward the hero; a leaning neck reaches out over the fan, so the mark sits just past the
		# fan's edge there (a hero cutting it stands outside the beam)
		var ahead := maxf((n - _gaze_origin()).dot(forward()), 0.0)
		var off := clampf(ahead * tan(deg_to_rad(float(T["gaze_fan_deg"]) * 0.5)) + 0.35, 0.7, 2.0)
		p += right * side * off
	elif state == &"stunned" and visual.is_standin:
		p = global_position + forward() * 3.0 * S      # the stand-in cannot lay its head down: where the head would lie
	p.y = global_position.y + clampf(n.y - global_position.y, NECK_Y_MIN, NECK_Y_MAX)
	if state == &"stunned" and visual.is_standin:
		p.y = global_position.y + 1.3
	_neck_socket.global_position = p


func _draw_beam(u: float, stop_at = null) -> void:
	_beam_mesh.clear_surfaces()
	var eye := visual.socket(&"eyes").global_position
	var half := deg_to_rad(float(T["gaze_fan_deg"]) * 0.5)
	var length := float(T["gaze_length"])
	if stop_at is Vector3:
		var flat: Vector3 = stop_at - _gaze_origin()
		flat.y = 0.0
		length = maxf(flat.length(), 1.0)
	var o := _gaze_origin()
	var l := o + _gaze_dir.rotated(Vector3.UP, half) * length
	var r := o + _gaze_dir.rotated(Vector3.UP, -half) * length
	# the light sheet slopes from the eyes down to the floor just short of the hero (the lit floor fan still shows the
	# full reach): a sheet to the far edge passed over the chase camera, a pale wedge over the frame and the stone hero
	var sheet_d := length
	if stop_at == null:
		sheet_d = clampf((player.global_position - o).dot(_gaze_dir) - (1.4 if _hit_at >= 0.0 else SHEET_STOP), 3.0, length)
	var sl := o + _gaze_dir.rotated(Vector3.UP, half) * sheet_d
	var sr := o + _gaze_dir.rotated(Vector3.UP, -half) * sheet_d
	var lift := Vector3.UP * 0.07
	var a := (0.55 + 0.25 * sin(u * 40.0)) * (1.0 - smoothstep(0.85, 1.0, u))
	var hot := Color(0.85, 1.0, 0.7, a)
	var cool := Color(GAZE_COLOR.r, GAZE_COLOR.g, GAZE_COLOR.b, a * 0.25)
	var floor_c := Color(GAZE_COLOR.r, GAZE_COLOR.g, GAZE_COLOR.b, a * 0.8)
	_beam_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	# light sheet from the eyes down onto the far edge of the fan
	_beam_mesh.surface_set_color(Color(hot.r, hot.g, hot.b, a * 0.45)); _beam_mesh.surface_add_vertex(eye)
	_beam_mesh.surface_set_color(cool); _beam_mesh.surface_add_vertex(sl + lift)
	_beam_mesh.surface_set_color(cool); _beam_mesh.surface_add_vertex(sr + lift)
	# lit fan on the floor
	_beam_mesh.surface_set_color(floor_c); _beam_mesh.surface_add_vertex(o + lift)
	_beam_mesh.surface_set_color(Color(floor_c.r, floor_c.g, floor_c.b, a * 0.3)); _beam_mesh.surface_add_vertex(l + lift)
	_beam_mesh.surface_set_color(Color(floor_c.r, floor_c.g, floor_c.b, a * 0.3)); _beam_mesh.surface_add_vertex(r + lift)
	# bright core ray: from the real eyes, along the locked direction, down to the floor where the hero stood (or the
	# shield), a camera-facing ribbon so it reads from right behind the hero
	var hit_d := clampf((player.global_position - o).dot(_gaze_dir), 4.0, length) if stop_at == null else length
	if stop_at == null and _hit_at >= 0.0:
		hit_d = maxf(hit_d - 1.4, 3.0)       # petrified: the ray stops short of the statue, which must read as grey stone
	var end := o + _gaze_dir * hit_d + Vector3.UP * (0.9 if stop_at == null else 0.0)
	if stop_at is Vector3:
		end = stop_at
	var cam := get_viewport().get_camera_3d()
	var view := (cam.global_position - (eye + end) * 0.5) if cam != null else Vector3.BACK
	var side := (end - eye).cross(view).normalized()
	var core := Color(0.92, 1.0, 0.8, minf(a * 1.4, 1.0))
	var glow := Color(GAZE_COLOR.r, GAZE_COLOR.g, GAZE_COLOR.b, a * 0.55)
	for w: Array in [[0.55, glow], [0.18, core]]:
		var hw: float = w[0]
		var col: Color = w[1]
		var edge := Color(col.r, col.g, col.b, 0.0)
		for q: Array in [[eye, end, 1.0], [eye, end, -1.0]]:
			var s := side * hw * float(q[2])
			_beam_mesh.surface_set_color(col); _beam_mesh.surface_add_vertex(eye)
			_beam_mesh.surface_set_color(edge); _beam_mesh.surface_add_vertex(eye + s * 0.4)
			_beam_mesh.surface_set_color(edge); _beam_mesh.surface_add_vertex(end + s)
			_beam_mesh.surface_set_color(col); _beam_mesh.surface_add_vertex(eye)
			_beam_mesh.surface_set_color(edge); _beam_mesh.surface_add_vertex(end + s)
			_beam_mesh.surface_set_color(col); _beam_mesh.surface_add_vertex(end)
	_beam_mesh.surface_end()


func _end_beam() -> void:
	if _beam != null:
		_beam.visible = false
		_beam_mesh.clear_surfaces()
	if _fan_edges != null:
		_fan_edges.visible = false
		_fan_mesh.clear_surfaces()
	if _eyes != null:
		_eyes.visible = false
		(_eye_halo.material_override as StandardMaterial3D).albedo_color.a = 0.0


func _petrify_flash() -> void:
	# grey stone chips + dust at his feet, no additive glow around him (QA: the white burst + beam made the petrified
	# hero a translucent white ghost; he must read as opaque grey stone)
	var pos := player.global_position + Vector3.UP * 1.0
	Fx.spark(arena, pos, Color(0.55, 0.56, 0.58), 24, 0.1)
	Fx.dust(arena, player.global_position, 1.2, Color(0.62, 0.63, 0.65, 0.85))


## A green crescent sweeping once around her at tail height: the low 360 degree swipe.
func _swoosh(center: Vector3) -> void:
	var r_out := float(T["tail_radius"])
	var im := ImmediateMesh.new()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_MIX      # additive white vanished on the white marble
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.render_priority = VFX_PRIORITY
	m.vertex_color_use_as_albedo = true
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(mi)
	mi.global_position = center + Vector3.UP * 0.6
	var segs := 48
	im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in segs:
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(i + 1) / float(segs)
		var k0 := float(i) / float(segs)
		var k1 := float(i + 1) / float(segs)
		var c0 := Color(0.20, 0.48, 0.24, 0.9 * pow(k0, 1.4))   # tail green, solid at the leading edge, fading behind it
		var c1 := Color(0.20, 0.48, 0.24, 0.9 * pow(k1, 1.4))
		var o0 := Vector3(sin(a0), 0, cos(a0))
		var o1 := Vector3(sin(a1), 0, cos(a1))
		for v in [[o0 * 1.6, c0], [o0 * r_out, c0], [o1 * r_out, c1], [o0 * 1.6, c0], [o1 * r_out, c1], [o1 * 1.6, c1]]:
			im.surface_set_color(v[1])
			im.surface_add_vertex(v[0])
	im.surface_end()
	mi.rotation.y = rotation.y
	var tw := mi.create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "rotation:y", rotation.y + TAU, 0.35)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.25).set_delay(0.25)
	tw.chain().tween_callback(mi.queue_free)


## Real model: a green crescent trailing the real tail tip while the tail sweeps (made once per swipe, turned each frame).
func _follow_sweep_fx(center: Vector3) -> void:
	if _sweep_fx == null:
		var r_out := float(T["tail_radius"])
		var im := ImmediateMesh.new()
		_sweep_fx = MeshInstance3D.new()
		_sweep_fx.mesh = im
		_sweep_fx.top_level = true
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.render_priority = VFX_PRIORITY
		m.vertex_color_use_as_albedo = true
		_sweep_fx.material_override = m
		_sweep_fx.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		arena.add_child(_sweep_fx)
		var segs := 30
		var span := deg_to_rad(150.0)
		im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
		for i in segs:
			var a0 := -span + span * float(i) / float(segs)
			var a1 := -span + span * float(i + 1) / float(segs)
			var c0 := Color(0.20, 0.48, 0.24, 0.85 * pow(float(i) / float(segs), 1.6))
			var c1 := Color(0.20, 0.48, 0.24, 0.85 * pow(float(i + 1) / float(segs), 1.6))
			var o0 := Vector3(sin(a0), 0, cos(a0))
			var o1 := Vector3(sin(a1), 0, cos(a1))
			for v in [[o0 * 1.6, c0], [o0 * r_out, c0], [o1 * r_out, c1], [o0 * 1.6, c0], [o1 * r_out, c1], [o1 * 1.6, c1]]:
				im.surface_set_color(v[1])
				im.surface_add_vertex(v[0])
		im.surface_end()
	var tip := _tip_world() - center
	_sweep_fx.global_position = center + Vector3.UP * 0.5
	_sweep_fx.rotation = Vector3(0, atan2(tip.x, tip.z), 0)


func _free_sweep_fx() -> void:
	if _sweep_fx != null and is_instance_valid(_sweep_fx):
		_sweep_fx.queue_free()
	_sweep_fx = null


## An expanding, fading additive sphere (petrify / reflect flashes).
func _burst(pos: Vector3, size: float, col: Color) -> void:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.5
	sm.height = 1.0
	mi.mesh = sm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.render_priority = VFX_PRIORITY
	m.albedo_color = col
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(mi)
	mi.global_position = pos
	mi.scale = Vector3.ONE * size * 0.25
	var tw := mi.create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE * size, 0.35)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.35)
	tw.chain().tween_callback(mi.queue_free)


func _flash_line(a: Vector3, b: Vector3) -> void:
	var im := ImmediateMesh.new()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.render_priority = VFX_PRIORITY
	m.albedo_color = Color(0.9, 1.0, 0.85, 1.0)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(mi)
	mi.global_transform = Transform3D.IDENTITY
	var side := (b - a).cross(Vector3.UP).normalized() * 0.25
	im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [a - side, a + side, b + side * 0.4, a - side, b + side * 0.4, b - side * 0.4]:
		im.surface_add_vertex(v)
	im.surface_end()
	var tw := mi.create_tween()
	tw.tween_property(m, "albedo_color:a", 0.0, 0.4)
	tw.tween_callback(mi.queue_free)
	Fx.spark(arena, b, Color(0.8, 1.0, 0.7), 24, 0.1)


## Camera hint for core (docs/notes/medusa.md request): extra lock-arm metres. Unused until PlayerCamera reads it
## (`if boss.has_method("lock_arm_extra")`). At hero-boss 6 m a 3.7 m arm shows her ~1.15x the hero's screen height,
## a 5.0 m arm ~1.33x (key_medusa.png ~1.4x). None in the stun close-up (hero at her lowered head: she towers already).
func lock_arm_extra() -> float:
	if state in [&"stunned", &"dead"] or player == null or not is_instance_valid(player):
		return 0.0
	return clampf(1.3 + 0.15 * (player_distance() - 6.0), 0.0, 1.8)


## Camera hook read by PlayerCamera.max_extra_for(): the lock arm may grow up to this much when her top would not fit
## (x1.5: 9.75 m standing, raised hands higher in the gaze windup), so her head and glowing eyes stay in frame.
func cam_max_extra() -> float:
	return CAM_MAX_EXTRA


## Camera hook (QA fixer 3; read by PlayerCamera once core lands docs/notes/qa_requests.md "medusa fixer 3" request 1):
## world points the lock camera must keep in frame on top of her live top points. During the gaze: her eyes (+0.3 m)
## and where they will be after the fire snap (measured, cam_probe trace: she rears back to eyes (0, 8.8, 0.4) in
## her frame during the windup, then the clip throws them to (0, 8.9, 4.2) at fire_start), so the arm grows during
## the 1.2 s windup instead of 0.3 s too late.
func cam_fit_points() -> PackedVector3Array:
	var out := PackedVector3Array()
	if state != &"gaze" or _eyes == null or visual.is_standin:
		return out
	out.append(_eyes.global_position + Vector3.UP * 0.3)
	if not _fired:
		out.append(to_global(SNAP_EYES_LOCAL + Vector3.UP * 0.3))
	return out


func get_lock_point() -> Vector3:
	var base := super.get_lock_point()
	if state == &"stunned" and _neck_socket != null:
		return base.lerp(_neck_socket.global_position, 0.6)
	if state == &"gaze" and not visual.is_standin:
		# QA fixer 3: during the gaze the lock point stands over her root at head height. PlayerCamera stops growing the
		# arm when the hero is within CAM_LOCK_BY_BOSS.cut_inside of the lock point, and her head (snapping forward at the
		# fire, lunging after it) came within ~4.8 m of a hero standing in the beam at 7 m: her eyes left the top of the
		# frame. Measured from her root the camera keeps its full cam_max_extra() growth there (work/medusa_fix3/cam_probe.gd).
		return Vector3(global_position.x, base.y, global_position.z)
	return base


# ------------------------------------------------------------------ test bot
## Win strategy: hold BOT_KEEP (6.4 m) in front of her (inside the 8 m gaze range); when a gaze winds up, stand in the fan and raise the shield just before
## it fires (reflect -> stunned); run to the lowered neck and cut twice; back off before the tail-swipe timer runs out;
## roll out of a tail swipe. `--medusa-bot=flank` instead steps out of the locked fan and cuts the side of the neck;
## `--medusa-bot=linger` crowds her while she stalks (provokes tail swipes, then dodges them).
func bot_advice() -> Dictionary:
	var adv := {"move_to": player.global_position, "face": global_position, "roll": false, "block": false, "attack": false}
	var to_player := player.global_position - global_position
	to_player.y = 0.0
	var dir := to_player.normalized() if to_player.length() > 0.1 else forward()
	var mode := str(Game.args.get("medusa-bot", ""))
	var flank := mode == "flank"
	match state:
		&"gaze":
			var t := state_time
			if flank:
				if is_exposed(&"neck") and (_fired or not _gaze_locked):
					_advise_strike(adv)
				elif _gaze_locked and not _fired:
					# out of the fan and toward her at once: aim 1.3 m outside the nearer fan edge, 3 m closer
					var o := _gaze_origin()
					var rel := player.global_position - o
					rel.y = 0.0
					var side := signf(_gaze_dir.cross(rel).y)
					if side == 0.0:
						side = 1.0
					var half := deg_to_rad(float(T["gaze_fan_deg"]) * 0.5)
					var edge := _gaze_dir.rotated(Vector3.UP, half * side)
					var outward := edge.cross(Vector3.UP) * -side
					if _gaze_dir.angle_to(rel.normalized()) < half + deg_to_rad(5.0):
						adv["move_to"] = player.global_position + _gaze_dir.cross(Vector3.UP) * -side * 3.0   # straight sideways first
						# a side-step (strafe 1.8 m/s for 0.3 s) cannot clear a 1.8 m half-fan before an enraged fire: roll
						adv["roll"] = _gaze_windup - t < 0.5
					else:
						adv["move_to"] = o + edge * maxf(rel.length() - 3.0, 2.5) + outward * 1.3
			elif not _fired:
				adv["block"] = t >= _gaze_windup - 0.45
			elif not _beam_done:
				adv["block"] = true
			else:
				_advise_keep(adv, dir)
		&"stunned":
			if is_exposed(&"neck"):
				_advise_strike(adv)
			else:
				_advise_keep(adv, dir)
		&"tail_swipe":
			# the rule a person follows: roll OUT of the ring before it fills (react BOT_REACT s after it lights up), roll
			# again while still inside, keep backing away in between
			var c := _body_center()
			var out := Vector3(player.global_position.x - c.x, 0.0, player.global_position.z - c.z)
			var r_c := out.length()
			out = out.normalized() if r_c > 0.1 else dir
			adv["move_to"] = c + out * (float(T["tail_radius"]) + 3.0)
			adv["roll"] = state_time >= BOT_REACT and r_c < float(T["tail_radius"]) + 0.5
		&"recoil":
			if is_exposed(&"neck"):
				_advise_strike(adv)
			else:
				_advise_keep(adv, dir)
		_:
			if is_exposed(&"neck"):
				_advise_strike(adv)
			else:
				_advise_keep(adv, dir)
	return adv


func _advise_keep(adv: Dictionary, dir: Vector3) -> void:
	var linger := str(Game.args.get("medusa-bot", "")) == "linger"     # probe: crowd her until the tail swipe comes
	var keep := Game.arg_float("medusa-keep", BOT_KEEP)   # probe: hold this range (default BOT_KEEP)
	adv["move_to"] = global_position + dir * (2.0 if linger else keep)
	if Game.args.has("medusa-keep") and not linger:
		# probe of a player who stands his ground between keep_min and `keep`: no backing off when she comes in
		var d := player_distance()
		if d >= float(T["keep_min"]) - 0.5 and d <= keep + 0.5:
			adv["move_to"] = player.global_position


func _advise_strike(adv: Dictionary) -> void:
	var wp: WeakPoint = weak_points[&"neck"]
	var p := wp.global_position
	if _skel != null:
		# real model: the hero faces her ORIGIN while locked, so he stands where the neck lies between him and her
		var fwd := forward()
		var n := p
		if state == &"stunned" or state == &"rise":
			n = to_global(STUN_NECK_LOCAL)          # where the neck will lie (the recoil holds it 7 m up first)
			adv["move_to"] = n + fwd * 2.35         # against the snake-hair capsule round the lowered head (hero >= ~2.3 m out)
		else:
			# gaze window: beside the lowered neck, outside the beam (fan edge + margin)
			var right := fwd.cross(Vector3.UP)
			var side := signf(right.dot(player.global_position - global_position))
			if side == 0.0:
				side = 1.0
			var s := n + right * side * 2.2 + fwd * 1.0
			var o := _gaze_origin()
			var rel := s - o
			rel.y = 0.0
			var half := deg_to_rad(float(T["gaze_fan_deg"]) * 0.5 + 7.0)
			if _beam_phase == 1 and _gaze_dir.angle_to(rel.normalized()) < half:
				s = n + right * side * 3.0 + fwd * 1.0          # wider while the beam still burns
			adv["move_to"] = s
		var dn := p - player.global_position
		var up := dn.y
		dn.y = 0.0
		var fc := player.facing
		# blade reach ~2.5 m + weak point radius 1.2: swing from up to ~3.3 m (the hair keeps him ~2.3 m from the neck)
		adv["attack"] = up < 2.7 and dn.length() < Tuning.SWORD_REACH + 1.3 and dn.normalized().dot(fc) > 0.3
		return
	# stand 1.4 m beyond the mark, on the side away from her (locked on, the hero faces her: the mark is then in front
	# of him). During a gaze the mark sits beside the neck: step out sideways; when stunned: out along her body line.
	var away := p - visual.socket(&"neck").global_position
	away.y = 0.0
	if state == &"stunned" or away.length() < 0.3:
		away = p - global_position
		away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else forward()
	adv["move_to"] = p + away * 1.4
	var dd := p - player.global_position
	dd.y = 0.0
	var facing := player.global_basis.z
	facing.y = 0.0
	adv["attack"] = dd.length() < Tuning.SWORD_REACH + 0.5 and dd.normalized().dot(facing.normalized()) > 0.2
