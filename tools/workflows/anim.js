export const meta = {
  name: 'hercules-anim',
  description: 'Keyframe every game clip to its Seedance front|side reference video with animkit: one animator per video, then an independent review and a fix pass',
  phases: [
    { title: 'Animate', detail: 'one animator per reference video', model: 'opus' },
    { title: 'Review', detail: 'independent check of each clip against its video', model: 'opus' },
    { title: 'Fix', detail: 'repair findings and re-bake', model: 'opus' },
  ],
}
// args: { videos: [{ id, video, clips: [..] }], review: true|false (false = animators only; a per-character review follows the merge) }
const R = '~/HerculesGame'   // the repo (your clone)
const ANIM = { type: 'object', properties: {
  status: { type: 'string', enum: ['done', 'partial', 'failed'] },
  reference_ok: { type: 'boolean' },
  reference_problems: { type: 'string' },
  clips: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, action_json: { type: 'string' }, length_s: { type: 'number' }, keys: { type: 'number' },
    mean_iou: { type: 'number' }, loop: { type: 'boolean' }, problems: { type: 'string' },
  }, required: ['name', 'action_json'] } },
  summary: { type: 'string' },
}, required: ['status', 'clips', 'summary'] }
const FINDINGS = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['pass', 'pass_with_fixes', 'fail'] },
  findings: { type: 'array', items: { type: 'object', properties: {
    severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
    clip: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
  }, required: ['severity', 'problem'] } },
  evidence: { type: 'string' },
}, required: ['verdict', 'findings'] }
const HEAD = `Hercules game build. Repo: ${R} (the owner is away: decide and note it).\nFirst make one trivial tool call (ls ${R}/docs), then read ${R}/docs/AGENT_RULES.md, ${R}/docs/ANIM_PIPELINE.md and ${R}/docs/briefs/anim_clip.md.\n`
const where = it => `Character "${it.id}", reference video "${it.video}" (folder art_src/chars/${it.id}/clips/${it.video}/: ref.mp4, ref_sheet.jpg, sheet.png, cam.json, prompt.txt). Game clips cut from this video: ${it.clips.join(', ')}.`
const out = await pipeline(args.videos,
  it => agent(`${HEAD}You are the ANIMATOR. ${where(it)}\nDo the brief docs/briefs/anim_clip.md for these clips: keyframe the real rig (art_src/chars/${it.id}/${it.id}.blend, read-only) with tools/ak until its front and side renders match the video, bake each clip to art_src/chars/${it.id}/clips/${it.video}/action_<clip>.json, make the strips, write notes.md. Scratch: work/anim/${it.id}_${it.video}/. Start simple: get one complete rough clip baked early, then refine keys; never plan the whole clip in one thought.\nFinal answer: the result schema (one entry per clip; reference_ok=false with reference_problems if the video is unusable).`, { label: `anim:${it.id}/${it.video}`, phase: 'Animate', schema: ANIM, model: 'opus', effort: 'high' }),
  async (built, it) => {
    if (!built) return { it, built: null, review: null }
    if (args.review === false) return { it, built, review: null }   // review happens per character after the merge
    const review = await agent(`${HEAD}You are an INDEPENDENT ANIMATION REVIEWER. ${where(it)}\nAnother agent keyframed these clips (files in that folder: action_<clip>.json, keys_<clip>.json, poses_<clip>/, strip_<clip>.jpg, notes.md). Do NOT edit that folder; work in work/anim_review/${it.id}_${it.video}/.\nFor each clip:\n1) Make your own strip with tools/ak strip (--n 10, the window from notes.md / keys) and LOOK at it: do the poses match the video in BOTH panels (the front panel is a mirror: the character's left is screen right — check the correct limb leads)? Are the in-betweens clean (no pops, no limb through the body, no twist flips)? Does the acting part do what the game needs (docs/SPEC.md §2-§3 and §8: e.g. the club ends in the ground in front with the forearm low; the stare is held; the correct foreleg stomps; the roll ends upright)?\n2) Technical checks with tools/ak / small scripts: action length, loop seam (first = last pose for loops), no horizontal root drift, feet on the ground where planted (ak reports ground), events present, inside the clip and at the right moment, chained clips share their boundary pose, weapons attached and readable.\n3) At most 10 image reads (<= 1024 px).\nReturn findings with severity (blocker = clip unusable in the game; major = visibly wrong motion, wrong side, pop, bad loop seam, missing event; minor = polish) and a concrete fix (clip, time, bones).\nThe animator reported: ${JSON.stringify(built).slice(0, 3000)}`, { label: `review:${it.id}/${it.video}`, phase: 'Review', schema: FINDINGS, model: 'opus', effort: 'high' })
    return { it, built, review }
  },
  async (prev) => {
    const it = prev.it
    if (!prev.built) return { id: it.id, video: it.video, failed: true }
    const all = (prev.review && prev.review.findings) || []
    const todo = all.filter(f => f.severity !== 'minor').concat(all.filter(f => f.severity === 'minor').slice(0, 4))
    if (!todo.length) return { id: it.id, video: it.video, built: prev.built, review: prev.review, fix: null }
    const fix = await agent(`${HEAD}You are the ANIMATION FIXER. ${where(it)}\nThe clips were keyframed by another agent (pose files, keys and notes are in that folder) and reviewed. Fix the findings below by editing the pose/key files in that folder, re-bake each changed clip to the same action_<clip>.json, re-make its strip and LOOK at it, and update notes.md. Scratch: work/anim/${it.id}_${it.video}_fix/.\nFINDINGS (JSON):\n${JSON.stringify(todo).slice(0, 30000)}\nFinal answer: the result schema (problems = what is still not right, per clip).`, { label: `fix:${it.id}/${it.video}`, phase: 'Fix', schema: ANIM, model: 'opus', effort: 'high' })
    return { id: it.id, video: it.video, built: prev.built, review: prev.review, fix }
  }
)
return out.map(o => o && ({ id: o.id, video: o.video, failed: !!o.failed,
  verdict: o.review && o.review.verdict,
  clips: ((o.fix || o.built || {}).clips || []).map(c => ({ name: c.name, len: c.length_s, iou: c.mean_iou, problems: (c.problems || '').slice(0, 300) })),
  reference_ok: o.built ? o.built.reference_ok : null, reference_problems: o.built ? (o.built.reference_problems || '').slice(0, 300) : '' }))
