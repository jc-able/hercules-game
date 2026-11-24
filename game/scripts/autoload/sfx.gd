extends Node
## Autoload `Sfx` (audio agent): every sound in the game goes through here.
## Manifest: res://assets/audio/audio.json (built by work/audio/process.py from docs/audio_list.json):
##   name -> {file, bus, volume_db, pitch_random, loop, loop_offset?, max_distance, unit_size, positional}
## One-shots:  play(name, pos = null, volume_db = 0.0, pitch = 1.0)   pos: Vector3 (positional sounds only) or null
## Loops:      loop(name, at = null, volume_db = 0.0) -> int id   (alias play_loop)
##             at = Node3D: the player follows it and dies with it; Vector3: fixed point; other Node: plays (2D) while
##             that node lives; null: global until stop_loop. Loops at a Vector3 / null also stop on the next scene change.
##             stop_loop(id, fade = 0.15), set_loop_volume(id, db_offset), move_loop(id, pos), loop_node(id)
## Music:      music(name, fade = 1.0) (crossfade; empty name = stop), stop_music(fade = 1.0), play_music(name) (legacy)
## Buses:      Master (hard limiter) <- Music, SFX, UI. set_bus_volume(bus, linear) / get_bus_volume(bus) for a settings page.
## Volumes add up: manifest volume_db + the call's volume_db. Positional sounds are AudioStreamPlayer3D (listener = camera).
## Missing name or file: one warning, no crash, no sound. `--sfx-log` (harness runs) prints `[H] event=sfx name=...` for
## every play / loop / music start, and a per-name count at exit.
## Names: docs/audio_list.json. ALIASES maps old or unregistered names to registry names.

const MANIFEST := "res://assets/audio/audio.json"
const AUDIO_DIR := "res://assets/audio/"
const SFX_DIR := "res://assets/audio/sfx/"          # fallback for names the manifest does not list
const MUSIC_DIR := "res://assets/audio/music/"
const EXTS := ["wav", "ogg", "mp3"]
const POOL_2D := 16
const POOL_3D := 32
const BUSES := ["Music", "SFX", "UI"]
const RETRIGGER_GAP := 0.03       ## the same name started again within this many seconds is skipped (stacked doubles)
const ALIASES := {
	"swing": "sword_swing", "strike": "sword_hit", "impact": "cyclops_slam", "guard_break": "block",
	"boss_hurt": "cyclops_hurt", "dummy_hurt": "cyclops_hurt", "dummy_death": "cyclops_death",
	"dummy_sweep_warn": "cyclops_sweep_warn", "dummy_sweep": "cyclops_sweep", "dummy_slam_warn": "cyclops_slam_warn",
	"dummy_slam": "cyclops_slam", "dummy_roar": "cyclops_roar", "dummy_step": "cyclops_step", "test_step": "cyclops_step",
	"title": "music_title", "flight": "music_flight", "music_test": "music_cyclops", "music_ending": "music_title",
	"music_home": "music_title", "music_sea": "music_flight", "step": "step_dirt", "footstep": "step_dirt",
	"telegraph": "", "hydra_fire_warn": "hydra_fire_sweep_warn", "hydra_fire_loop": "hydra_fire",
	"medusa_tail_warn": "medusa_tail_swipe_warn", "medusa_tail": "medusa_tail_swipe", "medusa_stunned": "medusa_stun",
}
## Footstep surface per scene: [sound, pitch]. Any footstep (step_dirt / step_stone / step / footstep) played in a listed
## scene uses this sound at this pitch, whatever the caller asked for; other scenes keep the caller's choice
## (player.gd asks step_stone in medusa, step_dirt elsewhere). Sanctuary = pale marble; volcano = black basalt (rock,
## pitched lower so it sounds heavier and duller than marble).
const STEP_SURFACES := {
	&"medusa": ["step_stone", 1.0],
	&"hydra": ["step_stone", 0.8],
}
const STEP_NAMES := ["step_dirt", "step_stone"]

var log_plays := false            ## --sfx-log: harness event per play
var counts := {}                  ## name -> times started (one-shots, loops, music)

