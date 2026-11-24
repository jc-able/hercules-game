extends Node3D
## Pegasus flight (world module; loaded by path, no class_name). Hercules rides Pegasus over the sea map:
## left stick / WASD steer (x = yaw, y = pitch; stick up / W climbs unless INVERT_PITCH), boost (RT / Shift),
## auto-level, banking, wing-beat bob, speed lines + FOV kick while boosting, a compass strip that points at the
## islands. Height 12-140 m (and never into an island), soft world limit 2200 m, locked islands turn Pegasus away.
## Entering a landing ring slows Pegasus; interact lands at once, or it lands by itself after AUTO_LAND_TIME.
## The node itself is the mount: its position = Pegasus's feet, its +Z = the flight direction (like every model).
## `world` (the sea scene) provides: islands {id: IslandProxy}, hud (Hud), next_target(), sea_y.
## bot_advice() (group "bot_advisor") steers to the next open ring and lands, for `--bot=win`.

signal landed(island_id: StringName)

const IslandProxyScript := preload("res://scripts/world/island_proxy.gd")

const TURN_DEG := 70.0              ## yaw rate at full stick
const MAX_PITCH_DEG := 32.0
const BANK_DEG := 38.0
const PITCH_RESPONSE := 2.6
const ACCEL := 16.0                 ## m/s^2 toward the wanted speed
const RING_SPEED := 13.0            ## inside the TARGET landing ring (so the auto-land has time)
const AUTO_LAND_TIME := 1.5         ## target ring only; other rings land on interact
const WORLD_LIMIT := 2200.0
const CLEARANCE := 9.0              ## metres kept above island tops and their dressing
const HARD_CLEARANCE := 2.0         ## absolute minimum above the island surface (only if the soft rise lags)
const FLOOR_RISE := 20.0            ## m/s cap on the vertical push when under the floor
const LEVEL_BAND := 6.0             ## a dive eases out within this many metres above the floor
const LOOK_AHEAD_TIMES := [0.5, 1.0, 1.75, 2.5, 3.25]   ## seconds ahead sampled for rising ground
const CLIMB_MAX_DEG := 45.0         ## steepest automatic climb over rising ground (the volcano)
const CLIMB_RESPONSE := 5.0
const CAM_DIST := 6.0               ## behind Pegasus's feet (the pair spans ~1/3 of the frame, wing tips inside)
const CAM_HEIGHT := 4.2             ## above its feet: above the rider's head, looking a little down on the pair
const CAM_AIM_AHEAD := 120.0        ## metres ahead the camera looks (horizon above the rider)
const CAM_AIM_UP := 4.0
const CAM_FOV := 70.0
const CAM_FOV_BOOST := 78.0
const CAM_BOOST_DIST := 0.8         ## extra distance while boosting
const CAM_MOUSE_SENS := 0.0035      ## radians per pixel
const CAM_PAD_SPEED := 2.4          ## radians per second
const INVERT_PITCH := false         ## true = stick forward dives (aircraft style)
const FORCED_TURN_DEG := 150.0
const CAM_BANK := 0.1               ## share of Pegasus's bank the camera follows (feedback 2: 0.3 tilted the horizon 11 deg)
## feedback 2 (owner: "just use the left stick", "the panning around the horse needs to be fixed"): in flight the
## right stick and the mouse no longer orbit the camera. It sits behind Pegasus and follows its heading with a short,
## capped lag (turns show the banked horse a little from the side), so the pair never leaves the frame.
const CAM_YAW_RESPONSE := 3.5       ## 1/s: how fast the camera heading catches up with Pegasus's
const CAM_YAW_LAG_MAX_DEG := 14.0   ## the camera heading never trails Pegasus's by more than this
const CAM_PITCH_RESPONSE := 2.5     ## 1/s: smoothing of Pegasus's pitch for the camera
const CAM_LOOK_DOWN_DEG := 11.0     ## level flight: the camera looks this much down (pair in the lower-middle, horizon high)
const CAM_PITCH_FOLLOW := 0.35      ## share of Pegasus's pitch the camera's look follows (climbs and dives keep the pair in frame)
const CAM_PITCH_DROP := 0.45        ## share of Pegasus's pitch the camera drops behind (climb) / rises (dive)
const CAM_GROUND_CLEAR := 3.0       ## metres the camera keeps above island ground (landing on the volcano)
const TAKEOFF_TIME := 1.8           ## take-off climb when the sea scene starts beside an island
const TAKEOFF_PITCH_DEG := 18.0
const TAKEOFF_DROP := 9.0           ## the climb starts this much below the cruise height
const LAND_DELAY := 0.9             ## seconds of descent before the scene fade starts
const LAND_PITCH_DEG := -14.0
const CLIMB_FLY_DEG := 5.0          ## pitched up more than this: fly (wing beats)
const DIVE_GLIDE_DEG := -4.0        ## pitched down more than this: glide
const CRUISE_GLIDE := 3.0           ## level cruise: seconds of glide ...
const CRUISE_BEATS := 2             ## ... then this many fly beats
const CLIP_MIN_HOLD := 0.6

