"""The owner's page of the paper playtest runs (docs/design/paper-playtest.md): every quest's milestones, each run's
four answers beside the record's information plan, and the player's notes at the end.

Reads `<runs>/<quest id>/<run>/milestones.json`, `run.json` and `notes.md`; a run kept from before milestones is
counted, not shown. Writes one self-contained HTML page (no script, nothing loaded from outside).

    python3 -m tools.playtest page [--out out/playtest/index.html] [--runs story/playtests]
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from tools.playtest import milestone as M
from tools.playtest import session as S

DEFAULT_OUT = S.REPO / "out/playtest/index.html"

STYLE = """
:root { --bg: #fbfaf7; --fg: #1d1d1b; --muted: #6b6a66; --line: #dddbd4; --card: #ffffff; --accent: #2f6b4f; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161614; --fg: #ecebe6; --muted: #a3a29c; --line: #34332f; --card: #1f1f1c; --accent: #7fc4a0; } }
:root[data-theme="dark"] { --bg: #161614; --fg: #ecebe6; --muted: #a3a29c; --line: #34332f; --card: #1f1f1c;
  --accent: #7fc4a0; }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 system-ui, sans-serif; margin: 0 auto;
  max-width: 1100px; padding: 16px; }
h1 { font-size: 22px; } h2 { font-size: 19px; margin-top: 32px; border-bottom: 1px solid var(--line); }
h3 { font-size: 16px; color: var(--accent); }
details { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px;
  margin: 10px 0; }
summary { cursor: pointer; font-weight: 600; }
.meta, .muted { color: var(--muted); font-size: 13px; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 14px; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 5px 8px; vertical-align: top; text-align: left; }
th { width: 120px; }
ul { margin: 0; padding-left: 18px; }
"""


def _e(x) -> str:
    return html.escape(str(x))


def _cell(v) -> str:
    if v is None or v == "" or v == []:
        return '<span class="muted">(none)</span>'
    if isinstance(v, list):
        return "<ul>" + "".join(f"<li>{_e(x)}</li>" for x in v) + "</ul>"
    return _e(v)


def collect(root: Path) -> dict:
    """{quest id: [run, ...]} for runs with milestones, newest first, and the count of older runs."""
    quests, older = {}, 0
    for rj in sorted(Path(root).glob("*/*/run.json")):
        folder = rj.parent
        ms = folder / "milestones.json"
        if not ms.exists():
            older += 1
            continue
        run = json.loads(rj.read_text(encoding="utf-8"))
        notes = folder / "notes.md"
        quests.setdefault(folder.parent.name, []).append({
            "name": folder.name, "run": run, "milestones": json.loads(ms.read_text(encoding="utf-8")),
            "notes": notes.read_text(encoding="utf-8").strip() if notes.exists() else None})
    for runs in quests.values():
        runs.sort(key=lambda r: r["name"], reverse=True)
    return {"quests": quests, "older": older}


def _run(r) -> str:
    run = r["run"]
    meta = ", ".join(_e(x) for x in (run.get("moment"), run.get("model"), run.get("effort"),
                                       f"way {run['way']}" if run.get("way") else None,
                                       f"choose {run['choose']}" if run.get("choose") else None,
                                       f"ended {run.get('ended')}",
                                       f"${run['cost_usd']:.2f}" if run.get("cost_usd") else None) if x)
    out = [f"<details><summary>{_e(r['name'])}</summary><p class=\"meta\">{meta}</p>"]
    for i, m in enumerate(r["milestones"], 1):
        plan = m.get("plan") or {}
        ans = m.get("answers") or [None] * 4
        out.append(f"<h3>{i}. Stage {_e(m['stage'])} ({_e(m['kind'])})</h3>")
        if m.get("journal"):
            out.append(f"<p class=\"muted\">Journal: {_e(m['journal'])}</p>")
        rows = "".join(f"<tr><th>{_e(lbl)}</th><td>{_cell(plan.get(k))}</td><td>{_cell(a)}</td></tr>"
                       for lbl, k, a in zip(M.SHORT, ("going", "next", "ways", "terms"), ans))
        out.append(f"<div class=\"scroll\"><table><tr><th></th><th>Plan</th><th>Player</th></tr>{rows}</table></div>")
    out.append(f"<h3>Notes</h3><p>{_e(r['notes']) if r['notes'] else '<span class=muted>(none)</span>'}</p>")
    out.append("</details>")
    return "".join(out)


def render(data: dict) -> str:
    body = ["<h1>Paper playtest runs</h1>",
            "<p class=\"muted\">At every milestone the player says what is going on, what they will do next and what "
            "options they have; each answer stands beside the quest's information plan.</p>"]
    if not data["quests"]:
        body.append("<p>No run with milestones yet.</p>")
    for q in sorted(data["quests"]):
        body.append(f"<h2>{_e(q)}</h2>" + "".join(_run(r) for r in data["quests"][q]))
    if data["older"]:
        body.append(f"<p class=\"muted\">{data['older']} earlier run(s) from before milestones are kept in the runs "
                    "folder and not shown.</p>")
    return (f"<title>Paper playtest runs</title>\n<meta name=\"viewport\" content=\"width=device-width, "
            f"initial-scale=1\">\n<style>{STYLE}</style>\n" + "\n".join(body) + "\n")


def write(out: Path = DEFAULT_OUT, root: Path = S.RUNS) -> tuple[Path, int, int]:
    data = collect(root)
    text = render(data)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out, sum(len(v) for v in data["quests"].values()), len(text.encode())
