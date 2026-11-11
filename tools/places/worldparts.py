"""The world records a place stands on, read from the world file by record: a built place is current against the
world while these are unchanged, whatever else of the file is rewritten.

    python -m tools.places worldparts <place_id> [--json]     what of the world moved under the place's ground bundle
                                                              and under its build; exit 1 when anything did

`read(esm, cells)` walks the file raw (the groups by size, as tools/newworld/world/lodkeys.py does) and returns one
digest per part:

  cells       per cell asked for, by grid: its CELL record whole and every record of its children (LAND, NAVM, each
              placed reference) but the references to the map stage's marker bases (a teleport marker moves no ground)
  bases       the world file's own base records those references name (model, bounds, flags)
  persistent  the references of the world's persistent cell that are no map or teleport marker
  world       the worldspace record but for its map box (MNAM)
  ltex        the land textures and the texture sets they name
  header      the file's masters and description (the land build's id), never its record count
  markers     every map marker of the persistent cell: editor id -> form id (what a travel line links)

`stamp(esm, cells, markers)` is what a tool keeps beside its output: those digests for the cells it read and the
markers it linked, with one key over them. `changed(stamp)` names every part that is no longer the stamp's. A file
rewritten with none of them changed (a map marker moved, the map box set, a far cell re-placed) keeps the key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import threading
import zlib
from pathlib import Path

from tools.newworld.world.lodkeys import COMPRESSED, MARKER_BASES, _subs
from tools.places.bundle import BUNDLES, REPO, sha256_file

WORLD_ESM = REPO / "out" / "newworld" / "plugin" / "ArgoniaNewWorld.esm"
SHARDS = REPO / "out" / "places" / "shards"
CACHE = REPO / "out" / "places" / "cache" / "worldparts.json"
MAP_MARKER = 0x00000010
HEADER_SUBS = {b"CNAM", b"SNAM", b"MAST"}   # author, description, masters: HEDR counts the file's records
PLACED = {b"REFR", b"ACHR", b"PGRE", b"PHZD", b"PMIS", b"PARW", b"PBAR", b"PBEA", b"PCON", b"PFLA"}
NAMES = {"header": "the file's masters or description", "world": "the worldspace record", "ltex": "the land textures",
         "persistent": "the persistent cell's references"}


def _body(h: bytes, raw: bytes) -> bytes:
    return zlib.decompress(raw[4:]) if struct.unpack_from("<I", h, 8)[0] & COMPRESSED else raw


def _records(buf: bytes):
    """Every record of a group's content, its sub-groups walked: (header, raw body)."""
    o = 0
    while o + 24 <= len(buf):
        h = buf[o:o + 24]
        n = struct.unpack_from("<I", h, 4)[0]
        if h[:4] == b"GRUP":
            yield from _records(buf[o + 24:o + n])
            o += n
        else:
            yield h, buf[o + 24:o + 24 + n]
            o += 24 + n


def _sha(*parts: bytes) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.hexdigest()[:16]


