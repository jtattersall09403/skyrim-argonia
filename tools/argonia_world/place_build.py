"""The built places (0.4 §d; decisions 0026 §3, 0031 §2): a place's `build_cell`, `build_ref` and `build_person` rows
as the records of Argonia.esm, one layer per place (`place:<slug>`).

- **Cells.** The exterior: one CELL override per ArgoniaWorld.esm cell the place's references stand in (the master's
  CELL copied by ArgoniaGen's PlaceCells.cs; persistent references go to the worldspace's persistent cell). A
  borrowed interior: a CELL override of the master's cell with the displayed name ours, carrying our references and
  the overrides of its own (relinked doors, disabled residents). An own interior: a CELL of ours.
- **References.** A `piece` resolves through pieces.py (a base record of the masters, else a new STAT of ours); a
  `base` is a FormKey of a master or the EditorID of a record of ours. Exterior positions go through the province
  grid (`intermediate._pos_exterior`, z on the 2.W1 ground when the row gives none); interior ones through
  `_pos_interior`. Load doors teleport to a point 1.2 m in front of their partner (exterior: out from the building,
  away from the door's building, `<b>` for `<b>-door`, else the nearest piece; interior: toward the cell's centre of references).
- **People.** Per `build_person`: an NPC_ templated on a vanilla NPC_ (Traits: face, body, voice; a creature also
  takes its stats, attacks, AI data, spells and inventory), the speaker keyword for people, Unique, no Respawn
  flag (a killed one stays dead), and one package per `npc_day_block` row: `work:N` sandboxes around the reference
  realising the person's N-th work socket (else their post), `home` sleeps at their bed (the reference realising
  their home socket that they own). A creature sandboxes around its den all day (the marker it owns, else where it
  stands): its territory is the radius.
- **Things.** The LF83 activators (ACTI) and the quest items (MISC from `item` rows, the ledger's BOOK from its
  document) that the place's references place; `thing_id` rows fill quest aliases (quest_gen.py reads `placed`).

Every unit conversion is skyrim_units'; ArgoniaGen makes no choices.
"""
from __future__ import annotations

import math
import re

from tools.argonia_world import skyrim_units as su

FK_RE = re.compile(r"^[0-9A-F]{6}:.+\.(esm|esp|esl)$", re.I)
DOOR_ARRIVAL_M = 1.2  # how far in front of a partner door the teleport lands
# LF83's activators (quest.local.lf83 things; their activation hooks are 1.4's ArgoniaCore runtime)
ACTIVATORS = {
    "ARG_ACTI_LF83WellHead": ("Well Head", "dungeons/mines/clutter/genericwell01.nif"),
    "ARG_ACTI_LF83MortarTub": ("Mortar Tub", "clutter/bucket01.nif"),
}
PEOPLE_TEMPLATE_FLAGS = ["Traits"]
# A Traits-only template gives face, body and voice; AI data, packages, inventory and outfit are the record's own, so a
# person carries what a vanilla townsperson does (lane npc-ai, vs Skyrim.esm's TreasCorpseCommoner* and Bendt):
# stats auto-calculated from class and level, AIDT energy 50 (0 is Mutagen's default, not a vanilla value), no crime.
PEOPLE_AI = {"aggression": "Unaggressive", "confidence": "Average", "energy": 50, "responsibility": "NoCrime",
             "mood": "Neutral", "assistance": "HelpsNobody", "soundLevel": "Normal"}
# AIData is not templated: a creature template can carry no aggro radius (EncCrocodileBlackMarsh01 has behaviour off and
# Warn/WarnOrAttack/Attack 0, so the crocodile detected the player and never fought). The creature's own AI is below.
CREATURE_TEMPLATE_FLAGS = ["Traits", "Stats", "Factions", "SpellList", "Inventory", "Script", "AttackData"]
# Vanilla predators' AIDT (EncWolf, EncBear, EncSabreCat): VeryAggressive, Foolhardy, aggro radius on, WarnOrAttack 2000,
# Attack 1500. These are vanilla's own numbers in game units, not metres, so no conversion is involved.
CREATURE_AGGRO = {"behavior": True, "warn": 0, "warnOrAttack": 2000, "attack": 1500}
CREATURE_AI = {"aggression": "VeryAggressive", "confidence": "Foolhardy", "energy": 50, "aggro": CREATURE_AGGRO}
# A settlement's crime faction (lane w3-infra): the settlement faction seated at the place (place_faction_presence role
# 'seat'), crime tracked, hidden from the player; its crime values are the Owing of the place's region in gold
# (owing_region rates). Escape and werewolf have no Owing rate yet (2.10), so they are 0. Every person of the place is
# a member (rank 0) and has it as their crime faction, as a vanilla townsperson has their hold's.
TOWN_FACTION_FLAGS = ["TrackCrime", "HiddenFromPC"]


