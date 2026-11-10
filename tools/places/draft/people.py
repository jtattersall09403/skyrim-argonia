"""People: every service the place record promises, given by a working person with a bed and a day; guards with
patrols and the town's crime faction; residents up to the beds of the copied homes. The day's shape, the shifts and
the service set-up follow Skyrim's own towns (docs/research/skyrim/town-life.md); nothing here is levelled.
"""
from __future__ import annotations

import hashlib
import math
import re

PERSON_GIVES = {
    "trader-general": "merchant", "trader-blacksmith": "smith", "trader-apothecary": "apothecary",
    "trader-spells": "spell-trader", "trader-innkeeper": "innkeeper", "inn-room": "innkeeper",
    "trader-bookseller": "merchant", "trader-clothier": "merchant", "trader-fletcher": "smith",
    "trader-jeweller": "merchant", "trader-hunter": "merchant", "fence": "fence",
    "boat-stop": "boatman", "coach-stop": "boatman", "rootworm-stop": "resident", "trainer": "trainer", "follower": "resident",
}
STATIONS = {"forge", "anvil", "armour-workbench", "grindstone", "smelter", "tanning-rack", "alchemy-lab",
            "arcane-enchanter", "cooking-pot", "oven", "staff-enchanter"}
STATION_MATCH = {
    "forge": r"forge", "anvil": r"anvil", "armour-workbench": r"workbench|armou?rtable", "grindstone": r"grindstone|sharpen",
    "smelter": r"smelter", "tanning-rack": r"tanning", "alchemy-lab": r"alchemy", "arcane-enchanter": r"enchant",
    "cooking-pot": r"cook|spit", "oven": r"oven", "staff-enchanter": r"staffenchant",
}
# what a source actor's base must show (class, factions, services, edid) to stand in for a role
ROLE_MATCH = {
    "merchant": r"merchant|vendor|general|trader", "smith": r"blacksmith|smith|weapon|armou?r", "apothecary": r"apothecary|alchem",
    "spell-trader": r"spell|mage|healer|priest|wizard", "innkeeper": r"innkeeper|inn\b|tavern|bartender",
    "boatman": r"boat|ferry|carriage|captain|sailor|ship", "guard": r"guard|soldier", "fence": r"fence|thie",
    "resident": r"citizen|villager|farmer|resident|townsperson|commoner",
}
INDOOR = {"innkeeper", "spell-trader"}
NO_BED = {"innkeeper"}
OUTDOOR_WORK = {"smith"}  # a smith works the forge in the yard       # Skyrim's innkeepers keep the inn all day and night: one 24-hour package, no bed
STATION_OWNER = {"forge": "smith", "anvil": "smith", "grindstone": "smith", "armour-workbench": "smith",
                 "smelter": "smith", "tanning-rack": "smith", "alchemy-lab": "apothecary",
                 "arcane-enchanter": "spell-trader", "staff-enchanter": "spell-trader", "cooking-pot": "innkeeper",
                 "oven": "innkeeper"}
SERVICE_HOURS = (8, 20)      # vendors open (town-life.md: VendorFaction hours)
NAMES_A = ["Ah", "Bee", "Chee", "Dee", "Ee", "Heem", "Jaa", "Kee", "Lee", "Mee", "Naa", "Okee", "Paa", "Ree",
           "Sei", "Tee", "Ula", "Vee", "Wan", "Xil", "Yee", "Zee", "Nur", "Tsa", "Heeta", "Ra"]
NAMES_B = ["-Ja", "-Tul", "-Wan", "-Lei", "-Rus", "-Kai", "-Meen", "-Neeus", "-Tah", "-Shei", "-Zish", "-Wulm",
           "-Xeeh", "-Sakka", "-Jeem", "-Daro", "-Teel", "-Nassa", "-Ruuk", "-Mar"]


