extends SceneTree
## freeze_fix probe: frame times + pipeline compilations; prints every frame > 50 ms and every frame that compiled
## pipelines, live, so the [H] events around it stay in order in the log. --perf-out=<json> optional.
var _last_us := 0
var _t0_us := 0
var _out := ""
var _frames: Array = []
var _pc := [0, 0, 0, 0, 0]
const MON := [34, 35, 36, 37, 38]   # canvas, mesh, surface, draw, specialization


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--perf-out="):
			_out = String(a).substr(11)
	change_scene_to_file("res://scenes/main.tscn")
	RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(), true)
	_t0_us = Time.get_ticks_usec()


func _process(_delta: float) -> bool:
	var now := Time.get_ticks_usec()
	var pc := []
	var d := []
	for i in 5:
		var v := int(Performance.get_monitor(MON[i]))
		pc.append(v)
		d.append(v - _pc[i])
	_pc = pc
	if _last_us != 0:
		var ms := (now - _last_us) / 1000.0
		var g := root.get_node_or_null("Game")
		var gt := 0.0
		if g != null:
			gt = float(g.get("time"))
		var scene := ""
		
		if g != null and g.get("current") != null:
			scene = str(g.get("current"))
		var rc := RenderingServer.viewport_get_measured_render_time_cpu(root.get_viewport_rid()) + RenderingServer.get_frame_setup_time_cpu()
		var rg := RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid())
		var pr := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
		var ph := Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		_frames.append([gt, (now - _t0_us) / 1000.0, ms, pr, ph, rc, rg, d])
		var compiled: int = d[0] + d[1] + d[2] + d[3] + d[4]
		if ms > 50.0 or compiled > 0:
			print("[P] t=%.2f wall=%.2f ms=%.1f proc=%.1f phys=%.1f rcpu=%.1f rgpu=%.1f pipe(c,m,s,d,sp)=%s" % [gt, (now - _t0_us) / 1e6, ms, pr, ph, rc, rg, str(d)])
	_last_us = now
	return false


func _finalize() -> void:
	if _out != "":
		var f := FileAccess.open(_out, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify({"frames": _frames}))
			f.close()
	print("[P] frames=%d out=%s" % [_frames.size(), _out])
