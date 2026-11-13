"""The ecology animation audit on synthetic plugins and a synthetic card (never out/ or the real stack)."""
from __future__ import annotations

import struct

from tools.argonia_world.esm import Plugin, Record
from tools.newworld.ecology import anim_audit as A

NAME = "Mod.esp"


def z(s: str) -> bytes:
    return s.encode() + b"\0"


def ref(fid: int) -> bytes:
    return struct.pack("<I", fid)


def nif(strings: list[str], skinned: bool) -> bytes:
    types = ["NiNode", "NiSkinInstance" if skinned else "BSTriShape"]
    h = b"Gamebryo File Format, Version 20.2.0.7\n" + struct.pack("<IBIII", 0x14020007, 1, 12, 2, 100)
    h += b"".join(bytes([len(s)]) + s for s in (b"a\0", b"b\0", b"c\0"))
    h += struct.pack("<H", 2) + b"".join(struct.pack("<I", len(t)) + t.encode() for t in types)
    h += struct.pack("<HH", 0, 1) + struct.pack("<II", 10, 10)
    h += struct.pack("<II", len(strings), max(map(len, strings)))
    return h + b"".join(struct.pack("<I", len(s)) + s.encode() for s in strings)


class Card:
    """A resolver over a dict of lower-case data path -> bytes."""

    def __init__(self, files: dict[str, bytes]):
        self.files = {A.norm(k): v for k, v in files.items()}
        self.loose = {k: "mod" for k in self.files}

    def read(self, key):
        return self.files.get(key)

    def archives(self):
        return []


def plugin(rows) -> Plugin:
    p = Plugin(NAME, [], [])
    for sig, fid, subs in rows:
        p._records.append(Record(sig, 0, fid, subs, (), p))
    return p


def race(fid: int, edid: str, skeleton: str, project: str):
    return ("RACE", fid, [("EDID", z(edid)), ("MNAM", b""), ("ANAM", z(skeleton)), ("FNAM", b""), ("ANAM", z(skeleton)),
                         ("MNAM", b""), ("MODL", z(project)), ("FNAM", b""), ("MODL", z(project))])


def creature(base: int, edid: str, race_fid: int, mesh: str):
    """NPC_ -> race and skin ARMO 0x..1 -> ARMA 0x..2 (this race) -> mesh."""
    return [("NPC_", base, [("EDID", z(edid)), ("ACBS", b"\0" * 24), ("RNAM", ref(race_fid)), ("WNAM", ref(base + 1))]),
            ("ARMO", base + 1, [("EDID", z(edid + "Skin")), ("MODL", ref(base + 2))]),
            ("ARMA", base + 2, [("EDID", z(edid + "AA")), ("RNAM", ref(race_fid)), ("MOD2", z(mesh))])]


BONES = ["NPC Root", "NPC Spine", "NPC Head", "NPC Tail1"]


def files(project_dir: str, rig_bones: list[str], skel_bones: list[str], mesh: str | None, skinned=True) -> dict:
    f = {f"{project_dir}\\Skel.nif": nif(skel_bones, False),
         f"{project_dir}\\XProject.hkx": b"..\0Characters\\XCharacter.hkx\0..",
         f"{project_dir}\\Characters\\XCharacter.hkx": b"Behaviors\\XBehavior.hkx\0Character Assets\\skeleton.hkx\0",
         f"{project_dir}\\Behaviors\\XBehavior.hkx": b"x",
         f"{project_dir}\\Character Assets\\skeleton.hkx": b"\0".join(b.encode() for b in rig_bones) + b"\0",
         f"{project_dir}\\Animations\\Idle.hkx": b"x"}
    if mesh:
        f[mesh] = nif(skel_bones, skinned)
    return f


def build(kind_files: dict, rows) -> A.Audit:
    p = plugin(rows)
    return A.Audit(Card(kind_files), lambda name: p, lambda name: True)


def row_for(project_dir: str, **kw):
    f = files(project_dir, kw.get("rig", BONES), kw.get("skel", BONES), "Actors\\X\\Body.nif" if kw.get("mesh", True) else None,
              kw.get("skinned", True))
    if kw.get("mesh") == "gone":
        f.pop("Actors\\X\\Body.nif", None)
    rows = [race(0x800, "XRace", f"{project_dir}\\Skel.nif", f"{project_dir}\\XProject.hkx")] + creature(0x810, "Xbeast", 0x800, "Actors\\X\\Body.nif")
    return build(f, rows).kind_of(f"{NAME}:Xbeast")


def test_a_working_creature_passes():
    r = row_for("Actors\\X")
    assert r["ok"], r["reasons"]
    assert r["clips"] == 1 and r["rig_bones_matched"] == 1.0 and r["meshes"][0]["skinned"] is True


def test_skeleton_that_the_projects_rig_does_not_name_fails():
    r = row_for("Actors\\X", rig=["Ice Root", "Ice Wing"])
    assert not r["ok"] and "cannot drive this skeleton" in r["reasons"][0]


def test_a_mesh_without_a_skin_instance_fails_as_rigid():
    r = row_for("Actors\\X", skinned=False)
    assert not r["ok"] and "no skin instance" in r["reasons"][0]


def test_a_missing_body_mesh_fails():
    r = row_for("Actors\\X", mesh="gone")
    assert not r["ok"] and "body mesh not on the card" in r["reasons"][0]


def test_missing_project_and_missing_record():
    p = plugin([race(0x800, "XRace", "Actors\\X\\Skel.nif", "Actors\\X\\XProject.hkx")] + creature(0x810, "Xbeast", 0x800, "Actors\\X\\Body.nif"))
    a = A.Audit(Card({"Actors\\X\\Skel.nif": nif(BONES, False)}), lambda n: p, None)
    r = a.kind_of(f"{NAME}:Xbeast")
    assert not r["ok"] and any("behaviour project not on the card" in x for x in r["reasons"])
    assert a.kind_of(f"{NAME}:Nothing")["reasons"] == ["npc record not found in its plugin"]


def test_run_fails_placed_kinds_only_and_checks_the_copy():
    f = files("Actors\\X", BONES, BONES, "Actors\\X\\Body.nif")
    rows = [race(0x800, "XRace", "Actors\\X\\Skel.nif", "Actors\\X\\XProject.hkx")] + creature(0x810, "Xbeast", 0x800, "Actors\\X\\Body.nif") \
        + creature(0x820, "Ybeast", 0x828, "Actors\\X\\Body.nif")
    a = build(f, rows)
    actors = {"actors": [{"src": f"{NAME}:Xbeast", "kind": "good"}]}
    bindings = {"kinds": {"good": {"records": [f"{NAME}:Xbeast"]}, "dangling": {"records": [f"{NAME}:Ybeast"]}}}
    copies = {"ANW_T_XRace": {"edid": "ANW_T_XRace", "M": {"skeleton": "actors/x/skel.nif", "project": "Actors\\X\\XProject.hkx"},
                              "F": {}}}
    res = A.run(actors, bindings, a, copies)
    assert res["failing"] == [] and res["kinds"]["dangling"]["verdict"] == "ok" and not res["kinds"]["dangling"]["placed"]
    copies["ANW_T_XRace"]["M"]["project"] = "Actors\\Y\\YProject.hkx"
    res = A.run(actors, bindings, a, copies)
    assert res["failing"] == ["good"] and "copy of the race differs" in res["kinds"]["good"]["reason"]
