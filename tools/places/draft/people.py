"""People: every service the place record promises, given by a working person with a bed and a day; guards with
patrols and the town's crime faction; residents up to the beds of the copied homes. The day's shape, the shifts and
the service set-up follow Skyrim's own towns (docs/research/skyrim/town-life.md); nothing here is levelled.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROUTES = Path(__file__).resolve().parents[3] / "newworld" / "story" / "data" / "db" / "travel_route.jsonl"

PERSON_GIVES = {
    "trader-general": "merchant", "trader-blacksmith": "smith", "trader-apothecary": "apothecary",
    "trader-spells": "spell-trader", "trader-innkeeper": "innkeeper", "inn-room": "innkeeper",
    "trader-bookseller": "merchant", "trader-clothier": "merchant", "trader-fletcher": "smith",
    "trader-jeweller": "merchant", "trader-hunter": "merchant", "fence": "fence",
    # a travel stop's operator (docs/design/travel-network.md): a boat stop's raft-master or sea-coaster is a
    # boatman who works the landing, a coach stop's carter waits where the road leaves the town; a rootworm stop's
    # root-tender is a townsman who calls the worm at the Hist beside his own life
    "boat-stop": "boatman", "coach-stop": "carter", "rootworm-stop": "resident", "trainer": "trainer", "follower": "resident",
}
TRAVEL_MODE = {"boat-stop": "boat", "coach-stop": "coach", "rootworm-stop": "rootworm"}   # give -> travel mode
STATIONS = {"forge", "anvil", "armour-workbench", "grindstone", "smelter", "tanning-rack", "alchemy-lab",
            "arcane-enchanter", "cooking-pot", "oven", "staff-enchanter"}
STATION_MATCH = {
    "forge": r"forge", "anvil": r"anvil", "armour-workbench": r"workbench|armou?rtable", "grindstone": r"grindstone|sharpen",
    "smelter": r"smelter", "tanning-rack": r"tanning", "alchemy-lab": r"alchemy", "arcane-enchanter": r"enchant",
    "cooking-pot": r"cook|spit", "oven": r"oven", "staff-enchanter": r"staffenchant",
}
# what a source actor's base must show (class, factions, services, edid) to stand in for a role
ROLE_MATCH = {
    "merchant": r"merchant|vendor|general|trader", "smith": r"blacksmith|smith|weapon|armou?r", "apothecary": r"apothecary|alchem|treeminder",
    "spell-trader": r"spell|mage|healer|priest|wizard", "innkeeper": r"innkeeper|inn\b|tavern|bartender",
    "boatman": r"boat|ferry|raft|captain|sailor|ship", "carter": r"carriage|carter|driver|stable|wagon|\bcart\b",
    "guard": r"guard|soldier|watchman", "fence": r"fence|thie",
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


def work_stops(folk: list[dict]) -> list[str]:
    """Each person's work hours are spent at their work stop as it stands (`work`: the spot a later stage set, a
    room's with its height): a routine's work stop that says otherwise is the work stop again. Returns who changed."""
    out = []
    for p in folk:
        w = p.get("work")
        if not w:
            continue
        for st in p.get("routine") or []:
            if st.get("kind") == "work" and st.get("at") != w:
                st["at"] = dict(w)
                if p["id"] not in out:
                    out.append(p["id"])
    return out


def apply_identities(folk: list[dict], identities: dict[str, dict]) -> None:
    """Each person's name from the people source newworld/sources/people/<place>.json (tools.places.identities); a
    person without a row keeps a placeholder, minted again if it collides with an identity's name."""
    named = {r["name"] for r in identities.values() if r.get("name")}
    taken = set(named)
    for p in folk:
        row = identities.get(p["id"])
        hh = (row or {}).get("household") or {}
        if hh.get("id") and not p.get("household"):   # a camp's people: their household is the people source's
            p["household"] = {"id": hh["id"], "relation": hh.get("role") or "kin"}
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


