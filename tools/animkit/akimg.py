"""animkit image helpers (numpy + Pillow only)."""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONTS = {}


def font(size=14):
    if size not in _FONTS:
        f = None
        for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc',
                  '/Library/Fonts/Arial.ttf'):
            if os.path.exists(p):
                try:
                    f = ImageFont.truetype(p, size)
                    break
                except Exception:
                    pass
        _FONTS[size] = f or ImageFont.load_default(size=size)
    return _FONTS[size]


def text(draw, xy, s, size=14, fill=(0, 0, 0), stroke=(255, 255, 255), sw=2, anchor='la'):
    draw.text(xy, s, font=font(size), fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def load_cam(p):
    cam = json.load(open(p))
    for k in ('width', 'height', 'ppm', 'front_w', 'side_w', 'centre_x', 'centre_y', 'ground_z'):
        if k not in cam:
            raise ValueError(f'cam.json lacks {k}')
    return cam


def bg_rgb(cam):
    return np.array([float(v) for v in cam.get('bg', [1, 1, 1])][:3], dtype=np.float32)


def compose_render(cam, front_png, side_png):
    """-> (rgb float HxWx3 0..1 composed over bg with the sheet divider, alpha mask HxW bool)"""
    bg = bg_rgb(cam)
    tiles, alphas = [], []
    for p in (front_png, side_png):
        a = np.asarray(Image.open(p).convert('RGBA'), dtype=np.float32) / 255.0
        al = a[..., 3:4]
        tiles.append(a[..., :3] * al + bg * (1 - al))
        alphas.append(a[..., 3] > 0.5)
    rgb = np.concatenate(tiles, axis=1)
    mask = np.concatenate(alphas, axis=1)
    fw = cam['front_w']
    rgb[:, fw - 2:fw + 2, :] = 0.25
    return rgb, mask


def to_img(rgb):
    return Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8))


def load_rgb(p, cam=None):
    im = Image.open(p).convert('RGB')
    if cam is not None and im.size != (cam['width'], cam['height']):
        im = im.resize((cam['width'], cam['height']), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def _erode(m, r=1):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o &= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def _dilate(m, r=1):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def _fit_bg(lum, keep, step=4):
    """least-squares quadratic surface lum(x,y) through the pixels marked keep (bg); returns the full surface"""
    H, W = lum.shape
    yy, xx = np.mgrid[0:H:step, 0:W:step]
    k = keep[::step, ::step]
    x = xx[k] / W - 0.5; y = yy[k] / H - 0.5
    if x.size < 20:
        return np.full_like(lum, np.median(lum))
    A = np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)
    c, *_ = np.linalg.lstsq(A, lum[::step, ::step][k], rcond=None)
    Y, X = np.mgrid[0:H, 0:W]
    X = X / W - 0.5; Y = Y / H - 0.5
    return c[0] + c[1] * X + c[2] * Y + c[3] * X * X + c[4] * X * Y + c[5] * Y * Y


def ground_y(cam):
    """pixel row of the floor (world z = ground_z) in the sheet framing"""
    return int(round(cam['height'] * (1 - cam.get('ground_frac', 0.08))))


def silhouette(rgb, cam, tol=0.2, clean=1, ctol=0.10, floor_px=3):
    """character mask of a sheet-like image (rendered sheet or Seedance frame).
    Background = a smooth grey surface fitted per panel (handles off-white gradients / vignettes). A pixel is character
    when its colourfulness (max-min channel) > ctol OR its brightness differs from the fitted bg by more than tol.
    Below the floor line (+floor_px) only colourful pixels count: grey/dark floor shadows stay background.
    Pure white or grey characters need a coloured --bg sheet."""
    fw = cam['front_w']
    m = np.zeros(rgb.shape[:2], bool)
    gy = ground_y(cam) + floor_px if floor_px is not None else None
    for sl in (slice(0, fw), slice(fw, None)):
        p = rgb[:, sl]
        lum = p.mean(axis=2)
        chroma = p.max(axis=2) - p.min(axis=2)
        fg = (chroma > ctol) | (lum < 0.45)
        for _ in range(2):
            bgs = _fit_bg(lum, ~_dilate(fg, 3))
            fg = (chroma > ctol) | (np.abs(lum - bgs) > tol)
        if gy is not None and 0 <= gy < fg.shape[0]:
            fg[gy:] = chroma[gy:] > ctol
        m[:, sl] = fg
    m[:, max(0, fw - 5):fw + 5] = False          # divider
    if clean:
        m = _dilate(_erode(m, clean), clean)      # opening: drop compression speckle
        m = _erode(_dilate(m, clean), clean)      # closing: fill pinholes
    return m


