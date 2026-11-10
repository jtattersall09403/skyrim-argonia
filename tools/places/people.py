"""People of a place, planned for tools/ArgoniaPlaces/Build (People.cs): the way Skyrim.esm's towns do it.

Each person of people.jsonl becomes an actor base of ours (a copy of `base_from` with a placeholder name, fixed
level, no levelled lists: decision 0035) placed once as a persistent actor, with:
  - packages from the routine, each a copy of a vanilla templated package of that kind (the template carries the
    procedure; we set the schedule and the place): sleep (WhiterunBraithSleep21x12, the Sleep template), work and
    wander (SolitudeTempleMinister0x8, Sandbox), eat (GuardRiftenEatDayShift20x4, Eat), patrol
    (GuardRiftenBarracksPatrol, Patrol: the first marker of a chain of linked XMarkerHeadings); a routine stop
    names a ref of the place or a position (a persistent XMarkerHeading of ours is placed there); then one
    unscheduled sandbox at home, the fallback;
  - the bed: a FURN bed ref of the place, owned by the person (XOWN on the bed), as vanilla residents' beds;
  - the town's crime faction (our CrimeFaction<place>: tracks crime; the actor's CRIF and a rank in it) and, for
    guards, IsGuardFaction;
  - services, one per give of the place record (newworld/story/data/db/place_give.jsonl) the person serves:
      trader-*        a vendor faction of ours (VENV hours from the person's work stop, VEND the vanilla vendor
                      list of that trade, VENC a merchant chest of ours in the place's chest cell, whose base is the
                      vanilla spouse/merchant chest of that trade with every levelled list flattened to fixed items)
                      plus the vanilla Job faction of the trade;
      trainer         a class of ours (the base's class with Teaches and the maximum training level) plus
                      JobTrainerFaction and JobTrainer<Skill>Faction;
      inn-room        the innkeeper's JobInnkeeperFaction and the rented bed: a bed ref of the place in
                      `room_bed`, owned by the innkeeper's vendor faction until rented (vanilla: the room's bed is
                      owned by the inn, and DialogueGeneric's rent-room line gives it to the player for a day);
      carriage-or-boat  (role boatman) a boatman faction of ours the travel lines are conditioned on; the quest, topics
                      and lines are build.py's `plan_boats` (place-studio.md, Build: boats); shrine-blessing is
                      build.py's `plan_shrines` (place-studio.md, Build: shrines).
"""
from __future__ import annotations

TEMPLATE = {  # routine kind -> the vanilla package copied (Skyrim.esm)
    "sleep": "Skyrim.esm:10F979",   # WhiterunBraithSleep21x12 (Sleep)
    "work": "Skyrim.esm:10FB3D",    # SolitudeTempleMinister0x8 (Sandbox)
    "wander": "Skyrim.esm:10FB3D",
    "sandbox": "Skyrim.esm:10FB3D",
    "eat": "Skyrim.esm:10C524",     # GuardRiftenEatDayShift20x4 (Eat)
    "patrol": "Skyrim.esm:10DE27",  # GuardRiftenBarracksPatrol (Patrol)
}
XMARKER_HEADING = "Skyrim.esm:000034"
CHEST_CELL_LIGHT = "Skyrim.esm:0300E2"
IS_GUARD = "Skyrim.esm:086EEE"
JOB_TRAINER = "Skyrim.esm:0E3A49"
TRAINER_SKILL = {  # skill -> JobTrainer<Skill>Faction (Skyrim.esm)
    "Enchanting": "0E3A5B", "Restoration": "0E3A5A", "Illusion": "0E3A59", "Conjuration": "0E3A58", "Speech": "0E3A57",
    "Alchemy": "0E3A56", "Sneak": "0E3A55", "Lockpicking": "0E3A54", "Pickpocket": "0E3A53", "LightArmor": "0E3A52",
    "HeavyArmor": "0E3A51", "Smithing": "0E3A50", "Block": "0E3A4F", "Archery": "0E3A4E", "TwoHanded": "0E3A4D",
    "OneHanded": "0E3A4C", "Alteration": "0E3A4B", "Destruction": "0E3A4A"}
