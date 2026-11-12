"""A playtest session and its run folder (docs/design/paper-playtest.md).

A session is a run folder `story/playtests/<quest id>/<utc>-<player>-<designed|built>/` holding:
session.json (the forms played, their hash, the world snapshot, the state), transcript.jsonl (one line per command:
time, think, command, result, a state summary), take.md and answers.md (the player's words), stream.jsonl (the
runner's raw model stream) and run.json (what the index lists). `index` rebuilds story/playtests/index.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from tools.playtest import game as G
from tools.playtest import world as W

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "story/playtests"
QUESTIONS = (
    "What do you think you are meant to do next?",
    "Who do you work for now, if anyone, and why?",
    "What was the most confusing moment?",
    "What would you tell the writer?",
)
STALL_VIEWS = ("journal", "map")


def load_forms(paths: list[str]) -> tuple[list[dict], list[str]]:
    files = []
    for p in map(Path, paths):
        files += sorted(p.glob("*.json")) if p.is_dir() else [p]
    files = [f for f in files if not f.name.endswith(".names.json")]
    if not files:
        raise G.HarnessError(f"no quest forms in {paths}")
    forms = []
    for f in files:
        try:
            forms.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as e:
            raise G.HarnessError(f"{f}: not a readable quest form ({e})") from e
    return forms, [str(f) for f in files]


def forms_hash(forms: list[dict]) -> str:
    return hashlib.sha256(json.dumps(forms, sort_keys=True).encode()).hexdigest()[:16]


def parse_sheet(text: str | None) -> dict:
    kv = dict(p.split("=", 1) for p in (text or "").split(",") if "=" in p)
    race, sex = kv.pop("race", "Argonian"), kv.pop("sex", "male")
    return G.new_sheet(race, sex, **kv)


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def new(forms_paths, *, player="hand", source="designed", start=None, at=None, sheet=None, know=None,
        names=(), use_db=True, max_commands=G.MAX_COMMANDS, root: Path = RUNS, model=None) -> tuple[Path, str]:
    """Make a session (its run folder) and return (folder, the opening screen)."""
    forms, files = load_forms(forms_paths)
    snap = W.snapshot(forms, [Path(n) for n in names], use_db=use_db)
    g = G.Game(forms, snap, sheet=parse_sheet(sheet))
    screen = g.begin(start=start, at=at)
    qid = start or forms[0]["quest"]["id"]
    folder = Path(root) / qid / f"{utc_stamp()}-{player}-{source}"
    n = 1
    while folder.exists():
        n += 1
        folder = folder.with_name(f"{folder.name.split('~')[0]}~{n}")
    folder.mkdir(parents=True)
    sess = {"quest": qid, "player": player, "source": source, "model": model, "form_files": files,
            "forms_hash": forms_hash(forms), "start": start, "at": at, "know": know,
            "max_commands": max_commands, "created": utc_stamp(), "forms": forms, "world": snap,
            "state": g.s, "broken": None, "take": None, "answers": None}
    _save(folder, sess)
    _append(folder, {"time": utc_stamp(), "think": None, "command": "(new game)", "result": screen,
                     "summary": g.summary()})
    return folder, screen


def _load(folder: Path) -> dict:
    return json.loads((Path(folder) / "session.json").read_text(encoding="utf-8"))


def _save(folder: Path, sess: dict) -> None:
    (Path(folder) / "session.json").write_text(json.dumps(sess, ensure_ascii=False) + "\n", encoding="utf-8")


def _append(folder: Path, row: dict) -> None:
    with open(Path(folder) / "transcript.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def do(folder, command: str, think: str) -> tuple[int, str]:
    """Apply one command; (exit code, the screen). 0 played, 2 refused, 3 a harness error (the run stops)."""
    if not (think or "").strip():
        return 2, "Refused: every command needs --think: say what you believe is going on and why you do this."
    sess = _load(folder)
    if sess["broken"]:
        return 3, f"HARNESS ERROR (the run has stopped): {sess['broken']}"
    if sess["take"] is not None:
        return 2, "You have given your take; the game is over."
    st = sess["state"]
    if st["commands"] >= sess["max_commands"]:
        return 2, (f"You have used all {sess['max_commands']} commands. Stop playing now and give your take: "
                   "play end --take '...'")
    try:
        g = G.Game(sess["forms"], sess["world"], state=st)
        screen = g.do(command)
        summary = g.summary()
        code = 0
    except G.HarnessError as e:
        sess["broken"] = str(e)
        screen, summary, code = f"HARNESS ERROR (the run has stopped): {e}", None, 3
    else:
        sess["state"] = g.s
    _save(folder, sess)
    _append(folder, {"time": utc_stamp(), "think": think, "command": command, "result": screen,
                     "summary": summary})
    return code, screen


def end(folder, take: str | None = None, answers: str | None = None) -> tuple[int, str]:
    sess = _load(folder)
    if take is not None:
        sess["take"] = take
        (Path(folder) / "take.md").write_text(take.strip() + "\n", encoding="utf-8")
        _save(folder, sess)
        write_run(folder)
        return 0, ("Thank you. Now, briefly, answer these in one reply with play answers '...':\n" +
                   "\n".join(f"{i}. {qq}" for i, qq in enumerate(QUESTIONS, 1)))
    if answers is not None:
        if sess["take"] is None:
            return 2, "Give your open take first: play end --take '...'"
        sess["answers"] = answers
        (Path(folder) / "answers.md").write_text(answers.strip() + "\n", encoding="utf-8")
        _save(folder, sess)
        write_run(folder)
        return 0, "Thank you. The session is closed; you can stop now."
    return 2, "end needs --take or --answers"


def transcript(folder) -> list[dict]:
    p = Path(folder) / "transcript.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def stalls(rows: list[dict]) -> int:
    """A command that repeats the one before and gets the same screen (a "say 1" that moves a conversation on is
    not a repeat), the third journal-or-map view running, or a think that says stuck."""
    n, prev, views = 0, None, 0
    for r in rows:
        if r["think"] is None:
            continue
        cmd = (" ".join(r["command"].lower().split()), r["result"])
        views = views + 1 if cmd[0].split(" ")[0] in STALL_VIEWS else 0
        if cmd == prev or (views and views % 3 == 0) or re.search(r"\bstuck\b", r["think"] or "", re.I):
            n += 1
        prev = cmd
    return n


def write_run(folder, extra: dict | None = None) -> dict:
    folder = Path(folder)
    sess = _load(folder)
    rows = transcript(folder)
    old = json.loads((folder / "run.json").read_text()) if (folder / "run.json").exists() else {}
    st = sess["state"]
    endings = {q: v["ended"] for q, v in st["quests"].items() if v["ended"]}
    if sess["broken"]:
        how = "harness error"
    elif sess["quest"] in endings:
        how = f"quest {endings[sess['quest']]}"
    elif st["commands"] >= sess["max_commands"]:
        how = "command limit"
    elif sess["take"] is not None:
        how = "stopped by the player"
    else:
        how = "open"
    run = {**old, "quest": sess["quest"], "player": sess["player"], "source": sess["source"],
           "model": sess.get("model"), "form_files": [_rel(f) for f in sess["form_files"]],
           "forms_hash": sess["forms_hash"], "created": sess["created"],
           "counts": {"commands": sum(1 for r in rows if r["think"] is not None), "stalls": stalls(rows),
                      "harness_errors": sum(1 for r in rows if r["result"].startswith("HARNESS ERROR"))},
           "stages": {q: v["done"] for q, v in st["quests"].items()}, "ended": how,
           "take": sess["take"] is not None, "answers": sess["answers"] is not None, **(extra or {})}
    (folder / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return run


def _rel(p: str) -> str:
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return p


def index(root: Path = RUNS) -> Path:
    runs = []
    for p in sorted(Path(root).glob("*/*/run.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        runs.append({"path": str(p.parent.relative_to(root)), **{k: r.get(k) for k in (
            "quest", "player", "source", "model", "created", "forms_hash", "counts", "ended", "cost_usd",
            "minutes")}})
    out = Path(root) / "index.json"
    out.write_text(json.dumps({"_about": "Every paper playtest run (python3 -m tools.playtest index rebuilds this)",
                               "runs": runs}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
