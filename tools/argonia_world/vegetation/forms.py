"""The Black Marsh mods' landscape forms (1.15 §e.1): every TREE, FLOR and STAT of BM&V, King of the Murkmire,
Here There Be Monsters, Depths of Skyrim and Mud Mother Grove whose mesh is a tree, plant, rock or mushroom, with
its OBND, its mesh path, where the stack resolves that mesh (a mod's own file, or the base game's: vanilla) and how
often the mod itself places it. Read from the laid stack (~/.argonia/stack/MO2, never the repo: decision 0003).

    python3 -m tools.argonia_world.vegetation forms [--tsv out/vegetation/forms.tsv]

The role is read from the editor ID and mesh path (ROLE_WORDS, first match wins); a form with no role word, or one
under an excluded path (EXCLUDE: architecture, clutter, weapons, ships, dungeons), is not landscape and is left out.
"""
from __future__ import annotations

import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from tools.navmesh.meshes import STACK

# Load order as the stack lays it (modlist.txt): BM&V first, then the gap-fillers (1.15 common: BM&V whole).
PLUGINS = (
    ("bmv", "Black Marsh.esm"),
    ("king-of-the-murkmire", "King of the Murkmire.esp"),
    ("htbm", "Here There Be Monsters.esp"),
    ("depths-of-skyrim", "DepthsOfSkyrim.esp"),
    ("mud-mother-grove", "ArgonianLakeHouse.esl"),
)
TYPES = ("TREE", "FLOR", "STAT")
EXCLUDE = ("architecture", "clutter", "weapon", "ship", "dungeon", "xanmeer", "mihail", "elements of skyrim",
           "furniture", "effects", "interior", "dwemer", "falmer", "imperial", "nord", "dragon", "snow", "ice",
           "frost", "pine", "aspen", "tundra", "reach", "winter", "skyrim\\", "farmhouse", "wheat", "lantern",
           "candle", "totem", "fence", "tent", "hut", "wallart", "wallhanging", "test", "marker")
# role -> words (lower-case, in the editor ID or mesh path); the order is the precedence
ROLE_WORDS = (
    ("mushroom", ("mushroom", "shroom", "tr_flora_ac", "cupling", "fungus", "bracket", "parasol")),
    ("rock", ("rock", "boulder", "stone0", "mountaintrim", "slab")),
    ("mangrove", ("mangrove",)),
    ("emergent", ("hist", "gkbjungletreenew", "giant", "ancient")),
    ("palm", ("palm",)),
    ("aquatic", ("lily", "lilli", "kelp", "seaweed", "reed", "cattail", "coral", "waterplan", "lotus", "marshgrass",
                 "tallgrass", "bulrush")),
    ("deadwood", ("log", "stump", "driftwood", "deadwood", "branch", "root")),
    ("gallery", ("willow", "bamboo", "weeping", "moss0", "hangingmoss")),
    ("canopy", ("tree", "cypress", "poplar", "birch", "jungle", "ceiba", "kapok", "banyan", "oak")),
    ("shrub", ("bush", "shrub", "fern", "braken", "bracken", "plant", "weed", "flower", "nettle", "chickweed", "vine",
               "undergrowth", "gorse", "ivy", "saltrice", "kanet", "heather", "thistle", "grass", "frond", "leaf")),
)


@dataclass(frozen=True)
class Form:
    form_key: str  # "0ABCDE:Black Marsh.esm"
    edid: str
    sig: str
    mod: str
    model: str
    obnd: tuple[int, int, int, int, int, int] | None
    role: str
    placed: int  # REFRs to it in its own plugin
    mesh_from: str | None  # "loose:<mod>", "<archive>.bsa", or None (not in any mod: the base game's mesh)


def role_of(edid: str, model: str) -> str | None:
    """The mesh's file name, then its path, decides (BM&V names forms loosely: its `01giantmushroom` is a gorse bush); the editor ID only
    when the path names no role."""
    if any(x in f"{edid} {model}".lower() for x in EXCLUDE):
        return None
    name = model.replace("\\", "/").rsplit("/", 1)[-1].lower()
    for s in (name, model.lower(), edid.lower()):  # the file name first: BM&V keeps bushes under landscape\trees
        for role, words in ROLE_WORDS:
            if any(w in s for w in words):
                return role
    return None


