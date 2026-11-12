"""Edits of single placed things, applied over the placement: a tree removed, a rock moved, a base swapped, a
thing added. Nothing else is placed again, and the rules never see an edit (a moved rock shifts no neighbour).

    python3 -m tools.newworld.place refs --cell CX CY | --fid HEX | --at X Y        the placed things there, as JSON lines
    python3 -m tools.newworld.place edit remove|move|swap|add|restore  --by WHO
            (--id IDENTITY | --fid HEX | --at X Y)  [--pos X Y [Z]] [--rot RX RY RZ] [--scale S] [--base KEY]
            [--why TEXT] [--confirm]                                                  validates and appends one row
    python3 -m tools.newworld.place edits apply|check|plan                            the rebuild's `edits` stage

The source is newworld/sources/placed_edits.jsonl (committed): one row an edit, appended, never rewritten.
    {"n": its number, "op": remove | move | swap | add | restore, "id": the thing's identity (place.py),
     "base": its base and "pos": its position when the edit was made, "origin": where the rules put it (x, y),
     "to": what the edit sets (move: pos, rot, scale; swap: base; add: base, pos, rot, scale), "fid": an added
     thing's form id (ADD_FIRST.., given once and never again), "by": who, "tier": the statement tier
     (OWNER_STATED for the owner's own edit: no later row of a lower tier is applied to that thing),
     "at": when, "why": words, "confirmed": the placement rules the owner chose to break}
`restore` takes a thing back to where the rules put it (an added thing: away).
`seat` is a rule over one base, not a thing: {"n", "op": "seat", "base": plugin:edid, "to": {"embed_m": m}, "by", "at",
"tier", "why"}; every thing of that base the rules placed (and no single-thing row names) is lowered until its mesh's
lowest vertex sits embed_m into the ground (tools/newworld/place/seat.py), its identity, form id, x, y, rotation and
scale kept; a thing already touching the ground is left as it is. `drop` (same shape, no `to`) takes away every thing
of one base the rules placed (a base that cannot stand alone, such as moss with nothing to hang from).

`apply` reads the placement (out/newworld/plugin/placed/flora, place.PLACED) and writes the placed-refs hook
(out/newworld/plugin/refs/flora, place.REFS): every shard the same bytes as the placement's but the rows of the
cells an edit names; a shard, the base list and the manifest are written only when their bytes change, so a second
run writes nothing. A row whose thing the rules no longer place is re-anchored to the thing of the same base
standing within REANCHOR units of where the rules had put it, when exactly one is nearest; otherwise the row is
kept, not applied and reported (`orphaned`) at every run until a `restore` row answers it. `edits.json` beside the
shards is the record: each row's fate and each edited thing before and after.

`check` judges the edited things alone by the placement's own rules (judge): a rule an owner's edit breaks is the
owner's choice (`confirmed` in the row, else printed TO CONFIRM; never red); a rule another tier's edit breaks is red.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

from tools.newworld import idspace
from tools.newworld.place import place as P
from tools.newworld.place.seat import Seater

EDITS = P.REPO / "newworld/sources/placed_edits.jsonl"
PLACES = P.REPO / "newworld/places"
KEY = P.REPO / "newworld/sources/key.json"
OWNER, OWNER_TIER, AGENT_TIER = "owner", "OWNER_STATED", "AGENT_INVENTED"
OPS = ("remove", "move", "swap", "add", "restore", "seat", "drop")
BASE_OPS = ("seat", "drop")  # rules over every thing of one base
REANCHOR = 70.0  # units (1 m): no two placed things stand closer, so the nearest of one base within it is the same thing
ADD_FIRST, ADD_LAST = idspace.SPAN["added"]  # form ids of added things (NewWorld.cs); the rules' own are P.FID_FIRST..
IDENT = re.compile(r"flora/(-?\d+),(-?\d+)/([0-9a-f]{10}|add\d{6})")
HOVER_M = 0.5
SEAT_EMBED_M = 0.1  # a seated thing's lowest vertex this far into the ground
RULES = {"road": "it stands on a road's surface",
         "road-walk": "its collision reaches into a road's walking width",
         "flowing-water": "a tree in flowing water",
         "standing-water": "a tree in standing water against its habitat's rule",
         "spacing": "closer than 1 m to another placed thing",
         "pad": "on a place's pad",
         "budget": f"its cell holds more than {P.CAP} natural things",
         "hover": "it stands clear above the ground",
         "underside": "part of its open underside shows above the ground"}


class EditError(ValueError):
    """A row or a request that cannot be an edit."""


def cell_of(x: float, y: float) -> tuple[int, int]:
    return int(math.floor(x / P.CELL)), int(math.floor(y / P.CELL))


def id_cell(ident: str) -> tuple[int, int]:
    m = IDENT.fullmatch(ident or "")
    if not m:
        raise EditError(f"{ident!r} is no identity (flora/<cx>,<cy>/<ten hex digits>)")
    return int(m.group(1)), int(m.group(2))


def is_added(ident: str) -> bool:
    return ident.rsplit("/", 1)[-1].startswith("add")


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.jsonl"


def tiers() -> list[str]:
    return [t["id"] for t in json.loads(KEY.read_text(encoding="utf-8"))["statement_tier"]]


# ---- the source file --------------------------------------------------------------------------------------------

def _vec(v, n) -> bool:
    return isinstance(v, list) and len(v) == n and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)


def validate(r: dict) -> None:
    """A row's shape; EditError names what is wrong."""
    def bad(why):
        raise EditError(f"row {r.get('n')}: {why}")
    if not isinstance(r.get("n"), int) or r.get("op") not in OPS:
        bad(f"op {r.get('op')!r} is none of {', '.join(OPS)}, or n is no number")
    if r["op"] in BASE_OPS:               # a rule over every thing of one base: no identity of its own
        if not isinstance(r.get("base"), str) or not isinstance((r.get("to") or {}).get("embed_m", 0.0), (int, float)):
            bad(f"{r['op']} needs base (plugin:edid); seat may give to.embed_m")
        if not r.get("by") or not r.get("at") or not r.get("tier"):
            bad("by, at and tier are all needed")
        return
    id_cell(r.get("id"))
    if not r.get("by") or not r.get("at") or not r.get("tier"):
        bad("by, at and tier are all needed")
    if (r["tier"] == OWNER_TIER) != (r["by"] == OWNER):
        bad(f"tier {OWNER_TIER} is the owner's alone, and the owner's rows carry it")
    to = r.get("to") or {}
    if r["op"] == "add":
        if not is_added(r["id"]) or not re.fullmatch(r"[0-9A-F]{6}", str(r.get("fid") or "")) or not ADD_FIRST <= int(r["fid"], 16) <= ADD_LAST:
            bad("an added thing needs an identity flora/<cx>,<cy>/add<n> and a form id of its own block")
        if not (isinstance(to.get("base"), str) and _vec(to.get("pos"), 3) and _vec(to.get("rot"), 3) and isinstance(to.get("scale"), (int, float))):
            bad("add needs to.base, to.pos, to.rot and to.scale")
    elif r["op"] != "restore" and not (isinstance(r.get("base"), str) and _vec(r.get("pos"), 3)):
        bad("the thing's base and position at the time of the edit are needed")
    if r["op"] == "move" and not (to and set(to) <= {"pos", "rot", "scale"} and all(_vec(to[k], 3) for k in ("pos", "rot") if k in to)
                                  and isinstance(to.get("scale", 1.0), (int, float))):
        bad("move needs to.pos, to.rot or to.scale")
    if r["op"] == "swap" and not isinstance(to.get("base"), str):
        bad("swap needs to.base")
    if not is_added(r["id"]) and r["op"] != "restore" and not _vec(r.get("origin"), 2):
        bad("origin (where the rules put the thing: x, y) is needed")
    if not set(r.get("confirmed") or ()) <= set(RULES):
        bad(f"confirmed names a rule that is none of {', '.join(RULES)}")


