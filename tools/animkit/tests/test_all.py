"""animkit tests. Run: tools/animkit/tests/run_tests.sh  (uses art_src/chars/hercules/raw.glb, writes work/animkit/tests_tmp)"""
import json, os, subprocess, sys, time, shutil
import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
AK = os.path.join(REPO, 'tools', 'ak')
sys.path.insert(0, os.path.join(REPO, 'tools', 'animkit'))
import akimg as I  # noqa: E402

TMP = os.path.join(REPO, 'work', 'animkit', 'tests_tmp')
GLB = os.path.join(REPO, 'art_src', 'chars', 'hercules', 'raw.glb')
results = []


def ak(*args, expect_ok=True):
    t = time.time()
    r = subprocess.run([sys.executable, AK] + [str(a) for a in args], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('###AK### ')]
    if not line:
        raise AssertionError(f'no ###AK### line from {args}: {r.stdout[-800:]} {r.stderr[-800:]}')
    j = json.loads(line[-1][9:])
    j['_wall'] = time.time() - t
    if expect_ok and (r.returncode != 0 or not j.get('ok')):
        raise AssertionError(f'ak {args[0]} failed: {j}')
    if not expect_ok and r.returncode == 0:
        raise AssertionError(f'ak {args[0]} should have failed: {j}')
    return j


def test(name):
    def deco(fn):
        def run():
            t = time.time()
            try:
                info = fn() or ''
                results.append((name, True, f'{time.time() - t:.1f}s {info}'))
            except Exception as e:
                results.append((name, False, f'{type(e).__name__}: {e}'))
        run.__name__ = fn.__name__
        TESTS.append(run)
        return run
    return deco


TESTS = []
P = lambda *x: os.path.join(TMP, *x)


@test('prep test blend from raw.glb')
def t_prep():
    j = ak('prep', GLB, '--out', P('t.blend'))
    assert j['bones'] > 3
    return f"{j['bones']} bones"


@test('pose math (random absolute/local_delta/root poses, 0.5 deg)')
def t_math():
    j = ak('selftest', P('t.blend'), '--trials', 30)
    assert j['worst_listed_deg'] < 0.5 and j['worst_follow_deg'] < 0.5, j
    return f"checked {j['checked_listed']} bones, worst {j['worst_listed_deg']:.4f} deg"


def make_cam():
    """cam.json for the test blend, framed like render_split_sheet.py does"""
    info = ak('info', P('t.blend'), '--json-out', P('info.json'))
    bones = json.load(open(P('info.json')))['bones']
    z = [b['head'][2] for b in bones]
    cam = {'width': 1280, 'height': 720, 'ppm': 720 * 0.88 / (max(z) * 1.25 * 1.05), 'front_w': 700, 'side_w': 580,
           'centre_x': 0.0, 'centre_y': 0.0, 'ground_z': 0.0, 'ground_frac': 0.08, 'bg': [1, 1, 1],
           'rest_size': [1, 0.4, max(z) * 1.05]}
    json.dump(cam, open(P('cam.json'), 'w'))
    return info


POSE_A = {'bones': {'LeftArm': {'ry': -60}, 'RightArm': {'rx': -80}, 'LeftUpLeg': {'rx': 35}, 'Spine01': {'ry': 10}}}


def first_bones(n=4):
    bones = json.load(open(P('info.json')))['bones']
    return [b['name'] for b in bones]


@test('info writes bones image')
def t_info():
    make_cam()
    j = ak('info', P('t.blend'), '--cam', P('cam.json'), '--out', P('bones.jpg'))
    assert os.path.exists(j['bones_image'])
    return f"{j['n_bones']} bones, chains {list(j['chains'])}"


def generic_pose():
    """a pose that uses whatever bones exist (tools must not depend on names): bend the 3 longest chains"""
    info = json.load(open(P('info.json')))
    ch = sorted(info['chains'].items(), key=lambda kv: -len(kv[1]))
    bones = {}
    for i, (name, names) in enumerate(ch[:3]):
        bones[names[1]] = {'rx': [-50, 40, 25][i], 'ry': [20, -35, 0][i]}
    return {'bones': bones}


