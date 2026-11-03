"""The creature records of ArgoniaWorld.esm (1.15 §g.3), the Skyrim way: what ArgoniaGen writes.

Skyrim.esm's own method (measured 2026-11-01, docs/research/2026-11-01/lane-1.15-creatures.md "The records"): a
wilderness spawn is an ACHR whose base is an NPC_ templated on an LVLN (TPLT; ACBS template flags 0x0FFF on 135 of
the 451 such NPC_, 0x1FFF on 40; RNAM the placeholder FoxRace on all 451), the LVLN flagged "calculate from all
levels <= PC" and "for each item in count" (LVLF 3 on 415 of 527), and an XEZN naming the encounter zone whose
min and max level fix what the list yields. Ours (decision 0035: nothing is levelled against the player): one LVLN
(LVLF 2, "for each item in count" only) and one templated NPC_ (the band's fixed level, CalcMin = CalcMax) per
creature_list row, every entry at level 1; a mod creature whose record scales (creature_form.pc_level_mult) or
whose death item is levelled is listed as our own copy of it at the band's fixed level (`actors`: the mod's AI,
model, sounds and spells kept, ACBS fixed, the death item swapped for a level-1 copy of its list); one ECZN per encounter_zone row with min = max (the band's fixed level, never the
player's); the den's own marker a REFR of XMarkerHeading; the predator beside it an ACHR of the mod's own NPC_.

Ids are computed, never allocated (as the grid's, 0031 §3): a list's index in roster.CLASSES x BANDS x MEDIUM,
so a class appended to the roster appends ids; a ref's id from its cell's grid position and its order in the cell.

    world.json "creatures": {"lists": [{"formKey", "edid", "entries": [[FormKey, level, count]]}],
                             "templates": [{"formKey", "edid", "list", "race", "level"}],
                             "actors": [{"formKey", "edid", "source", "level", "deathItem"}],
                             "plugins": {plugin: path}, the masters' own files (the copies' source records),
                             "zones": [{"formKey", "edid", "minLevel", "maxLevel", "neverResets"}],
                             "afflictions": [{"mgef", "spel", "kind", "name", "edid",
                                              "effects": [{"av", "archetype", "magnitude", "duration"}]}]}
    shards cy<+NNN>.jsonl.gz: {"x", "y", "refs": [[local id, "ACHR"|"REFR", base FormKey, zone FormKey|null,
                                                     x, y, z, rx, ry, rz]]}
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.creatures import roster as ro

PLUGIN = "ArgoniaWorld.esm"
LIST_BASE = 0x0D0000  # ArgoniaWorld.esm: past the rock STATs (0x0C0000), below the water (0x100000)
TEMPLATE_BASE = 0x0D1000
ZONE_BASE = 0x0D2000
REF_BASE = 0xE00000  # past the vegetation's refs (0x620000 + 126^2 x 512 = 0xDE0800)
REF_SLOT = 64  # ids per province cell; the province's busiest cell holds 9 (measured, report)
PLACEHOLDER_RACE = "109C7C:Skyrim.esm"  # FoxRace: Skyrim.esm's RNAM on every NPC_ templated on an LVLN (451 of 451)
DEN_MARKER = "000034:Skyrim.esm"  # XMarkerHeading: an editor marker, never drawn in game
ZONE_KINDS = ("wild", "clearable")
ACTOR_BASE = 0x0D4000  # our fixed-level copies of scaling mod creatures (0035): form index x bands + band
FIXED_ITEM_BASE = 0x0D6000  # our level-1 copies of levelled death-item lists (CreatureRecords.cs allocates in order)
PACK_BASE = 0x0D3F00  # our scheduled creature packages (day_package_records order)
SPELL_BASE = 0x0D3000  # our afflictions: MGEF at SPELL_BASE + 2i (a second effect's at the offset CreatureRecords.cs adds), SPEL at + 2i + 1
#                        (i: the roster.AFFLICTIONS order)

# The afflictions the mods ship as their own SPEL (read 2026-11-01 from the laid plugins: SPIT type 1 disease,
# 5 poison, or the creature's own attack spell): used as they are (route 1).
MOD_SPELLS = {
    "disease.swamp-rot": "265A22:King of the Murkmire.esp",  # DiseaseSwampRot (SPIT 1)
    "disease.swamp-fever": "265A1D:King of the Murkmire.esp",  # DiseaseSwampFever (SPIT 1)
    "poison.adder-venom": "92C99E:Here There Be Monsters - Curse of Cipactli.esp",  # mihailsnakepoisonVIPER (SPIT 5)
    "poison.centipede-numb": "000B16:King of the Murkmire.esp",  # mihailgiantcentipede_poisonspit_spell
}
# Ours where no mod ships one: Skyrim.esm's own shapes, measured 2026-11-01 (vanilla/afflictions in the report):
# a disease is SPIT 1, constant effect, contact, one PeakValueModifier (archetype 34) of 25 points (Brain Rot,
# Bone Break Fever) or a regen multiplier of 2.5 (Rattles: stamina rate); a creature poison is SPIT 5, contact, a
# ValueModifier (archetype 0) of 5 points for 5 s (crChaurusPoisonBite01). (actor value, archetype, magnitude, s)
OUR_EFFECTS = {
    "disease.blood-rot": [("StaminaRate", "PeakValueModifier", 2.5, 0)],  # as Rattles: stamina regenerates slowly
    "disease.the-droops": [("CarryWeight", "PeakValueModifier", 25.0, 0)],  # carry weight lowered
    "disease.rust-chancre": [("DamageResist", "PeakValueModifier", 25.0, 0)],  # armour lowered
    "disease.greenspore": [("Health", "PeakValueModifier", 25.0, 0)],  # as Sanguinare's: health lowered
    "poison.wasp-sting": [("Stamina", "ValueModifier", 5.0, 5)],  # damage stamina over time
    "poison.frog-breath": [("Health", "ValueModifier", 5.0, 5), ("SpeedMult", "ValueModifier", 25.0, 5)],
    "poison.voriplasm-acid": [("Health", "ValueModifier", 7.0, 7), ("DamageResist", "ValueModifier", 25.0, 7)],
}


def spell_form(aid: str) -> str:
    """The SPEL a creature's attack carries for one affliction: the mod's own, else ours."""
    if aid in MOD_SPELLS:
        return MOD_SPELLS[aid]
    return f"{SPELL_BASE + 2 * list(ro.AFFLICTIONS).index(aid) + 1:06X}:{PLUGIN}"


def afflictions() -> list[dict]:
    out = []
    for i, (aid, (kind, name, _eff, _src)) in enumerate(ro.AFFLICTIONS.items()):
        if aid in MOD_SPELLS:
            continue
        if aid not in OUR_EFFECTS:
            raise KeyError(f"{aid}: neither a mod's spell nor ours")
        out.append({"mgef": f"{SPELL_BASE + 2 * i:06X}:{PLUGIN}", "spel": spell_form(aid), "kind": kind, "name": name,
                    "edid": f"ARG_{'Dis' if kind == 'disease' else 'Poi'}{_camel(aid.split('.', 1)[1])}",
                    "effects": [{"av": av, "archetype": a, "magnitude": m, "duration": d}
                                for av, a, m, d in OUR_EFFECTS[aid]]})
    return out


def _camel(s: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in s.replace(".", "-").split("-"))


def list_index(lid: str) -> int:
    _, cls, band, medium = lid.split(".")
    return (list(ro.CLASSES).index(cls) * len(ro.BANDS) + list(ro.BANDS).index(band)) * len(ro.MEDIUM) \
        + list(ro.MEDIUM).index(medium)


def list_key(lid: str) -> str:
    return f"{LIST_BASE + list_index(lid):06X}:{PLUGIN}"


def template_key(lid: str) -> str:
    return f"{TEMPLATE_BASE + list_index(lid):06X}:{PLUGIN}"


def zone_key(zid: str) -> str:
    _, kind, band = zid.split(".")
    return f"{ZONE_BASE + ZONE_KINDS.index(kind) * len(ro.BANDS) + list(ro.BANDS).index(band):06X}:{PLUGIN}"


def ref_id(cx: int, cy: int, k: int) -> int:
    x0, y0 = su.PROVINCE_CELL_SW
    i = (cy - y0) * su.PROVINCE_CELLS + (cx - x0)
    if not (0 <= i < su.PROVINCE_CELLS ** 2) or not (0 <= k < REF_SLOT):
        raise ValueError(f"cell ({cx},{cy}) creature ref {k}: outside the reserved range")
    return REF_BASE + i * REF_SLOT + k


def masters(w) -> list[str]:
    """The plugins whose NPC_ the lists and dens name, in the stack's plugin order (planner, 2026-11-01:
    ArgoniaWorld.esm takes them as masters, as it does the rocks' plugins)."""
    deps = json.loads((Path(__file__).resolve().parents[3] / "data" / "dependencies.json").read_text(encoding="utf-8"))
    order = [p if isinstance(p, str) else p["file"] for p in deps["plugins"]]
    used = {r["p"] for r in w.query("SELECT DISTINCT substr(form_key, 8) AS p FROM creature_list_entry")}
    used |= {r["p"] for r in w.query("SELECT DISTINCT substr(form_key, 8) AS p FROM creature_form")}
    return [p for p in order if p in used] + sorted(used - set(order))


