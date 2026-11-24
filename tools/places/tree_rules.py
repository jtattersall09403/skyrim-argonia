"""The owner's tree notes into the placement rule (the skill world-build, A world plant moved at a place).

A note about a tree the world placed (tools/places/notes.py: a thing with `world` and `sink_m`, the depth its pivot
sits under the ground once he set it right) speaks for every tree of that type. This step gathers the sent, unanswered
tree notes of every place by tree type, sets that type's sink window in the flora table (newworld/story/data/db/
flora_base.jsonl `sink_lo_m`, `sink_hi_m`, `sink_m`, metres at scale 1) to the depths he gave, and answers each note
with the old and new window. The world is not rebuilt and the ground is never regenerated: the table is a source the
`place` and `edits` stages read (tools/newworld/rebuild.py, `db:flora_base`), so `tools/newworld/rebuild.sh plan`
reports them stale from it until a rebuild the owner asks for reseats every placed tree of that type.

    python -m tools.places tree_rules            the changes it would make, per tree type, and how many trees each reseats
    python -m tools.places tree_rules --apply    make them and answer the notes
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from tools.places import notes as N

DB = Path(__file__).resolve().parents[2] / "newworld/story/data/db/flora_base.jsonl"
PLACED = Path(__file__).resolve().parents[2] / "out/newworld/plugin/placed/flora"


def _form_key(base: str) -> str:
    """Ours "Black Marsh.esm:0D864C" as the flora table's "0D864C:black marsh.esm"."""
    plugin, _, fid = str(base).rpartition(":")
    return f"{fid}:{plugin}".lower()


def gathered(places: Path) -> dict[str, list[tuple[str, dict, float]]]:
    """{base: [(place_id, note, sink_m)]} over the sent, unanswered notes about world trees."""
    out: dict = {}
    for d in sorted(p for p in places.iterdir() if (p / "edits").is_dir()):
        for n in N.read(d.name, places):
            if N.state(n) != "sent":
                continue
            for t in n.get("things") or []:
                if t.get("world") and isinstance(t.get("sink_m"), (int, float)):
                    out.setdefault(t["world"].get("base") or t.get("base"), []).append((d.name, n, float(t["sink_m"])))
    return out


def window(sinks: list[float]) -> dict:
    """The new sink window from the owner's depths: from the shallowest to the deepest he set, its median the sink."""
    return {"sink_lo_m": round(min(sinks), 3), "sink_hi_m": round(max(sinks), 3), "sink_m": round(statistics.median(sinks), 3)}


def placed_count(base: str, placed: Path = PLACED) -> int:
    """How many trees of this base the placement holds: what the next rebuild reseats."""
    want = f'"key":"{_form_key(base)}"'
    n = 0
    for f in sorted(placed.glob("cy-*.jsonl")):
        with open(f, encoding="utf-8") as h:
            n += sum(1 for ln in h if want in ln.lower())
    return n


def plan(places: Path, db: Path = DB, placed: Path = PLACED) -> list[dict]:
    rows = [json.loads(ln) for ln in db.read_text(encoding="utf-8").splitlines() if ln.strip()]
    by_fk = {str(r.get("form_key", "")).lower(): r for r in rows}
    out = []
    for base, items in sorted(gathered(places).items()):
        r = by_fk.get(_form_key(base))
        old = {k: r.get(k) for k in ("sink_lo_m", "sink_hi_m", "sink_m")} if r else None
        out.append({"base": base, "flora": r.get("id") if r else None, "old": old, "new": window([s for _, _, s in items]),
                    "notes": [(pid, n["id"]) for pid, n, _ in items], "reseats": placed_count(base, placed) if r else 0})
    return out


def apply(changes: list[dict], places: Path, db: Path = DB) -> None:
    lines = db.read_text(encoding="utf-8").splitlines()
    want = {c["flora"]: c for c in changes if c["flora"]}
    out = []
    for ln in lines:
        if ln.strip():
            r = json.loads(ln)
            c = want.get(r.get("id"))
            if c:
                r.update(c["new"])
                r["sink_measured_in"] = "owner tree notes"
                ln = json.dumps(r, ensure_ascii=False, separators=(",", ":"))
        out.append(ln)
    db.write_text("\n".join(out) + "\n", encoding="utf-8")
    for c in changes:
        if not c["flora"]:
            continue
        o, w = c["old"], c["new"]
        was = (f"{o['sink_lo_m']} to {o['sink_hi_m']} m" if o.get("sink_lo_m") is not None
               else f"{o['sink_m']} m" if o.get("sink_m") is not None else "its kind's default")
        reply = (f"The depth you set is now the rule for every tree of this type: its sink was "
                 f"{was} and is now {w['sink_lo_m']} to {w['sink_hi_m']} m under "
                 f"the ground. The next world rebuild reseats all {c['reseats']} of them.")
        for pid, nid in c["notes"]:
            N.done(pid, nid, reply, places)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places tree_rules")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--places-dir", type=Path, default=N.PLACES)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--placed", type=Path, default=PLACED)
    a = ap.parse_args(argv)
    ch = plan(a.places_dir, a.db, a.placed)
    for c in ch:
        print(f"{c['base']} ({c['flora'] or 'not in the flora table'}): sink {c['old']} -> {c['new']}, "
              f"from notes {c['notes']}; the next rebuild reseats {c['reseats']}")
    if not ch:
        print("no tree notes waiting")
    if a.apply and ch:
        apply(ch, a.places_dir, a.db)
        print("flora_base changed; `tools/newworld/rebuild.sh plan` now shows the place and edits stages stale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
