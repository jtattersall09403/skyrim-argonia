#!/usr/bin/env python3
"""Build one dialogue brief per cast member, and one journal brief, from a quest record (quest-record.md).

Usage: python3 brief.py QUEST.yaml OUT_DIR [--place-facts EXTRA.json ...] [--repo ROOT]

Reads the imported world: the person registry (world/sources/registries/npcs.json) for each cast member's
race, sex, role, look and home; the place's stance file (world/sources/dialogue/stance/<slug>.json) for
voice and culture chain; the culture sheets (world/sources/dialogue/cultures/) named in the chain; the place
facts (world/sources/placement/facts/<settlement>.json, and each anchor place that has one); the topic web
(world/sources/dialogue/topics.json); the condition vocabulary (docs/design/quests/85-condition-vocabulary.md).
Every reference must resolve and every condition and action must be a vocabulary term, or no brief is written.
"""
import argparse
import glob
import json
import pathlib
import re
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
VOICES = HERE.parent / "dialogue-write" / "voices.md"
WEAPONS = ["long-blade", "short-blade", "axe", "blunt-weapon", "spear", "marksman", "hand-to-hand"]
STAGE_FIELDS = ["id", "place", "journal", "onEnter", "objectives", "successors"]


def voice_row(race: str) -> str:
    for line in VOICES.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == race.lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


def vocabulary(root):
    t = (root / "docs/design/quests/85-condition-vocabulary.md").read_text()
    a, b = t[t.index("## A."):t.index("## B.")], t[t.index("## B."):t.index("## C.")]
    preds = set()
    for m in re.finditer(r"^\| `([^`]+)`(?: / `([^`]+)`)?(?: / `([^`]+)`)?", a, re.M):
        preds |= {x for x in m.groups() if x}
    return preds, set(re.findall(r"`([a-zA-Z]+)\(", b))


def check_condition(c, preds, where, out):
    if isinstance(c, dict):
        for k, v in c.items():
            if k in ("all", "any"):
                for x in v:
                    check_condition(x, preds, where, out)
            elif k == "not":
                check_condition(v, preds, where, out)
            elif k not in preds:
                out.append(f"{where}: {k!r} is not a predicate in 85-condition-vocabulary.md §A")
    else:
        out.append(f"{where}: condition {c!r} is not a vocabulary term")


def check_actions(acts, verbs, where, out):
    for x in acts or []:
        if not isinstance(x, dict) or len(x) != 1 or next(iter(x)) not in verbs:
            out.append(f"{where}: {x!r} is not an action in 85-condition-vocabulary.md §B")


