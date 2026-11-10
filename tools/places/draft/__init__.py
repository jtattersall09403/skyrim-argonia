"""`python -m tools.places draft <place_id>` drafts a place from its source (skill place-build);
`draft check <place_id>` runs the draft's self-checks; `draft render <place_id>` writes top-down PNGs."""
from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "check":
        from tools.places.draft.check import main as m
        return m(argv[1:])
    if argv[0] == "render":
        from tools.places.draft.render import main as m
        return m(argv[1:])
    from tools.places.draft.run import draft
    force = "--force" in argv
    ids = [a for a in argv if not a.startswith("--")]
    if len(ids) != 1:
        print("usage: python -m tools.places draft [check|render] <place_id> [--force]", file=sys.stderr)
        return 2
    counts = draft(ids[0], force=force)
    from tools.places.draft import walk
    from tools.places.seat import main as seat_main
    counts["joins"] = walk.join(ids[0])
    if counts["joins"]:
        seat_main([ids[0]])
        from tools.places import edits   # the place files in canonical order, as every writer leaves them
        from tools.places.draft import io
        edits.write_place(io.PLACES / ids[0], edits.load_place(io.PLACES / ids[0]))
    import json
    print(json.dumps(counts, indent=1))
    return 0