def load(path: Path | None = None, seats: bool = False) -> list[dict]:
    """The rows of the source file in order (no file: none); a malformed row or a number used twice stops the build.
    The single-thing rows alone, or with `seats` every row (seat rows name a base, not a thing)."""
    path = Path(path or EDITS)
    if not path.exists():
        return []
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for r in rows:
        validate(r)
    ns = [r["n"] for r in rows]
    fids = [r["fid"] for r in rows if r["op"] == "add"]
    if len(set(ns)) != len(ns) or len(set(fids)) != len(fids) or ns != sorted(ns):
        raise EditError(f"{path}: the rows' numbers are not rising and single, or two added things share a form id")
    return rows if seats else [r for r in rows if r["op"] not in BASE_OPS]


def seat_rows(path: Path | None = None) -> dict[str, float]:
    """base (plugin:edid) -> how far its things' lowest vertex is set into the ground (the last seat row wins)."""
    return {r["base"]: float((r.get("to") or {}).get("embed_m", SEAT_EMBED_M)) for r in load(path, seats=True) if r["op"] == "seat"}


def drop_rows(path: Path | None = None) -> set[str]:
    """The bases (plugin:edid) every thing of which the edits take away."""
    return {r["base"] for r in load(path, seats=True) if r["op"] == "drop"}


# ---- the placement, read a row at a time --------------------------------------------------------------------------

class Placed:
    """The placement as the rules made it (place.PLACED): its manifest, its bases and its shards, each read once."""

    def __init__(self, d: Path | None = None):
        self.dir = Path(d or P.PLACED)
        self.manifest = json.loads((self.dir / "manifest.json").read_text())
        self.bases_doc = json.loads((self.dir / "bases.json").read_text())
        self.bases = {b["key"]: b for b in self.bases_doc["bases"]}
        self.rows = sorted((int(f.name[2:-6]) for f in self.dir.glob("cy*.jsonl")), reverse=True)
        self._lines: dict[int, list[tuple[str, dict]]] = {}

    def text(self, cy: int) -> str:
        return (self.dir / shard_name(cy)).read_text(encoding="utf-8")

    def lines(self, cy: int) -> list[tuple[str, dict]]:
        if cy not in self._lines:
            self._lines[cy] = [(ln, json.loads(ln)) for ln in self.text(cy).splitlines() if ln] if cy in self.rows else []
        return self._lines[cy]

    def get(self, ident: str) -> dict | None:
        return next((o for _, o in self.lines(id_cell(ident)[1]) if o["id"] == ident), None)

    def by_fid(self, fid: str) -> dict | None:
        needle = f'"fid":"{fid.upper()}"'
        for cy in self.rows:
            if needle in self.text(cy):
                return next(o for _, o in self.lines(cy) if o["fid"] == fid.upper())
        return None


def state_of(o: dict) -> dict:
    return {"base": o["key"], "pos": list(o["pos"]), "rot": list(o["rot"]), "scale": o["scale"], "cls": o["cls"], "db": o["db"],
            "fid": o["fid"]}


# ---- the rows folded over the placement ---------------------------------------------------------------------------

def reanchor(placed: Placed, base: str, origin, taken: set) -> tuple[str | None, float]:
    """The identity of the one thing of `base` nearest `origin` within REANCHOR that no row names, and how far."""
    cx, cy = cell_of(*origin)
    hits = []
    for row in (cy - 1, cy, cy + 1):
        for _, o in placed.lines(row):
            d = math.hypot(o["pos"][0] - origin[0], o["pos"][1] - origin[1])
            if d <= REANCHOR and o["key"].lower() == base.lower() and o["id"] not in taken:
                hits.append((d, o["id"]))
    hits.sort()
    if not hits or (len(hits) > 1 and hits[1][0] - hits[0][0] < 1e-6):
        return None, 0.0
    return hits[0][1], hits[0][0]


