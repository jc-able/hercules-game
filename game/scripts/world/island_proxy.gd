extends Node3D
## IslandProxy (world module; loaded by path, no class_name). One island of the sea map as seen from the air or from
## another island: a procedural rocky body + dressing that hints at what lives there, a landing ring, a pillar of
## light (open and undefeated) or a dark storm wall (locked). The node sits at the island centre at SEA LEVEL;
## everything inside is built relative to it, so the same island works in the sea scene (sea y = 0) and as distant
## scenery from the home plateau (sea y = -14).
## States: "home" (always a ring), "locked" (storm wall, no ring), "open" (pillar + ring), "defeated" (calm, ring only).
## Also holds small static helpers shared by the world scenes (meshes, loops, HUD tweaks).

const PROFILES := {
	# top_r / base_r: plateau radius at the top / at the waterline; top_h: plateau height above the sea;
	# ring_r / ring_up: landing ring radius and its height above the plateau; struct_h: tallest dressing on the top.
	"home": {"top_r": 24.0, "base_r": 38.0, "top_h": 14.0, "ring_r": 24.0, "ring_up": 30.0, "struct_h": 10.0,
		"top": Color(0.42, 0.62, 0.30), "side": Color(0.78, 0.66, 0.48), "seed": 1.7},
	# (play-test fix: cyclops and medusa got 20 m cliffs, green tops and tall silhouettes - a three-tier quarry wall,
	# a 12 m colonnade with its architrave - that read from 500 m; rings moved up to stay above the dressing)
	"cyclops": {"top_r": 46.0, "base_r": 64.0, "top_h": 20.0, "ring_r": 28.0, "ring_up": 38.0, "struct_h": 27.0,
		"top": Color(0.50, 0.62, 0.31), "side": Color(0.84, 0.69, 0.47), "seed": 4.2},
	"medusa": {"top_r": 40.0, "base_r": 58.0, "top_h": 20.0, "ring_r": 26.0, "ring_up": 30.0, "struct_h": 14.0,
		"top": Color(0.52, 0.63, 0.36), "side": Color(0.74, 0.75, 0.73), "seed": 2.9},
	"hydra": {"top_r": 70.0, "base_r": 92.0, "top_h": 12.0, "ring_r": 28.0, "ring_up": 30.0, "struct_h": 10.0,
		"top": Color(0.17, 0.15, 0.19), "side": Color(0.22, 0.18, 0.24), "seed": 6.1},
}
## The Hydra's volcano cone (local to the island centre): north of the basalt shelf, crater glowing, smoke plume.
const VOLCANO := {"offset": Vector3(0, 0, -82), "base_r": 64.0, "peak": 88.0, "crater_r": 15.0, "lava_y": -7.0}
const RING_HALF_H := 18.0          ## the landing zone spans ring height +- this
const STRUCT_FADE := 30.0          ## metres outside the top rim over which the dressing height fades out
const RIDER_STANDIN_HIPS := 0.47   ## stand-in hero (no hips bone): hips at this share of the height
const PILLAR_H := 700.0
const STORM_H := 175.0             ## above the flight ceiling (140 m): no flying over it
const STORM_MARGIN := 30.0
const SMOKE_PUFFS := 18

const PILLAR_SHADER := """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec4 color : source_color = vec4(1.0, 0.82, 0.42, 1.0);
uniform float intensity = 1.0;
uniform float height = 700.0;
varying float h;
void vertex() { h = VERTEX.y / height + 0.5; }
void fragment() {
	float core = pow(clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 1.6);
	float fade = pow(clamp(1.0 - h, 0.0, 1.0), 1.4) * smoothstep(0.0, 0.01, h);
	float shimmer = 0.85 + 0.15 * sin(h * 90.0 - TIME * 3.0);
	ALBEDO = color.rgb * intensity * core * fade * shimmer;
}
"""

const STORM_SHADER := """
shader_type spatial;
render_mode unshaded, cull_back, depth_draw_never, shadows_disabled;
uniform vec4 dark : source_color = vec4(0.09, 0.08, 0.14, 1.0);
uniform vec4 light : source_color = vec4(0.46, 0.42, 0.58, 1.0);
uniform float flash = 0.0;
uniform float height = 175.0;
varying vec3 lp;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.07; a *= 0.5; } return v; }
void vertex() { lp = VERTEX; }
void fragment() {
	float a = atan(lp.z, lp.x) / 6.28318 + 0.5;
	float hy = lp.y / height + 0.5;
	vec2 uv = vec2(a * 40.0 + TIME * 0.35, hy * 7.0 - TIME * 0.10);
	uv.x += sin(hy * 9.0 + TIME * 0.3) * 0.8;
	float n = fbm(uv);
	float n2 = fbm(uv * 2.4 + vec2(TIME * 0.5, 1.7));
	float swirl = smoothstep(0.42, 0.62, fbm(uv * vec2(1.0, 3.0) + vec2(n * 2.0, 0.0)));
	vec3 col = mix(dark.rgb, light.rgb, swirl * 0.8 + 0.2 * n);
	col = mix(col, dark.rgb * 0.6, smoothstep(0.55, 1.0, hy));
	col += vec3(0.80, 0.85, 1.0) * flash * smoothstep(0.45, 0.85, n2);
	float top_edge = 0.70 + 0.28 * fbm(vec2(a * 30.0 + TIME * 0.05, 3.1));   // ragged cloud top
	float alpha = (0.82 + 0.18 * n) * smoothstep(0.0, 0.06, hy) * (1.0 - smoothstep(top_edge - 0.08, top_edge, hy));
	ALBEDO = col;
	ALPHA = clamp(alpha, 0.0, 1.0);
}
"""

