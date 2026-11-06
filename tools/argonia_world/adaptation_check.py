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
    all_quests: set = field(default_factory=set)


def load() -> Ledger:
    from tools.argonia_world import db
    w = db.load()
    lg = Ledger()
    lg.all_quests = set(w.values("SELECT id FROM quest"))
    for r in w.query("""SELECT a.*, q.line, q.code FROM quest_adaptation a JOIN quest q ON q.id = a.quest"""):
        lg.quests[r["quest"]] = dict(line=r["line"], code=r["code"], verdict=r["verdict"], merged_into=r["merged_into"],
                                     band=r["band"], lore=r["lore"],
                                     text=" ".join(x or "" for x in (r["spirit"], r["premise"], r["changed"])))
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
    for t, es in sorted(changed.items()):
        if len(es) > 1:
            out.append(f"{t}: changed by {len(es)} edits ({', '.join(sorted(es))})")
    named = defaultdict(list)
    for e, ed in lg.edits.items():
        if ed["kind"] == "name_place":
            named[ed["settlement"]].append(e)
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
    for q, t in lg.needs:
        if t in lg.nord:
            out.append(f"{q}: needs {t}, a Nord (0006)")
        if t in lg.levelled and t not in fixed[q]:
            out.append(f"{q}: needs {t}, a levelled actor, without an edit fixing it (0035)")
    return out


CHECKS = (check_coverage, check_hosts, check_edits, check_graph, check_seats, check_danger, check_capacity,
          check_lore, check_nordic_and_levelled)


def run(lg: Ledger) -> list[str]:
    return [f"{c.__name__[6:]}: {f}" for c in CHECKS for f in c(lg)]


def main() -> int:
    findings = run(load())
    for f in findings:
        print(f)
    print(f"adaptation_check: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
