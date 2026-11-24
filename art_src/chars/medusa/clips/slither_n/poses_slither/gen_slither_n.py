"""medusa slither_n: phase-driven key generator, every pose = natural stance + slither motion.
Usage: python3 gen_slither_n.py params.json natural_pose.json outdir n_keys
phase p = i / n_keys; p = 0 is video t = params.t0 (hips at their extreme toward her RIGHT, -X; left arm forward)."""
import json, math, sys, os, copy
P = json.load(open(sys.argv[1])); NAT = json.load(open(sys.argv[2])); out = sys.argv[3]; n = int(sys.argv[4])
os.makedirs(out, exist_ok=True)
TAU = 2 * math.pi
def c(p, lag=0.0): return math.cos(TAU * (p - lag))
def s(p, lag=0.0): return math.sin(TAU * (p - lag))

def motion(p):
    """bone -> {key: delta}; aim keys (front/side/twist) add to the stance's aim angles, others add to rx/ry/rz."""
    # measured on the video masks (1.75 s cycle): every band x = amp * cos(2pi (p - p_max)); the sway runs DOWN the body
    # (head p_max .38, chest .41, hips .49, upright tail .55-.65), then into the ground wave.
    def X(name): A, pm = P["x_" + name]; return A * c(p, pm)
    d = X("pelvis")
    chest = X("chest"); headx = X("head")
    a1 = math.degrees(math.atan2(chest - d, 1.4)) * P["tilt_k"]        # spine_01+02 tilt (+ry = top to +X)
    a3 = math.degrees(math.atan2(headx - (d + 1.55 * math.tan(math.radians(a1))), 0.6)) * P["tilt_k"]
    # upright tail: each joint placed on its measured band (x2 at z 2.46, x3 at z 1.62, x4 at z 0.82)
    xs = [d, X("t2"), X("t3"), X("t4")]; Ls = [0.84, 0.84, 0.80]
    absang = [math.degrees(math.asin(max(-0.9, min(0.9, -(xs[i + 1] - xs[i]) / Ls[i])))) for i in range(3)]  # ry + = lower end to -X (sway on top of the stance offsets)
    tail_ry = [absang[0], absang[1] - absang[0], absang[2] - absang[1], -absang[2]]
    rock = P["rock"] * c(p, P["rock_pmax"])        # pelvis pitch: + leans forward (head forward, upright tail back)
    m = {}
    m["pelvis"] = {"rz": P["hip_yaw"] * c(p, P["arm_phase"]), "rx": rock}
    m["spine_01"] = {"ry": round(a1 * 0.6, 3), "rx": P["lean"] + P["lean_amp"] * c(p, P["lean_phase"]),
                     "rz": -P["chest_yaw"] * 0.4 * c(p, P["arm_phase"])}
    m["spine_02"] = {"ry": round(a1 * 0.4, 3), "rx": P["lean_amp"] * 0.5 * c(p, P["lean_phase"] + 0.03),
                     "rz": -P["chest_yaw"] * 0.6 * c(p, P["arm_phase"] + 0.03)}
    m["spine_03"] = {"ry": round(a3 * 0.5, 3), "rz": -P["chest_yaw"] * 0.3 * c(p, P["arm_phase"] + 0.06)}
    # head level, looking ahead (counter the chest yaw), tilting a little into the sway
    m["neck"] = {"rz": P["chest_yaw"] * 0.6 * c(p, P["arm_phase"] + 0.08), "rx": -P["lean_amp"] * 0.5 * c(p, P["lean_phase"] + 0.06),
                 "ry": round(a3 * 0.5, 3) - P["head_tilt"] * 0.4 * c(p, P["x_head"][1] + 0.5)}
    m["head"] = {"rz": P["chest_yaw"] * 0.5 * c(p, P["arm_phase"] + 0.1) + P["head_yaw"] * s(p, 0.1),
                 "rx": -P["lean_amp"] * 0.4 * c(p, P["lean_phase"] + 0.1) + P["nod"] * c(2 * p, 0.05),
                 "ry": -P["head_tilt"] * 0.6 * c(p, P["x_head"][1] + 0.54)}
    # arms swing alternately (left forward at p = 0), forearms and hands follow through (phase lag)
    for side, sg in (("l", 1.0), ("r", -1.0)):
        ph = P["arm_phase"] + (0.0 if side == "l" else 0.5)       # c(p, ph) = 1: this arm fully forward
        m[f"shoulder_{side}"] = {"ry": sg * P["shrug"] * c(p, ph + 0.02), "rz": -P["shoulder_yaw"] * c(p, ph + 0.02)}
        m[f"upper_arm_{side}"] = {"side": P["up_mean_" + side] - P["up_swing"] * c(p, ph),
                                  "front": sg * P["arm_out"] * (0.5 + 0.5 * c(2 * p, 2 * ph))}
        m[f"forearm_{side}"] = {"side": P["fore_mean_" + side] - P["fore_swing"] * c(p, ph + P["fore_lag"]),
                                "front": sg * P["fore_in"] * (0.5 + 0.5 * c(p, ph + P["fore_lag"]))}
        m[f"hand_{side}"] = {"side": -P["hand_swing"] * c(p, ph + P["hand_lag"]),
                             "twist": sg * P["hand_twist"] * s(p, ph + P["hand_lag"])}
    # six hair snakes: trail back, each with its own delay and amplitude (never in unison)
    for i, (name, ph, amp) in enumerate(P["hair"]):
        sd = 1.0 if name.startswith("hair_l") else -1.0
        m[name] = {"rz": sd * P["hair_trail"] + amp * s(p, ph), "ry": amp * 0.6 * c(p, ph + 0.2),
                   "rx": amp * 0.5 * s(2 * p, ph)}
    ry = tail_ry + [0.0] * 10
    rx = [0.0, 0.0, 0.0, -rock] + [0.0] * 10
    # ground tail: travelling wave in heading (deg), runs from the hips to the tip
    hs = {}
    for i in range(1, 15):
        if i < P["wave_start"]: hs[i] = 0.0; continue
        j = i - P["wave_start"]
        amp = P["wave_amp"] * min(1.0, (j + 1) / P["ramp"]) * (P["amp_taper"] ** j)
        hs[i] = amp * s(p - j / P["links_per_wave"] + P["wave_phase"])
    rz = [-(hs[i] - hs.get(i - 1, 0.0)) for i in range(1, 15)]
    return d, m, {"ry": ry, "rz": rz, "rx": rx}

