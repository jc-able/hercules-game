"""animkit Blender backend. Run only through `tools/ak` (it starts Blender headless with --factory-startup).

  Blender -b --factory-startup --python tools/animkit/ak_blender.py -- <cmd> <json-args-file>

Each command reads its arguments from a JSON file, writes raw outputs (PNGs, JSON) and prints one line
`###AKB### {json}`. Image composition / text drawing happens in tools/ak (Pillow), not here.
"""
import bpy, sys, os, json, math, time, traceback, re, hashlib, importlib.util, copy
import numpy as np
from mathutils import Matrix, Vector, Euler, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aknames  # noqa: E402

T0 = time.time()
WARN = []


def out(d):
    print('###AKB### ' + json.dumps(d))
    sys.stdout.flush()


def deep(x):
    return json.loads(json.dumps(x))


# ------------------------------------------------------------------ scene helpers
def find_armature():
    arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    if not arms:
        raise RuntimeError('no armature in the blend')
    return max(arms, key=lambda o: len(o.data.bones))


def helper_meshes():
    scene = bpy.context.scene
    shapes = {pb.custom_shape for a in scene.objects if a.type == 'ARMATURE' for pb in a.pose.bones if pb.custom_shape}
    return [o for o in scene.objects if o.type == 'MESH' and (o in shapes or not [m for m in o.data.materials if m])]


def hide_helpers():
    for o in helper_meshes():
        o.hide_render = True


def material_images():
    """images used by Image Texture nodes of any material"""
    res = set()
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    res.add(n.image)
    return res


def missing_images():
    res = []
    for im in bpy.data.images:
        if im.source not in ('FILE', 'SEQUENCE', 'TILED') or im.packed_file or not im.filepath:
            continue
        p = bpy.path.abspath(im.filepath, library=im.library)
        if not os.path.exists(p):
            res.append({'image': im.name, 'file': os.path.normpath(p)})
    return res


def open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    hide_helpers()
    miss = missing_images()
    if miss:
        WARN.append(f'{len(miss)} texture file(s) missing (renders/export lose them): '
                    + ', '.join(m['file'] for m in miss[:4]) + ' -- never copy a character blend; use it in place')
    return find_armature()


def bone_order(arm):
    """bones parents-first"""
    res = []

    def walk(b):
        res.append(b)
        for c in b.children:
            walk(c)
    for b in arm.data.bones:
        if b.parent is None:
            walk(b)
    return res


def chains_of(arm):
    """maximal single-child runs of 3+ bones (auto chains), named after their first bone"""
    chains = {}
    for b in bone_order(arm):
        if b.parent is not None and len(b.parent.children) == 1:
            continue          # inside a run started higher up
        run = [b]
        while len(run[-1].children) == 1:
            run.append(run[-1].children[0])
        if len(run) >= 3:
            chains[b.name] = [x.name for x in run]
    return chains


def rig_json_for(blend_path):
    p = os.path.join(os.path.dirname(os.path.abspath(blend_path)), 'rig.json')
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception as e:
            WARN.append(f'rig.json next to the blend is not valid JSON: {e}')
            return {}
    return {}


def load_driven(rj, blend_path):
    """rig.json "driven": {"bones": [...], "code": "path/to/file.py:function" | "path/to/file.py (function(rest, posed))"}
    -> (set of bone names, function(rest, posed) -> {bone: 4x4}) ; path is tried relative to the blend's folder and
    every folder above it (repo-relative paths work)."""
    d = rj.get('driven') if rj else None
    if not d:
        return set(), None, None
    bones = set(d.get('bones') or [])
    code = str(d.get('code') or '')
    m = re.search(r'([\w./\\-]+\.py)', code)
    if not m:
        raise RuntimeError(f'rig.json driven.code names no .py file: {code!r}')
    rel = m.group(1)
    rest = code[m.end():]
    fm = re.match(r'\s*:\s*(\w+)', rest) or re.search(r'(\w+)\s*\(', rest)
    if not fm:
        raise RuntimeError(f'rig.json driven.code names no function: {code!r} (use "file.py:function")')
    fn_name = fm.group(1)
    cands = [rel] if os.path.isabs(rel) else []
    dd = os.path.dirname(os.path.abspath(blend_path))
    while True:
        cands.append(os.path.join(dd, rel))
        up = os.path.dirname(dd)
        if up == dd:
            break
        dd = up
    path = next((c for c in cands if os.path.exists(c)), None)
    if path is None:
        raise RuntimeError(f'rig.json driven.code file not found: {rel} (looked next to the blend and in every parent folder)')
    spec = importlib.util.spec_from_file_location('ak_driven_' + hashlib.sha1(path.encode()).hexdigest()[:8], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, fn_name, None)
    if fn is None:
        raise RuntimeError(f'{path} has no function {fn_name}')
    return bones, fn, f'{os.path.relpath(path, os.path.dirname(os.path.abspath(blend_path)))}:{fn_name}'


# ------------------------------------------------------------------ pose math
def rot_xyz(rx, ry, rz):
    """R = Rz * Ry * Rx, degrees, in world (view) axes"""
    return (Matrix.Rotation(math.radians(rz), 3, 'Z') @ Matrix.Rotation(math.radians(ry), 3, 'Y')
            @ Matrix.Rotation(math.radians(rx), 3, 'X'))


