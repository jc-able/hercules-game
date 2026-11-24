"""colour the mesh by up to three bones' weights (R,G,B) -> label attribute; run on a skinned blend, saves to --save
Blender -b <blend> --python weight_colors.py -- <save.blend> boneR [boneG] [boneB]"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['medusa']; me = ob.data; n = len(me.vertices)
cols = np.zeros((n, 4)); cols[:, 3] = 1; cols[:, :3] = 0.15
for k, bn in enumerate(a[1:4]):
    g = ob.vertex_groups[bn].index
    for v in me.vertices:
        for ge in v.groups:
            if ge.group == g: cols[v.index, k] += ge.weight
attr = me.color_attributes.get('label') or me.color_attributes.new('label', 'FLOAT_COLOR', 'POINT')
attr.data.foreach_set('color', np.clip(cols, 0, 1).ravel())
me.color_attributes.active_color = attr
bpy.ops.wm.save_as_mainfile(filepath=a[0])