var island_id: StringName = &"home"
var prof: Dictionary = {}
var state := ""
var _ring: Node3D
var _ring_mat: StandardMaterial3D
var _ring_disc_mat: StandardMaterial3D
var _pillar: MeshInstance3D
var _beacon_sfx := 0                 # Sfx loop id of the pillar hum (0 = none)
var _storm: MeshInstance3D
var _storm_mat: ShaderMaterial
var _storm_bolt: Node3D
var _storm_t := 2.0
var _flash := 0.0
var _smoke: Array[MeshInstance3D] = []
var _smoke_phase: Array[float] = []
var _smoke_mat: StandardMaterial3D
var _lava_mat: StandardMaterial3D
var _clock := 0.0
## feedback 2 (owner: "see the creatures in the maps whenever we're flying over them ... animated walking around"):
## set by the sea scene before the node enters the tree. An island whose boss is not beaten shows the creature (the
## real model, its walk / idle clips, no collision, no AI) patrolling an arc of its arena: walk, stop and idle, turn
## round, walk back. Beaten bosses are not shown. Hidden (and not processed) beyond CREATURE_RANGE from the camera.
var creature_enabled := false
const CREATURE_RANGE := 900.0     ## re-fix: was 1300 m; beyond ~900 m the creature is under ~8 px tall (review projection)
const CREATURE_NEAR_FROM := 170.0  ## re-fix: from this flat distance to the camera in, the creature eases down ...
const CREATURE_NEAR_TO := 55.0     ## ... to CREATURE_NEAR_SCALE x its fight size here (the fight then opens at 1x)
const CREATURE_NEAR_SCALE := 1.2
## per island: model, walk clip, arena centre (local, on the top), patrol radius, arc (deg), size factor (the
## creatures are drawn 1.4-2.4x their fight size, 15-20 m, so they read from the flight height and from ~300 m out;
## nothing else uses this copy)
const CREATURES := {
	"cyclops": {"walk": &"walk", "centre": Vector3(0, 0.0, 0), "r": 36.0, "arc": 60.0, "scale": 2.6, "off": 69.0},
	"medusa": {"walk": &"slither", "centre": Vector3(0, 0.0, 0), "r": 37.0, "arc": 60.0, "scale": 3.0, "off": 69.0},
	"hydra": {"walk": &"walk", "centre": Vector3(0, 0.0, 14.0), "r": 18.0, "arc": 110.0, "scale": 1.7, "side": "side"},
}
const CREATURE_IDLE_TIME := 2.6     ## seconds of idle at each end of the arc
const CREATURE_TURN_TIME := 1.8     ## seconds to turn round on the spot (walk clip at half rate)
var _creature: CharacterVisual = null
var _cr_state := 0                  # 0 walk, 1 idle, 2 turn
var _cr_t := 0.0                    # seconds in the current state
var _cr_ang := 0.0                  # current angle on the patrol circle (radians)
var _cr_dir := 1.0                  # +1 / -1 along the circle
var _cr_a0 := 0.0                   # arc start / end angles
var _cr_a1 := 0.0
var _cr_yaw0 := 0.0                 # turn: yaw at the start of the turn
var _cr_shown := true             # (true: the first tick hides it when it must not show)


## Called before the node enters the tree.
func setup(id: StringName) -> void:
	island_id = id
	prof = PROFILES.get(String(id), PROFILES["home"])
	name = "Island_%s" % id


func _ready() -> void:
	if prof.is_empty():
		setup(island_id)
	_build_body()
	_build_dressing()
	_build_ring()
	_build_pillar()
	_build_storm()
	if creature_enabled and CREATURES.has(String(island_id)):
		_build_creature()
	refresh()
	Game.progress_changed.connect(refresh)


# ------------------------------------------------------------------ queries
## Display name ("The Quarry Isle").
func title() -> String:
	var t: Array = Tuning.ISLAND_TITLES.get(String(island_id), [String(island_id).capitalize(), ""])
	return String(t[0])


func top_height() -> float:
	return float(prof["top_h"])


## Global centre of the landing ring.
func ring_center() -> Vector3:
	return global_position + Vector3(0, float(prof["top_h"]) + float(prof["ring_up"]), 0)


func ring_radius() -> float:
	return float(prof["ring_r"])


func has_ring() -> bool:
	return state != "locked"


## True when `p` (global) is inside the landing zone (a disc of ring_radius, RING_HALF_H up and down).
func in_ring(p: Vector3) -> bool:
	if not has_ring():
		return false
	var c := ring_center()
	return Vector2(p.x - c.x, p.z - c.z).length() < ring_radius() and absf(p.y - c.y) < RING_HALF_H


## Radius of the storm wall around a locked island (from the island centre).
func storm_radius() -> float:
	var r := float(prof["base_r"])
	if island_id == &"hydra":
		r = maxf(r, absf(VOLCANO["offset"].z) + float(VOLCANO["base_r"]))
	return r + STORM_MARGIN


## True when the island is locked and `p` is inside its storm wall.
func blocks(p: Vector3) -> bool:
	return state == "locked" and flat_distance(p) < storm_radius()


## Horizontal distance from the island centre.
func flat_distance(p: Vector3) -> float:
	return Vector2(p.x - global_position.x, p.z - global_position.z).length()


## Global height of the island (with its tallest dressing) under `p`; the sea level when `p` is off the island.
func ground_height(p: Vector3) -> float:
	var l := p - global_position
	var d := Vector2(l.x, l.z).length()
	var top_r := float(prof["top_r"])
	var base_r := float(prof["base_r"])
	var top_h := float(prof["top_h"])
	var y := 0.0
	if d < top_r:
		y = top_h
	elif d < base_r:
		y = lerpf(top_h, 0.0, (d - top_r) / (base_r - top_r))
	# the tallest dressing fades in over 30 m outside the rim (a step here made Pegasus pop up in one frame)
	y += float(prof["struct_h"]) * (1.0 - smoothstep(top_r, top_r + STRUCT_FADE, d))
	if island_id == &"hydra":
		y = maxf(y, volcano_height(Vector2(l.x, l.z)))
	return global_position.y + y


## Height of the volcano cone above the sea at a local horizontal point (0 outside the cone).
static func volcano_height(local_xz: Vector2) -> float:
	var o: Vector3 = VOLCANO["offset"]
	var d := local_xz.distance_to(Vector2(o.x, o.z))
	var br := float(VOLCANO["base_r"])
	var cr := float(VOLCANO["crater_r"])
	if d >= br:
		return 0.0
	if d <= cr:
		return float(VOLCANO["peak"])
	var s := sqrt((d - cr) / (br - cr))
	return (1.0 - s) * float(VOLCANO["peak"])


