"""The key of each LOD step: what that step truly reads, so a change reruns only the steps it reaches (decision 0037).

    python -m tools.newworld.world.lodkeys [--plugin out/newworld/plugin] [--preset Medium] [--lodmodels <manifest>]
                                       [--esm ArgoniaNewWorld.esm] [--world ArgoniaBlackMarsh]
        -> one JSON object {"terrain-tool": k, "terrain": k, "texgen-tool": k, "texgen": k, "dyndolod": k,
                            "proof": {"terrain": k, "texgen": k, "dyndolod": k}, "parts": {...}}

  terrain-tool  (xLODGen, the long run) reads the world's land and water: from the ESM itself the world record's
            land and water fields, every LAND record, every exterior cell's grid, water height and water type, and
            the land textures (LTEX, TXST); the .lod file; lod-settings.json's terrain.tool; the xLODGen archive.
  terrain   (our pass over it: LODGen again with our mesh settings, the counts, the link into Data) stands on
            terrain-tool and reads lod-settings.json's terrain.post. A change there never reruns xLODGen.
  texgen-tool  (TexGen, the long run) reads the bases a billboard is made for: the billboard files, the ESM's tree
            and static base records (model, bounds, flags); lod-settings.json's texgen.tool; the DynDOLOD and
            Resources archives.
  texgen    (our pass: every planned billboard is there, the link into Data) stands on texgen-tool and reads
            lod-settings.json's texgen.post.
  dyndolod  (DynDOLOD) reads the whole ESM (references and bases), the rule file and billboard files, the derived
            LOD models, and stands on the other two steps' outputs (it culls object LOD under the terrain LOD and
            reads TexGen's textures): every record of the ESM bar what no LOD is made from (the teleport and map
            markers, the cells' names, the world's map box), the plan files, the LOD models' key, both other keys,
            lod-settings.json's "dyndolod" section, the preset, the DynDOLOD and Resources archives.

"proof" is each step's code key: the scripts that drive it, its settings, its tools and what writes its plan
(PROOF). `lod.sh selftest` records it on the machine for each step it ran green on the small world, and
`lod.sh stage` refuses a step whose code key is not the one recorded: the same code was never run on the small
world. A step whose code key stands is not proven again.

lod-settings.json holds each step's settings and a "rev" a change to that step's code in lod.ps1 raises when it
changes what the step writes; lod.ps1's own text is in no key, so a fix to how a window is driven reruns nothing.
The ESM is read raw (TES4 groups walked by size), so a key follows the world file, never a stamp beside it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SETTINGS = REPO / "infra/gpu-box/lod-settings.json"
TOOLS = REPO / "infra/gpu-box/lod-tools.json"
COMPRESSED = 0x00040000
WRLD_SUBS = {b"EDID", b"WNAM", b"PNAM", b"NAM2", b"NAM3", b"NAM4", b"DNAM", b"NAM0", b"NAM9", b"DATA"}  # land, water, bounds
CELL_SUBS = {b"DATA", b"XCLC", b"XCLW", b"XCWT"}  # flags (has water), grid, water height, water type
LAND_TEX = {b"LTEX", b"TXST"}
BASES = {b"STAT", b"TREE"}
# What the map stage writes and no LOD is made from: references to Skyrim.esm's marker bases (COCMarkerHeading 000032,
# MapMarker 000010; Skyrim.esm is every plugin's first master), a cell's editor id, the world's map box.
MARKER_BASES = {0x00000032, 0x00000010}


def _subs(body: bytes):
    o, big = 0, None
    while o + 6 <= len(body):
        sig, ln = body[o:o + 4], struct.unpack_from("<H", body, o + 4)[0]
        if sig == b"XXXX":  # the next subrecord's true size
            big = struct.unpack_from("<I", body, o + 6)[0]
            o += 6 + ln
            continue
        if big is not None:
            ln, big = big, None
        yield sig, body[o + 6:o + 6 + ln]
        o += 6 + ln


def esm_parts(esm: Path) -> dict[str, str]:
    """{"terrain": h, "bases": h, "world": h, "esm": h} of one plugin file: the records each step reads, hashed in
    file order ("world": everything DynDOLOD can read; "esm": the file's own sha, for the record)."""
    hs = {"terrain": hashlib.sha256(), "bases": hashlib.sha256(), "world": hashlib.sha256(), "esm": hashlib.sha256()}

    def world(h: bytes, raw: bytes, drop: set[bytes] | None = None) -> None:
        hs["world"].update(h[:4] + h[8:16])
        if drop is None:
            hs["world"].update(body(h, raw))
            return
        for sig, d in _subs(body(h, raw)):
            if sig not in drop:
                hs["world"].update(sig + struct.pack("<I", len(d)) + d)

    def body(h: bytes, raw: bytes) -> bytes:
        return zlib.decompress(raw[4:]) if struct.unpack_from("<I", h, 8)[0] & COMPRESSED else raw

    def picked(part: str, h: bytes, raw: bytes, keep: set[bytes]) -> None:
        hs[part].update(h[:4] + h[12:16])
        for sig, d in _subs(body(h, raw)):
            if sig in keep:
                hs[part].update(sig + struct.pack("<I", len(d)) + d)

    with open(esm, "rb") as f:
        size = f.seek(0, 2)
        f.seek(0)
        exterior = False
        while f.tell() < size:
            h = f.read(24)
            if len(h) < 24:
                break
            sig, n = h[:4], struct.unpack_from("<I", h, 4)[0]
            if sig == b"GRUP":
                label, kind = h[8:12], struct.unpack_from("<i", h, 12)[0]
                if kind == 0 and label not in (b"WRLD",) + tuple(LAND_TEX | BASES):
                    hs["world"].update(h[:12] + f.read(n - 24))  # a top group read whole: no part of it is keyed alone
                elif kind == 1:
                    exterior = True  # a world's children: its cells are exterior
                continue  # walk into the group
            raw = f.read(n)
            if sig == b"WRLD":
                world(h, raw, {b"MNAM"})
            elif sig == b"CELL":
                world(h, raw, {b"EDID"})
            elif sig == b"REFR":
                name = next((d for s, d in _subs(body(h, raw)) if s == b"NAME"), b"")
                if len(name) != 4 or struct.unpack("<I", name)[0] not in MARKER_BASES:
                    world(h, raw)
            elif sig != b"TES4":
                world(h, raw)
            if sig == b"LAND":
                hs["terrain"].update(body(h, raw))
            elif sig == b"WRLD":
                picked("terrain", h, raw, WRLD_SUBS)
            elif sig == b"CELL" and exterior:
                picked("terrain", h, raw, CELL_SUBS)
            elif sig in LAND_TEX:
                hs["terrain"].update(h[:4] + h[12:16] + body(h, raw))
            elif sig in BASES:
                hs["bases"].update(h[:4] + h[8:16] + body(h, raw))  # the flags too: Has Tree LOD is one
        f.seek(0)
        while chunk := f.read(1 << 22):
            hs["esm"].update(chunk)
    return {k: v.hexdigest() for k, v in hs.items()}


def _sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p if isinstance(p, bytes) else json.dumps(p, sort_keys=True).encode()) + b"\0")
    return h.hexdigest()[:16]


