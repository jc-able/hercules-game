extends SceneTree
## freeze_fix capture probe: records the material signature (what decides the compiled shader) of every
## GeometryInstance3D that enters the tree, and when it was first seen. --cap-out=<dir> saves the materials first
## seen after fight_start as .tres (one per signature).
var _seen := {}       # sig -> [time, node kind, node path, after_fight]
var _mats := {}       # sig -> Material
var _fight := false
var _out := ""


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--cap-out="):
			_out = String(a).substr(10)
	node_added.connect(_on_added)
	change_scene_to_file("res://scenes/main.tscn")


func _process(_d: float) -> bool:
	if not _fight:
		var b := get_first_node_in_group("boss")
		if b != null and String(b.get("state")) != "" and String(b.get("state")) != "idle":
			_fight = true
			print("[C] fight seen t=%.2f" % _gt())
			# hidden geometry present at fight start counts as before
			for n in root.find_children("*", "GeometryInstance3D", true, false):
				_scan(n, false)
	return false


func _gt() -> float:
	var g := root.get_node_or_null("Game")
	return float(g.get("time")) if g != null else 0.0


func _on_added(n: Node) -> void:
	if n is GeometryInstance3D:
		_scan.call_deferred(n, _fight)


func _sig(m: Material) -> String:
	if m is ShaderMaterial:
		var s: Shader = (m as ShaderMaterial).shader
		return "SM:" + (str(hash(s.code)) if s != null else "null")
	var parts := [m.get_class()]
	for p in m.get_property_list():
		if not (p.usage & PROPERTY_USAGE_STORAGE):
			continue
		var v = m.get(p.name)
		if p.type == TYPE_BOOL or (p.type == TYPE_INT and p.hint == PROPERTY_HINT_ENUM):
			if v != m.property_get_revert(p.name) if m.property_can_revert(p.name) else true:
				parts.append("%s=%s" % [p.name, str(v)])
		elif p.type == TYPE_OBJECT and v is Texture:
			parts.append("%s=tex" % p.name)
	return ",".join(parts)


func _mats_of(n: GeometryInstance3D) -> Array:
	var out := []
	if n.material_override != null:
		out.append(n.material_override)
	var mesh: Mesh = null
	if n is MeshInstance3D:
		mesh = (n as MeshInstance3D).mesh
		if mesh != null:
			for i in mesh.get_surface_count():
				var o = (n as MeshInstance3D).get_surface_override_material(i)
				if o != null:
					out.append(o)
	elif n is CPUParticles3D:
		mesh = (n as CPUParticles3D).mesh
	elif n is GPUParticles3D:
		mesh = (n as GPUParticles3D).draw_pass_1
		if (n as GPUParticles3D).process_material != null:
			out.append((n as GPUParticles3D).process_material)
	elif n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh != null:
		mesh = (n as MultiMeshInstance3D).multimesh.mesh
	if mesh != null:
		for i in mesh.get_surface_count():
			var sm := mesh.surface_get_material(i)
			if sm != null:
				out.append(sm)
	var more := []
	for m in out:
		var nx = m.next_pass if m != null else null
		while nx != null:
			more.append(nx)
			nx = nx.next_pass
	return out + more


func _scan(n: Node, after: bool) -> void:
	if not is_instance_valid(n) or not n.is_inside_tree():
		return
	var gi := n as GeometryInstance3D
	for m in _mats_of(gi):
		if m == null:
			continue
		var kind := n.get_class() + ("/sh" if gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF else "")
		var sig: String = kind + "|" + _sig(m)
		if _seen.has(sig):
			continue
		var owner_script := ""
		var p := n
		while p != null and owner_script == "":
			if p.get_script() != null:
				owner_script = (p.get_script() as Script).resource_path.get_file()
			p = p.get_parent()
		_seen[sig] = [_gt(), kind, owner_script, after, n.name]
		_mats[sig] = m
		if after:
			print("[C] NEW t=%.2f %s by %s node=%s sig=%s" % [_gt(), kind, owner_script, n.name, sig.substr(0, 240)])


func _finalize() -> void:
	var n_after := 0
	for sig in _seen:
		if _seen[sig][3]:
			n_after += 1
			if _out != "":
				DirAccess.make_dir_recursive_absolute(_out)
				var k: String = String(_seen[sig][1])
				var kind := "cpu" if k.begins_with("CPUParticles3D") else ("gpu" if k.begins_with("GPUParticles3D") else "mesh")
				if k.ends_with("/sh"):
					kind += "_sh"
				var m: Material = _mats[sig].duplicate(true)
				var path := "%s/%s_%08x.tres" % [_out, kind, hash(sig) & 0xffffffff]
				ResourceSaver.save(m, path)
				print("[C] saved %s (%s, first t=%.2f)" % [path.get_file(), _seen[sig][2], _seen[sig][0]])
	print("[C] signatures total=%d first seen after fight start=%d" % [_seen.size(), n_after])
