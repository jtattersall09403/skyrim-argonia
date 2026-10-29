"""Decision 0030's families: where each comes from in world/sources and how it becomes tables."""
from __future__ import annotations

import glob
import re
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world.migrate_0030.engine import Spec, jload, wrap

R = db.REPO
SRC = R / "world" / "sources"
MIGRATED: list[str] = []      # source files consumed (deleted after the migration)


def src(rel):
    p = SRC / rel
    MIGRATED.append(str(p.relative_to(R)))
    return jload(p)


def srcglob(pattern):
    out = []
    for f in sorted(glob.glob(str(SRC / pattern), recursive=True)):
        MIGRATED.append(str(Path(f).relative_to(R)))
        out.append((Path(f), jload(f)))
    return out


def entries(doc, ctx=None):
    return [(dict(ctx or {}), e) for e in doc["entries"]]


COMMON_DROP = {"schemaVersion": "per-row format version of the old files; the schema is versioned in git",
               "_": "a comment in the old file"}


def drops(*extra, **why):
    d = dict(COMMON_DROP)
    for e in extra:
        d[e] = "see the lane report"
    d.update(why)
    return d


# ---------------------------------------------------------------------------------------------------------------
def build(eng, only=()):
    specs = []

    def add(fn):
        if not only or fn.__name__ in only:
            specs.extend(fn(eng))
    for fn in FAMILIES:
        add(fn)
    return specs


def factions(eng):
    d = src("registries/factions.json")
    rules = dict(d["rules"])
    yield Spec("faction", "Home of every faction: name, kind, status, how it is joined and left, its doom tier.",
               entries(d), drop=drops(),
               lookup={"kind": "faction_kind", "status": "record_status", "standing.doom.default": "doom_tier",
                       "standing.doom.byRank.senior": "doom_tier"},
               maps={"standing.expel.unstated": "field"},
               fk={"standing.join.entryQuest": "quest", "standing.join.sponsor.npc": "npc"},
               tables={"sources": "faction_source"})
    reactions = rules.pop("reactions")
    yield Spec("faction_reaction", "Home of how one faction's members regard another's (disposition), symmetric or not.",
               [({}, r) for r in reactions], pk=["a", "b"], fk={"a": "faction", "b": "faction"})
    ladders = rules.pop("rankLadders")
    yield Spec("rank_ladder", "Home of each rank ladder: its ranks in order and the reputation each needs.",
               [({}, {"id": k, "ranks": v}) for k, v in ladders.items()],
               tables={"ranks": "rank_ladder_rank"})
    rules["id"] = "faction-rules"
    yield Spec("faction_rules", "Home of the faction system's single set of numbers (one row): ranges, member "
               "dispositions, crime weights against members, doom by role.", [({}, rules)],
               maps={"memberDisposition": "rank", "crimeAgainstMember": "crime", "doomByRole": "role"},
               lookup={"doomTiers[]": "doom_tier", "doomByRole{*}": "doom_tier"},
               tables={"doomTiers": "faction_rules_doom_tier"})


def npcs(eng):
    d = src("registries/npcs.json")
    for e in d["entries"]:
        if e.get("race") == "orc":
            e["race"] = "orsimer"
            eng.note(f"npc {e['id']}: race 'orc' repaired to the race table's 'orsimer'")
    yield Spec("npc", "Home of every person and creature placed in the world (decision 0030: people): who they are, "
               "where they live and work, their day, senses, loot, look and asset status.", entries(d),
               drop=drops(**{"crime": "always null in the import"}),
               lookup={"kind": "npc_kind", "status": "record_status", "hostility": "hostility_stance",
                       "doomTier": "doom_tier", "sex": "sex", "depth": "npc_depth",
                       "assetAvailability.status": "asset_status",
                       "notice.senses[]": "sense"},
               fk={"factions[].factionId": "faction", "loot.items[].item": "item",
                   "statblock.classId": "class", "dialogueSetId": "npc", "race": "race"},
               subs={"statblock", "loot", "fightFleeAlarm", "notice", "territory", "den"},
               inline={"home", "look", "assetAvailability", "day"},
               check={"fightFleeAlarm.fight": "{c} BETWEEN 0 AND 100", "fightFleeAlarm.flee": "{c} BETWEEN 0 AND 100",
                      "fightFleeAlarm.alarm": "{c} BETWEEN 0 AND 100"},
               tables={"factions": "npc_faction", "sources": "npc_source", "home.work": "npc_work",
                       "day.blocks": "npc_day_block", "day.roleExceptions": "npc_role_exception",
                       "services": "npc_service", "questHooks": "npc_quest_hook",
                       "signatureSpells": "npc_signature_spell"})


def items(eng):
    d = src("registries/items.json")
    yield Spec("item", "Home of every item: name, kind, pocket, weight, value, ladder band, model, effects, the "
               "set it belongs to and what it does.", entries(d), drop=drops(),
               lookup={"status": "record_status", "kind": "item_kind", "pocket": "pocket",
                       "assetAvailability.status": "asset_status"},
               rename={"recipe.inputs[].itemId": "input_item_id"},
               fk={"set": "item_set", "recipe.inputs[].itemId": "item", "cooksInto": "item", "lock": "lock", "quest": "quest",
                   "carriedBy": "npc"},
               subs={"condition", "recipe", "soulGem", "enchantment", "incendiary"},
               inline={"ladder", "assetAvailability"},
               tables={"sources": "item_source", "effects": "item_effect", "tags": "item_tag",
                       "assetAvailability.records": "item_asset_record"})
    yield Spec("item_set", "Home of each material set (wood, iron, ebony...): tier, scales, value per kg, "
               "requirement bonus and its materials.", [({}, {"id": k, **v}) for k, v in d["sets"].items()],
               maps={"requirementBonus": "attribute", "bonusDamage": "element"},
               fk={"requirementBonus{key}": "attribute", "materials[]": "item"},
               tables={"sources": "item_set_source"})


