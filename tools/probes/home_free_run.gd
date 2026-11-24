extends SceneTree
## Lead look probe: free run on the home island (no lock-on): forward 1.5 s, right 3 s, back 3 s, left 3 s.
var G: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	G = root.get_node("Game")
	var w: Node = null
	var player: Node = null
	while true:
		await process_frame
		w = G.world
		if w != null and "player" in w and w.player != null and w.player.control_enabled:
			player = w.player
			break
	await create_timer(0.5).timeout
	print("[P] home on, t=%.2f locked=%s" % [G.time, player.locked])
	for step in [["move_forward", 1.5], ["move_right", 3.0], ["move_back", 3.0], ["move_left", 3.0]]:
		Input.action_press(step[0], 1.0)
		var t := 0.0
		while t < step[1]:
			await physics_frame
			t += 1.0 / 60.0
		var cam := root.get_viewport().get_camera_3d()
		var cf := -cam.global_transform.basis.z
		cf.y = 0.0
		print("[P] %s end: hero facing vs camera forward = %.0f deg, clip=%s" % [step[0], rad_to_deg(cf.normalized().signed_angle_to(player.facing, Vector3.UP)), player._clip])
		Input.action_release(step[0])
	quit()
