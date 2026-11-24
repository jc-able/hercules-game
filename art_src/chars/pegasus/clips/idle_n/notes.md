# pegasus / idle (video "idle_n", from the natural stance) — idle_n animator, 2026-11-23

| clip | window | keys | IoU per matched key (front/side) | length | events |
|---|---|---|---|---|---|
| idle | ref.mp4 1.0-7.0 s (clip t = video t - 1.0) | 24 keys every 0.25 s + loop seam copy (poses_idle/k00..k23.json) | k04 (video 2.0, left-wing twitch) 0.83/0.90, k08 (3.0, tail flick) 0.86/0.88, k12 (4.0, weight shift) 0.88/0.88, k16 (5.0) 0.83/0.80, k20 (6.0, wing spread) 0.79/0.82, k22 (6.5) 0.61/0.80; rest pose on the same frames 0.44-0.58; strip (8 frames) mean 0.85, seam frame 0.92/0.96 | 6.0 s loop, 24 fps (old idle: 7.0 s) | none (the old clip had none either) |

## How it is built
- Every key = `art_src/chars/pegasus/natural_pose.json` (local_delta) + smooth deltas from `work/anim2/pegasus_idle_n/gen.py`
  with `params.json`. Bones the deltas do not touch keep their natural-stance angles; k00 is the natural stance EXACTLY (0.0 deg
  difference on every bone and the root): every periodic term is shifted to be 0 at t = 0 and t = 6.0, every event is a bump that
  starts and ends inside the loop. To change the idle, edit params.json and run `python3 gen.py`, then bake.
- Motion (clip time): two breaths (3 s each: spine_01/02/03 chest rise, neck answers, wing roots shrug, right wing 0.12 s late);
  head looks left (peak 1.5 s) then right (4.5 s), lag 0.15 s per link neck_01 -> neck_02 -> neck_03 -> head (head 18 deg yaw
  range, tilt with the turn), neck nods on a 3 s and head nods on a 2 s period; left wing twitch out at 1.0 s (video 2.0) with
  wing_02/03 and feather lag; tail sway (3 s period, phase lag down the chain) + one flick back at 2.05 s (video 3.0, tail_01 +32
  deg, tail lift stays < 60 deg); weight shift from the left hind resting (natural) to the right hind resting at 2.4-3.2 s (video
  ~3.6-4.2, prompt "at 4 s"), hips/spine yaw and root roll follow it, and back at 4.4-5.2 s; both wings flare out at 5.0 s (video
  6.0; wing_r_01 rz +16 / rx -8, wing_l_01 rz -11 and wing_l_02 rx +12 0.12-0.18 s later, read off an `ak fit` of video 6.0) and
  refold by 5.9 s; feather groups flutter 1.5-2.5 deg, left and right out of phase.
- Moving bones (max turn from the first key, keyed samples): 32 of 43. Not moving: root, saddle (non-deforming), the eight
  front-leg bones (planted on purpose: the video keeps the forelegs planted; leg_fl_01/fr_01 turn 0.8 deg with the shift), hips
  3.0 deg (borderline). Old idle: 16 of 43. Ground: lowest vertex 0.000 on every key; the resting hind toe stays <= 0.014 m.

## What does not match and why
- Compressed ending: the video spreads the wings at 6.0-7.0 s and shifts the weight back only at 8 s. A 3-6 s loop that starts
  and ends in the natural stance cannot hold that, so the shift back (4.4-5.2) and the wing refold (5.5-5.9) are authored earlier
  than the video. Key k22 (video 6.5, wings still wide in the video) therefore scores only 0.61 front.
- Seedance zooms in slowly (the horse is visibly larger in the side panel at video 4-6 s); calibration uses frame 0, so side IoU of
  the middle keys drops to ~0.80 from framing alone (the 6.0 s fit recovered 0.81/0.90 with view_offset [0.02, -0.06, -0.01]).
