extends Node3D
## Scene id "home" (world module; loaded by path, no class_name): the home plateau, ~47 m across, 14 m above the
## sea. Temple on the south rim facing north, three trophy pedestals in front of it (a trophy per beaten boss),
## olive trees, cypresses, amphorae, two braziers, a low wall round the edge, a sign with the next goal + controls,
## and Pegasus waiting on the grass. Hercules (normal Player, free camera) spawns in front of the temple looking
## north, where the three islands lie on the horizon (IslandProxy, same coordinates as the sea map).
## Interact near Pegasus -> short mount beat -> Game.goto("sea", {from = "home"}).
## Layout (metres, plateau top y = 0, -Z = north): see docs/notes/world.md.

const IslandProxy := preload("res://scripts/world/island_proxy.gd")
const SEA_Y := -14.0               ## the sea level under the plateau (= home island top_h in the sea scene)
const RIM_R := 23.5                ## plateau rim radius
const WALL_R := 21.6               ## low wall (visual) radius; the invisible boundary sits just inside it
const SPAWN := Vector3(0, 0.1, -4.0)
const PEGASUS_POS := Vector3(5.5, 0, -10.5)
const PEGASUS_YAW := -90.0         ## faces west: broadside to the hero walking up from the south
const MOUNT_OFFSET := Vector3(0, 0, 1.75)   ## the spot beside Pegasus the hero walks to (south side)
const INTERACT_DIST := 3.2
const PEDESTALS := {"cyclops": Vector3(-6.0, 0, 2.6), "medusa": Vector3(0.0, 0, 3.4), "hydra": Vector3(6.0, 0, 2.6)}
const SIGN_POS := Vector3(-4.0, 0, -5.5)
const MOUNT_HOP := 1.05            ## step, spring, swing over, settle (feedback 2: _mount_path; 0.9 in-out read as a snap)
const MOUNT_HOP_H := 0.75          ## arc height of the hop
const MOUNT_RIDE_BLEND := 0.3      ## the rider eases into `ride` from the spring (MOUNT_RIDE_AT) on: the leg swings over
const MOUNT_RIDE_AT := 0.3         ## hop fraction at which `ride` starts (the step before it plays the hero's idle)
const MOUNT_WINGS_AT := 0.55       ## re-fix: the wings stay FOLDED (idle) through the step and spring (the rider is
								   ## beside the flank, clear of them) and open as he swings over the back
const MOUNT_WINGS_OPEN := 0.35     ## the wings rise out of the folded idle to spread level (glide wings; legs keep standing)
const MOUNT_FLY_FROM := 0.3        ## seated: the beat starts at this fly time (wings near level, going down)
const WING_SPREAD_CLIP := &"glide" ## re-fix: wings spread LEVEL around the mount / dismount (a raised wing hid the rider)
const MOUNT_FLY_BLEND := 0.4       ## seated: the whole body joins the wing beat (legs tuck) before the lift
const MOUNT_SETTLE := 0.35         ## seated, wings beating, before the lift
const LAND_TIME := 1.9             ## arrival from the sea: Pegasus glides in and touches down beside the path
const LAND_FROM := Vector3(0, 4.5, -7.0)    ## landing start relative to its spot (up, and behind along its facing)
const DISMOUNT_WAIT := 0.3         ## landed: Pegasus settles into the idle (legs) before the rider hops off
const DISMOUNT_HOP := 0.85         ## the mirror of the mount hop: saddle -> the grass beside Pegasus
const DISMOUNT_HOP_H := 0.55       ## arc height of the hop down
const DISMOUNT_RIDE_BLEND := 0.5   ## the rider eases from `ride` into the hero's idle over the hop
const DISMOUNT_WINGS_AT := 0.12    ## hop fraction at which the spread wings start to fold (he is rising off the back)
const DISMOUNT_WINGS_CLOSE := 0.45 ## the wings fold back into the idle (done before he comes down beside the flank)
const DISMOUNT_CAM_TIME := DISMOUNT_WAIT + DISMOUNT_HOP   ## the camera eases from the landing view to the chase view
const MOUNT_LIFT := 1.6            ## take-off climb (the scene fade starts at 60 % of it)
const LIFT_TO := Vector3(0, 6.5, 9.0)       ## lift: up + ahead along Pegasus's facing
const LIFT_PITCH_DEG := 16.0
const MOUNT_CAM_BACK := 7.0        ## mount camera: behind and above the pair, like the flight camera
const MOUNT_CAM_UP := 3.4

var opts: Dictionary = {}
var player: Player
var hud: Hud
var pegasus_root: Node3D
var pegasus: CharacterVisual
var _sign_label: Label3D
var _trophy_nodes := {}
var _flames: Array[MeshInstance3D] = []
var _mounting := false
var _mount_rider: CharacterVisual = null
var _mount_hips: Array = [null, -1]
var _mount_t := -1.0               # seconds since the mount began (-1 = not mounting)
var _mount_from := Transform3D.IDENTITY
var _mount_seated := false
var _mount_socketed := false
var _mount_cam: Camera3D = null
var _mount_cam_from := Transform3D.IDENTITY   # the chase camera when the mount began
var _mount_cam_off := Vector3.ZERO            # camera offset from Pegasus when the rider sat down
var _mount_ride_started := false
var _mount_wings_open := false
var _wing_overlay: WingOverlay = null
var _landing_t := -1.0             # arrival from the sea: seconds into the touch-down beat (-1 = none)
var _land_rider: CharacterVisual = null      # arrival from the sea: the hero seated on Pegasus until he hops off
var _land_hips: Array = [null, -1]
var _land_socketed := false
var _land_wings: WingOverlay = null           # holds the wings up (fly beat) from the flare through the hop off
var _dismount_t := -1.0            # seconds since Pegasus touched down with the rider (-1 = none)
var _dismount_hop := false
var _dismount_from := Transform3D.IDENTITY
var _dismount_cam: Camera3D = null
var _dismount_cam_from := Transform3D.IDENTITY
var _sign_back: Label3D
var _near := false
var _clock := 0.0