def read(esm: Path, cells) -> dict:
    """The parts of one world file for the cells asked ((x, y) grids): see the module's text."""
    want = {(int(x), int(y)) for x, y in cells}
    out = {"header": "", "world": "", "ltex": "", "persistent": "", "cells": {}, "bases": {}, "markers": {}}
    tops: dict[int, tuple[bytes, bytes]] = {}       # the file's own top-level records, by form id
    ltex, named, sets = hashlib.sha256(), set(), {}
    used: set[int] = set()
    pers = hashlib.sha256()

    def persistent(buf: bytes) -> None:
        for rh, raw in _records(buf):
            b = _body(rh, raw)
            sub = dict(_subs(b)) if rh[:4] in PLACED else {}
            base = struct.unpack("<I", sub[b"NAME"])[0] if len(sub.get(b"NAME", b"")) == 4 else None
            if base == MAP_MARKER and sub.get(b"EDID"):
                out["markers"][sub[b"EDID"].rstrip(b"\0").decode("latin-1")] = f"{struct.unpack_from('<I', rh, 12)[0] & 0xFFFFFF:06X}"
            elif base not in MARKER_BASES:
                pers.update(rh[:4] + rh[8:16] + b)
                used.add(base)

    def alone(c) -> None:       # a wanted cell with no children group: its record alone
        if c is not None and c[2] in want:
            out["cells"][f"{c[2][0]},{c[2][1]}"] = _sha(c[0][:4] + c[0][8:16] + c[1])

    masters, top = 0, False
    with open(esm, "rb") as f:
        size = f.seek(0, 2)
        f.seek(0)
        cur: tuple | None = None        # (header, body, grid) of the cell whose children group may follow
        while f.tell() < size:
            h = f.read(24)
            if len(h) < 24:
                break
            sig, n = h[:4], struct.unpack_from("<I", h, 4)[0]
            if sig == b"GRUP":
                label, kind = h[8:12], struct.unpack_from("<i", h, 12)[0]
                if kind == 0 and label != b"WRLD":
                    buf = f.read(n - 24)
                    if label == b"CELL":
                        continue        # interiors: no place stands on them
                    for rh, raw in _records(buf):
                        fid = struct.unpack_from("<I", rh, 12)[0]
                        tops[fid] = (rh, raw)
                        if rh[:4] == b"LTEX":
                            b = _body(rh, raw)
                            ltex.update(rh[:4] + rh[12:16] + b)
                            named.update(struct.unpack("<I", d)[0] for s, d in _subs(b) if s == b"TNAM" and len(d) == 4)
                        elif rh[:4] == b"TXST":
                            sets[fid] = rh[:4] + rh[12:16] + _body(rh, raw)
                elif kind in (1, 4):    # a world's children open on its persistent cell; its blocks hold the rest
                    alone(cur)
                    cur, top = None, kind == 1
                elif kind == 6:         # a cell's children
                    c, cur = cur, None
                    if c is None or struct.unpack("<I", label)[0] != struct.unpack_from("<I", c[0], 12)[0]:
                        alone(c)
                        f.seek(n - 24, 1)
                    elif c[2] is None:
                        persistent(f.read(n - 24))
                    elif c[2] in want:
                        d = hashlib.sha256(c[0][:4] + c[0][8:16] + c[1])
                        for rh, raw in _records(f.read(n - 24)):
                            b = _body(rh, raw)
                            if rh[:4] in PLACED:
                                name = next((v for s, v in _subs(b) if s == b"NAME"), b"")
                                base = struct.unpack("<I", name)[0] if len(name) == 4 else None
                                if base in MARKER_BASES:
                                    continue
                                used.add(base)
                            d.update(rh[:4] + rh[8:16] + b)
                        out["cells"][f"{c[2][0]},{c[2][1]}"] = d.hexdigest()[:16]
                    else:
                        f.seek(n - 24, 1)
                else:
                    alone(cur)
                    cur = None
                continue                # any other group is walked into
            raw = f.read(n)
            alone(cur)
            cur = None
            if sig == b"TES4":
                out["header"] = _sha(*(s + d for s, d in _subs(_body(h, raw)) if s in HEADER_SUBS))
                masters = sum(1 for s, _ in _subs(_body(h, raw)) if s == b"MAST")
            elif sig == b"WRLD":
                out["world"] = _sha(h[:4] + h[8:16], *(s + struct.pack("<I", len(d)) + d for s, d in _subs(_body(h, raw)) if s != b"MNAM"))
            elif sig == b"CELL":
                b = _body(h, raw)
                xclc = next((d for s, d in _subs(b) if s == b"XCLC"), None)
                cur = (h, b, struct.unpack_from("<ii", xclc) if xclc and not top else None)
        alone(cur)
    for fid in sorted(named & set(sets)):
        ltex.update(sets[fid])
    out["ltex"], out["persistent"] = ltex.hexdigest()[:16], pers.hexdigest()[:16]
    for fid in sorted(b for b in used if b is not None and b >> 24 == masters and b in tops):
        rh, raw = tops[fid]
        out["bases"][f"{fid & 0xFFFFFF:06X}"] = _sha(rh[:4] + rh[8:16] + _body(rh, raw))
    return out


# ---- a stamp, kept beside what was read -----------------------------------------------------------------------------

def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(doc: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(doc))
    tmp.replace(CACHE)


