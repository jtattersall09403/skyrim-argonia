"""Referential integrity over the world's record families (decision 0104
decision 7): every family validates against its schema, every id reference
resolves to a record of the family it names, no id is defined by two
families, and every promise is filled or excused.

    python3 -m tools.argonia_world.integrity [--world world/]
    python3 tools/argonia_world/integrity.py --world world/    # every failing rule listed, exit 1 on any
    integrity_errors(root) -> {"schema": [...], "references": [...], "duplicates": [...],
                               "promises": {place id: [...]}, "quests": [...]}

It reads the authored records only (catalogue, npc registry, travel
services, layouts, blueprints, promise ledgers, quest rows); the compiled
bundles are build outputs and are never a home table (0104 decision 1). The
quest-socket check alone reads a bundle: a socket a quest row names must be
in its place's published bundle, because a beat the shipped place lacks is
the failure (walk 11: Gang Ground missed 8 of 18 opening beats with every
gate green).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a script: python3 tools/argonia_world/integrity.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.argonia_world import schema as ws  # noqa: E402
    from tools.argonia_world.promise_gate import (  # noqa: E402
        layout_sockets as _layout_sockets, promise_gate_errors)
else:
    from . import schema as ws
    from .promise_gate import layout_sockets as _layout_sockets, promise_gate_errors

# Port notes (0.1): the old gate imported worldgen.promise_gate / travel_services /
# architecture_regions; those pieces it needs are here. Rules that read build outputs
# this repo does not hold (published settlement bundles, the kit manifests, the old
# magic package data) are skipped, and the report says so.

REGION_CLASS_NAMES = {
    "ocean", "border mountains", "upland hills", "tidal delta", "coastal lagoon & salt marsh",
    "deep river corridor", "rootland deep marsh", "interior swamp", "fringe marsh",
    "seasonal floodplain", "firm lowland", "lake & standing water", "tropical jungle",
    "mangrove forest"}

SKIPPED: list[str] = []


def _skip(why: str) -> None:
    if why not in SKIPPED:
        SKIPPED.append(why)


def operator_socket_ids(place_id, places: dict, layouts: dict | None = None) -> set[str]:
    """The socket a travel operator of ``place_id`` stands on: a placed ``npc``
    socket of the place's layout once it has one, else a catalogue
    ``sockets.post`` id (the promise, until the place is laid out)."""
    lay = (layouts or {}).get(place_id or "")
    if lay is not None:
        return {op["id"] for op in _layout_sockets(lay) if op.get("id") and op.get("kind") == "npc"}
    return set(((places.get(place_id) or {}).get("sockets") or {}).get("post") or [])


def architecture_region_errors(assets: Path) -> list[str]:
    """Every architecture row carries regionClasses from the vocabulary and a
    source; an empty list names an unsourced group that exists (standard 18)."""
    rules = json.loads((assets / "architecture-regions.json").read_text())
    groups = {g["id"] for g in rules["unsourced"]}
    for rule in rules["rules"]:
        bad = set(rule["regionClasses"]) - REGION_CLASS_NAMES
        if bad:
            return [f"rule {rule['id']}: {sorted(bad)} are not region classes"]
    out: list[str] = []
    for path in sorted(assets.glob("registry-*.jsonl")):
        for line in path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            if row["category"] != "architecture":
                continue
            rc, src = row.get("regionClasses"), row.get("regionClassesSource")
            if rc is None or not src:
                out.append(f"{row['id']}: architecture row without regionClasses and its source")
            elif set(rc) - REGION_CLASS_NAMES:
                out.append(f"{row['id']}: {sorted(set(rc) - REGION_CLASS_NAMES)} are not region classes")
            elif not rc and src.removeprefix("unsourced:") not in groups:
                out.append(f"{row['id']}: empty regionClasses with no unsourced group (register row)")
    return out


#: catalogue socket buckets (0104 decision 2: `post` is an NPC's work post)
SOCKET_BUCKETS = ("scene", "evidence", "post", "marks")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalogue(root: Path) -> dict[str, dict]:
    out = {}
    for path in sorted((root / "world/sources/catalogue").glob("places-*.json")):
        for rec in _read(path).get("places") or []:
            out[rec["id"]] = rec
    # route places (16k type 10) have no catalogue record: their home table is
    # the route-structure exemplars file (worldgen.blueprint.catalogue_ids)
    routes = root / "world/sources/routes/route-structure-exemplars.json"
    if routes.exists():
        for rec in _read(routes).get("places") or []:
            out[rec["id"]] = rec
    return out


BUNDLES = "apps/world-studio/public/province/settlements"


def hazard_reference_errors(root: Path, doc: dict, places: dict, homes: dict, npc_ids: set) -> list[str]:
    """Every hazard-volume row (2.9c) names magic that exists, slice places, and anchors that
    resolve: a socket some family defines, a creature species, a living record."""
    magic = root / "private/old-packages/magic/src/data"
    have_magic = (magic / "effects.json").exists() and (magic / "spells.json").exists()
    if not have_magic:
        _skip("hazard-volume strike effects and spells (private/old-packages/magic/src/data absent)")
    effects = {e["id"] for e in _read(magic / "effects.json").get("effects") or []} if have_magic else set()
    spells = {s["id"] for s in _read(magic / "spells.json").get("spells") or []} if have_magic else set()
    creatures_path = root / "world/sources/registries/creatures.json"
    species = {e["id"] for e in (_read(creatures_path).get("entries") or [])} if creatures_path.exists() else set()
    index = root / BUNDLES / "index.json"
    slice_ids = {p["id"] for p in _read(index).get("places") or []
                 if not p["id"].startswith("place.fixture.") and p["id"] != "place.hist-heartland.helstrom"} if index.exists() else None
    if slice_ids is None:
        _skip("hazard-volume slice-place check (no published settlement bundles)")
    # interior item sockets live in their cell's frozen fill (kit-interiors/fill/<cell>.json)
    interior = {sid for path in sorted((root / "world/sources/placement/kit-interiors/fill").glob("*.json"))
                for sid in (_read(path).get("sockets") or {})}
    out = []
    for e in doc.get("entries") or []:
        hid = e["id"]
        for fx in e.get("strikeEffects") or []:
            if have_magic and fx not in effects:
                out.append(f"{hid}: strike effect {fx!r} is not in magic effects.json")
        sid = (e.get("cast") or {}).get("spellId")
        if have_magic and sid and sid not in spells:
            out.append(f"{hid}: spell {sid!r} is not in magic spells.json")
        for pid in e.get("places") or []:
            if pid not in places:
                out.append(f"{hid}: place {pid!r} is not in the catalogue")
            elif slice_ids is not None and pid not in slice_ids:
                out.append(f"{hid}: place {pid!r} is not a slice place")
        for a in e.get("anchors") or []:
            # a socket only: a catalogue or layout socket (never a place, promise, service or npc id) or an interior cell's
            if a.get("socket") and a["socket"] not in interior and not any(
                    "socket" in fam for fam in homes.get(a["socket"], ())):
                out.append(f"{hid}: anchor socket {a['socket']!r} is no catalogue, layout or interior socket")
            if a.get("creature") and a["creature"] not in species:
                out.append(f"{hid}: anchor creature {a['creature']!r} is not in creatures.json")
            if a.get("record") and a["record"] not in npc_ids:
                out.append(f"{hid}: anchor record {a['record']!r} is not in npcs.json")
    return out


def quest_socket_errors(root: Path, placed: dict[str, set]) -> list[str]:
    """Every `sockets[]` id on a quest row (place-build step 1b, Quest beats)
    names a socket of one of the row's anchor places (`socket.<place-slug>.*`);
    once that place is laid out the id is a placed socket of its layout, and
    once it is published the id is in the bundle's compiled objects."""
    errs: list[str] = []
    bundles: dict[str, set | None] = {}
    for path in sorted((root / "world/sources/quests").glob("*.json")):
        for q in _read(path).get("quests") or []:
            anchors = {pid.split(".")[-1]: pid for pid in q.get("anchorPlaces") or []}
            for sid in q.get("sockets") or []:
                parts = sid.split(".")
                pid = anchors.get(parts[1]) if len(parts) > 2 and parts[0] == "socket" else None
                if pid is None:
                    errs.append(f"quest {q['id']}: socket {sid!r} is no socket.<slug>.* id of an "
                                f"anchor place ({', '.join(sorted(anchors.values())) or 'none'})")
                    continue
                if pid not in placed:
                    continue  # not laid out yet: the place's own build lists the beat
                if sid not in placed[pid]:
                    errs.append(f"quest {q['id']}: socket {sid!r} is not a placed socket of "
                                f"{pid}'s layout (build the beat or rewrite the quest row)")
                    continue
                if pid not in bundles:
                    bp = root / BUNDLES / f"{pid}.json"
                    # a layout `socket` op publishes under settlement.sockets
                    # (export_settlement_bundle, 0103 decision 5), a blueprint
                    # socket as a compiled object: either is published
                    doc = _read(bp) if bp.exists() else None
                    bundles[pid] = None if doc is None else (
                        {o.get("id") for o in doc.get("compiledObjects") or []}
                        | {s.get("id") for s in (doc.get("settlement") or {}).get("sockets") or []})
                if bundles[pid] is not None and sid not in bundles[pid]:
                    errs.append(f"quest {q['id']}: socket {sid!r} is in {pid}'s layout but not in "
                                f"its published bundle (republish the place)")
    return errs


