# hydra / stomp — notes (animator agent, 2026-11-22)

stomp | window: video t 1.0-4.0 s (take 1; clip t = video t - 1.0) | 10 keys (k0, k0b, k1-k6, k6b, k0 again), 24 fps, 3.0 s, not looped, starts and ends in the rest/ready pose |
events: impact 1.75 s (video 2.75 s: the left forefoot `foot_fl` is back on the floor) |
IoU per key (front/side, framing corrected by view_offset/view_scale): k0 rest 0.83/0.93, k1 lift 0.5 s 0.72/0.86,
k2 peak 1.083 s 0.66/0.80, k3 hold 1.5 s 0.70/0.80, k4 descent 1.667 s 0.81/0.85, k5 impact 1.75 s 0.83/0.85, k6 recoil 2.0 s 0.78/0.88;
key mean 0.75 front / 0.84 side; strip mean 0.83 (8 frames), feet within 3 mm of the floor in every frame checked.
Doesn't match, and why:
- SIDE PANEL IS STATIC in both takes (only the head tops move a little: about 1,500 changed mask pixels against about 60,000 in the front panel).
  The lifted foreleg never shows there, so the side reference is unusable for the lift. The leg's forward/back motion (thigh forward
  about 80 degrees, shin about 25 degrees forward, foot curled) is authored from the prompt and the front panel. That is why side IoU drops to 0.80 at the peak.
- Front panel: the video draws the necks taller than the rig does (rest pose only scores 0.83 front at t=1.0), so the heads score red above ours at the peak.
- Weight shift: the video's upper body moves about 0.5 m toward the character's right (screen left) while the feet stay put. This is done as root.loc x
  (-0.45 to -0.6 m) with the three planted legs tilted 3-7 degrees in absolute space so their feet do not slide, plus a 0.3-1.1 degree roll to keep
  the left hind foot on the floor, plus a neck-fan lean. view_offset (framing only, ignored by bake) still absorbs about -0.15 m x and a 1-2.5 % zoom.
- Necks: the centre neck and the neck-fan lean/rise were traced on the front panel (ak fit + hand clamp; fit's inward 30-38 degree swings of necks 5-8 crossed
  the centre neck and were rejected). The per-neck phase offsets, the nods at impact/recoil (chain bend_up on the top links) and the tail lift (+3 degrees per link
  at the peak, -2 at impact) are authored secondary motion. The video shows no tail motion.
- Dust clouds in the video from 2.75 s on are an effect (not in the rig). They make the front IoU near the feet a little worse after impact.
- Fix made: the first bake pushed the lifting claws 15 cm through the floor at t=0.25 (ankle/foot rotated back before the leg rose). An early key k0b
  (thigh lifts first, ankle/foot neutral) fixed it: lowest vertex -0.002 m.
Files: keys_stomp.json, poses_stomp/k*.json (they carry view_offset/view_scale for scoring only), action_stomp.json, strip_stomp.jpg, strip_stomp.mp4.
Scratch: work/anim/hydra_stomp/ (fits, earlier versions v1-v5, final_keys.jpg = per-key TARGET|OURS|DIFF).

## animfix_hydra (2026-11-22)
See docs/notes/anim_hydra_fix.md for what changed in this folder (new/retimed clips, generators in work/animfix_hydra/).
