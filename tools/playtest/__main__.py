"""The paper playtest's command line (docs/design/paper-playtest.md).

    python3 -m tools.playtest new --forms <dir|files...> [--start <quest id>|--new-game] [--at <ref id>]
                                  [--sheet race=Argonian,sex=female,Speech=30] [--know <file>] [--names <file>...]
                                  [--player hand] [--source designed|built] [--no-db] [--max-commands N]
                                  [--after <quest id>...]   # those quests played to a completed ending first
    python3 -m tools.playtest do <session> "<command>" --think "<what I believe is going on and why I do this>"
    python3 -m tools.playtest end <session> --take "<open take>" | --answers "<answers>"
    python3 -m tools.playtest run --forms ... --player careful|impatient|wanderer [--model sonnet] [--know ...]
    python3 -m tools.playtest probe [--model haiku]      # proves the player cannot read the repo
    python3 -m tools.playtest reach <forms...> | --compiled [--gate]   # each ending reachable? its shortest path
    python3 -m tools.playtest page [--out <html>] [--runs <dir>]   # the owner's page for exploring the runs
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.playtest import game as G
from tools.playtest import session as S


def _common(p):
    p.add_argument("--forms", nargs="+", required=True)
    p.add_argument("--start")
    p.add_argument("--new-game", action="store_true", help="every quest that runs from a new game (the default)")
    p.add_argument("--at", help="the ref id the player starts beside (default: the first marker's target)")
    p.add_argument("--sheet")
    p.add_argument("--know")
    p.add_argument("--names", nargs="*", default=[])
    p.add_argument("--source", choices=("designed", "built"), default="designed")
    p.add_argument("--no-db", action="store_true", help="no world database: names and places from --names only")
    p.add_argument("--out", default=str(S.RUNS), help="the runs folder (default story/playtests)")
    p.add_argument("--after", nargs="+", default=[], help="quests the game plays to a completed ending first")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    _common(n)
    n.add_argument("--player", default="hand")
    n.add_argument("--max-commands", type=int, default=G.MAX_COMMANDS)
    d = sub.add_parser("do")
    d.add_argument("session")
    d.add_argument("command")
    d.add_argument("--think")
    e = sub.add_parser("end")
    e.add_argument("session")
    e.add_argument("--take")
    e.add_argument("--answers")
    e.add_argument("--ask-later", action="store_true", help="the runner asks the standing questions itself")
    e.add_argument("--think", help="accepted and not kept: a take needs no think")
    r = sub.add_parser("run")
    _common(r)
    r.add_argument("--player", required=True)
    r.add_argument("--model", default="sonnet")
    r.add_argument("--max-commands", type=int, default=40)
    pr = sub.add_parser("probe")
    pr.add_argument("--model", default="haiku")
    rc = sub.add_parser("reach")
    rc.add_argument("forms", nargs="*")
    rc.add_argument("--compiled", action="store_true", help="every staged quest that fits the form, compiled now")
    rc.add_argument("--max-states", type=int, default=None)
    rc.add_argument("--gate", action="store_true", help="make check: only what is wrong against the owed list")
    pg = sub.add_parser("page")
    pg.add_argument("--out", default=None, help="the HTML file (default out/playtest/index.html)")
    pg.add_argument("--runs", default=str(S.RUNS), help="the runs folder (default story/playtests)")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "new":
            folder, screen = S.new(a.forms, player=a.player, source=a.source, start=a.start, at=a.at,
                                   sheet=a.sheet, know=a.know, names=a.names, use_db=not a.no_db,
                                   max_commands=a.max_commands, root=Path(a.out), after=a.after)
            print(f"session: {folder}\n\n{screen}")
            return 0
        if a.cmd == "run":
            from tools.playtest import runner
            folder = runner.run(a.forms, a.player, model=a.model, know=a.know, names=a.names, at=a.at,
                                start=a.start, source=a.source, sheet=a.sheet, max_commands=a.max_commands,
                                use_db=not a.no_db, root=Path(a.out), after=a.after)
            print(f"run: {folder}")
            print((folder / "run.json").read_text())
            return 0
    except G.HarnessError as ex:
        print(f"HARNESS ERROR: {ex}")
        return 3
    if a.cmd == "reach":
        from tools.playtest import walk
        forms = walk.compiled() if a.compiled else S.load_forms(a.forms)[0]
        rows = walk.reach(forms, **({"max_states": a.max_states} if a.max_states else {}))
        bad = walk.unreached(rows)
        if a.gate:
            bad = walk.gate(bad)
        else:
            print(walk.report(rows))
        for b in bad:
            print(f"reach: {b}")
        if a.gate and not bad:
            print(f"reach: {len({r['quest'] for r in rows})} quests, {len(rows)} ways through: every stage and ending "
                  f"reached by a character of {', '.join(walk.SHEETS)}, and each completes every quest not owed")
        return 1 if bad else 0
    if a.cmd == "do":
        code, screen = S.do(a.session, a.command, a.think)
        print(screen)
        return code
    if a.cmd == "end":
        code, screen = S.end(a.session, take=a.take, answers=a.answers, ask=a.ask_later)
        print(screen)
        return code
    if a.cmd == "probe":
        from tools.playtest import runner
        ok, out = runner.probe(a.model)
        print(f"probe: {'the player could not read the repo' if ok else 'THE PLAYER READ THE REPO'}; stream {out}")
        return 0 if ok else 1
    if a.cmd == "page":
        from tools.playtest import page
        out, n, size = page.write(Path(a.out) if a.out else page.DEFAULT_OUT, Path(a.runs))
        print(f"page: {out} ({n} runs, {size / 1024:.0f} KB)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
