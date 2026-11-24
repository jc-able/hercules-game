extends Node3D
## Scene id "sea" (world module; loaded by path, no class_name): open water, painted sky, the four islands at the
## SPEC §4 coordinates (IslandProxy), and Pegasus flight (pegasus_flight.gd). opts: from = island id Pegasus starts
## near (default "home"), free_flight = true after the ending. Sea level is y = 0 here.
## When all three bosses are beaten and the ending card was not shown yet, the scene routes to "ending" at once
## (covers `--start=sea --defeated=all`); the ending scene comes back here with free_flight.

const IslandProxy := preload("res://scripts/world/island_proxy.gd")
const Flight := preload("res://scripts/world/pegasus_flight.gd")
const START_GAP := 55.0            ## metres outside the start island's ring where Pegasus appears
const NO_AUTO_LAND_TIME := 10.0    ## seconds the start island's ring lands on interact only

var opts: Dictionary = {}
var islands := {}                  ## id (String) -> IslandProxy node
var flight: Flight
var hud: Hud
var sea: MeshInstance3D
var env: Environment
var sea_y := 0.0
var _sea_step := 25.0
var _to_ending := false
var _probe := ""
var _probe_t := 0.0
var _probe_min := INF


## Called by Game before the scene enters the tree.
func setup(o: Dictionary) -> void:
	opts = o


func _ready() -> void:
	env = IslandProxy.world_sky(self, 0.0002)
	var sun := EnvKit.sun(self, Vector3(-42, -30, 0), Color(1.0, 0.94, 0.82), 1.05)
	sun.directional_shadow_max_distance = 220.0
	sea = EnvKit.sea(self, 6000.0, sea_y, 240)
	IslandProxy.build_clouds(self, sea_y)
	_sea_step = 6000.0 / 240.0
	for id in Tuning.ISLANDS:
		var prox := IslandProxy.new()
		prox.setup(StringName(id))
		prox.creature_enabled = not (Game.harness and Game.args.has("no-island-creatures"))   # feedback 2 (A/B flag)
		add_child(prox)
		prox.position = Tuning.ISLANDS[id] + Vector3(0, sea_y, 0)
		islands[String(id)] = prox
	hud = Hud.new()
	add_child(hud)
	IslandProxy.hide_hud_health(hud)
	flight = Flight.new()
	flight.world = self
	# free flight: after the ending card, and on every later flight once all three labors are won (mounting at home)
	flight.free_flight = bool(opts.get("free_flight", false)) or (Game.defeated_count() >= Tuning.UNLOCK_ORDER.size() and not Game.ending_pending())
	add_child(flight)
	_place_start()
	Game.capture_mouse(true)
	Sfx.play_music("music_flight")
	Sfx.loop("sea_loop", self, -5.0)    # the sea below Pegasus, under the wind
	if Game.ending_pending():
		_to_ending = true
		flight.frozen = true
		Game.event("ending_route", {"from": opts.get("from", "hydra")})
		Game.goto(&"ending", {"from": String(opts.get("from", "hydra"))})
		return
	var target := next_target()
	if flight.free_flight:
		hud.show_title_card("The Open Sea", "The labors are done. Fly where you like.", 3.0)
	else:
		hud.show_title_card("The Open Sea", "Fly to %s" % islands[String(target)].title(), 2.6)
		if Game.defeated_count() == 0:
			_combat_hint()
	Game.event("flight_start", {"from": String(opts.get("from", "home")), "target": target, "free": flight.free_flight})
	if Game.harness and Game.args.has("world-probe"):
		_start_probe(String(Game.args["world-probe"]))


func wants_mouse_captured() -> bool:
	return true


## The island the player should fly to next: the first undefeated one in unlock order, else home.
func next_target() -> StringName:
	for id in Tuning.UNLOCK_ORDER:
		if not bool(Game.defeated.get(String(id), false)):
			return id
	return &"home"


## First flight to the first labor: the fight controls once, after the title card (the home sign's back lists them
## too), so a player who skipped the Controls page reaches the Cyclops knowing how to strike, block, roll and lock on.
func _combat_hint() -> void:
	get_tree().create_timer(3.2, false).timeout.connect(func() -> void:
		if is_inside_tree() and Game.world == self and not flight.landing:
			flight.show_hint("For the fight:  {attack} strike    {shield} shield (hold)    {roll} roll    {lock_on} lock on", 7.0)
			Game.event("combat_hint"))


