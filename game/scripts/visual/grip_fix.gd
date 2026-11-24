extends SkeletonModifier3D
## Sword grip (feedback 2, 2026-11-23): the owner saw Hercules hold the sword "with his hands backwards". Cause: the
## clips pose the sword hand with the knuckles forward and the thumb toward the body, and the old socket ran the grip
## along the fingers, so the blade left the hand through the knuckles / little-finger side. Now the socket puts the grip
## THROUGH the closed fist (along the knuckle line, blade out of the thumb side), and this modifier turns the hand
## (a forearm twist shared between forearm and hand, then a small wrist bend) so the blade points where the clip
## authored it (strikes, block, roll: the swing and the hit volume are unchanged) or, in a carry, along `carry_dir`.
## Runs after the clip, the pose fade and the upper twist; the skeleton restores the clip pose every update.

var visual: Node = null              # CharacterVisual (current_clip)
var hand := -1
var forearm := -1
var blade_new := Vector3.UP          # blade direction in the hand bone frame with the fist socket
var blade_old := Vector3.UP          # blade direction in the hand bone frame the clips were authored with
var forearm_share := 0.45            # share of the twist taken by the forearm (the rest by the hand)
var swing_max := deg_to_rad(40.0)    # wrist bend limit after the twist
var carry_dir := Vector3.ZERO        # skeleton space; set by CharacterVisual.set_socket_aim()
var carry_w := 0.0
var clip_dirs := {}                  # clip name -> skeleton-space dir (a carry the clip itself asks for, e.g. ride)
var last_err := 0.0                  # degrees left between the blade and its target after the turn (probe)
var twist_rate := deg_to_rad(720.0)  # rad/s the twist may change (a gait change or a carry blend-out turned the hand
									 # 150 deg in 5 frames at 30 fps); the twist is unwrapped against the last frame's
var twist_max := deg_to_rad(230.0)   # never turn the forearm + hand further than this from the clip's own
var _tw := 0.0
var _tw_has := false
# feedback 2 re-fix (review): a clip_dirs clip (the rider's `ride`) eases in/out over clip_dir_blend s instead of
# switching at full weight (the blade turned 21 deg in one frame at the mount); the first frame starts settled
var clip_dir_blend := 0.4
var _cw := 0.0
var _cw_has := false
var _cd_last := Vector3.ZERO
# optional extra roll of the hand about the blade (manifest grip_fix.clip_roll_deg {clip: deg}) so the EDGE leads a
# strike: the blade keeps its direction (it moves a few cm sideways at most), eased at roll_rate
var clip_roll := {}                  # clip name -> radians
var clip_roll_from := {}             # clip name -> clip seconds from which the roll comes in (before: none)
var roll_rate := deg_to_rad(400.0)
var grip_local := Vector3.ZERO        # the grip (socket origin) in the hand bone frame
var _roll := 0.0
# seeded from another visual of the same rig (the mount rider takes over from the walking hero: copy_state)
var _seed_clip := ""
var _seed_tw := 0.0


## Takes over another GripFix's carry (and its twist, applied on the first frame if this visual then plays the same
## clip), so a second visual that replaces the first (the mount rider) starts with the same sword.
func copy_state(o: Node) -> void:
	if o == null:
		return
	carry_dir = o.carry_dir
	carry_w = o.carry_w
	if bool(o.get("_tw_has")) and o.visual != null:
		_seed_clip = String(o.visual.get("current_clip"))
		_seed_tw = float(o.get("_tw"))


func _process_modification_with_delta(delta: float) -> void:
	var skel := get_skeleton()
	if skel == null or hand < 0:
		return
	var cur := String(visual.get("current_clip")) if visual != null else ""
	if not _tw_has and _seed_clip != "" and cur == _seed_clip:
		_tw = _seed_tw
		_tw_has = true
	_seed_clip = ""
	var cw_to := 1.0 if clip_dirs.has(cur) else 0.0
	if clip_dirs.has(cur):
		_cd_last = clip_dirs[cur]
	if _cw_has:
		_cw = move_toward(_cw, cw_to, maxf(delta, 1.0 / 240.0) / maxf(clip_dir_blend, 0.01))
	else:
		_cw = cw_to
		_cw_has = true
	var hg := skel.get_bone_global_pose(hand)
	var t := (hg.basis * blade_old).normalized()
	if carry_w > 0.0005 and carry_dir.length() > 0.01:
		t = t.slerp(carry_dir.normalized(), clampf(carry_w, 0.0, 1.0)).normalized()
	if _cw > 0.0005 and _cd_last.length() > 0.01:
		t = t.slerp(_cd_last.normalized(), smoothstep(0.0, 1.0, _cw)).normalized()
	var b := (hg.basis * blade_new).normalized()
	var tw := _twist(b, t, hg.basis.y.normalized())
	if _tw_has:
		tw += TAU * roundf((_tw - tw) / TAU)          # unwrap: never flip through +-180 deg in one frame
		tw = clampf(tw, -twist_max, twist_max)
		tw = move_toward(_tw, tw, twist_rate * maxf(delta, 1.0 / 240.0))
	_tw = tw
	_tw_has = true
	var share := forearm_share if forearm >= 0 else 0.0
	if share > 0.0 and absf(tw) > 0.0001:
		var fg := skel.get_bone_global_pose(forearm)
		var af := fg.basis.y.normalized()
		fg.basis = Basis(Quaternion(af, tw * share)) * fg.basis
		skel.set_bone_global_pose(forearm, fg)
		hg = skel.get_bone_global_pose(hand)
		b = (hg.basis * blade_new).normalized()
	var a := hg.basis.y.normalized()
	# the hand's share, re-measured after the forearm turned (a bent wrist moves the hand axis): exact when settled,
	# never more than 30 deg from its planned share while the twist is still rate-limited
	var plan := tw * (1.0 - share)
	var htw := _twist(b, t, a)
	htw += TAU * roundf((plan - htw) / TAU)
	htw = clampf(htw, plan - deg_to_rad(30.0), plan + deg_to_rad(30.0))
	var q := Quaternion(a, htw)
	var b2 := (q * b).normalized()
	var ang := b2.angle_to(t)
	if ang > 0.0001:
		var ax := b2.cross(t)
		if ax.length() > 1e-6:
			q = Quaternion(ax.normalized(), minf(ang, swing_max)) * q
	last_err = rad_to_deg(maxf(ang - swing_max, 0.0))
	hg.basis = Basis(q) * hg.basis
	var roll_to := float(clip_roll.get(cur, 0.0))
	if roll_to != 0.0 and visual != null and float(visual.call("clip_position")) < float(clip_roll_from.get(cur, 0.0)):
		roll_to = 0.0                     # the wind-up keeps the clip's own blade; the roll comes in for the cut
	_roll = move_toward(_roll, roll_to, roll_rate * maxf(delta, 1.0 / 240.0))
	if absf(_roll) > 0.0001:
		# about the blade's own line through the grip: the blade (and the hit volume) stay exactly where they were
		var bd := (hg.basis * blade_new).normalized()
		var gp := hg * grip_local
		var rb := Basis(bd, _roll)
		hg.basis = rb * hg.basis
		hg.origin = gp + rb * (hg.origin - gp)
	skel.set_bone_global_pose(hand, hg)


## Signed angle about `a` that brings b's part across `a` onto t's part across `a`.
static func _twist(b: Vector3, t: Vector3, a: Vector3) -> float:
	var bp := b - a * b.dot(a)
	var tp := t - a * t.dot(a)
	if bp.length() < 0.001 or tp.length() < 0.001:
		return 0.0
	return bp.signed_angle_to(tp, a)
