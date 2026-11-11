"""The owner's water edits, from the atlas's shared database into the build's source files.

The atlas (https://claude.ai/artifact/SwMRMPndRrXfEKtTuodNsb, built by tools/newworld/map_page.py) keeps two
collections: `water_edits` (one document per body id: kind, flows, flow_deg, speed, name, and point, a map pixel inside the body
that finds it again after a terrain rebuild changes ids) and `water_paint` (one
document per painted stroke: kind, flows, radius_px, pts as a flat [x, y, ...] list in map pixels).

How an agent pulls them (the database is reached only through the ArtifactData tool, not from Python):
1. ArtifactData list, url = the atlas, collection = water_edits, out_dir = <dir>   (page with query.cursor if
   next_cursor comes back); the same for collection = water_paint. Each document lands as
   <dir>/water_edits/<id>.json and <dir>/water_paint/<id>.json.
2. python3 -m tools.newworld.water_overrides_pull <dir>
   writes newworld/sources/water_overrides.json ({body id: {water_kind_id, flows, flow_toward_deg, speed, name, point, at,
   area_m2, held}}) and newworld/sources/water_paint.json ([{water_kind_id, flows, speed, radius_px, points}], oldest
   first). Each edit taken in is stamped from the classification the atlas shows (out/newworld/water_classified.*):
   `area_m2`, the area of the body it was made on, and for a kind edit `held`, that body's water kept in
   newworld/sources/water_owner_bodies.png (tools/newworld/water_held.py), so the edit holds over the same water on
   every later build. Run it on the machine and the build the atlas was published from.
3. python3 -m tools.newworld.water_kinds --png, then build_db, puts them into the classification and the db.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.newworld import frame as f
from tools.newworld import water_held

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
        if e.get("at"):
            o["at"] = str(e["at"])
        if isinstance(e.get("point"), list) and len(e["point"]) == 2:
            o["point"] = [int(e["point"][0]), int(e["point"][1])]
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


def merge(had: dict, pulled: dict) -> dict:
    """The pulled edits laid over the file's. An edit made again at another point is an edit of other water: the
    water recorded for it (`area_m2`, `held`) is dropped, to be recorded afresh."""
    out = dict(had)
    for k, v in pulled.items():
        old = dict(had.get(k, {}))
        if v.get("point") and old.get("point") and v["point"] != old["point"]:
            old.pop("area_m2", None)
            old.pop("held", None)
        out[k] = {**old, **v}
    return out


def main(dirpath: str) -> None:
    d = Path(dirpath)
    ov, strokes, problems = convert(load(d, "water_edits"), load(d, "water_paint"))
    # the files are the record, the atlas's store only what was edited there since: an atlas published afresh
    # starts with an empty store, so what the files already hold is kept and the pulled edits are laid over it
    # (an edit is taken back by deleting its entry from the file)
    op, pp = SRC / "water_overrides.json", SRC / "water_paint.json"
    had = json.loads(op.read_text()) if op.exists() else {}
    ov = merge(had, ov)
    old = json.loads(pp.read_text()) if pp.exists() else []
    seen = {st.get("id") for st in strokes}
    strokes = [st for st in old if st.get("id") not in seen] + strokes
    if (f.OUT / "water_classified.png").exists():
        raster, rows = water_held.read(f.OUT)
        held = water_held.load(raster.shape)
        problems += [f"{k}: its point finds no water body" for k in water_held.record(ov, held, raster, rows)]
        water_held.save(ov, held)
    else:
        problems.append("no out/newworld/water_classified.png here: the new edits' water is not recorded; run "
                        "`python3 -m tools.newworld.water_held record` where the atlas's classification is")
        (SRC / "water_overrides.json").write_text(json.dumps(ov, indent=1, sort_keys=True) + "\n")
    (SRC / "water_paint.json").write_text(json.dumps(strokes, indent=1) + "\n")
    print(f"{len(ov)} body edits, {len(strokes)} painted strokes", *problems, sep="\n")


if __name__ == "__main__":
    main(sys.argv[1])
