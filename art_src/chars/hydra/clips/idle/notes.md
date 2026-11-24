# hydra / idle video: animator notes (2026-11-22)

| clip | video window | keys | IoU per key (front/side, mean) | length | events | loop |
|---|---|---|---|---|---|---|
| idle | 1.000-2.917 s (one `ak cycle` period, 1.917 s, IoU 0.993), slowed x1.565 to 3.0 s | 6 | k0 0.931/0.915 (0.923), k1 0.932/0.912 (0.922), k2 0.940/0.913 (0.927), k3 0.934/0.910 (0.922), k4 0.931/0.909 (0.920), k5 0.930/0.911 (0.921); rest pose scores 0.888-0.896 side, 0.898-0.922 front; strip mean 0.922 | 3.0 s @24 fps | none | yes |

Keys (clip time, every 0.5 s; video time = 1.0 + t / 1.565): k0 0.0 inhale (video 1.000) · k1 0.5 (1.333) · k2 1.0 (1.625) ·
k3 1.5 full exhale (1.958) · k4 2.0 (2.292) · k5 2.5 (2.583). The loop seam copies k0. Feet: left/right ground 0-2 mm on every key.

## What the video shows (measured on the masks, 40.5 px/m)
- The layout is fine: calib IoU front 0.951 / side 0.955, views in sync, no camera move. The Hydra holds its rest stance all 10 s.
- The motion is tiny and almost uniform: one breath every 1.917 s. At the exhale (~2.0 s) all nine heads drop ~2 px (5 cm),
  the side heads also move ~1-2 px (3-5 cm) forward, the chest drops ~3 px (7 cm), and the tail tip rises 8+ px (20+ cm).
  The prompt asked for heads that "sway and weave, each a little differently"; the video's heads move in lockstep.

## Decisions (owner away)
- Window: one cycle from the inhale (1.0 s; the first second is the sheet pose settling). Slowed to 3.0 s (whole frames:
  12 per key) because a 14 m beast breathing every 1.9 s reads as panting; the brief allows 2-4 s idles.
- TRACED: breath on neck_c (forward 0.1-0.15 deg/link + head_c 2 deg nod), the common head drop on every side neck (the
  necks lean 0.4 deg/link further out; neck_1/8 bend down), spine_03 -0.3 deg, tail lift 0.6 deg/link (tip +0.3 m).
- AUTHORED (not in the video): per-neck sway on the 8 side necks, one sine per neck with its own phase and amplitude
  (0.35 deg/link sideways, 0.3 forward/back, head twist up to 2.5 deg, head pitch 1.5 deg), and a 0.5 deg/link tail
  side-swish. Head tips move up to ~8 px (20 cm) in the front view vs ~1 px in the video; this costs < 0.01 IoU and
  stops nine heads from moving as one. Centre head: kept almost still sideways (0.05 deg/link) like the video.
- Front legs are listed at their rest orientation on every key so spine_03's breath does not swing the planted feet
  (without that, a 0.4 deg spine bend slid the front feet 3.4 cm and ground "lowest" lifted the hind feet).
- Framing: view_offset [0.02, 0.01, -0.07], view_scale 1.0 (fit on the rest pose at 1.0 s); render only, not baked.

## What does not match and why
- Chest drop: the video's chest sinks 7 cm on the exhale; ours ~2.5 cm. A bigger spine_03 bend lowers the front leg
  joints, which with planted feet needs front-leg IK (not worth it for 5 cm). Breath reads through the necks and tail instead.
- Side IoU tops out at ~0.91: the video's side panel is narrower than the sheet's, so the tail beyond ~3.5 m behind the
  hips (sheet x < ~648 px) has no reference pixels and counts as "ours only" (the blue wedge in every diff). The hind
  heel is also slightly longer on the model than in the video. Both are constant across keys.
- strip_idle.jpg shows the shipped 3.0 s action against the video at video speed (reference time = 1.0 + clip time), so
  the rows drift apart in phase after ~1 s; the poses themselves were checked key by key (table above) and in a
  video-timed bake of the same poses (work/anim/hydra_idle/action_idle_video5.json + strip_v5_videotimed.jpg: 8 frames
  0.928-0.940 front / 0.910-0.915 side, mean 0.922).

Files: `keys_idle.json`, `poses_idle/k0-k5.json`, `action_idle.json`, `strip_idle.jpg`. Generator (re-run to tweak):
`python3 work/anim/hydra_idle/tools/gen.py <outdir> "$(cat work/anim/hydra_idle/params_p5.json)"`; strip mp4
`work/anim/hydra_idle/strip_idle.mp4`.

## animfix_hydra (2026-11-22)
See docs/notes/anim_hydra_fix.md for what changed in this folder (new/retimed clips, generators in work/animfix_hydra/).
