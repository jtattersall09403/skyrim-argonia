"""The new world's off-game read-back (nw-02 step 12): every owner requirement checked with a number, on the files the
game consumes, and a PASS/FAIL table.

    python3 -m tools.newworld.verify [--plugin out/newworld/plugin] [--out out/newworld/verify] [--no-dump]
    tooling/job_guard.sh run nw-verify -- python3 -m tools.newworld.verify      (about 3 min on the full world)

Read: ArgoniaNewWorld.esm (through `ArgoniaPlugin nwverify dump`: masters, links, cells, LAND, layers, water, regions,
climate, navmesh, every placed object with the LAND's ground under it), the NewWorld profile's laid-file record
(~/.argonia/stack/installed-NewWorld.json) and its mods and archives (models and textures resolve), the LOD listing
fetched from the play machine (out/newworld/lod/files.txt), the .lod settings and the map data. The intent the files
are judged against: the land manifest's grid, cells.json (water kind and region per cell), water_flow_cells.json
(cells where water flows), margin_cells.json, the road and landcover rasters (through the placement checks, run over
the refs read back from the ESM, not over the placer's shards) and the navmesh build's check.json (seams,
connectivity, settlement paths).

Out: <out>/report.md (the table), <out>/report.json, <out>/dump/ (the ESM facts), <out>/refs/check.json. Exit 1 when
any row FAILs. A row that cannot be measured is a FAIL naming what is missing, never a crash.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "out/newworld"
STACK = Path(os.environ.get("ARGONIA_STACK") or Path.home() / ".argonia/stack")
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
BIN = REPO / "out/tools/ArgoniaPlugin-verify"
MASTERS = ["Skyrim.esm", "Update.esm", "Black Marsh.esm"]
ESM = "ArgoniaNewWorld.esm"
MARKERS = 116
GRASS_SHARE_MIN = 0.80   # land quadrants (mean height above water) with a grass-bearing texture layer
REFS_CAP = 162           # natural refs in a cell: vanilla's forested max
JACCARD_MAX = 0.60       # two regions' base sets: the most they may share (the place step reports 0.58, two sea regions)
PATHS_MIN = 20           # settlement-pair paths the navmesh check must have found
FLOW = re.compile(r"(River|Creek)WaterFlow", re.I)
BLEND = re.compile(r"^ANW_WaterBlend_(.+)_\d{4}$")    # a graded seam cell: its own type's editor id, look mixed


def own_type(edid: str) -> str:
    """A cell's water type as its kind and flow: a blend record (ArgoniaPlugin WaterBlend.cs) counts as its own type."""
    m = BLEND.match(edid or "")
    return m.group(1) if m else edid
MIST = re.compile(r"^FXMist", re.I)


class Report:
    def __init__(self):
        self.rows: list[dict] = []

    def row(self, area: str, req: str, value, ok: bool | None, detail: str = ""):
        self.rows.append({"area": area, "requirement": req, "value": value,
                          "result": "PASS" if ok else "FAIL", "detail": detail})

    def fail(self, area: str, req: str, missing: str):
        self.row(area, req, "-", False, missing)

    def md(self) -> str:
        n = Counter(r["result"] for r in self.rows)
        out = [f"# New world read-back ({time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC)", "",
               f"{n['PASS']} PASS, {n['FAIL']} FAIL of {len(self.rows)}.", "",
               "| Area | Requirement | Value | Result | Detail |", "|---|---|---|---|---|"]
        for r in self.rows:
            v = json.dumps(r["value"]) if not isinstance(r["value"], str) else r["value"]
            out.append(f"| {r['area']} | {r['requirement']} | {v} | **{r['result']}** | {r['detail'].replace('|', '/')} |")
        return "\n".join(out) + "\n"


