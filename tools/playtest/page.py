"""The owner's page for exploring the kept paper playtest runs (docs/design/paper-playtest.md).

    python3 -m tools.playtest page [--out out/playtest/index.html] [--runs story/playtests]

Reads the runs folder's index.json (or every */*/run.json when there is none) and each run's transcript, take,
answers, brief and session, and writes one self-contained HTML file: the data embedded as JSON, the code inline
(page.html beside this file). Nothing is fetched when the page is viewed; rerunning this is the only step.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tools.playtest import session as S

TEMPLATE = Path(__file__).with_name("page.html")
DEFAULT_OUT = S.REPO / "out/playtest/index.html"

WHY = {  # why a run is over -> (key, the words the page shows)
    "harness error": ("harness", "harness error"),
    "command limit": ("cutoff", "cut off at the command limit"),
    "stopped by the player": ("stopped", "stopped by the player"),
    "all quests ended": ("ended", "every quest ended"),
    "open": ("open", "unfinished"),
}


def outcome(ended: str, quest: str) -> tuple[str, str, dict]:
    """(key, label, how each quest stands) from run.json's "ended": "<why> (<quest> <state>, ...)", or the older
    "quest completed" form. The run's own quest decides completed or failed; otherwise why the run stopped does."""
    m = re.match(r"^(.*?)(?: \((.*)\))?$", ended or "open")
    why, each = m.group(1), {}
    for part in (m.group(2) or "").split(", "):
        q, _, state = part.rpartition(" ")
        if q:
            each[q] = state
    if why.startswith("quest ") and not each:
        each[quest] = why.split(" ", 1)[1]
        why = "all quests ended"
    key, label = WHY.get(why, ("other", why))
    own = each.get(quest)
    if key != "harness" and own in ("completed", "failed"):
        key = own
    label = "; ".join([label] + [f"{q} {s}" for q, s in each.items()]) if each else label
    return key, label, each

_LINE_KINDS = (  # (kind, pattern) in order; the first match wins
    ("harness", re.compile(r"^HARNESS ERROR")),
    ("quest", re.compile(r"^Quest started: (?P<text>.*)$")),
    ("questend", re.compile(r"^Quest (?P<who>completed|failed): (?P<text>.*)$")),
    ("journal", re.compile(r"^Journal entry \((?P<who>[^)]*)\): (?P<text>.*)$")),
    ("objnew", re.compile(r"^New objective: (?P<text>.*)$")),
    ("objdone", re.compile(r"^Objective completed: (?P<text>.*)$")),
    ("item", re.compile(r"^(?:Added|Removed|Gold)\b.*$")),
    ("message", re.compile(r"^\[Message box\] (?P<text>.*)$")),
    ("speech", re.compile(r"^(?P<who>[^:\"\n]{1,60}): \"(?P<text>.*)\"$")),
    ("place", re.compile(r"^You are (?:at|in) (?P<text>.*?)\.?$")),
    ("scene", re.compile(r"^(?:People|Things|Doors): .*$")),
    ("refused", re.compile(r"^(?:Refused|You have used all|That is not one of)")),
)
_MENU_HEAD = re.compile(r"^(Topics|Your answers):$")
_MENU_ITEM = re.compile(r"^\s+(\d+)\. (.*)$")
_MAP_MARKER = re.compile(r"^Marker (\d+): (.+?) \(")
PLACEHOLDER = "[not yet written; the gist:]"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _read(p: Path) -> str | None:
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def _json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:
        return {}


def classify(result: str) -> list[dict]:
    """The lines of one screen, each with the kind the page draws it as; a menu is one entry with its options."""
    out: list[dict] = []
    menu = None
    for raw in (result or "").splitlines():
        if not raw.strip():
            menu = None
            continue
        if menu is not None:
            m = _MENU_ITEM.match(raw)
            if m:
                menu["options"].append(m.group(2))
                continue
            menu = None
        h = _MENU_HEAD.match(raw.strip())
        if h:
            menu = {"k": "menu", "t": h.group(1), "options": []}
            out.append(menu)
            continue
        line = raw.strip()
        row = {"k": "text", "t": line}
        for kind, pat in _LINE_KINDS:
            m = pat.match(line)
            if m:
                g = m.groupdict()
                row = {"k": kind, "t": g.get("text", line) or line}
                if g.get("who"):
                    row["who"] = g["who"]
                break
        if PLACEHOLDER in line:
            row["ph"] = 1
        out.append(row)
    return out


