export const meta = {
  name: 'hercules-anim-finalize',
  description: 'Per character: merge the baked clips into the rig, export the game GLB + clip manifest, check it in Godot, then review every clip and fix what is wrong',
  phases: [
    { title: 'Assemble', detail: 'merge + export + Godot import check', model: 'opus' },
    { title: 'Review', detail: 'one reviewer per character over all clips', model: 'opus' },
    { title: 'Fix', detail: 'repair flagged clips, re-export', model: 'opus' },
  ],
}
// args: { chars: ['hercules', ...], extra: { <id>: 'game requirements for this character from the module notes' } }
const R = '~/HerculesGame'   // the repo (your clone)
const RESULT = { type: 'object', properties: {
  status: { type: 'string', enum: ['done', 'partial', 'failed'] }, summary: { type: 'string' },
  clips: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, length_s: { type: 'number' }, loop: { type: 'boolean' }, ok: { type: 'boolean' }, note: { type: 'string' } }, required: ['name', 'ok'] } },
  missing_clips: { type: 'array', items: { type: 'string' } },
  problems: { type: 'array', items: { type: 'string' } },
}, required: ['status', 'summary'] }
const FINDINGS = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['pass', 'pass_with_fixes', 'fail'] },
  findings: { type: 'array', items: { type: 'object', properties: {
    severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
    clip: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
  }, required: ['severity', 'problem'] } },
  evidence: { type: 'string' },
}, required: ['verdict', 'findings'] }
const HEAD = `Hercules game build. Repo: ${R} (the owner is away: decide and note it).\nFirst make one trivial tool call (ls ${R}/docs), then read ${R}/docs/AGENT_RULES.md and ${R}/docs/ANIM_PIPELINE.md.\n`
const EX = args.extra || {}
const need = id => `\nGAME REQUIREMENTS for ${id} (from the boss/world module builders; also see docs/notes/${id}.md): ${EX[id] || 'none listed'}\n`
const out = await pipeline(args.chars,
  id => agent(`${HEAD}You are the ASSEMBLER for the character "${id}". You are the ONLY writer of art_src/chars/${id}/${id}.blend and of game/assets/characters/${id}/ right now.\nInputs: baked clips in art_src/chars/${id}/clips/<video>/action_<clip>.json with keys_<clip>.json and notes.md (made by animator agents against Seedance front|side reference videos); the clip list for ${id} in docs/SPEC.md §8; rig.json (sockets, socket_offsets).${id === 'hercules' ? ' Also: Hercules needs strafe_r = the left/right mirror of strafe_l (tools/ak mirror --keys, then bake to clips/strafe/action_strafe_r.json), and if art_src/chars/ride/clips/ride/action_ride.json exists it is his `ride` clip.' : ''}${id === 'pegasus' ? ' Also: if art_src/chars/ride/clips/ride/ holds an action for pegasus (e.g. action_fly_ridden.json) include it.' : ''}\nDo:\n1) List the clips present vs the SPEC §8 list; report missing ones (do not invent animation; a missing optional clip is reported, not faked).\n2) tools/ak merge art_src/chars/${id}/${id}.blend <all action JSON files> (one call), then tools/ak export ... --out game/assets/characters/${id}/${id}.glb --clips-json game/assets/characters/${id}/${id}_clips.json. The manifest must carry: clips (length, loop, events from each keys file), sockets + socket_offsets from rig.json (logical names of SPEC §8/§10), and "size" (height etc. from rig.json). Check the GLB with pygltflib: every clip present with the manifest length, one skin, textures embedded, size reasonable (< 25 MB; if the texture makes it larger, say so).\n3) Godot: take the import lock (SPEC §10), run Godot --headless --path game --import, release the lock. Then prove the model works through the game's own loader: a throw-away script (work/assemble_${id}/probe.gd, run with the harness flags the core notes describe or with --script) that calls CharacterVisual.create("${id}"), checks has_clip/clip_length/event_time for every clip, socket() for every logical socket, and plays 3 clips while saving 4 windowed screenshots (1280x720) from a camera placed like the game's chase camera; look at them (<= 1024 px): model upright, facing the right way (+Z front), real size, textured with the toon look, props (sword/shield/club) in the hands, no exploded mesh. Fix what is mechanical in YOUR files (export options, manifest, offsets); if the problem is in core's CharacterVisual, write the exact request in docs/notes/assemble_${id}.md.\n4) Devlog: save one good in-engine shot per AGENT_RULES.${need(id)}Final answer: the result schema (one entry per clip).`, { label: `assemble:${id}`, phase: 'Assemble', schema: RESULT, model: 'opus', effort: 'high' }),
  async (built, id) => {
    if (!built) throw new Error('assembler returned nothing: ' + id)
    const review = await agent(`${HEAD}You are the INDEPENDENT ANIMATION REVIEWER for the character "${id}". Every clip was keyframed against a Seedance front|side reference video (folders art_src/chars/${id}/clips/<video>/: ref.mp4, sheet.png, cam.json, keys_<clip>.json, action_<clip>.json, strip_<clip>.jpg, notes.md) and merged into art_src/chars/${id}/${id}.blend; the game files are game/assets/characters/${id}/. Do NOT edit those; work in work/anim_review_${id}/. Also read docs/briefs/anim_clip.md (the animators' quality bar) and docs/SPEC.md §2-§3, §8, §10.\nFor EVERY clip:\n1) Look at a strip of it against its video (use the animator's strip_<clip>.jpg if it is recent, else make one with tools/ak strip --n 8). You may read up to 24 images in total (<= 1024 px each) — one per clip first, a second look only where something seems wrong.\n2) Judge: does the motion match the video in both panels (front panel is a mirror: check the correct side leads)? Clean in-betweens (no pops, no limb through the body)? Loop seam invisible? Starts/ends compatible with idle or with its chained neighbour? In place (no drift)? Feet on the ground? Does the acting part do what the game needs at the event times (weapon passes through the target zone at active_start..active_end / impact; the stare is held between fire_start and fire_end; the head really reaches the ground in head_down / stunned; the right foreleg/arm is used)?\n3) Technical: clip lengths and events in the manifest vs keys files; GLB clip count; anything the assembler listed as missing.${need(id)}Return findings with severity (blocker = clip unusable or missing but required for a boss attack / core player move; major = visibly wrong; minor = polish), each naming the clip and a concrete fix (time, bones).\nThe assembler reported: ${JSON.stringify(built).slice(0, 3500)}`, { label: `review:${id}`, phase: 'Review', schema: FINDINGS, model: 'opus', effort: 'high' })
    return { built, review }
  },
  async (prev, id) => {
    const all = (prev.review && prev.review.findings) || []
    const todo = all.filter(f => f.severity !== 'minor').concat(all.filter(f => f.severity === 'minor').slice(0, 6))
    if (!todo.length) return { id, ...prev, fix: null }
    const fix = await agent(`${HEAD}You are the ANIMATION FIXER for the character "${id}" and now the ONLY writer of art_src/chars/${id}/ (blend + clips) and game/assets/characters/${id}/. Also read docs/briefs/anim_clip.md.\nFix the findings below: edit the pose/key files of the flagged clips (art_src/chars/${id}/clips/<video>/), re-bake them (tools/ak bake ... --out-action), make a new strip and LOOK at it, then re-merge ALL clips, re-export the GLB + manifest exactly as the assembler did (its notes: docs/notes/assemble_${id}.md if present, else follow docs/ANIM_PIPELINE.md), re-import in Godot under the import lock (SPEC §10) and re-run the assembler's probe (work/assemble_${id}/probe.gd) to make sure nothing broke. A clip that is missing and required: author it from the closest reference video segment if one exists; otherwise say exactly which reference video the lead must generate.${need(id)}FINDINGS (JSON):\n${JSON.stringify(todo).slice(0, 40000)}\nFinal answer: the result schema (one entry per clip in the final GLB; problems = what is still not right).`, { label: `fix:${id}`, phase: 'Fix', schema: RESULT, model: 'opus', effort: 'high' })
    return { id, ...prev, fix }
  }
)
return out.map(o => o && ({ id: o.id, verdict: o.review && o.review.verdict,
  findings: ((o.review && o.review.findings) || []).filter(f => f.severity !== 'minor').map(f => `${f.severity} ${f.clip || ''}: ${(f.problem || '').slice(0, 160)}`),
  final: (o.fix || o.built) }))
