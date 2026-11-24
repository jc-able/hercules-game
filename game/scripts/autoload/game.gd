extends Node
## Autoload `Game`: command-line args, scene routing with a fade, progress + save, pause, hit pause, harness events.
## Scenes are built in code: each scene id maps to a builder script (see BUILDERS). A builder is any Node script;
## if it has `setup(opts: Dictionary)` it is called before the node enters the tree.

signal progress_changed
signal scene_changed(scene_id: StringName)
signal camera_shake(amount: float)

const SAVE_PATH := "user://save.json"
## scene id -> builder script path, or a list of candidate paths (the first that exists wins).
const BUILDERS := {
	"title": "res://scripts/ui/title_screen.gd",
	"ending": ["res://scripts/world/ending.gd", "res://scripts/ui/ending_card.gd"],
	"home": "res://scripts/world/home_base.gd",
	"sea": "res://scripts/world/sea_world.gd",
	"cyclops": "res://scripts/world/cyclops_arena.gd",
	"medusa": "res://scripts/world/medusa_arena.gd",
	"hydra": "res://scripts/world/hydra_arena.gd",
	"test": "res://scripts/test/test_arena.gd",
	"test_travel": "res://scripts/test/travel_test.gd",
}
const MISSING_BUILDER := "res://scripts/ui/missing_scene.gd"
const HARNESS_SCRIPT := "res://scripts/test/harness.gd"
const PAUSE_SCRIPT := "res://scripts/ui/pause_menu.gd"
const NOT_PAUSABLE := ["title", "ending", "missing"]
const FIXED_SEED := 1234567
## Gameplay buttons released when the pause menu closes or the scene changes, so the button that closed a menu
## (B = ui_cancel + roll, A = ui_accept + interact) never also acts in the game.
const GAMEPLAY_BUTTONS := ["roll", "attack", "shield", "interact", "lock_on", "boost"]
const HOLD_BUTTONS := ["shield", "boost"]   ## kept on resume (release_gameplay_buttons(true)): holds survive a pause

var defeated := {"cyclops": false, "medusa": false, "hydra": false}
var ending_seen := false           ## the ending card was shown once (saved with the progress)
var seed_used := FIXED_SEED        ## the random seed of this run (harness: --seed=<int>, default FIXED_SEED)
var args: Dictionary = {}          ## parsed user args after "--" (e.g. {"start":"cyclops","harness":true})
var harness := false               ## true in automated runs: no mouse capture, no save, fixed seed
var rng := RandomNumberGenerator.new()
var scene_id: StringName = &""
var scene_opts: Dictionary = {}
var world: Node = null             ## the node built for the current scene id
var time := 0.0                    ## scaled seconds since boot (harness timestamps)
var base_time_scale := 1.0

var _fade_layer: CanvasLayer
var _fade: ColorRect
var _busy := false
var _pause_menu: Node = null
var _hit_pause_until := 0
var _harness: Node = null
var _queued: Array = []            ## [id, opts] of a goto() asked for while a fade was running (latest wins)
var _extra_builders := {}          ## ids added at runtime with register_scene()
var _quitting := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().set_auto_accept_quit(false)    # the window close button goes through quit_game() (clean audio stop)
	_parse_args()
	harness = args.has("harness")
	if harness or args.has("seed"):
		seed_used = int(arg_float("seed", FIXED_SEED))
		seed(seed_used)
		rng.seed = seed_used
	else:
		rng.randomize()
		seed_used = int(rng.seed)
	if harness:
		_apply_harness_progress()
	else:
		_load_progress()
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 100
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_fade_layer.add_child(_fade)
	_boot.call_deferred()


func _process(delta: float) -> void:
	time += delta


func _boot() -> void:
	if harness and ResourceLoader.exists(HARNESS_SCRIPT):
		_harness = load(HARNESS_SCRIPT).new()
		_harness.name = "Harness"
		add_child(_harness)
	var start := StringName(str(args.get("start", "title")))
	_switch(start, {})


# ------------------------------------------------------------------ args
func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if not s.begins_with("--"):
			continue
		s = s.substr(2)
		var eq := s.find("=")
		if eq < 0:
			args[s] = true
		else:
			args[s.substr(0, eq)] = s.substr(eq + 1)


## Harness only: `--defeated=cyclops,medusa` presets progress in memory (never saved); `--ending-seen` too.
func _apply_harness_progress() -> void:
	var v = args.get("defeated", "")
	if typeof(v) == TYPE_STRING and String(v) != "":
		for id in String(v).split(",", false):
			var k := id.strip_edges()
			if k == "all":
				for b in defeated:
					defeated[b] = true
			elif defeated.has(k):
				defeated[k] = true
			else:
				push_warning("Game: --defeated has an unknown boss '%s'" % k)
	ending_seen = args.has("ending-seen")
	progress_changed.emit()


