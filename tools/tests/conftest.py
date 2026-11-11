"""Every test stands alone: it writes the pass ledger under its own tmp dir, never ~/.argonia/round/passes.jsonl,
and it never reads or writes the tree's own build outputs (out/), which change with every build and are absent in a
worktree. A module's path constant under out/ points into a tmp dir for the whole session; out/tools (the compiled
tools the dotnet tests run) stays."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
OUT, KEEP = REPO / "out", REPO / "out" / "tools"


def _reroot(root: Path) -> None:
    for name, mod in list(sys.modules.items()):
        if not name.startswith(("tools.", "tooling.")) or mod is None:
            continue
        for attr, v in list(vars(mod).items()):
            if isinstance(v, Path) and v.is_relative_to(OUT) and not v.is_relative_to(KEEP):
                setattr(mod, attr, root / v.relative_to(OUT))


@pytest.fixture(scope="session", autouse=True)
def _own_out_session(tmp_path_factory):
    root = tmp_path_factory.mktemp("tree-out")
    _reroot(root)
    return root


@pytest.fixture(autouse=True)
def _own_out(_own_out_session):
    _reroot(_own_out_session)   # modules a test imported late


@pytest.fixture(autouse=True)
def _isolated_pass_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("ARGONIA_PASSES", str(tmp_path / "passes.jsonl"))
