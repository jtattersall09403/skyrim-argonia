"""`terrain check-materials` (1.15 round 4, owner play test 3 findings 16-17): the ground's texture sets as laid.

For every LTEX the material gradient paints (`material.TEXTURES`) it resolves the TXST's diffuse and normal against
the laid stack (the local MO2 mirror `~/.argonia/stack/MO2/mods`, what stack.py pushes, with each row's
dependencies.json `drop` globs applied, loose over BSA; then the vanilla BSAs), and reads the normal's alpha (the
landscape shader's specular) and its relief (the mean tilt of its texels from straight up). It fails on a texture
with no normal, a flat normal, or a specular alpha above vanilla's: the bar is measured from Skyrim.esm's own 50
landscape normals (`textures/landscape/*_n.dds`), never set by hand (0034). It also fails on a region class whose
gradient lays one land texture only. Never the play machine: the mirror and the BSAs are local.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import dds
from tools.argonia_world.terrain import material as M

MO2 = Path.home() / ".argonia" / "stack" / "MO2" / "mods"
VANILLA = Path.home() / "games" / "skyrimse" / "Data"
DEPS = Path(__file__).resolve().parents[3] / "data" / "dependencies.json"
FLAT_DEG = 3.0  # a normal whose texels tilt less than this on average lights no relief (vanilla's flattest: below)


def _drops() -> dict[str, list[str]]:
    d = json.loads(DEPS.read_text(encoding="utf-8"))
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if "id" in o and "drop" in o:
                out[o["id"]] = [p.lower() for p in o["drop"]]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    return out


def _bsa_index(path: Path) -> tuple[int, list[tuple[str, int, int]]]:
    """(flags, [(lower path, size, offset)]) of a v104/v105 BSA, reading only its directory (whole-file reads of
    every mod BSA took 5 minutes)."""
    import struct
    with path.open("rb") as fh:
        b = fh.read(36)
        _, ver, off, flags, nf, _, _, tfn, _ = struct.unpack_from("<4sIIIIIIII", b, 0)
        rec = 24 if ver >= 105 else 16
        fh.seek(0)
        n = 1 << 20
        while True:
            b = fh.read(n) if n < path.stat().st_size else path.read_bytes()
            try:
                counts = [struct.unpack_from("<I", b, off + i * rec + 8)[0] for i in range(nf)]
                o, recs = off + nf * rec, []
                for c in counts:
                    ln = b[o]
                    d = b[o + 1:o + ln].rstrip(b"\0").decode("latin-1")
                    o += 1 + ln
                    recs += [(d, *struct.unpack_from("<QII", b, o + 16 * j)[1:]) for j in range(c)]
                    o += 16 * c
                if o + tfn > len(b):
                    raise IndexError
                names = b[o:o + tfn].split(b"\0")
                break
            except (IndexError, struct.error):
                if n >= path.stat().st_size:
                    raise
                n *= 8
                fh.seek(0)
    return flags, [((d + "\\" + nm.decode("latin-1")).lower().replace("\\", "/"), sz, fo)
                   for (d, sz, fo), nm in zip(recs, names)]


def _read(path: Path, flags: int, sz: int, fo: int) -> bytes:
    """One file of a BSA by ranged read (lz4 when compressed), as mesh_textures._bsa_file."""
    from tools.argonia_world.vegetation.mesh_textures import _bsa_file
    raw = sz & 0x3FFFFFFF
    with path.open("rb") as fh:
        fh.seek(fo)
        blob = fh.read(raw)
    return _bsa_file(blob, flags, sz, 0)


class Stack:
    """lower path -> (source row, reader) over the laid stack: loose files win over every BSA, vanilla last."""

    def __init__(self, mo2: Path = MO2, vanilla: Path = VANILLA, prefix: str = "textures/"):
        self.where: dict[str, tuple[str, Path, tuple | None]] = {}
        self.vanilla: dict[str, tuple[str, Path, tuple]] = {}  # Skyrim's own, whatever overrides it
        for b in sorted(vanilla.glob("*.bsa")):
            fl, recs = _bsa_index(b)
            for p, sz, fo in recs:
                if p.startswith(prefix):
                    self.vanilla.setdefault(p, ("vanilla", b, (fl, sz, fo)))
        self.where.update(self.vanilla)
        drops = _drops()
        loose = {}
        for m in sorted(x for x in mo2.iterdir() if x.is_dir()) if mo2.exists() else []:
            pats = drops.get(m.name, [])
            for f in m.rglob("*"):
                if not f.is_file():
                    continue
                r = str(f.relative_to(m)).lower().replace("\\", "/")
                if any(fnmatch.fnmatch(r, p) or r.startswith(p.rstrip("/") + "/") for p in pats):
                    continue
                if r.endswith(".bsa"):
                    fl, recs = _bsa_index(f)
                    for p, sz, fo in recs:
                        if p.startswith(prefix):
                            self.where[p] = (m.name, f, (fl, sz, fo))
                elif r.startswith(prefix):
                    loose[r] = (m.name, f, None)
        self.where.update(loose)

    def get(self, path: str, table: dict | None = None) -> tuple[str, bytes] | None:
        p = "textures/" + path.lower().replace("\\", "/")
        hit = (self.where if table is None else table).get(p)
        if hit is None:
            return None
        row, f, rec = hit
        return row, (f.read_bytes() if rec is None else _read(f, *rec))


def normal_stats(b: bytes) -> dict:
    px = dds.mip0(b)
    n = px[..., :3] / 255.0 * 2 - 1
    tilt = np.degrees(np.arccos(np.clip(n[..., 2] / np.maximum(np.linalg.norm(n, axis=-1), 1e-6), -1, 1)))
    hd = dds.header(b)
    return {"format": hd["fourcc"] or f"{hd['bits']}bit", "size": hd["w"], "mips": hd["mips"],
            "alpha_mean": round(float(px[..., 3].mean()), 1), "tilt_deg": round(float(tilt.mean()), 1)}


def vanilla_bar(stack: Stack) -> dict:
    """Skyrim.esm's landscape normals as the player's BSAs hold them (overridden or not): per-file alpha means."""
    means, tilts, per = [], [], {}
    for p in sorted(stack.vanilla):
        if p.startswith("textures/landscape/") and p.count("/") == 2 and p.endswith("_n.dds"):
            s = normal_stats(stack.get(p[len("textures/"):], stack.vanilla)[1])
            means.append(s["alpha_mean"])
            tilts.append(s["tilt_deg"])
            per[p] = s["alpha_mean"]
    if not means:
        return {"files": 0}
    a = np.array(means)
    return {"files": len(means), "alpha_mean": round(float(a.mean()), 1), "alpha_p50": round(float(np.median(a)), 1),
            "alpha_p90": round(float(np.percentile(a, 90)), 1), "alpha_max": round(float(a.max()), 1),
            "tilt_min": round(float(min(tilts)), 1), "tilt_p50": round(float(np.median(tilts)), 1), "per_file": per}


def class_problems() -> list[str]:
    """A region class whose gradient lays one land texture only (above the water: dh's top above the line)."""
    out = []
    for c, stops in M.STOPS.items():
        land = {s.ltex for s in stops if s.dh[1] > M.L}
        if len(land) < 2:
            out.append(f"class {c}: one land texture only ({', '.join(sorted(land))})")
    return out


def check(stack: Stack | None = None) -> dict:
    stack = stack or Stack()
    bar = vanilla_bar(stack)
    if not bar.get("files"):
        return {"rows": [], "vanilla": bar, "fails": ["no vanilla landscape normals found: is the Skyrim Data local?"]}
    limit = bar["alpha_p90"]
    rows, fails = [], list(class_problems())
    for t in M.TEXTURES:
        r = {"ltex": t.edid, "diffuse": t.bmv, "normal": t.normal}
        d = stack.get(t.bmv)
        r["diffuse_row"] = d[0] if d else None
        if d:
            hd = dds.header(d[1])
            r["diffuse_format"], r["diffuse_mips"] = hd["fourcc"], hd["mips"]
        n = stack.get(t.normal)
        r["normal_row"] = n[0] if n else None
        if d is None:
            fails.append(f"{t.edid}: diffuse {t.bmv} is laid by no row")
        if n is None:
            fails.append(f"{t.edid}: no normal map ({t.normal} resolves nowhere)")
        else:
            r |= normal_stats(n[1])
            if r["tilt_deg"] < FLAT_DEG:
                fails.append(f"{t.edid}: flat normal {t.normal} (mean tilt {r['tilt_deg']} deg < {FLAT_DEG})")
            own = bar["per_file"].get("textures/" + t.normal.lower().replace("\\", "/"))
            # the bar is vanilla's p90 over its 50 landscape normals; a texture may carry what Skyrim.esm itself
            # paints that same LTEX with (its own normal, e.g. the wet riverbed family), never more
            r["limit_alpha"] = max(limit, own or 0.0)
            if r["alpha_mean"] > r["limit_alpha"]:
                fails.append(f"{t.edid}: specular alpha {r['alpha_mean']} on {t.normal} ({r['normal_row']}) above "
                             f"vanilla's ({r['limit_alpha']})")
        rows.append(r)
    return {"rows": rows, "vanilla": bar, "limit_alpha": limit, "fails": fails}


def main(out: Path | None = None) -> int:
    res = check()
    for r in res["rows"]:
        print(f"{r['ltex']:22s} {r['diffuse']:44s} [{r['diffuse_row']}, mips {r.get('diffuse_mips')}]  "
              f"{r['normal']:34s} [{r['normal_row']}] alpha {r.get('alpha_mean')} tilt {r.get('tilt_deg')}")
    print("vanilla landscape normals:", json.dumps({k: v for k, v in res["vanilla"].items() if k != "per_file"}))
    for f in res["fails"]:
        print("FAIL", f)
    if out:
        out.write_text(json.dumps(res, indent=1) + "\n")
    print(f"check-materials: {len(res['rows'])} textures, {len(res['fails'])} fails")
    return 1 if res["fails"] else 0
