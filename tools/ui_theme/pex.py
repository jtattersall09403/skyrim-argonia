"""SkyUI's item-list font sizes (ui-review4): MCM Helper's SKI_ConfigMenu.ApplyItemListFontSize sets them as string overrides on
every game load ("13"/"12" small, "14"/"12" medium, "18"/"14" large, icons "16"/"18"/"20"), which win over
interface/skyui/config.txt; at 1080p medium read ~14 px a line. The recipe reads SKI_ConfigMenu.pex out of
SkyUI_SE.bsa (an uncompressed v105 archive), maps those numeric strings in its string table and writes a loose copy
into the overlay (scripts/), which the game prefers to the archive. Code refers to strings by index, so only the
table changes. Made on the player's machine (0014), never shipped.
"""
from __future__ import annotations

import struct
from pathlib import Path

# item-list sizes (and the icon sizes, shared strings) x1.6: medium's 14 -> 22 reads ~22 px a line at 1080p
SIZES = {"12": "19", "13": "21", "14": "22", "16": "26", "18": "29", "20": "32"}
TARGET = ("scripts", "ski_configmenu.pex")


def bsa_file(bsa: bytes, folder: str, name: str) -> bytes:
    """One file of a Skyrim SE (v105) BSA, uncompressed entries only."""
    magic, ver, off, flags, nfold, nfile, lfold, lfile = struct.unpack_from("<4sIIIIIII", bsa, 0)
    if magic != b"BSA\0" or ver != 105:
        raise ValueError(f"not a v105 BSA: {magic!r} {ver}")
    folders = [struct.unpack_from("<QIIQ", bsa, off + 24 * i) for i in range(nfold)]
    pos = off + 24 * nfold
    entries = []
    for _h, count, _p, _o in folders:
        n = bsa[pos]
        fname = bsa[pos + 1:pos + n].decode("latin1").lower()  # bzstring
        pos += 1 + n
        for _ in range(count):
            _fh, size, foff = struct.unpack_from("<QII", bsa, pos)
            entries.append((fname, size, foff))
            pos += 16
    names = bsa[pos:pos + lfile].split(b"\0")
    for (fname, size, foff), fn in zip(entries, names):
        if fname == folder and fn.decode("latin1").lower() == name:
            if bool(size & 0x40000000) != bool(flags & 4):
                raise ValueError(f"{folder}\\{name} is compressed")
            size &= 0x3FFFFFFF
            data = bsa[foff:foff + size]
            if flags & 0x100:  # names embedded before the data
                data = data[1 + data[0]:]
            return data
    raise KeyError(f"{folder}\\{name}")


def _table(pex: bytes) -> tuple[int, int, list[bytes]]:
    if pex[:4] != b"\xfa\x57\xc0\xde":
        raise ValueError("not a pex")
    o = 16
    for _ in range(3):  # source, user, machine
        o += 2 + struct.unpack_from(">H", pex, o)[0]
    start = o
    count = struct.unpack_from(">H", pex, o)[0]
    o += 2
    strs = []
    for _ in range(count):
        n = struct.unpack_from(">H", pex, o)[0]
        strs.append(pex[o + 2:o + 2 + n])
        o += 2 + n
    return start, o, strs


def strings(pex: bytes) -> list[str]:
    return [s.decode("latin1") for s in _table(pex)[2]]


def remap(pex: bytes, mapping: dict[str, str]) -> tuple[bytes, list[str]]:
    """The pex with each string-table entry equal to a key replaced by its value; the keys not found."""
    start, end, strs = _table(pex)
    found = set()
    out = []
    for s in strs:
        t = s.decode("latin1")
        if t in mapping:
            found.add(t)
            s = mapping[t].encode("latin1")
        out.append(struct.pack(">H", len(s)) + s)
    table = struct.pack(">H", len(strs)) + b"".join(out)
    return pex[:start] + table + pex[end:], [k for k in mapping if k not in found]


def write_overlay(mcm_helper_pex: Path, out: Path) -> str:
    """MCM Helper's SKI_ConfigMenu (it replaces SkyUI's and re-applies the sizes on every load, OnGameReload ->
    LoadSettings -> ApplyItemListFontSize); SkyUI's own copy in the BSA applies them only on an option change and
    would drop MCM Helper's page (ui-review4 research)."""
    pex = mcm_helper_pex.read_bytes()
    if "ApplyItemListFontSize" not in strings(pex):
        raise ValueError("SKI_ConfigMenu.pex has no ApplyItemListFontSize: a changed SkyUI")
    new, missing = remap(pex, SIZES)
    if missing:
        raise ValueError(f"SKI_ConfigMenu.pex lacks the size strings {missing}: a changed SkyUI")
    dest = out / TARGET[0] / TARGET[1]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(new)
    return f"{dest}: list font sizes {SIZES}"
