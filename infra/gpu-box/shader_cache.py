#!/usr/bin/env python3
"""The Community Shaders cache key (1.15-r4-fast-loop): what CS compiles from, read from the build VM's
installed.json (every laid file's hash). The shader sources (Data\\Shaders\\**), the CS DLL and its settings and
feature overrides (SKSE\\Plugins\\CommunityShaders*): a deploy whose key equals the machine's keeps Data\\ShaderCache;
a new machine (or one whose cache was lost) lays the archived cache of that key instead of compiling 3,484 shaders
(~11 min on the g6, 2026-11-02 10:14).

    shader_cache.py key [installed.json]     print the 12-hex key (the default installed.json is the stack's)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

INSTALLED = pathlib.Path.home() / ".argonia" / "stack" / "installed.json"


def shader_files(files: dict) -> dict:
    """Laid path -> hash, for the files CS compiles from or that choose what it compiles."""
    return {k: v[1] for k, v in files.items()
            if k.startswith("shaders\\") or (k.startswith("skse\\plugins\\") and "communityshaders" in k)}


def key(files: dict) -> str:
    own = shader_files(files)
    if not own:
        raise SystemExit("no Community Shaders files in installed.json (is the stack staged?)")
    return hashlib.sha256("".join(f"{k}={own[k]}\n" for k in sorted(own)).encode()).hexdigest()[:12]


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "key":
        print(__doc__)
        return 2
    path = pathlib.Path(argv[1]) if len(argv) > 1 else INSTALLED
    print(key(json.loads(path.read_text())["files"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
