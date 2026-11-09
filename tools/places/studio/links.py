"""The studio's calls into the other parts, each behind one function so the server never reaches past them.

  assets:  tools.places.assets.mesh(model) / tex(path, size) / thumb(model) -> Path | None (None: converting)
  seat:    tools.places.seat.ground_for(place_id).at(x, y)
  ground:  tools.places.ground_check.status() -> {ground_sha, deployed_sha, match}
A part not built yet raises Missing, which the server answers with 503 and the part's name."""
from __future__ import annotations

import importlib
import threading
from pathlib import Path


class Missing(RuntimeError):
    pass


def _module(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name and name.startswith(e.name):
            raise Missing(name) from None
        raise


def asset(kind: str, *args) -> Path | None:
    """kind: mesh, tex or thumb. A path when the converted file is ready; None when conversion has started."""
    fn = getattr(_module("tools.places.assets"), kind, None)
    if fn is None:
        raise Missing(f"tools.places.assets.{kind}")
    p = fn(*args)
    return Path(p) if p else None


_grounds: dict[str, tuple[float, object]] = {}
_glock = threading.Lock()


def seat_at(place_id: str, x: float, y: float, bundles: Path, places: Path) -> dict:
    seat = _module("tools.places.seat")
    bj = bundles / f"ground.{place_id}" / "bundle.json"
    if not bj.exists():
        raise FileNotFoundError(f"no ground bundle for {place_id}")
    land = places / place_id / "land.jsonl"
    key = bj.stat().st_mtime + (land.stat().st_mtime if land.exists() else 0)
    with _glock:
        hit = _grounds.get(place_id)
        if not hit or hit[0] != key:
            hit = (key, seat.ground_for(place_id, bundles, places))
            _grounds[place_id] = hit
    return hit[1].at(x, y)


def ground_status() -> dict:
    return dict(_module("tools.places.ground_check").status())