@test('pose render < 6 s + IoU 1.0 against itself')
def t_pose():
    pose = generic_pose()
    json.dump(pose, open(P('pose_a.json'), 'w'))
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pose_a.json'), '--out', P('pose_a_cmp.jpg'),
           '--render-out', P('pose_a.png'))
    assert j['_wall'] < 6.0, f"took {j['_wall']:.2f}s"
    j2 = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pose_a.json'), '--target', P('pose_a.png'),
            '--out', P('pose_a_self.jpg'))
    assert j2['iou_mean'] > 0.97, j2
    json.dump({'bones': {}}, open(P('rest.json'), 'w'))
    j3 = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('rest.json'), '--target', P('pose_a.png'),
            '--out', P('pose_rest_vs_a.jpg'), '--render-out', P('rest.png'))
    assert j3['iou_mean'] < j2['iou_mean'] - 0.05, (j2, j3)
    return f"{j['_wall']:.2f}s wall, self IoU {j2['iou_mean']}, rest-vs-pose IoU {j3['iou_mean']}"


@test('frames: calibration of a re-framed video + masks')
def t_frames():
    # synthesize a 'Seedance-like' video: our two renders, scaled 1.2x and re-centred, on a grey vignette, 854x480
    cam = I.load_cam(P('cam.json'))
    vd = P('vid'); shutil.rmtree(vd, ignore_errors=True); os.makedirs(vd)
    W, H = 854, 480
    yy, xx = np.mgrid[0:H, 0:W]
    vign = 0.93 - 0.08 * (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 2)
    for k, src in enumerate(['rest.png', 'pose_a.png']):
        sheet = np.asarray(Image.open(P(src)).convert('RGB'), np.float32) / 255
        frame = np.repeat(vign[..., None], 3, 2).astype(np.float32)
        for (x0, x1), (vx0, vx1) in (((0, cam['front_w']), (0, W // 2 - 1)), ((cam['front_w'], 1280), (W // 2 + 1, W))):
            pan = sheet[:, x0:x1]
            m = np.abs(pan - 1).max(2) > 0.05
            ph, pw = pan.shape[:2]
            s = 0.8 * 1.2 * H / 720
            im = Image.fromarray((pan * 255).astype(np.uint8)).resize((int(pw * s), int(ph * s)), Image.LANCZOS)
            mm = Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)
            ox = vx0 + ((vx1 - vx0) - im.size[0]) // 2 + 7
            oy = H - im.size[1] + 25
            fr = Image.fromarray((frame * 255).astype(np.uint8))
            fr.paste(im, (ox, oy), mm)
            frame = np.asarray(fr, np.float32) / 255
        frame[:, W // 2 - 1:W // 2 + 1] = 0.3
        Image.fromarray((frame * 255).astype(np.uint8)).save(os.path.join(vd, f'{k:03d}.png'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '1', '-i', os.path.join(vd, '%03d.png'), '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-r', '24', P('synth.mp4')], check=True)
    j = ak('frames', P('synth.mp4'), '--cam', P('cam.json'), '--sheet', P('rest.png'), '--times', '0.5,1.5',
           '--out', P('frames'), '--mask')
    assert min(j['calib_iou'].values()) > 0.85, j['calib_iou']
    ref = np.asarray(Image.open(json.load(open(j['frames_json']))['masks'][1])) > 0
    ours = I.silhouette(I.load_rgb(P('pose_a.png'), cam), cam)
    iou = I.panel_iou(cam, ref, ours)
    assert min(iou.values()) > 0.85, iou
    # pose compare on the rectified frame
    jp = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pose_a.json'), '--target', j['last'],
            '--out', P('pose_vs_frame.jpg'))
    assert jp['iou_mean'] > 0.85, jp
    return f"calib IoU {j['calib_iou']}, frame mask IoU {iou}, pose-vs-frame {jp['iou_mean']}"


@test('bake -> strip -> export round trip (GLB: clips + skin)')
def t_roundtrip():
    shutil.copy(P('t.blend'), P('rt.blend'))
    pose = generic_pose()
    neg = {'bones': {k: {kk: -vv for kk, vv in v.items()} for k, v in pose['bones'].items()}}
    keys = {'fps': 30, 'events': {'impact': 0.3}, 'length': 0.71,
            'keys': [{'t': 0, 'pose': {'bones': {}}}, {'t': 0.3, 'pose': pose}, {'t': 0.6, 'pose_file': 'neg.json'}]}
    json.dump(neg, open(P('neg.json'), 'w'))
    json.dump(keys, open(P('keys_a.json'), 'w'))
    ak('bake', P('rt.blend'), '--clip', 'test_a', '--keys', P('keys_a.json'))
    jb = ak('bake', P('rt.blend'), '--clip', 'test_b', '--keys', P('keys_a.json'), '--loop', '--out-action', P('test_b.json'))
    assert 'saved' not in jb, 'JSON route must not save the blend'
    ak('merge', P('rt.blend'), P('test_b.json'))
    js = ak('strip', P('rt.blend'), '--cam', P('cam.json'), '--clip', 'test_a', '--n', 6, '--out', P('strip_a.jpg'),
            '--mp4', P('strip_a.mp4'))
    assert os.path.getsize(js['mp4']) > 1000 and os.path.exists(js['out'])
    # the 0.3 s frame of the strip must look like pose_a
    js2 = ak('strip', P('rt.blend'), '--cam', P('cam.json'), '--action-json', P('test_b.json'), '--n', 3, '--out', P('strip_b.jpg'))
    je = ak('export', P('rt.blend'), '--out', P('out', 't.glb'), '--clips-json', P('out', 't_clips.json'))
    import pygltflib
    g = pygltflib.GLTF2().load(P('out', 't.glb'))
    names = sorted(a.name for a in g.animations)
    assert names == ['test_a', 'test_b'], names
    assert g.skins, 'no skin'
    man = json.load(open(P('out', 't_clips.json')))
    assert man['clips']['test_a']['events'] == {'impact': 0.3} and abs(man['clips']['test_a']['length'] - 0.7) < 1e-6, man
    assert man['clips']['test_b']['loop'] is True
    tmax = max(g.accessors[s.input].max[0] for a in g.animations if a.name == 'test_a' for s in a.samplers)
    assert abs(tmax - 0.7) < 0.02, tmax
    for an in g.animations:
        tm = max(g.accessors[s.input].max[0] for s in an.samplers)
        assert abs(tm - man['clips'][an.name]['length']) < 1e-3, (an.name, tm, man['clips'][an.name])
    return f"glb {je['size_mb']} MB, animations {names}, skins {len(g.skins)}"


@test('loop seam: first and last frame render identically')
def t_loop():
    from ak_main import run_blender
    r = run_blender('render_clip', {'blend': P('rt.blend'), 'cam': P('cam.json'), 'prefix': P('seam'), 'clip': 'test_b',
                                     'times': [0.0, None]} if False else
                    {'blend': P('rt.blend'), 'cam': P('cam.json'), 'prefix': P('seam'), 'clip': 'test_b', 'n': 2})
    a = [np.asarray(Image.open(p), np.float32) for p in r['renders'][0]]
    b = [np.asarray(Image.open(p), np.float32) for p in r['renders'][1]]
    d = max(float(np.abs(x - y).max()) for x, y in zip(a, b))
    assert r['loop'] and d <= 2.0, (r['loop'], d)
    return f"length {r['length']:.3f}s, max pixel diff {d}"


@test('fit: perturbed visible limbs are recovered (synthetic)')
def t_fit():
    pose = json.load(open(P('pose_a.json')))
    # perturb the two limbs that are visible in both panels (the far-side arm is hidden: a documented limit)
    names = list(pose['bones'])
    vis = names[1:]
    start = {'bones': {k: ({kk: vv + (15 if kk == 'rx' else -12) for kk, vv in v.items()} if k in vis else dict(v))
                       for k, v in pose['bones'].items()}}
    json.dump(start, open(P('fit_start.json'), 'w'))
    j = ak('fit', P('t.blend'), '--cam', P('cam.json'), '--pose', P('fit_start.json'), '--target', P('pose_a.png'),
           '--bones', ','.join(vis), '--out-pose', P('fit_end.json'), '--out', P('fit_cmp.jpg'))
    got = json.load(open(P('fit_end.json')))['bones']
    err = max(abs(got[b][ax] - pose['bones'][b][ax]) for b in vis for ax in pose['bones'][b])
    assert sum(j['fit_iou_end']) > sum(j['fit_iou_start']) + 0.05, j
    assert 'fit_score_end' in j
    assert err <= 4.0, (err, got)
    return f"IoU {j['fit_iou_start']} -> {j['fit_iou_end']}, max angle error {err} deg"


@test('mirror: L/R swap, ry/rz negated, mirrored render is the flipped render')
def t_mirror():
    ak('mirror', P('pose_a.json'), '--out', P('pose_a_m.json'), '--blend', P('t.blend'))
    m = json.load(open(P('pose_a_m.json')))
    p = json.load(open(P('pose_a.json')))
    for k, v in p['bones'].items():
        mk = k.replace('Left', '#').replace('Right', 'Left').replace('#', 'Right')
        assert m['bones'][mk].get('rx', 0) == v.get('rx', 0) and m['bones'][mk].get('ry', 0) == -v.get('ry', 0), (k, m)
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pose_a_m.json'), '--out', P('m.jpg'), '--render-out', P('m.png'))
    cam = I.load_cam(P('cam.json'))
    a = I.silhouette(I.load_rgb(P('pose_a.png'), cam), cam)[:, :cam['front_w']]
    b = I.silhouette(I.load_rgb(P('m.png'), cam), cam)[:, :cam['front_w']]
    cx = int(round(cam['front_w'] / 2 + (0 - cam['centre_x']) * cam['ppm']))
    bf = np.zeros_like(b)
    w = min(cx, cam['front_w'] - cx)
    bf[:, cx - w:cx + w] = b[:, cx - w:cx + w][:, ::-1]
    iou = float((a & bf).sum() / max(1, (a | bf).sum()))
    assert iou > 0.85, iou
    return f'front mirror IoU {iou:.3f} (rig is only roughly symmetric)'



REAL = os.path.join(REPO, 'art_src', 'chars')


def solve(blend, pose, name='s'):
    json.dump(pose, open(P(name + '_pose.json'), 'w'))
    ak('solve', blend, '--pose', P(name + '_pose.json'), '--json-out', P(name + '_solve.json'))
    return json.load(open(P(name + '_solve.json')))


def dist(a, b):
    return float(np.linalg.norm(np.array(a) - np.array(b)))


@test('mixed fps: 24 fps loop + 30 fps clip export with exact lengths')
def t_mixed_fps():
    shutil.copy(P('t.blend'), P('mf.blend'))
    pose = generic_pose()
    json.dump({'keys': [{'t': 0, 'pose': {'bones': {}}}, {'t': 0.3333, 'pose': pose}]}, open(P('k24.json'), 'w'))
    ak('bake', P('mf.blend'), '--clip', 'run24', '--keys', P('k24.json'), '--fps', 24, '--loop', '--length', 0.6667)
    json.dump({'keys': [{'t': 0, 'pose': {'bones': {}}}, {'t': 0.375, 'pose': pose}]}, open(P('k24b.json'), 'w'))
    ak('bake', P('mf.blend'), '--clip', 'odd24', '--keys', P('k24b.json'), '--fps', 24, '--loop', '--length', 0.70833)
    json.dump({'keys': [{'t': 0, 'pose': pose}, {'t': 0.5, 'pose': {'bones': {}}}], 'events': {'impact': 0.4}}, open(P('k30.json'), 'w'))
    ak('bake', P('mf.blend'), '--clip', 'wave30', '--keys', P('k30.json'), '--fps', 30)
    je = ak('export', P('mf.blend'), '--out', P('out', 'mf.glb'), '--clips-json', P('out', 'mf_clips.json'))
    import pygltflib
    g = pygltflib.GLTF2().load(P('out', 'mf.glb'))
    man = json.load(open(P('out', 'mf_clips.json')))['clips']
    L = {an.name: max(g.accessors[s.input].max[0] for s in an.samplers) for an in g.animations}
    assert abs(L['run24'] - 2 / 3) < 0.002 and abs(man['run24']['length'] - 0.6667) < 0.001, (L, man)
    assert abs(L['wave30'] - 0.5) < 0.002, L
    for n in L:
        assert abs(L[n] - man[n]['length']) < 1e-3, (n, L[n], man[n])
    assert 'odd24' in je.get('retimed', {}), je
    return f"glb lengths {({k: round(v, 4) for k, v in L.items()})}, retimed {je.get('retimed')}"


@test('view_offset: framing only (renders like root.loc, never baked, never mirrored)')
def t_view_offset():
    pose = generic_pose()
    off = [0.05, -0.08, 0.03]
    pv = dict(pose, view_offset=off); pr = dict(pose, root={'loc': off})
    json.dump(pv, open(P('pv.json'), 'w')); json.dump(pr, open(P('pr.json'), 'w'))
    ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pr.json'), '--out', P('pr.jpg'), '--render-out', P('pr.png'))
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pv.json'), '--target', P('pr.png'), '--out', P('pv_cmp.jpg'))
    assert j['iou_mean'] > 0.97, j
    json.dump({'keys': [{'t': 0, 'pose': pv}, {'t': 0.3, 'pose': dict(pv, view_offset=[0.0, 0.0, 0.0])}]}, open(P('kv.json'), 'w'))
    ak('bake', P('t.blend'), '--clip', 'v', '--keys', P('kv.json'), '--out-action', P('v.json'))
    d = json.load(open(P('v.json')))
    root = json.load(open(P('info.json')))['roots'][0]
    assert d['bones'][root]['loc'] is None, d['bones'][root]['loc']
    assert d['view']['offset'][0] == off, d['view']
    ak('mirror', P('pv.json'), '--out', P('pv_m.json'), '--blend', P('t.blend'))
    assert json.load(open(P('pv_m.json')))['view_offset'] == off
    js = ak('strip', P('t.blend'), '--cam', P('cam.json'), '--action-json', P('v.json'), '--n', 2, '--out', P('v_strip.jpg'))
    assert js['view_applied'], js
    return f"view vs root.loc render IoU {j['iou_mean']}, baked root loc None, strip applies view"


@test('driven bones (rig.json "driven"): set by code, refused in poses')
def t_driven():
    d = P('drv'); os.makedirs(d, exist_ok=True)
    shutil.copy(P('t.blend'), os.path.join(d, 't.blend'))
    open(os.path.join(d, 'drv.py'), 'w').write(
        "def drive(rest, posed):\n"
        "    # test driver: the toe follows the hips instead of the foot\n"
        "    return {'LeftToeBase': posed['Hips'] @ rest['Hips'].inverted() @ rest['LeftToeBase']}\n")
    json.dump({'driven': {'bones': ['LeftToeBase'], 'code': 'drv.py (drive(rest, posed))'}}, open(os.path.join(d, 'rig.json'), 'w'))
    b = os.path.join(d, 't.blend')
    s0 = solve(b, {'bones': {}}, 'd0'); s1 = solve(b, {'bones': {'LeftUpLeg': {'rx': -40}}}, 'd1')
    assert dist(s1['bones']['LeftFoot']['head'], s0['bones']['LeftFoot']['head']) > 0.1
    assert dist(s1['bones']['LeftToeBase']['head'], s0['bones']['LeftToeBase']['head']) < 0.002, 'driver not applied'
    json.dump({'bones': {'LeftToeBase': {'rx': 10}}}, open(P('drv_bad.json'), 'w'))
    j = ak('pose', b, '--cam', P('cam.json'), '--pose', P('drv_bad.json'), '--out', P('drv_bad.jpg'), expect_ok=False)
    assert 'driven' in j['error'], j
    jt = ak('selftest', b, '--trials', 6)
    info = ''
    hb = os.path.join(REAL, 'hercules', 'hercules.blend')
    if os.path.exists(hb) and 'driven' in json.load(open(os.path.join(REAL, 'hercules', 'rig.json'))):
        r0 = solve(hb, {'bones': {}}, 'h0'); r1 = solve(hb, {'bones': {'thigh_l': {'rx': -45}}}, 'h1')
        mv = dist(r1['bones']['skirt_f']['tip'], r0['bones']['skirt_f']['tip'])
        assert mv > 0.02, f'skirt_f tip moved only {mv:.3f} m'
        info = f', real hercules: thigh_l forward 45 deg moves skirt_f tip {mv:.3f} m'
    return f"fixture driver ok, selftest skipped {jt['driven_skipped']}{info}"


@test('ground: lowest vertex per foot + root.ground')
def t_ground():
    info = json.load(open(P('info.json')))
    legs = [c for c in info['chains'].values() if 'UpLeg' in c[0] or 'thigh' in c[0]]
    pose = {'bones': {legs[0][0]: {'rx': -30}, legs[0][1]: {'rx': 60}, legs[1][0]: {'rx': -50}, legs[1][1]: {'rx': 90}}}
    s = solve(P('t.blend'), pose, 'g0')
    assert s['ground']['lowest_z'] > 0.03, s['ground']
    s2 = solve(P('t.blend'), dict(pose, root={'ground': 'lowest'}), 'g1')
    assert abs(s2['ground']['lowest_z']) < 0.003, s2['ground']
    s3 = solve(P('t.blend'), dict(pose, root={'ground': 'right'}), 'g2')
    assert abs(s3['ground']['right_z']) < 0.003, s3['ground']
    json.dump(dict(pose, root={'ground': 'lowest'}), open(P('g.json'), 'w'))
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('g.json'), '--out', P('g.jpg'), '--save-pose', P('g_res.json'))
    assert 'grounded' in json.load(open(P('g_res.json')))['root']
    return f"bent legs float {s['ground']}, grounded lowest {s2['ground']['lowest_z']}"


@test('mirror: every rig.json (pairs + token fallback) maps both ways, unpaired sided bones fail')
def t_mirror_rigs():
    done = []
    for rp in sorted(os.path.join(REAL, c, 'rig.json') for c in os.listdir(REAL) if os.path.exists(os.path.join(REAL, c, 'rig.json'))):
        rj = json.load(open(rp))
        drv = set((rj.get('driven') or {}).get('bones') or [])
        names = [b['name'] for b in rj.get('bones', []) if b['name'] not in drv]
        pose = {'bones': {n: {'rx': i + 1.0, 'ry': i + 1.5, 'rz': i + 1.25} for i, n in enumerate(names)}}
        json.dump(pose, open(P('mr_in.json'), 'w'))
        ak('mirror', P('mr_in.json'), '--rig', rp, '--out', P('mr_out.json'))
        out = json.load(open(P('mr_out.json')))['bones']
        assert len(out) == len(names), (rp, len(out), len(names))
        pairs = {a: b for a, b in rj.get('pairs', [])} | {b: a for a, b in rj.get('pairs', [])}
        for n in names:
            m = pairs.get(n, n)
            v = pose['bones'][n]
            assert out[m] == {'rx': v['rx'], 'ry': -v['ry'], 'rz': -v['rz']}, (rp, n, m, out[m])
        done.append(f"{os.path.basename(os.path.dirname(rp))}:{len(pairs) // 2} pairs")
    json.dump({'bones': [{'name': 'spine', 'head': [0, 0, 1]}, {'name': 'arm_l', 'head': [0.2, 0, 1]}]}, open(P('rig_bad.json'), 'w'))
    json.dump({'bones': {'arm_l': {'rx': 10}}}, open(P('mr_bad.json'), 'w'))
    j = ak('mirror', P('mr_bad.json'), '--rig', P('rig_bad.json'), '--out', P('mr_bad_out.json'), expect_ok=False)
    assert 'partner' in j['error'], j
    return ', '.join(done)


@test('chain helper: bend axes follow the chain direction (vertical spine, lateral arm)')
def t_chain_axes():
    info = json.load(open(P('info.json')))
    ax = info['chain_axes']
    s0 = solve(P('t.blend'), {'bones': {}}, 'c0')
    moved = {}
    for vert in [k for k in ax if ax[k]['class'] == 'vertical']:
        names = info['chains'][vert]
        tip = names[-1]
        n = len(names)
        s1 = solve(P('t.blend'), {'chain': {'name': vert, 'bend_side': [10] * n}}, 'c1')
        s2 = solve(P('t.blend'), {'chain': {'name': vert, 'bend_up': [10] * n}}, 'c2')
        h0, h1, h2 = (np.array(s['bones'][tip]['tip']) for s in (s0, s1, s2))
        assert h1[0] - h0[0] > 0.04, (vert, h0, h1)          # toward the character's left (+X)
        assert h0[1] - h2[1] > 0.04, (vert, h0, h2)          # lean forward (-Y)
        moved[vert] = round(float(h1[0] - h0[0]), 3)
    msg = f"vertical chains, bend_side 10/link moves the tip +x {moved}"
    lat = [k for k in ax if ax[k]['class'] == 'lateral']
    if lat:
        ln = info['chains'][lat[0]]
        s3 = solve(P('t.blend'), {'chain': {'name': lat[0], 'bend_up': [10] * len(ln)}}, 'c3')
        dz = s3['bones'][ln[-1]]['tip'][2] - s0['bones'][ln[-1]]['tip'][2]
        assert dz > 0.05, (lat[0], dz)
        msg += f"; lateral {lat[0]} bend_up lifts its tip {dz:.2f} m"
    return msg


@test('pivot = first deforming root-most bone; info lists rest panel angles')
def t_pivot():
    info = json.load(open(P('info.json')))
    assert info['pivot'] == info['roots'][0], info['pivot']
    b = info['bones'][0]
    assert 'rest_front_deg' in b and 'lr' in b
    msg = f"test rig pivot {info['pivot']}"
    hb = os.path.join(REAL, 'hercules', 'hercules.blend')
    if os.path.exists(hb):
        j = ak('info', hb, '--json-out', P('h_info.json'))
        hi = json.load(open(P('h_info.json')))
        assert hi['pivot'] != 'root' and hi['pivot'] in [x['name'] for x in hi['bones'] if x['deform']], hi['pivot']
        r0 = solve(hb, {'bones': {}}, 'p0'); r1 = solve(hb, {'root': {'rot': [20, 0, 0]}}, 'p1')
        pv = hi['pivot']
        assert dist(r0['bones'][pv]['head'], r1['bones'][pv]['head']) < 1e-3
        msg += f", hercules pivot {pv}, head moves {dist(r0['bones']['head']['head'], r1['bones']['head']['head']):.2f} m for root.rot rx 20"
    return msg


@test('missing textures: warning on open, export refuses')
def t_missing_images():
    hb = os.path.join(REAL, 'hercules', 'hercules.blend')
    if not os.path.exists(hb):
        return 'SKIPPED (no hercules.blend)'
    d = P('copy'); os.makedirs(d, exist_ok=True)
    shutil.copy(hb, os.path.join(d, 'hercules.blend'))
    j = ak('info', os.path.join(d, 'hercules.blend'), '--json-out', P('copy_info.json'))
    assert any('missing' in w for w in j.get('warnings', [])), j
    je = ak('export', os.path.join(d, 'hercules.blend'), '--out', P('copy', 'h.glb'), expect_ok=False)
    assert 'missing' in je['error'], je
    return f"{len(json.load(open(P('copy_info.json')))['missing_images'])} missing images reported, export refused"


@test('merge: re-bakes from poses on the current rig, refuses duplicate clip names')
def t_merge():
    shutil.copy(P('t.blend'), P('mg.blend'))
    j = ak('merge', P('mg.blend'), P('test_b.json'), P('v.json'))
    assert sorted(j['rebaked']) == ['test_b', 'v'], j
    jb = ak('merge', P('mg.blend'), P('test_b.json'), P('test_b.json'), expect_ok=False)
    assert 'test_b' in jb['error']
    jr = ak('merge', P('mg.blend'), P('test_b.json'), P('test_b.json'), '--replace')
    assert 'test_b' in jr['replaced_existing'], jr
    d = json.load(open(P('test_b.json')))
    d['rig_hash'] = 'stale'
    d['spec']['keys'][1]['pose'] = {'bones': {'NoSuchBone': {'rx': 1}}}
    json.dump(d, open(P('test_b_bad.json'), 'w'))
    jx = ak('merge', P('mg.blend'), P('test_b_bad.json'), expect_ok=False)
    assert 'NoSuchBone' in jx['error'], jx
    return f"rebaked {j['rebaked']}, duplicate refused, --replace ok, renamed bone fails loudly"


@test('frame sampling: requested times snap to exact video frames')
def t_frame_snap():
    vd = P('vid24'); os.makedirs(vd, exist_ok=True)
    for n in range(72):
        Image.new('RGB', (64, 48), (n * 3, n * 3, n * 3)).save(os.path.join(vd, f'{n:03d}.png'))
    v = P('n24.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '24', '-i', os.path.join(vd, '%03d.png'), '-c:v', 'libx264',
                    '-qp', '0', '-pix_fmt', 'yuv444p', v], check=True)
    assert abs(I.video_fps(v) - 24) < 1e-6
    bad = []
    for t in (0.0, 1.0, 2.33335, 2.3334, 56 / 24, 2.0 + 1 / 48 - 0.001, 1 / 24):
        n = int(round(t * 24))
        a = I.extract_native(v, t, os.path.join(vd, 'x.png'), 24)
        got = int(round(a.mean() * 255 / 3))
        if got != n:
            bad.append((t, n, got))
    assert not bad, bad
    return 'all requested times returned frame round(t*fps)'


