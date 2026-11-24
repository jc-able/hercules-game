class_name Tuning
extends RefCounted
## Every gameplay number of SPEC §2-§4 in one place. Boss modules read their own block; tweak here, nowhere else.

# ------------------------------------------------------------------ player (SPEC §2)
const PLAYER_HEIGHT := 1.9
const PLAYER_RADIUS := 0.38
const PLAYER_HP := 100
const RUN_SPEED := 6.0
const LOCK_SPEED := 4.6
const BLOCK_MOVE_SPEED := 2.2          # walking with the shield raised (not in the spec: decision, see docs/notes/core.md)
const TURN_SPEED_DEG := 720.0          # free-run turn rate toward the stick
const GRAVITY := 22.0

const ROLL_TIME := 0.70
const ROLL_DISTANCE := 4.8
const ROLL_IFRAME_START := 0.08
const ROLL_IFRAME_END := 0.45
const ROLL_RECOVERY := 0.12

const ATTACK_1_TIME := 0.55
const ATTACK_1_ACTIVE := Vector2(0.18, 0.32)
const ATTACK_2_TIME := 0.65
const ATTACK_2_ACTIVE := Vector2(0.22, 0.38)
const ATTACK_CHAIN_FROM := 0.40        # attack_2 starts from here in attack_1 when the press was buffered
const ATTACK_BUFFER := 0.35            # a press this long before the chain point still counts
const ATTACK_LUNGE := 0.7              # metres stepped forward during the active window
const SWORD_DAMAGE := 1
const SWORD_REACH := 2.0               # sword hit box depth in front of the chest (m)
const SWORD_WIDTH := 2.2
const SWORD_HEIGHT := 2.8              # hit box spans y 0.1 .. 0.1 + this (stand-in hero only)
const SWORD_HIT_RADIUS := 0.45          # real hero: capsule radius around the real blade (grip -> tip), swept per frame
const SWORD_TIP_EXTRA := 0.7           # real hero: the capsule reaches this far past the blade tip (forgiving swing arc)

# locomotion clips (real hero; decisions with the owner away, see docs/notes/integrate_player.md)
const LOCK_BACK_SPEED := 2.4           # locked-on backing away: walk_back at 2.0x of its 1.2 m/s, no skating
const LOCK_STRAFE_SPEED := 1.8         # locked-on side-step on the strafe clip (2.5 x its 0.72 m/s, no skating)
const LOCK_STRAFE_TIME := 0.3          # a full-stick side-step lasts this long, then the hero turns into a circling run
const LOCO_ACCEL := 24.0               # m/s^2 toward the wanted ground speed (strafe -> circling run, stops)
const VIS_TURN_DEG := 900.0            # deg/s the body (visual) turns into / out of the circling run
const CIRCLE_TURN_DEG := 85.0          # circling run: the hips turn at most this far from the boss. Under 90, so a change of
									   # direction turns through the back-to-camera side and never shows his front
