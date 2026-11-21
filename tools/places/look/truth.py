"""`python -m tools.places look truth [--keep DIR]`: the look audit. Proves the pictures show what is there.

On the golden scene (tools/tests/fixtures/look_truth: known pieces, ground, a pool on two land rows, a marker, a
model that is missing, a stair, a bridge, a room) a look daemon of its own renders and every check asserts from the id
buffer and the image itself: geometry drawn where it is, eye cameras on the ground under them and out of every piece,
honest scores, pick, counts of what was sent, loaded and drawn, freshness after the files change, land rows that add,
rooms. `look truth <place> --sample N`: the sampling audit of a real draft (N pieces at random across kinds, each
`at <piece>`: in frame, its silhouette's centre within 5% of the frame of where its box projects).

Prints one line per check (PASS, FAIL or XFAIL with the reason) and a JSON summary; exit 1 on any FAIL.
Run by `LOOK_TRUTH=1 pytest tools/tests/test_places_look_truth.py` too. The fixture run takes about two minutes."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUDGET = ROOT / "tools" / "tests" / "fixtures" / "look_truth" / "budget.json"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(argv: list[str]) -> int:
    """Set up the golden scene (or the real place) and run the checks in a child with its own environment: the look
    modules read their folders and ports when imported."""
    keep = argv[argv.index("--keep") + 1] if "--keep" in argv else None
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--keep", "--sample"))]
    root = Path(keep or tempfile.mkdtemp(prefix="look-truth-"))
    root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LOOK_OUT=str(root / "look"), LOOK_PORT=str(free_port()), PYTHONPATH=str(ROOT))
    if not pos:
        sys.path.insert(0, str(ROOT / "tools" / "tests" / "fixtures" / "look_truth"))
        import make   # the golden scene's writer
        env |= make.make(root)
        args = ["--fixture"]
    else:
        args = ["--place", pos[0], "--sample", argv[argv.index("--sample") + 1] if "--sample" in argv else "40"]
    r = subprocess.run([sys.executable, "-m", "tools.places.look.truth_checks", str(root), *args], env=env, cwd=ROOT)
    if not keep and not pos:
        subprocess.run(["rm", "-rf", str(root)])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
