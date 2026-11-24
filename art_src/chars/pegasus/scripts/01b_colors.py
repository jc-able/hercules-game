"""Step 1b: per-vertex albedo colour (mean over the vertex's loops) -> npz, used to separate mane/tail hair (blue),
hooves (navy) and harness (gold) from the white body and wings when skinning.

Blender -b --factory-startup --python 01b_colors.py -- <workdir>
"""
import bpy, sys, os
import numpy as np
WK = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=os.path.join(WK, 'stage1.blend'))
ob = bpy.data.objects['pegasus']; me = ob.data
img = bpy.data.images['pegasus_albedo']
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3]
uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
lv = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', lv)
x = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(int); y = np.clip((uv[:, 1] % 1.0) * h, 0, h - 1).astype(int)
c = px[y, x]
nv = len(me.vertices)
acc = np.zeros((nv, 3)); cnt = np.zeros(nv)
np.add.at(acc, lv, c); np.add.at(cnt, lv, 1)
col = acc / np.maximum(cnt, 1)[:, None]
np.save(os.path.join(WK, 'vcol.npy'), col)
print('###COL###', nv, col.mean(0))