class Rig:
    def __init__(self, arm, rigjson=None, blend_path=None):
        self.arm = arm
        mw = arm.matrix_world
        loc, q, sc = mw.decompose()
        self.Ra = q.to_matrix()                 # armature axes -> world axes
        self.RaT = self.Ra.transposed()
        self.s = float(sum(sc) / 3.0)
        self.order = bone_order(arm)
        self.names = [b.name for b in self.order]
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        self.children = {b.name: [c.name for c in b.children] for b in arm.data.bones}
        self.deform = {b.name: b.use_deform for b in arm.data.bones}
        rj = rigjson or {}
        self.rj = rj
        self.chains = chains_of(arm)
        for k, v in (rj.get('chains') or {}).items():
            if isinstance(v, list) and all(n in self.rest for n in v):
                self.chains[k] = v
        self.roots = [b.name for b in self.order if b.parent is None]
        # driven bones (rig.json "driven"): set by code from the other bones after every solve
        self.driven, self.driven_fn, self.driven_code = (set(), None, None)
        if blend_path is not None:
            self.driven, self.driven_fn, self.driven_code = load_driven(rj, blend_path)
        self.driven = {n for n in self.driven if n in self.rest}
        self.driven_all = set()
        for n in self.names:
            if n in self.driven or (self.parent[n] in self.driven_all):
                self.driven_all.add(n)
        # pivot of root.rot: rig.json "pivot", else the root-most deforming bone (the hips)
        depth = {}
        for n in self.names:
            depth[n] = 0 if self.parent[n] is None else depth[self.parent[n]] + 1
        pv = rj.get('pivot')
        if pv in self.rest:
            self.pivot = pv
        else:
            deforming = [n for n in self.names if self.deform[n] and n not in self.driven_all]
            self.pivot = min(deforming, key=lambda n: depth[n]) if deforming else self.roots[0]
        # aim vector per bone (armature space): toward the single child's head, else the bone's Y axis
        self.aimvec = {}
        for n in self.names:
            kids = [c for c in self.children[n] if c not in self.driven_all]
            v = None
            if len(kids) == 1:
                v = self.rest[kids[0]].translation - self.rest[n].translation
                if v.length < 1e-6:
                    v = None
            self.aimvec[n] = (v if v is not None else self.rest[n].to_3x3().col[1]).normalized()
        # left/right partners and sides
        self.mirror, self.unpaired = aknames.mirror_map(self.names, rj.get('pairs'))
        px = (self.Ra @ self.rest[self.pivot].translation).x
        self.side = {}
        for n in self.names:
            if self.mirror.get(n, n) == n:
                self.side[n] = None
            else:
                x = (self.Ra @ (self.rest[n].translation + self.aimvec[n] * 1e-3)).x
                self.side[n] = 'l' if x > px else 'r'
        # trunk: pivot + the centre bones that connect it to every sided limb (for the limb IoU)
        self.torso = {self.pivot}
        for n in self.names:
            p = self.parent[n]
            if self.side[n] and p and not self.side[p] and n not in self.driven_all:
                self.torso.add(n)
                q_ = p
                while q_ is not None and q_ not in self.torso:
                    self.torso.add(q_)
                    q_ = self.parent[q_]
        self.torso = {n for n in self.torso if self.deform[n]}
        self.chain_axes = {k: self._chain_axes(v) for k, v in self.chains.items()}

    # -- helpers
    def world_dir(self, v_arm):
        return (self.Ra @ v_arm).normalized()

    def rest_dir_world(self, n):
        return self.world_dir(self.aimvec[n])

    def _chain_axes(self, names):
        h0 = self.rest[names[0]].translation
        d = None
        if len(names) > 1:
            d = self.rest[names[-1]].translation - h0
            if d.length < 1e-6:
                d = None
        d = self.world_dir(d if d is not None else self.aimvec[names[0]])
        cls = aknames.chain_class(d)
        up_t, side_t = aknames.chain_targets(cls)
        up = d.cross(Vector(up_t)).normalized()
        side = d.cross(Vector(side_t)).normalized()
        return {'class': cls, 'dir': d, 'up': up, 'side': side}

    def chain_report(self, name):
        ax = self.chain_axes[name]
        d = ax['dir']
        res = {'class': ax['class'], 'rest_dir': [round(v, 3) for v in d]}
        for key in ('up', 'side'):
            d2 = Matrix.Rotation(math.radians(10), 3, ax[key]) @ d
            f0, s0 = aknames.panel_angles(d, 0.05); f1, s1 = aknames.panel_angles(d2, 0.05)
            df = abs(((f1 - f0) + 180) % 360 - 180) if None not in (f0, f1) else 0.0
            ds = abs(((s1 - s0) + 180) % 360 - 180) if None not in (s0, s1) else 0.0
            tgt = aknames.chain_targets(ax['class'])[0 if key == 'up' else 1]
            word = {(0.0, -1.0, 0.0): 'FORWARD (-Y)', (0.0, 0.0, 1.0): 'UP (+Z)', (1.0, 0.0, 0.0): "the character's LEFT (+X)"}[tgt]
            res['bend_' + key] = f"+ moves the tip toward {word}; seen best in the {'FRONT' if df >= ds else 'SIDE'} panel"
        return res

    def to_arm(self, Rw):
        return self.RaT @ Rw @ self.Ra

    def aim_rotation(self, name, front, side, twist):
        r = self.rest_dir_world(name)
        d = Vector(aknames.aim_direction(front, side, tuple(r)))
        R = r.rotation_difference(d).to_matrix()
        if twist:
            R = Matrix.Rotation(math.radians(float(twist)), 3, d) @ R
        return R

    def _check_bone(self, name):
        if name not in self.rest:
            raise KeyError(f'unknown bone {name!r}')
        if name in self.driven_all:
            raise KeyError(f'bone {name!r} is driven by code ({self.driven_code}, rig.json "driven"): do not pose it, '
                           f'it follows the other bones automatically')

    def solve(self, pose):
        """pose dict -> {bone: posed 4x4 armature-space matrix}. view_offset / view_scale are NOT applied here (render only)"""
        pose = pose or {}
        space = pose.get('space', 'absolute')
        spec = {}
        for name, v in (pose.get('bones') or {}).items():
            self._check_bone(name)
            v = dict(v)
            aimk = [k for k in ('front', 'side', 'twist') if k in v]
            eulk = [k for k in ('rx', 'ry', 'rz') if k in v]
            if aimk and eulk:
                raise ValueError(f'bone {name!r}: give either front/side/twist (aim) or rx/ry/rz, not both')
            if aimk:
                if v.get('front') is None and v.get('side') is None:
                    raise ValueError(f'bone {name!r}: aim needs "front" and/or "side"')
                spec[name] = {'space': 'absolute',
                              'Rw': self.aim_rotation(name, v.get('front'), v.get('side'), v.get('twist', 0.0))}
            else:
                sp = v.get('space', space)
                if sp not in ('absolute', 'local_delta'):
                    raise ValueError('space must be absolute or local_delta')
                spec[name] = {'space': sp, 'Rw': rot_xyz(float(v.get('rx', 0.0)), float(v.get('ry', 0.0)), float(v.get('rz', 0.0)))}
        chains = pose.get('chain')
        if chains is not None:
            for ch in (chains if isinstance(chains, list) else [chains]):
                names = self.chains.get(ch.get('name'))
                if names is None:
                    raise KeyError(f"unknown chain {ch.get('name')!r}; chains: {sorted(self.chains)}")
                ax = self.chain_axes[ch['name']]

                def val(key, i):
                    arr = ch.get(key)
                    return float(arr[i]) if arr is not None and i < len(arr) else 0.0
                for i, bn in enumerate(names):
                    if bn in self.driven_all:
                        continue
                    R = (rot_xyz(val('rx', i), val('ry', i), val('rz', i))
                         @ Matrix.Rotation(math.radians(val('bend_side', i)), 3, ax['side'])
                         @ Matrix.Rotation(math.radians(val('bend_up', i)), 3, ax['up']))
                    spec[bn] = {'space': 'local_delta', 'Rw': R}
        P = {}
        for n in self.names:
            R0 = self.rest[n]
            sp = spec.get(n)
            p = self.parent[n]
            follow = R0.copy() if p is None else P[p] @ (self.rest[p].inverted() @ R0)
            if sp is None:
                M = follow
            else:
                Rd = self.to_arm(sp['Rw'])
                base = R0 if sp['space'] == 'absolute' else follow
                M = Matrix.Translation(follow.translation) @ (Rd @ base.to_3x3().normalized()).to_4x4()
            P[n] = M
        root = pose.get('root') or {}
        rl = root.get('loc', [0, 0, 0]); rr = root.get('rot', [0, 0, 0])
        if any(abs(float(x)) > 1e-9 for x in list(rl) + list(rr)):
            pivot = P[self.pivot].translation.copy()
            Rg = self.to_arm(rot_xyz(*[float(x) for x in rr])).to_4x4()
            t = self.RaT @ Vector([float(x) for x in rl]) / self.s
            G = Matrix.Translation(pivot + t) @ Rg @ Matrix.Translation(-pivot)
            P = {k: G @ v for k, v in P.items()}
        if self.driven_fn is not None:
            D = self.driven_fn(self.rest, P) or {}
            for n in self.names:          # parents first: driven bones from the code, their children follow them
                if n in self.driven and n in D:
                    P[n] = D[n].copy()
                elif n in self.driven_all and n not in self.driven:
                    p = self.parent[n]
                    P[n] = P[p] @ (self.rest[p].inverted() @ self.rest[n])
        return P

    def basis(self, P):
        """posed armature-space matrices -> matrix_basis per bone"""
        B = {}
        for n in self.names:
            p = self.parent[n]
            if p is None:
                B[n] = self.rest[n].inverted() @ P[n]
            else:
                rel = self.rest[p].inverted() @ self.rest[n]
                B[n] = rel.inverted() @ P[p].inverted() @ P[n]
        return B

    def apply(self, pose):
        B = self.basis(self.solve(pose))
        for pb in self.arm.pose.bones:
            pb.matrix_basis = B[pb.name]
        bpy.context.view_layer.update()
        return B

    def rig_hash(self):
        h = hashlib.sha1()
        for n in self.names:
            h.update(f"{n}|{self.parent[n]}|{[round(x, 4) for row in self.rest[n] for x in row]}|".encode())
        h.update(json.dumps(sorted(self.driven)).encode())
        return h.hexdigest()[:12]


