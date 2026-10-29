"""The hydrology family's one-off migration (decision 0030 §6, 2.W2): the old `hydrology-graph.json` -> the world's
hydrology tables, written through db.py. After it, every water tool reads the graph from the database only.

The graph file is named on the command line (this module names no `world/` path; the gate's world-reads check):

    python3 -m tools.argonia_world.water.migrate ddl     --graph <hydrology-graph.json>   # the schema block
    python3 -m tools.argonia_world.water.migrate migrate --graph <hydrology-graph.json>   # rows, through db.py

Lossless by construction: every scalar of every entity goes to a column (nested objects flattened, `a.bC` ->
`a_b_c`), every list to a child table keyed by its parent and `ord`; a field the mapping does not know is an error,
never dropped. The graph's `stats` are derived (the old derive's report) and are not carried; `thresholds`,
`grid`, `vocabulary` and the two hashes go to `hydrology_setting` (name -> JSON value as text).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# entity list -> (table, {source field: column} renames, {column: (parent table)} foreign keys)
ENTITIES = {
    "rivers": ("hydrology_river", {"tributaryOf.river": "tributary_of_river_id",
                                   "tributaryOf.junction": "tributary_of_junction_id",
                                   "mouth.bodyId": "mouth_body_id", "mouth.river": "mouth_river_id",
                                   "mouth.junction": "mouth_junction_id", "mouth.through": "mouth_through_body_id"},
               {"tributary_of_river_id": "hydrology_river", "tributary_of_junction_id": "hydrology_junction",
                "mouth_body_id": "hydrology_body", "mouth_river_id": "hydrology_river",
                "mouth_junction_id": "hydrology_junction", "mouth_through_body_id": "hydrology_body"}),
    "reaches": ("hydrology_reach", {"river": "river_id", "downstream": "downstream_reach_id",
                                    "fromJunction": "from_junction_id", "toJunction": "to_junction_id",
                                    "bodyId": "body_id", "fall.plungeBodyId": "fall_plunge_body_id",
                                    "terrainPrecondition.bodyId": "terrain_precondition_body_id"},
                {"river_id": "hydrology_river", "downstream_reach_id": "hydrology_reach",
                 "from_junction_id": "hydrology_junction", "to_junction_id": "hydrology_junction",
                 "body_id": "hydrology_body", "fall_plunge_body_id": "hydrology_body",
                 "terrain_precondition_body_id": "hydrology_body"}),
    "junctions": ("hydrology_junction", {"outflow": "outflow_reach_id"}, {"outflow_reach_id": "hydrology_reach"}),
    "bodies": ("hydrology_body", {"outflow": "outflow_reach_id", "causedBy.fall": "caused_by_fall_reach_id"},
               {"outflow_reach_id": "hydrology_reach", "caused_by_fall_reach_id": "hydrology_reach"}),
}
# list fields -> child table (parent key column, value column(s), value FK)
LISTS = {
    ("rivers", "reaches"): ("hydrology_river_reach", ["reach_id"], "hydrology_reach"),
    ("reaches", "upstream"): ("hydrology_reach_upstream", ["upstream_reach_id"], "hydrology_reach"),
    ("reaches", "centreline"): ("hydrology_reach_point", ["east_m", "south_m"], None),
    ("junctions", "inflow"): ("hydrology_junction_inflow", ["reach_id"], "hydrology_reach"),
    ("bodies", "inflow"): ("hydrology_body_inflow", ["reach_id"], "hydrology_reach"),
    ("bodies", "approved.merged"): ("hydrology_body_approved_merged", ["merged_body_id"], None),
    ("bodies", "terrainPrecondition.radiiM"): ("hydrology_body_radius", ["radius_m"], None),
}
# pairs stored as two columns on the row
PAIRS = {"deepestCell": ("deepest_x", "deepest_y"), "bboxCells": ("bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1")}
PARENT_COL = {"rivers": "river_id", "reaches": "reach_id", "junctions": "junction_id", "bodies": "body_id"}
HOME = {
    "hydrology_river": "a river: one stem from headwater to mouth (old 0058; the graph's README)",
    "hydrology_reach": "a reach: a stretch of one river with one kind and one surface; levels in metres above sea",
    "hydrology_junction": "a junction: a source, confluence or mouth of the river network",
    "hydrology_body": "a standing water body of the graph (ocean, lagoon, lake, tarn, pond, pool, plunge pool, "
                      "marsh family); levelM is the high-water line (old 0063); its extent is the connected "
                      "water of the frozen body-level raster around deepest_x/y (full-res samples, y south)",
    "hydrology_river_reach": "a river's reaches, headwater (ord 0) to mouth",
    "hydrology_reach_upstream": "a reach's upstream reaches",
    "hydrology_reach_point": "a reach's centreline, [east, south] metres from the province's north-west corner "
                             "every ~5.5 m, headwater first",
    "hydrology_junction_inflow": "a junction's inflowing reaches",
    "hydrology_body_inflow": "a body's inflowing reaches",
    "hydrology_body_approved_merged": "the approved (16a) bodies merged into a body's approved match",
    "hydrology_body_radius": "an authored bowl's radii (the Blackrose lake)",
    "hydrology_setting": "one setting of the hydrology graph (thresholds, grid, vocabulary, source hashes), "
                         "its value as JSON text",
}


def snake(path: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", path.replace(".", "_")).lower()


# a field that is an object in some rows and null in others: the null is the absence of the object's columns
OBJECTS = {"tributaryOf", "approved", "mouth", "fall", "terrainPrecondition", "causedBy", "preCarve",
           "terrainPrecondition.island"}


def flat(d: dict, p: str = ""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from flat(v, p + k + ".")
        elif p + k == "approved" and v is None:
            yield "approvedUnreviewed", True  # `approved: null`: a body the ground grew that the owner has not reviewed
        elif not (v is None and p + k in OBJECTS):
            yield p + k, v


def column(ent: str, path: str) -> str:
    return ENTITIES[ent][1].get(path) or snake(path)


def sqltype(vals) -> str:
    ts = {type(v) for v in vals if v is not None}
    if not ts:
        return "TEXT"  # null in every row (a river's name until lore names it)
    if ts <= {bool}:
        return "BOOLEAN"
    if ts <= {int}:
        return "INTEGER"
    if ts <= {int, float}:
        return "REAL"
    if ts <= {str}:
        return "TEXT"
    raise ValueError(f"mixed types {ts}")


def survey(g: dict) -> dict[str, dict[str, str]]:
    """Every table's columns and types as the graph has them (dict: table -> column -> type)."""
    out: dict[str, dict[str, str]] = {}
    for ent, (table, _, _) in ENTITIES.items():
        vals: dict[str, list] = {}
        for e in g[ent]:
            for path, v in flat(e):
                if (ent, path) in LISTS:
                    continue
                if path in PAIRS:
                    for c in PAIRS[path]:
                        vals.setdefault(c, [])
                    if v is not None:
                        for c, x in zip(PAIRS[path], v):
                            vals[c].append(x)
                    continue
                if isinstance(v, list):
                    raise ValueError(f"{ent}.{path}: a list with no child table")
                vals.setdefault(column(ent, path), []).append(v)
        out[table] = {"id": "TEXT", **{c: sqltype(v) for c, v in vals.items() if c != "id"}}
    return out