def item_reference_errors(docs: dict, layouts: dict, vocab: dict | None) -> list[str]:
    """2.3a: a key and its lock name each other; every loot row, socket `item`,
    socket and door `lock`, frozen `lootTable` row and plant class resolves."""
    def entries(fam: str) -> list[dict]:
        return [e for _, doc in docs.get(fam, []) for e in doc.get("entries") or []]
    items = {e["id"]: e for e in entries("items")}
    locks = {e["id"]: e for e in entries("locks")}
    rules = {e["id"] for e in entries("loot-rules")}
    plants = {k: v for k, v in ((vocab or {}).get("plantClasses") or {}).items() if k != "_"}
    errs: list[str] = []
    if not items:  # a fixture root without the item table checks nothing here
        return errs
    for lid, lock in locks.items():
        key = lock.get("key")
        if key and key not in items:
            errs.append(f"lock {lid}: key {key!r} is no item")
        elif key and items[key].get("lock") != lid:
            errs.append(f"lock {lid}: key {key} names lock {items[key].get('lock')!r}, not this one")
    for iid, it in items.items():
        if it.get("lock") and it["lock"] not in locks:
            errs.append(f"item {iid}: lock {it['lock']!r} is no lock")
        elif it.get("lock") and locks[it["lock"]].get("key") != iid:
            errs.append(f"item {iid}: lock {it['lock']} names key {locks[it['lock']].get('key')!r}, not this one")
    for r in entries("loot-rules"):
        for row in r.get("contents") or []:
            if row["item"] not in items:
                errs.append(f"loot rule {r['id']}: item {row['item']!r} is no item")
    for cls, row in plants.items():
        if row.get("ingredient") not in items:
            errs.append(f"plant class {cls}: ingredient {row.get('ingredient')!r} is no item")
    for place_id, (_, lay) in layouts.items():
        for op in _layout_sockets(lay):
            sid = op.get("id")
            if op.get("lock") and op["lock"] not in locks:
                errs.append(f"socket {sid}: lock {op['lock']!r} is no lock")
            if op.get("item") and op["item"] not in items:
                errs.append(f"socket {sid}: item {op['item']!r} is no item")
            rule = op.get("fillRule")
            if rule and rule != "authored" and rule not in rules:
                errs.append(f"socket {sid}: fillRule {rule!r} is no loot rule")
            if op.get("kind") == "plant" and op.get("plantClass") not in plants:
                errs.append(f"socket {sid}: plantClass {op.get('plantClass')!r} is not in the vocabulary")
            for row in (op.get("lootTable") or {}).get("items") or []:
                if row.get("item") not in items:
                    errs.append(f"socket {sid}: lootTable item {row.get('item')!r} is no item")
    for _, doc in docs.get("blueprint", []):
        for door in doc["blueprint"].get("doors") or []:
            if door.get("lock") and door["lock"] not in locks:
                errs.append(f"door {door.get('id')}: lock {door['lock']!r} is no lock")
    return errs