const CIRCLE_TWIST := 0.55             # share of that turn the spine twists back toward the boss (the camera keeps his back)
const CIRCLE_HEAD := 0.25              # extra share on neck + head (he keeps watching the boss)
const CIRCLE_TWIST_DEG_S := 500.0      # deg/s the twist follows the hips and eases out (a roll, a strike, a stop)
const ANIM_SPEED_MIN := 0.6            # locomotion playback = ground speed / clip move_speed, clamped to this range
const ANIM_SPEED_MAX := 2.5
## Sword carry (core_polish2): in idle / run / strafe / walk_back / the circling run the blade is aimed low, out to his
## right and back (hero space: -X = his right, +Z = front), so it reads beside him from the chase camera instead of a
## stub pointing at the boss. It follows the upper twist, keeps (1 - WEIGHT) of the clip's own wrist swing, and blends
## out for strikes, block, roll, flinch and death (OUT s) and back in afterwards (IN s).
## Hero cross-fades in real seconds (core_polish2 transition strips): between gaits, into idle, and out of an action
## (strike, flinch, roll, block_end) into locomotion; ROLL_BLEND / HIT_BLEND = into those one-shots (kept short).
const GAIT_BLEND := 0.2
const IDLE_BLEND := 0.25
const SETTLE_BLEND := 0.3
const ROLL_BLEND := 0.1
const HIT_BLEND := 0.08
## feedback 2 (owner: "he has his hands like backwards"): the carry now turns the HAND round the grip (grip_fix.gd) and
## points the blade FORWARD and down beside the right leg (was (-0.55, -0.45, -0.70): back and out, which left the
## blade on the little-finger side of an open hand). About 34 deg below horizontal, 25 deg out from straight ahead.
const SWORD_CARRY_DIR := Vector3(-0.36, -0.55, 0.75)
const SWORD_CARRY_WEIGHT := 0.85
## feedback 2 re-fix: at full run speed the carry eases to this weight, so more of the run clip's own arm swing turns
## the blade (at 0.85 it kept pointing the same way, ~4 deg over the cycle). Blended by ground speed / RUN_SPEED.
const SWORD_CARRY_WEIGHT_RUN := 0.6
const SWORD_CARRY_IN := 0.25
## core_polish2 re-fix: 0.08 s flicked the blade on its own (105-112 deg in one frame at a strike start, 64 at a shield
## raise). Strikes: OUT_STRIKE s, but always done by 85 % of the strike's active_start (read from the clip), so the
## swing is the clip's own. Block, roll, flinch, death: OUT s, with the arm.
const SWORD_CARRY_OUT_STRIKE := 0.16
const SWORD_CARRY_OUT := 0.25
## Body (visual) yaw: accelerates and brakes instead of turning at a constant rate (85 deg in 3 frames read as the legs
## spinning under him at every strike out of the circling run). VIS_TURN_DEG stays the top speed in locomotion;
## VIS_TURN_ATTACK_DEG is the top speed into a strike and back out of it (VIS_TURN_ATTACK_AFTER s after it ends).
const VIS_TURN_ACCEL := 9000.0
const VIS_TURN_ATTACK_DEG := 600.0
const VIS_TURN_ATTACK_AFTER := 0.4
## Cross-fade into the first strike from locomotion (real seconds; was 0.06 = a 2-frame pop of the sword arm). The chain
## attack_1 -> attack_2 keeps 0.06. Both end long before the active window, so hits are unchanged.
const ATTACK_BLEND := 0.1
## Locked-on facing (integrate2_hero): Player._face_lock aims at BossBase.strike_point(). A change up to SNAP deg in one
## physics frame follows at once; a bigger jump (the Hydra's jaw goes down beside him, a new lock) turns at JUMP deg/s.
const LOCK_FACE_SNAP_DEG := 12.0
const LOCK_FACE_JUMP_DEG := 540.0
## attack_1's recovery after the chain point (no chain asked for) plays at this speed instead of the strike's ~2.3x; the
## tail finishes standing still after control returns (a move cuts it). Hits and timings unchanged.
const ATTACK_RECOVER_SPEED := 1.3

const SHIELD_ARC_DEG := 120.0
const SHIELD_LOWER_TIME := 0.10
const BLOCK_PUSHBACK := 1.2            # metres slid back when a blow is blocked

const PETRIFY_TIME := 1.5
const PETRIFY_IFRAMES := 1.0
const HIT_FLINCH := 0.4
const HIT_IFRAMES := 0.8
const DEFAULT_KNOCKBACK := 4.0         # metres, decays over the flinch

