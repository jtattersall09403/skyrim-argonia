"""`draft <stage> <place_id>`: one step of the draft alone, on the place files as they stand.

A place is changed narrowly. Each stage applies its own rule to the standing files, changes only the rows it owns
and leaves every other row byte for byte as it was; the run prints the rows changed, added and removed per file.
A row a finalised studio save touched is the owner's and is never changed. A stage that would write outside what it
owns changes nothing and fails.

  fit        each piece in the cluster the source gives it (a light in its fixture's), standing where that cluster
             stands now; where a cluster sits on our land is the whole draft's search and is never run again here
  pieces     `draft.replace` and `draft.drop` as place.json has them: a row of another base than they give goes
             back to its source's piece or takes its replacement; a piece no longer dropped comes back
  seating    each source piece's seat rule as measured in the source (a light `on` its fixture), then its height
  clearance  the world's plants cleared by the source's own measure round the standing buildings, doors and streets
  streets    the build's network: flights, joins, arrivals, streets and patrols (`draft join`)
  people     each person's services as the record promises them (kind, detail, the network's destinations),
             promises a resident keeps, and names, from the people source
  lights     the lights of what we added (a forge's fire); each copied room's lights on the source's own bases
  stations   each promised crafting station the standing files lack, by the person who works it
  jail       the crime faction's jail: the jail room, the cell the player is put in, the prison markers both sides,
             the evidence chests (tools/places/draft/jail.py)
  primitives each copied ref's primitive by its class: a collision box kept with the piece it belongs to, one on
             the source's ground and a trigger that reaches nothing of ours dropped
             (tools/places/draft/primitives.py)
  hang       rope lanterns on the place's Hist and the trees round it, each on a hang point of its tree's own limbs
             (tools/places/draft/hang.py)
  add        the things the agent adds by hand (`draft.add`), outside or in a room (tools/places/draft/adds.py)
  names      each room's name, the one its door and the room show, from what the place data holds
             (tools/places/draft/names.py)
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from tools.places import edits
from tools.places.draft import geom, interiors, io, lights, seating
from tools.places.seat import Ground, seat_all

ANY = None
# what each stage owns: {file pattern: the fields of a standing row it may change (ANY: the whole row), and whether
# it may add or remove rows}
OWNS: dict[str, dict[str, tuple]] = {
    "fit": {"spaces/exterior/refs.jsonl": ({"pos", "rot", "cluster"}, True), "ledger.jsonl": (ANY, False)},
    "pieces": {"spaces/*/refs.jsonl": ({"base", "pos", "rot", "align", "seat"}, True), "ledger.jsonl": (ANY, True)},
    "seating": {"spaces/exterior/refs.jsonl": ({"seat", "pos"}, False)},
    "clearance": {"clear.jsonl": (ANY, True)},
    "streets": {"spaces/*/refs.jsonl": (ANY, True), "spaces/*/space.json": (ANY, True), "paths.jsonl": (ANY, True),
                "people.jsonl": (ANY, True), "clear.jsonl": (ANY, True), "ledger.jsonl": (ANY, True),
                "place.json": (ANY, True)},
    "people": {"people.jsonl": ({"name", "services", "work", "routine", "household", "identity"}, False)},
    "lights": {"spaces/*/refs.jsonl": (ANY, True), "place.json": ({"lights"}, False)},
    "stations": {"spaces/*/refs.jsonl": (ANY, True), "people.jsonl": ({"work", "routine"}, False),
                 "place.json": ({"stations"}, False)},
    "jail": {"spaces/*/refs.jsonl": (ANY, True), "place.json": ({"factions"}, False)},
    "primitives": {"spaces/exterior/refs.jsonl": ({"primitive", "pos", "rot", "seat", "cluster"}, True), "spaces/*/refs.jsonl": (ANY, True),
                   "ledger.jsonl": (ANY, True)},
    "hang": {"spaces/exterior/refs.jsonl": (ANY, True), "place.json": ({"hang"}, False)},
    "add": {"spaces/*/refs.jsonl": (ANY, True)},
    "names": {"spaces/*/space.json": ({"name"}, False)},
}
STAGES = tuple(OWNS)
BUILT = "formids.json"      # the build's own file in the place folder: no stage's, and no stage is judged by it


class StageError(RuntimeError):
    pass


# --- the standing files ---
class Standing:
    def __init__(self, place_id: str, places: Path = io.PLACES, bundles: Path = io.BUNDLES):
        self.place_id, self.pdir = place_id, places / place_id
        self.files = edits.load_place(self.pdir)
        self.place = self.files["place"]
        self.src = io.load(f"src.{self.place['source_id']}", bundles)
        self.grd = io.load(f"ground.{place_id}", bundles)
        self.bases = io.place_bases(self.src, self.grd, self.place)
        self.G = Ground.load(self.grd.path)
        self.G.apply_patches(self.files["land"])
        self.S = self.src.ground
        self.ext: list[dict] = self.files["spaces"]["exterior"]["refs"]
        lp = self.pdir / "ledger.jsonl"
        self.ledger = io.read_jsonl(lp) if lp.exists() else []
        self.src_ext = [r for r in self.src.exterior.refs]
        self.by_src = {r["id"]: r for r in self.src_ext}
        self.bound = lights.fixtures(self.src_ext, self.bases)
        self._clusters = None

    @property
    def clusters(self):
        if self._clusters is None:
            from tools.places.draft.cluster import decompose
            self._clusters = decompose(self.src_ext, self.bases, self.S)
        return self._clusters

    def turn(self, cid) -> float:
        return float((((self.place.get("fit") or {}).get("clusters") or {}).get(cid) or {}).get("rot", 0.0))

    def ours(self) -> dict[str, dict]:
        return {r["src"]: r for r in self.ext if r.get("src")}

    def led(self) -> dict[str, dict]:
        return {lr["src"]: lr for lr in self.ledger if lr.get("space") == "exterior" and "copy" not in lr}

    def stand(self, r: dict, cid: str) -> tuple[float, float, list[float]]:
        """Where source ref r stands in cluster cid as that cluster stands now: at its source offset, turned with the
        cluster, from the cluster's nearest piece that stands as the fit put it."""
        turn = self.turn(cid)
        nudged = {lr["src"] for lr in self.ledger if lr.get("space") == "exterior" and lr.get("nudge")}
        cand = [o for o in self.ext if o.get("cluster") == cid and o.get("src") in self.by_src and o["src"] != r["id"]
                and not o.get("align") and o["src"] not in nudged and o["src"] not in self.bound]
        if not cand:
            raise StageError(f"cluster {cid} has no standing piece to place {r['id']} by")
        a = min(cand, key=lambda o: (math.dist(self.by_src[o["src"]]["pos"][:2], r["pos"][:2]), o["id"]))
        ox, oy = lights.offset(r, self.by_src[a["src"]], turn)
        return round(a["pos"][0] + ox, 2), round(a["pos"][1] + oy, 2), geom.Xf((0, 0), (0, 0), turn).rot3(r.get("rot"))

    def seat_rule(self, r: dict, cid: str, ours: dict[str, dict]) -> dict:
        """Source ref r's seat rule as the draft gives it, naming our rows."""
        if r["id"] in self.bound and self.bound[r["id"]] in ours:
            f = self.by_src[self.bound[r["id"]]]
            return {**lights.seat(r, f), "on": ours[f["id"]]["id"]}
        members = next((c.members for c in self.clusters[0] if c.id == cid), [])
        s = seating.infer(r, [self.by_src[i] for i in members], self.bases, self.S, False)
        if s.get("mode") == "on":
            if s["on"] in ours:
                s["on"] = ours[s["on"]]["id"]
            else:
                s = seating.infer({**r, "kind": "tree"}, [], self.bases, self.S, False)
        return s

    def write(self) -> None:
        edits.write_place(self.pdir, self.files)
        if self.ledger or (self.pdir / "ledger.jsonl").exists():
            io.write_jsonl(self.pdir / "ledger.jsonl", sorted(self.ledger, key=lambda r: (r["space"], r["src"])))


