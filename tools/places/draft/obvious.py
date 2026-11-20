"""No obviously wrong thing stands in a draft (owner, 2026-11-19, #80): a piece whose model did not resolve or a bare
collision box standing where a building should be seen; a piece floating with nothing under it that carries it; a
bridge or walkway without support at both ends. `draft check` calls `faults`.

The rules for floating, unsupported ends and unresolved models are the look tool's own (tools/places/look/geom.py
`faults`), so `draft check` and `look probe --all` can never disagree: this module only turns the draft's rows into
the look tool's pieces and its faults into check lines. The one rule of its own is the bare collision box (the look
tool draws no markers). A disabled piece (parked under the world by its source) is never seen, so never judged.
"""
from __future__ import annotations

from tools.places import xform
from tools.places.look import geom as look
from tools.places.seat import model_bounds

COLLISION_BASES = {"Skyrim.esm:000021"}   # CollisionMarker: a box with no visible model
UNRESOLVED = "has no model that resolves: a stand-in where a thing should be seen"
BOX = "is a bare collision box standing on its own: a stand-in where a building should be seen"
FLOATS = "floats over what is under it"
BRIDGE = "is a bridge or walkway without support at"
STAND_IN = [[-32, -32, 0], [32, 32, 64]]


def _seen(r: dict) -> bool:
    return "initially_disabled" not in (r.get("flags") or []) and not r.get("removed")


def piece(r: dict, bases: dict) -> dict:
    """A draft row as the look tool's piece (a model resolves when its base names one with bounds)."""
    base = bases.get(r.get("base"))
    m = xform.matrix(r["pos"], r.get("rot") or [0, 0, 0], float(r.get("scale") or 1.0))
    if base is None:
        return {"id": r["id"], "base": r.get("base"), "kind": r.get("kind"), "edid": None, "model": None,
                "missing": True, "resolved": False, "m": m, "lo": STAND_IN[0], "hi": STAND_IN[1], "door": r.get("door")}
    b = model_bounds(base) if base.get("model") else None
    return {"id": r["id"], "base": r.get("base"), "kind": r.get("kind") or base.get("kind"), "edid": base.get("edid"),
            "model": base.get("model"), "resolved": bool(b), "m": m, "lo": list((b or STAND_IN)[0]),
            "hi": list((b or STAND_IN)[1]), "door": r.get("door")}


def faults(refs: list[dict], bases: dict, G, world_refs: list[dict] = ()) -> list[str]:
    """Every obviously wrong piece of the exterior rows `refs` over the ground `G`, one line each. `world_refs`: the
    world's own rows about the place (its trees, rocks), which hold up what hangs on or rests on them, as in probe."""
    bad: list[str] = []
    by_id = {r["id"]: r for r in refs}
    pieces = []
    for r in refs:
        if not _seen(r):
            continue
        base = bases.get(r.get("base"))
        if r.get("base") in COLLISION_BASES or (r.get("primitive") and not (base or {}).get("model")):
            on = (r.get("seat") or {}).get("on")
            if (r.get("seat") or {}).get("mode") != "on" or on not in by_id:
                bad.append(f"{r['id']} ({r.get('base')}) {BOX}")
            continue
        pieces.append(piece(r, bases))
    ends: dict[str, int] = {}
    world = [dict(p, world=True) for p in (piece(r, bases) for r in look.world_rows(world_refs, bases))
             if p.get("resolved")]
    for f in look.faults(pieces, G, world):
        i, name = f["id"], f.get("edid") or by_id[f["id"]].get("base")
        if f["fault"] in ("missing base", "unresolved"):
            bad.append(f"{i} ({name}, {by_id[i].get('kind')}) {UNRESOLVED}")
        elif f["fault"] == "floats":
            bad.append(f"{i} ({name}) {FLOATS}: lowest point {f['over']:.0f} over the ground ({f['why']})")
        elif f["fault"] == "unsupported end":
            ends[i] = ends.get(i, 0) + 1
        else:
            bad.append(f"{i} ({name}): {f['fault']}: {f['why']}")
    for i, n in ends.items():
        bad.append(f"{i} ({by_id[i].get('base')}) {BRIDGE} {'both ends' if n >= 2 else 'one end'}")
    return bad