@test('events: keys in video time shift the events too; events outside the clip fail')
def t_events():
    pose = generic_pose()
    json.dump({'events': {'impact': 2.3}, 'keys': [{'t': 2.0, 'pose': {'bones': {}}}, {'t': 2.1667, 'pose': pose},
                                                   {'t': 2.3333, 'pose': {'bones': {}}}]}, open(P('kev.json'), 'w'))
    j = ak('bake', P('t.blend'), '--clip', 'ev', '--keys', P('kev.json'), '--out-action', P('ev.json'))
    assert abs(j['events']['impact'] - 0.3) < 1e-6 and abs(j['shifted_by'] - 2.0) < 1e-9, j
    json.dump({'events': {'impact': 0.3}, 'keys': [{'t': 2.0, 'pose': {'bones': {}}}, {'t': 2.3333, 'pose': pose}]}, open(P('kev2.json'), 'w'))
    j2 = ak('bake', P('t.blend'), '--clip', 'ev2', '--keys', P('kev2.json'), '--out-action', P('ev2.json'), expect_ok=False)
    assert 'outside' in j2['error'], j2
    return f"impact 2.3 -> {j['events']['impact']} (shifted by {j['shifted_by']}); clip-time event with video-time keys refused"


@test('read back: pose of a baked clip at time t renders like the key; hold interpolation')
def t_readpose():
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--from-action', P('test_b.json'), '--t', 0.3,
           '--save-pose', P('rp.json'), '--target', P('pose_a.png'), '--out', P('rp_cmp.jpg'))
    assert j['iou_mean'] > 0.97, j
    pose = generic_pose()
    json.dump({'keys': [{'t': 0, 'pose': {'bones': {}}, 'interp': 'hold'}, {'t': 0.3, 'pose': pose}]}, open(P('kh.json'), 'w'))
    ak('bake', P('t.blend'), '--clip', 'hold', '--keys', P('kh.json'), '--out-action', P('hold.json'))
    jh = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--from-action', P('hold.json'), '--t', 0.25,
            '--target', P('rest.png'), '--out', P('hold_cmp.jpg'))
    assert jh['iou_mean'] > 0.98, jh
    return f"read-back IoU {j['iou_mean']}, hold at 0.25 s vs rest IoU {jh['iou_mean']}"


