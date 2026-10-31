"""The topic store's L2 fixture as C++ (1.3 §b; goal G11.2): five speakers' lines, topics and condition trees from the
world database, so skse/core's `topics` tests run over real rows and nothing is typed into a source.

The five speakers are the fixture place's people ranked by written lines, then by imported lines (written lines win
for a speaker who has any; a speaker with none lends its imported reference lines to the engine test only, never to
the game, decision 0024 §7). Rendered by `core_tables.py` into skse/core/generated/argonia/core/fixture_topics.h, so
the gate's `core_tables --check` sees a stale fixture.
"""
from __future__ import annotations

from collections import defaultdict

from tools.argonia_world import db

PLACE = "place.imperial-fringe.claywater-station"
SPEAKERS = 5


def _sv(s) -> str:
    if s is None or s == "":
        return '""'
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _num(v) -> str:
    r = repr(float(v))
    return r if ("e" in r or "." in r) else r + ".0"


def _arg(v) -> str:
    if isinstance(v, str):
        return f"{{FxArg::is_text, {_sv(v)}, 0.0}}"
    return f"{{FxArg::is_number, \"\", {_num(v)}}}"


def speakers(w: db.World) -> list[tuple[str, str]]:
    """(npc id, status) of the five fixture speakers."""
    rows = w.query("SELECT speaker, sum(status = 'written') wr, sum(status = 'imported') im FROM dialogue_line "
                   "WHERE place_id = ? AND speaker IS NOT NULL AND type != 'bark' GROUP BY speaker "
                   "ORDER BY wr DESC, im DESC, speaker", PLACE)
    out = [(r["speaker"], "written" if r["wr"] else "imported") for r in rows[:SPEAKERS]]
    if len(out) != SPEAKERS:
        raise SystemExit(f"topic fixture: {PLACE} has {len(out)} speakers with lines, need {SPEAKERS}")
    return out