## Death (QA: the hero stood upright under DEFEATED and only began to kneel as the scene restarted). The clip's
## first 0.25 s is a neutral stance; from there at 1.6x: struck at once, on his knees ~0.9 s, props drop ~1.2 s,
## flat on the floor ~2.2 s. The DEFEATED hold leaves him lying there ~2 s before the fade.
const DEATH_CLIP_FROM := 0.25          # clip time the death clip starts at
const DEATH_CLIP_SPEED := 1.6
const DEFEAT_HOLD := 4.5               # seconds from the killing blow to the restart (ArenaBase)
const DEFEAT_OVERLAY_DELAY := 1.4      # DEFEATED fades in this long after the killing blow (after the fall), upper third
## Victory (core_polish2, final check item 11): LABOR COMPLETE waits for the boss's fall and sits in the upper third.
## It fades in once the boss's top (live_top_points on screen) is below VICTORY_CARD_CLEAR of the screen height, or has
## stopped falling for VICTORY_CARD_STILL s while already below STILL_TOP, never before MIN_DELAY nor after
## CLIP_SHARE x the boss's death clip (capped at MAX_DELAY); the sea follows HOLD s later.
const VICTORY_CARD_MIN_DELAY := 0.6
const VICTORY_CARD_MAX_DELAY := 4.0
const VICTORY_CARD_CLIP_SHARE := 0.8
const VICTORY_CARD_CLEAR := 0.30
const VICTORY_CARD_STILL := 0.4
const VICTORY_CARD_STILL_TOP := 0.18
const VICTORY_CARD_HOLD := 2.8
const CAM_DEATH_RAISE := 0.6           # m the chase camera rises while the hero lies dead (clears low rim curbs)
const CAM_DEATH_EASE := 1.0            # s to ease that in
const CAM_DEATH_AIM := 0.35            # locked: share the aim moves from the framing point onto the fallen hero

const HIT_PAUSE := 0.06               # seconds of near-freeze on a weak-point strike / big impact

# ------------------------------------------------------------------ camera (SPEC §5)
const CAM_FOV := 70.0
const CAM_DISTANCE := 5.0              # free camera arm (exploring, flying off a fight)
const CAM_HEIGHT := 2.4                # (free camera default pitch is set by the player, see PlayerCamera)
# locked on (every fight): right behind the hero, low, tilting up at the boss - the owner's reference keyframes
# (art_src/reference_video/key_*.png); before/after in docs/notes/integrate_player.md
const CAM_LOCK_DISTANCE := 3.7         # arm length behind the hero while locked on
const CAM_LOCK_HEIGHT := 1.3          # camera height above the hero's feet while locked on (chest height)
const CAM_FREE_PITCH_MIN := -55.0
const CAM_FREE_PITCH_MAX := 25.0
const CAM_MOUSE_SENS := 0.18           # degrees per pixel
const CAM_PAD_SPEED := 160.0           # degrees per second at full stick
const CAM_RECENTER_DELAY := 1.0
const CAM_RECENTER_SPEED := 75.0       # deg/s, free mode, while running away from the camera
const LOCK_MAX_DISTANCE := 60.0
# lock framing for towering bosses (SPEC §10: a 14.4 m Hydra, an 8 m Cyclops; decision, see docs/notes/core_followup.md)
const CAM_LOCK_MAX_EXTRA := 1.0        # the arm grows up to this many metres when the boss's top would not fit (past
                                       # that the top is cut: a low camera tilting up beats pulling far back)
const CAM_LOCK_MAX_EXTRA_BY_BOSS := {  # per boss (boss_id); a boss's own cam_max_extra() wins (PlayerCamera.max_extra_for)
	"hydra": 3.0,                      # 14.4 m beast: the rearing centre neck stays in frame down to ~5.5 m (2.5 cut the
	                                   # glowing head by ~1 deg at the close inhale, work/player_fix/sheet_hydra.jpg)
}
## Per-boss lock framing (boss_id): arm `distance`, camera `height`, and `cut_inside` = flat distance (hero -> lock
## point) inside which the arm stops growing, so the boss's top may be cut when the hero stands close. Matches the
## owner's reference size (QA, owner away: hero ~50 % of the frame height, big in the lower centre, boss towering).
## Bosses not listed use CAM_LOCK_DISTANCE / CAM_LOCK_HEIGHT and grow freely (hydra).
const CAM_LOCK_BY_BOSS := {
	"cyclops": {"distance": 2.9, "height": 1.2, "cut_inside": 6.0},
	"medusa": {"distance": 2.9, "height": 1.2, "cut_inside": 6.0},
}
const CAM_LOCK_CUT_RAMP := 1.5         # the allowed growth fades to 0 over this many metres inside cut_inside
const CAM_LOCK_FEET_MARGIN := 0.025   # screen share kept free between the boss bar's top and the hero's feet
const CAM_LOCK_TOP_FRAC := 0.96        # the boss's top (real model bounds) stays below this screen height when it fits
const STICK_DEADZONE := 0.2