var _manifest := {}               # name -> Dictionary
var _cache := {}                  # "name" / "name#loop" -> AudioStream or null
var _warned := {}
var _last_start := {}             # name -> Time ticks msec
var _p2d: Array[AudioStreamPlayer] = []
var _p3d: Array[AudioStreamPlayer3D] = []
var _n2d := 0
var _n3d := 0
var _loops := {}                  # id -> {node, name, base_db, world (Node or null), owned (bool)}
var _next_loop := 1
var _music: Array[AudioStreamPlayer] = []
var _music_cur := 0
var _music_name := ""
var _music_tween: Tween
var _rng := RandomNumberGenerator.new()   # own RNG: pitch variation never shifts the seeded gameplay randomness


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_rng.randomize()
	_ensure_buses()
	_load_manifest()
	for i in POOL_2D:
		var p := AudioStreamPlayer.new()
		p.name = "P2D_%d" % i
		add_child(p)
		_p2d.append(p)
	for i in POOL_3D:
		var p3 := AudioStreamPlayer3D.new()
		p3.name = "P3D_%d" % i
		p3.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p3.panning_strength = 0.8
		add_child(p3)
		_p3d.append(p3)
	for i in 2:
		var m := AudioStreamPlayer.new()
		m.name = "Music_%d" % i
		m.bus = _bus("Music")
		add_child(m)
		_music.append(m)
	log_plays = Game.args.has("sfx-log")
	Game.scene_changed.connect(_on_scene_changed)


func _exit_tree() -> void:
	shutdown()
	if log_plays:
		var names := counts.keys()
		names.sort()
		var parts := PackedStringArray()
		for n in names:
			parts.append("%s:%d" % [n, counts[n]])
		print("[H] sfx_counts %s" % ",".join(parts))


## Stops and drops every stream (call right before get_tree().quit(): a stream still held at exit leaks its playback).
func shutdown() -> void:
	for p in _p2d + _music:
		p.stop()
		p.stream = null
	for p3 in _p3d:
		p3.stop()
		p3.stream = null
	for id in _loops.keys():
		var node = _loops[id]["node"]
		if is_instance_valid(node):
			node.call("stop")
			node.set("stream", null)
	_cache.clear()


# ------------------------------------------------------------------ setup
func _ensure_buses() -> void:
	# default_bus_layout.tres normally provides these; build them if it is missing
	for b in BUSES:
		if AudioServer.get_bus_index(b) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")
	var has_limiter := false
	for e in AudioServer.get_bus_effect_count(0):
		if AudioServer.get_bus_effect(0, e) is AudioEffectHardLimiter:
			has_limiter = true
	if not has_limiter:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = -0.5
		AudioServer.add_bus_effect(0, lim)


func _load_manifest() -> void:
	if not FileAccess.file_exists(MANIFEST):
		push_warning("Sfx: %s missing, falling back to file names" % MANIFEST)
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if d is Dictionary and d.get("sounds") is Dictionary:
		_manifest = d["sounds"]
	else:
		push_warning("Sfx: %s unreadable" % MANIFEST)


func _bus(b: String) -> StringName:
	return StringName(b) if AudioServer.get_bus_index(b) != -1 else &"Master"


# ------------------------------------------------------------------ lookup
## Registry name for `name` after ALIASES ("" when the alias says "no sound").
func resolve(name: String) -> String:
	if _manifest.has(name):
		return name
	if ALIASES.has(name):
		return String(ALIASES[name])
	return name


func _entry(name: String) -> Dictionary:
	return _manifest.get(name, {})


## True when a sound exists for this name (after aliases).
func has(name: String) -> bool:
	return _stream(resolve(name), false) != null


func _stream(name: String, as_loop: bool) -> AudioStream:
	if name == "":
		return null
	var key := name + ("#loop" if as_loop else "")
	if _cache.has(key):
		return _cache[key]
	var s: AudioStream = null
	var e := _entry(name)
	if e.has("file") and ResourceLoader.exists(AUDIO_DIR + String(e["file"])):
		s = load(AUDIO_DIR + String(e["file"])) as AudioStream
	else:
		var dir := MUSIC_DIR if name.begins_with("music_") else SFX_DIR
		for x in EXTS:
			var p := "%s%s.%s" % [dir, name, x]
			if ResourceLoader.exists(p):
				s = load(p) as AudioStream
				break
	if s != null and as_loop:
		s = _make_loop(s, float(e.get("loop_offset", 0.0)))
	_cache[key] = s
	return s


## A looping copy (never changes the shared cached resource). WAV loops through loop_mode/loop_end, Ogg/MP3 through `loop`.
func _make_loop(src: AudioStream, offset: float) -> AudioStream:
	var s := src.duplicate() as AudioStream
	if s is AudioStreamWAV:
		var w := s as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = int(offset * float(w.mix_rate))
		w.loop_end = int(round(w.get_length() * float(w.mix_rate)))
	else:
		if "loop" in s:
			s.set("loop", true)
		if "loop_offset" in s:
			s.set("loop_offset", offset)
	return s


func _warn_missing(name: String, why: String) -> void:
	if _warned.has(name):
		return
	_warned[name] = true
	push_warning("Sfx: no sound for '%s' (%s)" % [name, why])
	Game.event("sfx_missing", {"name": name})


