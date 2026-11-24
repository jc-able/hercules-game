"""Pegasus vertex regions for the ride checks: 'wing' (wing bones), 'hair' (blue mane/tail texels: soft, a hand or a
shield may press into it), 'skin' (everything else). Needs bpy; image = the material's albedo."""
import numpy as np


def pegasus_regions(obj):
    import bpy
    me = obj.data
    gn = {g.index: g.name for g in obj.vertex_groups}
    dom = np.array([gn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in me.vertices], dtype=object)
    img = next(n.image for m in obj.data.materials if m and m.node_tree for n in m.node_tree.nodes
               if n.type == 'TEX_IMAGE' and n.image)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
    xs = np.clip((uv[:, 0] % 1.0) * (w - 1), 0, w - 1).astype(int); ys = np.clip((uv[:, 1] % 1.0) * (h - 1), 0, h - 1).astype(int)
    col = px[ys, xs, :3]
    blue = (col[:, 2] > col[:, 0] + 0.15) & (col[:, 2] > col[:, 1] + 0.05)
    hair = np.zeros(len(me.vertices), bool)
    np.logical_or.at(hair, lv, blue)
    reg = np.where(np.char.startswith(dom.astype(str), 'wing'), 'wing', np.where(hair, 'hair', 'skin'))
    return reg, dom
