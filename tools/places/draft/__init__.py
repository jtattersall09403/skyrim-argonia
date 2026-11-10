"""`python -m tools.places draft <place_id>` drafts a place from its source (skill place-build);
`draft join <place_id>` runs the draft's last step alone on the place files as they stand (steps hung on their
decks, residents' promises, names, then the build's network: flights, joins, arrivals, streets and patrols);
`draft check <place_id>` runs the draft's self-checks; `draft render <place_id>` writes top-down PNGs."""
from __future__ import annotations

import json
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
    if argv[0] == "join":
        # the draft's last step alone, on the place files as they stand: what the fit, the clusters, the interiors
        # and the clearance settled is kept, and only what the join's own rules change is written
        from tools.places.draft import walk
        if len(argv) != 2:
            print("usage: python -m tools.places draft join <place_id>", file=sys.stderr)
            return 2
        print(json.dumps({"network": walk.join(argv[1])}))
        return 0
    from tools.places.draft.run import draft
    force = "--force" in argv
    ids = [a for a in argv if not a.startswith("--")]
    if len(ids) != 1:
        print("usage: python -m tools.places draft [check|render] <place_id> [--force]", file=sys.stderr)
        return 2
    counts = draft(ids[0], force=force)
    from tools.places.draft import walk
    # joins, rehomed sleepers, streets and patrols laid on the built network; it leaves the files seated and canonical
    counts["network"] = walk.join(ids[0])
    print(json.dumps(counts, indent=1))
    return 0