def locks(eng):
    d = src("registries/locks.json")
    yield Spec("lock", "Home of every lock: level, key, what it opens, its class and owner.", entries(d),
               drop=drops(), lookup={"status": "record_status", "kind": "lock_kind", "class": "lock_class",
                                     "owner.kind": "owner_kind"},
               fk={"key": "item"}, inline={"opens", "owner"},
               check={"level": "{c} BETWEEN 0 AND 100"}, tables={"sources": "lock_source"})


FAMILIES = [factions, npcs, items, locks]

LOOKUP_ABOUT = {}


def vocabulary_rows():
    """docs/design/quests/85-condition-vocabulary.md §A and §B as rows (the same terms brief.py parsed)."""
    t = (R / "docs/design/quests/85-condition-vocabulary.md").read_text()
    a, b = t[t.index("## A."):t.index("## B.")], t[t.index("## B."):t.index("## C.")]
    rows = [{"id": k, "kind": "combinator", "section": "D", "args": "conditions" if k != "not" else "condition",
             "reads": {"all": "every child holds", "any": "at least one child holds", "not": "the child fails"}[k]}
            for k in ("all", "any", "not")]
    sec = None
    for line in a.splitlines():
        m = re.match(r"### (A\d)\.", line)
        if m:
            sec = m.group(1)
        m = re.match(r"^\| `([^`]+)`(?: / `([^`]+)`)?(?: / `([^`]+)`)? \| (.*?) \|\s*(.*?)\s*\|\s*$", line)
        if m:
            reads = m.group(5) or None
            planned = re.search(r"planned: ([0-9.]+)", reads or "")
            for x in m.groups()[:3]:
                if x:
                    rows.append({"id": x, "kind": "predicate", "section": sec, "args": m.group(4),
                                 "reads": reads, "planned": planned.group(1) if planned else None})
    seen = {r["id"] for r in rows}
    sec = None
    for line in b.splitlines():
        m = re.match(r"### (B\d)\.", line)
        if m:
            sec = m.group(1)
            continue
        for m in re.finditer(r"`([a-zA-Z]+)\(([^)]*)\)`(?:\s*\*\(([^*]*)\)\*)?", line):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                rows.append({"id": m.group(1), "kind": "action", "section": sec, "args": m.group(2),
                             "reads": m.group(3)})
    return rows


def finish(eng):
    eng.terms = vocabulary_rows()
    # The promise family stays unmigrated (the place builds own it), but its keys come in now: a journal entry's
    # `groundedIn` names a fact or a promise, and the named check needs the promise ids to resolve. Read without
    # entering MIGRATED: the promise files stay in world/sources until their family migrates.
    eng.promise_keys = sorted(({"id": r["id"], "place_id": d["placeId"]}
                               for d in (jload(f) for f in sorted(glob.glob(str(SRC / "placement/promises/*.json"))))
                               for r in d.get("promises") or []), key=lambda r: r["id"])


def render(eng) -> str:
    out = ["-- The world's relational schema (decision 0030). The single description of the world's data; the",
           "-- guide is docs/design/world/98-data-model.md. Committed form: world/db/<table>.jsonl, one row per",
           "-- line, columns in schema order, sorted by primary key; read and written only through",
           "-- tools/argonia_world/db.py. Conventions: ids are the old stable id strings; a child table's key",
           "-- is its parent's key plus `ord` (list position) or the map key; BOOLEAN is 0/1.", "",
           "-- == Lookups: one row per allowed value of an enumeration ==", ""]
    for name, vals in eng.lookups.items():
        com = eng.lookup_comments.get(name) or f"Lookup: the allowed values of {name.replace('_', ' ')}."
        out.append("\n".join("-- " + x for x in wrap(com)))
        out.append(f'CREATE TABLE "{name}" (\n  "id" TEXT NOT NULL PRIMARY KEY,\n  "about" TEXT\n);\n')
    known = set(eng.tables) | set(eng.lookups) | {"condition", "action_list", "condition_term"}
    fam = None
    for t in eng.tables.values():
        if t.family != fam:
            fam = t.family
            out.append(f"-- == {fam} ==\n")
        out.append(eng.ddl(t, known))
    out.append(COND_DDL)
    out.append(FORMID_DDL)
    out.append(keyed_ddl())
    return "\n".join(out)


COND_DDL = """-- == Conditions and actions (docs/design/quests/85-condition-vocabulary.md as data) ==

-- Home of the condition and action vocabulary: every predicate (§A), combinator (all, any, not) and action verb
-- (§B) a quest, line, place or topic may use, with its argument shape and what it reads or does.
CREATE TABLE "condition_term" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('predicate', 'combinator', 'action')),
  "section" TEXT,
  "args" TEXT,
  "reads" TEXT,
  "planned" TEXT
);

-- Home of every condition: a tree of nodes; a root is named by the column that holds its id; a node is a
-- combinator over its children (ordered by `ord`) or a predicate over its arguments.
CREATE TABLE "condition" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "parent_id" TEXT REFERENCES "condition"("id") ON DELETE CASCADE,
  "ord" INTEGER,
  "term" TEXT NOT NULL REFERENCES "condition_term"("id"),
  CHECK (("parent_id" IS NULL) = ("ord" IS NULL))
);

-- Home of a predicate's arguments, in order (an id, a number, a flag or an enumeration value).
CREATE TABLE "condition_arg" (
  "condition_id" TEXT NOT NULL REFERENCES "condition"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "value" NOT NULL,
  PRIMARY KEY ("condition_id", "ord")
);

-- Home of every action list (a stage's onEnter, an ending's world changes, a line's onDelivered); the column
-- that holds the id is its owner.
CREATE TABLE "action_list" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of each action of a list, in order: one verb of the vocabulary.
CREATE TABLE "action" (
  "list_id" TEXT NOT NULL REFERENCES "action_list"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "term" TEXT NOT NULL REFERENCES "condition_term"("id"),
  PRIMARY KEY ("list_id", "ord")
);

-- Home of an action's arguments, in order.
CREATE TABLE "action_arg" (
  "list_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "arg_ord" INTEGER NOT NULL,
  "value" NOT NULL,
  PRIMARY KEY ("list_id", "ord", "arg_ord"),
  FOREIGN KEY ("list_id", "ord") REFERENCES "action" ("list_id", "ord") ON DELETE CASCADE
);
"""


