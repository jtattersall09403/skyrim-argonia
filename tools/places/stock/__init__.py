"""Stocking a place (skill `place-stock`; contract docs/design/place-studio.md, "Stock").

    python -m tools.places stock classify <place_id> [--out DIR] [--json PATH]
    python -m tools.places stock derive <place_id> [--out DIR] [--to PATH]
    python -m tools.places stock vanilla [--out PATH]
"""
from __future__ import annotations

import importlib
import sys

VERBS = ("classify", "derive", "vanilla")


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in VERBS:
        print(__doc__.strip(), file=sys.stderr)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    return int(importlib.import_module(f"tools.places.stock.{argv[0]}").main(argv[1:]) or 0)
