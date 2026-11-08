"""Talk read-back (docs/design/talk.md): out/Argonia.esp against the talk tables, after `plugin.sh check` built it.

For every talker with written lines: each of their topics has one INFO gated GetIsReference to their placed ref (and
no other topic is); a talker whose name differs from the placed base's (`known_as`) has their ref overridden to a
base of our own carrying that name, templated on the old base; and the vendors we restock show their chest's stock.

    python3 -m tools.argonia_world.talk_check [--esp out/Argonia.esp] [--settlement-prefix fact.lilmoth.]
"""
from __future__ import annotations

import argparse
import dataclasses
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db, esm

GET_IS_REFERENCE = 136

# Skyrim ingredient names a reply may say only when its speaker's own facts name them (owner ruling 2026-11-08: a
# plant stays only where BM&V places it, and a reply states only what its speaker's facts back).
INGREDIENTS = ("amanita", "parasol moss", "nightshade", "deathbell", "jazbay", "gleamblossom", "lavender", "juniper",
               "nirnroot", "lichen", "creep cluster", "glowing mushroom", "fungal pod", "mountain flower", "leek",
               "gourd", "thistle", "canis root", "frost mirriam", "snowberr")
_NAME = re.compile(r"(?<![.!?…] )(?<!^)\b[A-Z][A-Za-z]+(?:-[A-Za-z]+)*")
_SIDE = re.compile(r"\b(?:north|south|east|west)(?:-(?:north|south|east|west))* (?:side|edge|end)\b")


def unbacked(text: str, backing: str) -> list[str]:
    """What a reply names that its speaker's rows do not: a mid-sentence capitalised name, a Skyrim ingredient or a
    'south side'-style place, absent from `backing` (the speaker's facts and own row, as one string)."""
    back = backing.lower()
    out = [m.group(0) for m in _NAME.finditer(text) if m.group(0).lower() not in back]
    out += [i for i in INGREDIENTS if i in text.lower() and i not in back]
    out += [m.group(0) for m in _SIDE.finditer(text.lower()) if m.group(0) not in back]
    return out


def check_lines(w) -> int:
    """Every written reply's names, ingredients and sides against its speaker's facts and row; returns the count."""
    facts = {f.id: f.claim for f in w.rows("talk_fact")}
    bad = 0
    for t in w.rows("talker"):
        own = " ".join(facts[f.strip()] for tt in w.rows("talker_topic", talker=t.id)
                       for f in tt.facts.split(",") if f.strip() in facts)
        backing = own + " " + " ".join(str(v) for v in dataclasses.astuple(t))
        for ln in w.rows("talk_line", talker=t.id):
            miss = unbacked(ln.text, backing)
            if miss:
                bad += 1
                print(f"UNBACKED {t.id} {ln.topic} #{ln.ord}: {sorted(set(miss))}")
    print(f"talk_check lines: {bad} unbacked")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--esp", default="out/Argonia.esp")
    ap.add_argument("--lines-only", action="store_true", help="only the replies-versus-facts check (no ESP read)")
    a = ap.parse_args()
    w = db.open()
    nlines = check_lines(w)
    if a.lines_only:
        return 1 if nlines else 0
    pl = esm.Plugin.read(Path(a.esp))
    recs = pl.records()
    by_key = {r.key: r for r in recs}
    dial = {r.key: r.edid for r in recs if r.sig == "DIAL"}
    topic_of = {}
    for t in w.rows("talk_topic"):
        topic_of["ARG_Talk_" + "".join(p.capitalize() for p in t.id.split(".")[1].split("-"))] = t.id
    gated = defaultdict(set)
    for r in recs:
        if r.sig != "INFO":
            continue
        edid = dial.get(pl.form_key(r.parents[-1][1]), "")
        for d in r.all("CTDA"):
            if struct.unpack_from("<H", d, 8)[0] == GET_IS_REFERENCE:
                gated[pl.form_key(struct.unpack_from("<I", d, 12)[0])].add(topic_of.get(edid, edid))
    bad = nlines
    talkers = [t for t in w.rows("talker") if t.status in ("written", "built")]
    for t in talkers:
        c = w.get("bmv_talker", t.id)
        want = {tt.topic for tt in w.rows("talker_topic", talker=t.id)}
        got = gated.get(t.id, set())
        line = f"{t.id:32} {t.known_as:24} topics {len(got)}/{len(want)}"
        if got != want:
            line += f"  MISMATCH missing {sorted(want - got)} extra {sorted(got - want)}"
            bad += 1
        if t.known_as != c.name and not t.known_as.startswith("the "):
            ref = by_key.get(t.id)
            base = by_key.get(ref.ref("NAME")) if ref else None
            if base is None or base.zstr("FULL") != t.known_as or base.ref("TPLT") != c.npc:
                line += f"  NAME WRONG (ref {'overridden' if ref else 'not overridden'}, base {base.edid if base else None})"
                bad += 1
            else:
                line += f"  named: ref -> {base.edid} \"{base.zstr('FULL')}\" (template {c.npc})"
        print(line)
    for f in (r for r in recs if r.sig == "FACT" and r.ref("VENC")):
        chest = by_key.get(f.ref("VENC"))
        box = by_key.get(chest.ref("NAME")) if chest else None
        if box is None:
            print(f"{f.edid}: chest not ours"); bad += 1
            continue
        stock = [(pl.form_key(struct.unpack_from("<I", d, 0)[0]), struct.unpack_from("<i", d, 4)[0]) for d in box.all("CNTO")]
        print(f"{f.edid}: chest {chest.edid} -> {box.edid}: " + ", ".join(f"{k} x{n}" for k, n in stock))
    print(f"talk_check: {len(talkers)} talkers, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