def fixed_forms(w) -> list[str]:
    """The mod forms our plugin copies per band, in form-key order: every wild form (in a list or at a den), so each
    copy carries its fixed level (0035) and its kind's day packages (owner #37, 09:23). Kept animals stay the mods'."""
    return [r["form_key"] for r in w.query("SELECT f.form_key FROM creature_form f JOIN creature c ON c.id = "
                                           "f.creature_id WHERE NOT c.domestic ORDER BY f.form_key")]


# Time of day the Skyrim way (0034, measured 2026-11-03): Skyrim.esm's wild creatures run
# EncCreatureSandboxEditorLocation512 (10F7A5), DefaultSandboxEditorLocation512 (01B217) or
# EncSlaughterfishSboxEditorLocation256 (0DA751): the Sandbox template (01C254, 12 inputs), near the editor
# location, at any hour; an hour switch exists only as a package schedule (PSDT hour + duration, as
# DefaultSleepEditorLoc24x8 01B210: 0 h for 480 min). A kind's day_rule picks its abroad windows: a sandbox of
# 512 units then, of 256 units (resting near its spawn) the rest of the day; 'any' keeps vanilla's own 10F7A5.
ANY_PACKAGE = "10F7A5:Skyrim.esm"
ABROAD = {"diurnal": [(6, 14)], "nocturnal": [(20, 10)], "crepuscular": [(4, 4), (17, 4)]}
ABROAD_UNITS, REST_UNITS = 512, 256


