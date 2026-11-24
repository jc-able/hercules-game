"""Completes game/assets/characters/pegasus/pegasus_clips.json after `tools/ak export` (assembler, 2026-11-22;
assemble2 2026-11-23: same fields, new clip sources from art_src/chars/pegasus/clip_sources.json, idle clearance note;
finish_manifest5 = feedback2 pegasus re-fixer 2026-11-23: clearance/fly_bob texts for fly v5 / glide v5 (pitch); finish_manifest4 = feedback2 pegasus fixer 2026-11-23: clearance/fly_bob texts for fly v4 / glide v4; finish_manifest3 = animation fixer 2026-11-23: same fields, clearance texts updated for fly v3 / glide v3 / idle v2, new
rider.mount note).

  python3 art_src/chars/pegasus/ridden/finish_manifest2.py           (from the repo root)

- socket_offsets: rig.json gives them in ARMATURE axes relative to the bone head; CharacterVisual applies them in the
  BONE frame. They are converted here (bone frame = Blender bone frame = Godot bone frame) and written with
  "offset_space": "godot" (loc as is, identity basis), so a child of the socket node has the saddle bone's axes.
- saddle socket = the rider's HIPS seat point (0.20 m behind and 0.247 m above the saddle bone head, from
  art_src/chars/ride/ride.json), because the game glues the rider's hips bone to this socket
  (IslandProxy.seat_rider). The saddle bone head itself lies on the back surface.
- size from rig.json; rider block from art_src/chars/ride/ride_game.json; clip lengths/loops/events kept from export."""
import json, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
P = lambda *a: os.path.join(REPO, *a)
man_path = P('game/assets/characters/pegasus/pegasus_clips.json')
man = json.load(open(man_path))
rig = json.load(open(P('art_src/chars/pegasus/rig.json')))
ride = json.load(open(P('art_src/chars/ride/ride_game.json')))
ridej = json.load(open(P('art_src/chars/ride/ride.json')))

# rest bone frames (columns = bone X, Y, Z in armature axes), read from pegasus.blend bone.matrix_local (roll 0)
FRAMES = {
    'saddle': [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]],
    'head': [[1.0, 0.0, 0.0], [0.0, -0.761545, -0.648123], [0.0, 0.648113, -0.761565]],
}


def to_bone(bone, v):
    cols = FRAMES[bone]
    return [round(sum(c[i] * v[i] for i in range(3)), 4) for c in cols]


HIPS_SEAT_ARM = [0.0, 0.2, 0.2471]          # rider hips joint - saddle head, pegasus armature axes (ride.json check)
offs = {}
for logical, bone in rig['sockets'].items():
    o = rig['socket_offsets'].get(logical, {'loc': [0, 0, 0], 'rot_deg': [0, 0, 0]})
    loc_arm = list(o['loc'])
    if logical == 'saddle':
        loc_arm = [a + b for a, b in zip(loc_arm, HIPS_SEAT_ARM)]
    offs[logical] = {'loc': to_bone(bone, loc_arm), 'rot_deg': [0.0, 0.0, 0.0]}
man['sockets'] = dict(rig['sockets'])
man['offset_space'] = 'godot'
man['socket_offsets'] = offs
man['socket_notes'] = {
    'frame': 'loc in metres in the Godot bone frame (= Blender bone frame), identity basis ("offset_space": "godot").',
    'saddle': 'the rider HIPS seat point: 0.20 m behind and 0.247 m above the saddle bone head (ride.json seated pose). '
              'Glue the hercules hips bone here (IslandProxy.seat_rider) or parent the hercules scene root to this node '
              'with rider.offset. Axes: +Y up along the saddle bone, +Z Pegasus forward.',
    'head': 'middle of the skull (rig.json head offset, converted from armature axes).'}

g = ride['rider_offset']['godot']['position']               # rider root relative to the saddle BONE HEAD (bone frame)
sock = offs['saddle']['loc']
man['size'] = {'height': rig['height'], 'withers': rig['withers'], 'length': rig['size_xyz'][1],
               'width': rig['size_xyz'][0], 'units': 'm',
               'note': 'height = feet to the wing tops at rest; withers 1.9 m; length nose-tail; width across the wings at rest'}
