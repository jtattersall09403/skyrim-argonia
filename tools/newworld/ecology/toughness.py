"""Toughness by danger band: how hard a band's actors hit, fixed per record and band, never by the player's level.

    python -m tools.newworld.ecology.toughness measure     # -> newworld/sources/ecology/blows.json (numbers only)

A creature's hardest blow is its race's unarmed damage (plus any fortify-unarmed ability on its record, as Skyrim's
large mudcrabs carry) times the largest damage multiplier of its race's attacks. Measured from Skyrim.esm the same
way: wolf, skeever and mudcrab 7.5 (a level 1 character's 100 health takes 7.5 per blow), fox and deer 10, goat 15,
horker 22.5, bears 45 and 52.5, sabre cat and troll 52.5, giant 90, mammoth and frost troll 97.5. The mods' records
hit far harder (the hackwing 60, the otter 33, the dreugh 67.5, the megalodon 300), so their own numbers never
stand: each band copy carries our ability on the unarmed damage (`AbFortifyUnarmedDamage`'s effect, negative to
weaken) sized so its hardest blow is its band's: in D0 and D1 Skyrim's first animals' blow, above them the median
blow of Skyrim's races of its size class times the band's factor (D2 1, D3 1.4, D4 2, D5 2.8). People hit with the
weapon their kit gives, by tier. Nothing reads the player's level.
"""
from __future__ import annotations

import json
import re
import statistics
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BLOWS = REPO / "newworld/sources/ecology/blows.json"
BAND_DAMAGE = {"D0": 1.0, "D1": 1.0, "D2": 1.0, "D3": 1.4, "D4": 2.0, "D5": 2.8}   # of the creature's own damage
BAND_ORDER = tuple(BAND_DAMAGE)
SIZE_RACES = {   # the Skyrim races standing for each size class
    "insect": ["FrostbiteSpiderRace", "SkeeverRace", "MudcrabRace"],
    "small": ["FoxRace", "SkeeverRace", "WolfRace", "GoatDomesticsRace"],
    "game": ["GoatRace", "HorkerRace", "DeerRace", "BearBrownRace"],
    "predator": ["SabreCatRace", "BearBlackRace", "BearBrownRace", "TrollRace", "SabreCatSnowyRace"],
    "giant": ["GiantRace", "TrollFrostRace", "MammothRace"],
}
LOWEST_BAND = ("WolfRace", "SkeeverRace", "MudcrabRace")   # what a level 1 player meets first in Skyrim
NORD_VOICE = re.compile(r"Nord", re.I)     # a voice type of the Nords (VTCK): never a look
NORDIC_GEAR = re.compile(r"Nord|Fur|Stormcloak|Carved|Ancient|Skaal|Falmer|Draugr", re.I)   # never a kit
EARLY_HEALTH = 100        # an early character's health, to be lethal to
D1_MAX_HIT = 15           # a D1 creature never lands more than this (twice Skyrim's first animals' blow)
D5_LETHAL_HIT = 90        # a D5 hostile predator or giant lands at least this in one blow


def _plugins(names: list[str]) -> dict:
    """form key -> record over the plugins, in load order (a later plugin's override wins), for NPC_, LVLN, RACE, SPEL."""
    import importlib
    Plugin = importlib.import_module("tools.argonia_world.esm").Plugin
    plugin_path = importlib.import_module("tools.newworld.ecology.census").plugin_path
    recs: dict = {}
    for n in names:
        try:
            p = Plugin.read(plugin_path(n), {"NPC_", "LVLN", "RACE", "SPEL"})
        except FileNotFoundError:
            continue
        for r in p.records():
            recs[r.key] = r
    return recs


def race_blow(race) -> tuple[float, float]:
    """(unarmed damage, the largest damage multiplier of its attacks): a creature's hardest blow is their product."""
    d = race.sub("DATA")
    ud = struct.unpack_from("<f", d, 96)[0] if d and len(d) >= 100 else 0.0
    mults = [struct.unpack_from("<f", a, 0)[0] for a in race.all("ATKD") if len(a) >= 4]
    return round(ud, 2), round(max([m for m in mults if 0 < m < 20] or [1.0]), 2)


FORTIFY_UNARMED = "0424E2:Skyrim.esm"   # AbFortifyUnarmedDamage's effect (Value Modifier, UnarmedDamage)


