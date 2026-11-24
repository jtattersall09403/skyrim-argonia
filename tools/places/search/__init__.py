"""Search over the asset catalogue (docs/design/place-studio.md, Search): two halves scored together.

  text  a small CPU embedding model (bge-small) of each row's names, editor id, model path and descriptor, with
        exact and prefix matches on editor id and name so a typed name always finds its thing first;
  look  a CLIP vector of a thumbnail of each distinct model (look.py), compared with the query's CLIP text vector,
        so a query finds a model by what it looks like.

  python -m tools.places search build [--catalogue PATH]   build or update the text index (only changed keys embed)
  python -m tools.places search look [--jobs 4] [--limit N] [--mods] [--retry-errors] [--no-embed]
                                    draw every model not yet drawn, then embed the new thumbnails (resumable)
  python -m tools.places search look-report               counts: models, looked, failed by reason, embedded
  python -m tools.places search query <text> [--scope all|source --source-id ID --kind K --limit N --look]
                                    --look prints each hit's thumbnail path
  python -m tools.places search sheet <text> | --keys K ... [--n 48] [--out PNG]
                                    one contact sheet of the top hits' thumbnails with key and editor id under each
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
    lk = sub.add_parser("look")
    lk.add_argument("--jobs", type=int, default=4)
    lk.add_argument("--limit", type=int)
    lk.add_argument("--mods", action="store_true", help="mods' models only")
    lk.add_argument("--retry-errors", action="store_true")
    lk.add_argument("--no-embed", action="store_true")
    sub.add_parser("look-report")
    q = sub.add_parser("query")
    q.add_argument("text")
    q.add_argument("--scope", default="all")
    q.add_argument("--source-id")
    q.add_argument("--kind")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--look", action="store_true", help="print each hit's thumbnail path")
    s = sub.add_parser("sheet")
    s.add_argument("text", nargs="?")
    s.add_argument("--keys", nargs="+")
    s.add_argument("--kind")
    s.add_argument("--n", type=int, default=48)
    s.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        stats = Index.open().update(catalogue_path(a.catalogue))
        print(json.dumps(stats))
        return 0
    if a.cmd == "look":
        from tools.places.search import look
        print(json.dumps(look.thumbs(a.jobs, a.limit, a.mods, a.retry_errors)), flush=True)
        if not a.no_embed:
            print(json.dumps(look.embed()), flush=True)
        return 0
    if a.cmd == "look-report":
        from tools.places.search import look
        print(json.dumps(look.report(), indent=1))
        return 0
    if a.cmd == "sheet":
        from tools.places.search import sheet
        if not (a.text or a.keys):
            ap.error("sheet needs a query or --keys")
        path = sheet.make(a.text, a.keys, a.n, a.out, a.kind)
        print(path)
        return 0
    for hit in Index.open().query(a.text, scope=a.scope, source_id=a.source_id, kind=a.kind, limit=a.limit):
        line = (f"{hit['score']:.3f} [{hit['matched']}]  {hit['key']}  {hit.get('edid')}  {hit.get('name') or ''}  "
                f"{hit.get('model')}")
        if a.look:
            line += f"  {hit.get('look') or '(not looked: ' + (hit.get('look_why') or 'no thumbnail') + ')'}"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