# What each step's code is: the files whose change must be run on the small world before a full run (repo paths).
DRIVERS = ("infra/gpu-box/lod.sh", "infra/gpu-box/lod.ps1", "infra/gpu-box/pscheck.ps1", "tools/newworld/world/lodkeys.py")
PLAN = ("tools/newworld/world/lodplan.py", "tools/newworld/world/lod_models.json", "tools/ArgoniaPlugin/NewWorldMap.cs")
PROOF = {"terrain": (*DRIVERS, "tools/newworld/world/mapdata.py"),
         "texgen": (*DRIVERS, *PLAN),
         "dyndolod": (*DRIVERS, *PLAN, "tools/newworld/world/lodmodels.py", "tools/newworld/niflod/niflod.cpp")}


def proof_keys(settings: dict | None = None, tools: dict | None = None, repo: Path = REPO) -> dict:
    settings = settings or json.loads(SETTINGS.read_text())
    tools = tools or {m["id"]: m["sha256"] for m in json.loads(TOOLS.read_text())["mods"]}
    own = {"terrain": [tools["xlodgen"]], "texgen": [tools["dyndolod"], tools["dyndolod-resources"]],
           "dyndolod": [tools["dyndolod"], tools["dyndolod-resources"]]}
    return {step: _sha("proof", step, [hashlib.sha256((repo / f).read_bytes()).hexdigest() for f in files],
                       settings[step], own[step]) for step, files in PROOF.items()}


def keys(plugin: Path, preset: str = "Medium", lodmodels: str = "", settings: dict | None = None,
         tools: dict | None = None, parts: dict | None = None, esm: str = "ArgoniaNewWorld.esm",
         world: str = "ArgoniaBlackMarsh") -> dict:
    settings = settings or json.loads(SETTINGS.read_text())
    tools = tools or {m["id"]: m["sha256"] for m in json.loads(TOOLS.read_text())["mods"]}
    parts = parts or esm_parts(plugin / esm)
    m = plugin / "map"
    lod = hashlib.sha256((m / "LODSettings" / f"{world}.lod").read_bytes()).hexdigest()
    bills = [(f.name, hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(m.glob("DynDOLOD_SSE_TexGen_Billboards_*.txt"))]
    rules = [(f.name, hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(m.glob("DynDOLOD_SSE_*.ini"))]
    dyn = [tools["dyndolod"], tools["dyndolod-resources"]]
    # a save point inside a step: the long tool run alone, then our own pass over its output
    terrain_tool = _sha("terrain-tool", parts["terrain"], lod, settings["terrain"]["tool"], tools["xlodgen"])
    terrain = _sha("terrain", terrain_tool, settings["terrain"]["post"])
    texgen_tool = _sha("texgen-tool", parts["bases"], bills, settings["texgen"]["tool"], dyn)
    texgen = _sha("texgen", texgen_tool, settings["texgen"]["post"])
    dyndolod = _sha("dyndolod", parts["world"], bills, rules, lodmodels, terrain, texgen, settings["dyndolod"], preset, dyn)
    return {"terrain": terrain, "texgen": texgen, "dyndolod": dyndolod, "terrain-tool": terrain_tool, "texgen-tool": texgen_tool,
            "proof": proof_keys(settings, tools),
            "parts": {**parts, "lod": lod, "billboards": bills, "rules": rules, "lodmodels": lodmodels, "preset": preset}}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    ap.add_argument("--preset", default="Medium")
    ap.add_argument("--lodmodels", default="", help="the derived LOD models' manifest (its key enters dyndolod's)")
    ap.add_argument("--esm", default="ArgoniaNewWorld.esm", help="the world file's name in the plugin folder")
    ap.add_argument("--world", default="ArgoniaBlackMarsh", help="the worldspace (its .lod's name)")
    a = ap.parse_args(argv)
    lm = ""
    if a.lodmodels and Path(a.lodmodels).exists():
        lm = json.loads(Path(a.lodmodels).read_text())["key"]
    print(json.dumps(keys(Path(a.plugin), a.preset, lm, esm=a.esm, world=a.world)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
