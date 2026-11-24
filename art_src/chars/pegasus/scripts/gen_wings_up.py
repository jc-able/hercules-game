"""Pegasus `wings_up` (feedback 2 Pegasus re-fixer, 2026-11-23; request in docs/notes/feedback2_flight.md):
standing (idle k00 body, legs on the ground) with both wings RAISED high, for the mount / dismount wing overlay
(home_base `_make_wing_overlay` plays only the wing_ bones of a clip). The wing chain is the fly v5 top (f5_k00) turned
SWEEP deg back about the vertical through each shoulder (default -20 = FORWARD: swept back 45 the wings cut the
seated rider on 24/24 frames, work/feedback2_pegasus/r2/pair_wu_back45.json) and RAISE deg further up; a 2 s loop with a slow 4 deg breath so
the held wings are not frozen.
usage: python3 gen_wings_up.py [--write]   (then tools/ak bake ... --clip wings_up --loop --fps 24)
"""
import json, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pk import *

REPO = os.path.expanduser('~/HerculesGame')
CL = f'{REPO}/art_src/chars/pegasus/clips'
D = f'{CL}/wings_up'
SWEEP = float(os.environ.get('SWEEP', '-20'))
RAISE = float(os.environ.get('RAISE', '15'))
LEN = 2.0
idle_keys = json.load(open(f'{CL}/idle_n/keys_idle.json'))
body = json.load(open(f"{CL}/idle_n/{idle_keys['keys'][0]['pose_file']}"))
top = json.load(open(f'{CL}/fly/poses_fly/f5_k00.json'))
WING = {s: [f'wing_{s}_01', f'wing_{s}_02', f'wing_{s}_03', f'wing_{s}_feather_01', f'wing_{s}_feather_02',
            f'wing_{s}_feather_03'] for s in 'lr'}

keys = []
os.makedirs(f'{D}/poses_wings_up', exist_ok=True)
for i in range(5):
    t = LEN * i / 4
    breath = 4.0 * math.sin(2 * math.pi * t / LEN)
    p = json.loads(json.dumps(body))
    for s in 'lr':
        sg = 1 if s == 'l' else -1
        Q = Rz(sg * SWEEP) @ Ry(-sg * (RAISE + breath))      # back about the vertical, then up (front panel)
        for b in WING[s]:
            p['bones'][b] = dec(Q @ mat(top['bones'][b]))
    p['wings_up'] = f'idle k00 body + fly v5 top wings swept {SWEEP} back, raised {RAISE} (+-4 breath)'
    fn = f'poses_wings_up/k{i:02d}.json'
    if i < 4:
        keys.append({'t': round(t, 6), 'pose_file': fn})
        if '--write' in sys.argv: json.dump(p, open(f'{D}/{fn}', 'w'), indent=1)
k = {'fps': 24.0, 'loop': True, 'length': LEN, 'events': {},
     'note': 'wings_up (feedback2 pegasus re-fixer 2026-11-23, art_src/chars/pegasus/scripts/gen_wings_up.py): mount/dismount '
             'wing overlay pose: idle stance, wings raised, swept %g deg back (negative = forward)' % SWEEP, 'keys': keys}
if '--write' in sys.argv: json.dump(k, open(f'{D}/keys_wings_up.json', 'w'), indent=1)
print('ok', SWEEP, RAISE, len(keys))
