"""Every mesh, texture and sound our New World plugins name, checked against what the New World card stages.

For each record our plugins hold (the world file and the places plugin; any record type), every asset path it
names (MODL/MOD2-5 and any other string sub-record ending in an asset extension, TXST TX00-TX07, weather cloud
layers, sound files) is resolved as the game resolves it on the NewWorld card (tools/places/assets/resolve.py:
loose winners of the profile's install record, then archives a load order actually loads). Each NIF found is read
for every texture path it names (BSShaderTextureSet, BSEffectShaderProperty, any length-prefixed `.dds` string).
A missing file is ranked by the placed uses that reach it: references to a base (REFR/ACHR NAME), land quadrants
that carry a landscape texture (LAND BTXT/ATXT), and through the LTEX the grass (GNAM) and texture set (TNAM).

    python -m tools.newworld.assets_audit [--json OUT] [--plugin PATH ...]

Exit 1 when anything is missing (the readback gate)."""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALIASES = REPO / "mods/texture-aliases.json"          # laid by the stack at stage time (stack.py lay_aliases)
ALLOWED = REPO / "newworld/sources/assets_missing_allowed.json"  # path -> why it may stay missing
PLUGINS = [REPO / "out/newworld/plugin/ArgoniaNewWorld.esm", REPO / "out/places/plugin/ArgoniaNWPlaces.esp"]
ROOTS = {".nif": "meshes", ".dds": "textures", ".wav": "sound", ".xwm": "sound", ".fuz": "sound"}
# path-bearing sub-records that are not plain zstrings ending in an extension are none in SSE; the scan is generic
_ASSET = re.compile(rb"^[\x20-\x7e]+\.(nif|dds|wav|xwm|fuz)$", re.I)
_DDS = re.compile(rb"\.dds", re.I)
# references to a base (counted as placed uses)
_PLACED = {"REFR", "ACHR", "PGRE", "PHZD"}
# the master record types that carry a model or texture (read from a master for the bases we use)
MODEL_SIGS = {"GRAS", "LTEX", "TXST", "STAT", "MSTT", "TREE", "FLOR", "ACTI", "FURN", "CONT", "DOOR", "LIGH", "MISC",
              "SCOL", "WATR", "INGR", "ALCH", "BOOK", "WEAP", "ARMO", "AMMO", "KEYM", "SLGM", "IDLM", "ADDN", "NPC_",
              "EFSH", "SNDR", "SOUN", "MATO", "HAZD", "PROJ", "EXPL", "ARTO", "TACT", "BPTD", "CREA"}


def nif_textures(data: bytes) -> list[str]:
    """Every texture path a NIF names: each `.dds` that ends a length-prefixed string (NIF strings are u32 length +
    bytes, in the header string table and in BSShaderTextureSet / effect shader blocks)."""
    out = set()
    for m in _DDS.finditer(data):
        end = m.end()
        for start in range(end - 4, max(3, end - 260), -1):
            if not 0x20 <= data[start] <= 0x7e:
                break
            if struct.unpack_from("<I", data, start - 4)[0] == end - start:
                out.add(data[start:end].decode("ascii").lower())
                break
    return sorted(out)


def asset_paths(subs: list[tuple[str, bytes]]) -> list[tuple[str, str]]:
    """(sub-record, path) for every sub-record that is one asset path."""
    out = []
    for sig, d in subs:
        s = d.rstrip(b"\0")
        if 4 < len(s) < 260 and b"\0" not in s and _ASSET.match(s):
            out.append((sig, s.decode("ascii")))
    return out


def norm_asset(path: str) -> str:
    from tools.places.assets.resolve import norm
    ext = Path(path.lower()).suffix
    root = ROOTS.get(ext, "meshes")
    p = path.replace("/", "\\").lower()
    if p.lstrip("\\").removeprefix("data\\").startswith("music\\"):  # a music track (MUST ANAM) is Data\Music\..., not sound
        root = "music"
    cut = p.find("\\data\\" + root + "\\")      # an authoring tool's absolute path: the game reads from data\
    return norm(p[cut + 6:] if cut >= 0 else p, root)


def loaded_archive(name: str, active: set[str]) -> bool:
    """A BSA the game loads: the vanilla set and Creation Club archives by ini, else one named after an active plugin
    (`<plugin>.bsa` or `<plugin> - <anything>.bsa`)."""
    n = name.lower()
    if n.startswith(("skyrim - ", "cc")) or n in {"update.bsa", "dawnguard.bsa", "hearthfires.bsa", "dragonborn.bsa",
                                                 "marketplacetextures.bsa", "_resourcepack.bsa"}:
        return True
    stem = n[:-4].split(" - ")[0]
    return stem in active


