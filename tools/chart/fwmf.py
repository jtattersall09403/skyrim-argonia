"""Flat World Map Framework (FWMF, Nexus 29932) set for ARG_Province: the world map is our parchment chart's sketch
layer (1.2 §e, route 2: a dependency mod set by data). Every output is a derived file, made on the player's machine
(decision 0014; installer/steps/world-map.md) into an overlay mod above FWMF and the terrain LOD; nothing is committed.

FWMF draws a world map as one flat textured quad high above the land in the worldspace's level-32 terrain LOD block
0,0 (its Tamriel file, `meshes/terrain/tamriel/tamriel.32.0.0.btr`), with the map camera raised over it and the map
markers lifted to it by Flat Map Markers. For ARG_Province the overlay holds:
- `meshes/terrain/arg_province/arg_province.32.0.0.btr`, derived from the player's FWMF Tamriel block: its paper
  quad re-centred and re-scaled to the chart's extent and pointed at our texture, its background quad pointed at our
  paper, every other shape (Tamriel's own land and water chunk) hidden;
- `textures/terrain/arg_province/argonia-chart.dds`, the chart's sketch layer (base and ink: the coast, the major
  rivers and roads, the border, the seven cities; no player marker, C9) as DXT1, north up;
- `textures/terrain/arg_province/back.dds`, our dark paper round the chart;
- `SKSE/Plugins/FlatMapMarkersSSE.json`, the marker whitelist: ARG_Province only, at the paper's height.
The map camera (WRLD MNAM) and map offset (ONAM) that FWMF sets on Skyrim's worldspaces ride in Argonia.esm's WRLD
override (regions/api.py reads CAMERA and OFFSET here). The revealed layer stays for our own chart view (1.2 §e full).

    python -m tools.chart fwmf --fwmf <mods>/flat-world-map --out <mods>/argonia-map [--chart out/chart]
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image

from tools.argonia_world import skyrim_units as su
from tools.chart import render

WORLDSPACE = "ARG_Province"  # terrain/world.py's EDID
WS_DIR = WORLDSPACE.lower()
BLOCK = f"meshes/terrain/{WS_DIR}/{WS_DIR}.32.0.0.btr"
TEXTURE = f"textures/terrain/{WS_DIR}/argonia-chart.dds"
BACK = f"textures/terrain/{WS_DIR}/back.dds"
MARKERS = "SKSE/Plugins/FlatMapMarkersSSE.json"
MANIFEST = "argonia-map.json"
CELL_UNITS = float(su.CELL_UNITS)  # one exterior cell, game units (the chart index's cell lattice)

# Measured from FWMF 1.9.990 (FWMF for Fantasy Paper Maps: its Tamriel block, plugin and markers file; 2026-10-30).
FWMF_BLOCK = "meshes/terrain/tamriel/tamriel.32.0.0.btr"
PAPER_TEX = "skyrim.dds"  # the paper quad's texture (the default Skyrim map), by its file name
BACK_TEX = "back.dds"  # the background quad's
QUAD_HALF = 400000.0  # the paper quad's vertices, +-units before its node's scale
PAPER_Z = 180000.0  # the paper quad's node height
CAMERA = (269488.0, 435000.0, 90.0)  # Tamriel's map camera in FWMF's plugin: min, max height, pitch (top-down)
OFFSET = (0.0, 0.0, 0.0, 184072.97)  # Tamriel's ONAM in FWMF's plugin: scale, cell x, y, z offset
MARKER_HEIGHT = 180000  # FlatMapMarkersSSE.json's markerHeight for Tamriel

HIDDEN = 0x1  # NiAVObject flags: APP_CULLED


class FwmfChanged(SystemExit):
    """FWMF's Tamriel block is not what was measured (a new FWMF version): stop the install and report it."""


