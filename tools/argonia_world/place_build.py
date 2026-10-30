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
  away from the host piece's centre; interior: toward the cell's centre of references).
- **People.** Per `build_person`: an NPC_ templated on a vanilla NPC_ (Traits: face, body, voice; a creature also
  takes its stats, attacks, AI data, spells and inventory), the speaker keyword for people, Unique, no Respawn
  flag (a killed one stays dead), and one package per `npc_day_block` row: `work:N` sandboxes around the reference
  realising the person's N-th work socket (else their post), `home` sleeps at their bed (the reference realising
  their home socket that they own). A creature sandboxes around its den all day: its territory is the radius.
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
CREATURE_TEMPLATE_FLAGS = ["Traits", "Stats", "Factions", "SpellList", "AIData", "Inventory", "Script", "AttackData"]


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
    if kind == "exterior":  # out from the building: away from the nearest non-door piece of the same cell
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


def _people(ctx, world, refs) -> None:
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
                                    p.sandbox_radius_m, start, span)
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
        if creature:  # its den is the reference realising its home socket (LF83: the cut), else where it stands
            den = next((r for r in refs if r.thing_id == "thing.lf83.clay-bend"), actor) if p.npc_id.endswith("crocodile") else actor
            pk = packages.sandbox(ctx.alloc, f"{edid}_Den", f"{p.npc_id}#den", ref_form_key(ctx.alloc, den), p.sandbox_radius_m, 0, 24)
            ctx.records[pk["edid"]] = pk
            pkgs.append(pk["formKey"])
        rec = {"type": "NPC_", "edid": edid, "formKey": ctx.alloc.form_key(edid, "NPC_", p.npc_id), "name": npc.name,
               "race": p.race_form_key, "template": p.template_form_key,
               "templateFlags": CREATURE_TEMPLATE_FLAGS if creature else PEOPLE_TEMPLATE_FLAGS,
               "class": _studio_class(ctx.alloc), "female": npc.sex == "female", "level": 1, "healthOffset": 0,
               "aggression": "Unaggressive", "confidence": "Average", "height": su.NPC_DEFAULT_HEIGHT,
               "weight": su.NPC_DEFAULT_WEIGHT, "perks": [], "items": [], "packages": pkgs,
               "flags": [] if creature else ["Unique"]}
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
        _people(ctx, world, refs)
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
    return list(ctx.records.values()) + out


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


def layers(alloc, world, resolver, wrld_form_key: str) -> list:
    from tools.argonia_world.intermediate import Layer
    from tools.argonia_world.routes.build import Ground
    places = sorted({c.place_id for c in world.rows("build_cell")})
    if not places:
        return []
    ground = Ground()
    return [Layer(f"place:{p.rsplit('.', 1)[1]}", place_records(alloc, world, resolver, ground, wrld_form_key, p))
            for p in places]


def built_places(world) -> list[str]:
    return sorted({c.place_id for c in world.rows("build_cell")})