## Called by Game before the scene enters the tree.
func setup(o: Dictionary) -> void:
	opts = o


func _ready() -> void:
	IslandProxy.world_sky(self, 0.00025)
	var sun := EnvKit.sun(self, Vector3(-42, -30, 0), Color(1.0, 0.94, 0.82), 1.05)
	sun.directional_shadow_max_distance = 70.0
	sun.shadow_bias = 0.2
	sun.shadow_normal_bias = 2.5
	EnvKit.sea(self, 6000.0, SEA_Y, 240)
	IslandProxy.build_clouds(self, SEA_Y)
	_build_plateau()
	_build_props()
	_build_trophies()
	_build_sign()
	_build_pegasus()
	# harness `--home-from=sea`: `--start=home` arrives as if flown home (the landing + dismount beat, quick to record)
	var from_sea := String(opts.get("from", "")) == "sea" or (Game.harness and str(Game.args.get("home-from", "")) == "sea")
	if from_sea and str(Game.args.get("world-probe", "")) == "":
		_start_landing()
	for id in ["cyclops", "medusa", "hydra"]:
		var prox := IslandProxy.new()
		prox.setup(StringName(id))
		add_child(prox)
		var p: Vector3 = Tuning.ISLANDS[id]
		prox.position = Vector3(p.x, SEA_Y, p.z)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	player.global_position = SPAWN
	player.facing = Vector3(0, 0, -1)
	player.camera.snap_behind()
	if _land_rider != null and player.visual != null:
		# he flies in on Pegasus (the rider): the walking hero appears only when the rider has hopped off
		player.visual.visible = false
		player.set_control(false)
	hud = Hud.new()
	add_child(hud)
	hud.bind_player(player)
	IslandProxy.hide_hud_health(hud)
	Game.capture_mouse(true)
	Sfx.play_music("music_title")
	Sfx.loop("sea_loop", self)
	if Game.defeated_count() > 0:
		# a chime from the trophy pedestals as the hero arrives (one per visit)
		get_tree().create_timer(1.6, false).timeout.connect(func() -> void:
			if is_inside_tree():
				var c := Vector3.ZERO
				for id in PEDESTALS:
					c += PEDESTALS[id] / float(PEDESTALS.size())
				Sfx.play("trophy", c + Vector3(0, 1.4, 0)))
	Game.progress_changed.connect(_refresh_progress)
	Controls.device_changed.connect(func(_p: bool): _refresh_sign())
	var t: Array = Tuning.ISLAND_TITLES["home"]
	hud.show_title_card(t[0], _goal_line(), 3.0)
	Game.event("home_ready", {"next": _next_island()})
	if Game.harness and str(Game.args.get("world-probe", "")) == "trophies":
		# harness self-test view: the hero turns to the temple and the trophy pedestals
		player.global_position = Vector3(0, 0.1, -3.0)
		player.facing = Vector3(0, 0, 1)
		player.camera.snap_behind()


func wants_mouse_captured() -> bool:
	return true


func _physics_process(delta: float) -> void:
	_clock += delta
	for i in _flames.size():
		var k := 1.0 + 0.10 * sin(_clock * 11.0 + i * 2.0) + 0.06 * sin(_clock * 23.0 + i)
		_flames[i].scale = Vector3(1.0 / k, k, 1.0 / k)
	if _mounting or player == null or _landing_t >= 0.0 or _dismount_t >= 0.0:
		return
	var near :=_flat(player.global_position - PEGASUS_POS).length() < INTERACT_DIST
	if near != _near:
		_near = near
		hud.show_prompt("{interact} Fly" if near else "")
	if near and player.control_enabled and Input.is_action_just_pressed("interact"):
		_mount()


func _mount() -> void:
	_mounting = true
	hud.show_prompt("")
	player.set_control(false)
	Game.event("mount")
	Sfx.play("mount")
	Sfx.play("neigh", PEGASUS_POS + Vector3.UP * 2.0)
	# the idle folds the wings where the rider's legs go (natural_pegasus.md): they stay folded while he steps in and
	# springs up beside the flank, and spread level as he swings over the back (_open_wings at MOUNT_WINGS_AT), on the
	# wing bones only, so the hooves stay planted until the rider is seated (WingOverlay)
	_wing_overlay = null
	_mount_wings_open = false
	# the rider (a second hercules visual) starts exactly where the walking hero stands, in the hero's own clip at the
	# same clip time (same pose on screen, no pop), eases into `ride` over the hop (the first frame of _process) and
	# hops onto the saddle (MOUNT_HOP); then it rides the saddle socket with the pegasus manifest rider offset, the
	# same seat as in flight (IslandProxy.mount_rider), Pegasus beats its wings and lifts off under a chase camera
	var rider := CharacterVisual.create(&"hercules")
	rider.name = "Rider"
	add_child(rider)
	rider.global_transform = player.visual.global_transform
	rider.attach_prop(&"hand_r", "res://assets/props/sword.glb")
	rider.attach_prop(&"forearm_l", "res://assets/props/shield.glb")
	var pv := player.visual
	if pv != null and pv.current_clip != &"" and rider.has_clip(pv.current_clip):
		rider.play(pv.current_clip, 0.0, pv.get_speed(), pv.clip_position())
	_mount_ride_started = false
	player.visual.visible = false
	_mount_rider = rider
	_mount_hips = IslandProxy.find_hips(rider)
	_mount_from = rider.global_transform
	_mount_t = 0.0
	var cur := get_viewport().get_camera_3d()
	_mount_cam = Camera3D.new()
	_mount_cam.name = "MountCamera"
	_mount_cam.top_level = true
	_mount_cam.fov = cur.fov if cur != null else 70.0
	_mount_cam.near = 0.1
	_mount_cam.far = 6000.0
	add_child(_mount_cam)
	if cur != null:
		_mount_cam.global_transform = cur.global_transform
	_mount_cam_from = _mount_cam.global_transform
	_mount_cam.current = true