def routes_of(place_id: str, path: Path = ROUTES) -> dict[str, list[str]]:
    """The travel network's destinations from a place by mode, nearest first (travel_route)."""
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()] if path.exists() else []
    out: dict[str, list[str]] = {}
    for r in sorted(rows, key=lambda r: (r["travel_mode_id"], r["distance_m"])):   # as build.travel_routes
        if r["from_place_id"] == place_id:
            out.setdefault(r["travel_mode_id"], []).append(r["to_place_id"])
    return out


def service_row(g: dict, routes: dict[str, list[str]] | None = None) -> dict:
    """A person's service as the place record promises it: the give's seq, kind and detail, and for a travel stop
    the network's destinations from the place by that mode."""
    row = {"seq": g["seq"], "kind": g["give_kind_id"], "detail": g.get("detail")}
    mode = TRAVEL_MODE.get(g["give_kind_id"])
    if mode and routes is not None:
        row["destinations"] = list(routes.get(mode, []))
    return row


def refresh_services(folk: list[dict], gives: list[dict], routes: dict[str, list[str]]) -> list[str]:
    """Each person's services re-read from the place record's promises at their seq (kind, detail, destinations); a
    service whose seq the record no longer holds is dropped. Returns the ids of the people whose services changed."""
    by_seq = {g["seq"]: g for g in gives}
    out = []
    for p in folk:
        was = p.get("services")
        if not was:
            continue
        now = [service_row(by_seq[s["seq"]], routes) for s in was if s.get("seq") in by_seq]
        if now != was:
            p["services"] = now
            out.append(p["id"])
    return out


def service_problems(folk: list[dict], gives: list[dict], routes: dict[str, list[str]] | None = None) -> list[str]:
    """Where a person's service is not the record's promise: a seq the record lacks, a kind or detail other than the
    give's, destinations other than the network's, a travel stop's operator in another role than the mode's."""
    by_seq = {g["seq"]: g for g in gives if "seq" in g}
    bad = []
    for p in folk:
        for s in p.get("services") or []:
            g = by_seq.get(s.get("seq"))
            if g is None:
                bad.append(f"{p['id']}: service at seq {s.get('seq')} but the record promises nothing there")
                continue
            want = service_row(g, routes)
            for k in ("kind", "detail", "destinations"):
                if k in want and s.get(k) != want[k]:
                    bad.append(f"{p['id']}: service {g['seq']} {k} {s.get(k)!r} but the record promises {want[k]!r}")
            role = PERSON_GIVES.get(g["give_kind_id"])
            if g["give_kind_id"] in TRAVEL_MODE and p.get("role") != role:
                bad.append(f"{p['id']}: operates the {g['give_kind_id']} as {p.get('role')!r}, not its operator {role!r}")
    return bad


def road_end(paths: list[dict], centre, dry=None) -> list[float] | None:
    """Where a carter waits: the end of the place's streets farthest from its centre (the road out of town), on dry
    ground, as Skyrim's carriages wait outside the town by the road."""
    ends = [q for p in paths for q in (p["points"][0], p["points"][-1]) if p.get("points")]
    ends = [q for q in ends if dry is None or dry(q)]
    if not ends:
        return None
    q = max(ends, key=lambda q: (math.dist(q[:2], centre[:2]), q[0], q[1]))
    return [round(q[0], 1), round(q[1], 1)]


def service_people(gives: list[dict], routes: dict[str, list[str]] | None = None) -> list[dict]:
    """Group the place record's promises into the people who give them (one person may give several)."""
    people: list[dict] = []
    for g in sorted(gives, key=lambda r: r["seq"]):
        role = PERSON_GIVES.get(g["give_kind_id"])
        if role is None or role == "resident":   # what a resident gives makes no person of its own (`give_to_residents`)
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
        mate["gives"].append(service_row(g, routes))
        mate["details"].append(g.get("detail"))
        mate["tokens"] |= tok
    for p in people:
        p.pop("tokens")
    return people


