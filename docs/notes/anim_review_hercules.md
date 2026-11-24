# Independent animation review: hercules (2026-11-22; owner away, severity calls are mine)

Scratch + numbers: `work/anim_review_hercules/` (analyze.py / analysis.json = FK of every GLB clip: seams, pops, sword
tip path via socket_offsets; compat.py / compat.json = pose distance at the game's transition points + skinned-mesh
ground checks; a1_slash.jpg, a2_slash.jpg, death_topple.jpg = read-back renders). Nothing in art_src/ or game/ changed.
`docs/notes/hercules.md` (named in the review brief) does not exist; the game needs were taken from player.gd/tuning.gd.

Technical: 13/13 clips in the GLB, lengths/loop/events equal keys files and manifest, 29 joints, all loop seams exact
(0.0 cm), hips drift 0 in every clip, socket offsets reproduce the blend's blade/shield directions exactly.

Main problems (details and fixes in the review answer):
1. attack_1 start, attack_2 end and hit start/end are the rig REST A-pose (hips 1.084, feet together), not idle
   (hips 0.837, wide stagger): 0.58 m foot jump / 25 cm hip jump inside the game's 0.05-0.06 s cross-fades.
2. Game timing vs clips: chain at ATTACK_CHAIN_FROM 0.40 s = attack_1 clip 0.909 s, but the chain pose is at 1.25 s;
   block_start is cut at 0.15 s (mid-step); hit plays 0.4 s of 2.17 s; core never reads move_speed.
3. Strikes compressed by playback speed: attack_2 chop 0.458->0.5 s = one game frame at 2.31x; attack_1 slash 2 frames.
4. Skirt split (rig) visible in idle, run, strafe, block_idle. Death: sword tip 26 cm under the floor at 2.71-2.88 s.
