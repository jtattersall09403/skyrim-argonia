"""1.12 §4: ArgoniaPerks.esp (tools/argonia_world/perk_plugin.py) overrides exactly the 273 perk_text rows and differs
from the master's record only in FULL and DESC; every number of the vanilla text survives. Needs the player's masters
and the built plugin (skips without them; game data is never committed)."""
import json
import re
import struct
import zlib
from pathlib import Path

import pytest

from tools.argonia_world import db, perk_plugin

REPO = Path(__file__).resolve().parents[3]
ESP = REPO / "out" / "perks" / "argonia-perks" / "ArgoniaPerks.esp"
EXTRACT = REPO / "out" / "perk-text" / "vanilla.json"
NUM = re.compile(r"\d+(?:\.\d+)?")


def perks(path: Path):
    """{(master index-free) local formid: (masters, {sig: [data]})} for every PERK of a plugin."""
    b = path.read_bytes()
    out, masters = {}, []

    def walk(i, end):
        while i < end:
            sig = b[i:i + 4]
            size = struct.unpack_from("<I", b, i + 4)[0]
            if sig == b"GRUP":
                walk(i + 24, i + size)
                i += size
                continue
            flags, fid = struct.unpack_from("<II", b, i + 8)
            body = b[i + 24:i + 24 + size]
            if flags & 0x40000:
                body = zlib.decompress(body[4:])
            if sig == b"TES4":
                masters.extend(d.rstrip(b"\0").decode() for t, d in subs(body) if t == b"MAST")
            elif sig == b"PERK":
                out[fid] = subs(body)
            i += 24 + size

    def subs(body):
        r, j, big = [], 0, None
        while j < len(body):
            t, n = body[j:j + 4], struct.unpack_from("<H", body, j + 4)[0]
            if t == b"XXXX":
                big = struct.unpack_from("<I", body, j + 6)[0]
                j += 10
                continue
            if big is not None:
                n, big = big, None
            r.append((t, body[j + 6:j + 6 + n]))
            j += 6 + n
        return r

    walk(0, len(b))
    return masters, out


@pytest.fixture(scope="module")
def built():
    if not ESP.is_file():
        pytest.skip("no out/perks (python -m tools.argonia_world.perk_plugin --out out/perks/argonia-perks)")
    data = perk_plugin.data_dir()
    if not (data / "Dawnguard.esm").exists():
        pytest.skip("no game masters")
    return data


def test_273_overrides_differing_only_in_full_and_desc(built):
    masters, ours = perks(ESP)
    cache = {m: {k & 0xFFFFFF: v for k, v in perks(built / m)[1].items()} for m in ("Skyrim.esm", "Dawnguard.esm")}
    rows = {r.formkey: r for r in db.open().rows("perk_text")}
    assert len(ours) == len(rows) == 273
    for fk, row in rows.items():
        local, mfile = fk.split(":")
        fid = int(local, 16)
        idx = masters.index(mfile)
        got = ours[(idx << 24) | fid]
        van = cache[mfile][fid]
        # EPF2 is the entry's button label: a string-table id in the master, written inline in an unlocalized plugin
        strip = lambda ss: [(t, d) for t, d in ss if t not in (b"FULL", b"DESC", b"EPF2")]  # noqa: E731
        # master-index bytes inside links differ by plugin; compare everything but FULL/DESC by length and signature
        # Skyrim.esm records are byte-equal; Dawnguard's own links sit at its master index (2, after Update.esm) there
        # and at 1 here, so its records are compared by signature and size
        if mfile == "Skyrim.esm":
            assert strip(got) == strip(van), fk
        else:
            assert [(t, len(d)) for t, d in strip(got)] == [(t, len(d)) for t, d in strip(van)], fk
        text = {t: d.rstrip(b"\0").decode() for t, d in got if t in (b"FULL", b"DESC")}
        assert text[b"FULL"] == row.name and text[b"DESC"] == row.description, fk


def test_numbers_match_vanilla_text(built):
    if not EXTRACT.is_file():
        pytest.skip("no vanilla extract")
    van = {r["formkey"]: r for r in json.loads(EXTRACT.read_text(encoding="utf-8"))}
    masters, ours = perks(ESP)
    for fk, v in van.items():
        local, mfile = fk.split(":")
        got = ours[(masters.index(mfile) << 24) | int(local, 16)]
        desc = next(d for t, d in got if t == b"DESC").rstrip(b"\0").decode()
        assert sorted(NUM.findall(desc)) == sorted(NUM.findall(v["desc"])), fk
