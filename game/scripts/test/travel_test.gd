extends Node3D
## Scene id "test_travel": core regression for the bot's advisor fallback (what home and sea rely on).
## Phase "walk": a Player (free camera) walks to a marker and presses interact (like mounting Pegasus).
## Phase "fly": the Player is removed (as in the sea) and a flyer steered by the left stick + boost flies into a ring,
## then Game.goto("test") starts the dummy fight. The scene node itself answers bot_advice() (generic dictionary).
## `--start=test_travel --harness --bot=win` must end with result=victory. Also a small template for world modules.

const MARKER := Vector3(10, 0, -12)
const RING := Vector3(-60, 20, -140)
const FLY_SPEED := 20.0
const BOOST_SPEED := 40.0

var phase := "walk"
var player: Player
var hud: Hud
var flyer: Node3D
var _cam: Camera3D
var _yaw := 0.0
var _boosted := false


func _ready() -> void:
	EnvKit.sky(self)
	EnvKit.sun(self)
	EnvKit.floor_disc(self, 30.0, Color(0.55, 0.72, 0.42))
	EnvKit.sea(self, 3000.0, -3.0)
	var post := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.4
	cm.bottom_radius = 0.4
	cm.height = 2.5
	post.mesh = cm
	post.material_override = CharacterVisual.make_toon(Color(0.9, 0.85, 0.7), null, 0.02)
	add_child(post)
	post.position = MARKER + Vector3(0, 1.25, 0)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	player.global_position = Vector3(0, 0.1, 0)
	player.camera.snap_behind()
	hud = Hud.new()
	add_child(hud)
	hud.bind_player(player)
	Game.capture_mouse(true)
	Game.event("travel_phase", {"phase": phase})


func wants_mouse_captured() -> bool:
	return true


func _physics_process(delta: float) -> void:
	match phase:
		"walk":
			var near := _flat(player.global_position - MARKER).length() < 2.5
			hud.show_prompt("{interact} Mount" if near else "")
			if near and Input.is_action_just_pressed("interact"):
				_start_flight()
		"fly":
			var stick := Controls.get_move()
			_yaw -= stick.x * 1.4 * delta
			var speed := BOOST_SPEED if Input.is_action_pressed("boost") else FLY_SPEED
			if speed == BOOST_SPEED and not _boosted:
				_boosted = true
				Game.event("travel_boost")
			var fwd := Vector3(-sin(_yaw), 0, -cos(_yaw))
			flyer.global_position += fwd * speed * delta
			flyer.global_position.y = move_toward(flyer.global_position.y, RING.y, 6.0 * delta)
			flyer.rotation.y = _yaw
			_cam.global_position = flyer.global_position - fwd * 9.0 + Vector3.UP * 3.5
			_cam.look_at(flyer.global_position + fwd * 6.0, Vector3.UP)
			if flyer.global_position.distance_to(RING) < 8.0:
				phase = "landed"
				Game.event("travel_phase", {"phase": phase})
				Game.goto(&"test")


func _start_flight() -> void:
	phase = "fly"
	Game.event("travel_phase", {"phase": phase})
	hud.show_prompt("")
	var start := player.global_position + Vector3.UP * RING.y * 0.5
	player.queue_free()
	player = null
	flyer = CharacterVisual.create(&"pegasus")
	add_child(flyer)
	flyer.global_position = start
	_cam = Camera3D.new()
	add_child(_cam)
	_cam.current = true


## Generic bot advice (see scripts/test/bot.gd): walk to the marker and interact, then steer into the ring with boost.
func bot_advice() -> Dictionary:
	match phase:
		"walk":
			if player == null:
				return {}
			var near := _flat(player.global_position - MARKER).length() < 2.0
			return {"move_to": MARKER, "interact": near, "face": MARKER}
		"fly":
			var to := _flat(RING - flyer.global_position)
			var fwd := Vector3(-sin(_yaw), 0, -cos(_yaw))
			var err := fwd.signed_angle_to(to.normalized(), Vector3.UP)   # > 0 = ring to the left
			return {"stick": Vector2(clampf(-err * 2.0, -1.0, 1.0), 0.0), "boost": absf(err) < 0.3}
	return {}


func _flat(v: Vector3) -> Vector3:
	return Vector3(v.x, 0, v.z)
