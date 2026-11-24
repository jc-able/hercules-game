"""Step 4: deform test. Poses are rotations about WORLD axes (degrees, XYZ euler) applied at each bone's head on top
of what it inherits. Renders flat ortho FRONT | SIDE sheets with the same framing for every pose.
Blender -b --factory-startup <skinned.blend> --python 04_test.py -- <poses.json> <out_dir> [pose names...]
Writes <out_dir>/deform_<pose>.jpg and <out_dir>/deform_contact.jpg (all poses, small).
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector, Euler

argv = sys.argv[sys.argv.index('--') + 1:]
poses = json.load(open(argv[0])); outd = argv[1]; only = argv[2:]
os.makedirs(outd, exist_ok=True)
scene = bpy.context.scene
ao = next(o for o in scene.objects if o.type == 'ARMATURE')
arm = ao.data
arm.pose_position = 'POSE'

def order(bones):
    out = []
    def rec(b):
        out.append(b)
        for c in b.children:
            rec(c)
    for b in bones:
        if b.parent is None:
            rec(b)
    return out
ORDER = order(arm.bones)

def apply_pose(spec):
    for pb in ao.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    posed = {}
    for b in ORDER:
        pb = ao.pose.bones[b.name]
        if b.parent:
            M = posed[b.parent.name] @ b.parent.matrix_local.inverted() @ b.matrix_local
        else:
            M = b.matrix_local.copy()
        if b.name in spec:
            r = Euler([np.radians(a) for a in spec[b.name]], 'XYZ').to_matrix().to_4x4()
            h = M.to_translation()
            M = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ M
        posed[b.name] = M
        pb.matrix = M
        bpy.context.view_layer.update()

# render setup (flat workbench, white, ortho)
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_object_outline = False
scene.display.render_aa = '8'
world = bpy.data.worlds.new('w'); world.color = (1, 1, 1); scene.world = world
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('tcam'); cd.type = 'ORTHO'
co = bpy.data.objects.new('tcam', cd); scene.collection.objects.link(co); scene.camera = co
cd.clip_start = 0.01; cd.clip_end = 1000
PW, PH = 640, 720     # each panel; frame 12 x 13.5 m around the character
SPAN_W, SPAN_H = 9.8, 11.0
ZC = 5.0
XC = YC = 0.0
if os.environ.get('ZOOM'):      # ZOOM="x,y,z,span": centre of a close-up (front uses x,z; side uses y,z)
    XC, YC, ZC, sp = [float(v) for v in os.environ['ZOOM'].split(',')]
    SPAN_W, SPAN_H = sp * PW / PH, sp
def render_panel(view, path):
    scene.render.resolution_x = PW; scene.render.resolution_y = PH
    cd.ortho_scale = max(SPAN_W, SPAN_H)
    if view == 'front':
        co.location = Vector((XC, -200, ZC)); d = Vector((0, 1, 0))
    else:   # from the character's right (-X), it faces screen-right... camera at -X looks +X: character faces -Y = screen right
        co.location = Vector((-200, YC, ZC)); d = Vector((1, 0, 0))
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(PH, PW, 4)
    bpy.data.images.remove(im); os.remove(path)
    return px

def save(arr, path, q=88):
    h, w = arr.shape[:2]
    res = bpy.data.images.new('o', w, h)
    res.pixels = arr.ravel()
    res.filepath_raw = path; res.file_format = 'JPEG'
    scene.render.image_settings.quality = q
    res.save(); bpy.data.images.remove(res)

# ground line + bone overlay is skipped; a 1 m grid line strip on the ground helps scale reading
tiles = []
names = [n for n in poses if not only or n in only]
for name in names:
    apply_pose(poses[name])
    f = render_panel('front', os.path.join(outd, '_f.png'))
    s = render_panel('side', os.path.join(outd, '_s.png'))
    sheet = np.concatenate([f, np.zeros((PH, 4, 4), np.float32) + [0.3, 0.3, 0.3, 1], s], axis=1)
    save(sheet, os.path.join(outd, f'deform_{name}.jpg'))
    tiles.append(sheet)
    print('###POSE###', name)
# contact sheet: 2 columns, each tile downscaled x0.5
small = [t[::2, ::2] for t in tiles]
cols = 2
rows = (len(small) + cols - 1) // cols
h, w = small[0].shape[:2]
C = np.ones((rows * h, cols * w, 4), np.float32)
for i, t in enumerate(small):
    r, c = divmod(i, cols)
    C[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = t   # blender images are bottom-up
save(C, os.path.join(outd, 'deform_contact.jpg'))
print('###DONE###')
