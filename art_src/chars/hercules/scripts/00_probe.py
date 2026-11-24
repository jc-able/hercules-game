"""Probe raw.glb: objects, transforms, bones (world), weights stats."""
import bpy, sys, json
import numpy as np
from mathutils import Vector

src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in bpy.context.scene.objects:
    print('OBJ', o.name, o.type, 'parent', o.parent.name if o.parent else None, 'loc', tuple(round(v, 4) for v in o.location),
          'rot', tuple(round(v, 4) for v in o.rotation_euler), 'rotmode', o.rotation_mode, 'scale', tuple(round(v, 4) for v in o.scale),
          'mods', [m.type for m in o.modifiers] if o.type == 'MESH' else '')
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
M = arm.matrix_world
for b in arm.data.bones:
    h = M @ b.head_local; t = M @ b.tail_local
    print('BONE', b.name, 'parent', b.parent.name if b.parent else None, 'head', tuple(round(v, 3) for v in h), 'tail', tuple(round(v, 3) for v in t), 'deform', b.use_deform)
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    co = np.array([o.matrix_world @ v.co for v in me.vertices])
    print('MESH', o.name, len(me.vertices), 'polys', len(me.polygons), 'bbmin', co.min(0).round(3), 'bbmax', co.max(0).round(3))
    print('  vgroups', len(o.vertex_groups), [g.name for g in o.vertex_groups])
    names = [g.name for g in o.vertex_groups]
    ninf = np.zeros(len(me.vertices), int); tot = np.zeros(len(me.vertices))
    per = {n: 0 for n in names}
    for v in me.vertices:
        ws = [g for g in v.groups if g.weight > 1e-4]
        ninf[v.index] = len(ws); tot[v.index] = sum(g.weight for g in ws)
        for g in ws:
            per[names[g.group]] += 1
    print('  influences hist', np.bincount(ninf).tolist(), 'sum min/max', tot.min().round(3), tot.max().round(3))
    print('  per-group verts', per)
    print('  materials', [m.name for m in me.materials], 'uv', [u.name for u in me.uv_layers])
print('ACTIONS', [(a.name, a.frame_range[:]) for a in bpy.data.actions])
