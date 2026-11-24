# Hercules devlog

This folder is the record of how **Hercules** (a Godot boss-fight game with Hercules, a four-armed Cyclops, Medusa, a
nine-headed Hydra and Pegasus) is being built by JC talking to Claude Code and its agents. It holds every message JC sent,
every question Claude asked back, every decision, a timeline, the Higgsfield credits, before/after screenshots, clips and a
plan for the devlog videos.

**Covers:** Sun Nov 22 2026, 4:31 PM EST (the trailer prompt, P01) to Mon Nov 23, about 2:35 PM EST. The first night
(chapters 1-10): characters, rigs, 41 animation clips, three boss fights, the world and sound (1-8), integration, the AI
play-test, the macOS app and the hand-over state (9), and the lead's last fix before the 1:45 AM hand-over (10). Monday
morning (chapters 11-12): JC came back, clicked "Polish them now" (P05) and, six minutes later, asked for natural
animations (P06); the nine open items were polished with independent reviews, and every character got a natural stance,
nine new reference videos and 50 re-keyed or re-based clips; the app was rebuilt at 11:42 AM. Monday afternoon
(chapter 13): JC played it himself for 18 minutes, recording his screen and voice, wrote "Everything looks good" with six
small points (P08), and one workflow of 15 agents fixed them (the backwards sword hand, the mount, flight, creatures on
the islands, hit effects and damage, clipping). The app rebuild with those fixes comes after this devlog pass.

## What's in here

| File | What it is | Use it for |
|---|---|---|
| [VIDEO_OUTLINE.md](VIDEO_OUTLINE.md) | Seven episodes (hooks, beats, media files, numbers on screen, clips to record yourself; episode 7 is built on your own recorded play-test), a single-video cut and 15 Shorts ideas. | Planning and editing. Start here. |
| [DEVLOG.md](DEVLOG.md) | The story in thirteen chapters: what was asked (quotes), decisions, what was built, numbers, time and tokens, problems and fixes, talking points, media. Also the project-at-a-glance totals and the Higgsfield credits table (by model and by purpose). | The script source. |
| [PROMPTS.md](PROMPTS.md) | Every message JC sent (P01-P08), word for word with typos: the pasted trailer prompt, the feedback on the first trailer, the game request, the reply button "Polish them now", the stiffness message typed while Claude worked, "launch the game" and his play-test feedback; the 28 lines he spoke in his play-test recording (S01-S28); the interrupt (X01); Claude's questions and offers (Q01-Q03). No multiple-choice questions were asked. | Exact quotes for on-screen text. |
| [DECISIONS.md](DECISIONS.md) | 124 decisions (D01-D124): time, options, choice, who decided (JC, the lead, or a named agent), why, chapter. | "Why did you do it that way?" moments. |
| [TIMELINE.md](TIMELINE.md) | One line per event with its time, and time/agents/tokens per phase and for the whole session. | Timestamps and "how long did it take". |
| [MEDIA_INDEX.md](MEDIA_INDEX.md) | Captioned list of every image and clip in `media/`, by chapter, before/after pairs marked (kept by the media agent). | Finding the right picture fast. |
| `media/` | JPEGs (≤ 1600 px) and MP4 clips (≤ 1080p) with posters, one folder per chapter (`01_trailer` ... `13_owner_feedback`; chapter 13 also has clips from your own play-test recording, with your voice). | B-roll, before/after wipes. |
| [media_plan.md](media_plan.md) | The media agent's file plan. | Where a file should be. |
| `notes/lead_log.md` | The lead's raw facts, written during the build. | Source checks. |
| `media_inbox/` | Images the agents saved while working, with `captions.txt` per role. | Raw material for media. |
| `check_devlog.py` | Checks every link and scans for personal details. | Run it after every update. |

## The build in numbers
- 8 messages from JC: 4 on Nov 22 (the last at 5:33 PM), 4 on Nov 23 (a reply button at 8:40 AM, a message typed while
  Claude worked at 8:46 AM, "launch the game" at 12:51 PM, his play-test feedback at 1:12 PM), plus 28 spoken lines in his
  play-test recording. Claude asked 3 questions or offers (Q01 and Q03 unanswered, Q02 answered by P05).