# ---- the NIF block --------------------------------------------------------------------------------------------------
class Btr:
    """A terrain LOD block (NIF 20.2.0.7) as its header and blocks, enough to retarget FWMF's quads."""

    def __init__(self, b: bytes):
        from tools.navmesh.nif import Nif
        self.nif = Nif(b)
        self.b = b
        n = self.nif
        self.head_end = n.offsets[0] if n.offsets else len(b)
        self.blocks = [bytearray(b[o:o + s]) for o, s in zip(n.offsets, n.sizes)]
        self.tail = b[n.offsets[-1] + n.sizes[-1]:] if n.offsets else b""
        # the block-size table sits right after the block-type index table in the header
        self.sizes_at = self._sizes_offset()

    def _sizes_offset(self) -> int:
        b, n = self.b, len(self.blocks)
        want = struct.pack(f"<{n}I", *self.nif.sizes)
        at = b.find(want, 0, self.head_end)
        if at < 0:
            raise FwmfChanged("FWMF block: the header's block-size table was not found")
        return at

    @property
    def types(self) -> list[str]:
        return self.nif.types

    def shapes(self) -> list[tuple[int, str | None]]:
        """Each NiTriShape and the texture of the texture set that follows it (before the next shape or node)."""
        out, cur = [], None
        for i, t in enumerate(self.types):
            if t == "NiTriShape":
                cur = [i, None]
                out.append(cur)
            elif t.endswith("Node"):
                cur = None
            elif t == "BSShaderTextureSet" and cur is not None and cur[1] is None:
                cur[1] = self.textures(i)[0] if self.textures(i) else None
        return [(i, tex) for i, tex in out]

    def textures(self, i: int) -> list[str]:
        blk = self.blocks[i]
        n = struct.unpack_from("<I", blk, 0)[0]
        o, out = 4, []
        for _ in range(n):
            ln = struct.unpack_from("<I", blk, o)[0]
            out.append(blk[o + 4:o + 4 + ln].decode("latin-1"))
            o += 4 + ln
        return out

    def texture_set_of(self, shape: int) -> int:
        for i in range(shape + 1, len(self.types)):
            if self.types[i] == "BSShaderTextureSet":
                return i
        raise FwmfChanged(f"FWMF block: shape {shape} has no texture set")

    def set_texture(self, i: int, path: str) -> None:
        tex = self.textures(i)
        tex[0] = path
        blk = struct.pack("<I", len(tex)) + b"".join(struct.pack("<I", len(t)) + t.encode("latin-1") for t in tex)
        self.blocks[i] = bytearray(blk)

    # NiObjectNET then NiAVObject: name, extra data list, controller, flags, translation, rotation, scale
    def _av_at(self, i: int) -> int:
        blk = self.blocks[i]
        nex = struct.unpack_from("<I", blk, 4)[0]
        return 4 + 4 + 4 * nex + 4  # the flags field

    def transform(self, i: int) -> tuple[int, tuple[float, float, float], float]:
        o = self._av_at(i)
        blk = self.blocks[i]
        flags = struct.unpack_from("<I", blk, o)[0]
        t = struct.unpack_from("<3f", blk, o + 4)
        s = struct.unpack_from("<f", blk, o + 4 + 12 + 36)[0]
        return flags, t, s

    def set_transform(self, i: int, translation=None, scale=None, hide: bool = False) -> None:
        o = self._av_at(i)
        blk = self.blocks[i]
        if hide:
            struct.pack_into("<I", blk, o, struct.unpack_from("<I", blk, o)[0] | HIDDEN)
        if translation is not None:
            struct.pack_into("<3f", blk, o + 4, *translation)
        if scale is not None:
            struct.pack_into("<f", blk, o + 4 + 12 + 36, scale)

    def tobytes(self) -> bytes:
        head = bytearray(self.b[:self.head_end])
        struct.pack_into(f"<{len(self.blocks)}I", head, self.sizes_at, *(len(x) for x in self.blocks))
        return bytes(head) + b"".join(bytes(x) for x in self.blocks) + self.tail


# ---- the chart's place on the map ---------------------------------------------------------------------------------
def extent(index: dict) -> tuple[float, float, float]:
    """The chart image's centre (x, y) and half side in game units, from the chart index's cell rectangles (each
    cell's [tx, ty, x, y, w, h] in pixels; y down = south)."""
    cells = index["cells"]
    (k0, r0), (k1, _r1) = sorted(cells.items())[0], sorted(cells.items())[-1]
    cx0, cy0 = map(int, k0.split(","))
    cx1, cy1 = map(int, k1.split(","))
    px_per_cell = r0[4]
    if not px_per_cell or (cx0, cy0) == (cx1, cy1):
        raise ValueError("chart index: no cell lattice")
    upx = CELL_UNITS / px_per_cell  # game units per chart pixel
    left = cx0 * CELL_UNITS - r0[2] * upx  # the image's west edge
    top = (cy0 + 1) * CELL_UNITS + r0[3] * upx  # its north edge: cell cy0's north side, r0[3] px below the top
    half = index["size"] * upx / 2
    return left + half, top - half, half


