"""The owner's notes on changes (docs/design/place-studio.md, Edits: notes on changes), as an agent reads them: each
note with exactly the changes it covers, each change said as what was changed, from what to what, and where.

A save lists each note once, `notes: [{id, text, at}]`, and every op the note covers carries its id in
`note_group`. An older save's per-op `note` reads as a note on that op and on the ops beside it with the same
words. Finalise hands these to the lessons step (`notes.json` in the run folder); `python -m tools.places notes`
shows them for the saves not yet finalised.

    python -m tools.places change-notes <save.json> [--place <place_id>]   one save's notes, as the agent reads them
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLES = ROOT / "out" / "places" / "bundles"


def groups(save: dict) -> list[dict]:
    """The save's notes in the order of their first op: [{id, text, at, call, ops: [op...], changes: [[op...]...]}].
    A change is one op, or the ops of one stroke (a brush stroke, things moved together)."""
    by_id = {n["id"]: n for n in save.get("notes") or [] if isinstance(n, dict) and n.get("id")}
    out: dict[str, dict] = {}
    legacy = None
    for op in save.get("ops") or []:
        gid = op.get("note_group")
        if gid and gid in by_id:
            note, legacy = by_id[gid], None
        elif op.get("note"):
            if not (legacy and legacy["text"] == op["note"]):
                legacy = {"id": f"old{op['n']}", "text": op["note"], "at": op.get("at")}
            note, gid = legacy, legacy["id"]
        else:
            legacy = None
            continue
        g = out.setdefault(gid, {"id": gid, "text": note.get("text", ""), "at": note.get("at"), "ops": []})
        g["ops"].append(op)
    for g in out.values():
        g["changes"] = _changes(g["ops"])
        calls = {op.get("call", "fault") for op in g["ops"]}
        g["call"] = "taste" if calls == {"taste"} else "fault" if calls == {"fault"} else "mixed"
    return list(out.values())


def note_of(save: dict) -> dict[int, str]:
    """Each noted op's number -> its note's words."""
    return {op["n"]: g["text"] for g in groups(save) for op in g["ops"]}


def _changes(ops: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    for op in ops:
        if out and op.get("stroke") and out[-1][0].get("stroke") == op["stroke"]:
            out[-1].append(op)
        else:
            out.append([op])
    return out


# ---------- saying a change ----------

def base_names(place_id: str | None, bundles: Path = BUNDLES) -> dict[str, str]:
    """Base key -> its name (or editor id) from the place's draft and ground bundles, when they are on disk."""
    out: dict[str, str] = {}
    if not place_id:
        return out
    for b in (f"ground.{place_id}", f"draft.{place_id}"):
        p = bundles / b / "bases.jsonl"
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("key"):
                out[r["key"]] = r.get("name") or r.get("edid") or r["key"]
    return out


def ref_index(files: dict | None) -> dict[str, dict]:
    """Ref id -> its row, across the place files' spaces."""
    out: dict[str, dict] = {}
    for sp in ((files or {}).get("spaces") or {}).values():
        for r in (sp.get("refs") if isinstance(sp, dict) else sp) or []:
            out[r["id"]] = r
    return out


def _xyz(p) -> str:
    return "(" + ", ".join(f"{float(v):.0f}" for v in p[:3]) + ")" if isinstance(p, list) and len(p) >= 2 else "?"