def placeholder_name(seed: str, taken: set[str]) -> str:
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    for k in range(200):
        n = NAMES_A[(h >> (k % 40)) % len(NAMES_A)] + NAMES_B[(h // 7 + k * 13) % len(NAMES_B)].lower()
        n = n[0].upper() + n[1:]
        if n not in taken:
            taken.add(n)
            return n
    raise RuntimeError("names exhausted")


def apply_identities(folk: list[dict], identities: dict[str, dict]) -> None:
    """Each person's name from the people source newworld/sources/people/<place>.json (tools.places.identities); a
    person without a row keeps a placeholder, minted again if it collides with an identity's name."""
    named = {r["name"] for r in identities.values() if r.get("name")}
    taken = set(named)
    for p in folk:
        row = identities.get(p["id"])
        if row and row.get("name"):
            p["name"] = row["name"]
        elif p["name"] in taken:
            p["name"] = placeholder_name(p["id"], taken)
        else:
            taken.add(p["name"])


def _tokens(s: str) -> set[str]:
    words = re.findall(r"[a-z][a-z-]+", (s or "").lower())
    words += [p for w in words if "-" in w for p in w.split("-")]
    return {w for w in words if len(w) >= 3} - {"and", "for", "his", "her", "its",
        "with", "from", "their", "tomes", "adept", "expert", "journeyman", "master", "seller", "trader", "the"}


def service_people(gives: list[dict]) -> list[dict]:
    """Group the place record's promises into the people who give them (one person may give several)."""
    people: list[dict] = []
    for g in sorted(gives, key=lambda r: r["seq"]):
        role = PERSON_GIVES.get(g["give_kind_id"])
        if role is None:
            continue
        tok = _tokens(g.get("detail", ""))
        mate = None
        for p in people:
            same_detail = g.get("detail") and g["detail"] in p["details"]
            if same_detail or (role in ("trainer", "innkeeper", "fence") and tok & p["tokens"]):
                mate = p
                break
        if mate is None:
            mate = {"role": role, "gives": [], "details": [], "tokens": set()}
            if role == "trainer":
                mate["role"] = "trainer"
            people.append(mate)
        mate["gives"].append({"seq": g["seq"], "kind": g["give_kind_id"], "detail": g.get("detail")})
        mate["details"].append(g.get("detail"))
        mate["tokens"] |= tok
    for p in people:
        p.pop("tokens")
    return people


def role_score(npc: dict, role: str, races: dict | None = None) -> float:
    blob = " ".join(str(npc.get(k, "")) for k in ("edid", "name", "class", "services")) + " " + \
        " ".join(str(f.get("faction", "")) for f in npc.get("factions") or [])
    pat = ROLE_MATCH.get(role)
    s = 2.0 if pat and re.search(pat, blob, re.I) else 0.0
    race = str(npc.get("race_edid") or npc.get("race") or "")
    if re.search(r"argonian", race, re.I):
        s += 1.0
    return s


def usable(npc: dict, npcs: dict | None = None, _seen: frozenset = frozenset()) -> bool:
    """No levelled actor and no Nordic one. A base that takes anything from a template (stats, inventory, spells)
    is levelled unless the template is a base of `npcs` that is itself usable: a template outside them is taken
    for what Skyrim's are, a levelled actor list (LvlBanditMelee1H)."""
    t = str(npc.get("type") or npc.get("record") or "NPC_")
    race = str(npc.get("race_edid") or npc.get("race") or "")
    blob = f"{npc.get('edid', '')} " + " ".join(str(f.get("edid", "")) for f in npc.get("factions") or [])
    if (t in ("LVLN", "LeveledNpc") or npc.get("nordic") or re.search(r"\bnord", race, re.I)
            or re.search(r"corpse|bandit|dremora|draugr", blob, re.I)):
        return False
    tpl = npc.get("template")
    if tpl and npc.get("template_flags"):
        up = (npcs or {}).get(tpl)
        return up is not None and tpl not in _seen and usable(up, npcs, _seen | {tpl})
    return True


def routine(role: str, bed: dict, work: dict, eat: dict, wander: dict, shift: str = "day") -> list[dict]:
    """The day of one person, in Skyrim's shape (town-life.md): adults sleep from midnight, eat an hour at 7 and
    20, shops open 8 to 20; guards keep two 12-hour shifts and sleep the other half."""
    if role == "guard":
        if shift == "day":
            return [{"start": 9, "hours": 12, "kind": "patrol", "at": work},
                    {"start": 21, "hours": 1, "kind": "eat", "at": eat},
                    {"start": 22, "hours": 11, "kind": "sleep", "at": bed}]
        return [{"start": 21, "hours": 12, "kind": "patrol", "at": work},
                {"start": 9, "hours": 1, "kind": "eat", "at": eat},
                {"start": 10, "hours": 11, "kind": "sleep", "at": bed}]
    if role in NO_BED:
        return [{"start": 0, "hours": 24, "kind": "work", "at": work}]
    if role == "resident":
        return [{"start": 0, "hours": 7, "kind": "sleep", "at": bed},
                {"start": 7, "hours": 1, "kind": "eat", "at": eat},
                {"start": 8, "hours": 10, "kind": "wander", "at": wander},
                {"start": 18, "hours": 2, "kind": "eat", "at": eat},
                {"start": 20, "hours": 4, "kind": "wander", "at": wander}]
    return [{"start": 0, "hours": 7, "kind": "sleep", "at": bed},
            {"start": 7, "hours": 1, "kind": "eat", "at": eat},
            {"start": SERVICE_HOURS[0], "hours": SERVICE_HOURS[1] - SERVICE_HOURS[0], "kind": "work", "at": work},
            {"start": 20, "hours": 1, "kind": "eat", "at": eat},
            {"start": 21, "hours": 3, "kind": "wander", "at": wander}]


def guard_count(buildings: int) -> int:
    """Two guards a shift for a village, more for a town (town-life.md)."""
    per_shift = max(1, min(4, math.ceil(buildings / 6)))
    return 2 * per_shift


def beats(paths: list[dict]) -> list[list[list[float]]]:
    """The streets as guards' beats, longest first: each guard walks one end to end and back, never cutting across,
    and the day and night guard of a pair share it (Whiterun's patrol chains run along its streets, town-life.md)."""
    def length(p):
        return sum(math.dist(a[:2], b[:2]) for a, b in zip(p["points"], p["points"][1:]))
    return [[[round(q[0], 1), round(q[1], 1)] for q in p["points"]] for p in sorted(paths, key=lambda p: -length(p))]


def patrol(beats_: list, k: int, on=None) -> list[list[float]]:
    """Guard k's patrol points: its pair's beat out and back, only the points `on` holds (the walkable network);
    a beat left with fewer than two gives way to the next."""
    if not beats_:
        return []
    for j in range(len(beats_)):
        beat = beats_[(k // 2 + j) % len(beats_)]
        pts = [q for q in beat + beat[-2:0:-1] if on is None or on(q)]
        if len(pts) >= 2:
            return pts
    return []
