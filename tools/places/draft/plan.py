"""`draft.plan`: the place's plan, written before the first stage runs (skill place-build, "The place record is the
brief"). One line per thing the record names, set against the pieces that deliver it:

  {"thing": "<what the record names>", "by": "<the source or added pieces that deliver it>",
   "gives"?: "<a promise kind of the record>", "structure"?: "<a major source structure>", "kept"?: bool}

Every promise of the record has a line naming its kind in `gives`; every major source structure (`structures`) has a
line naming it in `structure` with its verdict in `kept`, and a structure the plan drops has every piece of it in
`draft.drop`. `draft plan <place_id>` prints the plan and its faults.
"""
from __future__ import annotations

import sys


def faults(plan: list[dict], gives: list[dict], structures: dict[str, dict], drop: dict) -> list[str]:
    """What the plan leaves unsaid or undone: a promise with no line, a structure with no verdict, a dropped
    structure with pieces still standing."""
    bad = []
    for k, ln in enumerate(plan):
        if not ln.get("thing") or not ln.get("by"):
            bad.append(f"plan line {k}: a line names the thing and what delivers it")
    said = {ln.get("gives") for ln in plan}
    for g in gives:
        if g.get("kind") not in said:
            bad.append(f"plan: the promise {g.get('kind')} has no line")
    verdict = {ln["structure"]: ln for ln in plan if ln.get("structure")}
    for cls, v in sorted(structures.items()):
        ln = verdict.get(cls)
        if ln is None or "kept" not in ln:
            bad.append(f"plan: the source's {cls} ({len(v['refs'])} pieces) has no verdict")
        elif not ln["kept"]:
            left = [r for r in v["refs"] if r not in drop]
            if left:
                bad.append(f"plan: the {cls} is dropped but {len(left)} of its pieces are not in draft.drop")
    return bad


def for_place(place_id: str) -> tuple[list[dict], list[str]]:
    import json

    from tools.places.draft import io, structures
    from tools.places.draft.run import place_record
    dec = json.loads((io.PLACES / place_id / "place.json").read_text()).get("draft") or {}
    plan = dec.get("plan") or []
    return plan, faults(plan, place_record(place_id)[1], structures.for_place(place_id), dec.get("drop") or {})


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft plan <place_id>")
        return 2
    plan, bad = for_place(argv[0])
    for ln in plan:
        tag = ln.get("gives") or (f"{ln['structure']}: {'kept' if ln.get('kept') else 'dropped'}"
                                  if ln.get("structure") else "")
        print(f"{argv[0]}: {ln.get('thing')}{f' [{tag}]' if tag else ''} <- {ln.get('by')}")
    for b in bad:
        print("FAIL", b)
    print(f"draft plan {argv[0]}: {'PASS' if not bad else f'{len(bad)} problems'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
