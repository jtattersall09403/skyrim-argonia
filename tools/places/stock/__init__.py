"""Stocking a place (skill `place-stock`; contract docs/design/place-studio.md, "Stock"; the ladder docs/design/items.md).

    python -m tools.places stock classify <place_id> [--out DIR] [--json PATH]
    python -m tools.places stock derive <place_id> [--out DIR] [--to PATH]
    python -m tools.places stock vanilla [--out PATH]
    python -m tools.places stock report <place_id> [--out DIR] [--json PATH]
    python -m tools.places stock reach <place_id> [--source PATH] [--md PATH]
    python -m tools.places stock mix <place_id> [--source PATH] [--json PATH]
"""
from __future__ import annotations

import importlib
import sys

VERBS = {"classify": ("classify", "main"), "derive": ("derive", "main"), "vanilla": ("vanilla", "main"),
         "report": ("report", "main"), "reach": ("reach", "main_reach"), "mix": ("reach", "main_mix")}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in VERBS:
        print(__doc__.strip(), file=sys.stderr)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    mod, fn = VERBS[argv[0]]
    return int(getattr(importlib.import_module(f"tools.places.stock.{mod}"), fn)(argv[1:]) or 0)
