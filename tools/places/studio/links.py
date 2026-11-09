"""The studio's calls into the other parts, each behind one function so the server never reaches past them.

  assets:  tools.places.assets.mesh(model, level) / tex(path, size) / thumb(model) / land_table()
  seat:    tools.places.seat.ground_for(place_id).at(x, y)
  ground:  tools.places.ground_check.status() -> {ground_sha, deployed_sha, match, ...}
  runs:    tools.places.finalise.start(place_id, save_id) / read_run(run_dir)"""
from __future__ import annotations

import threading
from pathlib import Path

from tools.places import assets, finalise, ground_check, seat


def asset(kind: str, *args) -> Path | None:
    """kind: mesh, tex, thumb or land; the converted file's path (None: the source does not exist)."""
    if kind == "land":
        return assets.land_table()
    p = getattr(assets, kind)(*args)
    return Path(p) if p else None


_grounds: dict[str, tuple[float, object]] = {}
_glock = threading.Lock()


def seat_at(place_id: str, x: float, y: float, bundles: Path, places: Path) -> dict:
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
    return dict(ground_check.status())


def run_start(place_id: str, save_id: str) -> str:
    return finalise.start(place_id, save_id)


def run_read(run_dir: Path) -> dict:
    return finalise.read_run(run_dir)
