"""A place's variant drafts: another draft of the same place held beside it as `newworld/places/<place id>@<variant>/`,
for the owner to see, edit and save in the studio exactly as a place, and to choose instead of the current draft.

A variant's place.json says `variant_of` (the place id), `variant` (its name) and `title` (how the studio's place
picker labels it). Its ground, record card, quests, people sources and needs are its place's: `record_id` resolves a
variant's id to its place, `ground` names the ground bundle it stands on. Everything that walks all places for the
game or the gate (the layer plugin's place build, the consistency check, the held-ground rows, the world rebuild's
place stages, the teleport clearances, the edit reach) walks `game_places`, which never yields a variant: a variant
never reaches the built plugin or a gate count.

python -m tools.places variant list [<place id>]
python -m tools.places variant use <place id> <variant>    the current draft becomes variant `previous`, the chosen
                                                          variant becomes the place (refused while either has unsaved
                                                          studio edits, or while `previous` is taken)
python -m tools.places variant drop <place id> <variant>   delete a variant draft
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SEP = "@"
ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
AUTOSAVES = ROOT / "out" / "places" / "autosave"
PREVIOUS = "previous"


def is_variant(place_id: str) -> bool:
    return SEP in place_id


def record_id(place_id: str) -> str:
    """The place a draft is of: its own id for a place, the place it is a variant of for a variant."""
    return place_id.split(SEP, 1)[0]


def ground(place_id: str) -> str:
    """The ground bundle a draft stands on (a variant stands on its place's ground)."""
    return f"ground.{record_id(place_id)}"


def bundle(bundle_id: str) -> str:
    """The bundle on disk a bundle id asks for: `ground.<variant>` is its place's ground; every other id is itself."""
    return ground(bundle_id[len("ground."):]) if bundle_id.startswith("ground.") else bundle_id


def variant_id(place_id: str, name: str) -> str:
    return f"{place_id}{SEP}{name}"


def game_places(places: Path | None = None) -> list[str]:
    """Every drafted place the game and the gate know: each folder with a place.json, never a variant."""
    root = Path(places or PLACES)
    return sorted(d.name for d in root.iterdir()
                  if (d / "place.json").exists() and not is_variant(d.name)) if root.is_dir() else []


def variants_of(place_id: str, places: Path | None = None) -> list[str]:
    """The variant names held beside a place."""
    root = Path(places or PLACES)
    pre = place_id + SEP
    return sorted(d.name[len(pre):] for d in root.glob(f"{place_id}{SEP}*") if (d / "place.json").exists()) \
        if root.is_dir() else []


def unsaved(place_id: str, places: Path | None = None, autosaves: Path | None = None) -> list[str]:
    """The studio saves of a draft holding edits not yet finalised into its files (the autosave, named saves)."""
    root, auto = Path(places or PLACES), Path(autosaves or AUTOSAVES)
    out = []
    for p in sorted((root / place_id / "edits").glob("*.json")) + [auto / f"{place_id}.json"]:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not s.get("final") and (s.get("ops") or s.get("notes")):
            out.append(str(p))
    return out


def _mark(pdir: Path, place_id: str, name: str | None, title: str | None) -> None:
    pj = pdir / "place.json"
    pl = json.loads(pj.read_text(encoding="utf-8"))
    pl["place_id"] = variant_id(place_id, name) if name else place_id
    for k in ("variant_of", "variant", "title"):
        pl.pop(k, None)
    if name:
        pl = {"place_id": pl.pop("place_id"), "variant_of": place_id, "variant": name, "title": title, **pl}
    pj.write_text(json.dumps(pl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def title_of(place_id: str, places: Path | None = None) -> str:
    root = Path(places or PLACES)
    db = root.parent / "story" / "data" / "db" / "place.jsonl"
    for ln in (db.read_text(encoding="utf-8").splitlines() if db.exists() else ()):
        if ln.strip() and json.loads(ln).get("id") == place_id:
            return json.loads(ln).get("name") or place_id
    return place_id


def use(place_id: str, name: str, places: Path | None = None, autosaves: Path | None = None) -> str:
    """Make variant `name` the place: the current draft becomes variant `previous`. Returns what moved."""
    root = Path(places or PLACES)
    cur, chosen, prev = root / place_id, root / variant_id(place_id, name), root / variant_id(place_id, PREVIOUS)
    if is_variant(place_id):
        raise ValueError(f"{place_id} is a variant; name the place it is a variant of")
    if not (chosen / "place.json").exists():
        raise ValueError(f"{place_id} has no variant {name!r} (variants: {', '.join(variants_of(place_id, root)) or 'none'})")
    if not (cur / "place.json").exists():
        raise ValueError(f"no place {place_id}")
    if name != PREVIOUS and prev.exists():
        raise ValueError(f"{prev.name} is taken: drop it first (variant drop {place_id} {PREVIOUS})")
    held = unsaved(place_id, root, autosaves) + unsaved(chosen.name, root, autosaves)
    if held:
        raise ValueError("unsaved studio edits: finalise or discard them first: " + ", ".join(held))
    parked = root / f".{place_id}.swap"
    cur.rename(parked)
    chosen.rename(cur)
    parked.rename(prev)
    _mark(cur, place_id, None, None)
    _mark(prev, place_id, PREVIOUS, f"{title_of(place_id, root)} (previous draft)")
    return f"{place_id}@{name} is now {place_id}; the draft it replaced is {prev.name}"


def drop(place_id: str, name: str, places: Path | None = None, autosaves: Path | None = None) -> str:
    root = Path(places or PLACES)
    d = root / variant_id(place_id, name)
    if not (d / "place.json").exists():
        raise ValueError(f"{place_id} has no variant {name!r}")
    held = unsaved(d.name, root, autosaves)
    if held:
        raise ValueError("unsaved studio edits: " + ", ".join(held))
    shutil.rmtree(d)
    return f"dropped {d.name}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="variant", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", choices=["list", "use", "drop"])
    ap.add_argument("place_id", nargs="?")
    ap.add_argument("variant", nargs="?")
    ap.add_argument("--places", type=Path, default=PLACES, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.verb == "list":
        for pid in [a.place_id] if a.place_id else game_places(a.places):
            for v in variants_of(pid, a.places):
                print(f"{pid}  {variant_id(pid, v)}")
        return 0
    if not (a.place_id and a.variant):
        ap.error(f"{a.verb} needs <place id> <variant>")
    try:
        print((use if a.verb == "use" else drop)(a.place_id, a.variant, a.places))
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    print("commit the renames by path (both folders)")
    return 0
