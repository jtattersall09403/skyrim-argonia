"""Read the actor side of a plugin: NPC_, LVLN, ECZN, RACE, FACT and every ACHR with its worldspace and cell
(decision 0034: measure how the builders did it; nothing read here enters git, 0003).

    scan(path) -> Scan   (stdlib + struct; one pass over the file, ~40 s for Skyrim.esm)

Field layouts are UESP's Skyrim mod-file format pages (NPC_ ACBS/AIDT/TPLT, LVLN LVLD/LVLF/LVLO, ECZN DATA,
RACE DATA flags), the same layouts xEdit reads.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from tools.argonia_world.skyrim_units import CELL_UNITS

KEEP = {b"NPC_", b"LVLN", b"ECZN", b"RACE", b"FACT", b"CELL", b"ACHR", b"WRLD", b"PACK"}


def _subs(body: bytes) -> list[tuple[bytes, bytes]]:
    out, i, big = [], 0, None
    while i + 6 <= len(body):
        sig = body[i:i + 4]
        size = struct.unpack_from("<H", body, i + 4)[0]
        i += 6
        if sig == b"XXXX":
            big = struct.unpack_from("<I", body, i)[0]
            i += size
            continue
        if big is not None:
            size, big = big, None
        out.append((sig, body[i:i + size]))
        i += size
    return out


def _z(b: bytes) -> str:
    return b.split(b"\0", 1)[0].decode("latin1")


@dataclass
class Npc:
    fid: int
    edid: str
    name: str
    race: int | None
    level: int  # ACBS level (or level mult x1000 when pc_mult)
    pc_mult: bool
    aggression: int  # AIDT[0]: 0 unaggressive, 1 aggressive, 2 very, 3 frenzied
    confidence: int  # AIDT[1]: 0 cowardly .. 4 foolhardy
    template: int | None  # TPLT: an LVLN or NPC_
    factions: list[int]
    model: str


@dataclass
class Lvln:
    fid: int
    edid: str
    chance_none: int
    flags: int  # 1 all levels <= PC, 2 each in count, 4 use all
    entries: list[tuple[int, int, int]]  # (level, form, count)


@dataclass
class Eczn:
    fid: int
    edid: str
    location: int
    min_level: int
    max_level: int
    flags: int  # 1 never resets, 2 match PC below min, 4 disable combat boundary


@dataclass
class Race:
    fid: int
    edid: str
    name: str
    flags: int  # DATA flags at +32: 0x10 swims, 0x20 flies, 0x40 walks
    size: int  # DATA +36: 0 small 1 medium 2 large 3 extra large


@dataclass
class Achr:
    base: int
    world: int | None
    cell: tuple[int, int] | None  # exterior grid (from XCLC, or from the position for a persistent ref)
    interior: int | None  # the CELL fid when interior
    pos: tuple[float, float, float]
    zone: int | None  # XEZN
    flags: int


@dataclass
class Scan:
    path: str
    masters: list[str] = field(default_factory=list)
    npcs: dict[int, Npc] = field(default_factory=dict)
    lvlns: dict[int, Lvln] = field(default_factory=dict)
    ecznS: dict[int, Eczn] = field(default_factory=dict)
    races: dict[int, Race] = field(default_factory=dict)
    factions: dict[int, str] = field(default_factory=dict)
    achrs: list[Achr] = field(default_factory=list)
    cell_zone: dict[tuple[int, int], int] = field(default_factory=dict)  # exterior cell XEZN
    interior_zone: dict[int, int] = field(default_factory=dict)
    worlds: dict[int, str] = field(default_factory=dict)
    world_water: dict[int, float] = field(default_factory=dict)  # WRLD DNAM default water height (units)
    cell_water: dict[tuple[int, int, int], float] = field(default_factory=dict)  # (world, x, y) -> XCLW


def scan(path: Path | str) -> Scan:
    blob = Path(path).read_bytes()
    out = Scan(str(path))
    hdr = _subs(blob[24:24 + struct.unpack_from("<I", blob, 4)[0]])
    out.masters = [_z(b) for s, b in hdr if s == b"MAST"]
    st = {"cell": None, "int": None}

    def body(i, size, flags):
        b = blob[i + 24:i + 24 + size]
        return zlib.decompress(b[4:]) if flags & 0x40000 else b

    def walk(i, end, wrld):
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                label, gtype = struct.unpack_from("<Ii", blob, i + 8)
                if gtype == 0 and blob[i + 8:i + 12] not in KEEP:
                    i += size
                    continue
                walk(i + 24, i + size, label if gtype == 1 else wrld)
                i += size
                continue
            flags, fid = struct.unpack_from("<II", blob, i + 8)
            if sig in KEEP:
                d = dict(_subs(body(i, size, flags)))
                edid = _z(d.get(b"EDID", b""))
                if sig == b"NPC_":
                    acbs = d.get(b"ACBS", b"\0" * 24)
                    fl = struct.unpack_from("<I", acbs)[0]
                    lvl = struct.unpack_from("<h", acbs, 8)[0]
                    ai = d.get(b"AIDT", b"\0\0")
                    facs = [struct.unpack_from("<I", b)[0] for s, b in _subs(body(i, size, flags)) if s == b"SNAM"]
                    out.npcs[fid] = Npc(fid, edid, _z(d.get(b"FULL", b"")) if len(d.get(b"FULL", b"")) != 4 else "",
                                        struct.unpack("<I", d[b"RNAM"])[0] if b"RNAM" in d else None, lvl,
                                        bool(fl & 0x80), ai[0], ai[1],
                                        struct.unpack("<I", d[b"TPLT"])[0] if b"TPLT" in d else None, facs,
                                        _z(d.get(b"MODL", b"")))
                elif sig == b"LVLN":
                    ents = []
                    for s, b in _subs(body(i, size, flags)):
                        if s == b"LVLO" and len(b) >= 10:
                            lv, _, f, n = struct.unpack_from("<HHIH", b)
                            ents.append((lv, f, n))
                    out.lvlns[fid] = Lvln(fid, edid, d.get(b"LVLD", b"\0")[0], d.get(b"LVLF", b"\0")[0], ents)
                elif sig == b"ECZN":
                    dd = d.get(b"DATA", b"\0" * 12)
                    if len(dd) >= 12:
                        _, loc, _, mn, fl, mx = struct.unpack_from("<IIbbBb", dd)
                    else:
                        loc, mn, fl, mx = 0, 0, 0, 0
                    out.ecznS[fid] = Eczn(fid, edid, loc, mn, mx, fl)
                elif sig == b"RACE":
                    dd = d.get(b"DATA", b"")
                    out.races[fid] = Race(fid, edid, _z(d.get(b"FULL", b"")) if len(d.get(b"FULL", b"")) != 4 else "",
                                          struct.unpack_from("<I", dd, 32)[0] if len(dd) >= 36 else 0,
                                          struct.unpack_from("<I", dd, 36)[0] if len(dd) >= 40 else 0)
                elif sig == b"FACT":
                    out.factions[fid] = edid
                elif sig == b"WRLD":
                    out.worlds[fid] = edid
                    if b"DNAM" in d:
                        out.world_water[fid] = struct.unpack_from("<f", d[b"DNAM"], 4)[0]
                elif sig == b"CELL":
                    if b"XCLC" in d:
                        st["cell"], st["int"] = struct.unpack_from("<ii", d[b"XCLC"]), None
                        if b"XEZN" in d:
                            out.cell_zone[st["cell"]] = struct.unpack("<I", d[b"XEZN"])[0]
                        if b"XCLW" in d and wrld is not None:
                            out.cell_water[(wrld, *st["cell"])] = struct.unpack("<f", d[b"XCLW"])[0]
                    else:
                        st["cell"], st["int"] = None, fid
                        if b"XEZN" in d:
                            out.interior_zone[fid] = struct.unpack("<I", d[b"XEZN"])[0]
                elif sig == b"ACHR" and b"NAME" in d and b"DATA" in d:
                    p = struct.unpack("<3f", d[b"DATA"][:12])
                    cell = st["cell"]
                    if wrld is not None and st["int"] is None:
                        cell = (int(p[0] // CELL_UNITS), int(p[1] // CELL_UNITS))
                    out.achrs.append(Achr(struct.unpack("<I", d[b"NAME"])[0], wrld if st["int"] is None else None,
                                          cell if st["int"] is None else None, st["int"], p,
                                          struct.unpack("<I", d[b"XEZN"])[0] if b"XEZN" in d else None, flags))
            i += 24 + size

    walk(struct.unpack_from("<I", blob, 4)[0] + 24, len(blob), None)
    return out


def resolve(s: Scan, fid: int, depth: int = 0) -> list[int]:
    """The NPC_ forms a base (NPC_ or LVLN, through templates and nested lists) can spawn."""
    if depth > 6:
        return []
    if fid in s.lvlns:
        return [n for _, f, _ in s.lvlns[fid].entries for n in resolve(s, f, depth + 1)]
    n = s.npcs.get(fid)
    if n is None:
        return []
    if n.template is not None and n.template in s.lvlns:
        return resolve(s, n.template, depth + 1)
    return [fid]
