"""Whether the published Atlas (the new world's map page) is current with the place records and the fast travel network it shows.

    python3 -m tools.newworld.atlas_state check            # exit 1 when the Atlas is behind
    python3 -m tools.newworld.atlas_state mark-published   # after publishing out/newworld/map/index.html

Runs on system python3 (no numpy). The tables are the ones tools/newworld/map_page.py reads for places and regions.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = Path("newworld/story/data/db")
TABLES = (
    "place", "place_alias", "place_danger", "place_encounter", "place_give", "place_kind", "place_law",
    "place_note", "place_note_source", "place_source", "place_terrain_need", "source_place", "region",
    "region_note", "region_note_source", "culture", "symbol", "cell", "road", "road_vertex", "border_vertex",
    "travel_mode", "travel_operator", "travel_stop", "travel_route",
)
TEMPLATE = Path("tools/newworld/map_page.html")
NETWORK = Path("newworld/sources/travel/network.json")  # the fast travel layer's source (tools/newworld/travel.py)
RECORD = Path(__file__).with_name("atlas.json")


def sources_hash(root: Path = ROOT) -> str:
    h = hashlib.sha256()
    for rel in [*(DB / f"{t}.jsonl" for t in TABLES), TEMPLATE, NETWORK]:
        p = root / rel
        h.update(str(rel).encode() + b"\0" + (p.read_bytes() if p.exists() else b"") + b"\0")
    return h.hexdigest()[:16]


def record(path: Path = RECORD) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def check(root: Path = ROOT, path: Path = RECORD) -> str | None:
    rec, now = record(path), sources_hash(root)
    if rec.get("published_hash") == now:
        return None
    return (f"Atlas behind: the place records are at {now}, the published page at {rec.get('published_hash')}. "
            f"Rebuild and republish it ({rec.get('url', 'no url recorded')}): "
            "~/.argonia/venv/bin/python -m tools.newworld.map_page; publish out/newworld/map/index.html to that url; "
            "python3 -m tools.newworld.atlas_state mark-published")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "check"
    if cmd == "check":
        msg = check()
        print(msg or "Atlas current")
        return 1 if msg else 0
    if cmd == "mark-published":
        rec = record()
        rec["published_hash"] = sources_hash()
        rec["published"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        RECORD.write_text(json.dumps(rec, indent=2) + "\n")
        print(f"recorded {rec['published_hash']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