var world = null                    ## the sea scene (untyped: module scripts have no class_name)
var visual: CharacterVisual
var rider: CharacterVisual
var cam: Camera3D
var yaw := 0.0                      ## radians; flight direction (sin yaw, 0, cos yaw)
var pitch := 0.0                    ## radians; > 0 climbs
var roll := 0.0
var speed := Tuning.FLY_SPEED
var frozen := false                 ## hover in place, no input (ending pending, scripted beats)
var landing := false
var boosting := false
var free_flight := false
var ring_island: StringName = &""
var ring_time := 0.0
var no_auto_land_island: StringName = &""   ## this ring lands on interact only until no_auto_land_until
var no_auto_land_until := 0.0               ## flight clock seconds (_clock)

var _clock := 0.0
var _look_yaw := 0.0
var _look_pitch := 0.0
var _look_idle := 10.0
var _forced_left := 0.0
var _forced_yaw := 0.0
var _msg_cd := {}
var _anim_key := ""
var _flap_t := 0.0
var _boost_k := 0.0
var _cam_pos := Vector3.ZERO
var _cam_off := Vector3.ZERO
var _cam_snap := true
var _cam_yaw := 0.0                  # smoothed heading the camera sits behind (feedback 2)
var _cam_pitch := 0.0                # smoothed pitch for the camera
var _hips: Array = [null, -1]       ## IslandProxy.find_hips(rider)
var _wind := 0                       # Sfx loop id of the wind (0 = none)
var _overlay: FlightOverlay
var _socketed := false               # rider parented to the saddle socket (real models)
var _peg_anim: AnimationPlayer = null
var _fly_pos_last := 0.0
var _clip_hold := 0.0                # seconds the current clip has been held (no flicker)
var _cruise_t := 0.0                 # level cruise: glide, then a few wing beats, repeat
var _takeoff := 0.0                  # seconds of take-off climb left
var _wanted_speed := Tuning.FLY_SPEED


func _ready() -> void:
	name = "PegasusFlight"
	add_to_group("bot_advisor")
	# harness only: `--world-glb=<dir>` loads pegasus.glb / hercules.glb (+ <id>_clips.json) from a folder, to check
	# the saddle fit with real rigs before they are in res://assets
	var glb_dir := str(Game.args.get("world-glb", "")) if Game.harness else ""
	if glb_dir != "":
		visual = CharacterVisual.create_from_file(&"pegasus", glb_dir.path_join("pegasus.glb"), glb_dir.path_join("pegasus_clips.json"))
		rider = CharacterVisual.create_from_file(&"hercules", glb_dir.path_join("hercules.glb"), glb_dir.path_join("hercules_clips.json"))
	else:
		visual = CharacterVisual.create(&"pegasus")
		rider = CharacterVisual.create(&"hercules")
	add_child(visual)
	rider.name = "Rider"
	# real models: child of the saddle socket with the manifest rider offset; stand-ins: hips glued every frame
	_socketed = IslandProxyScript.mount_rider(visual, rider)
	rider.attach_prop(&"hand_r", "res://assets/props/sword.glb")
	rider.attach_prop(&"forearm_l", "res://assets/props/shield.glb")
	rider.play(&"ride", 0.0)
	_hips = IslandProxyScript.find_hips(rider)
	_peg_anim = IslandProxyScript.anim_player(visual)
	cam = Camera3D.new()
	cam.name = "FlightCamera"
	cam.top_level = true
	cam.fov = CAM_FOV
	cam.near = 0.2
	cam.far = 6000.0
	add_child(cam)
	cam.current = true
	_overlay = FlightOverlay.new()
	_overlay.flight = self
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	layer.add_child(_overlay)
	_wind = Sfx.loop("wind_loop", self, -8.0)
	_play_anim()


