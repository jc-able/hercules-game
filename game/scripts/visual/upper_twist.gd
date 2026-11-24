extends SkeletonModifier3D
## Turns the upper body about the vertical axis on top of the playing clip (CharacterVisual.set_upper_twist()):
## `angle` radians shared equally by the `spine` bones (children inherit, so the chest ends up turned by the whole
## angle) and `head_extra` more shared by the `head` bones (neck, head). + = to the character's left, like rotation.y.
## The skeleton restores the clip's own pose after every update, so nothing accumulates.

var spine := PackedInt32Array()      # bone indices, parent first
var head := PackedInt32Array()
var angle := 0.0
var head_extra := 0.0


func _process_modification_with_delta(_delta: float) -> void:
	if is_zero_approx(angle) and is_zero_approx(head_extra):
		return
	var skel := get_skeleton()
	if skel == null:
		return
	var up := (skel.global_transform.basis.inverse() * Vector3.UP).normalized()
	_turn(skel, spine, angle, up)
	_turn(skel, head, head_extra, up)


func _turn(skel: Skeleton3D, bones: PackedInt32Array, total: float, up: Vector3) -> void:
	if bones.is_empty() or is_zero_approx(total):
		return
	var step := Basis(up, total / float(bones.size()))
	for b in bones:
		var pose := skel.get_bone_global_pose(b)
		pose.basis = step * pose.basis
		skel.set_bone_global_pose(b, pose)