def all_rows(eng):
    for name, vals in eng.lookups.items():
        yield name, [{"id": k, "about": v} for k, v in sorted(vals.items())]
    for t in eng.tables.values():
        yield t.name, t.rows
    yield "condition_term", eng.terms
    yield "condition", eng.cond_rows
    yield "condition_arg", eng.cond_args
    yield "action_list", eng.act_lists
    yield "action", eng.act_rows
    yield "action_arg", eng.act_args
    yield "promise", eng.promise_keys


def registry(table, rel, comment, **kw):
    d = src(rel)
    kw.setdefault("drop", drops())
    kw.setdefault("lookup", {"status": "record_status"})
    kw.setdefault("tables", {"sources": f"{table}_source"})
    return Spec(table, comment, entries(d), **kw)


def registries(eng):
    yield registry("deed", "registries/deeds.json", "Home of every deed counter (the silent-unlock counters, old 0039).",
                   lookup={"status": "record_status", "kind": "deed_kind"})
    yield registry("rumour_pool", "registries/rumour-pools.json", "Home of every rumour pool a place draws on.",
                   lookup={"status": "record_status", "kind": "rumour_pool_kind"})
    yield registry("document", "registries/documents.json", "Home of every readable document: its text reference, "
                   "the item that carries it, its leaves and what it teaches.",
                   lookup={"status": "record_status", "kind": "document_kind"}, fk={"item": "item"},
                   tables={"sources": "document_source", "leaves": "document_leaf", "teaches": "document_teaches"})
    yield registry("creature", "registries/creatures.json", "Home of every creature kind: regions, bands, habitat, "
                   "stat block, senses, reaction.", lookup={"status": "record_status", "kind": "creature_kind",
                                                            "hostility": "hostility_stance", "notice.senses[]": "sense"},
                   subs={"statblock", "fightFleeAlarm", "notice"},
                   tables={"sources": "creature_source", "regions": "creature_region", "bands": "creature_band"})
    yield registry("owing_region", "registries/owing.json", "Home of each region's Owing ledger: assessor, crime "
                   "rates, custody and amnesty hours (old 0039, 0151).",
                   lookup={"status": "record_status", "kind": "owing_kind"}, inline={"rates"})
    yield registry("marker", "registries/markers.json", "Home of every map marker id.")


def places(eng):
    items = []
    for f, d in srcglob("catalogue/places-*.json"):
        items += [({"region": d["region"]}, p) for p in d["places"]]
    known = {p["id"] for _, p in items}
    for f in sorted((SRC / "placement/facts").glob("*.json")):
        d = jload(f)
        if d["placeId"] not in known and d.get("world"):
            items.append(({"region": None}, {"id": d["placeId"], "name": d["world"]["name"]}))
            eng.note(f"place {d['placeId']}: not in the catalogue; a row with its built name only")
    yield Spec("place", "Home of every place of the catalogue (decision 0030: places): what it is, why it exists, "
               "its siting, culture, danger, vibe, contents, interior, hostility and quest hooks; one row per place, "
               "its region a column, never a file.", items, drop=drops(),
               lookup={"status": "record_status", "region": "region"},
               cond={"hostility.flips[].when"}, inline={"terrainRequests[].delivery"},
               tables={"sources": "place_source", "aliases": "place_alias"})


FAMILIES = [factions, npcs, items, locks, registries, places]


# -- the socket vocabulary, layouts and sockets ------------------------------------------------------------------
def socket_vocabulary(eng):
    d = src("vocab/socket-vocabulary.json")
    for key, name in [("socketKinds", "socket_kind"), ("valueBands", "value_band"), ("dangerBands", "danger_band"),
                      ("dayPhases", "day_phase"), ("schedulePurposes", "schedule_purpose"),
                      ("activities", "activity"), ("interactKinds", "interact_kind")]:
        lk = eng.lookups.setdefault(name, {})
        for v in d[key]:
            lk.setdefault(v, None)
    eng.lookup_comments["socket_kind"] = "Lookup: the kinds of place socket (old 0103 §5): " + d["about"]
    eng.lookup_comments["day_phase"] = f"Lookup: the day phases a schedule names ({d['dayPhaseSource']})."

    def ents(key, table, comment, **kw):
        v = {k: x for k, x in d[key].items() if k != "_"}
        rows = [({}, {"id": k, **(x if isinstance(x, dict) else {"value": x})}) for k, x in v.items()]
        return Spec(table, comment + (" " + d[key]["_"] if "_" in d[key] else ""), rows, drop=drops(), **kw)
    yield ents("itemClasses", "item_class", "Home of each item class a socket may name, its asset source, value band "
               "and kinds (each with the mesh that shows it). " + d["itemKindsAbout"], maps={"kinds": "kind"},
               lookup={"valueBand": "value_band"}, tables={"kinds": "item_class_kind"})
    yield ents("containerClasses", "container_class", "Home of each container class: its name families and "
               "default fill rule.", tables={"nameFamilies": "container_class_name_family"})
    yield ents("furnitureActivities", "furniture_activity", "Home of which furniture families host each activity.",
               tables={"value": "furniture_activity_family"})
    yield ents("fillRules", "fill_rule", "Home of the authored fill rule's needs. " + d["fillRulesAbout"])
    yield ents("plantClasses", "plant_class", "Home of each harvestable plant class.")
    yield ents("stationClasses", "station_class", "Home of each crafting or service station class: kit, asset, "
               "dressing.")
    yield ents("signPurposes", "sign_purpose", "Home of each sign purpose and the fields it needs.")
    yield ents("doorTypes", "door_type", "Home of each door type.")
    rest = {k: v for k, v in d.items() if k in ("decision", "about", "commonFields", "interactables",
                                                  "serviceSurfaces", "sign")}
    yield Spec("socket_vocabulary", "Home of the socket vocabulary's rules in prose (one row): its decisions, the "
               "common fields, interactables, service surfaces and the sign fields.",
               [({}, {"id": "socket-vocabulary", **rest})],
               maps={"commonFields": "field", "sign": "field"}, inline={"interactables", "serviceSurfaces"})


