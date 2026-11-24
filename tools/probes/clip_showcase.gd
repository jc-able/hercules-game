extends SceneTree
## Clip showcase (lead tool): loads one character through the game's own loader and saves N evenly spaced poses of
## EVERY clip from a three-quarter front camera, so a whole character's animation can be judged on one sheet.
##   tools/godot_bg/gdwin --path game --resolution 960x540 --script $PWD/tools/probes/clip_showcase.gd -- \
##       --harness --id=cyclops --out=$PWD/work/<role>/showcase/cyclops [--n=8] [--yaw=35] [--zoom=1.3] [--only=idle,walk]
## Then: python3 tools/probes/clip_showcase_sheet.py <out dir> <sheet.jpg> [title]

const PROPS := {
	"hercules": [["hand_r", "res://assets/props/sword.glb"], ["forearm_l", "res://assets/props/shield.glb"]],
	"cyclops": [["hand_ur", "res://assets/props/club.glb"]],
}

var id := "hercules"
var out := ""
var n := 8
var yaw := 35.0
var only: PackedStringArray = []
var zoom := 1.3                 # camera distance = zoom x the larger of height and width (smaller = closer)


func _init() -> void:
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--id="):
			id = s.substr(5)
		elif s.begins_with("--out="):
			out = s.substr(6)
		elif s.begins_with("--n="):
			n = int(s.substr(4))
		elif s.begins_with("--yaw="):
			yaw = float(s.substr(6))
		elif s.begins_with("--zoom="):
			zoom = float(s.substr(7))
		elif s.begins_with("--only="):
			only = s.substr(7).split(",")
	_run.call_deferred()


func _run() -> void:
	for i in 3:
		await process_frame
	var game := get_root().get_node_or_null("Game")
	if game != null and game.get("world") != null and is_instance_valid(game.world):
		game.world.queue_free()
		game.world = null
	for c in get_root().get_children():          # hide HUD layers the start scene may have left
		if c is CanvasLayer:
			c.visible = false
	var root := Node3D.new()
	get_root().add_child(root)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.86, 0.90, 0.95)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.66, 0.64, 0.62)
	env.environment.ambient_light_energy = 0.85
	env.environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 35, 0)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 120.0
	root.add_child(sun)
	var floor_mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(160, 160)
	floor_mi.mesh = pm
	floor_mi.material_override = CharacterVisual.make_toon(Color(0.60, 0.56, 0.50), null, 0.0, 0.0)
	root.add_child(floor_mi)
	var v := CharacterVisual.create(StringName(id))
	root.add_child(v)
	for p in PROPS.get(id, []):
		if v.socket(StringName(p[0])) != null and ResourceLoader.exists(p[1]):
			v.attach_prop(StringName(p[0]), p[1])
	var cam := Camera3D.new()
	cam.fov = 38.0
	cam.far = 800.0
	root.add_child(cam)
	cam.current = true
	await process_frame
	await process_frame
	var h: float = maxf(v.model_top(), 1.0)
	var size: Dictionary = v.manifest.get("size", {})
	var wide: float = maxf(float(size.get("width", h)), float(size.get("length", h)))
	var r: float = maxf(h, wide) * zoom
	var a := deg_to_rad(yaw)
	cam.position = Vector3(sin(a) * r, h * 0.62, cos(a) * r)        # the model faces +Z: a three-quarter front view
	cam.look_at(Vector3(0, h * 0.47, 0))
	var clips: Dictionary = v.manifest.get("clips", {})
	var names: Array = clips.keys()
	var info := {"id": id, "n": n, "clips": []}
	DirAccess.make_dir_recursive_absolute(out)
	for c in names:
		if not only.is_empty() and not only.has(String(c)):
			continue
		var length: float = v.clip_length(StringName(c), 1.0)
		var loop := bool((clips[c] as Dictionary).get("loop", false))
		for i in n:
			var t: float = length * float(i) / float(n) if loop else length * float(i) / float(maxi(n - 1, 1))
			v.play(StringName(c), 0.0)
			v._anim.seek(minf(t, length - 0.001), true)
			v._anim.speed_scale = 0.0
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			var img := get_root().get_texture().get_image()
			img.save_png("%s/%s__%02d.png" % [out, c, i])
		info["clips"].append({"name": String(c), "length": length, "loop": loop})
		print("[P] %s %.2fs loop=%s" % [c, length, loop])
	var f := FileAccess.open(out + "/showcase.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(info))
	f.close()
	quit()
