#!/usr/bin/env python3
"""The no-assets guard (decision 0003): refuse game or mod files and decompiled code in the repo.

    no_assets.py --staged   files in the git index (pre-commit hook)
    no_assets.py --tree     every tracked file (the gate)
Exit 0 clean, 1 with one line per refused file.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANNED_EXT = set("esm esp esl bsa ba2 nif dds hkx tri fuz xwm wav fsb swf gfx pex seq npy lip btr bto".split())
MAGIC = [(b"Gamebryo File Format", "NIF"), (b"BSA\0", "BSA"), (b"DDS ", "DDS"),
         (b"\x57\xe0\xe0\x57", "HKX packfile"), (b"FSB5", "FSB5"), (b"TES4", "plugin record header"),
         (b"BND4", "FromSoftware BND4"), (b"DCX\0", "FromSoftware DCX")]
DECOMPILED = re.compile(r"undefined8|__thiscall|FUN_[0-9a-f]{6,}|DAT_[0-9a-f]{6,}|Ghidra [Dd]ecompiler|IDA Pro")
MAX_BYTES = 1_000_000


def magic_of(head):
    """Name of the game format a file's first bytes show, else ''."""
    if head[:4] == b"RIFF" and head[8:12] == b"XWMA":
        return "XWM"
    return next((name for sig, name in MAGIC if head.startswith(sig)), "")


def allowed():
    out = set()
    for line in (HERE / "allowlist.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def check_file(rel, data, allow):
    """Reasons to refuse one file (its path and bytes), empty when fine."""
    why = []
    ext = rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
    if ext in BANNED_EXT:
        why.append(f"banned extension .{ext}")
    m = magic_of(data[:32])
    if m:
        why.append(f"{m} magic bytes")
    if len(data) > MAX_BYTES and rel not in allow:
        why.append(f"over 1 MB ({len(data)} bytes) and not in allowlist.txt")
    text = data.decode("utf-8", "ignore") if b"\0" not in data[:4096] else ""
    if ext == "md":  # prose may name the signatures in inline code; pasted code blocks still count
        text = re.sub(r"(?<!`)`[^`\n]+`(?!`)", "", text)
    # the guard and its test name the signatures on purpose; nothing else may
    if DECOMPILED.search(text) and not rel.startswith("tooling/guards/") and rel != "tooling/tests/test_no_assets.py":
        why.append("decompiler signature in text")
    return why


def git(*args, root=None):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def scan(mode, root=None):
    """List of 'path: reason' lines for the staged files or the tracked tree."""
    if mode == "staged":
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z", root=root)
    else:
        names = git("ls-files", "-z", root=root)
    allow, bad = allowed(), []
    for rel in filter(None, names.decode().split("\0")):
        try:
            data = git("show", f":{rel}", root=root) if mode == "staged" else (Path(root or ".") / rel).read_bytes()
        except (subprocess.CalledProcessError, OSError):
            continue
        bad += [f"{rel}: {w}" for w in check_file(rel, data, allow)]
    return bad


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--staged", "--tree"):
        print(__doc__)
        return 2
    bad = scan(argv[1][2:])
    for line in bad:
        print("no-assets REFUSED " + line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
