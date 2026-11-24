# Core review (independent reviewer, 2026-11-22)

Logs: `work/core_review/logs/`, frames: `work/core_review/shots/`. All brief done-checks pass (win, lose+restart, --pad,
title, --probe=ui) with 0 SCRIPT ERROR / Parse Error / leak lines. 40 death->restart cycles: object count flat (1974),
0 orphans. A throw-away medusa-like arena + boss written only from SPEC §7.1 + notes/core.md won with --bot=win
(reflect -> stun -> neck hits). Throw-away files deleted.

## Requests to core, most important first
1. BLOCKER for world: bot.gd only follows a fighting `boss.bot_advice()`; home/sea have no boss and the sea has no Player,
   so `--start=home --bot=win` (world done check) cannot move. Fallback: when no fighting boss, call
   `Game.world.bot_advice()` (or nodes in group "bot_advisor") returning {stick: Vector2, interact, boost, ...}.
2. World brief needs `--defeated=cyclops[,medusa]` (harness progress preset) — not parsed. Add in Game._ready (harness only).
3. World brief owns `scripts/world/ending.gd`, but BUILDERS maps "ending" to core `ui/ending_card.gd`; the brief also says
   the sea shows the ending card. Use `world/ending.gd` when it exists, else the core card; agree on one flow.
4. Sfx names do not match docs/audio_list.json: swing->sword_swing, strike->sword_hit, boss_hurt-><id>_hurt,
   music title/fight_<id>->music_title/music_<id>; telegraph/impact/guard_break do not exist; shield_up, reflect, death,
   title_card, music_flight are never played. Rename or add an alias table in Sfx.
5. CharacterVisual.play() on a real GLB does not restart a clip that is still playing (AnimationPlayer.play(same) resumes;
   tested on 4.7.2: pos 0.39 -> 0.40). Second sweep / repeated hit or hurt freezes mid-clip. Seek to 0 when the name repeats.
6. Closing the pause menu with pad B makes Hercules roll (probe_pad.log t=3.41 event=roll); A on Resume = interact.
   Release gameplay actions (Input.action_release) when unpausing.
7. Game.goto() during a fade is silently dropped (robust.log: goto title at 7.62 lost). Queue the latest request.
8. BossBase._on_defeated sets state="dead" without _exit_state(old): module cleanup (beam/fire VFX, decals, loops) never runs.
9. take_weak_hit plays no `hurt` clip (SPEC §7.1 says it does).
10. boss.arena / boss.player are null inside _build(); set them before add_child (and say so in notes).
11. No `--seed=` (boss brief asks for 3 seeded win runs).
Minor: boss-name label and title-card subtitle are white on bright sand/sky (add outline/shadow); exposed weak-point glow is
faint on sand; ATTACK_BUFFER unused (any press during attack_1 chains); bot ignores `face`; EnvKit.prop gives no warning
for an unknown prop name; manifest-less GLB plays every clip non-looping; sword box tops out at 2.9 m (Medusa's upright
neck needs a low socket or bigger radius); harness never exercises the post-victory goto (quits 1.5 s after the win).
