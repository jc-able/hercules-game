# Pose generator for the hydra bite (all local_delta). python3 gen.py <params.json> <outdir>
import json, sys, os, math
P = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
SIDE_R = ["neck_1", "neck_2", "neck_3", "neck_4"]; SIDE_L = ["neck_8", "neck_7", "neck_6", "neck_5"]
# side-plane joints (y, z) from rig.json
SP = [(2.6, 5.0), (1.0, 5.1), (-0.5, 5.25)]       # spine_01/02/03 heads
SH = (-1.55, 4.7); EL = (-1.4, 2.6); WR = (-1.5, 1.0)  # front leg shoulder, elbow, wrist
def rot(p, c, a):  # clockwise by a deg in the side panel (character faces screen right = -Y)
    u, z = -(p[0]-c[0]), p[1]-c[1]; r = math.radians(a)
    u2 = u*math.cos(r) + z*math.sin(r); z2 = -u*math.sin(r) + z*math.cos(r)
    return (c[0]-u2, c[1]+z2)
def ang(v):  # clockwise angle of a vector from straight down, side panel
    return math.degrees(math.atan2(v[0], -v[1]))
def leg_ik(sp):  # sp = [rx spine_01, 02, 03] -> (l1, l2, l3) keeping wrist + foot fixed, elbow behind
    sh = SH
    for i in range(3):
        c = SP[i]
        for j in range(i): c = rot(c, SP[j], sp[j])
    # rotate shoulder by each spine joint in order (each about its own current pivot)
    pts = [SP[0], SP[1], SP[2], SH]
    for i in range(3):
        piv = pts[i]
        pts = pts[:i+1] + [rot(p, piv, sp[i]) for p in pts[i+1:]]
    sh = pts[3]; S = sum(sp)
    a = math.dist(SH, EL); b = math.dist(EL, WR); d = math.dist(sh, WR)
    d = min(d, a+b-1e-6)
    base = ang((WR[0]-sh[0], WR[1]-sh[1]))
    alpha = math.degrees(math.acos((a*a + d*d - b*b)/(2*a*d)))
    # elbow behind (toward +Y, screen left): upper bone angle = base - alpha (counter-clockwise)
    up_w = base + alpha
    el = (sh[0] + a*math.sin(math.radians(up_w)), sh[1] - a*math.cos(math.radians(up_w)))
    lo_w = ang((WR[0]-el[0], WR[1]-el[1]))
    up_r = ang((EL[0]-SH[0], EL[1]-SH[1])); lo_r = ang((WR[0]-EL[0], WR[1]-EL[1]))
    l1 = (up_w - up_r) - S; l2 = (lo_w - lo_r) - (up_w - up_r); l3 = -(S + l1 + l2)
    return l1, l2, l3
def pose(k):
    bones = {}
    sp = k.get("spine", [0, 0, 0])
    for n, v in zip(["spine_01", "spine_02", "spine_03"], sp):
        if v: bones[n] = {"rx": v}
    if any(sp):
        l1, l2, l3 = leg_ik(sp)
        for s in ("fl", "fr"):
            bones[f"leg_{s}_01"] = {"rx": round(l1, 2)}; bones[f"leg_{s}_02"] = {"rx": round(l2, 2)}; bones[f"leg_{s}_03"] = {"rx": round(l3, 2)}
    for b, v in k.get("bones", {}).items(): bones[b] = v
    chains = []
    nc = k.get("neck_c", {})
    NC = ["neck_c_01", "neck_c_02", "neck_c_03", "neck_c_04", "neck_c_05", "head_c", "jaw_c"]
    for i, n in enumerate(NC):
        u = nc.get("up", [0]*7)[i]; sd = nc.get("side", [0]*7)[i]
        if u or sd: bones[n] = {"rx": u, "ry": sd}
    # side necks keep their own lean against the spine bow: comp = fraction of the spine bend undone at link 1
    comp = k.get("comp", 0.0) * sum(sp)
    spl = k.get("splay", [0, 0, 0, 0]); sup = k.get("side_up", [0, 0, 0, 0]); ph = k.get("phase", [1, 1, 1, 1])
    prof = [1.0, 1.0, 0.8, 0.6, 0.3]
    for i, (r, l) in enumerate(zip(SIDE_R, SIDE_L)):
        s = spl[i]; u = sup[i]
        if not (s or u or comp): continue
        for nm, sg, f in ((r, -1, 1.0), (l, 1, ph[i])):
            for j in range(5):
                bn = f"{nm}_0{j+1}" if j < 4 else f"head_{nm[-1]}"
                e = {}
                # view axes: ry + = clockwise in the front panel; character's right side (screen left) splays out with ry +
                if s: e["ry"] = round(sg * s * prof[j] * f, 2)
                rxv = u * prof[j] * f - (comp if j == 0 else 0)
                if rxv: e["rx"] = round(rxv, 2)
                if e: bones[bn] = e
    d = {"space": "local_delta", "root": {"loc": [0, 0, 0]},
         "view_offset": k.get("view_offset", P.get("view_offset", [0, 0, 0])), "bones": bones}
    if chains: d["chain"] = chains
    return d
if __name__ == "__main__":
    for name, k in P["keys"].items():
        json.dump(pose(k), open(os.path.join(out, name + ".json"), "w"), indent=1)
    print("ok", list(P["keys"]), "ik(10,12,25)=", [round(x, 2) for x in leg_ik([10, 12, 25])])