TRAINER_LEVEL = {"Journeyman": 50, "Expert": 75, "Master": 90}
TRADE = {  # give -> (Job faction, vendor list FLST, merchant chest CONT copied), all Skyrim.esm
    "trader-general": ("051596", "06CB48", "0C644F"),
    "trader-blacksmith": ("05091D", "066333", "0C644B"),
    "trader-apothecary": ("05091C", "09379F", "0C644C"),
    "trader-spells": ("050921", "0937A1", "0C644E"),
    "trader-innkeeper": ("05091B", "0914F0", "0C644D"),
    "trader-fletcher": ("051592", "0937A8", "0B2035"),
    "trader-jeweller": ("0806A9", "0937A7", "0C644F"),
    "trader-clothier": ("0806A8", "0937A0", "0A6C04"),
    "trader-hunter": ("051599", "10D9D4", "0C644F"),
    "trader-bookseller": ("051599", "10C42E", "10C430"),
    "fence": ("0806AA", "06CB48", "0C644F"),
}
JOB_INNKEEPER = "Skyrim.esm:05091B"
JOB_MERCHANT = "Skyrim.esm:051596"  # JobMerchantFaction
JOB_RENT_ROOM = "Skyrim.esm:09CC97"  # JobRentRoomFaction: rank -1 on a renting innkeeper
RENT_VOICES = "Skyrim.esm:03B4A5"  # the form list of voice types vanilla's rent offer is spoken in
RENT_WI = "Skyrim.esm:035D64"  # RentRoomScript's WI property, as on every vanilla innkeeper
PERSON_SERVES = set(TRADE) | {"trainer", "inn-room"}  # gives a person provides (the rest are refs or not built)
DEFAULT_RADIUS = 512
SLEEP_RADIUS = 256


def sk(local: str) -> str:
    return f"Skyrim.esm:{local}"


class Bad(Exception):
    """A fault of one person's row: listed as a problem, the rest still planned."""