def key_of(parts: dict) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def stamp(esm: Path, cells, markers=()) -> dict:
    """{file, sha256, cells, parts, key}: the parts of `esm` for these cells, with only the map markers named (a
    marker the file does not hold is kept as None, so its arrival is seen). The read is remembered by the file's
    size and time, and each file's key by its sha256 (`seen`: a file read here before, the play machine's say)."""
    esm = Path(esm)
    cells = sorted({(int(x), int(y)) for x, y in cells})
    markers = sorted(set(markers))
    st = esm.stat()
    req = hashlib.sha256(json.dumps([cells, markers]).encode()).hexdigest()[:16]
    slot = f"{esm.resolve()}|{req}"
    sig = [st.st_size, st.st_mtime_ns]
    cache = _load_cache()
    hit = cache.get("reads", {}).get(slot)
    if hit and hit["sig"] == sig:
        return hit["stamp"]
    p = read(esm, cells)
    p["markers"] = {m: p["markers"].get(m) for m in markers}
    doc = {"file": esm.name, "sha256": sha256_file(esm), "cells": [list(c) for c in cells], "parts": p, "key": key_of(p)}
    cache = _load_cache()
    cache.setdefault("reads", {})[slot] = {"sig": sig, "stamp": doc}
    seen_ = cache.setdefault("seen", {}).setdefault(req, {})
    seen_[doc["sha256"]] = doc["key"]
    for old in list(seen_)[:-8]:         # the last few files read: the one here, the play machine's, those between
        del seen_[old]
    _save_cache(cache)
    return doc


def again(st: dict, esm: Path = WORLD_ESM) -> dict:
    """The same stamp read from the world file as it now stands."""
    return stamp(esm, st["cells"], st["parts"]["markers"])


def changed(st: dict, esm: Path = WORLD_ESM) -> list[str]:
    """What of the world a stamp stands on is no longer the stamp's, by name; nothing when it is current."""
    now = again(st, esm)
    if now["key"] == st["key"]:
        return []
    a, b = st["parts"], now["parts"]
    out = [NAMES[k] for k in ("header", "world", "ltex", "persistent") if a.get(k) != b.get(k)]
    for part, word in (("cells", "cell"), ("bases", "base record"), ("markers", "map marker")):
        ids = sorted(k for k in a[part].keys() | b[part].keys() if a[part].get(k) != b[part].get(k))
        if ids:
            out.append(f"{len(ids)} {word}{'s' if len(ids) > 1 else ''} ({', '.join(ids[:4])}{', ...' if len(ids) > 4 else ''})")
    return out


def file_holds(st: dict, sha: str) -> bool | None:
    """Whether the world file of this sha256 holds the stamp's parts: True or False when that file was read here
    for the same cells, None when it never was."""
    if sha == st.get("sha256"):
        return True
    req = hashlib.sha256(json.dumps([sorted(tuple(c) for c in st["cells"]), sorted(st["parts"]["markers"])]).encode()).hexdigest()[:16]
    k = _load_cache().get("seen", {}).get(req, {}).get(sha)
    return None if k is None else k == st["key"]


# ---- a place's two stamps --------------------------------------------------------------------------------------------

def ground_stamp(place_id: str, bundles: Path = BUNDLES) -> dict | None:
    """The world stamp of the place's ground bundle (the cells it extracted), or None when it carries none."""
    try:
        return json.loads((bundles / f"ground.{place_id}" / "bundle.json").read_text()).get("world")
    except (OSError, ValueError):
        return None


def build_stamp(place_id: str, shards: Path = SHARDS) -> dict | None:
    """The world stamp of the place's build (the cells its plan read, the markers its travel lines link), or None."""
    try:
        return json.loads((shards / place_id / "world.json").read_text())
    except (OSError, ValueError):
        return None


def stale(place_id: str, esm: Path = WORLD_ESM, bundles: Path = BUNDLES, shards: Path = SHARDS) -> list[str]:
    """Why the built place is not current against the world file, one line a reason; nothing when it is."""
    out = []
    for what, st, fix in (("ground bundle", ground_stamp(place_id, bundles), f"python -m tools.places extract --ground {place_id}"),
                          ("build", build_stamp(place_id, shards), f"python -m tools.places build {place_id}")):
        if st is None:
            out.append(f"its {what} names no world records it stands on: run `{fix}`")
            continue
        ch = changed(st, esm)
        if ch:
            out.append(f"under its {what} the world changed: {'; '.join(ch)}: run `{fix}`")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places worldparts")
    ap.add_argument("place_id")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    why = stale(a.place_id)
    if a.json:
        print(json.dumps({"place_id": a.place_id, "current": not why, "why": why}, indent=2))
    else:
        print(f"{a.place_id}: " + ("current: the world records it stands on are unchanged" if not why else "; ".join(why)))
    return 1 if why else 0
