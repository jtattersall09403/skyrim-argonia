"""Studio saves (docs/design/place-studio.md, Edits and Studio API).

Named saves are `newworld/places/<place_id>/edits/<save_id>.json`, committed and pushed by path after each write,
so they survive the machine stopping and a lost disk. The autosave is `out/places/autosave/<place_id>.json`, kept
on disk and copied to the private bucket, never committed. Every write is atomic (temp file, fsync, rename).

Each save carries `rev`, a counter the server raises on every write. A PUT carries the `rev` the tab last read
(0 for a new save); if the file on disk has moved on, the write is refused with 409 and the current rev, so a
stale tab never silently overwrites newer work."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SAVE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
PLACE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
AUTOSAVE = "autosave"


class Conflict(Exception):
    def __init__(self, current: dict):
        super().__init__("stale")
        self.current = current


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    fd = os.open(p.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Saves:
    def __init__(self, places: Path, out: Path) -> None:
        self.places, self.out = places, out

    def path(self, place_id: str, save_id: str) -> Path:
        if not PLACE_ID.match(place_id) or not SAVE_ID.match(save_id):
            raise ValueError("bad place or save id (lower case letters, digits, dot, dash, underscore)")
        if save_id == AUTOSAVE:
            return self.out / "autosave" / f"{place_id}.json"
        return self.places / place_id / "edits" / f"{save_id}.json"

    def read(self, place_id: str, save_id: str) -> dict | None:
        p = self.path(place_id, save_id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def list(self, place_id: str) -> list[dict]:
        out = []
        files = sorted((self.places / place_id / "edits").glob("*.json"))
        auto = self.path(place_id, AUTOSAVE)
        for p in files + ([auto] if auto.exists() else []):
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            out.append({"save_id": s.get("save_id", p.stem if p != auto else AUTOSAVE), "name": s.get("name"),
                        "at": s.get("at"), "final": bool(s.get("final")), "rev": s.get("rev", 0),
                        "ops": len(s.get("ops") or []), "path": str(p)})
        return sorted(out, key=lambda s: s["at"] or "", reverse=True)

    def write(self, place_id: str, save_id: str, body: dict) -> dict:
        """Write a save if body['rev'] equals the rev on disk (0 when there is none); returns the stored save."""
        p = self.path(place_id, save_id)
        cur = self.read(place_id, save_id)
        have = (cur or {}).get("rev", 0)
        if int(body.get("rev") or 0) != have:
            raise Conflict({"rev": have, "at": (cur or {}).get("at"), "name": (cur or {}).get("name")})
        if cur and cur.get("final"):
            raise Conflict({"rev": have, "at": cur.get("at"), "final": True})
        if not isinstance(body.get("ops"), list):
            raise ValueError("a save needs ops: [...]")
        save = dict(body) | {"save_id": save_id, "place_id": place_id, "at": now(), "rev": have + 1,
                             "final": False}
        save.setdefault("name", save_id)
        atomic_write(p, (json.dumps(save, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        return save