class Audit:
    def __init__(self, resolver, active: set[str] | None = None, masters=(), vanilla_named=b"", aliases=None, allowed=None):
        self.R, self.masters, self.vanilla = resolver, list(masters), vanilla_named.lower()
        self.aliases = {k.replace("/", "\\").lower(): v for k, v in (aliases or {}).items()}  # wanted -> [mod, path]
        self.allowed = {k.replace("/", "\\").lower(): v for k, v in (allowed or {}).items()}
        if active is not None:
            self.R._arcs = [(n, a) for n, a in resolver.archives() if loaded_archive(n, active)]
        self._nif: dict[str, list[str] | None] = {}

    def nif(self, key: str) -> list[str] | None:
        if key not in self._nif:
            b = self.R.read(key)
            if b is None and key in self.aliases:      # an aliased mesh: the mod's own file at its real path
                f = self.R._find(self.R.stack / "MO2" / "mods" / self.aliases[key][0], self.aliases[key][1].lower())
                b = f.read_bytes() if f else None
            self._nif[key] = None if b is None else nif_textures(b)
        return self._nif[key]

    def run(self, plugins) -> dict:
        """plugins: esm.Plugin objects. Returns {checked, missing: [{path, kind, records, uses, via}], ...}."""
        uses: Counter = Counter()            # form key -> placed uses
        ltex_quads: Counter = Counter()
        recs = {}
        for p in plugins:
            for r in p.records():
                if r.sig in _PLACED:
                    b = r.ref("NAME")
                    if b:
                        uses[b] += 1
                elif r.sig == "LAND":
                    for sig, d in r.subs:
                        if sig in ("BTXT", "ATXT") and len(d) >= 4:
                            v = struct.unpack_from("<I", d)[0]
                            if v:
                                ltex_quads[p.form_key(v)] += 1
                elif r.sig not in ("CELL", "WRLD", "NAVM"):
                    recs[r.key] = r
        for k, n in ltex_quads.items():
            uses[k] += n
            lt = recs.get(k)
            if lt is not None:
                for t in [lt.ref("TNAM")] + [lt.plugin.form_key(struct.unpack_from("<I", g)[0]) for g in lt.all("GNAM")]:
                    if t:
                        uses[t] += n
        need: dict[str, dict] = {}             # asset key -> {records, uses, via}

        def want(key: str, rec, via: str | None):
            e = need.setdefault(key, {"records": set(), "uses": 0, "via": set()})
            if rec.edid not in e["records"]:
                e["records"].add(rec.edid or rec.key)
                e["uses"] += uses.get(rec.key, 0)
            if via:
                e["via"].add(via)

        if self.masters:                       # the foreign bases our refs, land and grass lists use
            refd = {k for k in uses if k not in recs}
            for m in self.masters:
                for r in m.records():
                    if r.key in refd and r.key not in recs:
                        recs[r.key] = r
        for r in recs.values():
            for _sig, path in asset_paths(r.subs):
                key = norm_asset(path)
                want(key, r, None)
                if key.endswith(".nif"):
                    for t in self.nif(key) or ():
                        want(norm_asset(t), r, key)
        missing = []
        for key, e in need.items():
            if key not in self.aliases and self.R.where(key) is None:
                missing.append({"path": key, "kind": ROOTS.get(Path(key).suffix, "?"), "records": sorted(e["records"]),
                                "uses": e["uses"], "via": sorted(e["via"])})
        for m in missing:                      # a path Skyrim.esm itself names and the game lacks is vanilla's own
            name = m["path"].split("\\", 1)[1].encode()
            m["vanilla_too"] = bool(self.vanilla) and name in self.vanilla
            m["allowed"] = self.allowed.get(m["path"])
        missing.sort(key=lambda m: (m["vanilla_too"] or bool(m["allowed"]), -m["uses"], m["path"]))
        gate = [m for m in missing if not m["vanilla_too"] and not m["allowed"]]
        return {"records": len(recs), "assets": len(need), "missing": missing,
                "missing_meshes": sum(m["kind"] == "meshes" for m in gate),
                "missing_textures": sum(m["kind"] == "textures" for m in gate),
                "vanilla_too": sum(m["vanilla_too"] for m in missing),
                "allowed": sum(bool(m["allowed"]) and not m["vanilla_too"] for m in missing)}


