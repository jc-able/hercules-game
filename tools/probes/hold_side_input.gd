extends SceneTree
## Lead look probe: the hero holds full side input while locked on (right 4 s, then left 4 s, then forward-right 2 s).
var G: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	G = root.get_node("Game")
	var arena: Node = null
	while true:
		await process_frame
		arena = G.world
		if arena != null and "boss" in arena and arena.boss != null and arena.boss.fighting:
			break
	var player: Node = arena.player
	player.hp = 100000
	print("[P] fight on, t=%.2f locked=%s" % [G.time, player.locked])
	for step in [["move_right", 4.0], ["move_left", 4.0]]:
		Input.action_press(step[0], 1.0)
		var t := 0.0
		while t < step[1]:
			await physics_frame
			t += 1.0 / 60.0
			if int(t * 60.0) % 30 == 0:
				print("[P] %s t=%.2f vis_yaw=%.1f clip=%s speed=%.2f" % [step[0], t, rad_to_deg(player._vis_yaw), player._clip, player._loco_speed])
		Input.action_release(step[0])
	quit()
