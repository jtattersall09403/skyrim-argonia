"""A place as stocking reads it: the draft bundle (the place files resolved: every ref of the exterior and of each
copied room, the people), the source bundle's plugins, and their item records.

    p = Place.load("helstrom", out=Path("out/places"))
    p.refs        -> [(space_id, ref)]       p.people -> [person row]
    p.rec         -> records.Records         p.place_dir -> newworld/places/<id>
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from tools.places import identities
from tools.places.bundle import read_jsonl
from tools.places.stock.records import Records

REPO = Path(__file__).resolve().parents[3]
OUT = Path(os.environ.get("ARGONIA_PLACES_OUT") or REPO / "out" / "places")


@dataclass
class Place:
    place_id: str
    out: Path
    place_dir: Path
    meta: dict
    refs: list[tuple[str, dict]] = field(default_factory=list)
    people: list[dict] = field(default_factory=list)
    identities: dict[str, dict] = field(default_factory=dict)
    rec: Records | None = None

    @classmethod
    def load(cls, place_id: str, out: Path | None = None, records: bool = True) -> "Place":
        out = Path(out or OUT)
        bdir = out / "bundles" / f"draft.{place_id}"
        if not (bdir / "bundle.json").exists():
            raise SystemExit(f"no draft bundle at {bdir}: run `python -m tools.places draft_bundle {place_id}`")
        meta = json.loads((bdir / "bundle.json").read_text())
        pdir = REPO / "newworld" / "places" / place_id
        p = cls(place_id, out, pdir, meta)
        for sp in sorted((bdir / "spaces").iterdir()):
            for r in read_jsonl(sp / "refs.jsonl"):
                if not r.get("removed"):
                    p.refs.append((sp.name, r))
        p.people = read_jsonl(pdir / "people.jsonl") or read_jsonl(bdir / "people.jsonl")
        p.identities = identities.read(place_id)
        if records:
            p.rec = Records.load(p.plugins())
        return p

    def plugins(self) -> list[str]:
        """Load order: the source bundle's plugins (masters first), then the draft's own others; our world file
        holds no items and is left out."""
        order: list[str] = []
        for src in self.meta.get("stamp", {}).get("inputs", {}):
            sb = self.out / "bundles" / src / "bundle.json"
            if sb.exists():
                for pl in json.loads(sb.read_text()).get("plugins", []):
                    if pl not in order:
                        order.append(pl)
        for pl in self.meta.get("plugins", []):
            if pl not in order:
                order.append(pl)
        return [pl for pl in order if pl != "ArgoniaNewWorld.esm"]