def resolve(rows: list[dict], placed: Placed, new_bases: dict | None = None) -> dict:
    """What the rows make of the placement: {"final": identity -> the thing's state after the edits (None: removed),
    for the things they change alone; "was": the same things as the rules placed them (None: added); "owner":
    the identities an owner's row made what they are; "confirmed": identity -> the rules its owner rows confirm;
    "rows": each row's fate (applied, reanchored, orphaned, held, void) with its reason}. `new_bases` gives the
    class and db id of bases the placement does not hold (key -> its bases.json row)."""
    bases = {**placed.bases, **(new_bases or {})}
    named = {r["id"] for r in rows if not is_added(r["id"]) and placed.get(r["id"]) is not None}
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["id"], []).append(r)
    final, was, owner, confirmed, fate = {}, {}, set(), {}, {}
    for ident, rs in groups.items():
        target, note = ident, ""
        o = None if is_added(ident) else placed.get(ident)
        if o is None and not is_added(ident):
            first = next((r for r in rs if r["op"] != "restore"), None)
            if first is None:           # only restores: nothing is asked of a thing that is not there
                fate.update({r["n"]: ("applied", "nothing to restore") for r in rs})
                continue
            target, d = reanchor(placed, first["base"], first["origin"], named | set(final))
            if target is None:
                if rs[-1]["op"] == "restore":
                    fate.update({r["n"]: ("applied", "restored: the rules no longer place it") for r in rs})
                else:
                    fate.update({r["n"]: ("orphaned", f"the rules no longer place {first['base']} within {REANCHOR / P.UPM:.0f} m of "
                                                      f"{first['origin'][0]:.0f},{first['origin'][1]:.0f}: kept, not applied") for r in rs})
                continue
            o, note = placed.get(target), f"re-anchored to {target}, {d / P.UPM:.2f} m from where it stood"
        pristine = state_of(o) if o is not None else None
        st, held, conf = (dict(pristine) if pristine else None), False, set()
        for r in rs:
            own = r["tier"] == OWNER_TIER
            if held and not own:
                fate[r["n"]] = ("held", "the owner has edited this thing: a lower tier's row is not applied")
                continue
            to, why = r.get("to") or {}, None
            if r["op"] == "restore":
                st, conf = (dict(pristine) if pristine else None), set()
            elif r["op"] == "add":
                if st is not None:
                    why = "the thing is already there"
                else:
                    b = bases.get(to["base"]) or {}
                    st = {"base": to["base"], "pos": list(to["pos"]), "rot": list(to["rot"]), "scale": to["scale"],
                          "cls": b.get("cls") or "added", "db": b.get("db_id") or "added", "fid": r["fid"]}
            elif st is None:
                why = "the thing is removed or not yet added"
            elif r["op"] == "remove":
                st = None
            elif r["op"] == "move":
                if "pos" in to and cell_of(*to["pos"][:2])[1] not in placed.rows:
                    why = "the new position lies outside the world's cells"
                else:
                    st = {**st, **{k: (list(v) if isinstance(v, list) else v) for k, v in to.items()}}
            elif r["op"] == "swap":
                b = bases.get(to["base"]) or {}
                st = {**st, "base": to["base"], "cls": st["cls"] if st["cls"].startswith("road_") else b.get("cls") or st["cls"],
                      "db": b.get("db_id") or st["db"]}
            if why:
                fate[r["n"]] = ("void", why)
                continue
            held |= own
            if own:
                conf |= set(r.get("confirmed") or ())
            fate[r["n"]] = ("reanchored" if note else "applied", note)
        if st != pristine:
            final[target], was[target] = st, pristine
            if held:
                owner.add(target)
            confirmed[target] = sorted(conf)
    return {"final": final, "was": was, "owner": owner, "confirmed": confirmed,
            "rows": [{"n": r["n"], "op": r["op"], "id": r["id"], "by": r["by"], "status": fate[r["n"]][0], "detail": fate[r["n"]][1]} for r in rows]}


def digest(res: dict) -> str:
    """The digest of what the edits change: empty when they change nothing."""
    if not res["final"]:
        return ""
    return hashlib.sha256(json.dumps(res["final"], sort_keys=True).encode()).hexdigest()[:12]


# ---- bases the placement does not hold ----------------------------------------------------------------------------

class Stack:
    """The laid mod stack as the placer reads a base from it: its record, its model, its textures, its collision."""
    tex_audit, collision = P.Palette.tex_audit, P.Palette.collision

    def __init__(self, bases: dict):
        from tools.navmesh import meshes
        meshes.PROFILE = "NewWorld"
        self.resolver = meshes.Resolver(P.DATA)
        self.rec = {k: b for k, b in bases.items()}

    def base(self, key: str) -> dict:
        """The bases.json row of a base the placement does not hold, read from its own plugin; EditError when it
        cannot be placed (no such record, no bounds or model, an editor id that names another record, a model or a
        diffuse texture the NewWorld profile does not lay)."""
        key = P.canon(key)
        rec = P.read_bases({key}).get(key)
        if not rec or not rec["obnd"] or not rec["model"]:
            raise EditError(f"{key}: no placeable record (STAT, TREE, FLOR, MSTT) with bounds and a model")
        if not rec["edid"] or P.first_edids(rec["plugin"]).get(rec["edid"].lower()) != int(key.split(":")[0], 16):
            raise EditError(f"{key}: its editor id does not name this record in its plugin")
        if self.resolver.where(rec["model"]) is None:
            raise EditError(f"{key}: its model {rec['model']} is not in the NewWorld profile")
        audit = self.tex_audit(rec["model"])
        if audit["missing_diffuse"]:
            raise EditError(f"{key}: a diffuse texture inside its model is not in the NewWorld profile")
        db = next((b for b in P.jsonl("flora_base") if b["form_key"].lower() == key.lower()), None)
        fam = {f["id"]: f for f in P.jsonl("flora_family")}
        row = P.base_row(key, rec, audit, db["id"] if db else None, fam[db["flora_family_id"]]["flora_class_id"] if db else None)
        self.rec[key] = row
        return row


def new_bases(rows: list[dict], placed: Placed) -> dict:
    """The bases.json rows of the bases the rows name and the placement does not hold."""
    want = sorted({(r.get("to") or {}).get("base") for r in rows} - {None} - set(placed.bases))
    if not want:
        return {}
    stack = Stack(placed.bases)
    return {k: stack.base(k) for k in want}


# ---- apply ----------------------------------------------------------------------------------------------------

def _write(path: Path, text: str) -> bool:
    """Write the file when its bytes differ; True when it was written."""
    data = text.encode("utf-8")
    try:
        if path.read_bytes() == data:
            return False
    except OSError:
        pass
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return True


def _line(ident: str, st: dict, bases: dict) -> str:
    pos = [round(float(v), 1) for v in st["pos"]]
    r = {"cell": list(cell_of(pos[0], pos[1])), "base": st["base"], "pos": pos, "rot": [round(float(v), 5) for v in st["rot"]],
         "scale": round(float(st["scale"]), 4), "cls": st["cls"], "db": st["db"], "id": ident, "fid": st["fid"]}
    return P.shard_line(r, bases[st["base"]])


