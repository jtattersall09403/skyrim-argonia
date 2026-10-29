#!/usr/bin/env python3
"""Written dialogue lines in and out of the world database (decision 0030 §5; 2.5 §b's importer, first rung in 1.3).

`dialogue-write` writes one YAML file per person; `import` replaces that person's written lines with the file's,
through db.py (every key, lookup and condition term enforced; nothing written while one fails); `export` rebuilds
the file from the rows. Written lines are `dialogue_line` rows whose id starts `line.`; the imported reference lines
(0024 §7: greeting.*, override.*, bark.*, pool lines) are never touched.

    speaker: npc.imperial-fringe.claywater-station.well-keeper
    place: place.imperial-fringe.claywater-station
    lines:
    - id: line.claywater-station.well-keeper.greeting
      type: greeting                    # line_type: greeting, dialogue, goodbye, bark
      topic: topic.x                    # the topic a dialogue line answers (none for a greeting or goodbye)
      available: {questStage: [quest.local.lf83, '>=', 20]}   # optional; the condition vocabulary only
      low: ...                          # disposition < 30 (optional; else `words` serves every band)
      words: ...                        # 30-69, and the fallback for a missing band
      high: ...                         # >= 70 (optional)
      facts: [fact.x]                   # every fact the line states
      links: [topic.y]                  # hyperlinked keywords the line grants
      onDelivered: [{setFlag: [flag.x, true]}]   # optional; the action vocabulary only

    python3 -m tools.argonia_world.lines import LINES.yaml [--dry-run]
    python3 -m tools.argonia_world.lines export <npc id> [-o LINES.yaml]
    python3 -m tools.argonia_world.lines text LINES.yaml    # every band of every line, one per row (for lint.py)
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import yaml

from tools.argonia_world import db, records
from tools.argonia_world.quest_record import Rows

PREFIX = "line."
KEYS = {"id", "type", "topic", "available", "low", "words", "high", "facts", "links", "onDelivered", "slot"}


def _check(doc: dict, w: db.World) -> list[str]:
    errs = []
    if not isinstance(doc, dict) or set(doc) - {"speaker", "place", "lines"}:
        return ["the file holds speaker, place and lines only"]
    if w.get("npc", doc.get("speaker")) is None:
        errs.append(f"speaker {doc.get('speaker')!r}: no npc row")
    preds, verbs = records.vocabulary(w)
    terms = preds | {"all", "any", "not"}
    seen = set()
    for i, ln in enumerate(doc.get("lines") or []):
        where = f"lines[{i}] {ln.get('id', '?') if isinstance(ln, dict) else ''}"
        if not isinstance(ln, dict):
            errs.append(f"{where}: not a line")
            continue
        if set(ln) - KEYS:
            errs.append(f"{where}: unknown key(s) {sorted(set(ln) - KEYS)}")
        lid = ln.get("id", "")
        if not str(lid).startswith(PREFIX):
            errs.append(f"{where}: a written line's id starts {PREFIX!r}")
        if lid in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(lid)
        if not ln.get("words"):
            errs.append(f"{where}: no words")
        if ln.get("type") == "dialogue" and not ln.get("topic"):
            errs.append(f"{where}: a dialogue line answers a topic")
        for term in _terms(ln.get("available")):
            if term not in terms:
                errs.append(f"{where}: {term!r} is not a condition term")
        for a in ln.get("onDelivered") or []:
            if not isinstance(a, dict) or len(a) != 1 or next(iter(a)) not in verbs:
                errs.append(f"{where}: {a!r} is not one action of the vocabulary")
    return errs


def _terms(c):
    if c is None:
        return
    if isinstance(c, list):
        for k in c:
            yield from _terms(k)
        return
    for k, v in c.items():
        yield k
        if k in ("all", "any"):
            yield from _terms(v)
        elif k == "not":
            yield from _terms(v)


def _owned(w: db.World, speaker: str) -> list[sqlite3.Row]:
    return w.query("SELECT id, available, on_delivered FROM dialogue_line WHERE speaker = ? AND id LIKE ?",
                   speaker, PREFIX + "%")


def import_lines(w: db.World, doc: dict) -> list[str]:
    """Replace the speaker's written lines with the file's. Returns the errors (nothing changed when any)."""
    errs = _check(doc, w)
    if errs:
        return errs
    out = Rows()
    rows, facts, links = [], [], []
    for ln in doc["lines"]:
        lid = ln["id"]
        row = {"id": lid, "type": ln.get("type", "dialogue"), "speaker": doc["speaker"], "words": ln["words"],
               "variants_low": ln.get("low"), "variants_high": ln.get("high"), "place_id": doc.get("place"),
               "keys_topic": ln.get("topic"), "slot": ln.get("slot")}
        if ln.get("available"):
            row["available"] = f"dialogue_line:{lid}:available"
            out.cond(ln["available"], row["available"])
        if ln.get("onDelivered"):
            row["on_delivered"] = f"dialogue_line:{lid}:on_delivered"
            out.actlist(ln["onDelivered"], row["on_delivered"])
        rows.append(row)
        facts += [{"dialogue_line_id": lid, "ord": i, "value": f} for i, f in enumerate(ln.get("facts") or [])]
        links += [{"dialogue_line_id": lid, "ord": i, "value": t} for i, t in enumerate(ln.get("links") or [])]
    if out.errors:
        return out.errors
    w._begin()
    w.con.execute("SAVEPOINT import_lines")
    try:
        for old in _owned(w, doc["speaker"]):
            w.delete("dialogue_line", old["id"])
            if old["available"]:
                w.delete("condition", old["available"])
            if old["on_delivered"]:
                w.delete("action_list", old["on_delivered"])
        w.insert_many("condition", sorted(out.conds, key=lambda r: r["id"].count(".")))
        w.insert_many("condition_arg", out.cargs)
        w.insert_many("action_list", out.lists)
        w.insert_many("action", out.acts)
        w.insert_many("action_arg", out.aargs)
        w.insert_many("dialogue_line", rows)
        w.insert_many("dialogue_line_fact", facts)
        w.insert_many("dialogue_line_link", links)
        bad = w.con.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise sqlite3.IntegrityError(f"dangling key(s): {sorted({tuple(b)[:3] for b in bad})[:5]}")
    except (ValueError, KeyError, sqlite3.IntegrityError) as e:
        w.con.execute("ROLLBACK TO import_lines")
        w.con.execute("RELEASE import_lines")
        return [f"{doc['speaker']}: {e.args[0] if e.args else e}"]
    w.con.execute("RELEASE import_lines")
    return []


def export(w: db.World, speaker: str) -> dict:
    lines, place = [], None
    for r in w.query("SELECT * FROM dialogue_line WHERE speaker = ? AND id LIKE ? ORDER BY id", speaker, PREFIX + "%"):
        place = place or r["place_id"]
        ln = {"id": r["id"], "type": r["type"]}
        if r["keys_topic"]:
            ln["topic"] = r["keys_topic"]
        if r["slot"]:
            ln["slot"] = r["slot"]
        if r["available"]:
            ln["available"] = records.condition(w, r["available"], collapse=True)
        for k, c in (("low", "variants_low"), ("words", "words"), ("high", "variants_high")):
            if r[c]:
                ln[k] = r[c]
        for k, t in (("facts", "dialogue_line_fact"), ("links", "dialogue_line_link")):
            v = w.values(f"SELECT value FROM {t} WHERE dialogue_line_id = ? ORDER BY ord", r["id"])
            if v:
                ln[k] = v
        if r["on_delivered"]:
            ln["onDelivered"] = records.actions(w, r["on_delivered"], collapse=True)
        lines.append(ln)
    return {"speaker": speaker, "place": place, "lines": lines}


def texts(doc: dict):
    """(line id, band, text) for every band of every line."""
    for ln in doc.get("lines") or []:
        for band in ("low", "words", "high"):
            if ln.get(band):
                yield ln["id"], band, " ".join(str(ln[band]).split())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("import")
    a.add_argument("file", type=Path)
    a.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("export")
    b.add_argument("speaker")
    b.add_argument("-o", type=Path)
    c = sub.add_parser("text")
    c.add_argument("file", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "text":
        for _, _, t in texts(yaml.safe_load(args.file.read_text(encoding="utf-8"))):
            print(t)
        return 0
    w = db.open()
    if args.cmd == "export":
        text = yaml.safe_dump(export(w, args.speaker), sort_keys=False, allow_unicode=True, width=120)
        if args.o:
            args.o.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    doc = yaml.safe_load(args.file.read_text(encoding="utf-8"))
    errs = import_lines(w, doc)
    if not errs:
        errs = w.errors()
    if errs:
        print(f"{args.file}: not imported, {len(errs)} error(s):", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    n = len(doc["lines"])
    if args.dry_run:
        print(f"{doc['speaker']}: {n} lines import cleanly (dry run, nothing written)")
        return 0
    w.save()
    print(f"{doc['speaker']}: imported {n} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
