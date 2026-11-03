#!/usr/bin/env python3
"""Whether the LOD archive for this ArgoniaWorld is already in the private bucket with the machine's mod (lod.sh
archive: a resumed run re-uploaded 1.7 GB every time, 2026-11-03).

    aws s3api head-object ... | lod_skip.py <files> <bytes>     exit 0: archived (skip), 1: upload

An archive lod.sh wrote carries its mod's file count and byte sum as metadata (argonia-files, argonia-bytes); they must
match. An older one without them matches when its size is what a tar of that mod can be: each file's bytes rounded up
to a 512-byte block plus a 512-byte header per file, and slack for the directory headers and the end blocks.
"""
from __future__ import annotations

import json
import sys

SLACK = 1 << 20  # directory headers (512 each) and the tar's end padding


def archived(head: dict | None, files: int, size: int) -> bool:
    if not head or files <= 0:
        return False
    meta = {k.lower(): v for k, v in (head.get("Metadata") or {}).items()}
    if "argonia-files" in meta or "argonia-bytes" in meta:
        return meta.get("argonia-files") == str(files) and meta.get("argonia-bytes") == str(size)
    n = int(head.get("ContentLength") or 0)
    low = size + 512 * files
    return low <= n <= low + 512 * files + SLACK


def main(argv=None) -> int:
    a = argv if argv is not None else sys.argv[1:]
    text = sys.stdin.read().strip()
    try:
        head = json.loads(text) if text else None
    except ValueError:
        head = None
    return 0 if archived(head, int(a[0]), int(a[1])) else 1


if __name__ == "__main__":
    sys.exit(main())
