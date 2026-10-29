"""The FormID allocator (decision 0009 §3): every record of ours keeps one FormID for good.

The table maps an EditorID (``ARG_`` plus the world id) to the object id it was first given. It is append-only:
an entry never changes and is never removed (a retired record's id is never reused, because the next id is
always past the highest ever given). ``check_append_only`` proves that against git's HEAD in the gate.

Storage: ``data/formids.json`` until db.py's FormID table lands (decision 0030), then that table through db.py;
the interface below stays.

    python3 -m tools.argonia_world.formids check     append-only against HEAD, ids in range and unique
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "data" / "formids.json"
MOD = "Argonia.esm"
EDID = re.compile(r"^ARG_[A-Za-z0-9_]+$")


class Allocator:
    """Hands out object ids for EditorIDs; ``save`` writes only when something new was allocated."""

    def __init__(self, path: Path = TABLE, mod: str = MOD, frozen: bool = False):
        self.path, self.mod, self.frozen = Path(path), mod, frozen
        self.ids: dict[str, int] = {}
        if self.path.exists():
            doc = json.loads(self.path.read_text(encoding="utf-8"))
            if doc.get("mod", mod) != mod:
                raise ValueError(f"{self.path}: table is for {doc['mod']}, not {mod}")
            self.ids = {k: int(v, 16) for k, v in doc["ids"].items()}
        self.dirty = False

    def next_id(self) -> int:
        return max(self.ids.values(), default=su.FORMID_FIRST - 1) + 1

    def get(self, edid: str) -> int:
        if edid in self.ids:
            return self.ids[edid]
        if not EDID.match(edid) or len(edid) > su.EDITOR_ID_MAX:
            raise ValueError(f"not an Argonia EditorID: {edid!r}")
        if self.frozen:
            raise KeyError(f"{edid}: no FormID yet; run `make plugin` and commit data/formids.json")
        new = self.next_id()
        if new > su.FORMID_LAST:
            raise OverflowError("FormID space exhausted: split by kind into ESL-flagged helpers (0.4 §a)")
        self.ids[edid] = new
        self.dirty = True
        return new

    def form_key(self, edid: str) -> str:
        """Mutagen's FormKey spelling, ``000800:Argonia.esm``."""
        return f"{self.get(edid):06X}:{self.mod}"

    def save(self) -> bool:
        if not self.dirty:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(dumps(self.mod, self.ids), encoding="utf-8")
        self.dirty = False
        return True


def dumps(mod: str, ids: dict[str, int]) -> str:
    """One entry per line, in allocation order, so a new id is a one-line diff at the end."""
    body = ",\n".join(f'  {json.dumps(k)}: "{v:06X}"' for k, v in sorted(ids.items(), key=lambda kv: kv[1]))
    return f'{{\n "schema": 1,\n "mod": {json.dumps(mod)},\n "ids": {{\n{body}\n }}\n}}\n'


def check_append_only(old: dict[str, int], new: dict[str, int]) -> list[str]:
    """Reasons the table is not a valid successor of ``old`` (empty when it is)."""
    errs = [f"{k}: removed (was {v:06X})" for k, v in old.items() if k not in new]
    errs += [f"{k}: changed {v:06X} -> {new[k]:06X}" for k, v in old.items() if k in new and new[k] != v]
    seen: dict[int, str] = {}
    for k, v in new.items():
        if not su.FORMID_FIRST <= v <= su.FORMID_LAST:
            errs.append(f"{k}: {v:06X} out of range")
        if v in seen:
            errs.append(f"{k}: {v:06X} also given to {seen[v]}")
        seen[v] = k
    top = max(old.values(), default=su.FORMID_FIRST - 1)
    errs += [f"{k}: new id {v:06X} reuses the range at or below {top:06X}"
             for k, v in new.items() if k not in old and v <= top]
    return errs


def _head_table() -> dict[str, int]:
    rel = TABLE.relative_to(ROOT).as_posix()
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, check=False, capture_output=True, text=True)
    if r.returncode != 0:
        return {}  # not committed yet
    return {k: int(v, 16) for k, v in json.loads(r.stdout)["ids"].items()}


def main(argv: list[str]) -> int:
    if argv[:1] != ["check"]:
        print(__doc__)
        return 2
    errs = check_append_only(_head_table(), Allocator().ids)
    for e in errs:
        print(f"formids: {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
