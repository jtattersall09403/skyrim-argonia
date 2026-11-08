import argparse
import sys

from tools.newworld.place import place


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.newworld.place")
    ap.add_argument("cmd", choices=("run", "check", "render", "cell"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--at", type=int, nargs=2, help="cell: cx cy")
    a = ap.parse_args(argv)
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