def layouts(eng):
    rows = []
    for f, d in srcglob("blueprints/*.layout.json"):
        rows.append(({"place_id": d["placeId"]}, {k: v for k, v in d.items() if k not in ("placeId",)}))
    ops = ["bind", "place", "socket", "note", "mount", "path", "snap", "mound", "group", "move", "settle", "remove",
           "pool", "swap"]
    yield Spec("layout", "Home of each place's layout: the authored pose of every placed thing as an ordered "
               "program of ops (old 0140); `ord` is the op's position across all the op tables, so the program "
               "replays in order. Sockets are the `socket` table.", rows, pk=["place_id"], drop=drops(),
               split={"ops": ("op", {o: ("socket" if o == "socket" else f"layout_{o}") for o in ops}, "layout_op")},
               fk={"place_id": "place", "ops[].lock": "lock", "ops[].item": "item",
                   "ops[].stationClass": "station_class", "ops[].signPurpose": "sign_purpose",
                   "ops[].itemClass": "item_class", "ops[].lootTable.items[].item": "item",
                   "ops[].containerClass": "container_class", "ops[].plantClass": "plant_class"},
               comments={"socket": "Home of every place socket (decision 0030: sockets; old 0103): an NPC post, "
                         "idle spot, item, container, station, sign, plant, mooring or marker, with its owner, value "
                         "tier, fill rule and loot; `ord` is its position in the place's layout program."})


# -- place facts, the built place, facts -------------------------------------------------------------------------
def facts(eng):
    rows = {}
    builds = []
    for f, d in srcglob("placement/facts/*.json"):
        for x in d["facts"]:
            rows[x["id"]] = ({"place_id": d["placeId"]}, dict(x))
        if d.get("world"):
            builds.append(({"place_id": d["placeId"]}, {k: v for k, v in d["world"].items()}))
    for x in src("dialogue/facts.json")["entries"]:
        if x["id"] in rows:
            rows[x["id"]][1].update({"says": x["says"], "cues": x["cues"]})
        else:
            rows[x["id"]] = ({}, dict(x))
    for q in QUEST_RECORDS:
        for x in q["facts"]:
            rows[x["id"]] = ({"quest_id": q["id"]}, dict(x))
    eng.fact_ids = set(rows)
    yield Spec("fact", "Home of every fact (decision 0030: facts): what is true, as the place states it (`claim`) "
               "and as a person says it (`says`), with the cues that name it; a place fact carries its place and "
               "carrier, a quest fact its quest and where it comes from (`from_ref`: a truth event, a place fact or "
               "a culture-sheet entry).", sorted(rows.values(), key=lambda r: r[1]["id"]),
               rename={"from": "from_ref"}, inline={"carrier"},
               fk={"place_id": "place", "quest_id": "quest"},
               tables={"cues": "fact_cue"})
    yield Spec("place_build", "Home of the old project's last build of each place, kept as the guide for 0.4 §d and "
               "the place briefs: its name, position, extent, route, stands, built sockets, landmarks, the people "
               "and their topics, services and hostility (the counts are derived and dropped).", builds,
               pk=["place_id"], drop=drops(counts="derived from the build's sockets"),
               fk={"place_id": "place", "people[].id": "npc", "people[].topics[]": "topic",
                   "services[].by[]": "npc", "hostility.owner": "faction"},
               lookup={"hostility.baseline": "hostility_stance", "people[].hostility": "hostility_stance",
                       "hostility.flips[].to": "hostility_stance"},
               cond={"hostility.flips[].when"}, subs={"hostility", "route"}, lists={"positionM"},
               tables={"people": "place_person", "people.topics": "place_person_topic"},
               rename={"people.topics": "topic"})


# -- quests ------------------------------------------------------------------------------------------------------
def _yaml_record(name):
    import yaml
    p = R / ".claude/skills/quest-write/examples" / f"{name}.yaml"
    t = p.read_text()
    # repairs of flow-mapping values the YAML parser split at their commas (the record meant one string each)
    t = re.sub(r"when: ((?:\d+|about sixty|the last three|a year|this|every|from)[^:{}\[\]]*?), (late evening|night|"
               r"dawn), who:", r'when: "\1, \2", who:', t)
    t = t.replace("setting: before witnesses (a council, a hearing, a household)",
                  'setting: "before witnesses (a council, a hearing, a household)"')
    return yaml.safe_load(t)


QUEST_RECORDS = []


