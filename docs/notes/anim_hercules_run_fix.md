# anim_hercules_run_fix notes (2026-11-22)

- DECISION (owner away, taken by the fixer as the lead's option (b)): the Hercules `run` clip now has an authored running
  stride on top of the traced jog. Leg IoU against the reference dropped on purpose (strip mean 0.857 -> 0.725).
  No reference re-generation (option (c), credits) was requested.
- REQUEST (core / player controller): the planted foot moves back at ~3.7 m/s at 1.0x. At the SPEC run speed of 6.0 m/s
  the feet still skate ~2.3 m/s. Suggest playing `run` with a speed scale of about 1.3 at full speed (stride cycle 0.64 s,
  ~3.1 steps/s, natural for 6 m/s; foot speed ~4.8 m/s), or scaling playback with velocity (1.3 * speed / 6.0).
- Tool tip: since pose angles are absolute, a small grid search over thigh/shin/foot rx with `ak solve`
  (root.ground lowest) hits a ball-of-foot position and a hip height in ~30 s
  (work/anim/hercules_run_fix/grid.py). `sample.py` there reads back every frame and prints foot contact and travel.
