"""The owner's notes on a place, written in the studio for an agent: about the place as a whole or about the things
selected when the note was written. One JSON line per note in newworld/places/<place_id>/edits/notes.jsonl (the
edits folder is outside the draft's and the build's identity, so a note never changes either), committed by path as
the saves are.

A note is written (unsent: the owner may edit or delete it, and no agent sees it), then sent with every other
unsent note of the place as one batch when the owner chooses (`send`; tools/places/notes_batch.py starts the agent),
then done with the agent's reply. A row without `sent` was written before notes were sent in batches: it counts as
sent.

    python -m tools.places notes                     every sent, open note, every place
    python -m tools.places notes helstrom --unsent   one place, the notes not sent yet too
    python -m tools.places notes helstrom --changes  the notes on changes in its saves not yet finalised
    python -m tools.places notes helstrom --all      every note: unsent, sent, done, and the notes on changes
    python -m tools.places notes done helstrom <note id> --reply "what was done"

A note: {id, at, text, things: [{id, space, base, name, kind, pos, src}], view: {space, at: [x, y, z]}, save,
sent, sent_at, batch, done, done_at, reply}; a note written on a tablet offline adds `client_id` (adding it again
returns the note already kept) and `written_at`, when it was written. An agent answers a sent note by changing what it asks for and closing it
with `done`; the reply shows beside the note in the studio.

The owner's notes on changes live in the saves with the changes they cover (tools/places/change_notes.py) and are
answered by finalising the save: its lessons step reads them. `--changes` shows them, for each save not yet
finalised (every save with --all), each note with its changes."""
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
AUTOSAVES = ROOT / "out" / "places" / "autosave"
PLACE_ID = re.compile(r"^[a-z0-9][a-z0-9._@-]{0,95}$")   # @: a variant
NOTE_ID = re.compile(r"n(\d+)")
MAX_TEXT, MAX_THINGS = 4000, 200
CLIENT_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
WHEN = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z")


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
    # a world plant (a tree the world placed): where the world put it, and how deep its pivot sits under the ground
    w = t.get("world")
    if isinstance(w, dict) and _xyz(w.get("pos")):
        out["world"] = {"base": str(w.get("base") or "")[:200], "pos": _xyz(w["pos"])}
    for k in ("sink_m", "ground"):
        v = t.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) < 1e7:
            out[k] = round(float(v), 3)
    return out


def rule_sink(base: str) -> dict | None:
    """The placement rule's sink for a tree's base (tools/newworld/place/place.py sink_m: flora_base sink_lo/hi_m or
    sink_m, metres at scale 1), or None when the base is not one of the world's flora."""
    try:
        from tools.newworld.place.place import jsonl
        rows = jsonl("flora_base")
    except (OSError, ValueError, ImportError):
        return None
    plugin, _, fid = str(base).rpartition(":")      # ours "Black Marsh.esm:0D864C"; the db "0D864C:black marsh.esm"
    b = next((r for r in rows if str(r.get("form_key", "")).lower() == f"{fid}:{plugin}".lower()), None)
    if not b:
        return None
    return {k: b.get(k) for k in ("sink_lo_m", "sink_hi_m", "sink_m", "height_m") if b.get(k) is not None}


def tree_notes(rows_by_place: dict[str, list[dict]]) -> str:
    """Notes about world trees, grouped by tree type: the owner's corrected sink against the placement rule's, for the
    placement rules (tools/newworld/place) to take forward."""
    by: dict[str, list] = {}
    for pid, rows in rows_by_place.items():
        for n in rows:
            for t in n.get("things", []):
                if t.get("world"):
                    by.setdefault(t["world"].get("base") or t.get("base"), []).append((pid, n, t))
    out = []
    for base, items in sorted(by.items()):
        r = rule_sink(base)
        rule = (f"rule sink {r.get('sink_lo_m')}-{r.get('sink_hi_m')} m" if r and r.get("sink_lo_m") is not None
                else f"rule sink {r['sink_m']} m" if r and r.get("sink_m") is not None else "no flora rule for this base")
        out.append(f"tree type {items[0][2].get('name') or base} ({base}): {rule}")
        for pid, n, t in items:
            out.append(f"  {pid} {n['id']}: owner's sink {t.get('sink_m', '?')} m at {t.get('pos')}: {n.get('text', '')[:160]}")
    return "\n".join(out)


def _next_id(rows: list[dict]) -> str:
    found = (NOTE_ID.fullmatch(str(r.get("id"))) for r in rows)
    return f"n{max((int(m.group(1)) for m in found if m), default=0) + 1}"


