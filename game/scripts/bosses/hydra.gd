extends BossBase
## The Hydra (SPEC §3.3, §10): a towering nine-headed beast that holds the centre of the volcano shelf.
## guard -> (fire_sweep -> head_down -> head_up -> stomp) | stomp (player at the forefeet) | bite (player at the sides).
## fire_sweep: the centre head inhales (arc decal), then a stream of fire rakes the 140 degree arc. The first pass starts
## at the edge on the side the player stood on when the fire began and travels away from it (escape to that shoulder
## while it inhales, then follow the flame in to the head); enraged, it sweeps there and back.
## head_down: the smoking head lies on the ground, weak point `jaw` open for one hit.
## Loaded by path (no class_name). Numbers: Tuning.HYDRA, then EXTRA below for the ones core has not added yet.

const T := Tuning.HYDRA
## Hydra numbers SPEC does not give (decisions, see docs/notes/hydra.md). Tuning.HYDRA wins when it has the same key.
const EXTRA := {
	"guard_time": 1.4, "guard_time_enraged": 1.0,       # wait in guard before the next attack
	"guard_force_fire": 4.5,                            # in guard this long: breathe fire whatever the angle
	"enraged_windup_scale": 0.8,                        # "below half health they speed up"
	"fire_origin_fwd": 2.5,                             # the arc's apex: the neck base, this far in front of the centre
	"fire_stream_half_deg": 12.0,                       # half width of the raking stream inside the arc
	"fire_knockback": 1.5,
	"fire_front_deg": 50.0,                             # breathe fire when the player is within this angle of the snout
	"head_up_time": 0.8,
	"stomp_trigger_dist": 4.5,                          # player this close to a forefoot (guard) -> stomp
	"stomp_knockback": 5.0, "stomp_recover": 0.7,
	"bite_min_dist": 4.5, "bite_max_dist": 12.0,        # side heads reach (from the body centre)
	"bite_min_deg": 25.0, "bite_max_deg": 180.0,        # bites from the sides AND behind (the necks reach back); the centre head owns the front
	"bite_track_frac": 0.35,                            # the bite circle follows the player for this share of the windup, then locks (flash)
	"bite_knockback": 3.5, "bite_recover": 0.5,
	"bites_before_fire": 2,
	"fire_lead_time": 0.35,                             # the stream enters the arc from just outside the start edge
	"fire_trail_time": 0.3,                             # the ground keeps burning this long behind the stream
	"forced_fire_clamp_deg": 60.0,                      # a forced fire (4.5 s in guard) aims at the hero, clamped to this off the snout
	"jaw_radius": 1.0,                                  # weak point sphere (Tuning.HYDRA wins; integrate2: 1.0 with the strike_point hook)
	"jaw_fwd_guess": 6.8,                               # where the jaw lands in head_down (real rig recipe: 6.8 m ahead, 1.2 m high)
	"jaw_ground_height": 1.2,                           # height of the fallback jaw marker when a clip leaves the jaw too high
	"cam_near_dist": 9.0, "cam_near_height": 4.0,       # lock aim drops toward this height when the hero is this close
	"cam_fire_weight": 0.35,                            # lock aim blends this far toward the stream while it rakes
	# real-model integration (hydra integrator, see docs/notes/hydra.md "Real model")
	"fire_head_gain": 1.65,                             # flame angle = gain x the real mouth's angle seen from the apex (head +-42.5 deg at fire_end -> arc edge 70)
	"bite_spot_reach": 1.5,                             # a bite is chosen when the hero is within bite_radius + this of where that head lands
	"bite_side_max_deg": 120.0,                         # side heads reach this far round (A5: no bite straight behind)
	"walk_turn_start_deg": 6.0, "walk_turn_stop_deg": 2.0,   # guard: play the walk clip while turning more than this
	"walk_turn_speed": 0.9,                             # walk clip rate while turning in place (feet ~1 m/s at x1)
	"fire_fade_near": 3.0, "fire_fade_far": 9.0,        # fire particles fade out closer than this to the camera (hero stays visible)
	"scorch_fade_time": 7.0,                            # the scorched arc fades this long after the fire
	"turn_spring_k": 6.0,                               # (Tuning.HYDRA wins) guard turn spring stiffness, 1/s^2
	"bite_turn_cap_deg": 15.0,                          # (Tuning.HYDRA wins) bite tracking turn cap, deg/s
	"attack_brake_deg": 5.0,                            # guard: an attack starts only once the body turn has slowed below this deg/s
	# integrate2 (2026-11-23, feet in rendered runs; Tuning.HYDRA wins)
	"turn_walk_blend": 0.5,                             # s: idle -> turn walk blend; the body turn cap ramps in over it
	"attack_wind_deg": 16.0,                            # deg/s: a pending attack lets the turn walk step on at this matched rate...
	"attack_wind_max": 1.2,                             # ...for at most this long, until the walk reaches its stop window
	"attack_walk_blend": 0.5,                           # s: blend into an attack clip out of a walk clip (feet off the stance)
}
## Where each bite clip's head lands (boss-local ground point, metres; measured in the real clips at event `impact` 1.5 s:
## bite: head_c (0, 1.29, 5.67); bite_r: head_3 (-5.35, 2.99, 1.43); bite_l: head_6 (5.35, 2.99, 1.43); spots pushed
## ~0.4 m out toward the snout). The warning circle is drawn there, so the strike lands where the head is seen to land.
const BITES := [
	{"clip": &"bite_r", "head": &"head_3", "spot": Vector3(-5.7, 0.0, 1.6), "side": true},
	{"clip": &"bite_l", "head": &"head_6", "spot": Vector3(5.7, 0.0, 1.6), "side": true},
	{"clip": &"bite", "head": &"head_c", "spot": Vector3(0.0, 0.0, 6.0), "side": false},
]
const FIRE_CLIPS := {1: &"fire_sweep_l", -1: &"fire_sweep"}            # A1: +1 = the head starts on +X (boss's left)
const FIRE_RETURN := {&"fire_sweep": &"fire_sweep_return", &"fire_sweep_l": &"fire_sweep_return_l"}   # A3
const SCORCH_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform float reach = 30.0;
uniform float a_lo = 0.0;
uniform float a_hi = 0.0;
uniform float alpha = 0.0;
uniform float heat = 0.0;
varying vec2 lp;
float h1(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 15731.743); }
float vn(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h1(i), h1(i + vec2(1, 0)), f.x), mix(h1(i + vec2(0, 1)), h1(i + vec2(1, 1)), f.x), f.y);
}
void vertex() { lp = VERTEX.xz; }
void fragment() {
	float r = length(lp);
	float a = atan(lp.x, lp.y);
	float soft = 0.9 / max(r, 1.0);
	float ins = smoothstep(a_lo - soft, a_lo + soft, a) * (1.0 - smoothstep(a_hi - soft, a_hi + soft, a));
	ins *= smoothstep(0.6, 2.5, r) * (1.0 - smoothstep(reach - 2.5, reach + 0.5, r));
	vec2 wp = lp;
	float n = vn(wp * 0.45) * 0.6 + vn(wp * 1.7) * 0.4;
	// sparse glowing specks that cool down (heat 1 -> 0 after the fire)
	float speck = step(0.965, h1(floor(wp * 3.0))) * smoothstep(0.3, 0.7, vn(wp * 0.6 + 3.0));
	float ember = speck * heat;
	ALBEDO = mix(vec3(0.025, 0.02, 0.018), vec3(1.5, 0.42, 0.06), ember);
	ALPHA = clamp(alpha * ins * (0.35 + 0.4 * n) + ember * ins * alpha, 0.0, 1.0);
}
"""

## Test bot at the lying jaw (real model; final check, docs/notes/hydra.md). The bot's stick stops 0.6 m short of a
## target, so both stand points lie INSIDE the resting-head collider (capsule r 0.7 ending ~0.65 m past the jaw): the
## hero walks until the collider stops him, ~1.0 m from the jaw centre.
const BOT_JAW_STAND := 0.2          ## front: this far past the jaw centre, radially (was 0.7: stopped ~1.3 m out)
## From the flank (hero not yet BOT_JAW_ROUND_REL past the jaw): first a waypoint clear of the head's rounded end, this
## far to his side of the jaw line and this far past the jaw; then the front stand. (Aiming inside the head's side made
## him slide along it: slow, and with --keys 2.4 s of the enraged 2.5 s opening; at 0.15 / 0.1 he stuck there.)
const BOT_JAW_SIDE := 0.8
const BOT_JAW_SIDE_OUT := 1.3
const BOT_JAW_ROUND_REL := 0.5
## Swing at the LYING jaw (y < 1 m) only from within this flat distance of its centre (probe: the slash's gap is about
## distance - 1.33 m; a slash from 1.6 m beside it glanced at +0.05 m and the combo ate the opening)
const BOT_JAW_REACH := 1.15
const BOT_JAW_LATERAL := 1.2        ## and only with the jaw within this of the hero -> boss line (any jaw height)

const COL_FIRE := Color(1.0, 0.30, 0.05)
const COL_STOMP := Color(0.95, 0.12, 0.10)
## qa fix: the bite warning was the only pink in the game; it now uses the flat ground circle of the other attacks in
## crimson / ember (no tall pillar, only a 0.3 m rim) and the biting head glows ember orange
const COL_BITE := Color(0.92, 0.18, 0.08)
const COL_BITE_LOCK := Color(1.0, 0.55, 0.15)      # the bite circle at the lock moment: hotter, brighter
const COL_BITE_GLOW := Color(1.0, 0.45, 0.10)      # glow on the biting head + its light
const BITE_RIM_H := 0.3                            # height of the rim on the locked bite circle (was a 3.2 m pillar)
## qa fix: the inhale cone painted the floor a flat opaque orange: Telegraph's fill (0.6 at full) x this alpha 0.38 =
## 0.23 (0.33 still read as paint in the windowed shots, glow + tonemap brighten it), the bright animated edge and hatch come from the module's own overlay (INHALE_SHADER)
## hydra polish 2: 0.38 -> 0.10. The flat fill was what read as paint; the heat now comes from INHALE_SHADER's glowing
## cracks, embers and inward heat fronts, so the fill only tints the zone a little
const COL_FIRE_WARN := Color(1.0, 0.30, 0.05, 0.10)
const COL_ARC_HOLD := Color(1.0, 0.32, 0.06, 0.32) # faint arc outline while the stream rakes
const STREAM_SPEED := 27.0
## The generated albedo is a bright magenta-violet (mean sRGB 123/24/88); under the volcano's orange light it read pink.
## A multiply tint brings it back to the sheet's black-violet + crimson (real models only; stand-ins keep their colours).
## qa fix: (0.52, 0.40, 0.62) left the necks raspberry and the plates maroon under the orange sun. Now a per-texel
## recolour (RECOLOUR_FN: dark purple -> violet, raspberry -> crimson), this mild tint, and a cool violet fill + rim on
## the boss only (VIOLET_FILL / RIM_COLOR). A tint alone ((0.44, 0.36, 0.74) tried) made the legs violet but the belly pink.
const MODEL_TINT := Color(0.78, 0.72, 0.84)       # after hydra_recolour (below): a mild darkening only
const RIM_COLOR := Color(0.70, 0.55, 1.0)          # toon rim on the boss's materials (was the warm cream default)
const RIM_STRENGTH := 0.30
const VIOLET_FILL := Color(0.55, 0.42, 1.0)        # boss-only directional fill (light cull mask = BOSS_LIGHT_LAYER)
const VIOLET_FILL_ENERGY := 0.35
const BOSS_LIGHT_LAYER := 1 << 10                  # render layer 11: only the hydra's meshes carry it
const DEATH_CLEAR_DIST := 14.5                     # at death the hero is pushed back to this far from the centre
## Inhale warning overlay (hydra polish 2: was hatch stripes): heat rising from the rock. Glowing cracks and embers that
## brighten toward the head and through the inhale, heat fronts running in toward the head, a bright steady edge, and
## only a faint fill (the cone telegraph under it is nearly clear).
const INHALE_SHADER := """
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform float reach = 30.0;
uniform float half_angle = 1.22;
uniform float progress = 0.0;
uniform vec4 col : source_color = vec4(1.0, 0.55, 0.15, 1.0);
uniform vec4 hot : source_color = vec4(1.0, 0.82, 0.42, 1.0);
varying vec2 lp;
vec2 h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float h1(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 15731.743); }
// distance-like value to the nearest cell border of a jittered grid (F2 - F1): small on the cracks
float crack(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = g + h2(i + g) - f;
			float d = dot(o, o);
			if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
		}
	}
	return sqrt(d2) - sqrt(d1);
}
void vertex() { lp = VERTEX.xz; }
void fragment() {
	float r = length(lp);
	float a = abs(atan(lp.x, lp.y));
	float ins = step(a, half_angle) * step(r, reach) * smoothstep(0.5, 2.0, r);
	float u = clamp(r / reach, 0.0, 1.0);                 // 0 at the head, 1 at the far rim
	// the danger zone's own bright edge (sides + rim), steady with a slight flicker
	float ew = 0.35 / max(r, 1.0);
	float side = smoothstep(half_angle - ew * 2.5, half_angle - ew * 0.3, a);
	float rim = smoothstep(reach - 0.9, reach - 0.25, r);
	float edge = max(side, rim) * ins;
	// glowing cracks in the rock: big plates + fine cracks, anti-aliased (fwidth) so they do not shimmer far away
	float c1 = crack(lp * 0.42);
	float c2 = crack(lp * 1.15 + 7.3);
	float w1 = 0.045 + 0.05 * (1.0 - u);
	float l1 = 1.0 - smoothstep(w1, w1 + fwidth(c1) * 1.5, c1);
	float l2 = (1.0 - smoothstep(0.035, 0.035 + fwidth(c2) * 1.5, c2)) * 0.25;   // re-fix: fine net 0.5 -> 0.25
	// re-fix: the cracks die out toward the far rim (the rim line stays), so the far floor is not an even grid
	float cracks = max(l1, l2) * (1.0 - smoothstep(0.62, 0.9, u));
	// heat: brighter toward the head, rising through the inhale; fronts of heat run along the cracks toward the head
	float heat = mix(0.3, 1.0, pow(1.0 - u, 1.4)) * (0.45 + 0.75 * progress);
	float front = fract(u * 1.6 + TIME * 0.85);          // re-fix: 2-3 wider pulses (was u * 2.4)
	float band = 1.0 - smoothstep(0.0, 0.3, front);       // sharp leading edge on the head side, tail outward
	// embers: sparse cells that flicker, lifted by the passing front (heat rising)
	vec2 ec = floor(lp * 2.2);
	float emb = step(0.982, h1(ec)) * (0.55 + 0.45 * sin(TIME * 6.0 + h1(ec + 1.7) * 40.0)) * (0.6 + 0.8 * band);
	// re-fix: the moving fronts carry most of the light (cracks between pulses stay dim)
	float glow = cracks * heat * (0.25 + 1.4 * band) + emb * heat * 0.9 + (0.02 + 0.06 * progress) * (1.0 - u);
	float k_edge = edge * (0.75 + 0.35 * progress) * (0.88 + 0.12 * sin(TIME * 9.0));
	float k = k_edge + glow * ins * (1.0 - edge);
	// re-fix: the fronts burn whiter than the arena's own orange lava veins, so they read as moving heat in a still
	vec3 c = mix(col.rgb, hot.rgb, clamp((1.0 - u) * 0.75 * progress + band * cracks * 0.7 + edge * 0.5, 0.0, 1.0));
	c = mix(c, vec3(1.0, 0.95, 0.8), band * cracks * 0.35 * (0.5 + 0.5 * progress));
	ALBEDO = c * k;
	ALPHA = 1.0;
}
"""
const ENRAGED_TINT := Color(1.0, 0.8, 0.8)

var _decal: Telegraph = null
var _impact_at := 0.0
var _impact_done := false
var _bites := 0
var _was_enraged := false
var _roared := false
# fire
var _fire_dir := Vector3.BACK
var _fire_origin := Vector3.ZERO
var _fire_windup := 1.5
var _fire_on := false
var _fire_side := 1.0             # +1: the first pass starts on the boss's left (+X local), -1 right
var _fire_legs := 1
var _fire_tick_t := 0.0
var _fire_fx: Node3D = null
var _stream: CPUParticles3D = null
var _core: CPUParticles3D = null
var _ground_fire: CPUParticles3D = null
var _fire_light: OmniLight3D = null
var _throat: MeshInstance3D = null
var _throat_light: OmniLight3D = null
var _fire_audio := 0                     # Sfx loop id of the fire stream (0 = none)
var _smoke: CPUParticles3D = null
var _arc_hold: Telegraph = null    # faint arc outline during the sweep
var _start_edge: MeshInstance3D = null
var _forced_fire := false
var _cam_fire_w := 0.0
var _cam_fire_target := Vector3.ZERO
# head_down / stomp / bite
var _head_down_end := 0.0
var _jaw_checked := false
var _jaw_moved := false
var _jaw_prev_y := 0.0
var _jaw_drop_t := 0.0
var _stomp_foot: StringName = &"foot_fl"
var _stomp_center := Vector3.ZERO
var _bite_center := Vector3.ZERO
var _bite_head: StringName = &"head_1"
var _bite_locked := false
var _bite_glow: MeshInstance3D = null
var _bite_glow_light: OmniLight3D = null
var _bite_pillar: MeshInstance3D = null
# real-model integration
var _fire_clip: StringName = &"fire_sweep"
var _fire_turn_rate := 0.0         # forced fire: deg/s the body turns to the aimed arc during the inhale
var _fire_return_on := false
var _flame_hist: Array = []        # [t, phi] of the flame actually shown (damage reads the same angles)
var _phi_now := 0.0
var _scorch: MeshInstance3D = null
var _scorch_mat: ShaderMaterial = null
var _scorch_lo := 0.0
var _scorch_hi := 0.0
var _scorch_tw: Tween = null
var _turn_walk := false
var _yaw_vel := 0.0                # guard: eased body turn rate, deg/s (+ = to the left)
var _foot_r := 0.0                 # forefeet distance from the pivot (m), measured once for the walk rate
var _walk_stop_wait := -1.0        # animfix3: >= 0 while a turn walk waits (s) for its stop window before the idle blend
var _pending_attack: StringName = &""   # guard: chosen attack waiting for the body turn to brake (no dead stop)
var _tw_age := 99.0                 # integrate2: s since the turn walk started (the body turn waits for the clip's blend-in)
var _wind_t := 0.0                  # integrate2: s a pending attack has let the turn walk step on toward its stop window
var _fire_stepping := false        # forced fire: the beast still steps round to the aimed arc (walk clip) before it inhales
var _bite_follow := true          # stand-in: the circle follows the hero (no per-side clips)
var _bite_clip: StringName = &"bite"
var _bite_spot := Vector3.ZERO     # boss-local landing point of the biting head
# qa fixes
var _inhale_fx: MeshInstance3D = null      # hatch + edge overlay on the inhale cone
var _inhale_mat: ShaderMaterial = null
const HEAD_COL_R := 0.85
var _head_col: CollisionShape3D = null     # the resting head blocks the hero during head_down
## Feedback 2 re-fix (clipping 15:00, sword arm / body inside the lowered snout): the head capsule ends 0.91 m past
## head_c but the snout reaches 1.36 m (skinned head_down mesh, work/vfx3/probes/hydra_snout.gd; half-width 0.50 at
## 0.8-1.0 m, 0.31 at 1.0-1.2, 0.23 at 1.2-1.36). A thin upright capsule fills the snout: front surface at 1.37 m.
const SNOUT_FWD := 0.95
const SNOUT_R := 0.42
const SNOUT_H := 1.5
var _snout_col: CollisionShape3D = null
var _smoke_mat: StandardMaterial3D = null
var _smoke_tw: Tween = null


func _init() -> void:
	boss_id = &"hydra"
	display_name = "The Hydra of the Burning Isle"
	max_hp = T["hp"]
	body_radius = 2.6
	body_height = 6.5
	# harness-only probe: `--hydra-glb=<abs path to a GLB>` (+ `--hydra-manifest=<clips json>`) shows a model that is
	# not in res://assets yet (framing checks with the real 14 m mesh). BossBase._ready keeps a visual set here.
	if Game.harness and Game.args.has("hydra-glb"):
		visual = CharacterVisual.create_from_file(boss_id, String(Game.args["hydra-glb"]), String(Game.args.get("hydra-manifest", "")))
		add_child(visual)


func _n(key: String) -> float:
	return float(T[key]) if T.has(key) else float(EXTRA[key])


func _ws() -> float:
	return _n("enraged_windup_scale") if enraged() else 1.0


# ------------------------------------------------------------------ build
func _build() -> void:
	# the torso and haunches (16 m long beast): a horizontal capsule from the chest back to the hips; the tail and the
	# necks stay passable so the hero can reach the head when it lies on the ground
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 2.4
	cap.height = 9.0
	cs.shape = cap
	cs.rotation_degrees = Vector3(90, 0, 0)
	cs.position = Vector3(0, 3.6, -1.0)
	cs.name = "Torso"
	add_child(cs)
	# qa fix: the head resting on the ground in head_down is solid (the hero ran through it and struck the jaw from on
	# top of / inside the head); enabled and moved onto the head_c socket only during head_down
	_head_col = CollisionShape3D.new()
	_head_col.name = "RestingHead"
	var hc := CapsuleShape3D.new()
	# feedback 2 (clipping 13:30 / 15:00): 0.7 -> HEAD_COL_R; the head is ~1.7 m wide, the hero stood half inside it.
	# The capsule's front end stays where it was (centre moved back by the same amount): the jaw keeps its reach.
	hc.radius = HEAD_COL_R
	hc.height = 2.0 + 2.0 * HEAD_COL_R
	_head_col.shape = hc
	_head_col.disabled = true
	add_child(_head_col)
	_snout_col = CollisionShape3D.new()
	_snout_col.name = "RestingSnout"
	var sc := CapsuleShape3D.new()
	sc.radius = SNOUT_R
	sc.height = SNOUT_H
	_snout_col.shape = sc
	_snout_col.disabled = true
	add_child(_snout_col)
	add_weak_point(&"jaw", &"jaw_c", _n("jaw_radius"))
	_build_fire_fx()
	for n in [_stream, _core, _ground_fire]:
		(n as Node3D).visible = false
	if not visual.is_standin:
		visual.set_tint(MODEL_TINT)
		_violet_look()


## qa fix (colours off the sheet): the generated albedo has two families, dark purple-violet (hue 260-320, ~63% of
## the texels: legs, plates, neck backs) and bright raspberry (hue 320-360, ~37%: neck undersides, belly). One multiply
## tint cannot push the first to violet and the second to crimson, so the hydra's own copy of core's toon shader
## remaps the texel by its redness first (RECOLOUR_FN, injected before the tint line; core's shader file is untouched and
## is re-read, so later core changes carry over). Plus a cool violet rim on the boss's materials and a violet directional
## fill that lights only the boss (BOSS_LIGHT_LAYER). Real model only.
const RECOLOUR_FN := """
vec3 hydra_recolour(vec3 t) {
	float red = (t.r - t.b) / max(t.r + t.b, 0.001);
	float w = smoothstep(0.12, 0.30, red);
	return mix(t * vec3(0.66, 1.0, 1.18), t * vec3(0.86, 0.78, 0.38), w);
}
"""
const RECOLOUR_ANCHOR := "c.rgb *= tint.rgb;"
static var _recolour_cache := {}      # original Shader instance id -> recoloured Shader


func _violet_look() -> void:
	for mi in visual.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.layers |= BOSS_LIGHT_LAYER
		var mats: Array = [m.material_override]
		if m.mesh != null:
			for i in m.mesh.get_surface_count():
				mats.append(m.get_surface_override_material(i))
		for mat in mats:
			if mat is ShaderMaterial and (mat as ShaderMaterial).shader != null \
					and (mat as ShaderMaterial).shader.get_shader_uniform_list().any(func(u: Dictionary) -> bool: return u["name"] == "rim_color"):
				var sm := mat as ShaderMaterial
				var rs := _recoloured(sm.shader)
				if rs != sm.shader:
					var keep := {}
					for u in sm.shader.get_shader_uniform_list():
						keep[u["name"]] = sm.get_shader_parameter(u["name"])
					sm.shader = rs
					for k in keep:
						if keep[k] != null:
							sm.set_shader_parameter(k, keep[k])
				sm.set_shader_parameter("rim_color", RIM_COLOR)
				sm.set_shader_parameter("rim_strength", RIM_STRENGTH)
	_add_violet_fill()


## The core toon shader with hydra_recolour() applied to the texel before the tint (cached); the original shader when
## the anchor line is not found (then only the tint applies).
func _recoloured(src: Shader) -> Shader:
	var key := src.get_instance_id()
	if _recolour_cache.has(key):
		return _recolour_cache[key]
	var code := src.code
	var out := src
	if code.contains(RECOLOUR_ANCHOR) and code.contains("void fragment()"):
		code = code.replace("void fragment()", RECOLOUR_FN + "\nvoid fragment()")
		code = code.replace(RECOLOUR_ANCHOR, "c.rgb = hydra_recolour(c.rgb);\n\t" + RECOLOUR_ANCHOR)
		out = Shader.new()
		out.code = code
	else:
		push_warning("Hydra: toon shader anchor '%s' not found; recolour skipped (tint only)" % RECOLOUR_ANCHOR)
	_recolour_cache[key] = out
	return out


func _add_violet_fill() -> void:
	var fill := DirectionalLight3D.new()
	fill.name = "HydraVioletFill"
	fill.light_color = VIOLET_FILL
	fill.light_energy = VIOLET_FILL_ENERGY
	fill.light_cull_mask = BOSS_LIGHT_LAYER
	fill.shadow_enabled = false
	fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	# boss-local (turns with the beast): from above and in front, where the chase camera looks from
	fill.rotation = Vector3(deg_to_rad(-40.0), deg_to_rad(20.0), 0.0)
	add_child(fill)


func _first_state() -> StringName:
	return &"guard"



# ------------------------------------------------------------------ states
func _enter_state(s: StringName) -> void:
	_impact_done = false
	match s:
		&"guard":
			halt()
			# 0.4 s: a bite / stomp ends mid-recovery (the state is shorter than the clip), so ease the rest of it out
			visual.play(&"idle", 0.4)
			_turn_walk = false
			_yaw_vel = 0.0
			_pending_attack = &""
			_wind_t = 0.0
			if not _roared:
				_roared = true
				Sfx.play("hydra_roar", global_position)
		&"fire_sweep":
			halt()
			_bites = 0
			_fire_windup = _n("fire_inhale") * _ws()
			_fire_dir = forward()
			_fire_turn_rate = 0.0
			_fire_stepping = false
			if _forced_fire:
				# forced fire (the hero kept out of the front): aim at the hero, clamped to +-60 deg off the snout
				var to_p := player.global_position - global_position
				to_p.y = 0.0
				if to_p.length() > 0.1:
					var a := forward().signed_angle_to(to_p.normalized(), Vector3.UP)
					var lim := deg_to_rad(_n("forced_fire_clamp_deg"))
					var turn := clampf(a, -lim, lim)
					_fire_dir = forward().rotated(Vector3.UP, turn).normalized()
					# the head clip sweeps around the body's forward, so the beast must face the arc it burns
					if not visual.is_standin and visual.has_clip(&"walk") and absf(rad_to_deg(turn)) > 3.0:
						# polish 2 re-fix (no pivot on the fire clip's still legs): it keeps stepping round on the walk
						# clip (eased, carrying the guard turn rate) and blends into the fire clip once it faces the arc;
						# the inhale is lengthened by the estimated turn time so the warning stays as long as the turn
						_fire_stepping = true
						_fire_windup = maxf(_fire_windup, _turn_time_est(rad_to_deg(turn), _urgent_turn_deg()) + 0.45)
					else:
						# stand-in: the body swings round during the first 60% of the inhale
						_fire_turn_rate = maxf(float(T["turn_deg"]), rad_to_deg(absf(turn)) / maxf(_fire_windup * 0.6, 0.1))
			_forced_fire = false
			_fire_origin = global_position + _fire_dir * _n("fire_origin_fwd")
			_fire_origin.y = 0.0
			_fire_legs = 2 if enraged() else 1
			# the first pass starts on the side the hero stands on NOW (shown by the bright start edge while it inhales)
			_fire_side = 1.0 if _signed_angle(player.global_position) >= 0.0 else -1.0
			Game.event("inhale", {"player_deg": snappedf(_signed_angle(player.global_position), 0.1), "side": _fire_side,
				"player_rho": snappedf(Vector2(player.global_position.x - _fire_origin.x, player.global_position.z - _fire_origin.z).length(), 0.01)})
			_fire_on = false
			_fire_return_on = false
			_flame_hist.clear()
			# A1: the clip whose head starts on the hero's side (fire_sweep_l: +X -> -X; fire_sweep: -X -> +X)
			_fire_clip = FIRE_CLIPS[int(_fire_side)] if visual.has_clip(FIRE_CLIPS[int(_fire_side)]) else &"fire_sweep"
			var ln := visual.clip_length(_fire_clip, 3.9)
			if _fire_stepping:
				_turn_walk = true
				if not _is_walk_clip(visual.current_clip):
					_start_turn_walk(_yaw_err_to(global_position + _fire_dir * 10.0))
			else:
				visual.play(_fire_clip, _attack_blend(0.3), visual.event_time(_fire_clip, &"fire_start", ln * 0.38) / _fire_windup)
			_decal = arena.telegraph_cone(_fire_origin, _fire_dir, T["fire_arc_deg"] * 0.5, T["fire_reach"], _fire_windup, COL_FIRE)
			_decal.set_colors(COL_FIRE_WARN, Color(1.0, 0.8, 0.4))
			_show_inhale_fx()
			_show_start_edge()
			Sfx.play("hydra_fire_sweep_warn", _head_pos())
			_throat.visible = true
			_throat_light.visible = true
		&"head_down":
			halt()
			# the fire clips end on head_down's chin rest: blend over what is left of them so the head lands, not snaps
			var fc := _fire_return_clip() if _fire_return_on else _fire_clip
			var left := visual.clip_length(fc, 0.5) - visual.event_time(fc, &"fire_end", visual.clip_length(fc, 0.5) - 0.5)
			visual.play(&"head_down", clampf(left / maxf(visual.get_speed(), 0.1), 0.2, 0.6))
			Sfx.play("hydra_head_down", _head_pos())
			expose(&"jaw", int(T["head_down_hits"]))
			_head_down_end = T["head_down_time"]
			_jaw_checked = false
			_jaw_prev_y = (weak_points[&"jaw"] as WeakPoint).global_position.y
			_jaw_drop_t = 0.0
			_smoke.global_position = _mouth_pos()
			if _smoke_tw != null and _smoke_tw.is_valid():
				_smoke_tw.kill()
			_smoke_mat.albedo_color.a = 0.3
			_smoke.visible = true
			_smoke.emitting = true
			_head_col.disabled = visual.is_standin
			_snout_col.disabled = _head_col.disabled
			_place_head_col()
		&"head_up":
			close_weak(&"jaw")
			visual.play(&"head_up", 0.2, visual.clip_length(&"head_up", 0.8) / _n("head_up_time"))
		&"stomp":
			halt()
			_impact_at = T["stomp_windup"] * _ws()
			_stomp_foot = _near_forefoot()
			_stomp_center = visual.socket(_stomp_foot).global_position
			_stomp_center.y = 0.0
			# A4: stomp lifts foot_fl (+X), stomp_r lifts foot_fr (-X)
			var sc := &"stomp_r" if _stomp_foot == &"foot_fr" and visual.has_clip(&"stomp_r") else &"stomp"
			var ls := visual.clip_length(sc, 1.5)
			visual.play(sc, _attack_blend(0.25), visual.event_time(sc, &"impact", ls * 0.6) / _impact_at)
			_decal = arena.telegraph_ring(_stomp_center, 0.8, T["stomp_radius"], _impact_at, COL_STOMP)
			Sfx.play("hydra_stomp_warn", _stomp_center)
		&"bite":
			halt()
			var opt := _pick_bite(player.global_position)     # before counting this bite (the centre head bites first only)
			_bites += 1
			# qa fix: the enraged bite (0.8 x 0.8 = 0.64 s) left no time to roll after the lock cue; floor 0.75 s
			_impact_at = maxf(float(T["bite_windup"]) * _ws(), minf(float(T["bite_windup"]), 0.75))
			_bite_locked = false
			_bite_follow = opt.is_empty()
			if _bite_follow:
				# stand-in (one bite clip for all heads): the circle follows the hero, the nearest side head glows
				_bite_clip = &"bite"
				_bite_head = _bite_head_for(player.global_position)
				_bite_center = player.global_position
			else:
				# A5: the real head lunge; the circle lies where that head lands and turns with the body
				_bite_clip = opt["clip"]
				_bite_head = opt["head"]
				_bite_spot = opt["spot"]
				_bite_center = to_global(_bite_spot)
			_bite_center.y = 0.0
			var lb := visual.clip_length(_bite_clip, 1.2)
			visual.play(_bite_clip, _attack_blend(0.2), visual.event_time(_bite_clip, &"impact", lb * 0.66) / _impact_at)
			Game.event("bite_start", {"clip": _bite_clip, "head": _bite_head})
			_decal = arena.telegraph_circle(_bite_center, T["bite_radius"], _impact_at, COL_BITE)
			Sfx.play("hydra_bite_warn", visual.socket(_bite_head).global_position)
			# the biting head glows (the stand-in shares one clip, so the glow says WHICH head comes)
			_bite_glow.visible = true
			_bite_glow_light.visible = true
			_bite_glow.scale = Vector3.ONE * 0.7
			_bite_glow_light.light_energy = 1.5
		&"idle":
			halt()
			visual.play(&"idle", 0.3)
		&"dead":
			_on_death_clear()


## qa fix (the corpse covered the hero and the camera): the death clip collapses in place from head_down, the necks
## splaying out to +-6 m and 7.7 m ahead, around a hero who struck the jaw from ~7.6 m. The collapse pushes him back
## to DEATH_CLEAR_DIST from the centre over 1.1 s (a slide, collision kept) and the camera snaps behind him, so the
## whole fallen beast lies in front of him during LABOR COMPLETE.
func _on_death_clear() -> void:
	if player == null or not is_instance_valid(player):
		return
	var c := global_position
	c.y = player.global_position.y
	var d := player.global_position.distance_to(c)
	if d < DEATH_CLEAR_DIST:
		# Player.push_back(from, dist, secs): the knockback slide try_hit uses (no damage, collision kept)
		player.push_back(c, DEATH_CLEAR_DIST - d, 1.1)
	if player.get("camera") != null and player.camera.has_method("snap_behind"):
		player.camera.snap_behind()
	Game.event("death_clear", {"from": snappedf(d, 0.01), "to": DEATH_CLEAR_DIST})


## Moves the resting-head collider onto the head_c socket: a horizontal capsule from 1.7 m behind the socket to 0.1 m
## in front of it along the head's ground direction (the jaw stays outside it, on the snout side).
func _place_head_col() -> void:
	if _head_col == null or _head_col.disabled:
		return
	var h := visual.socket(&"head_c").global_position
	var fwd := h - global_position
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.1 else forward()
	var mid := h - fwd * (0.8 + (HEAD_COL_R - 0.7))
	mid.y = maxf(h.y, 0.75)
	# capsule axis = local Y: lay it along fwd
	var basis := Basis.looking_at(fwd, Vector3.UP) * Basis(Vector3.RIGHT, PI * 0.5)
	_head_col.global_transform = Transform3D(basis, mid)
	if _snout_col != null and not _snout_col.disabled:
		var sp := h + fwd * SNOUT_FWD
		sp.y = maxf(h.y - 1.0, 0.0) + SNOUT_H * 0.5
		_snout_col.global_transform = Transform3D(Basis.looking_at(fwd, Vector3.UP), sp)


## True when the hero is on the jaw side of the head (in front of the snout or beside it), not behind it (between the
## head and the body) or on top of it: dot(hero - jaw, head direction) > -0.45 (horizontal, normalised; the finding's
## -0.3 glanced a hero standing right beside the jaw, 110 deg round; behind the head is 150-180 deg). Real model only.
func _jaw_side_ok() -> bool:
	if visual.is_standin or not weak_points.has(&"jaw"):
		return true
	var j := (weak_points[&"jaw"] as WeakPoint).global_position
	var fwd := j - global_position
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.1 else forward()
	var to_h := player.global_position - j
	to_h.y = 0.0
	return to_h.length() < 0.05 or to_h.normalized().dot(fwd) > -0.45


## qa fix: a jaw strike from the wrong side of the head (behind it / through it) glances: spark + clang, the weak
## point stays open, no damage. Everything else goes to BossBase.
func take_weak_hit(point: WeakPoint) -> void:
	if point.id == &"jaw" and hp > 0 and not _jaw_side_ok():
		point.open(1)
		Fx.spark(arena, point.global_position, Color(1.0, 0.85, 0.5), 14, 0.1)
		Sfx.play("glance", point.global_position)
		Game.event("jaw_glance", {"player": player.global_position})
		return
	super(point)


func _exit_state(s: StringName) -> void:
	match s:
		&"fire_sweep":
			var was_on := _fire_on
			_stop_fire()
			if is_instance_valid(_decal) and not was_on:
				_decal.cancel()
			_start_edge.visible = false
			_inhale_fx.visible = false
		&"head_down":
			close_weak(&"jaw")
			_restore_jaw()
			_head_col.disabled = true
			_snout_col.disabled = true
			# qa fix: the smoke hung in front of the chase camera after head_up and through the stomp warning: stop it
			# and fade what is left out in 0.5 s
			_smoke.emitting = false
			if _smoke_tw != null and _smoke_tw.is_valid():
				_smoke_tw.kill()
			if is_inside_tree():
				_smoke_tw = create_tween()
				_smoke_tw.tween_property(_smoke_mat, "albedo_color:a", 0.0, 0.5)
				_smoke_tw.tween_callback(func() -> void: _smoke.visible = false)
		&"stomp":
			if is_instance_valid(_decal) and not _impact_done:
				_decal.cancel()
		&"bite":
			if is_instance_valid(_decal) and not _impact_done:
				_decal.cancel()
			_bite_fx_off()


func _tick_state(delta: float) -> void:
	match state:
		&"guard":
			# (`--hydra-side` harness test: the beast holds still so the bot can stand by a side head's landing spot)
			if not (Game.harness and Game.args.has("hydra-side") and _has_side_bites()):
				# after guard_force_fire s without a shot the beast steps round faster to bring its snout to the hero
				var urgent := state_time >= _n("guard_force_fire")
				_guard_turn(player.global_position, float(T["turn_deg"]) * (_n("guard_urgent_turn_mult") if urgent else 1.0), delta,
					_pending_attack != &"")
			_tick_turn_walk()
			var wait :=_n("guard_time_enraged") if enraged() else _n("guard_time")
			if state_time >= wait:
				# polish 2 re-fix: an attack never starts while the body still swings round (it stopped dead in one tick):
				# the chosen attack waits while the turn brakes at turn_accel_deg (35 deg/s -> 0 in 0.39 s, ~7 deg)
				if _pending_attack != &"":
					if absf(_yaw_vel) < _n("attack_brake_deg"):
						var go := _pending_attack
						_pending_attack = &""
						# the fire still fits while the hero is well inside its arc; anything else is chosen again
						if go != &"fire_sweep" or angle_to_pos(player.global_position) >= float(T["fire_arc_deg"]) * 0.5 - 10.0:
							go = _choose_attack()
						if go != &"":
							set_state(go)
				else:
					var next := _choose_attack()
					if next != &"":
						# a forced fire carries the turn on into its own stepping turn (see _enter_state)
						if _forced_fire or absf(_yaw_vel) < _n("attack_brake_deg"):
							set_state(next)
						else:
							_pending_attack = next
							_wind_t = 0.0
		&"fire_sweep":
			_tick_fire(delta)
		&"head_down":
			if Game.harness and Game.args.has("hydra-debug") and fmod(state_time, 0.5) < delta:
				var wpd: WeakPoint = weak_points[&"jaw"]
				Game.event("dbg_jaw", {"jaw": wpd.global_position, "player": player.global_position, "exp": wpd.exposed,
					"mouth": _mouth_pos(), "head": _head_pos(), "throat": _throat.visible, "glow": _bite_glow.visible})
			_smoke.global_position = _mouth_pos()     # the smoke rises from the head lying on the ground
			if not _jaw_checked:
				_check_jaw_reachable()
			_place_head_col()
			if state_time >= _head_down_end:
				set_state(&"head_up")
		&"head_up":
			if state_time >= _n("head_up_time"):
				set_state(&"stomp")
		&"stomp":
			if absf(_yaw_vel) > 0.01 and not visual.is_standin:
				# the last few deg/s of the guard turn brake out (an attack starts below attack_brake_deg, never mid-swing)
				_ease_turn(0.0, float(T["turn_deg"]), _n("turn_accel_deg"), delta, false)
			if not _impact_done and state_time >= _impact_at:
				_impact_done = true
				var r := hit_circle(_stomp_center, T["stomp_radius"], T["stomp_dmg"], {"blockable": false, "knockback": _n("stomp_knockback")})
				_stomp_fx(_stomp_center)
				Game.event("attack_resolved", {"attack": "stomp", "result": r})
			if state_time >= _impact_at + _n("stomp_recover"):
				set_state(&"guard")
		&"bite":
			var track_end := _impact_at * _n("bite_track_frac")
			var head := visual.socket(_bite_head).global_position
			_bite_glow.global_position = head
			_bite_glow_light.global_position = head
			if state_time < track_end:
				var p := player.global_position
				p.y = 0.0
				if _bite_follow:
					_bite_center = _bite_center.lerp(p, 1.0 - exp(-8.0 * delta))
					face_towards(_bite_center, T["turn_deg"], delta)
				else:
					# turn so the head's landing spot swings toward the hero; the circle rides on the spot
					var c := global_position
					c.y = 0.0
					var yaw := atan2(_bite_spot.x, _bite_spot.z)
					# polish 2 re-fix: an eased weight shift, not a flat 35 deg/s spin on the bite clip's still legs:
					# at most bite_turn_cap_deg, and slow enough to be stopped (at 2 x turn_accel_deg) when the bite locks
					var acc2 := 2.0 * _n("turn_accel_deg")
					var cap := minf(_n("bite_turn_cap_deg"), acc2 * maxf(track_end - state_time - delta, 0.0))
					var err := _yaw_err_to(c + (p - c).rotated(Vector3.UP, -yaw))
					var want := signf(err) * minf(cap, sqrt(2.0 * acc2 * absf(err)))
					_yaw_vel = move_toward(_yaw_vel, want, acc2 * delta)
					if absf(_yaw_vel) > cap:
						_yaw_vel = signf(_yaw_vel) * cap
					rotation.y += deg_to_rad(_yaw_vel) * delta
					_bite_center = to_global(_bite_spot)
					_bite_center.y = 0.0
				if is_instance_valid(_decal):
					_decal.global_position = _bite_center
				var kg := clampf(state_time / maxf(track_end, 0.01), 0.0, 1.0)
				_bite_glow.scale = Vector3.ONE * (0.7 + 0.3 * kg)
			elif not _bite_locked:
				_yaw_vel = 0.0          # the eased shift is already ~0 here (cap = 2 x accel x time left)
				_lock_bite()
			elif not _impact_done:
				# locked: the head glows hot and pulses until it strikes
				_bite_glow.scale = Vector3.ONE * (1.1 + 0.15 * sin(state_time * 40.0))
			# the strike lands when the lunging head is down (it snaps 10 m in ~0.13 s; a frame of animation lag would
			# resolve it while the head is still high), at most 0.15 s after the fitted impact time
			var head_down_now := _bite_follow or visual.socket(_bite_head).global_position.y < 4.5
			if not _impact_done and state_time >= _impact_at and (head_down_now or state_time >= _impact_at + 0.15):
				_impact_done = true
				var r2 := _bite_hit()
				_bite_fx_off()
				if Game.harness and not _bite_follow:
					# where the head really is at the impact vs the warned circle (clip check)
					var hg := visual.socket(_bite_head).global_position
					Game.event("bite_land", {"clip": _bite_clip, "head_y": snappedf(hg.y, 0.01),
						"off": snappedf(Vector2(hg.x - _bite_center.x, hg.z - _bite_center.z).length(), 0.01)})
				Fx.spark(arena, _bite_center + Vector3.UP * 1.0, Color(1.0, 0.55, 0.2), 22, 0.12)
				Fx.dust(arena, _bite_center, T["bite_radius"], Color(0.18, 0.16, 0.16, 0.8))
				Sfx.play("hydra_bite", _bite_center)
				Game.shake(0.25)
				Game.event("attack_resolved", {"attack": "bite", "result": r2})
			if state_time >= _impact_at + _n("bite_recover"):
				set_state(&"guard")


## True when the real model has the per-side bite clips (A5).
func _has_side_bites() -> bool:
	return not visual.is_standin and visual.has_clip(&"bite_r") and visual.has_clip(&"bite_l")


## The bite whose head lands nearest the hero, if he stands within bite_radius + bite_spot_reach of that landing spot:
## side heads (bite_r / bite_l) from bite_min_deg to bite_side_max_deg off the snout, the centre head (bite) in front,
## once per guard cycle. {} = none (or the stand-in).
func _pick_bite(p: Vector3) -> Dictionary:
	if not _has_side_bites():
		return {}
	var ang := angle_to_pos(p)
	var reach := float(T["bite_radius"]) + _n("bite_spot_reach")
	var best := {}
	var bd := INF
	for o in BITES:
		if not visual.has_clip(o["clip"]):
			continue
		if o["side"]:
			var force_side := Game.harness and Game.args.has("hydra-side")
			if not force_side and (ang < _n("bite_min_deg") or ang > _n("bite_side_max_deg")):
				continue
		elif ang >= _n("bite_min_deg") or _bites > 0:
			continue
		var s := to_global(o["spot"])
		var d := Vector2(p.x - s.x, p.z - s.z).length()
		if d <= reach and d < bd:
			bd = d
			best = o
	return best


## Guard turn (hydra polish 2, natural movement): the body turns only while the walk clip steps. The turn rate eases in
## and out (turn_accel_deg, slowing down so it stops on the target) instead of pivoting at a flat 35 deg/s, and the
## walk clip's rate follows the real turn rate (see _walk_rate), so the feet step as fast as the body swings round.
## Real model with a walk clip only; the stand-in keeps the old face_towards.
## polish 2 re-fix: `brake` = slow the turn to a stop (an attack is about to start). The turn is a critically damped
## spring on the yaw error (turn_spring_k), its acceleration limited to turn_accel_deg and its rate to max_deg, so it
## settles onto a moving target without the old dead stop (v = 0 in one tick when the target was reached early).
func _guard_turn(target: Vector3, max_deg: float, delta: float, brake := false) -> void:
	if visual.is_standin or not visual.has_clip(&"walk"):
		if not brake:
			face_towards(target, max_deg, delta)
		return
	var err := _yaw_err_to(target)
	_tw_age += delta
	var c := visual.current_clip
	var turn_clip := _turn_walk and _is_walk_clip(c) and c != &"walk"
	# integrate2 (feet in a rendered run): an attack chosen mid-step blended its clip in from wherever the walk's feet
	# were (up to 1.2 m off the stance: 5 m/s foot slides under the fire clip's 0.3 s blend). The beast now steps on at
	# a slow matched turn (attack_wind_deg, the clip rate follows it, so the feet stay planted) until the walk reaches
	# its stop window (feet nearest the stance), at most attack_wind_max s, and only then brakes for the attack.
	if brake and turn_clip and not _in_stop_window() and _wind_t < _n("attack_wind_max"):
		_wind_t += delta
		var sgn := signf(_yaw_vel) if absf(_yaw_vel) > 0.5 else (signf(err) if absf(err) > 0.01 else 1.0)
		_yaw_vel = move_toward(_yaw_vel, sgn * _n("attack_wind_deg"), _n("turn_accel_deg") * delta)
		rotation.y += deg_to_rad(_yaw_vel) * delta
		return
	# integrate2: while the turn walk blends in from the idle the body barely turns (the blend moves the planted feet;
	# a full-rate turn on top of a half-weighted clip slid them 1-1.9 m/s): the rate cap ramps in over turn_walk_blend s
	if turn_clip and _tw_age < _n("turn_walk_blend"):
		var k := clampf(_tw_age / _n("turn_walk_blend"), 0.0, 1.0)
		max_deg = maxf(4.0, max_deg * k * k)
	_ease_turn(err, max_deg, _n("turn_accel_deg"), delta, not brake and (_turn_walk or absf(err) > _n("walk_turn_start_deg")))


## Signed yaw error (degrees, + = to the left) from the body's forward to `target`.
func _yaw_err_to(target: Vector3) -> float:
	var to := target - global_position
	to.y = 0.0
	if to.length() < 0.01:
		return 0.0
	return rad_to_deg(wrapf(atan2(to.x, to.z) - rotation.y, -PI, PI))


## One tick of the eased body turn: active = spring toward `err`, else brake to a stop. Rate and acceleration limited.
func _ease_turn(err: float, max_deg: float, acc: float, delta: float, active: bool) -> void:
	var dv := 0.0
	if active:
		var k := _n("turn_spring_k")
		dv = clampf((k * err - 2.0 * sqrt(k) * _yaw_vel) * delta, -acc * delta, acc * delta)
	else:
		dv = clampf(-_yaw_vel, -acc * delta, acc * delta)
	var v := _yaw_vel + dv
	if absf(v) > max_deg:
		# over the cap (the urgent rate ended): slow down to it at the acceleration limit, never in one tick
		v = signf(v) * maxf(max_deg, absf(_yaw_vel) - acc * delta)
	_yaw_vel = v
	rotation.y += deg_to_rad(_yaw_vel) * delta


func _urgent_turn_deg() -> float:
	return float(T["turn_deg"]) * _n("guard_urgent_turn_mult")


## Seconds the eased turn (_ease_turn, starting at the current _yaw_vel) needs to settle on an error of `err` degrees:
## simulated forward with the same numbers, at most 4 s.
func _turn_time_est(err: float, max_deg: float) -> float:
	var e := err
	var v := _yaw_vel
	var dt := 1.0 / 60.0
	var acc := _n("turn_accel_deg")
	var k := _n("turn_spring_k")
	var t := 0.0
	while t < 4.0 and (absf(e) > 1.5 or absf(v) > _n("attack_brake_deg")):
		var nv := v + clampf((k * e - 2.0 * sqrt(k) * v) * dt, -acc * dt, acc * dt)
		if absf(nv) > max_deg:
			nv = signf(nv) * maxf(max_deg, absf(v) - acc * dt)
		v = nv
		e -= v * dt
		t += dt
	return t


## Forced fire, inhale phase 1: the beast steps round to the aimed arc on the walk clip; once it faces it (or when
## only the fire clip's blend-in is left of the inhale) the fire clip blends in, timed so `fire_start` still lands at
## the end of the inhale.
func _tick_fire_step(delta: float) -> void:
	var err := _yaw_err_to(global_position + _fire_dir * 10.0)
	var left := _fire_windup - state_time
	_ease_turn(err, _urgent_turn_deg(), _n("turn_accel_deg"), delta, true)
	_update_turn_walk()
	if (absf(err) > 1.5 or absf(_yaw_vel) > _n("attack_brake_deg")) and left > 0.45:
		return
	_fire_stepping = false
	_turn_walk = false
	var ln := visual.clip_length(_fire_clip, 3.9)
	var fs := visual.event_time(_fire_clip, &"fire_start", ln * 0.38)
	var base := _n("fire_inhale") * _ws()
	var spd := fs / maxf(base, 0.1)
	if left * spd >= fs:
		visual.play(_fire_clip, 0.35, fs / maxf(left, 0.05))
	else:
		visual.play(_fire_clip, 0.35, spd, fs - left * spd)
	Game.event("fire_step_done", {"err": snappedf(err, 0.1), "yaw_vel": snappedf(_yaw_vel, 0.1), "left": snappedf(left, 0.01)})


## Walk clip rate for a body turning at `deg_s` in place: the forefeet sit ~r m from the pivot, so they must cover
## deg_s x r per second. With the manifest's `move_speed` (planted-foot speed at x1) that gives the exact rate; without
## it, walk_turn_speed is the rate at turn_deg. Clamped so a slow start or stop still shows steps.
func _walk_rate(deg_s: float, clip: StringName = &"") -> float:
	# animfix3: the turn-in-place clips (walk_turn_l/_r) carry their own move_speed (1.2: forefoot speed along its arc
	# at x1); their planted feet follow the turn exactly, so the rate may go lower (slow ease) and higher (urgent turn)
	var c := visual.current_clip if clip == &"" else clip
	var turn := _is_walk_clip(c) and c != &"walk"
	var ms := visual.move_speed(c if turn else &"walk")
	if ms > 0.05:
		if _foot_r <= 0.0:
			var r := 0.0
			for f in [&"foot_fl", &"foot_fr"]:
				var q := to_local(visual.socket(f).global_position)
				r += Vector2(q.x, q.z).length() * 0.5
			_foot_r = clampf(r, 1.0, 8.0)
		if turn:
			return clampf(deg_to_rad(deg_s) * _foot_r / ms, 0.1, 2.6)
		return clampf(deg_to_rad(deg_s) * _foot_r / ms, 0.3, 1.8)
	return clampf(_n("walk_turn_speed") * deg_s / float(T["turn_deg"]), 0.3, 1.5)


## Guard: the walk clip while the body turns (in place: the clip's feet step, the root stays), idle once it has
## stopped facing the hero. The clip rate tracks the eased turn rate every tick.
func _tick_turn_walk() -> void:
	if visual.is_standin or not visual.has_clip(&"walk"):
		return
	var ang := angle_to_pos(player.global_position)
	if _turn_walk and ang < _n("walk_turn_stop_deg") and absf(_yaw_vel) < 4.0:
		# animfix3: a turn walk ends in its stop window (feet nearest the stance), or after at most 0.35 s of waiting
		if _walk_stop_wait < 0.0:
			_walk_stop_wait = 0.0
		_walk_stop_wait += get_physics_process_delta_time()
		if _in_stop_window() or _walk_stop_wait > 0.35:
			Game.event("turn_walk_stop", {"clip": visual.current_clip, "t": snappedf(visual.clip_position(), 0.01),
				"in_window": _in_stop_window(), "waited": snappedf(_walk_stop_wait, 0.01)})
			_turn_walk = false
			_walk_stop_wait = -1.0
			visual.play(&"idle", 0.4)
		else:
			_update_turn_walk()
	elif not _turn_walk and ang > _n("walk_turn_start_deg"):
		_turn_walk = true
		_walk_stop_wait = -1.0
		_start_turn_walk(_yaw_err_to(player.global_position))
	elif _turn_walk:
		_walk_stop_wait = -1.0
		_update_turn_walk()


## animfix3 (planted feet while turning in place): the walk clip's feet travel straight back, so a body turning on it
## slid its planted feet 1.3-3.9 m/s. walk_turn_l / walk_turn_r move every planted foot along its circle about the body
## origin (the turn pivot); the clip follows the sign of the turn rate. Without them the old walk clip is used.
func _turn_clip(dir: float) -> StringName:
	var c := &"walk_turn_l" if dir >= 0.0 else &"walk_turn_r"
	return c if visual.has_clip(c) else &"walk"


## integrate2: an attack that starts out of a walk clip blends in longer (the walk's feet stand 0.45-1.2 m off the
## stance the attack clips start from: a 0.3 s blend slid them up to 5 m/s); out of the idle it keeps `base`.
func _attack_blend(base: float) -> float:
	return maxf(base, _n("attack_walk_blend")) if _is_walk_clip(visual.current_clip) else base


func _is_walk_clip(c: StringName) -> bool:
	return c == &"walk" or c == &"walk_turn_l" or c == &"walk_turn_r"


func _clip_row(c: StringName) -> Dictionary:
	return (visual.manifest.get("clips", {}) as Dictionary).get(String(c), {})


## Starts the turn walk toward `dir` (+ = left) at the clip's start_time (the phase whose feet sit nearest the stance:
## the idle -> walk blend then moves the feet ~0.45 m instead of up to 1.2 m).
func _start_turn_walk(dir: float) -> void:
	var d := dir if absf(_yaw_vel) < 2.0 else _yaw_vel
	var c := _turn_clip(d)
	var st := float(_clip_row(c).get("start_time", -1.0))
	_tw_age = 0.0
	visual.play(c, _n("turn_walk_blend") if c != &"walk" else 0.35, _walk_rate_for(c), st)
	Game.event("turn_walk_start", {"clip": c, "from": snappedf(st, 0.01)})


## Every tick of a turn walk: keep the clip on the side the body turns (same phase on a switch) and its rate on the
## real turn rate.
func _update_turn_walk() -> void:
	var c := visual.current_clip
	if c != &"walk" and _is_walk_clip(c) and absf(_yaw_vel) > 2.0:
		var want := _turn_clip(_yaw_vel)
		if want != c:
			visual.play(want, 0.25, _walk_rate_for(want), visual.clip_position())
	visual.set_speed(_walk_rate(maxf(absf(_yaw_vel), 4.0 if visual.current_clip != &"walk" else 12.0)))


func _walk_rate_for(c: StringName) -> float:
	return _walk_rate(maxf(absf(_yaw_vel), 4.0 if c != &"walk" else 12.0), c)


func _in_stop_window() -> bool:
	var w: Array = _clip_row(visual.current_clip).get("stop_window", [])
	if w.size() < 2:
		return true
	var t := visual.clip_position()
	return t >= float(w[0]) and t <= float(w[1])


## The next attack from guard (or &"" to keep guarding).
func _choose_attack() -> StringName:
	var p := player.global_position
	var d := player_distance()
	var ang := angle_to_pos(p)
	if Game.harness and Game.args.has("hydra-debug"):
		Game.event("dbg_choose", {"d": snappedf(d, 0.1), "ang": snappedf(ang, 0.1), "foot": snappedf(_dist_to_forefoot(p), 0.1), "bites": _bites})
	if _dist_to_forefoot(p) < _n("stomp_trigger_dist"):
		return &"stomp"
	if _bites < int(_n("bites_before_fire")):
		if not _has_side_bites():
			# stand-in: one clip for all heads, the circle follows the hero
			var side_ok := ang > _n("bite_min_deg") and ang < _n("bite_max_deg")
			if Game.harness and Game.args.has("hydra-side"):
				side_ok = true          # test variant: bites from any angle
			if d > _n("bite_min_dist") and d < _n("bite_max_dist") and side_ok:
				return &"bite"
		elif not _pick_bite(p).is_empty():
			return &"bite"
	if ang < _n("fire_front_deg"):
		return &"fire_sweep"
	# natural movement: from guard_force_fire the beast first steps round faster (see the guard tick); only when the
	# hero still outruns it for guard_force_fire_late more does it fire aimed off the snout (body pivots in the inhale)
	var force_at := _n("guard_force_fire") + (_n("guard_force_fire_late") if not visual.is_standin and visual.has_clip(&"walk") else 0.0)
	if state_time >= force_at:
		_forced_fire = true         # aimed at the hero (clamped), see _enter_state
		return &"fire_sweep"
	return &""


func _on_weak_hit(_point: WeakPoint) -> void:
	if state == &"head_down":
		_head_down_end = minf(_head_down_end, state_time + 0.6)
		_jaw_checked = true      # H1: the hurt clip lifts the jaw; a struck jaw was reachable, no fallback check after it
	if enraged() and not _was_enraged:
		_was_enraged = true
		visual.set_tint((Color.WHITE if visual.is_standin else MODEL_TINT) * ENRAGED_TINT)
		Sfx.play("hydra_roar", global_position)
		Game.event("enraged", {"boss": boss_id})


# ------------------------------------------------------------------ fire sweep
func _tick_fire(delta: float) -> void:
	var t := state_time - _fire_windup
	if t < 0.0:
		if _fire_turn_rate > 0.0:
			face_towards(global_position + _fire_dir * 10.0, _fire_turn_rate, delta)
		if _fire_stepping:
			_tick_fire_step(delta)
		elif absf(_yaw_vel) > 0.01 and not visual.is_standin:
			# the last of the stepping turn brakes out under the fire clip's blend-in
			_ease_turn(0.0, _urgent_turn_deg(), _n("turn_accel_deg"), delta, false)
		var k := clampf(state_time / _fire_windup, 0.0, 1.0)
		_throat.global_position = _mouth_pos()
		_throat.scale = Vector3.ONE * (0.4 + 1.4 * k)
		_throat_light.global_position = _mouth_pos()
		_throat_light.light_energy = 1.0 + 5.0 * k
		var em := _start_edge.material_override as StandardMaterial3D
		em.albedo_color.a = 0.55 + 0.4 * absf(sin(state_time * 9.0))
		_inhale_mat.set_shader_parameter("progress", k)
		return
	if not _fire_on:
		_inhale_fx.visible = false
		_start_fire()
	if _start_edge.visible and t >= _n("fire_lead_time"):
		_start_edge.visible = false
	var total := _n("fire_lead_time") + float(T["fire_time"]) * _fire_legs
	if t >= total:
		set_state(&"head_down")
		return
	# A3: enraged, the return pass starts where the first one ends (fire_end of fire_sweep / fire_sweep_l)
	if _fire_legs > 1 and not _fire_return_on and t >= _n("fire_lead_time") + float(T["fire_time"]):
		_fire_return_on = true
		var rc := _fire_return_clip()
		if visual.has_clip(rc):
			var span := visual.event_time(rc, &"fire_end", 2.2) - visual.event_time(rc, &"fire_start", 0.0)
			visual.play(rc, 0.2, span / float(T["fire_time"]))
	var phi := _flame_actual(t)
	_phi_now = phi
	_flame_hist.append([t, phi])
	while _flame_hist.size() > 2 and float(_flame_hist[0][0]) < t - _n("fire_trail_time") - 0.2:
		_flame_hist.pop_front()
	_scorch_paint(phi)
	var dir := _fire_dir.rotated(Vector3.UP, deg_to_rad(phi))
	_update_fire_fx(dir)
	if is_instance_valid(_arc_hold):
		_arc_hold.elapsed = 0.0         # keep the outline faint (no fill, never strikes) until the sweep ends
	_fire_tick_t -= delta
	if _fire_tick_t <= 0.0:
		_fire_tick_t += float(T["fire_tick"])
		if Game.harness and Game.args.has("hydra-debug"):
			Game.event("dbg_fire", {"t": snappedf(t, 0.01), "phi": snappedf(phi, 0.1), "th": snappedf(_signed_angle(player.global_position), 0.1),
				"tgt": snappedf(_signed_angle(_bot_fire_advice()["move_to"]), 0.1), "pstate": player.state})
		if _in_fire(player.global_position, t):
			var r := _burn_player()
			Game.event("attack_resolved", {"attack": "fire", "result": r})


## One fire tick on the hero (12 dmg per 0.25 s, unblockable): core's damage-over-time hit (opts `dot`) ignores the
## hit i-frames (roll i-frames still dodge), no flinch, no knockback, can kill. A landed tick reports "burn".
func _burn_player() -> StringName:
	var r := player.try_hit(int(T["fire_dmg"]), _fire_origin, {"blockable": false, "dot": true})
	return &"burn" if r == &"hit" else r


func _start_fire() -> void:
	_fire_on = true
	_fire_tick_t = float(T["fire_tick"])      # first tick 0.25 s in: a hero at the start edge gets a moment
	var th := _signed_angle(player.global_position)
	if is_instance_valid(_arc_hold):
		_arc_hold.cancel()
	_arc_hold = arena.telegraph_cone(_fire_origin, _fire_dir, T["fire_arc_deg"] * 0.5, T["fire_reach"], 999.0, COL_ARC_HOLD)
	_throat.visible = false
	_throat_light.visible = false
	# A2: re-time the clip so its rake (fire_start -> fire_end) lasts the lead-in + one pass (x1.0 with the 30 fps clips;
	# the enraged inhale ran it at x1.25 until here)
	if visual.current_clip == _fire_clip:
		var span := visual.event_time(_fire_clip, &"fire_end", 4.05) - visual.event_time(_fire_clip, &"fire_start", 1.5)
		if span > 0.1:
			visual.set_speed(span / (_n("fire_lead_time") + float(T["fire_time"])))
	_scorch_begin()
	for n in [_stream, _core, _ground_fire]:
		(n as Node3D).visible = true
	_stream.emitting = true
	_core.emitting = true
	_ground_fire.emitting = true
	_fire_light.visible = true
	Sfx.stop_loop(_fire_audio, 0.0)
	_fire_audio = Sfx.loop("hydra_fire", _head_pos())
	Game.event("fire_start", {"side": _fire_side, "legs": _fire_legs, "player_deg": snappedf(th, 0.1),
		"player_rho": snappedf(Vector2(player.global_position.x - _fire_origin.x, player.global_position.z - _fire_origin.z).length(), 0.01)})


func _stop_fire() -> void:
	if _fire_on:
		_scorch_end()
	_fire_on = false
	if _stream != null:
		_stream.emitting = false
		_core.emitting = false
		_ground_fire.emitting = false
		_fire_light.visible = false
		_throat.visible = false
		_throat_light.visible = false
	Sfx.stop_loop(_fire_audio, 0.25)
	_fire_audio = 0
	if _stream != null and is_inside_tree():
		# hide the emitters once their last particles are gone (see _fire_ramp: idle slots)
		get_tree().create_timer(1.5, false).timeout.connect(_hide_fire_emitters)
	if is_instance_valid(_arc_hold):
		_arc_hold.cancel()
	_arc_hold = null


## Flame angle (degrees, + = boss's left of the locked fire direction) at `t` seconds into the fire. The first
## `fire_lead_time` s the stream sweeps in from just outside the start edge (its inner edge reaches the arc edge at
## t = 0), then each pass rakes the 140 degree arc in fire_time.
func _flame_angle(t: float) -> float:
	var half: float = T["fire_arc_deg"] * 0.5
	var lead := _n("fire_lead_time")
	if t < lead:
		return _fire_side * lerpf(half + _n("fire_stream_half_deg"), half, clampf(t / maxf(lead, 0.01), 0.0, 1.0))
	t -= lead
	var leg_t: float = T["fire_time"]
	var leg := mini(int(t / leg_t), _fire_legs - 1)
	var u := clampf((t - leg * leg_t) / leg_t, 0.0, 1.0)
	var from := _fire_side * half
	var to := -_fire_side * half
	if leg % 2 == 1:
		var tmp := from
		from = to
		to = tmp
	return lerpf(from, to, u)


## True when `pos` is in the fire at `t`: inside the raking stream or on the ground it burned in the last
## `fire_trail_time` s, clipped to the warned arc (outside it is safe).
func _in_fire(pos: Vector3, t: float) -> bool:
	var to := pos - _fire_origin
	to.y = 0.0
	var rho := to.length()
	if rho > float(T["fire_reach"]) + Tuning.PLAYER_RADIUS * 0.5:
		return false
	var th := _signed_angle(pos)
	var pad := rad_to_deg(atan2(Tuning.PLAYER_RADIUS * 0.5, maxf(rho, 0.5)))
	var half: float = T["fire_arc_deg"] * 0.5
	if absf(th) > half + pad:
		return false
	var w := _n("fire_stream_half_deg") + pad
	var trail := _n("fire_trail_time")
	if not _flame_hist.is_empty():
		# the angles the flame was really shown at (the head-driven stream) over the trail
		for e in _flame_hist:
			if float(e[0]) >= t - trail - 0.001 and absf(th - float(e[1])) <= w:
				return true
		return false
	var k := 0.0
	while k <= trail + 0.001:
		if t - k < 0.0:
			break
		if absf(th - _flame_angle(t - k)) <= w:
			return true
		k += 0.05
	return false


## The flame angle shown at `t`: on the real model it follows the centre head (the mouth's angle seen from the apex x
## fire_head_gain, clamped to the arc + the stream's half width), so the stream leaves the head and sweeps with it; the
## stand-in uses the scripted sweep.
func _flame_actual(t: float) -> float:
	if visual.is_standin or not visual.has_clip(_fire_clip):
		return _flame_angle(t)
	var lim: float = T["fire_arc_deg"] * 0.5 + _n("fire_stream_half_deg")
	return clampf(_signed_angle(_mouth_pos()) * _n("fire_head_gain"), -lim, lim)


func _fire_return_clip() -> StringName:
	return FIRE_RETURN.get(_fire_clip, &"fire_sweep_return")


## +1 / -1: the direction the flame angle is moving at `t`.
func _flame_motion(t: float) -> float:
	var lead := _n("fire_lead_time")
	if t < lead:
		return -_fire_side
	var leg := mini(int((t - lead) / float(T["fire_time"])), _fire_legs - 1)
	return -_fire_side * (1.0 if leg % 2 == 0 else -1.0)


## Signed angle (degrees) of a position seen from the fire origin, relative to the locked fire direction.
func _signed_angle(pos: Vector3) -> float:
	var to := pos - _fire_origin
	to.y = 0.0
	var left := Vector3.UP.cross(_fire_dir)
	return rad_to_deg(atan2(to.dot(left), to.dot(_fire_dir)))


## A ground point at `ang_deg` (fire frame) and `rho` metres from the fire origin.
func _polar(ang_deg: float, rho: float) -> Vector3:
	return _fire_origin + _fire_dir.rotated(Vector3.UP, deg_to_rad(ang_deg)) * rho


# ------------------------------------------------------------------ helpers
func _head_pos() -> Vector3:
	return visual.socket(&"head_c").global_position


## The centre head's mouth: between head_c and the jaw socket, pushed out along the head bone (real model).
func _mouth_pos() -> Vector3:
	var h := visual.socket(&"head_c")
	if visual.is_standin:
		return h.global_position
	var j := visual.socket(&"jaw_c").global_position
	var bone := h.get_parent() as Node3D
	var d := Vector3.ZERO
	if bone != null:
		d = h.global_position - bone.global_position
		d = d.normalized() if d.length() > 0.01 else Vector3.ZERO
	return h.global_position.lerp(j, 0.5) + d * 0.7


## Where a locked-on strike from `from` should face (polish 2 re-fix, for core's requested Player._face_lock hook; not
## called until core adds BossBase.strike_point): the lying jaw when the hero is within 4 m of it, else the body.
func strike_point(from: Vector3) -> Vector3:
	if state == &"head_down" and weak_points.has(&"jaw"):
		var j := (weak_points[&"jaw"] as WeakPoint).global_position
		if Vector2(from.x - j.x, from.z - j.z).length() < 4.0:
			return j
	return global_position


func _near_forefoot() -> StringName:
	var p := player.global_position
	var a := visual.socket(&"foot_fl").global_position
	var b := visual.socket(&"foot_fr").global_position
	a.y = p.y
	b.y = p.y
	return &"foot_fl" if p.distance_to(a) <= p.distance_to(b) else &"foot_fr"


func _dist_to_forefoot(p: Vector3) -> float:
	var best := INF
	for f in [&"foot_fl", &"foot_fr"]:
		var q := visual.socket(f).global_position
		q.y = p.y
		best = minf(best, p.distance_to(q))
	return best


## The side head nearest the target, on the target's side (heads 1-4 on the right / -X, 5-8 on the left / +X).
func _bite_head_for(pos: Vector3) -> StringName:
	var local := to_local(pos)
	var ids := [&"head_5", &"head_6", &"head_7", &"head_8"] if local.x >= 0.0 else [&"head_1", &"head_2", &"head_3", &"head_4"]
	var best: StringName = ids[0]
	var bd := INF
	for id in ids:
		var d := visual.socket(id).global_position.distance_to(pos)
		if d < bd:
			bd = d
			best = id
	return best


## Lock aim: shoulder lerped 45% toward the centre head; it drops toward 4 m when the hero is close (at the shoulder
## the camera otherwise tilts up into the necks and loses the ground), and blends toward the stream while it rakes.
func get_lock_point() -> Vector3:
	var body := global_position + Vector3.UP * float(T["shoulder"])
	var lp := body.lerp(_head_pos(), 0.45)
	var near := _n("cam_near_dist")
	var k := clampf((near - player_distance()) / 4.0, 0.0, 1.0) if player != null else 0.0
	lp.y = lerpf(lp.y, _n("cam_near_height"), k)
	if _cam_fire_w > 0.001:
		lp = lp.lerp(_cam_fire_target, _cam_fire_w)
	return lp


func _process(delta: float) -> void:
	var want := _n("cam_fire_weight") if state == &"fire_sweep" and _fire_on else 0.0
	_cam_fire_w = move_toward(_cam_fire_w, want, delta * 1.2)


# ------------------------------------------------------------------ fire start edge / jaw fallback / bite lock
## The inhale overlay on the fire arc: apex at the fire origin, +Z of the plane along the fire direction.
func _show_inhale_fx() -> void:
	_inhale_fx.global_position = Vector3(_fire_origin.x, 0.06, _fire_origin.z)
	_inhale_fx.global_rotation = Vector3(0, atan2(_fire_dir.x, _fire_dir.z), 0)
	_inhale_mat.set_shader_parameter("progress", 0.0)
	_inhale_fx.visible = true


## Bright pulsing line on the edge of the arc where the first pass will start (shown while it inhales).
func _show_start_edge() -> void:
	var half: float = T["fire_arc_deg"] * 0.5
	var reach: float = T["fire_reach"]
	var d := _fire_dir.rotated(Vector3.UP, deg_to_rad(_fire_side * half))
	# a little inside the arc so it reads as the arc's own edge
	d = d.rotated(Vector3.UP, deg_to_rad(-_fire_side * 1.0))
	_start_edge.global_position = _fire_origin + d * (reach * 0.5) + Vector3.UP * 0.07
	_start_edge.global_rotation = Vector3(0, atan2(d.x, d.z), 0)
	_start_edge.visible = true


## From 0.3 s into head_down: once the jaw has stopped dropping (or at 1.0 s) and is still above sword reach (a real
## model whose head_down clip does not bring jaw_c down), move the weak point to a ground marker where the head should
## lie (6.8 m ahead, 1.2 m high), so the fight stays winnable. Called each tick until decided.
func _check_jaw_reachable() -> void:
	var wp: WeakPoint = weak_points[&"jaw"]
	var y := wp.global_position.y
	# poses update per render frame, physics may tick several times per frame: track the last time it dropped
	if y < _jaw_prev_y - 0.02:
		_jaw_prev_y = y
		_jaw_drop_t = state_time
	var limit := 0.1 + Tuning.SWORD_HEIGHT + wp.radius + 0.5
	var force := Game.harness and Game.args.has("hydra-jaw-fallback")    # harness test of the fallback
	if y <= limit and not force:
		# H1: reachable at any moment = reachable (a hurt flinch afterwards must not trigger the fallback)
		_jaw_checked = true
		Game.event("jaw_ok", {"jaw_y": snappedf(y, 0.01), "t": snappedf(state_time, 0.01)})
		return
	if state_time < 0.3:
		return
	if state_time - _jaw_drop_t < 0.15 and state_time < 1.0 and not force:
		return            # still coming down
	_jaw_checked = true
	var m := visual.add_socket(&"jaw_ground", Vector3.ZERO)
	m.global_position = to_global(Vector3(0, _n("jaw_ground_height"), _n("jaw_fwd_guess")))
	var was_y := wp.global_position.y
	wp.reparent(m, false)
	wp.position = Vector3.ZERO
	_jaw_moved = true
	var msg := "Hydra: jaw weak point at %.1f m in head_down (limit %.1f m): moved to the ground marker 'jaw_ground'. Art track: the head_down clip must bring jaw_c down." % [was_y, limit]
	push_warning(msg)
	Game.event("jaw_fallback", {"jaw_y": snappedf(was_y, 0.01), "limit": snappedf(limit, 0.01)})


func _restore_jaw() -> void:
	if not _jaw_moved:
		return
	_jaw_moved = false
	var wp: WeakPoint = weak_points[&"jaw"]
	wp.reparent(visual.socket(&"jaw_c"), false)
	wp.position = Vector3.ZERO


## The bite circle stops following: recolour (new decal for the time left), light pillar, hot head, second hiss.
func _lock_bite() -> void:
	_bite_locked = true
	if is_instance_valid(_decal):
		_decal.cancel()
	var left := maxf(_impact_at - state_time, 0.05)
	_decal = arena.telegraph_circle(_bite_center, T["bite_radius"], left, COL_BITE_LOCK)
	_bite_pillar.global_position = _bite_center + Vector3.UP * (BITE_RIM_H * 0.5 + 0.02)
	_bite_pillar.visible = true
	_bite_glow_light.light_energy = 5.0
	Sfx.play("hydra_bite_warn", visual.socket(_bite_head).global_position, 2.0, 1.35)
	Game.event("bite_lock", {"left": snappedf(left, 0.01)})


## Bite impact: radius test on the locked circle, then try_hit FROM the biting head's ground position, so the shield
## arc is tested against where the bite really comes from (hit_circle would test it against the circle centre).
func _bite_hit() -> StringName:
	var d := player.global_position - _bite_center
	d.y = 0.0
	if d.length() > float(T["bite_radius"]) + Tuning.PLAYER_RADIUS * 0.5:
		return &"miss"
	# the head's ground position, pulled in toward the body so it never lies past the hero (the stand-in's outer heads
	# hang up to 10 m out to the side, over or behind a hero standing 8 m away)
	var c := global_position
	c.y = 0.0
	var hp_ := player.global_position
	hp_.y = 0.0
	var hg := visual.socket(_bite_head).global_position
	hg.y = 0.0
	var off := hg - c
	var max_len := maxf(c.distance_to(hp_) - 1.5, 0.0)
	if off.length() > max_len:
		off = off.normalized() * max_len if off.length() > 0.01 else Vector3.ZERO
	var from := c + off
	if Game.harness and (Game.args.has("hydra-debug") or Game.args.has("hydra-probe")):
		var to_from := from - hp_
		Game.event("dbg_bite_from", {"head": _bite_head, "from_dist": snappedf(to_from.length(), 0.01),
			"facing_deg": snappedf(rad_to_deg(player.facing.angle_to(to_from.normalized())), 0.1), "pstate": player.state})
	return player.try_hit(T["bite_dmg"], from, {"blockable": true, "knockback": _n("bite_knockback")})


func _bite_fx_off() -> void:
	_bite_glow.visible = false
	_bite_glow_light.visible = false
	_bite_pillar.visible = false


# ------------------------------------------------------------------ VFX (built-in nodes only)
## Fire colour over a particle's life (yellow -> orange -> red -> out). `k` scales the alpha (additive layers stack up).
func _fire_ramp(k := 1.0) -> Gradient:
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.62, 0.12, 0.9 * k))
	# ends on black: CPUParticles3D draws idle particle slots at the emitter in the ramp's last colour (seen as dark or
	# orange balls hanging where the mouth was); black is invisible with the additive blend used for the fire
	g.set_color(1, Color(0.0, 0.0, 0.0, 0.0))
	g.add_point(0.25, Color(0.95, 0.32, 0.04, 0.85 * k))
	g.add_point(0.55, Color(0.7, 0.12, 0.03, 0.65 * k))
	g.add_point(0.8, Color(0.22, 0.06, 0.04, 0.35 * k))
	return g


func _fire_material(additive: bool) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if additive else BaseMaterial3D.BLEND_MODE_MIX
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true       # the ramp colours are picked in sRGB (linear made them pale yellow)
	m.albedo_texture = Fx.soft_dot()
	m.disable_fog = true
	# fade out near the camera so the chase camera never loses the hero in the flames
	m.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_ALPHA
	m.distance_fade_min_distance = _n("fire_fade_near")
	m.distance_fade_max_distance = _n("fire_fade_far")
	return m


func _scale_curve(a: float, b: float) -> Curve:
	var c := Curve.new()
	c.max_value = maxf(a, b)
	c.add_point(Vector2(0, a))
	c.add_point(Vector2(1, b))
	return c


func _build_fire_fx() -> void:
	_fire_fx = Node3D.new()
	_fire_fx.name = "HydraFX"
	_fire_fx.top_level = true          # world space (the boss is still being added to the arena here)
	add_child(_fire_fx)
	# the stream from the mouth
	_stream = CPUParticles3D.new()
	_stream.name = "Stream"
	_stream.emitting = false
	_stream.amount = 360
	_stream.lifetime = 1.0
	_stream.local_coords = false
	_stream.spread = 7.0
	_stream.initial_velocity_min = STREAM_SPEED * 0.9
	_stream.initial_velocity_max = STREAM_SPEED * 1.1
	_stream.gravity = Vector3(0, -3.0, 0)
	_stream.scale_amount_min = 0.8
	_stream.scale_amount_max = 1.3
	_stream.scale_amount_curve = _scale_curve(0.35, 2.8)
	_stream.color_ramp = _fire_ramp(0.5)
	var qm := QuadMesh.new()
	qm.size = Vector2(0.9, 0.9)
	qm.material = _fire_material(true)      # additive: CPUParticles3D draws its idle slots black at the emitter, ADD hides them
	_stream.mesh = qm
	_fire_fx.add_child(_stream)
	_core = CPUParticles3D.new()
	_core.name = "Core"
	_core.emitting = false
	_core.amount = 160
	_core.lifetime = 0.5
	_core.local_coords = false
	_core.spread = 2.5
	_core.initial_velocity_min = STREAM_SPEED
	_core.initial_velocity_max = STREAM_SPEED * 1.1
	_core.scale_amount_curve = _scale_curve(0.5, 1.6)
	var cg := Gradient.new()
	cg.set_color(0, Color(1.0, 0.95, 0.7, 0.8))
	cg.set_color(1, Color(0.0, 0.0, 0.0, 0.0))
	cg.add_point(0.7, Color(1.0, 0.45, 0.1, 0.4))
	_core.color_ramp = cg
	var qc := QuadMesh.new()
	qc.size = Vector2(0.55, 0.55)
	qc.material = _fire_material(true)
	_core.mesh = qc
	_fire_fx.add_child(_core)
	# flames rising from the ground along the stream's path (they linger as the stream rakes on)
	_ground_fire = CPUParticles3D.new()
	_ground_fire.name = "GroundFire"
	_ground_fire.emitting = false
	_ground_fire.amount = 220
	_ground_fire.lifetime = 0.7      # the burning trail behind the stream (damage lasts fire_trail_time = 0.3 s)
	_ground_fire.local_coords = false
	_ground_fire.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_ground_fire.emission_box_extents = Vector3(1.3, 0.2, 1.0)
	_ground_fire.direction = Vector3.UP
	_ground_fire.spread = 20.0
	_ground_fire.initial_velocity_min = 2.0
	_ground_fire.initial_velocity_max = 5.0
	_ground_fire.gravity = Vector3(0, 1.5, 0)
	_ground_fire.scale_amount_min = 1.0
	_ground_fire.scale_amount_max = 2.0
	_ground_fire.scale_amount_curve = _scale_curve(1.0, 2.6)
	_ground_fire.color_ramp = _fire_ramp(0.55)
	var qg := QuadMesh.new()
	qg.size = Vector2(1.4, 1.4)
	qg.material = _fire_material(true)
	_ground_fire.mesh = qg
	_fire_fx.add_child(_ground_fire)
	_fire_light = OmniLight3D.new()
	_fire_light.light_color = Color(1.0, 0.5, 0.15)
	_fire_light.light_energy = 4.0
	_fire_light.omni_range = 22.0
	_fire_light.visible = false
	_fire_fx.add_child(_fire_light)
	# glowing throat while inhaling
	_throat = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.6
	sm.height = 1.2
	_throat.mesh = sm
	var tm := StandardMaterial3D.new()
	tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	tm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	tm.albedo_color = Color(1.0, 0.55, 0.12, 0.85)
	_throat.material_override = tm
	_throat.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_throat.visible = false
	_fire_fx.add_child(_throat)
	_throat_light = OmniLight3D.new()
	_throat_light.light_color = Color(1.0, 0.45, 0.1)
	_throat_light.omni_range = 9.0
	_throat_light.visible = false
	_fire_fx.add_child(_throat_light)
	# smoke from the head while it lies on the ground
	_smoke = CPUParticles3D.new()
	_smoke.name = "Smoke"
	_smoke.emitting = false
	_smoke.amount = 20
	_smoke.lifetime = 1.4          # qa fix: was 2.2 s (the column outlived head_down)
	_smoke.local_coords = false
	_smoke.direction = Vector3.UP
	_smoke.spread = 25.0
	_smoke.initial_velocity_min = 1.0
	_smoke.initial_velocity_max = 2.2
	_smoke.gravity = Vector3(0, 0.6, 0)
	var sc := Curve.new()
	sc.max_value = 3.0
	sc.add_point(Vector2(0.0, 0.3))
	sc.add_point(Vector2(0.25, 1.6))
	sc.add_point(Vector2(0.75, 2.8))
	sc.add_point(Vector2(1.0, 0.2))
	_smoke.scale_amount_curve = sc
	var qs := QuadMesh.new()
	qs.size = Vector2(1.4, 1.4)
	# own plain material: with vertex colours from a ramp this emitter drew an opaque black blob where it stood
	# (seen in the windowed shots); a flat grey with a soft dot and a grow-then-shrink scale reads as smoke
	var smat := StandardMaterial3D.new()
	smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smat.albedo_color = Color(0.55, 0.51, 0.48, 0.3)
	smat.albedo_texture = Fx.soft_dot()
	smat.disable_fog = true
	# qa fix: smoke within ~4 m of the chase camera fades out (it covered the hero's torso)
	smat.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_ALPHA
	smat.distance_fade_min_distance = 2.5
	smat.distance_fade_max_distance = 6.5
	_smoke_mat = smat
	qs.material = smat
	_smoke.mesh = qs
	_fire_fx.add_child(_smoke)
	# inhale warning overlay (hatch + bright pulsing edge) over the translucent cone telegraph
	_inhale_fx = MeshInstance3D.new()
	_inhale_fx.name = "InhaleWarn"
	var ipl := PlaneMesh.new()
	var ireach: float = T["fire_reach"]
	ipl.size = Vector2(ireach * 2.0 + 2.0, ireach * 2.0 + 2.0)
	_inhale_fx.mesh = ipl
	_inhale_mat = ShaderMaterial.new()
	var ish := Shader.new()
	ish.code = INHALE_SHADER
	_inhale_mat.shader = ish
	_inhale_mat.set_shader_parameter("reach", ireach)
	_inhale_mat.set_shader_parameter("half_angle", deg_to_rad(float(T["fire_arc_deg"]) * 0.5))
	_inhale_mat.render_priority = -9           # over the telegraph fill (-10), under every other VFX
	_inhale_fx.material_override = _inhale_mat
	_inhale_fx.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_inhale_fx.visible = false
	_fire_fx.add_child(_inhale_fx)
	# bright start edge of the fire arc (where the first pass begins), shown while it inhales
	_start_edge = MeshInstance3D.new()
	_start_edge.name = "FireStartEdge"
	var bm := BoxMesh.new()
	bm.size = Vector3(0.55, 0.02, float(T["fire_reach"]))
	_start_edge.mesh = bm
	var em := StandardMaterial3D.new()
	em.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	em.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	em.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	em.albedo_color = Color(1.0, 0.85, 0.45, 0.9)
	em.disable_fog = true
	_start_edge.material_override = em
	_start_edge.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_start_edge.visible = false
	_fire_fx.add_child(_start_edge)
	# the biting head's glow (which head comes) and the light pillar over the locked bite circle (reads above the HUD)
	_bite_glow = MeshInstance3D.new()
	_bite_glow.name = "BiteGlow"
	var gs := QuadMesh.new()
	gs.size = Vector2(2.2, 2.2)
	_bite_glow.mesh = gs
	var gm := StandardMaterial3D.new()
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	gm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	gm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	gm.albedo_color = Color(COL_BITE_GLOW.r, COL_BITE_GLOW.g, COL_BITE_GLOW.b, 0.85)
	gm.albedo_texture = Fx.soft_dot()      # a soft ember glow (billboard), not a hard ball over the head
	gm.disable_fog = true
	_bite_glow.material_override = gm
	_bite_glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_bite_glow.visible = false
	_fire_fx.add_child(_bite_glow)
	_bite_glow_light = OmniLight3D.new()
	_bite_glow_light.light_color = COL_BITE_GLOW
	_bite_glow_light.omni_range = 7.0
	_bite_glow_light.visible = false
	_fire_fx.add_child(_bite_glow_light)
	_bite_pillar = MeshInstance3D.new()
	_bite_pillar.name = "BitePillar"
	var pc := CylinderMesh.new()
	pc.top_radius = float(T["bite_radius"])
	pc.bottom_radius = float(T["bite_radius"])
	pc.height = BITE_RIM_H        # qa fix: a thin ember rim on the circle's edge, not a 3.2 m column around the hero
	pc.cap_top = false
	pc.cap_bottom = false
	pc.radial_segments = 40
	pc.rings = 1
	_bite_pillar.mesh = pc
	var pm := StandardMaterial3D.new()
	pm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	pm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	pm.cull_mode = BaseMaterial3D.CULL_DISABLED
	pm.albedo_color = Color(1.0, 0.55, 0.15, 0.55)
	pm.disable_fog = true
	_bite_pillar.material_override = pm
	_bite_pillar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_bite_pillar.visible = false
	_fire_fx.add_child(_bite_pillar)
	# scorched arc decal (painted while the stream rakes, fades afterwards); drawn under the telegraphs (-10)
	_scorch = MeshInstance3D.new()
	_scorch.name = "ScorchArc"
	var pl := PlaneMesh.new()
	var reach: float = T["fire_reach"]
	pl.size = Vector2(reach * 2.0 + 2.0, reach * 2.0 + 2.0)
	_scorch.mesh = pl
	_scorch_mat = ShaderMaterial.new()
	var ssh := Shader.new()
	ssh.code = SCORCH_SHADER
	_scorch_mat.shader = ssh
	_scorch_mat.set_shader_parameter("reach", reach)
	_scorch_mat.render_priority = -12
	_scorch.material_override = _scorch_mat
	_scorch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_scorch.visible = false
	_fire_fx.add_child(_scorch)


## Points the stream from the mouth along `dir` and lays the ground fire along the burning line.
func _update_fire_fx(dir: Vector3) -> void:
	var mouth := _mouth_pos()
	# the head is still diving at fire start (13 m -> 5 m): start the visible stream once the mouth is low, so the
	# moving emitter does not leave a column of flame pointing up into the sky
	var low := mouth.y < 6.5 or visual.is_standin
	_stream.emitting = low
	_core.emitting = low
	var reach: float = T["fire_reach"]
	var land := _fire_origin + dir * reach * 0.62
	var to := land - mouth
	_stream.global_position = mouth
	_stream.direction = to.normalized()
	_stream.lifetime = clampf(to.length() / STREAM_SPEED, 0.4, 1.4)
	_core.global_position = mouth
	_core.direction = _stream.direction
	_core.lifetime = _stream.lifetime * 0.6
	# ground fire: a box from 3 m out to the full reach, along dir
	var mid := _fire_origin + dir * (reach * 0.5 + 1.5)
	_ground_fire.global_position = mid + Vector3.UP * 0.2
	_ground_fire.global_rotation = Vector3(0, atan2(dir.x, dir.z), 0)
	_ground_fire.emission_box_extents = Vector3(1.4, 0.2, reach * 0.5 - 1.5)
	_fire_light.global_position = land + Vector3.UP * 2.0
	_fire_light.light_energy = 3.5 + 1.5 * sin(state_time * 31.0)
	# camera: aim partly at the stream where it crosses the hero's distance (smoothed, see get_lock_point)
	var pr := Vector2(player.global_position.x - _fire_origin.x, player.global_position.z - _fire_origin.z).length()
	var tgt := _fire_origin + dir * clampf(pr, 8.0, reach * 0.6) + Vector3.UP * 1.5
	_cam_fire_target = tgt if _cam_fire_w <= 0.001 else _cam_fire_target.lerp(tgt, 1.0 - exp(-4.0 * get_physics_process_delta_time()))
	Sfx.move_loop(_fire_audio, mouth)


## Scorched arc on the basalt: soot + embers painted over the angles the stream has burned, faded after the fire.
func _hide_fire_emitters() -> void:
	if _fire_on:
		return
	for n in [_stream, _core, _ground_fire]:
		(n as Node3D).visible = false


func _scorch_begin() -> void:
	if _scorch_tw != null and _scorch_tw.is_valid():
		_scorch_tw.kill()
	_scorch.global_position = Vector3(_fire_origin.x, 0.03, _fire_origin.z)
	_scorch.global_rotation = Vector3(0, atan2(_fire_dir.x, _fire_dir.z), 0)
	_scorch_lo = 999.0
	_scorch_hi = -999.0
	_scorch_mat.set_shader_parameter("a_lo", 0.0)
	_scorch_mat.set_shader_parameter("a_hi", 0.0)
	_scorch_mat.set_shader_parameter("alpha", 0.85)
	_scorch_mat.set_shader_parameter("heat", 1.0)
	_scorch.visible = true


func _scorch_paint(phi: float) -> void:
	var half: float = T["fire_arc_deg"] * 0.5
	var w := _n("fire_stream_half_deg") * 0.7
	_scorch_lo = clampf(minf(_scorch_lo, phi - w), -half, half)
	_scorch_hi = clampf(maxf(_scorch_hi, phi + w), -half, half)
	if _scorch_hi > _scorch_lo:
		_scorch_mat.set_shader_parameter("a_lo", deg_to_rad(_scorch_lo))
		_scorch_mat.set_shader_parameter("a_hi", deg_to_rad(_scorch_hi))


func _scorch_end() -> void:
	if _scorch_tw != null and _scorch_tw.is_valid():
		_scorch_tw.kill()
	_scorch_tw = create_tween()
	_scorch_tw.set_parallel(true)
	_scorch_tw.tween_method(func(v: float) -> void: _scorch_mat.set_shader_parameter("heat", v), 1.0, 0.0, 1.6)
	_scorch_tw.tween_method(func(v: float) -> void: _scorch_mat.set_shader_parameter("alpha", v), 0.85, 0.0, _n("scorch_fade_time")).set_ease(Tween.EASE_IN)
	_scorch_tw.chain().tween_callback(func() -> void: _scorch.visible = false)


func _stomp_fx(center: Vector3) -> void:
	Fx.dust(arena, center, T["stomp_radius"], Color(0.2, 0.17, 0.16, 0.85))
	Fx.spark(arena, center + Vector3.UP * 0.4, Color(1.0, 0.55, 0.15), 30, 0.14)
	Sfx.play("hydra_stomp", center)
	Game.shake(0.7)
	# expanding shockwave ring
	var ring := MeshInstance3D.new()
	var tor := TorusMesh.new()
	tor.inner_radius = 0.86
	tor.outer_radius = 1.0
	tor.rings = 48
	ring.mesh = tor
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(1.0, 0.7, 0.35, 0.9)
	ring.material_override = m
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	arena.add_child(ring)
	ring.global_position = center + Vector3.UP * 0.15
	ring.scale = Vector3(0.6, 0.25, 0.6)
	var r: float = T["stomp_radius"]
	var tw := ring.create_tween()
	tw.set_parallel(true)
	tw.tween_property(ring, "scale", Vector3(r * 1.1, 0.25, r * 1.1), 0.35).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(m, "albedo_color:a", 0.0, 0.45)
	tw.chain().tween_callback(ring.queue_free)


# ------------------------------------------------------------------ test bot
## Strategy (SPEC intent): wait in front of the snout outside bite and stomp range; when the head inhales, run to the
## nearer shoulder (outside the arc); stay there while the stream comes; on the last pass follow it in from behind;
## strike under the jaw while the head lies on the ground; back away from the stomping forefoot; roll bites.
func bot_advice() -> Dictionary:
	if Game.harness and Game.args.has("hydra-probe"):
		return _probe_advice(String(Game.args["hydra-probe"]))
	var p := player.global_position
	var adv := {"move_to": p, "face": global_position, "roll": false, "block": false, "attack": false}
	var to_p := p - global_position
	to_p.y = 0.0
	var away := to_p.normalized() if to_p.length() > 0.1 else forward()
	match state:
		&"fire_sweep":
			var fa := _bot_fire_advice()
			adv["move_to"] = fa["move_to"]
			adv["roll"] = fa["roll"]
		&"head_down":
			if is_exposed(&"jaw"):
				var wp: WeakPoint = weak_points[&"jaw"]
				var j := wp.global_position
				j.y = 0.0
				var out := j - global_position
				out.y = 0.0
				out = out.normalized() if out.length() > 0.1 else forward()
				# final check: front stand 0.5 m closer (0.7 -> 0.2 m past the jaw, inside the resting head's collider:
				# the hero stops against its rounded end ~1.0 m from the jaw, the jaw straight ahead).
				# Harness probes: `--jaw-stand=<m>` overrides it, `--jaw-reach=<m>` the swing distance on the lying
				# jaw, `--jaw-wait=<s>` holds the swing until the head lies still.
				var stand_k := BOT_JAW_STAND if not visual.is_standin else 1.1
				if Game.harness and Game.args.has("jaw-stand"):
					stand_k = float(Game.args["jaw-stand"])
				adv["move_to"] = j + out * stand_k
				# coming from the flank on the body side of the head: the locked hero faces the body, so he must end up
				# outside the jaw. Stand-in: round a waypoint off the snout. Real model (final check: from the flank
				# the walk round that waypoint took ~1.9 s of the enraged 2.5 s opening): a waypoint just clear of the
				# head's rounded end on his own side, then the front stand (he stops against the head ~1.0 m from the jaw)
				var pin := p - global_position
				pin.y = 0.0
				var rel := pin.dot(out) - (j - global_position).dot(out)     # hero's radial position past the jaw
				var lat_v := pin - out * pin.dot(out)
				var lat := lat_v.normalized() if lat_v.length() > 0.1 else out.cross(Vector3.UP)
				if visual.is_standin:
					if rel < 0.2:
						adv["move_to"] = j + out * 1.4 + lat * 1.3
				elif rel < BOT_JAW_ROUND_REL:
					adv["move_to"] = j + out * BOT_JAW_SIDE_OUT + lat * BOT_JAW_SIDE
				# the locked hero faces the boss: strike only when the jaw is in front of him, inside the sword box
				var d := j - p
				d.y = 0.0
				var fwd := global_position - p
				fwd.y = 0.0
				fwd = fwd.normalized()
				var ahead := d.dot(fwd)
				var lateral := absf(d.dot(fwd.cross(Vector3.UP)))
				var wait_ok := not (Game.harness and Game.args.has("jaw-wait")) or state_time >= float(Game.args["jaw-wait"])
				if visual.is_standin:
					adv["attack"] = ahead > -0.2 and ahead < Tuning.SWORD_REACH + wp.radius * 0.6 \
							and lateral < Tuning.SWORD_WIDTH * 0.5 + wp.radius * 0.5 \
							and wp.global_position.y < 0.1 + Tuning.SWORD_HEIGHT + wp.radius * 0.6
				elif wp.global_position.y < 1.0:
					# the lying jaw (y 0.5-0.7): only from close in (BOT_JAW_REACH flat distance) and from past the jaw
					# (rel > 0.3: beside the head the swing's forward step carries him toward the body, gap ~0)
					var reach := BOT_JAW_REACH if not (Game.harness and Game.args.has("jaw-reach")) else float(Game.args["jaw-reach"])
					adv["attack"] = wait_ok and rel > 0.3 and ahead > -0.2 and d.length() < reach and lateral < BOT_JAW_LATERAL
				else:
					# still dropping (y >= 1 m, the first ~0.5 s): the slash at 1.4-1.7 m meets it further out
					adv["attack"] = wait_ok and ahead > -0.2 and ahead < Tuning.SWORD_REACH + wp.radius * 0.2 \
							and lateral < BOT_JAW_LATERAL and wp.global_position.y < 0.1 + Tuning.SWORD_HEIGHT + wp.radius * 0.6
			else:
				adv["move_to"] = _bot_away_from_feet(p)
		&"head_up":
			adv["move_to"] = _bot_away_from_feet(p)
		&"stomp":
			var off := p - _stomp_center
			off.y = 0.0
			var out2 := off.normalized() if off.length() > 0.1 else away
			var r: float = T["stomp_radius"]
			adv["move_to"] = _stomp_center + out2 * (r + 3.0)
			var left := _impact_at - state_time
			adv["roll"] = not _impact_done and left < 0.32 and left > 0.04 and off.length() < r + 0.8
		&"bite":
			var off2 := p - _bite_center
			off2.y = 0.0
			var side := away.cross(Vector3.UP)
			adv["move_to"] = p + side * 4.0
			if not _bite_follow:
				# the circle is where the head lands: get out of it, away from its centre (sideways when on it)
				var out3 := off2.normalized() if off2.length() > 0.4 else side
				adv["move_to"] = _bite_center + out3 * (float(T["bite_radius"]) + 3.0)
			var left2 := _impact_at - state_time
			adv["roll"] = not _impact_done and left2 < 0.3 and left2 > 0.04 and off2.length() < float(T["bite_radius"]) + 0.8
		_:
			# in front of the snout: no bites (front), no stomp (feet), close enough to reach a shoulder during the
			# inhale (closer when enraged: the inhale is shorter)
			adv["move_to"] = global_position + away * (6.6 if enraged() else 7.5)
			if Game.harness and Game.args.has("hydra-side"):
				# test variant (with the bite angle check off): wait 9 m out, in bite range, to exercise bite + roll
				adv["move_to"] = global_position + away * 9.0
				if _has_side_bites():
					# real model: wait by a side head's landing spot (7.2 m out, 86 deg off the snout, clear of the forefoot)
					var sx := 1.0 if to_local(p).x >= 0.0 else -1.0
					adv["move_to"] = to_global(Vector3(sx * 7.2, 0.0, 0.5))
	return adv


## During the fire: escape to the shoulder while it inhales; outside the arc wait for the stream; once the LAST pass
## has gone by, follow it in toward the head; caught inside with the stream coming, roll through it to its far side.
## Returns {move_to, roll}.
func _bot_fire_advice() -> Dictionary:
	var p := player.global_position
	var th := _signed_angle(p)
	var rho := Vector2(p.x - _fire_origin.x, p.z - _fire_origin.z).length()
	var half: float = T["fire_arc_deg"] * 0.5
	var flank_rho := clampf(rho, 4.5, 6.0)
	var side := 1.0 if th >= 0.0 else -1.0
	var t := state_time - _fire_windup
	if t < 0.0:
		return {"move_to": _polar(side * (half + 14.0), flank_rho), "roll": false}
	var phi := _phi_now if not _flame_hist.is_empty() else _flame_angle(t)
	var mv := _flame_motion(t)
	var sh := _n("fire_stream_half_deg")
	# stay behind the stream AND its burning trail (fire_trail_time worth of sweep)
	var trail_deg := float(T["fire_arc_deg"]) / float(T["fire_time"]) * _n("fire_trail_time")
	var margin := sh + trail_deg + 8.0
	var final_leg := t - _n("fire_lead_time") >= float(T["fire_time"]) * (_fire_legs - 1)
	var lead := mv * (th - phi)                # > 0: the stream is coming at the hero; < 0: it has gone by
	if lead < -margin:
		if final_leg:
			# follow the stream in toward where the head will land, staying `margin` behind it
			var jaw_rho := _n("jaw_fwd_guess") - _n("fire_origin_fwd") + 1.1
			var want := 0.0
			if mv * (phi - want) < margin:
				want = phi - mv * margin
			return {"move_to": _polar(want, jaw_rho), "roll": false}
		# it will come back: get outside on the side it came from
		return {"move_to": _polar(-mv * (half + 14.0), flank_rho), "roll": false}
	if lead <= 0.0:
		# just behind the stream: keep away from it
		return {"move_to": _polar(clampf(phi - mv * margin, -half - 14.0, half + 14.0), flank_rho), "roll": false}
	if absf(th) > half + 6.0:
		return {"move_to": _polar(side * (half + 14.0), flank_rho), "roll": false}
	# inside the arc and the stream is coming: run for the exit ahead, or roll through it when it is close
	var gap := rho * deg_to_rad(lead - sh) - Tuning.PLAYER_RADIUS
	if gap < 1.8:
		return {"move_to": _polar(phi - mv * margin, rho), "roll": gap > -0.5}
	return {"move_to": _polar(mv * (half + 14.0), flank_rho), "roll": false}


## Harness-only probes (`--bot=win --hydra-probe=<name>`), used to measure the review findings:
## block_front: 8 m at the boss's left side, shield held (locked, facing the boss)  -> bites "blocked";
##              `dbg_bite_from` logs the shield angle to the bite's origin (a hero facing away would be at 180 - it)
## block_strafe: same, but strafing sideways while the shield is up                  -> still "blocked"
## bite_run:    8 m at the side, during a bite run sideways (no roll)                -> how often a run escapes
## behind:      7 m straight behind the beast, never rolls                           -> bites + forced fire reach him
## edge:        during the inhale stand 3 deg INSIDE the start edge, 6 m out          -> first fire tick >= 0.25 s
func _probe_advice(probe: String) -> Dictionary:
	var p := player.global_position
	var adv := {"move_to": p, "face": global_position, "roll": false, "block": false, "attack": false}
	var side_spot := global_position + global_transform.basis.x.normalized() * 8.0
	side_spot.y = 0.0
	match probe:
		"block_front":
			adv["move_to"] = side_spot if state != &"bite" else p
			adv["block"] = state == &"bite"
		"block_strafe":
			if state == &"bite":
				var to_b := p - global_position
				to_b.y = 0.0
				adv["move_to"] = p + to_b.normalized().cross(Vector3.UP) * 6.0
				adv["block"] = true
			else:
				adv["move_to"] = side_spot
		"bite_run":
			if state == &"bite":
				var to_p := p - global_position
				to_p.y = 0.0
				adv["move_to"] = p + to_p.normalized().cross(Vector3.UP) * 6.0
			else:
				adv["move_to"] = side_spot
		"behind":
			var back := global_position - forward() * 7.0
			back.y = 0.0
			# go round the body (side first), then hold 7 m straight behind
			adv["move_to"] = back if angle_to_pos(p) > 110.0 else global_position + (side_spot - global_position) * 1.2 - forward() * 5.0
		"head_through":
			# qa probe H4: during head_down walk from the snout straight through the resting head toward the body,
			# swinging all the time (the head's collider must stop him; strikes from behind the head must glance)
			if state == &"head_down":
				var hc := visual.socket(&"head_c").global_position
				var hf := hc - global_position
				hf.y = 0.0
				adv["move_to"] = hc - hf.normalized() * 3.0
				adv["attack"] = true
				if fmod(state_time, 0.25) < get_physics_process_delta_time():
					var lp := to_local(p)
					Game.event("probe_head", {"p": Vector3(snappedf(lp.x, 0.01), 0.0, snappedf(lp.z, 0.01)),
						"head_z": snappedf(to_local(hc).z, 0.01), "side_ok": _jaw_side_ok()})
			elif state == &"fire_sweep":
				var fa := _bot_fire_advice()
				adv["move_to"] = fa["move_to"]
				adv["roll"] = fa["roll"]
			else:
				adv["move_to"] = global_position + forward() * 9.0
		"edge":
			if state == &"fire_sweep":
				adv["move_to"] = _polar(_fire_side * (float(T["fire_arc_deg"]) * 0.5 - 3.0), 6.0)
			else:
				adv["move_to"] = global_position + forward() * 7.5
	return adv


func _bot_away_from_feet(p: Vector3) -> Vector3:
	var best := Vector3.ZERO
	var bd := INF
	for f in [&"foot_fl", &"foot_fr"]:
		var q := visual.socket(f).global_position
		q.y = 0.0
		var d := Vector2(p.x - q.x, p.z - q.z).length()
		if d < bd:
			bd = d
			best = q
	var off := p - best
	off.y = 0.0
	if off.length() < 0.1:
		off = forward()
	return best + off.normalized() * (float(T["stomp_radius"]) + 3.0)
