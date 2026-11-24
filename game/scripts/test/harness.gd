extends Node
## Test harness (SPEC §7.2), created by Game when `--harness` is passed:
##   --start=<scene_id> --harness [--bot=win|lose|idle] [--shots=<dir>] [--shot-every=<s>] [--quit-after=<s>]
##   [--speed=<time scale>] [--pad | --keys] [--probe=ui] [--seed=<int>] [--defeated=a,b] [--after-victory=<s>]
## --pad / --keys: the bot sends synthetic joypad / keyboard+mouse events instead of pressing actions directly.
## --seed: random seed (default Game.FIXED_SEED). --defeated: preset progress in memory (never saved).
## --after-victory=<s>: after a victory keep running through the post-victory flow (LABOR COMPLETE, mark_defeated,
##   the goto) and end <s> seconds after the next scene event (default: end 1.5 s after the victory).
## --probe=ui: at t=3 opens the pause menu, reports the focused button, then backs out with B / Esc (menu check).
## --probe=goto: at t=2 asks goto("test") then, 0.1 s into that fade, goto("title"); reports the scene at t=3.5
##   (must be title: a goto during a fade is queued, never dropped).
## --campaign: the whole game in one run (with --start=title --bot=win): no victory ends the run; every scene change
##   prints `[H] campaign scene=<id> prev=<id> prev_secs=<game s>`; ends with result=victory 5 s (game time) after the
##   free-flight sea scene that follows the ending.
## Prints `[H] ...` event lines (Game.event) and ends with `[H] result=victory|defeat|timeout|quit|missing_scene`
## (exit code 0 for victory/quit, 1 otherwise). --bot=lose ends after the first defeat once the restarted fight began.
## A start scene without a builder script ends at once with result=missing_scene.

const BOT_SCRIPT := "res://scripts/test/bot.gd"

var bot_mode := ""
var quit_after := 0.0
var shots_dir := ""
var shot_every := 2.0
var speed := 1.0
var defeats := 0
var victories := 0
var _shot_t := 0.0
var _shot_n := 0
var _shot_on := {}         # event name -> delay (s), --shot-on
var _shot_on_left := {}    # event name -> shots still to take
var _finished := false
var _bot: Node = null
var _probe := ""
var _probe_step := 0
var _after_victory := -1.0
var _scenes_seen := 0
var _campaign := false
var _scene_prev := ""
var _scene_t0 := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	bot_mode = str(Game.args.get("bot", ""))
	quit_after = Game.arg_float("quit-after", 0.0)
	shot_every = Game.arg_float("shot-every", 2.0)
	shot_every = INF if shot_every <= 0.0 else maxf(shot_every, 0.1)
	_parse_shot_on()
	speed = clampf(Game.arg_float("speed", 1.0), 0.1, 8.0)
	if Game.args.has("shots"):
		shots_dir = _resolve(str(Game.args["shots"]))
		DirAccess.make_dir_recursive_absolute(shots_dir)
		if DisplayServer.get_name() != "headless":
			get_window().size = Vector2i(1280, 720)
	if speed != 1.0:
		Engine.physics_ticks_per_second = int(round(60.0 * speed))
		Engine.max_physics_steps_per_frame = int(ceil(16.0 * speed))
		Game.set_base_time_scale(speed)
	_probe = str(Game.args.get("probe", ""))
	_after_victory = Game.arg_float("after-victory", -1.0)
	_campaign = Game.args.has("campaign")
	if bot_mode != "":
		_bot = load(BOT_SCRIPT).new()
		_bot.name = "Bot"
		_bot.mode = bot_mode
		_bot.use_pad = Game.args.has("pad")
		_bot.use_keys = Game.args.has("keys") and not _bot.use_pad
		add_child(_bot)
	var defeated_list := []
	for k in Game.defeated:
		if Game.defeated[k]:
			defeated_list.append(k)
	print("[H] harness start=%s bot=%s speed=%.2f quit_after=%.1f pad=%s keys=%s seed=%d defeated=%s shots=%s" % [Game.args.get("start", "title"), bot_mode if bot_mode != "" else "none", speed, quit_after, Game.args.has("pad"), Game.args.has("keys"), Game.seed_used, ",".join(defeated_list) if not defeated_list.is_empty() else "none", shots_dir])


## Paths without a leading "/" are relative to the repo root (the folder holding game/).
func _resolve(p: String) -> String:
	if p.is_absolute_path():
		return p
	var game_dir := ProjectSettings.globalize_path("res://").trim_suffix("/")
	return game_dir.get_base_dir().path_join(p)


