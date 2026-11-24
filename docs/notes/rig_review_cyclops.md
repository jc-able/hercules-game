# Cyclops rig review (independent reviewer, 2026-11-22)
Scratch: work/rig_review_cyclops/ (check.py, stress.py, probe.py, heel.py; results in check.json, out*/).
Decisive finding: leg joints are one segment too low. Mesh slices (left leg, x>0.15): ankle narrowing z 0.9-1.1
(y centre ~0.57), calf bulge at the back z 1.5-1.8, knee hollow z 2.2-2.3 (y centre ~0.35, x ~0.82).
Rig has knee at z 1.12 and ankle at z 0.55 -> re-place knee/ankle, re-weight legs, rebuild rig.json/glb.
Upper-arm elbow (x 2.15) and wrist (x 3.05) match the mesh. Forearm_u weights are smeared (max avg 0.41).
Split sheet: sweep club reaches the front-panel edge (0.06 m margin); suggest --mw 1.3 --mh 1.55.
