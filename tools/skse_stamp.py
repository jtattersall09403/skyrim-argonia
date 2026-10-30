"""Decide whether make deploy can skip the 124 s SKSE build (infra/gpu-box/deploy.sh step 3).

The stamp is "<git tree hash of skse/>:<preset>"; skse_build.sh writes it beside the built DLLs on the
game machine after a successful, clean-tree build. The decision is a pure function; the CLI feeds it
the remote probe's text (lines "stamp=<value>" and "dll=<name>" for each DLL found).
"""
import sys

DLLS = ("ArgoniaCore.dll", "ArgoniaBridge.dll")


def make_stamp(tree: str, preset: str) -> str:
    return f"{tree.strip()}:{preset}"


def can_skip(stamp: str, remote_stamp: str | None, dlls_present, dirty: bool) -> bool:
    """Skip only for a clean skse/ worktree whose stamp matches and both DLLs are on the machine."""
    if dirty or not stamp or not remote_stamp:
        return False
    return remote_stamp.strip() == stamp and all(d in set(dlls_present) for d in DLLS)


def parse_probe(text: str):
    stamp, dlls = None, []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("stamp="):
            stamp = line[6:].strip() or None
        elif line.startswith("dll="):
            dlls.append(line[4:].strip())
    return stamp, dlls


if __name__ == "__main__":
    # skse_stamp.py <tree> <preset> <dirty 0|1>   (remote probe text on stdin); exit 0 = skip the build
    tree, preset, dirty = sys.argv[1:4]
    rs, dl = parse_probe(sys.stdin.read())
    sys.exit(0 if can_skip(make_stamp(tree, preset), rs, dl, dirty == "1") else 1)