## Called by Game.event for every harness event.
func on_event(name: String, _data: Dictionary) -> void:
	if shots_dir != "" and not _shot_on.is_empty() and _shot_on.has(name) and int(_shot_on_left.get(name, 0)) > 0:
		_shot_on_left[name] = int(_shot_on_left[name]) - 1
		_shot_later(float(_shot_on[name]))
	match name:
		"victory":
			victories += 1
			if _after_victory < 0.0 and not _campaign:
				_finish_later("victory", 1.5 / speed)
		"scene":
			_scenes_seen += 1
			if _campaign:
				var sid := str(_data.get("id", ""))
				print("[H] campaign scene=%s prev=%s prev_secs=%.1f" % [sid, _scene_prev if _scene_prev != "" else "none", Game.time - _scene_t0])
				_scene_prev = sid
				_scene_t0 = Game.time
				if sid == "sea" and bool(Game.scene_opts.get("free_flight", false)):
					_finish_later("victory", 5.0 / speed)
			elif victories > 0 and _after_victory >= 0.0:
				_finish_later("victory", _after_victory)
		"missing_scene":
			if _scenes_seen == 0:
				_finish_later("missing_scene", 0.1)
		"defeat":
			defeats += 1
		"fight_start":
			if defeats > 0 and bot_mode == "lose":
				_finish_later("defeat", 0.3)


func _process(delta: float) -> void:
	if _finished:
		return
	if shots_dir != "":
		_shot_t += delta
		if _shot_t >= shot_every:
			_shot_t = 0.0
			_take_shot()
	if _probe == "ui":
		_probe_ui()
	elif _probe == "goto":
		_probe_goto()
	if quit_after > 0.0 and Game.time >= quit_after:
		_finish("timeout" if bot_mode in ["win", "lose"] else "quit")


func _probe_ui() -> void:
	if _probe_step == 0 and Game.time >= 3.0:
		_probe_step = 1
		if Game.world != null and not String(Game.scene_id) in Game.NOT_PAUSABLE:
			_send_pause()
		else:
			Game.event("probe_skip", {"scene": Game.scene_id})
	elif _probe_step == 1 and Game.time >= 3.4:
		_probe_step = 2
		var f := get_viewport().gui_get_focus_owner()
		Game.event("probe_focus", {"paused": get_tree().paused, "focus": (f as Button).text if f is Button else "none"})
		_send_back(true)
	elif _probe_step == 2 and Game.time >= 3.5:
		_probe_step = 3
		_send_back(false)
	elif _probe_step == 3 and Game.time >= 3.8:
		_probe_step = 4
		Game.event("probe_after", {"paused": get_tree().paused})


## Back button (pad B / ui_cancel) press or release, like a real tap.
func _send_back(pressed: bool) -> void:
	var e: InputEvent
	if Game.args.has("pad"):
		e = InputEventJoypadButton.new()
		e.button_index = JOY_BUTTON_B
		e.pressed = pressed
	else:
		e = InputEventAction.new()
		e.action = "ui_cancel"
		e.pressed = pressed
	Input.parse_input_event(e)


func _probe_goto() -> void:
	if _probe_step == 0 and Game.time >= 2.0:
		_probe_step = 1
		Game.goto(&"test")
	elif _probe_step == 1 and Game.time >= 2.1:
		_probe_step = 2
		Game.goto(&"title")
	elif _probe_step == 2 and Game.time >= 3.5:
		_probe_step = 3
		Game.event("probe_goto", {"scene": Game.scene_id, "ok": Game.scene_id == &"title"})


func _send_pause() -> void:
	var e: InputEvent
	if Game.args.has("pad"):
		e = InputEventJoypadButton.new()
		e.button_index = JOY_BUTTON_START
		e.pressed = true
	else:
		e = InputEventAction.new()
		e.action = "pause"
		e.pressed = true
	Input.parse_input_event(e)


## `--shot-on=inhale@0.9,bite_start@0.5:2` (with --shots): a shot <delay> game seconds after each of the first <n>
## (default 1) harness events of that name - aimed frames instead of a timed series (--shot-every 0 turns that off).
func _parse_shot_on() -> void:
	for part in str(Game.args.get("shot-on", "")).split(",", false):
		var n := 1
		var p := part
		if p.contains(":"):
			n = maxi(p.get_slice(":", 1).to_int(), 1)
			p = p.get_slice(":", 0)
		var ev := p.get_slice("@", 0)
		_shot_on[ev] = p.get_slice("@", 1).to_float() if p.contains("@") else 0.0
		_shot_on_left[ev] = n


func _shot_later(delay: float) -> void:
	if delay > 0.0:
		await get_tree().create_timer(delay, false).timeout
	if not _finished:
		_take_shot()


func _take_shot() -> void:
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := shots_dir.path_join("shot_%04d.png" % _shot_n)
	_shot_n += 1
	img.save_png(path)
	Game.event("shot", {"file": path.get_file()})


func _finish_later(result: String, secs: float) -> void:
	await get_tree().create_timer(secs, true, false, true).timeout
	_finish(result)


func _finish(result: String) -> void:
	if _finished:
		return
	_finished = true
	if shots_dir != "":
		_take_shot()
	print("[H] t=%.2f defeats=%d victories=%d" % [Game.time, defeats, victories])
	print("[H] result=%s" % result)
	Engine.time_scale = 1.0
	# audio: stop every stream and give the mixer 0.15 s (paused tree) to release playing streams, else they leak at exit
	get_tree().paused = true
	Sfx.shutdown()
	await get_tree().create_timer(0.15, true, false, true).timeout
	get_tree().quit(0 if result in ["victory", "quit"] else 1)
