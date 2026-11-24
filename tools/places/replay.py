"""What the owner sees when he opens his open session in the studio again: his save replayed over the committed place
files the way the studio does it on load (edits.apply with the answers' rebase, the studio's edits.js mirror).

    python -m tools.places replay <place_id> [<save_id>|autosave] [--json]

Per op of his: applied as his, kept as no change (an agent's answer to its note already made the row; named with
the note), or a conflict (the studio would stop loading there: a fault to fix before he opens it). Then every row
his ops touched: where he left it, or changed by an answer (which note), or changed by something else (a fault).
Exit 0 when nothing conflicts and nothing he left moved without an answer.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict

from tools.places import edits


def _rows(files: dict) -> dict:
    out = {}
    for sid, sp in (files.get("spaces") or {}).items():
        for r in sp.get("refs") or []:
            out[("ref", r["id"])] = r
    for table, key in edits.TABLES.items():
        for r in files.get(key) or []:
            if isinstance(r, dict) and r.get("id"):
                out[(table, r["id"])] = r
    return out


def _his_after(save: dict, files: dict | None = None) -> dict:
    """The row each of his ops leaves, the last op on a row winning (a unit's members as their own moves, and only
    what the unit rule says the move carries: edits.unit_carried)."""
    out = {}
    ops = []
    for op in save.get("ops") or []:
        if op.get("op") == "unit.move" and files is not None:
            op = dict(op, **{k: edits.unit_carried(files, op, k) for k in ("people", "quests", "walks", "paths")})
        ops.append(op)
    for op in edits.expand(ops):
        rid = edits._row_id(op)
        if op["op"] == "ref.remove":
            out[("ref", rid)] = None
        elif op["op"] in ("ref.move",):
            out[("ref", rid)] = ("fields", op["after"])
        elif op["op"] == "ref.add":
            out[("ref", rid)] = ("row", op["ref"])
        elif "." in op["op"] and op["op"].split(".")[0] in edits.TABLES:
            t = op["op"].split(".")[0]
            out[(t, rid)] = None if op["op"].endswith(".remove") else ("row", op[t])
    return out


def _fits(row, want) -> bool:
    if want is None:
        return row is None or bool(row.get("removed"))
    kind, val = want
    if row is None:
        return False
    if kind == "fields":   # a seated height read back to a thousandth by the seat is where he left it
        return all(_near(row.get(k), v) if k == "pos" else edits.same(row.get(k), v) for k, v in val.items())
    return edits.same(row, val)


def _near(a, b, tol: float = 0.05) -> bool:
    return isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def replay(files: dict, save: dict, source=None, base: dict | None = None) -> dict:
    """{applied, no_change: {note: n}, conflicts: [...], rows: {where_left, answered: {note: [ids]}, moved: [ids]}}.
    `base`, when given, is the place files his session was made on: a row he left that the draft now holds
    differently is then judged against what his session made of it over that base."""
    answered = edits._answered(files)
    cur = edits.canonical(files)
    cur["_source"] = edits._cached(source) if source else None
    applied, kept, conflicts = 0, defaultdict(int), []
    for op in save.get("ops") or []:
        note = edits._note_of(op)
        reb = edits._rebased(cur, op, answered) if answered else op
        before = copy.deepcopy({k: v for k, v in cur.items() if k != "_source"})
        try:
            edits._apply_one(cur, reb)
        except edits.EditConflict as e:
            if edits._answered_note(op, answered):
                kept[note] += 1
                continue
            conflicts.append({"n": op.get("n"), "op": op["op"], "row": edits._row_id(op), "note": note, "why": str(e)})
            continue
        if not edits.same(reb, op) and _same_files(before, cur):
            kept[note] += 1
        else:
            applied += 1
    cur.pop("_source", None)
    now = _rows(cur)
    who = defaultdict(set)
    for a in (files.get("place") or {}).get("agent_answers") or []:
        for rid in a.get("rows") or []:
            who[rid].add(a.get("answers"))
    where_left, by_answer, moved = 0, defaultdict(list), []
    for key, want in _his_after(save, cur).items():
        if _fits(now.get(key), want):
            where_left += 1
        elif who.get(key[1]):
            for n in sorted(who[key[1]], key=str):
                by_answer[n].append(key[1])
        else:
            moved.append(key[1])
    return {"ops": len(save.get("ops") or []), "applied": applied, "no_change": dict(kept), "conflicts": conflicts,
            "rows": {"where_he_left": where_left, "changed_by_answer": {k: sorted(set(v)) for k, v in by_answer.items()},
                     "moved_without_answer": moved}, "files": cur}


def _same_files(a: dict, b: dict) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps({k: v for k, v in b.items() if k != "_source"},
                                                                    sort_keys=True, default=str)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("place_id")
    ap.add_argument("save_id", nargs="?", default="autosave")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    from tools.places.look.scene import data_out
    from tools.places.seat import PLACES
    pdir = PLACES / a.place_id
    p = (data_out() / "autosave" / f"{a.place_id}.json") if a.save_id == "autosave" else pdir / "edits" / f"{a.save_id}.json"
    save = json.loads(p.read_text(encoding="utf-8"))
    got = replay(edits.load_place(pdir), save, edits.bundle_source(data_out() / "bundles"))
    got.pop("files")
    if a.json:
        print(json.dumps(got, indent=1))
    else:
        r = got["rows"]
        print(f"{a.place_id}, {a.save_id}: {got['ops']} ops of his; {got['applied']} applied as his, "
              f"{sum(got['no_change'].values())} kept as no change because an answer made the row "
              f"({', '.join(f'{k}: {v}' for k, v in sorted(got['no_change'].items(), key=str))}), "
              f"{len(got['conflicts'])} conflicts")
        for c in got["conflicts"]:
            print(f"  CONFLICT op {c['n']} ({c['op']}, note {c['note']}) on {c['row']}: {c['why']}")
        print(f"rows he touched: {r['where_he_left']} where he left them; changed by an answer: "
              + "; ".join(f"{k}: {len(v)}" for k, v in sorted(r["changed_by_answer"].items(), key=str)))
        for rid in r["moved_without_answer"]:
            print(f"  MOVED WITHOUT AN ANSWER: {rid}")
    return 0 if not got["conflicts"] and not got["rows"]["moved_without_answer"] else 1