## Where the rider sits on the saddle (global): the saddle socket x the manifest rider offset (real models), else
## the stand-in hips rule (socket minus the stand-in hips height, Pegasus's facing).
func _seat_transform() -> Transform3D:
	var sad := pegasus.socket(&"saddle")
	var off = IslandProxy.rider_offset(pegasus)
	if off != null and not _mount_rider.is_standin:
		return sad.global_transform * (off as Transform3D)
	var b := pegasus.global_transform.basis.orthonormalized()
	return Transform3D(b, sad.global_position - b.y * _mount_rider.height * IslandProxy.RIDER_STANDIN_HIPS)


func _process(delta: float) -> void:
	if _landing_t >= 0.0:
		_tick_landing(delta)
	elif _dismount_t >= 0.0:
		_tick_dismount(delta)
	if _land_rider != null and not _dismount_hop:
		if not _land_socketed:
			IslandProxy.seat_rider(pegasus, _land_rider, _land_hips)
		IslandProxy.sync_rider(pegasus, _land_rider, pegasus.get_speed())
	if _mount_rider == null or _mount_t < 0.0:
		return
	_mount_t += delta
	var mu := _mount_t / MOUNT_HOP
	if _mount_t - delta <= 0.0 and _mount_rider.current_clip != &"idle" and _mount_rider.has_clip(&"idle"):
		# one frame after the rider appeared in the hero's pose: he stops (walk -> idle) for the step and the crouch
		_mount_rider.play(&"idle", 0.2)
	if not _mount_ride_started and mu >= MOUNT_RIDE_AT:
		# the spring: the legs gather and swing over the back with the arc of the path
		_mount_ride_started = true
		_mount_rider.play(&"ride", MOUNT_RIDE_BLEND)
	if not _mount_wings_open and not _mount_seated and mu >= MOUNT_WINGS_AT:
		_mount_wings_open = true
		_open_wings()
	if _mount_t < MOUNT_HOP:
		_mount_rider.global_transform = _mount_path(_mount_from, _seat_transform(), _mount_t / MOUNT_HOP)
	elif not _mount_seated:
		_mount_seated = true
		_mount_socketed = IslandProxy.mount_rider(pegasus, _mount_rider)
		if not _mount_socketed:
			IslandProxy.seat_rider(pegasus, _mount_rider, _mount_hips)
		Game.event("mount_seated", {"socketed": _mount_socketed, "t": snappedf(_mount_t, 0.01)})
		_body_joins_beat()
		if pegasus_root != null and _mount_cam != null:
			_mount_cam_off = _mount_cam.global_position - pegasus_root.global_position
		Sfx.play("wing_flap", pegasus.global_position, -3.0)
		var fwd := pegasus_root.global_transform.basis.z
		var to := PEGASUS_POS + Vector3(0, LIFT_TO.y, 0) + fwd * LIFT_TO.z
		var tw := create_tween()
		tw.tween_interval(MOUNT_SETTLE)
		tw.tween_property(pegasus_root, "position", to, MOUNT_LIFT).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(pegasus, "rotation:x", -deg_to_rad(LIFT_PITCH_DEG), MOUNT_LIFT * 0.5)
		get_tree().create_timer(MOUNT_SETTLE + MOUNT_LIFT * 0.6, false).timeout.connect(func() -> void:
			# a pause-menu choice during the lift (Quit to title) switches scenes itself: do not queue the sea after it
			if is_inside_tree() and not Game.is_switching() and Game.world == self:
				Game.goto(&"sea", {"from": "home"}))
	elif not _mount_socketed:
		IslandProxy.seat_rider(pegasus, _mount_rider, _mount_hips)
	if _mount_seated:
		IslandProxy.sync_rider(pegasus, _mount_rider, pegasus.get_speed())
	_update_mount_camera(delta)


## feedback 2 (owner: "the animation of getting on and off the horse can be improved"; the old hop was one in-out
## blend that read as a 0.2 s snap). The mount as three beats on one path, u = 0..1 over MOUNT_HOP:
## step (0-0.25): a step in toward the flank on the grass with a small crouch; spring (0.25-0.6): up fast to above the
## saddle while the body turns to Pegasus's facing (he rises beside the flank first, so he never passes through it);
## swing over (0.45-0.9): across into the seat, dropping onto it; settle (0.9-1): a small give in the seat.
func _mount_path(from: Transform3D, to: Transform3D, u: float) -> Transform3D:
	# re-fix (review: "floats up, no crouch shows, ground to seat in 0.17 s"): the crouch is 0.2 m and held in idle,
	# the rise to the seat height is spread over u 0.2-0.7 (~0.5 s), the swing in over the back over u 0.5-0.92
	u = clampf(u, 0.0, 1.0)
	var h := 0.3 * smoothstep(0.0, 0.25, u) + 0.7 * smoothstep(0.5, 0.92, u)
	var p := from.origin.lerp(to.origin, h)
	var v := smoothstep(0.2, 0.7, u)                               # rise to the seat height
	p.y = lerpf(from.origin.y, to.origin.y, v)
	p.y -= 0.2 * sin(PI * clampf(u / 0.34, 0.0, 1.0))              # crouch before the spring (deepest at u 0.17)
	p.y += MOUNT_HOP_H * sin(PI * clampf((u - 0.3) / 0.62, 0.0, 1.0))    # over the back
	p.y -= 0.06 * sin(PI * clampf((u - 0.92) / 0.08, 0.0, 1.0))    # settle
	var b := from.basis.orthonormalized().slerp(to.basis.orthonormalized(), smoothstep(0.2, 0.75, u))
	return Transform3D(b, p)


