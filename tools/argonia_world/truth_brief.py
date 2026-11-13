"""The truth reader's input (text-review, the truth step): every line, journal entry and objective of a quest, or
every line and the stated trade of each talker of a settlement, beside the surroundings sheet of its speaker and of
each person or thing it names (tools/argonia_world/surroundings.py), from the forms read back from the built plugin.

    python3 -m tools.argonia_world.truth_brief <quest id | code | settlement id> [--built DIR] [--out FILE]
        [--part i/n]
        a quest (quest.main.mq01, or mq01) reads its read-back form (DIR, default out/questform-read);
        a settlement (bmv.helstrom) reads its talkers from the story data
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world import surroundings as su

ASK = """# Truth reading: {title}

You are the truth reader. Read every row below beside the surroundings sheets (the measured facts of the built
world round each speaker and each person or thing a row names; each fact marked fixed or moving). List every claim
that a sheet does not support or contradicts:

- **place**: a place, building, structure or ground named or described that is not on the sheet as what it reads
  as (a "plank walk" where no plank walkway stands, a "camp" with no tent, bedroll or fire, a "pier" when the sheet
  says the deck of a ship);
- **position**: a thing or person placed where the sheet does not put them ("in the roots" when the sheet says bare
  earth), or placed by "us", "here", "beside me" or by anything marked moving instead of by something fixed;
- **work**: what someone is said to be doing or to do for a living that their sheet does not show (their class,
  factions and packages; a person who only wanders about a spot is not seen working);
- **event**: an event said to be happening now that the sheet does not show (a fire, a fight, a crowd, a ship
  arriving);
- **system**: something the game's systems do not do (tides, seasons, called weather, a fire with no fire object).

A claim about the past, about somewhere the player is not, or about what someone believes is not a finding unless
it describes this place as it is now. Directions to another place are checked only for what they say of this
place. A claim a sheet neither shows nor denies (a model the kinds table could not name stands near) is a finding
marked "unsure", with what to look at.

Write your findings to `{report}` as a table, one row per claim:

| row id | kind | the claim (quoted) | what the sheet says | a rewrite that is true (or "cut") |

Keep the speaker's voice in each rewrite and change only what is false; place things by fixed things. End with a
count per kind. If a row is true, do not list it.

"""


def _ref_sheets(refs: dict[str, tuple[dict, dict]], ids: list[str], built: str | None) -> dict[str, str]:
    specs = {}
    for i in ids:
        try:
            specs[i] = su.spot_of(i, refs)
        except SystemExit:
            continue
    raws = su.raw(list(dict.fromkeys(specs.values())))
    by_spec = dict(zip(dict.fromkeys(specs.values()), raws))
    out = {}
    for i, s in specs.items():
        name = refs[i][0].get("name") if i in refs else None
        out[i] = su.sheet(by_spec[s], f"{name} ({i})" if name else i)
    return out


def _names(form: dict, refs: dict) -> dict[str, str]:
    """Every ref of the form (and of the forms it reaches) by the name the player sees."""
    out = {}
    for r in form.get("refs", []):
        n = r.get("name") or form.get("names", {}).get(r["id"])
        if n:
            out[n] = r["id"]
    return out


def quest_rows(form: dict) -> list[dict]:
    rows = []
    for ln in form.get("lines", []):
        rows.append({"id": ln["id"], "speaker": ln.get("speaker"), "kind": ln.get("kind"),
                     "when": f"stages {ln.get('first_stage', '-')}..{ln.get('last_stage', '-')}",
                     "prompt": ln.get("prompt") or "", "text": ln.get("text") or ln.get("gist") or ""})
    for s in form.get("stages", []):
        if s.get("journal"):
            rows.append({"id": f"journal {s['number']}", "speaker": None, "kind": "journal", "when": "",
                         "prompt": "", "text": s["journal"]})
    for o in form.get("objectives", []):
        rows.append({"id": f"objective {o['number']}", "speaker": None, "kind": "objective",
                     "when": f"targets {', '.join(o.get('targets', []))}", "prompt": "", "text": o["text"],
                     "targets": o.get("targets", [])})
    return rows


def build_quest(qid: str, built: str | None, report: str) -> str:
    d = Path(built) if built else su.READ_BACK
    hits = [p for p in d.glob("*.json") if p.stem == qid or p.stem.endswith("." + qid)]
    if not hits:
        raise SystemExit(f"truth_brief: no read-back form for {qid} in {d}")
    form = json.loads(hits[0].read_text())
    refs = su.forms(d)
    names = _names(form, refs)
    rows = quest_rows(form)
    need: dict[str, None] = {}
    for r in rows:
        r["sheets"] = []
        for i in ([r["speaker"]] if r["speaker"] else []) + r.get("targets", []) + [
                i for n, i in names.items() if re.search(rf"\b{re.escape(n)}\b", r["prompt"] + " " + r["text"])]:
            if i not in r["sheets"]:
                r["sheets"].append(i)
                need[i] = None
    sheets = _ref_sheets(refs, list(need), built)
    L = [ASK.format(title=f"{form['quest']['name']} ({form['quest']['id']})", report=report)]
    L.append("## The rows\n")
    L.append("| row id | speaker | kind | when | prompt | text | sheets |\n|---|---|---|---|---|---|---|")
    for r in rows:
        who = (refs[r["speaker"]][0].get("name") or r["speaker"]) if r["speaker"] in refs else (r["speaker"] or "")
        L.append(f"| {r['id']} | {who} | {r['kind']} | {r['when']} | {r['prompt']} | {r['text']} | "
                 f"{', '.join(i for i in r['sheets'] if i in sheets)} |")
    L.append("\n# The sheets\n")
    L += [sheets[i] for i in need if i in sheets]
    return "\n".join(L) + "\n"


TALKERS = """A talker's sheet reaches a short way round them, in the talk's own distance words ("just", "a short way").
"Here" in a talker's line is the spot the sheet is taken at: it stands when the speaker keeps to that spot (wanders
about it) and the thing is told no nearer than it is; it is a finding when the speaker follows a routine across the
day or the place, or when the thing is called "just" or "beside" while the speaker strays further than that.

