"""= work/assemble2_hydra/finish_manifest2.py with the manifest path as argument + fix3 additions:
walk move_speed 1.73 (unchanged clip); walk_turn_l / walk_turn_r move_speed 1.2 (forefoot planted speed at x1, clip
frame, = the generator's Omega x the Godot forefoot radius 2.99 m) and stop_phase (clip time where the feet are nearest
the stance: hydra.gd starts and stops the turn walk there).   python3 finish_manifest3.py <hydra_clips.json>"""
import json, sys
mp = sys.argv[1]
rig = json.load(open('art_src/chars/hydra/rig.json'))
prm = json.load(open('art_src/chars/hydra/scripts/fix3/fix_params.json'))
m = json.load(open(mp))
sx, sy, sz = rig['size_xyz_m']
bmin, bmax = rig['bounds_min'], rig['bounds_max']
m['sockets'] = rig['sockets']
m['socket_offsets'] = rig['socket_offsets']
m['offset_space'] = 'blender'
m['weak_points'] = rig.get('weak_points', {})
m['size'] = {
    'height': rig['height'], 'shoulder_height': rig['shoulder_height'],
    'length': round(sy, 4), 'width': round(sx, 4),
    'size_xyz_m_blender': rig['size_xyz_m'], 'bounds_min_blender': bmin, 'bounds_max_blender': bmax,
    'bounds_min_godot': [bmin[0], bmin[2], -bmax[1]], 'bounds_max_godot': [bmax[0], bmax[2], -bmin[1]],
    'note': 'rest pose, metres; Godot model faces +Z, feet on y=0',
}
m['source'] = {'blend': 'art_src/chars/hydra/hydra.blend', 'clips_dir': 'art_src/chars/hydra/clips', 'assembled': '2026-11-23'}
m['clips']['walk']['move_speed'] = 1.73
for c in ('walk_turn_l', 'walk_turn_r'):
    if c in m['clips']:
        m['clips'][c]['move_speed'] = prm['turn']['move_speed']
        m['clips'][c]['stop_window'] = prm['turn']['stop_window']
        m['clips'][c]['start_time'] = prm['turn']['start_time']
json.dump(m, open(mp, 'w'), indent=1)
print(json.dumps({k: m['clips'][k] for k in m['clips']}, indent=None)[:3000])
