"""`draft primitives <place_id>`: the source's primitives (XPRM: the box, sphere or plane that gives a collision
marker, a trigger, a room marker or an acoustic space its shape) carried onto the place, by what each is.

A copied ref keeps its primitive, or is dropped with its reason in the ledger, by its class (`classify`):
  collision   a collision marker or plane (the CollisionMarker base): an invisible wall or floor the source's builders
              placed. Kept when it belongs to a piece we keep: its box touches or holds the record box of a kept
              building, static, furniture, door, activator or container (a wall on a balcony,
              a plug in a doorway, a cap on a roof); it then travels with that piece, at its source offset from it
              turned with the piece's cluster and seated `on` it, as a light travels with its fixture, and the
              navmesh is built round it as the solid it is. One that met only the source's ground (and its trees
              and rocks) is dropped: our ground is not the source's
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

import math
import re

import numpy as np

from tools.places.draft import geom, interiors, io, lights

COLLISION = {"Skyrim.esm:000021"}   # CollisionMarker
ROOM = re.compile(r"^(RoomMarker|PortalMarker|PlaneMarker|MultiBound)", re.I)
TRAP = re.compile(r"^Trap|TrapTrigger", re.I)
KEEPS = {"collision", "room", "acoustic", "trap", "volume"}
PIECE_KINDS = {"building", "static", "furniture", "door", "activator", "container"}  # what a collision box can belong to
GROUND_ONLY = ("a collision box on the source's own ground (it touches no piece the place keeps): "
               "our ground is not the source's, so it would hang in the air or lie buried where its builders never meant")


def _obb(pos, rot, lo, hi):
    from tools.places import build as B
    R = B.rotation(*(rot or [0.0, 0.0, 0.0]))
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return np.asarray(pos, float) + R @ ((lo + hi) / 2), R, (hi - lo) / 2


def boxes_meet(a, b) -> bool:
    """Whether two oriented boxes (centre, rotation, half extents) meet (the separating axis test)."""
    ca, Ra, ha = a
    cb, Rb, hb = b
    t = cb - ca
    axes = [Ra[:, i] for i in range(3)] + [Rb[:, i] for i in range(3)] + \
        [np.cross(Ra[:, i], Rb[:, j]) for i in range(3) for j in range(3)]
    for ax in axes:
        n = np.linalg.norm(ax)
        if n < 1e-6:
            continue
        ax = ax / n
        if abs(t @ ax) > sum(ha[i] * abs(Ra[:, i] @ ax) for i in range(3)) + sum(hb[i] * abs(Rb[:, i] @ ax) for i in range(3)):
            return False
    return True


def piece_of(r: dict, pieces: list[dict], bases: dict) -> dict | None:
    """The kept piece a collision box belongs to: of the source pieces whose record box it touches or holds, the
    nearest; None when it met only the ground."""
    b = np.asarray(r["primitive"]["bounds"], float)
    reach = float(np.linalg.norm(b))
    box = _obb(r["pos"], r.get("rot"), -b, b)
    best = None
    for p in pieces:
        bb = (bases.get(p["base"]) or {}).get("bounds")
        if not bb:
            continue
        s = float(p.get("scale") or 1.0)
        d = math.dist(p["pos"], r["pos"])
        if d > reach + math.dist(bb[0], bb[1]) * s or (best and d >= best[0]):
            continue
        if boxes_meet(box, _obb(p["pos"], p.get("rot"), [v * s for v in bb[0]], [v * s for v in bb[1]])):
            best = (d, p)
    return best[1] if best else None


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


def follow(row: dict, r: dict, prow: dict, piece: dict, st) -> None:
    """A kept collision box where its piece now stands: its source offset from the piece turned with the piece's
    cluster, its turn the same, seated `on` the piece at its source height over it."""
    turn = st.turn(prow.get("cluster"))
    ox, oy = lights.offset(r, piece, turn)
    sx, sy = lights.plan_shift(prow)
    row["pos"] = [round(prow["pos"][0] - sx + ox, 2), round(prow["pos"][1] - sy + oy, 2), row["pos"][2]]
    row["rot"] = geom.Xf((0, 0), (0, 0), turn).rot3(r.get("rot"))
    row["seat"] = lights.seat(r, prow)
    if prow.get("cluster"):
        row["cluster"] = prow["cluster"]
    st.offsets[row["id"]] = round(math.dist(r["pos"], piece["pos"]), 1)


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
    pieces = [r for r in st.src_ext if r.get("kind") in PIECE_KINDS and not r.get("primitive") and r["id"] in ours]
    st.offsets = {}
    for r in src_ext:
        cls, why = classify(r, st.bases.get(r["base"]) or {}, fol)
        row, lr = ours.get(r["id"]), led.get(r["id"])
        piece = piece_of(r, pieces, st.bases) if cls == "collision" else None
        if cls == "collision" and piece is None:
            why = GROUND_ONLY
        if why is None:
            if row is not None:
                if row.get("primitive") != shape(r["primitive"]):
                    row["primitive"] = shape(r["primitive"])
                if piece is not None:
                    follow(row, r, ours[piece["id"]], piece, st)
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
    from tools.places.seat import seat_all
    seat_all(st.ext, st.G)
    if st.offsets:
        log(f"draft primitives {st.place_id}: the farthest kept collision box stands {max(st.offsets.values())} units from its piece")
    log(f"draft primitives {st.place_id}: " + ", ".join(f"{k} {v['written']} written, {v['dropped']} dropped" for k, v in sorted(counts.items())))
    return counts
