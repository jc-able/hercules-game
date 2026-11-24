# Pegasus: natural stance + clip plan (natural-stance agent, 2026-11-23)

Owner at the Mac, no questions asked: every decision below is mine and written down here.

## 1. What reads stiff today (`python3 tools/clip_motion.py pegasus`, strips `work/natural/pegasus/strip_old_*.jpg`)
| clip | moving joints | what reads stiff |
|---|---|---|
| `idle` 7.0 s | 16 of 43 | The whole clip IS the rig rest pose: wings straight up and spread like a statue, all four legs square and frozen (16 leg bones), spine, hips and neck_01 frozen. Only three separate events move (tail flick 0.25-1.9 s, head toss 2.6-4.5 s, wing ruffle 5.2-6.9 s) with dead neutral holds between them. Front view is mirror-symmetric. This is what stands on the home island when the game starts. |
| `glide` 3.0 s | 13 of 43 | Matched V-wing "breathing" is fine, but legs (tucked), neck, head, spine, tail_01/tail_05 and all feathers are frozen: a cardboard cut-out with flapping wings. Symmetric left/right. |
| `fly` 1.04 s | 28 of 43 | The beat itself is good (matched, rider-safe v2). Frozen: spine, neck_03, wing_*_03 and every feather group, so the wing beats as one rigid paddle with no follow-through; the body never answers the beat except the root bob. |

## 2. The natural stance (`art_src/chars/pegasus/natural_pose.json`, local_delta, `ground: lowest`)
A calm winged horse standing ready:
- **Wings half folded against the body, uneven.** wing_l_01 rx -50 / ry +8 / rz +10 (folded further back and in),
  wing_r_01 rx -42 / ry -9 / rz -8 (a little more open). Curl wing_l_02 rx -8, wing_r_02 rx -5 rz -3. Feather lobes
  lifted back: feather_01 rx +15 (L) / +13 rz -3 (R), feather_02 rx +12 (neighbouring feather groups stay within 15
  deg of each other: rig limit ~20). Span 1.80 m (rest 2.29 m), top 2.92 m (rest 2.99 m). The fully folded variant
  (rx -60) pushed the left lobe under the belly between the legs, so I stopped at -50/-42.
- **Head up, neck arched.** neck_01 rx -10 (raises the neck), neck_02 +2, neck_03 +6, head rx +10 (face nearer
  vertical), the neck turned 2+2+2 deg and the head 5 deg to its left, head tilt ry -2. Within the rig notes
  (neck_01 <= 25, neck_02 <= 15).
- **Left hind leg resting** on the toe: leg_bl_01 rx -6 ry 2, leg_bl_02 -16, leg_bl_03 -12, hoof_bl +26 (hock and
  fetlock flexed, toe down). Root roll ry +0.5 drops the resting side; root pitch rx -1.3 puts the standing hind hoof
  on the floor. Fore legs: leg_fl_01 +2, leg_fr_01 -3 / leg_fr_02 +1 (the right fore a touch ahead), leg_br_01 +1.
- **Spine** relaxed: spine_01 +1, spine_02 +1 rz -1, spine_03 -1.5.
- **Tail** hangs closer to the hocks with a soft S curve and a lean to its right: tail_01..05 rx -10/-4/0/+4/+6,
  ry -3/-3/-2/+1/+2 (tail_01 well within the 45-deg rule).
- **Ground (`ak solve` + per-hoof lowest vertex):** fl 0.009 m, fr 0.011 m, bl (resting toe) 0.019 m, br 0.000 m:
  every hoof within 0.02 m. No mesh through mesh at the wing roots or the flank (close-up `work/natural/pegasus/c4z.jpg`).
  No props on Pegasus (breastplate and bridle are mesh and stay readable).
- Renders: `work/natural/pegasus/r_nat_v4_{front,side,q3}.png`; iterations v1-v4 in the same folder.

## 3. The new sheet
`art_src/chars/pegasus/sheet_nat_std.png` + `cam_nat_std.json`: 1280x720, FRONT | SIDE (faces right), 175.34 px/m in
both panels, `--env 1.75,1.9,1.9,3.4` (room for a wing lift to ~3.4 m span, tail swish, head toss), front panel 614 px,
side 666 px. Checked: both panels the same pose, nothing cut off, divider only at the top rows.
- **Background green, not white** (decision): every Pegasus sheet and reference video uses `--bg 0.35,0.72,0.47`
  (displayed 160,221,182, written into the cam json as `bg_srgb8`) because the white horse cannot be separated from a
  white sheet. Remember the pegasus animators' green-key ak wrapper (`work/anim/pegasus_idle/akg.py`): plain `tools/ak`
  counts this green as character.