## Puts Pegasus at `pos` flying along `yaw_rad` and snaps the camera behind.
func place(pos: Vector3, yaw_rad: float) -> void:
	global_position = pos
	yaw = yaw_rad
	pitch = 0.0
	roll = 0.0
	rotation = Vector3(0, yaw, 0)
	_takeoff = 0.0
	_cam_snap = true
	_update_camera(0.016)


## Take-off from an island (sea scene start): Pegasus starts TAKEOFF_DROP lower and slower, nose up, beating its
## wings, and climbs to the cruise height; the stick still steers. `floor_y` = lowest allowed start height.
func take_off(floor_y: float) -> void:
	global_position.y = maxf(global_position.y - TAKEOFF_DROP, floor_y)
	pitch = deg_to_rad(TAKEOFF_PITCH_DEG)
	speed = Tuning.FLY_SPEED * 0.5
	_takeoff = TAKEOFF_TIME
	_anim_key = ""                   # wing beats at once (no clip hold)
	_play_anim()
	rotation = Vector3(-pitch, yaw, 0)
	_cam_snap = true
	_update_camera(0.016)
	Sfx.play("wing_flap", null, -3.0)
	Game.event("take_off", {"y": snappedf(global_position.y, 0.1)})


func forward() -> Vector3:
	return Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))


func flat_forward() -> Vector3:
	return Vector3(sin(yaw), 0, cos(yaw))


# ------------------------------------------------------------------ input
## feedback 2: the mouse no longer orbits the flight camera (left stick / WASD do everything in flight).
func _unhandled_input(_e: InputEvent) -> void:
	pass


