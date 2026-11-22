"""The items ladder into the world file (docs/design/items.md, sections The ladder and Smithing): the stage `smithing`
of tools/newworld/rebuild.py.

    python -m tools.newworld.world.smithing run      # out/newworld/plugin/smithing/records.json for the writer
    python -m tools.newworld.world.smithing check    # the read-back of ArgoniaNewWorld.esm against it

`run` writes, from the stock sources (item_material.json, recipes.json, power.json, recipe_rules.json `new_items`):
- `overrides`: each ladder item whose own damage or rating differs from its tier's Skyrim base, with the base's
  damage or rating and value (split.ladder_override; weight, speed and reach stay the item's);
- `items`: every ladder item (gear of item_material), which the writer copies as ours (ForeignCopy) so the recipes and
  the places' stock name one record;
- `recipes`: every forge and tempering recipe (a forge row with no station is a relic's: none is written);
- `new_items`: the MISC records of ours an ingredient needs (ANW_Flint).
The writer (tools/ArgoniaPlugin/NewWorld.cs `Smithing`) copies each item, sets the overrides, adds the new items and one
COBJ per recipe, and writes `smithing/copies.json` (each source key -> our copy's key), which the places' build links
to and this check reads. The asset-only mods' own recipes never load (their plugins are not active), so every recipe,
kept or overriding, is written as ours and none of theirs needs switching off.

`check` proves, on the built file: every ladder item is copied; every override's damage or rating and value equal the
ladder's, and every item's power is its tier's base (the cross-check that the overrides took); every recipe is a COBJ
making that copy at the right bench, with the right perk and ingredients; nothing else of ours makes a ladder item.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from tools.places.stock import split

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "out" / "newworld" / "plugin"
STOCK = REPO / "newworld" / "sources" / "stock"
VANILLA = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]


def records() -> dict:
    from tools.places.stock.records import Records
    gear = split.item_materials()["gear"]
    rec = Records.load(VANILLA + sorted({k.rsplit(":", 1)[0] for k in gear} - set(VANILLA)))
    overrides, items = [], []
    for k in sorted(gear):
        it = rec.item(k)
        if it is None:
            continue
        items.append({"item": k, "sig": it["sig"], "tier": split.item_tier(it)[0], "edid": it["edid"]})
        o = split.ladder_override(it)
        if o:
            overrides.append({"item": k, "sig": it["sig"], "power": o["power"], "value": o["value"], "base": o["base"],
                              "was": o["was"]})
    rdoc = json.loads((STOCK / "recipes.json").read_text())
    recipes = [{"item": r["item"], "kind": r["kind"], "bench": r["station"], "perks": r["perk"],
                "ingredients": r["ingredients"]} for r in rdoc["recipes"] if r["station"]]
    rules = json.loads((STOCK / "recipe_rules.json").read_text())
    return {"items": items, "overrides": overrides, "recipes": recipes, "new_items": rules["new_items"]}


def run(out: Path = OUT) -> int:
    doc = records()
    d = out / "smithing"
    d.mkdir(parents=True, exist_ok=True)
    (d / "records.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"smithing: {len(doc['items'])} items, {len(doc['overrides'])} overrides, {len(doc['recipes'])} recipes, "
          f"{len(doc['new_items'])} new items")
    return 0


def _cobjs(esm: Path) -> tuple[dict, dict, list[dict]]:
    """(editor ids by key, items by key, COBJs) of the built file and its masters' keywords and perks."""
    from tools.argonia_world import esm as E
    from tools.places.extract import find_plugin, search_dirs
    from tools.places.stock.records import Records, place_key
    rec = Records.load(VANILLA + ["Black Marsh.esm", str(esm)])
    p = E.Plugin.read(esm, {"COBJ"})
    out = []
    for r in p.records():
        def ref(d, off=0, r=r):
            v = struct.unpack_from("<I", d, off)[0] if d and len(d) >= off + 4 else 0
            return place_key(r.plugin.form_key(v)) if v else None
        out.append({"key": place_key(r.key), "out": ref(r.sub("CNAM")), "bench": ref(r.sub("BNAM")),
                    "ings": [(ref(d), struct.unpack_from("<i", d, 4)[0]) for d in r.all("CNTO")],
                    "perks": [ref(c, 12) for c in r.all("CTDA") if len(c) >= 16 and struct.unpack_from("<H", c, 8)[0] == 448]})
    edid = {k: r.edid for k, r in rec.raw.items()}
    for name in VANILLA:
        q = E.Plugin.read(find_plugin(name, search_dirs()), {"KYWD", "PERK"})
        edid.update({place_key(r.key): r.edid for r in q.records()})
    return edid, rec, out


