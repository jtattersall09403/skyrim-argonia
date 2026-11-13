#!/usr/bin/env python3
"""Build one dialogue brief per cast member, and one journal brief, from a quest record (quest-record.md).

Usage: python3 brief.py QUEST_ID OUT_DIR [--place-facts EXTRA.json ...]

Reads the world database through tools/argonia_world/db.py (decision 0030): the quest's record rows (exported as
the YAML view by quest_record.py; import a record first), the `npc` rows for each cast member's race, sex, role,
look and home, the `stance` rows for voice and culture chain, the `culture_sheet` rows named in the chain, the
place's facts (`fact` rows of the settlement and each anchor place), the `topic` rows and the condition
vocabulary (`condition_term`). Every reference must resolve, every condition and action must be a vocabulary
term, the record must hold the `shapeData` sections its shapes require (shapes.yaml), every skill action must be a
use in skill-uses.yaml, and the record must compile to a quest form that passes its rules (docs/design/quest-form.md),
or no brief is written.
"""
import argparse
import dataclasses
import json
import pathlib
import re
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tools.argonia_world import db, echoes, quest_record, records, talk_route  # noqa: E402
from tools.questform.__main__ import terms_of  # noqa: E402
VOICES = HERE.parent / "dialogue-write" / "voices.md"
WEAPONS = ["one-handed", "two-handed", "archery"]   # what a record's `any-weapon` means
STAGE_FIELDS = ["id", "place", "journal"]   # onEnter, objectives, successors: no rows is an empty list


def voice_row(race: str) -> str:
    for line in VOICES.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == race.lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


# A stage needs no skill action of its own when every way on is hearing a line, handing over or taking what is held,
# using a named door or book (a flag its hook sets), another quest's stage, or a gate on who is alive; but a way on
# that is only a death is a fight, and the fight is the stage's act (principles/actions.md, "Drawing the plan" 3).
MOVES = {"topicHeardFrom", "questStage", "stageEverReached", "hasItem", "flag", "npcAlive", "goldAtLeast",
         "objectiveComplete", "all", "any", "not"}
DEATH_ONLY = {"npcAlive", "all", "any", "not"}


def terms(c):
    if isinstance(c, dict):
        for k, v in c.items():
            yield k
            if k in ("all", "any"):
                for x in v:
                    yield from terms(x)
            elif k == "not":
                yield from terms(v)


def moves_only(s, form) -> bool:
    edges = s.get("successors", [])
    if edges:
        return all(set(terms(e.get("when"))) <= MOVES and not set(terms(e.get("when"))) <= DEATH_ONLY for e in edges)
    # No successor in the record: the quest form's own ways on from this stage (a take or a use trigger, a line that
    # sets the stage), none of them a death or a skill check.
    n = s["id"]
    ways = [t["kind"] for t in (form or {}).get("triggers", []) if t.get("prerequisite", 0) <= n < t["sets"]]
    ways += ["skill" if any(c["is"] == "skill_at_least" for c in ln["conditions"]) else "line"
             for ln in (form or {}).get("lines", []) if ln["first_stage"] <= n <= ln["last_stage"]
             and any(r["do"] == "set_stage" for r in ln["results"])]
    return bool(ways) and not {"death", "skill"} & set(ways)


def skill_key(cat, skill) -> str:
    """A record's skill word as the catalogue's key: Skyrim's names in any case or spacing, or an older word through
    `aliases`."""
    norm = re.sub("[^a-z]", "", str(skill).lower())
    return cat["aliases"].get(norm, norm)


def check_condition(c, preds, where, out):
    if isinstance(c, dict):
        for k, v in c.items():
            if k in ("all", "any"):
                for x in v:
                    check_condition(x, preds, where, out)
            elif k == "not":
                check_condition(v, preds, where, out)
            elif k not in preds:
                out.append(f"{where}: {k!r} is not a predicate of the vocabulary (condition_term)")
    else:
        out.append(f"{where}: condition {c!r} is not a vocabulary term")


def check_actions(acts, verbs, where, out):
    for x in acts or []:
        if not isinstance(x, dict) or len(x) != 1 or next(iter(x)) not in verbs:
            out.append(f"{where}: {x!r} is not an action of the vocabulary (condition_term)")