# ------------------------------------------------------------------ state
## Reads Game progress and shows the ring / pillar / storm / smoke that fit.
func refresh() -> void:
	var s := "home"
	if island_id != &"home":
		if bool(Game.defeated.get(String(island_id), false)):
			s = "defeated"
		elif Game.is_unlocked(island_id):
			s = "open"
		else:
			s = "locked"
	state = s
	if _ring != null:
		_ring.visible = s != "locked"
		var col := Color(1.0, 0.80, 0.36)
		var energy := 3.0
		match s:
			"home":
				col = Color(0.62, 0.86, 1.0)
				energy = 2.2
			"defeated":
				col = Color(0.92, 0.92, 0.88)
				energy = 1.2
		_ring_mat.albedo_color = col
		_ring_mat.emission = col
		_ring_mat.emission_energy_multiplier = energy
		_ring_disc_mat.albedo_color = Color(col.r, col.g, col.b, 0.10)
	if _pillar != null:
		_pillar.visible = s == "open"
		# the pillar of light hums near the landing ring while the island is open
		if s == "open" and _beacon_sfx == 0 and _ring != null:
			_beacon_sfx = Sfx.loop("beacon_loop", _ring)
		elif s != "open" and _beacon_sfx != 0:
			Sfx.stop_loop(_beacon_sfx, 0.5)
			_beacon_sfx = 0
	if _storm != null:
		_storm.visible = s == "locked"
	if island_id == &"hydra":
		var calm := s == "defeated"
		for i in _smoke.size():
			_smoke[i].visible = not calm or i % 4 == 0
		if _lava_mat != null:
			_lava_mat.emission_energy_multiplier = 1.2 if calm else 3.2


func _process(delta: float) -> void:
	_clock += delta
	if _ring != null and _ring.visible:
		_ring.rotation.y += delta * 0.25
		var k := 1.0 + 0.025 * sin(_clock * 2.4)
		_ring.scale = Vector3(k, 1.0, k)
	if _storm != null and _storm.visible:
		_tick_storm(delta)
	if not _smoke.is_empty():
		_tick_smoke(delta)
	if _creature != null:
		_tick_creature(delta)


# ------------------------------------------------------------------ the creature seen from the air (feedback 2)
func _build_creature() -> void:
	var row: Dictionary = CREATURES[String(island_id)]
	_creature = CharacterVisual.create(island_id)
	_creature.name = "Creature"
	add_child(_creature)
	_creature.scale = Vector3.ONE * float(row["scale"])
	for mi in _creature.find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# the arc lies to the SIDE of the line Pegasus arrives on (from the previous island): flying in, Pegasus covers
	# the middle and the near side of the island in the frame, and the creature walks beside it in view
	var order: Array = Tuning.UNLOCK_ORDER
	var i := order.find(island_id)
	var prev: Vector3 = Tuning.ISLANDS["home"] if i <= 0 else Tuning.ISLANDS[String(order[i - 1])]
	var own: Vector3 = Tuning.ISLANDS.get(String(island_id), Vector3.ZERO)
	var mid := atan2(prev.x - own.x, prev.z - own.z) + PI * 0.5
	if row.has("off"):
		# re-fix (review: the Cyclops walked among the quarry stones and Medusa behind the colonnade, both behind the
		# pair on the way in): a short arc on the open grass OUTSIDE the columns (r 36-37, the top is r 40-46), on the
		# near half, centred `off` deg off the arrival line. Flying in, the pair covers the middle of the frame and the
		# columns hide the court from the flight height; out here the creature is 36 m to the side, beside the pair
		mid = atan2(prev.x - own.x, prev.z - own.z) + deg_to_rad(float(row["off"]))
	var half := deg_to_rad(float(row["arc"])) * 0.5
	_cr_a0 = mid - half
	_cr_a1 = mid + half
	_cr_ang = lerpf(_cr_a0, _cr_a1, 0.35)
	_cr_dir = 1.0
	_cr_state = 0
	_cr_t = 0.0
	_creature.play(StringName(row["walk"]), 0.0, _creature_rate())
	_place_creature(0.0)


## Walk clip rate (scaled model: the feet keep pace with the ground they cover).
func _creature_rate() -> float:
	return 0.8


## Ground speed (m/s) along the patrol at the current clip rate.
func _creature_speed() -> float:
	var row: Dictionary = CREATURES[String(island_id)]
	var ms := _creature.move_speed(StringName(row["walk"]))
	if ms <= 0.0:
		ms = 2.0
	return ms * _creature_rate() * _creature.scale.x


## Puts the creature on the patrol circle at _cr_ang facing along the walk (dir) or with yaw override `yaw_over`.
func _place_creature(_delta: float, yaw_over := INF) -> void:
	var row: Dictionary = CREATURES[String(island_id)]
	var c: Vector3 = row["centre"]
	var r := float(row["r"])
	_creature.position = Vector3(c.x + sin(_cr_ang) * r, float(prof["top_h"]) + c.y, c.z + cos(_cr_ang) * r)
	if yaw_over != INF:
		_creature.rotation.y = yaw_over
	else:
		_creature.rotation.y = _walk_yaw()


## Facing while walking: the tangent of the circle in the walk direction (+Z of the model = forward).
func _walk_yaw() -> float:
	var t := Vector3(cos(_cr_ang), 0, -sin(_cr_ang)) * _cr_dir
	return atan2(t.x, t.z)


func _tick_creature(delta: float) -> void:
	var want := state != "defeated"
	var cam_d := INF
	if want:
		var cam := get_viewport().get_camera_3d()
		if cam != null:
			cam_d = flat_distance(cam.global_position)
		want = cam_d < CREATURE_RANGE
	if want != _cr_shown:
		_cr_shown = want
		_creature.visible = want
		_creature.process_mode = Node.PROCESS_MODE_INHERIT if want else Node.PROCESS_MODE_DISABLED
	if not want:
		return
	var row: Dictionary = CREATURES[String(island_id)]
	var walk: StringName = StringName(row["walk"])
	var r := float(row["r"])
	# re-fix (review: the 2.2x Cyclops walked beside Pegasus at the landing, then the fight opened with the 1x boss):
	# drawn large from afar, eased down to ~1.2x by the time Pegasus is over the island
	var sc := lerpf(CREATURE_NEAR_SCALE, float(row["scale"]), smoothstep(CREATURE_NEAR_TO, CREATURE_NEAR_FROM, cam_d))
	_creature.scale = Vector3.ONE * sc
	_cr_t += delta
	match _cr_state:
		0:
			_cr_ang += _cr_dir * _creature_speed() * delta / r
			var at_end := (_cr_dir > 0.0 and _cr_ang >= _cr_a1) or (_cr_dir < 0.0 and _cr_ang <= _cr_a0)
			if at_end:
				_cr_ang = clampf(_cr_ang, _cr_a0, _cr_a1)
				_cr_state = 1
				_cr_t = 0.0
				_creature.play(&"idle", 0.5)
			_place_creature(delta)
		1:
			if _cr_t >= CREATURE_IDLE_TIME:
				_cr_state = 2
				_cr_t = 0.0
				_cr_yaw0 = _creature.rotation.y
				_cr_dir = -_cr_dir
				_creature.play(walk, 0.4, _creature_rate() * 0.5)
		2:
			var k := smoothstep(0.0, 1.0, clampf(_cr_t / CREATURE_TURN_TIME, 0.0, 1.0))
			var y1 := _walk_yaw()
			_place_creature(delta, _cr_yaw0 + angle_difference(_cr_yaw0, y1) * k)
			if _cr_t >= CREATURE_TURN_TIME:
				_cr_state = 0
				_cr_t = 0.0
				_creature.set_speed(_creature_rate())