# ------------------------------------------------------------------ frame
func _physics_process(delta: float) -> void:
	_clock += delta
	if world == null:
		return
	if frozen or landing:
		speed = move_toward(speed, 0.0 if frozen else 11.0, ACCEL * delta)
		pitch = lerpf(pitch, 0.0 if frozen else deg_to_rad(LAND_PITCH_DEG), 1.0 - exp(-3.0 * delta))
		roll = lerpf(roll, 0.0, 1.0 - exp(-3.0 * delta))
		global_position += forward() * speed * delta
		rotation = Vector3(-pitch, yaw, roll)
		_animate(delta)
		_update_camera(delta)
		return
	var inp := Controls.get_move()
	boosting = Input.is_action_pressed("boost")
	var steer_x := inp.x
	var steer_y := -inp.y if INVERT_PITCH else inp.y
	_check_limits()
	var turn_dir := -steer_x
	if _forced_left > 0.0:
		_forced_left -= delta
		var before := yaw
		yaw = rotate_toward(yaw, _forced_yaw, deg_to_rad(FORCED_TURN_DEG) * delta)
		turn_dir = signf(angle_difference(before, yaw)) if absf(angle_difference(before, yaw)) > 0.0001 else 0.0
		steer_y = 0.0
	else:
		yaw += -steer_x * deg_to_rad(TURN_DEG) * delta
	yaw = wrapf(yaw, -PI, PI)
	var target_pitch := -steer_y * deg_to_rad(MAX_PITCH_DEG)
	var pitch_resp := PITCH_RESPONSE
	# look ahead: rising ground (island slopes, dressing, the volcano) pitches Pegasus up early instead of
	# lifting it straight up when it gets there; it wins over the stick while it is needed
	var climb := _ahead_climb_pitch()
	if climb > 0.0 and climb > target_pitch:     # (climb is 0 over flat sea: it must not cancel a dive)
		target_pitch = climb
		pitch_resp = CLIMB_RESPONSE
	if _takeoff > 0.0:
		# take-off: nose up while the climb lasts, easing to the stick's pitch at the end
		_takeoff -= delta
		target_pitch = maxf(target_pitch, deg_to_rad(TAKEOFF_PITCH_DEG) * clampf(_takeoff / (TAKEOFF_TIME * 0.5), 0.0, 1.0))
	pitch = lerpf(pitch, target_pitch, 1.0 - exp(-pitch_resp * delta))
	roll = lerpf(roll, -turn_dir * deg_to_rad(BANK_DEG), 1.0 - exp(-4.0 * delta))
	# landing rings: only the current target's ring slows Pegasus and lands by itself; any other ring (a beaten
	# island, home before the ending) lands on interact only, so flying through one is quick and harmless
	var ring := _ring_at(global_position)
	var target: StringName = world.next_target()
	if ring != ring_island:
		ring_island = ring
		ring_time = 0.0
		if ring != &"":
			world.hud.show_prompt(_ring_prompt(ring, ring == target))
			Game.event("ring_enter", {"island": ring, "target": ring == target})
		else:
			world.hud.show_prompt("")
	var wanted := Tuning.FLY_BOOST if boosting else Tuning.FLY_SPEED
	if ring != &"":
		ring_time += delta
		if ring == target:
			wanted = RING_SPEED
		var auto_ok := ring == target and ring_time >= AUTO_LAND_TIME
		if ring == no_auto_land_island and _clock < no_auto_land_until:
			auto_ok = false          # the ring Pegasus just took off from never pulls him straight back down
		if Input.is_action_just_pressed("interact") or auto_ok:
			_land(ring)
	_wanted_speed = wanted
	speed = move_toward(speed, wanted, (ACCEL * 1.8 if wanted < speed else ACCEL) * delta)
	# move, then keep inside the height band and above the islands
	var p := global_position + forward() * speed * delta
	var sea_min: float = float(world.sea_y) + Tuning.FLY_MIN_HEIGHT
	var floor_h := maxf(sea_min, _ground(p) + CLEARANCE)
	var gap := p.y - floor_h
	if gap < LEVEL_BAND and pitch < 0.0:
		# ease the dive out as the floor comes near
		pitch = lerpf(pitch, 0.0, (1.0 - exp(-8.0 * delta)) * clampf(1.0 - gap / LEVEL_BAND, 0.0, 1.0))
	if gap < 0.0:
		p.y = move_toward(p.y, floor_h, FLOOR_RISE * delta)
	# hard limits: never below the SPEC minimum over the sea, never inside an island body
	p.y = maxf(p.y, sea_min)
	p.y = maxf(p.y, _ground(p) + HARD_CLEARANCE)
	var ceil_h: float = world.sea_y + Tuning.FLY_MAX_HEIGHT
	if p.y > ceil_h:
		p.y = ceil_h
		if pitch > 0.0:
			pitch = lerpf(pitch, 0.0, 1.0 - exp(-8.0 * delta))
	global_position = _push_out_of_storms(p)
	rotation = Vector3(-pitch, yaw, roll)
	_animate(delta)
	_update_camera(delta)


func _process(_delta: float) -> void:
	_follow_saddle()
	# ride in phase with the wing beat (pegasus manifest `rider` block); fly plays x1.25 while boosting
	IslandProxyScript.sync_rider(visual, rider, visual.get_speed())


## Island id whose landing ring holds `p`, or &"".
func _ring_at(p: Vector3) -> StringName:
	for id in world.islands:
		if world.islands[id].in_ring(p):
			return StringName(id)
	return &""


## Prompt shown inside a landing ring. The target ring also lands by itself after AUTO_LAND_TIME.
func _ring_prompt(id: StringName, is_target: bool) -> String:
	var t := String(world.islands[String(id)].title())
	if is_target:
		return "{interact} Land  -  %s" % t
	if id == &"home":
		return "{interact} Land  -  %s" % t
	return "{interact} Land  -  replay the labor  (%s)" % t


## Pitch (radians, > 0) needed to clear the ground a little ahead with CLEARANCE, or 0 when nothing rises ahead.
func _ahead_climb_pitch() -> float:
	var pos := global_position
	var fwd := flat_forward()
	var best := 0.0
	for t in LOOK_AHEAD_TIMES:
		var dist := maxf(speed, 10.0) * float(t)
		var need := _ground(pos + fwd * dist) + CLEARANCE - pos.y
		if need > 0.0:
			best = maxf(best, atan2(need, dist))
	return minf(best, deg_to_rad(CLIMB_MAX_DEG))


