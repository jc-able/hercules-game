# Cyclops animation fix pass (anim fixer, 2026-11-22; owner away, decisions noted)

Fixed the findings of docs/notes/anim_review_cyclops.md. Only writer of art_src/chars/cyclops/ and
game/assets/characters/cyclops/ for this pass. Backups of the previous clips, blend, GLB and manifest:
work/anim_fix_cyclops/backup/.

## What changed (per clip details in art_src/chars/cyclops/clips/<video>/notes.md "Fix pass")
| clip | before | after |
|---|---|---|
| hurt | 2.25 s upright hurt from the rest pose (5.0 m joint jump from stuck) | 0.667 s flinch from and back to slam/poses_stuck/k00_stuck.json; club head moves <= 0.03 m |
| stuck | club head 2.8 m left, lowest vertex +0.36-0.40 m, forearm 2.50-2.61 m, left hand 0.7 m off the club | club head (0.20, -5.32, 0.19) (Blender, -Y forward), lowest vertex -0.66 m, forearm_u_r mid 2.15-2.24 m, left hand on club_grip2 |
| slam | impact pose = old stuck | k07_impact on the new buried point; +1 grounded in-between |
| pull_free | 1.75 s, 1-frame left-hand snap, club dips 0.3 m under the floor | 1.5 s (game stretch x1.875), starts from the new stuck, club above the floor after 0.375 s, roar head key |
| sweep | club at 3.7-4.5 m over the hero at impact, club through the neck / face | low backhand: club lowest vertex 0.25-0.82 m from 1.208-1.375 s, impact 1.31 unchanged; club clear of the body after 1.5 s |
| death | falls FORWARD onto the hero (head ends 4.9 m in front) | falls BACKWARD: head ends 5.7 m behind, feet 1.2 m in front; root motion kept |
| walk | 3.917 s at video speed (feet skate at 2.6 m/s), no step event | 1.4167 s cycle, step 0.40; play at speed 1 |
| idle | unchanged | unchanged |

GLB: game/assets/characters/cyclops/cyclops.glb (9.1 MB, 8 clips, 24 fps, 1 skin), manifest re-run through
work/assemble_cyclops/finish_manifest.py (sockets incl. club_grip2, offset_space godot, size, death root_motion).
Merge: one `ak merge` per file (assembler's workaround). Import under work/.import_lock. Probe
work/assemble_cyclops/probe.gd: errors=0 (log work/anim_fix_cyclops/probe.log, shots work/anim_fix_cyclops/probe_shots/).
Fight check `--start=cyclops --harness --bot=win --seed=1 --speed=3`: victory, 2 forearm hits in each of the 4 stuck
windows, fight_start 2.42 s -> victory 32.49 s (was 62 s with 1 hit per window), 0 ERROR / WARNING lines.

## Decisions taken with the owner away
- stuck / slam impact / pull_free start deviate from the reference video on purpose (club on his centre line, deeper
  crouch): stuck IoU drops to 0.53/0.49. The game requirement wins over the video.
- Club head "buried": half the head in the earth (centre +0.19 m, lowest vertex -0.66 m, tip -0.05 m) so it still reads
  as a club in a crack from the chase camera. The club tip (club.global_transform * (0, 5.05, 0)) is 6.1 m ahead.
- hurt re-authored without a reference (the old ref.mp4 is a standing hurt, wrong context).
- death 2.6-4.5 re-authored as a backward fall (the video falls forward). Tuning cyclops fall "back" is now true.
- walk: two video holds dropped after the retime (a frozen stance foot slides at a constant root speed).

## Requests for the cyclops module (game/scripts/bosses/cyclops.gd)
- Keep `hurt` as is: do NOT blank hurt_clip any more (the reviewer's fallback is no longer needed). It is 0.667 s,
  so the resume timer is ~0.6 s instead of 2.0 s.
- walk: play at speed 1 (it already does); `_step_beat()` = 0.708 s now, first thud from the `step` event (0.40 s).
- pull_free is 1.5 s now: the 0.8 s stretch is x1.875 (was x2.19).
- Crack / chunks: the real club tip lands 6.1 m ahead of the boss on his centre line (x ~ +0.2 m): put the crack at
  club.global_transform * (0, 5.05, 0) as the assembler asked; the slam reach/lunge logic can use 6.0 m.
- death: falls backward, root motion (hips end 0.4 m behind their start, head ~5.7 m behind): play it without moving the body.

## Still open (not done here)
- idle frame 0 (poses_idle/k0_low) differs from the rest pose the one-shots start on (up to 0.585 m): hidden by the
  module's 0.12-0.25 s blends; hurt no longer starts from rest, so the 0.08 s blend case is gone.
- Small club/hand overlaps near the grip (<= 0.17 m, the left hand wraps the handle in stuck; pull_free 0.875 s one
  frame the handle crosses the left forearm).
- Death fall: hips bob 0.3 m between 3.29 and 3.42 s (grounded in-betweens of a fast fall), reads as the impact bounce.
- animkit: cmd_merge already calls clear_anim before bake_data and apply_grounded updates the depsgraph (the frame-0
  bug the assembler reported looks fixed in the tool); per-file merges were used anyway.

Scratch tools (not in git): work/anim_fix_cyclops/kit.py (pose IK/least-squares on top of animkit's Rig: club head,
grip, palm-on-grip2, clearance, floor), look.py (check renders), jobs/*.json.