def render(w: db.World) -> list[str]:
    sp = speakers(w)
    lines = []
    for npc, status in sp:
        lines += w.query("SELECT * FROM dialogue_line WHERE speaker = ? AND status = ? AND type != 'bark' "
                         "ORDER BY id", npc, status)
    links = defaultdict(list)
    for r in w.query("SELECT dialogue_line_id, value FROM dialogue_line_link ORDER BY dialogue_line_id, ord"):
        links[r[0]].append(r[1])
    topic_ids = sorted({l["keys_topic"] for l in lines if l["keys_topic"]} | {t for l in lines for t in links[l["id"]]})
    essential = set(w.values("SELECT value FROM quest_essential_topic"))

    # Condition trees, preorder; parent is the index within the tree (-1 for the root).
    kids = defaultdict(list)
    terms, cargs = {}, defaultdict(list)
    for r in w.query("SELECT id, parent_id, ord, term FROM condition ORDER BY parent_id, ord"):
        terms[r["id"]] = r["term"]
        if r["parent_id"]:
            kids[r["parent_id"]].append(r["id"])
    for r in w.query("SELECT condition_id, value FROM condition_arg ORDER BY condition_id, ord"):
        cargs[r[0]].append(r[1])
    nodes, args, conds = [], [], []

    def tree(root: str) -> int:
        first = len(nodes)
        stack = [(root, -1)]
        while stack:
            cid, parent = stack.pop()
            at = len(nodes) - first
            a = cargs.get(cid, [])
            nodes.append(f"    {{{parent}, {_sv(terms[cid])}, {len(args)}, {len(a)}}},")
            args.extend(_arg(v) for v in a)
            stack.extend((k, at) for k in reversed(kids.get(cid, [])))
        conds.append(f"    {{{first}, {len(nodes) - first}}},")
        return len(conds) - 1

    acts, aargs, alists = [], [], []
    a_args = defaultdict(list)
    for r in w.query("SELECT list_id, ord, value FROM action_arg ORDER BY list_id, ord, arg_ord"):
        a_args[(r[0], r[1])].append(r[2])

    def action_list(lid: str) -> int:
        first = len(acts)
        for r in w.query("SELECT ord, term FROM action WHERE list_id = ? ORDER BY ord", lid):
            a = a_args[(lid, r["ord"])]
            acts.append(f"    {{{_sv(r['term'])}, {len(aargs)}, {len(a)}}},")
            aargs.extend(_arg(v) for v in a)
        alists.append(f"    {{{_sv(lid)}, {first}, {len(acts) - first}}},")
        return len(alists) - 1

    out_lines, link_rows = [], []
    for l in lines:
        c = tree(l["available"]) if l["available"] else -1
        a = action_list(l["on_delivered"]) if l["on_delivered"] else -1
        ls = links[l["id"]]
        out_lines.append(f"    {{{_sv(l['id'])}, {_sv(l['type'])}, {_sv(l['speaker'])}, {_sv(l['keys_topic'])}, "
                         f"{_sv(l['words'])}, {_sv(l['variants_low'])}, {_sv(l['variants_high'])}, {c}, "
                         f"{len(link_rows)}, {len(ls)}, {a}}},")
        link_rows += [_sv(t) for t in ls]
    forms, topics = [], []
    for tid in topic_ids:
        t = w.get("topic", tid)
        f = w.values("SELECT f.value FROM glossary_form f JOIN glossary_term g ON g.id = f.glossary_term_id "
                     "WHERE g.topic_id = ? ORDER BY g.id, f.ord", tid)
        topics.append(f"    {{{_sv(tid)}, {_sv(t.label)}, {len(forms)}, {len(f)}, "
                      f"{'true' if tid in essential else 'false'}, {'true' if t.topic_class == 'service' else 'false'}}},")
        forms += [_sv(x) for x in f]

    def arr(typ: str, name: str, rows: list[str], per_line: bool = True) -> list[str]:
        if not rows:
            return [f"inline constexpr std::array<{typ}, 0> {name}{{}};"]
        if per_line:
            return [f"inline constexpr std::array<{typ}, {len(rows)}> {name}{{{{", *rows, "}};"]
        return [f"inline constexpr std::array<{typ}, {len(rows)}> {name}{{", *[f"    {r}," for r in rows], "};"]

    b = ["// The fixture speakers and the status of the lines each lends (written, or imported reference lines).",
         "struct FxSpeaker { std::string_view id, status; };",
         *arr("FxSpeaker", "kSpeakers", [f"    {{{_sv(n)}, {_sv(s)}}}," for n, s in sp]), "",
         "struct FxArg { enum Kind : std::uint8_t { is_text, is_number } kind; std::string_view text; double number; };",
         "struct FxNode { int parent; std::string_view term; std::size_t first_arg, arg_count; };  // preorder",
         "struct FxCond { std::size_t first_node, node_count; };",
         "struct FxAction { std::string_view verb; std::size_t first_arg, arg_count; };",
         "struct FxActionList { std::string_view id; std::size_t first, count; };",
         "struct FxTopic { std::string_view id, label; std::size_t first_form, form_count; bool essential, service; };",
         "struct FxLine {", "  std::string_view id, type, speaker, topic, words, low, high;",
         "  int cond;  // into kConds; -1: always available",
         "  std::size_t first_link, link_count;", "  int actions;  // into kActionLists; -1: none", "};", "",
         *arr("FxTopic", "kTopics", topics), *arr("std::string_view", "kForms", forms, False),
         *arr("FxLine", "kLines", out_lines), *arr("std::string_view", "kLinks", link_rows, False),
         *arr("FxNode", "kNodes", nodes), *arr("FxArg", "kArgs", [f"    {a}," for a in args]), *arr("FxCond", "kConds", conds),
         *arr("FxAction", "kActions", acts), *arr("FxArg", "kActionArgs", [f"    {a}," for a in aargs]),
         *arr("FxActionList", "kActionLists", alists)]
    return ["namespace fixture {", "", *b, "", "}  // namespace fixture"]