## Highest island surface under `p` (sea level when over open water).
func _ground(p: Vector3) -> float:
	var g: float = world.sea_y
	for id in world.islands:
		var prox = world.islands[id]
		if prox.flat_distance(p) < 260.0:
			g = maxf(g, prox.ground_height(p))
	return g


## Storm walls of locked islands and the world limit turn Pegasus away (with a message).
func _check_limits() -> void:
	var fwd := flat_forward()
	var pos := global_position
	for id in world.islands:
		var prox = world.islands[id]
		if prox.state != "locked":
			continue
		var d: float = prox.flat_distance(pos)
		if d > prox.storm_radius() + 45.0:
			continue
		var out := Vector3(pos.x - prox.global_position.x, 0, pos.z - prox.global_position.z).normalized()
		if fwd.dot(out) < 0.35:
			if _forced_left <= 0.0:
				Game.event("storm_turn", {"island": id, "dist": d})
			_forced_yaw = atan2(out.x, out.z)
			_forced_left = 1.4
			var i := Tuning.UNLOCK_ORDER.find(StringName(id))
			var need := String(world.islands[String(Tuning.UNLOCK_ORDER[i - 1])].title()) if i > 0 else "another island"
			_message("storm_" + String(id), "A storm walls off %s. Return when %s is won." % [prox.title(), need])
	var flat := Vector2(pos.x, pos.z)
	if flat.length() > WORLD_LIMIT:
		var inward := Vector3(-pos.x, 0, -pos.z).normalized()
		if fwd.dot(inward) < 0.5:
			if _forced_left <= 0.0:
				Game.event("world_limit", {"dist": flat.length()})
			_forced_yaw = atan2(inward.x, inward.z)
			_forced_left = 1.4
			_message("limit", "Only empty sea that way. Pegasus turns back.")


func _push_out_of_storms(p: Vector3) -> Vector3:
	for id in world.islands:
		var prox = world.islands[id]
		if prox.blocks(p):
			var c: Vector3 = prox.global_position
			var out := Vector3(p.x - c.x, 0, p.z - c.z)
			if out.length() < 0.01:
				out = Vector3(0, 0, 1)
			out = out.normalized() * prox.storm_radius()
			p = Vector3(c.x + out.x, p.y, c.z + out.z)
	return p


func _message(key: String, text: String) -> void:
	if Game.time < float(_msg_cd.get(key, -100.0)):
		return
	_msg_cd[key] = Game.time + 6.0
	show_hint(text, 3.5)


## A message line under the compass strip (the Hud toast sits on top of the strip in flight). `text` may hold
## {action} placeholders: they follow the device in use while it shows.
func show_hint(text: String, seconds := 3.5) -> void:
	if _overlay != null:
		_overlay.hint = text
		_overlay.hint_left = seconds


func _land(id: StringName) -> void:
	if landing:
		return
	landing = true
	world.hud.show_prompt("")
	Game.event("land", {"island": id})
	Sfx.play("land")
	landed.emit(id)
	# landing beat: Pegasus folds into a glide and descends toward the island for LAND_DELAY, then the fade
	var dest: StringName = &"home" if id == &"home" else id
	# a pause-menu choice made during the glide (Quit to title / Return home) starts its own scene switch: the
	# landing must then give way, or its goto would be queued after the menu's and win (latest wins)
	get_tree().create_timer(LAND_DELAY, false).timeout.connect(func() -> void:
		if is_inside_tree() and not Game.is_switching() and Game.world == world:
			Game.goto(dest, {"from": "sea"}))


