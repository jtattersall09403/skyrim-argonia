"""The owner's page for exploring the paper playtest runs (tools/playtest/page.py): made from the kept runs and from
an empty runs folder, it holds every run, embeds its data safely and loads nothing but fonts from outside."""
import json
import re

from tools.playtest import page as P
from tools.playtest import session as S


def _data(html: str) -> dict:
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    assert m, "the embedded data block is missing"
    return json.loads(m.group(1))


def _check_contract(html: str) -> None:
    assert html.lstrip().startswith("<title>")
    assert "<!doctype" not in html.lower() and "<body" not in html.lower()
    assert '@media (prefers-color-scheme: dark)' in html and ':root[data-theme="dark"]' in html
    for src in re.findall(r'<script[^>]+src="([^"]+)"', html):
        raise AssertionError(f"the page loads a script from outside: {src}")
    for href in re.findall(r'<link[^>]+href="([^"]+)"', html):
        assert href.startswith(("https://fonts.googleapis.com", "https://fonts.gstatic.com")), href
    assert "fetch(" not in html


def test_page_from_the_kept_runs(tmp_path):
    out, n, size = P.write(tmp_path / "index.html", S.RUNS)
    html = out.read_text(encoding="utf-8")
    _check_contract(html)
    data = _data(html)
    kept = sorted(p.parent.relative_to(S.RUNS).as_posix() for p in S.RUNS.glob("*/*/run.json"))
    assert n == len(data["runs"]) and sorted({r["path"] for r in data["runs"]}) == kept
    for run in data["runs"]:
        assert run["id"] in html and run["forms"] in data["forms"]
        assert len(run["steps"]) == len(S.transcript(S.RUNS / run["path"]))
    assert len({r["id"] for r in data["runs"]}) == len(data["runs"])
    assert size < 4_000_000


def test_page_from_an_empty_runs_folder(tmp_path):
    out, n, _ = P.write(tmp_path / "page.html", tmp_path / "runs")
    html = out.read_text(encoding="utf-8")
    _check_contract(html)
    assert n == 0 and _data(html)["runs"] == []


def test_screen_lines_flags_and_plain_words():
    lines = P.classify('Sample-Contact: "[not yet written; the gist:] Work."\nObjective completed: Find her.\n'
                       'Journal entry (Off the Pier): I found her.\nTopics:\n  1. Will you take me in?\n  2. Bye.')
    assert [x["k"] for x in lines] == ["speech", "objdone", "journal", "menu"]
    assert lines[0]["who"] == "Sample-Contact" and lines[0].get("ph") == 1
    assert lines[3]["options"] == ["Will you take me in?", "Bye."]
    assert P.plain("say 1", lines[3]["options"], {}) == "Chose “Will you take me in?”"
    assert P.plain("go marker 1", None, {"1": "Sample-Contact"}) == "Went to marker 1, Sample-Contact"
    rows = [{"think": None, "command": "(new game)", "result": "A new game.", "summary": None}] + [
        {"think": t, "command": "map", "result": "You: here", "summary": {"stages": {"q": 20}}}
        for t in ("where now", "where now", "I am stuck")]
    steps = P.steps(rows + [{"think": "x", "command": "use jar", "result": "HARNESS ERROR (the run has stopped): x",
                             "summary": None}], "q")
    assert steps[2]["flags"] == ["repeat"] and "stuck" in steps[3]["flags"] and steps[4]["flags"] == ["harness"]
    assert steps[1]["from"] is None and steps[1]["stage"] == 20


def test_a_chained_run_is_shown_under_every_quest_it_played():
    def row(stages):
        return {"think": "x", "command": "look", "result": "", "summary": {"stages": stages}}
    rows = [row({"q1": 10, "q2": 0, "q3": 0}), row({"q1": 90, "q2": 0, "q3": 0, "q4": 10}), row({"q1": 90, "q2": 10, "q3": 0, "q4": 10})]
    assert P._played({"stages": {"q1": [10, 90], "q2": [0, 10], "q3": [0], "q4": [10]}}, rows, "q1") == ["q1", "q2", "q4"]


def test_answers_are_matched_to_the_questions():
    rows = P.answers("1. Go on. 2. The Reed, because I agreed. 3. The placeholder. 4. Write the lines.")
    assert [r["n"] for r in rows] == [1, 2, 3, 4] and rows[1]["q"] == S.QUESTIONS[1]
    assert P.outcome("stopped by the player (q1 completed, q2 active)", "q1")[:1] == ("completed",)
    assert P.outcome("command limit (q1 active)", "q1")[0] == "cutoff"
    assert P.outcome("quest failed", "q1")[0] == "failed"
    assert P.answers("I would not go on.") == [{"q": None, "a": "I would not go on."}]
