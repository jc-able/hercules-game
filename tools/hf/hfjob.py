#!/usr/bin/env python3
"""Thin wrapper around the signed-in `higgsfield` CLI that keeps a credits ledger for the devlog.

  hfjob.py upload <file>...                         -> prints "<file> <media_id>" (cached in docs/higgsfield/uploads.json)
  hfjob.py submit --purpose TEXT --name NAME MODEL [cli flags...]
        quotes the cost, submits the job, appends a line to docs/higgsfield/jobs.jsonl, prints "NAME JOB_ID CREDITS"
        media flags take local paths (uploaded + cached first) or ids: --image P --image-references P --start-image P
  hfjob.py wait [--out DIR] [--timeout 30m] NAME...  -> waits for the named jobs, downloads results to DIR/NAME.<ext>
  hfjob.py ledger                                    -> credits by purpose / model

Everything is recorded in docs/higgsfield/jobs.jsonl (one JSON object per job, updated in place by `wait`).
"""
import sys, os, json, subprocess, re, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / 'docs' / 'higgsfield' / 'jobs.jsonl'
UPLOADS = ROOT / 'docs' / 'higgsfield' / 'uploads.json'
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
MEDIA_FLAGS = {'--image', '--image-references', '--start-image', '--end-image', '--video', '--video-references',
               '--audio', '--audio-references'}


def run(cmd, timeout=3600):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def load_jobs():
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def save_jobs(jobs):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(''.join(json.dumps(j, ensure_ascii=False) + '\n' for j in jobs))


def upload(path):
    path = str(pathlib.Path(path).resolve())
    st = os.stat(path)
    key = f'{path}|{st.st_size}|{int(st.st_mtime)}'
    cache = json.loads(UPLOADS.read_text()) if UPLOADS.exists() else {}
    if key in cache:
        return cache[key]['id']
    for attempt in range(4):   # the upload endpoint fails now and then ("Failed to upload media bytes"): retry
        rc, out, err = run(['higgsfield', 'upload', 'create', path, '--json'])
        if rc == 0:
            break
        time.sleep(3 + 3 * attempt)
    if rc != 0:
        raise SystemExit(f'upload failed for {path}: {err[-400:] or out[-400:]}')
    d = json.loads(out)
    d = d[0] if isinstance(d, list) else d
    cache[key] = {'id': d['id'], 'url': d.get('url'), 'file': os.path.relpath(path, ROOT)}
    UPLOADS.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS.write_text(json.dumps(cache, indent=1))
    return d['id']


def resolve_media(args):
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in MEDIA_FLAGS and i + 1 < len(args):
            v = args[i + 1]
            if not UUID.match(v):
                v = upload(v)
            out += [a, v]
            i += 2
        else:
            out.append(a)
            i += 1
    return out


def find_ids(obj):
    ids = []
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('id'), str) and UUID.match(o['id']):
                ids.append(o['id'])
            else:
                for v in o.values():
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and UUID.match(o):
            ids.append(o)
    walk(obj)
    return ids


def find_credits(text):
    try:
        d = json.loads(text)
    except Exception:
        m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*credits?', text)
        return float(m.group(1)) if m else None
    def walk(o):
        if isinstance(o, dict):
            for k in ('credits_exact', 'credits', 'cost'):
                if isinstance(o.get(k), (int, float)):
                    return float(o[k])
            for v in o.values():
                r = walk(v)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = walk(v)
                if r is not None:
                    return r
        return None
    return walk(d)