func _log(kind: String, name: String, extra := {}) -> void:
	counts[name] = int(counts.get(name, 0)) + 1
	if log_plays:
		var d := {"name": name}
		if kind != "sfx":
			d["kind"] = kind
		d.merge(extra)
		Game.event("sfx", d)


func _pitch(e: Dictionary, pitch: float) -> float:
	var pr := float(e.get("pitch_random", 0.0))
	return pitch * (1.0 + _rng.randf_range(-pr, pr)) if pr > 0.0 else pitch


# ------------------------------------------------------------------ one-shots
## Plays a one-shot; with `pos` (Vector3) a positional sound plays there in 3D. Silent (one warning) when missing.
func play(name: String, pos = null, volume_db := 0.0, pitch := 1.0) -> void:
	var n := resolve(name)
	if n == "":
		return
	if n in STEP_NAMES and STEP_SURFACES.has(Game.scene_id):
		var surf: Array = STEP_SURFACES[Game.scene_id]
		n = String(surf[0])
		pitch *= float(surf[1])
	var s := _stream(n, false)
	if s == null:
		_warn_missing(name, "no file")
		return
	var now := Time.get_ticks_msec()
	if now - int(_last_start.get(n, -100000)) < int(RETRIGGER_GAP * 1000.0):
		return
	_last_start[n] = now
	var e := _entry(n)
	var vol := float(e.get("volume_db", 0.0)) + volume_db
	var bus := _bus(String(e.get("bus", "SFX")))
	if pos is Vector3 and bool(e.get("positional", true)):
		var p3 := _free_3d()
		p3.stream = s
		p3.bus = bus
		p3.volume_db = vol
		p3.pitch_scale = _pitch(e, pitch)
		p3.unit_size = float(e.get("unit_size", 10.0))
		p3.max_distance = float(e.get("max_distance", 200.0))
		p3.global_position = pos
		p3.play()
	else:
		var p := _free_2d()
		p.stream = s
		p.bus = bus
		p.volume_db = vol
		p.pitch_scale = _pitch(e, pitch)
		p.play()
	_log("sfx", n)


## Footstep on the current scene's surface (STEP_SURFACES; packed earth / grass = step_dirt elsewhere).
func footstep(pos = null, volume_db := 0.0) -> void:
	play("step_dirt", pos, volume_db)


func _free_2d() -> AudioStreamPlayer:
	for i in POOL_2D:
		var p := _p2d[(_n2d + i) % POOL_2D]
		if not p.playing:
			_n2d = (_n2d + i + 1) % POOL_2D
			return p
	var q := _p2d[_n2d]          # all busy: steal the oldest round-robin slot
	_n2d = (_n2d + 1) % POOL_2D
	return q


func _free_3d() -> AudioStreamPlayer3D:
	for i in POOL_3D:
		var p := _p3d[(_n3d + i) % POOL_3D]
		if not p.playing:
			_n3d = (_n3d + i + 1) % POOL_3D
			return p
	var q := _p3d[_n3d]
	_n3d = (_n3d + 1) % POOL_3D
	return q


# ------------------------------------------------------------------ loops
## Starts a looping sound and returns its id (0 when the sound is missing). See the header for `at`.
func loop(name: String, at = null, volume_db := 0.0) -> int:
	var n := resolve(name)
	var s := _stream(n, true)
	if s == null:
		_warn_missing(name, "no file")
		return 0
	var e := _entry(n)
	var base := float(e.get("volume_db", 0.0))
	var positional := bool(e.get("positional", false)) and (at is Node3D or at is Vector3)
	var node: Node
	if positional:
		var p3 := AudioStreamPlayer3D.new()
		p3.unit_size = float(e.get("unit_size", 10.0))
		p3.max_distance = float(e.get("max_distance", 200.0))
		p3.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p3.panning_strength = 0.8
		node = p3
	else:
		node = AudioStreamPlayer.new()
	node.name = "Loop_%s_%d" % [n, _next_loop]
	node.set("stream", s)
	node.set("bus", _bus(String(e.get("bus", "SFX"))))
	node.set("volume_db", base + volume_db)
	var owned := at is Node and is_instance_valid(at)
	if owned:
		(at as Node).add_child(node)
	else:
		# into the current scene when there is one (pauses and dies with it), else here until the scene change
		var w = Game.world
		if w != null and is_instance_valid(w) and (w as Node).is_inside_tree():
			(w as Node).add_child(node)
		else:
			add_child(node)
		if positional:
			(node as Node3D).global_position = at
	if node.is_inside_tree():
		node.call("play")
	else:
		node.set("autoplay", true)      # owner not in the tree yet: starts when it enters
	var id := _next_loop
	_next_loop += 1
	_loops[id] = {"node": node, "name": n, "base_db": base, "world": Game.world, "owned": owned}
	_log("loop", n)
	return id


