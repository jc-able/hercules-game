# Brief — the natural-animation pass (2026-11-23, after the owner's first own test)

## What the owner said (word for word, 2026-11-23 8:47 AM)
> "Make sure that all animations look natural throughout the whole gameplay. Right now, some of the animations. Don't
> look natural, especially when the monsters are walking towards Hercules. Some of them are still in the static pose in
> terms of limbs. They seem a little stiff. Make every movement throughout the process natural, as well as the idle
> animation when the game first starts."

## What is wrong (measured by the lead, `python3 tools/clip_motion.py <id>`: a bone that turns < 3 degrees in a whole
## clip counts as frozen)
| Clip | Joints that move | What stays frozen |
|---|---|---|
| cyclops `walk` | 13 of 29 | all four arms (shoulders, upper arms, forearms, hands), head, spine_03: he walks in the T pose with the club straight up |
| cyclops `idle` | 9 of 29 | forearms, hands, neck, spine, legs: a T pose that barely breathes |
| hydra `idle` | 0 of 76 | everything: a statue |
| hydra `walk` | 24 of 76 | all nine heads, the jaw and most necks: only the legs move |
| medusa `slither` | 26 of 35 | hands, shoulders (arms held out) |
| medusa `idle` | 18 of 35 | upper arms, forearms, head, neck, spine |
| hercules `idle` | 6 of 29 | nearly everything (this is what stands on the home island when the game starts) |
| hercules `strafe_l/r`, `walk_back`, `block_idle`, `ride` | 3-10 of 29 | arms, head, neck, spine |
| hydra attacks (`bite*`, `fire_sweep*`, `stomp*`, `head_down`, `hurt`) | 25-47 of 76 | the eight heads that are not acting, the legs |
| medusa `gaze`, `stunned`, `hurt` | 13-17 of 35 | the whole tail, arms |

## Why (root cause)
Every reference video started from the split sheet of the rig in its REST pose (arms spread, heads fanned out). Seedance
kept that pose for every limb the prompt did not force to move (see `art_src/chars/cyclops/clips/walk/notes.md`: "the
video keeps the arms in the T pose and the club still"), and the animators matched the video faithfully. Limbs nobody
keyed stay in the rest pose in every clip.

## The fix (still the owner's method: sheet of the rigged asset -> Seedance 2.5 at 480p -> keyframes matched to the video)
1. **A natural stance per character** (`art_src/chars/<id>/natural_pose.json`, animkit pose format): how this creature
   stands ready when nothing happens. Arms hang or rest (the Cyclops's club low, on the shoulder or at his side),
   knees soft, weight slightly on one leg, heads at different heights and angles, nothing mirror-symmetric.
2. **New split sheets rendered from that stance** (`sheet_nat_<framing>.png` + `cam_nat_<framing>.json`): they are the
   first frame of the new reference videos, so the video starts natural.
3. **New reference videos** (the lead generates them: 480p, 10 s, FRONT | SIDE) for the clips the owner named: the
   boss walks, every idle. The motion prompt names every limb group and what it does.
4. **Keyframes for ALL limb groups**, matched to the new video; what the video does not show clearly is authored with
   believable overlap (arms against legs, phase lag down a tail or neck, heads never in unison, breathing).
5. **Every other clip is re-based**: a limb group the clip leaves frozen in the rest pose is moved to the natural
   stance and given quiet life (breathing, sway, a look toward the action). One-shots start from and return to the
   natural stance unless they end in their own pose.

## What "natural" means here (checklist for animators and reviewers)
- No limb group (arms, head and neck, spine, tail, extra heads, wings) is frozen for a whole clip, unless it is planted
  (feet on the ground while standing). `tools/clip_motion.py` proves it; a strip proves it looks right.
- Walks: arms swing against the legs, the torso counter-rotates and bobs, the head stays level and looks ahead, a held
  weapon swings with the arm. Feet do not slide (the game plays the clip at ground speed / `move_speed`).
- Idles: breathing in chest and shoulders (one breath every 3-4 s), a slow weight shift, small head turns, fingers and
  tails alive. No rocking back and forth like a pendulum, no perfectly symmetric motion.
- Many heads / tails / snakes: phase offsets, different amplitudes; follow-through after a strike.
- Clean in-betweens: no pops, no limb through the body, invisible loop seam.

## Contracts that must NOT change (the game's timing depends on them)
Clip names, the loop flag, events (their names; their times only when the move itself is unchanged), sockets and
socket_offsets, weak-point bones, ground contact, in-place motion (no travel), `move_speed` meaning (planted-foot speed).
A clip's length may change only when the new motion needs it: say so with the old and new numbers (the boss scripts are
re-tuned after you). Attack clips keep their acting limb exactly as it is (the club lands where the slam circle is).