def panel_iou(cam, ma, mb):
    fw = cam['front_w']
    res = {}
    for name, sl in (('front', slice(0, fw)), ('side', slice(fw, None))):
        a, b = ma[:, sl], mb[:, sl]
        u = np.logical_or(a, b).sum()
        res[name] = round(float(np.logical_and(a, b).sum() / u), 4) if u else 0.0
    return res


def diff_map(cam, mt, mr):
    """green = both, red = only target (reference), blue = only render"""
    H, W = mt.shape
    img = np.ones((H, W, 3), np.float32)
    both = mt & mr
    img[both] = (0.55, 0.85, 0.55)
    img[mt & ~mr] = (0.9, 0.15, 0.15)
    img[mr & ~mt] = (0.15, 0.3, 0.95)
    fw = cam['front_w']
    img[:, fw - 2:fw + 2, :] = 0.25
    return img


def label(img, s, size=18, xy=(8, 6)):
    d = ImageDraw.Draw(img)
    text(d, xy, s, size=size)
    return img


def grid(cells, cols, cell_w, pad=4, bg=(40, 40, 40)):
    """cells: list of PIL images (all same aspect) -> one grid image"""
    if not cells:
        raise ValueError('no cells')
    w0, h0 = cells[0].size
    cell_h = int(round(cell_w * h0 / w0))
    rows = (len(cells) + cols - 1) // cols
    out = Image.new('RGB', (cols * cell_w + (cols + 1) * pad, rows * cell_h + (rows + 1) * pad), bg)
    for i, c in enumerate(cells):
        r, k = divmod(i, cols)
        out.paste(c.resize((cell_w, cell_h), Image.LANCZOS), (pad + k * (cell_w + pad), pad + r * (cell_h + pad)))
    return out


def cap(img, long_side=1024):
    """shrinks an image so that its long side is <= long_side (agents may read it directly)"""
    w, h = img.size
    if long_side and max(w, h) > long_side:
        k = long_side / max(w, h)
        img = img.resize((max(1, int(round(w * k))), max(1, int(round(h * k)))), Image.LANCZOS)
    return img


def save_jpg(img, path, q=88, long_side=1024):
    """saves (JPEG, or PNG by extension); long side capped at 1024 px unless long_side=None"""
    img = cap(img, long_side)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    if path.lower().endswith('.png'):
        img.save(path)
    else:
        img.convert('RGB').save(path, quality=q)
    return img.size


def grid_pages(cells, cols, cell_w, max_h=1024, pad=4):
    """like grid() but split into pages whose height stays <= max_h -> list of images"""
    w0, h0 = cells[0].size
    cell_h = int(round(cell_w * h0 / w0))
    rows_per = max(1, (max_h - pad) // (cell_h + pad))
    per = rows_per * cols
    return [grid(cells[i:i + per], cols, cell_w, pad) for i in range(0, len(cells), per)]


def draw_ground(img, cam, box=None, color=(0, 150, 0)):
    """green floor line (cam ground) across a PIL sheet image, or across a crop_panels() image when box is given"""
    y = ground_y(cam) - (box[0] if box else 0)
    if 0 <= y < img.size[1]:
        d = ImageDraw.Draw(img)
        d.line([(0, y), (img.size[0], y)], fill=color, width=2)
    return img


def convex_hull(pts):
    pts = sorted(set((float(x), float(y)) for x, y in pts))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def trunk_mask(cam, joints, grow_m=0.06):
    """HxW bool mask of the trunk (convex hull of the trunk joints of each panel, grown by grow_m metres)"""
    H, W, fw = cam['height'], cam['width'], cam['front_w']
    m = np.zeros((H, W), bool)
    r = max(1, int(round(grow_m * cam['ppm'])))
    for panel, ox, pw in (('front', 0, fw), ('side', fw, W - fw)):
        pts = [j[panel] for j in joints.values() if j.get('torso')]
        if len(pts) < 2:
            continue
        hull = convex_hull(pts)
        im = Image.new('L', (pw, H), 0)
        d = ImageDraw.Draw(im)
        if len(hull) >= 3:
            d.polygon(hull, fill=255)
        d.line(hull + hull[:1], fill=255, width=2 * r)      # grow by r: thick outline + round corners
        for x, y in hull:
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        m[:, ox:ox + pw] = np.asarray(im) > 127
    return m

def ffprobe_duration(video):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate',
                        '-of', 'json', video], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffprobe failed: {r.stderr.strip()[:300]}')
    j = json.loads(r.stdout)
    st = [s for s in j.get('streams', []) if 'width' in s]
    return float(j['format']['duration']), (st[0]['width'], st[0]['height']) if st else None


_FPS = {}


