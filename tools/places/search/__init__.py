"""Search over the asset catalogue (docs/design/place-studio.md, Search): a small CPU embedding model, a vector
index on disk updated by key, and exact and prefix matches on editor id and name so a typed name always finds
its thing.

  python -m tools.places search build [--catalogue PATH]   build or update the index (only changed keys embed)
  python -m tools.places search query <text> [--scope all|source --source-id ID --kind K --limit N]
"""
from __future__ import annotations

import argparse
import json
import sys

from tools.places.search.index import Index, catalogue_path


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places search")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--catalogue")
    q = sub.add_parser("query")
    q.add_argument("text")
    q.add_argument("--scope", default="all")
    q.add_argument("--source-id")
    q.add_argument("--kind")
    q.add_argument("--limit", type=int, default=10)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        stats = Index.open().update(catalogue_path(a.catalogue))
        print(json.dumps(stats))
        return 0
    for hit in Index.open().query(a.text, scope=a.scope, source_id=a.source_id, kind=a.kind, limit=a.limit):
        print(f"{hit['score']:.3f}  {hit['key']}  {hit.get('edid')}  {hit.get('name') or ''}  {hit.get('model')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
