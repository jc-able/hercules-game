extends SceneTree
## Builds res://assets/fx/warm_fx.tscn from the materials fx_capture.gd saved (--cap-dir=<dir>): one tiny node per
## material, of the kind that drew it in the fight (mesh, CPU particles, GPU particles; "_sh" = casts shadows).
## ArenaBase.prewarm() draws this scene once under the island title card.
## usage: Godot --headless --path game --script <this> -- --cap-dir=<dir> [--out=res://assets/fx/warm_fx.tscn]
func _initialize() -> void:
	var dir := ""
	var out := "res://assets/fx/warm_fx.tscn"
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--cap-dir="):
			dir = String(a).substr(10)
		if String(a).begins_with("--out="):
			out = String(a).substr(6)
	var root := Node3D.new()
	root.name = "WarmFx"
	var files := DirAccess.get_files_at(dir)
	files.sort()
	var n := 0
	for f in files:
		if not f.ends_with(".tres"):
			continue
		var m := ResourceLoader.load(dir.path_join(f), "", ResourceLoader.CACHE_MODE_IGNORE) as Material
		if m == null:
			continue
		m = m.duplicate(true)       # no resource_path: saved inside the scene, not as a link to the capture folder
		var kind := f.get_basename()
		var shadow := "_sh" in kind
		var q := QuadMesh.new()
		q.size = Vector2(0.004, 0.004)
		var node: GeometryInstance3D
		if kind.begins_with("cpu"):
			var p := CPUParticles3D.new()
			p.amount = 1
			p.lifetime = 1.0
			p.preprocess = 0.5
			p.gravity = Vector3.ZERO
			p.initial_velocity_min = 0.0
			p.initial_velocity_max = 0.0
			q.material = m
			p.mesh = q
			node = p
		elif kind.begins_with("gpu"):
			var g := GPUParticles3D.new()
			g.amount = 1
			g.lifetime = 1.0
			if m is ParticleProcessMaterial or (m is ShaderMaterial and (m as ShaderMaterial).shader != null and (m as ShaderMaterial).shader.get_mode() == Shader.MODE_PARTICLES):
				g.process_material = m
				q.material = StandardMaterial3D.new()
			else:
				g.process_material = ParticleProcessMaterial.new()
				q.material = m
			g.draw_pass_1 = q
			node = g
		else:
			var mi := MeshInstance3D.new()
			mi.mesh = q
			mi.material_override = m
			node = mi
		node.name = kind
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.position = Vector3((n % 8) * 0.005, (n / 8) * 0.005, 0.0)
		root.add_child(node)
		node.owner = root
		n += 1
	var ps := PackedScene.new()
	ps.pack(root)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out.get_base_dir()))
	var err := ResourceSaver.save(ps, out)
	print("[W] %d materials -> %s (err %d)" % [n, out, err])
	root.free()
	quit()
