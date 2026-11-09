"""python -m tools.places assets <verb>: see tools/places/assets/__init__.py."""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str]) -> int:
    import tools.places.assets as A
    ap = argparse.ArgumentParser(prog="python -m tools.places assets")
    sub = ap.add_subparsers(dest="verb", required=True)
    m = sub.add_parser("mesh")
    m.add_argument("model")
    m.add_argument("--level", type=int, default=0)
    t = sub.add_parser("tex")
    t.add_argument("path")
    t.add_argument("--size", type=int, default=512)
    w = sub.add_parser("warm")
    w.add_argument("bundles", nargs="+", help="bundle ids under out/places/bundles, or bundle directories")
    w.add_argument("--jobs", type=int, default=3)
    w.add_argument("--size", type=int, default=512)
    sub.add_parser("land")
    sub.add_parser("catalogue")
    r = sub.add_parser("render")
    r.add_argument("model")
    r.add_argument("png")
    r.add_argument("--level", type=int, default=0)
    e = sub.add_parser("evict")
    e.add_argument("--cap-mb", type=float)
    a = ap.parse_args(argv)
    if a.verb == "mesh":
        print(json.dumps(A.mesh_info(a.model, a.level), indent=1))
    elif a.verb == "tex":
        i = A.tex_info(a.path, a.size)
        print(json.dumps(i, indent=1) if i else "not found")
        return 0 if i else 1
    elif a.verb == "warm":
        from tools.places.assets import warm
        rep = warm.run(a.bundles, a.jobs, a.size)
        print(json.dumps(rep["summary"], indent=1))
    elif a.verb == "land":
        from tools.places.assets import land
        print(json.dumps(land.run()["summary"], indent=1))
    elif a.verb == "catalogue":
        from tools.places.assets import catalogue
        print(json.dumps(catalogue.run(), indent=1))
    elif a.verb == "render":
        from tools.places.assets import render
        open(a.png, "wb").write(render.to_png(A.mesh(a.model, a.level).read_bytes()))
        print(a.png)
    elif a.verb == "evict":
        from tools.places.assets import cache
        print(json.dumps(cache.evict(int(a.cap_mb * 1024 * 1024) if a.cap_mb else None)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