# ------------------------------------------------------------------ ground
def body_meshes(arm):
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    res = [o for o in objs if any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers)]
    return res or objs


def ground_stats(rig):
    """lowest world z of the deformed body, overall and per side (x > pivot x = the character's left)"""
    dg = bpy.context.evaluated_depsgraph_get()
    px = (rig.arm.matrix_world @ rig.arm.pose.bones[rig.pivot].head).x
    lows = {'l': [], 'r': []}
    for o in body_meshes(rig.arm):
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        n = len(me.vertices)
        if n:
            co = np.empty(n * 3, np.float64)
            me.vertices.foreach_get('co', co)
            M = np.array(e.matrix_world)
            w = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
            for side, sel in (('l', w[:, 0] > px), ('r', w[:, 0] <= px)):
                if sel.any():
                    lows[side].append(float(w[sel, 2].min()))
        e.to_mesh_clear()
    lz = min(lows['l']) if lows['l'] else None
    rz = min(lows['r']) if lows['r'] else None
    vals = [v for v in (lz, rz) if v is not None]
    r4 = lambda v: None if v is None else round(v, 4)
    return {'lowest_z': r4(min(vals)) if vals else None, 'left_z': r4(lz), 'right_z': r4(rz)}


def apply_grounded(rig, pose):
    """applies the pose; root.ground ('lowest'|'left'|'right') shifts root.loc z so that foot touches Z=0.
    -> (resolved pose without 'ground', ground stats after)"""
    pose = pose or {}
    g = (pose.get('root') or {}).get('ground')
    rig.apply(pose)
    # merge fix: make sure the evaluated mesh shows THIS pose (the first key of a clip used to read the previous clip's
    # last pose from a stale depsgraph, so root.ground lifted/sank frame 0 of every merged clip after the first)
    bpy.context.evaluated_depsgraph_get().update()
    if not g:
        return pose, ground_stats(rig)
    key = {'lowest': 'lowest_z', 'left': 'left_z', 'right': 'right_z'}.get(g)
    if key is None:
        raise ValueError(f"root.ground must be 'lowest', 'left' or 'right', not {g!r}")
    st = ground_stats(rig)
    if st[key] is None:
        raise ValueError(f'root.ground {g!r}: no mesh on that side')
    p2 = deep(pose)
    r = p2['root']
    loc = [float(v) for v in r.get('loc', [0, 0, 0])]
    loc[2] = round(loc[2] - st[key], 5)
    r['loc'] = loc
    r.pop('ground', None)
    r['grounded'] = g
    rig.apply(p2)
    return p2, ground_stats(rig)


def view_of(pose):
    pose = pose or {}
    off = pose.get('view_offset') or [0, 0, 0]
    sc = float(pose.get('view_scale', 1.0) or 1.0)
    if all(abs(float(v)) < 1e-9 for v in off) and abs(sc - 1) < 1e-9:
        return None
    return [float(v) for v in off], sc


def clear_anim(arm):
    if arm.animation_data:
        arm.animation_data.action = None
        for tr in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(tr)
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def load_pose(p):
    if isinstance(p, dict):
        return p
    return json.load(open(p))


# ------------------------------------------------------------------ rendering
def setup_render(cam):
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_WORKBENCH'
    except TypeError:
        pass
    sh = scene.display.shading
    sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
    try:
        sh.show_shadows = False; sh.show_cavity = False
    except Exception:
        pass
    scene.display.render_aa = '8'
    world = bpy.data.worlds.new('ak_w'); world.color = cam.get('bg', [1, 1, 1]); scene.world = world
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.resolution_percentage = 100
    cd = bpy.data.cameras.new('akcam'); cd.type = 'ORTHO'
    co = bpy.data.objects.new('akcam', cd); scene.collection.objects.link(co); scene.camera = co
    cd.clip_start = 0.01; cd.clip_end = 1000
    return co


def _zc(cam):
    return cam['ground_z'] + (0.5 - cam.get('ground_frac', 0.08)) * cam['height'] / cam['ppm']


def render_panels(cam, co, prefix, view=None):
    """renders <prefix>.front.png and <prefix>.side.png (RGBA, transparent bg). view = (offset xyz m, scale): the
    character is drawn shifted by offset and scaled about the ground point under the frame centre (framing correction)"""
    scene = bpy.context.scene
    H, ppm = cam['height'], cam['ppm']
    fw, sw = cam['front_w'], cam['side_w']
    cx, cy, z0 = cam['centre_x'], cam['centre_y'], cam['ground_z']
    zc = _zc(cam)
    off, s = view if view else ([0.0, 0.0, 0.0], 1.0)
    pv = (cx, cy, z0)
    C = lambda c, i: pv[i] + (c - off[i] - pv[i]) / s
    dist = 200.0
    paths = []
    for name, pw, loc, d in (('front', fw, Vector((C(cx, 0), cy - dist, C(zc, 2))), Vector((0, 1, 0))),
                             ('side', sw, Vector((cx - dist, C(cy, 1), C(zc, 2))), Vector((1, 0, 0)))):
        scene.render.resolution_x = pw; scene.render.resolution_y = H
        co.data.ortho_scale = max(pw, H) / ppm / s
        co.location = loc
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        p = f'{prefix}.{name}.png'
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


def project(cam, w, view=None):
    """world point -> (front px, side px) pixel coords inside each panel"""
    H, ppm = cam['height'], cam['ppm']
    fw, sw = cam['front_w'], cam['side_w']
    if view:
        off, s = view
        pv = (cam['centre_x'], cam['centre_y'], cam['ground_z'])
        w = [pv[i] + s * (w[i] - pv[i]) + off[i] for i in range(3)]
    zc = _zc(cam)
    py = H / 2 - (w[2] - zc) * ppm
    fx = fw / 2 + (w[0] - cam['centre_x']) * ppm
    sx = sw / 2 - (w[1] - cam['centre_y']) * ppm
    return [round(fx, 1), round(py, 1)], [round(sx, 1), round(py, 1)]