def _menu_options(lines: list[dict]) -> list[str] | None:
    for row in reversed(lines):
        if row["k"] == "menu":
            return row["options"]
    return None


def plain(command: str, menu: list[str] | None, markers: dict[str, str]) -> str:
    """The command in plain words, using the choices and map markers the player last saw."""
    c = " ".join((command or "").split())
    if c == "(new game)":
        return "The game begins"
    verb, _, arg = c.partition(" ")
    v = verb.lower()
    if v == "say" and arg.isdigit() and menu and 0 < int(arg) <= len(menu):
        return f"Chose “{menu[int(arg) - 1]}”"
    if v == "say":
        return f"Said “{arg}”"
    if v == "go":
        m = re.match(r"marker (\d+)$", arg, re.I)
        if m and m.group(1) in markers:
            return f"Went to marker {m.group(1)}, {markers[m.group(1)]}"
        return f"Went to {arg}"
    words = {"look": "Looked around", "journal": "Read the journal", "map": "Checked the map",
             "wait": "Waited"}
    if v in words and not arg:
        return words[v]
    lead = {"talk": "Talked to", "take": "Took", "use": "Used", "fight": "Fought", "pick": "Picked the lock of",
            "pickpocket": "Tried to pickpocket", "persuade": "Tried to persuade", "wait": "Waited"}
    if v in lead:
        return f"{lead[v]} {arg}".strip()
    return c


def steps(rows: list[dict], quest: str) -> list[dict]:
    """The transcript as the page's steps: plain words, the screen's lines, the state after, the flags."""
    out, prev, views = [], None, 0
    menu: list[str] | None = None
    markers: dict[str, str] = {}
    last_stage = None
    for i, r in enumerate(rows):
        lines = classify(r.get("result") or "")
        s = r.get("summary") or {}
        stage = (s.get("stages") or {}).get(quest)
        flags = []
        if r.get("think") is not None:
            cmd = (" ".join((r.get("command") or "").lower().split()), r.get("result"))
            views = views + 1 if cmd[0].split(" ")[0] in S.STALL_VIEWS else 0
            if cmd == prev:
                flags.append("repeat")
            elif views and views % 3 == 0:
                flags.append("views")
            if re.search(r"\bstuck\b", r.get("think") or "", re.I):
                flags.append("stuck")
            prev = cmd
        if (r.get("result") or "").startswith("HARNESS ERROR"):
            flags.append("harness")
        if any(x.get("ph") for x in lines):
            flags.append("placeholder")
        if any(x["k"] == "refused" for x in lines):
            flags.append("refused")
        pos = s.get("position") or None
        out.append({
            "i": i, "time": r.get("time"), "think": r.get("think"), "cmd": r.get("command"),
            "plain": plain(r.get("command") or "", menu, markers), "lines": lines,
            "stage": stage, "from": last_stage if stage != last_stage else None,
            "others": {q: n for q, n in (s.get("stages") or {}).items() if q != quest},
            "pos": {k: pos.get(k) for k in ("cell", "place", "x", "y")} if pos else None,
            "markers": s.get("markers") or [], "talking": s.get("talking"),
            "ended": (s.get("ended") or {}).get(quest), "flags": flags,
        })
        if stage is not None:
            last_stage = stage
        verb = (r.get("command") or "").split(" ")[0].lower()
        menu = _menu_options(lines) or (menu if verb in ("look", "journal", "map", "wait") else None)
        for line in (r.get("result") or "").splitlines():
            m = _MAP_MARKER.match(line)
            if m:
                markers[m.group(1)] = m.group(2)
    return out


