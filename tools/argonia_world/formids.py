"""The FormID allocator (decision 0009 §3): every record of ours keeps one FormID for good.

The world database's ``formid`` table (decision 0030, read and written only through db.py) maps an EditorID
(``ARG_`` plus the world id) to the object id it was first given in its plugin. It is append-only: a row never
changes and is never removed (a retired record's id is never reused, because the next id is always past the
highest ever given). ``check_append_only`` proves that against git's HEAD in the gate.

    python3 -m tools.argonia_world.formids check     append-only against HEAD, ids in range and unique
"""
from __future__ import annotations

import re
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[2]
MOD = "Argonia.esm"
EDID = re.compile(r"^ARG_[A-Za-z0-9_]+$")


def read_ids(world, mod: str = MOD) -> dict[str, int]:
    return {r.editor_id: r.form_id for r in world.rows("formid", plugin=mod)}


class Allocator:
    """Hands out object ids for EditorIDs; ``save`` writes the formid table only when something was allocated.

    ``world`` is a db.World (default: ``db.open()``); ``frozen`` refuses to allocate (the gate's regeneration)."""

    def __init__(self, world=None, mod: str = MOD, frozen: bool = False):
        self.world = world if world is not None else db.open()
        self.mod, self.frozen = mod, frozen
        self.ids = read_ids(self.world, mod)
        self.dirty = False

    def next_id(self) -> int:
        return max(self.ids.values(), default=su.FORMID_FIRST - 1) + 1

    def get(self, edid: str, record_type: str | None = None, entity_key: str | None = None) -> int:
        if edid in self.ids:
            return self.ids[edid]
        if not EDID.match(edid) or len(edid) > su.EDITOR_ID_MAX:
            raise ValueError(f"not an Argonia EditorID: {edid!r}")
        if self.frozen:
            raise KeyError(f"{edid}: no FormID yet; run `make plugin` and commit the formid table")
        new = self.next_id()
        if new > su.FORMID_LAST:
            raise OverflowError("FormID space exhausted: split by kind into ESL-flagged helpers (0.4 §a)")
        self.world.insert("formid", editor_id=edid, plugin=self.mod, form_id=new, record_type=record_type,
                          entity_key=entity_key)
        self.ids[edid] = new
        self.dirty = True
        return new

    def form_key(self, edid: str, record_type: str | None = None, entity_key: str | None = None) -> str:
        """Mutagen's FormKey spelling, ``000800:Argonia.esm``."""
        return f"{self.get(edid, record_type, entity_key):06X}:{self.mod}"

    def save(self) -> bool:
        if not self.dirty:
            return False
        self.world.save(["formid"])
        self.dirty = False
        return True


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


def head_ids(mod: str = MOD) -> dict[str, int]:
    """The formid table as HEAD has it: HEAD's schema and tables loaded through db.py in a scratch root."""
    r = subprocess.run(["git", "archive", "HEAD", db.SCHEMA, db.DB_DIR], cwd=ROOT, capture_output=True, check=False)
    if r.returncode != 0:
        return {}  # not committed yet
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=BytesIO(r.stdout)) as t:
            t.extractall(tmp, filter="data")
        try:
            return read_ids(db.load(tmp, strict=False), mod)
        except Exception:  # HEAD predates the formid table  # noqa: BLE001
            return {}


def main(argv: list[str]) -> int:
    if argv[:1] != ["check"]:
        print(__doc__)
        return 2
    errs = check_append_only(head_ids(), read_ids(db.open()))
    for e in errs:
        print(f"formids: {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