def joints(rig, cam, view=None):
    arm = rig.arm
    mw = arm.matrix_world
    res = {}
    for pb in arm.pose.bones:
        h = mw @ pb.head
        # imported bones often have absurd lengths: draw a 0.08 m stub along the bone direction instead of the tail
        d = (mw.to_3x3() @ pb.matrix.to_3x3().col[1]).normalized()
        stub = 0.08 * cam.get('rest_size', [0, 0, 1.9])[2] / 1.9
        t = h + d * stub
        f, s = project(cam, h, view)
        ft, st = project(cam, t, view)
        res[pb.name] = {'front': f, 'side': s, 'front_tail': ft, 'side_tail': st, 'parent': rig.parent[pb.name],
                        'lr': rig.side.get(pb.name), 'torso': pb.name in rig.torso,
                        'deform': rig.deform[pb.name]}
    return res


# ------------------------------------------------------------------ commands
def cmd_prep(a):
    """glb -> clean test blend (no actions, helpers hidden)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a['glb'])
    arm = find_armature()
    clear_anim(arm)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    hide_helpers()
    save_atomic(a['out'])
    return {'out': a['out'], 'bones': len(arm.data.bones)}


def save_atomic(path):
    path = os.path.abspath(path)
    tmp = path + f'.tmp{os.getpid()}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True, compress=False)
    os.replace(tmp, path)
    for ext in ('.blend1',):
        if os.path.exists(tmp + ext):
            os.remove(tmp + ext)


def make_rig(a):
    arm = open_blend(a['blend'])
    rig = Rig(arm, rig_json_for(a['blend']), a['blend'])
    clear_anim(arm)
    return arm, rig


def cmd_info(a):
    arm, rig = make_rig(a)
    rj = rig.rj
    mw = arm.matrix_world
    bones = []
    for b in rig.order:
        f, s = aknames.panel_angles(rig.rest_dir_world(b.name))
        bones.append({'name': b.name, 'parent': rig.parent[b.name],
                      'head': [round(v, 4) for v in (mw @ b.head_local)],
                      'tail': [round(v, 4) for v in (mw @ b.tail_local)],
                      'length_m': round(b.length * rig.s, 4), 'deform': b.use_deform,
                      'children': [c.name for c in b.children], 'lr': rig.side[b.name],
                      'rest_front_deg': f, 'rest_side_deg': s, 'driven': b.name in rig.driven_all})
    meshes = []
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            meshes.append({'name': o.name, 'verts': len(o.data.vertices), 'tris': sum(len(p.vertices) - 2 for p in o.data.polygons),
                           'hidden_helper': o.hide_render, 'parent': o.parent.name if o.parent else None,
                           'parent_bone': o.parent_bone or None})
    res = {'armature': arm.name, 'armature_scale': rig.s, 'n_bones': len(bones), 'bones': bones,
           'roots': rig.roots, 'pivot': rig.pivot, 'chains': rig.chains,
           'chain_axes': {k: rig.chain_report(k) for k in rig.chains},
           'driven': {'bones': sorted(rig.driven_all), 'code': rig.driven_code} if rig.driven else None,
           'pairs': {n: rig.mirror[n] for n in rig.names if rig.mirror.get(n, n) != n},
           'unpaired_sided': rig.unpaired, 'rig_hash': rig.rig_hash(),
           'sockets': rj.get('sockets', {}), 'meshes': meshes, 'missing_images': missing_images(),
           'actions': [{'name': ac.name, 'range': list(ac.frame_range)} for ac in bpy.data.actions]}
    if a.get('cam'):
        cam = json.load(open(a['cam']))
        co = setup_render(cam)
        res['renders'] = render_panels(cam, co, a['prefix'])
        res['joints'] = joints(rig, cam)
    return res


def cmd_pose(a):
    arm, rig = make_rig(a)
    cam = json.load(open(a['cam'])) if a.get('cam') else None
    co = setup_render(cam) if cam else None
    res = []
    for i, p in enumerate(a['poses']):
        resolved = None
        if isinstance(p, dict) and 'from_action' in p:
            p = read_pose_from(rig, p['from_action'], float(p['t']))
            resolved = p
        pin = load_pose(p)
        pose, gst = apply_grounded(rig, pin)
        if pose is not pin and resolved is None:
            resolved = pose
        view = view_of(pose)
        item = {'ground': gst, 'resolved_pose': resolved}
        if cam:
            item['renders'] = render_panels(cam, co, f"{a['prefix']}_{i:03d}", view)
            item['joints'] = joints(rig, cam, view)
        if a.get('bones_out'):
            mw = arm.matrix_world
            bo = {}
            for pb in arm.pose.bones:
                kids = [c for c in rig.children[pb.name]]
                tip = (mw @ arm.pose.bones[kids[0]].head) if len(kids) == 1 else (mw @ pb.head + (mw.to_3x3() @ pb.matrix.to_3x3().col[1]).normalized() * 0.1)
                bo[pb.name] = {'head': [round(v, 4) for v in mw @ pb.head], 'tip': [round(v, 4) for v in tip]}
            item['bones'] = bo
        res.append(item)
    return {'poses': res, 'pivot': rig.pivot}


def cmd_selftest(a):
    """pose math test: random poses, compare each bone's world direction with the direct rotation of its rest direction;
    aim form: random target directions must be reached (0.5 deg). Driven bones (rig.json) are left out."""
    arm, rig = make_rig(a)
    rng = np.random.default_rng(int(a.get('seed', 1)))
    names = [n for n in rig.names if n not in rig.driven_all]
    mw = arm.matrix_world
    Rw = mw.to_quaternion().to_matrix()
    worst = 0.0; worst_follow = 0.0; worst_pos = 0.0; worst_aim = 0.0; n = 0; n_aim = 0; moved = []
    for trial in range(int(a.get('trials', 20))):
        listed = [nm for nm in names if rng.random() < 0.5]
        space = 'absolute' if trial % 2 == 0 else 'local_delta'
        pose = {'space': space, 'bones': {nm: {k: float(rng.uniform(-120, 120)) for k in ('rx', 'ry', 'rz')} for nm in listed}}
        if trial % 3 == 0:
            pose['root'] = {'loc': [float(v) for v in rng.uniform(-1, 1, 3)], 'rot': [float(v) for v in rng.uniform(-90, 90, 3)]}
        P = rig.solve(pose)
        rig.apply(pose)
        G3 = rot_xyz(*pose['root']['rot']) if 'root' in pose else Matrix.Identity(3)
        for pb in arm.pose.bones:
            nm = pb.name
            if nm in rig.driven_all:
                continue
            got = (Rw @ pb.matrix.to_3x3().col[1]).normalized()
            rest_dir = (Rw @ rig.rest[nm].to_3x3().col[1]).normalized()
            par = rig.parent[nm]
            if nm in pose['bones'] and space == 'absolute':
                s = pose['bones'][nm]
                exp = G3 @ rot_xyz(s['rx'], s['ry'], s['rz']) @ rest_dir
                ang = math.degrees(got.angle(exp.normalized(), 0.0)); worst = max(worst, ang); n += 1
                moved.append(math.degrees(got.angle(rest_dir, 0.0)))
            elif nm in pose['bones'] and space == 'local_delta' and par is not None:
                s = pose['bones'][nm]
                ppb = arm.pose.bones[par]
                follow3 = (ppb.matrix.to_3x3() @ (rig.rest[par].inverted() @ rig.rest[nm]).to_3x3())
                fdir = (Rw @ follow3.col[1]).normalized()
                exp = G3 @ rot_xyz(s['rx'], s['ry'], s['rz']) @ G3.transposed() @ fdir
                ang = math.degrees(got.angle(exp.normalized(), 0.0)); worst = max(worst, ang); n += 1
            elif nm not in pose['bones'] and par is not None:
                ppb = arm.pose.bones[par]
                exp_m = ppb.matrix @ (rig.rest[par].inverted() @ rig.rest[nm])
                ang = math.degrees((pb.matrix.to_3x3().col[1]).angle(exp_m.to_3x3().col[1], 0.0))
                worst_follow = max(worst_follow, ang)
                worst_pos = max(worst_pos, (pb.matrix.translation - exp_m.translation).length * rig.s)
            # solver matrix == what Blender evaluated
            worst_pos = max(worst_pos, (pb.matrix.translation - P[nm].translation).length * rig.s)
        # aim form
        aim = {}
        targets = {}
        for nm in names:
            if rng.random() < 0.3:
                d = Vector(rng.normal(size=3)).normalized()
                f, s = aknames.panel_angles(d, 0.0, None)
                if math.hypot(d.x, d.z) < 0.3 or math.hypot(d.y, d.z) < 0.3:
                    continue
                aim[nm] = {'front': f, 'side': s}
                targets[nm] = d
        if aim:
            P = rig.solve({'bones': aim})
            for nm, d in targets.items():
                kids = [c for c in rig.children[nm] if c not in rig.driven_all]
                v = (P[kids[0]].translation - P[nm].translation) if len(kids) == 1 and \
                    (rig.rest[kids[0]].translation - rig.rest[nm].translation).length > 1e-6 else P[nm].to_3x3().col[1]
                got = rig.world_dir(v)
                worst_aim = max(worst_aim, math.degrees(got.angle(d, 0.0))); n_aim += 1
    mean_moved = float(np.mean(moved)) if moved else 0.0
    ok = worst < 0.5 and worst_follow < 0.5 and worst_pos < 1e-4 and mean_moved > 20.0 and worst_aim < 0.5
    return {'ok': ok, 'checked_listed': n, 'checked_aim': n_aim, 'mean_moved_from_rest_deg': mean_moved,
            'worst_listed_deg': worst, 'worst_follow_deg': worst_follow, 'worst_pos_m': worst_pos,
            'worst_aim_deg': worst_aim, 'driven_skipped': sorted(rig.driven_all)}


# ------------------------------------------------------------------ actions
def action_fcurves(action):
    try:
        return list(action.fcurves)          # legacy API (Blender < 5)
    except AttributeError:
        pass
    res = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                res.extend(cb.fcurves)
    return res


INTERP = {'bezier': 'BEZIER', 'ease': 'BEZIER', 'linear': 'LINEAR', 'hold': 'CONSTANT', 'constant': 'CONSTANT'}


def bake_data(rig, spec):
    """spec: {name, fps, loop, length, events, keys: [{t, pose, interp?}], in_place} -> action data dict (the action JSON)"""
    spec_in = deep(spec)
    keys = sorted(spec['keys'], key=lambda k: float(k['t']))
    if not keys:
        raise ValueError('keys.json has no keys')
    fps = float(spec.get('fps', 30))
    poses = [deep(k['pose']) for k in keys]
    interp = [str(k.get('interp', 'bezier')).lower() for k in keys]
    bad = [x for x in interp if x not in INTERP]
    if bad:
        raise ValueError(f'unknown interp {bad[0]!r}: use hold, linear or bezier')
    ts = [float(k['t']) for k in keys]
    events = {k: float(v) for k, v in (spec.get('events') or {}).items()}
    notes = []
    shifted = 0.0
    if ts[0] != 0.0:
        shifted = ts[0]
        ts = [t - shifted for t in ts]        # clips start at 0
        events = {k: round(v - shifted, 6) for k, v in events.items()}
        notes.append(f'keys started at {shifted:g} s: keys AND events shifted by -{shifted:g} s (clip time starts at 0)')
    loop = bool(spec.get('loop'))
    length = spec.get('length')
    if loop:
        if length is None:
            gaps = np.diff(ts) if len(ts) > 1 else [1.0]
            length = ts[-1] + float(np.mean(gaps))
        if length <= ts[-1] + 1e-6:
            raise ValueError(f'loop length {length} must be after the last key {ts[-1]}')
        poses.append(deep(poses[0])); ts.append(float(length)); interp.append(interp[0])
    else:
        length = float(length) if length is not None else ts[-1]
        if length > ts[-1] + 0.5 / fps:
            poses.append(deep(poses[-1])); ts.append(length); interp.append('bezier')     # hold the last pose to the end
        length = max(length, ts[-1])
    # snap to whole frames: the glTF exporter samples whole frames, so the GLB length and the manifest agree
    ts = [round(t * fps) / fps for t in ts]
    length = round(float(length) * fps) / fps
    if any(b <= a_ for a_, b in zip(ts, ts[1:])):
        raise ValueError(f'two keys fall on the same frame at {fps} fps: {ts}')
    out_ev = [k for k, v in events.items() if v < -0.5 / fps or v > length + 0.5 / fps]
    if out_ev:
        raise ValueError(f'event(s) outside the clip 0..{length:.4f} s: '
                         + ', '.join(f'{k}={events[k]:.4f}' for k in out_ev)
                         + ('; events must use the same time base as the keys' if shifted else ''))
    # ground: resolve root.ground per key on the current rig
    grounds = []
    for i, p in enumerate(poses):
        q, st = apply_grounded(rig, p)
        poses[i] = q
        grounds.append(st)
    if spec.get('in_place', True) and len(poses) > 1:
        # remove the straight-line horizontal drift of root.loc (first -> last key); sway is kept.
        # root.loc is real body motion only; framing corrections live in view_offset and never reach the action.
        l0 = (poses[0].get('root') or {}).get('loc', [0, 0, 0]); l1 = (poses[-1].get('root') or {}).get('loc', [0, 0, 0])
        T = ts[-1] - ts[0] or 1.0
        for p, t in zip(poses, ts):
            r = p.setdefault('root', {}); loc = list(r.get('loc', [0, 0, 0]))
            f = (t - ts[0]) / T
            loc[0] -= l0[0] + f * (l1[0] - l0[0]); loc[1] -= l0[1] + f * (l1[1] - l0[1])
            r['loc'] = loc
    names = rig.names
    bones = {n: {'q': [], 'loc': []} for n in names}
    prev = {}
    for p in poses:
        B = rig.basis(rig.solve(p))
        for n in names:
            loc, q, sc = B[n].decompose()
            q = q.normalized()
            if n in prev and prev[n].dot(q) < 0:
                q = -q
            prev[n] = q
            bones[n]['q'].append([round(v, 6) for v in q])
            bones[n]['loc'].append([round(v, 6) for v in loc])
    for n in names:
        if max(abs(v) for l in bones[n]['loc'] for v in l) < 1e-5:
            bones[n]['loc'] = None
    view = None
    vs = [view_of(p) for p in poses]
    if any(v is not None for v in vs):
        view = {'offset': [(v[0] if v else [0.0, 0.0, 0.0]) for v in vs], 'scale': [(v[1] if v else 1.0) for v in vs]}
    # planted-foot / floating warnings
    for t, st in zip(ts, grounds):
        lz = st.get('lowest_z')
        if lz is not None and abs(lz) > 0.03:
            notes.append(f'at t={t:.3f}s the lowest vertex is at z={lz:+.3f} m ({"floating" if lz > 0 else "below the floor"}); '
                         'set "root": {"ground": "lowest"|"left"|"right"} or fix root.loc z')
    return {'format': 'animkit-action-1', 'name': spec['name'], 'fps': fps, 'loop': loop, 'length': float(length),
            'events': events, 'times': ts, 'interp': interp, 'bones': bones, 'poses': poses, 'view': view,
            'ground': grounds, 'shifted_by': shifted, 'notes': notes, 'rig_hash': rig.rig_hash(), 'spec': spec_in}


def write_action(rig, data):
    """create/replace the Action data['name'] on the armature from action data"""
    arm = rig.arm
    name = data['name']
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old)
    if arm.animation_data is None:
        arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    fps = data['fps']
    frames = [t * fps for t in data['times']]
    interp = data.get('interp') or ['bezier'] * len(frames)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    for n, ch in data['bones'].items():
        pb = arm.pose.bones.get(n)
        if pb is None:
            raise KeyError(f'action bone {n!r} not in this rig (re-bake the clip on the current rig)')
        for i, f in enumerate(frames):
            pb.rotation_quaternion = Quaternion(ch['q'][i])
            pb.keyframe_insert('rotation_quaternion', frame=f, group=n)
            if ch.get('loc'):
                pb.location = Vector(ch['loc'][i])
                pb.keyframe_insert('location', frame=f, group=n)
    for fc in action_fcurves(act):
        for i, kp in enumerate(fc.keyframe_points):
            kp.interpolation = INTERP.get(interp[i] if i < len(interp) else 'bezier', 'BEZIER')
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        if data['loop']:
            fc.modifiers.new('CYCLES')
        fc.update()
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = max(frames[-1], 1)
    try:
        act.use_cyclic = bool(data['loop'])
    except Exception:
        pass
    meta = {k: data.get(k) for k in ('fps', 'loop', 'length', 'events', 'times', 'view')}
    act['ak_meta'] = json.dumps(meta)
    return act


def set_time(scene, seconds, fps):
    f = seconds * fps
    fi = int(math.floor(f))
    scene.frame_set(fi, subframe=f - fi)


def view_at(view, times, t):
    """linear interpolation of the per-key framing correction at clip time t"""
    if not view:
        return None
    off = np.array(view['offset'], float); sc = np.array(view['scale'], float)
    o = [float(np.interp(t, times, off[:, i])) for i in range(3)]
    s = float(np.interp(t, times, sc))
    return (o, s) if (max(abs(v) for v in o) > 1e-9 or abs(s - 1) > 1e-9) else None


def cmd_bake(a):
    arm, rig = make_rig(a)
    data = bake_data(rig, a['spec'])
    res = {'name': data['name'], 'length': data['length'], 'loop': data['loop'], 'n_keys': len(data['times']),
           'events': data['events'], 'ground': data['ground'], 'rig_hash': data['rig_hash']}
    if data['shifted_by']:
        res['shifted_by'] = data['shifted_by']
    if data['notes']:
        res['notes'] = data['notes']
    if a.get('out_action'):
        tmp = a['out_action'] + '.tmp'
        json.dump(data, open(tmp, 'w'))
        os.replace(tmp, a['out_action'])
        res['out_action'] = a['out_action']
    if a.get('write_blend', True):
        clear_anim(arm)
        write_action(rig, data)
        arm.animation_data.action = None
        save_atomic(a['blend'])
        res['saved'] = a['blend']
    return res


def cmd_merge(a):
    arm, rig = make_rig(a)
    h = rig.rig_hash()
    existing = {ac.name for ac in bpy.data.actions}
    names, rebaked, legacy, changed, replaced = [], [], [], [], []
    for p in a['files']:
        data = json.load(open(p))
        clear_anim(arm)      # detach the previous clip's action before re-baking (stale first-key ground otherwise)
        if data.get('spec'):
            try:
                fresh = bake_data(rig, data['spec'])
            except Exception as e:
                raise RuntimeError(f'{os.path.basename(p)}: cannot re-bake on the current rig: {type(e).__name__}: {e}')
            if data.get('rig_hash') and data['rig_hash'] != h:
                changed.append(data['name'])
            data = fresh
            rebaked.append(data['name'])
        else:
            legacy.append(data['name'])
        clear_anim(arm)
        if data['name'] in existing:
            replaced.append(data['name'])
        write_action(rig, data)
        existing.add(data['name'])
        names.append(data['name'])
    arm.animation_data.action = None
    save_atomic(a['blend'])
    if changed:
        WARN.append(f'rig changed since these clips were baked (re-baked from their poses on the current rig): {changed}')
    if legacy:
        WARN.append(f'old action JSON without poses (stored rotations replayed, may be stale): {legacy}')
    return {'merged': names, 'rebaked': rebaked, 'replaced_existing': replaced,
            'actions': sorted(ac.name for ac in bpy.data.actions), 'rig_hash': h}


def assign_clip(rig, action_json=None, clip=None):
    """puts the clip on the armature -> (fps, length, loop, times, view)"""
    arm = rig.arm
    clear_anim(arm)
    if action_json:
        data = json.load(open(action_json)) if isinstance(action_json, str) else action_json
        write_action(rig, data)
        return data['fps'], data['length'], data['loop'], data['times'], data.get('view')
    act = bpy.data.actions.get(clip)
    if act is None:
        raise KeyError(f"no action {clip!r}; actions: {[x.name for x in bpy.data.actions]}")
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    meta = json.loads(act.get('ak_meta', '{}'))
    fps = meta.get('fps', bpy.context.scene.render.fps)
    length = meta.get('length', (act.frame_range[1] - act.frame_range[0]) / fps)
    return fps, length, meta.get('loop', False), meta.get('times') or [0.0, length], meta.get('view')


def read_pose_from(rig, src, t):
    """pose (absolute format) of a clip at clip time t. src = action json path or 'clip:<name>'"""
    if isinstance(src, str) and src.startswith('clip:'):
        fps, length, loop, times, view = assign_clip(rig, clip=src[5:])
    else:
        fps, length, loop, times, view = assign_clip(rig, action_json=src)
    scene = bpy.context.scene
    scene.render.fps = int(round(fps))
    set_time(scene, min(max(0.0, t), length), fps)
    bpy.context.view_layer.update()
    arm = rig.arm
    P = {pb.name: pb.matrix.copy() for pb in arm.pose.bones}
    clear_anim(arm)
    pose = {'space': 'absolute', 'bones': {}}
    for n in rig.names:
        if n in rig.driven_all:
            continue
        p = rig.parent[n]
        follow = rig.rest[n] if p is None else P[p] @ (rig.rest[p].inverted() @ rig.rest[n])
        R = P[n].to_3x3().normalized()
        if p is not None and R.to_quaternion().rotation_difference(follow.to_3x3().normalized().to_quaternion()).angle < math.radians(0.05):
            continue
        Rw = rig.Ra @ (R @ rig.rest[n].to_3x3().normalized().inverted()) @ rig.RaT
        e = Rw.to_euler('XYZ')
        pose['bones'][n] = {'rx': round(math.degrees(e.x), 3), 'ry': round(math.degrees(e.y), 3), 'rz': round(math.degrees(e.z), 3)}
    r0 = rig.roots[0]
    dt = rig.Ra @ (P[r0].translation - rig.rest[r0].translation) * rig.s
    if dt.length > 1e-6:
        pose['root'] = {'loc': [round(v, 5) for v in dt], 'rot': [0, 0, 0]}
    v = view_at(view, times, t)
    if v:
        pose['view_offset'] = [round(x, 5) for x in v[0]]
        pose['view_scale'] = round(v[1], 5)
    pose['read_from'] = {'source': src if isinstance(src, str) else 'action', 't': t}
    return pose


def cmd_readpose(a):
    arm, rig = make_rig(a)
    src = a.get('action_json') or ('clip:' + a['clip'])
    return {'pose': read_pose_from(rig, src, float(a['t']))}


def cmd_render_clip(a):
    """renders the clip (from action json or an existing action) at the given clip times"""
    arm, rig = make_rig(a)
    fps, length, loop, ktimes, view = assign_clip(rig, a.get('action_json'), a.get('clip'))
    if a.get('no_view'):
        view = None
    scene = bpy.context.scene
    scene.render.fps = int(round(fps))
    cam = json.load(open(a['cam']))
    co = setup_render(cam)
    times = a.get('times')
    if times is None:
        n = int(a.get('n', 8))
        times = [length * i / max(1, n - 1) for i in range(n)]
    renders, grounds = [], []
    for i, t in enumerate(times):
        set_time(scene, t, fps)
        renders.append(render_panels(cam, co, f"{a['prefix']}_{i:04d}", view_at(view, ktimes, t)))
        grounds.append(ground_stats(rig))
    return {'renders': renders, 'times': times, 'length': length, 'fps': fps, 'loop': loop, 'ground': grounds,
            'view_applied': bool(view)}


def cmd_export(a):
    arm, rig = make_rig(a)
    rj = rig.rj
    used = material_images()
    miss = [im.name for im in used if not im.packed_file and im.source == 'FILE'
            and not os.path.exists(bpy.path.abspath(im.filepath, library=im.library))]
    if miss:
        raise RuntimeError(f'texture files missing for {miss} (blend copied away from its textures?). Export the '
                           'character blend in place (art_src/chars/<id>/<id>.blend), never a copy')
    for o in helper_meshes():
        bpy.data.objects.remove(o, do_unlink=True)
    acts = [ac for ac in bpy.data.actions]
    if arm.animation_data is None:
        arm.animation_data_create()
    metas = {ac.name: json.loads(ac.get('ak_meta', '{}')) for ac in acts}
    fpss = {m.get('fps') for m in metas.values()} - {None}
    efps = int(round(max(fpss))) if fpss else int(bpy.context.scene.render.fps)
    bpy.context.scene.render.fps = efps
    bpy.context.scene.render.fps_base = 1.0
    clips, retimed = {}, {}
    for ac in acts:
        meta = metas[ac.name]
        cfps = float(meta.get('fps', efps))
        L = float(meta.get('length', (ac.frame_range[1] - ac.frame_range[0]) / cfps))
        nF = max(1, int(round(L * efps)))
        Lg = nF / efps
        # every action is written at its own fps; rescale its keys to the export fps so that it ends on a whole frame
        k = nF / (L * cfps) if L > 0 else efps / cfps
        if abs(k - 1) > 1e-9:
            for fc in action_fcurves(ac):
                for kp in fc.keyframe_points:
                    kp.co.x *= k; kp.handle_left.x *= k; kp.handle_right.x *= k
                fc.update()
        ac.use_frame_range = True
        ac.frame_start = 0
        ac.frame_end = nF
        sc = Lg / L if L > 0 else 1.0
        ev = {n: round(float(v) * sc, 4) for n, v in (meta.get('events') or {}).items()}
        if abs(Lg - L) > 1e-6:
            retimed[ac.name] = {'clip_length': round(L, 5), 'glb_length': round(Lg, 5), 'speed_change_pct': round((L / Lg - 1) * 100, 3)}
        clips[ac.name] = {'length': round(Lg, 4), 'loop': bool(meta.get('loop', False)), 'events': ev}
    for ac in acts:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = ac.name
        st = tr.strips.new(ac.name, 0, ac)
        st.name = ac.name
    arm.animation_data.action = None
    kw = dict(filepath=a['out'], export_format='GLB', export_yup=True, export_animations=True,
              export_animation_mode='NLA_TRACKS', export_skins=True, export_force_sampling=True)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_force_sampling', None)
        bpy.ops.export_scene.gltf(**kw)
    manifest = {'sockets': rj.get('sockets', {}), 'socket_offsets': rj.get('socket_offsets', {}), 'clips': clips}
    return {'out': a['out'], 'manifest': manifest, 'n_actions': len(acts), 'export_fps': efps, 'retimed': retimed,
            'n_material_images': len(used)}


def load_rgba(path):
    """image file -> HxWx4 float array, top row first, values as stored (display sRGB for PNG)"""
    img = bpy.data.images.load(path)
    w, h = img.size
    ch = img.channels
    px = np.empty(w * h * ch, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(h, w, ch)[::-1]
    if ch == 3:
        px = np.concatenate([px, np.ones((h, w, 1), np.float32)], axis=2)
    return px


def load_alpha_png_mask(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * img.channels, np.float32)
    img.pixels.foreach_get(px)
    ch = img.channels
    bpy.data.images.remove(img)
    return px.reshape(h, w, ch)[::-1, :, 0] > 0.5


def cmd_fit(a):
    """coordinate descent on the listed bones' angles (and view_offset / view_scale / root.loc) to maximise the mean
    silhouette IoU of both panels (optionally minus a colour-disagreement penalty)"""
    arm, rig = make_rig(a)
    cam = json.load(open(a['cam']))
    co = setup_render(cam)
    pct = int(a.get('pct', 50))
    bpy.context.scene.render.resolution_percentage = pct
    bpy.context.scene.display.render_aa = 'FXAA'
    k = 100 // pct
    tm = np.asarray(load_alpha_png_mask(a['target_mask']))
    H, W = tm.shape
    tm = tm[:H - H % k, :W - W % k].reshape(H // k, k, W // k, k).mean(axis=(1, 3)) > 0.5
    fwk = cam['front_w'] // k
    tf, ts_ = tm[:, :fwk], tm[:, fwk:]
    wcol = float(a.get('color', 0.0))
    bgc = np.array(cam.get('bg', [1, 1, 1])[:3], np.float32)
    tcf = tcs = None
    if wcol > 0:
        trgb = load_rgba(a['target_rgb'])[..., :3]
        trgb = trgb[:H - H % k, :W - W % k].reshape(H // k, k, W // k, k, 3).mean(axis=(1, 3))
        tcf, tcs = trgb[:, :fwk], trgb[:, fwk:]
    prefix = a['prefix']

    def score(pose):
        p2, _ = apply_grounded(rig, pose)
        pf, ps = render_panels(cam, co, prefix, view_of(p2))
        sc_, io_ = [], []
        for path, t, tc in ((pf, tf, tcf), (ps, ts_, tcs)):
            px = load_rgba(path)
            m = px[..., 3] > 0.5
            hh, ww = min(m.shape[0], t.shape[0]), min(m.shape[1], t.shape[1])
            m, t2 = m[:hh, :ww], t[:hh, :ww]
            un = np.logical_or(m, t2)
            u = un.sum()
            v = float(np.logical_and(m, t2).sum() / u) if u else 0.0
            io_.append(v)
            if wcol > 0 and u:
                al = px[:hh, :ww, 3:4]
                rc = px[:hh, :ww, :3] * al + bgc * (1 - al)
                v -= wcol * float(np.abs(rc - tc[:hh, :ww]).mean(axis=2)[un].mean())
            sc_.append(v)
        return sc_, io_

    pose = deep(load_pose(a['pose']))
    pose.setdefault('bones', {})
    grounded = bool((pose.get('root') or {}).get('ground'))
    axes = a.get('axes', ['rx', 'ry'])
    params = []
    for b in a['bones']:
        if b == 'root.loc':
            params += [('root', 'loc', i) for i in range(3) if not (grounded and i == 2)]
            continue
        if b == 'view_offset':
            params += [('view_offset', None, i) for i in range(3)]
            continue
        if b == 'view_scale':
            params += [('view_scale', None, None)]
            continue
        rig._check_bone(b)
        e = pose['bones'].setdefault(b, {})
        if any(x in e for x in ('front', 'side', 'twist')):
            raise ValueError(f'fit works on rx/ry/rz: bone {b!r} uses the aim form (front/side); convert it or leave it out')
        params += [(b, ax, None) for ax in axes]
    lim = float(a.get('limit', 60))
    STEP = {'root': 0.005, 'view_offset': 0.005, 'view_scale': 0.0025}     # per unit of the angle step (32 -> 16 cm .. 2 -> 1 cm)

    def get(p):
        b, ax, i = p
        if b == 'root':
            return float(pose.setdefault('root', {}).setdefault('loc', [0, 0, 0])[i])
        if b == 'view_offset':
            return float(pose.setdefault('view_offset', [0, 0, 0])[i])
        if b == 'view_scale':
            return float(pose.setdefault('view_scale', 1.0))
        return float(pose['bones'][b].get(ax, 0.0))

    def put(p, v):
        b, ax, i = p
        if b == 'root':
            pose['root']['loc'][i] = v
        elif b == 'view_offset':
            pose['view_offset'][i] = v
        elif b == 'view_scale':
            pose['view_scale'] = v
        else:
            pose['bones'][b][ax] = v

    start = {p: get(p) for p in params}
    s0, i0 = score(pose)
    best = sum(s0) / 2
    evals = 1
    for step in a.get('steps', [32, 16, 8, 4, 2]):
        improved = True
        passes = 0
        while improved and passes < 3:
            improved = False; passes += 1
            for p in params:
                cur = get(p)
                st = step * STEP.get(p[0], 1.0)
                for d in ((st, -st, 2 * st, -2 * st) if step >= 8 else (st, -st)):
                    v = cur + d
                    if p[0] not in STEP and abs(v - start[p]) > lim:
                        continue
                    if p[0] == 'view_scale' and not (0.7 <= v <= 1.4):
                        continue
                    put(p, v)
                    s, _ = score(pose); evals += 1
                    if sum(s) / 2 > best + 1e-4:
                        best = sum(s) / 2; cur = v; improved = True
                        break
                put(p, cur)
            if step >= 4 and len(axes) >= 2:
                # diagonal probes per bone: two axes at once (ridges in the IoU landscape)
                for b in [x for x in a['bones'] if x not in ('root.loc', 'view_offset', 'view_scale')]:
                    pa, pb_ = (b, axes[0], None), (b, axes[1], None)
                    ca, cb = get(pa), get(pb_)
                    for da, db in ((step, step), (step, -step), (-step, step), (-step, -step)):
                        if abs(ca + da - start[pa]) > lim or abs(cb + db - start[pb_]) > lim:
                            continue
                        put(pa, ca + da); put(pb_, cb + db)
                        sc_, _ = score(pose); evals += 1
                        if sum(sc_) / 2 > best + 1e-4:
                            best = sum(sc_) / 2; ca, cb = ca + da, cb + db; improved = True
                            break
                    put(pa, ca); put(pb_, cb)
    s1, i1 = score(pose)
    for b in pose['bones'].values():
        for ax in list(b):
            if isinstance(b[ax], float):
                b[ax] = round(b[ax], 2)
    for key in ('view_offset',):
        if key in pose:
            pose[key] = [round(v, 4) for v in pose[key]]
    if 'view_scale' in pose:
        pose['view_scale'] = round(pose['view_scale'], 4)
    if 'root' in pose and 'loc' in pose['root']:
        pose['root']['loc'] = [round(float(v), 4) for v in pose['root']['loc']]
    r4 = lambda l: [round(v, 4) for v in l]
    return {'pose': pose, 'score_start': r4(s0), 'score_end': r4(s1), 'iou_start': r4(i0), 'iou_end': r4(i1), 'evals': evals}


CMDS = {'prep': cmd_prep, 'info': cmd_info, 'pose': cmd_pose, 'selftest': cmd_selftest, 'bake': cmd_bake, 'fit': cmd_fit,
        'merge': cmd_merge, 'render_clip': cmd_render_clip, 'export': cmd_export, 'readpose': cmd_readpose}

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    try:
        cmd = argv[0]
        a = json.load(open(argv[1])) if len(argv) > 1 else {}
        r = CMDS[cmd](a)
        r['ok'] = r.get('ok', True)
        r['blender_s'] = round(time.time() - T0, 2)
        if WARN:
            r['warnings'] = WARN
        out(r)
        sys.exit(0 if r['ok'] else 1)
    except SystemExit:
        raise
    except Exception as e:
        traceback.print_exc()
        d = {'ok': False, 'error': f'{type(e).__name__}: {e}'}
        if WARN:
            d['warnings'] = WARN
        out(d)
        sys.exit(1)