# --- the stages ---
def fit(st: Standing, log=print) -> None:
    _, of, _ = st.clusters
    ours, led = st.ours(), st.led()
    for row in [r for r in st.ext if r.get("src") in st.bound and st.bound[r["src"]] not in ours]:
        from tools.places.draft.run import lights_out
        st.ext.remove(row)
        lr = led.get(row["src"])
        if lr is not None:
            lr.update({"status": "dropped", "why": lights_out(st.bound[row["src"]])})
            lr.pop("as", None)
    for row in st.ext:
        sid = row.get("src")
        if sid not in of or row.get("cluster") == of[sid] or row.get("primitive"):
            continue  # a collision box travels with its piece (`primitives`)
        r = st.by_src[sid]
        if sid in st.bound:
            row["rot"] = geom.Xf((0, 0), (0, 0), st.turn(of[sid])).rot3(r.get("rot"))
        else:
            x, y, rot = st.stand(r, of[sid])
            row["pos"][0], row["pos"][1], row["rot"] = x, y, rot
        log(f"draft fit {st.place_id}: {row['id']} ({row.get('kind')}) from cluster {row.get('cluster')} to {of[sid]}")
        row["cluster"] = of[sid]
        if sid in led and "cluster" in led[sid]:
            led[sid]["cluster"] = of[sid]
    lights.follow(st.ext, st.by_src, st.bound, st.turn)
    seat_all(st.ext, st.G)


