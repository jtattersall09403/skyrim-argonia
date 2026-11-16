"""What a story writer must know of a place before setting a quest there: its bands, what its record says it holds
and gives, and its source places with what each holds. Read from the place database.

    python3 -m tools.newworld.place_card "Fort Swiftmoth" Gemin        # by name, alias or id
    python3 -m tools.newworld.place_card --kind fort --band D3         # every place of a kind (and a band)
    python3 -m tools.newworld.place_card --region benthic-yobesh --mined   # all notes and the mined sources
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "newworld" / "story" / "data" / "db"


def rows(name: str) -> list[dict]:
    p = DB / f"{name}.jsonl"
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []


def mined() -> dict:
    """Each mined source candidate by id (out/newworld/sources/mined, `python -m tools.places sources-mine`); the
    main tree's copy when this tree has none."""
    out = {}
    for d in (DB.parents[3] / "out" / "newworld" / "sources" / "mined",
              Path("/home/ubuntu/skyrim-argonia/out/newworld/sources/mined")):
        for p in sorted(d.glob("*.jsonl")) if d.exists() else []:
            for line in p.read_text().splitlines():
                if line.strip():
                    c = json.loads(line)
                    out.setdefault(c["candidate_id"], c)
        if out:
            break
    return out


def mined_line(c: dict) -> str:
    counts = ", ".join(f"{k} {v}" for k, v in sorted(c.get("counts", {}).items()) if k not in ("refs", "marker"))
    tags = ", ".join(f"{k} {v}" for k, v in sorted(c.get("tags", {}).items(), key=lambda kv: -kv[1]))
    return (f"    mined: interiors {c.get('interiors') or []} named {c.get('interior_names') or []}; doors out "
            f"{c.get('doors_out')}; land cells {c.get('land_cells')}, wet cells {c.get('wet_cells')}; footprint "
            f"{c.get('footprint_m')} m; counts: {counts}; pieces: {tags}")


def card(place: dict, danger: dict, gives: list[dict], notes: list[dict], sources: list[dict], src: dict,
         mine: dict | None = None) -> str:
    d = danger.get(place["id"], {})
    out = [f"## {place['name']} ({place['id']}): {place['place_kind_id']}, {place['region_id']}, cell "
           f"{place['cell_x']},{place['cell_y']}",
           f"bands: place {place.get('danger_band_id')}, strength {d.get('strength_band_id')}, way in "
           f"{d.get('reach_band_id')}, reward {d.get('reward_band_id')}; {d.get('disposition_id')}; held by "
           f"{place.get('held_by')}; {place.get('population')} people; {place.get('siting')}",
           place.get("summary", "")]
    for g in gives:
        out.append(f"  gives: {g['give_kind_id']} x{g.get('count')}: {g.get('detail')}")
    for n in notes:
        if mine is not None or n["aspect_id"] in ("hooks", "look", "dangers", "source"):
            out.append(f"  {n['aspect_id']}: {n['text']}")
    for s in sorted(sources, key=lambda r: r["rank"]):
        sp = src.get(s["source_place_id"], {})
        out.append(f"  source {s['rank']}: {sp.get('title')} [{sp.get('plugin')}] {sp.get('kind')}; "
                   f"{sp.get('interiors')} interiors, {sp.get('residents')} people, {sp.get('enemies')} hostile, "
                   f"{sp.get('buildings')} buildings. {sp.get('description', '')}")
        if mine is not None and s["source_place_id"] in mine:
            out.append(mined_line(mine[s["source_place_id"]]))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--kind")
    ap.add_argument("--band", help="strength band, e.g. D3")
    ap.add_argument("--region", help="every place of a region")
    ap.add_argument("--mined", action="store_true",
                    help="every note, and each source place's mined interiors, doors and pieces")
    a = ap.parse_args(argv)
    mine = mined() if a.mined else None
    places = rows("place")
    alias = {r["alias"].lower(): r["place_id"] for r in rows("place_alias") if "alias" in r}
    danger = {r["place_id"]: r for r in rows("place_danger")}
    src = {r["id"]: r for r in rows("source_place")}
    chosen = []
    for p in places:
        named = any(n.lower() in (p["name"].lower(), p["id"].lower()) or alias.get(n.lower()) == p["id"]
                    for n in a.names)
        by_kind = a.kind and p["place_kind_id"] == a.kind and (
            not a.band or danger.get(p["id"], {}).get("strength_band_id") == a.band)
        if named or by_kind or (a.region and p["region_id"] == a.region):
            chosen.append(p)
    if not chosen:
        print("no such place", file=sys.stderr)
        return 1
    gives, notes, sources = rows("place_give"), rows("place_note"), rows("place_source")
    for p in chosen:
        print(card(p, danger, [g for g in gives if g["place_id"] == p["id"]],
                   [n for n in notes if n["place_id"] == p["id"]],
                   [s for s in sources if s["place_id"] == p["id"]], src, mine))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
