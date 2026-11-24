class_name ArenaBase
extends Node3D
## Base for every boss arena. Flow: build_environment() -> player -> spawn_boss() -> island title card ->
## boss.start_fight() (+ lock-on) -> on `defeated`: "LABOR COMPLETE", Game.mark_defeated, then the sea (the "ending"
## scene the first time all three bosses are beaten) -> on player death: "DEFEATED", then the same arena is rebuilt.
## Subclass: set arena_id + radius in _init(), override build_environment() and spawn_boss() (and player_spawn()).
## spawn_boss() should return the boss UNPARENTED: the base then sets boss.arena and boss.player before add_child,
## so both are valid inside the boss's _ready()/_build(). (`player` already exists when spawn_boss() runs.)

var arena_id: StringName = &"test"
var radius := 30.0
var player: Player
var boss: BossBase
var hud: Hud
var opts: Dictionary = {}
var victory_scene: StringName = &"sea"
var title_text := ""
var subtitle_text := ""
var title_card_time := 2.4
var ended := false


## Called by Game before the arena enters the tree.
func setup(o: Dictionary) -> void:
	opts = o


func _ready() -> void:
	var t: Array = Tuning.ISLAND_TITLES.get(String(arena_id), [String(arena_id).capitalize(), ""])
	if title_text == "":
		title_text = t[0]
	if subtitle_text == "":
		subtitle_text = t[1]
	build_environment()
	EnvKit.boundary(self, radius)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	player.global_position = player_spawn()
	boss = spawn_boss()
	if boss == null:
		push_error("ArenaBase %s: spawn_boss() returned null" % arena_id)
		return
	boss.arena = self
	boss.player = player
	if boss.get_parent() == null:
		add_child(boss)
	var to := boss.global_position - player.global_position
	to.y = 0.0
	if to.length() > 0.1:
		player.facing = to.normalized()
	player.camera.snap_behind()
	hud = Hud.new()
	add_child(hud)
	hud.bind_player(player)
	hud.bind_boss(boss)
	player.died.connect(_on_player_died)
	boss.defeated.connect(_on_boss_defeated)
	Game.capture_mouse(true)
	Sfx.stop_music(1.0)               # the island's fight music starts with the fight (below), after the title card
	_intro()


func _intro() -> void:
	var restart := bool(opts.get("restart", false))
	var secs := 1.0 if restart else title_card_time
	if not restart:
		hud.show_title_card(title_text, subtitle_text, secs)
		Sfx.play("title_card")
		prewarm([self])
	await get_tree().create_timer(secs, false).timeout
	if ended or not is_instance_valid(boss):
		return
	player.set_lock_target(boss)
	boss.start_fight()
	Sfx.music("music_" + String(arena_id), 0.6)


## Keep the mouse captured while this scene runs (Game re-captures after the pause menu).
func wants_mouse_captured() -> bool:
	return true


# ------------------------------------------------------------------ first-use warm-up (docs/notes/freeze_fix.md)
## Materials of the effects that are built at the moment they are used (sparks, dust, telegraph decals, slam ring,
## crack, debris...), captured from bot runs. Regenerate after an effect gets a new kind of material:
## tools/probes/fx_capture.gd, then tools/probes/fx_warm_build.gd (both explained in tools/probes/README.md).
const WARM_FX_SCENE := "res://assets/fx/warm_fx.tscn"
const WARM_FRAMES := 4
const WARM_SIZE := 0.004          # metres: a proxy is smaller than a pixel at WARM_DIST
const WARM_DIST := 1.5


## Draws every material once, tiny, just in front of the camera, while the island title card covers the start:
## all geometry under `roots` (hidden effects built ahead included: beams, fire, weak-point glows, props behind the
## camera) plus WARM_FX_SCENE. The GPU then compiles each shader now instead of the first time the effect appears
## (a ~0.3 s freeze per effect on a cold shader cache). Touches no game state, physics or Game.rng; skipped headless.
func prewarm(roots: Array) -> void:
	# the HUD's lock reticle too (canvas): its first draw at fight_start compiled a pipeline (57 ms cold, last_fixes)
	if hud != null and not Game.args.has("no-prewarm"):
		hud.warm_canvas(WARM_FRAMES)
	await ArenaBase.prewarm_in(self, roots)


