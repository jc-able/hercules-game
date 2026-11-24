# Hercules — standing rules for every Claude session and agent

## Devlog: keep it current for the whole lifetime of this build (owner rule)

JC makes YouTube devlog videos about this build. After **every** milestone, workflow run, owner decision or noteworthy
fix — before reporting the work as done — update `docs/devlog/` with the devlog-skill:

1. **PROMPTS.md**: every new owner message word for word with local time, incl. messages sent mid-task and multiple-choice
   answers; every question Claude asked and the answer (`extract_transcript.py` finds them all).
2. **DECISIONS.md**: every new decision with options, choice, who decided and why.
3. **DEVLOG.md**: extend the current chapter or start a new one — what was asked, built, measured, broken and fixed; time + tokens;
   talking points.
4. **TIMELINE.md**: one line per event. 5. **media/** + **MEDIA_INDEX.md**: BEFORE (captured before changing anything visible) and
   AFTER screenshots. 6. **VIDEO_OUTLINE.md**: place the new work in an episode.
7. Run `python3 docs/devlog/check_devlog.py` (add `--extra .devlog_tools/private_literals.txt`, a list of your own private
   words kept in that git-ignored folder), then push in small batches.

Privacy: the folder may be shown on YouTube — never write emails, team/device/user IDs, server IPs, keys, tokens, signing
identities or user-specific paths. `.devlog_tools/` (private-word list) is git-ignored. Workflow scripts for this game end with
a devlog step.