## The reverse (dismount), u = 0..1 over DISMOUNT_HOP: rise out of the seat and swing the leg over (0-0.35, he lifts
## above the back before moving out), out and down beside the flank (0.25-0.85), land with a small knee give (0.85-1).
func _dismount_path(from: Transform3D, to: Transform3D, u: float) -> Transform3D:
	u = clampf(u, 0.0, 1.0)
	var h := smoothstep(0.2, 0.85, u)
	var p := from.origin.lerp(to.origin, h)
	p.y = lerpf(from.origin.y, to.origin.y, smoothstep(0.35, 0.85, u))
	p.y += DISMOUNT_HOP_H * sin(PI * clampf(u / 0.75, 0.0, 1.0))
	p.y -= 0.1 * sin(PI * clampf((u - 0.85) / 0.15, 0.0, 1.0))
	var b := from.basis.orthonormalized().slerp(to.basis.orthonormalized(), smoothstep(0.2, 0.8, u))
	return Transform3D(b, p)


## Mount beat camera. Hop: a small move from the hero's chase camera (back 1.0 m, up 0.6 m) that turns to keep the
## hop and the saddle in frame. Seated: keeps its offset from Pegasus as it lifts and eases round to behind and above
## the pair, looking along its facing (the flight camera's view, where the sea scene starts).
func _update_mount_camera(delta: float) -> void:
	if _mount_cam == null:
		return
	var b := pegasus_root.global_transform.basis
	var p := pegasus_root.global_position
	var behind := -b.z * MOUNT_CAM_BACK + Vector3.UP * MOUNT_CAM_UP
	var want: Vector3
	var aim: Vector3
	var k := 1.0 - exp(-3.0 * delta)
	var seat := p + Vector3.UP * 2.0
	if not _mount_seated:
		var u := smoothstep(0.0, 1.0, clampf(_mount_t / MOUNT_HOP, 0.0, 1.0))
		# a small push in toward the saddle (1.2 m) and up (1.3 m; feedback 2: 0.4 m left the raised near wing in front
		# of the rider as he sat down): the hop fills more of the frame and is seen a little from above
		var to_seat := (seat - _mount_cam_from.origin)
		to_seat.y = 0.0
		want = _mount_cam_from.origin + to_seat.normalized() * (1.2 * u) + Vector3.UP * (1.3 * u)
		var from_aim := _mount_cam_from.origin - _mount_cam_from.basis.z * 8.0
		aim = from_aim.lerp(seat, u * 0.85)
		k = 1.0 - exp(-10.0 * delta)
	else:
		# take-off seen from where the camera stands: it rides along with Pegasus and turns at most 45 deg toward
		# behind the pair (a full swing to behind crossed close to the wings in 1 s); the sea scene's own chase
		# camera starts behind after the fade
		var s := smoothstep(0.0, 1.0, clampf((_mount_t - MOUNT_HOP) / (MOUNT_SETTLE + MOUNT_LIFT * 0.6), 0.0, 1.0))
		var a0 := atan2(_mount_cam_off.x, _mount_cam_off.z)
		var a1 := atan2(behind.x, behind.z)
		var a := a0 + clampf(angle_difference(a0, a1), -PI * 0.25, PI * 0.25) * s
		var l0 := Vector2(_mount_cam_off.x, _mount_cam_off.z).length()
		var l := lerpf(l0, maxf(l0, 8.0), s)
		# re-fix: rises 2.2 m (was 1.0) so the take-off beat is seen over the near wing, not through it
		want = p + Vector3(sin(a) * l, _mount_cam_off.y + 2.2 * s, cos(a) * l)
		aim = seat.lerp(p + Vector3.UP * 2.0 + b.z * 3.0, s)
		k = 1.0 - exp(-8.0 * delta)
	_mount_cam.global_position = _mount_cam.global_position.lerp(want, k)
	var cur := _mount_cam.global_transform
	var look := cur.looking_at(aim, Vector3.UP)
	_mount_cam.global_transform = Transform3D(cur.basis.slerp(look.basis, k).orthonormalized(), cur.origin)


## Mount, step 1: the wings open into the fly beat on the wing bones only (real model), legs and body stay in the idle.
## Stand-ins have no skeleton to split: the whole body plays fly.
func _open_wings() -> void:
	_land_wings = null                       # an arrival's wings may still be folding: that overlay frees itself
	# re-fix: the wings spread LEVEL (glide wing pose, pair check 0 hits with the rider seated) instead of being held
	# at the top of the beat: from the mount-side camera the raised near wing hid the whole seated rider
	_wing_overlay = _make_wing_overlay(MOUNT_WINGS_OPEN, 0.0, WING_SPREAD_CLIP)
	if _wing_overlay == null:
		pegasus.play(&"fly", 0.3)
		return
	Game.event("mount_wings", {"bones": _wing_overlay.bone_count()})


## A WingOverlay playing Pegasus `fly` on the 12 wing bones (last modifier on its skeleton), or null for stand-ins.
func _make_wing_overlay(rise: float, from_t := 0.0, clip := &"fly") -> WingOverlay:
	var skel: Skeleton3D = null
	for s in pegasus.find_children("*", "Skeleton3D", true, false):
		skel = s as Skeleton3D
		break
	var ap := IslandProxy.anim_player(pegasus)
	var names = pegasus.get("_anim_names")
	var anim: Animation = null
	if ap != null and names is Dictionary:
		var key := String(clip) if (names as Dictionary).has(String(clip)) else "fly"
		if (names as Dictionary).has(key):
			anim = ap.get_animation(String(names[key]))
	if skel == null or anim == null:
		return null
	var ov := WingOverlay.new()
	ov.name = "WingOverlay"
	skel.add_child(ov)                       # last modifier: after the skeleton fade and the socket aims
	ov.setup(anim, skel, "wing_", rise)
	ov.t = from_t
	return ov


