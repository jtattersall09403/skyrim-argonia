"""The quest form's command line (docs/design/quest-form.md).

    python3 -m tools.questform check <form.json...>              # the schema and every rule, each form with the others
    python3 -m tools.questform check --set <dir|form.json...>    # also the rules over the forms as one set
    python3 -m tools.questform compile <quest id...|--all> [--out dir] [--owed-ok]   # quest record -> form
        (default out/questform; --owed-ok: a quest on the owed list that does not fit is not a failure; the seed's way)
    python3 -m tools.questform gate                              # make check: every staged record against the owed list
    python3 -m tools.questform owed --write                      # rewrite the listed quests' terms (never adds one)
    python3 -m tools.questform diff <designed> <built>           # every difference, designed form against built
    python3 -m tools.questform sketch <story.md|file.sketch> [--quest ID] [--no-walk] [--paths] [--no-cache]
                                      [--time-limit SECONDS]
        # an outline's sketch: the rules a quest can meet before its places are built, then the reach walk (each
        # quest's result kept in out/sketch-cache until it or a quest it waits on changes)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.argonia_world import db
from tools.questform import compile as qc
from tools.questform import rules

OWED = db.REPO / "story/data/questform_owed.json"
EXAMPLES = Path(__file__).with_name("examples")
BLOCKTEST = Path(__file__).with_name("blocktest")
OUT = db.REPO / "out/questform"


def check_file(p: Path, others: list[dict] | None = None) -> list[tuple[str, str]]:
    """The rules over one form file; `others`: the forms checked with it (the quest that starts it among them)."""
    try:
        form = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [("schema", f"{p}: not readable JSON ({e})")]
    return rules.check(form, others)


_ALL: dict[int, list[dict]] = {}


def all_forms(w: db.World) -> list[dict]:
    """Every staged quest record compiled (fitting or not), once per world: the forms a quest is checked with."""
    if id(w) not in _ALL:
        _ALL[id(w)] = [f for f in (qc.compile_quest(w, q)[0] for q in qc.staged_quests(w)) if f is not None]
    return _ALL[id(w)]


def terms_of(w: db.World, qid: str) -> tuple[dict | None, list[str], list[str]]:
    """(form or None, the quest's owed terms, one line per refusal or failure)."""
    form, refused = qc.compile_quest(w, qid)
    lines = [f"{t} at {where}: {hint}" for t, where, hint in refused]
    terms = {t for t, _, _ in refused}
    if form is not None:
        fails = rules.check(form, all_forms(w))
        terms |= {f"check:{r}" for r, _ in fails}
        lines += [f"check:{r}: {m}" for r, m in fails]
    return form, sorted(terms), lines


def load_owed() -> dict[str, list[str]]:
    return json.loads(OWED.read_text(encoding="utf-8"))["quests"] if OWED.exists() else {}


def save_owed(quests: dict[str, list[str]]) -> None:
    doc = {"_about": "Quest records with stages that do not yet fit the quest form, each with its refused terms "
                     "(docs/design/quest-form.md). make check fails on a quest that does not fit and is not listed, "
                     "on a listed quest that now fits, and on a listed quest whose terms changed; the list only "
                     "shrinks (python3 -m tools.questform owed --write rewrites listed rows, never adds one).",
           "quests": {k: quests[k] for k in sorted(quests)}}
    OWED.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def gate(w: db.World) -> list[str]:
    errs = []
    for d in (EXAMPLES, BLOCKTEST):
        for p in sorted(d.glob("*.json")):
            errs += [f"example {p.name}: {r}: {m}" for r, m in check_file(p, load_forms([d]))]
    errs += [f"blocktest set: {r}: {m}" for r, m in rules.check_set(load_forms([BLOCKTEST]))]
    owed = load_owed()
    staged = qc.staged_quests(w)
    for qid in staged:
        _, terms, _ = terms_of(w, qid)
        listed = owed.get(qid)
        if terms and listed is None:
            errs.append(f"{qid} does not fit the quest form and is not on the owed list: {', '.join(terms)}")
        elif not terms and listed is not None:
            errs.append(f"{qid} now fits the quest form: take it off {OWED.name}")
        elif terms and sorted(listed) != terms:
            errs.append(f"{qid}: its owed terms changed to {', '.join(terms)} (python3 -m tools.questform owed "
                        "--write)")
    errs += [f"{qid} is on {OWED.name} and is not a staged quest record" for qid in owed if qid not in staged]
    errs += [f"set: {r}: {m}" for r, m in rules.check_set(fitting(w))]
    return errs


def fitting(w: db.World) -> list[dict]:
    """The forms of every staged quest record that fits, compiled together (the set the seed builds)."""
    out = []
    for qid in qc.staged_quests(w):
        form, terms, _ = terms_of(w, qid)
        if form is not None and not terms:
            out.append(form)
    return out


def load_forms(paths) -> list[dict]:
    files = [f for p in map(Path, paths) for f in (sorted(p.glob("*.json")) if p.is_dir() else [p])]
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("files", nargs="+")
    c.add_argument("--set", action="store_true", help="the files (or directories) are one set: check it whole too")
    k = sub.add_parser("compile")
    k.add_argument("quests", nargs="*")
    k.add_argument("--all", action="store_true")
    k.add_argument("--out", default=str(OUT))
    k.add_argument("--owed-ok", action="store_true")
    sub.add_parser("gate")
    o = sub.add_parser("owed")
    o.add_argument("--write", action="store_true")
    df = sub.add_parser("diff")
    df.add_argument("designed")
    df.add_argument("built")
    sk = sub.add_parser("sketch")
    sk.add_argument("file")
    sk.add_argument("--quest")
    sk.add_argument("--no-walk", action="store_true", help="skip the reach walk (the rules only)")
    sk.add_argument("--paths", action="store_true", help="print the walk's shortest path to each ending")
    sk.add_argument("--no-cache", action="store_true", help="walk every quest again, keeping nothing")
    sk.add_argument("--time-limit", type=float, help="seconds each quest's walk may take (default 180)")
    a = ap.parse_args(argv)
    if a.cmd == "sketch":
        from tools.questform import sketch
        return sketch.main(Path(a.file), a.quest, not a.no_walk, a.paths, not a.no_cache,
                           a.time_limit or sketch.TIME_LIMIT)
    if a.cmd == "diff":
        from tools.questform import diff
        return diff.main(a.designed, a.built)
    if a.cmd == "check":
        bad = 0
        files = [str(f) for p in map(Path, a.files) for f in (sorted(p.glob("*.json")) if p.is_dir() else [p])]
        try:
            together = load_forms(files)
        except (OSError, json.JSONDecodeError):
            together = None
        for f in files:
            fails = check_file(Path(f), together)
            bad += bool(fails)
            print(f"{f}: " + ("passes" if not fails else f"{len(fails)} failure(s)"))
            for r, m in fails:
                print(f"  {r}: {m}")
        if a.set:
            fails = rules.check_set(load_forms(files))
            bad += bool(fails)
            print(f"the set of {len(files)}: " + ("passes" if not fails else f"{len(fails)} failure(s)"))
            for r, m in fails:
                print(f"  {r}: {m}")
        return 1 if bad else 0
    w = db.open()
    if a.cmd == "compile":
        qids = qc.staged_quests(w) if a.all else a.quests
        bad = 0
        owed = load_owed() if a.owed_ok else {}
        for qid in qids:
            form, terms, lines = terms_of(w, qid)
            if not terms:
                print(f"{qid}: wrote {qc.write(form, Path(a.out))}")
                continue
            if qid in owed:
                print(f"{qid}: owed, not built ({', '.join(terms)})")
                continue
            bad += 1
            print(f"{qid}: does not fit ({', '.join(terms)})")
            for ln in lines:
                print(f"  {ln}")
        return 1 if bad else 0
    if a.cmd == "gate":
        errs = gate(w)
        for e in errs:
            print(f"questform: {e}")
        if not errs:
            n = len(qc.staged_quests(w))
            print(f"questform: {n} staged quest records: {n - len(load_owed())} fit, {len(load_owed())} owed")
        return 1 if errs else 0
    owed = load_owed()
    for qid in list(owed):
        owed[qid] = terms_of(w, qid)[1]
    if a.write:
        save_owed({k: v for k, v in owed.items() if v})
    print(json.dumps(owed, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
