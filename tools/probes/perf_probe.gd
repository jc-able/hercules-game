extends SceneTree
## QA throw-away probe (qa_build): runs the normal main scene and records frame times + render counters.
## Usage: Godot --path game --script res://zz_qa_perf.gd --resolution 1920x1080 -- --start=cyclops --harness --bot=win --perf-out=<file>

var _last_us := 0
var _frames: Array = []   # [game_time, wall_ms, frame_ms, draw_calls, primitives, objects]
var _started := false
var _t0_us := 0
var _out := ""
var _variant := ""
var _n := 0


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--perf-out="):
			_out = String(a).substr(11)
		if String(a).begins_with("--qa-variant="):
			_variant = String(a).substr(13)
	change_scene_to_file("res://scenes/main.tscn")
	RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(), true)
	_t0_us = Time.get_ticks_usec()
	if "novsync" in _variant:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	if "phys120" in _variant:
		Engine.physics_ticks_per_second = 120
	if "nomsaa" in _variant:
		root.msaa_3d = Viewport.MSAA_DISABLED
	if "shadow2k" in _variant:
		RenderingServer.directional_shadow_atlas_set_size(2048, true)


func _process(_delta: float) -> bool:
	var now := Time.get_ticks_usec()
	if _last_us != 0:
		var ms := (now - _last_us) / 1000.0
		var g := root.get_node_or_null("Game")
		var gt := 0.0
		if g != null:
			gt = float(g.get("time"))
		_frames.append([gt, (now - _t0_us) / 1000.0, ms,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
			Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
			RenderingServer.viewport_get_measured_render_time_cpu(root.get_viewport_rid()) + RenderingServer.get_frame_setup_time_cpu(),
			RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid())])
	_last_us = now
	_n += 1
	if "noshadow" in _variant and _n % 30 == 0:
		for l in root.find_children("*", "DirectionalLight3D", true, false):
			l.shadow_enabled = false
	if "nooutline" in _variant and _n % 30 == 0:
		for m in root.find_children("*", "MeshInstance3D", true, false):
			var mat = m.get_surface_override_material(0) if m.mesh != null and m.mesh.get_surface_count() > 0 else null
			if mat != null and mat.next_pass != null:
				mat.next_pass = null
	return false


func _finalize() -> void:
	var info := {
		"frames": _frames,
		"video_mem": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
		"static_mem": Performance.get_monitor(Performance.MEMORY_STATIC),
		"window": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y],
		"refresh": DisplayServer.screen_get_refresh_rate(),
		"vsync": DisplayServer.window_get_vsync_mode(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"variant": _variant,
	}
	if _out != "":
		var f := FileAccess.open(_out, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify(info))
			f.close()
	print("[QA] perf frames=%d out=%s" % [_frames.size(), _out])