# ------------------------------------------------------------------ bosses, common
const ENRAGE_FRACTION := 0.5           # below this share of hp a boss speeds up

# ------------------------------------------------------------------ Cyclops (SPEC §3.1)
const CYCLOPS := {
	"height": 8.0, "hp": 8, "arena_radius": 30.0,
	"walk_speed": 2.6, "turn_deg": 70.0,
	"sweep_windup": 0.6, "sweep_arc_deg": 150.0, "sweep_reach": 10.0, "sweep_dmg": 25,
	"slam_windup": 1.4, "slam_track_until": 0.35, "slam_radius": 3.4, "slam_dmg": 45,
	"stuck_time": 3.0, "stuck_hits": 2, "pull_free_time": 0.8,
	"skip_sweep_chance": 0.25, "enraged_windup_scale": 0.8, "enraged_double_slam_chance": 0.4,
	# cyclops module decisions (docs/notes/cyclops.md request 1; cyclops.gd reads them through _k(), same values)
	"engage_dist": 6.5, "engage_angle": 30.0, "approach_timeout": 5.0, "attack_anyway_dist": 7.0,
	"close_turn_dist": 5.0, "close_turn_deg": 110.0, "stall_time": 2.0,
	# slam windup (cyclops_polish2 re-fix): the slam clip has no step, so the body barely moves while it plays: lunge eased
	# (lunge_accel) and capped (lunge_speed, was 3.2), the shadow circle tracks the hero only within what that lunge can
	# cover, slam_turn_deg caps the windup turn; a slam starts only with the hero within slam_window m of the club's
	# landing distance (the stepping walk closes the rest), or after slam_close_wait s of a hero hugging him
	"lunge_speed": 1.2, "lunge_accel": 6.0, "slam_turn_deg": 40.0, "slam_window": 1.0, "slam_close_wait": 1.0, "slam_brake_speed": 0.6,
	"slam_rebound": 0.35, "step_interval": 0.65, "weak_radius": 0.85, "weak_line_y": 1.9,
	# natural movement (docs/notes/cyclops_polish2.md): he steps whenever he turns or moves; never rotates like a statue
	"walk_move_speed": 2.43,      # FALLBACK only: the manifest's walk move_speed wins (measured planted-foot speed, walk 2026-11-23)
	"step_on_turn_deg": 15.0, "step_on_speed": 0.3,   # above either he plays walk; below both for step_calm s: idle
	"step_calm": 0.25, "turn_step_ref_deg": 120.0,    # in-place turn: walk playback = turn rate / this (70 deg/s -> 0.58x, a heavy pivot; was 60)
	"walk_rate_min": 0.25, "walk_rate_max": 1.3,      # walk playback range (was 0.5: feet ran 1.2 m/s while he started at 0.3)
	"turn_accel_deg": 360.0, "turn_ease": 4.0,        # body yaw: deg/s^2 to speed up / slow down; deg/s per deg of error near the goal
	"walk_accel": 6.0, "walk_decel": 5.0,             # m/s^2 (accel was 4: a 0.65 s start ramp let the feet slide)
	"loco_blend": 0.3, "attack_blend": 0.22,          # cross-fades idle <-> walk, and into / out of every attack (>= 0.2 s)
}

