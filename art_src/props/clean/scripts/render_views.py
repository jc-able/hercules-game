"""Render front (-Y) and three-quarter views of cleaned props with a 1.8 m reference bar (Workbench, textured).
Usage: Blender -b --factory-startup --python render_views.py -- <name> [<name> ...]
Writes work/props/renders/<name>_front.png and <name>_tq.png (512x512)."""
import bpy, sys, os, math
from mathutils import Vector

REPO = os.path.expanduser('~/HerculesGame')
OUTD = f"{REPO}/work/props/renders"


def render(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if name.startswith("raw:"):
        name = name[4:]
        bpy.ops.import_scene.gltf(filepath=f"{REPO}/art_src/props/raw/prop_{name}.glb")
        name = "raw_" + name
    else:
        bpy.ops.import_scene.gltf(filepath=f"{REPO}/game/assets/props/{name}.glb")
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    # 1.8 m reference figure to the right of the prop
    bpy.ops.mesh.primitive_cube_add(size=1)
    ref = bpy.context.active_object
    ref.scale = (0.45, 0.3, 1.8)
    ref.location = (mx.x + 0.6, 0, 0.9)
    m = bpy.data.materials.new("ref")
    m.diffuse_color = (0.9, 0.15, 0.1, 1)
    ref.data.materials.append(m)
    lo = Vector((mn.x, mn.y, 0))
    hi = Vector((mx.x + 1.05, mx.y, max(mx.z, 1.8)))
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "TEXTURE"
    sh.show_cavity = False
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w")
    sc.world = w
    sh.background_type = "VIEWPORT" if hasattr(sh, "background_type") else sh.background_type
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for tag, az, el in (("front", 0, 8), ("tq", 40, 22)):
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = centre + d * (radius * 4)
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        cam_d.ortho_scale = radius * 2.1
        cam_d.clip_end = radius * 10
        sc.render.filepath = f"{OUTD}/{name}_{tag}.png"
        bpy.ops.render.render(write_still=True)


argv = sys.argv[sys.argv.index("--") + 1:]
for n in argv:
    if n.startswith("raw:") or os.path.exists(f"{REPO}/game/assets/props/{n}.glb"):
        render(n)