## Mount, step 2 (rider seated): the whole body takes up the beat at the wing overlay's phase (the wings do not jump),
## the legs tuck over MOUNT_FLY_BLEND, then the overlay goes (it and the clip show the same wing pose by then).
func _body_joins_beat() -> void:
	if _wing_overlay == null or not is_instance_valid(_wing_overlay):
		if pegasus.current_clip != &"fly":
			pegasus.play(&"fly", 0.3)
		return
	# re-fix: the beat starts near level going down (MOUNT_FLY_FROM) and the level-spread overlay eases out a little
	# slower than the body's crossfade, so the wings go from spread into the downstroke without dipping to folded
	pegasus.play(&"fly", MOUNT_FLY_BLEND, 1.0, MOUNT_FLY_FROM)
	var ov := _wing_overlay
	_wing_overlay = null
	ov.close(MOUNT_FLY_BLEND + 0.25)
	get_tree().create_timer(MOUNT_FLY_BLEND + 0.3, false).timeout.connect(func() -> void:
		if is_instance_valid(ov):
			ov.queue_free())


## Arrival from the sea (opts.from = "sea"): Pegasus glides down to its spot (LAND_TIME), flares with a few beats,
## and its legs reach for the grass and its wings fold as it settles into the idle. No mounting until it stands.
func _start_landing() -> void:
	_landing_t = 0.0
	pegasus.play(&"glide", 0.0)
	# the hero flew home on it: he stays seated (ride, in phase with the wing beat as in flight) until it stands
	var rider := CharacterVisual.create(&"hercules")
	rider.name = "Rider"
	_land_socketed = IslandProxy.mount_rider(pegasus, rider)
	rider.attach_prop(&"hand_r", "res://assets/props/sword.glb")
	rider.attach_prop(&"forearm_l", "res://assets/props/shield.glb")
	rider.play(&"ride", 0.0)
	_land_rider = rider
	_land_hips = IslandProxy.find_hips(rider)
	_tick_landing(0.0)


func _tick_landing(delta: float) -> void:
	_landing_t += delta
	var u := clampf(_landing_t / LAND_TIME, 0.0, 1.0)
	var e := 1.0 - pow(1.0 - u, 2.2)                          # ease out: fast in, soft touch-down
	var off := Vector3(0, LAND_FROM.y * (1.0 - e), 0) + pegasus_root.global_transform.basis.z * LAND_FROM.z * (1.0 - e)
	pegasus_root.position = PEGASUS_POS + off
	# nose up for the flare, level at the touch-down
	pegasus.rotation.x = -deg_to_rad(14.0) * sin(PI * clampf((u - 0.35) / 0.65, 0.0, 1.0))
	var prev := _landing_t - delta
	if prev < LAND_TIME * 0.45 and _landing_t >= LAND_TIME * 0.45:
		pegasus.play(&"fly", 0.35)                            # flare: wing beats to brake
		Sfx.play("wing_flap", pegasus_root.global_position, -3.0)
	if prev < LAND_TIME * 0.78 and _landing_t >= LAND_TIME * 0.78:
		# the idle folds the wings where the seated rider's legs are: while he is on, the wings keep the fly beat on
		# the wing bones (same clip time, no jump) and only the legs and body settle into the stance
		if _land_rider != null:
			# re-fix (review: the wings held at the top hid the rider for 0.55 s of the hop off): the wings ease from
			# the beat into a level spread (glide wing pose, clear of the seated rider) and fold as he rises off
			_land_wings = _make_wing_overlay(0.4, 0.0, WING_SPREAD_CLIP)
		pegasus.play(&"idle", 0.7)                            # legs reach down, (wings fold,) into the stance
	if u >= 1.0:
		pegasus_root.position = PEGASUS_POS
		pegasus.rotation.x = 0.0
		_landing_t = -1.0
		Game.event("pegasus_landed", {"rider": _land_rider != null})
		if _land_rider != null:
			_begin_dismount_camera()
			_dismount_t = 0.0


## Touch-down with the rider: the invisible hero is put on the grass beside Pegasus (the mount spot), facing away
## from the camera, and a beat camera eases from the landing view to his chase camera's view over the settle + hop
## (a push in of ~5 m); the chase camera takes over where it ends, so there is no cut.
func _begin_dismount_camera() -> void:
	var cur := get_viewport().get_camera_3d()
	var spot := _mount_spot() + Vector3(0, SPAWN.y, 0)
	var d := Vector3(0, 0, -1)
	if cur != null:
		var f := _flat(spot - cur.global_position)
		if f.length() > 0.5:
			d = f.normalized()
	player.global_position = spot
	player.facing = d
	player.camera.snap_behind()
	_dismount_cam = Camera3D.new()
	_dismount_cam.name = "DismountCamera"
	_dismount_cam.top_level = true
	_dismount_cam.fov = cur.fov if cur != null else Tuning.CAM_FOV
	_dismount_cam.near = 0.1
	_dismount_cam.far = 4000.0
	add_child(_dismount_cam)
	if cur != null:
		_dismount_cam.global_transform = cur.global_transform
	_dismount_cam_from = _dismount_cam.global_transform
	_dismount_cam.current = true