def give_to_residents(folk: list[dict], gives: list[dict], identities: dict[str, dict], hist: str | None = None,
                      routes: dict[str, list[str]] | None = None) -> list[str]:
    """A promise a townsman keeps beside his own life (a rootworm stop's handler, a follower: role `resident` in
    PERSON_GIVES) is given to one of the residents, never to a person made for it: the resident whose trade in the
    people source says the most of the promise's kind and detail, else the first resident who gives nothing yet. A
    stop's handler works at it through the service hours: a rootworm stop is at the place's Hist (`hist`, the shrine
    tree's ref: the worms run in its roots), where there is one. Returns the people given a promise."""
    out = []
    for g in sorted(gives, key=lambda r: r["seq"]):
        if PERSON_GIVES.get(g["give_kind_id"]) != "resident" or any(
                s.get("seq") == g["seq"] for p in folk for s in p.get("services") or []):
            continue
        tok = _tokens(g["give_kind_id"] + " " + (g.get("detail") or ""))
        res = [p for p in folk if p.get("role") == "resident"]
        if not res:
            continue
        said = [len(tok & _tokens((identities.get(p["id"]) or {}).get("trade") or "")) for p in res]
        p = res[said.index(max(said))] if max(said) else next((q for q in res if not q.get("services")), res[0])
        p["services"] = (p.get("services") or []) + [service_row(g, routes)]
        if g["give_kind_id"].endswith("-stop"):
            day = {st["kind"]: st["at"] for st in p.get("routine") or []}
            if hist:
                p["work"] = {"space": "exterior", "ref": hist, "radius": 384}
            if day.get("sleep") and day.get("eat"):
                p["routine"] = routine("handler", day["sleep"], p["work"], day["eat"], day.get("wander") or p["work"])
        out.append(p["id"])
    return out


def spots_of(place_id: str, place: dict) -> dict[str, str]:
    """{give kind: ref id} of the `draft.add` rows marked with a `stop` (the rootworm's root pool)."""
    from tools.places.draft import io
    return {a["stop"]: io.mint(place_id, "add", str(k), a.get("id_base") or a["base"])
            for k, a in enumerate((place.get("draft") or {}).get("add") or []) if a.get("stop")}


def stop_spots(folk: list[dict], spots: dict[str, str]) -> list[str]:
    """A stop's handler works at the stop's own thing where the place has one (`spots`: give kind -> the ref of the
    `draft.add` row marked with that `stop`, a rootworm's root pool): their work and the work hours of their day
    stand there. Returns the people moved."""
    out = []
    for p in folk:
        kind = next((s["kind"] for s in p.get("services") or [] if s.get("kind") in spots), None)
        if kind is None:
            continue
        want = {"space": "exterior", "ref": spots[kind], "radius": 384}
        if p.get("work") == want:
            continue
        p["work"] = want
        for st in p.get("routine") or []:
            if st.get("kind") == "work":
                st["at"] = dict(want)
        out.append(p["id"])
    return out


def role_score(npc: dict, role: str, races: dict | None = None) -> float:
    blob = " ".join(str(npc.get(k, "")) for k in ("edid", "name", "class", "services")) + " " + \
        " ".join(str(f.get("faction", "")) for f in npc.get("factions") or [])
    pat = ROLE_MATCH.get(role)
    s = 2.0 if pat and re.search(pat, blob, re.I) else 0.0
    race = str(npc.get("race_edid") or npc.get("race") or "")
    if re.search(r"argonian", race, re.I):
        s += 1.0
    return s


# the races a person of a place is built on: Skyrim's ten peoples and their elder and vampire forms (a creature's race,
# a fox's or a boar's, is never one)
PERSON_RACE = re.compile(r"(Argonian|Breton|DarkElf|HighElf|Imperial|Khajiit|Nord|Orc|Redguard|WoodElf|Elder)Race", re.I)


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
    if npc.get("race_edid") and not PERSON_RACE.match(str(npc["race_edid"])):
        return False   # a beast of the source (King of the Murkmire's marsh fox and boar) is no person to build on
    tpl = npc.get("template")
    if tpl and npc.get("template_flags"):
        up = (npcs or {}).get(tpl)
        return up is not None and tpl not in _seen and usable(up, npcs, _seen | {tpl})
    return True


# where the people of a place come from when its source has no one to build them on (a camp of beasts and empty
# beds): Black Marsh's own townsfolk, nothing levelled in them
PEOPLE_FALLBACK = ("bmv.helstrom",)


