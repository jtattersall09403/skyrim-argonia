"""A base's alternate textures (its model's MODS): which shapes of the model the game draws with another texture set,
and which it does not draw at all. A dead Hist of King of the Murkmire is its living tree's model with the leaf
shapes' texture set pointed at a form no plugin holds, so the game shows bare branches; the studio hides those
shapes the same way (studio/web/js/objects.js loadModel `hide`).

    hidden_shapes(key) -> [shape name, ...]   the shapes whose alternate texture set resolves to no record

Read straight from the plugin (a small record walk, cached per plugin), found as the extractor finds plugins."""
from __future__ import annotations

import struct
import zlib
from functools import lru_cache
from pathlib import Path

GRUP = b"GRUP"


@lru_cache(maxsize=None)
def _index(path: str) -> tuple[list[str], dict[int, tuple[bytes, int, int, int]]]:
    """(masters, {local form id: (signature, offset, size, flags)}) of one plugin."""
    data = Path(path).read_bytes()
    hsize = struct.unpack_from("<I", data, 4)[0]
    masters, head = [], data[24:24 + hsize]
    q = 0
    while q < len(head):
        sig, n = head[q:q + 4], struct.unpack_from("<H", head, q + 4)[0]
        if sig == b"MAST":
            masters.append(head[q + 6:q + 6 + n].rstrip(b"\0").decode("latin1"))
        q += 6 + n
    idx: dict[int, tuple[bytes, int, int, int]] = {}

    def walk(off: int, end: int):
        while off < end:
            sig, size = data[off:off + 4], struct.unpack_from("<I", data, off + 4)[0]
            if sig == GRUP:
                walk(off + 24, off + size)
                off += size
                continue
            flags, fid = struct.unpack_from("<II", data, off + 8)
            idx[fid] = (sig, off, size, flags)
            off += 24 + size
    walk(24 + hsize, len(data))
    return masters, idx


def _fields(path: str, fid: int) -> list[tuple[bytes, bytes]]:
    _, idx = _index(path)
    hit = idx.get(fid)
    if not hit:
        return []
    _, off, size, flags = hit
    data = Path(path).read_bytes()
    body = data[off + 24: off + 24 + size]
    if flags & 0x40000:
        body = zlib.decompress(body[4:])
    out, p = [], 0
    while p < len(body):
        sig, n = body[p:p + 4], struct.unpack_from("<H", body, p + 4)[0]
        out.append((sig, body[p + 6:p + 6 + n]))
        p += 6 + n
    return out


def parse_mods(v: bytes) -> list[tuple[str, int]]:
    """A MODS field: [(3D shape name, texture set form id as stored)]."""
    n = struct.unpack_from("<I", v, 0)[0]
    p, out = 4, []
    for _ in range(n):
        ln = struct.unpack_from("<I", v, p)[0]
        name = v[p + 4:p + 4 + ln].rstrip(b"\0").decode("latin1")
        fid = struct.unpack_from("<I", v, p + 4 + ln)[0]
        out.append((name, fid))
        p += 4 + ln + 8
    return out


def _find(name: str) -> str | None:
    from tools.places import extract
    try:
        return str(extract.find_plugin(name, extract.search_dirs()))
    except FileNotFoundError:
        return None


def _resolves(plugin: str, masters: list[str], fid: int) -> bool:
    """A stored form id resolves to a texture set: its owner (a master by index, else the plugin) holds the record."""
    i = fid >> 24
    owner = masters[i] if i < len(masters) else plugin
    path = _find(owner)
    if not path:
        return True   # a plugin we cannot read: assume it holds it (never hide on a guess)
    _, idx = _index(path)
    hit = idx.get(fid & 0xFFFFFF) or next((v for k, v in idx.items() if k & 0xFFFFFF == fid & 0xFFFFFF), None)
    return bool(hit and hit[0] == b"TXST")


def hidden_shapes(key: str) -> list[str]:
    """The shapes of a base's model the game does not draw: those its MODS points at a texture set no plugin holds."""
    plugin, _, local = key.partition(":")
    path = _find(plugin)
    if not path or not local:
        return []
    masters, idx = _index(path)
    want = int(local, 16)
    fid = next((k for k in idx if k & 0xFFFFFF == want and (k >> 24) == len(masters)), None)
    fid = fid if fid is not None else next((k for k in idx if k & 0xFFFFFF == want), None)
    if fid is None:
        return []
    out = []
    for sig, v in _fields(path, fid):
        if sig == b"MODS":
            out += [name for name, tid in parse_mods(v) if not _resolves(plugin, masters, tid)]
    return out
