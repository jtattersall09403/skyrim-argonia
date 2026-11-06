"""The adaptation ledger's checks over the whole set (phase 2, story/design/quests/adaptation.md).

    python3 -m tools.argonia_world.adaptation_check          # every check; exit 1 on any finding

Reads the story data through db.py: quest_adaptation, quest_host, quest_prereq, world_edit, quest_world_edit,
quest_bmv_need, line_hub, line_exclusion and the bmv_* census. Each check is a pure function of `Ledger`, so the
unit test (tools/tests/test_adaptation_check.py) builds small ledgers by hand.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIVE = ("keep", "adapt")
SHARED_PREFIXES = ("we.name.", "we.door.", "we.people.")   # the allocation's own edits, needed by the plan itself
REMOVING = ("npc_remove", "npc_change", "npc_move", "creature_remove", "ref_disable", "record_change")
NORDIC = re.compile(r"\b(draugr\w*|nords?|nordic|jarls?|skaal|sovngarde|dragon ?priests?|barrows?|thanes?|"
                    r"stormcloaks?|ysgramor|windhelm|whiterun|solitude|riften|markarth|falkreath|dawnstar|"
                    r"winterhold|morthal)\b", re.I)
NORD_RACES = ("NordRace", "NordRaceVampire", "Nord")
MAX_RISE = 2
PLACE_MAKING = ("place_new", "interior_new", "interior_copy", "land_new")


@dataclass
class Ledger:
    quests: dict = field(default_factory=dict)        # quest id -> {line, code, verdict, merged_into, band, lore, text}
    hosts: list = field(default_factory=list)         # (quest, settlement, cell, role, edit)
    prereqs: list = field(default_factory=list)       # (quest, needs)
    edits: dict = field(default_factory=dict)         # id -> {kind, settlement, cell, target, race, band, lore, text}
    quest_edits: list = field(default_factory=list)   # (quest, edit)
    needs: list = field(default_factory=list)         # (quest, target)
    hubs: list = field(default_factory=list)          # (line, settlement, cell, role, edit)
    exclusions: list = field(default_factory=list)    # (line, other)
    settlement_cells: set = field(default_factory=set)  # (settlement, cell)
    capacity: dict = field(default_factory=dict)      # settlement -> (people, interiors)
    levelled: set = field(default_factory=set)        # form keys of LVLN bases and their placements
    nord: set = field(default_factory=set)            # form keys of Nord-race bases and their placements
    levelled_at: dict = field(default_factory=dict)   # settlement -> placements that may scale (LVLN or templated)
    edit_targets: dict = field(default_factory=dict)  # edit -> every form it acts on
    levelled_in: dict = field(default_factory=dict)   # cell -> placements that may scale there
    no_navmesh: set = field(default_factory=set)      # cells without navmesh
    all_quests: set = field(default_factory=set)


def load() -> Ledger:
    from tools.argonia_world import db
    w = db.load()
    lg = Ledger()
    lg.all_quests = set(w.values("SELECT id FROM quest"))
    for r in w.query("""SELECT a.*, q.line, q.code FROM quest_adaptation a JOIN quest q ON q.id = a.quest"""):
        lg.quests[r["quest"]] = dict(line=r["line"], code=r["code"], verdict=r["verdict"], merged_into=r["merged_into"],
                                     band=r["band"], lore=r["lore"],
                                     text=" ".join(x or "" for x in (r["spirit"], r["premise"], r["changed"])),
                                     premise=r["premise"])
    lg.hosts = [tuple(r) for r in w.query("SELECT quest, settlement, cell, role, edit FROM quest_host")]
    lg.prereqs = [tuple(r) for r in w.query("SELECT quest, needs FROM quest_prereq")]
    for r in w.query("SELECT * FROM world_edit"):
        lg.edits[r["id"]] = dict(kind=r["kind"], settlement=r["settlement"], cell=r["cell"], target=r["target"],
                                 race=r["race"], band=r["band"], lore=r["lore"], text=r["description"])
    lg.quest_edits = [tuple(r) for r in w.query("SELECT quest, edit FROM quest_world_edit")]
    lg.needs = [tuple(r) for r in w.query("SELECT quest, target FROM quest_bmv_need")]
    lg.hubs = [tuple(r) for r in w.query("SELECT line, settlement, cell, role, edit FROM line_hub")]
    lg.exclusions = [tuple(r) for r in w.query("SELECT line, other FROM line_exclusion")]
    lg.settlement_cells = {tuple(r) for r in w.query("SELECT settlement, cell FROM bmv_settlement_cell")}
    for r in w.query("""SELECT s.id,
          (SELECT count(*) FROM bmv_placement p JOIN bmv_settlement_cell c ON c.cell = p.cell
             JOIN bmv_npc n ON n.id = p.npc WHERE c.settlement = s.id AND n.person) AS people,
          (SELECT count(*) FROM bmv_settlement_cell c WHERE c.settlement = s.id AND c.role = 'interior') AS ints
        FROM bmv_settlement s"""):
        lg.capacity[r["id"]] = (r["people"], r["ints"])
    lg.levelled = set(w.values("SELECT id FROM bmv_npc WHERE record = 'LVLN'")) | set(w.values(
        "SELECT p.id FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc WHERE n.record = 'LVLN'"))
    for c, pid in w.query("""SELECT p.cell, p.id FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc
            WHERE n.record = 'LVLN' OR n.template IS NOT NULL"""):
        lg.levelled_in.setdefault(c, set()).add(pid)
    for s, pid in w.query("""SELECT c.settlement, p.id FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc
            JOIN bmv_settlement_cell c ON c.cell = p.cell
            WHERE n.record = 'LVLN' OR n.template IS NOT NULL"""):
        lg.levelled_at.setdefault(s, set()).add(pid)
    for e, tg in w.query("SELECT edit, target FROM world_edit_target"):
        lg.edit_targets.setdefault(e, set()).add(tg)
    lg.no_navmesh = set(w.values("SELECT id FROM bmv_cell WHERE NOT has_navmesh"))
    nord_races = set(w.values("SELECT id FROM bmv_race WHERE editor_id LIKE 'Nord%'")) if _has_col(
        w, "bmv_race", "editor_id") else set()
    lg.nord = set(w.values(f"SELECT id FROM bmv_npc WHERE race IN ({','.join('?' * len(nord_races)) or 'NULL'})",
                           *nord_races))
    lg.nord |= set(w.values(f"SELECT p.id FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc "
                            f"WHERE n.race IN ({','.join('?' * len(nord_races)) or 'NULL'})", *nord_races))
    return lg


def _has_col(w, table: str, col: str) -> bool:
    return col in w.table(table).names


def capacity(people: int, interiors: int, added: int) -> int:
    """How many live quests may start or centre on a settlement: a few anyway, more for people and rooms."""
    return 2 + (people + added) // 3 + 2 * interiors


def check_coverage(lg: Ledger) -> list[str]:
    if not lg.quests:      # the ledger is not written yet: nothing to cover
        return []
    out = [f"{q}: no adaptation row" for q in sorted(lg.all_quests - set(lg.quests))]
    hosted = defaultdict(int)
    for q, *_ in lg.hosts:
        hosted[q] += 1
    for q, a in sorted(lg.quests.items()):
        if a["verdict"] in LIVE and not hosted[q]:
            out.append(f"{q}: kept but has no host")
        if a["verdict"] not in LIVE and hosted[q]:
            out.append(f"{q}: {a['verdict']} but still has hosts")
        if a["verdict"] == "merge" and lg.quests.get(a["merged_into"], {}).get("verdict") not in LIVE:
            out.append(f"{q}: merged into {a['merged_into']}, which is not kept")
    return out


def check_hosts(lg: Ledger) -> list[str]:
    """A host cell is in its settlement, or a door or copied interior linked to the quest provides it."""
    provided = defaultdict(set)
    for q, e in lg.quest_edits:
        ed = lg.edits.get(e)
        if ed and ed["kind"] in ("door_add", "interior_copy") and ed["cell"]:
            provided[q].add(ed["cell"])
    door_cells = {ed["cell"]: ed["settlement"] for ed in lg.edits.values() if ed["kind"] == "door_add" and ed["cell"]}
    out = []
    linked = defaultdict(set)
    for q, e in lg.quest_edits:
        linked[q].add(e)
    for q, s, c, _, e in lg.hosts:
        if e:
            ed = lg.edits.get(e)
            if not ed or ed["kind"] not in PLACE_MAKING:
                out.append(f"{q}: host edit {e} is not a ledgered place-making edit")
            elif e not in linked[q] and not e.startswith(SHARED_PREFIXES):
                out.append(f"{q}: hosted by {e} but does not list it as needed")
            continue
        if c and (s, c) not in lg.settlement_cells and c not in provided[q] and door_cells.get(c) != s:
            out.append(f"{q}: host cell {c} is not in {s} and no linked edit gives it a door there")
    return out


def check_edits(lg: Ledger) -> list[str]:
    out = []
    used = {e for _, e in lg.quest_edits}
    for e, ed in sorted(lg.edits.items()):
        if e not in used and not e.startswith(SHARED_PREFIXES):
            out.append(f"{e}: world edit no quest needs")
        if ed["kind"] in ("npc_add", "creature_add") and ed["band"] is None:
            out.append(f"{e}: an added actor without a fixed band (0035)")
        if ed["kind"] == "npc_add" and not ed["race"]:
            out.append(f"{e}: an added person without a race")
    need_by = defaultdict(set)
    for q, t in lg.needs:
        need_by[t].add(q)
    users = defaultdict(set)
    for q, e in lg.quest_edits:
        users[e].add(q)
    changed = defaultdict(list)
    for e, ed in lg.edits.items():
        if ed["kind"] in REMOVING and ed["target"]:
            changed[ed["target"]].append(e)
            for q in sorted(need_by[ed["target"]] - users[e]):
                out.append(f"{e}: {ed['kind']} of {ed['target']}, which {q} needs as it stands")
    for e, ts in lg.edit_targets.items():
        for t in ts:
            changed[t].append(e)
    for t, es in sorted(changed.items()):
        es = sorted(set(es))
        if len(es) > 1:
            out.append(f"{t}: changed by {len(es)} edits ({', '.join(sorted(es))})")
    named = defaultdict(list)
    for e, ed in lg.edits.items():
        if ed["kind"] == "name_place":
            named[ed["cell"] or ed["settlement"]].append(e)
    for s, es in sorted(named.items()):
        if len(es) > 1:
            out.append(f"{s}: named twice ({', '.join(sorted(es))})")
    return out


def check_graph(lg: Ledger) -> list[str]:
    out = []
    graph = defaultdict(set)
    for q, n in lg.prereqs:
        graph[q].add(n)
        if lg.quests.get(n, {}).get("verdict") not in LIVE:
            out.append(f"{q}: needs {n}, which is not kept")
    by_line = defaultdict(list)
    for q, a in lg.quests.items():
        if a["verdict"] in LIVE:
            by_line[a["line"]].append((a["code"], q))
    for line, qs in by_line.items():
        if line.endswith((".local", ".daedric", ".proposed")):
            continue
        qs.sort()
        for (_, a), (_, b) in zip(qs, qs[1:]):
            graph[b].add(a)
    state: dict[str, int] = {}

    def visit(n, path):
        if state.get(n) == 1:
            out.append("prerequisite cycle: " + " -> ".join(path[path.index(n):] + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in sorted(graph[n]):
            visit(m, path + [n])
        state[n] = 2
    for n in sorted(graph):
        visit(n, [])
    excl = {frozenset(x) for x in lg.exclusions}
    for q, n in lg.prereqs:
        la, lb = lg.quests.get(q, {}).get("line"), lg.quests.get(n, {}).get("line")
        if frozenset((la, lb)) in excl:
            out.append(f"{q} needs {n} across exclusive lines {la} and {lb}")
    return out


def check_seats(lg: Ledger) -> list[str]:
    out = []
    seats = defaultdict(set)
    for line, s, c, role, e in lg.hubs:
        if e and (e not in lg.edits or lg.edits[e]["kind"] not in PLACE_MAKING):
            out.append(f"{line}: hub edit {e} is not a ledgered place-making edit")
        if role == "seat":
            seats[(s, c, e)].add(line)
    for k, ls in sorted(seats.items(), key=str):
        if len(ls) > 1:
            out.append(f"seat {k} shared by {', '.join(sorted(ls))}")
    return out


def check_danger(lg: Ledger) -> list[str]:
    out = []
    by_line = defaultdict(list)
    for q, a in lg.quests.items():
        if a["verdict"] in LIVE and a["band"] is not None:
            by_line[a["line"]].append((a["code"], q, a["band"]))
    for line, qs in sorted(by_line.items()):
        if line.endswith((".local", ".daedric")):
            continue
        peak = None
        for code, q, band in sorted(qs):
            if peak is not None and band > peak + MAX_RISE:
                out.append(f"{q}: band {band} jumps more than {MAX_RISE} over the line's earlier peak {peak}")
            peak = band if peak is None else max(peak, band)
    return out


def check_capacity(lg: Ledger) -> list[str]:
    load_ = defaultdict(set)
    for q, s, _, role, e in lg.hosts:
        if role in ("start", "main") and lg.quests.get(q, {}).get("verdict") in LIVE:
            load_[s or e].add(q)
    added = defaultdict(int)
    for ed in lg.edits.values():
        if ed["kind"] == "npc_add" and (ed["settlement"] or ed["cell"]):
            m = re.match(r"\s*(\w+)", ed["text"] or "")
            words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
            n = (m and (int(m.group(1)) if m.group(1).isdigit() else words.get(m.group(1).lower()))) or 1
            added[ed["settlement"] or ed["cell"]] += n
    out = []
    for s, qs in sorted(load_.items()):
        people, ints = lg.capacity.get(s, (0, 0))   # a place an edit makes starts with none
        cap = capacity(people, ints, added[s])
        if len(qs) > cap:
            out.append(f"{s}: {len(qs)} quests start or centre here, capacity {cap} "
                       f"({people} people, {added[s]} added, {ints} interiors)")
    return out


def _lore_ok(ref: str | None, root: Path) -> bool:
    if not ref:
        return False
    m = re.search(r"(story/lore/[\w./-]+\.(?:md|json))", ref)
    return bool(m) and (root / m.group(1)).exists()


def check_lore(lg: Ledger, root: Path = ROOT) -> list[str]:
    out = [f"{q}: lore citation missing or not a story/lore file: {a['lore']!r}"
           for q, a in sorted(lg.quests.items()) if a["verdict"] in LIVE and not _lore_ok(a["lore"], root)]
    out += [f"{e}: lore citation missing or not a story/lore file: {ed['lore']!r}"
            for e, ed in sorted(lg.edits.items()) if not _lore_ok(ed["lore"], root)]
    return out


def check_nordic_and_levelled(lg: Ledger) -> list[str]:
    out = []
    for q, a in sorted(lg.quests.items()):
        if a["verdict"] in LIVE and NORDIC.search(a["text"]):
            out.append(f"{q}: Nordic element in its text ({NORDIC.search(a['text']).group(0)}; 0006)")
    for e, ed in sorted(lg.edits.items()):
        if ed["kind"] in ("npc_add", "creature_add", "ref_place") and NORDIC.search(ed["text"] or ""):
            out.append(f"{e}: adds a Nordic element ({NORDIC.search(ed['text']).group(0)}; 0006)")
        if (ed["race"] or "") in NORD_RACES:
            out.append(f"{e}: adds a Nord (0006)")
    fixed = defaultdict(set)
    for q, e in lg.quest_edits:
        ed = lg.edits.get(e)
        if ed and ed["target"] and ed["kind"] in REMOVING:
            fixed[q].add(ed["target"])
    whole = {(q, s) for q, s, c, *_ in lg.hosts if s and not c}
    for q, s, c, *_ in lg.hosts:
        scaling = lg.levelled_at.get(s, set()) if (q, s) in whole else lg.levelled_in.get(c, set())
        if s and scaling and lg.quests.get(q, {}).get("verdict") in LIVE:
            clean = "we.clean." + s.split(".")[-1]
            if (q, clean) not in set(lg.quest_edits):
                out.append(f"{q}: hosted at {c or s}, which has {len(scaling)} placement(s) that may scale and "
                           f"no clean-up edit {clean} linked (0035)")
            else:
                left = scaling - lg.edit_targets.get(clean, set())
                if left:
                    out.append(f"{q}: {clean} leaves {len(left)} placement(s) that may scale (first {min(left)}; 0035)")
    for q, t in lg.needs:
        if t in lg.nord:
            out.append(f"{q}: needs {t}, a Nord (0006)")
        if t in lg.levelled and t not in fixed[q]:
            out.append(f"{q}: needs {t}, a levelled actor, without an edit fixing it (0035)")
    return out


def check_navmesh(lg: Ledger) -> list[str]:
    """An actor placed in a cell without navmesh cannot walk: a linked navmesh_add must give it one."""
    out = []
    meshed = defaultdict(set)
    for q, e in lg.quest_edits:
        ed = lg.edits.get(e)
        if ed and ed["kind"] == "navmesh_add" and ed["cell"]:
            meshed[q].add(ed["cell"])
    for q, e in sorted(lg.quest_edits):
        ed = lg.edits.get(e)
        if ed and ed["kind"] == "npc_add" and ed["cell"] in lg.no_navmesh and ed["cell"] not in meshed[q]:
            out.append(f"{q}: {e} places people in {ed['cell']}, which has no navmesh, and no navmesh_add is linked")
    return out


CHECKS = (check_navmesh, check_coverage, check_hosts, check_edits, check_graph, check_seats, check_danger, check_capacity,
          check_lore, check_nordic_and_levelled)



# Procedure and bureaucracy words (owner, 2026-11-06: an arbitration resolving a quest is "the classic boring
# bureaucracy issue"; story/design/province-vibe.md's "what jars"). A hit is a warning for the planner's triage, not a
# failure: a word may be licensed (Gideon's courthouse, a port's customs) or describe what was removed.
PROCEDURE = re.compile(r"\b(arbitrat\w*|hearings?|tribunals?|trials?|rulings?|verdicts?|courts?|testimon\w*|"
                       r"witness(?:es|ed)?|ledgers?|tall(?:y|ies)|registers?|rolls?|clerks?|permits?|petitions?|"
                       r"writs?|decrees?|paperwork|contracts?|couriers?|letters?|papers?|fines?|negotiat\w*)\b", re.I)


def motif_warnings(lg: Ledger, stages: dict | None = None) -> list[str]:
    """Each adapted quest's premise, and its stages' journal text when given, scanned for procedure words."""
    out = []
    for q, r in sorted(lg.quests.items()):
        if r["verdict"] not in ("keep", "adapt"):
            continue
        hits = sorted({m.lower() for m in PROCEDURE.findall(r.get("premise") or "")})
        if hits:
            out.append(f"{q} premise: {', '.join(hits)}")
        for sid, text in (stages or {}).get(q, []):
            hits = sorted({m.lower() for m in PROCEDURE.findall(text or "")})
            if hits:
                out.append(f"{q} {sid}: {', '.join(hits)}")
    return out


# ---- record rules (2026-11-06): what quest-review used to judge by hand and a program can check. Warnings until the
# current rows are clean; each returns "<quest or edit>: <what>" lines.
VANILLA = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm")
FORM_KEY = re.compile(r"\b[0-9A-F]{6}:[A-Za-z][\w .&'-]*?\.es[mpl]\b")
FREE_TERMS = {"all", "any", "inZone", "inCell", "inSettlement", "timeOfDay", "questStage", "stageEverReached",
              "knowsTopic", "topicHeardFrom", "flag"}


@dataclass
class Records:
    census: set = field(default_factory=set)          # every bmv_* form key
    base_placements: dict = field(default_factory=dict)  # bmv_npc base -> placements
    door_base: dict = field(default_factory=dict)     # bmv_door -> its DOOR base key
    texts: list = field(default_factory=list)         # (owner, text) scanned for form keys
    needs: list = field(default_factory=list)         # (owner, form key) that must be in the census
    names: dict = field(default_factory=dict)         # npc id -> name
    people: list = field(default_factory=list)        # (quest, npc) speakers and cast
    placing: str = ""                                 # every text that places someone (edits, actor things, needs)
    quest_text: dict = field(default_factory=dict)    # quest -> foundation and notes
    stages: dict = field(default_factory=dict)        # quest -> {stage: {"succ": [(to, terms, args)], "ff": set}}
    topics: list = field(default_factory=list)        # (quest, npc, essential, {stages})
    edits: dict = field(default_factory=dict)         # edit -> (kind, target)
    edit_targets: dict = field(default_factory=dict)  # edit -> forms
    quest_forms: dict = field(default_factory=dict)   # quest -> form keys it uses
    live: set | None = None                           # quests kept or adapted; None checks every quest


def _tree(w) -> dict:
    kids, terms, args = defaultdict(list), {}, defaultdict(set)
    for r in w.query("SELECT id, parent_id, term FROM condition"):
        terms[r["id"]] = r["term"]
        if r["parent_id"]:
            kids[r["parent_id"]].append(r["id"])
    for r in w.query("SELECT condition_id, value FROM condition_arg"):
        args[r["condition_id"]].add(str(r["value"]))

    def walk(c):
        t, a = {terms.get(c)}, set(args[c])
        for k in kids[c]:
            kt, ka = walk(k)
            t |= kt
            a |= ka
        return t, a
    return {c: walk(c) for c in terms}


def load_records() -> Records:
    from tools.argonia_world import db
    w = db.load()
    rc = Records()
    for t in ("bmv_worldspace", "bmv_location", "bmv_cell", "bmv_race", "bmv_class", "bmv_faction", "bmv_npc",
              "bmv_placement", "bmv_quest", "bmv_door", "bmv_map_marker", "bmv_book"):
        rc.census |= set(w.values(f"SELECT id FROM {t}"))
    rc.base_placements = {r[0]: r[1] for r in w.query("SELECT npc, count(*) FROM bmv_placement GROUP BY npc")}
    rc.door_base = {r[0]: r[1] for r in w.query("SELECT id, base FROM bmv_door")}
    for r in w.query("SELECT id, kind, cell, target, description FROM world_edit"):
        rc.edits[r["id"]] = (r["kind"], r["target"])
        rc.texts.append((r["id"], r["description"]))
        rc.needs += [(r["id"], k) for k in (r["cell"], r["target"]) if k]
        rc.placing += " " + r["description"]
    for e, t in w.query("SELECT edit, target FROM world_edit_target"):
        rc.edit_targets.setdefault(e, set()).add(t)
        rc.needs.append((e, t))
    for q, t, what in w.query("SELECT quest, target, what FROM quest_bmv_need"):
        rc.needs.append((q, t))
        rc.placing += " " + what
        rc.quest_forms.setdefault(q, set()).add(t)
    for r in w.query('SELECT quest_id, kind, source, "where" FROM quest_thing'):
        txt = f"{r['source']} {r['where'] or ''}"
        rc.texts.append((r["quest_id"], txt))
        rc.quest_forms.setdefault(r["quest_id"], set()).update(FORM_KEY.findall(txt))
        if r["kind"] == "actors":
            rc.placing += " " + txt
    for q, e in w.query("SELECT quest, edit FROM quest_world_edit"):
        ed = rc.edits.get(e)
        if ed and ed[1]:
            rc.quest_forms.setdefault(q, set()).add(ed[1])
    rc.live = set(w.values("SELECT quest FROM quest_adaptation WHERE verdict IN ('keep', 'adapt')"))
    rc.names = {r[0]: r[1] for r in w.query("SELECT id, name FROM npc")}
    rc.people = sorted({tuple(r) for r in w.query("SELECT quest_id, person FROM quest_topic")} |
                       {tuple(r) for r in w.query("SELECT quest_id, id FROM quest_cast")})
    rc.quest_text = {r[0]: f"{r[1] or ''} {r[2] or ''}" for r in w.query("SELECT id, foundation, notes FROM quest")}
    tree = _tree(w)
    sid = {(r[0], r[1]): r[2] for r in w.query("SELECT quest_id, ord, id FROM quest_stage")}
    for (q, o), s in sid.items():
        rc.stages.setdefault(q, {})[s] = {"succ": [], "ff": set()}
    for r in w.query('SELECT quest_id, stages_ord, "to", "when" FROM quest_successor'):
        t, a = tree.get(r["when"], (set(), set()))
        rc.stages[r["quest_id"]][sid[(r["quest_id"], r["stages_ord"])]]["succ"].append((r["to"], t, a))
    for r in w.query('SELECT quest_id, stages_ord, "when" FROM quest_fail_forward'):
        rc.stages[r["quest_id"]][sid[(r["quest_id"], r["stages_ord"])]]["ff"] |= tree.get(r["when"], (set(), set()))[1]
    st = defaultdict(set)
    for r in w.query("SELECT quest_id, topics_ord, value FROM quest_topic_stage"):
        st[(r[0], r[1])].add(r[2])
    rc.topics = [(r[0], r[2], bool(r[3]), st[(r[0], r[1])])
                 for r in w.query("SELECT quest_id, ord, person, essential FROM quest_topic")]
    return rc


def rule_census_ids(rc: Records) -> list[str]:
    """Every form key a row names is a census row (free text: BM&V's own plugins only)."""
    out = {f"{o}: {k} is not in the census" for o, k in rc.needs if FORM_KEY.fullmatch(k) and k not in rc.census}
    for o, txt in rc.texts:
        for k in FORM_KEY.findall(txt or ""):
            if k.split(":", 1)[1] not in VANILLA and k not in rc.census:
                out.add(f"{o}: {k} is not in the census")
    return sorted(out)


def rule_placed(rc: Records) -> list[str]:
    """A speaker or cast member is placed: some edit, actor thing or BM&V need names them."""
    out = []
    for q, p in rc.people:
        name = rc.names.get(p) or ""
        if p not in rc.placing and not (name and name in rc.placing):
            out.append(f"{q}: {p} ({name}) speaks or acts but no edit, actor thing or need places them")
    return out


def _guarded(text: str, name: str) -> bool:
    return any(name in s and re.search(r"\b(essential|protected)\b", s) for s in re.split(r"(?<=[.;])\s", text))


def rule_helgen(rc: Records) -> list[str]:
    """Someone a stage needs (an essential topic's speaker there, or named in its successors) is essential or protected
    in the record's text, or the stage fails forward on them (Helgen's Hadvar and Ralof)."""
    need = defaultdict(set)
    for q, p, ess, sts in rc.topics:
        if ess:
            for s in sts:
                need[(q, s)].add(p)
    for q, sts in rc.stages.items():
        for s, d in sts.items():
            for _, _, a in d["succ"]:
                need[(q, s)] |= {x for x in a if x.startswith("npc.")}
    out = []
    for (q, s), ps in sorted(need.items(), key=str):
        ff = rc.stages.get(q, {}).get(s, {}).get("ff", set())
        for p in sorted(ps):
            name = rc.names.get(p) or p
            if p not in ff and not _guarded(rc.quest_text.get(q, ""), name):
                out.append(f"{q}: stage {s} needs {name} alive, who is not essential or protected and has no fail-forward")
    return out


def rule_shared_base(rc: Records) -> list[str]:
    """An edit to an actor base changes every placement of it."""
    return [f"{e}: {k} of base {t}, which has {rc.base_placements[t]} placements (edit the placement instead)"
            for e, (k, t) in sorted(rc.edits.items())
            if k in ("npc_change", "record_change") and rc.base_placements.get(t, 0) > 1]


def rule_vanilla_door(rc: Records) -> list[str]:
    """A door a quest uses shows no vanilla Skyrim model unless a record_change re-models it (0006)."""
    fixed = set()
    for e, (k, t) in rc.edits.items():
        if k == "record_change":
            fixed |= {t} | rc.edit_targets.get(e, set())
    out = []
    for q, forms in sorted(rc.quest_forms.items()):
        for d in sorted(forms):
            b = rc.door_base.get(d)
            if b and b.split(":", 1)[-1] in VANILLA and d not in fixed:
                out.append(f"{q}: door {d} uses vanilla model {b} and no record_change re-models it (0006)")
    return out


def rule_skill_gate(rc: Records) -> list[str]:
    """A skill-gated successor is not doubled by a free one to the same stage."""
    out = []
    for q, sts in sorted(rc.stages.items()):
        for s, d in sorted(sts.items()):
            for to, t, _ in d["succ"]:
                if "skillAtLeast" in t and any(to2 == to and t2 <= FREE_TERMS for to2, t2, _ in d["succ"]):
                    out.append(f"{q}: stage {s} -> {to} is skill-gated, but a free successor walks round it")
    return out


RULES = (rule_census_ids, rule_placed, rule_helgen, rule_shared_base, rule_vanilla_door, rule_skill_gate)


def record_warnings(rc: Records) -> list[str]:
    live = lambda f: rc.live is None or not f.startswith("quest.") or f.split(":")[0] in rc.live
    return [f"{r.__name__[5:]}: {f}" for r in RULES for f in r(rc) if live(f)]


def run(lg: Ledger) -> list[str]:
    return [f"{c.__name__[6:]}: {f}" for c in CHECKS for f in c(lg)]


def main() -> int:
    lg = load()
    findings = run(lg)
    for f in findings:
        print(f)
    from tools.argonia_world import db
    stages: dict = {}
    for row in db.load().query("SELECT quest_id, id, journal FROM quest_stage"):
        stages.setdefault(row["quest_id"], []).append((row["id"], row["journal"]))
    warns = motif_warnings(lg, stages)
    for w in warns:
        print(f"motif (warning): {w}")
    recs = record_warnings(load_records())
    for w in recs:
        print(f"record: {w}")
    print(f"adaptation_check: {len(findings) + len(recs)} finding(s), {len(warns)} procedure-word warning(s)")
    return 1 if findings or recs else 0


if __name__ == "__main__":
    sys.exit(main())