## A numeric user arg (`--speed=2` -> 2.0), or `default` when absent.
func arg_float(key: String, default: float) -> float:
	if not args.has(key) or typeof(args[key]) == TYPE_BOOL:
		return default
	return String(args[key]).to_float()


## Prints one harness event line `[H] t=1.23 event=name k=v ...` (only in harness runs).
func event(name: String, data := {}) -> void:
	if not harness:
		return
	var line := "[H] t=%.2f event=%s" % [time, name]
	for k in data:
		var v = data[k]
		if v is float:
			v = "%.2f" % v
		line += " %s=%s" % [k, str(v).replace(" ", "_")]
	print(line)
	if _harness != null and _harness.has_method("on_event"):
		_harness.on_event(name, data)


# ------------------------------------------------------------------ progress
## True when the island can be visited (home and the first island always; then in unlock order).
func is_unlocked(island: StringName) -> bool:
	var i := Tuning.UNLOCK_ORDER.find(island)
	if i <= 0:
		return true
	return bool(defeated.get(String(Tuning.UNLOCK_ORDER[i - 1]), false))


## Records a beaten boss (saved unless harness) and emits progress_changed.
func mark_defeated(boss: StringName) -> void:
	if not defeated.has(String(boss)):
		return
	defeated[String(boss)] = true
	_save_progress()
	progress_changed.emit()


## True when all three bosses are beaten and the ending card has not been shown yet.
func ending_pending() -> bool:
	return defeated_count() >= defeated.size() and not ending_seen


## Records that the ending card was shown (saved unless harness). Whoever shows the card calls this.
func mark_ending_seen() -> void:
	if ending_seen:
		return
	ending_seen = true
	_save_progress()
	progress_changed.emit()


## Number of bosses beaten so far.
func defeated_count() -> int:
	var n := 0
	for k in defeated:
		if defeated[k]:
			n += 1
	return n


## True when a save file exists (always false in harness runs, unless `--fake-save`: the title then behaves as with
## a save, for menu tests; nothing is ever written).
func has_save() -> bool:
	if harness:
		return args.has("fake-save")
	return FileAccess.file_exists(SAVE_PATH)


## True when New game would erase something (a boss beaten or the ending seen): the title asks first.
func new_game_needs_confirm() -> bool:
	return has_save() and (defeated_count() > 0 or ending_seen)


## Resets progress and goes to the home island. The title asks for confirmation first when
## new_game_needs_confirm() (QA: one press under Continue erased every beaten labor).
func new_game() -> void:
	for k in defeated:
		defeated[k] = false
	ending_seen = false
	_save_progress()
	progress_changed.emit()
	goto(&"home")


func _save_progress() -> void:
	if harness:
		return
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"defeated": defeated, "ending_seen": ending_seen}))


func _load_progress() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if data is Dictionary and data.get("defeated") is Dictionary:
		for k in defeated:
			defeated[k] = bool(data["defeated"].get(k, false))
		ending_seen = bool(data.get("ending_seen", false))


# ------------------------------------------------------------------ scenes
## Current player or null.
func player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


## Fades out, replaces the current scene with the one built for `scene_id`, fades back in.
## opts are passed to the builder's setup(opts) (e.g. {"from": "cyclops"}; arenas get {"restart": true} on a retry).
## A request made while a fade runs is kept (the latest wins): before the switch it replaces the target, after the
## switch it runs once the fade-in ends. Never dropped silently.
func goto(id: StringName, opts := {}) -> void:
	if _busy:
		_queued = [id, opts]
		event("goto_queued", {"id": id})
		return
	_busy = true
	var t := 0.18 if harness else 0.35
	var tw := create_tween()
	tw.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(_fade, "color:a", 1.0, t)
	await tw.finished
	if not _queued.is_empty():
		id = _queued[0]
		opts = _queued[1]
		_queued = []
	_switch(id, opts)
	await get_tree().process_frame
	var tw2 := create_tween()
	tw2.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw2.tween_property(_fade, "color:a", 0.0, t)
	await tw2.finished
	_busy = false
	if not _queued.is_empty():
		var q := _queued
		_queued = []
		goto(q[0], q[1])


## True while a scene fade is running.
func is_switching() -> bool:
	return _busy


## Adds (or replaces) a scene id at runtime: goto(id) then builds `path`. For new ids without editing BUILDERS.
func register_scene(id: StringName, path: String) -> void:
	_extra_builders[String(id)] = path


## The builder script path for a scene id ("" when none exists yet).
func builder_path(id: StringName) -> String:
	var entry = _extra_builders.get(String(id), BUILDERS.get(String(id), ""))
	var cands: Array = entry if entry is Array else [entry]
	for c in cands:
		if String(c) != "" and ResourceLoader.exists(String(c)):
			return String(c)
	return ""


## Restarts the current scene (a lost fight): same id, opts + {"restart": true}.
func restart_scene() -> void:
	var o := scene_opts.duplicate()
	o["restart"] = true
	goto(scene_id, o)


