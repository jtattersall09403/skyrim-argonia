import argparse
import sys
from pathlib import Path

from tools.newworld import small


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["tool"]:            # a stage tool's own arguments follow: not ours to parse
        return small.tool(argv[1:])
    ap = argparse.ArgumentParser(prog="tools/newworld/rebuild.sh small", description=small.__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="run", choices=("run", "plan", "cut", "holds", "esm", "readback", "plan-holds", "play", "real-names"))
    ap.add_argument("step", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--from", dest="src", help="the real build to cut from (default: this tree's, else the main tree's)")
    ap.add_argument("--to")
    ap.add_argument("--force", action="append", default=[])
    a = ap.parse_args(argv)
    src = small.source(a.src)
    if a.cmd == "cut":
        small.cut(src)
        return 0
    if a.cmd == "holds":
        from tools.newworld.small import holds
        return holds.check(src, Path(small.ROOT))
    if a.cmd == "esm":
        return small.esm(a.step)
    if a.cmd == "readback":
        return small.readback()
    if a.cmd == "plan-holds":
        return small.plan_holds()
    if a.cmd == "real-names":       # <folder of the machine's logs> <folder to write>
        print(f"{small.real_names(Path(a.step), Path(a.dst))} files under the stage tools' names in {a.dst}")
        return 0
    if a.cmd == "play":
        small.play()
        return 0
    return small.run(src, a.to, tuple(a.force), plan_only=a.cmd == "plan")


if __name__ == "__main__":
    sys.exit(main())