# ------------------------------------------------------------------ look
func _animate(delta: float) -> void:
	_play_anim(delta)
	# no code bob: fly v2 carries its own 8 cm body bob (peak at clip t 0.625) and the rider rides the saddle bone
	visual.position.y = 0.0
	if visual.current_clip == &"fly":
		# one wing_flap per downstroke, phased from the clip itself (t = 0 = wing top = start of the downstroke)
		var pos := _flap_t
		if _peg_anim != null and _peg_anim.is_playing():
			pos = _peg_anim.current_animation_position
		else:
			var beat := visual.clip_length(&"fly", 1.0417) / maxf(visual.get_speed(), 0.1)
			_flap_t = fmod(_flap_t + delta, beat)
			pos = _flap_t
		if pos < _fly_pos_last:
			Sfx.play("wing_flap", null, -6.0, randf_range(0.95, 1.05))   # level set in audio.json; -6 under the wind
		_fly_pos_last = pos
	else:
		_fly_pos_last = 0.0
	var wanted_boost := 1.0 if (boosting and not frozen and not landing) else 0.0
	_boost_k = move_toward(_boost_k, wanted_boost, delta * 2.5)
	Sfx.set_loop_volume(_wind, lerpf(-12.0, 3.0, clampf((speed - 10.0) / 36.0, 0.0, 1.0)))   # dB around the audio.json level


## fly (wing beats) while boosting, climbing, taking off, speeding up or hovering; glide while descending or
## landing; level cruise alternates CRUISE_GLIDE s of glide with CRUISE_BEATS wing beats. A clip is held at least
## CLIP_MIN_HOLD s so small stick moves do not flicker between the two.
func _play_anim(delta := 0.0) -> void:
	_clip_hold += delta
	var fly_len := visual.clip_length(&"fly", 1.0417)
	var clip := &"glide"
	if frozen:
		clip = &"fly"
	elif landing:
		clip = &"glide"
	elif boosting or _takeoff > 0.0 or pitch > deg_to_rad(CLIMB_FLY_DEG) or speed < _wanted_speed - 3.0:
		clip = &"fly"
		_cruise_t = 0.0
	elif pitch < deg_to_rad(DIVE_GLIDE_DEG):
		clip = &"glide"
		_cruise_t = 0.0
	else:
		_cruise_t += delta
		var cycle := CRUISE_GLIDE + fly_len * CRUISE_BEATS
		clip = &"fly" if fmod(_cruise_t, cycle) >= CRUISE_GLIDE else &"glide"
	var rate := 1.25 if (boosting and clip == &"fly") else 1.0
	var key := "%s_%s" % [clip, rate]
	if key == _anim_key:
		return
	var urgent := frozen or landing or _anim_key == ""
	var same_clip := visual.current_clip == clip and _anim_key != ""
	if not urgent and not same_clip and _clip_hold < CLIP_MIN_HOLD:
		return
	if same_clip:
		# same clip, new rate (boost on / off): re-time it without restarting the beat
		visual.set_speed(rate)
		_anim_key = key
		return
	_anim_key = key
	_clip_hold = 0.0
	visual.play(clip, 0.35, rate)


## Stand-ins only: keeps the rider's hips on Pegasus's saddle socket (the rider is a child of the Pegasus visual,
## same facing). Real models ride the socket itself (IslandProxy.mount_rider), so nothing is done here.
func _follow_saddle() -> void:
	if not _socketed:
		IslandProxyScript.seat_rider(visual, rider, _hips)


