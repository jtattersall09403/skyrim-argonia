"""`draft.plan`: the place's plan, written before the first stage runs (skill place-build, "The place record is the
brief"). The one shape, read by `draft plan`, `draft check` and the consistency checker's draft family:

  {"source"?: "<which source and why>",
   "look":       [{"line": "<a thing the record's look names>", "by": "<the pieces that deliver it>"}],
   "gives":      [{"kind": "<a promise kind of the record>", "by": "<what delivers it>", "line"?: "<its words>"}],
   "structures": [{"cluster"?: "<source cluster ids, comma-separated>", "structure"?: "<a major structure class>",
                   "what": "<what it is>", "verdict": "kept" | "dropped", "why": "<the reason>"}]}

Every row has its `by` (or `why`); every promise of the record has a `gives` row; every standing source building's
cluster and every major source structure (`draft structures`) has a verdict; a dropped structure has every piece in
`draft.drop` and no building of a dropped cluster stands. `faults` returns (cause, detail) pairs.
"""
from __future__ import annotations

import sys

MISSING = "a draft with no plan"
UNDELIVERED = "a plan line delivered by nothing"
NO_GIVE = "the plan misses a gives row"
NO_VERDICT = "a major structure without a verdict"
STANDS = "a dropped structure still stands"


def _clusters(row: dict) -> list[str]:
    return [c.strip() for c in str(row.get("cluster") or "").split(",") if c.strip()]


def faults(plan, gives: list[dict], structures: dict[str, dict] | None = None, drop: dict | None = None,
           clusters: set[str] | None = None) -> list[tuple[str, str]]:
    """What the plan leaves unsaid or undone. `gives`: the record's promise rows (place_give: {give_kind_id}); `structures`: the source's
    major structures (`structures.for_place`: {class: {refs}}); `drop`: `draft.drop`; `clusters`: the source clusters
    holding a standing building in the draft. Each is checked only when given."""
    if not isinstance(plan, dict) or not (plan.get("look") or plan.get("gives") or plan.get("structures")):
        return [(MISSING, "draft.plan is missing or not {look, gives, structures}: write it against the place record "
                          "before drafting (place-build)")]
    bad = []
    for key, need in (("look", "by"), ("gives", "by"), ("structures", "why")):
        for k, row in enumerate(plan.get(key) or []):
            if not str((row or {}).get(need) or "").strip():
                bad.append((UNDELIVERED, f"{key}[{k}] '{row.get('line') or row.get('kind') or row.get('what')}' has no {need}"))
    said = {g.get("kind") for g in plan.get("gives") or []}
    for g in gives:
        kind = g.get("kind") or g.get("give_kind_id")
        if kind not in said:
            bad.append((NO_GIVE, f"the promise {kind} has no gives row"))
    rows = plan.get("structures") or []
    for k, row in enumerate(rows):
        if row.get("verdict") not in ("kept", "dropped"):
            bad.append((NO_VERDICT, f"structures[{k}] '{row.get('what')}' has no verdict kept|dropped"))
    by_class = {r["structure"]: r for r in rows if r.get("structure")}
    for cls, v in sorted((structures or {}).items()):
        r = by_class.get(cls)
        if r is None or r.get("verdict") not in ("kept", "dropped"):
            bad.append((NO_VERDICT, f"the source's {cls} ({len(v['refs'])} pieces) has no verdict"))
        elif r["verdict"] == "dropped":
            left = [x for x in v["refs"] if x not in (drop or {})]
            if left:
                bad.append((STANDS, f"the {cls} is dropped but {len(left)} of its pieces are not in draft.drop"))
    by_cluster = {c: r for r in rows for c in _clusters(r)}
    for cid in sorted(clusters or ()):
        r = by_cluster.get(cid)
        if r is None:
            bad.append((NO_VERDICT, f"the structure of cluster {cid} has no verdict"))
        elif r.get("verdict") == "dropped":
            bad.append((STANDS, f"cluster {cid} still stands though the plan drops it ({r.get('why')})"))
    return bad


def for_place(place_id: str) -> tuple[dict, list[tuple[str, str]]]:
    import json

    from tools.places.draft import io, structures
    from tools.places.draft.run import place_record
    dec = json.loads((io.PLACES / place_id / "place.json").read_text()).get("draft") or {}
    plan = dec.get("plan")
    return plan, faults(plan, place_record(place_id)[1], structures.for_place(place_id), dec.get("drop") or {})


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft plan <place_id>")
        return 2
    plan, bad = for_place(argv[0])
    plan = plan if isinstance(plan, dict) else {}
    for r in plan.get("look") or []:
        print(f"{argv[0]}: look  {r.get('line')} <- {r.get('by')}")
    for r in plan.get("gives") or []:
        print(f"{argv[0]}: gives {r.get('kind')} <- {r.get('by')}")
    for r in plan.get("structures") or []:
        print(f"{argv[0]}: {r.get('structure') or r.get('cluster')} {r.get('verdict')}: {r.get('what')} ({r.get('why')})")
    for cause, detail in bad:
        print(f"FAIL {cause}: {detail}")
    print(f"draft plan {argv[0]}: {'PASS' if not bad else f'{len(bad)} problems'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