- Mane and tail hair are drawn as a broad mass in the video; our 5-bone tail follows its centre line.
- Tool: plain `tools/ak` counts the green background as character; all scoring went through the green-key wrapper
  `work/anim2/pegasus_idle_n/akg.py` (a copy of `work/anim/pegasus_idle/akg.py`).
- Check video: `work/anim2/pegasus_idle_n/strip_idle.mp4`.

## Rider check (for the lead: game code, not this clip)
`ridden/pair_check.py` (seated Hercules `ride` at speed 1.0 + this idle, run on a scratch copy of ride.blend with symlinked
texture folders): wing triangles hit the rider on 36 of 36 frames, 1000-1600 pairs (thighs, shins, skirt, right hand, sword),
INCLUDING k00, which is the natural stance itself. The folded wings of the natural stance lie where a seated rider's legs hang
(predicted in docs/notes/natural_pegasus.md section 5); the old rest-pose idle had wings straight up and 0 hits. This cannot be fixed
inside an idle that must start and end in the natural stance. Decision: keep the idle as briefed; the game must not show this
idle with a rider seated: start `fly` at the hop start in home_base.gd (around line 132) instead of when the rider is seated, and
the same for any dismount. Result file: work/anim2/pegasus_idle_n/pair_check.json.

## idle v2 (animation fixer, 2026-11-23, after the natural review: sliding hind hooves, floating forehooves)
idle v2 | video window 1.0-9.0 s (clip t = video t - 1.0) | 67 keys + seam: every 0.25 s, every frame inside the four steps | **8.0 s loop (was 6.0)**, 24 fps | events: none
- Built by `work/anim2/pegasus_fix/gen2_bl.py` + `params2.json` (headless Blender, blend read-only). The life layer is the
  v1 one (gen.py terms: breathing, look, nods, tail sway + flick, wing twitch, feathers), now on an 8 s loop; the right-wing
  lift is centred at 5.5 s, half-width 0.75 s (video 6.0-7.0 holds the spread). The LEGS are solved by IK every key: each
  hoof has a world target (fetlock head + hoof world orientation, absolute bone space corrected for root.rot); planted hooves
  keep their spot exactly, root z is fixed (no root.ground), all four hooves sit at lowest z 0.000 (+-0.0002).
- Weight shift = four staged steps (matches the prompt: shift at video 4 s, back at 8 s): 2.45-2.85 left hind lifts (toe
  clearance 6.9 cm, fetlock +9.8 cm, hoof curls 14 deg) and plants under the hip; 2.85-3.25 right hind lifts 5.7 cm and is set
  down in the resting spot, toe down; 6.85-7.25 right hind back under the hip (6.8 cm); 7.25-7.65 left hind back to rest
  (5.7 cm). Root roll (+0.5 -> -0.5 deg) and hip yaw (3 deg) lead each pair by 0.1 s (2.35-3.15, 6.75-7.55).
- Resting spot moved from 0.48 m to 0.20 m ahead of the standing hoof (and 4 cm inward): `natural_pose.json` updated (= k00;
  old one kept as `natural_pose.v1.json`, which gen2 reads as its base). The resting hoof keeps its tipped-toe orientation.
- Measured (`work/anim2/pegasus_fix/pk.py` + `slide.py`, every half frame): planted fetlock heads move <= 0.65 cm in xz
  (forehooves 0.00 cm, z 0.263 / 0.254 constant) while the other hoof is in the air; v1 slid 36-39 cm at up to 0.98 m/s and
  floated the forehooves 2.8 cm. Moving bones 32 -> 39 of 43 (still: root, saddle, hips 3.0 deg, leg_fl_03 2.8 deg = planted).
- Strip (8 frames, akg): mean 0.829 (front 0.93 at the seam; 0.60 at 5.7 s while the video's wings are still spread).
- Old v1: keys_idle.v1.json, action_idle.v1.json, poses_idle_v1/, strip_idle.v1.jpg (clip name idle: never merge them).
