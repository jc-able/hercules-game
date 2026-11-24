"""Headless Blender prop cleaner, data-driven from PROPS table.

Usage:
  Blender -b --factory-startup --python clean_props.py -- <name|all> [<name> ...]

For each prop: import raw glb -> join -> apply transforms -> merge doubles -> (brazier flame strip)
-> decimate to budget -> outward normals + smooth-by-angle -> orient (front -Y) -> scale to real size
-> centre X/Y, base on Z=0 -> one material, base colour only, resized texture -> export glb (+Y up)
-> re-import and verify. Writes work/props/stats/<name>.json.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

REPO = os.path.expanduser('~/HerculesGame')
RAW = f"{REPO}/art_src/props/raw/prop_{{}}.glb"
OUT = f"{REPO}/game/assets/props/{{}}.glb"
CLEAN = f"{REPO}/art_src/props/clean"
STATS = f"{REPO}/work/props/stats"
SAVE_BLEND = False

# size_axis: 'z' height, 'x' width, 'max' longest dimension.  rot_z: degrees about Z applied so the front faces -Y.
# collision: box | cylinder | none.  tree=True -> cylinder fitted around the trunk.
PROPS = {
    "column":       dict(size=6.0, axis="z",   budget=3000,  tex=1024, collision="cylinder"),
    "column_broken":dict(size=2.4, axis="z",   budget=3000,  tex=1024, collision="box", strip_ground=True),
    "statue_a":     dict(size=2.6, axis="z",   budget=6000,  tex=1024, collision="box"),
    "statue_b":     dict(size=2.6, axis="z",   budget=6000,  tex=1024, collision="box"),
    "basalt_spire": dict(size=7.0, axis="z",   budget=3000,  tex=1024, collision="cylinder"),
    "boulder":      dict(size=2.2, axis="max", budget=3000,  tex=1024, collision="box"),
    "temple":       dict(size=9.0, axis="x",   budget=12000, tex=2048, collision="box"),
    "olive_tree":   dict(size=5.0, axis="z",   budget=6000,  tex=1024, collision="cylinder", tree=True),
    "brazier":      dict(size=1.5, axis="z",   budget=3000,  tex=1024, collision="cylinder", strip_flame=True, scale_from_raw=True),
    "amphora":      dict(size=1.3, axis="z",   budget=3000,  tex=1024, collision="cylinder"),
    "pedestal":     dict(size=1.1, axis="z",   budget=3000,  tex=1024, collision="cylinder"),
    "gate":         dict(size=7.0, axis="z",   budget=6000,  tex=1024, collision="box", gate=True),
    "cypress":      dict(size=8.0, axis="z",   budget=6000,  tex=1024, collision="cylinder", tree=True, tree_full=True),
    "cliff_rock":   dict(size=4.0, axis="max", budget=3000,  tex=1024, collision="box"),
}
# per-prop overrides decided after looking at the renders (front must face -Y)
ROT_Z = {}


def log(*a):
    print("[props]", *a, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def tri_count(obj):
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def find_base_image(obj):
    for slot in obj.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            inp = bsdf.inputs["Base Color"]
            if inp.is_linked:
                n = inp.links[0].from_node
                # walk through possible mix/colour nodes
                seen = 0
                while n.type != "TEX_IMAGE" and seen < 5:
                    lk = next((i for i in n.inputs if i.is_linked), None)
                    if not lk:
                        break
                    n = lk.links[0].from_node
                    seen += 1
                if n.type == "TEX_IMAGE" and n.image:
                    return n.image
        img = next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
        if img:
            return img
    return None


def strip_flame(obj, img):
    """Delete loose parts that look like fire (bright warm texture) and sit in the top part of the object."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    w, h = img.size
    px = list(img.pixels[:]) if uv_layer else None
    zmin = min(v.co.z for v in bm.verts)
    zmax = max(v.co.z for v in bm.verts)
    # loose parts by flood fill over faces
    parts, seen = [], set()
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        stack.append(nf)
        parts.append(comp)
    log(f"brazier loose parts: {len(parts)}")
    kill = []
    for comp in parts:
        zs = [l.vert.co.z for f in comp for l in f.loops]
        zc = sum(zs) / len(zs)
        warm = 0
        n = 0
        if px:
            for f in comp[:: max(1, len(comp) // 200)]:
                for l in f.loops:
                    u, v = l[uv_layer].uv
                    x = min(w - 1, max(0, int((u % 1.0) * w)))
                    y = min(h - 1, max(0, int((v % 1.0) * h)))
                    i = (y * w + x) * 4
                    r, g, b = px[i], px[i + 1], px[i + 2]
                    n += 1
                    if r > 0.6 and r > b * 1.8 and g > 0.25:
                        warm += 1
        frac = warm / max(1, n)
        rel = (zc - zmin) / max(1e-6, zmax - zmin)
        log(f"  part faces={len(comp)} zrel={rel:.2f} warm={frac:.2f}")
        if frac > 0.5 and rel > 0.55 and len(parts) > 1:
            kill.extend(comp)
    removed = len(kill)
    if kill:
        bmesh.ops.delete(bm, geom=list(set(kill)), context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    return removed


def sample_tex(img, px, u, v):
    w, h = img.size
    x = min(w - 1, max(0, int((u % 1.0) * w)))
    y = min(h - 1, max(0, int((v % 1.0) * h)))
    i = (y * w + x) * 4
    return px[i], px[i + 1], px[i + 2]


def strip_flame_faces(obj, img):
    """Flame fused to the bowl: delete faces in the upper part whose texture is bright fire colour,
    then drop small floating islands left above the rim."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    px = img.pixels[:]
    zmin = min(v.co.z for v in bm.verts)
    zmax = max(v.co.z for v in bm.verts)
    H = zmax - zmin
    kill = []
    for f in bm.faces:
        zr = (f.calc_center_median().z - zmin) / H
        if zr < 0.5:
            continue
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops)
        v = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        r, g, b = sample_tex(img, px, u, v)
        # fire: red high, blue low, bright (coals are dark, bronze is darker / less saturated)
        if r > 0.75 and g > 0.3 and b < 0.35 and r - b > 0.5:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    # islands: keep the biggest component, drop components < 3% of faces
    bm.faces.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        st, comp = [f], []
        seen.add(f.index)
        while st:
            c = st.pop()
            comp.append(c)
            for e in c.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        st.append(nf)
        parts.append(comp)
    total = len(bm.faces)
    small = [f for comp in parts if len(comp) < 0.03 * total for f in comp]
    bmesh.ops.delete(bm, geom=small, context="FACES")
    # rim cut: the bowl rim is the widest horizontal section in the upper body; everything well above it is flame
    vs = [v.co for v in bm.verts]
    z0, z1 = min(p.z for p in vs), max(p.z for p in vs)
    Hc = z1 - z0
    bins = {}
    for p in vs:
        zr = (p.z - z0) / Hc
        if 0.3 <= zr <= 0.95:
            k = int(zr * 60)
            bins[k] = max(bins.get(k, 0.0), math.hypot(p.x, p.y))
    rim_k = max(bins, key=lambda k: bins[k])
    rim_z = z0 + (rim_k + 1) / 60 * Hc
    cut = rim_z + 0.04 * Hc
    above = [f for f in bm.faces if f.calc_center_median().z > cut]
    bmesh.ops.delete(bm, geom=above, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    log(f"flame faces removed {len(kill)}, island faces removed {len(small)}, above-rim faces removed {len(above)} "
        f"(rim at {(rim_z - z0) / Hc:.2f} of height)")
    return len(kill) + len(small) + len(above)


def strip_ground(obj):
    """Delete a baked ground/shadow card: faces lying in the bottom 1.5% of the height that are either up-facing
    or not under any geometry standing above them."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    zmin = min(v.co.z for v in bm.verts)
    zmax = max(v.co.z for v in bm.verts)
    H = zmax - zmin
    thr = zmin + 0.03 * H
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    cell = 0.02 * max(max(xs) - min(xs), max(ys) - min(ys))
    occ = set()
    for f in bm.faces:
        c = f.calc_center_median()
        if thr < c.z < zmin + 0.4 * H:
            for v in f.verts:
                cx, cy = int(math.floor(v.co.x / cell)), int(math.floor(v.co.y / cell))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        occ.add((cx + dx, cy + dy))
    kill = []
    for f in bm.faces:
        if max(v.co.z for v in f.verts) > thr:
            continue
        c = f.calc_center_median()
        covered = (int(math.floor(c.x / cell)), int(math.floor(c.y / cell))) in occ
        if f.normal.z > 0.5 or not covered:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    # drop leftover slivers (< 2% of faces)
    bm.faces.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        st, comp = [f], []
        seen.add(f.index)
        while st:
            c = st.pop()
            comp.append(c)
            for e in c.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        st.append(nf)
        parts.append(comp)
    total = len(bm.faces)
    small = [f for comp in parts if len(comp) < 0.02 * total for f in comp]
    bmesh.ops.delete(bm, geom=small, context="FACES")
    kill += small
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    log(f"ground card faces removed {len(kill)}")
    return len(kill)


def gate_parts(obj):
    """Three boxes (left post, right post, lintel) in Godot axes: [{"size": [x,y,z], "offset": [x,y,z]}]."""
    vs = [v.co for v in obj.data.vertices]
    xmin, xmax = min(p.x for p in vs), max(p.x for p in vs)
    ymin, ymax = min(p.y for p in vs), max(p.y for p in vs)
    zmax = max(p.z for p in vs)
    W = xmax - xmin
    mid = [p for p in vs if abs(p.x) < 0.15 * W]
    lintel_bot = min(p.z for p in mid) if mid else 0.75 * zmax
    parts = []
    for side in (-1, 1):
        pts = [p for p in vs if p.x * side > 0.15 * W and p.z < lintel_bot]
        if not pts:
            continue
        a = Vector((min(p.x for p in pts), min(p.y for p in pts), 0.0))
        b = Vector((max(p.x for p in pts), max(p.y for p in pts), lintel_bot))
        parts.append((a, b))
    parts.append((Vector((xmin, ymin, lintel_bot)), Vector((xmax, ymax, zmax))))
    out = []
    for a, b in parts:
        s, c = b - a, (a + b) / 2
        out.append({"size": [round(s.x, 3), round(s.z, 3), round(s.y, 3)],
                    "offset": [round(c.x, 3), round(c.z, 3), round(-c.y, 3)]})
    return out, lintel_bot


def decimate_to(obj, budget):
    start = tri_count(obj)
    if start <= budget:
        return start
    ratio = budget / start
    for attempt in range(6):
        mod = obj.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        ev.to_mesh_clear()
        if n <= budget:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            return n
        obj.modifiers.remove(mod)
        ratio *= (budget / n) * 0.995
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return tri_count(obj)


def world_bbox(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def trunk_fit(obj, height):
    """Trunk centre/radius from vertices in a low band (10%..25% of height)."""
    lo, hi = 0.10 * height, 0.25 * height
    pts = [v.co for v in obj.data.vertices if lo <= v.co.z <= hi]
    if len(pts) < 10:
        return None
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    d = sorted(math.hypot(p.x - cx, p.y - cy) for p in pts)
    r = d[int(0.9 * (len(d) - 1))]
    return cx, cy, r


def process(name):
    cfg = PROPS[name]
    src = RAW.format(name)
    if not os.path.exists(src):
        log(f"{name}: raw missing, skipped")
        return None
    reset()
    bpy.ops.import_scene.gltf(filepath=src)
    objs = mesh_objects()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    # drop empties/parents, bake transforms
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.context.scene.objects):
        if o != obj:
            bpy.data.objects.remove(o, do_unlink=True)
    raw_tris = tri_count(obj)
    rmn, rmx = world_bbox(obj)
    raw_dim = rmx - rmn
    img = find_base_image(obj)
    if img is None:
        raise RuntimeError(f"{name}: no base colour image")
    raw_tex = list(img.size)

    # merge doubles (raw units ~1 m)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nv0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    merged = nv0 - len(bm.verts)
    bm.to_mesh(obj.data)
    bm.free()

    flame_faces = None
    if cfg.get("strip_flame"):
        flame_faces = strip_flame(obj, img) + strip_flame_faces(obj, img)
    ground_faces = None
    if cfg.get("strip_ground"):
        ground_faces = strip_ground(obj)

    tris = decimate_to(obj, cfg["budget"])

    # outward normals, clear custom normals, smooth by angle
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    if obj.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40), keep_sharp_edges=True)

    # orient, scale, place
    rz = ROT_Z.get(name, 0.0)
    if rz:
        obj.rotation_euler = (0, 0, math.radians(rz))
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    mn, mx = world_bbox(obj)
    dim = mx - mn
    if cfg.get("scale_from_raw"):  # size refers to the raw object (e.g. brazier incl. flame), keep that scale
        dim = raw_dim
    ref = {"z": dim.z, "x": dim.x, "max": max(dim)}[cfg["axis"]]
    s = cfg["size"] / ref
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mn, mx = world_bbox(obj)
    c = (mn + mx) / 2
    obj.location = (-c.x, -c.y, -mn.z)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    mn, mx = world_bbox(obj)
    dim = mx - mn

    # one clean material, base colour only, resized texture
    t = cfg["tex"]
    if img.size[0] != t or img.size[1] != t:
        img.scale(t, t)
    tex_path = f"{CLEAN}/{name}_albedo.png"
    img.filepath_raw = tex_path
    img.file_format = "PNG"
    img.save()
    img2 = bpy.data.images.load(tex_path, check_existing=False)
    img2.name = f"{name}_albedo"
    mat = bpy.data.materials.new(f"M_{name}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.85
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img2
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.name = name
    obj.data.name = f"{name}_mesh"

    # collision
    col = {"collision": cfg["collision"]}
    if cfg.get("tree"):
        tf = trunk_fit(obj, dim.z)
        if tf:
            cx, cy, r = tf
            hh = dim.z if cfg.get("tree_full") else dim.z * 0.5  # cypress: dense canopy blocks to the top
            col["collision_size"] = [round(r, 3), round(hh, 3)]  # cylinder radius, height
            col["collision_offset"] = [round(cx, 3), round(hh / 2, 3), round(-cy, 3)]  # Godot axes
    elif cfg["collision"] == "cylinder":
        r = max(dim.x, dim.y) / 2
        col["collision_size"] = [round(r, 3), round(dim.z, 3)]
        col["collision_offset"] = [0.0, round(dim.z / 2, 3), 0.0]
    elif cfg["collision"] == "box":
        col["collision_size"] = [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)]
        col["collision_offset"] = [0.0, round(dim.z / 2, 3), 0.0]
    if cfg.get("gate"):
        col["collision_parts"], lb = gate_parts(obj)
        col["opening_height"] = round(lb, 3)

    # save clean source .blend (not opened anywhere) and export
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if SAVE_BLEND:  # off: the .blend keeps the 4k source image (~20 MB each); the GLB + albedo are the clean source
        img2.pack()
        bpy.ops.wm.save_as_mainfile(filepath=f"{CLEAN}/{name}.blend", compress=True)
    out = OUT.format(name)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=True, export_animations=False, export_normals=True,
        export_texcoords=True, export_materials="EXPORT", export_image_format="AUTO",
    )

    # verify by re-import
    reset()
    bpy.ops.import_scene.gltf(filepath=out)
    vobjs = mesh_objects()
    vt = sum(tri_count(o) for o in vobjs)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in vobjs for v in o.data.vertices]
    vmn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    vmx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    vd = vmx - vmn
    imgs = [list(i.size) for i in bpy.data.images if i.size[0] > 0]
    mats = sorted({s.material.name for o in vobjs for s in o.material_slots if s.material})
    st = dict(
        name=name, raw_tris=raw_tris, raw_tex=raw_tex, merged_verts=merged, flame_faces_removed=flame_faces, ground_faces_removed=ground_faces,
        rot_z=rz, tris=vt, tex=imgs, materials=mats,
        size_blender=[round(vd.x, 3), round(vd.y, 3), round(vd.z, 3)],
        size_godot=[round(vd.x, 3), round(vd.z, 3), round(vd.y, 3)],
        min_z=round(vmn.z, 4), centre_xy=[round((vmn.x + vmx.x) / 2, 4), round((vmn.y + vmx.y) / 2, 4)],
        file_bytes=os.path.getsize(out), **col,
    )
    with open(f"{STATS}/{name}.json", "w") as f:
        json.dump(st, f, indent=1)
    log(json.dumps(st))
    return st


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    names = list(PROPS) if argv == ["all"] else argv
    for n in names:
        try:
            process(n)
        except Exception as e:
            import traceback
            traceback.print_exc()
            log(f"{n}: FAILED {e}")


main()
