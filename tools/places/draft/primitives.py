"""`draft primitives <place_id>`: the source's primitives (XPRM: the box, sphere or plane that gives a collision
marker, a trigger, a room marker or an acoustic space its shape) carried onto the place, by what each is.

A copied ref keeps its primitive, or is dropped with its reason in the ledger, by its class (`classify`):
  collision   a collision marker or plane (the CollisionMarker base): an invisible wall or floor the source's builders
              placed; written with its box, and the navmesh is built round it as the solid it is
  room        a room, portal or plane marker, a multibound: how the engine culls what is drawn; written
  acoustic    an acoustic space: the room's echo; written
  trap        a trap's trigger (a base of the trap kit): stays with its trap
  trigger     an activator with a script: stays when something the place keeps follows it (a ref whose activate
              parent it is, a linked ref, an enable child); else dropped, the source's quest or scene, not ours
  volume      anything else with a primitive (a light or sound volume): written
Outside, each row whose source ref has a primitive carries it (`primitive`: {type, bounds (half extents), color,
unknown}); in a copied room the build copies the source ref's own, and a dropped one is a `removed` row.
"""
from __future__ import annotations

import re

from tools.places.draft import interiors, io

COLLISION = {"Skyrim.esm:000021"}   # CollisionMarker
ROOM = re.compile(r"^(RoomMarker|PortalMarker|PlaneMarker|MultiBound)", re.I)
TRAP = re.compile(r"^Trap|TrapTrigger", re.I)
KEEPS = {"collision", "room", "acoustic", "trap", "volume"}


def classify(r: dict, base: dict, followers: set[str]) -> tuple[str, str | None]:
    """(class, why it is dropped or None) of a source ref with a primitive. `followers`: the refs of the place's
    space that follow another's activation (their activate parents), link to it or are enabled by it."""
    edid, typ = str(base.get("edid") or ""), str(base.get("type") or "")
    if r.get("base") in COLLISION or edid == "CollisionMarker":
        return "collision", None
    if ROOM.search(edid):
        return "room", None
    if typ in ("AcousticSpace", "ASPC"):
        return "acoustic", None
    if TRAP.search(edid):
        return "trap", None
    scripts = list(r.get("scripts") or []) + list(base.get("scripts") or [])
    if typ in ("Activator", "ACTI") and (scripts or "TRIG" in edid.upper()):
        if r["id"] in followers or r.get("linked"):
            return "trigger", None
        return "trigger", (f"a trigger ({edid}, script {', '.join(scripts) or 'none'}) whose activation reaches nothing "
                           f"the place keeps (no ref follows it, it links to none): the source's quest or scene, not ours")
    return "volume", None


def followed(refs: list[dict]) -> set[str]:
    """The refs another ref of the space follows: activate parents, linked refs, enable parents."""
    out: set[str] = set()
    for r in refs:
        out |= set(r.get("activate_parents") or [])
        out |= {ln.get("ref") for ln in r.get("linked") or [] if ln.get("ref")}
        ep = r.get("enable_parent")
        out |= {ep.get("ref") if isinstance(ep, dict) else ep} - {None}
    return out


def shape(p: dict) -> dict:
    return {k: p[k] for k in ("type", "bounds", "color", "unknown") if k in p}


def apply(st, log=print) -> dict:
    """The stage. Returns {class: {"written": n, "dropped": n}}."""
    counts: dict[str, dict[str, int]] = {}

    def tally(cls, kept):
        c = counts.setdefault(cls, {"written": 0, "dropped": 0})
        c["written" if kept else "dropped"] += 1

    src_ext = [r for r in st.src_ext if r.get("primitive")]
    if src_ext and not all("type" in r["primitive"] for r in src_ext):
        raise ValueError(f"the source bundle src.{st.place['source_id']} writes primitives without their type: extract it again")
    fol = followed(st.src_ext)
    ours, led = st.ours(), st.led()
    for r in src_ext:
        cls, why = classify(r, st.bases.get(r["base"]) or {}, fol)
        row, lr = ours.get(r["id"]), led.get(r["id"])
        if why is None:
            if row is not None and row.get("primitive") != shape(r["primitive"]):
                row["primitive"] = shape(r["primitive"])
            tally(cls, row is not None)
            continue
        tally(cls, False)
        if row is not None:
            st.ext.remove(row)
        if lr is not None:
            lr.update({"status": "dropped", "why": why})
            lr.pop("as", None)
        log(f"draft primitives {st.place_id}: {r['id']} dropped: {why}")
    for sid, sp in sorted(st.files["spaces"].items()):
        info = sp.get("space") or {}
        if sid == "exterior" or not info.get("copy_of"):
            continue
        t = info["copy_of"].split("/", 1)[1]
        src_sp = st.src.spaces.get(t)
        if src_sp is None:
            continue
        keep = interiors.kept(info["copy_of"], info.get("room"))
        refs = [r for r in src_sp.refs if keep is None or r["id"] in keep]
        fol = followed(refs)
        rows = {o.get("src"): o for o in sp["refs"] if o.get("src")}
        for r in refs:
            if not r.get("primitive"):
                continue
            cls, why = classify(r, st.bases.get(r["base"]) or {}, fol)
            tally(cls, why is None)
            if why is None:
                continue
            row = rows.get(r["id"])
            if row is None:
                sp["refs"].append({"id": io.mint(st.place_id, sid, r["id"]), "src": r["id"], "removed": True})
            elif not row.get("removed"):
                row.clear()
                row.update({"id": io.mint(st.place_id, sid, r["id"]), "src": r["id"], "removed": True})
            st.ledger[:] = [x for x in st.ledger if not (x.get("src") == r["id"] and x.get("copy") == sid)]
            st.ledger.append({"src": r["id"], "space": t, "copy": sid, "status": "dropped", "why": why})
            log(f"draft primitives {st.place_id}: {sid}/{r['id']} dropped: {why}")
    log(f"draft primitives {st.place_id}: " + ", ".join(f"{k} {v['written']} written, {v['dropped']} dropped" for k, v in sorted(counts.items())))
    return counts
