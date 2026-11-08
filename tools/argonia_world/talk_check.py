"""Talk read-back (docs/design/talk.md): out/Argonia.esp against the talk tables, after `plugin.sh check` built it.

For every talker with written lines: each of their topics has one INFO gated GetIsReference to their placed ref (and
no other topic is); a talker whose name differs from the placed base's (`known_as`) has their ref overridden to a
base of our own carrying that name, templated on the old base; and the vendors we restock show their chest's stock.

    python3 -m tools.argonia_world.talk_check [--esp out/Argonia.esp] [--settlement-prefix fact.lilmoth.]
"""
from __future__ import annotations

import argparse
import struct
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db, esm

GET_IS_REFERENCE = 136


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--esp", default="out/Argonia.esp")
    a = ap.parse_args()
    pl = esm.Plugin.read(Path(a.esp))
    w = db.open()
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
    bad = 0
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