func _tick_storm(delta: float) -> void:
	_storm.rotation.y += delta * 0.05
	_storm_t -= delta
	if _storm_t <= 0.0:
		_storm_t = randf_range(1.5, 5.0)
		_flash = 1.0
		var a := randf() * TAU
		_storm_bolt.position = Vector3(sin(a), 0, cos(a)) * storm_radius() + Vector3(0, randf_range(50.0, 130.0), 0)
		var p := Game.player()
		var cam := get_viewport().get_camera_3d()
		var near_pos := cam.global_position if cam != null else (p.global_position if p != null else Vector3.ZERO)
		if flat_distance(near_pos) < storm_radius() + 400.0:
			Sfx.play("thunder", _storm_bolt.global_position, -4.0, randf_range(0.85, 1.1))
	_flash = maxf(_flash - delta * 5.0, 0.0)
	var f := _flash * (0.6 + 0.4 * sin(_clock * 60.0))
	_storm_mat.set_shader_parameter("flash", f)


func _tick_smoke(delta: float) -> void:
	var o: Vector3 = VOLCANO["offset"]
	var base := Vector3(o.x, float(VOLCANO["peak"]) - 2.0, o.z)
	var wind := Vector3(0.55, 0.0, 0.35)
	for i in _smoke.size():
		var p := fmod(_smoke_phase[i] + delta * 0.035, 1.0)
		_smoke_phase[i] = p
		var wob := Vector3(sin(p * 9.0 + i) * 4.0, 0, cos(p * 7.0 + i * 1.3) * 4.0)
		_smoke[i].position = base + wind * p * p * 160.0 + Vector3(0, p * 110.0, 0) + wob * (1.0 + p * 3.0)
		_smoke[i].scale = Vector3(1.0, 0.75, 1.0) * (7.0 + p * 34.0) * (1.0 - smoothstep(0.8, 1.0, p) * 0.7)


# ------------------------------------------------------------------ building
func _build_body() -> void:
	var top_r := float(prof["top_r"])
	var base_r := float(prof["base_r"])
	var top_h := float(prof["top_h"])
	var seed_v := float(prof["seed"])
	add_child(plateau_mesh(top_r, base_r, top_h, -6.0, seed_v, prof["top"], prof["side"]))
	if island_id == &"hydra":
		var o: Vector3 = VOLCANO["offset"]
		var cone := cone_mesh(float(VOLCANO["base_r"]), float(VOLCANO["crater_r"]), float(VOLCANO["peak"]), -6.0,
			seed_v + 3.0, Color(0.20, 0.16, 0.22), Color(0.10, 0.08, 0.10))
		cone.position = o
		add_child(cone)
		_build_lava(o)


func _build_lava(o: Vector3) -> void:
	_lava_mat = glow_material(Color(1.0, 0.42, 0.10), 3.2)
	var peak := float(VOLCANO["peak"])
	var cr := float(VOLCANO["crater_r"])
	var lava := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = cr * 0.72
	cm.bottom_radius = cr * 0.72
	cm.height = 0.5
	cm.radial_segments = 24
	lava.mesh = cm
	lava.material_override = _lava_mat
	lava.position = o + Vector3(0, peak + float(VOLCANO["lava_y"]), 0)
	add_child(lava)
	# glowing rivers down the cone
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var br := float(VOLCANO["base_r"])
	for j in 6:
		var a := TAU * float(j) / 6.0 + 0.4 + 0.3 * sin(float(j) * 2.1)
		var prev_l := Vector3.ZERO
		var prev_r := Vector3.ZERO
		var steps := 9
		for k in steps + 1:
			var s := lerpf(0.02, 0.62 + 0.12 * sin(float(j) * 1.7), float(k) / float(steps))   # 0 = rim, 1 = base
			var d := cr + (br - cr) * s * s + 1.0
			var y := lerpf(peak, -6.0, s) + 0.9
			var wig := a + 0.06 * sin(float(k) * 1.3 + float(j))
			var dir := Vector3(sin(wig), 0, cos(wig))
			var side := Vector3(cos(wig), 0, -sin(wig))
			var w := lerpf(1.2, 3.2, s)
			var c := o + dir * d + Vector3(0, y, 0)
			var l := c - side * w
			var r := c + side * w
			if k > 0:
				for v in [prev_l, prev_r, r, prev_l, r, l]:
					st.add_vertex(v)
			prev_l = l
			prev_r = r
	st.generate_normals()
	var rivers := MeshInstance3D.new()
	rivers.mesh = st.commit()
	var rm := _lava_mat.duplicate() as StandardMaterial3D
	rm.cull_mode = BaseMaterial3D.CULL_DISABLED
	rivers.material_override = rm
	rivers.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(rivers)
	# (no OmniLight at the crater: the toon shader bands any light > 0 into square cluster tiles; the glow comes
	# from the emissive lava + the plume's emission)
	# smoke plume
	_smoke_mat = StandardMaterial3D.new()
	_smoke_mat.albedo_color = Color(0.26, 0.24, 0.25, 0.55)
	_smoke_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_smoke_mat.roughness = 1.0
	_smoke_mat.emission_enabled = true
	_smoke_mat.emission = Color(0.35, 0.12, 0.04)
	_smoke_mat.emission_energy_multiplier = 0.22
	var sm := SphereMesh.new()
	sm.radius = 1.0
	sm.height = 1.7
	sm.radial_segments = 10
	sm.rings = 6
	for i in SMOKE_PUFFS:
		var mi := MeshInstance3D.new()
		mi.mesh = sm
		mi.material_override = _smoke_mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_smoke.append(mi)
		_smoke_phase.append(float(i) / float(SMOKE_PUFFS))
	_tick_smoke(0.0)


