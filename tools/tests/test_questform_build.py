"""`ArgoniaPlugin questform --selftest`: the generic quest builder refuses each wrong form with its rule (no game data)."""

import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOTNET = Path.home() / ".dotnet"


@pytest.mark.skipif(not DOTNET.exists(), reason="~/.dotnet is absent")
def test_questform_selftest():
    env = {
        **os.environ,
        "DOTNET_ROOT": str(DOTNET),
        "PATH": f"{DOTNET}:{os.environ['PATH']}",
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_NOLOGO": "1",
    }
    out = REPO / "out" / "tools" / "ArgoniaPlugin"
    build = subprocess.run(
        ["dotnet", "build", "-c", "Release", "-o", str(out), "tools/ArgoniaPlugin"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stdout[-2000:]
    run = subprocess.run(
        ["dotnet", str(out / "ArgoniaPlugin.dll"), "questform", "--selftest"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
