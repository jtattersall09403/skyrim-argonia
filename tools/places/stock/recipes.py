"""Smithing recipes for the items ladder (docs/design/items.md, section Smithing): a forge and a tempering recipe for
every weapon and armour piece of item_material, shaped as Skyrim's own (decision 0034) and made of our materials.

    python3 -m tools.newworld.stockdb recipes      # write newworld/sources/stock/recipes.json (generated)
    recipes.check(doc, wares, goods_made)          # every piece has both, or a reason; every ingredient obtainable

`generate` reads newworld/sources/stock/recipe_rules.json (authored), item_material.json and every plugin's COBJ
records: it measures, from Skyrim's own forge recipes, how many of the main material and of leather strips each
weapon type and armour slot takes and which perk each Skyrim material keyword asks for; keeps a mod's recipe whose
every ingredient is one of ours; and writes the rest from our material's ingredients.
"""
from __future__ import annotations

import json
import statistics
import struct
from collections import Counter, defaultdict

from tools.places.stock import split

STOCK = split.STOCK
VANILLA = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
HAS_PERK = 448          # the CTDA function index of HasPerk


def read_cobj(plugins: list[str]) -> tuple[list[dict], dict[str, str]]:
    """Every COBJ of the plugins: {key, plugin, out, bench, ings: [(key, n)], perks: [key]}, and editor ids by key."""
    from tools.argonia_world import esm
    from tools.places.extract import find_plugin, search_dirs
    from tools.places.stock.records import place_key
    dirs = search_dirs()
    edid, out = {}, []
    for name in plugins:
        p = esm.Plugin.read(find_plugin(name, dirs), {"COBJ", "KYWD", "PERK", "MISC", "INGR", "WEAP", "ARMO"})
        for r in p.records():
            k = place_key(r.key)
            edid[k] = r.edid

            def ref(d, off=0, r=r):
                v = struct.unpack_from("<I", d, off)[0] if d and len(d) >= off + 4 else 0
                return place_key(r.plugin.form_key(v)) if v else None
            if r.sig == "COBJ":
                out.append({"key": k, "plugin": name, "out": ref(r.sub("CNAM")), "bench": ref(r.sub("BNAM")),
                            "ings": [(ref(d), struct.unpack_from("<i", d, 4)[0]) for d in r.all("CNTO")],
                            "perks": [ref(c, 12) for c in r.all("CTDA") if len(c) >= 16
                                      and struct.unpack_from("<H", c, 8)[0] == HAS_PERK]})
    return out, edid