def npc_fortify(recs: dict, key: str) -> float:
    """What the record's own abilities add to its unarmed damage (Skyrim's large mudcrabs +15 and +20)."""
    r = recs.get(key)
    if r is None or r.sig != "NPC_":
        return 0.0
    add = 0.0
    for d in r.all("SPLO"):
        sp = recs.get(r.plugin.form_key(struct.unpack_from("<I", d)[0]))
        if sp is None or sp.sig != "SPEL":
            continue
        eff = None
        for sig, b in sp.subs:
            if sig == "EFID":
                eff = sp.plugin.form_key(struct.unpack_from("<I", b)[0])
            elif sig == "EFIT" and eff == FORTIFY_UNARMED:
                add += struct.unpack_from("<f", b)[0]
    return add


def resolve_race(recs: dict, key: str, seen: tuple = ()):
    """The race an NPC_ takes: its own RNAM, or its template's when it inherits traits (ACBS template flag 0x1)."""
    r = recs.get(key)
    if r is None or key in seen:
        return None
    if r.sig == "LVLN":
        for e in r.all("LVLO"):
            k = r.plugin.form_key(struct.unpack_from("<I", e, 4)[0])
            got = resolve_race(recs, k, seen + (key,))
            if got:
                return got
        return None
    acbs = r.sub("ACBS") or b"\0" * 24
    tflags = struct.unpack_from("<H", acbs, 18)[0] if len(acbs) >= 20 else 0
    if tflags & 1 and r.ref("TPLT"):
        got = resolve_race(recs, r.ref("TPLT"), seen + (key,))
        if got:
            return got
    return recs.get(r.ref("RNAM")) if r.ref("RNAM") else None


def measure_blows(bind: dict, plugins: list[str]) -> dict:
    """Each bound creature record's own hardest blow (its race's unarmed damage times its largest attack multiplier),
    and Skyrim's measured races the same way: the stage sets each band copy to its band's blow from these."""
    recs = _plugins(plugins)
    by_edid = {(k.split(":", 1)[1], r.edid): k for k, r in recs.items() if r.edid}   # by the record's own plugin
    out = {}
    for kind, b in sorted(bind["kinds"].items()):
        for src in b.get("records", []):
            pl, ed = src.split(":", 1)
            key = by_edid.get((pl, ed))
            race = resolve_race(recs, key) if key else None
            if race is None:
                out[src] = {"race": None, "unarmed": None, "mult": None, "blow": None}
                continue
            ud, m = race_blow(race)
            ud = round(ud + npc_fortify(recs, key), 2)
            out[src] = {"race": race.edid, "unarmed": ud, "mult": m, "blow": round(ud * m, 1)}
    sky = {}
    for k, r in recs.items():
        if r.sig == "RACE" and k.endswith(":Skyrim.esm") and r.edid in {n for v in SIZE_RACES.values() for n in v}:
            ud, m = race_blow(r)
            sky[r.edid] = {"unarmed": ud, "mult": m, "blow": round(ud * m, 1)}
    by_size = {c: statistics.median(sky[n]["blow"] for n in names if n in sky) for c, names in SIZE_RACES.items()}
    low = statistics.median(sky[n]["blow"] for n in LOWEST_BAND if n in sky)
    return {"source": "RACE DATA unarmed damage (offset 96) plus the record's own fortify-unarmed abilities, times the "
                      "largest ATKD damage multiplier; the NPC_'s race by RNAM or its traits template; Skyrim's races the "
                      "same way, a size class's blow the median of its races, the lowest band's the median of "
                      "Skyrim's first animals (wolf, skeever, mudcrab)",
            "records": out, "skyrim": dict(sorted(sky.items())), "blow_by_size": by_size, "lowest_band_blow": low}


def load() -> dict:
    """The stage's toughness table (blows.json): each bound record's own unarmed damage and attack multiplier, Skyrim's
    blow per size class and its lowest band's blow."""
    d = json.loads(BLOWS.read_text())
    return {"records": d["records"], "blow_by_size": d["blow_by_size"], "lowest": d["lowest_band_blow"]}


def target(size: str, band: str, t: dict) -> float:
    """The blow a creature of the class lands in the band: in D0 and D1 Skyrim's first animals' (wolf, skeever, mudcrab),
    above them the size class's Skyrim blow times the band's factor."""
    if band in ("D0", "D1"):
        return t["lowest"]
    return t["blow_by_size"][size] * BAND_DAMAGE[band]


def bonus(src: str, size: str, band: str, t: dict) -> int:
    """What the band copy's ability adds to (or, negative, takes from) the record's own unarmed damage so that its
    hardest blow (unarmed damage times its largest attack multiplier) is the band's: fixed per record and band."""
    own = t["records"].get(src)
    if not own or own.get("unarmed") is None or size not in t["blow_by_size"]:
        return 0
    return int(round(target(size, band, t) / own["mult"] - own["unarmed"]))


