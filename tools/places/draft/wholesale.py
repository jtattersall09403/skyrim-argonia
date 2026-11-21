"""A place laid wholesale from its source (the by-hand experiment): every source exterior piece inside the place's
footprint at the fit's one main transform and its source height plus one common offset, and the source's whole relief
inside the footprint carried as land rows at the same offset (no cap; the band's slope held to SLOPE_DEG; our water
line kept by the ground stage's own rule). No fit per cluster, no seating, no drop rule but these three: an actor
(people come from the place's people rows), the source's water plane (our world's water stands where it stands) and
a levelled base (decision 0035). The place's people, quest spots, interiors and stock rows are left as they are; the
draft's added pieces, streets, land patches and agent edits are cleared, since the experiment starts from the source.

    python -m tools.places.draft.wholesale <place_id> --offset <units> [--dry]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil

from tools.places.draft import ground, io
from tools.places.draft.stages import Standing
from tools.places.seat import Ground

SLOPE_DEG = 35.0
LEVELLED = {"LVLN", "LVLI", "LVLC"}


def lay(st: Standing, offset: float) -> tuple[list[dict], list[dict], list[dict], dict]:
    from tools.places.extract import load_place
    fit = st.place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s = math.cos(rot), math.sin(rot)
    rec = load_place(st.place_id)
    centre = (float(rec["world_x"]), float(rec["world_y"]))
    radius = float(st.place["radius_m"]) * ground.UNITS_PER_M

    def pt(x, y):
        dx, dy = x - pv[0], y - pv[1]
        return an[0] + dx * c - dy * s, an[1] + dx * s + dy * c
    ext, ledger, our_id = [], [], {}
    _, of, _ = st.clusters        # the source's own groups, as names for the look tool only; nothing is moved by them
    for r in st.src_ext:
        rid = r["id"]
        x, y = pt(r["pos"][0], r["pos"][1])
        b = st.bases.get(r["base"]) or {}
        why = None
        if math.dist((x, y), centre) > radius:
            why = "outside the place's footprint"
        elif r.get("kind") == "actor":
            why = "a person: the place's people come from its people rows"
        elif r.get("kind") == "water":
            why = "the source's water plane; our world's water stands where it stands"
        elif (b.get("type") or b.get("sig")) in LEVELLED:
            why = "levelled (decision 0035)"
        if why:
            ledger.append({"src": rid, "space": "exterior", "status": "dropped", "why": why})
            continue
        rz = list(r.get("rot") or [0, 0, 0])
        rz[2] = round(float(rz[2]) + rot, 5)
        row = {"id": io.mint(st.place_id, "exterior", rid), "base": r["base"], "kind": r.get("kind"),
               "pos": [round(x, 2), round(y, 2), round(float(r["pos"][2]) + offset, 2)], "rot": rz,
               "scale": r.get("scale", 1.0), "layer": "place", "flags": r.get("flags") or [], "src": rid,
               "seat": {"mode": "free", "dz": 0.0}}
        if of.get(rid):
            row["cluster"] = of[rid]
        for k in ("owner", "lock", "door", "linked", "enable_parent", "primitive", "map_marker", "edid", "radius", "count"):
            if r.get(k) is not None:
                row[k] = r[k]
        our_id[rid] = row["id"]
        ext.append(row)
        ledger.append({"src": rid, "space": "exterior", "status": "placed", "as": row["id"]})
    for row in ext:
        ep = row.get("enable_parent")
        if ep:
            if ep["ref"] in our_id:
                row["enable_parent"] = {**ep, "ref": our_id[ep["ref"]]}
            else:
                row.pop("enable_parent")
        if row.get("linked"):
            row["linked"] = [{**lk, "ref": our_id[lk["ref"]]} for lk in row["linked"] if lk.get("ref") in our_id]
            if not row["linked"]:
                row.pop("linked")
    G0 = Ground.load(st.grd.path)
    pieces = [(r["pos"][0], r["pos"][1]) for r in ext]
    land, rep = ground.carry(G0, st.S, pv, an, float(fit.get("rot_deg", 0.0)), pieces, centre, radius,
                             cap=1e9, offset=offset, slope=SLOPE_DEG)
    for r in land:
        r["why"] = f"the source's whole relief carried wholesale at offset {offset:g}"
    rep.update(pieces=len(ext), dropped=sum(1 for lr in ledger if lr["status"] == "dropped"))
    return ext, ledger, land, rep


def carry_rooms(st: Standing, offset: float, drop_removals: set[str] = frozenset()) -> list[str]:
    """The source's rooms carried with their doors working: each way out of a room copied from this source leads to our
    copy of the source's own exterior door and lands where the source landed one, at the one transform (the room's door
    rows written afresh from the source's); `drop_removals`: rooms whose earlier `removed` rows are let go, so the room
    stands whole as the source built it. Rooms copied from another source are left as they are."""
    fit = st.place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s_ = math.cos(rot), math.sin(rot)
    said = []
    for sp, space in st.files["spaces"].items():
        meta = space.get("space") or {}
        if sp == "exterior" or not str(meta.get("copy_of", "")).startswith(st.place["source_id"] + "/"):
            continue
        src_sp = st.src.spaces.get(sp)
        if not src_sp:
            continue
        rows = [r for r in space["refs"] if not (r.get("door") and (r["door"].get("to_space") == "exterior"))
                and not (sp in drop_removals and r.get("removed"))]
        first = None
        for q in src_sp.refs:
            d = q.get("door") or {}
            if not d.get("to_ref") or d["to_ref"] not in st.by_src:     # a way out to the source's exterior only
                continue
            x, y, z = d["to_pos"]
            dx, dy = x - pv[0], y - pv[1]
            to_rot = list(d.get("to_rot") or [0, 0, 0])
            to_rot[2] = round(float(to_rot[2]) + rot, 6)
            row = {k: q[k] for k in ("edid", "base", "kind", "pos", "rot", "scale", "layer", "flags") if k in q}
            row = {"id": io.mint(st.place_id, sp, q["id"]), **row, "src": q["id"],
                   "door": {**d, "to_space": "exterior", "to_ref": io.mint(st.place_id, "exterior", d["to_ref"]),
                            "to_pos": [round(an[0] + dx * c - dy * s_, 2), round(an[1] + dx * s_ + dy * c, 2),
                                       round(float(z) + offset, 2)], "to_rot": to_rot},
                   "seat": {"mode": "free"}}
            rows.append(row)
            first = first or io.mint(st.place_id, "exterior", d["to_ref"])
        space["refs"][:] = rows
        if first:
            meta["door_from"] = first
        said.append(sp)
    return said


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("place_id")
    ap.add_argument("--offset", type=float, required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--rooms", action="store_true", help="carry only the rooms' doors (the town as it stands)")
    ap.add_argument("--whole", default="", help="rooms (comma-separated) whose removals are let go")
    a = ap.parse_args(argv)
    st = Standing(a.place_id)
    if a.rooms:
        from tools.places import edits
        said = carry_rooms(st, a.offset, set(filter(None, a.whole.split(","))))
        if not a.dry:
            edits.write_place(st.pdir, st.files)
        print("rooms carried:", ", ".join(said))
        return 0
    ext, ledger, land, rep = lay(st, a.offset)
    print(json.dumps({k: v for k, v in rep.items() if k != "hull"}))
    if a.dry:
        return 0
    pdir = st.pdir
    old = io.read_jsonl(pdir / "ledger.jsonl")
    keep = [lr for lr in old if lr.get("space") != "exterior"]
    io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", ext)
    io.write_jsonl(pdir / "ledger.jsonl", keep + ledger)
    io.write_jsonl(pdir / "land.jsonl", land)
    io.write_jsonl(pdir / "paths.jsonl", [])
    place = json.loads((pdir / "place.json").read_text())
    place["wholesale"] = {k: rep.get(k) for k in ("offset", "band", "pieces", "dropped", "raised_max", "lowered_max",
                                                  "band_steepest_deg", "source_water_area_m2", "held_by_water")}
    place["agent_saves_applied"] = []
    place.pop("steps", None)
    (pdir / "place.json").write_text(json.dumps(place, indent=1, ensure_ascii=False) + "\n")
    shutil.rmtree(pdir / "agent-edits", ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