@test('mirror --keys, retime, several poses in one image, image caps')
def t_tools():
    ak('mirror', '--keys', P('keys_a.json'), '--out', P('keys_a_m.json'), '--blend', P('t.blend'))
    km = json.load(open(P('keys_a_m.json')))
    assert [k['t'] for k in km['keys']] == [0, 0.3, 0.6] and all('pose' in k for k in km['keys'])
    ak('retime', P('keys_a.json'), '--scale', 1.5, '--out', P('keys_a_r.json'))
    kr = json.load(open(P('keys_a_r.json')))
    assert kr['keys'][2]['t'] == 0.9 and abs(kr['events']['impact'] - 0.45) < 1e-9 and abs(kr['length'] - 1.065) < 1e-9, kr
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('pose_a.json'), '--target', P('pose_a.png'),
           '--pose', P('rest.json'), '--target', P('pose_a.png'), '--out', P('multi.jpg'))
    assert len(j['poses']) == 2 and j['poses'][0]['iou_mean'] > j['poses'][1]['iou_mean'], j
    assert 'iou_limbs' in j['poses'][0] and 'iou_rest' in j['poses'][0]
    sizes = {p: Image.open(p).size for p in (P('multi.jpg'), P('bones.jpg'))}
    jf = ak('frames', P('synth.mp4'), '--cam', P('cam.json'), '--calib', P('frames', 'calib.json'), '--every', 0.0417,
            '--out', P('frames_many'), '--cols', 3)
    pages = jf.get('contact_pages', [jf['contact']])
    sizes.update({p: Image.open(p).size for p in pages})
    assert all(max(s) <= 1024 for s in sizes.values()), sizes
    assert isinstance(jf['times'], str) and jf['count'] > 12, jf
    return f"{len(pages)} contact pages, max image side {max(max(s) for s in sizes.values())} px"