def quests(eng):
    QUEST_RECORDS[:] = [_yaml_record("lh38"), _yaml_record("mr01")]
    reg = {e["id"]: e for e in src("registries/quests.json")["entries"]}
    lines_doc = src("quests/lines.json")
    lines = []
    for ln in lines_doc["lines"]:
        r = reg[ln["id"]]
        ctx = {"registry_status": r["status"], "registry_note": r["notes"], "depth": r.get("depth")}
        lines.append((ctx, ln))
    yield Spec("quest_line", "Home of every questline: its code prefix, name, group, faction, tier, home region "
               "and target count.", lines, drop=drops(),
               lookup={"group": "quest_group", "registry_status": "record_status", "homeRegion": "region"},
               fk={"faction": "faction"}, tables={"sources": "quest_line_source"})
    rec = {q["id"]: q for q in QUEST_RECORDS}
    rows, exceptions = [], []
    for f, d in srcglob("quests/quests-*.json") + srcglob("quests/local-*.json"):
        for k, v in (d.get("budgetExceptions") or {}).items():
            for shape, why in v.items():
                exceptions.append(({}, {"packet": d["packet"], "line": k, "shape": shape, "reason": why}))
        for q in d["quests"]:
            r = reg[q["id"]]
            if r["sources"] != q["sources"]:
                eng.note(f"quest {q['id']}: the registry's sources {r['sources']} differ from the quest row's; "
                         "the quest row's kept")
            ctx = {"packet": d["packet"], "registry_status": r["status"], "registry_note": r["notes"]}
            obj = dict(q)
            if q["id"] in rec:
                obj = {k: v for k, v in rec[q["id"]].items() if k != "facts"}
                eng.note(f"quest {q['id']}: the reviewed record replaces the data-file row "
                         f"(fields that differed: {sorted(k for k in set(q) | set(obj) if q.get(k) != obj.get(k))})")
            rows.append((ctx, obj))
    yield Spec("quest", "Home of every quest (decision 0030: quests): the quest object (code, title, line, group, "
               "tier, shapes, region, settlement, anchor places, premise) and, once a quest is written, its record "
               "(quest-write/quest-record.md) as child tables: truth, cast and what each knows, things, clues, "
               "conclusions, shape data, stages with objectives and edges, endings, topics, review.", rows,
               drop=drops(), rename={"from": "from_ref"},
               lookup={"group": "quest_group", "status": "quest_status", "registry_status": "record_status",
                       "region": "region", "shapes[]": "quest_shape", "costTier": "cost_tier",
                       "touches[].access": "touch_access", "centrepiece": "verb_tag"},
               fk={"line": "quest_line", "settlement": "place", "anchorPlaces[]": "place",
"stages[].place": "place", "cast[].id": "npc",
                   "playerStart[]": "fact", "clues[].gives[]": "fact",
                   "topics[].uses[]": "fact", "topics[].hides[]": "fact", "stages[].learns[]": "fact",
                   "cast[].changes[].fact": "fact", "standInFor": "quest", "topics[].person": "npc"},
               maps={"shapeData": "section", "cast[].knowledge": "fact_id", "things[].states": "state",
                     "recordSources": "source"},
               cond={"startWhen", "stages[].objectives[].completeWhen", "stages[].successors[].when",
                     "stages[].failForward[].when"},
               actions={"stages[].onEnter", "endings[].world", "endings[].rewards"},
               inline={"stages[].outside", "review"},
               tables={"sources": "quest_source", "shapes": "quest_shape_of", "anchorPlaces": "quest_anchor_place",
                       "touches": "quest_touch", "essentialTopics": "quest_essential_topic",
                       "sockets": "quest_socket", "stages": "quest_stage", "stages[].objectives": "quest_objective",
                       "stages[].successors": "quest_successor", "stages[].failForward": "quest_fail_forward",
                       "stages[].approaches": "quest_approach", "stages[].approaches[].actions": "quest_approach_action",
                       "stages[].actions": "quest_action", "stages[].learns": "quest_stage_learns",
                       "cast": "quest_cast", "cast[].knowledge": "quest_cast_knowledge",
                       "cast[].changes": "quest_cast_change", "things": "quest_thing",
                       "things[].states": "quest_thing_state", "clues": "quest_clue", "clues[].gives": "quest_clue_gives",
                       "clues[].supports": "quest_clue_supports", "conclusions": "quest_conclusion",
                       "conclusions[].clues": "quest_conclusion_clue", "endings": "quest_ending",
                       "topics": "quest_topic", "topics[].stages": "quest_topic_stage",
                       "topics[].uses": "quest_topic_uses", "topics[].hides": "quest_topic_hides",
                       "topics[].grants": "quest_topic_grants", "truth": "quest_truth", "truth[].who": "quest_truth_who",
                       "playerStart": "quest_player_start", "actionPlan": "quest_action_plan",
                       "shapeData": "quest_shape_data", "review.findings": "quest_review_finding",
                       "recordSources": "quest_record_source"})
    yield Spec("quest_budget_exception", "Home of each recorded departure from the shape budget (old 55 §47c step "
               "5): the packet, the line, the shape and the one-line reason.", exceptions,
               pk=["packet", "line", "shape"], fk={"line": "quest_line"}, lookup={"shape": "quest_shape"})
    jr = []
    for f, d in srcglob("text/journal/*.json"):
        jr += entries(d)
    yield Spec("journal_entry", "Home of every journal entry's text: its quest, surface, the facts it states and "
               "those it is grounded in.", jr, drop=drops(), fk={"questId": "quest", "factIds[]": "fact"},
               tables={"factIds": "journal_entry_fact", "groundedIn": "journal_entry_grounding"})


