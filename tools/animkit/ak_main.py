"""animkit commands (driver side). Entry: tools/ak."""
import argparse, fcntl, json, os, subprocess, sys, tempfile, time, shutil
import numpy as np
from PIL import Image, ImageDraw
import akimg as I
import aknames

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get('AK_BLENDER', '/Applications/Blender.app/Contents/MacOS/Blender')
MEMGATE = os.environ.get('AK_MEMGATE_SCRIPT', '')   # optional free-memory gate script (not included); unset = launch directly
T0 = time.time()
WARNINGS = []


class AKError(Exception):
    pass


def finish(d, ok=True):
    d = dict(d)
    d.setdefault('ok', ok)
    if WARNINGS:
        d['warnings'] = list(dict.fromkeys(WARNINGS))
    d['seconds'] = round(time.time() - T0, 2)
    print('###AK### ' + json.dumps(d))
    sys.stdout.flush()
    sys.exit(0 if d['ok'] else 1)


# ------------------------------------------------------------------ Blender launches (slots + memgate)
def _acquire_slot():
    """machine-wide file-lock semaphore: at most AK_SLOTS (default 6) Blender backends run at once"""
    n = max(1, int(os.environ.get('AK_SLOTS', '6')))
    d = os.path.join(tempfile.gettempdir(), 'animkit_slots')
    os.makedirs(d, exist_ok=True)
    t_end = time.time() + float(os.environ.get('AK_SLOT_TIMEOUT', '900'))
    while True:
        for i in range(n):
            f = open(os.path.join(d, f'slot{i}.lock'), 'w')
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return f
            except OSError:
                f.close()
        if time.time() > t_end:
            raise AKError(f'no free Blender slot after waiting (AK_SLOTS={n})')
        time.sleep(0.2)


def run_blender(cmd, args, timeout=600):
    """runs ak_blender.py <cmd> with args (dict) in headless Blender, returns its ###AKB### json.
    Waits for one of AK_SLOTS slots and goes through the optional memory gate (AK_MEMGATE_SCRIPT) unless AK_MEMGATE=0."""
    fd, ap = tempfile.mkstemp(prefix='ak_', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(args, f)
    argv = [BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'ak_blender.py'), '--', cmd, ap]
    if os.environ.get('AK_MEMGATE', '1') != '0' and os.path.exists(MEMGATE):
        py = '/opt/homebrew/bin/python3' if os.path.exists('/opt/homebrew/bin/python3') else sys.executable
        argv = [py, MEMGATE, 'run', '--need', os.environ.get('AK_NEED_GB', '4'), '--'] + argv
    slot = _acquire_slot()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    finally:
        slot.close()
        os.remove(ap)
    res = None
    for line in r.stdout.splitlines():
        if line.startswith('###AKB### '):
            res = json.loads(line[10:])
    if res is None:
        tail = (r.stdout[-1500:] + '\n' + r.stderr[-1500:]).strip()
        raise AKError(f'blender backend gave no result (exit {r.returncode}): {tail}')
    WARNINGS.extend(res.get('warnings') or [])
    if not res.get('ok', False) and 'error' in res:
        raise AKError(res['error'])
    return res


def need_file(p, what):
    if not p or not os.path.exists(p):
        raise AKError(f'{what} not found: {p}')
    return os.path.abspath(p)


def tmpdir(tag):
    return tempfile.mkdtemp(prefix=f'ak_{tag}_')


def jload(p, what):
    try:
        return json.load(open(need_file(p, what)))
    except json.JSONDecodeError as e:
        raise AKError(f'{what} {p} is not valid JSON: {e}')


# ------------------------------------------------------------------ prep / info
def c_prep(a):
    glb = need_file(a.glb, 'glb')
    r = run_blender('prep', {'glb': glb, 'out': os.path.abspath(a.out)})
    return {'out': r['out'], 'bones': r['bones']}


SIDE_COL = {'l': (30, 90, 235), 'r': (245, 140, 20), None: (120, 120, 120)}


def draw_bones(sheet, cam, joints, size=13):
    """skeleton lines (parent->child, stubs for leaves) + every bone name in two label columns per panel with leaders"""
    d = ImageDraw.Draw(sheet)
    fw, sw, H = cam['front_w'], cam['side_w'], sheet.size[1]
    kids = {}
    for n, j in joints.items():
        if j.get('parent'):
            kids.setdefault(j['parent'], []).append(n)
    for panel, ox in (('front', 0), ('side', fw)):
        for n, j in joints.items():
            h = j[panel]
            for c in kids.get(n, []):
                ch = joints[c][panel]
                d.line([(h[0] + ox, h[1]), (ch[0] + ox, ch[1])], fill=(230, 40, 40), width=3)
            if n not in kids:
                t = j[panel + '_tail']
                d.line([(h[0] + ox, h[1]), (t[0] + ox, t[1])], fill=(230, 40, 40), width=3)
        for n, j in joints.items():
            h = j[panel]
            d.ellipse([h[0] + ox - 4, h[1] - 4, h[0] + ox + 4, h[1] + 4], fill=SIDE_COL[j.get('lr')])
    for panel, ox, pw in (('front', 0, fw), ('side', fw, sw)):
        xs = [j[panel][0] for j in joints.values()]
        mid = (min(xs) + max(xs)) / 2
        cols = {'L': [], 'R': []}
        for n, j in joints.items():
            cols['L' if j[panel][0] < mid else 'R'].append((j[panel][1], n))
        for side, items in cols.items():
            items.sort()
            step = min(size + 3, (H - 40) / max(1, len(items)))
            y_prev = 30 - step
            lx = ox + 6 if side == 'L' else ox + pw - 6
            for y, n in items:
                ly = max(y, y_prev + step)
                ly = min(ly, H - 8 - (len(items) - items.index((y, n)) - 1) * step)
                y_prev = ly
                jx, jy = joints[n][panel][0] + ox, joints[n][panel][1]
                tw = d.textlength(n, font=I.font(size))
                ex = lx + tw + 4 if side == 'L' else lx - tw - 4
                d.line([(ex, ly), (jx, jy)], fill=(120, 120, 160), width=1)
                I.text(d, (lx, ly), n, size=size, fill=SIDE_COL[joints[n].get('lr')] if joints[n].get('lr') else (0, 0, 120),
                       anchor='lm' if side == 'L' else 'rm')
    return sheet


