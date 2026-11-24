"""[clipfix2_hercules v4, 2026-11-23: idle alive FROM BEHIND: pelvis shift 7.5 cm, left knee softens (heel lifts),
shoulders counter-tilt, breath raises the shoulders/upper back, look left ~38 deg (head+neck+chest), sword re-grip
(blade turns ~25 cm at the tip), shield arm settles once. Amplitudes in A below.]
[animfix_hercules v3, 2026-11-23: + continuous head/neck drift (yaw P 6.0 + 3.0 s, pitch P 2.0 + 6.0 s, never
still), bigger breath (spine_02 4.5 deg, shoulders 6), shield-arm drift lagging the breath, sword-wrist roll;
left arm comes from natural_pose.json v2]
Generate the hercules idle (video idle_n) key poses: natural stance + layered, phase-offset deltas.

Every key pose = art_src/chars/hercules/natural_pose.json with deltas added (stance merged into every key).
Layers (all zero at t=0 and t=L, so the loop starts and ends on the natural stance):
  B  breath, 2 per loop (3.0 s each)           -> chest/shoulders/arms/shield/head, lagged down the arms
  W  weight shift onto the LEFT leg and back    -> hips, legs, spine counter, shoulders, sword sway
  H  head looks to his left and back             -> head, neck, spine_03 (chest follows late)
  N  small nod when the head comes back to centre
  G  right-hand grip flex (twice)
  S  slow pendulum of the sword hand (one cycle)
Usage: python3 gen.py <out_dir> [--every 0.25]
"""
import json, math, os, sys, copy

REPO = os.path.expanduser('~/HerculesGame')
L = 6.0
A = dict(shift=0.075, look=1.0, breath=1.0, regrip=1.0, settle=1.0, kt=-8.0, ks=7.5, kf=7.0)
NAT = json.load(open(f'{REPO}/art_src/chars/hercules/natural_pose.json'))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def bump(t, a, b, c, d):
    t = t % L
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return smooth((t - a) / (b - a))
    if t <= c:
        return 1.0
    return 1.0 - smooth((t - c) / (d - c))


def B(t):            # breath 0..1, two per loop, inhale peaks at 1.5 and 4.5
    return 0.5 - 0.5 * math.cos(2 * math.pi * 2 * t / L)


def W(t):            # sway over the right leg (video: ~4.0-5.0 s => clip 3.5-4.5)
    return bump(t, 2.3, 3.6, 4.3, 5.6)


def H(t):            # head look left
    return bump(t, 3.5, 4.4, 4.9, 5.6)


def N(t):            # nod as the head comes back
    return bump(t, 5.2, 5.5, 5.55, 5.95)


def G(t):            # grip flex
    return bump(t, 1.4, 1.65, 1.75, 2.1) + 0.7 * bump(t, 5.0, 5.2, 5.3, 5.6)


def S(t):            # sword pendulum
    return -(math.sin(2 * math.pi * t / L) + 0.35 * math.sin(2 * math.pi * 3 * t / L))


def Z(fn, t, lag):     # lagged layer, pinned to 0 at t=0 (and t=L): the loop starts exactly on the stance
    return fn(t - lag) - fn(-lag)


def D1(t):           # slow head yaw drift: one 6 s cycle + a 3 s harmonic (never holds still)
    return math.sin(2 * math.pi * t / L) + 0.45 * math.sin(2 * math.pi * 2 * t / L + 1.1) - 0.45 * math.sin(1.1)


def D2(t):           # head pitch drift: 2.0 s cycle + 6 s cycle, other phase than the yaw
    return 0.6 * math.sin(2 * math.pi * 3 * t / L) + 0.7 * math.sin(2 * math.pi * t / L + 2.0) - 0.7 * math.sin(2.0)


def AD(t):           # shield-arm drift: 3 s cycle (with the breath, 0.6 s late) + 6 s sway
    return math.sin(2 * math.pi * 2 * t / L) + 0.5 * math.sin(2 * math.pi * t / L + 0.7) - 0.5 * math.sin(0.7)


def ST(t):           # shield-arm settle: hitch up/out and back down once (after the first breath)
    return bump(t, 2.3, 2.75, 2.85, 3.5)


def GO(t):           # sword fingers loosen just before the hand turns, close as it comes back
    return G(t + 0.12)