## Metres the flight keeps above island surfaces (pegasus_flight CLEARANCE).
func pegasus_clearance() -> float:
	return float(Flight.CLEARANCE)


## Pegasus starts just outside the ring of the island it came from, facing the next open island.
func _place_start() -> void:
	var from := String(opts.get("from", "home"))
	if not islands.has(from):
		from = "home"
	var src = islands[from]
	var dst = islands[String(next_target())]
	var dir := Vector3(dst.global_position.x - src.global_position.x, 0, dst.global_position.z - src.global_position.z)
	if flight.free_flight:
		# free flight: start facing away from home, out over the open sea (the compass target is home, but nothing
		# pulls Pegasus back there; home itself: north, toward the other islands)
		var home = islands["home"]
		dir = Vector3(src.global_position.x - home.global_position.x, 0, src.global_position.z - home.global_position.z)
	if dir.length() < 1.0:
		dir = Vector3(0, 0, -1)
	dir = dir.normalized()
	# the ring Pegasus starts beside never auto-lands in the first seconds (it only takes interact then)
	flight.no_auto_land_island = StringName(from)
	flight.no_auto_land_until = NO_AUTO_LAND_TIME
	var rc: Vector3 = src.ring_center()
	var pos: Vector3 = rc + dir * (float(src.ring_radius()) + START_GAP)
	if src.ground_height(pos) - src.global_position.y > src.top_height() + 20.0:
		# that side is the hydra's volcano (free flight faces north from it): start a quarter turn round, over open sea
		dir = Vector3(-dir.z, 0, dir.x)
		pos = rc + dir * (float(src.ring_radius()) + START_GAP)
	pos.y = maxf(pos.y, src.ground_height(pos) + 12.0)
	flight.place(pos, atan2(dir.x, dir.z))
	# take-off beat: Pegasus climbs away from the island it just left (home mount, arena victory, ending)
	if not Game.ending_pending():
		flight.take_off(maxf(src.ground_height(pos) + pegasus_clearance(), sea_y + Tuning.FLY_MIN_HEIGHT))


func _process(delta: float) -> void:
	if _probe != "":
		_tick_probe(delta)
	# the sea plane follows the camera (the water shader works in world space, so the move is invisible)
	var cam := get_viewport().get_camera_3d()
	if cam != null and sea != null:
		var c := cam.global_position
		sea.position = Vector3(snappedf(c.x, _sea_step), sea_y, snappedf(c.z, _sea_step))


## Fallback advisor (the flight node is in group "bot_advisor" and normally answers first).
func bot_advice() -> Dictionary:
	if _to_ending or flight == null:
		return {}
	return flight.bot_advice()


# ------------------------------------------------------------------ harness probes (world module self-tests)
## `--world-probe=storm`: Pegasus starts 150 m outside Medusa's storm (medusa locked), flying straight at it;
## `--world-probe=limit`: starts at 2150 m from the centre flying outward. Run with `--bot=idle` (no stick input).
## After 12 s prints `probe_result` with the closest approach (storm: must stay >= the storm radius; limit: the
## farthest distance must stay below ~2300 m).
func _start_probe(kind: String) -> void:
	_probe = kind
	if kind == "storm":
		var m = islands["medusa"]
		var r: float = m.storm_radius()
		var pos: Vector3 = m.global_position + Vector3(0, 60, r + 150.0)
		flight.place(pos, PI)          # flying north (-Z), straight at the island
		_probe_min = INF
	elif kind == "tour":
		flight.frozen = true
		_tour_step(0)
	elif kind == "seat":
		_probe_min = 0.0
	elif kind == "limit":
		flight.place(Vector3(0, 60, 2150), 0.0)   # flying south, away from the centre
		_probe_min = 0.0


## `--world-probe=seat`: every 0.25 s prints where the rider sits (his hips relative to the saddle socket, in the
## Pegasus visual's axes; his up / forward against Pegasus's), the Pegasus clip, and the ride clip phase against the
## wing-beat phase it should have (`phase_err` in seconds). Ends after 10 s with `probe_result` (worst values).
var _seat_next := 0.0
var _seat_worst := {"hips_err": 0.0, "phase_err": 0.0, "tilt_deg": 0.0}