- How it was rendered: `work/natural/pegasus/nat_render.py` (imports animkit's own Rig, opens pegasus.blend read-only,
  applies natural_pose.json, saves `work/natural/pegasus/pegasus_nat.blend` with ABSOLUTE texture paths and the pose in
  the pose bones, no action), then `tools/blender/render_split_sheet.py --in <that copy> --out sheet_nat_std.png --cam
  cam_nat_std.json --bg 0.35,0.72,0.47 --env 1.75,1.9,1.9,3.4`. The copy is only for the sheet: never bake into it.
- **No `sheet_nat_wide`**: no V clip needs more room (fly and glide are R, see below).

## 4. Plan for every clip (game/assets/characters/pegasus/pegasus_clips.json: fly, glide, idle)
| clip | action | what to do |
|---|---|---|
| `idle` | **V** -> `idle_n` from `nat_std` | New 10 s reference from the natural stance; key ALL groups (breathing in chest, weight shift between the hind legs, head/neck looks with phase lag neck_01 -> head, wing shrugs left and right at different times, tail sway + one flick). Loop window ~7-8 s chosen on the video (the weight shift should go out and back inside it). Length may change from 7.0 s (no events, nothing times on it). |
| `glide` | **R** | Keep the matched V-wing breathing (wing_*_01/02) and the tucked legs as keyed. Add quiet life to the frozen groups: head + neck slow look/nod 2-4 deg with neck_01->head lag, leg tuck drifting 3-5 deg with the hind pair out of phase with the fore pair and left vs right offset, spine 1-2 deg answering the wing breathing, the whole tail chain waving (tail_01 too) streaming back, wing_*_03 and feathers trailing the wing breath by ~0.2 s (<= 10 deg, neighbours within 15). Left and right never equal. Root stays 0 (glide/fly crossfade contract). Length 3.0 s, loop unchanged. Re-run `ridden/pair_check.py` (0 rider hits today). |
| `fly` | **R** | The wing beat stays exactly as keyed (rider-safe v2 with the 25-deg forward sweep). Add follow-through: wing_*_03 and feather_01..03 lag the beat by 2-3 frames (curl up on the downstroke, trail on the upstroke, <= 15-20 deg, neighbours within 15), spine_02/03 1-2 deg answering each beat, neck_03/head a small counter-nod (neck_03 is frozen now), slightly different amplitudes left vs right. No root pitch, root bob unchanged (fly_bob contract). Length 1.0417 s, loop, beat phase (t 0 = wing top) unchanged. Re-run pair_check: the feather lag must not bring the lobe back into the rider's legs. |

Total: **1 V** (`idle_n`). The fly and glide motions are right; only their frozen groups are wrong, and a new flight video
would have to re-solve the rider clearance from scratch.

### idle_n Seedance motion text (what follows "Motion:"; the lead adds the fixed split-screen header)
> The winged horse stands calmly on the spot and keeps its design. Its chest rises and falls in one slow breath every
> 3.5 seconds. Its left hind leg rests on the hoof tip; at 4 seconds it shifts its weight and rests the right hind leg
> instead, and at 8 seconds it shifts back. The forelegs stay planted. The arched neck slowly turns the head to the
> left, then to the right. The half-folded wings settle with small shrugs: the left wing twitches at 2 seconds, the
> right wing lifts slightly and refolds at 6 seconds. The tail sways gently and flicks once at 3 seconds.

(106 words.) Note for the lead's header: the old pegasus header says "Plain green background"; keep it, the sheet is green.

## 5. Risk for the lead (not my files)
- **Mount: folded wings vs the rider's legs.** The natural stance folds the wings along the flanks where a seated
  rider's thighs hang (the old idle had the wings straight up: 0 hits). `home_base.gd` plays Pegasus `idle` during the
  0.55 s hop and only starts `fly` (0.3 s blend) when the rider is seated (line ~188). With the new idle the rider will
  land in the folded wings for ~0.3 s. Suggest: start `pegasus.play(&"fly", 0.3)` at the hop start (around line 132),
  or have the idle_n animator run `ridden/pair_check.py` and the game hold the wings up during the hop. Same check for
  any dismount that plays `idle` with the rider still on.
