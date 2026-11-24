# Hydra animation fixer notes (2026-11-22)

Role: the only writer of `art_src/chars/hydra/` (blend + clips) and `game/assets/characters/hydra/` for this pass.
Scratch + every generator/script: `work/animfix_hydra/` (backup of the clips, GLB and manifest before the pass:
`work/animfix_hydra/backup/`).

## Result
- GLB: 17 clips (was 9), 10.39 MB, export fps 30, 76 joints, 66,440 tris. Manifest rebuilt by `ak export` +
  `work/assemble_hydra/finish_manifest.py` (sockets, offsets, weak_points, size).
- `ak merge` of all 17 action JSONs (re-baked on rig hash e682e3c4dce2), Godot import under `work/.import_lock`.
- `work/assemble_hydra/probe.gd`: 0 failures. `work/animfix_hydra/probe_fix.gd` (new clips): 0 failures.

| clip | length | events | what changed |
|---|---|---|---|
| idle | 3.0 loop | - | necks 7/8 sway raised (amplitude 1.3, new phases): head_7 0.25 m, head_8 0.16 m (were 0.09 / 0.09) |
| walk | 2.1667 loop | - | unchanged (unused by the fight) |
| fire_sweep | 4.6 | fire_start 1.5, fire_end 4.05 | retimed so fire_start = the module's 1.5 s inhale (speed 1.0); head crosses x -4.0 (1.7 s) -> 0 (2.85) -> +4.0 (3.95) over the 2.2 s rake; jaw 16-17 deg (was at the 20 limit); centred chin rest; forefeet by leg IK (slide 0.24 m -> 2.7 cm) |
| fire_sweep_l | 4.6 | same | mirror: head +X -> -X, ends on the same chin rest |
| fire_sweep_return(_l) | 2.7667 | fire_start 0, fire_end 2.2 | NEW enraged return pass, starts on fire_sweep's end-of-pass key (3.95 s), ends on the chin rest |
| head_down | 1.5 loop | - | chin rest centred: jaw_c socket x 0.00 (was -0.78), 0.51-0.72 m high, 6.97 m ahead; forefeet by IK |
| head_up | 1.5 | - | starts on the centred chin rest; forefeet by IK (slide 0.16 m -> 2 cm) |
| stomp | 3.0 | impact 1.75 | unchanged (lifts foot_fl) |
| stomp_r | 3.0 | impact 1.75 | NEW mirror: lifts foot_fr 1.63 m, foot_fl stays <= 0.08 m |
| bite | 3.5 | impact 1.5 | centre head as before; side-neck pairs no longer mirror twins (left scale 0.68-1.05 + per-neck noise: pair diff up to 1.0-1.6 m, was <= 0.1 m) |
| bite_r | 3.5 | impact 1.5 | NEW authored side-head bite, neck_3 (creature's right, -X): head_3 socket at impact (-5.35, 2.99, 1.43) Godot = snout ~2 m high, ~5.5 m out |
| bite_l | 3.5 | impact 1.5 | NEW mirror of bite_r, neck_6: head_6 at (5.35, 2.99, 1.43) |
| hurt | 0.9 | - | NOW FROM head_down: starts/ends exactly on the chin rest (gap 0.000 m); flinch lifts the jaw to 2.4 m at 0.07-0.1 s, back on the floor (0.51 m) by 0.3 s |
| hurt_standing | 1.6333 | - | the old standing hurt, kept |
| death | 3.8 | - | NOW FROM head_down: spasm (jaw to 3.6 m), side necks thrash with the traced k1/k1b/k2/k2b angles, last heave, traced collapse k4..k8 with the centre neck kept low; floor contact -1.1/+1.6 cm on every frame; no body bounce in the belly drop |
| death_standing | 5.5 | - | the old standing death, kept |

## Decisions taken with the owner away
- `hurt` and `death` keep their names and now start from head_down (no module change needed); the standing versions
  stay in the GLB as `hurt_standing` / `death_standing` for any future use.
- head_down jaw height: accepted at 0.51-0.72 m (the requirement says ~1.2 m). The head lies on the floor (SPEC) and the
  jaw is inside the sword box; raising it would make the head hover. The chin rest is now centred (x 0) as asked.
- bite_r reach: the rig's neck_3 (5.3 m + 1.5 m head, base 6.8 m high) cannot put the snout 6-8 m out AND 1.5-2.5 m
  high: the best low strike puts the snout ~2 m high, ~5.5 m out (head_3 socket 3.0 m high). Kept the joint bends to
  about 25-30 deg per link (rig comfort ~25) except the neck root (~60 deg).
- bite_r has no body roll/yaw: a roll or a spine yaw slides or lifts the forefeet (the straight forelegs cannot follow).
  The strike leans in with a small spine bow (3/3/8 deg) with front-leg IK instead.
- Fire clips are baked at 30 fps (the GLB rate) so fire_start stays exactly 1.5 s (a 24 fps bake was retimed by export
  to 1.5055).
- fire_sweep rear-up reduced (spine_03 +1.5/+2 instead of +3/+4): the straight forelegs cannot follow a bigger rear, the
  forefeet lifted 7 cm.

## Requests for the hydra module (hydra.gd)
A1. Fire direction: play `fire_sweep_l` when `_fire_side == +1` (the head then starts on +X with the stream), keep
    `fire_sweep` for -1. Both have fire_start 1.5 / fire_end 4.05 and end on the same head_down chin rest.
A2. Fire speed: with fire_start = 1.5 the existing `speed = fire_start / inhale` is 1.0 (0.8x inhale enraged -> 1.25x).
    The clip's rake (fire_start + 0.2 -> fire_end) is 2.55 s = lead 0.35 + one 2.2 s pass, so core C1 is not needed.
A3. Enraged return pass: when the first pass ends (fire_end of fire_sweep / fire_sweep_l), play `fire_sweep_return`
    (after fire_sweep) or `fire_sweep_return_l` (after fire_sweep_l) with a short blend (0.1 s); its fire_start 0 /
    fire_end 2.2 match one 2.2 s pass; it ends on the chin rest at 2.77 s, then head_down.
A4. Stomp: play `stomp_r` when `_stomp_foot == foot_fr` (it lifts foot_fr, impact 1.75); `stomp` for foot_fl.
A5. Bite: pick `bite_r` (hero on the creature's right, -X) / `bite_l` (+X) and use `head_3` / `head_6` as the biting
    head (glow, bite origin): those are the heads that strike. Keep `bite` for a hero near the front. Bite only out to
    ~120 deg off the snout (a head cannot reach a hero directly behind); the snout lands ~5.5 m from the body centre.
A6. H1 (false jaw_fallback) should be gone: hurt keeps the jaw at <= 2.4 m and back at 0.51 m by 0.3 s.
A7. H5 (hurt from head_down) is fixed in the clip itself; no `hurt_clip = &""` needed.

## Files
- fire family: `art_src/chars/hydra/clips/fire_sweep/` keys_fire_sweep(.json/_l/_return/_return_l), poses_* (generator
  `work/animfix_hydra/fs/gen.py` = the animator's gen.py + centring, jaw, leg IK; `deploy.py` + `ikfix.py` rebuild all).
- hurt: `clips/hurt/keys_hurt.json` + `poses_hurt_down/` (`work/animfix_hydra/fs/gen_hurt.py`), keys_hurt_standing.json.
- death: `clips/death/keys_death.json` + `poses_death_down/` (`work/animfix_hydra/fs/death_pipeline.py`: gen_death.py,
  legblend.py, fixground.py), keys_death_standing.json.
- bite: `clips/bite/keys_bite_r.json` + `poses_bite_r/` (`work/animfix_hydra/bite/gen_bite_r.py`), keys_bite_l.json
  (mirror), `poses_bite/params_fix.json` + `poses_bite/noise.py` for the bite asymmetry.
- stomp: `clips/stomp/keys_stomp_r.json` (mirror). idle: `clips/idle/poses_idle/gen_fix.py` + `params_fix.json`.
- Tools: `work/animfix_hydra/sample.py` + `smp.py` (socket/floor sampler, read-only on the blend), `readback.py`
  (read-back keys, optional front-leg IK), `probe_fix.gd`.
