"""Check place records against their tier, their gives and the ground before they are written (decision 0040).

    python3 -m tools.newworld.record_check            # every place in the built database
    python3 -m tools.newworld.record_check jal-veesa  # one or more places

The consistency checker's internal and ground families (tools/newworld/consistency.py holds the one set of rules),
run for the named places: population against the settlement tier and the true settlements' order, gives against
the disposition, water words and siting against the classified water, every Hist pool a pool of sap. One fault line
per finding; exit 1 when any stands.
"""
from __future__ import annotations

import sys

from tools.newworld import consistency as C

FAMILIES = ("internal", "ground")


def faults(ctx: dict, places: list[str] | None = None) -> list[C.Finding]:
    R = C.Report()
    for fam in FAMILIES:
        if places:
            for pid in places:
                C.FAMILIES[fam](ctx, R, pid)
        else:
            C.FAMILIES[fam](ctx, R)
    return R.items


def main(argv: list[str]) -> int:
    ctx = C.load()
    unknown = [p for p in argv if p not in ctx["places"]]
    if unknown:
        print(f"no such place: {', '.join(unknown)}")
        return 2
    found = faults(ctx, argv or None)
    for f in found:
        print(f"{f.place}: {f.family}: {f.cause}: {f.what}  [{f.evidence}]")
    print(f"{len(found)} faults in {len(argv) or len(ctx['places'])} places")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