fly_len = man['clips']['fly']['length']
man['rider'] = {
    'socket': 'saddle',
    'offset': {'position': [round(g[i] - sock[i], 4) for i in range(3)], 'rotation_degrees': [0.0, 0.0, 0.0],
               'relative_to': 'the saddle socket node (hips seat point); hercules glb scene root, Godot axes'},
    'offset_from_saddle_bone_head': {'position': g, 'rotation_degrees': [0.0, 0.0, 0.0],
                                     'relative_to': 'BoneAttachment3D on bone saddle (ride_game.json godot form)'},
    'hips_seat_from_saddle_bone_head': sock,
    'beat_period_s': ride['beat_period_s'],
    'rider_clip': ride['rider_clip'],
    'rider_clip_length_s': ride['rider_clip_length_s'],
    'fly_beat_s': fly_len,
    'rider_speed_on_fly': round(ride['rider_clip_length_s'] / fly_len, 4),
    'rider_speed_on_glide': 0.4,
    'phase': 'fly t=0 and ride t=0 are both the wing TOP: start them together and re-sync each fly loop '
             '(rider_pos = fmod(fly_pos / fly_beat_s, 1) * rider_clip_length_s).',
    'beat_note': 'beat_period_s 1.48 is the ride reference video; the game fly clip beats once per fly_beat_s '
                 '(1.042 s, from the fly reference video); scale the rider by rider_speed_on_fly.',
    'clearance': 'fly is the rider-safe version (both wings swept 25 deg forward). fly v5 / glide v5 (feedback 2 re-fix, '
                 '2026-11-23, art_src/chars/pegasus/scripts/gen5.py): fly stroke +50 deg top -> -30 deg bottom (down 0.625 s, '
                 'quicker up 0.417 s), upstroke FOLDED (hand swept back 55 deg, down 15, peak mid/late upstroke), hind legs '
                 'stretched back along the body, forelegs tucked, tail streaming, neck stretched, constant 9 deg nose-down '
                 'pitch; glide wings flat and spread (shape of the level fly downstroke, +10 deg, 3 deg breath). Checked '
                 'against the seated rider (pair_check: fly one rider loop per beat, 25 frames; glide 36 frames at 0.4x): 0 '
                 'wing/rider/sword/shield overlaps (docs/notes/feedback2_pegasus.md). In flight the hooves sit about at belly '
                 'height (legs stretched/tucked). The natural idle folds the wings where a seated '
                 'rider\'s legs hang: see idle_clearance.',
    'idle_clearance': 'idle is NOT rider-safe: its folded wings hit a seated rider on 48 of 48 checked frames of the 8 s '
                      'idle v2 (36 of 36 on the 6 s v1), including its first pose (the natural stance). Never play idle with '
                      'the rider seated or hopping on: start fly at the START of the mount hop (home_base.gd _mount, next to '
                      'the neigh), and on a dismount leave fly/glide only after the rider is off.',
    'mount': 'The rider mounts from the side at the saddle (home_base MOUNT_OFFSET 1.75 m sideways, clear of the folded wings, '
             'about 1.1 m from the centre line). During idle the hind hooves step: 2.45-3.25 s and 6.85-7.65 s of the 8 s loop '
             '(each hoof moves 0.2 m fore-aft, 4 cm sideways, under the hip, 0.26-0.30 m from the centre line); the forehooves '
             'never move. Switching idle -> fly (0.3 s blend) at the hop start lifts the wings before the rider arrives.',
    'fly_bob': 'fly carries its own body bob (v2 bob x1.5): root height 0 at the wing top (t 0, lowest), '
               '+0.06 m at t 0.33, +0.12 m at t 0.625 (highest, end of the downstroke), +0.045 m at t 0.9. '
               'fly AND glide carry the same constant 9 deg nose-down body pitch (root.rot, about the hips; the rider on the '
               'saddle socket leans with it) and glide has root height 0, so the fly<->glide crossfade neither jumps nor '
               'rocks; a glide/fly -> idle crossfade levels the body over the blend. '
               'Drop any code bob on top of fly (or phase it to the AnimationPlayer position, peak at t 0.625).'}
srcs = json.load(open(P('art_src/chars/pegasus/clip_sources.json')))['clips']
for c in man['clips']:
    man['clips'][c]['source'] = srcs[c]
json.dump(man, open(man_path, 'w'), indent=1)
print(json.dumps({'socket_offsets': offs, 'rider_offset': man['rider']['offset']['position'], 'size': man['size']}))
