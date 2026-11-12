"""Toughness by danger band: how hard a band's actors hit, as Skyrim scales its fixed-level variants.

    python -m tools.newworld.ecology.toughness measure     # Skyrim's own numbers -> newworld/sources/ecology/toughness.json

Skyrim's creatures hit by their race's unarmed damage (skeever, wolf, fox, mudcrab and frostbite spider 5; goat
7.5; horker 15; black and brown bear 35 and 30; troll and sabre cat 35; snow bear and snowy sabre cat 45; giant 60;
frost troll and mammoth 65), and a stronger variant of one kind is an ability on the record that adds to that
damage (`AbFortifyUnarmedDamage` at a magnitude: the dragons' tiers +25, +75, +125, +175; the werewolves' and
vampires' +5 to +25; the large and giant mudcrabs +15 and +20); its health comes from the level and the record's
health offset. The stage does the same by band: each band copy of a creature carries our own ability, one per
magnitude, adding `size class base * (band damage factor - 1)` to its unarmed damage, beside its band health.
People hit with the weapon their kit gives, by tier (iron and hide, steel, then steel two-handed, elven and
orcish). Nothing reads the player's level: damage is a function of the band and the size class alone.
"""
from __future__ import annotations

import json
import re
import statistics
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MEASURE = REPO / "newworld/sources/ecology/toughness.json"
BAND_DAMAGE = {"D0": 1.0, "D1": 1.0, "D2": 1.0, "D3": 1.4, "D4": 2.0, "D5": 2.8}   # of the creature's own damage
BAND_ORDER = tuple(BAND_DAMAGE)
SIZE_RACES = {   # the Skyrim races standing for each size class
    "insect": ["FrostbiteSpiderRace", "SkeeverRace", "MudcrabRace"],
    "small": ["FoxRace", "SkeeverRace", "WolfRace", "GoatDomesticsRace"],
    "game": ["GoatRace", "HorkerRace", "DeerRace", "BearBrownRace"],
    "predator": ["SabreCatRace", "BearBlackRace", "BearBrownRace", "TrollRace", "SabreCatSnowyRace"],
    "giant": ["GiantRace", "TrollFrostRace", "MammothRace"],
}
NORD_VOICE = re.compile(r"Nord", re.I)     # a voice type of the Nords (VTCK): never a look
NORDIC_GEAR = re.compile(r"Nord|Fur|Stormcloak|Carved|Ancient|Skaal|Falmer|Draugr", re.I)   # never a kit
EARLY_HEALTH = 100        # an early character's health, to be lethal to
D1_MAX_HIT = 15           # a D1 hostile never hits harder than this (no player-killer in the first band)
D5_LETHAL_HIT = 90        # a D5 hostile predator or giant lands at least this in one blow


def measure(plugin: Path | None = None) -> dict:
    """Unarmed damage of Skyrim's races (RACE DATA at 96) and the base per size class: the median of its races."""
    sys.path.insert(0, str(REPO))
    import importlib   # the measure runs by hand on the machine that holds the game; the stage never reads the plugins
    Plugin = importlib.import_module("tools.argonia_world.esm").Plugin
    plugin_path = importlib.import_module("tools.newworld.ecology.census").plugin_path
    p = Plugin.read(plugin or plugin_path("Skyrim.esm"), {"RACE"})
    races = {}
    for r in p.records("RACE"):
        d = r.sub("DATA")
        if r.own and d and len(d) >= 100:
            races[r.edid] = round(struct.unpack_from("<f", d, 96)[0], 1)
    base = {c: statistics.median(races[n] for n in names) for c, names in SIZE_RACES.items()}
    return {"source": "Skyrim.esm RACE DATA: unarmed damage", "races": {n: races[n] for v in SIZE_RACES.values() for n in v},
            "unarmed_by_size": base,
            "ability": "AbFortifyUnarmedDamage magnitudes by variant: dragon tiers 25/75/125/175, werewolf 5-25, vampire 5-20, mudcrab 15/20"}