def ddl(g: dict) -> str:
    cols = survey(g)
    lines = ["-- == The hydrology family (2.W2; migrated from the old hydrology graph, decision 0030 §6) ==",
             "-- Read through db.py by tools/argonia_world/water; the migration is tools/argonia_world/water/migrate.py.",
             "-- Frame: east/south metres from the province's north-west corner; x = column (east), y = row (south)",
             "-- of the 4033^2 full-res samples; levels in metres above sea.", ""]
    order = ["hydrology_river", "hydrology_junction", "hydrology_reach", "hydrology_body"]
    for table in order:
        ent = next(e for e, t in ENTITIES.items() if t[0] == table)
        fks = ENTITIES[ent][2]
        if table != "hydrology_body":  # the body's placeholder above the 0030 marker is expanded in place
            lines += table_ddl(table, cols[table], fks)
    for (ent, _), (table, vcols, vfk) in LISTS.items():
        pcol = PARENT_COL[ent]
        body = [f'  "{pcol}" TEXT NOT NULL REFERENCES "{ENTITIES[ent][0]}"("id"),', '  "ord" INTEGER NOT NULL,']
        for c in vcols:
            t = "REAL" if c.endswith("_m") else "TEXT"
            ref = f' REFERENCES "{vfk}"("id")' if vfk else ""
            body.append(f'  "{c}" {t} NOT NULL{ref},')
        body.append(f'  PRIMARY KEY ("{pcol}", "ord")')
        lines += [f"-- Home of {HOME[table]}.", f'CREATE TABLE "{table}" (', *body, ");", ""]
    lines += [f"-- Home of {HOME['hydrology_setting']}.", 'CREATE TABLE "hydrology_setting" (',
              '  "id" TEXT NOT NULL PRIMARY KEY,', '  "value" TEXT NOT NULL', ");", ""]
    return "\n".join(lines)


