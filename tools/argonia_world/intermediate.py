"""Intermediate JSON writers (0.4 §a): the records Argonia.esm holds, resolved to the last FormKey and unit,
for ArgoniaGen to write with Mutagen. Nothing downstream makes a choice.

Layers by record id (old 0140): every record belongs to a layer (``base``, ``place:<id>``, ``population:<id>``,
``quest:<id>``, ``patch:<id>``), and records are identified by EditorID (ours) or FormKey (an override of a
master's record). ``compose`` lays the layers over each other in kind order; a later layer may add records or
set fields on an earlier layer's record, two layers of the same kind may not set the same field. Regenerating
the base never drops a layer, because each layer is generated from its own rows and composed afresh.

    python3 -m tools.argonia_world.intermediate --data <Skyrim Data dir> [--out out/intermediate/argonia.json]
        [--scan out/vanilla-scan.json] [--index out/pieces-index.json] [--frozen 1: allocate nothing]
"""
from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator
from tools.argonia_world.pieces import Index, Resolver

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "intermediate" / "argonia.json"
QUARANTINE = ROOT / "data" / "quarantine"
KIND_ORDER = ("base", "place", "population", "quest", "patch")
TYPE_ORDER = ("GLOB", "MUSC", "STAT", "CLAS", "SPEL", "LVLI", "QUST", "CELL")


@dataclass
class Layer:
    name: str  # kind:id
    records: list[dict] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return self.name.split(":", 1)[0]


def record_id(r: dict) -> str:
    return r.get("edid") if not r.get("override") else r["formKey"]


def compose(layers: list[Layer], masters: list[str] = ()) -> list[dict]:
    """The layers' records merged by record id, in kind order; a same-kind clash on a field is an error."""
    for lay in layers:
        if lay.kind not in KIND_ORDER:
            raise ValueError(f"layer {lay.name}: kind must be one of {KIND_ORDER}")
    out: dict[str, dict] = {}
    owner: dict[tuple[str, str], str] = {}  # (record id, field) -> layer that set it
    for lay in sorted(layers, key=lambda x: (KIND_ORDER.index(x.kind), x.name)):
        for rec in lay.records:
            rid = record_id(rec)
            cur = out.setdefault(rid, {})
            for k, v in rec.items():
                prev = owner.get((rid, k))
                if prev and prev != lay.name and prev.split(":")[0] == lay.kind and cur.get(k) != v:
                    raise ValueError(f"{rid}.{k}: set by both {prev} and {lay.name}")
                cur[k] = copy.deepcopy(v)
                owner[(rid, k)] = lay.name
            cur.setdefault("layer", lay.name)
    # Within a type, the order of the raw FormID the ESM stores (master index, then object id): the canonical
    # order the round-trip check also puts Spriggit's output in.
    rank = {m.lower(): i for i, m in enumerate(masters)}

    def raw(fk: str) -> tuple[int, int]:
        oid, mod = fk.split(":")
        return rank.get(mod.lower(), len(rank)), int(oid, 16)
    return sorted(out.values(), key=lambda r: (TYPE_ORDER.index(r["type"]), raw(r["formKey"])))


# Imported and authored positions run x east, y SOUTH (old 0003; measured by 2.W1 on the route-grade profiles),
# z up, in metres; Skyrim's y runs north. A straight metres_to_units on y mirrored every layout north-south.
def _pos_exterior(at_m) -> list[float]:
    """A province position (metres from the NW corner, y south) as worldspace units: through the grid."""
    x, y = su.province_to_skyrim(at_m[0], at_m[1])
    return [su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(at_m[2]), 2)]


def _pos_interior(at_m) -> list[float]:
    """An interior position (metres from the cell's origin, y south) as cell units: y negated, no grid."""
    x, y, z = at_m
    return [su.rounded(su.metres_to_units(x), 2), su.rounded(-su.metres_to_units(y), 2),
            su.rounded(su.metres_to_units(z), 2)]


def _rot(yaw) -> list[float]:
    return [su.rounded(v, 6) for v in su.yaw_to_rot(yaw)]


