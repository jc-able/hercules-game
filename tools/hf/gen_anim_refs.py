#!/usr/bin/env python3
"""Generate the Seedance 2.5 FRONT | SIDE reference videos (the owner's animation method).

usage: gen_anim_refs.py <char[,char...]|all> [video_name ...] [--suffix _v2]
Reads docs/anim_clips.json. First frame = art_src/chars/<char>/sheet_<std|wide|...>.png (rendered from the rigged asset in
Blender with tools/blender/render_split_sheet.py; framing in cam_<name>.json).
Each video: Seedance 2.5, omni_reference, 480p (lowest), 10 s, 16:9, no audio = 30 credits.
Result: art_src/chars/<char>/clips/<video>/ref.mp4 + ref_sheet.jpg (2 frames per second) + sheet.png + cam.json + prompt.txt.
Videos that already have a ref.mp4 are skipped (pass --suffix to make another take: ref<suffix>.mp4).
All submissions go out first (one process, so the ledger file is never written by two processes), then all waits.
"""
import json, subprocess, sys, pathlib, os, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
HF = str(ROOT / 'tools' / 'hf' / 'hfjob.py')
args = sys.argv[1:]
suffix = ''
names = []
i = 1
while i < len(args):
    if args[i] == '--suffix':
        suffix = args[i + 1]; i += 2
    else:
        names.append(args[i]); i += 1
reg = json.load(open(ROOT / 'docs' / 'anim_clips.json'))
chars = list(reg['characters']) if args[0] == 'all' else args[0].split(',')
CONC = 6   # Higgsfield account limit: 6 concurrent jobs
todo = []
for char in chars:
    if char == 'ride':
        spec = {'noun': reg['ride']['noun'], 'bg': reg['ride']['bg'], 'videos': [reg['ride']]}
    else:
        spec = reg['characters'][char]
    cdir = ROOT / 'art_src' / 'chars' / char
    base = reg['base'].format(noun=spec['noun'], bg=spec['bg'])
    for v in spec['videos']:
        if names and v['name'] not in names:
            continue
        out = cdir / 'clips' / v['name']
        out.mkdir(parents=True, exist_ok=True)
        if (out / f'ref{suffix}.mp4').exists():
            continue
        sname = v.get('sheet', 'std')
        sheet = cdir / f'sheet_{sname}.png'
        cam = cdir / f'cam_{sname}.json'
        if not sheet.exists():
            print('MISSING SHEET', sheet); continue
        shutil.copy(sheet, out / 'sheet.png')     # every clip folder carries the exact first frame + framing
        if cam.exists():
            shutil.copy(cam, out / 'cam.json')
        prompt = base + ' Motion: ' + v['motion']
        (out / f'prompt{suffix}.txt').write_text(prompt)
        todo.append((char, v['name'], str(sheet), prompt, out))
tmp = ROOT / 'work' / 'refs_tmp'
tmp.mkdir(parents=True, exist_ok=True)
ok = 0
existing = {json.loads(l)['name'] for l in open(ROOT / 'docs' / 'higgsfield' / 'jobs.jsonl') if l.strip()}
for i in range(0, len(todo), CONC):
    jobs = []
    for char, vname, sheet, prompt, out in todo[i:i + CONC]:
        job = f'ref_{char}_{vname}{suffix}'
        n = 2
        while job in existing:          # a name is used once in the ledger; retries get _r2, _r3 ...
            job = f'ref_{char}_{vname}{suffix}_r{n}'; n += 1
        existing.add(job)
        r = subprocess.run([sys.executable, HF, 'submit', '--purpose', f'anim reference video: {char} {vname}', '--name', job,
                            'seedance_2_5', '--mode', 'omni_reference', '--start-image', sheet, '--duration', '10',
                            '--resolution', '480p', '--aspect_ratio', '16:9', '--generate_audio', 'false', '--prompt', prompt],
                           capture_output=True, text=True)
        line = (r.stdout.strip().splitlines() or [r.stderr.strip()[-300:]])[-1]
        print('submit', line[:140], flush=True)
        if r.returncode == 0:
            jobs.append((job, out))
    for job, out in jobs:
        r = subprocess.run([sys.executable, HF, 'wait', '--out', str(tmp), '--timeout', '40m', job], capture_output=True, text=True)
        print(r.stdout.strip()[-160:], flush=True)
        src = tmp / (job + '.mp4')
        if src.exists():
            dst = out / f'ref{suffix}.mp4'
            shutil.move(str(src), str(dst))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(dst), '-vf', 'fps=2,scale=480:-1,tile=5x4:padding=3',
                            '-frames:v', '1', str(out / f'ref_sheet{suffix}.jpg')])
            ok += 1
print('done', ok, 'of', len(todo), 'videos')