def load_world(root, q, extra):
    npcs = {e["id"]: e for e in json.loads((root / "world/sources/registries/npcs.json").read_text())["entries"]}
    claims, places = {}, [q.get("settlement")] + list(q.get("anchorPlaces", []))
    for p in dict.fromkeys(x for x in places if x):
        f = root / f"world/sources/placement/facts/{p}.json"
        if f.exists():
            claims.update({x["id"]: x["claim"] for x in json.loads(f.read_text())["facts"]})
    for f in extra:
        claims.update({x["id"]: x["claim"] for x in json.loads(pathlib.Path(f).read_text())["facts"]})
    stance = {}
    for f in glob.glob(str(root / "world/sources/dialogue/stance/*.json")):
        stance.update({e["personId"]: e for e in json.loads(pathlib.Path(f).read_text())["entries"]})
    sheets = {}
    for f in glob.glob(str(root / "world/sources/dialogue/cultures/**/*.json"), recursive=True):
        sheets.update({e["id"]: e for e in json.loads(pathlib.Path(f).read_text()).get("entries", [])})
    topics = {e["id"]: e for e in json.loads((root / "world/sources/dialogue/topics.json").read_text())["entries"]}
    return npcs, claims, stance, sheets, topics


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("quest")
    ap.add_argument("out")
    ap.add_argument("--place-facts", nargs="*", default=[])
    ap.add_argument("--repo", default=str(HERE.parents[2]))
    a = ap.parse_args()
    root = pathlib.Path(a.repo)

    q = yaml.safe_load(pathlib.Path(a.quest).read_text())
    npcs, claims, stance, sheets, topic_rows = load_world(root, q, a.place_facts)
    preds, verbs = vocabulary(root)
    routing = yaml.safe_load((HERE / "shapes.yaml").read_text())
    cat = yaml.safe_load((HERE / "skill-uses.yaml").read_text())
    claims.update({f["id"]: f["claim"] for f in q["facts"]})
    things = {t["id"]: t for t in q["things"]}
    cast = {c["id"]: c for c in q["cast"]}
    truth = {t["id"] for t in q["truth"]}
    stage_ids = {s["id"] for s in q["stages"]}
    missing = []

    # The imported quest object.
    for k in ("id", "code", "title", "line", "group", "tier", "status", "shapes", "region", "settlement",
              "anchorPlaces", "premise", "costTier", "milestone", "touches", "sources", "stages"):
        if k not in q:
            missing.append(f"quest object: {k} missing (world/sources/quests/README.md)")
    if q.get("group") not in routing["lines"]:
        missing.append(f"group {q.get('group')!r}: not one of {', '.join(routing['lines'])}")

    # Facts, cast, clues, topics resolve.
    for f in q["facts"]:
        if f["from"] not in truth and f["from"] not in claims and not f["from"].startswith("culture."):
            missing.append(f"fact {f['id']}: from {f['from']}")
        if f["from"].startswith("culture.") and f["from"].split("#")[0] not in sheets:
            missing.append(f"fact {f['id']}: culture sheet {f['from'].split('#')[0]} not found")
    missing += [f"playerStart: {fid}" for fid in q.get("playerStart", []) if fid not in claims]
    for c in q["cast"]:
        if c["id"] not in npcs and not c.get("persona", {}).get("race"):
            missing.append(f"cast {c['id']}: not in npcs.json and no invented persona")
        missing += [f"{c['id']} knowledge: {fid}" for fid in c["knowledge"] if fid not in claims]
        missing += [f"{c['id']} change: {ch['fact']}" for ch in c.get("changes", []) if ch["fact"] not in claims]
    for k in q["clues"]:
        if k["carrier"] not in things and k["carrier"] not in cast:
            missing.append(f"clue {k['id']}: carrier {k['carrier']}")
        missing += [f"clue {k['id']}: {g}" for g in k["gives"] if g not in claims]
    for con in q["conclusions"]:
        if len(con["clues"]) < 3:
            missing.append(f"conclusion {con['id']}: {len(con['clues'])} clues, needs 3")
    for t in q["topics"]:
        if t["person"] not in cast:
            missing.append(f"topic {t['id']}: person {t['person']}")
        if t["id"] not in topic_rows and not t.get("new"):
            missing.append(f"topic {t['id']}: not in topics.json and not marked new")
        missing += [f"topic {t['id']}: {g}" for g in t.get("uses", []) + t.get("hides", []) if g not in claims]
    for e in q.get("essentialTopics", []):
        if not any(t["id"] == e for t in q["topics"]):
            missing.append(f"essentialTopics: {e} has no topic row")

    # Shapes, actions, centrepiece.
    data = q.get("shapeData", {})
    for shape in q.get("shapes", []):
        keys = [shape] + ([f"{shape}/{data['theftMode']}"] if shape == "THEFT" and "theftMode" in data else [])
        for key in keys:
            if key not in routing["shapes"]:
                missing.append(f"shape {key}: not in shapes.yaml")
                continue
            missing += [f"shapeData.{r}: required by {key}" for r in routing["shapes"][key]["require"] if r not in data]

    def stage_actions(s):
        return list(s.get("actions", [])) + [x for ap_ in s.get("approaches", []) for x in ap_.get("actions", [])]

    used = set()
    for s in q["stages"]:
        for x in stage_actions(s):
            if "system" in x:
                if x.get("use") not in cat["supporting"]:
                    missing.append(f"stage {s['id']}: supporting {x.get('use')} not in skill-uses.yaml")
                continue
            skills = WEAPONS if x.get("skill") == "any-weapon" else [x.get("skill")]
            if not any(sk in cat["skills"] and x.get("use") in cat["skills"][sk]["uses"] for sk in skills):
                missing.append(f"stage {s['id']}: {x.get('skill')}: {x.get('use')} is not in skill-uses.yaml")
            used.add(x.get("use"))
    if "actionPlan" not in q:
        missing.append("actionPlan: missing (principles/actions.md)")
    tag = q.get("centrepiece")
    if tag not in cat["verbTags"]:
        missing.append(f"centrepiece {tag!r}: not a verb tag ({', '.join(cat['verbTags'])})")
    elif not used & set(cat["verbTags"][tag]):
        missing.append(f"centrepiece {tag}: no stage action carries it")

    # Stages: the imported fields, vocabulary terms, graph, journal draft.
    for s in q["stages"]:
        w = f"stage {s.get('id')}"
        missing += [f"{w}: {k} missing (imported stage shape)" for k in STAGE_FIELDS if k not in s]
        check_actions(s.get("onEnter"), verbs, f"{w} onEnter", missing)
        for o in s.get("objectives", []):
            check_condition(o.get("completeWhen"), preds, f"{w} objective {o.get('id')}", missing)
        for edge in s.get("successors", []) + s.get("failForward", []):
            check_condition(edge.get("when"), preds, f"{w} edge to {edge.get('to')}", missing)
            if edge.get("to") not in stage_ids:
                missing.append(f"{w}: successor {edge.get('to')} is not a stage")
        if not s.get("journalText"):
            missing.append(f"{w}: journalText missing (style guide § journal)")
        if s.get("ending"):
            if s.get("endingId") not in {e["id"] for e in q["endings"]}:
                missing.append(f"{w}: endingId {s.get('endingId')!r} is not an endings row")
        elif not s.get("outside"):
            if not s.get("successors"):
                missing.append(f"{w}: no successors and not an ending")
            named = re.findall(r"npc\.[a-z0-9.-]+", json.dumps({k: v for k, v in s.items() if k != "failForward"}))
            if named and not s.get("failForward"):
                missing.append(f"{w}: names {named[0]} but has no failForward (old 0138: nobody is unkillable)")
            if "WONDER" not in q.get("shapes", []) and not [x for x in stage_actions(s) if "skill" in x]:
                missing.append(f"{w}: no skill action (principles/actions.md)")
            missing += [f"{w}: learns {g}" for g in s.get("learns", []) if g not in claims]
    if len(q["endings"]) < 2:
        missing.append("endings: fewer than two")
    for e in q["endings"]:
        check_actions(e.get("world"), verbs, f"ending {e['id']} world", missing)
        check_actions(e.get("rewards"), verbs, f"ending {e['id']} rewards", missing)
    if q.get("startWhen"):
        check_condition(q["startWhen"], preds, "startWhen", missing)
    if missing:
        print("record is not whole; no briefs written:\n  " + "\n  ".join(missing))
        return 1

    def knows_at(stage):
        learned = list(q.get("playerStart", []))
        for s in q["stages"]:
            if s["id"] < stage:
                learned += s.get("learns", [])
        return learned

    def column(c, stage):
        col = dict(c["knowledge"])
        for ch in c.get("changes", []):
            if ch["atStage"] <= stage:
                col[ch["fact"]] = ch["to"]
        return col

    def person(cid):
        r, over = npcs.get(cid, {}), cast[cid].get("persona", {})
        p = {"race": r.get("race"), "sex": r.get("sex"), "role": r.get("role"), "name": r.get("name"),
             "visible": f"{r.get('notes', '')} Outfit: {r.get('look', {}).get('outfit', 'unknown')}".strip(),
             "factions": r.get("factions", []), "home": r.get("home", {}).get("placeId")}
        p.update({k: v for k, v in over.items() if v is not None})
        return p

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for c in q["cast"]:
        p, st = person(c["id"]), stance.get(c["id"], {})
        v = st.get("voice", {})
        my_topics = [t for t in q["topics"] if t["person"] == c["id"]]
        L = [f"# Dialogue brief: {p['name']} ({q['code']} {q['title']})", "",
             "Built by quest-write/brief.py from the quest record and the world records. Do not add facts; ask for them.", "",
             "## What the player can see", f"- {p['race']}, {p['sex']}; {p['visible']}", "",
             "## What the player cannot see", f"- Role: {p['role']} (npcs.json)",
             f"- Factions: {', '.join(x if isinstance(x, str) else x.get('id', str(x)) for x in p['factions']) or 'none'}",
             f"- Wants: {c['wants']}", f"- Fears: {c['fears']}"]
        if p.get("backstory"):
            L.append(f"- Backstory: {p['backstory']}")
        if p.get("invented"):
            L.append(f"- Invented, for 2.4 to write back to the registry: {', '.join(p['invented'])}")
        L += ["", "## Voice", f"- {p['race']}: {voice_row(p['race'] or '')} (dialogue-write/voices.md)"]
        if v:
            L += [f"- Stance voice: chatter {v.get('chatter')}; contraction rate {v.get('contractionRate')}; "
                  f"addresses the player as \"{v.get('addressTerm')}\"; favourite subject {v.get('favouriteSubject')}",
                  f"- Quirk: {v.get('quirk')}"]
            L += [f"- Never mentions: {x}" for x in v.get("neverMentions", [])]
        else:
            L.append("- No stance file row for this person: 2.4 composes one before lines are written.")
        chain = [sheets[s] for s in st.get("chain", []) if s in sheets]
        if chain:
            L += ["", "## Culture chain (most specific last)"]
            for s in chain:
                sp = s.get("speech", {})
                L.append(f"- **{s['name']}** ({s['level']}): formality {sp.get('formality')}; "
                         f"never says: {'; '.join(x['text'] for x in sp.get('neverSaid', [])) or 'nothing listed'}")
        L += ["", "## Others in the quest (the player may be sent to them)"]
        L += [f"- {person(o['id'])['name']}: {person(o['id'])['role']}" for o in q["cast"] if o is not c]
        L += ["", "## Things lines may name (and only these)"]
        L += [f"- `{t['id']}`: {t['kind']}; {t.get('where', t['source'])}; {t['states']}" for t in q["things"]]
        L += ["", "## Topics"]
        for t in my_topics:
            first = t["stages"][0]
            L += [f"### {t['label']} (`{t['id']}`; stages {t['stages']}; "
                  f"{'essential: no refusal band' if t['essential'] else 'not essential'})",
                  f"- Intent: {t['intent']}", "- May state:"] + [f"  - `{f}`: {claims[f]}" for f in t.get("uses", [])]
            if t.get("hides"):
                L += ["- Hides (until the intent says otherwise):"] + [f"  - `{f}`: {claims[f]}" for f in t["hides"]]
            if t.get("grants"):
                L.append(f"- Words that become topic links: {', '.join(t['grants'])}")
            acts = [x for s_ in q["stages"] if s_["id"] in t["stages"] for x in stage_actions(s_) if "skill" in x]
            if acts:
                L += ["- What the player does at these stages (set it up: who, where, what danger, what they need):"]
                L += [f"  - {x['skill']}: {x['use']}" + (f" ({x['target']})" if x.get("target") else "")
                      + (f", {x['setting']}" if x.get("setting") else "") for x in acts]
            dirs = [s_["directions"] for s_ in q["stages"] if s_["id"] in t["stages"] and s_.get("directions")]
            L += [f"- Directions to give: {d}" for d in dirs]
            L += [f"- {p['name']}'s knowledge at stage {first}:"] + [f"  - `{f}`: {v_}" for f, v_ in column(c, first).items()]
            L += [f"- The player already knows at stage {first} (anything else is explained when first named):"]
            L += [f"  - `{f}`: {claims[f]}" for f in knows_at(first)]
            L.append("")
        name = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        path = out / f"{q['code'].lower()}-{name}.md"
        path.write_text("\n".join(L) + "\n")
        print(f"wrote {path} ({len(my_topics)} topics)")

    J = [f"# Journal brief: {q['code']} {q['title']}", "",
         "Write each entry in the style guide's journal register (docs/design/standards/text/style-guide.md § journal):",
         "first person; past tense for events; \"I'm to\" for the objective; full names every entry; re-summarise the",
         "chain; directions in landmark prose; failure entries flat, with the consequence.", ""]
    for s in q["stages"]:
        J += [f"## Stage {s['id']} (`{s['journal']}`){' ending: ' + s['ending'] if s.get('ending') else ''}",
              f"- Draft: {s['journalText']}"]
        if s.get("directions"):
            J.append(f"- Directions: {s['directions']}")
        J += [f"- The player knows: {', '.join(knows_at(s['id'] + 1))}", ""]
    (out / f"{q['code'].lower()}-journal.md").write_text("\n".join(J) + "\n")
    print(f"wrote {out / (q['code'].lower() + '-journal.md')} ({len(q['stages'])} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