# --- the quarantine (0.4 §b, decision 0012) ---------------------------------------------------------------
def quarantine_layers(alloc: Allocator, scan: dict, resolver: Resolver) -> list[Layer]:
    start = json.loads((QUARANTINE / "start.json").read_text(encoding="utf-8"))
    allowed = json.loads((QUARANTINE / "allowed-quests.json").read_text(encoding="utf-8"))
    fk = alloc.form_key
    q, cell = start["quest"], start["cell"]
    never = start["never"]
    records: list[dict] = [
        {"type": "GLOB", "edid": never["edid"], "formKey": fk(never["edid"], "GLOB"), "value": never["value"]},
        {"type": "MUSC", "edid": start["music"]["edid"], "formKey": fk(start["music"]["edid"], "MUSC"), "flags": []},
    ]
    m, fl = cell["marker"], cell["floor"]
    floor = resolver.resolve(fl["piece"])
    if len(floor) != 1 or floor[0].kind == "unresolved":
        raise ValueError(f"holding-cell floor {fl['piece']}: {floor[0].why if floor else 'no member'}")
    floor_base = floor[0].form_key
    if floor[0].kind == "new-stat":
        floor_base = fk(floor[0].edid, "STAT", floor[0].mesh)
        records.append({"type": "STAT", "edid": floor[0].edid, "formKey": floor_base, "model": floor[0].mesh})
    records.append({
        "type": "CELL", "edid": cell["edid"], "formKey": fk(cell["edid"], "CELL"),
        "flags": ["IsInteriorCell", "CantTravelFromHere"], "music": fk(start["music"]["edid"]),
        "lighting": cell["lighting"],
        "refs": [
            {"edid": m["edid"], "formKey": fk(m["edid"], "REFR"), "base": su.ENGINE_MARKER_HEADING,
             "pos": _pos_interior(m["atM"]), "rot": _rot(m["yaw"]), "persistent": True},
            {"edid": fl["edid"], "formKey": fk(fl["edid"], "REFR"), "base": floor_base,
             "pos": _pos_interior(fl["atM"]), "rot": _rot(fl["yaw"])},
        ],
    })
    records.append({
        "type": "QUST", "edid": q["edid"], "formKey": fk(q["edid"], "QUST"),
        "flags": ["StartGameEnabled", "RunOnce"], "priority": q["priority"],
        "stages": [{"index": 0}, {"index": 10}],
        "scripts": [{"name": q["script"], "properties": [{"name": "HoldingMarker", "object": fk(m["edid"])}]}],
    })
    starter = Layer("quest:start", records)

    keep = {k["edid"] for k in allowed["keepVanilla"]}
    never_cond = [{"function": "GetGlobalValue", "global": fk(never["edid"]), "op": "EqualTo", "value": 1}]
    shells: dict[str, dict] = {}
    for row in scan["quests"] + allowed["prevent"]:
        if row["edid"] in keep:
            continue
        # The inert shell: the master's id and EditorID only, no flags, stages, aliases or scripts, and an event
        # condition that is never true, so neither the new game nor the story manager can start it.
        shells[row["formKey"]] = {"type": "QUST", "override": True, "edid": row["edid"], "formKey": row["formKey"],
                                  "flags": [], "eventConditions": never_cond}
    for row in scan["musicTypes"]:
        shells[row["formKey"]] = {"type": "MUSC", "override": True, "edid": row["edid"], "formKey": row["formKey"],
                                  "flags": row["flags"]}  # no tracks: vanilla music never plays
    return [starter, Layer("patch:quarantine", list(shells.values()))]