func _update_camera(delta: float) -> void:
	# feedback 2: no right-stick / mouse orbit. The camera sits behind Pegasus on a smoothed heading (capped lag) and
	# looks along that heading a little down, so the pair stays centred left-right and in the lower-middle of the
	# frame through turns, climbs, dives, the take-off and the landing glide.
	if _cam_snap:
		_cam_yaw = yaw
		_cam_pitch = pitch
		_cam_snap = false
	else:
		_cam_yaw = wrapf(_cam_yaw + angle_difference(_cam_yaw, yaw) * (1.0 - exp(-CAM_YAW_RESPONSE * delta)), -PI, PI)
		_cam_pitch = lerpf(_cam_pitch, pitch, 1.0 - exp(-CAM_PITCH_RESPONSE * delta))
	var lag := angle_difference(yaw, _cam_yaw)
	var lag_max := deg_to_rad(CAM_YAW_LAG_MAX_DEG)
	if absf(lag) > lag_max:
		_cam_yaw = wrapf(yaw + signf(lag) * lag_max, -PI, PI)
	var side_view := Game.harness and Game.args.has("world-cam-yaw")
	var cy := _cam_yaw
	if side_view:
		# harness only: hold the camera at a fixed orbit angle (side views of the rider and the wings)
		cy = yaw + deg_to_rad(float(Game.args["world-cam-yaw"]))
	var lp := clampf(-_cam_pitch * CAM_PITCH_DROP, -0.6, 0.6)
	var dist := CAM_DIST + _boost_k * CAM_BOOST_DIST
	var offset := Basis(Vector3.UP, cy) * Vector3(0, CAM_HEIGHT + sin(lp) * dist, -cos(lp) * dist)
	_cam_off = offset
	_cam_pos = global_position + offset
	if world != null:
		_cam_pos.y = maxf(_cam_pos.y, float(world.sea_y) + 1.5)
		_cam_pos.y = maxf(_cam_pos.y, _ground(_cam_pos) + CAM_GROUND_CLEAR)
	cam.global_position = _cam_pos
	if side_view:
		var aim := global_position + Vector3.UP * 2.0     # harness side views look at the pair itself
		if cam.global_position.distance_to(aim) > 0.1:
			cam.look_at(aim, Vector3.UP)
	else:
		var look_p := deg_to_rad(-CAM_LOOK_DOWN_DEG) + _cam_pitch * CAM_PITCH_FOLLOW
		var dir := Vector3(sin(cy) * cos(look_p), sin(look_p), cos(cy) * cos(look_p))
		cam.look_at(_cam_pos + dir, Vector3.UP)
		# lean into the bank a little (camera local +Z points back, so the sign flips)
		cam.rotate_object_local(Vector3(0, 0, 1), -roll * CAM_BANK)
	cam.fov = lerpf(CAM_FOV, CAM_FOV_BOOST, _boost_k)


# ------------------------------------------------------------------ bot
## Steers toward the next open island's ring (height included), boosts when lined up and far, lands inside.
func bot_advice() -> Dictionary:
	if world == null or frozen or landing or Game.is_switching():
		return {}
	var target: StringName = world.next_target()
	var prox = world.islands.get(String(target))
	if prox == null:
		return {}
	if ring_island == target:
		return {"interact": true, "stick": Vector2.ZERO}
	var c: Vector3 = prox.ring_center()
	var to := Vector3(c.x - global_position.x, 0, c.z - global_position.z)
	var err := flat_forward().signed_angle_to(to.normalized(), Vector3.UP)   # > 0 = target to the left
	var dy := c.y - global_position.y
	var sy := clampf(-dy / 12.0, -1.0, 1.0)
	if INVERT_PITCH:
		sy = -sy
	return {"stick": Vector2(clampf(-err * 2.5, -1.0, 1.0), sy), "boost": absf(err) < 0.35 and to.length() > 220.0}