def mesh_key(model: str) -> str:
    return "meshes/" + model.replace("\\", "/").lower().lstrip("/")


def mesh_source(f: Form, bmv_nifs: set[str]) -> str:
    """Where the game gets the form's mesh: a laid mod's file, BM&V's archive (laid once its keep list names it),
    or no mod at all (the base game's mesh: vanilla, never used)."""
    if f.mesh_from:
        return "laid:" + f.mesh_from.split(":", 1)[1] if f.mesh_from.startswith("loose:") else "laid:" + f.mesh_from
    return "bmv" if mesh_key(f.model) in bmv_nifs else "vanilla"


def write(w, inv: list[Form], bmv_nifs: set[str]) -> dict:
    """Replace object_form with the inventory (every Skyrim.esm form dropped); returns counts per (mod, source)."""
    for t in ("land_region_object", "vegetation_form"):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    w.con.execute("DELETE FROM object_form WHERE form_key NOT LIKE '%:ArgoniaWorld.esm'")  # keep our rocks.py STATs
    w.dirty.add("object_form")
    n = Counter()
    for f in inv:
        src = mesh_source(f, bmv_nifs)
        ob = f.obnd or (None,) * 6
        w.insert("object_form", form_key=f.form_key, edid=f.edid, record_type=f.sig, role_id=f.role, ts_model=None,
                 review=("the base game's mesh: never placed (0012)" if src == "vanilla" else
                         f"{f.mod}'s own record and mesh, Black Marsh flora; nothing Nordic in its path (0006)"),
                 mod=f.mod, model=f.model, mesh_source=src, bound_x0=ob[0], bound_y0=ob[1], bound_z0=ob[2],
                 bound_x1=ob[3], bound_y1=ob[4], bound_z1=ob[5], placed_by_mod=f.placed)
        n[(f.mod, src.split(":")[0])] += 1
    return dict(n)


def _zstr(b: bytes | None) -> str:
    return (b or b"").split(b"\0", 1)[0].decode("latin-1")


def read_plugin(path: Path, masters_out: list | None = None):
    """[(local formid, sig, edid, model, obnd)] of its own TREE/FLOR/STAT and {local formid: REFR count}."""
    from tools.argonia_world.terrain import esm
    blob = path.read_bytes()
    masters, own, refs = [], [], Counter()
    for r in esm.records(blob):
        if r.sig == "TES4":
            masters = [_zstr(b) for s, b in r.subs if s == "MAST"]
        elif r.sig in TYPES and (r.formid >> 24) == len(masters):
            ob = r.first("OBND")
            obnd = struct.unpack("<6h", ob) if ob and len(ob) == 12 else None
            own.append((r.formid & 0xFFFFFF, r.sig, _zstr(r.first("EDID")), _zstr(r.first("MODL")), obnd))
        elif r.sig == "REFR":
            n = r.first("NAME")
            if n and (struct.unpack("<I", n)[0] >> 24) == len(masters):
                refs[struct.unpack("<I", n)[0] & 0xFFFFFF] += 1
    if masters_out is not None:
        masters_out.extend(masters)
    return own, refs


def inventory(stack: Path = STACK, resolver=None) -> list[Form]:
    out = []
    for mod, name in PLUGINS:
        p = stack / "mods" / mod / name
        if not p.exists():
            raise FileNotFoundError(f"{p}: the laid stack (infra/gpu-box/stack.py) is not on this machine")
        own, refs = read_plugin(p)
        for fid, sig, edid, model, obnd in own:
            role = role_of(edid, model)
            if not role or not model:
                continue
            src = resolver.where(model) if resolver else None
            out.append(Form(f"{fid:06X}:{name}", edid, sig, mod, model, obnd, role, refs[fid], src))
    return out


def resolver():
    """The stack's mesh resolver over the mods alone (no base-game Data on the build VM: a mesh no mod supplies
    is the base game's)."""
    import tempfile
    from tools.navmesh.meshes import Resolver
    return Resolver(Path(tempfile.mkdtemp()))
