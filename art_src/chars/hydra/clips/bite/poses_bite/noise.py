"""animfix_hydra: per-neck bend noise (deg per link, front panel ry) on the bite side necks at k3/k4/k5 so the
mirror pairs never move as twins. Run after poses_bite/gen.py poses_bite/params_fix.json poses_bite."""
import json
N = {"k3": [3, -4, 2, -3, -3.5, 2.5, -3.5, 4], "k4": [-3.5, 3, -4, 2.5, 2, -3.5, 3, -3], "k5": [2, -2.5, 3.5, -2, -2.5, 3, -2, 2.5]}
# pair (i, 9-i): same sign = OPPOSITE motion after the mirror, so the twins split
prof = [1.0, 1.0, 0.8, 0.6]
for k, v in N.items():
    fn = f"poses_bite/{k}.json"; p = json.load(open(fn))
    for i, n in enumerate(v, start=1):
        for j in range(4):
            bn = f"neck_{i}_0{j + 1}"
            e = p["bones"].setdefault(bn, {})
            e["ry"] = round(e.get("ry", 0.0) + n * prof[j], 2)
    p["noise_note"] = "animfix_hydra noise.py: per-neck ry noise " + json.dumps(v)
    json.dump(p, open(fn, "w"), indent=1)
print("noise ok")