# -- topics, glossary, lines, culture, stance --------------------------------------------------------------------
def dialogue(eng):
    d = src("dialogue/topics.json")
    yield Spec("topic", "Home of every dialogue topic of the topic web: class, label, glossary term, what it is "
               "keyed to and what requires it.", entries(d), drop=drops(),
               lookup={"topicClass": "topic_class"}, inline={"keys", "requiredFor"},
               fk={"keys.place": "place", "keys.faction": "faction", "keys.quest": "quest",
                   "requiredFor.places[]": "place", "requiredFor.factions[]": "faction",
                   "requiredFor.people[]": "npc", "glossaryTerm": "glossary_term",
                   "requiredFor.glossaryTerms[]": "glossary_term"})
    g = src("dialogue/glossary.json")
    yield Spec("glossary_term", "Home of every glossary term: its forms, its topic, whether it is act-one and "
               "opaque, its gloss and section. `load_bearing` marks the forms the old glossary listed as load-bearing.",
               [({"load_bearing": None}, e) for e in g["entries"]], drop=drops(),
               fk={"topicId": "topic"}, tables={"forms": "glossary_form"})
    eng.load_bearing = g["loadBearing"]
    rows = []
    for f, d in srcglob("dialogue/lines/*.json"):
        rows += [({"place_id": d["placeId"], "pool": None}, e) for e in d["entries"]]
    for f, d in srcglob("dialogue/pool/*.json"):
        rows += [({"place_id": None, "pool": f.stem}, e) for e in d["entries"]]
    yield Spec("dialogue_line", "Home of every dialogue line (decision 0030: lines): greeting, topic answer, "
               "override or pool line; its speaker (or its pool), topic, words and variants, conditions "
               "(`available`), the facts it states, links and what it does when delivered. The imported lines are "
               "reference only (0024 §7): `status` says so.", rows, drop=drops(),
               lookup={"type": "line_type"}, fk={"speaker": "npc", "keys.topic": "topic", "place_id": "place", "derivedFrom.poolLineId": "dialogue_line",
                                                  "factIds[]": "fact", "links[]": "topic"},
               cond={"available"}, actions={"onDelivered"}, inline={"keys", "derivedFrom", "variants"},
               tables={"factIds": "dialogue_line_fact", "links": "dialogue_line_link"})
    sheets = []
    for f, d in srcglob("dialogue/cultures/**/*.json"):
        sheets += entries(d, {"file": str(f.relative_to(SRC / "dialogue/cultures"))})
    for _, e in sheets:
        if e.get("race") == "orc":
            e["race"] = "orsimer"
            eng.note(f"culture sheet {e['id']}: race 'orc' repaired to 'orsimer'")
    lists = ["norms", "taboos", "values", "contempts", "speech.addressTerms", "speech.oaths", "speech.neverSaid",
             "talk.grievances", "talk.rumours"]
    kinds = {"norms": "norm", "taboos": "taboo", "values": "value", "contempts": "contempt",
             "speech.addressTerms": "address-term", "speech.oaths": "oath", "speech.neverSaid": "never-said",
             "talk.grievances": "grievance", "talk.rumours": "rumour"}
    yield Spec("culture_sheet", "Home of every culture sheet (decision 0030: culture): one node of the culture "
               "chain (province, region, people, faction, settlement, group, household) with its parent, speech, "
               "opinions per topic class, views and dissent; its entries are `culture_entry`.", sheets,
               drop=drops(), fk={"parent": "culture_sheet", "factionId": "faction", "placeId": "place",
                                 "members[]": "npc", "dissent[].personId": "npc", "race": "race",
                                 "views[].node": "culture_sheet"},
               lookup={"level": "culture_level", "speech.formality": "formality", "opinions{key}": "opinion_class"},
               maps={"opinions": "opinion_class"}, inline={"speech", "talk"},
               merge={k: ("culture_entry", kinds[k]) for k in lists},
               comments={"culture_entry": "Home of every culture-sheet entry, by kind (norm, taboo, value, contempt, "
                         "address term, oath, never-said, grievance, rumour), in order, with its source."},
               tables={"opinions": "culture_opinion", "members": "culture_member", "views": "culture_view",
                       "dissent": "culture_dissent"})
    st = []
    for f, d in srcglob("dialogue/stance/*.json"):
        st += entries(d, {"place_id": d["placeId"]})
    yield Spec("stance", "Home of each person's stance and voice (decision 0030: culture): the culture chain they "
               "speak from, per topic class their lean and where it comes from and any deviation, and their voice.",
               st, pk=["personId"], drop=drops(), fk={"personId": "npc", "chain[]": "culture_sheet",
                                                      "topics{*}.from": "culture_sheet", "place_id": "place",
                                                      "voice.explainerOf[]": "topic"},
               maps={"topics": "opinion_class", "voice.answerLength": "length_class"}, inline={"voice"},
               lookup={"topics{key}": "opinion_class"},
               tables={"chain": "stance_chain", "topics": "stance_topic", "voice.neverMentions": "stance_never_mentions",
                       "voice.answerLength": "stance_answer_length", "voice.explainerOf": "stance_explainer_of"})


FAMILIES += [socket_vocabulary, layouts, quests, facts, dialogue]


# -- routes ------------------------------------------------------------------------------------------------------
def _file_tables(rel, prefix, comments, entity_maps=(), drop_keys=(), settings_comment=None, **kw):
    """One file's lists and maps as entity tables (key `id` when every element has a unique one, else `ord`),
    its remaining fields as a one-row settings table."""
    d = src(rel)
    rest = {}
    for k, v in d.items():
        if k in ("schemaVersion", "_") or k in drop_keys:
            continue
        name = comments.get(k, (f"{prefix}_{snake_(k)}", None))[0]
        com = comments.get(k, (None, None))[1] or f"Home of each entry of {rel}'s `{k}`."
        opts = kw.get(k, {})
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            ids = [x.get("id") for x in v]
            if all(ids) and len(set(ids)) == len(ids):
                yield Spec(name, com, [({}, x) for x in v], drop=drops(), **opts)
            else:
                yield Spec(name, com, [({"ord": i}, x) for i, x in enumerate(v)], pk=["ord"], drop=drops(), **opts)
        elif isinstance(v, dict) and (k in entity_maps):
            items = [({}, {"id": kk, **(vv if isinstance(vv, dict) else {"value": vv})})
                     for kk, vv in v.items() if kk != "_"]
            yield Spec(name, com + (" " + v["_"] if "_" in v else ""), items, drop=drops(), **opts)
        else:
            rest[k] = v
    if rest:
        yield Spec(f"{prefix}_settings", settings_comment or f"Home of {rel}'s single set of rules and notes (one "
                   "row).", [({}, {"id": prefix, **rest})], drop=drops(), **kw.get("settings", {}))


def snake_(s):
    from tools.argonia_world.migrate_0030.engine import snake
    return snake(s)


