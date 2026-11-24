# anim_cyclops_slam notes

- Rig request (cyclops): the upper-arm chain is short for this body (upper_arm_u 0.80 + forearm_u 0.80 m); in the slam/stuck
  poses the left upper hand cannot reach the club handle (stays 0.6-0.9 m above it). Longer upper arm/forearm bones (or
  a two-hand IK in game to socket `club_grip2`) would fix it. Clips are delivered as is.
- Helper for future animators: work/anim/cyclops_slam/aim2eul.py converts aim-form bones (front/side/twist) to the rx/ry/rz
  that `ak fit` needs (exact: same IoU). kin.py is an FK matching `ak solve` to 1 mm (absolute space) + two-bone IK;
  club.py measures the club line in both panels of an aligned frame. Suggest folding aim->euler into `ak fit` itself.