def cells_counts(placed: Placed, keep: bool = False) -> Counter:
    """Placed things a cell, from the placement's count beside its shards; counted from the shards when that is not
    this placement's, and with `keep` written there."""
    f = placed.dir / "counts.json"
    if f.exists() and json.loads(f.read_text()).get("key") == placed.manifest["key"]:
        return Counter({tuple(map(int, k.split(","))): v for k, v in json.loads(f.read_text())["cells"].items()})
    n = Counter()
    for cy in placed.rows:
        for ln in placed.text(cy).splitlines():
            if ln:
                o = json.loads(ln)
                n[cell_of(o["pos"][0], o["pos"][1])] += 1
    if keep:
        f.write_text(json.dumps({"key": placed.manifest["key"], "cells": {f"{c[0]},{c[1]}": v for c, v in sorted(n.items())}}))
    return n


def counts_after(placed: Placed, res: dict) -> Counter:
    n = Counter(cells_counts(placed, keep=True))
    for ident, st in res["final"].items():
        w = res["was"][ident]
        if w is not None:
            n[cell_of(*w["pos"][:2])] -= 1
        if st is not None:
            n[cell_of(*st["pos"][:2])] += 1
    return +n


def apply(edits: Path | None = None, placed_dir: Path | None = None, refs_dir: Path | None = None, log=print) -> dict:
    """The placement with the edits applied, written to the placed-refs hook; returns the record (edits.json)."""
    t0 = time.time()
    placed = Placed(placed_dir)
    out = Path(refs_dir or P.REFS)
    out.mkdir(parents=True, exist_ok=True)
    rows = load(edits)
    seats, drops = seat_rows(edits), drop_rows(edits)
    seater, seated, dropped, dropped_cells = (Seater() if seats else None), Counter(), Counter(), Counter()
    extra = new_bases(rows, placed)
    res = resolve(rows, placed, extra)
    bases = {**placed.bases, **extra}
    # the shard rows the edits touch: where each changed thing stood and where it stands
    here: dict[int, dict[str, dict | None]] = {}     # row -> identity -> its state there (None: no longer in this row)
    arrive: dict[int, list[str]] = {}
    for ident, st in res["final"].items():
        w = res["was"][ident]
        home = id_cell(ident)[1] if w is not None else None
        dest = cell_of(*st["pos"][:2])[1] if st is not None else None
        if home is not None:
            here.setdefault(home, {})[ident] = st if dest == home else None
        if dest is not None and dest != home:
            here.setdefault(dest, {})
            arrive.setdefault(dest, []).append(ident)
    d = digest(res)
    if seats or drops:
        d = hashlib.sha256((d + json.dumps(sorted(seats.items())) + json.dumps(sorted(drops))).encode()).hexdigest()[:12]
    key = placed.manifest["key"] + (f"+{d}" if d else "")
    man_path = out / "manifest.json"
    try:
        standing = json.loads(man_path.read_text()).get("key") == key
    except (OSError, ValueError):
        standing = False
    if not standing:
        man_path.unlink(missing_ok=True)      # a stopped pass leaves no manifest: the shards are compared again
    h, total, wrote = hashlib.sha256(), 0, []
    for cy in placed.rows:
        if cy in here or seats or drops:
            lines = []
            for ln, o in placed.lines(cy):
                if o["id"] not in here.get(cy, ()) and o["base"] in drops:
                    dropped[o["base"]] += 1
                    dropped_cells[tuple(o["cell"])] += 1
                    continue
                if o["id"] not in here.get(cy, ()):
                    z = seater.seat(o, seats[o["base"]]) if o["base"] in seats else None
                    if z is None:
                        lines.append(ln)
                    else:                    # a seated thing: its own z, all else as the rules placed it
                        st = state_of(o)
                        st["pos"][2] = z
                        lines.append(_line(o["id"], st, bases))
                        seated[o["base"]] += 1
                elif here[cy][o["id"]] is not None:
                    lines.append(_line(o["id"], here[cy][o["id"]], bases))
            lines += [_line(i, res["final"][i], bases) for i in sorted(arrive.get(cy, ()))]
            text = "\n".join(lines) + ("\n" if lines else "")
        else:
            text = placed.text(cy)
        h.update(text.encode())
        total += text.count("\n")
        if _write(out / shard_name(cy), text):
            wrote.append(cy)
    for old in out.glob("cy*.jsonl"):
        if int(old.name[2:-6]) not in placed.rows:
            old.unlink()
    bdoc = dict(placed.bases_doc)
    if extra:
        bdoc["bases"] = sorted([*bdoc["bases"], *extra.values()], key=lambda b: b["key"])
        bdoc["key"] = f"{bdoc['key']}+{hashlib.sha256(json.dumps(sorted(extra)).encode()).hexdigest()[:12]}"
    _write(out / "bases.json", json.dumps(bdoc, indent=1))
    counts = counts_after(placed, res)
    for c, n in dropped_cells.items():
        counts[c] -= n
    _write(out / "counts.json", json.dumps({f"{c[0]},{c[1]}": v for c, v in sorted(counts.items())}))
    tally = Counter(r["status"] for r in res["rows"])
    rec = {"placed_key": placed.manifest["key"], "digest": d, "file_rows": len(rows), "by_status": dict(sorted(tally.items())),
           "rows": res["rows"],
           "things": [{"id": i, "fid": (st or res["was"][i])["fid"], "owner": i in res["owner"], "confirmed": res["confirmed"][i],
                       "was": res["was"][i], "now": st} for i, st in sorted(res["final"].items())],
           "new_bases": sorted(extra), "seated": dict(sorted(seated.items())),
           "dropped": dict(sorted(dropped.items()))}
    _write(out / "edits.json", json.dumps(rec, indent=1))
    man = {**placed.manifest, "key": key, "refs": total, "shard_sha256": h.hexdigest()[:16],
           "placed": {k: placed.manifest.get(k) for k in ("key", "refs", "shard_sha256", "bases")}, "bases": len(bdoc["bases"]),
           "edits": {"rows": len(rows) + len(seats), "things": len(res["final"]), "digest": d, "seated": sum(seated.values()), "dropped": sum(dropped.values()),
                     **dict(sorted(tally.items()))}}
    _write(man_path, json.dumps(man, indent=1))
    log(f"edits: {len(rows)} rows, {len(res['final'])} things changed; the placement itself untouched ({placed.manifest['refs']} references, "
        f"none placed again); shards written: {len(wrote)} of {len(placed.rows)}"
        + (f" (rows {', '.join(f'{c:+d}' for c in wrote[:12])}{' ...' if len(wrote) > 12 else ''})" if wrote else "")
        + f"; {total} references; {time.time() - t0:.1f} s")
    for r in res["rows"]:
        if r["status"] != "applied":
            log(f"  {r['status'].upper()} row {r['n']} ({r['op']} {r['id']}, by {r['by']}): {r['detail']}")
    return rec