## The same for any scene (the sea / flight can call it too): `scene` hosts the proxies for WARM_FRAMES frames.
static func prewarm_in(scene: Node, roots: Array, frames := WARM_FRAMES) -> void:
	if DisplayServer.get_name() == "headless" or scene == null or not scene.is_inside_tree():
		return
	if Game.args.has("no-prewarm"):         # harness A/B: measure the game without the warm-up
		return
	var tree := scene.get_tree()
	var cam := scene.get_viewport().get_camera_3d()
	if cam == null:
		await tree.process_frame
		if not is_instance_valid(scene):
			return
		cam = scene.get_viewport().get_camera_3d()
		if cam == null:
			return
	var holder := Node3D.new()
	holder.name = "Prewarm"
	cam.add_child(holder)
	holder.position = Vector3(0, 0, -WARM_DIST)
	var seen := {}
	var n := 0
	for r in roots:
		if not (r is Node) or not is_instance_valid(r):
			continue
		var geo: Array = (r as Node).find_children("*", "GeometryInstance3D", true, false)
		if r is GeometryInstance3D:
			geo.append(r)
		for g in geo:
			if g is GeometryInstance3D and not holder.is_ancestor_of(g):
				n = _warm_proxies(holder, g, seen, n)
	if ResourceLoader.exists(WARM_FX_SCENE):
		var ps := load(WARM_FX_SCENE) as PackedScene
		if ps != null:
			holder.add_child(ps.instantiate())
	# the core effects through their own code (one particle each, smaller than a pixel): sparks and dust
	Fx.spark(holder, holder.global_position, Color.WHITE, 1, WARM_SIZE)
	Fx.dust(holder, holder.global_position, WARM_SIZE)
	Fx.warm_strike(holder, WARM_SIZE)   # feedback 2: cut streak, star/ring, ichor, wound decal
	for i in frames:
		await tree.process_frame
	if is_instance_valid(holder):
		holder.queue_free()


## One tiny proxy per material of `g` not seen yet, of g's kind (mesh / CPU particles / GPU particles) and with its
## shadow setting, so the same shader versions are compiled. Returns the new proxy count.
static func _warm_proxies(holder: Node3D, g: GeometryInstance3D, seen: Dictionary, n: int) -> int:
	var mats: Array = []
	var proc: Material = null
	if g.material_override != null:
		mats.append(g.material_override)
	var mesh: Mesh = null
	if g is MeshInstance3D:
		mesh = (g as MeshInstance3D).mesh
		if mesh != null:
			for i in mesh.get_surface_count():
				mats.append((g as MeshInstance3D).get_surface_override_material(i))
	elif g is CPUParticles3D:
		mesh = (g as CPUParticles3D).mesh
	elif g is GPUParticles3D:
		mesh = (g as GPUParticles3D).draw_pass_1
		proc = (g as GPUParticles3D).process_material
	elif g is MultiMeshInstance3D and (g as MultiMeshInstance3D).multimesh != null:
		mesh = (g as MultiMeshInstance3D).multimesh.mesh
	if mesh != null:
		for i in mesh.get_surface_count():
			mats.append(mesh.surface_get_material(i))
	for i in mats.size():
		var nx = mats[i].next_pass if mats[i] != null else null
		while nx != null:
			mats.append(nx)
			nx = nx.next_pass
	if proc != null and not seen.has(proc.get_instance_id()):
		seen[proc.get_instance_id()] = true
		mats.append(null)       # make sure a GPU proxy is built for a new process material
	for m in mats:
		if m != null and seen.has(m.get_instance_id()):
			continue
		if m == null and not (g is GPUParticles3D):
			continue
		if m != null:
			seen[m.get_instance_id()] = true
		var q := QuadMesh.new()
		q.size = Vector2(WARM_SIZE, WARM_SIZE)
		var node: GeometryInstance3D
		if g is CPUParticles3D:
			var p := CPUParticles3D.new()
			p.amount = 1
			p.preprocess = 0.5
			p.gravity = Vector3.ZERO
			p.initial_velocity_min = 0.0
			p.initial_velocity_max = 0.0
			q.material = m
			p.mesh = q
			node = p
		elif g is GPUParticles3D:
			var gp := GPUParticles3D.new()
			gp.amount = 1
			gp.process_material = proc if proc != null else ParticleProcessMaterial.new()
			q.material = m
			gp.draw_pass_1 = q
			node = gp
		else:
			var mi := MeshInstance3D.new()
			mi.mesh = q
			mi.material_override = m
			node = mi
		node.cast_shadow = g.cast_shadow
		holder.add_child(node)
		node.position = Vector3((n % 16) * WARM_SIZE * 1.5, (n / 16) * WARM_SIZE * 1.5, 0.0)
		n += 1
	return n


# ------------------------------------------------------------------ overrides
## Override: floor, props, light, sky. Default: sunny sand disc with a sea and a painted sky.
func build_environment() -> void:
	EnvKit.sky(self)
	EnvKit.sun(self)
	EnvKit.floor_disc(self, radius, Color(0.86, 0.76, 0.56))
	EnvKit.sea(self, 3000.0, -3.0)


## Override: create and position the boss and return it unparented (set `position`, not global_position);
## the base sets boss.arena / boss.player and adds it. A boss added here by the module still works, but then
## arena and player are null inside its _ready()/_build().
func spawn_boss() -> BossBase:
	push_error("ArenaBase.spawn_boss() not overridden")
	return null