# ------------------------------------------------------------------ overlay: compass strip + speed lines
class FlightOverlay extends Control:
	var flight = null             # the PegasusFlight node
	var hint := ""                # message line under the compass (show_hint)
	var hint_left := 0.0
	var _streaks: Array = []      # [angle, phase, length]

	func _ready() -> void:
		set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		var r := RandomNumberGenerator.new()
		r.seed = 77
		for i in 30:
			_streaks.append([r.randf() * TAU, r.randf(), r.randf_range(60.0, 160.0)])

	func _process(delta: float) -> void:
		for s in _streaks:
			s[1] = fmod(s[1] + delta * 1.6, 1.0)
		hint_left = maxf(hint_left - delta, 0.0)
		queue_redraw()

	func _draw() -> void:
		if flight == null or flight.world == null:
			return
		_draw_streaks()
		_draw_compass()
		_draw_hint()

	func _draw_hint() -> void:
		if hint_left <= 0.0 or hint == "":
			return
		var a := clampf(hint_left / 0.5, 0.0, 1.0)
		var font := ThemeDB.fallback_font
		var text := Controls.fill(hint)
		var y := 22.0 + 100.0
		var w := 1100.0
		var x := size.x * 0.5 - w * 0.5
		draw_rect(Rect2(size.x * 0.5 - 420.0, y - 26.0, 840.0, 38.0), Color(0.05, 0.04, 0.03, 0.45 * a))
		draw_string(font, Vector2(x + 1.5, y + 1.5), text, HORIZONTAL_ALIGNMENT_CENTER, w, 22, Color(0, 0, 0, 0.7 * a))
		draw_string(font, Vector2(x, y), text, HORIZONTAL_ALIGNMENT_CENTER, w, 22, Color(UiStyle.TEXT, a))

	func _draw_streaks() -> void:
		var k: float = flight._boost_k
		if k <= 0.02:
			return
		var c := size * 0.5
		var rad := size.length() * 0.5
		for s in _streaks:
			var dir := Vector2(cos(s[0]), sin(s[0]))
			var r0: float = lerpf(rad * 0.35, rad * 1.05, s[1])
			var a: float = k * 0.55 * sin(PI * float(s[1]))
			draw_line(c + dir * r0, c + dir * (r0 + float(s[2])), Color(1, 1, 1, a), 2.0, true)

	func _draw_compass() -> void:
		var font := ThemeDB.fallback_font
		var w := 680.0
		var cx := size.x * 0.5
		var top := 22.0
		var half_deg := 70.0
		draw_rect(Rect2(cx - w * 0.5 - 12.0, top - 6.0, w + 24.0, 44.0), Color(0.05, 0.04, 0.03, 0.45))
		var fwd: Vector3 = flight.flat_forward()
		var bearing := rad_to_deg(atan2(fwd.x, -fwd.z))
		for deg in range(0, 360, 15):
			var rel := wrapf(float(deg) - bearing, -180.0, 180.0)
			if absf(rel) > half_deg:
				continue
			var x := cx + rel / half_deg * w * 0.5
			var major := deg % 90 == 0
			draw_line(Vector2(x, top + 26.0), Vector2(x, top + (8.0 if major else 18.0)), Color(0.97, 0.93, 0.85, 0.9 if major else 0.5), 2.0)
			if major:
				var letter: String = ["N", "E", "S", "W"][deg / 90]
				draw_string(font, Vector2(x - 20.0, top + 4.0), letter, HORIZONTAL_ALIGNMENT_CENTER, 40.0, 20, UiStyle.GOLD)
		var target: StringName = flight.world.next_target()
		var info := ""
		var p: Vector3 = flight.global_position
		for id in flight.world.islands:
			var prox = flight.world.islands[id]
			var d := Vector3(prox.global_position.x - p.x, 0, prox.global_position.z - p.z)
			var rel := wrapf(rad_to_deg(atan2(d.x, -d.z)) - bearing, -180.0, 180.0)
			var col := Color(1.0, 0.80, 0.36)
			match String(prox.state):
				"home":
					col = Color(0.62, 0.86, 1.0)
				"defeated":
					col = Color(0.85, 0.85, 0.82)
				"locked":
					col = Color(0.45, 0.40, 0.55)
			var is_target: bool = StringName(id) == target
			var x := cx + clampf(rel, -half_deg, half_deg) / half_deg * w * 0.5
			var y := top + 17.0
			var s := 9.0 if is_target else 6.0
			if absf(rel) > half_deg:
				var dirx := signf(rel)
				var tri := PackedVector2Array([Vector2(x + dirx * 14.0, y), Vector2(x, y - s), Vector2(x, y + s)])
				draw_colored_polygon(tri, col)
			else:
				var dia := PackedVector2Array([Vector2(x, y - s), Vector2(x + s, y), Vector2(x, y + s), Vector2(x - s, y)])
				draw_colored_polygon(dia, col)
				draw_polyline(PackedVector2Array([dia[0], dia[1], dia[2], dia[3], dia[0]]), Color(0, 0, 0, 0.7), 1.5)
			if is_target:
				info = "%s   %d m" % [prox.title(), int(d.length())]
		if info != "":
			var label := ("Free flight  -  " if flight.free_flight else "") + info
			draw_string(font, Vector2(cx - 300.0 + 1.5, top + 64.0 + 1.5), label, HORIZONTAL_ALIGNMENT_CENTER, 600.0, 22, Color(0, 0, 0, 0.7))
			draw_string(font, Vector2(cx - 300.0, top + 64.0), label, HORIZONTAL_ALIGNMENT_CENTER, 600.0, 22, UiStyle.TEXT)