def pose_at(t):
    p = copy.deepcopy(NAT)
    bones = p['bones']
    k = A['shift'] / 0.045          # v3 leg angles were solved for a 4.5 cm pelvis shift
    lk, br, rg, sa = A['look'], A['breath'], A['regrip'], A['settle']

    def add(bone, **kw):
        e = bones.setdefault(bone, {'space': 'local_delta'})
        for kk, v in kw.items():
            e[kk] = round(e.get(kk, 0.0) + v, 3)

    b, bs, ba, bh = B(t), Z(B, t, 0.15), Z(B, t, 0.3), Z(B, t, 0.45)
    w, wl, wa, ws = W(t), Z(W, t, 0.2), Z(W, t, 0.35), Z(W, t, 0.5)
    h, hc, hb = H(t), Z(H, t, 0.3), Z(H, t, 0.45)
    n, g, s = N(t), G(t), Z(S, t, 0.2)
    go, st, stl = GO(t), ST(t), Z(ST, t, 0.15)

    # --- root + hips: pelvis sways over the RIGHT leg (video), left hip drops, left knee softens (heel lifts)
    p['root'] = {'loc': [round(-A['shift'] * w, 4), 0.0, 0.0], 'ground': 'lowest'}
    add('hips', ry=8.0 * w, rz=-4.0 * w, rx=0.6 * b)
    add('thigh_l', ry=-4.2 * k * w, rx=A['kt'] * w)
    add('shin_l', ry=-4.2 * k * w, rx=A['ks'] * w)
    add('foot_l', rx=A['kf'] * w)
    add('thigh_r', ry=-3.9 * k * w, rx=1.0 * w)
    add('shin_r', ry=-3.9 * k * w, rx=-1.5 * w)

    # --- spine: breath straightens/lifts the chest; counter-tilt over the standing leg; chest follows the look
    add('spine_01', rx=-1.0 * b * br, ry=-5.0 * wl, rz=2.5 * wl)
    add('spine_02', rx=-4.6 * b * br, ry=-5.0 * wl, rz=1.0 * wl + 4.0 * hb * lk)
    add('spine_03', rx=-2.2 * b * br, rz=7.0 * hc * lk, ry=-1.5 * wl)
    add('neck', rx=3.0 * bh + 2.0 * n + 0.5 * Z(D2, t, 0.15), rz=8.0 * h * lk - 2.2 * Z(D1, t, 0.2), ry=1.5 * wl)
    add('head', rx=2.4 * bh + 5.0 * n + 1.0 * D2(t), rz=13.0 * h * lk - 4.5 * D1(t), ry=-3.0 * h - 1.0 * wl)

    # --- shoulders: shrug with each breath (seen from behind), tilt against the hips in the shift
    add('shoulder_l', ry=-10.0 * bs * br - 4.0 * wl)
    add('shoulder_r', ry=9.0 * bs * br - 4.0 * wl)

    # --- shield arm: rises with the breath, opens as the weight comes over, one settle (hitch out/up, back down)
    ua = bones['upper_arm_l']
    ad = Z(AD, t, 0.6)
    ua['front'] = round(ua['front'] - 2.0 * ba + 2.0 * wa - 2.0 * ad - 4.0 * st * sa, 3)
    ua['side'] = round(ua['side'] - 1.5 * ba + 3.0 * ad - 3.0 * st * sa, 3)
    fa = bones['forearm_l']
    fa['side'] = round(fa['side'] - 5.0 * ba - 3.0 * Z(AD, t, 0.8) - 8.0 * stl * sa, 3)
    fa['front'] = round(fa['front'] - 1.5 * wa - 2.0 * stl * sa, 3)
    add('hand_l', rx=4.0 * ba + 5.0 * Z(ST, t, 0.3) * sa, ry=-2.0 * ws)
    add('fingers_l', rx=7.0 * bh)

    # --- sword arm: breath, pendulum, follows the shift late; re-grip: fingers loosen, wrist turns the blade, close
    ur = bones['upper_arm_r']
    ur['front'] = round(ur['front'] + 1.5 * ba + 3.0 * wa, 3)
    ur['side'] = round(ur['side'] + 2.5 * s, 3)
    fr = bones['forearm_r']
    fr['front'] = round(fr['front'] + 1.0 * ba - 4.5 * ws, 3)
    fr['side'] = round(fr['side'] + 5.0 * Z(S, t, 0.35) - 4.0 * g * rg, 3)
    add('hand_r', rx=4.0 * Z(S, t, 0.5) - 16.0 * g * rg, ry=3.0 * ws + 4.0 * g * rg,
        rz=4.0 * math.sin(2 * math.pi * 2 * t / L + 0.4) - 4.0 * math.sin(0.4) + 12.0 * g * rg)
    add('fingers_r', rx=8.0 * g - 14.0 * go * rg)
    return p


def main():
    out = sys.argv[1]
    if '--A' in sys.argv:
        A.update(json.loads(sys.argv[sys.argv.index('--A') + 1]))
    every = float(sys.argv[sys.argv.index('--every') + 1]) if '--every' in sys.argv else 0.25
    os.makedirs(f'{out}/poses_idle', exist_ok=True)
    keys = []
    n = int(round(L / every))
    for i in range(n):
        t = round(i * every, 4)
        name = f'poses_idle/k{i:02d}.json'
        json.dump(pose_at(t), open(f'{out}/{name}', 'w'), indent=1)
        keys.append({'t': t, 'pose_file': name})
    json.dump({'fps': 24, 'loop': True, 'length': L, 'events': {}, 'keys': keys},
              open(f'{out}/keys_idle.json', 'w'), indent=1)
    print(len(keys), 'keys')


if __name__ == '__main__':
    main()
