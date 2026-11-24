extends SkeletonModifier3D
## Cross-fade at the skeleton (core_polish2): CharacterVisual.play() on a frame-clock character (hero, Pegasus) calls
## start(seconds); from then on the bones ease (sine in-out) from the pose that was ON SCREEN at that moment to the new
## clip's live pose. Unlike the AnimationPlayer's own cross-fade it lasts real seconds whatever the play speed, and a
## change started during another fade begins from where the body is (no pop). It must run first among the modifiers
## (CharacterVisual moves it there), so the upper twist and the socket aims act on the faded pose.

var _from: Array[Transform3D] = []
var _last: Array[Transform3D] = []
var _t := 0.0
var _len := 0.0


## Fade from the current on-screen pose over `seconds` (0 = cut).
func start(seconds: float) -> void:
	var skel := get_skeleton()
	if skel == null:
		return
	if _last.size() != skel.get_bone_count():
		_last.resize(skel.get_bone_count())
		for b in skel.get_bone_count():
			_last[b] = skel.get_bone_pose(b)
	_from = _last.duplicate()
	_len = maxf(seconds, 0.0)
	_t = 0.0


func fading() -> bool:
	return _t < _len


func _process_modification_with_delta(delta: float) -> void:
	var skel := get_skeleton()
	if skel == null:
		return
	var n := skel.get_bone_count()
	if _last.size() != n:
		_last.resize(n)
	if _t < _len and _from.size() == n:
		_t += delta
		var u := clampf(_t / _len, 0.0, 1.0)
		var k := 0.5 - 0.5 * cos(u * PI)
		for b in n:
			var f := _from[b]
			var p := skel.get_bone_pose_position(b)
			var r := skel.get_bone_pose_rotation(b)
			var s := skel.get_bone_pose_scale(b)
			var fr := f.basis.get_rotation_quaternion()
			var np := f.origin.lerp(p, k)
			var nr := fr.slerp(r, k)
			var ns := f.basis.get_scale().lerp(s, k)
			skel.set_bone_pose_position(b, np)
			skel.set_bone_pose_rotation(b, nr)
			skel.set_bone_pose_scale(b, ns)
			_last[b] = Transform3D(Basis(nr) * Basis.from_scale(ns), np)
		return
	for b in n:
		_last[b] = skel.get_bone_pose(b)