func _build_dressing() -> void:
	var top := float(prof["top_h"])
	match String(island_id):
		"home":
			EnvKit.prop(self, "temple", Vector3(0, top, 11), 180.0, 1.0, false)
			for p in [Vector3(-10, 0, 13), Vector3(10, 0, 13), Vector3(-15, 0, 6), Vector3(15, 0, 6), Vector3(-8, 0, -16)]:
				EnvKit.prop(self, "cypress", p + Vector3(0, top, 0), 0.0, 1.0, false)
			for p in [Vector3(-13, 0, -6), Vector3(14, 0, -3)]:
				EnvKit.prop(self, "olive_tree", p + Vector3(0, top, 0), randf() * 360.0, 1.0, false)
		"cyclops":
			# the quarry floor: a packed-earth disc (the arena ring, r 30) cut into the grassy top
			var floor_disc := MeshInstance3D.new()
			var fm := CylinderMesh.new()
			fm.top_radius = 30.0
			fm.bottom_radius = 30.5
			fm.height = 0.4
			fm.radial_segments = 64
			floor_disc.mesh = fm
			floor_disc.material_override = CharacterVisual.make_toon(Color(0.80, 0.65, 0.44), null, 0.0, 0.0)
			floor_disc.position = Vector3(0, top + 0.2, 0)
			add_child(floor_disc)
			for i in 12:
				if i % 4 == 3:
					continue
				var a := TAU * float(i) / 12.0
				var pos := Vector3(sin(a) * 32.0, top, cos(a) * 32.0)
				EnvKit.prop(self, "column_broken" if i % 2 == 0 else "column", pos, rad_to_deg(a), 1.4, false)
			# quarry wall: a horseshoe of cut blocks in three receding tiers (~27 m) round the north-east rim, the
			# isle's silhouette from far off
			for i in 10:
				var a := deg_to_rad(0.0 + 15.0 * float(i))
				var r := 38.5
				var out := Vector3(sin(a), 0, -cos(a))
				var pos := out * r + Vector3(0, top, 0)
				var yaw := rad_to_deg(atan2(-out.x, -out.z))
				var edge := i == 0 or i == 9          # the horseshoe's ends step down
				EnvKit.prop(self, "cliff_rock", pos, yaw, 2.6, false)
				EnvKit.prop(self, "cliff_rock", pos + Vector3(0, 9.6, 0) + out * 1.6, yaw + 20.0, 2.0 if edge else 2.4, false)
				if not edge:
					EnvKit.prop(self, "cliff_rock", pos + Vector3(0, 18.6, 0) + out * 3.0, yaw - 15.0, 2.1, false)
			# cypresses on the south-west rim (green against the sea, height for the silhouette's other side)
			for i in 5:
				var a := deg_to_rad(195.0 + 22.0 * float(i))
				EnvKit.prop(self, "cypress", Vector3(sin(a) * 39.0, top, -cos(a) * 39.0), 0.0, 1.3 + 0.15 * float(i % 2), false)
			for p in [Vector3(-20, 0, 24), Vector3(24, 0, 20), Vector3(-30, 0, -10)]:
				EnvKit.prop(self, "boulder", p + Vector3(0, top, 0), randf() * 360.0, 1.6, false)
		"medusa":
			var disc := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 30.0
			cm.bottom_radius = 30.5
			cm.height = 0.4
			cm.radial_segments = 64
			disc.mesh = cm
			disc.material_override = CharacterVisual.make_toon(Color(0.95, 0.94, 0.90), null, 0.0, 0.0)
			disc.position = Vector3(0, top + 0.2, 0)
			add_child(disc)
			# the sanctuary colonnade: 14 columns of 12 m carrying a continuous architrave ring (the isle's silhouette)
			var col_r := 34.0
			var col_s := 2.0
			var lintel_y := top + 6.0 * col_s
			var lintel_mat := CharacterVisual.make_toon(Color(0.93, 0.92, 0.88), null, 0.0, 0.05)
			for i in 14:
				var a := TAU * float(i) / 14.0
				EnvKit.prop(self, "column", Vector3(sin(a) * col_r, top, cos(a) * col_r), 0.0, col_s, false)
				var a2 := TAU * (float(i) + 0.5) / 14.0
				var seg := MeshInstance3D.new()
				var bm := BoxMesh.new()
				bm.size = Vector3(2.0 * col_r * sin(PI / 14.0) + 1.6, 1.4, 2.8)
				seg.mesh = bm
				seg.material_override = lintel_mat
				seg.position = Vector3(sin(a2), 0, cos(a2)) * col_r * cos(PI / 14.0) + Vector3(0, lintel_y + 0.7, 0)
				seg.rotation.y = a2
				add_child(seg)
			for i in 10:
				var a := TAU * (float(i) + 0.5) / 10.0
				var pos := Vector3(sin(a) * 30.0, top, cos(a) * 30.0)
				EnvKit.prop(self, "statue_a" if i % 2 == 0 else "statue_b", pos, rad_to_deg(atan2(-pos.x, -pos.z)), 1.6, false)
			EnvKit.prop(self, "gate", Vector3(0, top, -38.0), 0.0, 1.5, false)
		"hydra":
			for i in 8:
				var a := TAU * float(i) / 8.0 + 0.3
				var r := 38.0 + 4.0 * sin(float(i) * 2.7)
				EnvKit.prop(self, "basalt_spire", Vector3(sin(a) * r, top, cos(a) * r), randf() * 360.0, 1.2 + 0.3 * sin(float(i)), false)


