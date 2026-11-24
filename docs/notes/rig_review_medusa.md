# Independent rig review: medusa (2026-11-22)

Work files: `work/rig_review_medusa/`. These are reviewer copies. Nothing in `art_src/chars/medusa/` was changed.
Scripts: `check_contract.py` (contract), `stress.py` + `stress_poses.json` (6 own poses + 80-degree single-joint sweep),
`stress2.py` (moderate-angle per-joint tests -> `moderate_report.json`), `stress3.py` (seam heat close-ups).

Contract: PASS. 1 mesh (34,976 verts / 70,000 tris, 1 island, manifold) + 1 armature, both with identity transforms.
Size 3.73 x 9.89 x 6.5 m, min Z 0, centred on X, faces -Y. 35 bones / 34 deforming; the `root` bone is non-deforming at the origin.
Sides are correct (_l at +X). Weights: all vertices weighted, max 4 influences, normalised, no NaN. The texture is 2048 px.
rig.json matches the blend exactly. Sockets head/neck/tail_tip (+eyes) exist. The GLB has 1 skin with 35 joints, 1 mesh and 0 animations.

Weight problems (max edge stretch at normal angles; target < 5 cm):
- Neck/shoulder seam: a strip at y -0.45, z 4.8-5.0, |x| 0.4-0.7 has spine_03 0.5 / neck 0.5, right next to vertices with
  shoulder/upper_arm 0.9. Results: clavicle up 30 = 26 cm, neck turn 35 = 23 cm, upper arm forward 90 = 13 cm.
- Head/neck: the neck weight runs up into the face (neck 0.41 at the chin z 5.5, 0.23 at z 5.8). Head turn 45 = 27 cm,
  nod 40 = 23 cm.
- Snake roots: a hard 0 -> 0.6 step at each hair_* root. hair_l_01 up 45 = 17 cm, hair_l_03 forward 60 = 17 cm.
- The clavicles leak across the midline: shoulder_l reaches the right shoulder (<= 0.09 on 292 verts), and the same mirrored.
- Fine: elbow 110 (< 3 cm), wrist 70, spine bends, tail side 60 and up 45.

Split sheet: the front panel is only +-4.84 m wide, but the tail swings out to +-9.3 m in tail_swipe (my r3 render clips it).
In the side panel the tail pointing forward reaches y -10.2 against an edge at -9.37. The character fills only 235 of 720 px in height.