def add(place_id: str, body: dict, places: Path = PLACES) -> dict:
    text = str(body.get("text") or "").strip()
    if not text:
        raise ValueError("a note needs some words")
    things = body.get("things") if isinstance(body.get("things"), list) else []
    note = {"id": None, "at": _now(), "text": text[:MAX_TEXT],
            "things": [_thing(t) for t in things[:MAX_THINGS] if isinstance(t, dict)], "sent": False, "done": False}
    view = body.get("view")
    if isinstance(view, dict) and _xyz(view.get("at")):
        note["view"] = {"space": str(view.get("space") or "exterior")[:200], "at": _xyz(view["at"])}
    if body.get("save"):
        note["save"] = str(body["save"])[:64]
    cid = body.get("client_id")
    if cid is not None:   # written on a tablet offline: sent again after a lost answer, it is the same note
        if not (isinstance(cid, str) and CLIENT_ID.fullmatch(cid)):
            raise ValueError("client_id: letters, digits, dot, dash, underscore, at most 64")
        note["client_id"] = cid
        if isinstance(body.get("written_at"), str) and WHEN.fullmatch(body["written_at"]):
            note["written_at"] = body["written_at"]
    with _locked(place_id, places):
        rows = read(place_id, places)
        same = next((r for r in rows if cid is not None and r.get("client_id") == cid), None)
        if same:
            return same
        note["id"] = _next_id(rows)
        _write(place_id, rows + [note], places)
    return note


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


ANSWER_HOURS = 4.0     # a submitted note is answered (its change landed on main, closed with `done`) within this


