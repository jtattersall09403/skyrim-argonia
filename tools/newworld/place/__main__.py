import argparse
import sys

from tools.newworld.place import place


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] and argv[0] in ("refs", "edit", "edits"):
        from tools.newworld.place import edits
        return edits.main(argv)
    ap = argparse.ArgumentParser(prog="python -m tools.newworld.place")
    ap.add_argument("cmd", choices=("run", "check", "render", "cell", "current"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--at", type=int, nargs=2, help="cell: cx cy")
    a = ap.parse_args(argv)
    if a.cmd == "current":      # exit 0 when the refs' manifest holds today's key (writes nothing)
        import json
        m = place.REFS / "manifest.json"
        ok = m.exists() and json.loads(m.read_text()).get("key") == place.key()
        print("placed refs:", "their key is today's" if ok else "their key is not today's")
        return 0 if ok else 1
    if a.cmd == "run":
        place.run(a.force, a.workers)
    elif a.cmd == "cell":
        import time
        place._init()
        t = time.time()
        refs, tally = place.place_cell(a.at[0], a.at[1], [])
        print(len(refs), f"{time.time() - t:.2f} s", dict(tally))
    elif a.cmd == "check":
        from tools.newworld.place import checks
        return checks.run()
    elif a.cmd == "render":
        from tools.newworld.place import render
        render.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
