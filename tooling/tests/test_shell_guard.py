import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = str(Path(__file__).resolve().parents[1] / "shell_guard.py")


def run(cmd):
    p = subprocess.run([sys.executable, GUARD], input=json.dumps({"tool_input": {"command": cmd}}),
                       capture_output=True, text=True)
    return p.returncode, p.stderr


@pytest.mark.parametrize("cmd", [
    "sleep 5", "rtk sleep 5", "make && sleep 1",
    "until test -f x; do echo; done", "while kill -0 123; do :; done", "tail -f log", "tail -n5 --pid=3 log",
    "git checkout -- file", "git restore file", "git stash", "git reset --hard HEAD~1", "git update-ref refs/heads/main abc123",
    "pkill python", "killall node", "kill -9 -1", "git commit -m x --", "git commit -m x -- ; ls",
    "cat ~/.argonia/secrets.env", "head -3 ~/.argonia/secrets.env", "rtk less ~/.argonia/secrets.env"])
def test_refused(cmd):
    code, err = run(cmd)
    assert code == 2 and err.startswith("shell_guard:")


@pytest.mark.parametrize("cmd", [
    "ls", "git status", "git commit -m x -- a.py", "git checkout main", "tail -n 20 log", "rtk git diff",
    "kill 123", "echo sleeping", "grep secrets docs/x.md", "make check"])
def test_allowed(cmd):
    assert run(cmd)[0] == 0