def overdue(place_id: str, places: Path = PLACES, now: float | None = None, hours: float = ANSWER_HOURS) -> list[dict]:
    """The place's submitted notes still open longer than `hours` since they were sent: an agent answers a submitted
    note at once, over the owner's open session; nothing it does waits for his Save or his finalise."""
    import calendar
    now = time.time() if now is None else now
    out = []
    for n in read(place_id, places):
        if state(n) != "sent":
            continue
        at = n.get("sent_at") or n.get("at") or ""
        try:
            t = calendar.timegm(time.strptime(at, "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            t = now
        if now - t > hours * 3600:
            out.append(n)
    return out


def state(n: dict) -> str:
    """unsent (the owner's still), sent (waiting for the agent) or done."""
    return "done" if n.get("done") else "sent" if n.get("sent", True) else "unsent"


def _change(place_id: str, note_id: str, places: Path, fn) -> dict:
    """One note changed by fn(row, rows) under the lock; fn returns the rows to write."""
    with _locked(place_id, places):
        rows = read(place_id, places)
        r = next((r for r in rows if r.get("id") == note_id), None)
        if r is None:
            raise ValueError(f"no note {note_id} on {place_id}")
        _write(place_id, fn(r, rows), places)
        return r


def done(place_id: str, note_id: str, reply: str = "", places: Path = PLACES, undo: bool = False,
         asked: str = "") -> dict:
    """Close a sent note with the agent's reply, or reopen it (undo). A note not sent yet is the owner's still, unless
    he asked for his notes to be actioned sent or not: `asked` names where he did (an owner issue, "#96"), kept on the
    note and shown to him with the reply."""
    def close(r, rows):
        if state(r) == "unsent" and not (asked and not undo):
            raise ValueError(f"note {note_id} on {place_id} has not been sent yet; only a sent note is answered "
                             f"(or one the owner asked to be actioned unsent: --asked \"<where he asked>\")")
        if state(r) == "unsent":
            r["sent"], r["sent_at"], r["asked"] = True, _now(), str(asked)[:200]
        r["done"] = not undo
        if undo:
            r.pop("done_at", None)
        else:
            r["done_at"] = _now()
            if reply:
                r["reply"] = reply[:MAX_TEXT]
        return rows
    return _change(place_id, note_id, places, close)


def _unsent_only(r: dict, what: str) -> None:
    if state(r) != "unsent":
        raise ValueError(f"this note has been sent to the agent, so it can no longer be {what}")


def edit(place_id: str, note_id: str, text: str, places: Path = PLACES) -> dict:
    """New words for a note not sent yet."""
    text = str(text or "").strip()
    if not text:
        raise ValueError("a note needs some words")

    def put(r, rows):
        _unsent_only(r, "changed")
        r["text"] = text[:MAX_TEXT]
        return rows
    return _change(place_id, note_id, places, put)


def delete(place_id: str, note_id: str, places: Path = PLACES) -> dict:
    """Take away a note not sent yet."""
    def drop(r, rows):
        _unsent_only(r, "deleted")
        return [x for x in rows if x is not r]
    return _change(place_id, note_id, places, drop) | {"deleted": True}


def send(place_id: str, places: Path = PLACES) -> dict:
    """Every unsent note of the place, sent as one batch: {batch, sent: [notes]}; nothing to send is an error."""
    with _locked(place_id, places):
        rows = read(place_id, places)
        out = [r for r in rows if state(r) == "unsent"]
        if not out:
            raise ValueError("there are no unsent notes to send")
        n = 1 + max((int(m.group(1)) for r in rows if (m := re.fullmatch(r"b(\d+)", str(r.get("batch"))))), default=0)
        at = _now()
        for r in out:
            r.update(sent=True, sent_at=at, batch=f"b{n}")
        _write(place_id, rows, places)
    return {"batch": f"b{n}", "sent": out}


def show(place_id: str, n: dict) -> str:
    said = {"done": "answered", "sent": "sent, open", "unsent": "not sent yet (the owner's draft)"}[state(n)]
    out = [f"{place_id} {n['id']}  {n['at']}  {said}", f"  {n['text']}"]
    if n.get("view"):
        out.append(f"  written looking at {n['view']['space']} near {n['view']['at']}")
    for t in n.get("things", []):
        out.append(f"  about: {t.get('name') or t.get('base')} ({t.get('kind', 'thing')}) id {t.get('id')} in {t.get('space')}"
                   f" at {t.get('pos')}" + (f", copied from source thing {t['src']}" if t.get("src") else "")
                   + (f", the world's tree from {t['world']['pos']}" if t.get("world") else "")
                   + (f", its pivot {t['sink_m']} m under the ground" if t.get("sink_m") is not None else ""))
    if n.get("reply"):
        out.append(f"  reply: {n['reply']}")
    return "\n".join(out)


def change_notes(place_id: str, everything: bool = False, places: Path = PLACES, autosaves: Path = AUTOSAVES) -> str:
    """The notes on changes in the place's saves (the autosave and named saves; finalised ones only with
    `everything`), each with its changes; a note in several saves (a named copy of the autosave) is shown once."""
    from tools.places import change_notes as cn
    files = sorted((places / place_id / "edits").glob("*.json")) + [autosaves / f"{place_id}.json"]
    try:
        from tools.places.edits import load_place
        place_files = load_place(places / place_id)
    except (OSError, ValueError, KeyError):
        place_files = None
    seen, out = set(), []
    for p in files:
        try:
            save = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        except (OSError, ValueError):
            continue
        if not isinstance(save, dict) or not isinstance(save.get("ops"), list) or (save.get("final") and not everything):
            continue
        said = [s for s in cn.present(save, place_id, place_files)
                if (key := (s["text"], tuple(o["n"] for c in s["changes"] for o in c["ops"]))) not in seen and not seen.add(key)]
        if said:
            where = "the unsaved work (autosave)" if p.parent == autosaves else f"save {save.get('save_id', p.stem)}"
            stage = "finalised" if save.get("final") else "not finalised yet"
            out.append(f"{place_id}, notes on changes in {where} ({stage}):\n" + cn.show(said, "  "))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if argv and argv[0] == "done":
        ap = argparse.ArgumentParser(prog="python -m tools.places notes done")
        ap.add_argument("place_id")
        ap.add_argument("note_id")
        ap.add_argument("--reply", default="")
        ap.add_argument("--asked", default="", help="where the owner asked for his notes to be actioned unsent (\"#96\")")
        ap.add_argument("--places", type=Path, default=PLACES, help=argparse.SUPPRESS)   # a test place's folder
        a = ap.parse_args(argv[1:])
        print(show(a.place_id, done(a.place_id, a.note_id, a.reply, a.places, asked=a.asked)))
        return 0
    ap = argparse.ArgumentParser(prog="python -m tools.places notes")
    ap.add_argument("place_id", nargs="?")
    ap.add_argument("--unsent", action="store_true", help="the notes the owner has not sent yet too")
    ap.add_argument("--changes", action="store_true", help="the notes on changes in saves not yet finalised")
    ap.add_argument("--all", action="store_true", help="every note: unsent, sent, answered, and on changes")
    ap.add_argument("--places", type=Path, default=PLACES, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    ids = [a.place_id] if a.place_id else sorted(d.name for d in a.places.iterdir() if (d / "edits").is_dir())
    wanted = {"sent"} | ({"unsent"} if a.unsent or a.all else set()) | ({"done"} if a.all else set())
    shown = 0
    late = 0
    for pid in ids:
        for n in overdue(pid, a.places):
            print(f"OVERDUE {pid} {n['id']}: submitted {n.get('sent_at') or n.get('at')} and not answered within "
                  f"{ANSWER_HOURS:g} hours: land its change now and close it with `notes done`")
            late += 1
        for n in read(pid, a.places):
            if state(n) in wanted:
                print(show(pid, n))
                shown += 1
        text = change_notes(pid, a.all, a.places) if a.changes or a.all else ""
        if text:
            print(text)
            shown += 1
    trees = tree_notes({pid: [n for n in read(pid, a.places) if state(n) in wanted] for pid in ids})
    if trees:
        print("Tree notes by tree type (for the placement rules, tools/newworld/place):\n" + trees)
        shown += 1
    if not shown:
        print("no notes" if a.all else "no open notes")
    return 1 if late else 0