def generate() -> dict:
    from tools.places.stock.records import Records
    rules = json.loads((STOCK / "recipe_rules.json").read_text(encoding="utf-8"))
    gear = split.item_materials()["gear"]
    wares = split.item_materials()["wares"]
    plugins = VANILLA + sorted({k.rsplit(":", 1)[0] for k in gear} - set(VANILLA))
    cobj, edid = read_cobj(plugins)
    rec = Records.load(plugins)
    by_edid = {e: k for k, e in edid.items() if e}
    st = rules["stations"]
    forge, wheel, table = (by_edid[st[x]] for x in ("forge", "temper_weapon", "temper_armour"))
    binding = rules["binding"]["item"]

    # Skyrim's own shape (vanilla forge recipes of vanilla items): main count and strips per kind; perk per keyword
    mains, strips, perks = defaultdict(list), defaultdict(list), defaultdict(Counter)
    for c in cobj:
        if c["plugin"] not in VANILLA or c["bench"] != forge or not c["out"]:
            continue
        it = rec.item(c["out"])
        if it is None or it["ench"]:
            continue
        kind = split.power_kind(it)
        mat = next((k for k in it["keywords"] if "Material" in k), None)
        if mat:
            perks[mat][tuple(sorted(edid.get(p) or p for p in c["perks"]))] += 1
        if kind:
            n = [m for k, m in c["ings"] if k != binding]
            mains[kind].append(max(n) if n else 1)
            strips[kind].append(sum(m for k, m in c["ings"] if k == binding))
    shape = {k: {"main": max(1, round(statistics.median(mains[k]))), "binding": round(statistics.median(strips[k]))}
             for k in mains}
    perk_of = {kw: list(c.most_common(1)[0][0]) for kw, c in perks.items()}

    ours = {binding} | {v for m in rules["materials"].values() for k, v in m.items() if k in ("main", "second")} \
        | set(rules["temper_main"].values()) | set(wares)
    mod = defaultdict(dict)
    for c in cobj:
        if c["out"] in gear and c["bench"] in (forge, wheel, table):
            mod[c["out"]]["forge" if c["bench"] == forge else "temper"] = c
    temper_only = set(rules["temper_only"]["materials"])
    out = []
    for key, row in sorted(gear.items()):
        it = rec.item(key)
        if it is None or row.get("races"):       # clothing is cut and sewn, never forged or tempered
            continue
        mid, kind, slot = row["material"], split.power_kind(it), split.slot_of(it)
        tier = split.item_tier(it)[0]
        pw = split.materials()["materials"][mid]["power"]["weapon" if slot == "weapon" else "armour"]
        perk = perk_of.get(pw, [])
        for kind_ in ("forge", "temper"):
            station = forge if kind_ == "forge" else (wheel if it["sig"] == "WEAP" else table)
            if kind_ == "forge" and (mid in temper_only or tier == rules["temper_only"]["tier"]):
                out.append({"item": key, "kind": "forge", "station": None, "perk": [], "ingredients": [],
                            "source": "none", "why": f"{mid} {tier}: {rules['temper_only']['why']}"})
                continue
            have = mod[key].get(kind_)
            if have and have["ings"] and rules["keep_when_ours"] and all(k in ours for k, _ in have["ings"]) and \
                    (kind_ == "temper" or [edid.get(p) for p in have["perks"]] in (perk, [])):
                out.append({"item": key, "kind": kind_, "station": edid[station], "perk": [edid.get(p) for p in have["perks"]],
                            "ingredients": have["ings"], "source": f"kept:{have['key']}",
                            "why": f"the mod's own recipe ({edid.get(have['key'])}): every ingredient is one of ours"})
                continue
            m = rules["materials"].get(mid) or {"main": rules["temper_main"].get(mid)}
            if kind_ == "temper":
                ings = [(m["main"] or rules["temper_main"].get(mid), 1)]
                why = f"tempered with {mid}'s main ingredient, as Skyrim tempers with one of its material"
            else:
                sh = shape.get(kind, {"main": 1, "binding": 1})
                ings = [(m["main"], sh["main"])] + ([(m["second"], 1)] if m.get("second") else []) + \
                    ([(binding, sh["binding"])] if sh["binding"] else [])
                why = (f"Skyrim's {kind or 'piece'} shape ({sh['main']} main, {sh['binding']} strips) in {mid}: "
                       f"{m.get('why', '')}; perk of {pw or 'no keyword'}")
            out.append({"item": key, "kind": kind_, "station": edid[station], "perk": perk if kind_ == "forge" else [],
                        "ingredients": ings, "source": "overrides:" + have["key"] if have else "generated", "why": why})
    return {"about": "Generated by `python3 -m tools.newworld.stockdb recipes` from recipe_rules.json, item_material.json "
                     "and the plugins' COBJ records (tools/places/stock/recipes.py). Do not edit.",
            "shape": shape, "perks": perk_of, "new_items": rules["new_items"], "recipes": out,
            "audit": {"mod_recipes": sum(len(v) for v in mod.values()),
                      "kept": sum(r["source"].startswith("kept") for r in out),
                      "overridden": sum(r["source"].startswith("overrides") for r in out)}}


def check(doc: dict, wares: dict, made: set[str]) -> list[str]:
    """Every gear item of item_material has a forge recipe (or a reason it has none) and a tempering recipe; every
    ingredient is a ware whose good some region or place makes, or a new item of ours."""
    bad = []
    have = defaultdict(dict)
    for r in doc["recipes"]:
        have[r["item"]][r["kind"]] = r
    new = {f"new:{n['edid']}" for n in doc.get("new_items", [])}
    for key, row in split.item_materials()["gear"].items():
        if row.get("races"):                      # clothing has no forge or tempering recipe
            continue
        h = have.get(key, {})
        if "temper" not in h or not h["temper"]["ingredients"]:
            bad.append(f"{key}: no tempering recipe")
        f = h.get("forge")
        if f is None or (not f["ingredients"] and not f["why"]):
            bad.append(f"{key}: no forge recipe and no reason")
    for r in doc["recipes"]:
        for k, _n in r["ingredients"]:
            if k in new:
                continue
            g = (wares.get(k) or {}).get("good")
            if g is None:
                bad.append(f"{r['item']} {r['kind']}: ingredient {k} is no ware (item_good): nobody makes or sells it")
            elif g not in made:
                bad.append(f"{r['item']} {r['kind']}: ingredient {k}'s good {g} is made by no region or place")
    return sorted(set(bad))