func _build_ring() -> void:
	_ring = Node3D.new()
	_ring.name = "LandingRing"
	add_child(_ring)
	_ring.position = Vector3(0, float(prof["top_h"]) + float(prof["ring_up"]), 0)
	var r := ring_radius()
	var tm := TorusMesh.new()
	tm.inner_radius = r - 1.4
	tm.outer_radius = r + 1.4
	tm.rings = 72
	tm.ring_segments = 10
	_ring_mat = glow_material(Color(1.0, 0.8, 0.36), 3.0)
	var torus := MeshInstance3D.new()
	torus.mesh = tm
	torus.material_override = _ring_mat
	torus.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ring.add_child(torus)
	# faint disc: reads as a landing zone from above
	var disc := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r - 1.0
	cm.bottom_radius = r - 1.0
	cm.height = 0.2
	cm.radial_segments = 48
	disc.mesh = cm
	_ring_disc_mat = StandardMaterial3D.new()
	_ring_disc_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ring_disc_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ring_disc_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_ring_disc_mat.albedo_color = Color(1.0, 0.8, 0.36, 0.1)
	disc.material_override = _ring_disc_mat
	disc.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ring.add_child(disc)


func _build_pillar() -> void:
	_pillar = MeshInstance3D.new()
	_pillar.name = "Pillar"
	var cm := CylinderMesh.new()
	cm.top_radius = 7.0
	cm.bottom_radius = 7.0
	cm.height = PILLAR_H
	cm.cap_top = false
	cm.cap_bottom = false
	cm.radial_segments = 24
	cm.rings = 1
	_pillar.mesh = cm
	var sh := Shader.new()
	sh.code = PILLAR_SHADER
	var m := ShaderMaterial.new()
	m.shader = sh
	m.set_shader_parameter("height", PILLAR_H)
	_pillar.material_override = m
	_pillar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_pillar.position = Vector3(0, float(prof["top_h"]) + PILLAR_H * 0.5, 0)
	add_child(_pillar)


func _build_storm() -> void:
	if island_id == &"home" or island_id == &"cyclops":
		return   # never locked
	_storm = MeshInstance3D.new()
	_storm.name = "StormWall"
	var cm := CylinderMesh.new()
	cm.top_radius = storm_radius()
	cm.bottom_radius = storm_radius()
	cm.height = STORM_H
	cm.cap_top = false
	cm.cap_bottom = false
	cm.radial_segments = 72
	cm.rings = 4
	_storm.mesh = cm
	var sh := Shader.new()
	sh.code = STORM_SHADER
	_storm_mat = ShaderMaterial.new()
	_storm_mat.shader = sh
	_storm_mat.set_shader_parameter("height", STORM_H)
	_storm_mat.render_priority = 1   # after the sea (transparent, writes depth): the sea no longer paints over the wall
	# only the outside faces render (cull_back): from outside the far side no longer blends over the near side;
	# Pegasus is always pushed out of the wall, so the inside is never seen
	_storm.material_override = _storm_mat
	_storm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_storm.position = Vector3(0, STORM_H * 0.5 - 8.0, 0)
	add_child(_storm)
	_storm_bolt = Node3D.new()      # where the thunder sound comes from (no light: see the crater note)
	add_child(_storm_bolt)


# ------------------------------------------------------------------ static helpers (shared by the world scenes)
static func _ring_noise(a: float, s: float) -> float:
	return 0.55 * sin(a * 3.0 + s) + 0.3 * sin(a * 7.0 + s * 2.3) + 0.15 * sin(a * 13.0 + s * 4.1)


static func _hash(i: int, k: int, s: float) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(k) * 78.233 + s * 3.7) * 43758.5453, 1.0)


## Adds a triangle whose outward side is given by the right-hand rule (b - a) x (c - a)
## (Godot treats clockwise as the front face, so the vertices go in as a, c, b).
static func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
	st.add_vertex(a)
	st.add_vertex(c)
	st.add_vertex(b)


## Emits a wall between rings ordered top -> bottom (each ring = points at increasing angle); faces point outward.
static func _wall(st: SurfaceTool, rings: Array) -> void:
	for k in rings.size() - 1:
		var up: PackedVector3Array = rings[k]
		var dn: PackedVector3Array = rings[k + 1]
		var n := up.size()
		for i in n:
			var j := (i + 1) % n
			_tri(st, up[i], dn[i], up[j])
			_tri(st, up[j], dn[i], dn[j])


## A rocky plateau island: a flat top of radius ~top_r at height top_h and faceted cliffs flaring out to base_r at
## base_y (below the waterline). Two surfaces: top (top_col) and cliffs (side_col), toon shaded, no outline.
static func plateau_mesh(top_r: float, base_r: float, top_h: float, base_y: float, s: float, top_col: Color, side_col: Color, segs := 56, rows := 5) -> MeshInstance3D:
	var rim := PackedFloat32Array()
	var rim2 := PackedFloat32Array()
	for i in segs:
		var a := TAU * float(i) / float(segs)
		rim.append(1.0 + 0.07 * _ring_noise(a, s))
		rim2.append(1.0 + 0.10 * _ring_noise(a, s + 1.9))
	var top := SurfaceTool.new()
	top.begin(Mesh.PRIMITIVE_TRIANGLES)
	var centre := Vector3(0, top_h, 0)
	for i in segs:
		var j := (i + 1) % segs
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(j) / float(segs)
		var p0 := Vector3(sin(a0) * top_r * rim[i], top_h, cos(a0) * top_r * rim[i])
		var p1 := Vector3(sin(a1) * top_r * rim[j], top_h, cos(a1) * top_r * rim[j])
		_tri(top, centre, p0, p1)
	top.generate_normals()
	var side := SurfaceTool.new()
	side.begin(Mesh.PRIMITIVE_TRIANGLES)
	side.set_smooth_group(-1)
	var rings := []
	for k in rows + 1:
		var t := float(k) / float(rows)
		var ring := PackedVector3Array()
		for i in segs:
			var a := TAU * float(i) / float(segs)
			var r := lerpf(top_r * rim[i], base_r * rim2[i], t * t * 0.7 + t * 0.3)
			var y := lerpf(top_h, base_y, t)
			if k > 0 and k < rows:
				r += (_hash(i, k, s) - 0.5) * 3.2
				y += (_hash(i + 101, k, s) - 0.5) * 1.6
			ring.append(Vector3(sin(a) * r, y, cos(a) * r))
		rings.append(ring)
	_wall(side, rings)
	side.generate_normals()
	var mesh := top.commit()
	side.commit(mesh)
	var mi := MeshInstance3D.new()
	mi.name = "IslandBody"
	mi.mesh = mesh
	mi.set_surface_override_material(0, CharacterVisual.make_toon(top_col, null, 0.0, 0.05))
	mi.set_surface_override_material(1, CharacterVisual.make_toon(side_col, null, 0.0, 0.12))
	return mi


