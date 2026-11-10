"""The owner's notes on a place, left in the studio for an agent to pick up: about the place as a whole or about
the things selected when the note was written. One JSON line per note in newworld/places/<place_id>/edits/notes.jsonl
(the edits folder is outside the draft's and the build's identity, so a note never changes either).

    python -m tools.places notes                     every open note, every place
    python -m tools.places notes helstrom --all      one place, answered notes too
    python -m tools.places notes done helstrom <note id> --reply "what was done"

A note: {id, at, text, things: [{id, space, base, name, kind, pos, src}], view: {space, at: [x, y, z]}, save,
done, done_at, reply}. An agent answers a note by changing what it asks for and closing it with `done`; the reply
shows beside the note in the studio."""
import argparse
import fcntl
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
PLACE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
NOTE_ID = re.compile(r"n(\d+)")
MAX_TEXT, MAX_THINGS = 4000, 200


def path(place_id: str, places: Path = PLACES) -> Path:
    if not PLACE_ID.match(place_id):
        raise ValueError("bad place id")
    return places / place_id / "edits" / "notes.jsonl"


def read(place_id: str, places: Path = PLACES) -> list[dict]:
    p = path(place_id, places)
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []


@contextmanager
def _locked(place_id: str, places: Path):
    """One change to a place's notes at a time, across processes (the studio server adds and closes notes while an
    agent's `notes done` answers them): a lock on the edits folder itself, held from the read to the write."""
    d = path(place_id, places).parent
    d.mkdir(parents=True, exist_ok=True)
    fd = os.open(d, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _write(place_id: str, rows: list[dict], places: Path) -> None:
    p = path(place_id, places)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(p)


def _xyz(v) -> list[float] | None:
    """Three finite numbers rounded to a tenth of a unit, or None."""
    if not (isinstance(v, list) and len(v) == 3 and all(isinstance(c, (int, float)) and not isinstance(c, bool)
                                                         and c == c and abs(c) != float("inf") for c in v)):
        return None
    return [round(float(c), 1) for c in v]


def _thing(t: dict) -> dict:
    out = {k: str(t[k])[:200] for k in ("id", "space", "base", "name", "kind", "src") if t.get(k) is not None}
    if _xyz(t.get("pos")):
        out["pos"] = _xyz(t["pos"])
    return out


def _next_id(rows: list[dict]) -> str:
    found = (NOTE_ID.fullmatch(str(r.get("id"))) for r in rows)
    return f"n{max((int(m.group(1)) for m in found if m), default=0) + 1}"


def add(place_id: str, body: dict, places: Path = PLACES) -> dict:
    text = str(body.get("text") or "").strip()
    if not text:
        raise ValueError("a note needs some words")
    things = body.get("things") if isinstance(body.get("things"), list) else []
    note = {"id": None, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "text": text[:MAX_TEXT],
            "things": [_thing(t) for t in things[:MAX_THINGS] if isinstance(t, dict)], "done": False}
    view = body.get("view")
    if isinstance(view, dict) and _xyz(view.get("at")):
        note["view"] = {"space": str(view.get("space") or "exterior")[:200], "at": _xyz(view["at"])}
    if body.get("save"):
        note["save"] = str(body["save"])[:64]
    with _locked(place_id, places):
        rows = read(place_id, places)
        note["id"] = _next_id(rows)
        _write(place_id, rows + [note], places)
    return note


def done(place_id: str, note_id: str, reply: str = "", places: Path = PLACES, undo: bool = False) -> dict:
    with _locked(place_id, places):
        rows = read(place_id, places)
        for r in rows:
            if r.get("id") == note_id:
                r["done"] = not undo
                if undo:
                    r.pop("done_at", None)
                else:
                    r["done_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    if reply:
                        r["reply"] = reply[:MAX_TEXT]
                _write(place_id, rows, places)
                return r
    raise ValueError(f"no note {note_id} on {place_id}")


def show(place_id: str, n: dict) -> str:
    out = [f"{place_id} {n['id']}  {n['at']}  {'answered' if n.get('done') else 'open'}", f"  {n['text']}"]
    if n.get("view"):
        out.append(f"  written looking at {n['view']['space']} near {n['view']['at']}")
    for t in n.get("things", []):
        out.append(f"  about: {t.get('name') or t.get('base')} ({t.get('kind', 'thing')}) id {t.get('id')} in {t.get('space')}"
                   f" at {t.get('pos')}" + (f", copied from source thing {t['src']}" if t.get("src") else ""))
    if n.get("reply"):
        out.append(f"  reply: {n['reply']}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if argv and argv[0] == "done":
        ap = argparse.ArgumentParser(prog="python -m tools.places notes done")
        ap.add_argument("place_id")
        ap.add_argument("note_id")
        ap.add_argument("--reply", default="")
        a = ap.parse_args(argv[1:])
        print(show(a.place_id, done(a.place_id, a.note_id, a.reply)))
        return 0
    ap = argparse.ArgumentParser(prog="python -m tools.places notes")
    ap.add_argument("place_id", nargs="?")
    ap.add_argument("--all", action="store_true", help="answered notes too")
    a = ap.parse_args(argv)
    ids = [a.place_id] if a.place_id else sorted(d.name for d in PLACES.iterdir() if (d / "edits" / "notes.jsonl").exists())
    shown = 0
    for pid in ids:
        for n in read(pid):
            if a.all or not n.get("done"):
                print(show(pid, n))
                shown += 1
    if not shown:
        print("no open notes" if not a.all else "no notes")
    return 0