# --- the studio character's sheet records (0.4 §a; 2.1 fills the rest) ------------------------------------
def sheet_layer(alloc: Allocator, world, studio: dict) -> Layer:
    """One race package, class and birthsign from the world's sheet tables. Their meaning (attributes, skill
    bonuses, effects) is ArgoniaCore's; these records give each a stable Skyrim identity the scenes and the
    co-save name. No player-visible text: the sheet's screens are ours."""
    race, cls, sign = studio["race"], studio["class"], studio["birthsign"]
    if world.get("race", race) is None or world.get("class", cls) is None or world.get("birthsign", sign) is None:
        raise ValueError(f"studio sheet {studio}: a race, class or birthsign is not in the world database")
    weights = dict.fromkeys(su.SKYRIM_SKILLS, 0)
    majors = [r.value for r in world.rows("class_majors", class_id=cls)]
    for table, w in (("class_majors", su.CLAS_WEIGHT_MAJOR), ("class_minors", su.CLAS_WEIGHT_MINOR)):
        for r in world.rows(table, class_id=cls):
            if su.SKILL_AV.get(r.value):
                weights[su.SKILL_AV[r.value]] += w
    teaches = next((su.SKILL_AV[m] for m in majors if su.SKILL_AV.get(m)), "OneHanded")

    def ability(edid, key):
        return {"type": "SPEL", "edid": edid, "formKey": alloc.form_key(edid, "SPEL", key),
                "spellType": "Ability", "castType": "ConstantEffect", "targetType": "Self", "flags": []}
    slug = {k: v.replace("-", "_") for k, v in studio.items()}
    edid_c = f"ARG_Class_{slug['class']}"
    return Layer("base:sheet", [
        {"type": "CLAS", "edid": edid_c, "formKey": alloc.form_key(edid_c, "CLAS", f"class.{cls}"),
         "teaches": teaches, "maxTrainingLevel": su.CLAS_MAX_TRAINING, "skillWeights": weights,
         "statWeights": {"Health": 1, "Magicka": 1, "Stamina": 1}},
        ability(f"ARG_Race_{slug['race']}", f"race.{race}"),
        ability(f"ARG_Sign_{slug['birthsign']}", f"birthsign.{sign}"),
    ])


# --- the load order --------------------------------------------------------------------------------------
def load_order(data: Path) -> list[str]:
    """The runtime's masters present in Data, then its Creation Club masters, then the dependency plugins."""
    present = {p.name.lower(): p.name for p in Path(data).iterdir() if p.suffix.lower() in (".esm", ".esp", ".esl")}
    order = [m for m in su.OFFICIAL_MASTERS if m.lower() in present]
    ccc = Path(data).parent / "Skyrim.ccc"
    if ccc.exists():
        order += [present[n.strip().lower()] for n in ccc.read_text().splitlines() if n.strip().lower() in present]
    deps = ROOT / "data" / "dependencies.json"
    if deps.exists():
        doc = json.loads(deps.read_text(encoding="utf-8"))
        for d in doc.get("plugins", []) if isinstance(doc, dict) else []:
            name = d["file"] if isinstance(d, dict) else d
            if name.lower() in present and present[name.lower()] not in order:
                order.append(present[name.lower()])
    return order


def build(data: Path, scan: dict, index: Index, alloc: Allocator, extra: list[Layer] = ()) -> dict:
    resolver = Resolver(index)
    studio = json.loads((QUARANTINE / "start.json").read_text(encoding="utf-8"))["studio"]
    layers = quarantine_layers(alloc, scan, resolver) + [sheet_layer(alloc, alloc.world, studio)] + list(extra)
    order = load_order(data)
    return {
        "schema": 1,
        "mod": "Argonia.esm",
        "author": "Elder Souls: Argonia",
        "description": "Generated by tools/argonia_world and tools/ArgoniaGen; never hand-edited (decision 0009).",
        "loadOrder": order,
        "records": compose(layers, order),
    }


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[0::2], argv[1::2]))
    if "--data" not in opts:
        print(__doc__)
        return 2
    data = Path(opts["--data"]).expanduser()
    out = Path(opts.get("--out", OUT))
    scan = json.loads(Path(opts.get("--scan", ROOT / "out" / "vanilla-scan.json")).read_text(encoding="utf-8"))
    alloc = Allocator(frozen=opts.get("--frozen") == "1")
    doc = build(data, scan, Index.load(Path(opts.get("--index", ROOT / "out" / "pieces-index.json"))), alloc)
    alloc.save()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps(doc), encoding="utf-8")
    print(f"intermediate: {len(doc['records'])} records -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
