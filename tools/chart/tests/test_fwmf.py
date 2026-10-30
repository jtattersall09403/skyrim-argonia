"""L1/L2: the FWMF world-map overlay (fwmf.py) on a synthetic terrain block shaped like FWMF 1.9.990's Tamriel one
(a land chunk, the paper quad, the background quad), and the chart's extent from its cell index."""
import struct

import pytest

from tools.chart import fwmf


def _av(flags=14, t=(0.0, 0.0, 0.0), s=1.0) -> bytes:
    rot = (1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0)
    return struct.pack("<iIi", -1, 0, -1) + struct.pack("<I3f9ff", flags, *t, *rot, s) + struct.pack("<i", -1)


def _texset(path: str) -> bytes:
    tex = [path] + [""] * 8
    return struct.pack("<I", len(tex)) + b"".join(struct.pack("<I", len(x)) + x.encode() for x in tex)


def _nif(blocks: list[tuple[str, bytes]]) -> bytes:
    types = sorted({t for t, _ in blocks})
    h = b"Gamebryo File Format, Version 20.2.0.7\n"
    h += struct.pack("<IBII", 0x14020007, 1, 12, len(blocks)) + struct.pack("<I", 83)
    h += b"\x00\x00\x00"  # author, process and export scripts: empty
    h += struct.pack("<H", len(types)) + b"".join(struct.pack("<I", len(t)) + t.encode() for t in types)
    h += struct.pack(f"<{len(blocks)}H", *(types.index(t) for t, _ in blocks))
    h += struct.pack(f"<{len(blocks)}I", *(len(b) for _, b in blocks))
    h += struct.pack("<II", 0, 0) + struct.pack("<I", 0)  # no strings, no groups
    return h + b"".join(b for _, b in blocks) + struct.pack("<II", 1, 0)


def _tamriel() -> bytes:
    return _nif([("BSMultiBoundNode", _av()),
                 ("NiTriShape", _av(t=(0, 0, 0), s=32.0)), ("BSShaderTextureSet", _texset(r"Data\Textures\Terrain\Tamriel\Tamriel.32.0.0.DDS")),
                 ("NiTriShape", _av(t=(0, 0, fwmf.PAPER_Z), s=0.655)), ("BSShaderTextureSet", _texset(r"textures\terrain\tamriel\skyrim.dds")),
                 ("NiTriShape", _av(t=(0, 0, 162000.0), s=1.675)), ("BSShaderTextureSet", _texset(r"textures\terrain\tamriel\back.dds"))])


def test_block_retargets_the_quads_and_hides_tamriel():
    out, info = fwmf.derive_block(_tamriel(), 4096.0, 4096.0, 262144.0)
    btr = fwmf.Btr(out)  # the header's sizes match the rewritten blocks, or this fails to parse
    shapes = dict(btr.shapes())
    assert shapes[3] == fwmf.TEXTURE.replace("/", "\\") and shapes[5] == fwmf.BACK.replace("/", "\\")
    flags, t, s = btr.transform(3)
    assert not flags & fwmf.HIDDEN and t == (4096.0, 4096.0, fwmf.PAPER_Z) and s == pytest.approx(0.65536)
    assert btr.transform(5)[1] == (4096.0, 4096.0, 162000.0) and btr.transform(5)[2] == pytest.approx(1.675)
    assert btr.transform(1)[0] & fwmf.HIDDEN  # Tamriel's own land chunk never draws on our map
    assert info["hidden_shapes"] == [1]
    assert out.endswith(struct.pack("<II", 1, 0))


def test_a_changed_fwmf_stops_the_install():  # proven on purpose: no paper quad, or one moved, is a stop
    with pytest.raises(fwmf.FwmfChanged):
        fwmf.derive_block(_nif([("NiTriShape", _av()), ("BSShaderTextureSet", _texset("x.dds"))]), 0, 0, 1)
    moved = _tamriel().replace(struct.pack("<f", fwmf.PAPER_Z), struct.pack("<f", 1000.0))
    with pytest.raises(fwmf.FwmfChanged):
        fwmf.derive_block(moved, 0, 0, 1)


def test_extent_from_the_chart_index():
    # the 4096 master: one cell is 32 px, the province's cells -62..63 sit one cell in from each edge
    index = {"size": 4096, "cells": {"-62,63": [0, 0, 32.0, 32.0, 32.0, 32.0], "63,-62": [15, 15, 4032.0, 4032.0, 32.0, 32.0]}}
    cx, cy, half = fwmf.extent(index)
    assert (cx, cy, half) == (4096.0, 4096.0, 262144.0)  # west edge -63 cells, north edge +65 cells, 128 cells a side


def test_markers_whitelist_our_worldspace_only():
    m = fwmf.markers_json()["whiteListedWorldSpaces"]
    assert [w["editorID"] for w in m] == ["ARG_Province"] and m[0]["markerHeight"] == fwmf.MARKER_HEIGHT