def pieces(st: Standing, log=print) -> None:
    from tools.places.draft.run import replace_piece, src_outside
    dec = st.place.get("draft") or {}
    refused: list[str] = []
    replace = io.replacements(dec, st.bases, refused)
    for m in refused:
        log(f"draft pieces {st.place_id}: {m}")
    drop = dec.get("drop") or {}
    _, of, _ = st.clusters
    ours, led = st.ours(), st.led()
    # a piece dropped by this step's old verdict and no longer dropped comes back; one newly dropped goes
    for sid, lr in sorted(led.items()):
        r = st.by_src.get(sid)
        if r is None:
            continue
        if lr["status"] == "dropped" and sid not in drop and sid in of and (
                str(lr.get("why", "")).startswith("Nordic base") or lr.get("by") == "draft.drop"):
            x, y, rot = st.stand(r, of[sid])
            row = {"id": io.mint(st.place_id, "exterior", sid), "base": r["base"], "kind": r.get("kind"),
                   "pos": [x, y, r["pos"][2]], "rot": rot, "scale": r.get("scale", 1.0), "layer": "place",
                   "flags": r.get("flags") or [], "src": sid, "seat": {"mode": "free"}, "cluster": of[sid]}
            for k in ("owner", "lock", "door", "linked", "enable_parent", "primitive", "map_marker", "edid", "radius", "count"):
                if r.get(k) is not None:
                    row[k] = r[k]
            st.ext.append(row)
            ours[sid] = row
            row["seat"] = st.seat_rule(r, of[sid], ours)
            lr.pop("why", None)
            lr.pop("by", None)
            lr.update({"status": "placed", "as": row["id"], "cluster": of[sid]})
            log(f"draft pieces {st.place_id}: {sid} ({(st.bases.get(r['base']) or {}).get('edid')}) is placed again")
        elif sid in drop and sid in ours:
            st.ext.remove(ours.pop(sid))
            lr.update({"status": "dropped", "why": drop[sid], "by": "draft.drop"})
            lr.pop("as", None)
            lr.pop("base", None)
    # every standing piece on the base the step gives it
    for sid, row in sorted(ours.items()):
        r = st.by_src.get(sid)
        if r is None or r.get("kind") == "actor":
            continue
        rep = replace.get(r["base"])
        want = rep["base"] if rep else r["base"]
        if row["base"] == want:
            continue
        cid = row.get("cluster") or of.get(sid)
        was = row["base"]
        x, y, rot = st.stand(r, cid)
        row.pop("align", None)
        row["base"], row["pos"], row["rot"] = r["base"], [x, y, row["pos"][2]], rot
        row["seat"] = st.seat_rule(r, cid, ours)
        if rep:
            xf_turn, at = st.turn(cid), (x, y)

            def outside(r=r, at=at, turn=xf_turn):
                o = src_outside(st.src, r)
                c, s = math.cos(turn), math.sin(turn)
                dx, dy = o[0] - r["pos"][0], o[1] - r["pos"][1]
                return at[0] + dx * c + dy * s, at[1] - dx * s + dy * c
            replace_piece(row, r, rep, st.bases, outside)
        lr = led.get(sid)
        if lr is not None:
            lr.pop("base", None)
            if rep:
                lr.update({"status": "replaced", "base": rep["base"]})
            elif lr["status"] == "replaced":
                lr["status"] = "placed"
        log(f"draft pieces {st.place_id}: {row['id']} ({row.get('kind')}) {was} -> {row['base']}")
    # the copied rooms: each override on the base the step gives it; a room's piece once removed stands again
    for sid, sp in sorted(st.files["spaces"].items()):
        info = sp.get("space") or {}
        if sid == "exterior" or not info.get("copy_of"):
            continue
        src_sp = st.src.spaces.get(info["copy_of"].split("/", 1)[1])
        by_id = {r["id"]: r for r in (src_sp.refs if src_sp else [])}
        keep = []
        for row in sp["refs"]:
            r = by_id.get(row.get("src"))
            if r is None:
                keep.append(row)
                continue
            rep = replace.get(r["base"])
            door = interiors.door_target(r)
            if row.get("removed"):
                if door:            # another room's way out: the room rule's, not this step's
                    keep.append(row)
                else:
                    log(f"draft pieces {st.place_id}: {sid}/{r['id']} stands again")
                    _unledger(st, r["id"], sid)
                continue
            want = rep["base"] if rep else r["base"]
            if row.get("base") == want:
                keep.append(row)
                continue
            log(f"draft pieces {st.place_id}: {sid}/{r['id']} {row.get('base')} -> {want}")
            row.pop("align", None)
            row.update({"base": r["base"], "pos": list(r["pos"]), "rot": list(r.get("rot") or [0, 0, 0])})
            if rep:
                row.update(interiors.swap(r, st.bases, rep))
            else:
                _unledger(st, r["id"], sid)
            if rep or door:         # a door's row carries its pairing: kept, on the source's own piece
                keep.append(row)
        sp["refs"] = keep
    seat_all(st.ext, st.G)


