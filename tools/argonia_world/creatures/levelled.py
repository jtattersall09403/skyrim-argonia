"""Decision 0035 in the creature records: what of a mod creature scales with the player, and the L1 check.

A mod NPC_ scales when its stats (its own, or its template's through the Use Stats flag) carry ACBS's PC-level
multiplier; its death item is levelled when any levelled item list it reaches holds an entry above level 1 (the
player's level then gates that entry: Skyrim's DeathItemMudCrab01 reaches LItemGemsSmall, entries 1-18). Read from
the laid stack and the game's Data (never the repo: decision 0003); a form id's top byte names the master as the
plugin's own MAST list does.

    check(esm)  every record a plugin of ours writes, read back from its bytes: no NPC_ with the PC-level
                multiplier or CalcMin <> CalcMax, no LVLN or LVLI entry above level 1, no ECZN with min <> max, no
                NPC_ templated on a scaling mod creature that takes its stats from it (Use Stats, 0x02)
"""
from __future__ import annotations

import struct
import zlib
from functools import lru_cache
from pathlib import Path

from tools.argonia_world.creatures.actors import _subs

PC_MULT = 0x80  # ACBS flags
USE_STATS, USE_TRAITS = 0x02, 0x01  # ACBS template flags
LVL_ALL_BELOW_PC = 0x01  # LVLF: calculate from all levels <= the player's
KEEP = (b"NPC_", b"LVLI", b"LVLN", b"ECZN")


def _path(name: str) -> Path:
    from tools.argonia_world.creatures.inventory import MODS, PLUGINS
    from tools.argonia_world.vanilla import load
    for d, p in PLUGINS:
        if p.lower() == name.lower() and (MODS / d / p).exists():
            return MODS / d / p
    return load.data_dir() / name


def read(path: Path) -> tuple[list[str], dict[int, tuple[bytes, list]]]:
    """(masters, {local id: (signature, subrecords)}) for the NPC_, LVLI, LVLN and ECZN of one plugin."""
    blob = Path(path).read_bytes()
    hl = struct.unpack_from("<I", blob, 4)[0]
    masters = [b.rstrip(b"\0").decode() for s, b in _subs(blob[24:24 + hl]) if s == b"MAST"]
    out: dict[int, tuple[bytes, list]] = {}

    def walk(i: int, end: int) -> None:
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                if struct.unpack_from("<i", blob, i + 12)[0] == 0 and blob[i + 8:i + 12] not in KEEP:
                    i += size
                    continue
                walk(i + 24, i + size)
                i += size
                continue
            fl, fid = struct.unpack_from("<II", blob, i + 8)
            if sig in KEEP:
                b = blob[i + 24:i + 24 + size]
                out[fid] = (sig, _subs(zlib.decompress(b[4:]) if fl & 0x40000 else b))
            i += 24 + size

    walk(hl + 24, len(blob))
    return masters, out


@lru_cache(maxsize=None)
def _plugin(name: str):
    return read(_path(name))


def _owner(name: str, fid: int) -> tuple[str, int]:
    masters, _ = _plugin(name)
    i = fid >> 24
    return (masters[i] if i < len(masters) else name), fid & 0xFFFFFF


def _get(name: str, fid: int):
    owner, local = _owner(name, fid)
    masters, recs = _plugin(owner)
    return owner, recs.get((len(masters) << 24) | local) or recs.get(local)


def _one(subs: list, sig: bytes) -> bytes | None:
    return next((b for s, b in subs if s == sig), None)


def acbs(subs: list) -> tuple[int, int, int, int, int]:
    """(flags, level, calc min, calc max, template flags) of an NPC_."""
    a = _one(subs, b"ACBS") or b"\0" * 24
    fl, = struct.unpack_from("<I", a)
    lvl, mn, mx = struct.unpack_from("<hHH", a, 8)
    tf, = struct.unpack_from("<H", a, 18)
    return fl, lvl, mn, mx, tf