def hit(src: str, size: str, band: str, t: dict, given: int | None = None) -> float:
    """The band copy's hardest blow, from the record's own numbers and its ability."""
    own = t["records"].get(src) or {}
    if own.get("unarmed") is None:
        return float("nan")
    b = bonus(src, size, band, t) if given is None else given
    return round((own["unarmed"] + b) * own["mult"], 1)


def check(acts: dict, bind: dict, t: dict, worn: dict) -> tuple[list, dict]:
    """The toughness check over the written actors, from each copied record's own blow: every creature's measured,
    its ability its band's, its hardest blow within a point of its band's target; nothing in D1 a player-killer, D5
    lethal to an early character; blows rise with the band; nothing levelled to the player. `worn` maps a band to the
    weapon values of the people's kit there."""
    faults: list[str] = []
    by_band: dict[str, list[float]] = {b: [] for b in BAND_ORDER}
    for name, a in acts.items():
        if a.get("kind", "").startswith("npc:"):
            continue
        size, src = a.get("size"), a.get("src", name.rsplit("@", 1)[0])
        if size not in t["blow_by_size"]:
            continue
        if (t["records"].get(src) or {}).get("unarmed") is None:
            faults.append(f"{name}: its record's blow is not measured (toughness.py blows)")
            continue
        if a.get("damage_bonus") != bonus(src, size, a["band"], t):
            faults.append(f"{name}: damage bonus {a.get('damage_bonus')} is not the band's {bonus(src, size, a['band'], t)}")
        h = hit(src, size, a["band"], t, a.get("damage_bonus"))
        if abs(h - target(size, a["band"], t)) > t["records"][src]["mult"]:
            faults.append(f"{name}: lands {h} in one blow, not its band's {target(size, a['band'], t)}")
        by_band[a["band"]].append(h)
    for name, a in acts.items():   # never levelled to the player: a fixed level, no multiplier, no template of stats
        if not isinstance(a.get("level"), int) or any(k in a for k in ("level_mult", "pc_level_mult", "template", "lvln")):
            faults.append(f"{name}: a level that is not fixed, or a template or list to scale it")
    means = {b: round(statistics.mean(v), 1) for b, v in by_band.items() if v}
    peaks = {b: max(v) for b, v in by_band.items() if v}
    if "D1" in peaks and peaks["D1"] > D1_MAX_HIT:
        faults.append(f"a D1 creature lands {peaks['D1']} in one blow, over {D1_MAX_HIT}")
    order = [b for b in BAND_ORDER if b in peaks]
    for lo, hi in zip(order, order[1:]):
        if peaks[hi] < peaks[lo] or means[hi] < means[lo] - 1:   # a point of rounding in the abilities
            faults.append(f"damage falls from {lo} to {hi}: means {means[lo]} {means[hi]}, peaks {peaks[lo]} {peaks[hi]}")
    ceiling = {b: max(target(s, b, t) for s in ("predator", "giant")) for b in BAND_ORDER}   # the bands' table, placed or not
    if ceiling["D5"] < D5_LETHAL_HIT or ceiling["D5"] < EARLY_HEALTH * 0.9:
        faults.append(f"D5 predators and giants land {ceiling['D5']} in one blow: not lethal to {EARLY_HEALTH} health")
    if not all(ceiling[lo] <= ceiling[hi] for lo, hi in zip(BAND_ORDER, BAND_ORDER[1:])) or ceiling["D5"] < 2 * ceiling["D2"]:
        faults.append(f"the table's top blow does not rise with the band: {ceiling}")
    weapons = {b: round(statistics.mean(v)) for b, v in sorted(worn.items()) if v}
    wo = [weapons[b] for b in BAND_ORDER if b in weapons]
    if wo != sorted(wo):
        faults.append(f"people's weapon value falls with the band: {weapons}")
    return faults, {"mean_hit_by_band": means, "peak_hit_by_band": peaks, "top_blow_table": ceiling,
                    "weapon_value_by_band": weapons, "blow_by_size": t["blow_by_size"], "lowest_band_blow": t["lowest"]}


def main(argv: list[str]) -> int:
    if argv[:1] == ["measure"]:
        from tools.newworld.ecology.census import PLUGINS
        bind = json.loads((REPO / "newworld/sources/ecology/bindings.json").read_text())
        BLOWS.write_text(json.dumps(measure_blows(bind, PLUGINS), indent=1, sort_keys=True) + "\n")
        print(BLOWS.read_text()[:3000])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
