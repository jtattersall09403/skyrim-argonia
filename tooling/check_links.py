#!/usr/bin/env python3
"""Every relative markdown link under docs/ and CLAUDE.md must resolve to a file (anchors ignored)."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"\]\(([^)\s]+)\)")


def broken(root=ROOT):
    # docs/design/ is imported unchanged from the old project (0.1 §f); its internal links are not ours to fix
    files = [f for f in glob.glob(os.path.join(root, "docs/**/*.md"), recursive=True)
             if not f.startswith(os.path.join(root, "docs/design/")) or f.endswith("docs/design/goals.md")
             or f.endswith("docs/design/README.md")] + [os.path.join(root, "CLAUDE.md")]
    out = []
    for f in sorted(files):
        if not os.path.exists(f):
            continue
        text = re.sub(r"```.*?```|`[^`\n]*`", "", open(f, encoding="utf-8").read(), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"[a-z]+:|#|mailto:", target):
                continue
            path = target.split("#")[0]
            if path and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), path))):
                out.append(f"{os.path.relpath(f, root)}: {target}")
    return out


if __name__ == "__main__":
    bad = broken()
    for b in bad:
        print("broken link " + b)
    sys.exit(1 if bad else 0)