def boat_errors(root: Path, docs: dict, layouts: dict, places: dict, services: list, npc_ids: set) -> list[str]:
    """Boats (2.15b, 0159). Every mooring socket's `accepts` names boat classes,
    its `minDepthDryM` clears the deepest accepted draught plus the class
    table's margin, its `serviceLink` is null or a travel service; every Boat's
    class resolves, its owner is null, "player", an npc or a parcel of its
    place, its moorings are real mooring sockets, and its placementUid is a
    placement of its place's published bundle."""
    errs: list[str] = []
    classes_doc = next((d for _, d in docs.get("boat-classes", [])), None)
    if classes_doc is None:
        # the table is owed only by a tree that holds boats or mooring sockets
        owed = any(d.get("boats") for _, d in docs.get("boats", [])) or any(
            op.get("kind") == "mooring" for _, lay in layouts.values() for op in _layout_sockets(lay))
        return ["boat-classes: the class table (world/sources/vocab/boat-classes.json) is missing"] if owed else []
    draught = {c["id"]: c["draughtM"] for c in classes_doc.get("classes") or []}
    margin = classes_doc.get("mooringMarginM", 0)
    service_ids = {s["id"] for s in services}
    mooring_ids: set[str] = set()
    for _, lay in layouts.values():
        for op in _layout_sockets(lay):
            if op.get("kind") != "mooring":
                continue
            sid = op.get("id")
            mooring_ids.add(sid)
            acc = op.get("accepts")
            if not isinstance(acc, list) or not acc:
                errs.append(f"mooring {sid}: accepts is missing or empty (it names the boat classes it takes)")
                acc = []
            for a in acc:
                if a not in draught:
                    errs.append(f"mooring {sid}: accepts {a!r} is no boat class")
            known = [draught[a] for a in acc if a in draught]
            need = max(known, default=0) + margin
            if known and not isinstance(op.get("minDepthDryM"), (int, float)):
                errs.append(f"mooring {sid}: minDepthDryM is missing")
            elif known and op["minDepthDryM"] + 1e-9 < need:
                errs.append(f"mooring {sid}: minDepthDryM {op['minDepthDryM']} is under the deepest "
                            f"accepted draught plus margin ({need:.2f} m)")
            if op.get("serviceLink") is not None and op["serviceLink"] not in service_ids:
                errs.append(f"mooring {sid}: serviceLink {op['serviceLink']!r} is no travel service")
    fac_path = root / "world/sources/registries/factions.json"
    # no registry, no faction owner checks out: a missing factions.json fails every faction owner, never waves it through
    faction_ids = {e["id"] for e in _read(fac_path).get("entries") or []} if fac_path.exists() else set()
    bundles: dict[str, tuple[set, set] | None] = {}
    for _, doc in docs.get("boats", []):
        for b in doc.get("boats") or []:
            bid, pid = b.get("id"), b.get("placeId")
            if b.get("classId") not in draught:
                errs.append(f"boat {bid}: classId {b.get('classId')!r} is no boat class")
            if pid not in places:
                errs.append(f"boat {bid}: placeId {pid!r} is no place")
            for f in ("lastMooring", "currentMooring"):
                if b.get(f) is not None and b[f] not in mooring_ids:
                    errs.append(f"boat {bid}: {f} {b[f]!r} is no mooring socket")
            if pid not in bundles:
                bp = root / BUNDLES / f"{pid}.json"
                if not (root / BUNDLES).is_dir():
                    _skip("boat placementUid / owner checks against published bundles (no bundles)")
                    bundles[pid] = "absent"
                elif bp.exists():
                    pls = _read(bp).get("placements") or []
                    bundles[pid] = ({p.get("id") for p in pls}, {p.get("parcelId") for p in pls if p.get("parcelId")})
                else:
                    bundles[pid] = None
            info = bundles[pid]
            if info == "absent":
                continue
            if info is None:
                errs.append(f"boat {bid}: {pid} has no published bundle to hold placementUid")
                continue
            if b.get("placementUid") not in info[0]:
                errs.append(f"boat {bid}: placementUid {b.get('placementUid')!r} is no placement of {pid}'s bundle")
            owner = b.get("owner")
            is_faction = isinstance(owner, str) and owner in faction_ids
            if owner not in (None, "player") and owner not in npc_ids and owner not in info[1] and not is_faction:
                errs.append(f"boat {bid}: owner {owner!r} is no npc, faction or parcel of {pid}")
    return errs


