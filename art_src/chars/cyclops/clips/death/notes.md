# cyclops / death video: clip notes (animator, 2026-11-22; owner away, decisions noted)

The reference is usable: both panels stay in sync and the layout holds (calib IoU front 0.93 / side 0.95). The camera drifts
slightly: a framing fit gives about +0.17 m x, -0.2 m z from 2.75 s on. The traced key files carry that as `view_offset`
[0.17, -0.1, -0.2], which affects renders only. The video starts sinking at about 1.5 s, so the ready key at clip 0 is
scored against the 1.0 s frame.
IoU = silhouette overlap (front / side) of each key against its aligned video frame (`ak pose`).

| clip | window (video s) | keys | IoU per key (front/side) | length | events | what does not match |
|---|---|---|---|---|---|---|
| death | 1.5-6.0 (lying pose from 6.5) | 21: 11 traced + 10 grounded read-back in-betweens (g*.json) | k0_ready 0.75/0.82 (vs 1.0 s), k1_sink 0.54/0.51, k1b_land 0.41/0.50, k2_kneel 0.69/0.49, k3_slump 0.75/0.52, k3b_hold 0.74/0.42, k4_tip 0.73/0.60, k5_fall 0.70/0.62, k5b_land 0.51/0.43, k6_land 0.64/0.60, k6_lie 0.66/0.62; mean 0.65/0.56; strip mean 0.58 | 4.5 s @24 fps, not looping (lying pose held from 4.0 s) | none (SPEC §8 has no death event) | see below |

Timeline (clip s): 0 ready, 0.75 crouch (club arm still out), 1.0 knees land (heels up), 1.25 kneeling upright, 2.0-2.6
slumped with every arm hanging and the head down, 3.0 tipping, 3.29 falling, 3.5 lands on his front, 4.0 settled, held to 4.5.

What does not match and why:
- **The club stays in his hand.** In the video he drops it at about 2.0 s and it lies loose on the floor. Here it is
  bone-parented to `hand_u_r` in the blend, so it cannot be let go. Instead his right upper arm lowers and the club comes
  to rest on the floor beside him: while he kneels its head is on the floor at his right, and when he lies flat it lies
  sideways on the floor at his right. The loose club in the video costs about 0.1-0.25 IoU in the side panel on every
  key from 2.5 s on, which is why side IoU stays near 0.5. To drop it for real, the game would detach the club node at
  clip ~0.6 s and let it fall (request for the cyclops module; noted in docs/notes/anim_cyclops_death.md).
- **The clip keeps root motion** (baked with `--keep-root-motion`; decided by me, owner away). He falls forward from his
  knees, so his hips end up ~0.6 m forward and his head ~4 m forward of where he started. With the default in-place bake
  that forward fall would turn into a slide along the floor. Nothing travels: the knees stay at the spot where he knelt.
  The game should play this clip without moving the body.
- The k1b/k5b in-betweens score lower (0.41-0.51 front). These are quick transition frames (heels lift and feet flop
  flat; chest coming down), placed to stop the long 1.3 m foot bone and the falling body from passing through the floor.
- In the video his lying body is thicker in the middle (the shoulder hump is higher) and his arms spread wider on the floor.
  Ours is flatter: we would need to prop him on his arms, and then the club head lifts the body off the floor.
- The video's right upper arm stays out in a T until about 3.0 s. Ours lowers from 1.0 s so that the club can reach the floor.
- Floor contact is checked on every frame: the lowest vertex stays within -0.05 to +0.04 m of the floor across the whole
  clip (strip `lowest_z_range`).

Files: `keys_death.json`, `poses_death/*.json` (k* = traced, g* = read back from the bake and re-grounded),
`action_death.json`, `strip_death.jpg` (reference row above our row, t0 = 1.5). Scratch, gen.py and the mp4 strip are in
`work/anim/cyclops_death/`.

## Fix pass (anim fixer, 2026-11-22; owner away, decisions noted)
- death | 0-2.6 s kept (traced) + 2.6-4.5 RE-AUTHORED as a backward fall | 36 keys (b1_sitback 2.833, b2_tip 3.0, b3_fall 3.29, b4_land 3.42, b5_bounce 3.5, b5b_slide 3.75, b6_lie 4.0, plus i_*.json re-grounded read-back in-betweens) | strip IoU 0.55/0.38 (the video falls forward) | 4.5 s, root_motion kept (--keep-root-motion) | no events | sits back on his heels, tips back about the hips (root.rot rx -35/-70/-90), lands on his back knees up, legs slide out; head ends at y +5.74 m (BEHIND his start), feet at y -1.16 m; club lies flat at his right (lowest vertex +0.08 m). Kneel keys g112/k2/k3/k3b: right arm raised so the club stays above the floor. Feet within -0.03..+0.04 m of the floor every frame, club >= -0.04 m. Forward-fall keys kept in poses_death/old_forward_fall/. Seedance prompt if a reference is wanted: "sinks to his knees, then topples backward onto his back".