func _tick_seat_probe() -> void:
	if _probe_t < _seat_next:
		return
	_seat_next = _probe_t + 0.25
	var peg: CharacterVisual = flight.visual
	var rider: CharacterVisual = flight.rider
	var sad := peg.socket(&"saddle")
	var hips := IslandProxy.find_hips(rider)
	var hip_rel := Vector3.ZERO
	if hips[0] is Skeleton3D:
		var sk := hips[0] as Skeleton3D
		var hw := sk.global_transform * sk.get_bone_global_pose(int(hips[1])).origin
		hip_rel = peg.global_transform.basis.inverse() * (hw - sad.global_position)
	var pb := peg.global_transform.basis.orthonormalized()
	var rb := rider.global_transform.basis.orthonormalized()
	var tilt := rad_to_deg(pb.y.angle_to(rb.y))
	var yaw_err := rad_to_deg(pb.z.angle_to(rb.z))
	var ph := IslandProxy.rider_phase(peg, peg.get_speed())
	var rap := IslandProxy.anim_player(rider)
	var rpos := rap.current_animation_position if rap != null else -1.0
	var perr := 0.0
	if float(ph[1]) >= 0.0 and rap != null:
		perr = absf(angle_difference(rpos / 1.5 * TAU, float(ph[1]) / 1.5 * TAU)) / TAU * 1.5
	_seat_worst["hips_err"] = maxf(_seat_worst["hips_err"], hip_rel.length())
	_seat_worst["phase_err"] = maxf(_seat_worst["phase_err"], perr)
	_seat_worst["tilt_deg"] = maxf(_seat_worst["tilt_deg"], maxf(tilt, yaw_err))
	Game.event("seat", {"clip": peg.current_clip, "peg_rate": snappedf(peg.get_speed(), 0.01),
		"rider_rate": snappedf(rider.get_speed(), 0.01), "ride_pos": snappedf(rpos, 0.001),
		"want": snappedf(float(ph[1]), 0.001), "phase_err": snappedf(perr, 0.001),
		"hips": "%.3f,%.3f,%.3f" % [hip_rel.x, hip_rel.y, hip_rel.z], "tilt": snappedf(tilt, 0.1),
		"yaw_err": snappedf(yaw_err, 0.1), "socketed": flight._socketed, "pitch": snappedf(rad_to_deg(flight.pitch), 0.1)})
	if _probe_t >= 10.0:
		Game.event("probe_result", {"probe": "seat", "hips_err": snappedf(_seat_worst["hips_err"], 0.001),
			"phase_err": snappedf(_seat_worst["phase_err"], 0.001), "tilt_deg": snappedf(_seat_worst["tilt_deg"], 0.1),
			"ok": _seat_worst["phase_err"] < 0.05})
		_probe = ""


## `--world-probe=tour`: parks Pegasus (frozen, hovering) in front of each island for 3 s (screenshots).
const TOUR := [["home", 140.0, 30.0, 200.0], ["cyclops", 150.0, 40.0, 30.0], ["medusa", 170.0, 45.0, 120.0], ["hydra", 260.0, 70.0, 210.0]]


func _tour_step(i: int) -> void:
	var row: Array = TOUR[i % TOUR.size()]
	var prox = islands[row[0]]
	var a := deg_to_rad(float(row[3]))
	var c: Vector3 = prox.global_position
	var pos := c + Vector3(sin(a), 0, cos(a)) * float(row[1]) + Vector3(0, float(row[2]), 0)
	var to := c - pos
	flight.place(pos, atan2(to.x, to.z))
	Game.event("tour", {"island": row[0]})


func _tick_probe(delta: float) -> void:
	_probe_t += delta
	if _probe == "tour":
		var step := int((_probe_t + 1.5) / 3.0)      # switches half-way between the 3 s screenshots
		if step != int((_probe_t - delta + 1.5) / 3.0):
			_tour_step(step)
		return
	if _probe == "seat":
		_tick_seat_probe()
		return
	var p := flight.global_position
	if _probe == "storm":
		_probe_min = minf(_probe_min, islands["medusa"].flat_distance(p))
	else:
		_probe_min = maxf(_probe_min, Vector2(p.x, p.z).length())
	if _probe_t >= 12.0:
		var r: float = islands["medusa"].storm_radius()
		var ok := _probe_min >= r - 0.5 if _probe == "storm" else _probe_min < 2320.0
		Game.event("probe_result", {"probe": _probe, "value": _probe_min, "storm_r": r, "ok": ok})
		_probe = ""