## Settle (DISMOUNT_WAIT), then the hop off: the mirror of the mount. The rider leaves the saddle socket, eases from
## `ride` into the hero's idle and hops in an arc onto the walking hero's spot and pose; the held wings fold once he
## is clear of them; then the walking hero replaces the rider (same clip, same clip time) and gets control.
func _tick_dismount(delta: float) -> void:
	_dismount_t += delta
	if _dismount_cam != null and player.camera != null and player.camera.cam != null:
		var c := smoothstep(0.0, 1.0, clampf(_dismount_t / DISMOUNT_CAM_TIME, 0.0, 1.0))
		_dismount_cam.global_transform = _dismount_cam_from.interpolate_with(player.camera.cam.global_transform, c)
	if _dismount_t < DISMOUNT_WAIT or _land_rider == null:
		return
	if not _dismount_hop:
		_dismount_hop = true
		var from := _land_rider.global_transform
		_land_rider.get_parent().remove_child(_land_rider)
		add_child(_land_rider)
		_land_rider.global_transform = from
		_dismount_from = from
		var clip := player.visual.current_clip if player.visual.current_clip != &"" else &"idle"
		_land_rider.play(clip, DISMOUNT_RIDE_BLEND)
		Game.event("dismount")
		Sfx.play("mount", PEGASUS_POS + Vector3.UP, -4.0)
	var u := clampf((_dismount_t - DISMOUNT_WAIT) / DISMOUNT_HOP, 0.0, 1.0)
	_land_rider.global_transform = _dismount_path(_dismount_from, player.visual.global_transform, u)
	if u >= DISMOUNT_WINGS_AT and _land_wings != null and is_instance_valid(_land_wings) and not _land_wings.closing:
		_land_wings.close(DISMOUNT_WINGS_CLOSE)
		var ref: WeakRef = weakref(_land_wings)
		get_tree().create_timer(DISMOUNT_WINGS_CLOSE + 0.05, false).timeout.connect(func() -> void:
			var ov: Object = ref.get_ref()
			if ov != null:
				ov.queue_free())
	if u >= 1.0:
		_end_dismount()


func _end_dismount() -> void:
	var pv := player.visual
	pv.visible = true
	if pv.current_clip == _land_rider.current_clip and pv.current_clip != &"":
		pv.play(pv.current_clip, 0.0, _land_rider.get_speed(), _land_rider.clip_position())
	_land_rider.queue_free()
	_land_rider = null
	if player.camera != null and player.camera.cam != null:
		player.camera.cam.current = true
	if _dismount_cam != null:
		_dismount_cam.queue_free()
		_dismount_cam = null
	_dismount_t = -1.0
	_dismount_hop = false
	player.set_control(true)
	Game.event("dismount_done")


## Bot (`--bot=win`): walk to the spot beside Pegasus, face it, interact.
func bot_advice() -> Dictionary:
	if _mounting or player == null or Game.is_switching() or _landing_t >= 0.0 or _dismount_t >= 0.0:
		return {}
	var spot := _mount_spot()
	var near := _flat(player.global_position - PEGASUS_POS).length() < INTERACT_DIST - 0.4
	return {"move_to": spot, "interact": near, "face": PEGASUS_POS}


func _mount_spot() -> Vector3:
	return PEGASUS_POS + MOUNT_OFFSET


func _flat(v: Vector3) -> Vector3:
	return Vector3(v.x, 0, v.z)


# ------------------------------------------------------------------ progress
func _next_island() -> StringName:
	for id in Tuning.UNLOCK_ORDER:
		if not bool(Game.defeated.get(String(id), false)):
			return id
	return &""


func _refresh_progress() -> void:
	_refresh_sign()
	for id in _trophy_nodes:
		(_trophy_nodes[id] as Node3D).visible = bool(Game.defeated.get(id, false))


## One line for the home title card: where to fly next.
func _goal_line() -> String:
	var nxt := _next_island()
	if nxt == &"":
		return "The labors are done. Fly where you like."
	var t: Array = Tuning.ISLAND_TITLES[String(nxt)]
	return "Next: %s, to the %s" % [t[0], IslandProxy.compass_word(Tuning.ISLANDS[String(nxt)])]


## Front face (toward the spawn): the next goal in three big lines. Back face: the controls.
func _refresh_sign() -> void:
	if _sign_label == null:
		return
	var nxt := _next_island()
	if nxt == &"":
		_sign_label.text = "LABORS DONE\nThe sea is yours"
	else:
		var t: Array = Tuning.ISLAND_TITLES[String(nxt)]
		_sign_label.text = "NEXT LABOR\n%s\nto the %s" % [t[0], IslandProxy.compass_word(Tuning.ISLANDS[String(nxt)])]
	if _sign_back != null:
		# travel block, then the fight block (the only place in play besides the first flight's hint that teaches it)
		_sign_back.text = Controls.fill("{move} move   {camera} look\n{interact} mount / land   {boost} fly faster\n\n{attack} strike   {shield} shield (hold)\n{roll} roll   {lock_on} lock on\n{pause} pause")


# ------------------------------------------------------------------ building
func _build_plateau() -> void:
	var body := StaticBody3D.new()
	body.name = "Plateau"
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = RIM_R + 2.0
	shape.height = 4.0
	cs.shape = shape
	cs.position.y = -2.0
	body.add_child(cs)
	body.add_child(IslandProxy.plateau_mesh(RIM_R, 36.0, 0.0, SEA_Y - 6.0, 1.7, Color(0.44, 0.64, 0.30), Color(0.78, 0.66, 0.48)))
	add_child(body)
	EnvKit.boundary(self, WALL_R - 0.9, 3.0, 48)
	# low stone wall (visual)
	var seg := 40
	var wall_mat := CharacterVisual.make_toon(Color(0.86, 0.80, 0.68), null, 0.0, 0.1)
	var cap_mat := CharacterVisual.make_toon(Color(0.93, 0.89, 0.80), null, 0.0, 0.1)
	var seg_len := TAU * WALL_R / float(seg) * 1.03
	for i in seg:
		var a := TAU * float(i) / float(seg)
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(seg_len, 0.8, 0.6)
		mi.mesh = bm
		mi.material_override = wall_mat
		mi.position = Vector3(sin(a) * WALL_R, 0.4, cos(a) * WALL_R)
		mi.rotation.y = a
		add_child(mi)
		var cap := MeshInstance3D.new()
		var cb := BoxMesh.new()
		cb.size = Vector3(seg_len, 0.14, 0.8)
		cap.mesh = cb
		cap.material_override = cap_mat
		cap.position = Vector3(sin(a) * WALL_R, 0.87, cos(a) * WALL_R)
		cap.rotation.y = a
		add_child(cap)
	# pale flagstone court in front of the temple and a path to Pegasus (visual only)
	var court_mat := CharacterVisual.make_toon(Color(0.74, 0.66, 0.52), null, 0.0, 0.0)
	var court := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 6.0
	cm.bottom_radius = 6.0
	cm.height = 0.06
	cm.radial_segments = 48
	court.mesh = cm
	court.material_override = court_mat
	court.position = Vector3(0, 0.03, 3.6)
	add_child(court)
	var path := MeshInstance3D.new()
	var pm := BoxMesh.new()
	pm.size = Vector3(1.8, 0.05, 9.0)
	path.mesh = pm
	path.material_override = court_mat
	var mid := (Vector3(0, 0, -3.5) + _mount_spot()) * 0.5
	path.position = Vector3(mid.x, 0.025, mid.z)
	path.rotation.y = atan2(_mount_spot().x - 0.0, _mount_spot().z + 3.5)
	add_child(path)