def load() -> dict:
    return json.loads(MEASURE.read_text())["unarmed_by_size"]


def bonus(size: str, band: str, base: dict) -> int:
    """The unarmed damage a band copy adds to its creature's own: the size class's base times the band's factor above 1."""
    return int(round(base.get(size, 0) * (BAND_DAMAGE[band] - 1))) if size in base else 0


def hit(size: str, band: str, base: dict) -> float:
    """What a creature of the class lands in one blow in the band."""
    return base[size] + bonus(size, band, base)


def check(acts: dict, bind: dict, base: dict, worn: dict) -> tuple[list, dict]:
    """The toughness check over the written actors: damage is the band's and the class's alone and rises with the
    band; no D1 hostile is a player-killer, a D5 one is lethal to an early character; nothing is levelled to the
    player. `worn` maps a band to the weapon values of the people's kit there."""
    faults: list[str] = []
    by_band: dict[str, list[float]] = {b: [] for b in BAND_ORDER}
    for name, a in acts.items():
        if a.get("kind", "").startswith("npc:"):
            continue
        size = a.get("size")
        if size not in base:
            continue
        if a.get("damage_bonus") != bonus(size, a["band"], base):
            faults.append(f"{name}: damage bonus {a.get('damage_bonus')} is not the band's {bonus(size, a['band'], base)}")
        by_band[a["band"]].append(hit(size, a["band"], base))
    for name, a in acts.items():   # never levelled to the player: a fixed level, no multiplier, no template of stats
        if not isinstance(a.get("level"), int) or any(k in a for k in ("level_mult", "pc_level_mult", "template", "lvln")):
            faults.append(f"{name}: a level that is not fixed, or a template or list to scale it")
    means = {b: round(statistics.mean(v), 1) for b, v in by_band.items() if v}
    peaks = {b: max(v) for b, v in by_band.items() if v}
    if "D1" in peaks and peaks["D1"] > D1_MAX_HIT:
        faults.append(f"a D1 hostile lands {peaks['D1']} in one blow, over {D1_MAX_HIT}")
    order = [b for b in BAND_ORDER if b in peaks]
    for lo, hi in zip(order, order[1:]):
        if peaks[hi] < peaks[lo] or means[hi] < means[lo]:
            faults.append(f"damage falls from {lo} to {hi}: means {means[lo]} {means[hi]}, peaks {peaks[lo]} {peaks[hi]}")
    ceiling = {b: max(hit(s, b, base) for s in ("predator", "giant")) for b in BAND_ORDER}   # the bands' table, placed or not
    if ceiling["D5"] < D5_LETHAL_HIT or ceiling["D5"] < EARLY_HEALTH * 0.9:
        faults.append(f"D5 predators and giants land {ceiling['D5']} in one blow: not lethal to {EARLY_HEALTH} health")
    if not all(ceiling[lo] <= ceiling[hi] for lo, hi in zip(BAND_ORDER, BAND_ORDER[1:])) or ceiling["D5"] < 2 * ceiling["D2"]:
        faults.append(f"the table's top blow does not rise with the band: {ceiling}")
    weapons = {b: round(statistics.mean(v)) for b, v in sorted(worn.items()) if v}
    wo = [weapons[b] for b in BAND_ORDER if b in weapons]
    if wo != sorted(wo):
        faults.append(f"people's weapon value falls with the band: {weapons}")
    return faults, {"mean_hit_by_band": means, "peak_hit_by_band": peaks, "top_blow_table": ceiling,
                    "weapon_value_by_band": weapons, "unarmed_by_size": base}


def main(argv: list[str]) -> int:
    if argv[:1] != ["measure"]:
        print(__doc__)
        return 2
    MEASURE.write_text(json.dumps(measure(), indent=1) + "\n")
    print(MEASURE.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