## Override: where the hero starts (default: south side of the ring, facing the boss).
func player_spawn() -> Vector3:
	return Vector3(0, 0.1, radius * 0.5)


# ------------------------------------------------------------------ telegraphs
## A circle warning decal at `center` that fills over `seconds` (returns it so it can be moved or cancelled).
func telegraph_circle(center: Vector3, r: float, seconds: float, color := Color.RED) -> Telegraph:
	var t := Telegraph.circle(r, seconds, color)
	add_child(t)
	t.global_position = center
	return t


## A cone/arc warning decal from `origin` along `dir`.
func telegraph_cone(origin: Vector3, dir: Vector3, half_angle_deg: float, length: float, seconds: float, color := Color.RED) -> Telegraph:
	var t := Telegraph.cone(half_angle_deg, length, seconds, color)
	add_child(t)
	t.global_position = origin
	t.aim(dir)
	return t


## A ring warning decal between `inner` and `outer` radius.
func telegraph_ring(center: Vector3, inner: float, outer: float, seconds: float, color := Color.RED) -> Telegraph:
	var t := Telegraph.ring(inner, outer, seconds, color)
	add_child(t)
	t.global_position = center
	return t


# ------------------------------------------------------------------ end of fight
func _on_boss_defeated() -> void:
	if ended:
		return
	ended = true
	player.set_lock_target(null)
	Game.mark_defeated(boss.boss_id)
	Game.event("victory", {"boss": boss.boss_id})
	# the fall stays in view: the card waits until the boss's top is below it (or has stopped falling), upper third
	var wait := 0.0
	var lowest := -1.0
	var still := 0.0
	var top := -1.0
	var first := INF
	# at the latest near the end of the death clip (the Cyclops kneels ~2 s before he falls back)
	var latest := clampf(boss.visual.clip_length(&"death", 3.0) * Tuning.VICTORY_CARD_CLIP_SHARE, Tuning.VICTORY_CARD_MIN_DELAY, Tuning.VICTORY_CARD_MAX_DELAY)
	while wait < latest:
		await get_tree().create_timer(0.05, false).timeout
		wait += 0.05
		top = _boss_screen_top()
		first = minf(first, top)
		if top > lowest + 0.003:
			lowest = top
			still = 0.0
		else:
			still += 0.05
		# "stopped falling" counts once the top has dropped a little and is already low (a kneel is not the end)
		var fell := lowest - first >= 0.03 and top >= Tuning.VICTORY_CARD_STILL_TOP
		if wait >= Tuning.VICTORY_CARD_MIN_DELAY and (top >= Tuning.VICTORY_CARD_CLEAR or (fell and still >= Tuning.VICTORY_CARD_STILL)):
			break
	Game.event("victory_card", {"after": snappedf(wait, 0.05), "boss_top": snappedf(top, 0.01)})
	# the emptied boss bar + name and the reticle leave with the card (as on the DEFEATED path)
	hud.set_boss_visible(false)
	hud.show_overlay("LABOR COMPLETE", "%s is overcome" % boss.display_name, Tuning.VICTORY_CARD_HOLD, Color(1.0, 0.82, 0.35), 0.0, true)
	await get_tree().create_timer(Tuning.VICTORY_CARD_HOLD, false).timeout
	var next := victory_scene
	if next == &"sea" and Game.ending_pending():
		next = &"ending"          # the first time all three are beaten; the ending scene then goes to the sea
	Game.goto(next, {"from": String(arena_id)})


## Highest point of the boss on screen as a fraction of the screen height (0 = top edge; it can be < 0 above the
## frame), from the boss's live top points; -1 when unknown (no camera, no boss).
func _boss_screen_top() -> float:
	var cam := get_viewport().get_camera_3d()
	if cam == null or not is_instance_valid(boss) or boss.visual == null:
		return -1.0
	var h := maxf(get_viewport().get_visible_rect().size.y, 1.0)
	var best := INF
	for p in boss.visual.live_top_points():
		if not cam.is_position_behind(p):
			best = minf(best, cam.unproject_position(p).y / h)
	return best if best < INF else -1.0


func _on_player_died() -> void:
	if ended:
		return
	ended = true
	boss.stop_fight()
	# the fall stays readable: boss bar + reticle hidden at once, DEFEATED fades in after the fall, in the upper third
	hud.set_boss_visible(false)
	hud.show_overlay("DEFEATED", "The labor begins again", Tuning.DEFEAT_HOLD - Tuning.DEFEAT_OVERLAY_DELAY - 0.75,
		Color(0.85, 0.2, 0.15), Tuning.DEFEAT_OVERLAY_DELAY, true)
	Sfx.stop_music(0.4)
	Sfx.play("defeat")
	Game.event("defeat", {"boss": boss.boss_id, "boss_hp": boss.hp})
	await get_tree().create_timer(Tuning.DEFEAT_HOLD, false).timeout   # the hero lies on the floor ~2 s before the fade
	Game.restart_scene()
