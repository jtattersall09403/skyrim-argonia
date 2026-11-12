"""python -m tools.places source <place_id> [--rank N] [--force]

Writes the bundle of a place's source place: rank 0 its allocated source, 1-3 its alternates (the database's
place_source, from newworld/sources/source_match/place_source.jsonl). The bundle is `src.<source_id>` under
out/places/bundles/: every ref of its cells and the interiors behind its doors in 3D, the bases and actors they
use, its navmesh, and its local terrain (heights and land textures of its cells); a current bundle is not rewritten.
"""
from __future__ import annotations

import argparse
import json

from tools.places import extract
from tools.places.bundle import REPO

MATCH = REPO / "newworld" / "sources" / "source_match" / "place_source.jsonl"


def source_of(place_id: str, rank: int = 0) -> str:
    for line in MATCH.read_text().splitlines():
        r = json.loads(line)
        if r["place_id"] == place_id and r["rank"] == rank:
            return r["source_place_id"]
    raise KeyError(f"no rank {rank} source for {place_id!r} in {MATCH.relative_to(REPO)}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places source")
    ap.add_argument("place_id", nargs="+")
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    rows = extract.load_sources()
    for pid in a.place_id:
        sid = source_of(pid, a.rank)
        print(f"{pid}: source {sid}")
        extract.run(extract.source_job(rows[sid]), a.force)
    return 0
