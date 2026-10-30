#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash: refuse a few commands that waste time or destroy work.

Reads the tool-call JSON on stdin; exit 2 with a one-line reason refuses, exit 0 allows.
"""
import json
import re
import sys

START = r"(?:^|[;&|(]\s*|\bdo\s+|\bthen\s+)(?:rtk\s+)?"
RULES = [
    (START + r"sleep\b", "no sleep: run long jobs under job_guard.sh and wait with it"),
    (r"\buntil\b[^\n]*;\s*do\b", "no poll loops: use job_guard.sh wait"),
    (r"\bwhile\b[^\n]*\bkill\s+-0\b", "no poll loops: use job_guard.sh wait"),
    (START + r"tail\b[^|;&\n]*\s(-[a-zA-Z]*f\b|--follow|--pid)", "no tail -f or --pid: use job_guard.sh wait"),
    (START + r"git\s+checkout\s+--(\s|$)", "git checkout -- discards work: use the Edit tool"),
    (START + r"git\s+restore\b", "git restore discards work: use the Edit tool"),
    (START + r"git\s+stash\b", "git stash hides work from other lanes: commit or leave it"),
    (START + r"git\s+reset\s+--hard\b", "git reset --hard discards work"),
    (START + r"git\s+update-ref\b", "git update-ref can drop other lanes' commits (2026-10-30): commit by pathspec"),
    (r"\bGIT_INDEX_FILE=", "a temporary git index commits a stale view of shared files (2026-10-30, twice): git add + git commit -- <paths>"),
    (START + r"(pkill|killall)\b", "pkill/killall can hit other lanes: kill one pid you started"),
    (START + r"kill\s+-9\s+-1\b", "kill -9 -1 kills every process"),
    (START + r"git\s+commit\b[^;&|\n]*\s--(\s*$|\s*[;&|])", "git commit with an empty pathspec commits everything staged"),
    (START + r"(cat|less|head|more|tail)\b[^;&|\n]*secrets\.env", "never read ~/.argonia/secrets.env"),
]


def reason(cmd):
    """Why a command is refused, or ''."""
    for pat, why in RULES:
        if re.search(pat, cmd, re.M):
            return why
    return ""


def main():
    try:
        cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
    except ValueError:
        return 0
    why = reason(cmd)
    if why:
        print("shell_guard: " + why, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