func _switch(id: StringName, opts: Dictionary) -> void:
	set_paused(false)
	release_gameplay_buttons()
	if world != null and is_instance_valid(world):
		world.queue_free()
		world.get_parent().remove_child(world)
	world = null
	var restarting := id == scene_id and bool(opts.get("restart", false))
	scene_id = id
	scene_opts = opts
	var path := builder_path(id)
	var node: Node
	if path != "":
		node = (load(path) as Script).new()
	else:
		var entry = _extra_builders.get(String(id), BUILDERS.get(String(id), ""))
		var wanted := String(entry[0]) if entry is Array else String(entry)
		node = (load(MISSING_BUILDER) as Script).new()
		opts = {"id": String(id), "path": wanted}
		event("missing_scene", {"id": id, "path": wanted})
	node.name = "Scene_%s" % id
	if node.has_method("setup"):
		node.setup(opts)
	# free the mouse BEFORE the new scene enters the tree: its _ready() captures it again when it wants
	# (home, sea, arenas). Freeing it after add_child undid that capture (QA: mouse camera dead after every goto).
	capture_mouse(false)
	var parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	parent.add_child(node)
	world = node
	if restarting:
		event("restart", {"scene": id})
	event("scene", {"id": id})
	scene_changed.emit(id)


# ------------------------------------------------------------------ pause, mouse, feel
func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("pause") and not e.is_echo():
		if _busy or String(scene_id) in NOT_PAUSABLE or world == null:
			return
		if not get_tree().paused:
			set_paused(true)
			get_viewport().set_input_as_handled()


## Pauses the game and shows the pause menu (or hides it and resumes).
func set_paused(on: bool) -> void:
	if on == get_tree().paused and (on == (_pause_menu != null)):
		return
	get_tree().paused = on
	if on:
		if _pause_menu == null and ResourceLoader.exists(PAUSE_SCRIPT):
			_pause_menu = load(PAUSE_SCRIPT).new()
			add_child(_pause_menu)
		capture_mouse(false)
		event("paused")
	else:
		if _pause_menu != null:
			_pause_menu.queue_free()
			_pause_menu = null
		release_gameplay_buttons(true)
		event("resumed")
		if world != null and world.has_method("wants_mouse_captured") and world.wants_mouse_captured():
			capture_mouse(true)


## Releases the gameplay button actions (a released button must be pressed again to act). `taps_only` (resume from
## the pause menu) keeps the HOLD actions (shield, boost) on Input's real state: a shield held through the pause
## stays up. Only the tap actions can be the button that closed a menu.
func release_gameplay_buttons(taps_only := false) -> void:
	for a in GAMEPLAY_BUTTONS:
		if taps_only and a in HOLD_BUTTONS:
			continue
		if InputMap.has_action(a):
			Input.action_release(a)


## Quits the game cleanly: pauses, stops the audio (music streams still playing at quit leaked ObjectDB instances
## and resources), waits a moment, then quits. Used by the title's Quit and the window close button.
func quit_game() -> void:
	if _quitting:
		return
	_quitting = true
	get_tree().paused = true
	if Sfx.has_method("shutdown"):
		Sfx.shutdown()
	await get_tree().create_timer(0.15, true, false, true).timeout
	get_tree().quit()


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_WM_CLOSE_REQUEST:
			quit_game()
		NOTIFICATION_APPLICATION_FOCUS_OUT:
			# Cmd-Tab / a notification click mid-fight: pause so the player does not come back to DEFEATED
			if harness or _busy or _quitting or world == null or String(scene_id) in NOT_PAUSABLE:
				return
			if not get_tree().paused:
				set_paused(true)
				event("focus_pause")
		NOTIFICATION_APPLICATION_FOCUS_IN:
			if harness or _quitting:
				return
			if _pause_menu == null and world != null and is_instance_valid(world) \
					and world.has_method("wants_mouse_captured") and world.wants_mouse_captured():
				capture_mouse(true)


## Captures (or frees) the mouse for camera control; never in harness runs.
func capture_mouse(on: bool) -> void:
	if harness or DisplayServer.get_name() == "headless":
		return
	Controls.set_mouse_mode(Input.MOUSE_MODE_CAPTURED if on else Input.MOUSE_MODE_VISIBLE)


## Sets the normal time scale (harness --speed); hit pauses return to it.
func set_base_time_scale(s: float) -> void:
	base_time_scale = s
	Engine.time_scale = s


## A short near-freeze on big impacts (weak-point strikes, heavy hits).
func hit_pause(seconds := Tuning.HIT_PAUSE) -> void:
	Engine.time_scale = base_time_scale * 0.05
	var until := Time.get_ticks_msec() + int(seconds * 1000.0)
	_hit_pause_until = until
	await get_tree().create_timer(seconds, true, false, true).timeout
	if _hit_pause_until == until:
		Engine.time_scale = base_time_scale


## Asks the active camera to shake (0.0 - 1.0).
func shake(amount: float) -> void:
	camera_shake.emit(amount)