def table_ddl(table: str, cols: dict[str, str], fks: dict[str, str]) -> list[str]:
    body = ['  "id" TEXT NOT NULL PRIMARY KEY']
    for c, t in cols.items():
        if c == "id":
            continue
        ref = f' REFERENCES "{fks[c]}"("id")' if c in fks else ""
        body.append(f'  "{c}" {t}{ref}')
    return [f"-- Home of {HOME[table]}.", f'CREATE TABLE "{table}" (', ",\n".join(body), ");", ""]


def rows(g: dict):
    """(table, row dict) for every row of the family."""
    for ent, (table, _, _) in ENTITIES.items():
        for e in g[ent]:
            row = {}
            for path, v in flat(e):
                if (ent, path) in LISTS:
                    ctable, vcols, _ = LISTS[(ent, path)]
                    for i, x in enumerate(v or []):
                        xs = x if isinstance(x, list) else [x]
                        yield ctable, {PARENT_COL[ent]: e["id"], "ord": i, **dict(zip(vcols, xs))}
                elif path in PAIRS:
                    if v is not None:
                        row.update(zip(PAIRS[path], v))
                else:
                    row[column(ent, path)] = v
            yield table, {k: v for k, v in row.items() if v is not None}
    for k in ("thresholds", "grid", "vocabulary", "sourceHeightSha256", "contentSha256", "schemaVersion"):
        yield "hydrology_setting", {"id": snake(k), "value": json.dumps(g[k], sort_keys=True)}


TABLES = [t for t, _, _ in ENTITIES.values()] + [t for t, _, _ in LISTS.values()] + ["hydrology_setting"]


def migrate(g: dict, world) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in TABLES:
        world._begin()
        world.con.execute(f'DELETE FROM "{t}"')
        world.dirty.add(t)
    # ids an entity names that the graph does not hold (the approved record's merged ids) are kept as text
    for table, row in rows(g):
        world.insert(table, row)
        counts[table] = counts.get(table, 0) + 1
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="water.migrate", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["ddl", "migrate"])
    ap.add_argument("--graph", required=True)
    a = ap.parse_args(argv)
    g = json.loads(Path(a.graph).read_text(encoding="utf-8"))
    if a.cmd == "ddl":
        ent = "bodies"
        print("\n".join(table_ddl("hydrology_body", survey(g)["hydrology_body"], ENTITIES[ent][2])))
        print(ddl(g))
        return 0
    from tools.argonia_world import db
    w = db.load()
    counts = migrate(g, w)
    w.save()
    for t, n in sorted(counts.items()):
        print(f"{n:7d}  {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