def load_world(w, q, extra):
    npcs = {}
    for c in q["cast"]:
        r = records.person(w, c["id"])
        if r is not None:
            npcs[c["id"]] = r
    claims, places = {}, [q.get("settlement")] + list(q.get("anchorPlaces", []))
    for p in dict.fromkeys(x for x in places if x):
        claims.update({x["id"]: x["claim"] for x in records.place_facts(w, p)})
    for f in extra:
        claims.update({x["id"]: x["claim"] for x in json.loads(pathlib.Path(f).read_text())["facts"]})
    stance = {c["id"]: st for c in q["cast"] if (st := records.stance(w, c["id"])) is not None}
    sheet_ids = {s_ for st in stance.values() for s_ in st["chain"]}
    sheet_ids |= {f["from"].split("#")[0] for f in q["facts"] if f["from"].startswith("culture.")}
    sheets = {i: sh for i in sorted(sheet_ids) if (sh := records.sheet(w, i)) is not None}
    return npcs, claims, stance, sheets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("quest", help="a quest id (quest.local.lh38); import the record first with quest_record.py")
    ap.add_argument("out")
    ap.add_argument("--place-facts", nargs="*", default=[])
    a = ap.parse_args()

    w = db.open()
    try:
        q = quest_record.export(w, a.quest)
    except KeyError as e:
        print(f"{e.args[0]}; import the record first (python3 -m tools.argonia_world.quest_record import ...)")
        return 1
    # The export leaves out a list with no rows; the record's lists are read as empty, not as a crash.
    for k in ("cast", "things", "truth", "clues", "conclusions", "topics", "endings", "facts", "stages"):
        q.setdefault(k, [])
    for c in q["cast"]:
        c.setdefault("knowledge", {})
    npcs, claims, stance, sheets = load_world(w, q, a.place_facts)
    # Who else the player hears in each stage's place: this record's topics, the quest people and the talkers there.
    # A greeting has no prompt: it is keyed by its topic.
    said = [s if s.topic is not None else dataclasses.replace(s, topic=s.key.split("#")[0]) for s in echoes.speech(w, q)]
    owner = echoes.owners(said)
    all_claims = echoes.claims(w)
    preds, verbs = records.vocabulary(w)
    routing = yaml.safe_load((HERE / "shapes.yaml").read_text())
    cat = yaml.safe_load((HERE / "skill-uses.yaml").read_text())
    claims.update({f["id"]: f["claim"] for f in q["facts"]})
    for f, c in all_claims.items():   # a fact another quest established (the player learnt it there) also resolves
        claims.setdefault(f, c)
    things = {t["id"]: t for t in q["things"]}
    cast = {c["id"]: c for c in q["cast"]}
    truth = {t["id"] for t in q["truth"]}
    stage_ids = {s["id"] for s in q["stages"]}
    missing = []

    # The imported quest object.
    for k in ("id", "code", "title", "line", "group", "tier", "status", "shapes", "region", "settlement",
              "anchorPlaces", "premise", "costTier", "milestone", "touches", "sources", "stages"):
        if k not in q:
            missing.append(f"quest object: {k} missing (the quest row)")
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
            missing.append(f"cast {c['id']}: not an npc row and no invented persona")
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
        missing +=[f"topic {t['id']}: {g}" for g in t.get("uses", []) + t.get("hides", []) if g not in claims]
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
    notes = [f"shapeData.{k}: its job is done elsewhere now ({why})" for k, why in routing.get("cut", {}).items()
             if k in data]

    def stage_actions(s):
        return list(s.get("actions", [])) + [x for ap_ in s.get("approaches", []) for x in ap_.get("actions", [])]

    def skilled(x):
        """A skill action: not a supporting act, and not movement (swimming and climbing are not skills)."""
        return "system" not in x and skill_key(cat, x.get("skill")) not in cat["movement"]

    used = set()
    for s in q["stages"]:
        for x in stage_actions(s):
            if not skilled(x):
                if x.get("use") not in cat["supporting"]:
                    missing.append(f"stage {s['id']}: supporting {x.get('use')} not in skill-uses.yaml")
                used.add(x.get("use"))
                continue
            skills = WEAPONS if x.get("skill") == "any-weapon" else [skill_key(cat, x.get("skill"))]
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

    # The stage graph, the ways on, who must live, markers and hand-ins: the quest form's own rules.
    form, _, form_lines = terms_of(w, q["id"])
    missing += [f"quest form: {x}" for x in form_lines]

    # Stages: the imported fields, vocabulary terms, journal draft, a skill action where the stage asks one.
    for s in q["stages"]:
        at = f"stage {s.get('id')}"
        hidden = bool(s.get("hidden"))   # a stage the build needs and the player never reads: no journal, no objective
        missing += [f"{at}: {k} missing (imported stage shape)" for k in STAGE_FIELDS if k not in s
                    and not (hidden and k == "journal")]
        check_actions(s.get("onEnter"), verbs, f"{at} onEnter", missing)
        for o in s.get("objectives", []):
            check_condition(o.get("completeWhen"), preds, f"{at} objective {o.get('id')}", missing)
        for edge in s.get("successors", []) + s.get("failForward", []):
            check_condition(edge.get("when"), preds, f"{at} edge to {edge.get('to')}", missing)
            if edge.get("to") not in stage_ids:
                missing.append(f"{at}: successor {edge.get('to')} is not a stage")
        if not s.get("journalText") and not hidden:
            missing.append(f"{at}: journalText missing (style guide § journal)")
        if s.get("ending"):
            # A played ending names its endings row; a failed ending (a death the quest cannot go on without) may not.
            if s.get("endingId") not in {e["id"] for e in q["endings"]} and (s.get("endingId") or s["ending"] != "failed"):
                missing.append(f"{at}: endingId {s.get('endingId')!r} is not an endings row")
        elif not s.get("outside"):
            if "WONDER" not in q.get("shapes", []) and not hidden and not moves_only(s, form) and not any(
                    skilled(x) for x in stage_actions(s)):
                missing.append(f"{at}: no skill action (principles/actions.md)")
            missing += [f"{at}: learns {g}" for g in s.get("learns", []) if g not in claims]
    if len(q["endings"]) < 1:
        missing.append("endings: none")
    for e in q["endings"]:
        check_actions(e.get("world"), verbs, f"ending {e['id']} world", missing)
        check_actions(e.get("rewards"), verbs, f"ending {e['id']} rewards", missing)
    if q.get("startWhen"):
        check_condition(q["startWhen"], preds, "startWhen", missing)
    for n in notes:
        print(f"note: {n}")
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
        outfit = r.get("outfit") if r.get("outfit") is not None else "unknown"
        p = {"race": r.get("race"), "sex": r.get("sex"), "role": r.get("role"), "name": r.get("name"),
             "visible": f"{r.get('notes') or ''} Outfit: {outfit}".strip(),
             "factions": r.get("factions", []), "home": r.get("home")}
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
             "## What the player cannot see", f"- Role: {p['role']} (npc)",
             f"- Factions: {', '.join(p['factions']) or 'none'}",
             f"- Wants: {c['wants']}", f"- Fears: {c['fears']}"]
        if p.get("backstory"):
            L.append(f"- Backstory: {p['backstory']}")
        if p.get("invented"):
            L.append(f"- Invented, for 2.4 to write back to the registry: {', '.join(p['invented'])}")
        L += ["", "## Voice", f"- {p['race']}: {voice_row(p['race'] or '')} (dialogue-write/voices.md)"]
        if v:
            L += [f"- Stance voice: chatter {v.get('chatter')}; contraction rate {v.get('contraction_rate')}; "
                  f"addresses the player as \"{v.get('address_term')}\"; favourite subject {v.get('favourite_subject')}",
                  f"- Quirk: {v.get('quirk')}"]
            L += [f"- Never mentions: {x}" for x in v.get("never_mentions", [])]
        else:
            L.append("- No stance row for this person: 2.4 composes one before lines are written.")
        chain = [sheets[s] for s in st.get("chain", []) if s in sheets]
        if chain:
            L += ["", "## Culture chain (most specific last)"]
            for s in chain:
                L.append(f"- **{s['name']}** ({s['level']}): formality {s['formality']}; "
                         f"never says: {'; '.join(s['entries'].get('never-said', [])) or 'nothing listed'}")
        L += ["", "## Others in the quest (the player may be sent to them)"]
        L += [f"- {person(o['id'])['name']}: {person(o['id'])['role']}" for o in q["cast"] if o is not c]
        L += ["", "## Things lines may name (and only these)"]
        L += [f"- `{t['id']}`: {t['kind']}; {t.get('where', t['source'])}; {t.get('states', {})}" for t in q["things"]]
        L += ["", "## Topics"]
        for t in my_topics:
            first = t["stages"][0]
            L += [f"### {t['label']} (`{t['id']}`; stages {t['stages']}; "
                  f"{'essential: no refusal band' if t['essential'] else 'not essential'})",
                  f"- Intent: {t['intent']}"]
            here = next(s_.windows for s_ in said if s_.key == t["id"] and s_.source.startswith("record"))
            others = {f: o for f in t.get("uses", []) for x in sorted(here)
                      if (o := owner.get((x, f))) is not None and o.speaker != echoes.ident(p["name"])}
            L += ["- May state:"] + [f"  - `{f}`: {claims[f]}" for f in t.get("uses", []) if f not in others]
            if others:
                L += ["- Said by its owner near you (point to them in a few words; never restate it):"]
                L += [f"  - `{f}`: {o.name} says it ({claims[f]})" for f, o in others.items()]
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
            L += [f"- Directions to give (landmarks, the way, compass points and a word for how far; never a count): "
                  f"{talk_route.in_words(d)}" for d in dirs]
            L += [f"- {p['name']}'s knowledge at stage {first}:"] + [f"  - `{f}`: {v_}" for f, v_ in column(c, first).items()]
            L += [f"- The player already knows at stage {first} (anything else is explained when first named):"]
            L += [f"  - `{f}`: {claims[f]}" for f in knows_at(first)]
            L.append("")
        L += echoes.brief_section(said, p["name"], all_claims)
        name = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        path = out / f"{q['code'].lower()}-{name}.md"
        path.write_text("\n".join(L) + "\n")
        print(f"wrote {path} ({len(my_topics)} topics)")

    # The quest's people with no topic of their own (quest_people.json): one reply each, said near the cast.
    for s_ in [x for x in said if x.source == "quest_people.json" and x.key.startswith(f"ARG_{q['code']}_")]:
        P = [f"# Quest person brief: {s_.name} ({q['code']} {q['title']}), \"{s_.topic}\"", "",
             "One reply of one to three sentences: who this person is, their own work and stake in this stretch of the "
             "quest, in their own voice (voices.md for their race). They add no fact the record does not hold; a fact "
             "another speaker owns is pointed to by name, never told. List the fact ids the reply states in its "
             "entry's `facts`.", "",
             f"- Heard in: {', '.join(sorted(s_.windows))}", ""]
        P += echoes.brief_section(said, s_.name, all_claims)
        path = out / f"{q['code'].lower()}-people-{echoes.ident(s_.name)}-{len(s_.windows)}.md"
        path.write_text("\n".join(P) + "\n")
        print(f"wrote {path} (quest person)")

    J = [f"# Journal brief: {q['code']} {q['title']}", "",
         "Write each entry in the style guide's journal register (story/design/text/style-guide.md § journal):",
         "first person; past tense for what just happened; one \"I'm to\" for the one step now owed, never a later",
         "step; full names as the game shows them; two to four sentences; an ending's entry may sum up the quest;",
         "directions in landmark prose with a word for how far, never a count; failure entries flat, with the consequence. Each objective is an imperative",
         "with a full stop and no \"I\" or \"you\", naming its target.", ""]
    for s in q["stages"]:
        if s.get("hidden"):
            continue
        J += [f"## Stage {s['id']} (`{s['journal']}`){' ending: ' + s['ending'] if s.get('ending') else ''}",
              f"- Draft: {s['journalText']}"]
        if s.get("directions"):
            J.append(f"- Directions: {talk_route.in_words(s['directions'])}")
        J += [f"- The player knows: {', '.join(knows_at(s['id'] + 1))}", ""]
    (out / f"{q['code'].lower()}-journal.md").write_text("\n".join(J) + "\n")
    print(f"wrote {out / (q['code'].lower() + '-journal.md')} ({len(q['stages'])} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
