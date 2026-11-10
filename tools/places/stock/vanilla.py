"""What vanilla towns yield (decision 0034): a check on our stocking scale, never its source.

    python -m tools.places stock vanilla [--out PATH]      # JSON summary (default out/places/stock/vanilla.json)

Reads Skyrim.esm with Update.esm (and the DLC masters for item records) through tools/argonia_world/esm.py and
measures, at the reference levels 1, 10 and 30 (vanilla scales its lists with the player; we take fixed levels):
- per town interior (cells whose editor id starts with a hold town's name), by the cell's kind: what its containers
  and loose things hold: gold, significant value and set-dressing value (the split's own rules);
- per container kind: count, share locked, lock levels, the same three values;
- per role (the Job faction of the people placed in those cells): gold and significant value carried;
- the level at which each weapon and armour material and each enchantment grade first appears in the LItem lists;
- the expected gold of vanilla's gold lists.
Write-up: docs/research/skyrim/stocking-yields.md.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from tools.argonia_world import esm
from tools.places.stock import split
from tools.places.stock.records import Records, place_key

REPO = Path(__file__).resolve().parents[3]
LEVELS = (1, 10, 30)
MASTERS = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
TOWNS = ("Riverwood", "Whiterun", "Ivarstead", "Solitude", "Windhelm", "Riften", "Markarth", "Falkreath", "Dawnstar",
         "Morthal", "Winterhold", "Rorikstead", "DragonBridge", "Karthwasten", "Shors")
CELL_KINDS = [  # editor id words -> the kind of building
    ("jail", r"jail|prison|dungeon|cidhna"), ("keep", r"dragonsreach|palace|keep|jarl|castle|understone|mistveil|highmoon|longhouse|chillfurrow|hall(?!ofthedead)"),
    ("temple", r"temple|hallofthedead|catacomb"), ("inn", r"inn$|inn\b|mare|giant|huntsman|bee|tavern|hearth|corner|rest|moth|dead.*drink|windpeak|frozen|bunkhouse|ragged"),
    ("barracks", r"barracks|guard|garrison|castle"), ("guild", r"jorrvaskr|guild|college|ratway|cistern|underforge|bard"),
    ("shop", r"trader|goods|cauldron|warmaiden|smith|forge|store|shop|emporium|alchemist|apothecary|fletcher|jewel|raiment|market|bits|arcane|pawned|sundries|elixir|angeline|radiant|bothela|hag"),
    ("house", r".")]
ROLES = [("jarl", "JobJarlFaction"), ("steward", "JobStewardFaction"), ("housecarl", "JobHousecarlFaction"),
         ("court-wizard", "JobCourtWizardFaction"), ("smith", "JobBlacksmithFaction"), ("merchant", "JobMerchantFaction"),
         ("innkeeper", "JobInnkeeperFaction"), ("inn-server", "JobInnServer"), ("apothecary", "JobApothecaryFaction"),
         ("priest", "JobPriestFaction"), ("bard", "JobBardFaction"), ("trainer", "JobTrainerFaction"),
         ("guard", "IsGuardFaction"), ("beggar", "FavorJobsBeggarsFaction"), ("farmer", "JobFarmerFaction")]


def ev(rec: Records, key: str, level: int, rules: dict, memo: dict) -> tuple[float, float, float]:
    """(gold, significant value, set-dressing value) a base gives on average at `level`."""
    k = (key, level)
    if k in memo:
        return memo[k]
    g = s = d = 0.0
    for item, n, ch in rec.expand(key, level):
        it = rec.item(item)
        if it is None:
            continue
        kind, sig, _ = split.item_class(it, rules)
        v = n * ch * (it["value"] or 0)
        if kind == "gold":
            g += v
        elif sig:
            s += v
        else:
            d += v
    memo[k] = (g, s, d)
    return memo[k]


def cell_kind(edid: str) -> str:
    e = edid.lower()
    for town in TOWNS:
        if e.startswith(town.lower()):
            e = e[len(town):]
            break
    return next(k for k, pat in CELL_KINDS if re.search(pat, e))


def measure(data: Path) -> dict:
    rules = split.rules()
    rec = Records.load([data / m for m in MASTERS])
    cells, refs = {}, {}
    for name in ("Skyrim.esm", "Update.esm"):
        p = esm.Plugin.read(data / name, {"CELL"})
        for r in p.records():
            if r.sig == "CELL":
                cells[place_key(r.key)] = r
            elif r.sig in ("REFR", "ACHR"):
                lbl = next((lab for gt, lab in reversed(r.parents) if gt in (6, 8, 9, 10)), None)
                if lbl is not None:
                    refs[place_key(r.key)] = (place_key(p.form_key(lbl)), r)
    town = {k: c.edid for k, c in cells.items() if c.edid and c.edid.startswith(TOWNS)}
    memo: dict = {}
    per_cell = defaultdict(lambda: {"kind": None, "containers": 0, **{f"L{l}": [0.0, 0.0, 0.0] for l in LEVELS}})
    by_cont = defaultdict(lambda: {"n": 0, "locked": 0, "locks": Counter(), "owned": 0,
                                   **{f"L{l}": [0.0, 0.0, 0.0] for l in LEVELS}})
    loose = defaultdict(lambda: {"n": 0, "value": 0.0})
    roles = defaultdict(lambda: {"n": 0, "names": [], **{f"L{l}": [0.0, 0.0, 0.0] for l in LEVELS}})
    for rk, (ck, r) in refs.items():
        if ck not in town or r.flags & 0x20:          # deleted
            continue
        base = r.ref("NAME")
        if not base:
            continue
        base = place_key(base)
        cell = per_cell[ck]
        cell["kind"] = cell_kind(town[ck])
        if r.sig == "ACHR":
            npc = rec.npc(base)
            if npc is None:
                continue
            if not npc["items"] and npc["template"] and rec.npc(npc["template"]):
                npc = {**npc, "items": rec.npc(npc["template"])["items"]}
            facs = {f["edid"] for f in npc["factions"] if f["edid"]}
            role = next((rl for rl, fac in ROLES if fac in facs), "citizen")
            ro = roles[role]
            ro["n"] += 1
            if len(ro["names"]) < 6:
                ro["names"].append(npc["edid"])
            for lv in LEVELS:
                tot = [0.0, 0.0, 0.0]
                for item, n in npc["items"]:
                    for i, x in enumerate(ev(rec, item, lv, rules, memo)):
                        tot[i] += x * n
                ro[f"L{lv}"] = [a + b for a, b in zip(ro[f"L{lv}"], tot)]
            continue
        c = rec.cont(base)
        if c is not None:
            kind, _ = split.container_kind(c, rules)
            bc = by_cont[kind]
            bc["n"] += 1
            cell["containers"] += 1
            xloc = r.sub("XLOC")
            if xloc:
                bc["locked"] += 1
                bc["locks"][xloc[0]] += 1
            if r.sub("XOWN") or cells[ck].sub("XOWN"):
                bc["owned"] += 1
            for lv in LEVELS:
                tot = [0.0, 0.0, 0.0]
                for item, n in c["items"]:
                    for i, x in enumerate(ev(rec, item, lv, rules, memo)):
                        tot[i] += x * n
                bc[f"L{lv}"] = [a + b for a, b in zip(bc[f"L{lv}"], tot)]
                cell[f"L{lv}"] = [a + b for a, b in zip(cell[f"L{lv}"], tot)]
            continue
        it = rec.item(base) if rec.sig(base) != "LVLI" else None
        if it is None and rec.sig(base) != "LVLI":
            continue
        xc = r.sub("XCNT")
        n = struct.unpack_from("<i", xc)[0] if xc else 1
        for lv in LEVELS:
            g, s, d = ev(rec, base, lv, rules, memo)
            cell[f"L{lv}"] = [a + b * n for a, b in zip(cell[f"L{lv}"], (g, s, d))]
        kind, sig, _ = split.item_class(it, rules) if it else ("levelled-list", True, "")
        lo = loose[(kind, sig)]
        lo["n"] += n
        lo["value"] += n * (it["value"] if it else ev(rec, base, 10, rules, memo)[1])

    def per(rows, n):
        return {f"L{lv}": {"gold": round(rows[f"L{lv}"][0] / n, 1), "significant": round(rows[f"L{lv}"][1] / n, 1),
                           "dressing": round(rows[f"L{lv}"][2] / n, 1)} for lv in LEVELS} if n else {}

    houses = defaultdict(list)
    for ck, c in per_cell.items():
        houses[c["kind"]].append(c)
    out = {"towns": TOWNS, "cells": len(per_cell), "levels": LEVELS,
           "per_house_kind": {k: {"n": len(v), "containers_mean": round(mean(c["containers"] for c in v), 1),
                                  **{f"L{lv}": {"gold_median": round(median(c[f"L{lv}"][0] for c in v), 1),
                                                "significant_median": round(median(c[f"L{lv}"][1] for c in v), 1),
                                                "gold_mean": round(mean(c[f"L{lv}"][0] for c in v), 1),
                                                "significant_mean": round(mean(c[f"L{lv}"][1] for c in v), 1)}
                                     for lv in LEVELS}} for k, v in sorted(houses.items())},
           "per_container_kind": {k: {"n": v["n"], "locked": v["locked"], "owned": v["owned"],
                                      "lock_levels": dict(sorted(v["locks"].items())), **per(v, v["n"])}
                                  for k, v in sorted(by_cont.items(), key=lambda kv: -kv[1]["n"])},
           "per_role": {k: {"n": v["n"], "examples": v["names"], **per(v, v["n"])}
                        for k, v in sorted(roles.items(), key=lambda kv: -kv[1]["n"])},
           "loose": {f"{k[0]}{'*' if k[1] else ''}": {"n": v["n"], "value": round(v["value"])}
                     for k, v in sorted(loose.items(), key=lambda kv: -kv[1]["value"])}}
    out["gates"] = gates(rec)
    out["gold_lists"] = {r.edid: {f"L{lv}": round(ev(rec, k, lv, rules, memo)[0], 1) for lv in LEVELS}
                         for k, r in rec.raw.items() if r.sig == "LVLI" and r.edid and re.search(r"gold", r.edid, re.I)
                         and r.plugin.name == "Skyrim.esm"}
    return out


def gates(rec: Records) -> dict:
    """The lowest list level at which each material (weapons, armour) and each enchantment grade appears in
    vanilla's LItem lists: the level gates vanilla uses."""
    lists = {k for k, r in rec.raw.items() if r.sig == "LVLI" and r.plugin.name == "Skyrim.esm"}
    inner = {e[1] for k in lists for e in rec.lvli(k)["entries"] if e[1] in lists}
    roots = [k for k in lists if k not in inner]
    per_root_mat: dict = defaultdict(dict)
    per_root_grade: dict = defaultdict(dict)

    for root in roots:
        mat = defaultdict(lambda: 999)
        grade = defaultdict(lambda: 999)
        walk(rec, lists, root, 1, {root}, mat, grade)
        for m, g in mat.items():
            per_root_mat[m][root] = g
        for m, g in grade.items():
            per_root_grade[m][root] = g
    # the gate is the median over the lists that hold it: a few special lists hand anything out at level 1
    return {"roots": len(roots), "rule": "median over every unreferenced Skyrim.esm list of the lowest level it gives the thing at",
            "materials": {m: {"gate": median(v.values()), "lists": len(v)}
                          for m, v in sorted(per_root_mat.items(), key=lambda kv: median(kv[1].values()))},
            "enchant_grades": {m: {"gate": median(v.values()), "lists": len(v)} for m, v in sorted(per_root_grade.items())}}


def walk(rec, lists, k, gate, seen, mat, grade) -> None:
    """Each weapon or armour a list reaches, at the highest entry level on the way to it."""
    for lvl, ek, _n in rec.lvli(k)["entries"]:
        g = max(gate, lvl)
        if ek in lists and ek not in seen:
            walk(rec, lists, ek, g, seen | {ek}, mat, grade)
            continue
        it = rec.item(ek) if ek else None
        if not it or it["sig"] not in ("WEAP", "ARMO"):
            continue
        for kw in it["keywords"]:
            if re.match(r"(DLC\d)?(Weap|Armor)Material", kw):
                tag = kw + (" (enchanted)" if it["ench"] else "")
                mat[tag] = min(mat[tag], g)
        if it["ench"]:
            m = re.search(r"(\d\d)$", rec.edid(it["ench"]) or "")
            if m:
                grade[int(m.group(1))] = min(grade[int(m.group(1))], g)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="stock vanilla")
    ap.add_argument("--data", default=str(Path.home() / "games/skyrimse/Data"))
    ap.add_argument("--out", default=str(REPO / "out" / "places" / "stock" / "vanilla.json"))
    a = ap.parse_args(argv)
    out = measure(Path(a.data))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}: {out['cells']} town interiors")
    return 0