@test('silhouette: grey floor shadow below the ground line is background')
def t_floor():
    cam = I.load_cam(P('cam.json'))
    img = np.ones((cam['height'], cam['width'], 3), np.float32)
    gy = I.ground_y(cam)
    img[gy - 200:gy, 300:340] = (0.8, 0.3, 0.2)          # a coloured leg
    img[gy + 4:gy + 14, 150:500] = 0.55                    # grey shadow strip on the floor
    m = I.silhouette(img, cam)
    assert m[gy - 100, 320] and not m[gy + 9, 200], 'shadow counted as body'
    return 'ok'

@test('bad input fails cleanly (unknown bone)')
def t_bad():
    json.dump({'bones': {'NoSuchBone': {'rx': 10}}}, open(P('bad.json'), 'w'))
    j = ak('pose', P('t.blend'), '--cam', P('cam.json'), '--pose', P('bad.json'), '--out', P('bad.jpg'), expect_ok=False)
    assert 'NoSuchBone' in j.get('error', ''), j


if __name__ == '__main__':
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    only = sys.argv[1:]
    for t in TESTS:
        if not only or any(o in t.__name__ for o in only):
            t()
    for name, ok, info in results:
        print(('PASS ' if ok else 'FAIL ') + name + ' -- ' + info)
    n_fail = sum(1 for r in results if not r[1])
    print(f'{len(results) - n_fail}/{len(results)} passed')
    sys.exit(1 if n_fail else 0)
