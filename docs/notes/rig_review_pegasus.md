# Pegasus rig: independent review (reviewer agent, 2026-11-22)

Workspace: `work/rig_review_pegasus/`. Scripts: `contract_check.py`, `bleed.py`, `stress.py` (own poses R1-R6 plus isolated
normal poses N1-N8), `saddle_w.py`. `art_src/chars/pegasus/` was not modified.

Contract: PASS (1 mesh + 1 armature, transforms identity, faces -Y, ground 0, centred, withers 1.90, names and sides OK,
root OK, 34,981 verts all weighted, max 4, normalised, 2048 texture, rig.json matches, sockets OK, GLB has 1 skin / 41 joints).

Verdict: pass with fixes, no blockers. Decided while the owner was away: the rig can go to animation, but the weight fixes
below should be made first, because the fly, glide and ride clips depend on them.
1. Neck weights bleed onto the back under the saddle (average 0.24 neck weight on the bare white back). Neck forward 35 deg
   lifts the rider's seat 0.19 m.
2. The rear mane rides neck_02, so mane streaks are dragged over the withers and wing roots in normal neck moves (game camera).
3. Breastplate folds when the head tosses up (neck weight on the chest band).
4. Flank under the wing stretches at the top of the upstroke (fused wing edge weighted to spine_02).
Minor: both forearm bones reach the chest midline; the 3-bone tail stretches when lifted; the glide margin in
split_sheet is tight (0.35 m each side); cam.json bg is stored as linear, not as the sRGB pixel value.
