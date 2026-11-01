"""Write the creature data into the world database (1.15 §g.2-3) from roster.py and the mods' own records.

The mod forms are read from the laid stack (inventory.py; nothing of the mods enters git, only form keys). The
lists and zones are derived here from the rows: one list per region class, band and medium whose every entry is
at the band's fixed level; one wild and one clearable zone per band.
"""
from __future__ import annotations

from tools.argonia_world.creatures import records, roster as ro

TABLES = ("creature", "creature_band", "creature_form", "creature_region_class", "creature_spawn_rule",
          "danger_band_level", "creature_affliction", "danger_band_effect", "creature_list", "creature_list_entry",
          "encounter_zone", "place_no_spawn")


def band_levels(w) -> dict[str, int]:
    return {r["band"]: r["level"] for r in w.query("SELECT band, level FROM danger_band_combat")}


def new_creature(cid: str, d: dict) -> dict:
    return {"id": cid, "name": d["name"], "kind": d["kind"], "status": "canon", "notes": d["notes"],
            "habitat_ground": d["ground"], "habitat_water": d["water"], "habitat_network": "both",
            "hostility": d["hostility"], "reaction_on_notice": "fight" if d["hostility"] == "hostile" else "flee",
            "reaction_note": "", "den_type": "none", "den_why": "cover", "den_note": "", "den_activity": "rest",
            "territory_radius_m": 30, "territory_network": "both", "territory_group_kind": "loose",
            "territory_group_min": d["group"][0], "territory_group_max": d["group"][1],
            "territory_per_stretch_min": 1, "territory_per_stretch_max": 3,
            "territory_per_stretch_unit": "groups per km of path or swim network in a matching band",
            "day_active": d["day"], "diet": "", "eaten_by": "", "harvest": "", "why_here": d["why"],
            "domestic": False, "hand_authored_only": False, "look_model_set": None, "sourcing_status": "sourced",
            "sourcing_via": "the mods' own NPC_ (the creature_form table)", "sourcing_notes": "",
            "sourcing_redesign": None, "table_row": "docs/research/2026-11-01/lane-1.15-creatures.md#inventory"}


def form_keys(inv: dict) -> dict[tuple[str, str], dict]:
    out = {}
    for plugin, v in inv.items():
        for f in v.get("forms", []):
            if ":" in f["form"]:
                out[(plugin, f["edid"])] = f
    return out


def _clear(w, t: str) -> None:
    """Empty a derived table (every row is rewritten from the roster)."""
    w._begin()
    w.con.execute(f'DELETE FROM "{t}"')
    w.dirty.add(t)


def seed(w, inv: dict) -> dict[str, int]:
    lv = band_levels(w)
    for cid, d in ro.NEW.items():
        w.upsert("creature", new_creature(cid, d))
        w.delete("creature_band", creature_id=cid)
        for i, b in enumerate(d["bands"]):
            w.insert("creature_band", creature_id=cid, ord=i, value=b)
    for t in TABLES[2:]:
        _clear(w, t)
    keys = form_keys(inv)
    crows = {r["id"]: r for r in w.query("SELECT * FROM creature")}
    bands = {}
    for r in w.query("SELECT creature_id, value FROM creature_band"):
        bands.setdefault(r["creature_id"], set()).add(r["value"])
    forms_of = {}
    for cid, (medium, forms, classes, den) in ro.R.items():
        for plugin, edid in forms:
            f = keys[(plugin, edid)]
            w.insert("creature_form", form_key=f["form"], creature_id=cid, mod=plugin, edid=edid, race=f["race"],
                     aggression=f["aggression"], why=f"{plugin}'s own {edid} ({f['race']}) stands for {crows[cid]['name']}")
            forms_of.setdefault(cid, []).append(f["form"])
        hab = f"{crows[cid]['habitat_ground']}; water: {crows[cid]['habitat_water']}"
        for c in classes:
            w.insert("creature_region_class", creature_id=cid, region_class=c,
                     why=f"{hab} -> {ro.CLASSES[c]} ({crows[cid]['table_row'] or ro.ECO})")
        mn, mx, above, slope = ro.MEDIUM[medium]
        mn = ro.DEEP.get(cid, mn)
        g0, g1 = max(1, crows[cid]["territory_group_min"]), max(1, crows[cid]["territory_group_max"])
        w.insert("creature_spawn_rule", creature_id=cid, medium=medium, min_depth_m=mn, max_depth_m=mx,
                 shore_above_m=above, max_slope_deg=slope, group_min=g0, group_max=max(g0, g1), den=den,
                 dens_per_100_cells=(1.5 if crows[cid]["kind"] == "apex" else 3.0) if den else 0.0,
                 why=f"{medium}: {hab}; den {crows[cid]['den_type']} ({crows[cid]['den_why']})")
    for b, k in ro.BANDS.items():
        w.insert("danger_band_level", band=b, level=lv[b], spawns_per_cell=k,
                 why="level: danger_band_combat (76 §128); spawns: Skyrim.esm wilderness refs per cell scaled by band")
    for a, (kind, name, eff, src) in ro.AFFLICTIONS.items():
        w.insert("creature_affliction", id=a, kind=kind, name=name, effect=eff, source=src)
    for b, cid, a, carrier, ch, why in ro.EFFECTS:
        w.insert("danger_band_effect", band=b, creature_id=cid, affliction_id=a, carrier=carrier, chance=ch,
                 spell_form=records.spell_form(a), why=why)
    for c in ro.CLASSES:
        for b in ro.BANDS:
            for m in ro.MEDIUM:
                ents = [f for cid, (med, _, cls, _) in ro.R.items() if med == m and c in cls and b in bands.get(cid, ())
                        and not crows[cid]["hand_authored_only"] for f in forms_of[cid]]
                if not ents:
                    continue
                lid = f"lvln.{c}.{b}.{m}"
                w.insert("creature_list", id=lid, region_class=c, band=b, medium=m, level=lv[b], chance_none=0)
                for f in ents:
                    w.insert("creature_list_entry", list_id=lid, form_key=f, level=lv[b], count=1)
    for b in ro.BANDS:
        w.insert("encounter_zone", id=f"eczn.wild.{b}", band=b, kind="wild", min_level=lv[b], max_level=lv[b],
                 never_resets=False, respawn="onRest", why="the wild resets with its cell (Skyrim: 219 of 280 ECZN reset)")
        w.insert("encounter_zone", id=f"eczn.clearable.{b}", band=b, kind="clearable", min_level=lv[b],
                 max_level=lv[b], never_resets=False, respawn="untilCleared",
                 why="resets until the place is cleared, then never (1.14 sets never-resets on clearing)")
    for k, (r, why) in ro.NO_SPAWN.items():
        w.insert("place_no_spawn", place_class=k, radius_m=r, why=why)
    w.save()
    return {t: len(w.rows(t)) for t in TABLES}
