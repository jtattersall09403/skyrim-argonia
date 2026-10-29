#!/usr/bin/env python3
"""Write and check agent briefs (docs/ways-of-working.md section 2).

    brief_template.py --write [--lane L --paths P.. --acceptance A --report R --test-level L3 --route "3 why" --prior-art T]
    brief_template.py --check <file>     exit 2 naming the first missing or unfilled field
    brief_template.py --chunk <id>       the chunk's row from docs/phases/*/README.md and its brief file

Fields: Lane, Paths, Acceptance (a runnable command or a number; no <placeholder>), Report path,
Test level (L1-L6), Route (decision 0010 route 1-7, then why higher routes were not enough), Prior art.
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROW = re.compile(r"^\|\s*([\w.-]+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)")
FIELDS = ("Lane", "Paths", "Acceptance", "Report path", "Test level", "Route", "Prior art")
PLACEHOLDER = re.compile(r"<[^<>\n]+>")
COMMAND = re.compile(r"\b(python3?|pytest|make|bash|sh|node|cmake|git|grep|\./\S+)\b|`[^`]+`|\d")


def parse(text):
    """{field: value} for every 'Field: value' line (a value may continue on indented lines)."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*]\s*)?(%s)\s*:\s*(.*)$" % "|".join(FIELDS), line, re.I)
        if m:
            cur = next(f for f in FIELDS if f.lower() == m.group(1).lower())
            out[cur] = m.group(2).strip()
        elif cur and line.startswith((" ", "\t")) and line.strip():
            out[cur] += " " + line.strip()
        else:
            cur = None
    return out


def problem(fields):
    """First problem with a parsed brief, or ''."""
    for f in FIELDS:
        v = fields.get(f, "")
        if not v:
            return f"missing field: {f}"
        if PLACEHOLDER.search(v):
            return f"{f} still has a <placeholder>"
    if not COMMAND.search(fields["Acceptance"]):
        return "Acceptance names no runnable command or number"
    if not re.fullmatch(r"L[1-6]\b.*", fields["Test level"]):
        return "Test level must be L1 to L6"
    m = re.match(r"([1-7])\b\W*(.*)$", fields["Route"])
    if not m:
        return "Route must start with a decision 0010 route number 1 to 7"
    if m.group(1) != "1" and len(m.group(2).split()) < 3:
        return "Route must say why higher routes (lower numbers) were not enough"
    return ""


def chunk_row(cid):
    """(table row, brief file path) for a chunk id, or None."""
    for readme in sorted(glob.glob(os.path.join(ROOT, "docs/phases/*/README.md"))):
        for line in open(readme, encoding="utf-8"):
            m = ROW.match(line)
            if m and m.group(1) == cid:
                return line.strip(), os.path.normpath(os.path.join(os.path.dirname(readme), m.group(3).split("#")[0]))
    return None


def render(a):
    v = {"Lane": a.lane, "Paths": " ".join(a.paths or []), "Acceptance": a.acceptance, "Report path": a.report,
         "Test level": a.test_level, "Route": a.route, "Prior art": a.prior_art}
    ph = {"Lane": "<lane id>", "Paths": "<paths the lane owns>", "Acceptance": "<command or number>",
          "Report path": "<report path>", "Test level": "<L1-L6>", "Route": "<1-7 and why higher routes were not enough>",
          "Prior art": "<what was searched and reused>"}
    return "\n".join(f"{f}: {v[f] or ph[f]}" for f in FIELDS) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", metavar="FILE")
    p.add_argument("--chunk", metavar="ID")
    p.add_argument("--lane")
    p.add_argument("--paths", nargs="*")
    p.add_argument("--acceptance")
    p.add_argument("--report")
    p.add_argument("--test-level")
    p.add_argument("--route")
    p.add_argument("--prior-art")
    a = p.parse_args(argv)
    if a.chunk:
        r = chunk_row(a.chunk)
        if not r:
            print(f"no chunk {a.chunk} in docs/phases/*/README.md")
            return 1
        print(r[0] + "\nbrief file: " + os.path.relpath(r[1], ROOT))
        return 0
    if a.check:
        why = problem(parse(open(a.check, encoding="utf-8").read()))
        if why:
            print(f"brief refused: {why}")
            return 2
        print("brief ok")
        return 0
    if a.write:
        text = render(a)
        print(text, end="")
        why = problem(parse(text))
        if why:
            print(f"# not yet valid: {why}", file=sys.stderr)
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