# ---- the placement's rules on one thing ---------------------------------------------------------------------------

def things_near(placed: Placed, res: dict, cells: set) -> list[dict]:
    """Every placed thing of the cells as the edits leave it: {"id", **state}."""
    out = []
    for cy in sorted({c[1] for c in cells}):
        for _, o in placed.lines(cy):
            if o["id"] in res["final"]:
                continue
            if cell_of(o["pos"][0], o["pos"][1]) in cells:
                out.append({"id": o["id"], **state_of(o), "model": o["model"], "edid": o["base"]})
    for i, st in res["final"].items():
        if st is not None and cell_of(*st["pos"][:2]) in cells:
            b = placed.bases.get(st["base"]) or {}
            out.append({"id": i, **st, "model": b.get("model"), "edid": b.get("ref"), "edited": True})
    return out


class Judge:
    """The placement's rules (checks.py) asked of one thing: the codes of RULES it breaks."""

    def __init__(self, placed: Placed, res: dict, bases: dict):
        self.placed, self.res = placed, res
        self.W, self.R = P.World(), P.Roads()
        self.base = {r["id"]: r for r in P.jsonl("flora_base")}
        self.fam = {r["id"]: r for r in P.jsonl("flora_family")}
        flows = {r["id"]: r["flows"] for r in P.jsonl("water_kind")}
        self.flows = [flows.get(k, False) for k in self.W.legend["kinds"]]
        self.bases = bases
        self._stack = None

    def breaks(self, ident: str, st: dict) -> list[str]:
        import numpy as np
        W, out = self.W, []
        x, y, z = (float(v) for v in st["pos"])
        xs, ys = np.array([x]), np.array([y])
        cls = st["cls"]
        clear = float(self.R.clear(xs, ys)[0])
        if clear < 0:
            out.append("road")
        elif clear < 1e8:                   # within the roads' reach: its collision against the walking width
            if self._stack is None:
                self._stack = Stack(self.bases)
            if P.road_shortfall(W, self._stack, self.R, {"base": st["base"], "pos": st["pos"], "rot": st["rot"], "scale": st["scale"]}) > 0:
                out.append("road-walk")
        t1, t2 = W.tri_grounds(xs, ys)
        depth = -float(W.ground(xs, ys)[0]) / P.UPM
        if cls in P.TREES and depth > 0.05:
            kind = int(W.at("kind", xs, ys)[0])
            fam = self.fam.get((self.base.get(st["db"]) or {}).get("flora_family_id")) or {}
            hab = W.legend["habitats"][int(W.at("habitat", xs, ys)[0])]
            if kind < len(self.flows) and self.flows[kind]:
                out.append("flowing-water")
            elif hab not in P.TREE_IN_WATER or depth > (fam.get("standing_water_max_m") or 0) + 0.05:
                out.append("standing-water")
        if int(W.at("flags", xs, ys)[0]) & 2:
            out.append("pad")
        cx, cy = cell_of(x, y)
        near = things_near(self.placed, self.res, {(cx + i, cy + j) for i in (-1, 0, 1) for j in (-1, 0, 1)})
        if any(o["id"] != ident and math.hypot(o["pos"][0] - x, o["pos"][1] - y) < P.MIN_SPACING_M * P.UPM - 1e-6 for o in near):
            out.append("spacing")
        if not cls.startswith("road_") and sum(1 for o in near if cell_of(*o["pos"][:2]) == (cx, cy) and not o["cls"].startswith("road_")) > P.CAP:
            out.append("budget")
        ob = (self.bases.get(st["base"]) or {}).get("obnd")
        if cls in P.ROCKS and ob:
            if P.underside_gap(W, x, y, z, ob, float(st["scale"]), st["rot"]) > 0.5:
                out.append("underside")
        elif z - float(max(t1[0], t2[0])) > HOVER_M * P.UPM:
            out.append("hover")
        return out


def check(edits: Path | None = None, placed_dir: Path | None = None, refs_dir: Path | None = None, log=print) -> int:
    """The edited things judged by the placement's rules; writes edits_check.json beside the shards. Red when the
    hook is not the edits' (apply first), when an edit below the owner's tier breaks a rule, or when a form id is
    used twice or lies in another allocator's range (form_id_faults)."""
    placed = Placed(placed_dir)
    out = Path(refs_dir or P.REFS)
    rows = load(edits)
    extra = new_bases(rows, placed)
    res = resolve(rows, placed, extra)
    try:
        rec = json.loads((out / "edits.json").read_text())
    except (OSError, ValueError):
        rec = {}
    if rec.get("digest") != digest(res) or rec.get("placed_key") != placed.manifest["key"]:
        log("FAIL the placed-refs hook is not this placement with these edits applied: run the edits stage")
        return 1
    judged, red = [], 0
    alive = {i: st for i, st in res["final"].items() if st is not None}
    judge = Judge(placed, res, {**placed.bases, **extra}) if alive else None
    for i, st in sorted(alive.items()):
        got = judge.breaks(i, st)
        ok = set(res["confirmed"][i])
        owner = i in res["owner"]
        row = {"id": i, "fid": st["fid"], "owner": owner, "breaks": got, "confirmed": sorted(set(got) & ok),
               "to_confirm": sorted(set(got) - ok) if owner else [], "fail": [] if owner else got}
        judged.append(row)
        for c in row["confirmed"]:
            log(f"  CONFIRMED by the owner: {i} ({st['fid']}): {RULES[c]}")
        for c in row["to_confirm"]:
            log(f"  TO CONFIRM (the owner's choice, not a fault): {i} ({st['fid']}): {RULES[c]}")
        for c in row["fail"]:
            red += 1
            log(f"  FAIL {i} ({st['fid']}): {RULES[c]}: an edit below the owner's tier keeps the placement's rules")
    tally = Counter(r["status"] for r in res["rows"])
    doc = {"digest": digest(res), "things": len(res["final"]), "judged": len(judged), "removed": len(res["final"]) - len(alive),
           "confirmed": sum(len(r["confirmed"]) for r in judged), "to_confirm": sum(len(r["to_confirm"]) for r in judged),
           "failed": red, "orphaned": tally.get("orphaned", 0), "reanchored": tally.get("reanchored", 0), "held": tally.get("held", 0),
           "void": tally.get("void", 0), "rows": judged}
    _write(out / "edits_check.json", json.dumps(doc, indent=1))
    for r in res["rows"]:
        if r["status"] in ("orphaned", "void", "held", "reanchored"):
            log(f"  {r['status'].upper()} row {r['n']} ({r['op']} {r['id']}): {r['detail']}")
    log(f"edits check: {doc['things']} things changed ({doc['removed']} removed, {doc['judged']} judged by the placement's rules): "
        f"{doc['confirmed']} rule breaks confirmed by the owner, {doc['to_confirm']} to confirm, {red} failed; rows orphaned "
        f"{doc['orphaned']}, re-anchored {doc['reanchored']}, held {doc['held']}, void {doc['void']}")
    ids = form_id_faults(out, log)
    log("PASS" if not red and not ids else "FAIL")
    return 1 if red or ids else 0