def video_fps(video):
    if video not in _FPS:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                            '-of', 'csv=p=0', video], capture_output=True, text=True)
        num, _, den = (r.stdout.strip().split('\n')[0] or '24/1').partition('/')
        _FPS[video] = float(num) / float(den or 1)
    return _FPS[video]


def snap(t, fps):
    """time -> (frame index, exact frame time)"""
    n = max(0, int(round(float(t) * fps)))
    return n, n / fps


def _seek(t, fps):
    """seek point that returns exactly frame round(t*fps): half a frame before its timestamp"""
    if not fps:
        return f'{t:.4f}'
    n, _ = snap(t, fps)
    return f'{max(0.0, (n - 0.5) / fps):.6f}'


def extract_frame(video, t, cam, path, fps=None):
    """one frame at time t (s), scaled to the cam size, saved as PNG (fps given: the frame nearest t, exactly)"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', _seek(t, fps), '-i', video, '-frames:v', '1',
                        '-vf', f"scale={cam['width']}:{cam['height']}:flags=lanczos", path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(path):
        raise RuntimeError(f'ffmpeg could not read t={t} from {video}: {r.stderr.strip()[:300]}')
    return path


# ------------------------------------------------------------------ video -> sheet calibration
def find_divider(rgb):
    """x of the thin dark vertical divider line between the panels (searched in the middle 40%)"""
    lum = rgb.mean(axis=2)
    W = lum.shape[1]
    best, bx = -1.0, W // 2
    for x in range(int(W * 0.3), int(W * 0.7)):
        d = np.minimum(lum[:, x - 3], lum[:, x + 3]) - lum[:, x]
        s = float((d > 0.04).mean())
        if s > best + 1e-9:
            best, bx = s, x
    xs = [x for x in range(int(W * 0.3), int(W * 0.7))
          if float(((np.minimum(lum[:, x - 3], lum[:, x + 3]) - lum[:, x]) > 0.04).mean()) > 0.8 * best]
    xs = [x for x in xs if abs(x - bx) <= 4]
    return (min(xs) + max(xs)) / 2.0 if xs else float(bx), best


def _bounds(m):
    rows = np.where(m.sum(axis=1) > 2)[0]
    cols = np.where(m.sum(axis=0) > 2)[0]
    if len(rows) < 10 or len(cols) < 5:
        raise RuntimeError('no character silhouette found for calibration')
    t, b = float(rows[0]), float(rows[-1])
    # horizontal centre from the upper 80% only (floor shadows smear the bottom rows sideways)
    up = m[int(t):int(t + 0.8 * (b - t)) + 1]
    xs = np.nonzero(up)[1]
    return t, b, float(np.median(xs)) if xs.size else float((cols[0] + cols[-1]) / 2)


def calibrate(video_rgb0, sheet_rgb, cam, tol=0.2):
    """frame 0 of the video (native px) vs the split sheet it started from -> per-panel uniform scale + offset"""
    H, W = video_rgb0.shape[:2]
    dx, score = find_divider(video_rgb0)
    vcam = dict(cam, front_w=int(round(dx)))
    vm = silhouette(video_rgb0, vcam, tol)
    sm = silhouette(sheet_rgb, cam, tol)
    fw = cam['front_w']
    res = {'video_size': [W, H], 'divider_x': dx, 'divider_score': round(score, 3), 'panels': {}}
    for name, vsl, ssl, vox, sox in (('front', slice(0, int(dx) - 4), slice(0, fw), 0, 0),
                                     ('side', slice(int(dx) + 5, W), slice(fw, None), int(dx) + 5, fw)):
        vt, vb, vc = _bounds(vm[:, vsl]); st, sb, sc = _bounds(sm[:, ssl])
        s = (sb - st) / max(1.0, vb - vt)
        c = {'scale': s, 'video_cx': vc + vox, 'video_bottom': vb, 'sheet_cx': sc, 'sheet_bottom': sb,
             'video_x0': vox, 'video_x1': (int(dx) - 4) if name == 'front' else W}
        c['iou_bounds'] = _panel_fit(vm, sm[:, ssl], c, H)
        best = (c['iou_bounds'], 0.0, 0.0, 1.0)
        # refine: offset (coarse, fine) and scale, maximising silhouette IoU against the sheet
        for stage, (rng, step, sc_list) in enumerate((((-48, 48), 4, [1.0]), ((0, 0), 1, [0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03]),
                                                     ((-4, 4), 1, [1.0]))):
            _, bx, by, bs = best
            for k in sc_list:
                for ox in range(rng[0], rng[1] + 1, step):
                    for oy in range(rng[0], rng[1] + 1, step):
                        t = dict(c, video_cx=c['video_cx'] + bx + ox, video_bottom=c['video_bottom'] + by + oy, scale=c['scale'] * bs * k)
                        v = _panel_fit(vm, sm[:, ssl], t, H)
                        if v > best[0] + 1e-6:
                            best = (v, bx + ox, by + oy, bs * k)
        v, bx, by, bs = best
        c.update(video_cx=c['video_cx'] + bx, video_bottom=c['video_bottom'] + by, scale=c['scale'] * bs, iou=round(v, 4))
        res['panels'][name] = c
    return res


def _panel_fit(vmask, smask_panel, c, H):
    """IoU of the video mask warped into the sheet panel (half resolution for speed)"""
    pw = smask_panel.shape[1]
    src = Image.fromarray((vmask * 255).astype(np.uint8)).crop((int(c['video_x0']), 0, int(c['video_x1']), vmask.shape[0]))
    s = c['scale']; cx = c['video_cx'] - c['video_x0']
    h = 2.0
    a = (h / s, 0, cx - c['sheet_cx'] / s, 0, h / s, c['video_bottom'] - c['sheet_bottom'] / s)
    w = np.asarray(src.transform((pw // 2, H // 2), Image.AFFINE, a, resample=Image.NEAREST)) > 127
    sm = smask_panel[::2, ::2][:w.shape[0], :w.shape[1]]
    u = np.logical_or(w, sm).sum()
    return float(np.logical_and(w, sm).sum() / u) if u else 0.0


def rectify(video_rgb, calib, cam):
    """native video frame -> image in the cam.json sheet framing (same layout as our renders)"""
    H, fw, sw = cam['height'], cam['front_w'], cam['side_w']
    src = Image.fromarray(np.clip(video_rgb * 255 + 0.5, 0, 255).astype(np.uint8))
    tiles = []
    for name, pw in (('front', fw), ('side', sw)):
        c = calib['panels'][name]
        s = c['scale']
        crop = src.crop((int(c['video_x0']), 0, int(c['video_x1']), src.size[1]))
        border = np.concatenate([np.asarray(crop)[:4].reshape(-1, 3), np.asarray(crop)[-4:].reshape(-1, 3)])
        fill = tuple(int(v) for v in np.median(border, axis=0))
        cx = c['video_cx'] - c['video_x0']
        a = (1 / s, 0, cx - c['sheet_cx'] / s, 0, 1 / s, c['video_bottom'] - c['sheet_bottom'] / s)
        tiles.append(np.asarray(crop.transform((pw, H), Image.AFFINE, a, resample=Image.BILINEAR, fillcolor=fill),
                                dtype=np.float32) / 255.0)
    rgb = np.concatenate(tiles, axis=1)
    rgb[:, fw - 2:fw + 2, :] = 0.25
    return rgb


def extract_native(video, t, path, fps=None):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', _seek(t, fps), '-i', video, '-frames:v', '1', path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(path):
        raise RuntimeError(f'ffmpeg could not read t={t} from {video}: {r.stderr.strip()[:300]}')
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0


# ------------------------------------------------------------------ crop to the character
def union_box(cam, masks, margin=24, ground=True):
    """one crop box per panel covering every mask (same y range for both panels) -> (y0, y1, (fx0, fx1), (sx0, sx1)).
    ground=True keeps the floor line inside the box."""
    fw, H, W = cam['front_w'], cam['height'], cam['width']
    m = np.zeros((H, W), bool)
    for k in masks:
        m |= k
    rows = np.where(m.any(axis=1))[0]
    if rows.size == 0:
        return None
    y0 = max(0, rows[0] - margin); y1 = min(H, rows[-1] + margin + 1)
    if ground:
        y1 = min(H, max(y1, ground_y(cam) + 12))
    boxes = []
    for x0p, x1p in ((0, fw), (fw, W)):
        cols = np.where(m[:, x0p:x1p].any(axis=0))[0]
        if cols.size == 0:
            boxes.append((x0p, x1p)); continue
        boxes.append((max(x0p, x0p + cols[0] - margin), min(x1p, x0p + cols[-1] + margin + 1)))
    return y0, y1, boxes[0], boxes[1]


def crop_panels(img, box):
    """PIL sheet image -> front crop | side crop (3 px divider)"""
    if box is None:
        return img
    y0, y1, (a0, a1), (b0, b1) = box
    f = img.crop((a0, y0, a1, y1)); s = img.crop((b0, y0, b1, y1))
    out = Image.new('RGB', (f.size[0] + s.size[0] + 3, y1 - y0), (64, 64, 64))
    out.paste(f, (0, 0)); out.paste(s, (f.size[0] + 3, 0))
    return out