# ------------------------------------------------------------------ Medusa (SPEC §3.2)
## The ONE place for Medusa's numbers (medusa.gd reads only this; medusa_polish2 2026-11-23). Values are as built
## (SPEC §10.1), not SPEC §3.2: she is scaled x1.5, so keep 7-10 m (SPEC 9-14), gaze from 9 m (SPEC 10), tail trigger
## 6.0 m (SPEC 5.5), ring = hit radius 8.0 m from her body centre (SPEC 7.0), ring fill (coil) 1.8 s (SPEC 0.7).
## tail_radius 9.0 -> 8.0 (medusa_polish2): ONE roll started 0.7 s after the ring appears now clears it from beside
## her body 49/50 times (was 22/50); work/medusa_polish2/tail_probe2.gd, numbers in docs/notes/medusa_polish2.md.
const MEDUSA := {
	"height": 6.5, "tail_length": 9.9, "hp": 6, "arena_radius": 28.0,    # tail: SPEC §10 as built (SPEC §3.2 said ~14 m)
	"keep_min": 7.0, "keep_max": 10.0, "turn_deg": 90.0, "slither_speed": 3.2,
	"gaze_windup": 1.2, "gaze_lock_at": 0.5, "gaze_fan_deg": 24.0, "gaze_length": 26.0,
	"gaze_beam_time": 1.0, "gaze_dmg": 30, "gaze_petrify": 1.5, "neck_open_after_fire": 0.8,
	"stun_time": 3.0, "stun_hits": 2,
	# tail swipe rule: hero within tail_trigger_dist of her root for tail_trigger_time -> the ring (radius tail_radius
	# around her body centre) fills in tail_coil (enraged too) -> the sweep. "Roll out of the ring before it fills."
	"tail_trigger_dist": 6.0, "tail_trigger_time": 1.5, "tail_coil": 1.8, "tail_radius": 8.0, "tail_dmg": 20,
	"enraged_second_gaze_delay": 0.6,
	# locomotion animation (natural pass): the slither clip plays whenever she moves OR turns, at
	# max(ground speed, turn rate x slither_turn_radius) / slither reference speed (manifest move_speed, else slither_speed)
	"slither_accel": 6.0,             # m/s^2: she gathers speed / slows down instead of jumping to 3.2 m/s
	"slither_turn_radius": 2.2,       # m: a turn in place at turn_deg (90 deg/s) reads as a ~3.5 m/s slither
	"slither_start_speed": 0.45,      # m/s (effective): idle -> slither
	"slither_stop_speed": 0.2,        # m/s (effective) held for slither_stop_hold s: slither -> idle
	"slither_stop_hold": 0.25,
	"loco_blend": 0.35,               # one-shot -> idle hand-over cross-fade (s, clip clock)
	# integrate2 (new clips 11-23): the new slither tail trails straight back, the idle tail curls round her (tip
	# 4.3-5.6 m apart), so idle <-> slither fades in REAL seconds (medusa.gd scales by the clip rate) over:
	"loco_blend_start": 0.75,         # idle (or a one-shot's end stance) -> slither
	"loco_blend_stop": 0.8,           # slither -> idle
	"action_blend": 0.25,             # cross-fade into gaze / tail_swipe / stun_start / rise (s)
	# polish 3 (review of the natural pass): no backwards glide, eased turns, a soft gaze end and tail-swipe start
	"slither_back_speed": 1.4,        # m/s: backing off from a hero inside keep_min (she still faces him), on an arc
	"retreat_arc_deg": 55.0,          # her retreat target is turned this far to the side of straight away from him
	"slither_back_play": -0.3,        # m/s signed (along her facing) below which the slither plays backwards
	"turn_accel_deg": 360.0,          # deg/s^2: turns gather and lose speed instead of 0 <-> 90 deg/s in one frame
	"turn_ease": 4.0,                 # 1/s: the wanted turn rate is at most |angle left| x this (eases into the facing)
	"lean_out_time": 0.9,             # s: the gaze lunge eases out over this after the neck window (rise uses rise_time)
	"gaze_exit_blend": 0.5,           # s: gaze -> idle / slither cross-fade
	"post_gaze_turn_deg": 45.0,       # deg/s: turn cap for post_gaze_turn_time s after a gaze
	"post_gaze_turn_time": 0.4,
	"gaze_timeout_angle": 60.0,       # deg: the +2.5 s timeout gaze starts only with the hero this close to ahead
	"tail_brake_time": 0.35,          # s: she brakes into the tail swipe over this instead of stopping dead
	# medusa module decisions (not in SPEC; reasons in docs/notes/medusa.md)
	"gaze_neck_hits": 1,              # side-of-the-neck cut during a gaze window
	"gaze_interval": [2.2, 3.6],      # seconds of stalking before a gaze (random in range)
	"gaze_interval_enraged": [1.5, 2.6],
	"gaze_max_angle": 25.0,           # a gaze starts only with the hero this close to straight ahead (or after +2.5 s)
	"gaze_recover": 0.6,              # after the beam (no second gaze)
	"enraged_windup_scale": 0.85,     # "below half they speed up": gaze windup and tail coil x this
	"tail_knockback": 5.0,
	"tail_recover": 0.9,
	"rise_time": 1.2,                 # animfix_medusa: the 2.5 s rise clip reads at 1.2 s (was 0.8, a 0.16 s pop)
	"stalk_area": 12.0,               # her body stays within this radius of the centre (14.9 m tail behind, rim 28 m)
	"gaze_max_dist": 9.0,             # a gaze only starts with the hero this close
	"gaze_chase_limit": 8.0,          # s after the gaze is due: a kiting hero is gazed anyway
	"gaze_hit_followup_gap": 0.6,     # enraged follow-up after a HIT starts this long after the hero's petrify ends
}