def form_id_faults(refs_dir: Path, log=print) -> int:
    """The form ids of every producer's references as they now stand (this hook's shards and, in a plugin's refs/,
    the other producers' beside it) with the plugin's other allocators (idspace.py): none used twice, none in
    another allocator's range. A fault here stops the run before the navmesh and the world file are made."""
    plugin = refs_dir.parent.parent if refs_dir.parent.name == "refs" else None
    bad, n = idspace.faults(plugin or refs_dir, producers=None if plugin else [refs_dir])
    for b in bad:
        log(f"  FAIL form ids: {b}")
    log(f"form ids: {n['ids']} read ({', '.join(f'{k} {v}' for k, v in n.items() if k != 'ids')}): "
        + ("none used twice, none outside its allocator's range" if not bad else f"{len(bad)} faults"))
    return len(bad)


# ---- what an edit makes stale -------------------------------------------------------------------------------------

def reach_cells(pos, radius: float) -> set:
    """The cells whose navmesh reads ground or collision within `radius` of `pos`: each cell is cut from its own
    ground and the border the navmesh reads round it."""
    from tools.navmesh import params
    r = radius + params.BORDER_SAMPLES * P.SAMPLE + params.AGENT_RADIUS
    return {(cx, cy) for cx in range(int(math.floor((pos[0] - r) / P.CELL)), int(math.floor((pos[0] + r) / P.CELL)) + 1)
            for cy in range(int(math.floor((pos[1] - r) / P.CELL)), int(math.floor((pos[1] + r) / P.CELL)) + 1)}


def places_touched(spots: list, cells: set, places: Path | None = None) -> dict:
    """Built places an edit reaches: {place: {"clear": rows of its clear.jsonl standing where an edited thing stood,
    "cells": True when its exterior or land patches lie in the edit's cells}}."""
    out = {}
    for d in sorted(Path(places or PLACES).glob("*/place.json")):
        d = d.parent
        hit = {"clear": 0, "cells": False}
        f = d / "clear.jsonl"
        for ln in (f.read_text(encoding="utf-8").splitlines() if f.exists() else ()):
            if ln.strip():
                q = json.loads(ln)["pos"]
                hit["clear"] += any(abs(q[0] - s[0]) <= 1.0 and abs(q[1] - s[1]) <= 1.0 for s in spots)
        for name, pick in (("spaces/exterior/refs.jsonl", lambda r: [cell_of(*r["pos"][:2])] if "pos" in r else []),
                           ("land.jsonl", lambda r: [tuple(r["cell"])] if "cell" in r else [])):
            f = d / name
            for ln in (f.read_text(encoding="utf-8").splitlines() if f.exists() and not hit["cells"] else ()):
                if ln.strip() and any(c in cells for c in pick(json.loads(ln))):
                    hit["cells"] = True
                    break
        if hit["clear"] or hit["cells"]:
            out[d.name] = hit
    return out


def pending(edits: Path | None = None, placed_dir: Path | None = None, refs_dir: Path | None = None, places: Path | None = None) -> dict:
    """What the source file changes that the placed-refs hook does not hold yet, and what that makes stale."""
    from tools.newworld.world import mist
    placed = Placed(placed_dir)
    out = Path(refs_dir or P.REFS)
    rows = load(edits)
    res = resolve(rows, placed, {k: {} for k in {(r.get("to") or {}).get("base") for r in rows} - {None} - set(placed.bases)})
    try:
        rec = json.loads((out / "edits.json").read_text())
        held = {t["id"]: t["now"] for t in rec["things"]} if rec.get("placed_key") == placed.manifest["key"] else {}
    except (OSError, ValueError, KeyError):
        held = {}
    changed = sorted(i for i in set(res["final"]) | set(held) if res["final"].get(i, "-") != held.get(i, "-"))
    spots, nav, shard_rows, new = [], set(), set(), set()
    before_n, after_n = Counter(), Counter()
    for i in changed:
        was = res["was"].get(i) if i in res["was"] else (placed.get(i) and state_of(placed.get(i)))
        a = held[i] if i in held else was            # as the hook holds it
        b = res["final"][i] if i in res["final"] else was   # as the file makes it
        for st, n in ((a, before_n), (b, after_n)):
            if st is None:
                continue
            ob = (placed.bases.get(st["base"]) or {}).get("obnd") or [0] * 6
            nav |= reach_cells(st["pos"], max(abs(v) for v in ob) * float(st["scale"]))
            spots.append(st["pos"])
            shard_rows.add(cell_of(*st["pos"][:2])[1])
            n[cell_of(*st["pos"][:2])] += 1
            if st["base"] not in placed.bases:
                new.add(st["base"])
    base_n = cells_counts(placed) if changed else Counter()
    hook_n = Counter(base_n)
    for i, st in held.items():
        w = placed.get(i)
        if w is not None:
            hook_n[cell_of(*w["pos"][:2])] -= 1
        if st is not None:
            hook_n[cell_of(*st["pos"][:2])] += 1
    budget = lambda n: max(0, min(mist.CAP, mist.REFS_CAP - n))  # noqa: E731  (mist.py's own line)
    mist_cells = sorted(c for c in set(before_n) | set(after_n)
                        if budget(hook_n[c]) != budget(hook_n[c] - before_n[c] + after_n[c]))
    count_cells = sorted(c for c in set(before_n) | set(after_n) if before_n[c] != after_n[c])
    return {"things": changed, "shard_rows": sorted(shard_rows), "navmesh_cells": sorted(nav), "count_cells": count_cells,
            "mist_cells": mist_cells, "new_bases": sorted(new),
            "places": places_touched(spots, {cell_of(*s[:2]) for s in spots}, places) if spots else {},
            "orphaned": [r for r in res["rows"] if r["status"] == "orphaned"]}