"""


def build_settlement(sid: str, report: str, part: str | None = None) -> str:
    w = db.open()
    talkers = w.query("SELECT t.id, t.known_as, t.trade, t.spot, t.backstory FROM talker t JOIN bmv_talker b "
                      "ON b.id = t.id WHERE b.settlement = ? ORDER BY t.id", sid)
    if not talkers:
        raise SystemExit(f"truth_brief: no talkers in {sid}")
    if part:    # "i/n": the i-th of n even slices, for a settlement too big for one reader
        i, n = (int(x) for x in part.split("/"))
        talkers = talkers[(i - 1) * len(talkers) // n:i * len(talkers) // n]
    raws = su.raw([f"{t['id']}@{su.TALK_RADIUS:g}" for t in talkers])
    L = [ASK.format(title=f"the talkers of {sid}" + (f", part {part}" if part else ""), report=report), TALKERS,
         "## The rows\n",
         "| row id | speaker | kind | prompt | text | sheet |\n|---|---|---|---|---|---|"]
    for t in talkers:
        L.append(f"| {t['id']}#trade | {t['known_as']} | stated trade and spot | | {t['trade']}; {t['spot']}; "
                 f"{t['backstory']} | {t['id']} |")
        for ln in w.query("SELECT l.topic, l.ord, l.text, p.prompt FROM talk_line l JOIN talk_topic p ON p.id = "
                          "l.topic WHERE l.talker = ? ORDER BY l.topic, l.ord", t["id"]):
            L.append(f"| {t['id']}#{ln['topic']}#{ln['ord']} | {t['known_as']} | line | {ln['prompt']} | "
                     f"{ln['text']} | {t['id']} |")
    L.append("\n# The sheets\n")
    L += [su.sheet(r, f"{t['known_as']} ({t['id']})", bands=su.TALK_BANDS) for t, r in zip(talkers, raws)]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what")
    ap.add_argument("--built")
    ap.add_argument("--out")
    ap.add_argument("--report", help="where the reader writes its findings (named in the brief)")
    ap.add_argument("--part", help="i/n: a settlement's i-th of n slices of talkers (one reader each)")
    a = ap.parse_args(argv)
    key = a.what.rsplit(".", 1)[-1]
    report = a.report or (f"story/design/quests/review/truth/{key}.md" if not a.what.startswith("bmv.")
                          else f"story/design/quests/review/truth/talkers-{key}.md")
    text = build_settlement(a.what, report, a.part) if a.what.startswith("bmv.") else build_quest(a.what, a.built, report)
    if a.out:
        Path(a.out).write_text(text)
        print(f"wrote {a.out} ({len(text)} characters)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
