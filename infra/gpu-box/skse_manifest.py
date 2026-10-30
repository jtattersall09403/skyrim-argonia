#!/usr/bin/env python3
"""Content-aware file times for skse_build.sh (the stale-object fix).

The tree goes to the game machine as a tar that keeps file times, so Ninja rebuilds only what changed. A source
edited on the build VM can carry an mtime older than the .obj Ninja built earlier, and Ninja then skips it and the
link fails. So before tarring:
  touch  <tree> <manifest> <filelist>   set mtime=now on each listed file whose SHA-256 differs from the manifest
                                        (path<TAB>sha256 per line) or is new; unchanged files keep their time
  save   <tree> <manifest> <filelist>   write the manifest for the listed files (deleted files drop out); run only
                                        after a build succeeded, so a failed build leaves its edits to be touched again
The filelist is NUL-separated paths relative to <tree> (git ls-files -co -z).
"""
import hashlib, os, sys


def read_list(path):
    with open(path, 'rb') as f:
        return [p.decode() for p in f.read().split(b'\0') if p]


def digest(tree, rel):
    h = hashlib.sha256()
    with open(os.path.join(tree, rel), 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load(manifest):
    try:
        with open(manifest, encoding='utf-8') as f:
            return dict(line.rstrip('\n').split('\t', 1) for line in f if '\t' in line)
    except FileNotFoundError:
        return {}


def current(tree, files):
    return {rel: digest(tree, rel) for rel in files if os.path.isfile(os.path.join(tree, rel))}


def changed(tree, files, manifest):
    old = load(manifest)
    return [rel for rel, h in current(tree, files).items() if old.get(rel) != h]


def touch(tree, files, manifest, now=None):
    out = changed(tree, files, manifest)
    for rel in out:
        os.utime(os.path.join(tree, rel), None if now is None else (now, now))
    return out


def save(tree, files, manifest):
    cur = current(tree, files)
    tmp = manifest + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for rel in sorted(cur):
            f.write(f'{rel}\t{cur[rel]}\n')
    os.replace(tmp, manifest)


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] not in ('touch', 'save'):
        sys.exit(__doc__)
    cmd, tree, manifest, lst = sys.argv[1:]
    files = read_list(lst)
    if cmd == 'touch':
        c = touch(tree, files, manifest)
        print(f'skse: {len(c)} of {len(files)} files changed since the last good build (mtime set to now)')
    else:
        save(tree, files, manifest)