func _build_props() -> void:
	EnvKit.prop(self, "temple", Vector3(0, 0, 11), 180.0)
	for p in [Vector3(-10, 0, 13.5), Vector3(10, 0, 13.5), Vector3(-15.5, 0, 6.5), Vector3(15.5, 0, 6.5), Vector3(-9, 0, -16.5), Vector3(-17.5, 0, -3)]:
		EnvKit.prop(self, "cypress", p, 0.0)
	EnvKit.prop(self, "olive_tree", Vector3(-12.5, 0, -8.5), 35.0)
	EnvKit.prop(self, "olive_tree", Vector3(14.5, 0, -2.5), 160.0, 0.9)
	EnvKit.prop(self, "olive_tree", Vector3(12.0, 0, 9.5), 250.0, 0.8)
	for p in [Vector3(-4.6, 0, 6.6), Vector3(-5.5, 0, 7.5), Vector3(4.9, 0, 6.9), Vector3(11.0, 0, -11.5), Vector3(11.8, 0, -10.6)]:
		EnvKit.prop(self, "amphora", p, randf() * 360.0)
	EnvKit.prop(self, "boulder", Vector3(-15.0, 0, -12.0), 20.0, 0.8)
	EnvKit.prop(self, "column_broken", Vector3(16.0, 0, -9.5), 60.0, 0.8)
	for x in [-3.4, 3.4]:
		var pos := Vector3(x, 0, 5.0)
		EnvKit.prop(self, "brazier", pos, 0.0)
		var flame := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.0
		cm.bottom_radius = 0.34
		cm.height = 0.75
		cm.radial_segments = 10
		flame.mesh = cm
		flame.material_override = IslandProxy.glow_material(Color(1.0, 0.55, 0.15), 4.0)
		flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		flame.position = pos + Vector3(0, 1.25, 0)
		add_child(flame)
		_flames.append(flame)
		Sfx.loop("fire_loop", flame)   # brazier crackle follows the flame node (dies with it)
		# no OmniLight here: the toon shader bands any light > 0, so a light's clustered cut-off shows as square
		# tiles on the grass (seen in the first home screenshots); the emissive flame is enough


func _build_trophies() -> void:
	var titles := {"cyclops": "FIRST LABOR", "medusa": "SECOND LABOR", "hydra": "THIRD LABOR"}
	for id in PEDESTALS:
		var base: Vector3 = PEDESTALS[id]
		EnvKit.prop(self, "pedestal", base, 0.0)
		var top := base + Vector3(0, 1.1, 0)
		var holder := Node3D.new()
		holder.name = "Trophy_%s" % id
		add_child(holder)
		holder.position = top
		match id:
			"cyclops":
				_trophy_club(holder)
			"medusa":
				_trophy_snake_head(holder)
			"hydra":
				_trophy_horn(holder)
		holder.visible = bool(Game.defeated.get(id, false))
		_trophy_nodes[id] = holder
		var lab := Label3D.new()
		lab.text = titles[id]
		lab.font_size = 40
		lab.pixel_size = 0.004
		lab.modulate = Color(0.30, 0.22, 0.10)
		lab.outline_size = 0
		lab.position = base + Vector3(0, 0.55, -0.70)
		lab.rotation.y = PI       # faces north: read by the hero walking from Pegasus back to the temple
		add_child(lab)


func _trophy_club(holder: Node3D) -> void:
	var club := EnvKit.prop(holder, "club", Vector3(0, 0.15, 0), 0.0, 0.2, false)
	club.rotation_degrees = Vector3(0, 35, 72)


func _trophy_snake_head(holder: Node3D) -> void:
	var stone := CharacterVisual.make_toon(Color(0.66, 0.64, 0.60), null, 0.02)
	var coil := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.18
	tm.outer_radius = 0.38
	coil.mesh = tm
	coil.material_override = stone
	coil.position = Vector3(0, 0.1, 0)
	holder.add_child(coil)
	var neck := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.09
	cm.bottom_radius = 0.11
	cm.height = 0.5
	neck.mesh = cm
	neck.material_override = stone
	neck.position = Vector3(0.28, 0.35, 0)
	neck.rotation_degrees = Vector3(0, 0, 18)
	holder.add_child(neck)
	var head := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.17
	sm.height = 0.26
	head.mesh = sm
	head.material_override = stone
	head.position = Vector3(0.2, 0.62, -0.1)
	head.scale = Vector3(1.0, 0.8, 1.5)
	holder.add_child(head)
	for sx in [-1.0, 1.0]:
		var fang := MeshInstance3D.new()
		var fm := CylinderMesh.new()
		fm.top_radius = 0.025
		fm.bottom_radius = 0.0
		fm.height = 0.12
		fang.mesh = fm
		fang.material_override = CharacterVisual.make_toon(Color(0.86, 0.84, 0.78))
		fang.position = Vector3(0.2 + sx * 0.06, 0.52, -0.3)
		holder.add_child(fang)