def _actors(b) -> list[tuple[str, dict]]:
    return [(sp_id, r) for sp_id, sp in sorted(b.spaces.items()) for r in sp.refs
            if r.get("kind") == "actor" and r.get("base") in b.npcs]


def base_pool(src, dec: dict, load) -> tuple[list, dict, list[str]]:
    """The actors our people are built on and their bases: the source's own; or the actors of the sources
    `draft.people_from` names (the source's people are not the place's); or, where the source holds no person to
    build on, those of PEOPLE_FALLBACK, so no draft leaves a person without a base. Returns (pool, npcs, from)."""
    pool, npcs = _actors(src), dict(src.npcs)
    named = list(dec.get("people_from") or [])
    if not named and any(usable(npcs[r["base"]], npcs) for _, r in pool):
        return pool, npcs, []
    pool, npcs = [], {}
    for sid in named or PEOPLE_FALLBACK:
        b = load(sid)
        npcs.update(b.npcs)
        pool += _actors(b)
    return pool, npcs, named or list(PEOPLE_FALLBACK)


def base_picker(pool: list, npcs: dict, used: dict[str, int] | None = None):
    """pick(role): the usable base that best fits the role, the least used first."""
    used = {} if used is None else used
    cands = sorted({r["base"] for _, r in pool if usable(npcs[r["base"]], npcs)})

    def pick(role: str) -> str | None:
        if not cands:
            return None
        best = max(cands, key=lambda k: (role_score(npcs[k], role), -used.get(k, 0), k))
        used[best] = used.get(best, 0) + 1
        return best
    return pick


def rebase(folk: list[dict], src_npcs: dict, pool: list, npcs: dict) -> list[str]:
    """Give a new base to each person built on none, or on one of the source's that is no person to build on (a
    beast, a levelled or Nordic actor). Returns the ids changed."""
    used: dict[str, int] = {}
    for p in folk:
        if p.get("base_from"):
            used[p["base_from"]] = used.get(p["base_from"], 0) + 1
    pick, out = base_picker(pool, npcs, used), []
    for p in folk:
        b = p.get("base_from")
        if b and not (b in src_npcs and not usable(src_npcs[b], src_npcs)):
            continue
        nb = pick(p.get("role") or "resident")
        if nb and nb != b:
            p["base_from"] = nb
            out.append(p["id"])
    return out


def guard_eat(bed: dict | None) -> dict:
    """Where a guard eats: in the room of their bed (a barracks, a home that lodges them), or, sleeping in their camp
    outdoors, at their own bed, as a camp eats round its beds; a stop outdoors with no spot is put where the town's
    middle is, which may be open water or a pocket the network never reaches."""
    if bed is None:
        return {"space": "exterior", "radius": 1024}
    if bed["space"] == "exterior":
        return {"space": "exterior", "ref": bed["ref"], "radius": 1024}
    return {"space": bed["space"], "radius": 1024}


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