def slug(s: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[^0-9A-Za-z]+", s) if p)


def npc_edid(npc_id: str) -> str:
    return "ARG_Npc_" + slug(npc_id.rsplit(".", 1)[1])


def ref_edid(ref_id: str) -> str:
    return ("ARG_Ref_" + slug(ref_id.split(".", 1)[1]))[:su.EDITOR_ID_MAX]


def hours(hhmm: str) -> float:
    h, m = hhmm.split(":")
    return int(h) + int(m) / 60


def placed(world) -> dict[str, str]:
    """thing or person id -> the build_ref id that places it (persistent), for quest aliases."""
    return {r.thing_id: r.id for r in world.rows("build_ref") if r.thing_id}


def ref_form_key(alloc, r) -> str:
    if r.host_ref_form_key:
        return r.host_ref_form_key
    return alloc.form_key(ref_edid(r.id), "ACHR" if r.npc_id else "REFR", r.id)


class _Ctx:
    def __init__(self, alloc, world, resolver, ground):
        self.alloc, self.world, self.resolver, self.ground = alloc, world, resolver, ground
        self.records: dict[str, dict] = {}  # base records of ours this layer adds, by EditorID

    def ours(self, edid: str) -> str:
        if edid in self.records:
            return self.records[edid]["formKey"]
        row = self.world.get("formid", edid)
        if row is None:
            raise ValueError(f"build_ref base {edid}: no record of ours by that EditorID")
        return f"{row.form_id:06X}:{row.plugin}"

    def base(self, r) -> str:
        if r.piece:
            res = self.resolver.resolve(r.piece)
            if len(res) != 1 or res[0].kind == "unresolved":
                raise ValueError(f"{r.id}: piece {r.piece} does not resolve ({res[0].why if res else 'composite'})")
            x = res[0]
            if x.kind == "base":
                return x.form_key
            fk = self.alloc.form_key(x.edid, "STAT", x.mesh)
            self.records.setdefault(x.edid, {"type": "STAT", "edid": x.edid, "formKey": fk, "model": x.mesh[len("meshes/"):]})
            return fk
        return r.base if FK_RE.match(r.base) else self.ours(r.base)


def _pos(ctx, cell_kind: str, r) -> list[float]:
    from tools.argonia_world.intermediate import _pos_exterior, _pos_interior
    if cell_kind == "exterior":
        z = r.z_m if r.z_m is not None else ctx.ground.z(r.x_m, r.y_m)
        return _pos_exterior([r.x_m, r.y_m, z])
    return _pos_interior([r.x_m, r.y_m, r.z_m or 0.0])


def _arrival(ctx, refs_by_id, cells, partner) -> tuple[list[float], list[float]]:
    """A point DOOR_ARRIVAL_M in front of the partner door, facing away from it."""
    from tools.argonia_world.intermediate import _rot
    kind = cells[partner.cell_id].kind
    if kind == "exterior":  # out from the building: away from the door's own building (`<b>-door` -> `<b>`, a
        # piece or a base), else from the nearest non-door piece of the same cell
        h = refs_by_id.get(partner.id.removesuffix("-door"))
        if h is None or h.id == partner.id or h.cell_id != partner.cell_id:
            hosts = [o for o in refs_by_id.values() if o.cell_id == partner.cell_id and o.piece and o.id != partner.id
                     and "door" not in o.id]
            h = min(hosts, key=lambda o: (o.x_m - partner.x_m) ** 2 + (o.y_m - partner.y_m) ** 2)
        dx, dy = partner.x_m - h.x_m, partner.y_m - h.y_m
    else:  # into the room: toward the centre of the cell's references
        own = [o for o in refs_by_id.values() if o.cell_id == partner.cell_id and o.id != partner.id]
        dx = sum(o.x_m for o in own) / len(own) - partner.x_m
        dy = sum(o.y_m for o in own) / len(own) - partner.y_m
    n = math.hypot(dx, dy) or 1.0
    x, y = partner.x_m + DOOR_ARRIVAL_M * dx / n, partner.y_m + DOOR_ARRIVAL_M * dy / n
    z = partner.z_m
    yaw = math.degrees(math.atan2(dx, -dy)) % 360  # province frame: y south, yaw clockwise from north
    p = type("P", (), {"x_m": x, "y_m": y, "z_m": z})
    return _pos(ctx, kind, p), _rot(yaw)


def _ref_record(ctx, r, cells, refs_by_id) -> dict:
    from tools.argonia_world.intermediate import _rot
    kind = cells[r.cell_id].kind
    rec = {"formKey": ref_form_key(ctx.alloc, r), "base": ctx.base(r), "pos": _pos(ctx, kind, r), "rot": _rot(r.yaw_deg)}
    if r.persistent and not r.host_ref_form_key:
        rec["edid"] = ref_edid(r.id)
    if r.persistent:
        rec["persistent"] = True
    if r.scale:
        rec["scale"] = r.scale
    if r.npc_id or r.actor:
        rec["actor"] = True
    if r.disabled:
        rec["disabled"] = True
    if r.owner_npc_id:
        rec["owner"] = ctx.alloc.form_key(npc_edid(r.owner_npc_id), "NPC_", r.owner_npc_id)
    if r.door_to:
        partner = refs_by_id[r.door_to]
        pos, rot = _arrival(ctx, refs_by_id, cells, partner)
        rec["teleport"] = {"door": ref_form_key(ctx.alloc, partner), "pos": pos, "rot": rot}
    return rec


def _items(ctx, world, refs) -> None:
    from tools.argonia_world import items_records as ir
    for r in refs:
        b = r.base or ""
        if b.startswith("ARG_Misc_") and b not in ctx.records:
            item = next(i for i in world.rows("item") if b == "ARG_Misc_" + slug(i.id[len("item."):]))
            ctx.records[b] = {"type": "MISC", "edid": b, "formKey": ctx.alloc.form_key(b, "MISC", item.id), "name": item.name,
                              "model": ir.model_path(item), "value": int(item.value or 0),
                              "weight": su.kg_to_weight(item.weight_kg or 0)}
        elif b.startswith("ARG_Book_") and b not in ctx.records:
            doc = next(d for d in world.rows("document") if d.item and b == "ARG_Book_" + ir.slug(d.item[len("item."):]))
            rec = ir.book_record(ctx.alloc, world, doc.id)
            ctx.records[rec["edid"]] = rec
        elif b in ACTIVATORS and b not in ctx.records:
            name, model = ACTIVATORS[b]
            ctx.records[b] = {"type": "ACTI", "edid": b, "formKey": ctx.alloc.form_key(b, "ACTI", r.thing_id), "name": name,
                              "model": model.replace("/", "\\")}


def town_faction(ctx, world, place_id: str) -> str | None:
    """The FormKey of the place's crime faction (its FACT added to the layer), or None if no settlement sits there."""
    f = next(iter(world.query("SELECT f.id, f.name FROM place_faction_presence s JOIN faction f ON f.id = s.faction_ref "
                              "WHERE s.place_id = ? AND s.role = 'seat' AND f.kind = 'settlement' ORDER BY s.ord",
                              place_id)), None)
    if f is None:
        return None
    edid = "ARG_Faction_" + slug(f["id"].split(".", 1)[1])
    rec = {"type": "FACT", "edid": edid, "formKey": ctx.alloc.form_key(edid, "FACT", f["id"]), "name": f["name"],
           "flags": TOWN_FACTION_FLAGS, "ranks": [{"number": 0, "title": "Resident"}]}
    o = next(iter(world.query("SELECT * FROM owing_region WHERE region = ?", world.get("place", place_id).region)), None)
    if o is None:
        raise ValueError(f"{place_id}: no Owing for its region, so its crime faction has no crime values")
    rec["crime"] = {"arrest": True, "attackOnSight": True, "murder": o["rates_murder"], "assault": o["rates_assault"],
                    "trespass": o["rates_trespass"], "pickpocket": o["rates_pickpocket"],
                    "stealMult": float(o["rates_theft_per_value"]), "escape": 0, "werewolf": 0}
    ctx.records[edid] = rec
    return rec["formKey"]


def _people(ctx, world, refs, cells, crime: str | None = None) -> None:
    from tools.argonia_world import packages
    from tools.argonia_world.combat_records import _studio_class
    from tools.argonia_world.hooks_records import SPEAKER_EDID
    by_socket: dict[str, list] = {}
    for r in refs:
        if r.socket_id:
            by_socket.setdefault(r.socket_id, []).append(r)
    for p in world.rows("build_person"):
        actor = next((r for r in refs if r.npc_id == p.npc_id), None)
        if actor is None:  # placed by another place
            continue
        npc = world.get("npc", p.npc_id)
        edid = npc_edid(p.npc_id)
        pkgs = []
        creature = npc.kind == "creature"
        blocks = world.rows("npc_day_block", npc_id=p.npc_id) if not creature else []
        for b in sorted(blocks, key=lambda x: x.ord):
            start, end = hours(b.from_), hours(b.to)
            span = (end - start) % 24
            if b.spot == "home":
                bed = next((r for r in by_socket.get(npc.home_home_socket_id, []) if r.owner_npc_id == p.npc_id), None)
                if bed is None:
                    raise ValueError(f"{p.npc_id}: no bed of theirs realises {npc.home_home_socket_id}")
                pk = packages.sleep(ctx.alloc, f"{edid}_Sleep", f"{p.npc_id}#sleep", ref_form_key(ctx.alloc, bed),
                                    p.sandbox_radius_m, start, span, cell_form_key=_interior_key(ctx.alloc, cells.get(bed.cell_id)))
            else:
                n = int(b.spot.split(":")[1])
                work = [w.socket_id for w in world.rows("npc_work", npc_id=p.npc_id) if w.ord == n]
                cand = [r for s in work + [npc.home_post] for r in by_socket.get(s, []) if not r.npc_id]
                if not cand:
                    raise ValueError(f"{p.npc_id}: no reference realises {work} or their post {npc.home_post}")
                pk = packages.sandbox(ctx.alloc, f"{edid}_Day{n}", f"{p.npc_id}#{b.spot}", ref_form_key(ctx.alloc, cand[0]),
                                      p.sandbox_radius_m, start, span)
            ctx.records[pk["edid"]] = pk
            pkgs.append(pk["formKey"])
        if creature:  # its den is the marker it owns (Claywater's crocodile: on the bank by LF83's pool), else where it stands
            den = next((r for r in refs if r.owner_npc_id == p.npc_id and not r.npc_id), actor)
            pk = packages.sandbox(ctx.alloc, f"{edid}_Den", f"{p.npc_id}#den", ref_form_key(ctx.alloc, den), p.sandbox_radius_m, 0, 24)
            ctx.records[pk["edid"]] = pk
            pkgs.append(pk["formKey"])
        rec = {"type": "NPC_", "edid": edid, "formKey": ctx.alloc.form_key(edid, "NPC_", p.npc_id), "name": npc.name,
               "race": p.race_form_key, "template": p.template_form_key,
               "templateFlags": CREATURE_TEMPLATE_FLAGS if creature else PEOPLE_TEMPLATE_FLAGS,
               "class": _studio_class(ctx.alloc), "female": npc.sex == "female", "level": 1, "healthOffset": 0,
               "aggression": "Unaggressive", "confidence": "Average", "height": su.NPC_DEFAULT_HEIGHT,
               "weight": su.NPC_DEFAULT_WEIGHT, "perks": [], "items": [], "packages": pkgs,
               "flags": [] if creature else ["Unique", "AutoCalcStats"]}
        if creature:
            rec.update(CREATURE_AI)
        else:
            rec.update(PEOPLE_AI)
            if crime:
                rec.update(factions=[{"faction": crime, "rank": 0}], crimeFaction=crime)
            if p.outfit_form_key:
                rec["outfit"] = p.outfit_form_key
        if p.respawn:
            rec["flags"].append("Respawn")
        if p.speaker:
            rec["keywords"] = [ctx.alloc.form_key(SPEAKER_EDID, "KYWD", "hook.speaker")]
        ctx.records[edid] = rec


def place_records(alloc, world, resolver, ground, wrld_form_key: str, place_id: str) -> list[dict]:
    cells = {c.id: c for c in world.rows("build_cell", place_id=place_id)}
    refs = sorted((r for r in world.rows("build_ref") if r.cell_id in cells), key=lambda r: r.id)
    by_id = {r.id: r for r in world.rows("build_ref")}
    ctx = _Ctx(alloc, world, resolver, ground)
    _items(ctx, world, refs)
    if any(r.npc_id for r in refs):
        _people(ctx, world, refs, cells, town_faction(ctx, world, place_id))
    out: list[dict] = []
    ext_cells: dict[tuple[int, int], list[dict]] = {}
    for cid, c in sorted(cells.items()):
        recs = [_ref_record(ctx, r, cells, by_id) for r in refs if r.cell_id == cid]
        if c.kind == "exterior":
            for rec in recs:
                ext_cells.setdefault(su.cell_of(rec["pos"][0], rec["pos"][1]), []).append(rec)
        elif c.kind == "borrowed":
            out.append({"type": "CELL", "override": True, "edid": f"ARG_Cell_{slug(cid.split('.', 1)[1])}_Host",
                        "formKey": c.host_form_key, "name": c.name, "refs": recs})
        else:
            out.append({"type": "CELL", "edid": c.edid, "formKey": alloc.form_key(c.edid, "CELL", cid), "name": c.name,
                        "flags": ["IsInteriorCell"], "refs": recs})
    if ext_cells:
        keys = _cell_keys()
        for (cx, cy), recs in sorted(ext_cells.items()):
            out.append({"type": "CELL", "override": True, "edid": f"ARG_Cell_{slug(place_id.rsplit('.', 1)[1])}_{cx}_{cy}",
                        "formKey": keys(cx, cy), "worldspace": wrld_form_key, "refs": recs})
    out = list(ctx.records.values()) + out
    check_package_targets(out)
    check_people(out)
    check_creatures(out)
    return out


def check_people(records: list[dict]) -> None:
    """L1 (lane npc-ai): every person's NPC_ (a Traits-only template, so these are the record's own) carries packages,
    AI data, a default outfit, a class, a faction and a crime faction (lane w3-infra); every PACK carries its template's data-input count (packages.py)."""
    from tools.argonia_world.packages import TEMPLATE_INPUTS
    bad = []
    for r in records:
        if r.get("type") == "NPC_" and r.get("templateFlags") == PEOPLE_TEMPLATE_FLAGS:
            missing = [k for k in ("packages", "aggression", "confidence", "energy", "outfit", "class", "factions",
                                         "crimeFaction") if not r.get(k)]
            if missing:
                bad.append(f"{r['edid']}: no {', '.join(missing)}")
        elif r.get("type") == "PACK" and r.get("inputCount") != TEMPLATE_INPUTS.get(r.get("template")):
            bad.append(f"{r['edid']}: {r.get('inputCount')} data inputs, template {r.get('template')} has "
                       f"{TEMPLATE_INPUTS.get(r.get('template'))}")
    if bad:
        raise ValueError("people records short of a vanilla NPC_'s AI fields: " + "; ".join(bad))


def check_creatures(records: list[dict]) -> None:
    """L1: a creature NPC_ (templated beyond Traits) carries its own attack radius and does not template AIData, whose
    template may hold radius 0 (the crocodile detected the player and never fought)."""
    bad = [r["edid"] for r in records if r.get("type") == "NPC_" and r.get("templateFlags") != PEOPLE_TEMPLATE_FLAGS
           and (r.get("aggro", {}).get("attack", 0) <= 0 or "AIData" in r["templateFlags"])]
    if bad:
        raise ValueError("creatures with no attack radius of their own: " + ", ".join(bad))


def _interior_key(alloc, c) -> str | None:
    """The CELL FormKey of an interior build cell (a home a sleep package can name), None outdoors."""
    if c is None or c.kind == "exterior":
        return None
    return c.host_form_key if c.kind == "borrowed" else alloc.form_key(c.edid, "CELL", c.id)


def check_package_targets(records: list[dict]) -> None:
    """Every PACK location ref is a persistent reference: ours, or an override of a master's with the Persistent
    flag set. The engine resolves a package's target while its cell is unloaded only when the ref is persistent
    (game-7: Livia's sleep package at a temporary borrowed bed gave GetCurrentAIPackage -1). A location "in cell"
    (the native sleep, game-10) names a CELL of these records holding a bed ref owned by every NPC_ that runs it."""
    persistent, cell_owners = {}, {}
    for rec in records:
        if rec.get("type") == "CELL":
            for ref in rec.get("refs", []):
                persistent[ref["formKey"]] = bool(ref.get("persistent"))
            cell_owners[rec.get("formKey")] = {ref["owner"] for ref in rec.get("refs", []) if ref.get("owner")}
    runners: dict[str, list[str]] = {}
    for rec in records:
        if rec.get("type") == "NPC_":
            for pk in rec.get("packages") or []:
                runners.setdefault(pk, []).append(rec["formKey"])
    bad = []
    for r in records:
        if r.get("type") != "PACK":
            continue
        loc = r["location"]
        if "cell" in loc:
            if loc["cell"] not in cell_owners:
                bad.append(f"{r['edid']} -> cell {loc['cell']}: not a cell of these records")
            for npc in runners.get(r["formKey"], []):
                if npc not in cell_owners.get(loc["cell"], set()):
                    bad.append(f"{r['edid']} -> cell {loc['cell']}: no ref there owned by {npc}")
        elif not persistent.get(loc["ref"], False):
            bad.append(f"{r['edid']} -> {loc['ref']}: not persistent")
    if bad:
        raise ValueError("package targets that are not persistent references of ours, or homes without the sleeper's "
                         "own bed: " + "; ".join(bad))


def _cell_keys():
    """The ArgoniaWorld.esm CELL FormKey of a grid cell (terrain/build.py's numbering over the frozen grid)."""
    import numpy as np

    from tools.argonia_world.terrain import build as tb
    from tools.argonia_world.terrain.grid import PAD, Sources, data_root
    g = np.load(data_root() / "terrain" / "refined-height-f32.npy", mmap_mode="r")
    gx0, gy0, gx1, _ = Sources(ground=g, apron=None, cover=None, tint=None, pad=PAD).cell_range
    gw, base = gx1 - gx0 + 1, su.FORMID_FIRST + 0x10

    def key(cx: int, cy: int) -> str:
        return tb.form_key(base, 2 * ((cy - gy0) * gw + (cx - gx0)), tb.LAND_PLUGIN)
    return key


class GameGround:
    """The final game ground at province metres (x east, y south): bilinear over `build.game_heights_m` with every
    layer applied (the river regrade and the place ground edits), the numbers the LAND stores, so a reference
    with no explicit z stands on the ground the player sees, not on the frozen 2.W1 array."""

    def __init__(self, src=None):
        from tools.argonia_world.terrain.grid import Sources
        self.src = src if src is not None else Sources.load()
        self._cache: dict[tuple[int, int], object] = {}

    def _block(self, br: int, bc: int):
        from tools.argonia_world.terrain import build as tb
        b = self._cache.get((br, bc))
        if b is None:  # 33 x 33 samples with a shared edge, so a bilinear 2x2 is inside
            p = self.src.pad
            b = tb.game_heights_m(self.src, p + br * 32, p + br * 32 + 33, p + bc * 32, p + bc * 32 + 33)
            self._cache[(br, bc)] = b
        return b

    def z(self, x: float, y: float) -> float:
        n = self.src.n
        c = min(max(x / su.PROVINCE_SAMPLE_M, 0), n - 1e-6)
        r = min(max(y / su.PROVINCE_SAMPLE_M, 0), n - 1e-6)
        c0, r0 = int(c), int(r)
        fc, fr = c - c0, r - r0
        h = self._block(r0 // 32, c0 // 32)
        i, j = r0 % 32, c0 % 32
        a, b, cc, d = (float(h[i, j]), float(h[i, j + 1]), float(h[i + 1, j]), float(h[i + 1, j + 1]))
        return (a * (1 - fc) + b * fc) * (1 - fr) + (cc * (1 - fc) + d * fc) * fr


def layers(alloc, world, resolver, wrld_form_key: str) -> list:
    from tools.argonia_world.intermediate import Layer
    places = sorted({c.place_id for c in world.rows("build_cell")})
    if not places:
        return []
    ground = GameGround()
    return [Layer(f"place:{p.rsplit('.', 1)[1]}", place_records(alloc, world, resolver, ground, wrld_form_key, p))
            for p in places]


def built_places(world) -> list[str]:
    return sorted({c.place_id for c in world.rows("build_cell")})