def section(rep: Report, area: str):
    """Run one group of checks; an exception becomes a FAIL row naming it, never a crash."""
    def wrap(fn):
        try:
            fn()
        except BaseException as e:  # SystemExit from a reused tool included
            if isinstance(e, KeyboardInterrupt):
                raise
            rep.fail(area, "(group could not run)", f"{type(e).__name__}: {str(e)[:300]}")
            traceback.print_exc()
        return fn
    return wrap


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# ---- the ESM facts

def dump(plugin: Path, out: Path) -> None:
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    env["PATH"] = f"{Path.home() / '.dotnet'}:{env['PATH']}"
    subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(BIN), str(REPO / "tools/ArgoniaPlugin"), "-v", "q", "-nologo"],
                   check=True, env=env, capture_output=True)
    subprocess.run(["dotnet", str(BIN / "ArgoniaPlugin.dll"), "nwverify", "dump", str(plugin / ESM), str(DATA), str(out / "dump")],
                   check=True, env=env)


def read_cells(d: Path) -> dict:
    with open(d / "cells.tsv", newline="") as f:
        return {(int(r["x"]), int(r["y"])): r for r in csv.DictReader(f, delimiter="\t")}


def read_refs(d: Path) -> list[dict]:
    with gzip.open(d / "refs.tsv.gz", "rt", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ---- resolution in the NewWorld profile

class Assets:
    """Every file the NewWorld profile lays (installed-NewWorld.json) plus every archive it loads, lower-case keys."""

    def __init__(self):
        from tools.navmesh import bsa
        rec = STACK / "installed-NewWorld.json"
        self.record = jload(rec) if rec.exists() else None
        self.loose = set(self.record["files"]) if self.record else set()
        self.archived: set[str] = set()
        mods = STACK / "MO2/mods"
        ml = STACK / "MO2/profiles/NewWorld/modlist.txt"
        order = [ln[1:].strip() for ln in ml.read_text(errors="replace").splitlines() if ln.startswith("+")] if ml.exists() else []
        paths = [p for m in order for p in sorted((mods / m).glob("*.bsa"))] + sorted(DATA.glob("*.bsa"))
        for p in paths:
            try:
                self.archived |= set(bsa.Archive(bsa.local(p)).files)
            except (ValueError, OSError):
                continue
        for m in order:  # loose files of mods not in the record (hand-laid asset folders)
            root = mods / m
            if root.is_dir() and not self.record:
                self.loose |= {str(f.relative_to(root)).lower().replace("/", "\\") for f in root.rglob("*") if f.is_file()}

    def has(self, path: str) -> bool:
        k = path.replace("/", "\\").lower().lstrip("\\")
        return k in self.loose or k.replace("\\", "/") in self.archived


MESHES = re.compile(r"^[\\/]?meshes[\\/]", re.I)


def nif_textures(raw: bytes) -> set[str]:
    return {m.decode("latin-1").lower().replace("/", "\\") for m in re.findall(rb"[\x21-\x7e][\x20-\x7e]{2,}\.dds", raw, re.I)}


# ---- the checks

def run(plugin: Path, out: Path, do_dump: bool = True) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    rep = Report()
    d = out / "dump"
    if not (plugin / ESM).exists():
        rep.fail("plugin", "ArgoniaNewWorld.esm built", f"{plugin / ESM} missing: run tools/newworld/world/world.sh")
        return finish(rep, out, t0)
    if do_dump:
        try:
            dump(plugin, out)
        except subprocess.CalledProcessError as e:
            rep.fail("plugin", "ESM loads in Mutagen", f"nwverify dump failed (exit {e.returncode}); see the log")
            return finish(rep, out, t0)
    H = jload(d / "header.json")
    cells = read_cells(d)
    refs = read_refs(d)
    man = jload(plugin / "land/manifest.json")
    g = man["grid"]
    water_h = g.get("water", 0)
    intent = jload(plugin / "cells.json") if (plugin / "cells.json").exists() else None
    land = {k for k, c in cells.items() if c["h_max"] and float(c["h_max"]) > water_h}
    placed = [r for r in refs if r["edid"] != "MapMarker"]
    mist = [r for r in placed if MIST.match(r["edid"] or "")]
    natural = [r for r in placed if not MIST.match(r["edid"] or "")]

    @section(rep, "plugin")
    def _plugin():
        rep.row("plugin", "ESM loads in Mutagen with 0 errors", len(H["errors"]), not H["errors"], "; ".join(H["errors"][:3]))
        rep.row("plugin", "ESM flag set", H["esm_flag"], H["esm_flag"])
        m = H["masters"]
        extra, miss = [x for x in m if x not in MASTERS], [x for x in MASTERS if x not in m]
        rep.row("plugin", "masters are Skyrim.esm, Update.esm, Black Marsh.esm only", m, not extra and not miss,
                (f"extra {extra} " if extra else "") + (f"missing {miss}" if miss else ""))
        rep.row("plugin", "no link into KotM/TS/Depths or any non-master", H["foreign_links"], H["foreign_links"] == 0,
                "; ".join(H["foreign_examples"][:3]))
        rep.row("plugin", "every link resolves in the masters or ours", H["unresolved_links"], H["unresolved_links"] == 0,
                "; ".join(H["unresolved_examples"][:3]))

    @section(rep, "land")
    def _land():
        exp = {(x, y) for y in range(g["cy_bottom"], g["cy_top"] + 1) for x in range(g["cx0"], g["cx1"] + 1)}
        have = {k for k, c in cells.items() if c["land"] == "1"}
        miss = sorted(exp - have)
        rep.row("land", "every cell of the grid has LAND", f"{len(have & exp)}/{len(exp)}", not miss,
                f"missing e.g. {miss[:5]}" if miss else "")

    @section(rep, "textures")
    def _tex():
        lt = H["ltex"]
        rep.row("textures", "ground textures (LTEX) in the ESM", len(lt), len(lt) > 1,
                "" if len(lt) > 1 else "no LTEX of ours: the ground paint (world/texture.py) is not written into the ESM yet")
        if lt:
            A = assets()
            def tex_path(d):  # the dump gives the data-relative path ("Textures/..."), the TXST field omits it
                d = d.replace("/", "\\")
                return d if d.lower().startswith("textures\\") else "textures\\" + d
            bad = [t["edid"] for t in lt if not t["diffuse"] or not A.has(tex_path(t["diffuse"]))]
            rep.row("textures", "every LTEX diffuse resolves in the NewWorld profile", len(bad), not bad, f"e.g. {bad[:5]}")
        lq = sum(int(c["land_quads"] or 0) for c in cells.values())
        gq = sum(int(c["grass_quads"] or 0) for c in cells.values())
        share = round(gq / lq, 3) if lq else 0.0
        rep.row("textures", f"GRAS coverage: land quadrants with a grass-bearing layer >= {GRASS_SHARE_MIN}", share,
                share >= GRASS_SHARE_MIN, f"{gq}/{lq} quadrants; {sum(1 for t in lt if t['grasses'])} LTEX carry GRAS")
        from tools.newworld.world import texcheck
        if not (plugin / "tex/manifest.json").exists():
            rep.fail("textures", "texture edge and swathe metrics", "out/newworld/plugin/tex/manifest.json missing: run world/texture.py")
            return
        tc = texcheck.check(plugin)
        (out / "texcheck.json").write_text(json.dumps(tc, indent=1, default=str))
        edge = {k: v for k, v in tc.items() if "step" in k or "edge" in k}
        rep.row("textures", "edge metric (blend step p99 <= 0.41, max <= 0.75, seam <= 3/255)", edge,
                bool(tc.get("pass")), "texcheck.check over the painted shards the ESM was written from")
        rep.row("textures", "swathe metric (one material's share of any 1 km of land <= 0.40)", tc.get("swathe_max_1km_land"),
                tc.get("swathe_max_1km_land") is not None and tc["swathe_max_1km_land"] <= 0.40,
                f"{tc.get('swathe_material')} at {tc.get('swathe_at_cell')}")

    @section(rep, "water")
    def _water():
        if intent is None:
            rep.fail("water", "every water cell's WATR matches its kind", "cells.json missing: run world/cells.py")
            return
        watr = intent["watr"]
        want_ed = {k: (v.get("edid") or v.get("link", "").split(":", 1)[-1]) for k, v in watr.items()}
        world_w = H.get("world", {}).get("water")
        bad, n, ex = 0, 0, []
        for key, c in intent["cells"].items():
            w = c.get("water")
            if not w:
                continue
            x, y = map(int, key.split(","))
            got = own_type((cells.get((x, y)) or {}).get("water") or f"(world) {world_w}")
            n += 1
            if got != want_ed[w]:
                bad += 1
                if len(ex) < 3:
                    ex.append(f"{key} {w}: {got}")
        rep.row("water", "every water cell's WATR matches its kind", f"{n - bad}/{n}", n > 0 and bad == 0,
                ("; ".join(ex) + (" (no XCWT written: cells fall back to the world's water)" if bad == n else "")) if bad else "")
        flow_cells = {tuple(c["cell"]) for c in jload(OUT / "water_flow_cells.json")}
        wrong = [k for k, c in cells.items() if FLOW.search(c["water"] or "") and k not in flow_cells]
        nflow = sum(1 for c in cells.values() if FLOW.search(c["water"] or ""))
        rep.row("water", "flowing water types only in cells where water flows", f"{len(wrong)} of {nflow} flowing cells",
                nflow > 0 and not wrong, f"e.g. {wrong[:4]}" if wrong else ("no flowing WATR in the ESM" if not nflow else ""))
        hw = [k for k, c in cells.items() if c["water_h"] not in ("", str(water_h), f"{water_h}", "0")]
        rep.row("water", f"one water level ({water_h}) everywhere", len(hw), not hw, f"e.g. {hw[:4]}")
        from tools.newworld.world import water_check  # kinds as seen, flow, seams, land against the plane
        water_check.rows(rep, water_check.esm_check(BIN / "ArgoniaPlugin.dll", plugin, DATA, OUT / "water_flow_cells.json", out),
                         water_check.shore(plugin))

    @section(rep, "refs")
    def _refs():
        if not natural:
            rep.fail("refs", "placed trees, plants, rocks, cliffs, road dressing",
                     f"0 placed objects in the ESM ({len(refs)} map markers or markers only): the step 8 refs are not written yet")
            return
        rep.row("refs", "placed objects in the ESM", len(natural), True, ", ".join(f"{k} {v}" for k, v in Counter(r["sig"] for r in natural).most_common(5)))
        unk = [r for r in natural if not r["sig"]]
        rep.row("refs", "every ref's base record resolves", len(unk), not unk, f"e.g. {unk[0]['base']}" if unk else "")
        A = assets()
        from tools.navmesh import meshes
        meshes.PROFILE = "NewWorld"
        rv = meshes.Resolver(DATA, STACK / "MO2")
        models = sorted({MESHES.sub("", r["model"]) for r in placed if r["model"]})  # the dump keeps the data-relative Meshes/
        nomodel = [m for m in models if rv.where(m) is None]
        rep.row("refs", "every ref's base model resolves in the NewWorld profile", f"{len(models) - len(nomodel)}/{len(models)}",
                not nomodel, f"missing e.g. {nomodel[:4]}")
        # only a missing diffuse shows purple: it fails unless the placer's alternate-texture repair covers the shape
        # (bases.json alt_textures, written onto our copy as MODS + TXST); other missing slots are a warning count
        from tools.newworld.place import place as P, texsets
        src = P.REFS / "bases.json"
        fixed = {(MESHES.sub("", b["model"]).lower().replace("/", "\\"), a["shape"]) for b in (jload(src)["bases"] if src.exists() else [])
                 for a in b.get("alt_textures", []) if a["slots"][0]}
        audit = texsets.Audit(A, P.mod_textures)
        notex, other = Counter(), 0
        for m in models:
            raw = rv.read(m) if m not in nomodel else None
            a = audit.model(raw or b"", P.model_mod(rv, m))
            other += len(a["missing_other"])
            for d in a["missing_diffuse"]:
                notex[d["path"]] += 1
            for r in a["repairs"]:
                if r["slots"][0] and (m.lower().replace("/", "\\"), r["shape"]) not in fixed:
                    notex[r["from"][0]] += 1
        rep.row("refs", "every model's diffuse textures resolve in the NewWorld profile (alt textures applied)", len(notex), not notex,
                f"missing e.g. {list(notex)[:4]}; " * bool(notex) + f"warning: {other} non-diffuse slots missing")
        place_rows(rep, natural, out)

    @section(rep, "mist")
    def _mist():
        if not mist:
            rep.fail("mist", "mist refs over marsh and inland water", "0 FXMist refs in the ESM: the mist refs (refs/mist) are not written yet")
            return
        kinds = {k: c.get("water") for k, c in intent["cells"].items()} if intent else {}
        at_sea = [r for r in mist if kinds.get(f"{r['cx']},{r['cy']}") == "sea" and float(r["ground"]) < water_h]
        rep.row("mist", "mist refs in marsh and inland water", len(mist), len(mist) > 0)
        rep.row("mist", "no mist over the sea", len(at_sea), not at_sea, f"e.g. cell {at_sea[0]['cx']},{at_sea[0]['cy']}" if at_sea else "")
        from tools.newworld.world import mist as mist_rows  # density by water kind and class, strength, height, budget
        for req, v, ok, det in mist_rows.rows(mist, natural, intent["cells"] if intent else {}):
            rep.row("mist", req, v, ok, det)

    @section(rep, "atmosphere")
    def _atmo():
        w = H.get("world") or {}
        cw = w.get("climate_weathers") or []
        rep.row("atmosphere", "the world's climate has weathers", f"{w.get('climate')}: {len(cw)}", bool(cw))
        regs = H["regions"]
        want = len(intent["regions"]) if intent else None
        rep.row("atmosphere", "REGN per research region", f"{len(regs)}/{want}", bool(regs) and len(regs) == want,
                "" if regs else "no REGN in the ESM yet (world/cells.py regions not written)")
        noweather = [r["edid"] for r in regs if not r["weathers"]]
        if regs:
            rep.row("atmosphere", "every REGN has a weather list", len(noweather), not noweather, f"e.g. {noweather[:3]}")
        nreg = [k for k, c in cells.items() if not c["region"]]
        rep.row("atmosphere", "every cell links a region", f"{len(cells) - len(nreg)}/{len(cells)}", not nreg)
        from tools.newworld import atmosphere  # our weathers read back: fields, region lists, climate, distinct, warm
        for req, v, ok, det in atmosphere.rows(plugin):
            rep.row("atmosphere", req, v, ok, det)

    @section(rep, "navmesh")
    def _nav():
        # margin_cells.json and scope_cells.json are in map cells (8192 units, two Skyrim cells a side)
        margin = {tuple(c) for c in jload(OUT / "margin_cells.json")}
        scope = {tuple(c) for c in jload(OUT / "scope_cells.json")}
        need = sorted(k for k in land if (k[0] // 2, k[1] // 2) in scope and (k[0] // 2, k[1] // 2) not in margin)
        miss = [k for k in need if int(cells[k]["navm"] or 0) == 0]
        rep.row("navmesh", "NAVM on every non-margin land cell", f"{len(need) - len(miss)}/{len(need)}", not miss,
                f"missing e.g. {miss[:4]}" if miss else "")
        rep.row("navmesh", "NAVI entries", H["navi"], H["navi"] > 0)
        cj = plugin / "navmesh/check.json"
        if not cj.exists():
            rep.fail("navmesh", "0 seam faults; connectivity; settlement paths", f"{cj.relative_to(REPO)} missing: the full navmesh run is owed")
            return
        c = jload(cj)
        p = c.get("province", {})
        s = p.get("seams", {})
        rep.row("navmesh", "0 seam faults", s.get("mismatched", 0) + s.get("unmatched_segments", 0),
                s.get("mismatched", 0) + s.get("unmatched_segments", 0) == 0)
        comp = p.get("components", {})
        # islands across water cannot join the main component; the share is of the main landmass's walkable area
        main_m2, cut_m2 = comp.get("main_m2") or 0, comp.get("cut_off_m2") or 0
        share = round(main_m2 / (main_m2 + cut_m2), 4) if main_m2 else None
        rep.row("navmesh", "connectivity: main landmass share >= 0.99", share, (share or 0) >= 0.99,
                f"{comp.get('islands')} islands ({comp.get('islands_m2')} m2) apart; {comp.get('cut_off_on_a_main_landmass')} pieces cut off")
        pa = p.get("paths", {})
        rep.row("navmesh", f"settlement-pair paths ({PATHS_MIN})", f"{pa.get('ok')}/{pa.get('pairs')}",
                (pa.get("pairs") or 0) >= PATHS_MIN and pa.get("ok") == pa.get("pairs"))

    @section(rep, "lod")
    def _lod():
        ls = plugin / "map/LODSettings/ArgoniaBlackMarsh.lod"
        rep.row("lod", ".lod settings file (16 bytes)", ls.stat().st_size if ls.exists() else "missing",
                ls.exists() and ls.stat().st_size == 16)
        listing = OUT / "lod/files.txt"
        if not listing.exists():
            rep.fail("lod", "terrain LOD files expected/found per level", "out/newworld/lod/files.txt missing: the LOD run (lod.sh stage) is owed")
            return
        p = subprocess.run([sys.executable, "-m", "tools.newworld.world.mapdata", "check", str(listing), "--plugin", str(plugin)],
                           cwd=REPO, capture_output=True, text=True)
        rep.row("lod", "terrain LOD files expected/found per level", p.stdout.strip().replace("\n", "; "), p.returncode == 0)

    @section(rep, "map")
    def _map():
        w = H.get("world") or {}
        nw, se = w.get("map_nw") or [0, 0], w.get("map_se") or [0, 0]
        ok = se[0] > nw[0] and nw[1] > se[1]  # usable size stays 0,0 as on Tamriel; the NW/SE pan box carries the map
        rep.row("map", "world map pan box (WRLD MNAM NW/SE cells)", f"NW{nw} SE{se}", ok,
                "" if ok else "MNAM empty: world.sh's map stage (nwmap apply) has not run on this ESM")
        mk = w.get("map_markers", 0)
        rep.row("map", f"map markers in the persistent cell ({MARKERS})", mk, mk == MARKERS)

    @section(rep, "start")
    def _start():
        m = H.get("marker")
        rep.row("start", "`coc ArgoniaNWStart` names one cell", H.get("start_cells"), H.get("start_cells") == 1)
        if not m:
            rep.fail("start", "start marker on dry ground", "ArgoniaNWStartMarker not in the ESM")
            return
        ok = m["ground"] > m["water"] and m["ground"] <= m["pos"][2] <= m["ground"] + 64
        rep.row("start", "start marker on dry ground, within 64 units above it", f"z {m['pos'][2]:.0f}, ground {m['ground']:.0f}", ok,
                f"cell {m['cell']}")

    @section(rep, "deploy")
    def _deploy():
        # Our plugins are laid from C:\argonia\ours (stack.ps1's $OursPlugins), not staged as a mod row, so the deploy is
        # proved by stack.ps1 laying the ESM in the NewWorld profile and by the machine's copy (lod.sh send reads its
        # hash back into verify/play-esm.sha256) being this build.
        ps1 = (Path(__file__).resolve().parents[2] / "infra/gpu-box/stack.ps1").read_text(encoding="utf-8", errors="replace")
        lays = "ours\\newworld\\ArgoniaNewWorld.esm" in ps1 and "$World -eq 'NewWorld'" in ps1
        rep.row("deploy", "stack.ps1 lays ArgoniaNewWorld.esm in the NewWorld profile only", lays, lays,
                "" if lays else "stack.ps1 has no NewWorld-only ours\\newworld\\ArgoniaNewWorld.esm entry")
        shaf = OUT / "verify/play-esm.sha256"
        sha = hashlib.sha256((plugin / ESM).read_bytes()).hexdigest()
        have = shaf.read_text().strip() if shaf.exists() else ""
        rep.row("deploy", "the play machine's ESM is this build", have[:12] or "-", have == sha,
                f"built {sha[:12]}" if have else "no record: run `infra/gpu-box/lod.sh send`")
        pv = OUT / "verify/play-verify.txt"
        rep.row("deploy", "play machine's `stack.py verify --profile NewWorld` record", "found" if pv.exists() else "missing",
                pv.exists() and "FAIL" not in pv.read_text(errors="replace"),
                "" if pv.exists() else f"{pv.relative_to(REPO)}: save the play machine's verify output there after the push")

    @section(rep, "places")
    def _places():
        # the place layer (tools/places build/check, docs/design/place-studio.md): rows only once a layer is built
        pl = REPO / "out/places/plugin"
        if not (pl / "build.json").exists():
            return
        b = json.loads((pl / "build.json").read_text())
        sha = hashlib.sha256((plugin / ESM).read_bytes()).hexdigest()
        rep.row("places", "ArgoniaNWPlaces.esp is built over this world ESM", b.get("world_sha256", "")[:12], b.get("world_sha256") == sha,
                "" if b.get("world_sha256") == sha else "rerun `python -m tools.places build`")
        for pid in sorted(b.get("places") or {}):
            c = REPO / "out/places/shards" / pid / "check.json"
            if not c.exists():
                rep.fail("places", f"{pid}: every place check green", f"never checked: run `python -m tools.places check {pid}`")
                continue
            r = json.loads(c.read_text())
            if r.get("esp_sha256") != b.get("esp_sha256"):
                rep.row("places", f"{pid}: every place check green", "stale", False,
                        f"the check read another build of the plugin: rerun `python -m tools.places check {pid}`")
                continue
            red = [f"{k} {v['n']}" for k, v in sorted(r["results"].items()) if not v["ok"]]
            rep.row("places", f"{pid}: every place check green", f"{len(r['results']) - len(red)}/{len(r['results'])}", not red,
                    ", ".join(red))

    return finish(rep, out, t0)


_ASSETS: list = []


def assets() -> Assets:
    if not _ASSETS:
        _ASSETS.append(Assets())
    return _ASSETS[0]


def place_rows(rep: Report, natural: list[dict], out: Path) -> None:
    """The placement checks (tools/newworld/place/checks.py) run over the refs read back from the ESM."""
    from tools.newworld.place import checks
    from tools.newworld.place import place as P
    src = P.REFS / "bases.json"
    bases = jload(src)["bases"]
    by_key = {b["key"].lower(): b for b in bases}
    def em(edid, model):  # two sources may share an editor id (BM&V North and Valenwood): the model tells them apart
        return (edid or "").lower(), MESHES.sub("", (model or "").replace("/", "\\")).lower()
    by_edid = {em(b["edid"], b["model"]): b for b in bases}
    Pa = P.Palette(P.World())
    rows, unmapped = [], 0
    for r in natural:
        e = (r["edid"] or "").lower()
        b = by_key.get(r["base"].lower()) or by_edid.get(em(re.sub(r"^anw_[a-z0-9]+_", "", e), r["model"]))  # ForeignCopy: ANW_<initials>_<edid>
        if b is None:
            unmapped += 1
            continue
        db = b["db_id"]
        cls = Pa.class_of.get(db, "road_dressing")
        pos = [float(r["x"]), float(r["y"]), float(r["z"])]
        rows.append({"base": b["ref"], "key": b["key"], "db": db, "cls": cls, "cell": [int(r["cx"]), int(r["cy"])],
                     "pos": pos, "rot": [float(r["rx"]), float(r["ry"]), float(r["rz"])], "scale": float(r["scale"]), "model": b["model"]})
    rep.row("refs", "every placed ref maps to a catalogued base", unmapped, unmapped == 0)
    work = out / "refs"
    work.mkdir(exist_ok=True)
    shutil.copy(src, work / "bases.json")
    P.REFS = work
    checks.load = lambda: rows
    checks.run()
    c = jload(work / "check.json")
    sw = c["trees_in_standing_water"]
    op = c["open_sides_facing_uphill"]
    pc = c["refs_per_cell"]
    v = c["variety"]
    for req, val, ok in [
        ("no refs on roads", c["refs_on_road_surface"], c["refs_on_road_surface"] == 0),
        ("no trees in flowing water", c["trees_in_flowing_water"], c["trees_in_flowing_water"] == 0),
        ("trees in standing water only per habitat rule", f"{c['trees_in_standing_water_against_rule']} against, {sw['count']} in",
         c["trees_in_standing_water_against_rule"] == 0),
        ("seating error <= 0.45 m (LAND step + quad twist)", c["seating_error_max_m"], "seating_error_max_m" not in c["fails"]),
        ("rocks: no open underside above ground", c["rocks_with_open_underside_above_ground"], c["rocks_with_open_underside_above_ground"] == 0),
        ("cliffs: open sides within 45 deg of uphill >= 95%", f"{op['within_45deg']}/{op['of']}", "open_sides_uphill_share_ok" not in c["fails"]),
        ("cliffs no taller than their hill", c["cliffs_taller_than_their_hill"], c["cliffs_taller_than_their_hill"] == 0),
        ("no two refs closer than 1 m", c["pairs_closer_than_1m"], c["pairs_closer_than_1m"] == 0),
        (f"refs per cell <= {REFS_CAP}", f"p50 {pc['p50']}, p99 {pc['p99']}, max {pc['max']}", pc["max"] <= REFS_CAP),
        (f"regional variety: Jaccard max <= {JACCARD_MAX}", f"max {v['jaccard_max']}, mean {v['jaccard_mean']}", v["jaccard_max"] <= JACCARD_MAX),
        ("regional variety: distinct bases in every region >= 10", min(v["distinct_bases_per_region"].values()),
         min(v["distinct_bases_per_region"].values()) >= 10),
    ]:
        rep.row("refs", req, val, ok)


def finish(rep: Report, out: Path, t0: float) -> int:
    (out / "report.md").write_text(rep.md())
    (out / "report.json").write_text(json.dumps({"rows": rep.rows, "seconds": round(time.time() - t0, 1)}, indent=1, default=str))
    n = Counter(r["result"] for r in rep.rows)
    for r in rep.rows:
        print(f"{r['result']}  {r['area']}: {r['requirement']} = {r['value']}" + (f"  ({r['detail']})" if r["detail"] and r["result"] == "FAIL" else ""))
    print(f"verify: {n['PASS']} PASS, {n['FAIL']} FAIL in {time.time() - t0:.0f} s -> {out / 'report.md'}")
    return 1 if n["FAIL"] else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plugin", type=Path, default=OUT / "plugin")
    ap.add_argument("--out", type=Path, default=OUT / "verify")
    ap.add_argument("--no-dump", action="store_true", help="judge the last dump again")
    a = ap.parse_args(argv)
    return run(a.plugin, a.out, not a.no_dump)


if __name__ == "__main__":
    sys.exit(main())