def routes(eng):
    yield from _file_tables("routes/registry.json", "route", {"routes": (
        "route", "Home of every named route (road, track, boat lane, ferry, rootway): its mode, class, ends, "
                 "aliases, confidence and sources (decision 0030: routes).")},
        routes={"lookup": {"mode": "route_mode", "class": "route_class"}, "fk": {"joinsRouteId": "route"},
                "tables": {"aliases": "route_alias", "sources": "route_source"}})
    yield from _file_tables("routes/authored-routes.json", "authored_track", {"routes": (
        "authored_track", "Home of each hand-authored track's polyline (metres).")},
        routes={"tables": {"pointsM": "authored_track_point"}})
    yield from _file_tables("routes/authored-minor-waterways.json", "minor_waterway", {})
    yield from _file_tables("routes/harbour-stations.json", "harbour", {"harbours": (
        "harbour", "Home of each city's harbour station: the place that serves as its quay and why.")},
        entity_maps={"harbours"}, harbours={"fk": {"placeId": "place"}})
    yield from _file_tables("routes/junctions.json", "junction", {"junctions": (
        "junction", "Home of each road junction or pin: position, roads and why.")},
        junctions={"fk": {"roads[]": "route"}, "tables": {"roads": "junction_road"}})
    yield from _file_tables("routes/lane-terminals.json", "lane_terminal", {"terminals": (
        "lane_terminal", "Home of each boat lane's terminal where the city anchor is inland.")},
        entity_maps={"terminals"})
    yield from _file_tables("routes/rootworm-stations.json", "rootworm", {
        "stations": ("rootworm_station", "Home of each rootworm station (root node): its place and kind."),
        "rootways": ("rootworm_rootway", "Home of each rootway between two root nodes.")},
        stations={"fk": {"placeId": "place"}}, rootways={"fk": {"from": "rootworm_station", "to": "rootworm_station"}})
    yield from _file_tables("routes/route-structure-exemplars.json", "route_structure_exemplar", {"places": (
        "route_structure_exemplar", "Home of each exemplar route-structure place (old 2.W): its way, chainage "
                                    "and position.")}, places={"fk": {"id": "place", "wayId": "route"}})
    yield from _file_tables("routes/route-structures.json", "route_structure", {"structures": (
        "route_structure", "Home of each structure on a route (stair, bridge, causeway...): its piece, span and "
                           "rise.")})
    yield from _file_tables("routes/travel-services.json", "travel", {
        "stations": ("travel_station", "Home of every travel station (ferry landing, place station, root node): "
                     "its kind, place, berth and piece."),
        "services": ("travel_service", "Home of every travel service: its form, fare, hops and operator."),
        "roadEdges": ("travel_road_edge", "Home of each road edge between travel stations."),
        "rootways": ("travel_rootway", "Home of each rootway as a travel edge."),
        "transferEdges": ("travel_transfer_edge", "Home of each walking transfer between stations."),
        "craft": ("travel_craft", "Home of each craft and landing piece a travel service uses."),
        "harbourStations": ("travel_harbour_station", "Home of each city's harbour station id.")},
        entity_maps={"craft", "harbourStations"},
        services={"cond": {"available"}, "fk": {"hops[].from": "travel_station", "hops[].to": "travel_station"}},
        harbourStations={"fk": {"placeId": "place", "stationId": "travel_station"}},
        stations={"fk": {"placeId": "place"}},
        settings={"maps": {"policy": "key", "vocabulary": "key"}})
    yield from _file_tables("routes/water-crossings.json", "water_crossing", {"crossings": (
        "water_crossing", "Home of each place a way crosses water: the way, the water body, banks, span, depth "
                          "and band.")}, drop_keys=("counts", "deepestM", "widestM"))
    eng.note("routes: water-crossings `counts`, `deepestM`, `widestM` dropped (derived from the crossings)")


# -- the sheet (1.3 §a, 0.4 §a's studio character), frozen arrays, FormIDs ---------------------------------------
def sheet(eng):
    base = R / "private/old-packages/game-core/src/stats/data"
    if not base.exists():
        raise SystemExit("the sheet's tables come from private/old-packages (gitignored, the import); not present")
    a = jload(base / "attributes.json")
    ref = a["reference"]
    yield Spec("attribute", "Home of the seven attributes (no Luck; 76 §117) and each one's reference value.",
               [({}, {"id": x["id"], "reference": ref.get(x["id"])}) for x in a["attributes"]])
    yield Spec("sheet_rules", "Home of the sheet's single set of attribute rules (one row; 76 §117): the start "
               "range, the favoured bonus, the purchase cap.",
               [({}, {"id": "sheet", "startRange": a["startRange"], "favouredBonus": a["favouredBonus"],
                      "purchaseCap": a["purchaseCap"], "designRef": a["designRef"]})])
    s = jload(base / "skills.json")
    yield Spec("skill", "Home of the 27 skills (76 §118): governing attribute, specialisation, family, the bands "
               "that scale with skill and the attribute its score uses.", [({}, x) for x in s["skills"]],
               fk={"gov": "attribute", "score": "attribute"}, lookup={"spec": "specialisation", "family": "skill_family"},
               maps={"bands": "band"})
    r = jload(base / "races.json")
    for x in r["races"]:
        x["baseAttributes"] = [{"sex": sx, "attribute": at, "value": v}
                               for sx, vals in x.pop("attributes").items() for at, v in vals.items()]
    for v in r["sexes"]:
        eng.lookups.setdefault("sex", {}).setdefault(v, None)
    yield Spec("race", "Home of every race (76 §127, UESP Morrowind:Races, old 0089, 0096): base attributes by sex, "
               "skill bonuses, permanent effects and powers.", [({}, x) for x in r["races"]],
               maps={"skillBonuses": "skill"},
               fk={"skillBonuses{key}": "skill", "baseAttributes[].attribute": "attribute"},
               lookup={"baseAttributes[].sex": "sex"}, tables={"baseAttributes": "race_base_attribute",
                                                    "skillBonuses": "race_skill_bonus", "effects": "race_effect",
                                                    "powers": "race_power"})
    c = jload(base / "classes.json")
    yield from _sheet_file(c, "class", "Home of every class (76): specialisation, favoured attributes, major and "
                           "minor skills.")
    b = jload(base / "birthsigns.json")
    yield from _sheet_file(b, "birthsign", "Home of every birthsign (76): its effects, abilities and powers.")


