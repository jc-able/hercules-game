"""Derive a rider-safe version of a matched Pegasus clip: both wings swept forward by `yaw` degrees about the body's
vertical axis through each wing root (docs/notes/ride_anim.md: the plain beat cuts through a seated rider).

  python3 make_ridden.py <action_<clip>.json> <yaw deg, e.g. 10> <out_dir> [--name fly]

The sweep is an outermost body-frame Rz on every wing bone that the pose gives in ABSOLUTE space (ak pose rotation is
Rz*Ry*Rx applied to the rest orientation, so Rz(s)*Rz(rz)*Ry*Rx = rz + s exactly). Wing bones in local_delta space and
unlisted wing bones ride along with their parent. Left wing (+X): rz - yaw (forward = toward -Y); right wing: rz + yaw.
Writes <out_dir>/keys_<name>.json (inline poses, same times/interp/loop/length/events) and poses/<name>_kNN.json."""
import json, os, sys, copy

src, yaws, out = sys.argv[1], sys.argv[2], sys.argv[3]
# yaw: one number for every key, or a comma list (one per key, in key order)
yl = [float(x) for x in yaws.split(',')]
yaw = yl[0]
name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else None
act = json.load(open(src))
spec = act['spec']
name = name or spec['name']
os.makedirs(os.path.join(out, 'poses'), exist_ok=True)
keys = []
changed = []
for i, k in enumerate(spec['keys']):
    pose = copy.deepcopy(k['pose'])
    yaw = yl[i] if len(yl) > 1 else yl[0]
    psp = pose.get('space', 'absolute')
    for b, v in pose.get('bones', {}).items():
        if not b.startswith('wing_'):
            continue
        sp = v.get('space', psp)
        if sp != 'absolute':
            continue
        if any(x in v for x in ('front', 'side')):
            raise SystemExit(f'key {i} bone {b}: aim form not handled')
        side = b.split('_')[1]
        d = -yaw if side == 'l' else yaw
        v['rz'] = round(float(v.get('rz', 0.0)) + d, 3)
        changed.append((i, b))
    pose['ridden_sweep_deg'] = yaw
    pf = os.path.join(out, 'poses', f'{name}_k{i:02d}.json')
    json.dump(pose, open(pf, 'w'), indent=1)
    row = {'t': k['t'], 'pose_file': os.path.abspath(pf)}
    if k.get('interp'):
        row['interp'] = k['interp']
    keys.append(row)
kj = {'fps': spec['fps'], 'loop': spec['loop'], 'length': spec['length'], 'events': spec.get('events', {}),
      'derived_from': os.path.relpath(src, os.path.dirname(os.path.abspath(out))) if False else src,
      'ridden_sweep_deg': yl if len(yl) > 1 else yl[0], 'keys': keys}
json.dump(kj, open(os.path.join(out, f'keys_{name}.json'), 'w'), indent=1)
print(json.dumps({'keys': len(keys), 'changed_bones': len(changed), 'out': os.path.join(out, f'keys_{name}.json')}))
