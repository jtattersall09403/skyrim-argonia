"""The milestone gate shared by both paper games (docs/design/paper-playtest.md; quest-playtest §1).

A milestone is every point where the journal changes: the quest starts, a stage is shown, an ending is reached. The
game shows the new entry and objective as a toast, asks the four questions, and refuses every command but `answer`
until they are answered. After an ending it asks for the player's notes. Each run keeps `milestones.json` (the
milestones with the record's information plan and the player's answers) and writes `milestones.md` from it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

QUESTIONS = (
    "What is going on? (who you work for, what has happened, why it matters, as far as you know)",
    "What are you expected to do next, and where?",
    "What options do you have for doing it? (the ways through you can see, and any choice in front of you)",
    "Is there any word, name, person or thing you do not understand? Do you know how you could find out?",
)
NOTES_ASK = ("The quest is over. Write your notes: what you now know and have, as you would tell a friend picking up "
             "your save. Give them in one command: answer '...'")
SHORT = ("Going on", "Next", "Ways", "Not understood")


def ask(entry: dict) -> str:
    """The toast for a milestone and the four questions."""
    head = {"start": "Quest started", "stage": "Journal updated", "ending": "Quest " + str(entry.get("ending") or "ended")}
    out = [f"*** {head.get(entry['kind'], 'Journal updated')}: {entry['title']} ***"]
    if entry.get("journal"):
        out.append(f"Journal: {entry['journal']}")
    out += [f"Objective: {o}" for o in entry.get("objectives") or []]
    out += ["", "The game pauses. Answer these four questions from what the game has shown you, in your own words, "
            "numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'"]
    out += [f"{i}. {q}" for i, q in enumerate(QUESTIONS, 1)]
    return "\n".join(out)


def refusal() -> str:
    return "The game is paused at a milestone. Answer the four questions first: answer '1. ... 2. ... 3. ... 4. ...'"


def split_answers(text: str) -> list[str]:
    """The player's answer split by its numbers 1 to 4; unnumbered text is all answer 1."""
    parts = re.split(r"(?:^|\s)([1-4])[.):]\s+", " " + text.strip())
    got = {}
    if len(parts) > 1:
        for i in range(1, len(parts) - 1, 2):
            got.setdefault(int(parts[i]), parts[i + 1].strip())
    else:
        got[1] = text.strip()
    return [got.get(i, "") for i in range(1, 5)]


def _cell(x) -> str:
    if isinstance(x, list):
        x = "<br>".join(f"- {_cell(v)}" for v in x)
    return str(x or "").replace("|", "/").replace("\n", " ").strip() or "(none)"


def markdown(quest: str, rows: list[dict]) -> str:
    """milestones.md: each milestone's plan beside the player's four answers."""
    out = [f"# Milestones: {quest}", ""]
    if not rows:
        out.append("(no milestone was reached)")
    for i, m in enumerate(rows, 1):
        plan = m.get("plan") or {}
        out += [f"## {i}. Stage {m['stage']} ({m['kind']}): {m['title']}", ""]
        if m.get("journal"):
            out += [f"Journal: {m['journal']}", ""]
        out += ["| | Plan | Player |", "|---|---|---|"]
        ans = m.get("answers") or ["", "", "", ""]
        for k, (label, key) in enumerate(zip(SHORT, ("going", "next", "ways", "terms"))):
            p = plan.get(key) if key != "terms" else plan.get("terms")
            if p is None and key != "terms" and not plan:
                p = "(no information plan)"
            out.append(f"| {label} | {_cell(p)} | {_cell(ans[k]) if m.get('answers') else '(not answered)'} |")
        out.append("")
    return "\n".join(out) + "\n"


def write(folder: Path, quest: str, rows: list[dict]) -> None:
    folder = Path(folder)
    (folder / "milestones.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (folder / "milestones.md").write_text(markdown(quest, rows), encoding="utf-8")


def plan_of(stage: dict, terms: list[dict] | None = None) -> dict:
    """A stage's information plan for the milestone table, with the terms first met at that stage."""
    info = stage.get("information") or {}
    met = [f"{t.get('term')}: {t.get('told') or ''}".strip(": ") for t in (terms or [])
           if str(t.get("meets", "")).split(" ")[0].split(":")[0] in (str(stage.get("id")),)]
    out = {k: info.get(k) for k in ("going", "next", "ways") if info.get(k) is not None}
    if met:
        out["terms"] = met
    return out