## A volcano cone (concave profile) from base_r at base_y up to a crater rim of crater_r at `peak`, with an inner
## crater wall. Local origin = the cone axis at sea level.
static func cone_mesh(base_r: float, crater_r: float, peak: float, base_y: float, s: float, col: Color, inner_col: Color, segs := 48, rows := 10) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var rings := []
	for k in rows + 1:
		var t := float(k) / float(rows)            # 0 = rim, 1 = base
		var ring := PackedVector3Array()
		for i in segs:
			var a := TAU * float(i) / float(segs)
			var r := crater_r + (base_r - crater_r) * t * t
			var y := lerpf(peak, base_y, t)
			if k > 0 and k < rows:
				r *= 1.0 + 0.06 * _ring_noise(a + t, s)
				r += (_hash(i, k, s) - 0.5) * 2.0
			ring.append(Vector3(sin(a) * r, y, cos(a) * r))
		rings.append(ring)
	_wall(st, rings)
	st.generate_normals()
	var inner := SurfaceTool.new()
	inner.begin(Mesh.PRIMITIVE_TRIANGLES)
	var lip := PackedVector3Array()
	var floor_ring := PackedVector3Array()
	for i in segs:
		var a := TAU * float(i) / float(segs)
		lip.append(Vector3(sin(a) * crater_r, peak, cos(a) * crater_r))
		floor_ring.append(Vector3(sin(a) * crater_r * 0.72, peak + float(VOLCANO["lava_y"]) - 0.5, cos(a) * crater_r * 0.72))
	_wall(inner, [floor_ring, lip])   # bottom -> top: faces point inward
	inner.generate_normals()
	var mesh := st.commit()
	inner.commit(mesh)
	var mi := MeshInstance3D.new()
	mi.name = "Volcano"
	mi.mesh = mesh
	mi.set_surface_override_material(0, CharacterVisual.make_toon(col, null, 0.0, 0.12))
	mi.set_surface_override_material(1, CharacterVisual.make_toon(inner_col, null, 0.0, 0.0))
	return mi


## The painted sky of the open-air world scenes (home + sea): a deep zenith blue, a light but not white horizon and
## thin distance fog, so the islands keep their colour and silhouette at 500 m (play-test: the old near-white
## horizon band + fog 0.00045-0.0006 washed them out). Returns the Environment.
const SKY_TOP := Color(0.05, 0.23, 0.64)
const SKY_HORIZON := Color(0.53, 0.72, 0.90)
const SKY_BOTTOM := Color(0.28, 0.52, 0.68)
const SKY_FOG := Color(0.60, 0.76, 0.91)
const SKY_CLOUDS := 0.2            ## painted cloud streaks (0.45 before: they whitened the band above the horizon;
                                   ## the 3D cloud banks of build_clouds carry the clouds now)


static func world_sky(parent: Node, fog_density: float) -> Environment:
	var env := EnvKit.sky(parent, SKY_TOP, SKY_HORIZON, SKY_BOTTOM, 0.34, SKY_CLOUDS)
	env.fog_density = fog_density
	env.fog_light_color = SKY_FOG
	return env