def draw_skeleton(img, cam, joints, width=2):
    """thin skeleton over a full-size sheet image: character LEFT bones blue, RIGHT bones orange, centre grey"""
    d = ImageDraw.Draw(img)
    fw = cam['front_w']
    for panel, ox in (('front', 0), ('side', fw)):
        for n, j in joints.items():
            p = j.get('parent')
            if not p or p not in joints or not joints[p].get('deform', True):
                continue          # no line down to a non-deforming root bone at the floor
            a, b = joints[p][panel], j[panel]
            d.line([(a[0] + ox, a[1]), (b[0] + ox, b[1])], fill=SIDE_COL[j.get('lr')], width=width)
    return img


def c_info(a):
    blend = need_file(a.blend, 'blend')
    td = tmpdir('info')
    args = {'blend': blend, 'prefix': os.path.join(td, 'rest')}
    if a.cam:
        args['cam'] = need_file(a.cam, 'cam.json')
    r = run_blender('info', args)
    keys = ('armature', 'armature_scale', 'n_bones', 'roots', 'pivot', 'chains', 'chain_axes', 'driven', 'pairs',
            'unpaired_sided', 'rig_hash', 'sockets', 'meshes', 'missing_images', 'actions')
    res = {k: r.get(k) for k in keys}
    res['bones'] = r['bones']
    if a.cam:
        cam = I.load_cam(a.cam)
        rgb, _ = I.compose_render(cam, *r['renders'])
        img = draw_bones(I.to_img(rgb), cam, r['joints'])
        I.draw_ground(img, cam)
        I.label(img, 'FRONT (char faces you; its LEFT = screen right = +X)  blue = LEFT, orange = RIGHT', 16, (8, 6))
        I.label(img, 'SIDE (char faces screen right = -Y)', 16, (cam['front_w'] + 8, 6))
        outp = a.out or os.path.splitext(blend)[0] + '_bones.jpg'
        I.save_jpg(img, outp)
        res['bones_image'] = os.path.abspath(outp)
    shutil.rmtree(td, ignore_errors=True)
    if a.json_out:
        json.dump(res, open(a.json_out, 'w'), indent=1)
        res = {'json': os.path.abspath(a.json_out), 'n_bones': res['n_bones'], 'bones_image': res.get('bones_image'),
               'pivot': res['pivot'], 'driven': res['driven'], 'chains': res['chains'], 'chain_axes': res['chain_axes'],
               'bone_names': [b['name'] for b in res['bones']],
               'rest_angles': {b['name']: [b['rest_front_deg'], b['rest_side_deg']] for b in res['bones']}}
    return res


# ------------------------------------------------------------------ video frames
def parse_times(a, dur, fps):
    """requested times -> exact frame times (each snapped to the nearest video frame), sorted, unique"""
    t0 = a.t0 if a.t0 is not None else 0.0
    t1 = a.t1 if a.t1 is not None else dur
    t1 = min(t1, dur - 0.5 / fps)
    if a.times:
        ts = [float(x) for x in a.times.split(',') if x.strip()]
    elif a.every:
        n = int(np.floor((t1 - t0) / a.every + 1e-6)) + 1
        ts = [t0 + i * a.every for i in range(n)]
    else:
        raise AKError('give --times or --every')
    bad = [t for t in ts if t < 0 or t > dur]
    if bad:
        raise AKError(f'times outside the video (0..{dur:.2f}s): {bad}')
    nmax = int(np.floor(dur * fps - 0.5))
    out = []
    for t in ts:
        n, _ = I.snap(t, fps)
        n = min(n, nmax)
        if n not in [x[0] for x in out]:
            out.append((n, n / fps))
    return out


def video_reader(video, cam, sheet=None, calib=None, save_calib=None):
    """-> (frame(t) -> (rgb in the cam.json framing, exact frame time, frame index), calib dict or None, fps).
    Seedance re-frames the sheet (other scale, divider moved), so frames are rectified with a calibration that maps
    video frame 0 (= the sheet the video started from) onto the sheet. Times snap to whole video frames."""
    td = tmpdir('vid')
    fps = I.video_fps(video)
    cal = None
    if calib:
        cal = jload(calib, 'calib json')
    elif sheet:
        v0 = I.extract_native(video, 0.0, os.path.join(td, 'v0.png'), fps)
        cal = I.calibrate(v0, I.load_rgb(need_file(sheet, 'sheet'), cam), cam)
        cal['video'] = os.path.abspath(video); cal['sheet'] = os.path.abspath(sheet)
        if save_calib:
            json.dump(cal, open(save_calib, 'w'), indent=1)
    k = [0]

    def frame(t):
        k[0] += 1
        n, tt = I.snap(t, fps)
        p = os.path.join(td, f'v{k[0]}.png')
        if cal is None:
            I.extract_frame(video, tt, cam, p, fps)
            return I.load_rgb(p, cam), tt, n
        return I.rectify(I.extract_native(video, tt, p, fps), cal, cam), tt, n
    return frame, cal, fps


