# Brief — audio (process the generated sounds and wire them into the game)

Read `docs/AGENT_RULES.md`, SPEC §2-§5 and `docs/notes/core.md`. You own `game/assets/audio/**`,
`game/scripts/autoload/sfx.gd` (the core workflow is finished: you may rewrite it, keep `Sfx.play(name, pos?)` working),
`game/default_bus_layout.tres` and `docs/notes/audio.md`. In OTHER scripts you may only add or rename `Sfx.` calls
(no gameplay changes); list every such edit in your notes.

## Input
- `art_src/audio/raw/<name>.mp3` — generated on Higgsfield (Mirelo sound effects, ElevenLabs instrumental music).
  Registry with the prompt, intended length and loop flag of every sound: `docs/audio_list.json`.

## Do
1. Listen with numbers (you cannot hear): for every raw file measure duration, leading/trailing silence, peak and
   integrated loudness (`ffmpeg -af ebur128` / `volumedetect`, `silencedetect`). Flag files that are silent, clipped or far
   from the intended length.
2. Process into `game/assets/audio/sfx/<name>.wav` (mono 44.1 kHz 16-bit, trimmed head silence <= 10 ms, short fade out,
   peak about -3 dBFS, one-shots cut to the useful part) and `game/assets/audio/music/<name>.ogg`
   (stereo, Vorbis q5 with `/opt/homebrew/opt/ffmpeg@4/bin/ffmpeg` — the default ffmpeg has no libvorbis; about -16 LUFS).
   Loops (`"loop": true` + the music): make them seamless (equal-power crossfade of tail into head, cut on zero crossings),
   then verify the seam numerically.
3. `game/assets/audio/audio.json`: per sound `{file, bus, volume_db, pitch_random, loop, max_distance, positional}`.
4. `Sfx` autoload: loads the manifest, pools AudioStreamPlayer / AudioStreamPlayer3D, `play(name, pos = null)`,
   `play_loop(name) -> id` / `stop_loop(id)`, `music(name, fade = 1.0)` / `stop_music(fade)`, buses Master / Music / SFX / UI
   with a limiter on Master, volume settings hooks if core has a settings page. Missing sound = one warning, no crash.
   Loop flags are set in code on the streams (import defaults do not loop).
5. Wiring audit: `grep -rn 'Sfx\.' game/scripts` — every name used must exist in the manifest (rename the call or add an
   alias); every sound in the registry should be used somewhere sensible: footsteps from the player's movement, roll,
   swing, weak-point hit, glance, block, reflect, hurt, death, petrify; each boss's warn / attack / hurt / death / roar;
   arena ambiences (sea_loop at the quarry and sanctuary, lava_loop at the volcano), brazier fire_loop, beacon_loop near
   landing rings, wind_loop + wing_flap in flight, thunder in the storm wall, UI move/accept/back, title_card, victory,
   defeat, trophy; music: music_title on title + home, music_flight over the sea, music_<boss> in each fight
   (start on `start_fight`, stop on victory/defeat stings).
6. Proof: a headless harness run of each scene id with a debug flag that logs every `Sfx.play` name
   (`[H] event=sfx name=...`) — show that each fight fires its warn/attack/hit sounds; plus a 20-second Movie Maker
   capture of one fight (`--write-movie`, windowed) whose audio track you measure (not silent, no clipping).

## Done when
Manifest + files exist for every registry entry, the audit shows no unknown names and no unused sounds (or says why),
the runs print no errors, and `docs/notes/audio.md` lists levels, loop seams, edits made in other scripts, and any sound
that should be regenerated (with a better prompt suggestion for the lead).