## Same as loop() (name from the audio brief).
func play_loop(name: String, at = null, volume_db := 0.0) -> int:
	return loop(name, at, volume_db)


## Stops a loop started with loop(); fades out over `fade` seconds. Unknown / already freed ids are ignored.
func stop_loop(id: int, fade := 0.15) -> void:
	if not _loops.has(id):
		return
	var node: Node = _loops[id]["node"]
	_loops.erase(id)
	if not is_instance_valid(node):
		return
	if fade <= 0.0 or not node.is_inside_tree():
		node.queue_free()
		return
	var tw := node.create_tween()
	tw.tween_property(node, "volume_db", -60.0, fade)
	tw.tween_callback(node.queue_free)


## Volume of a running loop relative to its manifest volume (dB).
func set_loop_volume(id: int, db_offset: float) -> void:
	var node := loop_node(id)
	if node != null:
		node.set("volume_db", float(_loops[id]["base_db"]) + db_offset)


## Moves a positional loop (no-op for 2D loops).
func move_loop(id: int, pos: Vector3) -> void:
	var node := loop_node(id)
	if node is Node3D and node.is_inside_tree():
		(node as Node3D).global_position = pos


## The player node of a running loop, or null.
func loop_node(id: int) -> Node:
	if not _loops.has(id):
		return null
	var node = _loops[id]["node"]
	if not is_instance_valid(node):
		_loops.erase(id)
		return null
	return node


## True while the loop is alive.
func is_looping(id: int) -> bool:
	return loop_node(id) != null


func _on_scene_changed(_id: StringName) -> void:
	# loops parented to Sfx belong to the scene that started them: Game.world is null while a new scene is being
	# built (its loops are adopted now); loops started under an older scene stop
	for id in _loops.keys():
		var l: Dictionary = _loops[id]
		if bool(l["owned"]):
			if not is_instance_valid(l["node"]):
				_loops.erase(id)
			continue
		var w = l["world"]
		if w == null or (is_instance_valid(w) and w == Game.world):
			l["world"] = Game.world
		else:
			stop_loop(id, 0.3)


# ------------------------------------------------------------------ music
## Crossfades to a music track (loops; intro plays once, then it wraps to the manifest loop_offset).
## The same track already playing continues. Empty name or a missing file fades the music out.
func music(name: String, fade := 1.0) -> void:
	var n := resolve(name) if name != "" else ""
	if n == _music_name and n != "" and _music[_music_cur].playing:
		return
	var s := _stream(n, true) if n != "" else null
	if n != "" and s == null:
		_warn_missing(name, "no music file")
	_music_name = n if s != null else ""
	if _music_tween != null and _music_tween.is_valid():
		_music_tween.kill()
	_music_tween = null
	var old := _music[_music_cur]
	var p: AudioStreamPlayer = null
	if s != null:
		_music_cur = 1 - _music_cur
		p = _music[_music_cur]
		p.stop()
		p.stream = s
		p.bus = _bus(String(_entry(n).get("bus", "Music")))
		p.volume_db = float(_entry(n).get("volume_db", 0.0))
		if fade > 0.0:
			p.volume_db = -40.0
		p.play()
		_log("music", n)
	if fade <= 0.0:
		if old != p:
			old.stop()
		return
	_music_tween = create_tween().set_parallel(true)
	if p != null:
		_music_tween.tween_property(p, "volume_db", float(_entry(n).get("volume_db", 0.0)), fade)
	if old.playing and old != p:
		_music_tween.tween_property(old, "volume_db", -60.0, fade)
		_music_tween.chain().tween_callback(old.stop)
	elif p == null:
		_music_tween.tween_interval(0.01)


## Fades the music out.
func stop_music(fade := 1.0) -> void:
	music("", fade)


## Legacy name (core + world call it): crossfade to `name` over 1 s.
func play_music(name: String) -> void:
	music(name, 1.0)


## Name of the music track playing now ("" when none).
func current_music() -> String:
	return _music_name


# ------------------------------------------------------------------ settings hooks
## Linear volume 0..1 of a bus ("Master", "Music", "SFX", "UI") for a settings page.
func set_bus_volume(bus: String, linear: float) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i != -1:
		AudioServer.set_bus_volume_db(i, linear_to_db(clampf(linear, 0.0, 1.0)))
		AudioServer.set_bus_mute(i, linear <= 0.001)


func get_bus_volume(bus: String) -> float:
	var i := AudioServer.get_bus_index(bus)
	return db_to_linear(AudioServer.get_bus_volume_db(i)) if i != -1 else 1.0