- Nov 22: 9.16 h wall clock (8.89 h active), of which the game 8.14 h; 136 agents in 16 workflows, 40.84 agent-hours;
  1,762.63 M tokens, 9.13 M output (final count at the hand-over).
- Nov 23 up to 2:38 PM: 5.98 h wall (4.67 h active); 75 agents in 11 workflows, 15.97 agent-hours; 975.61 M tokens, 4.71 M
  output (the Chapter 13 devlog agent was still writing).
- Whole project up to 2:38 PM: 211 agents, 56.81 agent-hours, 2,742.66 M tokens, 13.85 M output; 22.12 h wall clock
  including a 6.9 h quiet night (13.64 h active).
- Higgsfield: 2,018.29 credits for the game (163 ledger jobs, incl. 90 for three unpriced Meshy jobs at catalogue price;
  270 of it on Nov 23 for nine natural-stance videos, no retakes) + 835 for the trailer, about 2,853 in all.
- 5 characters generated and rigged (29 / 29 / 35 / 76 / 43 bones), 18 props, 42 Seedance reference videos (33 + 9),
  53 clips in the game files (51 on Nov 22 + 2 Hydra turn walks), 62 sounds, 3 boss fights, the world with flight on Pegasus.
- Play-test: 6 AI testers + the lead, 54 findings (0 blockers, 19 majors), all majors fixed; the last bot run beat the
  whole game (3 victories, 0 defeats, 0 script errors). A 231 MB macOS app in `builds/`.
- After the final check the lead found Hercules side-on while circling a boss, the main move of every fight, and fixed
  it in code in about 11 minutes (chapter 10): the camera now keeps his back. On an idle machine the three fights hold
  120 fps; the stutter measured during the build came from the build's own load.
- Monday (chapters 11-12): the nine open items polished by 13 agents with 4 independent reviews (23 findings; the 22 handed to the re-fixers were all real, one only partly);
  the first-use freeze (2-4 freezes of 362-910 ms per fight on a cold start) gone. Then the stiff animations: the share of
  joints that move across all old clips went from 53 % to 80 % (the Hydra's idle from 0 to 43 of 76 joints). The AI's
  own mistakes are in there too: it took JC's keyboard focus twice before it built a no-focus wrapper, its night-time
  checks never counted frozen limbs, and its first new Hercules idle was too quiet from behind.
- Monday afternoon (chapter 13): JC's first own play-test, 18 minutes recorded with his voice (3 wins, 2 losses, "it's not
  too easy to play, which is good"), then "Everything looks good" and six small points. 15 agents in one workflow: the
  sword now sits in a closed fist (two of the AI's own earlier fixes had stacked into a reverse grip), the left stick
  alone steers in flight with Pegasus held in the centre of the frame, a real hop on and off the horse, Pegasus's fly and
  glide remade, unbeaten bosses walking on their islands, hit effects with cut marks that stay, and capsules that keep
  Hercules out of the bosses. The reviewers wrote 25 findings (6 major), among them the rider still hidden behind the wing
  getting off: JC's exact complaint. No Higgsfield credits.

## Words used throughout
- **JC:** the owner. **The lead:** the main Claude Code session (Fable 5.2). **Agents:** extra Claude sessions (Opus 5.5)
  started for one job each inside a workflow.
- **P01, Q01, D01, AQ1, X01:** a prompt, a question Claude asked, a decision, a multiple-choice question + answer, an interrupt.
- **IoU:** how much the rig's silhouette overlaps the reference video's (0 = none, 1 = identical); the score the animators chase.
- **Times** are New York time (EST) unless marked UTC. **Tokens:** "total" includes every cached re-read of the context;
  "output" is what the models wrote.

## Privacy (this folder may be shown on YouTube)
No emails, account ids, Higgsfield result links (they contain an account id) or full home paths (`~/HerculesGame` is written
instead). The private-word list the checker uses lives in the repo's git-ignored `.devlog_tools/` folder and is never
committed. JC's own wording in P02 names a commercial game; nothing else in the project does.

## Kept up to date for the whole build
After every milestone, workflow run, owner decision or noteworthy fix these files are extended and checked with
`check_devlog.py`. The checklist lives in the repo's `CLAUDE.md`.