def plan(P: dict, S: dict, ids, facts: dict, notes: list[str]) -> dict:
    from tools.places.build import cell_of
    pid = P["place"]["place_id"]
    people = P["people"]
    if not people:
        return {}
    by_id = S["by_id"]
    out = {"crime_faction": {"fk": ids("fact:crime"), "edid": f"ANP_{pid}_CrimeFaction", "name": f"{pid} crime"},
           "factions": [], "classes": [], "containers": [], "npcs": [], "packages": [], "actors": [], "markers": [],
           "owned_beds": [], "chest_cell": None}

    by_src = {(r["space"], r.get("src")): r for r in S["refs"] if r.get("src")}

    def find_ref(at: dict):
        """A ref of the place named by our id, or by its source key within a copied space."""
        return by_id.get(at["ref"]) or by_src.get((at.get("space", "exterior"), at["ref"]))

    def ground_z(x, y):
        from tools.places.build import CELL, QUAD, cell_steps
        cx, cy = cell_of(x, y)
        c = facts["by_cell"].get((cx, cy))
        if not c or not c.get("deltas"):
            return 0.0
        st = cell_steps(c)
        return float(st[min(int((y - cy * CELL) / QUAD), 32), min(int((x - cx * CELL) / QUAD), 32)]) * 8.0

    def norm_at(at: dict) -> dict:
        at = dict(at)
        if at.get("ref") and find_ref(at) is not None:
            r = find_ref(at)
            at["ref"] = r["id"]
            return at
        if at.get("ref"):  # a source ref the copy did not keep: the space's first furniture stands in, noted
            notes.append(f"people.jsonl: stop ref {at['ref']} in {at.get('space')} is not in the place; its space's first furniture is used")
            at.pop("ref")
        if at.get("pos") is None:  # a stop that names only a space: its first furniture, else its first ref
            sp = at.get("space", "exterior")
            rs = [r for r in S["refs"] if r["space"] == sp]
            r = next((r for r in rs if r.get("kind") == "furniture"), rs[0] if rs else None)
            if r is None:
                raise Bad(f"people.jsonl: stop in {sp}, which has no refs")
            at["ref"] = r["id"]
            return at
        if len(at["pos"]) == 2:
            at["pos"] = [at["pos"][0], at["pos"][1], ground_z(*at["pos"])]
        return at

    def place_at(at: dict, why: str) -> str:
        """A routine stop's target: the named ref of the place, else a persistent XMarkerHeading of ours there."""
        at = norm_at(at)
        if at.get("ref"):
            r = by_id.get(at["ref"])
            if r is None:
                raise Bad(f"people.jsonl: {why}: ref {at['ref']} is not in the place")
            r["persistent"] = True
            return r["fk"]
        key = f"marker:{why}"
        fk = ids(key)
        sp = at.get("space", "exterior")
        out["markers"].append({"fk": fk, "base": XMARKER_HEADING, "space": sp, "pos": at["pos"], "rot": [0.0, 0.0, 0.0],
                               "cell": list(cell_of(*at["pos"][:2])) if sp == "exterior" else None})
        return fk

    made = {}
    taken_beds = set()
    for q in people:
        b = q.get("bed")
        r = find_ref(b) if isinstance(b, dict) else by_id.get(b or "")
        if r is not None:
            taken_beds.add(r["id"])

    def one(p):
        who = p["id"]
        npc_fk = ids(f"npc:{who}")
        if isinstance(p.get("bed"), dict):
            b = find_ref(p["bed"])
            p["bed"] = b["id"] if b else p["bed"]["ref"]
        packs = []
        patrol_start = None
        for i, st in enumerate(p.get("routine", [])):
            kind = st["kind"]
            if kind not in TEMPLATE:
                raise Bad(f"people.jsonl: {who}: routine kind {kind!r} (known: {sorted(TEMPLATE)})")
            fk = ids(f"pack:{who}:{i}")
            row = {"fk": fk, "edid": f"ANP_{pid}_{_edid(who)}_{kind}{i}", "from": TEMPLATE[kind], "kind": kind,
                   "hour": int(st["start"]), "minutes": int(round(float(st["hours"]) * 60)), "days": st.get("days")}
            if kind == "patrol":
                pts = p.get("patrol") or []
                loop = True
                if isinstance(pts, dict):
                    loop = pts.get("loop", True)
                    pts = pts.get("points") or []
                if len(pts) < 2:
                    raise Bad(f"people.jsonl: {who}: a patrol needs two or more patrol points")
                chain = [place_at(pt if isinstance(pt, dict) else {"pos": pt}, f"{who}:patrol{j}") for j, pt in enumerate(pts)]
                for a, b in zip(chain, chain[1:] + (chain[:1] if loop else [])):
                    m = next(x for x in out["markers"] + S["refs"] if x["fk"] == a)
                    m.setdefault("linked", []).append({"ref": b, "keyword": ""})
                # vanilla: the Patrol template's input 0 is PackageTargetLinkedReference with no keyword, and the
                # actor's own linked ref (no keyword) names the first marker of the chain
                row["target_linked"] = True
                patrol_start = chain[0]
            else:
                at = st["at"]
                if kind == "sleep" and p.get("bed"):
                    at = {"ref": p["bed"]}
                row["location"] = {"ref": place_at(at, f"{who}:{i}"),
                                   "radius": int(at.get("radius", SLEEP_RADIUS if kind == "sleep" else DEFAULT_RADIUS))}
            out["packages"].append(row)
            packs.append(fk)
        home = p.get("home_at") or (p["routine"][0]["at"] if p.get("routine") and p["routine"][0].get("at") else None)
        if home:
            fk = ids(f"pack:{who}:home")
            out["packages"].append({"fk": fk, "edid": f"ANP_{pid}_{_edid(who)}_home", "from": TEMPLATE["sandbox"], "kind": "sandbox",
                                    "hour": -1, "minutes": 0, "location": {"ref": place_at(home, f"{who}:home"), "radius": DEFAULT_RADIUS}})
            packs.append(fk)
        if p.get("bed"):
            bed = by_id.get(p["bed"])
            if bed is None:
                raise Bad(f"people.jsonl: {who}: bed {p['bed']} is not in the place")
            bed["owner"] = npc_fk
            bed["persistent"] = True
            out["owned_beds"].append({"bed": bed["fk"], "owner": npc_fk})
        factions = [{"faction": out["crime_faction"]["fk"], "rank": 0}]
        for fr in p.get("faction_ranks", []):
            f = fr["faction"]
            if f == f"{pid}.crime" or f.startswith(f"{pid}.vendor"):
                continue  # the crime faction is every person's; vendor factions come from the services
            if f.startswith(f"{pid}."):  # a faction of the place (town, guard, ...): one of ours per name
                name = f.split(".", 1)[1]
                if name not in made:
                    made[name] = {"fk": ids("fact:town" if name == "town" else f"fact:{name}"),
                                  "edid": f"ANP_{pid}_{_edid(name).title()}Faction", "name": f"{pid} {name}"}
                    out["factions"].append({**made[name]})
                f = made[name]["fk"]
            elif ":" not in f:
                raise Bad(f"people.jsonl: {who}: faction {f!r} is neither a form key nor a faction of {pid}")
            factions.append({"faction": f, "rank": int(fr.get("rank", 0))})
        if p.get("role") == "guard":
            factions.append({"faction": IS_GUARD, "rank": 0})
        cls = None
        gives = []
        scripts, voice_list, boat_faction = [], None, None
        for sv in p.get("services", []):
            g = sv.get("give_kind_id") or sv["kind"]
            if g in TRADE:
                job, flst, chest = TRADE[g]
                chest_base = ids(f"cont:{who}:{g}")
                out["containers"].append({"fk": chest_base, "edid": f"ANP_{pid}_{_edid(who)}_Chest", "from": sk(chest)})
                if out["chest_cell"] is None:
                    out["chest_cell"] = {"fk": ids("space:chests"), "edid": f"ANP_{pid}_MerchantChests", "light": CHEST_CELL_LIGHT}
                chest_ref = ids(f"ref:chest:{who}:{g}")
                out["markers"].append({"fk": chest_ref, "base": chest_base, "space": "__chests__", "pos": [0.0, 0.0, 0.0],
                                       "rot": [0.0, 0.0, 0.0], "cell": None})
                work = next((s for s in p.get("routine", []) if s["kind"] == "work"), None)
                fk = ids(f"fact:vendor:{who}:{g}")
                out["factions"].append({"fk": fk, "edid": f"ANP_{pid}_{_edid(who)}_{g}", "name": f"{p.get('name') or who} ({g})",
                                        "vendor": {"list": sk(flst), "chest": chest_ref,
                                                   "start": int(work["start"]) if work else 8,
                                                   "end": (int(work["start"]) + int(round(float(work["hours"])))) % 24 if work else 20,
                                                   "stolen_only": g == "fence"}})
                factions += [{"faction": fk, "rank": 0}, {"faction": sk(job), "rank": 0}]
                gives.append(g)
            elif g == "trainer":
                skill, level = sv.get("skill"), sv.get("level")
                if not skill:  # "Expert Restoration (a tree-minder)"
                    words = (sv.get("detail") or "").split()
                    level = words[0] if words and words[0] in TRAINER_LEVEL else "Journeyman"
                    skill = next((w for w in words if w in TRAINER_SKILL), None)
                level = level or "Journeyman"
                if skill not in TRAINER_SKILL:
                    raise Bad(f"people.jsonl: {who}: trainer skill {skill!r} (known: {sorted(TRAINER_SKILL)})")
                cls = {"fk": ids(f"clas:{who}"), "edid": f"ANP_{pid}_{_edid(who)}_Class", "teaches": skill,
                       "max_level": TRAINER_LEVEL.get(level, int(level) if str(level).isdigit() else 50)}
                out["classes"].append(cls)
                factions += [{"faction": JOB_TRAINER, "rank": 0}, {"faction": sk(TRAINER_SKILL[skill]), "rank": 0}]
                gives.append(g)
            elif g == "inn-room":
                rb = by_id.get(sv.get("room_bed", "")) if sv.get("room_bed") else None
                rent = (P["place"].get("stations") or {}).get("rent_bed")
                if rb is None and rent:  # place.json stations.rent_bed: the inn's bed kept for renting
                    rb = find_ref(rent) if isinstance(rent, dict) else by_id.get(rent)
                    if rb is None:
                        raise Bad(f"place.json: stations.rent_bed {rent} is not in the place")
                if rb is None:  # vanilla: a bed of the inn no resident sleeps in (the innkeeper's own house, else where they work)
                    hb = by_id.get(p.get("bed") or "")
                    inn = hb["space"] if hb else (p.get("work") or {}).get("space") or p.get("home")
                    rb = next((r for r in S["refs"] if r["space"] == inn and r is not hb and r["id"] not in taken_beds
                               and r.get("kind") == "furniture" and "bed" in (r.get("base_edid") or "").lower()), None)
                if rb is None:
                    beds = sorted(r.get("src") or r["id"] for r in S["refs"] if r["space"] == inn and r.get("kind") == "furniture"
                                  and "bed" in (r.get("base_edid") or "").lower())
                    raise Bad(f"people.jsonl: {who}: inn-room has no bed to rent: set room_bed, or leave a bed of {inn} that no "
                              f"resident sleeps in (its beds {beds} are all residents')")
                rb["persistent"] = True
                rb["owner_inn_of"] = who  # owned by the innkeeper's vendor faction (set below)
                # the vanilla innkeeper (Dagur, Faida): JobRentRoomFaction at rank -1, the Innkeeper and Merchant job
                # factions, RentRoomScript(Bed = the room's bed ref, WI = WIRentRoom...) and a voice of form list 03B4A5
                # (RentVoices: Male/Female Commoner and Argonian). The offer INFO 079B1A reads the faction.
                for fa, rank in ((JOB_RENT_ROOM, -1), (JOB_INNKEEPER, 0), (JOB_MERCHANT, 0)):
                    if not any(f["faction"] == fa for f in factions):
                        factions.append({"faction": fa, "rank": rank})
                scripts.append({"name": "RentRoomScript", "props": [{"name": "Bed", "type": "object", "value": rb["fk"]},
                                                                    {"name": "WI", "type": "object", "value": RENT_WI}]})
                # People.cs picks: the base's own voice when it is in the list, else the list's voice of its sex
                # (Argonian for an Argonian race, else Commoner)
                voice_list = RENT_VOICES
                gives.append(g)
            elif g == "carriage-or-boat" and p.get("role") == "boatman":
                boat_faction = ids(f"fact:boat:{who}")
                out["factions"].append({"fk": boat_faction, "edid": f"ANP_{pid}_Boatman_{_edid(who)}", "name": f"{p.get('name') or who} (boatman)"})
                factions.append({"faction": boat_faction, "rank": 0})
                gives.append(g)
            else:
                notes.append(f"{who}: service {g} is not a person's to give here (built by refs, or not built yet)")
        # the rented bed: owned by the inn (the innkeeper's vendor faction)
        for r in S["refs"]:
            if r.pop("owner_inn_of", None) == who:
                vf = next((f for f in out["factions"] if f["fk"] in {x["faction"] for x in factions} and f.get("vendor")), None)
                r["owner"] = vf["fk"] if vf else out["crime_faction"]["fk"]
                out["owned_beds"].append({"bed": r["fk"], "owner": r["owner"], "rented": True})
        spot = p.get("placed_at") or (p["routine"][0]["at"] if p.get("routine") else None)
        if spot is None:
            raise Bad(f"people.jsonl: {who}: no routine stop to place them at")
        pos, space = _spot(norm_at(spot), by_id)
        out["npcs"].append({"fk": npc_fk, "edid": f"ANP_{pid}_{_edid(who)}", "name": p.get("name") or who, "from": p["base_from"],
                            "level": int(p.get("level", 10)), "factions": factions, "packages": packs,
                            "class": cls["fk"] if cls else None, "gives": gives, "role": p.get("role"), "id": who,
                            **({"scripts": scripts} if scripts else {}), **({"voice_list": voice_list} if voice_list else {}),
                            **({"boat_faction": boat_faction} if boat_faction else {})})
        out["actors"].append({"fk": ids(f"actor:{who}"), "base": npc_fk, "space": space, "pos": pos, "rot": [0.0, 0.0, 0.0],
                              "cell": list(cell_of(*pos[:2])) if space == "exterior" else None, "person": who,
                              **({"linked": [{"ref": patrol_start, "keyword": ""}]} if patrol_start else {})})
    from tools.places.build import problem
    for p in people:
        try:
            one(p)
        except Bad as e:
            problem(str(e))
        except (KeyError, TypeError, ValueError, IndexError, AttributeError) as e:  # a row of a shape not read: never a crash
            problem(f"people.jsonl: {p.get('id') if isinstance(p, dict) else p}: a row the builder cannot read "
                    f"({type(e).__name__}: {e}); the person row's shape is in place-studio.md, Place files")
    return out


def _spot(at: dict, by_id: dict) -> tuple[list[float], str]:
    if at.get("ref"):
        r = by_id[at["ref"]]
        return [float(v) for v in r["pos"]], r["space"]
    return [float(v) for v in at["pos"]], at.get("space", "exterior")


def _edid(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.split(".")[-1])