def answers(text: str | None) -> list[dict]:
    """Numbered answers matched to the standing questions; one unnumbered answer when they are not numbered."""
    if not text:
        return []
    parts = re.split(r"(?:^|\s)([1-9])\.\s+", text.strip())
    found = {int(parts[k]): parts[k + 1].strip() for k in range(1, len(parts) - 1, 2)}
    if not found:
        return [{"q": None, "a": text.strip()}]
    head = parts[0].strip()
    rows = [{"q": None, "a": head}] if head else []
    for n in sorted(found):
        rows.append({"n": n, "q": S.QUESTIONS[n - 1] if n <= len(S.QUESTIONS) else None, "a": found[n]})
    return rows


def _forms_meta(sess: dict, quest: str) -> dict:
    """What the page needs of the forms played: the quest's name, stages and objectives; names, places and where
    each ref stands (for the map)."""
    meta = {"name": quest, "kind": None, "stages": [], "objectives": [], "refs": {}, "quests": {}}
    for f in sess.get("forms") or []:
        qq = f.get("quest") or {}
        if qq.get("id"):
            meta["quests"][qq["id"]] = qq.get("name") or qq["id"]
        for ref in f.get("refs") or []:
            at = ref.get("at") or {}
            if at:
                meta["refs"][ref["id"]] = {k: at.get(k) for k in ("cell", "interior", "x", "y")}
        if (f.get("quest") or {}).get("id") != quest:
            continue
        meta["name"] = f["quest"].get("name") or quest
        meta["kind"] = f["quest"].get("kind")
        meta["stages"] = [{"n": s["number"], "ending": s.get("ending") or "none", "journal": s.get("journal") or ""}
                          for s in sorted(f.get("stages") or [], key=lambda s: s["number"])]
        meta["objectives"] = [{"n": o["number"], "text": o.get("text"), "shown": o.get("shown_at") or []}
                              for o in f.get("objectives") or []]
    w = sess.get("world") or {}
    meta["names"] = w.get("names") or {}
    meta["places"] = {c: {"name": p.get("name"), "interior": p.get("interior"), "entrance": p.get("entrance")}
                      for c, p in (w.get("places") or {}).items()}
    return meta


def _run_paths(root: Path) -> list[str]:
    idx = _json(root / "index.json")
    paths = [r["path"] for r in idx.get("runs") or [] if r.get("path")]
    if not paths:
        paths = [str(p.parent.relative_to(root)) for p in sorted(root.glob("*/*/run.json"))]
    return [p for p in paths if (root / p / "run.json").exists()]


def collect(root: Path = S.RUNS) -> dict:
    root = Path(root)
    runs, forms = [], {}
    for path in _run_paths(root):
        folder = root / path
        run = _json(folder / "run.json")
        sess = _json(folder / "session.json")
        quest = run.get("quest") or sess.get("quest") or path.split("/")[0]
        fh = run.get("forms_hash") or sess.get("forms_hash") or path
        key = f"{quest}@{fh}"
        if key not in forms:
            forms[key] = _forms_meta(sess, quest)
        ended = run.get("ended") or "open"
        how, label, each = outcome(ended, quest)
        st = steps(S.transcript(folder), quest)
        runs.append({
            "id": _slug(path), "path": path, "quest": quest, "qid": _slug(quest), "forms": key,
            "player": run.get("player") or "unknown", "source": run.get("source") or "designed",
            "model": run.get("model"), "created": run.get("created"), "ended": ended, "outcome": how,
            "outcome_label": label, "quests": each, "counts": run.get("counts") or {},
            "stages_done": (run.get("stages") or {}).get(quest) or [],
            "cost_usd": run.get("cost_usd"), "minutes": run.get("minutes"), "turns": run.get("turns"),
            "know": sess.get("know"), "at": sess.get("at"),
            "take": _read(folder / "take.md"), "answers": answers(_read(folder / "answers.md")),
            "brief": _read(folder / "brief.md"), "broken": sess.get("broken"), "steps": st,
        })
    return {"runs": runs, "forms": forms, "questions": list(S.QUESTIONS)}


def render(data: dict) -> str:
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", blob, 1)


def write(out: Path = DEFAULT_OUT, root: Path = S.RUNS) -> tuple[Path, int, int]:
    data = collect(root)
    html = render(data)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out, len(data["runs"]), len(html.encode("utf-8"))
