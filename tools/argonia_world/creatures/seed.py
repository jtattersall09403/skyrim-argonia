"""Write the creature data into the world database (1.15 §g.2-3) from roster.py and the mods' own records.

The mod forms are read from the laid stack (inventory.py; nothing of the mods enters git, only form keys). The
lists and zones are derived here from the rows: one list per region class, band and medium whose every entry is
at level 1 (decision 0035: the band picks the list, the player's level never gates an entry); one wild and one clearable zone per band.
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
            "domestic": d.get("domestic", False), "hand_authored_only": False, "look_model_set": None, "sourcing_status": "sourced",
            "sourcing_via": "the mods' own NPC_ (the creature_form table)", "sourcing_notes": "",
            "sourcing_redesign": None, "table_row": "docs/research/2026-11-01/lane-1.15-creatures.md#inventory"}


def derive_lists(w, lv: dict[str, int] | None = None) -> int:
    """Rewrite creature_list and creature_list_entry from the rows (1.15 round 4, owner play test 3 finding 13).

    One list per region class, band and medium, every entry at level 1 (0035). A list holds every kind of its class
    and medium whose own lowest band is at or below the list's: the prey of the quiet bands lives on in the
    dangerous ones, as Skyrim.esm's wilderness lists mix prey with predators (LCharAnimalForestPredator, 26 entries;
    list entries p50 4, p90 13). Before, a list held only the kinds that named its exact band, so a D2 land list of
    the coast was hackwing and fleshfly alone. An apex kind (creature.kind 'apex') is never in a list: it stands at
    its den (place.py's dens), rare by dens_per_100_cells (74-ecology: the big predators keep their ground).
    Returns the entries written."""
    lv = lv or band_levels(w)
    order = list(ro.BANDS)
    for t in ("creature_list", "creature_list_entry"):
        _clear(w, t)
    low = {}
    for r in w.query("SELECT creature_id, value FROM creature_band"):
        if r["value"] in order:
            low[r["creature_id"]] = min(low.get(r["creature_id"], 9), order.index(r["value"]))
    crows = {r["id"]: r for r in w.query("SELECT id, kind, hand_authored_only FROM creature")}
    med = {r["creature_id"]: r["medium"] for r in w.query("SELECT creature_id, medium FROM creature_spawn_rule")}
    forms = {}
    for r in w.query("SELECT creature_id, form_key FROM creature_form ORDER BY rowid"):
        forms.setdefault(r["creature_id"], []).append(r["form_key"])
    cls = {}
    for r in w.query("SELECT creature_id, region_class FROM creature_region_class ORDER BY rowid"):
        cls.setdefault(r["region_class"], []).append(r["creature_id"])
    n = 0
    for c in ro.CLASSES:
        for bi, b in enumerate(order):
            for m in ro.MEDIUM:
                ents = [f for cid in cls.get(c, []) if med.get(cid) == m and low.get(cid, 9) <= bi
                        and crows[cid]["kind"] != "apex" and not crows[cid]["hand_authored_only"]
                        for f in forms.get(cid, [])]
                if not ents:
                    continue
                lid = f"lvln.{c}.{b}.{m}"
                w.insert("creature_list", id=lid, region_class=c, band=b, medium=m, level=lv[b], chance_none=0)
                for f in ents:
                    w.insert("creature_list_entry", list_id=lid, form_key=f, level=1, count=1)  # 0035
                    n += 1
    return n


def domestic(w) -> int:
    """Kept animals at every lived-in settlement (owner #37: Skyrim and the mod place 5 domestic kinds in every
    settled region; ours had none): npc rows of kind creature at the settlement, each with its creature's band
    (0035: never levelled). Rewrites the rows it owns ('.domestic-'); returns the rows written."""
    w._begin()
    w.con.execute("DELETE FROM npc_statblock WHERE npc_id LIKE 'creature-at.%.domestic-%'")
    w.con.execute("DELETE FROM npc WHERE id LIKE 'creature-at.%.domestic-%'")
    w.dirty.update({"npc", "npc_statblock"})
    band = {r["creature_id"]: r["value"] for r in w.query("SELECT creature_id, value FROM creature_band WHERE ord = 0")}
    names = {r["id"]: r["name"] for r in w.query("SELECT id, name FROM creature")}
    n = 0
    q = ("SELECT id, region FROM place WHERE classification_class = 'settlement' AND status IN (%s) ORDER BY id"
         % ",".join("?" * len(ro.LIVED_IN)))
    for p in w.query(q, *ro.LIVED_IN):
        for cid, (regions, count, why, role) in ro.KEPT.items():
            if regions and p["region"] not in regions:
                continue
            for i in range(count):
                nid = f"creature-at.{p['id'].split('.', 1)[1]}.domestic-{cid.split('.')[1]}-{i + 1}"
                w.insert("npc", id=nid, kind="creature", name=names[cid], role=role, hostility="neutral",
                         home_place_id=p["id"], doom_tier="none", status="creature", notes=why, species=cid,
                         nav="large", look_model_set=cid.split(".")[1], table_row="docs/research/2026-11-03/lane-1.15-r5-creatures.md")
                w.insert("npc_statblock", npc_id=nid, **{"class": "creature"}, band=band[cid], position=0.5,
                         respawn="never", soul_trappable=True)
                n += 1
    return n


DAY_RULE = {"always": "any", "diurnal": "diurnal", "nocturnal": "nocturnal", "crepuscular": "crepuscular"}


def ground(w) -> int:
    """Fill each creature_region_class row's grounding from the rows (owner #37, 09:23): ecology from the creature's
    habitat and diet against the class, its fixed bands, the class's climatology from land_region_weather (summed
    chance per weather over the class's land regions), and its day rule from creature.day_active."""
    clim = {}
    for r in w.query("SELECT lr.eco_class_id c, wt.weather_id k, SUM(wt.chance) n FROM land_region_weather wt "
                     "JOIN land_region lr ON lr.id = wt.land_region_id GROUP BY 1, 2"):
        clim.setdefault(r["c"], []).append((r["n"], r["k"]))
    climate = {}
    for c, v in clim.items():
        tot = sum(n for n, _ in v) or 1
        climate[c] = ", ".join(f"{k} {round(100 * n / tot)}%" for n, k in sorted(v, reverse=True)[:4])
    bands = {}
    for r in w.query("SELECT creature_id, value FROM creature_band ORDER BY ord"):
        bands.setdefault(r["creature_id"], []).append(r["value"])
    cr = {r["id"]: r for r in w.query("SELECT * FROM creature")}
    n = 0
    for r in w.query("SELECT creature_id, region_class, why FROM creature_region_class"):
        c = cr[r["creature_id"]]
        eco = (f"{c['habitat_ground'] or '-'}; water: {c['habitat_water'] or '-'}; diet: {c['diet'] or '-'}; "
               f"-> {ro.CLASSES[r['region_class']]}")
        w.upsert("creature_region_class", {**dict(r), "ecology": eco, "bands": "-".join(bands.get(c["id"], [])),
                                           "climate": climate.get(r["region_class"], ""),
                                           "day_rule": DAY_RULE[c["day_active"]]})
        n += 1
    return n


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
                     aggression=f["aggression"], pc_level_mult=f["pc_level_mult"],
                     death_item_levelled=f["death_item_levelled"], why=f"{plugin}'s own {edid} ({f['race']}) stands for {crows[cid]['name']}")
            forms_of.setdefault(cid, []).append(f["form"])
        hab = f"{crows[cid]['habitat_ground']}; water: {crows[cid]['habitat_water']}"
        for c in classes:
            w.insert("creature_region_class", creature_id=cid, region_class=c,
                     why=f"{hab} -> {ro.CLASSES[c]} ({crows[cid]['table_row'] or ro.ECO})")
        added, cite = ro.WIDEN.get(cid, ((), ""))
        for c in added:
            assert c not in classes, f"{cid}: {c} is already its class"
            w.insert("creature_region_class", creature_id=cid, region_class=c,
                     why=f"round 5 (owner #37): {cite} -> {ro.CLASSES[c]}")
        mn, mx, above, slope = ro.MEDIUM[medium]
        mn = ro.DEEP.get(cid, mn)
        g0, g1 = max(1, crows[cid]["territory_group_min"]), max(1, crows[cid]["territory_group_max"])
        w.insert("creature_spawn_rule", creature_id=cid, medium=medium, min_depth_m=mn, max_depth_m=mx,
                 shore_above_m=above, max_slope_deg=slope, group_min=g0, group_max=max(g0, g1), den=den,
                 dens_per_100_cells=(1.5 if crows[cid]["kind"] == "apex" else 3.0) if den else 0.0,
                 why=f"{medium}: {hab}; den {crows[cid]['den_type']} ({crows[cid]['den_why']})")
    for cid, forms in ro.DOMESTIC.items():  # kept at settlements by npc rows; never in a wild list
        for plugin, edid in forms:
            f = keys[(plugin, edid)]
            w.insert("creature_form", form_key=f["form"], creature_id=cid, mod=plugin, edid=edid, race=f["race"],
                     aggression=f["aggression"], pc_level_mult=f["pc_level_mult"],
                     death_item_levelled=f["death_item_levelled"], why=f"{plugin}'s own {edid} ({f['race']}) stands for {crows[cid]['name']}")
    for b, k in ro.BANDS.items():
        w.insert("danger_band_level", band=b, level=lv[b], spawns_per_cell=k,
                 why="level: danger_band_combat (76 §128); spawns: Skyrim.esm wilderness refs per cell scaled by band")
    for a, (kind, name, eff, src) in ro.AFFLICTIONS.items():
        w.insert("creature_affliction", id=a, kind=kind, name=name, effect=eff, source=src)
    for b, cid, a, carrier, ch, why in ro.EFFECTS:
        w.insert("danger_band_effect", band=b, creature_id=cid, affliction_id=a, carrier=carrier, chance=ch,
                 spell_form=records.spell_form(a), why=why)
    ground(w)
    derive_lists(w, lv)
    domestic(w)
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