def _way(a, b) -> str:
    """A move in metres and compass words (north is +y; 70 game units are about a metre)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    dz = (b[2] - a[2]) if len(a) > 2 and len(b) > 2 else 0
    d = math.hypot(dx, dy)
    parts = []
    if d >= 1:
        ang = math.degrees(math.atan2(dx, dy)) % 360
        word = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][int((ang + 22.5) // 45) % 8]
        parts.append(f"{d / 70:.1f} m {word}")
    if abs(dz) >= 1:
        parts.append(f"{abs(dz) / 70:.1f} m {'up' if dz > 0 else 'down'}")
    return ", ".join(parts) or "in place"


def _deg(r) -> str:
    return f"{math.degrees((r or [0, 0, 0])[2]) % 360:.0f} degrees" if isinstance(r, list) and len(r) == 3 else "?"


def say(op: dict, names: dict[str, str] | None = None, refs: dict[str, dict] | None = None) -> dict:
    """One op as {n, op, space, what, from, to, where}: plain words an agent can act on."""
    names, refs = names or {}, refs or {}
    kind, space = op["op"], op.get("space", "exterior")

    def thing(rid=None, base=None):
        base = base or (refs.get(rid) or {}).get("base")
        nm = names.get(base, base) if base else None
        return f"{nm or 'a thing'} (ref {rid}{f', base {base}' if base and nm != base else ''})" if rid else (nm or "a thing")

    out = {"n": op["n"], "op": kind, "space": space, "call": op.get("call", "fault")}
    if kind == "ref.add":
        r = op["ref"]
        out |= {"what": f"added {thing(r['id'], r.get('base'))}", "from": None, "to": {k: r.get(k) for k in ("pos", "rot", "scale")},
                "where": _xyz(r.get("pos"))}
        if op.get("space_copy_of"):
            out["what"] += f", the first thing in a new room copied from {op['space_copy_of']}"
    elif kind == "ref.remove":
        b = op.get("before") or {}
        out |= {"what": f"removed {thing(op['id'], b.get('base'))}", "from": {k: b.get(k) for k in ("pos", "rot", "scale")},
                "to": None, "where": _xyz(b.get("pos"))}
    elif kind == "ref.move":
        b, a = op["before"], op["after"]
        bits = []
        if "pos" in a:
            bits.append(f"moved {_way(b['pos'], a['pos'])}")
        if "rot" in a:
            bits.append(f"turned from {_deg(b['rot'])} to {_deg(a['rot'])}")
        if "scale" in a:
            bits.append(f"scaled from {b['scale']} to {a['scale']}")
        if "seat" in a:
            bits.append(f"seated {((a.get('seat') or {}).get('mode'))} instead of {((b.get('seat') or {}).get('mode'))}")
        out |= {"what": f"{thing(op['id'], op.get('base'))}: " + "; ".join(bits), "from": b, "to": a,
                "where": _xyz(a.get("pos") or (refs.get(op["id"]) or {}).get("pos"))}
    elif kind in ("veg.clear", "veg.restore"):
        items = op["items"]
        kinds = sorted({names.get(i["base"], i["base"]) for i in items})
        mid = [sum(i["pos"][k] for i in items) / len(items) for k in range(3)] if items else None
        out |= {"what": f"{'cleared' if kind == 'veg.clear' else 'brought back'} {len(items)} plant{'s' * (len(items) != 1)} "
                        f"({', '.join(kinds[:5])}{'...' if len(kinds) > 5 else ''})",
                "from": None, "to": None, "where": f"around {_xyz(mid)}"}
    elif kind == "land.patch":
        v = op["verts"]
        ch = [x[3] - x[2] for x in v]
        tool = (op.get("tool") or {}).get("kind", "changed")
        out |= {"what": f"land {tool}: {len(v)} points, by {min(ch) / 70:+.1f} to {max(ch) / 70:+.1f} m" if v else f"land {tool}",
                "from": None, "to": None, "where": f"cell {op['cell'][0]}, {op['cell'][1]} (4096 units a side)"}
    elif kind.startswith("path."):
        p, b = op["path"], op.get("before")
        verb = {"add": "drew", "edit": "changed", "remove": "erased"}[kind.split(".")[1]]
        pts = p.get("points") or []
        out |= {"what": f"{verb} a {p.get('style') or ''} {p.get('kind') or 'path'} {p['id']}, {p.get('width', '?')} units wide, "
                        f"{len(pts)} points".replace("  ", " "),
                "from": b, "to": p if kind != "path.remove" else None,
                "where": f"from {_xyz(pts[0])} to {_xyz(pts[-1])}" if pts else "?"}
    elif kind.startswith("person."):
        p, b = op["person"], op.get("before")
        verb = {"add": "added", "edit": "changed", "remove": "removed"}[kind.split(".")[1]]
        out |= {"what": f"{verb} person {p.get('name') or p['id']} (id {p['id']})", "from": b, "to": p if kind != "person.remove" else None,
                "where": _xyz(p.get("pos") or (p.get("stops") or [{}])[0].get("pos"))}
    else:   # who a person is, what a thing holds
        field = next((k for k in ("person", "container", "loose", "possessions", "trader", "delivery") if k in op), None)
        row, before = op.get(field), op.get("before")
        named = row or before or {}
        who = named.get("id") or named.get("person") or named.get("ref") or (f"give {named['give_seq']}" if "give_seq" in named else "?")
        diff = sorted(k for k in set(row or {}) | set(before or {}) if (row or {}).get(k) != (before or {}).get(k))
        out |= {"what": f"{kind} on {who}" + (f": {', '.join(diff)} changed" if diff and row and before else ""),
                "from": before, "to": row, "where": named.get("space") or space}
    return out


def present(save: dict, place_id: str | None = None, files: dict | None = None, bundles: Path = BUNDLES) -> list[dict]:
    """Each note with its changes said: [{note, text, call, at, changes: [{change, ops: [said...]}]}]."""
    names, refs = base_names(place_id or save.get("place_id"), bundles), ref_index(files)
    out = []
    for g in groups(save):
        out.append({"note": g["id"], "text": g["text"], "call": g["call"], "at": g.get("at"),
                    "changes": [{"change": i + 1, "ops": [say(op, names, refs) for op in ch]} for i, ch in enumerate(g["changes"])]})
    return out


def show(said: list[dict], head: str = "") -> str:
    """The notes as text, one block per note, each change under it."""
    lines = []
    for s in said:
        n = len(s["changes"])
        lines.append(f"{head}note {s['note']} ({s['call']}, about {n} change{'s' * (n != 1)}): \"{s['text']}\"")
        for c in s["changes"]:
            for o in c["ops"]:
                lines.append(f"  - {o['what']}; in {o['space']}, at {o['where']} (op {o['n']}, {o['op']})")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places change-notes")
    ap.add_argument("save")
    ap.add_argument("--place")
    a = ap.parse_args(argv)
    save = json.loads(Path(a.save).read_text(encoding="utf-8"))
    print(show(present(save, a.place)) or "no notes on changes in this save")
    return 0
