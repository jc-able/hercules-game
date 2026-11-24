"""Generate medusa slither poses from a phase p in [0,1).
Usage: python3 gen.py params.json outdir n_keys"""
import json, math, sys, os
P = json.load(open(sys.argv[1])); out = sys.argv[2]; n = int(sys.argv[3])
os.makedirs(out, exist_ok=True)
TAIL = [f"tail_{i:02d}" for i in range(1, 15)]
def s(x): return math.sin(2*math.pi*x)
def pose(p):
    # travelling wave on the ground tail: bend per link, wave runs head->tip
    # tangent heading of each flat tail link (+ = toward char LEFT, +X); wave runs head->tip
    hs = {}
    for i in range(1, 15):
        if i < P["wave_start"]: hs[i] = 0.0; continue
        j = i - P["wave_start"]
        amp = P["wave_amp"] * min(1.0, (j + 1) / P.get("ramp", 1)) * (P["amp_taper"] ** j)
        hs[i] = amp * s(p - j / P["links_per_wave"] + P["wave_phase"])
    # rz (view axes, local delta): + turns a backward-pointing link's tip to -X
    rz = [round(-(hs[i] - hs.get(i - 1, 0.0)), 2) for i in range(1, 15)]
    base = P["base_amp"] * s(p + P["base_phase"])     # +: base swings to char LEFT (+X)
    bones = {
        # tail_01 hangs down: ry + swings its lower end to screen left (-X) -> use -base
        "spine_01": {"space": "local_delta", "ry": round(base * P["spine_k"], 2), "rx": P["lean"]},
        "spine_02": {"space": "local_delta", "ry": round(base * P["spine_k"] * 0.5, 2)},
        "neck": {"space": "local_delta", "ry": round(-base * P["spine_k"] * 0.6, 2)},
        "head": {"space": "local_delta", "ry": round(-base * P["spine_k"] * 0.6, 2),
                 "rz": round(P["head_yaw"] * s(p + P["base_phase"] + 0.1), 2)},
        "upper_arm_l": {"space": "local_delta", "rx": round(P["arm_amp"] * s(p + 0.25), 2),
                        "ry": round(-P["arm_out"] * (0.5 + 0.5 * s(2 * p)), 2)},
        "upper_arm_r": {"space": "local_delta", "rx": round(-P["arm_amp"] * s(p + 0.25), 2),
                        "ry": round(P["arm_out"] * (0.5 + 0.5 * s(2 * p)), 2)},
        "forearm_l": {"space": "local_delta", "rx": round(-P["fore_amp"] * (0.5 + 0.5 * s(p)), 2)},
        "forearm_r": {"space": "local_delta", "rx": round(-P["fore_amp"] * (0.5 + 0.5 * s(p + 0.5)), 2)},
    }
    # hair snakes: secondary motion with phase offsets
    for ii, side in enumerate("lr"):
        for jj in range(1, 4):
            ph = p + 0.17 * jj + 0.5 * ii
            bones[f"hair_{side}_{jj:02d}"] = {"space": "local_delta",
                "ry": round(P["hair_amp"] * s(ph), 2), "rx": round(P["hair_amp"] * 0.7 * s(ph + 0.25), 2)}
    return {"space": "absolute", "root": {"loc": [0, 0, 0], "ground": "lowest"},
            "view_offset": P.get("view_offset", [0, 0, 0]), "view_scale": P.get("view_scale", 1.0),
            "chain": {"name": "tail", "rz": rz, "ry": [round(-base, 2), round(-base * P.get("base2", 0.0), 2), round(base * (1 + P.get("base2", 0.0)) * P["base_counter"], 2)] + [0.0] * 11}, "bones": bones}
files = []
for i in range(n):
    p = i / n
    f = os.path.join(out, f"k{i}.json"); json.dump(pose(p), open(f, "w"), indent=1); files.append(f)
print("\n".join(files))
