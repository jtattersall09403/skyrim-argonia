"""A minimal reader of a written plugin's records, for the writer test and the stills (no game data; stdlib only).

Walks the GRUP tree, inflates compressed records (flag 0x40000: a uint32 size then zlib) and splits subrecords
(4-byte type, uint16 size; an XXXX subrecord carries the next one's uint32 size).
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field

COMPRESSED = 0x40000


@dataclass
class Record:
    sig: str
    flags: int
    formid: int
    subs: list[tuple[str, bytes]] = field(default_factory=list)

    def first(self, sig: str) -> bytes | None:
        return next((b for s, b in self.subs if s == sig), None)


def _subrecords(data: bytes) -> list[tuple[str, bytes]]:
    out, i, big = [], 0, None
    while i < len(data):
        sig = data[i:i + 4].decode("ascii")
        size = struct.unpack_from("<H", data, i + 4)[0]
        i += 6
        if sig == "XXXX":
            big = struct.unpack_from("<I", data, i)[0]
            i += size
            continue
        if big is not None:
            size, big = big, None
        out.append((sig, data[i:i + size]))
        i += size
    return out


def records(blob: bytes):
    """Yield every record (TES4 included) in file order."""
    def walk(i: int, end: int):
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                yield from walk(i + 24, i + size)
                i += size
                continue
            flags, formid = struct.unpack_from("<II", blob, i + 8)
            body = blob[i + 24:i + 24 + size]
            if flags & COMPRESSED:
                body = zlib.decompress(body[4:])
            yield Record(sig.decode("ascii"), flags, formid, _subrecords(body))
            i += 24 + size
    yield from walk(0, len(blob))