# ------------------------------------------------------------------ Hydra (SPEC §3.3)
const HYDRA := {
	"shoulder": 6.5, "head_height": 13.5, "length": 16.0, "hp": 8, "arena_radius": 34.0,   # sizes: SPEC §10 as built
	"turn_deg": 35.0,
	"fire_inhale": 1.5, "fire_arc_deg": 140.0, "fire_reach": 30.0, "fire_time": 2.2,
	"fire_tick": 0.25, "fire_dmg": 12,
	"head_down_time": 2.5, "head_down_hits": 1,
	"stomp_windup": 0.9, "stomp_radius": 5.0, "stomp_dmg": 35,
	"bite_windup": 0.8, "bite_radius": 2.5, "bite_dmg": 25,
	# hydra module decisions (not in SPEC; reasons in docs/notes/hydra.md)
	"guard_time": 1.4, "guard_time_enraged": 1.0,       # wait in guard before the next attack
	"guard_force_fire": 4.5,                            # in guard this long: breathe fire whatever the angle
	"enraged_windup_scale": 0.8,                        # "below half health they speed up"
	"fire_origin_fwd": 2.5,                             # the arc's apex: the neck base, this far in front of the centre
	"fire_stream_half_deg": 12.0,                       # half width of the raking stream inside the arc
	"fire_knockback": 1.5,                              # unused since fire ticks are damage-over-time (no knockback)
	"fire_front_deg": 50.0,                             # breathe fire when the player is within this angle of the snout
	"head_up_time": 0.8,
	"stomp_trigger_dist": 4.5,                          # player this close to a forefoot (guard) -> stomp
	"stomp_knockback": 5.0, "stomp_recover": 0.7,
	"bite_min_dist": 4.5, "bite_max_dist": 12.0,        # side heads reach (from the body centre)
	"bite_min_deg": 25.0, "bite_max_deg": 180.0,        # bites from the sides and behind; the centre head owns the front
	"bite_track_frac": 0.35,                            # the bite circle follows the player for this share of the windup
	"bite_knockback": 3.5, "bite_recover": 0.5,
	"bites_before_fire": 2,
	"fire_lead_time": 0.35,                             # the stream enters the arc from just outside the start edge
	"fire_trail_time": 0.3,                             # the ground keeps burning this long behind the stream
	"forced_fire_clamp_deg": 60.0,                      # a forced fire aims at the hero, clamped to this off the snout
	"jaw_radius": 1.0,                                  # weak point sphere (integrate2: 1.0 again now that Player._face_lock aims at strike_point; see docs/notes/integrate2_hydra.md)
	"jaw_fwd_guess": 6.8,                               # where the jaw lands in head_down (real rig recipe)
	"jaw_ground_height": 1.2,                           # height of the fallback jaw marker when a clip leaves the jaw too high
	"cam_near_dist": 9.0, "cam_near_height": 4.0,       # lock aim drops toward this height when the hero is this close
	"cam_fire_weight": 0.35,                            # lock aim blends this far toward the stream while it rakes
	# natural movement (hydra polish 2, 2026-11-23): the body turns only while the walk clip steps, eased in and out
	"turn_accel_deg": 90.0,                             # deg/s^2: the guard turn speeds up and slows down (no snap to 35 deg/s)
	"guard_urgent_turn_mult": 1.6,                      # after guard_force_fire s: turn (stepping) this much faster to bring the snout round
	"guard_force_fire_late": 2.0,                       # still not facing the hero this long after that: forced fire (steps round, then inhales)
	"turn_spring_k": 6.0,                               # 1/s^2: guard turn = critically damped spring on the yaw error (no dead stop on the target)
	"bite_turn_cap_deg": 15.0,                          # bite tracking: eased body shift, at most this deg/s, stopped by the lock
}