def integrity_errors(root: Path) -> dict:
    root = Path(root)
    ws.configure(root / "world" / "schemas")
    fams = ws.families()
    schema_errs: list[str] = []
    docs: dict[str, list[tuple[Path, dict]]] = {}
    for fam, row in fams.items():
        if not row.get("files"):
            continue
        docs[fam] = ws.load_family(fam, root)
        for path, doc in docs[fam]:
            schema_errs += [f"{path.relative_to(root)}: {e}" for e in ws.validate(fam, doc)]

    places = _catalogue(root)
    layouts = {doc["placeId"]: (path, doc) for path, doc in docs.get("layout", [])}
    ledgers = {doc["placeId"]: (path, doc) for path, doc in docs.get("promises", [])}
    blueprints = {doc["blueprint"]["id"]: (path, doc["blueprint"])
                  for path, doc in docs.get("blueprint", [])}
    services = [s for _, doc in docs.get("travel-services", []) for s in doc.get("services") or []]
    npcs_path = root / "world/sources/registries/npcs.json"
    npcs = _read(npcs_path).get("entries") or [] if npcs_path.exists() else []

    # --- homes: which family defines each id -----------------------------
    homes: dict[str, list[str]] = {}

    def define(i: str, family: str) -> None:
        homes.setdefault(i, []).append(family)

    for pid, rec in places.items():
        define(pid, "catalogue place")
        for bucket in SOCKET_BUCKETS:
            for sid in dict.fromkeys((rec.get("sockets") or {}).get(bucket) or []):
                define(sid, f"catalogue sockets.{bucket}")
    for place_id, (_, lay) in layouts.items():
        for op in _layout_sockets(lay):
            sid = op.get("id")
            # `fill.`/`yard.` ids are derived per place (sockets.py): unique within one layout only
            define(f"{place_id}:{sid}" if str(sid).startswith(("fill.", "yard.")) else sid,
                   f"layout socket ({place_id})")
    for place_id, (_, led) in ledgers.items():
        for row in led.get("promises") or []:
            define(row["id"], f"promise ledger ({place_id})")
    for s in services:
        define(s["id"], "travel service")
    for e in npcs:
        define(e["id"], "npc registry")

    # --- references resolve to the family they name ----------------------
    refs: list[str] = []
    placed = {pid: {op.get("id") for op in _layout_sockets(lay)} for pid, (_, lay) in layouts.items()}
    for s in services:
        op = s.get("operator") or {}
        npid, ref = op.get("nearestPlaceId"), op.get("socketRef")
        if npid and npid not in places:
            refs.append(f"travel service {s['id']}: operator.nearestPlaceId {npid!r} is no place")
        if ref is None:
            continue
        lays = {pid: lay for pid, (_, lay) in layouts.items()}
        if ref not in operator_socket_ids(npid, places, lays):
            refs.append(f"travel service {s['id']}: operator.socketRef {ref!r} is not a "
                        + (f"placed npc socket of {npid} (its layout is the home of its "
                           f"interactables; the catalogue `sockets.post` id is the promise only, "
                           f"0104 decision 2)" if npid in lays else f"sockets.post id of {npid}"))
    for e in npcs:
        home = e.get("home") or {}
        pid, sid = home.get("placeId"), home.get("post")
        if pid and pid not in places:
            refs.append(f"npc {e['id']}: home.placeId {pid!r} is no place")
        # a laid-out place is the home of its interactables (0104 decision
        # 2): its people stand on placed sockets only; a catalogue post id is
        # the promise, allowed only until the place is laid out
        if sid and pid in placed:
            if sid not in placed[pid]:
                refs.append(f"npc {e['id']}: home.post {sid!r} is not a placed socket of "
                            f"{pid}, which is laid out (npc_roster.slot_socket reads the layout)")
        elif sid and sid not in ((places.get(pid) or {}).get("sockets") or {}).get("post", []):
            refs.append(f"npc {e['id']}: home.post {sid!r} is not a sockets.post id of {pid}")
        # the spots (home, bed, work, a creature's den) name a placed socket of
        # the place's layout, or another place when they name no socket
        spots = [("home", home.get("home")), ("bed", home.get("bed"))]
        spots += [("work", s) for s in home.get("work") or []]
        if e.get("den"):
            spots.append(("den", e["den"]))
        for label, spot in spots:
            if not spot:
                continue
            ssid, spid = spot.get("socketId"), spot.get("placeId")
            if spid and spid not in places:
                refs.append(f"npc {e['id']}: {label} spot placeId {spid!r} is no place")
            # the socket belongs to the place the spot names, else the home;
            # an unlaid place holds only its catalogue sockets (the promise)
            target = spid or pid
            if ssid and target in placed:
                if ssid not in placed[target]:
                    refs.append(f"npc {e['id']}: {label} spot {ssid!r} is not a placed socket of {target}")
            elif ssid:
                buckets = ((places.get(target) or {}).get("sockets") or {}).values()
                if not any(isinstance(ids, list) and ssid in ids for ids in buckets):
                    refs.append(f"npc {e['id']}: {label} spot {ssid!r} is not a catalogue socket of "
                                f"{target}, which is not laid out")
            if not ssid and not spid:
                refs.append(f"npc {e['id']}: {label} spot names no socket and no other place")
    route_ids = set()
    registry = root / "world/sources/routes/registry.json"
    if registry.exists():
        route_ids = {r["id"] for r in _read(registry).get("routes") or []}
    for place_id, (path, lay) in layouts.items():
        if place_id not in places:
            refs.append(f"{path.relative_to(root)}: placeId {place_id!r} is no place")
        route_ids |= {op.get("id") for op in lay.get("ops") or [] if op.get("op") == "path"}
        ids = placed[place_id]
        for op in _layout_sockets(lay):
            for entry in op.get("schedule") or []:
                if entry.get("socketId") not in ids:
                    refs.append(f"layout socket {op['id']}: schedule socketId "
                                f"{entry.get('socketId')!r} is no socket of this layout")
    for place_id, (path, lay) in layouts.items():
        for op in _layout_sockets(lay):
            for arm in op.get("pointsTo") or []:
                if arm not in route_ids and arm not in places:
                    refs.append(f"sign socket {op['id']}: pointsTo {arm!r} is no route or place")
    for place_id, (path, led) in ledgers.items():
        if place_id not in places:
            refs.append(f"{path.relative_to(root)}: placeId {place_id!r} is no place")
        for row in led.get("promises") or []:
            if not (root / row["source"]["file"]).exists():
                refs.append(f"{row['id']}: source file {row['source']['file']} does not exist")
    for place_id in layouts:
        if place_id not in ledgers:
            refs.append(f"{place_id} has a layout and no promise ledger (run "
                        f"`blueprint_promises --id {place_id} --write`)")
    # every architecture row names its region classes, or the register row excusing it
    if (root / "world/sources/assets/architecture-regions.json").exists():
        refs += architecture_region_errors(root / "world/sources/assets")

    vocab = next((doc for _, doc in docs.get("socket-vocabulary", [])), None)
    refs += item_reference_errors(docs, layouts, vocab)
    for fam in ("items", "locks", "loot-rules", "physical-materials"):
        for _, doc in docs.get(fam, []):
            for e in doc.get("entries") or []:
                define(e["id"], fam)
    for _, doc in docs.get("hazard-volumes", []):
        for e in doc.get("entries") or []:
            define(e["id"], "hazard-volumes")
        refs += hazard_reference_errors(root, doc, places, homes, {e["id"] for e in npcs})
    for _, doc in docs.get("boats", []):
        for b in doc.get("boats") or []:
            define(b["id"], "boats")
    for _, doc in docs.get("boat-classes", []):
        for c in doc.get("classes") or []:
            define(c["id"], "boat-classes")
    refs += boat_errors(root, docs, layouts, places, services, {e["id"] for e in npcs})
    duplicates = [f"id {i!r} is defined by {len(fs)} records: {', '.join(fs)}"
                  for i, fs in sorted(homes.items()) if i and len(fs) > 1]

    # --- every promise filled or excused ----------------------------------
    promises: dict[str, list[str]] = {}
    for place_id, (_, led) in ledgers.items():
        bp = (blueprints.get(place_id) or (None, {"id": place_id}))[1]
        lay = (layouts.get(place_id) or (None, {}))[1]
        # the root's own layout, never the committed one fills_index reads by default
        promises[place_id] = promise_gate_errors(bp, led, _layout_sockets(lay), layout=lay)
    return {"schema": schema_errs, "references": refs, "duplicates": duplicates,
            "promises": promises, "quests": quest_socket_errors(root, placed)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="World referential-integrity gate (decision 0104).")
    ap.add_argument("--world", default=str(Path(__file__).resolve().parents[2] / "world"),
                    help="the world/ folder (default: this repo's)")
    args = ap.parse_args(argv)
    world = Path(args.world).resolve()
    if not (world / "schemas" / "families.json").exists():
        print(f"world integrity: {world}/schemas/families.json not found", file=sys.stderr)
        return 2
    out = integrity_errors(world.parent)
    n = 0
    for key in ("schema", "references", "duplicates", "quests"):
        for line in out[key]:
            print(f"{key}: {line}")
            n += 1
    for place_id, errs in out["promises"].items():
        for line in errs:
            print(f"promises ({place_id}): {line}")
            n += 1
    for why in SKIPPED:
        print(f"skipped: {why}")
    print(f"world integrity: {n} error(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
