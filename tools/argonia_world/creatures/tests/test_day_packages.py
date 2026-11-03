"""Time of day in the written records (owner #37, 09:23): ArgoniaGen writes each day package as Skyrim's Sandbox
shape with its schedule (PSDT hour, minutes) near the editor location, and each copied creature carries its kind's
packages (PKID, abroad first) with the template's AI packages flag off. L1 on the plugin's bytes; skipped where
the writer, the game data or the laid mods are absent (the build VM and the dev box have them)."""
import json
import struct
import subprocess
import zlib

import pytest

from tools.ArgoniaGen import pipeline
from tools.argonia_world import db
from tools.argonia_world.creatures import records
from tools.argonia_world.terrain import world as tw
from tools.argonia_world.vanilla import load


def test_rest_fills_the_day():
    recs, by = records.day_packages()
    for rule, keys in by.items():
        if rule == "any":
            assert keys == [records.ANY_PACKAGE]
            continue
        hours = sorted((r["schedule"]["hour"] + k) % 24 for r in recs if r["formKey"] in keys
                       for k in range(r["schedule"]["durationHours"]))
        assert hours == list(range(24)), rule  # every hour covered once, abroad or at rest


def _records(blob: bytes, want: set[bytes]):
    out = []

    def walk(i, end):
        while i < end:
            sig, size = blob[i:i + 4], struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                walk(i + 24, i + size)
                i += size
                continue
            fl, fid = struct.unpack_from("<II", blob, i + 8)
            if sig in want:
                b = blob[i + 24:i + 24 + size]
                b = zlib.decompress(b[4:]) if fl & 0x40000 else b
                subs, j = [], 0
                while j + 6 <= len(b):
                    s, n = b[j:j + 4], struct.unpack_from("<H", b, j + 4)[0]
                    subs.append((s, b[j + 6:j + 6 + n]))
                    j += 6 + n
                out.append((sig, fid & 0xFFFFFF, subs))
            i += 24 + size

    walk(struct.unpack_from("<I", blob, 4)[0] + 24, len(blob))
    return out


@pytest.mark.skipif(not pipeline.GEN.exists() or not (load.data_dir() / "Skyrim.esm").exists(),
                    reason="ArgoniaGen or the game data absent")
def test_written_packages_and_actor_links(tmp_path):
    w = db.open()
    try:
        doc = tw.document((0, 0, 0, 0), tmp_path / "land", world=w)
    except (FileNotFoundError, KeyError) as e:
        pytest.skip(f"laid mods absent: {e}")
    (tmp_path / "land").mkdir()
    cr = doc["creatures"]
    day = [a for a in cr["actors"] if len(a["packages"]) == 2][:1] + \
          [a for a in cr["actors"] if a["packages"] == [records.ANY_PACKAGE]][:1]
    cr.update(actors=day, lists=[], templates=[], afflictions=[])
    doc.update(regions=[], cellRegions=[], borderRegion=None, borderCells=[], statics=[], dropAltTextures=[])
    src = tmp_path / "world.json"
    src.write_text(json.dumps(doc))
    out = tmp_path / "ArgoniaWorld.esm"
    subprocess.run([str(pipeline.GEN), "world", "--in", str(src), "--land", str(tmp_path / "land"),
                    "--data", str(load.data_dir()), "--out", str(out)], check=True, capture_output=True, env=pipeline.ENV)
    recs = _records(out.read_bytes(), {b"PACK", b"NPC_"})
    packs = {fid: dict(s) for sig, fid, s in recs if sig == b"PACK"}
    for r in cr["packages"]:
        p = packs[int(r["formKey"].split(":")[0], 16)]
        hour, = struct.unpack_from("<b", p[b"PSDT"], 3)
        mins, = struct.unpack_from("<i", p[b"PSDT"], 8)
        assert (hour, mins) == (r["schedule"]["hour"], r["schedule"]["durationHours"] * 60), r["edid"]
        assert p[b"PKCU"][4:8] == bytes.fromhex("54c20100")  # templated on Skyrim's Sandbox 01C254
    npcs = {fid: s for sig, fid, s in recs if sig == b"NPC_"}
    for a in day:
        s = npcs[int(a["formKey"].split(":")[0], 16)]
        pk = [struct.unpack("<I", b)[0] & 0xFFFFFF for t, b in s if t == b"PKID"]
        assert pk == [int(k.split(":")[0], 16) for k in a["packages"]], a["edid"]
        flags, = struct.unpack_from("<H", dict(s)[b"ACBS"], 22)
        assert not flags & 0x20, f"{a['edid']}: AI packages still from its template"