AIM = ("front", "side", "twist")
def pose(p):
    d, m, ch = motion(p)
    q = copy.deepcopy(NAT); q.pop("_note", None)
    q["root"] = {"loc": [round(d, 4), 0, 0], "ground": "lowest"}
    q["view_offset"] = P.get("view_offset", [0, 0, 0]); q["view_scale"] = P.get("view_scale", 1.0)
    B = q["bones"]
    for b, dl in m.items():
        e = B.setdefault(b, {"space": "local_delta"})
        aim = any(k in e for k in AIM)
        for k, v in dl.items():
            if k in AIM and not aim:      # stance gives this bone no aim: express as rx/ry delta instead
                k = {"front": "ry", "side": "rx", "twist": "rz"}[k]; v = v if k != "rx" else -v
            if k in AIM or e.get("space") == "local_delta" or k in e or True:
                e[k] = round(e.get(k, 0.0) + v, 2)
    # hands are aim-form (absolute): keep the stance's wrist bend relative to the forearm, plus the follow-through term
    for sd in ("l", "r"):
        nh, nf = NAT["bones"][f"hand_{sd}"], NAT["bones"][f"forearm_{sd}"]
        h, f = B[f"hand_{sd}"], B[f"forearm_{sd}"]
        for k in ("front", "side"):
            h[k] = round(f[k] + (nh[k] - nf[k]) + m[f"hand_{sd}"].get(k, 0.0), 2)
    nc = q["chain"]
    for key in ("rx", "ry", "rz"):
        base = list(nc.get(key, [])) + [0.0] * (14 - len(nc.get(key, [])))
        if key == "rz":   # animfix2 2026-11-23: fade the stance's floor-tail J-curl so the wave runs on the travel axis
            fade = P.get("stance_tail_fade", 0.0)
            base = [b * (1.0 - fade) if i >= P.get("fade_from", 4) else b for i, b in enumerate(base)]
        nc[key] = [round(base[i] + ch[key][i], 2) for i in range(14)]
    return q

for i in range(n):
    p = i / n
    f = os.path.join(out, f"k{i}.json"); json.dump(pose(p), open(f, "w"), indent=1)
print(out)