func _trophy_horn(holder: Node3D) -> void:
	var cols := [Color(0.20, 0.14, 0.26), Color(0.30, 0.14, 0.30), Color(0.50, 0.12, 0.22), Color(0.72, 0.14, 0.16)]
	var pos := Vector3(0, 0.05, 0)
	var ang := 0.0
	var r := 0.20
	for i in 4:
		var seg := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.bottom_radius = r
		cm.top_radius = r * 0.62
		cm.height = 0.34
		seg.mesh = cm
		seg.material_override = CharacterVisual.make_toon(cols[i], null, 0.015)
		seg.rotation.z = -ang
		seg.position = pos + Vector3(sin(ang), cos(ang), 0) * 0.17
		holder.add_child(seg)
		pos += Vector3(sin(ang), cos(ang), 0) * 0.32
		ang += deg_to_rad(22.0)
		r *= 0.62


func _build_sign() -> void:
	var root := Node3D.new()
	root.name = "Sign"
	add_child(root)
	root.position = SIGN_POS
	root.rotation.y = deg_to_rad(15.0)
	var wood := CharacterVisual.make_toon(Color(0.52, 0.36, 0.20), null, 0.02)
	var board_mat := CharacterVisual.make_toon(Color(0.90, 0.82, 0.62), null, 0.025)
	for x in [-1.62, 1.62]:
		var post := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.16, 2.9, 0.16)
		post.mesh = bm
		post.material_override = wood
		post.position = Vector3(x, 1.45, -0.06)
		root.add_child(post)
	var board := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(3.4, 2.0, 0.08)
	board.mesh = bb
	board.material_override = board_mat
	board.position = Vector3(0, 1.75, 0)
	root.add_child(board)
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(3.4, 2.9, 0.3)
	cs.shape = shape
	cs.position = Vector3(0, 1.45, 0)
	body.add_child(cs)
	root.add_child(body)
	# front (faces the spawn): the goal, big enough to read from the spawn point
	_sign_label = _sign_text(56, Vector3(0, 1.75, 0.05), 0.0)
	root.add_child(_sign_label)
	# back: the controls
	_sign_back = _sign_text(34, Vector3(0, 1.75, -0.05), PI)
	root.add_child(_sign_back)
	_refresh_sign()


func _sign_text(size: int, pos: Vector3, yaw: float) -> Label3D:
	var l := Label3D.new()
	l.font_size = size
	l.pixel_size = 0.0058
	l.modulate = Color(0.20, 0.12, 0.05)
	l.outline_size = 0
	l.double_sided = false
	l.width = 540.0
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.position = pos
	l.rotation.y = yaw
	return l


func _build_pegasus() -> void:
	pegasus_root = Node3D.new()
	pegasus_root.name = "Pegasus"
	add_child(pegasus_root)
	pegasus_root.position = PEGASUS_POS
	pegasus_root.rotation_degrees.y = PEGASUS_YAW
	pegasus = CharacterVisual.create(&"pegasus")
	pegasus_root.add_child(pegasus)
	pegasus.play(&"idle", 0.0)
	var body := StaticBody3D.new()
	body.name = "PegasusBody"
	body.collision_layer = 1
	body.collision_mask = 0
	body.add_to_group("camera_ignore")
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(0.9, 1.8, 2.6)
	cs.shape = shape
	cs.position = Vector3(0, 0.9, 0)
	body.add_child(cs)
	pegasus_root.add_child(body)


# ------------------------------------------------------------------ wing overlay (mount)
## Plays one clip (Pegasus `fly`) on a subset of bones (names starting with `prefix`) over whatever the skeleton
## shows, weight eased in over `rise` seconds. t = the overlay's clip time (so the full clip can take over in phase).
class WingOverlay extends SkeletonModifier3D:
	var anim: Animation = null
	var t := 0.0
	var _tracks: Array = []        # [bone, track, type]
	var _w := 0.0
	var _rise := 0.35
	var closing := false           # close(): the weight eases back to 0 (the wings return to the clip under it)
	var _fall := 0.5
	## feedback 2: true = the beat runs on to the next wing TOP (t wraps to 0) and the wings stay raised there, clear
	## of the rider's legs and body while he climbs on or off (the beating near wing swept through him before)
	var hold_top := false
	var _held := false

	func close(fall: float) -> void:
		closing = true
		_fall = maxf(fall, 0.01)

	func setup(a: Animation, skel: Skeleton3D, prefix: String, rise: float) -> void:
		anim = a
		_rise = maxf(rise, 0.01)
		for i in a.get_track_count():
			var tt := a.track_get_type(i)
			if tt != Animation.TYPE_ROTATION_3D and tt != Animation.TYPE_POSITION_3D:
				continue
			var bone := String(a.track_get_path(i).get_concatenated_subnames())
			if not bone.begins_with(prefix):
				continue
			var b := skel.find_bone(bone)
			if b >= 0:
				_tracks.append([b, i, tt])

	func bone_count() -> int:
		var seen := {}
		for e in _tracks:
			seen[e[0]] = true
		return seen.size()

	func _process_modification_with_delta(delta: float) -> void:
		var skel := get_skeleton()
		if skel == null or anim == null or anim.length <= 0.0:
			return
		if closing:
			# the beat stops where it is and the wings settle from that pose into the clip under them (no last flap)
			_w = maxf(_w - delta / _fall, 0.0)
		else:
			if hold_top and (_held or t + delta >= anim.length):
				_held = true
				t = 0.0
			else:
				t = fmod(t + delta, anim.length)
			_w = minf(_w + delta / _rise, 1.0)
		var k := 0.5 - 0.5 * cos(_w * PI)
		if k <= 0.0:
			return
		for e in _tracks:
			var b: int = e[0]
			if int(e[2]) == Animation.TYPE_ROTATION_3D:
				var r := anim.rotation_track_interpolate(int(e[1]), t)
				skel.set_bone_pose_rotation(b, skel.get_bone_pose_rotation(b).slerp(r, k))
			else:
				var p := anim.position_track_interpolate(int(e[1]), t)
				skel.set_bone_pose_position(b, skel.get_bone_pose_position(b).lerp(p, k))
