"""Named checks: the world's rules that SQL constraints cannot state (decision 0030 §3).

Each check reads the loaded world through db.World and returns one line per violation. The load itself (types,
keys, foreign keys, CHECKs) is the rest of the integrity gate; a rule goes here only when the schema cannot hold it.
"""
from __future__ import annotations

from typing import Callable

CHECKS: dict[str, Callable] = {}


def check(name: str):
    def deco(fn):
        CHECKS[name] = fn
        return fn
    return deco


def run(w, only: list[str] | None = None) -> list[str]:
    out = []
    for name, fn in CHECKS.items():
        if only and name not in only:
            continue
        out += [f"[{name}] {e}" for e in fn(w)]
    return out
