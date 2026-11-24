"""Step 7: final blend + GLB test export.
Blender -b --factory-startup <work>/03_skin.blend --python 07_final.py -- <chars/cyclops dir> <club.blend>
- relative texture path, names, transforms check
- a copy of the club (linked mesh data appended from club.blend) parented to bone hand_u_r, held like a bat
  (handle through the fist, club head up; the T-pose hands have thumbs up / palms forward)
- saves <dir>/cyclops.blend and exports <dir>/export/cyclops.glb (mesh + skeleton only, +Y up, no animation)
- writes <dir>/export/club_world.json (club world matrix in Blender space) for the rig.json offsets
"""
import bpy, sys, os, json
from mathutils import Matrix, Vector

D, CLUB = [os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:][:2]]
GRIP = Vector((-3.38, -0.02, 6.40))   # palm centre of the right upper hand, axis just in front of the palm
scene = bpy.context.scene
ao = bpy.data.objects['cyclops_rig']; ob = bpy.data.objects['cyclops']
for o in (ao, ob):
    assert all(abs(v) < 1e-6 for v in o.location) and all(abs(v) < 1e-6 for v in o.rotation_euler), o.name
    assert all(abs(v - 1) < 1e-6 for v in o.scale), o.name
ao.data.pose_position = 'POSE'
for pb in ao.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
img = bpy.data.images['cyclops_albedo']
img.filepath = os.path.join(D, 'cyclops_albedo.png')
# club
for o in list(bpy.data.objects):
    if o.name.startswith('club'):
        bpy.data.objects.remove(o, do_unlink=True)
with bpy.data.libraries.load(CLUB, link=False) as (src, dst):
    dst.objects = ['club']
club = dst.objects[0]
scene.collection.objects.link(club)
club.name = 'club'
club.parent = ao; club.parent_type = 'BONE'; club.parent_bone = 'hand_u_r'
bpy.context.view_layer.update()
club.matrix_world = Matrix.Translation(GRIP)
bpy.context.view_layer.update()
cimg = club.data.materials[0].node_tree.nodes['Image Texture'].image if 'Image Texture' in club.data.materials[0].node_tree.nodes else None
for n in club.data.materials[0].node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        n.image.filepath = os.path.join(os.path.dirname(CLUB), 'club_albedo.png')
json.dump({'club_world': [list(r) for r in club.matrix_world], 'grip': list(GRIP)},
          open(os.path.join(D, 'export', 'club_world.json'), 'w'), indent=1)
# extra cleanup: no stray data
for o in list(scene.objects):
    if o not in (ao, ob, club):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.preferences.filepaths.save_version = 0     # no cyclops.blend1 backup next to the deliverable
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'cyclops.blend'), relative_remap=True)
# review fix 11-22: absolute texture paths turned the blend magenta when the repo moves -> make them relative to the
# saved blend ('//cyclops_albedo.png', '//../../props/club/club_albedo.png') and save again
bpy.ops.file.make_paths_relative()
for im in bpy.data.images:
    im.reload()
paths = {im.name: im.filepath for im in bpy.data.images}
assert all(p.startswith('//') for p in paths.values()), paths
assert all(im.has_data or im.size[0] > 0 for im in bpy.data.images), [(im.name, im.filepath) for im in bpy.data.images]
bpy.ops.wm.save_mainfile()
print('###PATHS###', paths)

# GLB: mesh + skeleton only
bpy.ops.object.select_all(action='DESELECT')
ao.select_set(True); ob.select_set(True)
bpy.context.view_layer.objects.active = ao
bpy.ops.export_scene.gltf(filepath=os.path.join(D, 'export', 'cyclops.glb'), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=False, export_skins=True, export_animations=False,
                          export_materials='EXPORT', export_image_format='AUTO')
print('###FINAL###', [o.name for o in scene.objects], club.matrix_world.translation[:])