def _unledger(st: Standing, src_id: str, copy_id: str) -> None:
    st.ledger[:] = [lr for lr in st.ledger if not (lr.get("src") == src_id and lr.get("copy") == copy_id)]


def seating_stage(st: Standing, log=print) -> None:
    from tools.places.draft import walk
    _, of, _ = st.clusters
    ours = st.ours()
    for sid, row in sorted(ours.items()):
        r = st.by_src.get(sid)
        if r is None or sid not in of or row.get("base") != r.get("base") or row.get("primitive"):
            continue    # a replaced piece keeps the seat its replacement was given; a collision box, its piece's
        rule = st.seat_rule(r, row.get("cluster") or of[sid], ours)
        if rule != row.get("seat"):
            row["seat"] = rule
    walk.flush_steps(st.ext, st.bases, log=lambda *_: None)
    seat_all(st.ext, st.G)


def clearance(st: Standing, log=print) -> None:
    from tools.places.draft import clear as clearmod
    from tools.places.draft.cluster import VEG
    measure = st.place.get("clearance")
    if not measure:
        raise StageError("place.json holds no clearance measure: the whole draft measures it from the source")
    world = [r for r in (st.grd.exterior.refs if st.grd.exterior else []) if r.get("layer", "world") == "world"]
    paths = st.files["paths"]
    doors = [tuple(r["door"]["arrival"][:2]) for r in st.ext if (r.get("door") or {}).get("arrival")]
    doors += [tuple(p["points"][k][:2]) for p in paths for k in (0, -1) if p.get("points")]
    buildings = [r for r in st.ext if r.get("kind") == "building"]
    feet = [r for r in st.ext if geom.foot(r, st.bases) and (r.get("kind") not in VEG or r.get("kind") in geom.SOLID_KINDS)]
    rows = clearmod.apply(world, measure, buildings, st.bases, paths, doors, feet)
    got = {r.get("ref") for r in rows}
    rows += clearmod.along(world, measure, [p for p in paths if "re-laid" in str(p.get("laid"))], got)
    from tools.places.draft import bodies
    solid = bodies.load(st.bases)
    if solid is None:
        log(f"draft clearance {st.place_id}: no world land is built here: the world's things are cleared by their roots alone")
    else:
        rows += clearmod.across(world, {r.get("ref") for r in rows}, paths, doors, solid)
    # a plant already cleared keeps its row as it stands (the reason first given); the stage owns which plants go.
    # A row is that plant's only while the world still has it there: a re-scattered world reuses its refs' ids
    was = {r.get("ref"): r for r in st.files["clear"] if r.get("by") == "draft"}

    def kept(r: dict) -> dict:
        o = was.get(r.get("ref"))
        same = o is not None and o.get("base") == r.get("base") and math.dist(o["pos"], r["pos"]) <= 1.0
        return o if same else r
    st.files["clear"] = [r for r in st.files["clear"] if r.get("by") != "draft"] + [kept(r) for r in rows]