def _resolve(name: str, fid: int, flag: int, depth: int = 0):
    """The NPC_ whose part `flag` (Use Stats, Use Traits) a form takes, through its template chain."""
    owner, r = _get(name, fid)
    if r is None or r[0] != b"NPC_" or depth > 6:
        return owner, r
    t = _one(r[1], b"TPLT")
    if t and acbs(r[1])[4] & flag:
        return _resolve(owner, struct.unpack("<I", t)[0], flag, depth + 1)
    return owner, r


def scales(form_key: str) -> bool:
    """The mod form's stats carry the PC-level multiplier."""
    fid, name = form_key.split(":", 1)
    masters, _ = _plugin(name)
    _, r = _resolve(name, (len(masters) << 24) | int(fid, 16), USE_STATS)
    return bool(r and r[0] == b"NPC_" and acbs(r[1])[0] & PC_MULT)


def full_name(form_key: str) -> str:
    """The FULL name the game shows for a mod NPC_ (`0008F6:King of the Murkmire.esp`): its own, else its template's
    through the Use Traits flag; "" when none. Read from the plugin's bytes, never typed."""
    fid, name = form_key.split(":", 1)
    masters, _ = _plugin(name)
    _, r = _resolve(name, (len(masters) << 24) | int(fid, 16), USE_TRAITS)
    full = r and _one(r[1], b"FULL")
    return full.rstrip(b"\0").decode("utf-8", "replace") if full and len(full) != 4 else ""


def levelled_list(name: str, fid: int, depth: int = 0) -> bool:
    """An LVLI that reaches an entry above level 1."""
    owner, r = _get(name, fid)
    if r is None or r[0] != b"LVLI" or depth > 10:
        return False
    for s, b in r[1]:
        if s == b"LVLO":
            lv, _, f = struct.unpack_from("<HHI", b)
            if lv > 1 or levelled_list(owner, f, depth + 1):
                return True
    return False


def death_item_levelled(form_key: str) -> bool:
    fid, name = form_key.split(":", 1)
    masters, _ = _plugin(name)
    owner, r = _resolve(name, (len(masters) << 24) | int(fid, 16), USE_TRAITS)
    inam = r and _one(r[1], b"INAM")
    return bool(inam) and levelled_list(owner, struct.unpack("<I", inam)[0])


def check(esm: Path, scaling: set[str]) -> dict:
    """Decision 0035's L1 check over a plugin's own records (read back from its bytes); `scaling`: the mod form
    keys whose records scale (creature_form.pc_level_mult)."""
    masters, recs = read(esm)
    own = len(masters)
    bad = []
    n = {"NPC_": 0, "LVLN": 0, "LVLI": 0, "ECZN": 0}
    for fid, (sig, subs) in recs.items():
        if fid >> 24 != own:
            continue
        s = sig.decode()
        n[s] += 1
        edid = (_one(subs, b"EDID") or b"?").rstrip(b"\0").decode()
        if sig == b"NPC_":
            fl, _, mn, mx, tf = acbs(subs)
            if fl & PC_MULT or mn != mx:
                bad.append(f"{edid}: PC-level multiplier or CalcMin {mn} <> CalcMax {mx}")
            t = _one(subs, b"TPLT")
            if t and tf & USE_STATS:
                tid = struct.unpack("<I", t)[0]
                fk = f"{tid & 0xFFFFFF:06X}:{masters[tid >> 24]}" if tid >> 24 < own else None
                if fk in scaling:
                    bad.append(f"{edid}: takes its stats from the scaling {fk}")
        elif sig in (b"LVLN", b"LVLI"):
            hi = [struct.unpack_from("<H", b)[0] for t, b in subs if t == b"LVLO"]
            if any(v > 1 for v in hi):
                bad.append(f"{edid}: a levelled entry at {max(hi)}")
        elif sig == b"ECZN":
            d = _one(subs, b"DATA") or b""
            if len(d) >= 12:
                _, _, _, mn, _, mx = struct.unpack_from("<IIbbBb", d)
                if mn != mx:
                    bad.append(f"{edid}: zone min {mn} <> max {mx}")
    return {"records": n, "fail": bad[:10] or None}