def cmd_submit(argv):
    purpose = name = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == '--purpose':
            purpose = argv[i + 1]; i += 2
        elif argv[i] == '--name':
            name = argv[i + 1]; i += 2
        else:
            rest.append(argv[i]); i += 1
    model, flags = rest[0], resolve_media(rest[1:])
    jobs = load_jobs()
    if any(j['name'] == name for j in jobs):
        raise SystemExit(f'a job named {name} already exists in the ledger (use a new name for a re-roll)')
    rc, out, err = run(['higgsfield', 'generate', 'cost', model] + flags + ['--json'])
    credits = find_credits(out) if rc == 0 else None
    rc, out, err = run(['higgsfield', 'generate', 'create', model] + flags + ['--json'])
    if rc != 0:
        raise SystemExit(f'submit failed ({name}): {(err or out)[-600:]}')
    try:
        ids = find_ids(json.loads(out))
    except Exception:
        ids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out)
    if not ids:
        raise SystemExit(f'no job id in output ({name}): {out[-400:]}')
    shown = [f if not (f.startswith('--prompt')) else f for f in flags]
    jobs.append({'name': name, 'purpose': purpose, 'model': model, 'job_id': ids[0], 'credits_quoted': credits,
                 'flags': shown, 'submitted': time.strftime('%Y-%m-%dT%H:%M:%S'), 'status': 'submitted'})
    save_jobs(jobs)
    print(name, ids[0], credits)


def cmd_wait(argv):
    out_dir, timeout, names = None, '30m', []
    i = 0
    while i < len(argv):
        if argv[i] == '--out':
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == '--timeout':
            timeout = argv[i + 1]; i += 2
        else:
            names.append(argv[i]); i += 1
    jobs = load_jobs()
    for name in names:
        j = next((x for x in jobs if x['name'] == name), None)
        if not j:
            print(name, 'UNKNOWN'); continue
        rc, out, err = run(['higgsfield', 'generate', 'wait', j['job_id'], '--timeout', timeout, '--interval', '10s',
                            '--quiet', '--json'], timeout=7200)
        status, url, extra = 'unknown', None, {}
        try:
            d = json.loads(out)
            d = d[0] if isinstance(d, list) else d
            status = d.get('status', 'unknown')
            url = d.get('result_url')
            extra = {k: v for k, v in d.items() if k not in ('params',) and isinstance(v, (str, int, float))}
            # keep any other result urls (rigged glb, fbx, thumbnails ...) for inspection
            urls = sorted(set(re.findall(r'https://[^"\s]+', out)))
            extra['all_urls'] = [u for u in urls if u != url][:20]
        except Exception:
            m = re.search(r'"status":\s*"([^"]+)"', out); status = m.group(1) if m else 'unknown'
            m = re.search(r'"result_url":\s*"([^"]+)"', out); url = m.group(1) if m else None
        jobs = load_jobs()
        j = next(x for x in jobs if x['name'] == name)
        j.update({'status': status, 'result_url': url, 'finished': time.strftime('%Y-%m-%dT%H:%M:%S'), 'result': extra})
        if url and out_dir:
            ext = os.path.splitext(url.split('?')[0])[1] or '.bin'
            dst = os.path.join(out_dir, name + ext)
            os.makedirs(out_dir, exist_ok=True)
            urllib.request.urlretrieve(url, dst)
            j['file'] = os.path.relpath(os.path.abspath(dst), ROOT)
        save_jobs(jobs)
        print(name, status, j.get('file', ''), '' if status == 'completed' else (err or out)[-300:].replace('\n', ' '))


def cmd_ledger(_):
    jobs = load_jobs()
    tot = 0.0
    by = {}
    for j in jobs:
        c = j.get('credits_quoted') or 0
        tot += c
        by[j['model']] = by.get(j['model'], 0) + c
    for j in jobs:
        print(f"{j['name']:<34} {j['model']:<28} {str(j.get('credits_quoted')):>6}  {j.get('status')}")
    print('--- by model:', json.dumps(by))
    print('--- total quoted credits:', tot, 'jobs:', len(jobs))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'upload':
        for f in sys.argv[2:]:
            print(f, upload(f))
    elif c == 'submit':
        cmd_submit(sys.argv[2:])
    elif c == 'wait':
        cmd_wait(sys.argv[2:])
    elif c == 'ledger':
        cmd_ledger(sys.argv[2:])
