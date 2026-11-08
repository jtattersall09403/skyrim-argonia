"""The owner's water edits, from the atlas's shared database into the build's source files.

The atlas (https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g, built by tools/newworld/map_page.py) keeps two
collections: `water_edits` (one document per body id: kind, flows, flow_deg, speed, name) and `water_paint` (one
document per painted stroke: kind, flows, radius_px, pts as a flat [x, y, ...] list in map pixels).

How an agent pulls them (the database is reached only through the ArtifactData tool, not from Python):
1. ArtifactData list, url = the atlas, collection = water_edits, out_dir = <dir>   (page with query.cursor if
   next_cursor comes back); the same for collection = water_paint. Each document lands as
   <dir>/water_edits/<id>.json and <dir>/water_paint/<id>.json.
2. python3 -m tools.newworld.water_overrides_pull <dir>
   writes newworld/sources/water_overrides.json ({body id: {water_kind_id, flows, flow_toward_deg, speed, name}})
   and newworld/sources/water_paint.json ([{water_kind_id, flows, speed, radius_px, points}], oldest first).
3. python3 -m tools.newworld.water_kinds --png, then build_db, puts them into the classification and the db.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.newworld import frame as f

SRC = f.ROOT / "sources"
KINDS = {"ocean", "shallow-coast", "bay", "estuary", "river", "stream", "lake", "pond", "green-marsh",
         "blackwater-swamp"}
SPEEDS = {"still", "slow", "moderate", "fast"}


def load(dirpath: Path, coll: str) -> dict:
    out = {}
    for p in sorted((dirpath / coll).glob("*.json")):
        d = json.loads(p.read_text())
        d = d.get("data", d) if isinstance(d.get("data"), dict) else d
        out[p.stem] = d
    return out


def convert(edits: dict, paint: dict) -> tuple[dict, list, list]:
    ov, problems = {}, []
    for bid, e in sorted(edits.items()):
        o = {}
        if e.get("kind"):
            if e["kind"] in KINDS:
                o["water_kind_id"] = e["kind"]
            else:
                problems.append(f"{bid}: unknown kind {e['kind']}")
        if e.get("flows") is not None:
            o["flows"] = bool(e["flows"])
        if e.get("flow_deg") is not None:
            o["flow_toward_deg"] = round(float(e["flow_deg"])) % 360
        if e.get("speed") in SPEEDS:
            o["speed"] = e["speed"]
        if e.get("name"):
            o["name"] = str(e["name"])[:80]
        if o:
            ov[bid] = o
    strokes = []
    for sid, st in sorted(paint.items(), key=lambda kv: str(kv[1].get("at", ""))):
        pts = st.get("pts") or []
        if st.get("kind") not in KINDS or len(pts) < 2:
            problems.append(f"paint {sid}: unusable")
            continue
        strokes.append({"id": sid, "water_kind_id": st["kind"], "flows": bool(st.get("flows")),
                        "speed": st.get("speed") if st.get("speed") in SPEEDS else None,
                        "radius_px": int(st.get("radius_px") or 20),
                        "points": [[int(pts[i]), int(pts[i + 1])] for i in range(0, len(pts) - 1, 2)]})
    return ov, strokes, problems


def main(dirpath: str) -> None:
    d = Path(dirpath)
    ov, strokes, problems = convert(load(d, "water_edits"), load(d, "water_paint"))
    (SRC / "water_overrides.json").write_text(json.dumps(ov, indent=1, sort_keys=True) + "\n")
    (SRC / "water_paint.json").write_text(json.dumps(strokes, indent=1) + "\n")
    print(f"{len(ov)} body edits, {len(strokes)} painted strokes", *problems, sep="\n")


if __name__ == "__main__":
    main(sys.argv[1])