def c_frames(a):
    video = need_file(a.video, 'video')
    cam = I.load_cam(need_file(a.cam, 'cam.json'))
    dur, size = I.ffprobe_duration(video)
    os.makedirs(a.out, exist_ok=True)
    cpath = os.path.abspath(os.path.join(a.out, 'calib.json'))
    frame, cal, fps = video_reader(video, cam, a.sheet, a.calib, cpath)
    ts = parse_times(a, dur, fps)
    files, masks, rgbs, ms, times = [], [], [], [], []
    for i, (n, t) in enumerate(ts):
        rgb, t, n = frame(t)
        p = os.path.join(a.out, f'f{i:03d}_t{t:06.3f}.png')
        I.to_img(rgb).save(p)
        files.append(os.path.abspath(p)); times.append(round(t, 5))
        m = I.silhouette(rgb, cam, a.tol)
        rgbs.append(rgb); ms.append(m)
        if a.mask:
            mp = os.path.join(a.out, f'f{i:03d}_t{t:06.3f}_mask.png')
            Image.fromarray((m * 255).astype(np.uint8)).save(mp)
            masks.append(os.path.abspath(mp))
    box = None if a.no_crop else I.union_box(cam, ms)
    fs = max(14, int(round(0.06 * ((box[1] - box[0]) if box else cam['height']))))
    thumbs, mthumbs = [], []
    for i, ((n, _), t, rgb, m) in enumerate(zip(ts, times, rgbs, ms)):
        im = I.draw_ground(I.crop_panels(I.to_img(rgb), box), cam, box)
        thumbs.append(I.label(im, f'#{i} {t:.3f}s', fs, (6, 4)))
        if a.mask:
            vis = rgb * 0.35 + 0.65; vis[m] = rgb[m] * 0.4 + np.array([0.0, 0.6, 0.0])
            mthumbs.append(I.label(I.crop_panels(I.to_img(vis), box), f'#{i} {t:.3f}s', fs, (6, 4)))
    cols = min(len(thumbs), a.cols)
    cw = max(64, (1024 - 4 * (cols + 1)) // cols)
    pages = []
    for k, page in enumerate(I.grid_pages(thumbs, cols, cw)):
        cp = os.path.join(a.out, 'contact.jpg' if k == 0 else f'contact_p{k + 1}.jpg')
        I.save_jpg(page, cp)
        pages.append(os.path.abspath(cp))
    json.dump({'video': video, 'fps': fps, 'times': times, 'frames': files, 'masks': masks}, open(os.path.join(a.out, 'frames.json'), 'w'), indent=1)
    res = {'video': video, 'duration': dur, 'video_fps': fps, 'video_size': size, 'count': len(files),
           'out_dir': os.path.abspath(a.out), 'pattern': 'f###_tSS.SSS.png (exact video frame time)',
           'first': files[0], 'last': files[-1], 'times': times if len(times) <= 12 else f'{len(times)} times, see frames.json',
           'frames_json': os.path.abspath(os.path.join(a.out, 'frames.json')), 'contact': pages[0]}
    if len(pages) > 1:
        res['contact_pages'] = pages
    if cal:
        res['calib'] = cpath if not a.calib else os.path.abspath(a.calib)
        res['calib_iou'] = {k: v.get('iou') for k, v in cal['panels'].items()}
        vals = [v for v in res['calib_iou'].values() if v is not None]
        if vals and min(vals) < 0.75:
            res['warning'] = 'calibration IoU < 0.75: frame 0 does not look like the sheet; check --sheet'
    else:
        res['warning'] = 'no --sheet/--calib: frames are only scaled, NOT aligned to the sheet framing'
    if a.mask:
        mpages = []
        for k, page in enumerate(I.grid_pages(mthumbs, cols, cw)):
            mp = os.path.join(a.out, 'contact_mask.jpg' if k == 0 else f'contact_mask_p{k + 1}.jpg')
            I.save_jpg(page, mp)
            mpages.append(os.path.abspath(mp))
        res['contact_mask'] = mpages[0]
    return res


# ------------------------------------------------------------------ pose
def compare_cells(cam, target_rgb, rend_rgb, joints, tol, crop=True, skeleton=True, rest_rgb=None):
    """-> (dict of PIL cells cropped to the character, metrics dict or None)"""
    rend_full = I.to_img(rend_rgb)
    if skeleton and joints:
        draw_skeleton(rend_full, cam, joints)
    if target_rgb is None:
        box = I.union_box(cam, [I.silhouette(rend_rgb, cam, tol)]) if crop else None
        im = I.draw_ground(I.crop_panels(rend_full, box), cam, box)
        return {'ours': I.label(im, 'OURS')}, None
    tmask = I.silhouette(target_rgb, cam, tol)
    rmask = I.silhouette(rend_rgb, cam, tol)      # same method on both sides: thresholds bias both masks alike
    iou = I.panel_iou(cam, tmask, rmask)
    met = {'iou': iou, 'iou_mean': round((iou['front'] + iou['side']) / 2, 4)}
    if joints:
        trunk = I.trunk_mask(cam, joints)
        if trunk.any():
            met['iou_limbs'] = I.panel_iou(cam, tmask & ~trunk, rmask & ~trunk)
    if rest_rgb is not None:
        ri = I.panel_iou(cam, tmask, I.silhouette(rest_rgb, cam, tol))
        met['iou_rest'] = ri
        met['gain_over_rest'] = round(met['iou_mean'] - (ri['front'] + ri['side']) / 2, 4)
    box = I.union_box(cam, [tmask, rmask]) if crop else None
    C = lambda im: I.draw_ground(I.crop_panels(im, box), cam, box)
    cells = {'target': I.label(C(I.to_img(target_rgb)), 'TARGET'),
             'ours': I.label(C(rend_full), 'OURS'),
             'overlay': I.label(C(I.to_img(0.5 * target_rgb + 0.5 * rend_rgb)), '50% OVERLAY')}
    dm = C(I.to_img(I.diff_map(cam, tmask, rmask)))
    line = f"IoU front {iou['front']:.3f}  side {iou['side']:.3f}"
    if 'iou_limbs' in met:
        line2 = f"limbs {met['iou_limbs']['front']:.2f}/{met['iou_limbs']['side']:.2f}"
        if 'iou_rest' in met:
            line2 += f"  rest {met['iou_rest']['front']:.2f}/{met['iou_rest']['side']:.2f}"
    else:
        line2 = ''
    I.label(dm, line, 16)
    I.label(dm, (line2 + '  ' if line2 else '') + 'red=target only blue=ours only', 13, (8, 28))
    cells['diff'] = dm
    return cells, met


def compare_image(cam, target_rgb, rend_rgb, joints, tol, title='', crop=True, skeleton=True, rest_rgb=None):
    """2x2: target | render / 50% overlay | silhouette diff. returns (PIL image, metrics or None)"""
    cells, met = compare_cells(cam, target_rgb, rend_rgb, joints, tol, crop, skeleton, rest_rgb)
    if met is None:
        img = cells['ours']
    else:
        img = I.grid([cells['target'], cells['ours'], cells['overlay'], cells['diff']], 2, 508)
    if title:
        I.label(img, title + ('   (skeleton: blue = char LEFT, orange = RIGHT; green line = floor)' if skeleton else ''),
                13, (12, img.size[1] - 20))
    return img, met


def c_pose(a):
    blend = need_file(a.blend, 'blend')
    cam = I.load_cam(need_file(a.cam, 'cam.json'))
    poses, labels = [], []
    if a.from_action:
        if a.t is None:
            raise AKError('--from-action needs --t <clip seconds>')
        src = need_file(a.from_action, 'action json') if not a.from_action.startswith('clip:') else a.from_action
        poses.append({'from_action': src, 't': a.t}); labels.append(f'{os.path.basename(a.from_action)} @ {a.t:g}s')
    for p in a.pose or []:
        poses.append(jload(p, 'pose json')); labels.append(os.path.basename(p))
    if not poses:
        raise AKError('give --pose p.json (repeatable) or --from-action a.json --t s')
    targets = [need_file(t, 'target') for t in (a.target or [])]
    if len(targets) not in (0, 1, len(poses)):
        raise AKError(f'{len(poses)} poses but {len(targets)} targets: give one target per pose, or one for all')
    td = tmpdir('pose')
    send = list(poses) + ([{'bones': {}}] if targets else [])          # rest pose = baseline IoU
    r = run_blender('pose', {'blend': blend, 'cam': os.path.abspath(a.cam), 'poses': send, 'prefix': os.path.join(td, 'p')})
    prs = r['poses']
    rest_rgb = I.compose_render(cam, *prs[-1]['renders'])[0] if targets else None
    items, rows = [], []
    for i, (pr, lab) in enumerate(zip(prs[:len(poses)], labels)):
        rgb, _ = I.compose_render(cam, *pr['renders'])
        tgt = I.load_rgb(targets[0] if len(targets) == 1 else targets[i], cam) if targets else None
        it = {'pose': lab, 'ground': pr['ground']}
        if pr.get('resolved_pose') is not None:
            it['resolved_pose'] = pr['resolved_pose']
        if len(poses) == 1:
            img, met = compare_image(cam, tgt, rgb, pr['joints'], a.tol, lab, not a.no_crop, not a.no_skeleton, rest_rgb)
            if tgt is None and a.joints:
                img = draw_bones(img, cam, pr['joints'], 12)
            rows.append(img)
        else:
            cells, met = compare_cells(cam, tgt, rgb, pr['joints'], a.tol, not a.no_crop, not a.no_skeleton, rest_rgb)
            I.label(cells['ours'], f'#{i} {lab}', 14, (8, 28))
            rows.append([cells['target'], cells['ours'], cells['diff']] if met else [cells['ours']])
        if met:
            it.update(met)
        if a.render_out and i == 0:
            I.save_jpg(I.to_img(rgb), a.render_out, long_side=None)
            it['render'] = os.path.abspath(a.render_out)
        items.append(it)
    if len(poses) == 1:
        img = rows[0]
    else:
        cols = len(rows[0])
        flat = [c for row in rows for c in row]
        img = I.grid(flat, cols, max(64, (1024 - 4 * (cols + 1)) // cols))
    I.save_jpg(img, a.out)
    if a.save_pose:
        rp = items[0].get('resolved_pose') or poses[0]
        json.dump(rp, open(a.save_pose, 'w'), indent=1)
    shutil.rmtree(td, ignore_errors=True)
    res = {'out': os.path.abspath(a.out), 'blender_s': r['blender_s'], 'pivot': r.get('pivot')}
    if a.save_pose:
        res['saved_pose'] = os.path.abspath(a.save_pose)
    if len(items) == 1:
        it = items[0]
        it.pop('pose')
        if a.save_pose:
            it.pop('resolved_pose', None)
        res.update(it)
    else:
        for it in items:
            if a.save_pose:
                it.pop('resolved_pose', None)
        res['poses'] = items
    return res


def c_solve(a):
    """bone positions (world) + lowest vertex per side for a pose, no render"""
    blend = need_file(a.blend, 'blend')
    pose = jload(a.pose, 'pose json')
    r = run_blender('pose', {'blend': blend, 'poses': [pose], 'bones_out': True})
    pr = r['poses'][0]
    res = {'pivot': r.get('pivot'), 'ground': pr['ground'], 'bones': pr['bones']}
    if pr.get('resolved_pose') is not None:
        res['resolved_pose'] = pr['resolved_pose']
    if a.json_out:
        json.dump(res, open(a.json_out, 'w'), indent=1)
        return {'json': os.path.abspath(a.json_out), 'pivot': res['pivot'], 'ground': res['ground']}
    return res


def c_selftest(a):
    r = run_blender('selftest', {'blend': need_file(a.blend, 'blend'), 'trials': a.trials})
    return {k: v for k, v in r.items() if k != 'ok'} | {'ok': r['ok']}


# ------------------------------------------------------------------ bake / merge / strip / export
def load_keys(path, clip, loop=None, fps=None, length=None, in_place=True):
    """keys.json -> bake spec with poses inlined.
    keys: [{"t": s, "pose": {...}} | {"t": s, "pose_file": "p.json"}, optional "interp": "hold"|"linear"|"bezier"]"""
    k = jload(path, 'keys json')
    base = os.path.dirname(os.path.abspath(path))
    keys = []
    for i, e in enumerate(k.get('keys', [])):
        if 't' not in e:
            raise AKError(f'key #{i} has no "t" (seconds)')
        if 'pose' in e:
            pose = e['pose']
        elif 'pose_file' in e:
            pose = jload(os.path.join(base, e['pose_file']), f'pose_file of key #{i}')
        else:
            raise AKError(f'key #{i} needs "pose" or "pose_file"')
        kk = {'t': float(e['t']), 'pose': pose}
        if 'interp' in e:
            kk['interp'] = e['interp']
        keys.append(kk)
    if not keys:
        raise AKError('keys.json has an empty "keys" list')
    ev = k.get('events') or {}
    for n, v in ev.items():
        if not isinstance(v, (int, float)):
            raise AKError(f'event {n!r} must be a time in seconds')
    return {'name': clip or k.get('name'), 'fps': fps or k.get('fps', 30),
            'loop': k.get('loop', False) if loop is None else loop,
            'length': length if length is not None else k.get('length'), 'events': ev, 'keys': keys, 'in_place': in_place}


def c_bake(a):
    blend = need_file(a.blend, 'blend')
    spec = load_keys(a.keys, a.clip, True if a.loop else None, a.fps, a.length, not a.keep_root_motion)
    if not spec['name']:
        raise AKError('give --clip <name>')
    args = {'blend': blend, 'spec': spec, 'write_blend': not a.no_save}
    if a.out_action:
        args['out_action'] = os.path.abspath(a.out_action)
    if a.out_action and not a.save_blend_too:
        args['write_blend'] = False          # JSON route for parallel agents: never touch the shared blend
    r = run_blender('bake', args)
    return {k: v for k, v in r.items() if k not in ('ok', 'blender_s', 'warnings')}


def c_merge(a):
    blend = need_file(a.blend, 'blend')
    files = [need_file(f, 'action json') for f in a.files]
    seen = {}
    for f in files:
        j = jload(f, 'action json')
        if j.get('format') != 'animkit-action-1':
            raise AKError(f'{f} is not an animkit action json')
        if j['name'] in seen and not a.replace:
            raise AKError(f"two files carry clip {j['name']!r}: {seen[j['name']]} and {f} (pass --replace to let the later win)")
        seen[j['name']] = f
    r = run_blender('merge', {'blend': blend, 'files': files})
    return {k: r[k] for k in ('merged', 'rebaked', 'replaced_existing', 'actions', 'rig_hash')}


def c_strip(a):
    blend = need_file(a.blend, 'blend')
    cam = I.load_cam(need_file(a.cam, 'cam.json'))
    if not (a.action_json or a.clip):
        raise AKError('give --action-json <file> or --clip <name>')
    td = tmpdir('strip')
    args = {'blend': blend, 'cam': os.path.abspath(a.cam), 'prefix': os.path.join(td, 'r'), 'n': a.n,
            'no_view': bool(a.no_view)}
    if a.action_json:
        args['action_json'] = need_file(a.action_json, 'action json')
    else:
        args['clip'] = a.clip
    if a.mp4:
        info = run_blender('render_clip', dict(args, n=2, prefix=os.path.join(td, 'probe')))
        L = info['length']
        nfr = max(2, int(round(L * a.mp4_fps)) + 1)
        args['times'] = [L * i / (nfr - 1) for i in range(nfr)]
    r = run_blender('render_clip', args)
    L, times = r['length'], r['times']
    frame = None
    res = {'length': L, 'loop': r['loop'], 'times': [round(t, 4) for t in times], 'view_applied': r.get('view_applied')}
    if a.video:
        video = need_file(a.video, 'video')
        frame, cal, vfps = video_reader(video, cam, a.sheet, a.calib)
        t0 = a.t0 if a.t0 is not None else 0.0
        if a.t1 is not None and abs((a.t1 - t0) - L) > 1.0 / vfps:
            WARNINGS.append(f'--t1 ignored: the reference frame for clip time t is t0 + t (clip length {L:.4f} s, '
                            f't1 - t0 = {a.t1 - t0:.4f} s)')
    raw, ious, allm = [], [], []
    for i, (t, rp) in enumerate(zip(times, r['renders'])):
        rgb, _ = I.compose_render(cam, *rp)
        rmask = I.silhouette(rgb, cam, a.tol)
        allm.append(rmask)
        if frame is not None:
            ref, vt, vn = frame(t0 + t)
            tm = I.silhouette(ref, cam, a.tol)
            allm.append(tm)
            iou = I.panel_iou(cam, tm, rmask)
            ious.append(iou)
            raw.append((t, vt, ref, rgb, iou))
        else:
            raw.append((t, None, None, rgb, None))
    box = None if a.no_crop else I.union_box(cam, allm)
    fs = max(14, int(round(0.05 * ((box[1] - box[0]) if box else cam['height']))))
    pairs = []
    for t, vt, ref, rgb, iou in raw:
        ours = I.draw_ground(I.crop_panels(I.to_img(rgb), box), cam, box)
        I.label(ours, f'OURS {t:.3f}s', fs, (6, 4))
        if ref is not None:
            refi = I.draw_ground(I.crop_panels(I.to_img(ref), box), cam, box)
            I.label(refi, f'REF {vt:.3f}s', fs, (6, 4))
            I.label(ours, f"IoU {iou['front']:.2f}/{iou['side']:.2f}", fs, (6, 8 + fs))
            pairs.append((refi, ours))
        else:
            pairs.append((None, ours))
    if ious:
        res['iou'] = [[x['front'], x['side']] for x in ious]
        res['iou_mean'] = round(float(np.mean([[x['front'], x['side']] for x in ious])), 4)
        res['ref_times'] = [round(x[1], 4) for x in raw]
    gl = [g.get('lowest_z') for g in r.get('ground') or [] if g.get('lowest_z') is not None]
    if gl:
        res['lowest_z_range'] = [round(min(gl), 4), round(max(gl), 4)]
    if a.mp4:
        fdir = os.path.join(td, 'mp4'); os.makedirs(fdir)
        for i, (ref, ours) in enumerate(pairs):
            w, h = ours.size[0] // 2, ours.size[1] // 2
            canvas = Image.new('RGB', (w, h * (2 if ref else 1)), (0, 0, 0))
            if ref:
                canvas.paste(ref.resize((w, h), Image.LANCZOS), (0, 0))
            canvas.paste(ours.resize((w, h), Image.LANCZOS), (0, h if ref else 0))
            canvas.save(os.path.join(fdir, f'{i:04d}.png'))
        os.makedirs(os.path.dirname(os.path.abspath(a.mp4)) or '.', exist_ok=True)
        cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(a.mp4_fps), '-i', os.path.join(fdir, '%04d.png'),
               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', a.mp4]
        rr = subprocess.run(cmd, capture_output=True, text=True)
        if rr.returncode != 0:
            raise AKError('ffmpeg mp4 failed: ' + rr.stderr[-400:])
        res['mp4'] = os.path.abspath(a.mp4)
        # the review image still uses N evenly spaced frames
        idx = [int(round(i * (len(pairs) - 1) / max(1, a.n - 1))) for i in range(a.n)]
        pairs = [pairs[i] for i in idx]
    if a.out:
        cells = []
        cols = a.cols
        for k in range(0, len(pairs), cols):
            grp = pairs[k:k + cols]
            if grp[0][0] is not None:
                cells += [p[0] for p in grp] + [None] * (cols - len(grp))
            cells += [p[1] for p in grp] + [None] * (cols - len(grp))
        blank = Image.new('RGB', pairs[0][1].size, (40, 40, 40))
        img = I.grid([c or blank for c in cells], cols, max(64, (a.width - 4 * (cols + 1)) // cols))
        I.save_jpg(img, a.out)
        res['out'] = os.path.abspath(a.out)
    shutil.rmtree(td, ignore_errors=True)
    return res


def c_export(a):
    blend = need_file(a.blend, 'blend')
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp.glb'
    r = run_blender('export', {'blend': blend, 'out': tmp})
    import pygltflib
    g = pygltflib.GLTF2().load(tmp)
    names = [an.name for an in g.animations]
    man = r['manifest']
    missing = [c for c in man['clips'] if c not in names]
    if missing or len(names) != r['n_actions']:
        raise AKError(f'GLB has animations {names}, expected {sorted(man["clips"])}')
    if not g.skins:
        raise AKError('GLB has no skin')
    if r.get('n_material_images') and not g.images:
        raise AKError(f"the blend's materials use {r['n_material_images']} images but the GLB has none")
    efps = float(r['export_fps'])
    bad = {}
    lengths = {}
    for an in g.animations:
        tm = max(g.accessors[s.input].max[0] for s in an.samplers)
        lengths[an.name] = round(tm, 4)
        if abs(tm - man['clips'][an.name]['length']) > 1.0 / efps + 1e-4:
            bad[an.name] = {'glb': round(tm, 4), 'manifest': man['clips'][an.name]['length']}
    if bad:
        raise AKError(f'GLB clip lengths differ from the manifest by more than one frame: {bad}')
    os.replace(tmp, out)
    res = {'out': out, 'animations': names, 'skins': len(g.skins), 'images': len(g.images or []),
           'export_fps': r['export_fps'], 'glb_lengths': lengths, 'size_mb': round(os.path.getsize(out) / 1e6, 2)}
    if r.get('retimed'):
        res['retimed'] = r['retimed']
    if a.clips_json:
        old = {}
        if os.path.exists(a.clips_json):
            try:
                old = json.load(open(a.clips_json))
            except Exception:
                old = {}
        for k in ('sockets', 'socket_offsets'):
            if not man.get(k) and old.get(k):
                man[k] = old[k]          # keep sockets written by the rig agent when there is no rig.json
        json.dump(man, open(a.clips_json, 'w'), indent=1)
        res['clips_json'] = os.path.abspath(a.clips_json)
    return res


# ------------------------------------------------------------------ fit / cycle
def c_fit(a):
    blend = need_file(a.blend, 'blend')
    cam = I.load_cam(need_file(a.cam, 'cam.json'))
    need_file(a.pose, 'start pose'); need_file(a.target, 'target')
    td = tmpdir('fit')
    tm = I.silhouette(I.load_rgb(a.target, cam), cam, a.tol)
    mp = os.path.join(td, 'target_mask.png')
    Image.fromarray((tm * 255).astype(np.uint8)).save(mp)
    bones = [b.strip() for b in a.bones.split(',') if b.strip()]
    args = {'blend': blend, 'cam': os.path.abspath(a.cam), 'pose': jload(a.pose, 'start pose'), 'target_mask': mp,
            'bones': bones, 'axes': a.axes.split(','), 'limit': a.limit, 'prefix': os.path.join(td, 'f'),
            'color': a.color, 'target_rgb': os.path.join(td, 'target.png')}
    I.to_img(I.load_rgb(a.target, cam)).save(os.path.join(td, 'target.png'))
    r = run_blender('fit', args, timeout=900)
    outp = a.out_pose or os.path.splitext(a.pose)[0] + '_fit.json'
    json.dump(r['pose'], open(outp, 'w'), indent=1)
    res = {'out_pose': os.path.abspath(outp), 'fit_score_start': r['score_start'], 'fit_score_end': r['score_end'],
           'fit_iou_start': r['iou_start'], 'fit_iou_end': r['iou_end'], 'evals': r['evals'],
           'note': 'fit_iou_* = silhouette IoU at the fit resolution (front, side); fit_score_* also subtracts the colour penalty'}
    if a.out:
        pr = run_blender('pose', {'blend': blend, 'cam': os.path.abspath(a.cam), 'poses': [r['pose']], 'prefix': os.path.join(td, 'p')})
        p0 = pr['poses'][0]
        rgb, _ = I.compose_render(cam, *p0['renders'])
        img, met = compare_image(cam, I.load_rgb(a.target, cam), rgb, p0['joints'], a.tol, os.path.basename(outp))
        I.save_jpg(img, a.out)
        res['out'] = os.path.abspath(a.out)
        res.update(met)
    shutil.rmtree(td, ignore_errors=True)
    return res


def c_cycle(a):
    """loop length finder: silhouette IoU of every video frame against the frame at t0"""
    video = need_file(a.video, 'video')
    cam = I.load_cam(need_file(a.cam, 'cam.json'))
    dur, _ = I.ffprobe_duration(video)
    frame, cal, fps = video_reader(video, cam, a.sheet, a.calib)
    t1 = min(a.t1 if a.t1 is not None else a.t0 + 3.0, dur - 0.05)
    rgb0, t0, n0 = frame(a.t0)
    m0 = I.silhouette(rgb0, cam, a.tol)
    rows = []
    n = n0 + max(1, int(round(a.min * fps)))
    while n / fps <= t1 + 1e-6:
        rgb, t, _ = frame(n / fps)
        iou = I.panel_iou(cam, m0, I.silhouette(rgb, cam, a.tol))
        rows.append((round(t - t0, 4), round((iou['front'] + iou['side']) / 2, 4), iou))
        n += 1
    # local maxima, best first
    peaks = [rows[i] for i in range(1, len(rows) - 1) if rows[i][1] >= rows[i - 1][1] and rows[i][1] >= rows[i + 1][1]]
    peaks.sort(key=lambda r: -r[1])
    if not peaks:
        raise AKError('no repeat found in the range; widen --t1')
    best = peaks[0]
    return {'t0': round(t0, 5), 'video_fps': fps, 'period': best[0], 'period_iou': best[2],
            'candidates': [{'period': p[0], 'iou_mean': p[1]} for p in peaks[:5]],
            'hint': 'a loop clip of this length repeats the motion; the best peak may be 2 periods: check the shorter candidates'}


# ------------------------------------------------------------------ mirror / retime
class MirrorCtx:
    def __init__(self, names, mapping, unpaired, chains, classes):
        self.names, self.m, self.unpaired, self.chains, self.classes = names, mapping, set(unpaired), chains, classes


def mirror_ctx(a):
    if a.rig:
        rj = jload(a.rig, 'rig.json')
        bones = rj.get('bones') or []
        if not bones:
            raise AKError(f'{a.rig} has no "bones" list; use --blend <char.blend>')
        names = [b['name'] for b in bones]
        m, unpaired = aknames.mirror_map(names, rj.get('pairs'))
        head = {b['name']: b.get('head', [0, 0, 0]) for b in bones}
        tail = {b['name']: b.get('tail', [0, 0, 1]) for b in bones}
        chains = {k: v for k, v in (rj.get('chains') or {}).items() if isinstance(v, list) and all(n in head for n in v)}
        classes = {}
        for k, v in chains.items():
            h0 = head[v[0]]; h1 = head[v[-1]] if len(v) > 1 else tail[v[0]]
            classes[k] = aknames.chain_class([h1[i] - h0[i] for i in range(3)])
        return MirrorCtx(names, m, unpaired, chains, classes)
    if a.blend:
        r = run_blender('info', {'blend': need_file(a.blend, 'blend')})
        names = [b['name'] for b in r['bones']]
        m = {n: r['pairs'].get(n, n) for n in names}
        return MirrorCtx(names, m, r.get('unpaired_sided') or [], r['chains'],
                         {k: v['class'] for k, v in (r.get('chain_axes') or {}).items()})
    raise AKError('mirror needs the rig: --blend <char.blend> (reads rig.json next to it) or --rig <rig.json>')


def mirror_pose(p, ctx):
    """left/right mirror across the character's centre plane (X = 0): swap partner bones (rig.json pairs, then name
    tokens), negate ry/rz (and aim front/twist), negate root.loc x and root.rot y/z, swap root.ground left/right.
    view_offset / view_scale (camera framing) are kept as they are."""
    q = json.loads(json.dumps(p))
    nb = {}
    for n, v in (p.get('bones') or {}).items():
        if n in ctx.unpaired:
            raise AKError(f'bone {n!r} looks left/right but the rig has no partner for it: add it to rig.json "pairs"')
        if n not in ctx.m:
            raise AKError(f'bone {n!r} is not in the rig')
        mn = ctx.m[n]
        v = dict(v)
        for ax in ('ry', 'rz', 'front', 'twist'):
            if v.get(ax) is not None:
                v[ax] = -v[ax]
        if mn in nb:
            raise AKError(f'two pose bones mirror onto {mn!r}')
        nb[mn] = v
    q['bones'] = nb
    if 'root' in p:
        r = dict(p['root'])
        if 'loc' in r:
            r['loc'] = [-r['loc'][0], r['loc'][1], r['loc'][2]]
        if 'rot' in r:
            r['rot'] = [r['rot'][0], -r['rot'][1], -r['rot'][2]]
        if r.get('ground') in ('left', 'right'):
            r['ground'] = {'left': 'right', 'right': 'left'}[r['ground']]
        q['root'] = r
    if 'chain' in p:
        chs = p['chain'] if isinstance(p['chain'], list) else [p['chain']]
        outl = []
        for ch in chs:
            ch = dict(ch)
            names = ctx.chains.get(ch['name'])
            if names is None:
                raise AKError(f"unknown chain {ch['name']!r}; chains: {sorted(ctx.chains)}")
            mb = [ctx.m.get(n, n) for n in names]
            target = [k for k, v in ctx.chains.items() if v == mb]
            if not target:
                raise AKError(f"chain {ch['name']!r} has no mirrored partner chain")
            cls = ctx.classes.get(ch['name'], 'vertical')
            ch['name'] = ch['name'] if ch['name'] in target else target[0]
            for k in ('ry', 'rz'):
                if k in ch:
                    ch[k] = [-x for x in ch[k]]
            if 'bend_side' in ch and aknames.mirror_flips_bend_side(cls):
                ch['bend_side'] = [-x for x in ch['bend_side']]
            outl.append(ch)
        q['chain'] = outl
    return q


def c_mirror(a):
    ctx = mirror_ctx(a)
    if a.keys:
        k = jload(a.keys, 'keys json')
        base = os.path.dirname(os.path.abspath(a.keys))
        out = dict(k)
        out['keys'] = []
        for i, e in enumerate(k.get('keys', [])):
            pose = e['pose'] if 'pose' in e else jload(os.path.join(base, e['pose_file']), f'pose_file of key #{i}')
            ne = {kk: vv for kk, vv in e.items() if kk not in ('pose', 'pose_file')}
            ne['pose'] = mirror_pose(pose, ctx)
            out['keys'].append(ne)
        json.dump(out, open(a.out, 'w'), indent=1)
        return {'out': os.path.abspath(a.out), 'n_keys': len(out['keys'])}
    if not a.pose:
        raise AKError('give a pose json or --keys keys.json')
    p = jload(a.pose, 'pose')
    q = mirror_pose(p, ctx)
    json.dump(q, open(a.out, 'w'), indent=1)
    return {'out': os.path.abspath(a.out), 'renamed': {k: ctx.m[k] for k in (p.get('bones') or {}) if ctx.m.get(k, k) != k}}


def c_retime(a):
    k = jload(a.keys, 'keys json')
    s = float(a.scale)
    if s <= 0:
        raise AKError('--scale must be > 0')
    base = os.path.dirname(os.path.abspath(a.keys))
    outdir = os.path.dirname(os.path.abspath(a.out))
    for e in k.get('keys', []):
        e['t'] = round(float(e['t']) * s, 5)
        if 'pose_file' in e and outdir != base:
            e['pose_file'] = os.path.relpath(os.path.join(base, e['pose_file']), outdir)
    if k.get('length') is not None:
        k['length'] = round(float(k['length']) * s, 5)
    k['events'] = {n: round(float(v) * s, 5) for n, v in (k.get('events') or {}).items()}
    json.dump(k, open(a.out, 'w'), indent=1)
    return {'out': os.path.abspath(a.out), 'scale': s, 'length': k.get('length'), 'times': [e['t'] for e in k.get('keys', [])]}


# ------------------------------------------------------------------ main
def build_parser():
    p = argparse.ArgumentParser(prog='ak', description='animkit: match rig animations to front+side reference videos')
    sp = p.add_subparsers(dest='cmd', required=True)

    q = sp.add_parser('prep', help='glb -> clean blend (no actions)')
    q.add_argument('glb'); q.add_argument('--out', required=True)

    q = sp.add_parser('info', help='bones, chains, pivot, rest panel angles + <char>_bones.jpg')
    q.add_argument('blend'); q.add_argument('--cam'); q.add_argument('--out'); q.add_argument('--json-out')

    q = sp.add_parser('frames', help='extract reference frames + contact sheet (+ masks)')
    q.add_argument('video'); q.add_argument('--cam', required=True)
    q.add_argument('--times'); q.add_argument('--every', type=float)
    q.add_argument('--t0', type=float); q.add_argument('--t1', type=float)
    q.add_argument('--out', required=True); q.add_argument('--mask', action='store_true')
    q.add_argument('--tol', type=float, default=0.2); q.add_argument('--cols', type=int, default=4)
    q.add_argument('--sheet', help='the split sheet PNG the video started from (aligns frames to the cam framing)')
    q.add_argument('--calib', help='reuse a calib.json written by an earlier frames --sheet run')
    q.add_argument('--no-crop', action='store_true', help='contact sheet keeps the full framing')

    q = sp.add_parser('pose', help='render poses, compare with target frames (one image)')
    q.add_argument('blend'); q.add_argument('--cam', required=True)
    q.add_argument('--pose', action='append', help='pose json; repeat for several poses in one image')
    q.add_argument('--target', action='append', help='target frame; one per --pose, or one for all')
    q.add_argument('--from-action', help='read the pose of a baked clip (action json, or clip:<name>) at --t')
    q.add_argument('--t', type=float); q.add_argument('--save-pose', help='write the (read back / grounded) pose json')
    q.add_argument('--out', required=True); q.add_argument('--render-out')
    q.add_argument('--tol', type=float, default=0.2); q.add_argument('--joints', action='store_true')
    q.add_argument('--no-skeleton', action='store_true', help='no blue/orange skeleton over OURS')
    q.add_argument('--no-crop', action='store_true', help='keep the full sheet framing in the comparison image')

    q = sp.add_parser('solve', help='bone positions + lowest vertex per side for a pose (numbers, no render)')
    q.add_argument('blend'); q.add_argument('--pose', required=True); q.add_argument('--json-out')

    q = sp.add_parser('bake', help='timed poses -> Action (in the blend, or --out-action JSON for parallel agents)')
    q.add_argument('blend'); q.add_argument('--clip'); q.add_argument('--keys', required=True)
    q.add_argument('--loop', action='store_true'); q.add_argument('--fps', type=float); q.add_argument('--length', type=float)
    q.add_argument('--out-action', help='write the baked action as JSON and leave the blend untouched')
    q.add_argument('--save-blend-too', action='store_true'); q.add_argument('--no-save', action='store_true')
    q.add_argument('--keep-root-motion', action='store_true', help='do not remove the horizontal root drift')

    q = sp.add_parser('merge', help='re-bake many action JSON files on the current rig into the blend (one save)')
    q.add_argument('blend'); q.add_argument('files', nargs='+')
    q.add_argument('--replace', action='store_true', help='allow two files with the same clip name (the later wins)')

    q = sp.add_parser('strip', help='review image (+mp4): reference on top, our render below')
    q.add_argument('blend'); q.add_argument('--cam', required=True)
    q.add_argument('--action-json'); q.add_argument('--clip')
    q.add_argument('--video'); q.add_argument('--sheet'); q.add_argument('--calib')
    q.add_argument('--t0', type=float); q.add_argument('--t1', type=float, help='only checked: reference time = t0 + clip time')
    q.add_argument('--n', type=int, default=8)
    q.add_argument('--out'); q.add_argument('--mp4'); q.add_argument('--mp4-fps', type=int, default=15)
    q.add_argument('--cols', type=int, default=4); q.add_argument('--width', type=int, default=1024)
    q.add_argument('--tol', type=float, default=0.2)
    q.add_argument('--no-crop', action='store_true', help='keep the full sheet framing')
    q.add_argument('--no-view', action='store_true', help='ignore the keys\' view_offset/view_scale framing corrections')

    q = sp.add_parser('export', help='GLB with all actions as clips + clips manifest')
    q.add_argument('blend'); q.add_argument('--out', required=True); q.add_argument('--clips-json')

    q = sp.add_parser('fit', help='refine the listed bones to maximise silhouette IoU against a target frame')
    q.add_argument('blend'); q.add_argument('--cam', required=True); q.add_argument('--pose', required=True)
    q.add_argument('--target', required=True)
    q.add_argument('--bones', required=True, help='a,b,c (+ view_offset, view_scale, root.loc)')
    q.add_argument('--axes', default='rx,ry'); q.add_argument('--limit', type=float, default=45.0, help='max change per angle (deg)')
    q.add_argument('--out-pose'); q.add_argument('--out'); q.add_argument('--tol', type=float, default=0.2)
    q.add_argument('--color', type=float, default=1.0, help='weight of the colour-agreement term (0 = silhouette only)')

    q = sp.add_parser('cycle', help='find the loop length of a cyclic motion in a reference video')
    q.add_argument('video'); q.add_argument('--cam', required=True); q.add_argument('--sheet'); q.add_argument('--calib')
    q.add_argument('--t0', type=float, required=True); q.add_argument('--t1', type=float)
    q.add_argument('--min', type=float, default=0.25); q.add_argument('--tol', type=float, default=0.2)

    q = sp.add_parser('mirror', help='left/right mirror of a pose json or a whole keys.json')
    q.add_argument('pose', nargs='?'); q.add_argument('--keys'); q.add_argument('--out', required=True)
    q.add_argument('--blend', help='character blend (uses rig.json next to it)'); q.add_argument('--rig', help='rig.json')

    q = sp.add_parser('retime', help='scale every key time, the length and the events of a keys.json')
    q.add_argument('keys'); q.add_argument('--scale', type=float, required=True); q.add_argument('--out', required=True)

    q = sp.add_parser('selftest', help='pose-math unit test on a blend')
    q.add_argument('blend'); q.add_argument('--trials', type=int, default=20)
    return p


CMDS = {'prep': c_prep, 'info': c_info, 'frames': c_frames, 'pose': c_pose, 'solve': c_solve, 'selftest': c_selftest,
        'bake': c_bake, 'merge': c_merge, 'strip': c_strip, 'export': c_export, 'fit': c_fit, 'cycle': c_cycle,
        'mirror': c_mirror, 'retime': c_retime}


def main(argv):
    p = build_parser()
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        if e.code:
            print('###AK### ' + json.dumps({'ok': False, 'error': 'bad arguments (see usage above)'}))
        raise
    try:
        res = CMDS[a.cmd](a)
        finish({'cmd': a.cmd} | res, ok=res.get('ok', True) if isinstance(res, dict) else True)
    except AKError as e:
        finish({'cmd': a.cmd, 'error': str(e)}, ok=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        finish({'cmd': a.cmd, 'error': f'{type(e).__name__}: {e}'}, ok=False)