ENGINE_SIGS = {"IPCT", "ADDN"}   # the engine's own effects (impacts, addon nodes: the water splash), drawn in every world
DEPENDENCIES = REPO / "mods/dependencies.json"


def dropped(deps: dict) -> set[tuple[str, str]]:
    """(mod, data path) of every file a dependency row drops at staging (its `drop` list, exact paths)."""
    return {(m["id"], p.replace("/", "\\").lower()) for m in deps.get("mods", []) for p in m.get("drop", []) if "*" not in p}


def engine_overrides(resolver, skyrim, drops: set[tuple[str, str]]) -> list[dict]:
    """Every model of Skyrim.esm's engine effects (IPCT, ADDN: the water splash among them) that a staged mod lays
    loose over the game's own, and that names a texture nothing staged holds: drawn in every water of every world
    (BM&V's watersplash.nif naming water_ring.dds was the black splash). A path its mod's row drops is not laid."""
    out = []
    for r in skyrim.records():
        if r.sig not in ENGINE_SIGS:
            continue
        for _sig, path in asset_paths(r.subs):
            key = norm_asset(path)
            mod = resolver.loose.get(key)
            if not key.endswith(".nif") or not mod or (mod, key) in drops:
                continue
            f = resolver.loose_file(key)
            gone = [t for t in nif_textures(f.read_bytes()) if resolver.where(norm_asset(t)) is None] if f else []
            if gone:
                out.append({"path": key, "mod": mod, "record": r.edid, "missing": gone})
    return out


def active_plugins(profile_dir: Path) -> set[str]:
    f = profile_dir / "plugins.txt"
    names = {"skyrim", "update", "dawnguard", "hearthfires", "dragonborn", "argonianewworld", "argonianwplaces"}
    if f.exists():
        for ln in f.read_text(errors="replace").splitlines():
            if ln.startswith("*"):
                names.add(ln[1:].strip().rsplit(".", 1)[0].lower())
    return names


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plugin", action="append", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    from tools.argonia_world.esm import Plugin
    from tools.places.assets.resolve import Resolver, STACK
    from tools.places.assets.resolve import DATA
    plugins = [Plugin.read(p) for p in (a.plugin or PLUGINS) if p.exists()]
    names = {m for p in plugins for m in p.masters} - {p.name for p in plugins}
    masters = [Plugin.read(DATA / n, MODEL_SIGS) for n in sorted(names) if (DATA / n).exists()]
    vanilla = (DATA / "Skyrim.esm").read_bytes() if (DATA / "Skyrim.esm").exists() else b""
    aliases = json.loads(ALIASES.read_text())["aliases"] if ALIASES.exists() else {}
    allowed = json.loads(ALLOWED.read_text())["allowed"] if ALLOWED.exists() else {}
    R = Resolver()
    rep = Audit(R, active_plugins(STACK / "MO2/profiles/NewWorld"), masters, vanilla, aliases, allowed).run(plugins)
    sky = Plugin.read(DATA / "Skyrim.esm", ENGINE_SIGS) if (DATA / "Skyrim.esm").exists() else None
    rep["engine_overrides"] = engine_overrides(R, sky, dropped(json.loads(DEPENDENCIES.read_text()))) if sky else []
    print(f"assets audit: {rep['records']} records, {rep['assets']} asset paths; missing "
          f"{rep['missing_meshes']} meshes, {rep['missing_textures']} textures; "
          f"{len(rep['engine_overrides'])} engine effect meshes a mod lays naming a missing texture")
    for e in rep["engine_overrides"]:
        print(f"  {e['path']} ({e['mod']}, {e['record']}) names {', '.join(e['missing'])}")
    for m in [m for m in rep["missing"] if not m["vanilla_too"] and not m["allowed"]][:60]:
        print(f"  {m['uses']:>8}  {m['path']}  <- {', '.join(m['records'][:4])}{' ...' if len(m['records']) > 4 else ''}")
    if rep["allowed"]:
        print(f"  (+{rep['allowed']} on the allow-list with their reasons: {ALLOWED.relative_to(REPO)})")
    if rep["vanilla_too"]:
        print(f"  (+{rep['vanilla_too']} paths Skyrim.esm also names and the game lacks: vanilla's own, not gating)")
    if a.json:
        a.json.write_text(json.dumps(rep, indent=1))
    return 1 if rep["missing_meshes"] or rep["missing_textures"] or rep["engine_overrides"] else 0


if __name__ == "__main__":
    sys.exit(main())