def check(out: Path = OUT, esm: Path | None = None) -> int:
    esm = esm or out / "ArgoniaNewWorld.esm"
    doc = json.loads((out / "smithing" / "records.json").read_text())
    copies = json.loads((out / "smithing" / "copies.json").read_text())
    edid, rec, cobjs = _cobjs(esm)
    bad = []
    ours = {}
    for it in doc["items"]:
        k = copies.get(it["item"])
        if not k or rec.item(k) is None:
            bad.append(f"{it['edid']} ({it['item']}): not copied into the world file")
            continue
        ours[it["item"]] = k
    for o in doc["overrides"]:
        got = rec.item(ours.get(o["item"], "")) or {}
        pw = got.get("damage") if o["sig"] == "WEAP" else got.get("rating")
        if pw is None or abs(float(pw) - o["power"]) > 0.01 or got.get("value") != o["value"]:
            bad.append(f"override {o['item']}: built power {pw} value {got.get('value')}, the ladder's {o['power']} {o['value']}")
    stats = split.power_table()
    for it in doc["items"]:        # the cross-check: every ladder item now has its tier's power
        got = rec.item(ours.get(it["item"], "")) or {}
        kind = split.power_kind(got) if got else None
        base = ((stats.get(kind) or {}).get("stats") or {}).get(it["tier"]) if kind else None
        pw = got.get("damage") if got.get("sig") == "WEAP" else got.get("rating")
        if base and pw is not None and abs(float(pw) - base["power"]) > 0.5:
            bad.append(f"{it['edid']}: built power {pw}, its tier {it['tier']}'s base {base['edid']} is {base['power']}")
    by_out = {}
    for c in cobjs:
        by_out.setdefault(c["out"], []).append(c)
    for r in doc["recipes"]:
        k = ours.get(r["item"])
        bench = [c for c in by_out.get(k, []) if edid.get(c["bench"]) == r["bench"]]
        if len(bench) != 1:
            bad.append(f"{r['item']} {r['kind']}: {len(bench)} COBJ(s) at {r['bench']}, want 1")
            continue
        c = bench[0]
        if sorted(edid.get(p) for p in c["perks"]) != sorted(r["perks"]):
            bad.append(f"{r['item']} {r['kind']}: perks {[edid.get(p) for p in c['perks']]}, want {r['perks']}")
        got = sorted((i, n) for i, n in c["ings"])
        want = sorted((copies.get(i, i), n) for i, n in r["ingredients"])    # a vanilla ingredient is linked as it is
        if got != want:
            bad.append(f"{r['item']} {r['kind']}: ingredients {got}, want {want}")
    for b in bad[:60]:
        print(b)
    n_c = sum(len(v) for v in by_out.values() if v and v[0]["out"] in ours.values())
    print(f"smithing check: {len(ours)}/{len(doc['items'])} items copied, {len(doc['overrides'])} overrides, "
          f"{len(doc['recipes'])} recipes ({n_c} COBJs making a ladder item); {len(bad)} problem(s)")
    (out / "smithing" / "check.json").write_text(json.dumps({"problems": bad}, indent=1) + "\n")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tools.newworld.world.smithing")
    ap.add_argument("verb", choices=("run", "check"))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--esm")
    a = ap.parse_args(argv)
    return run(Path(a.out)) if a.verb == "run" else check(Path(a.out), Path(a.esm) if a.esm else None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
