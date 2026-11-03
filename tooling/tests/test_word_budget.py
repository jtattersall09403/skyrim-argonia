from pathlib import Path

LIMIT = 1800  # the owner relaxed the budget on 2026-11-02 (CLAUDE.md: keep it lean) and added four binding lines on 2026-11-03 (interruptions, no reruns, direct screens); 1,381 words that day
ROOT = Path(__file__).resolve().parents[2]


def words(text):
    return len(text.split())


def test_claude_md_under_budget():
    n = words((ROOT / "CLAUDE.md").read_text())
    assert n < LIMIT, f"CLAUDE.md is {n} words; the budget is {LIMIT}"


def test_budget_fails_on_purpose():
    # The same measure on a fixture that is over budget must read as over.
    assert words("word " * (LIMIT + 1)) >= LIMIT
