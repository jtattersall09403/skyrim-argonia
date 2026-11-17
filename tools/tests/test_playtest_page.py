"""The owner's page of the paper playtest runs (tools/playtest/page.py): each quest's milestones with each run's
answers beside the plan, self-contained, from the kept runs and from an empty folder."""
import json
import re

from tools.playtest import page as P
from tools.playtest import session as S


def _check_contract(text: str) -> None:
    assert text.lstrip().startswith("<title>")
    assert "<!doctype" not in text.lower() and "<body" not in text.lower()
    assert '@media (prefers-color-scheme: dark)' in text and ':root[data-theme="dark"]' in text
    assert not re.findall(r'<script[^>]+src=', text) and "<link" not in text


def test_page_from_the_kept_runs(tmp_path):
    out, n, _size = P.write(tmp_path / "index.html", S.RUNS)
    _check_contract(out.read_text(encoding="utf-8"))
    assert n == len(list(S.RUNS.glob("*/*/milestones.json")))


def test_page_from_an_empty_runs_folder(tmp_path):
    out, n, _ = P.write(tmp_path / "index.html", tmp_path / "none")
    assert n == 0 and "No run with milestones yet." in out.read_text(encoding="utf-8")


def test_a_run_shows_plan_beside_answers(tmp_path):
    run = tmp_path / "runs/quest.x/20261117T000000Z-designed"
    run.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps({"moment": "designed", "ended": "complete"}))
    (run / "milestones.json").write_text(json.dumps([{"stage": 10, "kind": "start", "journal": "J <b>",
        "plan": {"going": "Teeka lost her satchel", "ways": ["ask", "pick"]},
        "answers": ["Teeka lost it", "Ask Hanu", "Ask", "None"]}]))
    (run / "notes.md").write_text("I have ten gold.\n")
    text = P.write(tmp_path / "i.html", tmp_path / "runs")[0].read_text(encoding="utf-8")
    assert "<td>Teeka lost her satchel</td><td>Teeka lost it</td>" in text and "<li>pick</li>" in text
    assert "J &lt;b&gt;" in text and "I have ten gold." in text