def print_pending(p: dict, file=None) -> None:
    file = file or sys.stdout
    if not p["things"]:
        print("edits of placed things: none waiting", file=file)
        return
    say = lambda s: print("  " + s, file=file)  # noqa: E731
    print(f"edits of placed things: {len(p['things'])} waiting ({', '.join(p['things'][:4])}{' ...' if len(p['things']) > 4 else ''})", file=file)
    say(f"edits      an edits-only pass: nothing is placed again; {len(p['shard_rows'])} shard rows are written again "
        f"({', '.join(f'{c:+d}' for c in p['shard_rows'][:8])}), every other row keeps its bytes")
    say(f"navmesh    at most {len(p['navmesh_cells'])} cells within reach are cut again ({', '.join(f'{c[0]},{c[1]}' for c in p['navmesh_cells'][:9])}"
        f"{' ...' if len(p['navmesh_cells']) > 9 else ''}) and their seams joined to their neighbours; every other cell is taken from "
        "its cache (the run's own line counts them: cells reused, built)")
    say("mist       " + (f"its budget changes in {len(p['mist_cells'])} cells: their rows are written again" if p["mist_cells"] else
                         "not run: no cell's count of placed things changes" if not p["count_cells"] else
                         "run, and writes the same rows: no cell's budget changes"))
    say("map        the LOD plan's counts by base are made again (the same plan files unless a base is new)")
    say("esm        the world file is written again whole (about a minute for the province); every other reference keeps its form id")
    say("readback   the rows for placed things, on the written file")
    say("LOD        DynDOLOD cannot redo less than the world's object and tree LOD: one run at the end of the edit session "
        "(about 16 minutes), not one an edit; the edit shows in the loaded cells without it. TexGen "
        + (f"runs only if a new base is a tree ({', '.join(p['new_bases'])}: the LOD's own key decides)" if p["new_bases"] else "not run: no base is new")
        + ". Terrain LOD: never")
    if p["places"]:
        for name, hit in p["places"].items():
            say(f"place      {name}: " + "; ".join(x for x in (
                f"{hit['clear']} rows of its clear.jsonl name an edited thing: take those rows out, then build the place" if hit["clear"] else "",
                "its cells hold an edited thing: its ground bundle and build follow the world file" if hit["cells"] else "") if x))
    else:
        say("places     no built place's cells or clear list is touched")
    for r in p["orphaned"]:
        say(f"ORPHANED   row {r['n']} ({r['op']} {r['id']}): {r['detail']}")


# ---- the door: list and edit ------------------------------------------------------------------------------------

def find(placed: Placed, res: dict, rows: list[dict], ident: str | None, fid: str | None, at) -> tuple[str, dict | None]:
    """(identity, the thing's state today or None when it is removed) for --id, --fid or --at."""
    if at is not None:
        cx, cy = cell_of(*at)
        near = sorted((math.hypot(o["pos"][0] - at[0], o["pos"][1] - at[1]), o["id"]) for o in
                      things_near(placed, res, {(cx + i, cy + j) for i in (-1, 0, 1) for j in (-1, 0, 1)}))
        if not near or near[0][0] > REANCHOR:
            raise EditError(f"no placed thing within {REANCHOR / P.UPM:.0f} m of {at[0]:.1f},{at[1]:.1f}")
        ident = near[0][1]
    elif fid is not None:
        fid = fid.upper().rsplit(":", 1)[-1].zfill(6)
        added = next((r["id"] for r in rows if r.get("fid") == fid), None)
        o = None if added else placed.by_fid(fid)
        if not added and o is None:
            raise EditError(f"no placed thing has the form id {fid}")
        ident = added or o["id"]
    id_cell(ident)
    if ident in res["final"]:
        return ident, res["final"][ident]
    o = None if is_added(ident) else placed.get(ident)
    if o is None:
        raise EditError(f"{ident}: no such placed thing")
    return ident, state_of(o)


