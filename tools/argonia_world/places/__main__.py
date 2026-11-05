"""A place's clearance over its water, on the current game ground (place_build.GameGround: the LAND's numbers).

    python3 -m tools.argonia_world.places check claywater

Prints, for every built thing of the place's exterior cells (the marker refs the saves and journeys teleport to
first), its ground height, its seated z, its cell's water level and the clearance, and exits 0 only when the ground
under every dry-land thing stands at least DRY_M over its cell's water and every dock piece or person over the water
keeps its seat (DOCK_DECK_M; a boat 0). In the water by design: a creature's actor or marker (the crocodile wades), and
anything within a bowl's reach (the scour pool and the clay cut beside it). Lane 1.15-r6-claywater-water.

Two seat rules (lane 1.15-r6-claywater-pads-look): no prop stands inside a creature's pen (its den sandbox radius plus
PEN_BODY_M; round 6: a guar penned on the well walked through a post), and every placed thing with no height of its
own stands within SUPPORT_TOL_M of its ground, or keeps its seat on the water."""
from __future__ import annotations

import argparse
import math
import sys

from tools.argonia_world import db, place_build
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import patches

DRY_M = 0.5
SEAT_TOL_M = 0.02
SUPPORT_TOL_M = 0.1
PEN_BODY_M = 1.5  # a guar's half length: the body reaches past the sandbox point it walks to
# the refs the region save and the claywater journeys teleport to, the save's marker first
MARKERS = ("quest-board", "well", "livia", "keeper-work", "road-in", "takes", "signs", "crocodile", "gaius", "b1-door")


def _creature(w, r) -> bool:
    nid = getattr(r, "npc_id", None) or getattr(r, "owner_npc_id", None)
    return bool(nid) and w.get("npc", nid).kind == "creature"


def _is_prop(r) -> bool:
    """A placed thing with a body: a piece, or a base that is no actor, marker or person spot."""
    if getattr(r, "npc_id", None):
        return False
    base = getattr(r, "base", None) or ""
    return bool(getattr(r, "piece", None)) or (bool(base) and base != "000034:Skyrim.esm" and not base.startswith("ARG_Npc"))


def pens(w, refs) -> list[tuple[str, float, float, float]]:
    """(creature npc, x, y, reach) of every kept (neutral) creature: its owned den marker and its sandbox radius +
    body. A wild creature's den is no pen (the crocodile's pool holds LF83's clay basket by design)."""
    out = []
    for r in refs:
        nid = getattr(r, "owner_npc_id", None)
        n = w.get("npc", nid) if nid and not getattr(r, "npc_id", None) else None
        if n is not None and n.kind == "creature" and n.hostility == "neutral":
            p = w.get("build_person", nid)
            if p is not None:
                out.append((nid, r.x_m, r.y_m, p.sandbox_radius_m + PEN_BODY_M))
    return out


def in_pen(w, refs) -> dict[str, str]:
    """ref id -> the creature whose pen it stands in."""
    out = {}
    for nid, x, y, reach in pens(w, refs):
        for r in refs:
            if _is_prop(r) and math.hypot(r.x_m - x, r.y_m - y) <= reach:
                out[r.id] = nid
    return out


def rows(w, ground, place: str) -> list[dict]:
    cells = {c.id for c in w.rows("build_cell") if c.kind == "exterior" and place in c.place_id}
    bowls = w.query(f'SELECT * FROM "{patches.TABLE}" WHERE kind = ? AND place_id LIKE ?', "bowl", f"%{place}%")
    ctx = type("Ctx", (), {"ground": ground, "world": w})
    out = []
    mine = [r for r in w.rows("build_ref") if r.cell_id in cells]
    penned = in_pen(w, mine)
    for r in mine:
        g = ground.z(r.x_m, r.y_m)
        z = place_build._pos(ctx, "exterior", r)[2] / su.UNITS_PER_METRE
        lv = place_build.water_level(w, r.x_m, r.y_m)
        seat = place_build.water_seat(getattr(r, "piece", None))
        if seat is None and place_build._is_person_spot(w, r) and lv is not None and g < lv:
            seat = place_build.DOCK_DECK_M
        if lv is None:
            kind, ok = "dry cell", True
        elif any(math.hypot(r.x_m - b["x_m"], r.y_m - b["y_m"]) <= b["radius_m"] + patches.BOWL_REACH_M
                 for b in bowls) or _creature(w, r):
            kind, ok = "wet", True
        elif seat is not None:
            kind, ok = "dock", abs(z - max(g, lv) - seat) <= SEAT_TOL_M
        else:
            kind, ok = "dry", g - lv >= DRY_M  # it stands on this ground (a doorway's origin sits 1.2 m under its door)
        if kind in ("dry", "dry cell") and getattr(r, "z_m", None) is None and getattr(r, "z_over_m", None) is None and abs(z - g) > SUPPORT_TOL_M:
            kind, ok = "afloat", False
        if r.id in penned:
            kind, ok = "in a pen", False
        short = r.id.split(".")[-1]
        out.append({"id": r.id, "short": short, "ground": g, "z": z, "water": lv, "kind": kind, "ok": ok,
                    "marker": short in MARKERS})
    out.sort(key=lambda d: (not d["marker"], MARKERS.index(d["short"]) if d["marker"] else 0, d["id"]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m tools.argonia_world.places")
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("place", help="a place id or part of one (claywater)")
    a = ap.parse_args(argv)
    got = rows(db.open(), place_build.GameGround(), a.place)
    if not got:
        print(f"no exterior refs for {a.place}")
        return 2
    for d in got:
        c = "-" if d["water"] is None else f"{(d['z'] if d['kind'] == 'dock' else d['ground']) - d['water']:+.2f}"
        wl = "-" if d["water"] is None else f"{d['water']:.2f}"
        print(f"{'ok ' if d['ok'] else 'RED'} {'*' if d['marker'] else ' '} {d['short']:24} {d['kind']:8} "
              f"ground {d['ground']:7.2f} z {d['z']:7.2f} water {wl:>6} clear {c:>6}")
    bad = [d["short"] for d in got if not d["ok"]]
    print(f"{a.place}: {len(got)} refs, {len(bad)} red{': ' + ', '.join(bad) if bad else ''}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
