"""Every test writes the pass ledger under its own tmp dir, never ~/.argonia/round/passes.jsonl."""
import pytest


@pytest.fixture(autouse=True)
def _isolated_pass_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("ARGONIA_PASSES", str(tmp_path / "passes.jsonl"))