def streets(place_id: str, places: Path, log=print) -> None:
    from tools.places.draft import walk
    walk.join(place_id, places, log=log)


def people_stage(st: Standing, log=print) -> None:
    from tools.places import identities
    from tools.places.draft import people
    from tools.places.draft.run import place_record
    who = identities.read(st.place_id, st.pdir.parent)
    hist = next(iter(((st.place.get("stations") or {}).get("found") or {}).get("shrine") or []), None)
    gives = place_record(st.place_id)[1]
    routes = people.routes_of(st.place_id)
    changed = people.refresh_services(st.files["people"], gives, routes)
    if changed:
        log(f"draft people {st.place_id}: services re-read from the record for {', '.join(changed)}")
    people.give_to_residents(st.files["people"], gives, who, hist, routes)
    people.apply_identities(st.files["people"], who)


def lights_stage(st: Standing, log=print) -> None:
    rec = st.place.get("lights") or {}
    want = lights.station_lights(st.place_id, st.ext, st.place.get("stations"))
    have = {r["id"]: r for r in st.ext}
    for old in rec.get("added") or []:
        if old["id"] in have and old["id"] not in {r["id"] for r in want}:
            st.ext.remove(have[old["id"]])
    for r in want:
        if r["id"] in have:
            have[r["id"]].update({k: r[k] for k in ("base", "pos", "seat")})
        else:
            st.ext.append(r)
            log(f"draft lights {st.place_id}: {r['why']} at {[round(v) for v in r['pos']]}")
    for sid, sp in sorted(st.files["spaces"].items()):
        info = sp.get("space") or {}
        src_sp = st.src.spaces.get(info["copy_of"].split("/", 1)[1]) if sid != "exterior" and info.get("copy_of") else None
        if src_sp is None:
            continue
        sp["refs"], back, gone = interiors.own_lights(src_sp.refs, sp["refs"])
        if back or gone:
            log(f"draft lights {st.place_id}: room {sid}: {back + gone} lights back on the source's own base")
    st.place["lights"] = {"added": [{"id": r["id"], "base": r["base"], "on": r["seat"]["on"]} for r in want]}
    st.bases.update({k: b for k, b in lights.light_bases().items() if k in {r["base"] for r in want}})
    seat_all(st.ext, st.G)


