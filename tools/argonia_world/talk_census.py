"""The talk census: every person BM&V places (an enabled ACHR of a person base, from the bmv_* census) with what the
engine gives them to say, written to `bmv_talker` for the talk pipeline (docs/design/talk.md).

Why "E to talk" opens nothing (measured 2026-11-07, `measure`): Skyrim opens the dialogue menu only when a top-level
player topic has an INFO whose conditions pass for that speaker. Of Skyrim.esm and Update.esm's top-level player INFOs,
93% are gated to one speaker (GetIsID or a quest alias) and the rest to a job or role faction (JobMerchantFaction and
the like); none is generic. BM&V's own plugins add no dialogue (Black Marsh.esm: 0 DIAL; Black Marsh North.esp: one
branch; Valenwood.esp: 3 INFOs). So a BM&V person not in such a faction, and not a vanilla base with its own lines, has
no topic: the Hello bark plays (or, with no voice type, nothing) and no menu opens. Vanilla's generic townsfolk are the
same; Bethesda gives every person who talks lines of their own.

Rerunning replaces every bmv_talker row; the authored talk tables (talker, talker_topic, talk_fact, talk_line) are kept.

    python3 -m tools.argonia_world.talk_census build     # bmv_talker from the plugins and the bmv_* tables
    python3 -m tools.argonia_world.talk_census measure   # the mechanism's numbers, printed
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
from collections import Counter, defaultdict

from tools.argonia_world import db, esm
from tools.argonia_world.bmv_census import DIR, MASTERS, MASTER_FILES, PLUGINS

SIGS = {"DIAL", "DLBR", "FLST", "VTYP", "NPC_", "LVLN"}
GET_IS_ID, GET_IN_FACTION, GET_IS_ALIAS_REF, GET_IS_VOICE_TYPE = 72, 71, 566, 426
VANILLA = ("Skyrim.esm", "Update.esm")
HOSTILE = {"BanditFaction", "VampireFaction", "CreatureFaction", "DremoraFaction", "SprigganFaction",
           "SprigganPredatorFaction", "WarlockFaction", "NecromancerFaction", "ForswornFaction"}
HOSTILE_RACES = {"BMNagaRace"}


class World:
    """The load order's winning DIAL/DLBR/FLST/VTYP/NPC_/LVLN records and every INFO by its topic."""

    def __init__(self) -> None:
        self.win: dict[str, esm.Record] = {}
        self.infos: dict[str, list[tuple[str, esm.Record]]] = defaultdict(list)
        self.own_dial: Counter = Counter()
        for path in [MASTERS / f for f in MASTER_FILES] + [DIR / f for f in PLUGINS]:
            pl = esm.Plugin.read(path, SIGS)
            for r in pl.records():
                if r.sig == "INFO":
                    self.infos[pl.form_key(r.parents[-1][1])].append((pl.name, r))
                    if pl.name in PLUGINS:
                        self.own_dial["INFO", pl.name] += 1
                else:
                    self.win[r.key] = r
                    if r.sig == "DIAL" and pl.name in PLUGINS:
                        self.own_dial["DIAL", pl.name] += 1

    def voice_types(self, key: str) -> set[str]:
        def walk(k: str, seen: tuple) -> set[str]:
            r = self.win.get(k)
            if r is None or k in seen:
                return set()
            if r.sig == "VTYP":
                return {r.edid or k}
            if r.sig == "FLST":
                return set().union(*[walk(r.plugin.form_key(_u32(d)), seen + (k,)) for d in r.all("LNAM")] or [set()])
            if r.sig == "LVLN":
                return set().union(*[walk(r.plugin.form_key(_u32(d, 4)), seen + (k,)) for d in r.all("LVLO")]
                                   or [set()])
            acbs, t = r.sub("ACBS"), r.ref("TPLT")
            if t and acbs and struct.unpack_from("<H", acbs, 18)[0] & 1:     # traits (voice) from the template
                return walk(t, seen + (k,))
            v = r.ref("VTCK")
            return walk(v, seen + (k,)) if v else set()
        return walk(key, ())

    def template_chain(self, key: str) -> list[str]:
        out, k = [], key
        while k and k not in out and (r := self.win.get(k)) is not None and r.sig == "NPC_":
            out.append(k)
            k = r.ref("TPLT")
        return out

    def top_level_infos(self):
        for r in self.win.values():
            if r.sig != "DLBR" or r.key.split(":")[1] not in VANILLA:
                continue
            d = r.sub("DNAM")
            if d and _u32(d) & 1:
                for pn, info in self.infos.get(r.ref("SNAM") or "", []):
                    if pn in VANILLA:
                        yield info


def _u32(d: bytes, o: int = 0) -> int:
    return struct.unpack_from("<I", d, o)[0]


