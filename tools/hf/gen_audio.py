#!/usr/bin/env python3
"""Generate every sound in docs/audio_list.json on Higgsfield (through hfjob.py so the ledger stays complete).
Raw results land in art_src/audio/raw/<name>.<ext>; entries that already have a raw file are skipped.
usage: gen_audio.py [sfx|music|all]
"""
import json, subprocess, sys, pathlib, glob, os

ROOT = pathlib.Path(__file__).resolve().parents[2]
HF = str(ROOT / 'tools' / 'hf' / 'hfjob.py')
OUT = ROOT / 'art_src' / 'audio' / 'raw'
OUT.mkdir(parents=True, exist_ok=True)
what = sys.argv[1] if len(sys.argv) > 1 else 'all'
reg = json.load(open(ROOT / 'docs' / 'audio_list.json'))
names = []
for kind in ('sfx', 'music'):
    if what not in (kind, 'all'):
        continue
    for e in reg[kind]:
        if glob.glob(str(OUT / (e['name'] + '.*'))):
            continue
        if kind == 'sfx':
            cmd = ['mirelo_text_to_audio', '--prompt', e['prompt'], '--duration', str(e['dur'])]
        else:
            cmd = ['elevenlabs_music_v2_5', '--prompt', e['prompt'], '--duration', str(e['dur']), '--force_instrumental', 'true']
        job = e['name'] + (f"_t{e['take']}" if e.get('take') else '')   # a retake gets its own ledger name
        r = subprocess.run([sys.executable, HF, 'submit', '--purpose', f'audio {kind}: {e["name"]}', '--name', job] + cmd,
                           capture_output=True, text=True)
        line = (r.stdout.strip().splitlines() or [r.stderr.strip()[-200:]])[-1]
        print('submit', line[:120], flush=True)
        if r.returncode == 0:
            names.append(job)
for i in range(0, len(names), 8):
    r = subprocess.run([sys.executable, HF, 'wait', '--out', str(OUT), '--timeout', '20m'] + names[i:i + 8],
                       capture_output=True, text=True)
    print(r.stdout.strip()[-900:], flush=True)
import re
for f in os.listdir(OUT):        # retakes are stored under the sound's own name
    m = re.match(r'(.+)_t\d+(\.[a-z0-9]+)$', f)
    if m:
        os.replace(OUT / f, OUT / (m.group(1) + m.group(2)))
print('raw files:', len(os.listdir(OUT)))
