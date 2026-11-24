# anim_pegasus_idle_n (idle_n animator, 2026-11-23) — owner at the Mac, decisions written here

- Clip `idle` from video idle_n: 6.0 s loop (was 7.0 s; nothing times on it, no events). Files in
  art_src/chars/pegasus/clips/idle_n/ (keys_idle.json, poses_idle/, action_idle.json, strip_idle.jpg, notes.md).
  The ASSEMBLER merges clips/idle_n/action_idle.json in place of clips/idle/action_idle.json (both are clip `idle`; never merge both).
- Decision: window video 1.0-7.0 s, ending compressed (weight shift back and wing refold authored before 6.0 s) so the loop
  starts and ends exactly in natural_pose.json (k00 = natural stance, 0 deg difference).
- Decision: keys sampled every 0.25 s from smooth functions (work/anim2/pegasus_idle_n/gen.py + params.json) instead of
  hand poses, so phase lags and the loop seam are exact.
- FOR THE LEAD (game code): the natural stance's folded wings hit a seated rider on every frame (pair_check 36/36 frames).
  Do not play Pegasus `idle` while Hercules sits on it: start `fly` at the hop start in home_base.gd (~line 132). See notes.md.
- Tool (not mine, still open): animkit silhouette counts the green pegasus background as character; I used the green-key
  wrapper work/anim2/pegasus_idle_n/akg.py.
- ak info without --out wrote art_src/chars/pegasus/pegasus_bones.jpg (untracked); I moved it to my scratch.
