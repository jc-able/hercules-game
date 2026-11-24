extends SceneTree
## Lead probe: transitions out of the locked-on circling run (roll sideways, roll back, strike, shield, stop, reverse).
## Logs the largest twist seen in every phase and the state / clip, with screenshots from the harness flags.
var G: Node
var player: Node


func _initialize() -> void:
	_run.call_deferred()


func hold(actions: Array, secs: float, tag: String) -> void:
	for a in actions:
		Input.action_press(a, 1.0)
	var t := 0.0
	var max_tw := 0.0
	var max_vy := 0.0
	var states := {}
	while t < secs:
		await physics_frame
		t += 1.0 / 60.0
		max_tw = maxf(max_tw, absf(rad_to_deg(player._twist)))
		max_vy = maxf(max_vy, absf(rad_to_deg(wrapf(player._vis_yaw, -PI, PI))))
		states[String(player.state) + "/" + String(player._clip)] = true
	for a in actions:
		Input.action_release(a)
	print("[P] %-26s max_twist=%5.1f max_vis_yaw=%6.1f end_twist=%5.1f states=%s" % [tag, max_tw, max_vy, rad_to_deg(player._twist), ",".join(states.keys())])


func tap(action: String) -> void:
	Input.action_press(action, 1.0)
	await physics_frame
	await physics_frame
	Input.action_release(action)


func _run() -> void:
	G = root.get_node("Game")
	var arena: Node = null
	while true:
		await process_frame
		arena = G.world
		if arena != null and "boss" in arena and arena.boss != null and arena.boss.fighting:
			break
	player = arena.player
	player.hp = 100000
	await hold(["move_right"], 1.5, "circle right")
	Input.action_press("move_right", 1.0)
	await tap("roll")
	await hold(["move_right"], 1.2, "side roll from circling")
	await hold([], 0.5, "stop")
	await hold(["move_left"], 1.2, "circle left")
	Input.action_press("move_back", 1.0)
	await tap("roll")
	await hold(["move_back"], 1.0, "back roll after circling")
	await hold(["move_right"], 1.0, "circle right again")
	await tap("attack")
	await hold([], 0.9, "strike from circling")
	await hold(["move_left"], 1.0, "circle left again")
	await hold(["shield"], 0.6, "shield from circling")
	await hold(["move_right"], 0.8, "right")
	await hold(["move_left"], 0.8, "reverse to left")
	await hold(["move_forward", "move_right"], 0.8, "forward-right diagonal")
	await hold(["move_back"], 0.8, "back away")
	quit()
