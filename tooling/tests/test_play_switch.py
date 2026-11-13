"""The play switch Worker's offline tests (infra/cloudflare/test), under node: the play machine's rules and the
studio's address. The tests that reach AWS (state.mjs, switch.mjs, studio_live.mjs) are run by hand, never here."""
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[2] / "infra" / "cloudflare" / "test"


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
@pytest.mark.parametrize("name", ["heartbeat", "spot", "pool", "studio"])
def test_play_switch(name):
    r = subprocess.run(["node", str(TESTS / f"{name}.mjs")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