def stations(st: Standing, log=print) -> None:
    from tools.places.draft import people
    from tools.places.draft import run as R
    gives = R.place_record(st.place_id)[1]
    need = sorted({g["give_kind_id"] for g in gives if g["give_kind_id"] in people.STATIONS})
    stn = st.place.setdefault("stations", {})
    every = {r["id"] for sp in st.files["spaces"].values() for r in sp["refs"]}
    found = {k: [i for i in v if i in every] for k, v in (stn.get("found") or {}).items()}
    added = [a for a in stn.get("added") or [] if a["id"] in every]
    folk = st.files["people"]
    for kind in sorted(need, key=lambda x: (x != "forge", x)):
        if found.get(kind):
            continue
        same = next((o for o in need if o != kind and found.get(o)
                     and io.STATION_KEYWORD.get(o) == io.STATION_KEYWORD.get(kind) and io.STATION_KEYWORD.get(o)), None)
        if same:
            found[kind] = list(found[same])
            continue
        role = people.STATION_OWNER.get(kind)
        owner = next((p for p in folk if p["role"] == role), None) or next((p for p in folk if p["role"] != "guard"), None)
        b = io.station_base(kind)
        if owner is None or b is None:
            continue
        st.bases[b["key"]] = b
        w = owner["work"]
        k = sum(1 for a in added if a["by"] == owner["id"])
        if w.get("space", "exterior") == "exterior":
            c = w.get("pos") or next(r["pos"] for r in st.ext if r["id"] == w.get("ref"))
            row = R.yard_place(st.place_id, kind, b, st.bases, st.ext, st.files["paths"], st.G, c, found, owner, added)
            if row is None:
                continue
            st.ext.append(row)
            space = "exterior"
            if kind == "forge":
                w.pop("pos", None)
                w["ref"] = row["id"]
        else:
            space = w["space"]
            sp = st.files["spaces"][space]
            info = sp["space"]
            src_refs = st.src.spaces[info["copy_of"].split("/", 1)[1]].refs
            beds = interiors.beds_in(src_refs, st.bases, info.get("room"), info["copy_of"])
            anchor = {b_["ref"] for b_ in beds} or {info.get("room")}
            pts = [r["pos"] for r in src_refs if r["id"] in anchor] or [src_refs[0]["pos"]]
            into = next(((r.get("door") or {}).get("to_pos") for s2 in st.files["spaces"].values() for r in s2["refs"]
                         if r["id"] == info.get("door_from")), None)
            row = R.room_station(st.place_id, kind, b, st.bases, src_refs, sp["refs"], pts, into, k, owner)
            sp["refs"].append(row)
        added.append({"station": kind, "id": row["id"], "base": b["key"], "space": space, "by": owner["id"]})
        found.setdefault(kind, []).append(row["id"])
        log(f"draft stations {st.place_id}: {kind} added in {space} for {owner['id']}")
    stn.update({"needed": sorted(set(need) | ({"shrine"} if "shrine" in (stn.get("needed") or []) else set())),
                "found": {**(stn.get("found") or {}), **found}, "added": added,
                "missing": [s for s in need if not found.get(s)]
                + [s for s in (stn.get("missing") or []) if s == "shrine"]})
    seat_all(st.ext, st.G)


def jail_stage(st: Standing, log=print) -> None:
    from tools.places.draft import jail
    jail.apply(st, log)


def primitives_stage(st: Standing, log=print) -> None:
    from tools.places.draft import primitives
    primitives.apply(st, log)


def hang_stage(st: Standing, log=print) -> None:
    from tools.places.draft import hang
    hang.apply(st, log)


def add_stage(st: Standing, log=print) -> None:
    from tools.places.draft import adds
    adds.apply(st, log)


def names_stage(st: Standing, log=print) -> None:
    from tools.places.draft import names
    names.apply(st, log)


RUN = {"fit": fit, "pieces": pieces, "seating": seating_stage, "clearance": clearance, "people": people_stage,
       "lights": lights_stage, "stations": stations, "jail": jail_stage, "primitives": primitives_stage,
       "hang": hang_stage, "add": add_stage, "names": names_stage}


# --- the run: snapshot, stage, proof of ownership, counts ---
def snapshot(pdir: Path) -> dict[str, str]:
    return {str(p.relative_to(pdir)): p.read_text(encoding="utf-8") for p in sorted(pdir.rglob("*"))
            if p.is_file() and p.suffix in (".json", ".jsonl") and "edits" not in p.relative_to(pdir).parts
            and p.name != BUILT}


def restore(pdir: Path, snap: dict[str, str]) -> None:
    for rel in set(snapshot(pdir)) - set(snap):
        (pdir / rel).unlink()
    for rel, text in snap.items():
        p = pdir / rel
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")