def _sheet_file(d, table, comment):
    key = next(k for k, v in d.items() if isinstance(v, list) and v and isinstance(v[0], dict))
    yield Spec(table, comment, [({}, x) for x in d[key]], drop=drops(designRef="the doc reference"))
    rest = {k: v for k, v in d.items() if k not in (key, "schemaVersion", "designRef")}
    if rest:
        yield Spec(f"{table}_rules", f"Home of the {table} file's single set of rules (one row).",
                   [({}, {"id": table, **rest})])


def frozen(eng):
    d = src("terrain/freeze.json")
    rows = [({}, {"id": k, **v}) for k, v in d["frozen"].items()]
    yield Spec("frozen_array", "Home of every frozen terrain and hydrology array's identity (the vault fetcher's "
               "manifest): file name, SHA-256 over its contents, the day it froze and why.", rows,
               check={"sha256": "length({c}) = 64"})
    rest = {k: v for k, v in d.items() if k not in ("frozen", "schemaVersion")}
    if rest:
        yield Spec("freeze_rules", "Home of the freeze record's rules (one row).", [({}, {"id": "freeze", **rest})])


FAMILIES += [routes, sheet, frozen]


FORMID_DDL = """-- == The FormID table (decision 0009 §3, 0030 §4) ==

-- Home of every FormID of ours: an EditorID (`ARG_` plus the world id) to the object id it was first given in its
-- plugin; append-only (an entry never changes and is never removed; the next id is past the highest ever given).
-- `entity_key` is the world row the record is generated from, when it has one. Written only by the allocator
-- (tools/argonia_world/formids.py) through db.py.
CREATE TABLE "formid" (
  "editor_id" TEXT NOT NULL PRIMARY KEY CHECK ("editor_id" GLOB 'ARG_*' AND length("editor_id") <= 99),
  "plugin" TEXT NOT NULL,
  "form_id" INTEGER NOT NULL CHECK ("form_id" BETWEEN 2048 AND 16777215),
  "record_type" TEXT,
  "entity_key" TEXT,
  UNIQUE ("plugin", "form_id")
);
"""

# The families later chunks migrate (decision 0030 §6), designed now as keyed tables: each chunk that first reads
# one adds its columns and rows and deletes its files from world/sources.
KEYED = [
    ("terrain_patch", "the world track (2.W1)", "world/sources/terrain/terrain-patches.json, route-grade-patches.json",
     "a terrain patch over the frozen heightfield"),
    ("hydrology_body", "2.W2", "world/sources/hydrology/*.json", "a water body (lake, river reach, marsh) of the graph"),
    ("hydrology_edge", "2.W2", "world/sources/hydrology/hydrology-graph.json", "a flow edge between two bodies",
     [("from_body_id", "hydrology_body"), ("to_body_id", "hydrology_body")]),
    ("region_class", "2.W3", "world/sources/regions/authored-overrides.json", "an ecological region class and its polygons"),
    ("flora_rule", "2.W4", "world/sources/flora/*.json", "a flora placement rule (species, density, slope, water)"),
    ("anchor", "2.W1", "world/sources/anchors/settlement-anchors.json", "a settlement anchor over the heightfield"),
    ("weather_state", "2.W3", "world/sources/climate/weather-states.json", "a weather state of the calendar"),
    ("star", "2.W4", "world/sources/sky/star-catalogue.json", "a star or patron constellation of the night sky"),
    ("magic_effect", "2.9", "the magic dossier", "a magic effect"),
    ("spell", "2.9", "the magic dossier", "a spell or power"),
    ("recipe", "2.10", "world/sources/economy/, registries/resource-nodes.json", "a crafting recipe"),
    ("trade_class", "2.10", "world/sources/economy/trade-classes.json", "a merchant's trade class and its stock"),
    ("loot_rule", "2.3", "world/sources/registries/loot-rules.json", "a blanket loot rule a container fills from"),
    ("trap", "2.11", "world/sources/registries/traps.json", "a trap"),
    ("hazard_volume", "2.11", "world/sources/registries/hazard-volumes.json", "a hazard volume"),
    ("physical_material", "2.6", "world/sources/registries/physical-materials.json", "a physical material"),
    ("detection_rule", "2.11", "world/sources/registries/detection.json", "a detection rule of the notice service"),
    ("boat_class", "2.8", "world/sources/vocab/boat-classes.json", "a boat class"),
    ("boat", "2.8", "world/sources/placement/boats.json", "a placed boat", [("class_id", "boat_class")]),
    ("blueprint_parcel", "2.W/place builds", "world/sources/blueprints/place.*.json", "a parcel of a place's blueprint",
     [("place_id", "place")]),
    ("blueprint_door", "2.W/place builds", "world/sources/blueprints/place.*.json", "a door of a place's blueprint",
     [("place_id", "place")]),
    ("promise", "the place builds", "world/sources/placement/promises/*.json", "one claim a place's build must keep",
     [("place_id", "place")]),
    ("asset", "the place builds", "world/sources/assets/registry-*.jsonl", "a mesh of a dependency the world may place"),
    ("culture_kit", "the place builds", "world/sources/placement/culture-kits.json", "a culture's kit of pieces"),
]


def keyed_ddl():
    out = ["-- == Keyed tables for the families later chunks migrate (decision 0030 §6) ==", ""]
    for row in KEYED:
        name, chunk, src_, what = row[:4]
        refs = row[4] if len(row) > 4 else []
        out.append(f"-- Home of {what}. Migrated by {chunk} from {src_}; until then a key only.")
        cols = ['  "id" TEXT NOT NULL PRIMARY KEY'] + [f'  "{c}" TEXT REFERENCES "{t}"("id")' for c, t in refs]
        out.append(f'CREATE TABLE "{name}" (\n' + ",\n".join(cols) + "\n);\n")
    return "\n".join(out)