# ------------------------------------------------------------------ dummy boss (core regression test)
const DUMMY := {
	"height": 6.0, "hp": 4, "arena_radius": 26.0,
	"walk_speed": 2.4, "turn_deg": 80.0, "engage_dist": 5.5,
	"sweep_windup": 0.7, "sweep_arc_deg": 140.0, "sweep_reach": 7.5, "sweep_dmg": 15,
	"slam_windup": 1.3, "slam_track_until": 0.35, "slam_radius": 3.4, "slam_dmg": 30,
	"stuck_time": 3.0, "stuck_hits": 2, "recover_time": 0.9,
}

# ------------------------------------------------------------------ world + flight (SPEC §4)
const ISLANDS := {
	"home": Vector3(0, 0, 0),
	"cyclops": Vector3(520, 0, -380),
	"medusa": Vector3(-640, 0, -700),
	"hydra": Vector3(120, 0, -1350),
}
const UNLOCK_ORDER: Array[StringName] = [&"cyclops", &"medusa", &"hydra"]
const ISLAND_TITLES := {
	"home": ["Home Isle", "Where the hero rests"],
	"cyclops": ["The Quarry Isle", "First Labor - the One-Eyed Giant"],
	"medusa": ["The Sanctuary Isle", "Second Labor - the Stone Gaze"],
	"hydra": ["The Volcano Isle", "Third Labor - the Nine Heads"],
	"test": ["Training Ground", "Core test - the Straw Colossus"],
}
const FLY_SPEED := 28.0
const FLY_BOOST := 46.0
const FLY_MIN_HEIGHT := 12.0
const FLY_MAX_HEIGHT := 140.0

# ------------------------------------------------------------------ characters (stand-ins + outline sizing)
# shape: humanoid | serpent | hydra | horse | dummy. Sizes in metres; stand-ins face +Z (Godot), feet on y = 0.
# fall (stand-in death): side (default) | back (bosses: away from the hero and the chase camera) | forward (the hero).
const CHARS := {
	"hercules": {"height": 1.9, "radius": 0.38, "color": Color(0.80, 0.62, 0.45), "accent": Color(0.70, 0.12, 0.10), "shape": "humanoid", "fall": "forward"},
	"cyclops": {"height": 8.0, "radius": 1.7, "color": Color(0.66, 0.53, 0.68), "accent": Color(0.55, 0.14, 0.14), "shape": "humanoid", "four_arms": true, "fall": "back"},
	"medusa": {"height": 6.5, "radius": 1.1, "color": Color(0.36, 0.55, 0.40), "accent": Color(0.75, 0.68, 0.30), "shape": "serpent", "tail": 9.9},
	"hydra": {"height": 6.5, "radius": 2.6, "color": Color(0.16, 0.12, 0.20), "accent": Color(0.65, 0.12, 0.18), "shape": "hydra", "length": 16.0, "head_height": 13.0},
	"pegasus": {"height": 1.9, "radius": 0.7, "color": Color(0.95, 0.95, 0.97), "accent": Color(0.85, 0.75, 0.40), "shape": "horse"},
	"dummy": {"height": 6.0, "radius": 1.2, "color": Color(0.72, 0.62, 0.40), "accent": Color(0.45, 0.30, 0.20), "shape": "humanoid", "fall": "back"},
}


## Returns the CHARS entry for an id (a neutral grey box when unknown).
static func char_info(id: StringName) -> Dictionary:
	return CHARS.get(String(id), {"height": 2.0, "radius": 0.5, "color": Color(0.6, 0.6, 0.6), "accent": Color(0.3, 0.3, 0.3), "shape": "humanoid"})