def fill_homes(place_id: str, folk: list[dict], homes: dict[str, list[str]], population: int | None,
               keep_free=frozenset()) -> list[str]:
    """Residents fill the homes' free beds before the open beds (place-build, "Beds decide the people"), until the
    place holds the record's `population`: each joins the family of the home whose bed they take (its first sleeper
    heads it, the second is the partner, the rest their kin), and spends the day in the town as its residents do.
    `homes`: {home space: a bed ref per sleeper} (stages.home_beds). Returns the ids added."""
    from tools.places.draft import io
    want = int(population or 0)
    used: dict[tuple, int] = {}
    for p in folk:
        b = p.get("bed") or {}
        used[(b.get("space"), b.get("ref"))] = used.get((b.get("space"), b.get("ref")), 0) + 1
    town = next((p["work"] for p in folk if p.get("role") == "resident" and (p.get("work") or {}).get("pos")), None) \
        or {"space": "exterior", "radius": 1024}
    taken = {p.get("name") for p in folk}
    ids = {p["id"] for p in folk}
    members = {}
    for p in folk:
        hh = (p.get("household") or {}).get("id")
        if hh:
            members[hh] = members.get(hh, 0) + 1
    crime = f"{place_id}.crime"
    n = sum(1 for p in folk if p.get("role") == "resident")
    added: list[str] = []
    for sid in sorted(homes):
        for ref in homes[sid]:
            if len(folk) >= want:
                return added
            if ref in keep_free or used.get((sid, ref), 0) >= homes[sid].count(ref):
                continue
            used[(sid, ref)] = used.get((sid, ref), 0) + 1
            pid = io.mint(place_id, "person", "resident", str(n))
            while pid in ids:
                n += 1
                pid = io.mint(place_id, "person", "resident", str(n))
            n += 1
            ids.add(pid)
            hh = f"{place_id}.household.{sid}"
            k = members.get(hh, 0)
            members[hh] = k + 1
            bed = {"space": sid, "ref": ref, "radius": 128}
            folk.append({"id": pid, "name": placeholder_name(pid, taken),
                         "household": {"id": hh, "relation": ("head", "partner")[k] if k < 2 else "kin"},
                         "base_from": None, "role": "resident", "home": sid, "bed": bed, "work": dict(town),
                         "services": [], "faction_ranks": [{"faction": crime, "rank": 0},
                                                           {"faction": f"{place_id}.town", "rank": 0}],
                         "routine": routine("resident", bed, dict(town), {"space": sid, "radius": 1024}, dict(town))})
            added.append(pid)
    return added


def fill_to_record(place_id: str, folk: list[dict], ext: list[dict], bases: dict, population: int | None,
                   guards: int | None = None, keep_free=frozenset(), keep=frozenset(),
                   centre: list[float] | None = None) -> tuple[list[str], list[str], int]:
    """A draft holds all its people (owner, #80, 2026-11-19). `guards` (`draft.guards`, a count) is how many of the
    drafted guards the place keeps (a camp held by a gang-master keeps none): the rest are taken out, last first.
    Residents then sleep in the open beds left (a camp's tents and bedrolls, beds standing outdoors), one to a bed,
    until the place holds the record's `population`; a bed in `keep_free` (the free bed the record promises, the
    inn's rented bed) stays unowned. Returns (removed ids, added ids, people still short of a bed)."""
    from tools.places.draft import interiors, io
    removed: list[str] = []
    if guards is not None:
        for p in [p for p in folk if p.get("role") == "guard"][max(0, guards):]:
            folk.remove(p)
            removed.append(p["id"])
    want = int(population or 0)
    if population is not None:   # a record that holds fewer people: residents go, the last first, the cast never
        for p in [p for p in folk if p.get("role") == "resident" and p["id"] not in keep][::-1]:
            if len(folk) <= want:
                break
            folk.remove(p)
            removed.append(p["id"])
    owned = {(p.get("bed") or {}).get("ref") for p in folk}
    beds = sorted((r for r in ext if r.get("kind") == "furniture" and interiors.is_bed(bases.get(r.get("base")) or {})
                   and r["id"] not in owned and r["id"] not in keep_free), key=lambda r: r["id"])
    mid = centre or (beds[0]["pos"][:2] if beds else [0.0, 0.0])
    town = {"space": "exterior", "pos": [round(mid[0], 1), round(mid[1], 1)], "radius": 1024}
    taken = {p.get("name") for p in folk}
    n = sum(1 for p in folk if p.get("role") == "resident")
    ids = {p["id"] for p in folk}
    added: list[str] = []
    crime = f"{place_id}.crime"
    while len(folk) < want and beds:
        pid = io.mint(place_id, "person", "resident", str(n))
        n += 1
        if pid in ids:
            continue
        bed = beds.pop(0)
        at = {"space": "exterior", "ref": bed["id"], "radius": 128}
        folk.append({"id": pid, "name": placeholder_name(pid, taken), "base_from": None, "role": "resident",
                     "home": "exterior", "bed": at, "work": town, "services": [],
                     "faction_ranks": [{"faction": crime, "rank": 0}, {"faction": f"{place_id}.town", "rank": 0}],
                     "routine": routine("resident", at, town, guard_eat(at), town)})
        added.append(pid)
    return removed, added, max(0, want - len(folk))