def derive_block(fwmf_btr: bytes, centre_x: float, centre_y: float, half: float) -> tuple[bytes, dict]:
    """Our level-32 block 0,0 from FWMF's Tamriel one: the paper and background quads retargeted, the rest hidden."""
    btr = Btr(fwmf_btr)
    shapes = btr.shapes()
    paper = [i for i, t in shapes if t and t.lower().replace("/", "\\").endswith("\\" + PAPER_TEX)]
    back = [i for i, t in shapes if t and t.lower().replace("/", "\\").endswith("\\" + BACK_TEX)]
    if len(paper) != 1 or len(back) != 1:
        raise FwmfChanged(f"FWMF block: {len(paper)} paper and {len(back)} background quads (measured 1 and 1)")
    p, bk = paper[0], back[0]
    _, (_, _, pz), ps = btr.transform(p)
    if abs(pz - PAPER_Z) > 1 or abs(ps * QUAD_HALF - 262000) > 1000:
        raise FwmfChanged(f"FWMF block: the paper quad stands at z {pz} with scale {ps} (measured {PAPER_Z}, 0.655)")
    _, (_, _, bz), bs = btr.transform(bk)
    btr.set_transform(p, translation=(centre_x, centre_y, PAPER_Z), scale=half / QUAD_HALF)
    btr.set_transform(bk, translation=(centre_x, centre_y, bz), scale=bs)
    btr.set_texture(btr.texture_set_of(p), TEXTURE.replace("/", "\\"))
    btr.set_texture(btr.texture_set_of(bk), BACK.replace("/", "\\"))
    hidden = [i for i, _ in shapes if i not in (p, bk)]
    for i in hidden:
        btr.set_transform(i, hide=True)
    out = btr.tobytes()
    return out, {"paper_shape": p, "background_shape": bk, "hidden_shapes": hidden,
                 "paper": {"centre": [centre_x, centre_y, PAPER_Z], "half_units": half, "scale": half / QUAD_HALF}}


def markers_json() -> dict:
    return {"whiteListedWorldSpaces": [{"name": "Black Marsh", "editorID": WORLDSPACE, "markerHeight": MARKER_HEIGHT,
                                        "enabled": True}]}


def write_dds(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, pixel_format="DXT1")


def dds_header(path: Path) -> dict:
    b = path.read_bytes()[:128]
    if b[:4] != b"DDS ":
        raise ValueError(f"{path}: not a DDS")
    h, w = struct.unpack_from("<II", b, 12)
    return {"width": w, "height": h, "fourcc": b[84:88].decode("latin-1")}


def build(fwmf: Path, chart: Path, out: Path, size: int = render.MASTER) -> dict:
    """The overlay into `out` from the player's FWMF folder and the rendered chart (`python -m tools.chart render`)."""
    src = next((p for p in fwmf.rglob("*.btr") if p.as_posix().lower().endswith(FWMF_BLOCK)), None)
    if src is None:
        raise FwmfChanged(f"{fwmf}: no {FWMF_BLOCK} (FWMF for Fantasy Paper Maps not installed)")
    index = json.loads((chart / "index.json").read_text())
    sketch = chart / f"sketch-{index['size']}.png"
    if not sketch.exists():
        raise SystemExit(f"{sketch}: render the chart first (python -m tools.chart render)")
    cx, cy, half = extent(index)
    block, info = derive_block(src.read_bytes(), cx, cy, half)
    (out / BLOCK).parent.mkdir(parents=True, exist_ok=True)
    (out / BLOCK).write_bytes(block)
    img = Image.open(sketch)
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    write_dds(img, out / TEXTURE)
    write_dds(Image.new("RGB", (256, 256), render.PAPER_DARK), out / BACK)
    (out / MARKERS).parent.mkdir(parents=True, exist_ok=True)
    (out / MARKERS).write_text(json.dumps(markers_json(), indent=1) + "\n")
    report = {"from": str(src), "chart": str(sketch), "block": info,
              "files": sorted([BLOCK, TEXTURE, BACK, MARKERS]),
              "texture": dds_header(out / TEXTURE), "camera": CAMERA, "offset": OFFSET}
    (out / MANIFEST).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return report


def verify(out: Path) -> list[str]:
    """What the next lane checks off-game: the block parses, its paper and background point at ours, the rest hidden."""
    bad = []
    btr = Btr((out / BLOCK).read_bytes())
    for i, tex in btr.shapes():
        flags, t, s = btr.transform(i)
        mine = tex in (TEXTURE.replace("/", "\\"), BACK.replace("/", "\\"))
        if not mine and not flags & HIDDEN:
            bad.append(f"shape {i} ({tex}) is shown: a Tamriel chunk on our map")
    if TEXTURE.replace("/", "\\") not in [t for _, t in btr.shapes()]:
        bad.append("no shape draws the chart")
    h = dds_header(out / TEXTURE)
    if h["fourcc"] != "DXT1" or h["width"] != h["height"]:
        bad.append(f"chart texture {h}")
    if json.loads((out / MARKERS).read_text()) != markers_json():
        bad.append("marker whitelist differs")
    return bad
