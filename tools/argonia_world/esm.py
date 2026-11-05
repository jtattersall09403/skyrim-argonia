"""A small read-only reader of Skyrim SE plugin files (TES4 format): records, their subrecords and the group they sit
in. Used by the census (bmv_census.py) to read a mod's own records into rows of our data about it; nothing it reads
is written anywhere but derived values (form keys, editor ids, names, coordinates, links).

    p = esm.Plugin.read(path)
    for rec in p.records("NPC_"): rec.key, rec.edid, rec.sub("FULL")
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

COMPRESSED = 0x00040000
LOCALIZED = 0x80


@dataclass
class Record:
    sig: str
    flags: int
    formid: int
    subs: list[tuple[str, bytes]]
    parents: tuple = ()          # enclosing groups, outermost first: (group type, label int)
    plugin: "Plugin" = field(default=None, repr=False)

    def sub(self, sig: str) -> bytes | None:
        return next((d for s, d in self.subs if s == sig), None)

    def all(self, sig: str) -> list[bytes]:
        return [d for s, d in self.subs if s == sig]

    def zstr(self, sig: str) -> str | None:
        d = self.sub(sig)
        return d.split(b"\0", 1)[0].decode("cp1252") if d else None

    @property
    def edid(self) -> str | None:
        return self.zstr("EDID")

    @property
    def name(self) -> str | None:
        if self.plugin.strings is not None:      # a localized plugin's FULL is a string id
            d = self.sub("FULL")
            return self.plugin.strings.get(struct.unpack_from("<I", d)[0]) or None if d and len(d) == 4 else None
        return self.zstr("FULL") or None

    @property
    def key(self) -> str:
        return self.plugin.form_key(self.formid)

    def ref(self, sig: str, offset: int = 0) -> str | None:
        d = self.sub(sig)
        if not d or len(d) < offset + 4:
            return None
        v = struct.unpack_from("<I", d, offset)[0]
        return self.plugin.form_key(v) if v else None

    @property
    def own(self) -> bool:
        return self.plugin.is_own(self.formid)


class Plugin:
    def __init__(self, name: str, masters: list[str], records: list[Record]):
        self.name, self.masters, self._records = name, masters, records
        self.strings: dict[int, str] | None = None

    def form_key(self, formid: int) -> str:
        idx = formid >> 24
        owner = self.masters[idx] if idx < len(self.masters) else self.name
        return f"{formid & 0xFFFFFF:06X}:{owner}"

    def is_own(self, formid: int) -> bool:
        return (formid >> 24) >= len(self.masters)

    def records(self, sig: str | None = None) -> list[Record]:
        return [r for r in self._records if sig is None or r.sig == sig]

    @classmethod
    def read(cls, path: Path | str, sigs: set[str] | None = None) -> "Plugin":
        """Every record, or only those under the top-level groups of `sigs` (a fast read of a large master)."""
        data = Path(path).read_bytes()
        p = cls(Path(path).name, [], [])
        hdr = _record(data, 0)
        p.masters = [d.split(b"\0", 1)[0].decode("cp1252") for s, d in hdr.subs if s == "MAST"]
        if hdr.flags & LOCALIZED:
            p.strings = strings(Path(path), p.name)
        off = 24 + struct.unpack_from("<I", data, 4)[0]
        p._walk(data, off, len(data), (), sigs)
        return p

    def _walk(self, data: bytes, off: int, end: int, parents: tuple, sigs: set[str] | None = None) -> None:
        while off < end:
            sig = data[off:off + 4].decode("ascii")
            size = struct.unpack_from("<I", data, off + 4)[0]
            if sig == "GRUP":
                label = struct.unpack_from("<I", data, off + 8)[0]
                gtype = struct.unpack_from("<i", data, off + 12)[0]
                if sigs is not None and not parents and data[off + 8:off + 12].decode("ascii") not in sigs:
                    off += size
                    continue
                self._walk(data, off + 24, off + size, parents + ((gtype, label),))
                off += size
            else:
                rec = _record(data, off)
                rec.parents, rec.plugin = parents, self
                self._records.append(rec)
                off += 24 + size


def _record(data: bytes, off: int) -> Record:
    sig = data[off:off + 4].decode("ascii")
    size, flags, formid = struct.unpack_from("<III", data, off + 4)
    body = data[off + 24: off + 24 + size]
    if flags & COMPRESSED:
        body = zlib.decompress(body[4:])
    return Record(sig, flags, formid, _subs(body))


def _subs(body: bytes) -> list[tuple[str, bytes]]:
    out, i, big = [], 0, None
    while i + 6 <= len(body):
        s = body[i:i + 4].decode("ascii", "replace")
        n = struct.unpack_from("<H", body, i + 4)[0]
        if s == "XXXX":
            big = struct.unpack_from("<I", body, i + 6)[0]
            i += 6 + n
            continue
        if big is not None:
            n, big = big, None
        out.append((s, body[i + 6:i + 6 + n]))
        i += 6 + n
    return out


def strings(path: Path, plugin: str, lang: str = "english") -> dict[int, str]:
    """A localized plugin's .STRINGS table: loose in Data/Strings, else in an uncompressed SE archive beside it
    (Skyrim - Interface.bsa holds the base game's)."""
    want = f"{Path(plugin).stem}_{lang}.strings".lower()
    loose = path.parent / "Strings" / want
    if loose.exists():
        return _parse_strings(loose.read_bytes())
    for bsa in sorted(path.parent.glob("*.bsa")):
        data = _bsa_file(bsa, want)
        if data is not None:
            return _parse_strings(data)
    return {}


def _parse_strings(d: bytes) -> dict[int, str]:
    n, _size = struct.unpack_from("<II", d)
    base = 8 + 8 * n
    out = {}
    for i in range(n):
        sid, off = struct.unpack_from("<II", d, 8 + 8 * i)
        out[sid] = d[base + off: d.index(b"\0", base + off)].decode("cp1252", "replace")
    return out


def _bsa_file(bsa: Path, want: str) -> bytes | None:
    """One file of a version-105 archive, by name, when the archive stores it uncompressed."""
    with bsa.open("rb") as f:
        h = f.read(36)
        if h[:4] != b"BSA\0" or struct.unpack_from("<I", h, 4)[0] != 105:
            return None
        _, _, _, flags, nfold, _nfile, _lfold, lfile, _ = struct.unpack("<4sIIIIIIII", h)
        counts = [struct.unpack("<QIIQ", f.read(24))[1] for _ in range(nfold)]
        entries = []
        for cnt in counts:
            f.read(f.read(1)[0])
            entries += [struct.unpack("<QII", f.read(16))[1:] for _ in range(cnt)]
        names = f.read(lfile).split(b"\0")
        for (size, off), nm in zip(entries, names):
            if nm.decode("cp1252").lower() == want:
                compressed = bool(flags & 4) != bool(size & 0x40000000)
                if compressed or flags & 0x100:
                    return None
                f.seek(off)
                return f.read(size & 0x3FFFFFFF)
    return None
