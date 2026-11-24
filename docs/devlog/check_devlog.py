#!/usr/bin/env python3
"""Check a game devlog folder before sharing or committing it (part of the devlog-skill).

Run:  python3 check_devlog.py [--dir docs/devlog] [--extra .devlog_tools/private_literals.txt]
(default --dir: the folder this script sits in, else ./docs/devlog)

1. Every relative link and image in the .md files points to a file that exists
   (anchors like DEVLOG.md#chapter-3 are checked too).
2. Every `media/...` path written in backticks exists.
3. The text has no personal details: emails (placeholders like <your email> are fine),
   UUIDs (device, CoreDevice and app user IDs), iPhone UDIDs, keys and tokens,
   signing identities, user-specific local paths, IP addresses.
   --extra FILE adds literal strings to search for (one per line), for example your
   Apple team ID. Keep that file in the repo's git-ignored .devlog_tools/ (never committed); matches are reported
   without the value.
4. Lists media files that no .md file uses (information only).

Prints OK and exits 0 when everything passes.
"""
import os
import re
import sys

def _pick_dir():
    if '--dir' in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index('--dir') + 1])
    here = os.path.dirname(os.path.abspath(__file__))
    if any(f.endswith('.md') for f in os.listdir(here)) and os.path.isdir(os.path.join(here, 'media')):
        return here
    return os.path.abspath('docs/devlog')


HERE = _pick_dir()

PRIVACY = [
    (re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'), 'email'),
    (re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I), 'uuid'),
    (re.compile(r'\b[0-9A-F]{8}-[0-9A-F]{16}\b'), 'iphone udid'),
    (re.compile(r'ssh-(?:ed25519|rsa) |-----BEGIN [A-Z ]*KEY'), 'key'),
    (re.compile(r'\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,})'), 'token'),
    (re.compile(r'Apple (?:Development|Distribution): ?[A-Z]'), 'signing identity'),
    (re.compile(r'/Users/[^/\s`)]+|/home/[^/\s`)]+|/private/tmp/claude-\d+|Application Support/[^/\s]+/data/users'), 'user path'),
    (re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])'), 'ip address'),
    (re.compile(r'(?i)team[ _-]?id\W{0,3}[A-Z0-9]{10}\b'), 'team id'),
]
ALLOWED_EMAIL = set()  # add public addresses here if a chapter ever needs one


def md_files():
    return sorted(f for f in os.listdir(HERE) if f.endswith('.md'))


def slug(text):
    t = text.strip().lower()
    t = re.sub(r'[^\w\- ]', '', t)
    return t.replace(' ', '-')


def anchors_of(path):
    s = open(path, encoding='utf-8').read()
    ids = set(re.findall(r'<a id="([^"]+)"', s))
    for h in re.findall(r'^#{1,6} (.+)$', s, re.M):
        ids.add(slug(h))
    return ids


def main():
    extra = []
    if '--extra' in sys.argv:
        p = sys.argv[sys.argv.index('--extra') + 1]
        extra = [l.strip() for l in open(p, encoding='utf-8') if l.strip()]
    problems, used, n_links, n_images = [], set(), 0, 0
    anchor_cache = {}
    for name in md_files():
        path = os.path.join(HERE, name)
        text = open(path, encoding='utf-8').read()
        # template examples live in HTML comments: blank them out (keep the line count for line numbers)
        text = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), text, flags=re.S)
        for m in re.finditer(r'(!?)\[[^\]]*\]\(([^)\s]+)\)', text):
            target = m.group(2)
            if re.match(r'[a-z]+:', target):
                continue
            n_links += 1
            n_images += bool(m.group(1))
            file_part, _, anchor = target.partition('#')
            tpath = os.path.normpath(os.path.join(HERE, file_part)) if file_part else path
            if not os.path.exists(tpath):
                problems.append(f'{name}: missing file {target}')
                continue
            if file_part.startswith('media/'):
                used.add(os.path.normpath(file_part))
            if anchor:
                if tpath not in anchor_cache:
                    anchor_cache[tpath] = anchors_of(tpath)
                if anchor not in anchor_cache[tpath]:
                    problems.append(f'{name}: missing anchor {target}')
        for m in re.finditer(r'`(media/[^`\s]+\.(?:jpg|jpeg|png|gif|mp4|mov|webm))`', text):
            n_links += 1
            if not os.path.exists(os.path.join(HERE, m.group(1))):
                problems.append(f'{name}: missing file {m.group(1)}')
            used.add(os.path.normpath(m.group(1)))
        for lineno, line in enumerate(text.splitlines(), 1):
            for rx, label in PRIVACY:
                for hit in rx.finditer(line):
                    if label == 'email' and hit.group(0) in ALLOWED_EMAIL:
                        continue
                    problems.append(f'{name}:{lineno}: privacy [{label}] {hit.group(0)}')
            for lit in extra:
                if lit.lower() in line.lower():
                    problems.append(f'{name}:{lineno}: privacy [extra literal, value hidden]')
    media = set()
    for root, _, files in os.walk(os.path.join(HERE, 'media')):
        for f in files:
            if not f.startswith('.'):
                media.add(os.path.normpath(os.path.relpath(os.path.join(root, f), HERE)))
    unused = sorted(media - used)
    big = [(m, os.path.getsize(os.path.join(HERE, m)) / 1e6) for m in media
           if os.path.getsize(os.path.join(HERE, m)) > 50e6]
    for m, mb in big:
        problems.append(f'{m}: {mb:.0f} MB is too big to push reliably (GitHub refuses > 100 MB) — re-run clips.py with --max-mb/--dur')
    n_clips = sum(1 for m in media if m.lower().endswith(('.mp4', '.mov', '.webm')))
    print(f'{len(md_files())} markdown files, {n_links} links checked ({n_images} images), '
          f'{len(media)} media files ({n_clips} clips), {len(unused)} not linked from any .md file')
    for u in unused:
        print('  unused:', u)
    if problems:
        print(f'PROBLEMS ({len(problems)}):')
        print('\n'.join('  ' + p for p in problems))
        sys.exit(1)
    print('OK: every link resolves and the privacy scan is clean')


if __name__ == '__main__':
    main()