def _rest(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """The day's hours outside the abroad windows, as (start, hours)."""
    on = {(h + k) % 24 for h, n in windows for k in range(n)}
    out, h = [], 0
    starts = [x for x in range(24) if x not in on and (x - 1) % 24 in on]
    for st in starts:
        n = 0
        while (st + n) % 24 not in on:
            n += 1
        out.append((st, n))
    return out


def day_packages() -> tuple[list[dict], dict[str, list[str]]]:
    """(the PACK records, rule -> the package form keys an actor carries, abroad first: Skyrim runs the first
    package whose schedule holds)."""
    from tools.argonia_world import packages as pk
    recs, by = [], {"any": [ANY_PACKAGE]}
    for rule, win in ABROAD.items():
        by[rule] = []
        for kind, ws, units in (("Abroad", win, ABROAD_UNITS), ("Rest", _rest(win), REST_UNITS)):
            for i, (h, n) in enumerate(ws):
                fk = f"{PACK_BASE + len(recs):06X}:{PLUGIN}"
                recs.append({"type": "PACK", "formKey": fk, "edid": f"ARG_CrPk_{rule.title()}{kind}{i}",
                             "template": pk.SANDBOX_TEMPLATE, "inputCount": pk.TEMPLATE_INPUTS[pk.SANDBOX_TEMPLATE],
                             "flags": [], "schedule": {"hour": h, "minute": 0, "durationHours": n, "dayOfWeek": "Any"},
                             "location": {"editor": True, "radius": units}})
                by[rule].append(fk)
    return recs, by


def actor_key(w, form_key: str, band: str) -> str:
    """The NPC_ a list or den names for a mod form in a band: the mod's own, or our fixed copy."""
    fixed = fixed_forms(w)
    if form_key not in fixed:
        return form_key
    return f"{ACTOR_BASE + fixed.index(form_key) * len(ro.BANDS) + list(ro.BANDS).index(band):06X}:{PLUGIN}"


def actors(w) -> list[dict]:
    lv = {r["band"]: r["level"] for r in w.query("SELECT band, level FROM danger_band_level")}
    rule = {r["id"]: r["day_active"] for r in w.query("SELECT id, day_active FROM creature")}
    _, by = day_packages()
    day = {"always": "any", "diurnal": "diurnal", "nocturnal": "nocturnal", "crepuscular": "crepuscular"}
    fixed = set(fixed_forms(w))
    out = []
    for r in w.query("SELECT * FROM creature_form ORDER BY form_key"):
        if r["form_key"] not in fixed:
            continue
        for b in ro.BANDS:
            out.append({"formKey": actor_key(w, r["form_key"], b), "edid": f"ARG_Cr_{r['edid']}_{b}",
                        "source": r["form_key"], "level": lv[b], "deathItem": bool(r["death_item_levelled"]),
                        "packages": by[day[rule[r["creature_id"]]]]})
    return out


def plugins(w) -> dict[str, str]:
    from tools.argonia_world.creatures import levelled
    return {p: str(levelled._path(p)) for p in masters(w)}


def base_masters(w) -> list[str]:
    """The masters of the mods the lists name, in their own MAST order: our fixed death-item lists name their
    items (Skyrim.esm's, Dragonborn.esm's), so these go on the load order the writer sorts masters against."""
    from tools.argonia_world.creatures import levelled
    out: list[str] = []
    for p in masters(w):
        for m in levelled._plugin(p)[0]:
            if m not in out:
                out.append(m)
    return out


def document(w) -> dict:
    ents: dict[str, list] = {}
    band = {r["id"]: r["band"] for r in w.query("SELECT id, band FROM creature_list")}
    lv = {r["band"]: r["level"] for r in w.query("SELECT band, level FROM danger_band_level")}
    for r in w.query("SELECT list_id, form_key, level, count FROM creature_list_entry ORDER BY list_id, form_key"):
        ents.setdefault(r["list_id"], []).append([actor_key(w, r["form_key"], band[r["list_id"]]), r["level"],
                                                  r["count"]])
    lists, templates = [], []
    for r in w.query("SELECT id FROM creature_list ORDER BY id"):
        lid = r["id"]
        name = _camel(lid.split(".", 1)[1])
        lists.append({"formKey": list_key(lid), "edid": f"ARG_LCr_{name}", "entries": ents[lid]})
        templates.append({"formKey": template_key(lid), "edid": f"ARG_Enc_{name}", "list": list_key(lid),
                          "race": PLACEHOLDER_RACE, "level": lv[band[lid]]})
    zones = [{"formKey": zone_key(r["id"]), "edid": f"ARG_Zone_{_camel(r['id'].split('.', 1)[1])}",
              "minLevel": r["min_level"], "maxLevel": r["max_level"], "neverResets": bool(r["never_resets"])}
             for r in w.query("SELECT * FROM encounter_zone ORDER BY id")]
    return {"lists": lists, "templates": templates, "actors": actors(w), "plugins": plugins(w), "zones": zones,
            "afflictions": afflictions(), "packages": day_packages()[0]}


def base_of(r: dict, fixed: list[str] | None = None) -> tuple[str, str]:
    """(signature, base FormKey) of one planned ref (place.plan_cell's kinds); fixed: fixed_forms."""
    if r["kind"] == "spawn":
        return "ACHR", template_key(r["base"])
    if r["kind"] == "den":
        return "REFR", DEN_MARKER
    if fixed and r["base"] in fixed:  # the predator: the mod's own NPC_, or our fixed copy (0035)
        return "ACHR", f"{ACTOR_BASE + fixed.index(r['base']) * len(ro.BANDS) + list(ro.BANDS).index(r['band']):06X}:{PLUGIN}"
    return "ACHR", r["base"]


def write_shards(refs: list[dict], out: Path, fixed: list[str] | None = None) -> int:
    """The planner's refs as the splice's shards (one file per cell row); returns the ref count."""
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("cy*.jsonl.gz"):
        f.unlink()
    cells: dict[tuple[int, int], list] = {}
    for r in refs:
        cx, cy = r["cell"]
        row = cells.setdefault((cx, cy), [])
        sig, base = base_of(r, fixed)
        row.append([ref_id(cx, cy, len(row)), sig, base, zone_key(r["zone"]) if sig == "ACHR" else None,
                    r["x"], r["y"], r["z"], 0.0, 0.0, r["rz"]])
    rows: dict[int, list] = {}
    for (cx, cy), rr in sorted(cells.items()):
        rows.setdefault(cy, []).append({"x": cx, "y": cy, "refs": rr})
    for cy, cc in rows.items():
        with gzip.open(out / f"cy{cy:+04d}.jsonl.gz", "wt") as f:
            for c in cc:
                f.write(json.dumps(c, sort_keys=True) + "\n")
    return len(refs)


def read_cells(out: Path):
    for p in sorted(out.glob("cy*.jsonl.gz")):
        with gzip.open(p, "rt") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