## A lit material that glows (emission) - rings, lava, beacons.
static func glow_material(col: Color, energy := 3.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.emission_enabled = true
	m.emission = col
	m.emission_energy_multiplier = energy
	m.roughness = 1.0
	return m


## Kept for old callers: a looping sound owned by `parent` through the Sfx loop helper. Returns the Sfx loop id
## (0 when missing). `volume_db` is an offset from the level in assets/audio/audio.json. New code: call Sfx.loop().
static func make_loop(parent: Node, sound: String, volume_db := 0.0) -> int:
	return Sfx.loop(sound, parent, volume_db)


## Hides the hero health panel of a Hud (no fight here) through core's Hud.set_health_visible.
static func hide_hud_health(hud: Node) -> void:
	if hud != null and hud.has_method("set_health_visible"):
		hud.call("set_health_visible", false)
		return
	var bar = hud.get("_hp_bar")
	if bar is Control and (bar as Control).get_parent() != null and (bar as Control).get_parent().get_parent() is Control:
		((bar as Control).get_parent().get_parent() as Control).visible = false


## The rider's hips bone: [Skeleton3D, bone index] (first bone named *hip* / *pelvis*), or [null, -1] (stand-in).
static func find_hips(rider: Node3D) -> Array:
	for s in rider.find_children("*", "Skeleton3D", true, false):
		var skel := s as Skeleton3D
		for i in skel.get_bone_count():
			var bn := skel.get_bone_name(i).to_lower()
			if bn.contains("hip") or bn.contains("pelvis"):
				return [skel, i]
		return [null, -1]
	return [null, -1]


## Places `rider` (a child of `mount`, same facing) so its hips sit on the mount's `saddle` socket.
## `hips` = find_hips(rider). Shared by the flight and the home mount beat, so both seat the rider the same way.
static func seat_rider(mount: CharacterVisual, rider: CharacterVisual, hips: Array) -> void:
	if mount == null or rider == null:
		return
	var sad := mount.socket(&"saddle")
	if sad == null:
		return
	var target := mount.to_local(sad.global_position)
	var h := Vector3(0, rider.height * RIDER_STANDIN_HIPS, 0)
	var skel = hips[0] if hips.size() == 2 else null
	if skel is Skeleton3D and is_instance_valid(skel) and int(hips[1]) >= 0:
		var sk := skel as Skeleton3D
		h = rider.to_local(sk.global_transform * sk.get_bone_global_pose(int(hips[1])).origin)
	rider.position = target - h


## The rider transform from the mount's manifest (`rider.offset`: the hercules scene root relative to the `saddle`
## socket node, Godot axes; art_src/chars/ride/ride_game.json gives the same seat from the saddle bone head), or null
## when the mount is a stand-in or its manifest has no rider block.
static func rider_offset(mount: CharacterVisual) -> Variant:
	if mount == null or mount.is_standin:
		return null
	var r: Dictionary = mount.manifest.get("rider", {})
	var o: Dictionary = r.get("offset", {})
	if not o.has("position"):
		return null
	var p: Array = o["position"]
	var rd: Array = o.get("rotation_degrees", [0.0, 0.0, 0.0])
	var rot := Vector3(deg_to_rad(float(rd[0])), deg_to_rad(float(rd[1])), deg_to_rad(float(rd[2])))
	return Transform3D(Basis.from_euler(rot), Vector3(float(p[0]), float(p[1]), float(p[2])))


## Seats `rider` on `mount`. Real models (both): the rider becomes a child of the mount's `saddle` socket with the
## manifest rider offset, so he rides the saddle bone (its bob and sway) with no per-frame code; returns true.
## Stand-ins: the rider becomes a child of the mount and the caller glues his hips with seat_rider() every frame;
## returns false.
static func mount_rider(mount: CharacterVisual, rider: CharacterVisual) -> bool:
	var off = rider_offset(mount)
	var sad: Node3D = mount.socket(&"saddle") if mount != null else null
	var parent: Node3D = mount
	var socketed := off != null and sad != null and not rider.is_standin
	if socketed:
		parent = sad
	if rider.get_parent() != parent:
		if rider.get_parent() != null:
			rider.get_parent().remove_child(rider)
		parent.add_child(rider)
	if socketed:
		rider.transform = off
	else:
		rider.transform = Transform3D.IDENTITY
	return socketed


## The AnimationPlayer inside a real CharacterVisual (null for stand-ins); used to phase the rider to the wing beat.
static func anim_player(v: CharacterVisual) -> AnimationPlayer:
	if v == null or v.is_standin:
		return null
	var ap = v.get("_anim")
	if ap is AnimationPlayer:
		return ap
	var found := v.find_children("*", "AnimationPlayer", true, false)
	return found[0] as AnimationPlayer if found.size() > 0 else null


## Rider playback for the clip the mount plays (pegasus manifest `rider` block): returns [speed, phase or -1].
## fly: speed rider_speed_on_fly x the fly playback rate and the ride clip phase locked to the fly clip
## (both t = 0 at the wing top: ride_pos = fmod(fly_pos / fly_beat_s, 1) * rider_clip_length_s); glide / idle: the
## glide speed, free-running (the seated pose is valid for any Pegasus clip).
static func rider_phase(mount: CharacterVisual, fly_rate: float) -> Array:
	var r: Dictionary = mount.manifest.get("rider", {}) if mount != null else {}
	var ride_len := float(r.get("rider_clip_length_s", 1.5))
	var beat := float(r.get("fly_beat_s", mount.clip_length(&"fly", 1.0417) if mount != null else 1.0417))
	if mount == null or mount.current_clip != &"fly":
		return [float(r.get("rider_speed_on_glide", 0.4)), -1.0]
	var speed := float(r.get("rider_speed_on_fly", ride_len / maxf(beat, 0.05))) * fly_rate
	var ap := anim_player(mount)
	if ap == null or not ap.is_playing():
		return [speed, -1.0]
	var pos := ap.current_animation_position
	return [speed, fmod(pos / maxf(beat, 0.05), 1.0) * ride_len]


## Applies rider_phase(): sets the rider's rate and, while Pegasus beats its wings, steers his ride clip onto the
## wing beat by running it a little faster or slower (catch-up in ~0.6 s, rate x0.5..x1.6) instead of seeking: a
## seek jumped the rider's pose by up to half a ride cycle whenever glide gave way to fly (integrate2_world).
static func sync_rider(mount: CharacterVisual, rider: CharacterVisual, fly_rate: float) -> void:
	if rider == null or mount == null or rider.current_clip != &"ride":
		return
	var ph := rider_phase(mount, fly_rate)
	var base := float(ph[0])
	var rate := base
	var want := float(ph[1])
	var ap := anim_player(rider)
	if want >= 0.0 and ap != null and ap.is_playing() and ap.current_animation_length > 0.0:
		var ride_len := ap.current_animation_length
		# signed phase error in clip seconds (> 0: the rider is behind the beat)
		var d := angle_difference(ap.current_animation_position / ride_len * TAU, want / ride_len * TAU) / TAU * ride_len
		if absf(d) > 1.0 / 48.0:
			rate = base + clampf(d / 0.6, -0.5 * base, 0.6 * base)
	if absf(rider.get_speed() - rate) > 0.001:
		rider.set_speed(rate)


## Compass word for a horizontal direction (-Z = north).
static func compass_word(dir: Vector3) -> String:
	var ang := fposmod(rad_to_deg(atan2(dir.x, -dir.z)), 360.0)
	var names := ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
	return names[int(round(ang / 45.0)) % 8]


## Big painted cloud banks (clusters of flattened toon spheres) above the flight ceiling, spread over the sea map.
## Pure scenery: no collision, no shadows. `sea_y` = the scene's sea level.
static func build_clouds(parent: Node3D, sea_y: float, count := 34, spread := 2400.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Clouds"
	parent.add_child(root)
	var r := RandomNumberGenerator.new()
	r.seed = 4242
	var mat_top := CharacterVisual.make_toon(Color(1.0, 0.99, 0.96), null, 0.0, 0.35)
	var mat_low := CharacterVisual.make_toon(Color(0.86, 0.89, 0.96), null, 0.0, 0.25)
	var sm := SphereMesh.new()
	sm.radius = 1.0
	sm.height = 2.0
	sm.radial_segments = 14
	sm.rings = 7
	for i in count:
		var c := Vector3(r.randf_range(-spread, spread), sea_y + r.randf_range(175.0, 260.0), r.randf_range(-spread - 600.0, spread - 600.0))
		var size := r.randf_range(35.0, 80.0)
		for k in r.randi_range(5, 8):
			var mi := MeshInstance3D.new()
			mi.mesh = sm
			var s := size * r.randf_range(0.45, 1.0)
			mi.scale = Vector3(s * r.randf_range(1.2, 1.8), s * 0.55, s * r.randf_range(0.9, 1.3))
			mi.position = c + Vector3(r.randf_range(-1.2, 1.2) * size, r.randf_range(-0.1, 0.35) * size, r.randf_range(-0.8, 0.8) * size)
			mi.material_override = mat_low if mi.position.y < c.y else mat_top
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.add_child(mi)
	return root
