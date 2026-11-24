# Hydra assembly notes (assembler, 2026-11-22)

Files written: `art_src/chars/hydra/hydra.blend` (9 actions merged), `game/assets/characters/hydra/hydra.glb`,
`game/assets/characters/hydra/hydra_clips.json` (+ Godot's `.import` files and the extracted `hydra_hydra_albedo.png`).
Scratch: `work/assemble_hydra/` (`probe.gd`, `probe_chain.gd`, `probe_fight.gd`, `finish_manifest.py`, logs, shots).

## Result
- Clips: all 9 in SPEC §8 (idle, walk, fire_sweep, head_down, head_up, stomp, bite, hurt, death). None missing.
- `ak merge` (1 call, 9 action JSONs, re-baked on rig hash e682e3c4dce2), `ak export`: 1 skin (76 joints), 1 mesh, 66,440 tris,
  albedo PNG embedded (5.5 MB), material doubleSided, export fps 30 (hurt was keyed at 30, the rest at 24), GLB 9.54 MB.
  Every GLB clip length equals the manifest length.
- Manifest: clips (length, loop, events from the keys files), sockets + socket_offsets from rig.json, `offset_space: blender`,
  `weak_points` {jaw: jaw_c}, `size` (height 14.381, shoulder 6.5, length 16.008, width 10.139, Blender and Godot bounds).
  Re-run `python3 work/assemble_hydra/finish_manifest.py` after any new `ak export` (export rewrites the manifest without size).
- Godot import done under the lock. `probe.gd` through `CharacterVisual.create("hydra")`: 0 failures (has_clip,
  clip_length, loop flags, event_time, 12 sockets on their bones, faces +Z, rest bounds = rig.json).
- Measured in Godot:
  - head_down jaw_c socket 0.53-0.74 m high, 6.93 m ahead, x -0.78 (the bone sits at 1.13 m; the socket is the underside on the floor).
    The sword box (y 0.1-2.9) reaches it.
  - The chain fire_sweep end -> head_down -> head_up start lines up within 0.011 / 0.037 m.
  - stomp lifts foot_fl (the creature's left, +X) 1.63 m; foot_fr stays planted (socket y <= 0.07); impact 1.75 s.
  - bite: the CENTRE head strikes, jaw 1.20 m high, 5.1 m straight ahead (x 0).
- `--start=hydra --bot=win` with the installed GLB: victory, 8/8 jaw hits, no SCRIPT ERROR. But `jaw_fallback` fires on most
  openings. That is a false alarm, see request H1.

## Decisions taken with the owner away
- No `bite_l` / `bite_r`: the bite clip uses the centre head (the animator found that the side necks cannot reach the floor).
  The requirement asks for a mirror only when the bite uses a head on the right. A mirror of a centre-head bite would be the
  same strike, so I did not make one.
- jaw_c socket left at rig.json's offset (0.53-0.74 m in head_down instead of ~1.2 m). It is reachable and it is the soft
  underside. Changing the rig's offset would also move the weak point in every other clip.
- No retiming of the animators' clips (fire timing, see H2): the game is meant to stretch the clips (SPEC §8).

## Requests for the hydra module (hydra.gd)
H1. False `jaw_fallback`. The bot strikes the jaw 0.2-0.3 s into head_down, before `_check_jaw_reachable` has finished deciding.
    BossBase then plays `hurt`, which lifts the head to ~12 m. At 0.3 s the check reads 9-11 m and moves the weak point
    to the ground marker (seen in `work/assemble_hydra/probe_fight.gd`). Fix: set `_jaw_checked = true` once the jaw
    has been struck or closed, or once its y has been at or below the limit at any moment.
H2. Fire timing. `fire_sweep` plays at fire_start/inhale = 3.3/1.5 = 2.2x for the whole clip. The clip's sweep
    (fire_start 3.3 -> fire_end 4.3) then lasts only 0.45 s, and the head lies on the floor for the last ~1.8 s while the stream
    still rakes (seen in-game). Fix: at fire start, change the playback speed so (fire_end - fire_start) lasts
    lead + fire_time * legs. This needs core request C1.
H3. Sweep direction. The clip always sweeps from the creature's RIGHT (-X, head at x -4.8 at fire_start) to its LEFT
    (x +4.0 at fire_end). `_fire_side` +1 (the hero on the creature's left, +X) starts the stream on +X, so the stream and
    the head go opposite ways. Side -1 matches the clip
    (the in-game shot `docs/devlog/media_inbox/assemble_hydra/hydra_ingame_fire_sweep.jpg` shows the head on one side and the
    stream on the other). There are two options. (a) Start the first pass on the creature's right always. (b) Ask the assembler for
    mirrored `fire_sweep_l` + `head_down_l` + `head_up_l` (`ak mirror --keys`, the jaw then rests at x +0.8).
    Enraged there-and-back has no clip for the return; the head can hold at the chin rest.
H4. Bite heads. The clip lunges the centre head straight ahead (5.1 m). The module bites the hero at the side (25-180 deg off
    the snout) with `head_1..8` chosen by side, so the visible strike and the damage circle are in different places.
    Options: turn the body toward the target during the windup (35 deg/s is too slow for 180 deg), bite only within
    ~40 deg of the snout, or keep the glow and pillar as the read. A real side-head bite needs a longer side neck (rig track).
H5. Hurt during head_down. `hurt` starts from the standing pose, so a jaw hit whips the head from the floor to 12 m in the 0.15 s
    blend. Suggestion: `hurt_clip = &""` while in head_down (head_up follows 0.6 s later anyway), or play `head_up` at once.

## Requests for core (CharacterVisual)
C1. A playback-speed setter (`set_speed(s)`, which sets the AnimationPlayer's speed for the current clip without restarting it)
    for H2.
C2. `_apply_toon` ignores the GLB's `doubleSided` (toon.gdshader is `cull_back`). rig.json asks for double-sided because
    the necks were split along fused seams. Suggestion: when the source BaseMaterial3D has `cull_mode == CULL_DISABLED`, use a
    `cull_disabled` toon variant. I saw no hole in my shots, but a neck that leaves its neighbour can show a seam.

## For the art / rig track
- When the creature bows (fire lunge, head_down), a grey, untextured-looking patch shows on top of the centre-neck base
  (in-game shot). It is probably the cap where the 10th tube was deleted. It needs paint or a UV fix in the albedo.
- Side necks cannot reach the floor (bite note). A side-head bite needs longer side necks.
