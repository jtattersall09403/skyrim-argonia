"""The piece resolver (0.4 §a): a kit id or a mesh path -> the source plugin and base record that places it.

A piece is one of
  * a mesh path, ``meshes/.../x.nif`` (any case, either slash);
  * an asset id ``<pool>:<path>`` from the asset registry (the registry row names its mesh);
  * a composite id ``composite:<name>``, which expands to its member pieces (each resolved in turn).

Resolution, in order: a base record in the synced plugins whose model is that mesh (``base``); else the mesh
exists in the plugins' archives or loose files with no base record, so a new STAT of ours places it
(``new-stat``); else ``unresolved``. A place's design that uses an unresolved piece fails the L1 check.

The index (``out/pieces-index.json``) is written by ``ArgoniaGen index`` from the player's own plugins and
archives on the build VM; it is derived from game files and never committed (decision 0003).

    python3 -m tools.argonia_world.pieces check [--index out/pieces-index.json] [--pieces FILE] [--registry FILE]
        [--places a,b]  FILE of pieces: a JSON list of piece strings, or {"place": [pieces]}; default the
        layouts of every place (or of --places; the gate passes the places the plugin builds) through db.py.
        Exit 1 on any unresolved piece, listing each with why.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "out" / "pieces-index.json"
PREFERENCE = ROOT / "data" / "pieces-preference.json"
# Among several base records for one mesh: the preference tier (data/pieces-preference.json: a kit's own mod for
# its folder, then the Black Marsh mods, Tropical Skyrim, vanilla, other mods, the DLCs last, 0006 §8), then the
# later plugin in load order, then the kind a placed piece most often is, then the lowest FormID (vanilla's snow
# and ice variants come later, so the plain one wins).
TYPE_RANK = {"Static": 0, "MoveableStatic": 1, "Furniture": 2, "Door": 3, "Container": 4, "Activator": 5,
             "Light": 6, "Flora": 7, "Tree": 8, "Grass": 9}


class Preference:
    """The tier of a (mesh, plugin) pair, from the preference table."""

    def __init__(self, doc: dict):
        self.tiers = {t: i for i, t in enumerate(doc["tiers"])}
        self.plugins = [(r["pattern"].lower(), self.tiers[r["tier"]]) for r in doc["plugins"]]
        self.kits = sorted(((norm_mesh(r["prefix"]), r["plugin"].lower(), self.tiers[r["tier"]]) for r in doc["kits"]),
                           key=lambda k: -len(k[0]))
        self.other = self.tiers["other"]

    @classmethod
    def load(cls, path: Path = PREFERENCE) -> Preference:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def tier(self, mesh: str, plugin: str) -> int:
        p = plugin.lower()
        for prefix, kit, t in self.kits:
            if mesh.startswith(prefix) and p == kit:
                return t
        return next((t for pat, t in self.plugins if fnmatch.fnmatchcase(p, pat)), self.other)


def norm_mesh(p: str) -> str:
    s = p.replace("\\", "/").lstrip("/").lower()
    return s if s.startswith("meshes/") else "meshes/" + s


def stat_edid(mesh: str) -> str:
    """The EditorID of our own STAT for a mesh with no base record."""
    stem = norm_mesh(mesh)[len("meshes/"):].removesuffix(".nif")
    return "ARG_STAT_" + re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_")[:85]


@dataclass(frozen=True)
class Resolution:
    piece: str
    kind: str  # base | new-stat | unresolved
    mesh: str = ""
    form_key: str = ""  # Mutagen spelling; empty for new-stat (the allocator gives it) and unresolved
    plugin: str = ""
    edid: str = ""
    why: str = ""


class Index:
    def __init__(self, doc: dict, prefer: Preference | None = None):
        self.plugins = list(doc["plugins"])
        self.prefer = prefer or Preference.load()
        rank = {p.lower(): i for i, p in enumerate(self.plugins)}
        self.by_mesh: dict[str, list[dict]] = {}
        for r in doc["records"]:
            self.by_mesh.setdefault(norm_mesh(r["mesh"]), []).append(r)
        for mesh, rows in self.by_mesh.items():
            rows.sort(key=lambda r: (self.prefer.tier(mesh, r["plugin"]), -rank.get(r["plugin"].lower(), -1),
                                     TYPE_RANK.get(r["type"], 99), int(r["formKey"].split(":")[0], 16)))
        self.meshes = {norm_mesh(m) for m in doc["meshes"]} | set(self.by_mesh)
        self.by_edid: dict[str, set[str]] = {}
        for r in doc["records"]:
            self.by_edid.setdefault(r["edid"], set()).add(r["formKey"])

    def form_keys_of(self, edid: str) -> set[str]:
        """The FormKeys of the masters' records with this EditorID (an override keeps its origin's key)."""
        return set(self.by_edid.get(edid, ()))

    @classmethod
    def load(cls, path: Path = INDEX) -> Index:
        if not Path(path).exists():
            raise FileNotFoundError(f"{path}: run `make plugin` (ArgoniaGen index) on the build VM first")
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))


class Resolver:
    def __init__(self, index: Index, registry: dict[str, str] | None = None,
                 composites: dict[str, list[str]] | None = None):
        self.index = index
        self.registry = {k: norm_mesh(v) for k, v in (registry or {}).items()}  # asset id -> mesh
        self.composites = composites or {}

    def mesh_of(self, piece: str) -> tuple[str, str]:
        """(mesh, why-not) for a non-composite piece."""
        if piece.lower().endswith(".nif"):
            return norm_mesh(piece), ""
        if piece in self.registry:
            return self.registry[piece], ""
        return "", "not a mesh path and not in the asset registry"

    def resolve(self, piece: str, _open: tuple[str, ...] = ()) -> list[Resolution]:
        """One resolution per placed piece (a composite gives one per member)."""
        if piece.startswith("composite:"):
            if piece in _open:
                return [Resolution(piece, "unresolved", why="composite contains itself")]
            members = self.composites.get(piece)
            if not members:
                return [Resolution(piece, "unresolved", why="composite with no member list")]
            return [r for m in members for r in self.resolve(m, (*_open, piece))]
        mesh, why = self.mesh_of(piece)
        if not mesh:
            return [Resolution(piece, "unresolved", why=why)]
        rows = self.index.by_mesh.get(mesh)
        if rows:
            r = rows[0]
            return [Resolution(piece, "base", mesh, r["formKey"], r["plugin"], r["edid"])]
        if mesh in self.index.meshes:
            return [Resolution(piece, "new-stat", mesh, edid=stat_edid(mesh))]
        return [Resolution(piece, "unresolved", mesh, why="mesh in no synced plugin's archives or loose files")]

    def unresolved(self, pieces) -> list[Resolution]:
        return [r for p in sorted(set(pieces)) for r in self.resolve(p) if r.kind == "unresolved"]


def asset_mesh(asset_id: str) -> str:
    """The registry's rule for a ``<pool>:<path>`` asset id: ``meshes/<path>.nif`` (34,119 of the imported
    registry's 34,169 rows; the 50 that differ are htbm texture-folder meshes, which no design places). The
    registry joins the world database with the chunk that first needs its other columns."""
    pool, _, path = asset_id.partition(":")
    return norm_mesh(path + ".nif") if pool and path and pool != "composite" else ""


def db_pieces(world=None, places=None) -> dict[str, list[str]]:
    """Every (or the named) place's design pieces from the world's layouts, through db.py (decision 0030)."""
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    out: dict[str, list[str]] = {}
    for r in w.rows("layout_place"):
        if places is None or r.place_id in places:
            out.setdefault(r.place_id, []).append(r.asset)
    return out


def main(argv: list[str]) -> int:
    if argv[:1] != ["check"]:
        print(__doc__)
        return 2
    opts = dict(zip(argv[1::2], argv[2::2]))
    index = Index.load(Path(opts.get("--index", INDEX)))
    registry: dict[str, str] = {}
    composites: dict[str, list[str]] = {}
    if "--registry" in opts:
        doc = json.loads(Path(opts["--registry"]).read_text(encoding="utf-8"))
        registry, composites = doc.get("assets", {}), doc.get("composites", {})
    if "--pieces" in opts:
        doc = json.loads(Path(opts["--pieces"]).read_text(encoding="utf-8"))
        by_place = doc if isinstance(doc, dict) else {"(file)": doc}
    else:
        places = set(opts["--places"].split(",")) - {""} if "--places" in opts else None
        if places == set():
            print("pieces: no place is built yet (no place layer in the plugin); nothing to check")
            return 0
        by_place = db_pieces(places=places)
        registry = {p: asset_mesh(p) for ps in by_place.values() for p in ps if asset_mesh(p)} | registry
    res = Resolver(index, registry, composites)
    bad = 0
    for place, pieces in sorted(by_place.items()):
        for r in res.unresolved(pieces):
            print(f"pieces: {place}: {r.piece}: unresolved ({r.why})")
            bad += 1
    total = sum(len(set(p)) for p in by_place.values())
    print(f"pieces: {total} pieces over {len(by_place)} places, {bad} unresolved")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