def _rows(rel: str, text: str) -> dict:
    if rel.endswith(".json"):
        return json.loads(text) if text.strip() else {}
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = r.get("id") or r.get("ref") or (f"{r.get('space')}|{r.get('src')}|{r.get('copy')}" if "status" in r else None) or line
        out[key] = r
    return out


def owner_rows(pdir: Path) -> set[str]:
    """The ids of the rows the owner's finalised studio saves touched."""
    ids = set()
    for p in sorted((pdir / "edits").glob("*.json")) if (pdir / "edits").exists() else []:
        save = json.loads(p.read_text(encoding="utf-8"))
        if save.get("final"):
            ids |= {op["id"] for op in save.get("ops") or [] if op.get("id")}
    return ids


def owner_saves(pdir: Path) -> list[str]:
    """The owner's finalised studio saves of a place (edits/*.json with `final`)."""
    out = []
    for p in sorted((pdir / "edits").glob("*.json")) if (pdir / "edits").exists() else []:
        if json.loads(p.read_text(encoding="utf-8")).get("final"):
            out.append(p.stem)
    return out


def diff(before: dict[str, str], after: dict[str, str], owns: dict | None = None) -> tuple[dict, list[str]]:
    """({file: {changed, added, removed}} for the files that differ, [what was written outside `owns`])."""
    import fnmatch
    counts, bad = {}, []
    for rel in sorted(set(before) | set(after)):
        a, b = before.get(rel, ""), after.get(rel, "")
        if a == b:
            continue
        ra, rb = _rows(rel, a), _rows(rel, b)
        ch = sorted(k for k in ra if k in rb and ra[k] != rb[k])
        ad, rm = sorted(set(rb) - set(ra)), sorted(set(ra) - set(rb))
        counts[rel] = {"changed": len(ch), "added": len(ad), "removed": len(rm)}
        if owns is None:
            continue
        rule = next((v for pat, v in owns.items() if fnmatch.fnmatch(rel, pat)), None)
        if rule is None:
            bad.append(f"{rel}: not a file this stage owns")
            continue
        fields, adds = rule
        if (ad or rm) and not adds and not (rel.endswith(".json") and fields is not ANY):
            bad.append(f"{rel}: rows added or removed ({(ad + rm)[:3]})")
        if rel.endswith(".json"):
            touched = set(ch) | set(ad) | set(rm)
            if fields is not ANY and not touched <= fields:
                bad.append(f"{rel}: keys {sorted(touched - fields)} are not this stage's")
            continue
        if fields is not ANY:
            for k in ch:
                off = {f for f in set(ra[k]) | set(rb[k]) if ra[k].get(f) != rb[k].get(f)} - fields
                if off:
                    bad.append(f"{rel}: row {k}: fields {sorted(off)} are not this stage's")
    return counts, bad


def run(stage: str, place_id: str, places: Path = io.PLACES, bundles: Path = io.BUNDLES, log=print) -> dict:
    """Run one stage on the standing files of a place. Returns {file: {changed, added, removed}}."""
    if stage not in OWNS:
        raise StageError(f"no stage {stage}: one of {', '.join(STAGES)}")
    pdir = places / place_id
    before = snapshot(pdir)
    try:
        if stage == "streets":
            streets(place_id, places, log)
        else:
            st = Standing(place_id, places, bundles)
            was = {sid: {r["id"]: copy.deepcopy(r) for r in sp["refs"]} for sid, sp in st.files["spaces"].items()}
            RUN[stage](st, log)
            mine = owner_rows(pdir)
            for sid, sp in st.files["spaces"].items():      # the owner's rows stand as the owner left them
                for i, r in enumerate(sp["refs"]):
                    if r["id"] in mine and r["id"] in was.get(sid, {}) and r != was[sid][r["id"]]:
                        sp["refs"][i] = was[sid][r["id"]]
                        log(f"draft {stage} {place_id}: {r['id']} is the owner's (a finalised save): kept as it stands")
            st.write()
    except Exception:
        restore(pdir, before)
        raise
    counts, bad = diff(before, snapshot(pdir), OWNS[stage])
    if bad:
        restore(pdir, before)
        raise StageError(f"draft {stage} {place_id} wrote outside what it owns; nothing is changed: " + "; ".join(bad[:8]))
    return counts
