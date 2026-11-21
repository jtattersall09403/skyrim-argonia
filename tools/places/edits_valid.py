"""The whole check of a change that touches only a place's edits/ folder (the owner's saves and notes).

    python -m tools.places.edits_valid [paths...]      # each given file; --all: every edits file in newworld/places

A save (`edits/<save_id>.json`) parses and passes the studio's schema check (tools/places/edits.py check_save: save_id,
place_id, ops, notes); a notes file (`edits/notes.jsonl`) is one JSON object a line with an id and its text. Nothing
else reads these files into a build or a check (the draft's and the build's identity leave edits/ out), so this is
all a save's commit needs (tooling/gate_map.toml, the `only` rule).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.places import edits

REPO = Path(__file__).resolve().parents[2]


def check_file(p: Path) -> str | None:
    """None when the file is a valid edits file, else what is wrong with it."""
    if not p.exists():
        return None   # a deleted save
    try:
        if p.suffix == ".jsonl":
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not (isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("text"), str)):
                    return f"line {i}: a note is an object with an id and its text"
        elif p.suffix == ".json":
            save = json.loads(p.read_text(encoding="utf-8"))
            edits.check_save(save)
            if p.stem != save["save_id"]:
                return f"save_id {save['save_id']!r} is not the file's name"
            if "@" not in p.parent.parent.name and save["place_id"] != p.parent.parent.name:
                return f"the save is for place {save['place_id']!r}, not {p.parent.parent.name!r}"
        else:
            return "not a save (.json) or the notes (.jsonl)"
    except (ValueError, edits.EditError) as e:
        return str(e)
    return None


def main(argv: list[str]) -> int:
    paths = [REPO / p for p in argv if p != "--all"]
    if "--all" in argv:
        from tools.places import variant   # every place of the game and each one's variant drafts
        root = REPO / "newworld" / "places"
        for pid in variant.game_places():
            for d in [pid, *variant.variants_of(pid)]:
                paths += sorted((root / d / "edits").glob("*"))
    bad = [(p, why) for p in paths if (why := check_file(p))]
    for p, why in bad:
        print(f"{p.relative_to(REPO)}: {why}", file=sys.stderr)
    print(f"edits files: {len(paths)} checked, {len(bad)} bad")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
