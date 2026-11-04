#!/usr/bin/env python3
"""The Community Shaders cache key (1.15-r4-fast-loop): what CS compiles from, read from the build VM's
installed.json (every laid file's hash). The shader sources (Data\\Shaders\\**), the CS DLL and its settings and
feature overrides (SKSE\\Plugins\\CommunityShaders*): a deploy whose key equals the machine's keeps Data\\ShaderCache;
a new machine (or one whose cache was lost) lays the archived cache of that key instead of compiling 3,484 shaders
(~11 min on the g6, 2026-11-02 10:14).

    shader_cache.py key [installed.json] [--gpu "<name>, <driver>"]
        print the key: 12 hex of the shaders, plus "-<6 hex>" of the GPU name and driver when given (a clone on another
        GPU recompiled everything on each launch, round 6, 2026-11-04: the cache is keyed by the card it was built on)
    shader_cache.py decide <machine-key|-> <key> <archived 0|1>     print current | lay | compile
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


def gpu_tag(gpu: str) -> str:
    """6 hex of "name, driver" (nvidia-smi --query-gpu=name,driver_version --format=csv,noheader), case and space blind."""
    return hashlib.sha256(" ".join(gpu.lower().split()).encode()).hexdigest()[:6]


def full_key(files: dict, gpu: str = "") -> str:
    return key(files) + (f"-{gpu_tag(gpu)}" if gpu.strip() else "")


def decide(have: str, want: str, archived: bool) -> str:
    """The deploy's choice: the machine's cache is this key's (current), the archive has it (lay), or compile."""
    if have == want:
        return "current"
    return "lay" if archived else "compile"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "decide" and len(argv) == 4:
        print(decide("" if argv[1] == "-" else argv[1], argv[2], argv[3] == "1"))
        return 0
    if not argv or argv[0] != "key":
        print(__doc__)
        return 2
    args, gpu = argv[1:], ""
    if "--gpu" in args:
        i = args.index("--gpu")
        gpu = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    path = pathlib.Path(args[0]) if args else INSTALLED
    print(full_key(json.loads(path.read_text())["files"], gpu))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