def conditions(r: esm.Record):
    for d in r.all("CTDA"):
        fn, p1 = struct.unpack_from("<H", d, 8)[0], _u32(d, 12)
        yield fn, (r.plugin.form_key(p1) if p1 else None), struct.unpack_from("<f", d, 4)[0], _u32(d, 20)


def gates(w: World) -> tuple[set[str], set[str], Counter]:
    """The speakers (bases) and factions that vanilla's top-level player topics are gated to, and the tally."""
    subjects, factions, tally = set(), set(), Counter()
    for info in w.top_level_infos():
        cs = [c for c in conditions(info) if c[3] == 0]            # run on the subject
        fns = {c[0] for c in cs}
        if GET_IS_ID in fns or GET_IS_ALIAS_REF in fns:
            tally["one speaker (GetIsID or alias)"] += 1
            subjects |= {c[1] for c in cs if c[0] == GET_IS_ID and c[2] == 1.0 and c[1]}
        elif GET_IN_FACTION in fns:
            tally["a job or role faction"] += 1
            factions |= {c[1] for c in cs if c[0] == GET_IN_FACTION and c[2] == 1.0 and c[1]}
        else:
            tally["other (quest or follower state)"] += 1
    return subjects, factions, tally


def build(w: World, store) -> list[dict]:
    subjects, gate_factions, _ = gates(w)
    people = store.query(
        "SELECT p.id, p.npc, p.cell, p.x, p.y, n.editor_id, n.name, n.sex, r.editor_id AS race, c.name AS class, "
        "ce.interior, ce.name AS cell_name, ce.editor_id AS cell_edid, sc.settlement, s.name AS settlement_name "
        "FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc JOIN bmv_cell ce ON ce.id = p.cell "
        "LEFT JOIN bmv_race r ON r.id = n.race LEFT JOIN bmv_class c ON c.id = n.class "
        "LEFT JOIN bmv_settlement_cell sc ON sc.cell = p.cell LEFT JOIN bmv_settlement s ON s.id = sc.settlement "
        "WHERE n.person = 1 AND p.disabled = 0 ORDER BY p.id")
    facs = defaultdict(list)
    for f in store.query("SELECT nf.npc, f.id, f.editor_id FROM bmv_npc_faction nf JOIN bmv_faction f ON f.id = nf.faction"):
        facs[f["npc"]].append((f["id"], f["editor_id"] or f["id"]))
    markers = defaultdict(list)
    for m in store.query("SELECT settlement, name, x, y FROM bmv_map_marker WHERE settlement IS NOT NULL AND name IS NOT NULL"):
        markers[m["settlement"]].append(m)
    rows = []
    for p in people:
        fl = facs.get(p["npc"], [])
        names = {e for _, e in fl}
        voices = sorted(w.voice_types(p["npc"]))
        chain = w.template_chain(p["npc"])
        if p["race"] in HOSTILE_RACES or names & HOSTILE:
            status = "hostile"
        elif "corpse" in (p["editor_id"] or "").lower():
            status = "corpse"
        elif subjects & set(chain):
            status = "vanilla-lines"
        elif gate_factions & {k for k, e in fl if e.startswith("Job")}:   # a trade's menu (CW and follower gates need quest state)
            status = "service"
        else:
            status = "silent"
        if p["interior"]:
            sub = p["cell_name"] or p["cell_edid"]
        else:
            near = min(markers.get(p["settlement"], []), default=None,
                       key=lambda m: math.hypot(m["x"] - p["x"], m["y"] - p["y"]))
            sub = (f"near {near['name']}" if near and math.hypot(near["x"] - p["x"], near["y"] - p["y"]) < 8192
                   else (p["cell_name"] or p["cell_edid"] or "open ground"))
        rows.append(dict(id=p["id"], npc=p["npc"], editor_id=p["editor_id"], name=p["name"], race=p["race"],
                         sex=p["sex"], class_name=p["class"], factions=", ".join(sorted(names)) or None,
                         voice=", ".join(voices) or None, settlement=p["settlement"], cell=p["cell"],
                         interior=bool(p["interior"]), sub_location=sub, x=round(p["x"]), y=round(p["y"]),
                         status=status))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "measure"])
    a = ap.parse_args()
    w, store = World(), db.open()
    if a.cmd == "measure":
        _, _, tally = gates(w)
        print("vanilla top-level player INFOs by who they are gated to:", dict(tally))
        print("BM&V's own dialogue records:", dict(w.own_dial))
        rows = build(w, store)
        print("placed persons by talk status:", dict(Counter(r["status"] for r in rows)))
        print("of them with no voice type:", sum(1 for r in rows if not r["voice"]))
        return 0
    rows = build(w, store)
    store.con.execute('DELETE FROM "bmv_talker"')
    store.dirty.add("bmv_talker")
    store.insert_many("bmv_talker", rows)
    store.save(["bmv_talker"])
    print(f"bmv_talker: {len(rows)} rows", dict(Counter(r["status"] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