def append(path: Path, row: dict) -> None:
    validate(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")


def edit(op: str, by: str, edits: Path | None = None, placed_dir: Path | None = None, ident: str | None = None, fid: str | None = None,
         at=None, pos=None, rot=None, scale=None, base: str | None = None, why: str = "", confirm: bool = False,
         tier: str | None = None, now: str | None = None, judge: bool = True) -> dict:
    """Validate one edit against the placement and the rows already in the file, and append it. Returns
    {"row": the row, "breaks": the placement rules it breaks, "appended": bool}: an owner's edit that breaks a rule
    is appended only with `confirm` (the rules go into the row); another tier's is refused."""
    path = Path(edits or EDITS)
    placed = Placed(placed_dir)
    rows = load(path, seats=True)
    res = resolve([r for r in rows if r["op"] not in BASE_OPS], placed, {})
    tier = tier or (OWNER_TIER if by == OWNER else AGENT_TIER)
    if tier not in tiers():
        raise EditError(f"tier {tier!r} is none of the statement tiers ({', '.join(tiers())})")
    n = max((r["n"] for r in rows), default=0) + 1
    row = {"n": n, "op": op}
    if op == "add":
        if base is None or pos is None:
            raise EditError("add needs --base and --pos")
        cx, cy = cell_of(*pos[:2])
        if cy not in placed.rows:
            raise EditError(f"{pos[0]:.0f},{pos[1]:.0f} lies outside the world's cells")
        nfid = ADD_FIRST + sum(1 for r in rows if r["op"] == "add")
        if nfid > ADD_LAST:
            raise EditError("the form ids for added things are used up")
        ident, st = f"flora/{cx},{cy}/add{n:06d}", None
        row.update(id=ident, fid=f"{nfid:06X}")
    else:
        ident, st = find(placed, res, rows, ident, fid, at)
        if st is None and op != "restore":
            raise EditError(f"{ident} is removed: restore it first")
        row["id"] = ident
        if st is not None and op != "restore":
            row.update(base=st["base"], pos=st["pos"])
        o = None if is_added(ident) else placed.get(ident)
        if o is not None:
            row["origin"] = o["pos"][:2]
    if by != OWNER and any(r["id"] == ident and r["tier"] == OWNER_TIER for r in rows):
        raise EditError(f"{ident}: the owner has edited this thing; only the owner edits it again")
    to: dict = {}
    if op in ("move", "add"):
        if pos is not None:
            to["pos"] = [round(float(v), 1) for v in pos]
            if len(to["pos"]) == 2:             # seated: an added thing on the ground, a moved thing as deep as it stood
                W = P.World()
                g = lambda x, y: float(W.ground(x, y))  # noqa: E731
                sink = g(*st["pos"][:2]) - st["pos"][2] if st else 0.0
                to["pos"].append(round(g(*to["pos"]) - sink, 1))
            if cell_of(*to["pos"][:2])[1] not in placed.rows:
                raise EditError(f"{to['pos'][0]:.0f},{to['pos'][1]:.0f} lies outside the world's cells")
        if rot is not None or op == "add":
            to["rot"] = [round(float(v), 5) for v in (rot or (0.0, 0.0, 0.0))]
        if scale is not None or op == "add":
            to["scale"] = round(float(scale if scale is not None else 1.0), 4)
        if not to:
            raise EditError("move needs --pos, --rot or --scale")
    if op in ("swap", "add"):
        if base is None:
            raise EditError(f"{op} needs --base")
        to["base"] = base if base in placed.bases else P.canon(base)
    if to:
        row["to"] = to
    row.update(by=by, tier=tier, at=now or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if why:
        row["why"] = why
    validate(row)
    # the thing as this row leaves it, judged by the placement's rules
    extra = new_bases([row], placed)
    after = resolve([*rows, row], placed, extra)
    fate = after["rows"][-1]
    if fate["status"] != "applied":
        raise EditError(f"{ident}: {fate['detail']}")
    now_st = after["final"].get(ident)
    breaks = Judge(placed, after, {**placed.bases, **extra}).breaks(ident, now_st) if judge and now_st is not None and op != "restore" else []
    if breaks and by != OWNER:
        raise EditError(f"{ident}: the edit breaks the placement's rules ({'; '.join(RULES[c] for c in breaks)}): only the owner may choose to")
    if breaks and not confirm:
        return {"row": row, "breaks": breaks, "appended": False}
    if breaks:
        row["confirmed"] = breaks
    append(path, row)
    return {"row": row, "breaks": breaks, "appended": True}


def listing(placed_dir: Path | None = None, edits: Path | None = None, cell=None, fid: str | None = None, at=None) -> list[dict]:
    """The placed things of a cell (or the one named by form id or position) as the edits leave them: identity,
    form id, base, editor id, class, position, rotation, scale, and whether an edit made it what it is."""
    placed = Placed(placed_dir)
    rows = load(edits)
    res = resolve(rows, placed, {})
    if cell is None:
        ident, st = find(placed, res, rows, None, fid, at)
        if st is None:
            return []
        cell = cell_of(*st["pos"][:2])
        return [o for o in things_near(placed, res, {cell}) if o["id"] == ident]
    return sorted(things_near(placed, res, {tuple(cell)}), key=lambda o: o["id"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.newworld.place")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("refs", help="the placed things of a cell, with their identities and form ids")
    ed = sub.add_parser("edit", help="validate one edit and append it to the source file")
    ed.add_argument("op", choices=OPS)
    ed.add_argument("--by", required=True, help="owner, or the agent's name")
    ed.add_argument("--tier")
    for k in ("--pos", "--rot"):
        ed.add_argument(k, type=float, nargs="+")
    ed.add_argument("--scale", type=float)
    ed.add_argument("--base", help="the base's form key, XXXXXX:<plugin>")
    ed.add_argument("--why", default="")
    ed.add_argument("--confirm", action="store_true", help="the owner chooses to break the placement rules the edit breaks")
    st = sub.add_parser("edits", help="the rebuild's stage: apply, check, plan")
    st.add_argument("step", choices=("apply", "check", "plan"))
    for p in (ls, ed):
        p.add_argument("--id")
        p.add_argument("--fid", help="the thing's form id in the world file (six hex digits, or ArgoniaNewWorld.esm:XXXXXX)")
        p.add_argument("--at", type=float, nargs=2, metavar=("X", "Y"))
    ls.add_argument("--cell", type=int, nargs=2, metavar=("CX", "CY"))
    for p in (ls, ed, st):
        p.add_argument("--edits", type=Path, help="the edits' source file (default: newworld/sources/placed_edits.jsonl)")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "refs":
            if a.id:
                a.cell = id_cell(a.id)
            if not (a.cell or a.fid or a.at):
                ap.error("refs needs --cell, --id, --fid or --at")
            for o in listing(edits=a.edits, cell=a.cell, fid=a.fid, at=a.at):
                if not a.id or o["id"] == a.id:
                    print(json.dumps(o, separators=(",", ":")))
            return 0
        if a.cmd == "edit":
            if a.pos and len(a.pos) not in (2, 3) or a.rot and len(a.rot) != 3:
                ap.error("--pos takes x y or x y z; --rot takes rx ry rz")
            got = edit(a.op, a.by, a.edits, ident=a.id, fid=a.fid, at=a.at, pos=a.pos, rot=a.rot, scale=a.scale, base=a.base,
                       why=a.why, confirm=a.confirm, tier=a.tier)
            print(json.dumps({**got, "breaks": [{"rule": c, "means": RULES[c]} for c in got["breaks"]]}))
            if not got["appended"]:
                print("not appended: the edit breaks the placement's rules above; the owner confirms with --confirm", file=sys.stderr)
                return 3
            return 0
        if a.step == "apply":
            apply(a.edits)
            return 0
        if a.step == "check":
            return check(a.edits)
        print_pending(pending(a.edits))
        return 0
    except EditError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
